"""Gardener scheduler tests (T6): metrics, debounce deferral, session-end
flush, and fake-mode cycle-event resilience.

- Completion metrics must count the real NodeAction literals
  ("confirm"/"prune"/"merge"), not the never-emitted "solidify"/"remove".
- The 5s safety debounce must DEFER early Redis events, never ACK-and-drop.
- Ending a session with unprocessed chunks/ghosts must publish a Gardener
  trigger (sessions with < ratio chunks otherwise never get a pass).
- Fake mode must broadcast GardenerCycleEvent even when the cycle fails.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pytest

from app.agents.gardener import NodeAction
from app.api import sessions as sessions_api
from app.models import GardenerCycleEvent, SessionSummary
from app.services import scheduler as scheduler_module
from app.services.scheduler import GardenerScheduler, _summarise_node_actions


class FakeSSEManager:
    """Records broadcast events (pattern from test_flower_lifecycle)."""

    def __init__(self) -> None:
        self.events: list[tuple[str, object]] = []

    async def broadcast(self, session_id: str, event: object) -> None:
        self.events.append((session_id, event))

    def events_of(self, event_type: type) -> list[object]:
        return [event for _, event in self.events if isinstance(event, event_type)]


# ---------------------------------------------------------------------------
# T6.1 — completion metrics from a synthetic action list
# ---------------------------------------------------------------------------


def test_summarise_node_actions_counts_real_literals():
    """confirm -> solidified; prune and merge (source deleted) -> removed."""
    actions = [
        NodeAction(action="confirm", node_id="node-1"),
        NodeAction(action="confirm", node_id="node-2"),
        NodeAction(action="confirm", node_id="node-3"),
        NodeAction(action="prune", node_id="node-4"),
        NodeAction(action="merge", node_id="node-5", merge_into="node-1"),
        NodeAction(action="merge", node_id="node-6", merge_into="node-2"),
    ]

    solidified, removed = _summarise_node_actions(actions)

    assert solidified == 3, "every confirm counts as solidified"
    assert removed == 3, "prunes plus merged-away sources count as removed"


def test_summarise_node_actions_empty_list():
    assert _summarise_node_actions([]) == (0, 0)


# ---------------------------------------------------------------------------
# T6.2 — early events are deferred, not ACKed-and-dropped
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_early_event_deferred_not_dropped(monkeypatch):
    """An event inside the debounce window must still run (after the window)
    and be ACKed — previously it was ACKed and permanently discarded."""
    scheduler = GardenerScheduler()
    scheduler._safety_debounce_seconds = 0.2

    runs: list[str] = []
    acks: list[str] = []

    async def fake_run(session_id: str) -> None:
        runs.append(session_id)

    async def fake_ack(stream: str, group: str, message_id: str) -> None:
        acks.append(message_id)

    monkeypatch.setattr(scheduler_module, "is_fake_llm_enabled", lambda: True)
    monkeypatch.setattr(scheduler, "_run_gardener_fake", fake_run)
    monkeypatch.setattr(scheduler_module, "ack_event", fake_ack)

    loop = asyncio.get_event_loop()

    await scheduler._handle_event("1-0", {"session_id": "s1", "chunk_id": "c1"})
    t_after_first = loop.time()

    # Second event arrives immediately — well inside the debounce window.
    await scheduler._handle_event("2-0", {"session_id": "s1", "chunk_id": "c2"})
    elapsed = loop.time() - t_after_first

    assert runs == ["s1", "s1"], "the early event must be processed, not dropped"
    assert acks == ["1-0", "2-0"], "both events ACKed only after processing"
    assert elapsed >= 0.15, "second run must be deferred past the debounce window"


@pytest.mark.asyncio
async def test_event_outside_window_runs_immediately(monkeypatch):
    """No deferral when the debounce window has already elapsed."""
    scheduler = GardenerScheduler()
    scheduler._safety_debounce_seconds = 0.2

    runs: list[str] = []
    acks: list[str] = []

    async def fake_run(session_id: str) -> None:
        runs.append(session_id)

    async def fake_ack(stream: str, group: str, message_id: str) -> None:
        acks.append(message_id)

    monkeypatch.setattr(scheduler_module, "is_fake_llm_enabled", lambda: True)
    monkeypatch.setattr(scheduler, "_run_gardener_fake", fake_run)
    monkeypatch.setattr(scheduler_module, "ack_event", fake_ack)

    loop = asyncio.get_event_loop()
    # Pretend the last run for this session was long ago.
    scheduler._last_run["s1"] = loop.time() - 60

    start = loop.time()
    await scheduler._handle_event("1-0", {"session_id": "s1", "chunk_id": "c1"})

    assert runs == ["s1"]
    assert acks == ["1-0"]
    assert loop.time() - start < 0.1, "no debounce sleep expected"


# ---------------------------------------------------------------------------
# T6.3 — session end flushes the Gardener when work remains
# ---------------------------------------------------------------------------


class FakeBuilderService:
    def __init__(self, pending: int) -> None:
        self._pending = pending
        self.reset_calls: list[str] = []

    def get_builder_count(self, session_id: str) -> int:
        return self._pending

    def reset_builder_count(self, session_id: str) -> None:
        self.reset_calls.append(session_id)


def _session_record(session_id: str = "s1") -> SessionSummary:
    return SessionSummary(
        id=session_id,
        name="test session",
        language_variant="en-GB",
        created_at=datetime.now(timezone.utc),
        ended_at=None,
    )


def _patch_session_endpoint(monkeypatch, *, builder: FakeBuilderService, published: list, ghosts: list | None = None):
    record = _session_record()

    async def fake_get_session_record(session_id: str):
        return record

    async def fake_update_session_record(session_id: str, **kwargs):
        return record.model_copy(update={"ended_at": kwargs.get("ended_at")})

    async def fake_publish_chunk_added(**kwargs):
        published.append(kwargs)

    async def fake_list_nodes(session_id: str, *, status=None, flower_id=None):
        if ghosts is None:
            raise AssertionError("ghost check must be skipped when chunks are pending")
        return list(ghosts)

    monkeypatch.setattr(sessions_api, "get_session_record", fake_get_session_record)
    monkeypatch.setattr(sessions_api, "update_session_record", fake_update_session_record)
    monkeypatch.setattr(sessions_api, "publish_chunk_added", fake_publish_chunk_added)
    monkeypatch.setattr(sessions_api, "list_nodes", fake_list_nodes)
    monkeypatch.setattr(sessions_api, "get_builder_service", lambda: builder)


@pytest.mark.asyncio
async def test_session_end_flush_publishes_when_chunks_pending(monkeypatch):
    """Ending a session with unpublished Builder runs must publish a trigger."""
    published: list[dict] = []
    builder = FakeBuilderService(pending=2)  # e.g. a 2-chunk session (< ratio 5)
    _patch_session_endpoint(monkeypatch, builder=builder, published=published)

    response = await sessions_api.end_session(session_id="s1")

    assert response.ended_at is not None
    assert len(published) == 1, "session end must publish a Gardener trigger"
    assert published[0]["session_id"] == "s1"
    assert builder.reset_calls == ["s1"], "builder counter cleared on session end"


@pytest.mark.asyncio
async def test_session_end_flush_publishes_when_ghosts_remain(monkeypatch):
    """No pending chunks, but ghost nodes remain -> still flush."""
    published: list[dict] = []
    builder = FakeBuilderService(pending=0)
    _patch_session_endpoint(
        monkeypatch, builder=builder, published=published, ghosts=[object(), object()]
    )

    await sessions_api.end_session(session_id="s1")

    assert len(published) == 1
    assert published[0]["session_id"] == "s1"


@pytest.mark.asyncio
async def test_session_end_no_flush_when_nothing_pending(monkeypatch):
    """Nothing pending and no ghosts -> no spurious Gardener trigger."""
    published: list[dict] = []
    builder = FakeBuilderService(pending=0)
    _patch_session_endpoint(monkeypatch, builder=builder, published=published, ghosts=[])

    await sessions_api.end_session(session_id="s1")

    assert published == []
    assert builder.reset_calls == ["s1"]


@pytest.mark.asyncio
async def test_session_end_flush_failure_does_not_fail_endpoint(monkeypatch):
    """Redis being down must not break ending the session."""
    builder = FakeBuilderService(pending=3)
    record = _session_record()

    async def fake_get_session_record(session_id: str):
        return record

    async def fake_update_session_record(session_id: str, **kwargs):
        return record.model_copy(update={"ended_at": kwargs.get("ended_at")})

    async def failing_publish(**kwargs):
        raise ConnectionError("redis down")

    monkeypatch.setattr(sessions_api, "get_session_record", fake_get_session_record)
    monkeypatch.setattr(sessions_api, "update_session_record", fake_update_session_record)
    monkeypatch.setattr(sessions_api, "publish_chunk_added", failing_publish)
    monkeypatch.setattr(sessions_api, "get_builder_service", lambda: builder)

    response = await sessions_api.end_session(session_id="s1")

    assert response.ended_at is not None, "endpoint must succeed despite flush failure"
    assert builder.reset_calls == ["s1"]


# ---------------------------------------------------------------------------
# T6.4 — fake mode broadcasts GardenerCycleEvent even on failure
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fake_mode_broadcasts_cycle_event_on_failure(monkeypatch):
    """A partial failure mid-cycle must still emit the cycle event so the
    UI counter reflects reality."""
    sse = FakeSSEManager()
    monkeypatch.setattr(scheduler_module, "sse_manager", sse)

    async def failing_list_nodes(session_id: str, *, status=None, flower_id=None):
        raise RuntimeError("neo4j exploded")

    async def empty_list(session_id: str, **kwargs):
        return []

    monkeypatch.setattr(scheduler_module, "list_nodes", failing_list_nodes)
    monkeypatch.setattr(scheduler_module, "list_relationships", empty_list)
    monkeypatch.setattr(scheduler_module, "list_flowers", empty_list)

    scheduler = GardenerScheduler()
    with pytest.raises(RuntimeError, match="neo4j exploded"):
        await scheduler._run_gardener_fake("session-1")

    cycle_events = sse.events_of(GardenerCycleEvent)
    assert len(cycle_events) == 1, "cycle event must be broadcast despite the failure"
    assert sse.events[0][0] == "session-1"

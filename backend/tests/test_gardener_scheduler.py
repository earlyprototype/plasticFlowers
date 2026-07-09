"""Gardener scheduler tests (T6): metrics, event coalescing, session-end
flush, and fake-mode cycle-event resilience.

- Completion metrics must count the real NodeAction literals
  ("confirm"/"prune"/"merge"), not the never-emitted "solidify"/"remove".
- Chunk events are ACKed immediately and COALESCED per session: rapid events
  produce exactly one scheduled run (plus at most one follow-up if events
  arrive mid-run), and one session's debounce window never blocks another's.
- Ending a session with unprocessed chunks/ghosts must publish a Gardener
  trigger (sessions with < ratio chunks otherwise never get a pass); the
  scheduler drops the session's state after the flush sentinel is handled.
- Fake mode must broadcast GardenerCycleEvent even when the cycle fails.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pytest

from app.agents.gardener import NodeAction
from app.api import chunks as chunks_api
from app.api import sessions as sessions_api
from app.models import GardenerCycleEvent, SessionSummary
from app.services import scheduler as scheduler_module
from app.services.redis_streams import SESSION_END_FLUSH_CHUNK_ID
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
# T6.2 — events are ACKed immediately and coalesced, never head-of-line block
# ---------------------------------------------------------------------------


def _wire_fake_run(monkeypatch, scheduler: GardenerScheduler, runs: list[str], acks: list[str]):
    async def fake_run(session_id: str) -> None:
        runs.append(session_id)

    async def fake_ack(stream: str, group: str, message_id: str) -> None:
        acks.append(message_id)

    monkeypatch.setattr(scheduler_module, "is_fake_llm_enabled", lambda: True)
    monkeypatch.setattr(scheduler, "_run_gardener_fake", fake_run)
    monkeypatch.setattr(scheduler_module, "ack_event", fake_ack)


@pytest.mark.asyncio
async def test_rapid_events_coalesce_into_exactly_one_run(monkeypatch):
    """3 rapid events inside the debounce window -> ACKed immediately, exactly
    ONE scheduled Gardener run (previously each queued event became its own
    run and the consumer slept between them)."""
    scheduler = GardenerScheduler()
    scheduler._debounce_seconds = 0.1

    runs: list[str] = []
    acks: list[str] = []
    _wire_fake_run(monkeypatch, scheduler, runs, acks)

    loop = asyncio.get_event_loop()
    scheduler._last_run["s1"] = loop.time()  # window open: events must coalesce

    await scheduler._handle_event("1-0", {"session_id": "s1", "chunk_id": "c1"})
    await scheduler._handle_event("2-0", {"session_id": "s1", "chunk_id": "c2"})
    await scheduler._handle_event("3-0", {"session_id": "s1", "chunk_id": "c3"})

    assert acks == ["1-0", "2-0", "3-0"], "events must be ACKed immediately"
    assert runs == [], "no run inside the window - _handle_event never sleeps"
    assert set(scheduler._pending_tasks) == {"s1"}, "exactly one scheduled run"

    task = scheduler._pending_tasks["s1"]
    await task

    assert runs == ["s1"], "3 rapid events coalesce into exactly one run"
    assert scheduler._pending_tasks == {}, "no follow-up: nothing arrived mid-run"


@pytest.mark.asyncio
async def test_event_during_active_run_schedules_exactly_one_followup(monkeypatch):
    """Events arriving while a run is EXECUTING request exactly ONE follow-up
    run (not one run per event)."""
    scheduler = GardenerScheduler()
    scheduler._debounce_seconds = 0.0

    runs: list[str] = []
    run_started = asyncio.Event()
    release_run = asyncio.Event()

    async def fake_run(session_id: str) -> None:
        runs.append(session_id)
        if len(runs) == 1:
            run_started.set()
            await release_run.wait()

    async def fake_ack(stream: str, group: str, message_id: str) -> None:
        pass

    monkeypatch.setattr(scheduler_module, "is_fake_llm_enabled", lambda: True)
    monkeypatch.setattr(scheduler, "_run_gardener_fake", fake_run)
    monkeypatch.setattr(scheduler_module, "ack_event", fake_ack)

    await scheduler._handle_event("1-0", {"session_id": "s1", "chunk_id": "c1"})
    first_task = scheduler._pending_tasks["s1"]
    await run_started.wait()

    # Two events arrive mid-run -> exactly one follow-up requested.
    await scheduler._handle_event("2-0", {"session_id": "s1", "chunk_id": "c2"})
    await scheduler._handle_event("3-0", {"session_id": "s1", "chunk_id": "c3"})
    assert scheduler._rerun_requested == {"s1"}

    release_run.set()
    await first_task

    # The zero-delay follow-up may already have completed while awaiting the
    # first task; wait until all scheduling activity settles either way.
    for _ in range(100):
        follow_up = scheduler._pending_tasks.get("s1")
        if follow_up is not None:
            await follow_up
        if not scheduler._pending_tasks and not scheduler._running:
            break
        await asyncio.sleep(0.01)

    assert runs == ["s1", "s1"], "mid-run events coalesce into exactly one follow-up"
    assert scheduler._rerun_requested == set()


@pytest.mark.asyncio
async def test_session_b_runs_while_session_a_window_pends(monkeypatch):
    """Session A's debounce window must not head-of-line block session B —
    previously the single consumer slept out A's window before touching B."""
    scheduler = GardenerScheduler()
    scheduler._debounce_seconds = 5.0  # deliberately long window for A

    runs: list[str] = []
    acks: list[str] = []
    _wire_fake_run(monkeypatch, scheduler, runs, acks)

    loop = asyncio.get_event_loop()
    scheduler._last_run["session-a"] = loop.time()  # A is inside its window

    await scheduler._handle_event("1-0", {"session_id": "session-a", "chunk_id": "c1"})
    assert "session-a" in scheduler._pending_tasks, "A's run is scheduled, not blocking"

    # B has never run -> processed immediately while A's window still pends.
    await scheduler._handle_event("2-0", {"session_id": "session-b", "chunk_id": "c2"})
    task_b = scheduler._pending_tasks.get("session-b")
    assert task_b is not None
    await task_b

    assert runs == ["session-b"], "B ran while A's debounce window was pending"
    assert "session-a" in scheduler._pending_tasks, "A is still waiting for its window"
    assert acks == ["1-0", "2-0"], "both sessions' events ACKed immediately"

    # Cleanup: cancel A's still-pending debounce task.
    scheduler._pending_tasks["session-a"].cancel()
    await asyncio.gather(scheduler._pending_tasks["session-a"], return_exceptions=True)


@pytest.mark.asyncio
async def test_flush_sentinel_drops_scheduling_state_after_run(monkeypatch):
    """A session-end flush sentinel triggers a final run, after which the
    scheduler drops ALL of the session's scheduling state — previously
    _last_run was repopulated by the flush run and leaked forever."""
    scheduler = GardenerScheduler()
    scheduler._debounce_seconds = 0.0

    runs: list[str] = []
    acks: list[str] = []
    _wire_fake_run(monkeypatch, scheduler, runs, acks)

    await scheduler._handle_event(
        "1-0", {"session_id": "s1", "chunk_id": SESSION_END_FLUSH_CHUNK_ID}
    )
    assert acks == ["1-0"]
    task = scheduler._pending_tasks["s1"]
    await task

    assert runs == ["s1"], "the flush sentinel still triggers a final run"
    assert "s1" not in scheduler._last_run, "_last_run must not leak after session end"
    assert scheduler._pending_tasks == {}
    assert scheduler._flush_requested == set()
    assert scheduler._rerun_requested == set()


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
    assert published[0]["chunk_id"] == SESSION_END_FLUSH_CHUNK_ID, (
        "flush must carry the sentinel so the scheduler drops session state"
    )
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


@pytest.mark.asyncio
async def test_session_end_drains_inflight_builder_tasks_before_flush_check(monkeypatch):
    """Chunks accepted moments before session end may still be processing in
    detached tasks: end_session must drain them BEFORE the flush check, so the
    builder-count/ghost inspection observes their results."""
    published: list[dict] = []
    builder = FakeBuilderService(pending=0)
    _patch_session_endpoint(monkeypatch, builder=builder, published=published, ghosts=[])

    async def slow_builder_work() -> None:
        await asyncio.sleep(0.1)
        # Result of the in-flight chunk becomes visible only once it completes.
        builder._pending = 2

    task = asyncio.create_task(slow_builder_work())
    monkeypatch.setitem(chunks_api._active_tasks, "s1", {task})

    response = await sessions_api.end_session(session_id="s1")

    assert task.done(), "end_session must wait for the in-flight builder task"
    assert response.ended_at is not None
    assert len(published) == 1, "flush must observe the drained builder state"
    assert published[0]["session_id"] == "s1"


@pytest.mark.asyncio
async def test_session_end_without_flush_clears_scheduler_activity(monkeypatch):
    """When no flush event is published there is no sentinel for the scheduler
    to clean up after, so end_session itself must drop the session's Gardener
    scheduling state."""
    published: list[dict] = []
    builder = FakeBuilderService(pending=0)
    _patch_session_endpoint(monkeypatch, builder=builder, published=published, ghosts=[])

    cleared: list[str] = []
    fake_scheduler = type(
        "FakeScheduler", (), {"clear_activity": lambda self, sid: cleared.append(sid)}
    )()
    monkeypatch.setattr(sessions_api, "gardener_scheduler", fake_scheduler)

    await sessions_api.end_session(session_id="s1")

    assert published == []
    assert cleared == ["s1"], "no flush -> endpoint clears scheduler state itself"


@pytest.mark.asyncio
async def test_session_end_with_flush_defers_cleanup_to_scheduler(monkeypatch):
    """When the flush IS published, cleanup happens in the scheduler after the
    sentinel run — clearing it in the endpoint would race the flush event
    (the run would repopulate _last_run and leak it)."""
    published: list[dict] = []
    builder = FakeBuilderService(pending=2)
    _patch_session_endpoint(monkeypatch, builder=builder, published=published)

    cleared: list[str] = []
    fake_scheduler = type(
        "FakeScheduler", (), {"clear_activity": lambda self, sid: cleared.append(sid)}
    )()
    monkeypatch.setattr(sessions_api, "gardener_scheduler", fake_scheduler)

    await sessions_api.end_session(session_id="s1")

    assert len(published) == 1
    assert cleared == [], "cleanup is deferred to the scheduler's sentinel handling"


@pytest.mark.asyncio
async def test_drain_session_tasks_times_out_but_does_not_raise():
    """A stuck builder task must not wedge end_session: drain returns False
    after the timeout instead of raising."""
    release = asyncio.Event()

    async def stuck() -> None:
        await release.wait()

    task = asyncio.create_task(stuck())
    chunks_api._active_tasks["stuck-session"].add(task)
    try:
        drained = await chunks_api.drain_session_tasks("stuck-session", timeout=0.05)
        assert drained is False
    finally:
        release.set()
        await task
        chunks_api._active_tasks.pop("stuck-session", None)


@pytest.mark.asyncio
async def test_drain_session_tasks_no_tasks_returns_immediately():
    assert await chunks_api.drain_session_tasks("unknown-session", timeout=0.05) is True


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

"""Flower lifecycle tests (T3): create/update/dissolve through the scheduler.

Locks the Flower `member_ids` contract end-to-end in the backend:
- creation produces a Flower with non-empty member_ids and a truthful edge_count
- update mutates member_ids (and refreshes edge_count)
- dissolve detaches every member
- FlowerAction(flower_id=None) validates (None = create-new, fake-mode path)
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

import pytest

from app.agents.gardener import FlowerAction
from app.models import (
    Flower,
    FlowerCreatedEvent,
    FlowerDissolvedEvent,
    FlowerUpdatedEvent,
    Node,
    NodeStatus,
    Relationship,
    RelationshipCategory,
    RelationshipSource,
)
from app.services import scheduler as scheduler_module
from app.services.scheduler import GardenerScheduler, _count_internal_edges


def _make_node(node_id: str, label: str | None = None, offset_s: int = 0) -> Node:
    """Helper to create a solid Node (mirrors test_builder_service helpers)."""
    return Node(
        id=node_id,
        label=label or node_id.replace("-", " ").title(),
        confidence=0.9,
        mentions=2,
        timestamps=[1.0],
        inferred_type="concept",
        flower_id=None,
        embedding=None,
        created_at=datetime.now(timezone.utc) + timedelta(seconds=offset_s),
        status=NodeStatus.SOLID,
    )


def _make_rel(rel_id: str, source_id: str, target_id: str) -> Relationship:
    return Relationship(
        id=rel_id,
        source_id=source_id,
        target_id=target_id,
        category=RelationshipCategory.ASSOCIATIVE,
        description="related to",
        confidence=0.8,
        evidence="test evidence",
        source=RelationshipSource.GARDENER,
        created_at=datetime.now(timezone.utc),
    )


def _make_flower(flower_id: str, member_ids: list[str], stem: str) -> Flower:
    return Flower(
        id=flower_id,
        label="Existing Flower",
        stem_node_id=stem,
        edge_count=2,
        member_ids=member_ids,
        created_at=datetime.now(timezone.utc),
    )


class FakeSSEManager:
    """Records broadcast events (pattern from existing service tests)."""

    def __init__(self) -> None:
        self.events: list[tuple[str, object]] = []

    async def broadcast(self, session_id: str, event: object) -> None:
        self.events.append((session_id, event))

    def events_of(self, event_type: type) -> list[object]:
        return [event for _, event in self.events if isinstance(event, event_type)]


class GraphRecorder:
    """Fakes the graph_db functions the flower paths call, recording calls."""

    def __init__(self, existing_flowers: list[Flower] | None = None) -> None:
        self.existing_flowers = list(existing_flowers or [])
        self.upserted: list[Flower] = []
        self.returned: list[Flower] = []
        self.deleted: list[str] = []
        self.memberships: list[tuple[str, str | None]] = []

    def patch(self, monkeypatch: pytest.MonkeyPatch, sse: FakeSSEManager) -> None:
        async def fake_list_flowers(session_id: str) -> list[Flower]:
            return list(self.existing_flowers)

        async def fake_upsert_flower(session_id: str, flower: Flower) -> Flower:
            # Mirror the real upsert_flower contract: membership is reconciled
            # against flower.member_ids and a NEW object is returned with
            # member_ids re-derived from the reconciled BELONGS_TO edges.
            self.upserted.append(flower)
            reconciled = flower.model_copy(deep=True)
            self.returned.append(reconciled)
            return reconciled

        async def fake_delete_flower(session_id: str, flower_id: str) -> None:
            self.deleted.append(flower_id)

        async def fake_set_node_flower(session_id: str, node_id: str, flower_id: str | None) -> None:
            self.memberships.append((node_id, flower_id))

        monkeypatch.setattr(scheduler_module, "list_flowers", fake_list_flowers)
        monkeypatch.setattr(scheduler_module, "upsert_flower", fake_upsert_flower)
        monkeypatch.setattr(scheduler_module, "delete_flower", fake_delete_flower)
        monkeypatch.setattr(scheduler_module, "set_node_flower", fake_set_node_flower)
        monkeypatch.setattr(scheduler_module, "sse_manager", sse)


@pytest.mark.asyncio
async def test_create_flower_populates_member_ids_and_edge_count(monkeypatch):
    """Creation must produce a Flower with non-empty member_ids and truthful edge_count."""
    nodes = [_make_node("node-a"), _make_node("node-b", offset_s=1), _make_node("node-c", offset_s=2)]
    relationships = [
        _make_rel("rel-1", "node-a", "node-b"),
        _make_rel("rel-2", "node-b", "node-c"),
        _make_rel("rel-3", "node-c", "node-zz"),  # external edge, must not count
    ]
    action = FlowerAction(
        action="create",
        flower_id=None,  # None = create-new
        label="Demo Flower",
        member_ids=["node-a", "node-b", "node-c", "node-missing"],  # unknown id filtered out
        stem_node_id="node-a",
    )

    sse = FakeSSEManager()
    recorder = GraphRecorder()
    recorder.patch(monkeypatch, sse)

    scheduler = GardenerScheduler()
    await scheduler._apply_flower_actions("session-1", [action], nodes, relationships)

    assert len(recorder.upserted) == 1
    flower = recorder.upserted[0]
    assert flower.member_ids == ["node-a", "node-b", "node-c"], "member_ids must be populated (unknown ids dropped)"
    assert flower.edge_count == 2, "edge_count must count only internal edges"
    assert flower.stem_node_id == "node-a"

    # Membership is reconciled inside upsert_flower — no per-node
    # set_node_flower calls remain on the create path.
    assert recorder.memberships == []

    created_events = sse.events_of(FlowerCreatedEvent)
    assert len(created_events) == 1
    assert created_events[0].payload is recorder.returned[0], (
        "broadcast must carry the flower RETURNED by upsert_flower (reconciled "
        "member_ids), not the pre-upsert input"
    )
    payload = created_events[0].model_dump()["payload"]
    assert payload["member_ids"] == ["node-a", "node-b", "node-c"], "SSE payload must carry member_ids"
    assert payload["edge_count"] == 2


@pytest.mark.asyncio
async def test_update_flower_mutates_member_ids(monkeypatch):
    """Update must overwrite member_ids on the existing Flower model."""
    nodes = [
        _make_node("node-a"),
        _make_node("node-b", offset_s=1),
        _make_node("node-c", offset_s=2),
        _make_node("node-d", offset_s=3),
    ]
    relationships = [
        _make_rel("rel-1", "node-a", "node-b"),
        _make_rel("rel-2", "node-b", "node-c"),
        _make_rel("rel-3", "node-c", "node-d"),
    ]
    existing = _make_flower("flower-1", ["node-a", "node-b", "node-c"], stem="node-a")
    action = FlowerAction(
        action="update",
        flower_id="flower-1",
        label="Updated Flower",
        member_ids=["node-a", "node-b", "node-c", "node-d"],
        stem_node_id="node-b",
    )

    sse = FakeSSEManager()
    recorder = GraphRecorder(existing_flowers=[existing])
    recorder.patch(monkeypatch, sse)

    scheduler = GardenerScheduler()
    await scheduler._apply_flower_actions("session-1", [action], nodes, relationships)

    assert len(recorder.upserted) == 1
    flower = recorder.upserted[0]
    assert flower.id == "flower-1"
    assert flower.member_ids == ["node-a", "node-b", "node-c", "node-d"], "update must mutate member_ids"
    assert flower.label == "Updated Flower"
    assert flower.stem_node_id == "node-b"
    assert flower.edge_count == 3, "edge_count must be refreshed on update"

    # Membership reconciliation happens inside upsert_flower now
    assert recorder.memberships == []

    updated_events = sse.events_of(FlowerUpdatedEvent)
    assert len(updated_events) == 1
    assert updated_events[0].payload is recorder.returned[0], (
        "broadcast must carry the reconciled flower returned by upsert_flower"
    )
    assert updated_events[0].model_dump()["payload"]["member_ids"] == [
        "node-a", "node-b", "node-c", "node-d",
    ]


@pytest.mark.asyncio
async def test_update_flower_shrinking_membership_detaches_dropped_member(monkeypatch):
    """Regression: an update that SHRINKS membership must hand the full
    authoritative (shrunk) list to upsert_flower, and the broadcast flower —
    whose member_ids are derived from the reconciled edges — must no longer
    contain the dropped node. Previously the update path only attached new
    members and never detached dropped ones."""
    nodes = [
        _make_node("node-a"),
        _make_node("node-b", offset_s=1),
        _make_node("node-c", offset_s=2),
        _make_node("node-d", offset_s=3),
    ]
    relationships = [
        _make_rel("rel-1", "node-a", "node-b"),
        _make_rel("rel-2", "node-b", "node-c"),
    ]
    existing = _make_flower(
        "flower-1", ["node-a", "node-b", "node-c", "node-d"], stem="node-a"
    )
    action = FlowerAction(
        action="update",
        flower_id="flower-1",
        label="Shrunk Flower",
        member_ids=["node-a", "node-b", "node-c"],  # node-d dropped
        stem_node_id="node-a",
    )

    sse = FakeSSEManager()
    recorder = GraphRecorder(existing_flowers=[existing])
    recorder.patch(monkeypatch, sse)

    scheduler = GardenerScheduler()
    await scheduler._apply_flower_actions("session-1", [action], nodes, relationships)

    assert len(recorder.upserted) == 1
    assert recorder.upserted[0].member_ids == ["node-a", "node-b", "node-c"], (
        "upsert_flower receives the authoritative (shrunk) member list, so it "
        "can detach node-d's BELONGS_TO edge in the same transaction"
    )
    assert recorder.memberships == [], "no per-node set_node_flower calls on update"

    updated_events = sse.events_of(FlowerUpdatedEvent)
    assert len(updated_events) == 1
    payload = updated_events[0].model_dump()["payload"]
    assert "node-d" not in payload["member_ids"], (
        "detached node must not appear in the derived member_ids"
    )
    assert payload["member_ids"] == ["node-a", "node-b", "node-c"]


@pytest.mark.asyncio
async def test_dissolve_flower_detaches_members(monkeypatch):
    """Dissolve must delete the flower and clear membership for surviving nodes."""
    nodes = [_make_node("node-a"), _make_node("node-b", offset_s=1)]  # node-c no longer exists
    existing = _make_flower("flower-1", ["node-a", "node-b", "node-c"], stem="node-a")
    action = FlowerAction(action="dissolve", flower_id="flower-1")

    sse = FakeSSEManager()
    recorder = GraphRecorder(existing_flowers=[existing])
    recorder.patch(monkeypatch, sse)

    scheduler = GardenerScheduler()
    await scheduler._apply_flower_actions("session-1", [action], nodes, [])

    assert recorder.deleted == ["flower-1"]
    # Surviving members detached (flower_id=None); vanished node-c skipped
    assert recorder.memberships == [("node-a", None), ("node-b", None)]

    dissolved_events = sse.events_of(FlowerDissolvedEvent)
    assert len(dissolved_events) == 1
    assert dissolved_events[0].model_dump()["payload"]["id"] == "flower-1"


@pytest.mark.asyncio
async def test_create_rejected_when_criteria_not_met(monkeypatch):
    """Fewer than 3 members or fewer than 2 internal edges must not create a flower."""
    nodes = [_make_node("node-a"), _make_node("node-b", offset_s=1), _make_node("node-c", offset_s=2)]
    relationships = [_make_rel("rel-1", "node-a", "node-b")]  # only 1 internal edge
    action = FlowerAction(
        action="create",
        label="Weak Flower",
        member_ids=["node-a", "node-b", "node-c"],
        stem_node_id="node-a",
    )

    sse = FakeSSEManager()
    recorder = GraphRecorder()
    recorder.patch(monkeypatch, sse)

    scheduler = GardenerScheduler()
    await scheduler._apply_flower_actions("session-1", [action], nodes, relationships)

    assert recorder.upserted == []
    assert recorder.memberships == []
    assert sse.events_of(FlowerCreatedEvent) == []


def test_flower_action_accepts_none_flower_id():
    """FlowerAction with flower_id=None must validate (None = create-new)."""
    action = FlowerAction(
        action="create",
        flower_id=None,
        label="Demo Flower",
        member_ids=["node-a", "node-b", "node-c"],
        stem_node_id="node-a",
    )
    assert action.flower_id is None
    # Empty string (legacy "else empty" convention) still validates too
    legacy = FlowerAction(action="create", flower_id="", label="X", member_ids=[], stem_node_id="")
    assert legacy.flower_id == ""


def test_fake_mode_synthesises_valid_flower_actions():
    """The fake-mode path builds FlowerAction(flower_id=None) for create, id for update."""
    scheduler = GardenerScheduler()
    nodes = [_make_node("node-a"), _make_node("node-b", offset_s=1), _make_node("node-c", offset_s=2)]
    relationships = [
        _make_rel("rel-1", "node-a", "node-b"),
        _make_rel("rel-2", "node-b", "node-c"),
    ]

    # No existing flowers -> create with flower_id=None
    actions = scheduler._synthesise_fake_flower_actions(nodes, relationships, [])
    assert len(actions) == 1
    assert actions[0].action == "create"
    assert actions[0].flower_id is None
    assert actions[0].member_ids == ["node-a", "node-b", "node-c"]
    assert actions[0].stem_node_id == "node-a"

    # Existing flower -> update targeting its id
    existing = _make_flower("flower-1", ["node-a", "node-b", "node-c"], stem="node-a")
    actions = scheduler._synthesise_fake_flower_actions(nodes, relationships, [existing])
    assert len(actions) == 1
    assert actions[0].action == "update"
    assert actions[0].flower_id == "flower-1"


def test_count_internal_edges_ignores_external_endpoints():
    relationships = [
        _make_rel("rel-1", "a", "b"),
        _make_rel("rel-2", "b", "external"),
        _make_rel("rel-3", "external", "a"),
    ]
    assert _count_internal_edges(["a", "b"], relationships) == 1

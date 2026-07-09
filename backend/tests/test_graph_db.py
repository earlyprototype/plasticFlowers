from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.models import Node, NodeStatus, Relationship, RelationshipCategory, RelationshipSource
from app.services import graph_db
from .fakes import FakeNeo4jDriver


def _sample_node(created_at: datetime | None = None) -> Node:
    return Node(
        id="node-1",
        label="Transformer attention",
        confidence=0.92,
        mentions=1,
        timestamps=[1.2],
        inferred_type="concept",
        flower_id=None,
        embedding=None,
        created_at=created_at or datetime.now(timezone.utc),
        status=NodeStatus.GHOST,
    )


@pytest.mark.asyncio
async def test_create_node_returns_new_node(monkeypatch):
    node = _sample_node()
    stored_doc = node.model_dump()
    stored_doc["session_id"] = "session-1"
    driver = FakeNeo4jDriver([[{"node": stored_doc}]])

    async def fake_get_driver():
        return driver

    monkeypatch.setattr(graph_db, "get_driver", fake_get_driver)

    created = await graph_db.create_node("session-1", node)

    assert created == node
    assert "CREATE (n:Node)" in driver.calls[0]["query"]


@pytest.mark.asyncio
async def test_list_nodes_applies_filters(monkeypatch):
    node = _sample_node()
    stored_doc = node.model_dump()
    stored_doc["session_id"] = "session-1"
    driver = FakeNeo4jDriver([[{"node": stored_doc, "flower_id": "flower-1"}]])

    async def fake_get_driver():
        return driver

    monkeypatch.setattr(graph_db, "get_driver", fake_get_driver)

    nodes = await graph_db.list_nodes("session-1", status=NodeStatus.GHOST, flower_id="flower-1")

    assert len(nodes) == 1
    assert nodes[0].label == node.label
    assert nodes[0].flower_id == "flower-1"
    recorded = driver.calls[-1]
    assert "n.status = $status" in recorded["query"]
    assert "BELONGS_TO" in recorded["query"]
    assert recorded["params"]["status"] == NodeStatus.GHOST.value
    assert recorded["params"]["flower_id"] == "flower-1"


@pytest.mark.asyncio
async def test_create_relationship_returns_relationship(monkeypatch):
    rel = Relationship(
        id="rel-1",
        source_id="node-a",
        target_id="node-b",
        category=RelationshipCategory.CAUSAL,
        description="enables training",
        confidence=0.81,
        evidence="speaker said training enabled",
        source=RelationshipSource.BUILDER,
        created_at=datetime.now(timezone.utc),
    )
    stored = rel.model_dump()
    stored["session_id"] = "session-1"
    driver = FakeNeo4jDriver([[{"relationship": stored}]])

    async def fake_get_driver():
        return driver

    monkeypatch.setattr(graph_db, "get_driver", fake_get_driver)

    created = await graph_db.create_relationship("session-1", rel)

    assert created == rel
    # The query is now a MERGE, not just CREATE
    assert "MERGE (source)-[rel:RELATIONSHIP {id: $relationship_id}]->(target)" in driver.calls[0]["query"]


@pytest.mark.asyncio
async def test_record_node_mention_appends_timestamp(monkeypatch):
    node = _sample_node()
    stored_doc = node.model_dump()
    stored_doc["session_id"] = "session-1"
    stored_doc["mentions"] = 2
    stored_doc["timestamps"] = node.timestamps + [42.0]
    driver = FakeNeo4jDriver([[{"node": stored_doc}]])

    async def fake_get_driver():
        return driver

    monkeypatch.setattr(graph_db, "get_driver", fake_get_driver)

    updated = await graph_db.record_node_mention("session-1", node.id, 42.0)

    assert updated.mentions == 2
    assert updated.timestamps[-1] == pytest.approx(42.0)
    params = driver.calls[-1]["params"]
    assert params["new_timestamp"] == [42.0]


@pytest.mark.asyncio
async def test_set_node_flower_creates_relationship(monkeypatch):
    driver = FakeNeo4jDriver([[]])

    async def fake_get_driver():
        return driver

    monkeypatch.setattr(graph_db, "get_driver", fake_get_driver)

    await graph_db.set_node_flower("session-1", "node-1", "flower-1")

    recorded = driver.calls[-1]
    assert "BELONGS_TO" in recorded["query"]
    assert "CREATE (n)-[:BELONGS_TO]->(f)" in recorded["query"]
    assert recorded["params"]["node_id"] == "node-1"
    assert recorded["params"]["flower_id"] == "flower-1"
    assert recorded["params"]["session_id"] == "session-1"


@pytest.mark.asyncio
async def test_set_node_flower_removes_relationship(monkeypatch):
    driver = FakeNeo4jDriver([[]])

    async def fake_get_driver():
        return driver

    monkeypatch.setattr(graph_db, "get_driver", fake_get_driver)

    await graph_db.set_node_flower("session-1", "node-1", None)

    recorded = driver.calls[-1]
    assert "BELONGS_TO" in recorded["query"]
    assert "DELETE r" in recorded["query"]
    assert recorded["params"]["node_id"] == "node-1"
    assert recorded["params"]["session_id"] == "session-1"

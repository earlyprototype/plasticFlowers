from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.models import Flower, Node, NodeStatus, Relationship, RelationshipCategory, RelationshipSource
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
    query = recorded["query"]
    assert "n.status = $status" in query
    assert "BELONGS_TO" in query
    assert recorded["params"]["status"] == NodeStatus.GHOST.value
    assert recorded["params"]["flower_id"] == "flower-1"
    # The generated Cypher must be valid: the status filter needs a WHERE
    # clause, and any AND must come after it (a bare AND after MATCH is a
    # Cypher syntax error — the fake driver never parses queries, so assert
    # on the captured query string).
    assert "WHERE" in query, "status filter requires a WHERE clause"
    before_where = query.split("WHERE", 1)[0]
    assert " AND " not in before_where, "AND with no preceding WHERE is invalid Cypher"
    if " AND " in query:
        assert query.index("WHERE") < query.index(" AND ")


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
async def test_delete_session_record_covers_all_session_data(monkeypatch):
    """delete_session_record must clean up the session-scoped side-car nodes
    (Reference, SessionVocabulary, ProofreadCheckpoint, SessionContext) and
    orphaned Source nodes — these were previously left behind."""
    # First response answers the cited-urls snapshot; the rest are deletes.
    driver = FakeNeo4jDriver(
        [[{"urls": ["https://a.example", "https://b.example"]}]] + [[] for _ in range(20)]
    )

    async def fake_get_driver():
        return driver

    monkeypatch.setattr(graph_db, "get_driver", fake_get_driver)

    await graph_db.delete_session_record("session-1")

    all_queries = " || ".join(call["query"] for call in driver.calls)

    # Original coverage
    assert "RELATIONSHIP {session_id: $session_id}" in all_queries
    assert "(n:Node {session_id: $session_id})" in all_queries
    assert "Flower {session_id: $session_id}" in all_queries
    assert "TranscriptChunk {session_id: $session_id}" in all_queries
    assert "Session {id: $session_id}" in all_queries

    # Previously-orphaned labels now covered
    assert "Reference {session_id: $session_id}" in all_queries
    assert "SessionVocabulary {session_id: $session_id}" in all_queries
    assert "ProofreadCheckpoint {session_id: $session_id}" in all_queries
    assert "SessionContext {session_id: $session_id}" in all_queries

    # The session's cited Source urls are snapshotted BEFORE its References
    # are deleted, and the orphan sweep is anchored to that url set rather
    # than scanning the whole Source label.
    collect_query = driver.calls[0]["query"]
    assert "Reference {session_id: $session_id}" in collect_query
    assert "CITED_BY" in collect_query
    assert "collect(DISTINCT src.url)" in collect_query

    orphan_calls = [c for c in driver.calls if "DETACH DELETE src" in c["query"]]
    assert len(orphan_calls) == 1
    assert "src.url IN $cited_urls" in orphan_calls[0]["query"]
    assert "NOT (src)<-[:CITED_BY]-()" in orphan_calls[0]["query"]
    assert orphan_calls[0]["params"]["cited_urls"] == [
        "https://a.example",
        "https://b.example",
    ]

    # Every query ran with the session id bound
    for call in driver.calls:
        assert call["params"]["session_id"] == "session-1"


@pytest.mark.asyncio
async def test_delete_session_record_skips_orphan_sweep_without_citations(monkeypatch):
    """No cited Sources -> nothing can be orphaned -> no Source scan at all."""
    driver = FakeNeo4jDriver([[{"urls": []}]] + [[] for _ in range(20)])

    async def fake_get_driver():
        return driver

    monkeypatch.setattr(graph_db, "get_driver", fake_get_driver)

    await graph_db.delete_session_record("session-1")

    assert not any("DETACH DELETE src" in call["query"] for call in driver.calls)
    # The session delete itself still ran
    assert any("Session {id: $session_id}" in call["query"] for call in driver.calls)


def _sample_flower(member_ids: list[str]) -> Flower:
    return Flower(
        id="flower-1",
        label="Test Flower",
        stem_node_id=member_ids[0] if member_ids else "node-a",
        edge_count=2,
        member_ids=member_ids,
        created_at=datetime.now(timezone.utc),
    )


def _stored_flower_record(member_ids: list[str]) -> dict:
    flower = _sample_flower(member_ids)
    props = flower.model_dump()
    props.pop("member_ids")  # membership is derived from BELONGS_TO edges
    props["session_id"] = "session-1"
    return {"flower": props, "member_ids": member_ids}


@pytest.mark.asyncio
async def test_upsert_flower_reconciles_membership_in_one_transaction(monkeypatch):
    """upsert_flower must MERGE the flower, detach BELONGS_TO edges of nodes
    not in the authoritative list, attach edges for listed nodes, and return
    the flower with member_ids derived from the reconciled edges — all inside
    a single transaction (one execute_write)."""
    authoritative = ["node-a", "node-b", "node-c"]
    driver = FakeNeo4jDriver([[], [], [], [_stored_flower_record(authoritative)]])

    async def fake_get_driver():
        return driver

    monkeypatch.setattr(graph_db, "get_driver", fake_get_driver)

    stored = await graph_db.upsert_flower("session-1", _sample_flower(authoritative))

    assert stored.member_ids == authoritative, "member_ids derived AFTER reconciliation"

    queries = [call["query"] for call in driver.calls]
    assert len(queries) == 4, "upsert, detach, attach, return — one transaction"
    assert "MERGE (f:Flower {id: $flower_id, session_id: $session_id})" in queries[0]
    # Detach: members NOT in the authoritative list lose their edge
    assert "NOT old.id IN $member_ids" in queries[1]
    assert "DELETE stale" in queries[1]
    # Attach: listed nodes gain the edge (session-scoped on both ends)
    assert "UNWIND $member_ids AS member_id" in queries[2]
    assert "MATCH (n:Node {id: member_id, session_id: $session_id})" in queries[2]
    assert "MERGE (n)-[:BELONGS_TO]->(f)" in queries[2]
    # Return: member_ids re-derived from the edges
    assert "collect(n.id) AS member_ids" in queries[3]

    for call in driver.calls:
        assert call["params"]["member_ids"] == authoritative
        assert call["params"]["session_id"] == "session-1"


@pytest.mark.asyncio
async def test_upsert_flower_shrinking_membership_drops_detached_member(monkeypatch):
    """Regression (scheduler update path): shrinking the member list must
    detach the dropped node — the returned member_ids no longer contain it."""
    shrunk = ["node-a", "node-b"]  # node-c was dropped by the update
    driver = FakeNeo4jDriver([[], [], [], [_stored_flower_record(shrunk)]])

    async def fake_get_driver():
        return driver

    monkeypatch.setattr(graph_db, "get_driver", fake_get_driver)

    stored = await graph_db.upsert_flower("session-1", _sample_flower(shrunk))

    assert "node-c" not in stored.member_ids
    assert stored.member_ids == shrunk

    detach_call = driver.calls[1]
    assert "NOT old.id IN $member_ids" in detach_call["query"]
    assert detach_call["params"]["member_ids"] == shrunk, (
        "node-c is outside the authoritative list, so its edge is deleted"
    )


@pytest.mark.asyncio
async def test_upsert_flower_empty_member_list_skips_attach(monkeypatch):
    """Empty member list: detach everything, never run the UNWIND attach
    (UNWIND [] would silently kill the rest of a combined query)."""
    driver = FakeNeo4jDriver([[], [], [_stored_flower_record([])]])

    async def fake_get_driver():
        return driver

    monkeypatch.setattr(graph_db, "get_driver", fake_get_driver)

    stored = await graph_db.upsert_flower("session-1", _sample_flower([]))

    assert stored.member_ids == []
    queries = [call["query"] for call in driver.calls]
    assert len(queries) == 3, "attach step skipped for an empty member list"
    assert not any("UNWIND" in q for q in queries)


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

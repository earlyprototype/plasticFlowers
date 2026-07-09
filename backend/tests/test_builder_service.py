"""Integration tests for BuilderService (similarity check feature)."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models import (
    Node,
    NodeStatus,
    Relationship,
    RelationshipAddedEvent,
    RelationshipCategory,
    RelationshipSource,
    TranscriptChunk,
)
from app.services.builder_service import BuilderService
from app.agents import BuilderAgentResult, UnresolvedRelationship


def _make_chunk(text: str = "Test chunk", chunk_id: str = "chunk-1") -> TranscriptChunk:
    """Helper to create a TranscriptChunk."""
    return TranscriptChunk(
        id=chunk_id,
        session_id="session-1",
        text=text,
        start_time=1.0,
        end_time=2.0,
        original_text=text,
        sequence=0,
    )


def _make_node(label: str, node_id: str = "node-1") -> Node:
    """Helper to create a Node."""
    return Node(
        id=node_id,
        label=label,
        confidence=0.85,
        mentions=1,
        timestamps=[1.0],
        inferred_type="concept",
        flower_id=None,
        embedding=[0.1, 0.2, 0.3],
        created_at=datetime.now(timezone.utc),
        status=NodeStatus.GHOST,
    )


@pytest.mark.asyncio
async def test_similarity_check_disabled_creates_all_ghost_nodes(monkeypatch):
    """
    Test that when similarity_check_enabled=False, all extracted nodes
    are created as new GHOST nodes (legacy behavior, no similarity checking).
    
    This is the proper integration test for the rollback flag (ADR-011).
    """
    from app.config import Settings
    from app.services import builder_service
    
    # Mock config with similarity check DISABLED
    disabled_settings = Settings(
        similarity_check_enabled=False,  # Key flag
        neo4j_uri="bolt://localhost:7687",
        neo4j_username="neo4j",
        neo4j_password="test",
        redis_url="redis://localhost:6379",
    )
    monkeypatch.setattr(builder_service, "get_settings", lambda: disabled_settings)
    
    # Mock BuilderAgent to return nodes
    agent_result = BuilderAgentResult(
        nodes=[
            _make_node("Machine Learning", "node-ml"),
            _make_node("Python", "node-py"),
        ],
        relationships=[],
        raw_response=MagicMock(),
        llm_duration_ms=100.0,
    )
    
    mock_agent = AsyncMock()
    mock_agent.build = AsyncMock(return_value=agent_result)
    
    # Mock embeddings
    async def fake_embed(label: str, language: str = "en"):
        return [0.1, 0.2, 0.3]
    
    monkeypatch.setattr(builder_service, "generate_embedding", fake_embed)
    
    # Mock graph DB operations
    created_nodes = []
    async def fake_create_node(session_id: str, node: Node) -> Node:
        created_nodes.append(node)
        return node
    
    async def fake_list_nodes(*args, **kwargs):
        return []
    
    async def fake_list_relationships(*args, **kwargs):
        return []

    monkeypatch.setattr(builder_service, "create_node", fake_create_node)
    monkeypatch.setattr(builder_service, "list_nodes", fake_list_nodes)
    monkeypatch.setattr(builder_service, "list_relationships", fake_list_relationships)
    
    # Mock SSE manager
    mock_sse = AsyncMock()
    monkeypatch.setattr(builder_service, "sse_manager", mock_sse)
    
    # Mock Redis publishing
    async def fake_publish(*args, **kwargs):
        pass
    monkeypatch.setattr(builder_service, "publish_chunk_added", fake_publish)
    
    # CRITICAL: Mock the similarity check functions so they're never called
    similarity_called = {"count": 0}
    
    async def fake_query_best_match(*args, **kwargs):
        similarity_called["count"] += 1
        raise AssertionError("Similarity check should not be called when disabled!")
    
    async def fake_types_compatible(*args, **kwargs):
        similarity_called["count"] += 1
        raise AssertionError("Type compatibility check should not be called when disabled!")
    
    async def fake_record_mention(*args, **kwargs):
        raise AssertionError("record_node_mention should not be called when disabled!")
    
    async def fake_get_node(*args, **kwargs):
        raise AssertionError("get_node should not be called when disabled!")
    
    monkeypatch.setattr(builder_service, "_query_best_match", fake_query_best_match)
    monkeypatch.setattr(builder_service, "types_compatible", fake_types_compatible)
    monkeypatch.setattr(builder_service, "record_node_mention", fake_record_mention)
    monkeypatch.setattr(builder_service, "get_node", fake_get_node)
    
    # Create service and process chunk
    service = BuilderService()
    service._agent = mock_agent
    
    chunk = _make_chunk("Machine Learning and Python are great")
    result = await service.process_chunk("session-1", chunk)
    
    # Verify: All nodes created as new GHOST nodes (no similarity checking)
    assert len(created_nodes) == 2, "Both nodes should be created"
    assert created_nodes[0].label == "Machine Learning"
    assert created_nodes[1].label == "Python"
    assert all(n.status == NodeStatus.GHOST for n in created_nodes)
    
    # Verify: No similarity checks were performed
    assert similarity_called["count"] == 0, "Similarity checks should be bypassed when flag is disabled"
    
    # Verify: Result contains both nodes
    assert len(result.nodes) == 2, "Result should contain both created nodes"


@pytest.mark.asyncio
async def test_similarity_check_enabled_performs_deduplication(monkeypatch):
    """
    Test that when similarity_check_enabled=True, extracted nodes are
    checked against existing nodes and duplicates are matched (not created).
    """
    from app.config import Settings
    from app.services import builder_service
    
    # Mock config with similarity check ENABLED
    enabled_settings = Settings(
        similarity_check_enabled=True,  # Key flag
        neo4j_uri="bolt://localhost:7687",
        neo4j_username="neo4j",
        neo4j_password="test",
        redis_url="redis://localhost:6379",
        similarity_threshold=0.92,  # ADR-008
    )
    monkeypatch.setattr(builder_service, "get_settings", lambda: enabled_settings)
    
    # Mock BuilderAgent to return a node that will match existing
    agent_result = BuilderAgentResult(
        nodes=[
            _make_node("machine learning", "node-ml-new"),  # Will match existing
        ],
        relationships=[],
        raw_response=MagicMock(),
        llm_duration_ms=100.0,
    )
    
    mock_agent = AsyncMock()
    mock_agent.build = AsyncMock(return_value=agent_result)
    
    # Mock embeddings
    async def fake_embed(label: str, language: str = "en"):
        return [0.9, 0.1, 0.0]
    
    monkeypatch.setattr(builder_service, "generate_embedding", fake_embed)
    
    # Mock similarity check to return a match
    from app.services.similarity import _MatchCandidate
    
    async def fake_query_best_match(session_id: str, embedding, top_k: int):
        # Return high similarity match
        return _MatchCandidate(node_id="node-existing-ml", score=0.95)
    
    monkeypatch.setattr(builder_service, "_query_best_match", fake_query_best_match)
    
    # Mock get_node to return existing node
    existing_node = Node(
        id="node-existing-ml",
        label="Machine Learning",
        confidence=0.9,
        mentions=5,
        timestamps=[0.5, 1.0, 1.5, 2.0, 2.5],
        inferred_type="concept",
        flower_id=None,
        embedding=[0.9, 0.1, 0.0],
        created_at=datetime.now(timezone.utc),
        status=NodeStatus.SOLID,
    )
    
    async def fake_get_node(session_id: str, node_id: str) -> Node:
        if node_id == "node-existing-ml":
            return existing_node
        return None

    monkeypatch.setattr(builder_service, "get_node", fake_get_node)
    
    # Mock types_compatible to return True
    async def fake_types_compatible(type_a: str, type_b: str) -> bool:
        return True
    
    monkeypatch.setattr(builder_service, "types_compatible", fake_types_compatible)
    
    # Mock record_node_mention to return updated node
    updated_node = Node(
        id="node-existing-ml",
        label="Machine Learning",
        confidence=0.9,
        mentions=6,  # Incremented
        timestamps=[0.5, 1.0, 1.5, 2.0, 2.5, 1.0],  # New timestamp added
        inferred_type="concept",
        flower_id=None,
        embedding=[0.9, 0.1, 0.0],
        created_at=datetime.now(timezone.utc),
        status=NodeStatus.SOLID,
    )
    
    async def fake_record_mention(session_id: str, node_id: str, timestamp: float):
        assert node_id == "node-existing-ml"
        return updated_node
    
    monkeypatch.setattr(builder_service, "record_node_mention", fake_record_mention)
    
    # Track create_node calls (should NOT be called for matched node)
    created_nodes = []
    async def fake_create_node(session_id: str, node: Node) -> Node:
        created_nodes.append(node)
        return node
    
    monkeypatch.setattr(builder_service, "create_node", fake_create_node)
    
    # Mock other required functions
    async def fake_list_nodes(*args, **kwargs):
        return []
    
    async def fake_list_relationships(*args, **kwargs):
        return []

    monkeypatch.setattr(builder_service, "list_nodes", fake_list_nodes)
    monkeypatch.setattr(builder_service, "list_relationships", fake_list_relationships)
    
    # Mock SSE manager
    mock_sse = AsyncMock()
    monkeypatch.setattr(builder_service, "sse_manager", mock_sse)
    
    # Mock Redis publishing
    async def fake_publish(*args, **kwargs):
        pass
    monkeypatch.setattr(builder_service, "publish_chunk_added", fake_publish)
    
    # Create service and process chunk
    service = BuilderService()
    service._agent = mock_agent
    
    chunk = _make_chunk("machine learning is important")
    result = await service.process_chunk("session-1", chunk)
    
    # Verify: No new node was created (matched existing instead)
    assert len(created_nodes) == 0, "No new nodes should be created when match found"
    
    # Verify: Result contains the matched node
    assert len(result.nodes) == 1, "Result should contain the matched node"
    assert result.nodes[0].id == "node-existing-ml", "Should be the existing node"
    assert result.nodes[0].mentions == 6, "Mentions should be incremented"
    
    # Verify: SSE broadcast should include node_updated event (not node_added)
    # The mock_sse.broadcast would have been called with NodeUpdatedEvent
    assert mock_sse.broadcast.called


def _make_rel(rel_id: str, source_id: str, target_id: str) -> Relationship:
    return Relationship(
        id=rel_id,
        source_id=source_id,
        target_id=target_id,
        category=RelationshipCategory.ASSOCIATIVE,
        description="related to",
        confidence=0.8,
        evidence="test evidence",
        source=RelationshipSource.BUILDER,
        created_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_persist_relationships_skips_none_from_missing_nodes(monkeypatch):
    """create_relationship returns None when an endpoint node is missing;
    the None must be skipped (T7) — previously it was appended and later
    crashed RelationshipAddedEvent(payload=None), failing the whole chunk."""
    from app.services import builder_service

    rel_ok = _make_rel("rel-ok", "node-a", "node-b")
    rel_missing = _make_rel("rel-missing", "node-a", "node-ghosted")

    async def fake_create_relationship(session_id: str, rel: Relationship):
        if rel.id == "rel-missing":
            return None  # endpoint node missing
        return rel

    monkeypatch.setattr(builder_service, "create_relationship", fake_create_relationship)

    service = BuilderService()
    persisted = await service._persist_relationships("session-1", [rel_ok, rel_missing])

    assert persisted == [rel_ok], "None results must be skipped, not appended"

    # And broadcasting the persisted list must not construct a None payload.
    broadcasts = []

    class FakeSSE:
        async def broadcast(self, session_id: str, event):
            broadcasts.append(event)

    monkeypatch.setattr(builder_service, "sse_manager", FakeSSE())
    await service._broadcast_relationships("session-1", persisted)

    assert len(broadcasts) == 1
    assert isinstance(broadcasts[0], RelationshipAddedEvent)
    assert broadcasts[0].payload.id == "rel-ok"


@pytest.mark.asyncio
async def test_similarity_below_threshold_creates_new_node(monkeypatch):
    """A candidate below similarity_threshold must create a new GHOST node,
    never record a mention (covers the create branch of
    _check_similarity_and_persist; equivalent coverage previously lived in
    the removed similarity.run_similarity tests)."""
    from app.config import Settings
    from app.services import builder_service

    settings = Settings(
        similarity_check_enabled=True,
        similarity_threshold=0.92,
        neo4j_uri="bolt://localhost:7687",
        neo4j_username="neo4j",
        neo4j_password="test",
        redis_url="redis://localhost:6379",
    )
    monkeypatch.setattr(builder_service, "get_settings", lambda: settings)

    async def fake_embed(label: str, language: str = "en"):
        return [0.1, 0.2, 0.3]

    async def fake_query_best_match(session_id: str, embedding, top_k: int):
        from app.services.similarity import _MatchCandidate
        return _MatchCandidate(node_id="node-other", score=0.5)  # below 0.92

    async def fail_record_mention(*args, **kwargs):
        raise AssertionError("record_node_mention must not run below threshold")

    created_nodes: list[Node] = []

    async def fake_create_node(session_id: str, node: Node) -> Node:
        created_nodes.append(node)
        return node

    monkeypatch.setattr(builder_service, "generate_embedding", fake_embed)
    monkeypatch.setattr(builder_service, "_query_best_match", fake_query_best_match)
    monkeypatch.setattr(builder_service, "record_node_mention", fail_record_mention)
    monkeypatch.setattr(builder_service, "create_node", fake_create_node)

    service = BuilderService()
    node = _make_node("new concept", "node-new")
    results = await service._check_similarity_and_persist("session-1", [node], 1.0)

    assert len(results) == 1
    assert results[0].is_match is False
    assert created_nodes == [node], "below-threshold candidate must create a node"

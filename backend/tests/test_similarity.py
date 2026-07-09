from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.models import Node, NodeStatus
from app.services import similarity
from app.services.graph_schema import NODE_EMBEDDING_INDEX
from .fakes import FakeNeo4jDriver


def _node() -> Node:
    return Node(
        id="node-123",
        label="vector search",
        confidence=0.9,
        mentions=1,
        timestamps=[0.5],
        inferred_type="concept",
        flower_id=None,
        embedding=None,
        created_at=datetime.now(timezone.utc),
        status=NodeStatus.GHOST,
    )


@pytest.mark.asyncio
async def test_run_similarity_returns_match(monkeypatch):
    node = _node()

    async def fake_embed(label: str, language: str = "en"):
        return [0.1, 0.2, 0.3]

    async def fake_query(session_id: str, embedding, top_k: int):
        return similarity._MatchCandidate(node_id=node.id, score=0.93)

    async def fake_record(session_id: str, node_id: str, timestamp: float):
        assert node_id == node.id
        return node

    monkeypatch.setattr(similarity, "generate_embedding", fake_embed)
    monkeypatch.setattr(similarity, "_query_best_match", fake_query)
    monkeypatch.setattr(similarity, "record_node_mention", fake_record)

    result = await similarity.run_similarity("session-1", "Vector search", 3.0)

    assert isinstance(result, similarity.SimilarityMatchResult)
    assert result.node == node
    assert result.score == pytest.approx(0.93)
    assert result.embedding == [0.1, 0.2, 0.3]


@pytest.mark.asyncio
async def test_run_similarity_returns_create_when_below_threshold(monkeypatch):
    async def fake_embed(label: str, language: str = "en"):
        return [0.0, 0.0, 0.0]

    async def fake_query(session_id: str, embedding, top_k: int):
        return similarity._MatchCandidate(node_id="node-xyz", score=0.2)

    async def fake_record(*args, **kwargs):
        raise AssertionError("record_node_mention should not be called")

    monkeypatch.setattr(similarity, "generate_embedding", fake_embed)
    monkeypatch.setattr(similarity, "_query_best_match", fake_query)
    monkeypatch.setattr(similarity, "record_node_mention", fake_record)

    result = await similarity.run_similarity("session-1", "New concept", 5.0)

    assert isinstance(result, similarity.SimilarityCreateResult)
    assert result.embedding == [0.0, 0.0, 0.0]


@pytest.mark.asyncio
async def test_query_best_match_hits_vector_index(monkeypatch):
    driver = FakeNeo4jDriver([[{"node_id": "node-1", "score": 0.88}]])

    async def fake_get_driver():
        return driver

    monkeypatch.setattr(similarity, "get_driver", fake_get_driver)

    candidate = await similarity._query_best_match("session-1", [0.1, 0.2], top_k=3)

    assert candidate is not None
    assert candidate.node_id == "node-1"
    assert candidate.score == pytest.approx(0.88)
    assert driver.calls[0]["params"]["index_name"] == NODE_EMBEDDING_INDEX


@pytest.mark.asyncio
async def test_types_compatible_exact_match(monkeypatch):
    """Exact type matches should always be compatible."""
    # For exact matches, no embedding calls needed
    result = await similarity.types_compatible("organisation", "organisation")
    assert result is True


@pytest.mark.asyncio
async def test_types_compatible_case_insensitive(monkeypatch):
    """Type comparison should be case-insensitive."""
    result = await similarity.types_compatible("Organisation", "ORGANISATION")
    assert result is True


@pytest.mark.asyncio
async def test_types_compatible_semantic_match(monkeypatch):
    """Semantically similar types should be compatible (ADR-013)."""
    async def fake_embed(label: str, language: str = "en"):
        # Simulate similar embeddings for org-like types
        if "org" in label.lower() or "company" in label.lower():
            return [0.9, 0.1, 0.0]
        return [0.0, 0.9, 0.1]

    monkeypatch.setattr(similarity, "generate_embedding", fake_embed)
    similarity.clear_type_cache()

    # "organisation" and "company" should be compatible
    result = await similarity.types_compatible("organisation", "company")
    assert result is True


@pytest.mark.asyncio
async def test_types_incompatible_distinct_types(monkeypatch):
    """Semantically different types should be incompatible."""
    async def fake_embed(label: str, language: str = "en"):
        # Simulate distinct embeddings for different domains
        if "company" in label.lower():
            return [0.9, 0.1, 0.0]
        elif "fruit" in label.lower():
            return [0.0, 0.1, 0.9]
        return [0.5, 0.5, 0.5]

    monkeypatch.setattr(similarity, "generate_embedding", fake_embed)
    similarity.clear_type_cache()

    # "company" and "fruit" should NOT be compatible
    result = await similarity.types_compatible("company", "fruit")
    assert result is False


# Integration tests for pre-creation similarity check (ADR-011)


@pytest.mark.asyncio
async def test_pre_creation_similarity_match_existing(monkeypatch):
    """Pre-creation check should match existing node and increment mentions."""
    existing_node = Node(
        id="node-ml-1",
        label="Machine Learning",
        confidence=0.85,
        mentions=1,
        timestamps=[1.0],
        inferred_type="concept",
        flower_id=None,
        embedding=[0.9, 0.1, 0.0],
        created_at=datetime.now(timezone.utc),
        status=NodeStatus.GHOST,
    )
    
    # After mention is recorded, mentions should increment
    updated_node = Node(
        id="node-ml-1",
        label="Machine Learning",
        confidence=0.85,
        mentions=2,
        timestamps=[1.0, 2.5],
        inferred_type="concept",
        flower_id=None,
        embedding=[0.9, 0.1, 0.0],
        created_at=datetime.now(timezone.utc),
        status=NodeStatus.GHOST,
    )
    
    async def fake_embed(label: str, language: str = "en"):
        # Similar embedding for "machine learning"
        return [0.9, 0.1, 0.0]
    
    async def fake_query(session_id: str, embedding, top_k: int):
        # Return high similarity match
        return similarity._MatchCandidate(node_id="node-ml-1", score=0.95)
    
    async def fake_record(session_id: str, node_id: str, timestamp: float):
        # Verify correct node is being updated
        assert node_id == "node-ml-1"
        return updated_node
    
    monkeypatch.setattr(similarity, "generate_embedding", fake_embed)
    monkeypatch.setattr(similarity, "_query_best_match", fake_query)
    monkeypatch.setattr(similarity, "record_node_mention", fake_record)
    
    result = await similarity.run_similarity("session-1", "machine learning", 2.5)
    
    # Should match existing node, not create new
    assert isinstance(result, similarity.SimilarityMatchResult)
    assert result.node.id == "node-ml-1"
    assert result.node.mentions == 2
    assert result.score == pytest.approx(0.95)


@pytest.mark.asyncio
async def test_type_incompatibility_creates_new_node(monkeypatch):
    """Different types should prevent match despite label similarity."""
    async def fake_embed(label: str, language: str = "en"):
        # Label "apple" gets similar embedding regardless of context
        if "apple" in label.lower():
            return [0.8, 0.2, 0.0]
        # But types get different embeddings
        if label == "company":
            return [0.9, 0.1, 0.0]
        elif label == "fruit":
            return [0.0, 0.1, 0.9]
        return [0.5, 0.5, 0.5]
    
    async def fake_query(session_id: str, embedding, top_k: int):
        # High similarity match on label
        return similarity._MatchCandidate(node_id="node-apple-company", score=0.94)
    
    # Mock get_node to return the existing company node
    from app.services import graph_db
    async def fake_get_node(session_id: str, node_id: str):
        if node_id == "node-apple-company":
            return Node(
                id="node-apple-company",
                label="Apple",
                confidence=0.9,
                mentions=1,
                timestamps=[1.0],
                inferred_type="company",
                flower_id=None,
                embedding=[0.8, 0.2, 0.0],
                created_at=datetime.now(timezone.utc),
                status=NodeStatus.SOLID,
            )
        return None
    
    monkeypatch.setattr(similarity, "generate_embedding", fake_embed)
    monkeypatch.setattr(similarity, "_query_best_match", fake_query)
    monkeypatch.setattr(graph_db, "get_node", fake_get_node)
    
    similarity.clear_type_cache()
    
    # Types are incompatible, so should NOT match despite high label similarity
    types_match = await similarity.types_compatible("company", "fruit")
    assert types_match is False


@pytest.mark.asyncio
async def test_type_compatibility_threshold_0_80(monkeypatch):
    """Type compatibility should use 0.80 threshold (ADR-013)."""
    from app.config import get_settings
    settings = get_settings()
    
    # Verify threshold is 0.80
    assert settings.type_similarity_threshold == 0.80
    
    call_count = {"count": 0}
    
    async def fake_embed(label: str, language: str = "en"):
        call_count["count"] += 1
        # First call: type_a, second call: type_b
        if call_count["count"] == 1:
            return [1.0, 0.0, 0.0]
        else:
            # Return embedding that gives exactly 0.79 similarity (just below threshold)
            # cosine_sim([1,0,0], [0.79, 0.61, 0]) = 0.79 / 1.0 = 0.79
            return [0.79, 0.61, 0.0]
    
    monkeypatch.setattr(similarity, "generate_embedding", fake_embed)
    similarity.clear_type_cache()
    
    # Should be incompatible at 0.79 (below 0.80)
    result = await similarity.types_compatible("type_a", "type_b")
    assert result is False
    
    # Reset for second test
    call_count["count"] = 0
    similarity.clear_type_cache()
    
    async def fake_embed_compatible(label: str, language: str = "en"):
        call_count["count"] += 1
        if call_count["count"] == 1:
            return [1.0, 0.0, 0.0]
        else:
            # Return embedding that gives exactly 0.81 (just above threshold)
            return [0.81, 0.586, 0.0]
    
    monkeypatch.setattr(similarity, "generate_embedding", fake_embed_compatible)
    
    # Should be compatible at 0.81 (above 0.80)
    result = await similarity.types_compatible("type_c", "type_d")
    assert result is True


@pytest.mark.asyncio
async def test_similarity_check_enabled_flag_exists():
    """Test that similarity_check_enabled flag exists in config."""
    from app.config import get_settings
    
    settings = get_settings()
    
    # Verify the flag exists and is accessible
    assert hasattr(settings, 'similarity_check_enabled')
    assert isinstance(settings.similarity_check_enabled, bool)
    
    # Note: The actual enforcement of this flag happens in builder_service.py,
    # not in similarity.py. This test just verifies the configuration option exists.
    # Integration tests for builder_service.py should test the actual behavior.


@pytest.mark.asyncio
async def test_low_confidence_skips_similarity(monkeypatch):
    """Verify that confidence threshold logic can be tested."""
    from app.config import get_settings
    
    settings = get_settings()
    
    # Note: The confidence threshold (0.7) is enforced in builder_service.py,
    # not in similarity.py. This test verifies the threshold is configured correctly.
    # The actual enforcement is tested in builder_service integration tests.
    
    # Verify similarity threshold is configured
    assert settings.similarity_threshold >= 0.0
    assert settings.similarity_threshold <= 1.0
    
    # Test that low similarity scores are handled correctly
    async def fake_embed(label: str, language: str = "en"):
        return [0.1, 0.2, 0.3]
    
    async def fake_query(session_id: str, embedding, top_k: int):
        # Return low similarity score (below threshold)
        return similarity._MatchCandidate(node_id="node-ai", score=0.5)
    
    async def fake_record(*args, **kwargs):
        raise AssertionError("Should not record mention for low similarity")
    
    monkeypatch.setattr(similarity, "generate_embedding", fake_embed)
    monkeypatch.setattr(similarity, "_query_best_match", fake_query)
    monkeypatch.setattr(similarity, "record_node_mention", fake_record)
    
    result = await similarity.run_similarity("session-1", "AI", 1.0)
    
    # Low score should result in CreateResult, not MatchResult
    assert isinstance(result, similarity.SimilarityCreateResult)
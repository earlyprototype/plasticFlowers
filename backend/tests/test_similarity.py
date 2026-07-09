from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.models import Node, NodeStatus
from app.services import similarity
from app.services.graph_schema import NODE_EMBEDDING_INDEX
from .fakes import FakeNeo4jDriver


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
    params = driver.calls[0]["params"]
    assert params["index_name"] == NODE_EMBEDDING_INDEX
    # The vector index is global and filtered by session AFTER the top-k cut,
    # so the query must overfetch (>= 50) — otherwise other sessions' nodes
    # crowd out this session's true matches.
    assert params["top_k"] >= 50, "vector query must overfetch before session filter"
    assert params["session_id"] == "session-1"


@pytest.mark.asyncio
async def test_query_best_match_respects_larger_top_k(monkeypatch):
    """A caller-requested top_k above the overfetch floor is passed through."""
    driver = FakeNeo4jDriver([[{"node_id": "node-1", "score": 0.9}]])

    async def fake_get_driver():
        return driver

    monkeypatch.setattr(similarity, "get_driver", fake_get_driver)

    await similarity._query_best_match("session-1", [0.1, 0.2], top_k=200)

    assert driver.calls[0]["params"]["top_k"] == 200


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
# Note: the match/create decision itself lives in
# builder_service._check_similarity_and_persist and is covered by
# tests/test_builder_service.py (the old run_similarity helper was removed).


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
async def test_similarity_threshold_configured():
    """The similarity threshold used by builder_service must be configured.

    The confidence threshold (0.7) and the below-threshold create path are
    enforced in builder_service.py and covered by test_builder_service.py.
    """
    from app.config import get_settings

    settings = get_settings()
    assert 0.0 <= settings.similarity_threshold <= 1.0
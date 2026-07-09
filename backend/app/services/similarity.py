"""Pre-Builder similarity pipeline: embedding -> Neo4j vector query.

Includes type compatibility checking (ADR-013) using embedding similarity.
"""

from __future__ import annotations

import logging
from collections import OrderedDict
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, List, Optional, Union

import numpy as np

from ..config import get_settings
from ..models import Node
from .embeddings import generate_embedding
from .graph_db import record_node_mention
from .graph_schema import NODE_EMBEDDING_INDEX
from .neo4j import get_driver

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class SimilarityBaseResult:
    embedding: List[float]


@dataclass(slots=True)
class SimilarityMatchResult(SimilarityBaseResult):
    node: Node
    score: float


@dataclass(slots=True)
class SimilarityCreateResult(SimilarityBaseResult):
    """Indicates caller should create a new ghost node."""


SimilarityResult = Union[SimilarityMatchResult, SimilarityCreateResult]


async def run_similarity(session_id: str, label: str, timestamp: float) -> SimilarityResult:
    """Run the embedding + vector search flow and return the decision."""

    settings = get_settings()
    embedding = await generate_embedding(label)
    candidate = await _query_best_match(session_id, embedding, settings.similarity_top_k)

    if candidate and candidate.score >= settings.similarity_threshold:
        updated_node = await record_node_mention(session_id, candidate.node_id, timestamp)
        return SimilarityMatchResult(embedding=embedding, node=updated_node, score=candidate.score)

    return SimilarityCreateResult(embedding=embedding)


@dataclass(slots=True)
class _MatchCandidate:
    node_id: str
    score: float


# The vector index is global: queryNodes takes the top-k across ALL sessions
# and only then do we filter by session_id. Overfetch so other sessions'
# nodes cannot crowd this session's true matches out of the candidate set.
_VECTOR_OVERFETCH_K = 50


async def _query_best_match(
    session_id: str, embedding: List[float], top_k: int
) -> Optional[_MatchCandidate]:
    """Return the highest-scoring node id for the provided embedding.

    ``top_k`` is the caller-requested candidate count; internally we overfetch
    (at least _VECTOR_OVERFETCH_K) before the session filter is applied.
    """

    driver = await get_driver()
    query = """
    CALL db.index.vector.queryNodes($index_name, $top_k, $embedding)
    YIELD node, score
    WHERE node.session_id = $session_id
    RETURN node.id AS node_id, score
    ORDER BY score DESC
    LIMIT 1
    """
    params = {
        "index_name": NODE_EMBEDDING_INDEX,
        "top_k": max(top_k, _VECTOR_OVERFETCH_K),
        "embedding": embedding,
        "session_id": session_id,
    }

    async with driver.session() as session:
        async def _work(tx, cypher: str, arguments: dict) -> Optional[_MatchCandidate]:
            result = await tx.run(cypher, **arguments)
            record = await result.single()
            if record is None:
                return None
            return _MatchCandidate(node_id=record["node_id"], score=float(record["score"]))

        return await session.execute_read(_work, query, params)


# Type embedding cache with LRU eviction (ADR-013)
# Key: normalised type string, Value: embedding vector
# Max size prevents unbounded memory growth in long-running systems
_TYPE_EMBEDDING_CACHE: OrderedDict[str, List[float]] = OrderedDict()
_CACHE_MAX_SIZE = 256  # ~1.5MB max for 256 type embeddings (768-dim vectors)


def _normalise_type(type_str: str) -> str:
    """Normalise type string for cache lookup."""
    return type_str.strip().lower()


async def get_type_embedding(type_str: str) -> List[float]:
    """Get embedding for a type string, using LRU cache (max 256 entries)."""
    normalised = _normalise_type(type_str)
    
    if normalised in _TYPE_EMBEDDING_CACHE:
        # Move to end (mark as recently used)
        _TYPE_EMBEDDING_CACHE.move_to_end(normalised)
        return _TYPE_EMBEDDING_CACHE[normalised]
    
    embedding = await generate_embedding(normalised)
    _TYPE_EMBEDDING_CACHE[normalised] = embedding
    
    # Evict oldest if over limit
    if len(_TYPE_EMBEDDING_CACHE) > _CACHE_MAX_SIZE:
        _TYPE_EMBEDDING_CACHE.popitem(last=False)  # Remove oldest
    
    return embedding


def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Compute cosine similarity using numpy for performance.
    
    10-100x faster than pure Python on 768-dim vectors.
    Better numerical stability for edge cases.
    """
    if len(vec_a) != len(vec_b) or len(vec_a) == 0:
        return 0.0
    
    a = np.array(vec_a)
    b = np.array(vec_b)
    
    norm_product = np.linalg.norm(a) * np.linalg.norm(b)
    if norm_product == 0:
        return 0.0
    
    return float(np.dot(a, b) / norm_product)


async def types_compatible(type_a: str, type_b: str) -> bool:
    """Check if two inferred types are semantically compatible (ADR-013).
    
    Uses embedding similarity of type names instead of hardcoded dictionary.
    This respects the emergent types architecture where LLM can return
    any type string.
    
    Args:
        type_a: First type string (e.g., "organisation")
        type_b: Second type string (e.g., "company")
    
    Returns:
        True if types are considered compatible for matching.
    """
    settings = get_settings()
    
    # Exact match (fast path)
    if _normalise_type(type_a) == _normalise_type(type_b):
        return True
    
    # Semantic similarity of type names
    try:
        emb_a = await get_type_embedding(type_a)
        emb_b = await get_type_embedding(type_b)
        similarity = _cosine_similarity(emb_a, emb_b)
        
        is_compatible = similarity >= settings.type_similarity_threshold
        
        logger.debug(
            "type_compatibility type_a=%s type_b=%s similarity=%.3f compatible=%s",
            type_a, type_b, similarity, is_compatible,
        )
        
        return is_compatible
    except Exception as exc:
        # On error, be conservative and reject the match
        logger.warning(
            "type_compatibility_error type_a=%s type_b=%s error=%s, rejecting",
            type_a, type_b, exc,
        )
        return False


def clear_type_cache() -> None:
    """Clear the type embedding cache (for testing)."""
    _TYPE_EMBEDDING_CACHE.clear()


__all__ = [
    "run_similarity",
    "SimilarityResult",
    "SimilarityMatchResult",
    "SimilarityCreateResult",
    "types_compatible",
    "clear_type_cache",
]

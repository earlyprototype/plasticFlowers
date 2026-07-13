"""Google embedding utility with LRU caching (Gate 3 requirement)."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import math
from collections import OrderedDict
import os
import random
import threading
from typing import List, Tuple

from google import genai

from ..config import get_settings


class EmbeddingError(RuntimeError):
    """Raised when the embedding service cannot fulfil a request."""


_CACHE: "OrderedDict[str, Tuple[float, ...]]" = OrderedDict()
_CACHE_LOCK = asyncio.Lock()
_CLIENT: genai.Client | None = None
_CLIENT_LOCK = threading.Lock()

_FAKE_EMBEDDINGS_ENABLED = bool(
    os.getenv("PLASTICFLOWER_FAKE_EMBEDDINGS", "").strip().lower()
    in {"1", "true", "yes", "on"}
)
if _FAKE_EMBEDDINGS_ENABLED:
    logger = logging.getLogger(__name__)
    logger.warning("PLASTICFLOWER_FAKE_EMBEDDINGS enabled - using synthetic vectors")


def _get_client(settings) -> genai.Client:
    """Get or create a thread-safe singleton Client instance."""
    global _CLIENT
    if _CLIENT:
        return _CLIENT
    
    with _CLIENT_LOCK:
        if _CLIENT:
            return _CLIENT

        api_key = settings.gemini_api_key.get_secret_value()
        if not api_key:
            raise EmbeddingError("GEMINI_API_KEY is not configured")

        # Unified client handles both AI Studio and Vertex AI
        if settings.vertex_project_id:
            _CLIENT = genai.Client(
                vertexai=True,
                project=settings.vertex_project_id,
                location=settings.vertex_location,
                api_key=api_key, 
            )
        else:
            _CLIENT = genai.Client(
                api_key=api_key
            )
        return _CLIENT


async def generate_embedding(text: str, *, language: str = "en") -> List[float]:
    """Return (and cache) the embedding vector for the supplied text."""

    stripped = text.strip()
    if not stripped:
        raise ValueError("text must not be empty")

    settings = get_settings()
    if _FAKE_EMBEDDINGS_ENABLED:
        return _fake_embedding_vector(stripped, settings.embedding_dimensions)
    cache_key = _build_cache_key(stripped, language)

    async with _CACHE_LOCK:
        cached = _CACHE.get(cache_key)
        if cached is not None:
            _CACHE.move_to_end(cache_key)
            return list(cached)

    vector = await asyncio.to_thread(
        _embed_sync,
        stripped,
        settings,
    )

    async with _CACHE_LOCK:
        _CACHE[cache_key] = vector
        while len(_CACHE) > settings.embedding_cache_size:
            _CACHE.popitem(last=False)

    return list(vector)


def _embed_sync(
    text: str,
    settings,
) -> Tuple[float, ...]:
    """Blocking helper executed in a worker thread."""
    
    client = _get_client(settings)
    
    try:
        # Unified call for both Vertex and AI Studio. output_dimensionality is
        # explicit so the vector always matches embedding_dimensions (and the
        # Neo4j index) regardless of the model's native default.
        response = client.models.embed_content(
            model=settings.embedding_model,
            contents=text,
            config={
                'task_type': 'retrieval_document',
                'output_dimensionality': settings.embedding_dimensions,
            },
        )
    except Exception as exc:  # pragma: no cover
        raise EmbeddingError(f"Google embedding request failed: {exc}") from exc

    # Response structure differs in new SDK
    # It returns an EmbedContentResponse object with an 'embeddings' attribute
    # which is a list of ContentEmbedding objects
    if not response.embeddings:
         raise EmbeddingError("Google returned an empty embedding payload")

    embedding = response.embeddings[0].values
    _validate_embedding(embedding, settings.embedding_dimensions)
    # gemini-embedding-001 unit-normalises only at its native 3072; truncated
    # outputs (768/1536) are NOT normalised, so cosine similarity would be off.
    # Normalise here so any configured dimension is safe. (No-op at 3072.)
    return _l2_normalize(embedding)


def _l2_normalize(embedding: List[float]) -> Tuple[float, ...]:
    """Return the unit-length vector (cosine-safe for truncated embeddings)."""
    norm = math.sqrt(sum(float(v) * float(v) for v in embedding))
    if norm == 0.0:
        return tuple(float(v) for v in embedding)
    return tuple(float(v) / norm for v in embedding)


def _validate_embedding(embedding: List[float] | None, expected_dimensions: int) -> None:
    if not embedding:
        raise EmbeddingError("Google returned an empty embedding payload")
    if len(embedding) != expected_dimensions:
        raise EmbeddingError(
            f"Embedding dimensions mismatch: expected {expected_dimensions}, got {len(embedding)}"
        )


def _build_cache_key(text: str, language: str) -> str:
    return f"{language.lower()}::{text.lower()}"


def _fake_embedding_vector(text: str, dimensions: int) -> List[float]:
    """Deterministic pseudo-random vector for offline development."""

    digest = hashlib.blake2s(text.encode("utf-8"), digest_size=16).digest()
    seed = int.from_bytes(digest, "big")
    rng = random.Random(seed)
    return [round(rng.uniform(-0.5, 0.5), 6) for _ in range(dimensions)]


def is_fake_embeddings_enabled() -> bool:
    return _FAKE_EMBEDDINGS_ENABLED


__all__ = ["generate_embedding", "EmbeddingError", "is_fake_embeddings_enabled"]

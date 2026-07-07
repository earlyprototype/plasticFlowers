"""Transcript chunk store with Neo4j persistence.

Gate 7 persistence: chunks are now stored in Neo4j and linked to sessions.
"""

from __future__ import annotations

from typing import List

from ..models import TranscriptChunk
from . import graph_db


class ChunkStore:
    """Chunk repository backed by Neo4j."""

    async def save(self, chunk: TranscriptChunk) -> None:
        await graph_db.save_chunk(chunk)

    async def get(self, chunk_id: str) -> TranscriptChunk | None:
        return await graph_db.get_chunk(chunk_id)

    async def delete(self, chunk_id: str) -> None:
        # Note: No direct delete by chunk_id in graph_db
        # For now, implement as no-op (session cleanup handles bulk delete)
        pass

    async def list_for_session(self, session_id: str) -> List[TranscriptChunk]:
        return await graph_db.list_chunks_for_session(session_id)
    
    async def get_recent_transcript(self, session_id: str, word_limit: int = 1000) -> str:
        """Retrieve recent transcript text for Gardener context."""
        return await graph_db.get_recent_transcript(session_id, word_limit)


chunk_store = ChunkStore()

__all__ = ["ChunkStore", "chunk_store"]

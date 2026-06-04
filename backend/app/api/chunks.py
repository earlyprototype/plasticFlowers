"""Transcript chunk submission endpoint.

This endpoint is intentionally thin - it validates the request,
queues background processing, and returns immediately.

All orchestration logic lives in BuilderService.
"""

from __future__ import annotations

import asyncio
import logging
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Path, status

from ..models import (
    ChunkSubmissionRequest,
    ChunkSubmissionResponse,
    TranscriptChunk,
)
from ..services import (
    chunk_store,
    get_builder_service,
    get_session_record,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions/{session_id}/chunks", tags=["chunks"])

# Track active background tasks to prevent garbage collection
_active_tasks: set[asyncio.Task[None]] = set()


@router.post(
    "",
    response_model=ChunkSubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit transcript chunk",
)
async def submit_chunk(
    payload: ChunkSubmissionRequest,
    session_id: str = Path(..., description="Session identifier"),
) -> ChunkSubmissionResponse:
    """POST /sessions/{id}/chunks - queue a chunk for Builder processing.
    
    Returns 202 Accepted immediately. Processing happens in background.
    SSE events notify when complete.
    """
    # Validate session exists and is not ended
    session = await get_session_record(session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    if session.ended_at:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Session has ended; no further chunks accepted",
        )

    # Truncate massive chunks to protect LLM context
    text = payload.text
    if len(text) > 50000:
        logger.warning(
            "chunk.truncated session=%s original_len=%d",
            session_id, len(text),
        )
        text = text[:50000]

    # Create chunk record
    chunk_id = f"chunk_{uuid4().hex}"
    chunk = TranscriptChunk(
        id=chunk_id,
        text=text,
        start_time=payload.start_time,
        end_time=payload.end_time,
        session_id=session_id,
    )

    # Save to in-memory store for transcript context
    await chunk_store.save(chunk)

    # Queue background processing
    _queue_processing(session_id, chunk)

    return ChunkSubmissionResponse(chunk_id=chunk_id)


def _queue_processing(session_id: str, chunk: TranscriptChunk) -> None:
    """Queue chunk for background Builder processing."""
    task = asyncio.create_task(
        _process_chunk(session_id, chunk),
        name=f"builder-{chunk.id}",
    )
    _active_tasks.add(task)
    task.add_done_callback(lambda t: _active_tasks.discard(t))


async def _process_chunk(session_id: str, chunk: TranscriptChunk) -> None:
    """Background task: run Builder pipeline via service."""
    service = get_builder_service()
    
    try:
        result = await service.process_chunk(session_id, chunk)
        logger.info(
            "chunk.processed session=%s chunk=%s nodes=%d rels=%d ms=%.0f",
            session_id, chunk.id,
            len(result.nodes),
            len(result.relationships),
            result.total_duration_ms,
        )
    except Exception:
        # Service already handles SSE error broadcast
        logger.exception(
            "chunk.failed session=%s chunk=%s",
            session_id, chunk.id,
        )

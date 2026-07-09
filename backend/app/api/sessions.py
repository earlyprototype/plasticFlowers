"""Session management endpoints (Gate 6 implementation).

Spec alignment:
- `_docs/_dev/_MVP/_api/01_contracts.md` — Session Management section
- `_docs/_dev/_MVP/_schema/01_data_model.md` — Session entity shape
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Path, status

from ..models import (
    NodeStatus,
    SessionCreateRequest,
    SessionCreateResponse,
    SessionDetail,
    SessionEndResponse,
    SessionListResponse,
    SessionNameResponse,
    SessionRenameRequest,
)
from ..services import (
    create_session_record,
    delete_session_record,
    gardener_scheduler,
    get_builder_service,
    get_session_record,
    list_chunks_for_session,
    list_nodes,
    list_session_records,
    publish_chunk_added,
    update_session_record,
)
from ..services.redis_streams import SESSION_END_FLUSH_CHUNK_ID
from .chunks import drain_session_tasks

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post(
    "",
    response_model=SessionCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create session",
)
async def create_session(payload: SessionCreateRequest) -> SessionCreateResponse:
    """POST /sessions — create a new session (DEC-010 naming rule)."""

    session_id = f"session_{uuid4().hex}"
    created_at = datetime.now(timezone.utc)

    # DEC-010: User-provided name or timestamp fallback
    if payload.name and payload.name.strip():
        name = payload.name.strip()
    else:
        name = created_at.strftime("%Y-%m-%d %H:%M")

    session = await create_session_record(
        session_id, name, created_at, language_variant=payload.language_variant
    )

    return SessionCreateResponse(
        id=session.id,
        name=session.name,
        language_variant=session.language_variant,
        created_at=session.created_at,
    )


@router.get("", response_model=SessionListResponse, summary="List sessions")
async def list_sessions() -> SessionListResponse:
    """GET /sessions — list existing sessions."""

    sessions = await list_session_records()
    return SessionListResponse(sessions=sessions)


@router.get(
    "/{session_id}",
    response_model=SessionDetail,
    summary="Get session detail (includes transcript)",
)
async def get_session(session_id: str = Path(..., description="Session identifier")) -> SessionDetail:
    """GET /sessions/{id} — fetch a session detail record with transcript."""

    session = await get_session_record(session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    # Reconstruct transcript from chunks
    chunks = await list_chunks_for_session(session_id)
    transcript = " ".join(chunk.text for chunk in chunks)

    return SessionDetail(
        id=session.id,
        name=session.name,
        language_variant=session.language_variant,
        created_at=session.created_at,
        ended_at=session.ended_at,
        transcript=transcript,
    )


@router.patch(
    "/{session_id}",
    response_model=SessionNameResponse,
    summary="Rename session",
)
async def rename_session(
    payload: SessionRenameRequest,
    session_id: str = Path(..., description="Session identifier"),
) -> SessionNameResponse:
    """PATCH /sessions/{id} — rename a session."""

    session = await get_session_record(session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    updated = await update_session_record(session_id, name=payload.name)
    return SessionNameResponse(id=updated.id, name=updated.name)


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete session",
)
async def delete_session(session_id: str = Path(..., description="Session identifier")) -> None:
    """DELETE /sessions/{id} — delete a session and its data."""

    session = await get_session_record(session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    await delete_session_record(session_id)


@router.post(
    "/{session_id}/end",
    response_model=SessionEndResponse,
    summary="End session",
)
async def end_session(session_id: str = Path(..., description="Session identifier")) -> SessionEndResponse:
    """POST /sessions/{id}/end — mark session as ended, stop Gardener for session."""

    session = await get_session_record(session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    if session.ended_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Session has already ended",
        )

    ended_at = datetime.now(timezone.utc)
    updated = await update_session_record(session_id, ended_at=ended_at)

    # Drain in-flight Builder tasks BEFORE the flush check below: chunks
    # accepted moments before session end may still be processing, and the
    # builder-count/ghost checks must observe their results.
    await drain_session_tasks(session_id)

    # Gardener flush (T6): sessions with fewer chunks than the
    # Builder->Gardener ratio never trip the ratio gate, leaving their
    # nodes GHOST forever. Publish one final trigger if work remains.
    # (The Gardener scheduler drops the session's scheduling state after it
    # processes the flush sentinel; if no flush is published we clear it here.)
    await _flush_gardener_on_session_end(session_id)

    return SessionEndResponse(id=updated.id, ended_at=updated.ended_at)  # type: ignore[arg-type]


async def _flush_gardener_on_session_end(session_id: str) -> None:
    """Publish a final Gardener trigger if the session has unprocessed work.

    "Unprocessed work" means Builder runs that haven't reached the ratio gate
    yet (builder run counter > 0), or ghost nodes still awaiting review.
    Failures are logged, never raised — ending the session must not fail
    because Redis/Neo4j are unavailable.
    """
    builder = get_builder_service()
    pending_chunks = builder.get_builder_count(session_id)

    ghost_count = 0
    if pending_chunks == 0:
        # No pending Builder runs — only flush if ghosts remain.
        try:
            ghost_count = len(await list_nodes(session_id, status=NodeStatus.GHOST))
        except Exception as exc:
            logger.warning(
                "session_end.ghost_check_failed session=%s error=%s", session_id, exc
            )

    flush_published = False
    try:
        if pending_chunks > 0 or ghost_count > 0:
            # Same publish pattern the Builder uses to trigger the Gardener
            # (services/redis_streams.py); the consumer only needs session_id.
            # The sentinel chunk_id tells the scheduler to drop the session's
            # scheduling state once this final run has been processed.
            await publish_chunk_added(
                session_id=session_id,
                chunk_id=SESSION_END_FLUSH_CHUNK_ID,
                text="",
            )
            flush_published = True
            logger.info(
                "session_end.gardener_flush session=%s pending_chunks=%d ghosts=%d",
                session_id,
                pending_chunks,
                ghost_count,
            )
    except Exception as exc:
        logger.warning(
            "session_end.gardener_flush_failed session=%s error=%s", session_id, exc
        )
    finally:
        # The session is over either way — clear the Builder run counter.
        builder.reset_builder_count(session_id)
        if not flush_published:
            # No flush event for the scheduler to clean up after — drop the
            # session's Gardener scheduling state (e.g. _last_run) here.
            gardener_scheduler.clear_activity(session_id)

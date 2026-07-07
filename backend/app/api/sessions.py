"""Session management endpoints (Gate 6 implementation).

Spec alignment:
- `_docs/_dev/_MVP/_api/01_contracts.md` — Session Management section
- `_docs/_dev/_MVP/_schema/01_data_model.md` — Session entity shape
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Path, status

from ..models import (
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
    get_session_record,
    list_chunks_for_session,
    list_session_records,
    update_session_record,
)

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

    # Stop Gardener activity tracking for this session
    gardener_scheduler.clear_activity(session_id)

    return SessionEndResponse(id=updated.id, ended_at=updated.ended_at)  # type: ignore[arg-type]

"""SSE subscription endpoint."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Path
from sse_starlette.sse import EventSourceResponse

from ..services import sse_manager


router = APIRouter(prefix="/sessions/{session_id}", tags=["stream"])


@router.get("/stream", summary="Subscribe to session SSE stream")
async def stream_session(session_id: str = Path(..., description="Session identifier")):
    """GET /sessions/{id}/stream — SSE event subscription."""

    queue = await sse_manager.subscribe(session_id)

    async def event_generator():
        try:
            while True:
                try:
                    # Wait for 15s max before sending a keep-alive
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield event
                except asyncio.TimeoutError:
                    # Send explicit heartbeat event so frontend watchdog can verify liveness
                    yield {"event": "heartbeat", "data": "ping"}
        except asyncio.CancelledError:
            raise
        finally:
            await sse_manager.unsubscribe(session_id, queue)

    return EventSourceResponse(event_generator())

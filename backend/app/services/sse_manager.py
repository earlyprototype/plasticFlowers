"""In-process Server-Sent Events broadcast manager."""

from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from typing import Dict, Set

from ..models import (
    ChunkProcessedEvent,
    FlowerCreatedEvent,
    FlowerDissolvedEvent,
    FlowerUpdatedEvent,
    GardenerCycleEvent,
    NodeAddedEvent,
    NodeCorrectedEvent,
    NodeMergedEvent,
    NodeRemovedEvent,
    NodeUpdatedEvent,
    RelationshipAddedEvent,
    RelationshipRemovedEvent,
    ReferenceAddedEvent,
)

SSEventType = (
    NodeAddedEvent
    | NodeCorrectedEvent
    | NodeUpdatedEvent
    | NodeRemovedEvent
    | NodeMergedEvent
    | RelationshipAddedEvent
    | RelationshipRemovedEvent
    | FlowerCreatedEvent
    | FlowerUpdatedEvent
    | FlowerDissolvedEvent
    | ChunkProcessedEvent
    | GardenerCycleEvent
    | ReferenceAddedEvent
)


class SSEManager:
    """Tracks per-session subscribers and broadcasts SSE payloads."""

    def __init__(self) -> None:
        self._connections: Dict[str, Set[asyncio.Queue[dict]]] = defaultdict(set)
        self._lock_internal: asyncio.Lock | None = None

    @property
    def _lock(self) -> asyncio.Lock:
        if self._lock_internal is None:
            self._lock_internal = asyncio.Lock()
        return self._lock_internal

    async def subscribe(self, session_id: str) -> asyncio.Queue[dict]:
        """Register a new subscriber queue for the supplied session."""

        queue: asyncio.Queue[dict] = asyncio.Queue()
        async with self._lock:
            self._connections[session_id].add(queue)
        return queue

    async def unsubscribe(self, session_id: str, queue: asyncio.Queue[dict]) -> None:
        async with self._lock:
            subscribers = self._connections.get(session_id)
            if not subscribers:
                return
            subscribers.discard(queue)
            if not subscribers:
                self._connections.pop(session_id, None)

    async def broadcast(self, session_id: str, event: SSEventType) -> None:
        """Broadcast the event to all subscribers of the session."""

        message = self._serialise_event(event)
        async with self._lock:
            targets = list(self._connections.get(session_id, ()))
        if targets:
            print(f"SSE: {event.type} -> {len(targets)} subscriber(s)")
        for queue in targets:
            await queue.put(message)

    def _serialise_event(self, event: SSEventType) -> dict:
        payload = event.model_dump(mode="json").get("payload", {})
        data = json.dumps(payload, default=str)
        return {"event": event.type, "data": data}


# Singleton used by routers/services
sse_manager = SSEManager()

__all__ = ["SSEManager", "sse_manager", "SSEventType"]

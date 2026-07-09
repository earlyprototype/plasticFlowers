"""In-process Server-Sent Events broadcast manager."""

from __future__ import annotations

import asyncio
import json
import logging
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
    ResyncRequiredEvent,
    ResyncRequiredPayload,
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
    | ResyncRequiredEvent
)

logger = logging.getLogger(__name__)

#: Upper bound per subscriber queue. A slow/stalled SSE consumer drops its
#: OLDEST queued event instead of growing the queue without bound (the client
#: re-syncs the full graph state on reconnect, so a dropped event is not fatal).
SUBSCRIBER_QUEUE_MAXSIZE = 1000


class SSEManager:
    """Tracks per-session subscribers and broadcasts SSE payloads."""

    def __init__(self) -> None:
        self._connections: Dict[str, Set[asyncio.Queue[dict]]] = defaultdict(set)
        self._lock_internal: asyncio.Lock | None = None
        #: Queues currently inside an overflow episode: they already received a
        #: resync_required control event and are not re-signalled until they
        #: drain below half capacity.
        self._resync_signalled: Set[asyncio.Queue[dict]] = set()

    @property
    def _lock(self) -> asyncio.Lock:
        if self._lock_internal is None:
            self._lock_internal = asyncio.Lock()
        return self._lock_internal

    async def subscribe(self, session_id: str) -> asyncio.Queue[dict]:
        """Register a new subscriber queue for the supplied session."""

        queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=SUBSCRIBER_QUEUE_MAXSIZE)
        async with self._lock:
            self._connections[session_id].add(queue)
        return queue

    async def unsubscribe(self, session_id: str, queue: asyncio.Queue[dict]) -> None:
        async with self._lock:
            self._resync_signalled.discard(queue)
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
            logger.debug(
                "sse.broadcast session=%s event=%s subscribers=%d",
                session_id,
                event.type,
                len(targets),
            )
        for queue in targets:
            # A previously signalled queue that has drained below half capacity
            # ends its overflow episode: the next overflow re-signals.
            if (
                queue in self._resync_signalled
                and queue.qsize() <= queue.maxsize // 2
            ):
                self._resync_signalled.discard(queue)
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                # Bounded queue: drop the oldest event(s) so the broadcast hot
                # path never blocks behind a stalled subscriber. On the FIRST
                # drop of an overflow episode, enqueue a resync_required
                # control event ahead of the new message so the client knows
                # the stream is no longer complete and must re-fetch state.
                first_drop = queue not in self._resync_signalled
                dropped = self._drop_oldest(queue)
                if first_drop:
                    self._resync_signalled.add(queue)
                    # Make room for the control event AND the new message.
                    self._drop_oldest(queue)
                    queue.put_nowait(
                        self._serialise_event(
                            ResyncRequiredEvent(
                                payload=ResyncRequiredPayload(reason="event_overflow")
                            )
                        )
                    )
                logger.warning(
                    "sse.queue_full session=%s dropped_event=%s new_event=%s maxsize=%d resync_signalled=%s",
                    session_id,
                    dropped.get("event") if dropped else "unknown",
                    event.type,
                    SUBSCRIBER_QUEUE_MAXSIZE,
                    first_drop,
                )
                queue.put_nowait(message)

    @staticmethod
    def _drop_oldest(queue: asyncio.Queue[dict]) -> dict | None:
        """Remove and return the oldest queued event (None if empty)."""
        try:
            dropped = queue.get_nowait()
            queue.task_done()
            return dropped
        except asyncio.QueueEmpty:  # pragma: no cover - racy edge
            return None

    def _serialise_event(self, event: SSEventType) -> dict:
        payload = event.model_dump(mode="json").get("payload", {})
        data = json.dumps(payload, default=str)
        return {"event": event.type, "data": data}


# Singleton used by routers/services
sse_manager = SSEManager()

__all__ = ["SSEManager", "sse_manager", "SSEventType"]

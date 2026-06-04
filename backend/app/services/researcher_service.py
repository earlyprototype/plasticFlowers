"""Researcher service for external enrichment (Gate 4).

Consumes `nodes.needs_research` events from Redis, invokes the ResearcherAgent,
persists results to Neo4j, and broadcasts `reference_added` SSE events.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from ..agents import ResearcherAgent, ResearcherAgentError, ResearcherAgentResult
from ..models import ReferenceAddedEvent, ReferenceAddedPayload
from ..services.chunk_store import chunk_store
from ..services.graph_db import create_reference, get_node
from ..services.redis_streams import (
    ack_event,
    consume_events,
    flush_stale_events,
    STREAM_NODES_NEEDS_RESEARCH,
    GROUP_RESEARCHER,
)
from ..services.sse_manager import sse_manager

logger = logging.getLogger(__name__)

REDIS_CONSUMER_NAME = "researcher-worker-1"


class ResearcherService:
    """Orchestrates research tasks via Redis event consumption."""

    def __init__(self) -> None:
        self._agent = ResearcherAgent()
        self._stop_event = asyncio.Event()
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the Redis consumer loop."""
        if self._task and not self._task.done():
            return
        
        # Flush stale events to avoid processing old triggers on restart
        try:
            flushed = await flush_stale_events(
                STREAM_NODES_NEEDS_RESEARCH, 
                GROUP_RESEARCHER, 
                max_age_seconds=600  # 10 minutes max age
            )
            if flushed > 0:
                logger.info("researcher.startup_flushed stale_events=%d", flushed)
        except Exception as exc:
            logger.warning("researcher.startup_flush_failed error=%s", exc)

        self._stop_event.clear()
        self._task = asyncio.create_task(
            self._redis_consumer_loop(),
            name="researcher-redis-consumer"
        )
        logger.info("researcher.started stream=%s", STREAM_NODES_NEEDS_RESEARCH)

    async def stop(self) -> None:
        """Stop the Researcher service."""
        self._stop_event.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("researcher.stopped")

    async def _redis_consumer_loop(self) -> None:
        """Consume research events and trigger the agent."""
        
        # Small delay for system initialization
        await asyncio.sleep(2)
        
        try:
            async for message_id, data in consume_events(
                STREAM_NODES_NEEDS_RESEARCH,
                GROUP_RESEARCHER,
                REDIS_CONSUMER_NAME,
                count=1,
                block_ms=5000,
            ):
                if self._stop_event.is_set():
                    break
                
                # Parse event data (handle bytes/strings)
                session_id = data.get("session_id") or data.get(b"session_id")
                node_id = data.get("node_id") or data.get(b"node_id")
                label = data.get("label") or data.get(b"label")
                entity_type = data.get("entity_type") or data.get(b"entity_type")
                
                if isinstance(session_id, bytes): session_id = session_id.decode()
                if isinstance(node_id, bytes): node_id = node_id.decode()
                if isinstance(label, bytes): label = label.decode()
                if isinstance(entity_type, bytes): entity_type = entity_type.decode()
                
                if not (session_id and node_id and label):
                    logger.warning("researcher.invalid_event id=%s data=%s", message_id, data)
                    await ack_event(STREAM_NODES_NEEDS_RESEARCH, GROUP_RESEARCHER, message_id)
                    continue

                try:
                    await self._process_research_request(session_id, node_id, label, str(entity_type))
                except Exception:
                    logger.exception("researcher.process_failed session=%s node=%s", session_id, node_id)
                
                await ack_event(STREAM_NODES_NEEDS_RESEARCH, GROUP_RESEARCHER, message_id)
                
        except asyncio.CancelledError:
            logger.info("researcher.consumer_cancelled")
        except Exception:
            logger.exception("researcher.consumer_crashed")

    async def _process_research_request(
        self,
        session_id: str,
        node_id: str,
        label: str,
        entity_type: str,
    ) -> None:
        """Execute research logic for a single node."""
        
        # Check if node still exists and needs research
        node = await get_node(session_id, node_id)
        if not node:
            logger.info("researcher.node_missing session=%s node=%s", session_id, node_id)
            return

        # Fetch recent context for better search queries
        context = await chunk_store.get_recent_transcript(session_id, word_limit=300)
        
        logger.info(
            "researcher.executing session=%s node=%s label='%s' type=%s",
            session_id, node_id, label, entity_type
        )
        
        result = await self._agent.research(
            session_id=session_id,
            node_id=node_id,
            node_label=label,
            entity_type=entity_type,
            context=context,
        )
        
        if result.reference:
            # Persist ReferenceNode
            persisted_ref = await create_reference(session_id, result.reference)
            
            # Broadcast event
            await sse_manager.broadcast(
                session_id,
                ReferenceAddedEvent(
                    payload=ReferenceAddedPayload(
                        node_id=node_id,
                        reference_id=persisted_ref.id,
                        summary=persisted_ref.canonical_summary,
                        provider=result.provider_used.value,
                        url=persisted_ref.sources[0].url if persisted_ref.sources else None,
                    )
                )
            )
            
            logger.info(
                "researcher.completed session=%s node=%s ref=%s provider=%s duration=%.0fms",
                session_id, node_id, persisted_ref.id, result.provider_used.value, result.search_duration_ms
            )
        else:
            logger.warning("researcher.no_result session=%s node=%s", session_id, node_id)


# Module singleton
researcher_service = ResearcherService()

__all__ = ["ResearcherService", "researcher_service"]

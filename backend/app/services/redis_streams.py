"""Redis Streams client for event-driven agent coordination.

This module provides an event bus for decoupled communication between agents:
- Builder publishes `chunks.added` when new transcript chunks are processed
- Gardener consumes chunk events and publishes `nodes.needs_research`
- Researcher consumes research events

Spec reference: _docs/_dev/_MVP/_schema/02_redis_streams.md (if exists)
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

import redis.asyncio as redis
from pydantic import BaseModel, Field

from ..config import get_settings

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Stream Names (namespaced by session)
# -----------------------------------------------------------------------------

STREAM_CHUNKS_ADDED = "pf:chunks:added"  # Builder -> Gardener
STREAM_NODES_NEEDS_RESEARCH = "pf:nodes:needs_research"  # Gardener -> Researcher

# Consumer group names
GROUP_GARDENER = "gardener"
GROUP_RESEARCHER = "researcher"


# -----------------------------------------------------------------------------
# Event Payloads
# -----------------------------------------------------------------------------


class ChunkAddedEvent(BaseModel):
    """Event published when Builder processes a new chunk."""
    session_id: str = Field(..., description="Session identifier")
    chunk_id: str = Field(..., description="Chunk identifier")
    text: str = Field(..., description="Chunk text content")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    nodes_created: int = Field(0, description="Number of nodes created from chunk")
    relationships_created: int = Field(0, description="Number of relationships created")


class NodeNeedsResearchEvent(BaseModel):
    """Event published when Gardener identifies a node needing research."""
    session_id: str = Field(..., description="Session identifier")
    node_id: str = Field(..., description="Node identifier")
    label: str = Field(..., description="Node label")
    entity_type: str = Field(..., description="Inferred entity type")
    research_reason: str = Field(..., description="Why research is needed")
    priority: str = Field("normal", description="Research priority: high or normal")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# -----------------------------------------------------------------------------
# Redis Connection Management
# -----------------------------------------------------------------------------

_redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """Get or create Redis async client."""
    global _redis_client
    
    if _redis_client is None:
        settings = get_settings()
        redis_url = getattr(settings, 'redis_url', 'redis://localhost:6379')
        _redis_client = redis.from_url(redis_url, decode_responses=True)
        
        # Test connection
        try:
            await _redis_client.ping()
            logger.info("redis.connected url=%s", redis_url)
        except redis.ConnectionError as exc:
            logger.error("redis.connection_failed url=%s error=%s", redis_url, exc)
            raise
    
    return _redis_client


async def close_redis() -> None:
    """Close Redis connection (call on shutdown)."""
    global _redis_client
    
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
        logger.info("redis.disconnected")


# -----------------------------------------------------------------------------
# Stream Publishing
# -----------------------------------------------------------------------------


async def publish_event(
    stream: str,
    event: BaseModel,
    *,
    maxlen: int = 10000,
) -> str:
    """
    Publish an event to a Redis Stream.
    
    Args:
        stream: Stream name (e.g., STREAM_CHUNKS_ADDED)
        event: Pydantic model to publish
        maxlen: Maximum stream length (older entries trimmed)
    
    Returns:
        Message ID assigned by Redis
    """
    client = await get_redis()
    
    # Convert Pydantic model to dict, serializing datetime
    data = event.model_dump(mode="json")
    
    message_id = await client.xadd(
        stream,
        data,
        maxlen=maxlen,
        approximate=True,
    )
    
    logger.debug(
        "redis.publish stream=%s id=%s type=%s",
        stream,
        message_id,
        type(event).__name__,
    )
    
    return message_id


# -----------------------------------------------------------------------------
# Stream Consumption
# -----------------------------------------------------------------------------


async def ensure_consumer_group(stream: str, group: str) -> None:
    """Create consumer group if it doesn't exist."""
    client = await get_redis()
    
    try:
        # Create group starting from the latest message
        await client.xgroup_create(stream, group, id="$", mkstream=True)
        logger.info("redis.group_created stream=%s group=%s", stream, group)
    except redis.ResponseError as exc:
        if "BUSYGROUP" in str(exc):
            # Group already exists - that's fine
            pass
        else:
            raise


async def flush_stale_events(stream: str, group: str, max_age_seconds: int = 60) -> int:
    """
    Flush ALL pending and unread events from a consumer group on startup.
    
    This prevents processing stale events from dead sessions after a server restart.
    Uses a nuclear approach: delete and recreate the group starting from '$' (latest).
    
    Args:
        stream: Stream name
        group: Consumer group name
        max_age_seconds: UNUSED - kept for API compatibility
        
    Returns:
        Number of events that were pending (now flushed)
    """
    client = await get_redis()
    
    try:
        # Check if stream exists
        if not await client.exists(stream):
            logger.debug("redis.flush_stale stream=%s does_not_exist", stream)
            return 0
        
        # Get pending count before destroying
        pending_count = 0
        try:
            pending = await client.xpending(stream, group)
            pending_count = pending.get("pending", 0) if pending else 0
        except redis.ResponseError:
            pass  # Group might not exist
        
        # Get stream length to know how many unread messages exist
        stream_len = await client.xlen(stream)
        
        # Delete the consumer group (this clears all pending and position info)
        try:
            await client.xgroup_destroy(stream, group)
            logger.info(
                "redis.group_destroyed stream=%s group=%s pending=%d stream_len=%d",
                stream, group, pending_count, stream_len,
            )
        except redis.ResponseError as exc:
            if "NOGROUP" not in str(exc):
                raise
        
        # Recreate group starting from latest message (skip all existing)
        await client.xgroup_create(stream, group, id="$", mkstream=True)
        logger.info(
            "redis.group_recreated stream=%s group=%s position=latest",
            stream, group,
        )
        
        if pending_count > 0 or stream_len > 0:
            logger.warning(
                "redis.flushed_stale_events stream=%s group=%s pending=%d unread=%d",
                stream, group, pending_count, stream_len,
            )
        
        return pending_count
        
    except Exception as exc:
        logger.warning("redis.flush_stale_failed stream=%s error=%s", stream, exc)
        return 0


async def consume_events(
    stream: str,
    group: str,
    consumer: str,
    *,
    count: int = 10,
    block_ms: int = 5000,
) -> AsyncIterator[Tuple[str, Dict[str, Any]]]:
    """
    Consume events from a Redis Stream using consumer groups.
    
    Yields (message_id, data) tuples. Caller must acknowledge messages
    using `ack_event()` after processing.
    
    Args:
        stream: Stream name
        group: Consumer group name
        consumer: Unique consumer name within group
        count: Max events to read per batch
        block_ms: Block timeout in milliseconds (0 = forever)
    
    Yields:
        Tuple of (message_id, event_data_dict)
    """
    client = await get_redis()
    
    # Ensure group exists
    await ensure_consumer_group(stream, group)
    
    while True:
        try:
            # Read pending messages first, then new ones
            messages = await client.xreadgroup(
                group,
                consumer,
                {stream: ">"},  # ">" = only new messages
                count=count,
                block=block_ms,
            )
            
            if not messages:
                continue
            
            for stream_name, stream_messages in messages:
                for message_id, data in stream_messages:
                    yield message_id, data
                    
        except redis.ResponseError as exc:
            # Handle NOGROUP errors by recreating the group
            if "NOGROUP" in str(exc):
                logger.warning("redis.nogroup_error - recreating group stream=%s group=%s", stream, group)
                await ensure_consumer_group(stream, group)
                await asyncio.sleep(0.5)
                continue
            logger.error("redis.response_error stream=%s error=%s", stream, exc)
            await asyncio.sleep(1)
        except redis.ConnectionError as exc:
            logger.error("redis.consume_error stream=%s error=%s", stream, exc)
            await asyncio.sleep(1)  # Backoff before retry


async def ack_event(stream: str, group: str, message_id: str) -> None:
    """Acknowledge a processed event (removes from pending list)."""
    client = await get_redis()
    await client.xack(stream, group, message_id)
    logger.debug("redis.ack stream=%s group=%s id=%s", stream, group, message_id)


# -----------------------------------------------------------------------------
# Convenience Publishers
# -----------------------------------------------------------------------------


async def publish_chunk_added(
    session_id: str,
    chunk_id: str,
    text: str,
    nodes_created: int = 0,
    relationships_created: int = 0,
) -> str:
    """Publish a chunks.added event (called by Builder)."""
    event = ChunkAddedEvent(
        session_id=session_id,
        chunk_id=chunk_id,
        text=text,
        nodes_created=nodes_created,
        relationships_created=relationships_created,
    )
    return await publish_event(STREAM_CHUNKS_ADDED, event)


async def publish_node_needs_research(
    session_id: str,
    node_id: str,
    label: str,
    entity_type: str,
    research_reason: str,
    priority: str = "normal",
) -> str:
    """Publish a nodes.needs_research event (called by Gardener)."""
    event = NodeNeedsResearchEvent(
        session_id=session_id,
        node_id=node_id,
        label=label,
        entity_type=entity_type,
        research_reason=research_reason,
        priority=priority,
    )
    return await publish_event(STREAM_NODES_NEEDS_RESEARCH, event)


# -----------------------------------------------------------------------------
# Health Check
# -----------------------------------------------------------------------------


async def redis_health_check() -> Dict[str, Any]:
    """Check Redis connection health."""
    try:
        client = await get_redis()
        info = await client.info("server")
        return {
            "status": "healthy",
            "version": info.get("redis_version", "unknown"),
            "connected_clients": (await client.info("clients")).get("connected_clients", 0),
        }
    except Exception as exc:
        return {
            "status": "unhealthy",
            "error": str(exc),
        }


__all__ = [
    # Stream names
    "STREAM_CHUNKS_ADDED",
    "STREAM_NODES_NEEDS_RESEARCH",
    # Group names
    "GROUP_GARDENER",
    "GROUP_RESEARCHER",
    # Event types
    "ChunkAddedEvent",
    "NodeNeedsResearchEvent",
    # Connection
    "get_redis",
    "close_redis",
    # Publishing
    "publish_event",
    "publish_chunk_added",
    "publish_node_needs_research",
    # Consuming
    "ensure_consumer_group",
    "consume_events",
    "ack_event",
    "flush_stale_events",
    # Health
    "redis_health_check",
]


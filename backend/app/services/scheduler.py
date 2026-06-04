"""Gardener scheduler and orchestration (Gate 5).

Redis-only event-driven Gardener: runs when Builder publishes chunk events.
Debounce controlled via GARDENER_DEBOUNCE_SECONDS in config (default 60s).
"""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
from uuid import uuid4

from ..agents.gardener import (
    CorrectionAction,
    GardenerAgent,
    GardenerAgentError,
    FlowerAction,
    NewRelationship,
    NodeAction,
)
from ..models import (
    Flower,
    FlowerCreatedEvent,
    FlowerDissolvedEvent,
    FlowerUpdatedEvent,
    GardenerCycleEvent,
    Node,
    NodeCorrectedEvent,
    NodeCorrectedPayload,
    NodeMergedEvent,
    NodeRemovedEvent,
    NodeStatus,
    NodeUpdatedEvent,
    Relationship,
    RelationshipAddedEvent,
    RelationshipRemovedEvent,
    RelationshipCategory,
    RelationshipSource,
)
from .chunk_store import chunk_store
from .graph_db import (
    apply_corrections_to_graph,
    apply_temporal_decay,
    create_relationship,
    delete_flower,
    delete_node,
    delete_relationship,
    get_chunks_after,
    get_node,
    get_proofread_checkpoint,
    get_session_context,
    get_session_record,
    get_session_vocabulary,
    list_flowers,
    list_nodes,
    list_relationships,
    set_node_flower,
    update_node,
    update_proofread_checkpoint,
    update_session_context,
    update_session_vocabulary,
    upsert_flower,
)
from .llm import is_fake_llm_enabled
from .redis_streams import (
    ack_event,
    consume_events,
    flush_stale_events,
    publish_gardener_complete,
    publish_node_needs_research,
    STREAM_CHUNKS_ADDED,
    GROUP_GARDENER,
)
from .sse_manager import sse_manager

logger = logging.getLogger(__name__)

# Redis consumer configuration
REDIS_CONSUMER_NAME = "gardener-worker-1"


def apply_vocabulary_to_text(text: str, vocabulary: Optional[Dict[str, str]]) -> str:
    """Apply known vocabulary corrections to text before LLM processing.
    
    This pre-proofread pass instantly corrects recurring STT errors,
    reducing LLM workload and improving consistency.
    """
    if not vocabulary or not text:
        return text
    
    result = text
    for original, correction in vocabulary.items():
        # Case-insensitive replacement
        pattern = re.compile(re.escape(original), re.IGNORECASE)
        result = pattern.sub(correction, result)
    
    return result


def apply_vocabulary_to_nodes(
    nodes: Sequence[Node], 
    vocabulary: Optional[Dict[str, str]]
) -> Sequence[Node]:
    """Apply vocabulary corrections to node labels before LLM sees them."""
    if not vocabulary:
        return nodes
    
    for node in nodes:
        corrected_label = apply_vocabulary_to_text(node.label, vocabulary)
        if corrected_label != node.label:
            logger.debug(
                "pre_proofread.node_label corrected '%s' -> '%s'",
                node.label,
                corrected_label,
            )
            node.label = corrected_label
    
    return nodes


class GardenerScheduler:
    """Redis-only event-driven Gardener scheduler.
    
    Simplified architecture: Builder publishes to Redis, Gardener consumes.
    Debounce is configurable via config.gardener_debounce_seconds.
    """

    def __init__(self) -> None:
        self._agent = GardenerAgent()
        self._stop_event = asyncio.Event()
        self._task: asyncio.Task | None = None
        self._lock = asyncio.Lock()
        self._last_run: Dict[str, float] = {}
        self._active_sessions: set[str] = set()  # Track sessions with SSE clients

    def mark_activity(self, session_id: str) -> None:
        """Note that a session is active (has SSE clients watching)."""
        self._active_sessions.add(session_id)

    def clear_activity(self, session_id: str) -> None:
        """Clear activity tracking for a session (called when session ends)."""
        self._active_sessions.discard(session_id)
        self._last_run.pop(session_id, None)

    async def start(self) -> None:
        """Start the Redis consumer loop."""
        if self._task and not self._task.done():
            return
        
        # Flush stale events from previous sessions (prevents processing dead events on restart)
        try:
            flushed = await flush_stale_events(
                STREAM_CHUNKS_ADDED, 
                GROUP_GARDENER, 
                max_age_seconds=30,  # Anything older than 30s is stale
            )
            if flushed > 0:
                logger.info("gardener.startup_flushed stale_events=%d", flushed)
        except Exception as exc:
            logger.warning("gardener.startup_flush_failed error=%s", exc)
        
        self._stop_event.clear()
        self._task = asyncio.create_task(
            self._redis_consumer_loop(), 
            name="gardener-redis-consumer"
        )
        logger.info("gardener.started mode=redis_only stream=%s", STREAM_CHUNKS_ADDED)

    async def stop(self) -> None:
        """Stop the Gardener scheduler."""
        self._stop_event.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("gardener.stopped")

    async def _redis_consumer_loop(self) -> None:
        """Consume chunk events from Redis and trigger Gardener.
        
        Ratio-based triggering: Builder only publishes to Redis every N chunks
        (controlled by builder_gardener_ratio). This means each Redis event
        represents a batch of Builder work, so we run Gardener for each event.
        
        Minimal safety debounce (5s) prevents rapid consecutive runs if
        there's unexpected Redis burst.
        """
        from ..config import get_settings
        settings = get_settings()
        ratio = settings.builder_gardener_ratio
        safety_debounce = 5  # Minimal safety debounce (seconds)
        
        logger.info(
            "gardener.consumer_started ratio=%d:1 stream=%s",
            ratio,
            STREAM_CHUNKS_ADDED,
        )
        
        # Small delay to let the system initialize
        await asyncio.sleep(2)
        
        try:
            async for message_id, data in consume_events(
                STREAM_CHUNKS_ADDED,
                GROUP_GARDENER,
                REDIS_CONSUMER_NAME,
                count=1,  # Process one at a time (ratio already batches)
                block_ms=5000,
            ):
                if self._stop_event.is_set():
                    break
                    
                # DIAGNOSTIC: Check if Redis returns bytes or strings
                logger.warning("gardener.REDIS_DATA raw_data=%s keys=%s", data, list(data.keys())[:3])
                
                # Handle both bytes and string keys from Redis
                session_id = data.get("session_id") or data.get(b"session_id")
                chunk_id = data.get("chunk_id") or data.get(b"chunk_id")
                
                # Decode bytes if necessary
                if isinstance(session_id, bytes):
                    session_id = session_id.decode()
                if isinstance(chunk_id, bytes):
                    chunk_id = chunk_id.decode()
                
                if not session_id:
                    logger.warning("gardener.event_missing_session id=%s data=%s", message_id, data)
                    await ack_event(STREAM_CHUNKS_ADDED, GROUP_GARDENER, message_id)
                    continue
                
                # Minimal safety debounce to prevent burst
                loop = asyncio.get_event_loop()
                last_run = self._last_run.get(session_id, 0)
                time_since_last = loop.time() - last_run
                
                if time_since_last < safety_debounce:
                    logger.debug(
                        "gardener.safety_debounce session=%s wait=%.0fs",
                        session_id,
                        time_since_last,
                    )
                    await ack_event(STREAM_CHUNKS_ADDED, GROUP_GARDENER, message_id)
                    continue
                
                logger.info(
                    "gardener.triggered session=%s after=%d_chunks chunk=%s",
                    session_id,
                    ratio,
                    chunk_id,
                )
                
                # Run Gardener
                async with self._lock:
                    try:
                        if is_fake_llm_enabled():
                            await self._run_gardener_fake(session_id)
                        else:
                            await self._run_gardener(session_id)
                        self._last_run[session_id] = loop.time()
                        logger.info("gardener.complete session=%s", session_id)
                    except GardenerAgentError as exc:
                        logger.warning(
                            "gardener.agent_error session=%s code=%s error=%s",
                            session_id,
                            exc.code,
                            exc,
                        )
                    except Exception:
                        logger.exception("gardener.run_failed session=%s", session_id)
                
                await ack_event(STREAM_CHUNKS_ADDED, GROUP_GARDENER, message_id)
                
        except asyncio.CancelledError:
            logger.info("gardener.consumer_cancelled")
        except Exception:
            logger.exception("gardener.consumer_crashed")

    async def _run_gardener(self, session_id: str) -> None:
        from time import perf_counter
        t_start = perf_counter()
        
        try:
            # DIAGNOSTIC: Log session_id before querying
            logger.warning(
                "gardener.TIMING_START session_id=%s",
                session_id,
            )
            
            t1 = perf_counter()
            ghost_nodes, solid_nodes, relationships, flowers = await asyncio.gather(
                list_nodes(session_id, status=NodeStatus.GHOST),
                list_nodes(session_id, status=NodeStatus.SOLID),
                list_relationships(session_id),
                list_flowers(session_id),
            )
            t2 = perf_counter()
            
            logger.warning(
                "gardener.TIMING_DB_LOAD session=%s ms=%.0f ghosts=%d solids=%d rels=%d flowers=%d",
                session_id,
                (t2-t1)*1000,
                len(ghost_nodes),
                len(solid_nodes),
                len(relationships),
                len(flowers),
            )

            if not ghost_nodes and not solid_nodes:
                logger.debug("gardener.skip_empty session=%s", session_id)
                return

            # Phase D: Get session for language variant
            session_record = await get_session_record(session_id)
            language_variant = session_record.language_variant if session_record else "en-GB"
            
            # Phase D: Pre-proofread pass - apply vocabulary before LLM
            vocabulary = await get_session_vocabulary(session_id)
            
            if vocabulary:
                ghost_nodes = list(apply_vocabulary_to_nodes(ghost_nodes, vocabulary))
                solid_nodes = list(apply_vocabulary_to_nodes(solid_nodes, vocabulary))

            # Gate 7: Retrieve recent transcript for context
            recent_transcript = await chunk_store.get_recent_transcript(session_id, word_limit=1000)
            
            # Apply vocabulary to transcript as well
            if vocabulary:
                recent_transcript = apply_vocabulary_to_text(recent_transcript, vocabulary)
            
            # Incremental proofreading: only process chunks since last checkpoint
            last_chunk_id = await get_proofread_checkpoint(session_id)
            new_chunks = await get_chunks_after(session_id, last_chunk_id, limit=10)
            new_chunk_text = " ".join(c.text for c in new_chunks) if new_chunks else ""
            
            logger.debug(
                "gardener.checkpoint session=%s last_chunk=%s new_chunks=%d",
                session_id, last_chunk_id, len(new_chunks),
            )
            
            # Load session context for consistent understanding across incremental proofreading
            session_context = await get_session_context(session_id)
            
            t3 = perf_counter()
            logger.warning(
                "gardener.TIMING_PREP_DONE session=%s prep_ms=%.0f calling_llm...",
                session_id,
                (t3-t2)*1000,
            )
            
            result = await self._agent.run(
                ghost_nodes=ghost_nodes,
                solid_nodes=solid_nodes,
                relationships=relationships,
                flowers=flowers,
                recent_transcript=recent_transcript,
                language_variant=language_variant,
                session_context=session_context,
            )
            
            t4 = perf_counter()
            logger.warning(
                "gardener.TIMING_LLM_DONE session=%s llm_total_ms=%.0f",
                session_id,
                (t4-t3)*1000,
            )

            # Diagnostic logging for Gardener results
            logger.warning(
                "gardener.agent_complete session=%s node_actions=%d flower_actions=%d corrections=%d new_rels=%d llm_ms=%.0f ghosts=%d solids=%d",
                session_id,
                len(result.node_actions),
                len(result.flower_actions),
                len(result.corrections),
                len(result.new_relationships),
                result.llm_duration_ms,
                len(ghost_nodes),
                len(solid_nodes),
            )
            
            # Log individual actions for debugging
            if result.node_actions:
                for action in result.node_actions[:10]:  # Limit to first 10
                    logger.warning("  gardener.node_action: %s node=%s merge_into=%s reason=%s", 
                        action.action, action.node_id, action.merge_into, action.reason[:50] if action.reason else "")
            else:
                logger.warning("  gardener.NO_NODE_ACTIONS returned by LLM - ghosts will remain ghosts!")
                
            if result.flower_actions:
                for action in result.flower_actions[:5]:
                    logger.warning("  gardener.flower_action: %s flower=%s label=%s members=%d",
                        action.action, action.flower_id, action.label, len(action.member_ids))

            # Apply actions in deterministic order: nodes -> relationships -> flowers -> heartbeat
            nodes_by_id = {node.id: node for node in [*ghost_nodes, *solid_nodes]}
            relationships_by_id = {rel.id: rel for rel in relationships}

            # Apply corrections first (they may affect node labels before merging)
            await self._apply_corrections(session_id, result.corrections)
            
            # Update proofread checkpoint after successful processing
            if new_chunks:
                last_processed_chunk = new_chunks[-1]
                await update_proofread_checkpoint(session_id, last_processed_chunk.id)
                logger.debug(
                    "gardener.checkpoint_updated session=%s chunk=%s",
                    session_id, last_processed_chunk.id,
                )

            await self._apply_node_actions(session_id, result.node_actions, nodes_by_id, relationships_by_id)

            # Refresh relationships after node actions
            relationships_after_nodes = await list_relationships(session_id)
            await self._apply_new_relationships(session_id, result.new_relationships)

            # Refresh current state for flowers
            current_nodes = await list_nodes(session_id)
            current_relationships = await list_relationships(session_id)
            await self._apply_flower_actions(
                session_id,
                result.flower_actions,
                current_nodes,
                current_relationships,
            )
            
            # Phase D: Apply temporal decay (mark old SOLID nodes as LEGACY)
            decayed_count = await apply_temporal_decay(session_id, threshold_minutes=5)
            if decayed_count > 0:
                logger.info(
                    "gardener.temporal_decay session=%s nodes_decayed=%d",
                    session_id,
                    decayed_count,
                )
            
            # Phase 3: Publish research triggers (fire and forget)
            if result.research_actions:
                await self._publish_research_actions(session_id, result.research_actions)
            
            # Phase D.5: Publish completion event to Redis
            try:
                await publish_gardener_complete(
                    session_id=session_id,
                    nodes_solidified=len([a for a in result.node_actions if a.action == "solidify"]),
                    nodes_removed=len([a for a in result.node_actions if a.action == "remove"]),
                    flowers_created=len([a for a in result.flower_actions if a.action == "create"]),
                    corrections_applied=len(result.corrections),
                )
            except Exception as redis_err:
                logger.warning("gardener.redis_publish_failed session=%s error=%s", session_id, redis_err)
        finally:
            await sse_manager.broadcast(
                session_id,
                GardenerCycleEvent(payload={"timestamp": datetime.now(timezone.utc)}),
            )

    async def _run_gardener_fake(self, session_id: str) -> None:
        """Deterministic Gardener cycle for fake LLM mode (no external calls)."""

        ghost_nodes, solid_nodes, relationships, flowers = await asyncio.gather(
            list_nodes(session_id, status=NodeStatus.GHOST),
            list_nodes(session_id, status=NodeStatus.SOLID),
            list_relationships(session_id),
            list_flowers(session_id),
        )

        if not ghost_nodes and not solid_nodes:
            logger.debug("gardener.fake.skip_empty session=%s", session_id)
            return

        node_actions = [
            NodeAction(action="confirm", node_id=node.id, merge_into="", reason="fake_mode_autoconfirm")
            for node in ghost_nodes
        ]

        nodes_by_id = {node.id: node for node in [*ghost_nodes, *solid_nodes]}
        relationships_by_id = {rel.id: rel for rel in relationships}

        await self._apply_node_actions(session_id, node_actions, nodes_by_id, relationships_by_id)

        # Deterministically add a couple of relationships if missing to exercise downstream flows
        new_relationships = self._synthesise_fake_relationships(nodes_by_id, relationships_by_id)
        await self._apply_new_relationships(session_id, new_relationships)

        # Refresh state after node and relationship actions
        current_nodes = await list_nodes(session_id)
        current_relationships = await list_relationships(session_id)

        # Create or update a Flower so UI/export paths have data in fake mode
        flower_actions = self._synthesise_fake_flower_actions(current_nodes, current_relationships, flowers)
        await self._apply_flower_actions(
            session_id,
            flower_actions,
            current_nodes,
            current_relationships,
        )
        await sse_manager.broadcast(
            session_id,
            GardenerCycleEvent(payload={"timestamp": datetime.now(timezone.utc)}),
        )

    def _synthesise_fake_relationships(
        self,
        nodes_by_id: Dict[str, Node],
        relationships_by_id: Dict[str, Relationship],
    ) -> List[NewRelationship]:
        """Create minimal deterministic relationships when running in fake mode."""

        sorted_nodes = sorted(nodes_by_id.values(), key=lambda n: n.created_at)
        if len(sorted_nodes) < 2:
            return []

        existing_keys = {
            (rel.source_id, rel.target_id, rel.description.lower()) for rel in relationships_by_id.values()
        }
        pairs = []
        # Link the first few nodes together to guarantee edges for Flower formation
        for idx in range(min(len(sorted_nodes) - 1, 2)):
            source_id = sorted_nodes[idx].id
            target_id = sorted_nodes[idx + 1].id
            key = (source_id, target_id, "related to")
            if key in existing_keys or source_id == target_id:
                continue
            pairs.append(
                NewRelationship(
                    source_id=source_id,
                    target_id=target_id,
                    category=RelationshipCategory.ASSOCIATIVE,
                    description="related to",
                    confidence=0.65,
                    reason="fake_mode_autolink",
                )
            )
            existing_keys.add(key)

        return pairs

    def _synthesise_fake_flower_actions(
        self,
        nodes: Sequence[Node],
        relationships: Sequence[Relationship],
        existing_flowers: Sequence[Flower],
    ) -> List[FlowerAction]:
        """Return a single create/update Flower action for deterministic fake mode."""

        if len(nodes) < 3:
            return []

        sorted_nodes = sorted(nodes, key=lambda n: n.created_at)
        member_ids = [node.id for node in sorted_nodes[: min(len(sorted_nodes), 5)]]
        edge_count = _count_internal_edges(member_ids, relationships)
        if edge_count < 2:
            return []

        action = "update" if existing_flowers else "create"
        flower_id = existing_flowers[0].id if existing_flowers else None
        label = existing_flowers[0].label if existing_flowers else "Demo Flower"
        stem_node_id = member_ids[0]

        return [
            FlowerAction(
                action=action,
                flower_id=flower_id,
                label=label,
                member_ids=member_ids,
                stem_node_id=stem_node_id,
                reason="fake_mode_autoflower",
            )
        ]

    async def _apply_corrections(
        self,
        session_id: str,
        corrections: Sequence[CorrectionAction],
    ) -> None:
        """Apply STT corrections to nodes, relationships, and transcript chunks."""
        if not corrections:
            return
        
        logger.info(
            "gardener.corrections session=%s count=%d",
            session_id,
            len(corrections),
        )
        
        # Convert to tuples for apply_corrections_to_graph
        correction_tuples = [(c.original, c.corrected) for c in corrections]
        
        # Apply to graph and get affected node IDs
        counts = await apply_corrections_to_graph(session_id, correction_tuples)
        
        logger.info(
            "gardener.corrections_applied session=%s nodes=%d rels=%d chunks=%d",
            session_id,
            counts["nodes_updated"],
            counts["relationships_updated"],
            counts["chunks_updated"],
        )
        
        # Broadcast node_corrected events for UI feedback
        for correction in corrections:
            # Get affected node IDs from the counts (we track in apply_corrections_to_graph)
            affected_node_ids = counts.get("affected_node_ids", [])
            for node_id in affected_node_ids:
                await sse_manager.broadcast(
                    session_id,
                    NodeCorrectedEvent(
                        payload=NodeCorrectedPayload(
                            node_id=node_id,
                            old_label=correction.original,
                            new_label=correction.corrected,
                            confidence=correction.confidence,
                        )
                    ),
                )
        
        # Update session vocabulary for future instant correction
        new_vocab = {c.original.lower(): c.corrected for c in corrections if c.confidence > 0.8}
        if new_vocab:
            await update_session_vocabulary(session_id, new_vocab)
            logger.debug(
                "gardener.vocabulary_updated session=%s terms=%d",
                session_id,
                len(new_vocab),
            )

    async def _apply_node_actions(
        self,
        session_id: str,
        node_actions: Sequence,
        nodes_by_id: Dict[str, Node],
        relationships_by_id: Dict[str, Relationship],
    ) -> None:
        for action in node_actions:
            if action.node_id not in nodes_by_id:
                logger.warning("gardener.node_missing session=%s node=%s", session_id, action.node_id)
                continue
            if action.action == "confirm":
                await self._confirm_node(session_id, nodes_by_id[action.node_id])
                nodes_by_id[action.node_id].status = NodeStatus.SOLID
            elif action.action == "prune":
                await self._prune_node(session_id, nodes_by_id[action.node_id], relationships_by_id)
                nodes_by_id.pop(action.node_id, None)
            elif action.action == "merge":
                await self._merge_node(
                    session_id,
                    nodes_by_id,
                    relationships_by_id,
                    source_id=action.node_id,
                    target_id=action.merge_into,
                )
                nodes_by_id.pop(action.node_id, None)

    async def _confirm_node(self, session_id: str, node: Node) -> None:
        node.status = NodeStatus.SOLID
        updated = await update_node(session_id, node)
        await sse_manager.broadcast(session_id, NodeUpdatedEvent(payload=updated))

    async def _prune_node(
        self,
        session_id: str,
        node: Node,
        relationships_by_id: Dict[str, Relationship],
    ) -> None:
        # Emit relationship removals for edges attached to this node
        for rel in list(relationships_by_id.values()):
            if rel.source_id == node.id or rel.target_id == node.id:
                await delete_relationship(session_id, rel.id)
                await sse_manager.broadcast(
                    session_id, RelationshipRemovedEvent(payload={"id": rel.id})
                )
                relationships_by_id.pop(rel.id, None)
        await delete_node(session_id, node.id)
        await sse_manager.broadcast(session_id, NodeRemovedEvent(payload={"id": node.id}))

    async def _merge_node(
        self,
        session_id: str,
        nodes_by_id: Dict[str, Node],
        relationships_by_id: Dict[str, Relationship],
        *,
        source_id: str,
        target_id: str | None,
    ) -> None:
        if not target_id:
            logger.warning("gardener.merge_missing_target session=%s node=%s", session_id, source_id)
            return
        if target_id not in nodes_by_id:
            logger.warning(
                "gardener.merge_invalid_target session=%s node=%s target=%s",
                session_id,
                source_id,
                target_id,
            )
            return
        if source_id == target_id:
            return

        source_node = await get_node(session_id, source_id)
        target_node = await get_node(session_id, target_id)
        if not source_node or not target_node:
            logger.warning("gardener.merge_nodes_missing session=%s source=%s target=%s", session_id, source_id, target_id)
            return

        # Transfer properties
        target_node.mentions += source_node.mentions
        target_node.timestamps = sorted(set([*target_node.timestamps, *source_node.timestamps]))
        target_node.confidence = max(target_node.confidence, source_node.confidence)
        # preserve target_node.inferred_type and flower_id

        # Rewire relationships that involve the source node
        existing_keys = {
            (rel.source_id, rel.target_id, rel.description.lower()): rel.id
            for rel in relationships_by_id.values()
        }
        for rel in list(relationships_by_id.values()):
            if rel.source_id != source_id and rel.target_id != source_id:
                continue
            new_source = target_id if rel.source_id == source_id else rel.source_id
            new_target = target_id if rel.target_id == source_id else rel.target_id
            if new_source == new_target:
                # Drop self-loop
                await delete_relationship(session_id, rel.id)
                await sse_manager.broadcast(session_id, RelationshipRemovedEvent(payload={"id": rel.id}))
                relationships_by_id.pop(rel.id, None)
                continue

            dedup_key = (new_source, new_target, rel.description.lower())
            await delete_relationship(session_id, rel.id)
            await sse_manager.broadcast(session_id, RelationshipRemovedEvent(payload={"id": rel.id}))
            relationships_by_id.pop(rel.id, None)

            if dedup_key in existing_keys:
                continue

            recreated = Relationship(
                id=rel.id,
                source_id=new_source,
                target_id=new_target,
                category=rel.category,
                description=rel.description,
                confidence=rel.confidence,
                evidence=rel.evidence,
                source=rel.source,
                created_at=rel.created_at,
            )
            await create_relationship(session_id, recreated)
            await sse_manager.broadcast(session_id, RelationshipAddedEvent(payload=recreated))
            relationships_by_id[rel.id] = recreated
            existing_keys[dedup_key] = rel.id

        await delete_node(session_id, source_id)
        await update_node(session_id, target_node)
        await sse_manager.broadcast(session_id, NodeUpdatedEvent(payload=target_node))
        await sse_manager.broadcast(
            session_id, NodeMergedEvent(payload={"from_id": source_id, "into_id": target_id})
        )

    async def _apply_new_relationships(
        self, session_id: str, new_relationships: Sequence
    ) -> None:
        for rel in new_relationships:
            if rel.source_id == rel.target_id:
                continue
            relationship = Relationship(
                id=f"rel_{uuid4().hex}",
                source_id=rel.source_id,
                target_id=rel.target_id,
                category=rel.category if isinstance(rel.category, RelationshipCategory) else RelationshipCategory(rel.category),
                description=rel.description,
                confidence=rel.confidence,
                evidence=rel.reason or rel.description,
                source=RelationshipSource.GARDENER,
                created_at=datetime.now(timezone.utc),
            )
            await create_relationship(session_id, relationship)
            await sse_manager.broadcast(session_id, RelationshipAddedEvent(payload=relationship))

    async def _apply_flower_actions(
        self,
        session_id: str,
        flower_actions: Sequence,
        nodes: Sequence[Node],
        relationships: Sequence[Relationship],
    ) -> None:
        nodes_by_id = {node.id: node for node in nodes}
        flowers_by_id = {flower.id: flower for flower in await list_flowers(session_id)}

        for action in flower_actions:
            member_ids = list(action.member_ids or [])
            member_ids = [mid for mid in member_ids if mid in nodes_by_id]
            edge_count = _count_internal_edges(member_ids, relationships)
            if action.action in {"create", "update"}:
                if len(member_ids) < 3 or edge_count < 2:
                    logger.warning(
                        "gardener.flower_rejected session=%s id=%s reason=criteria_not_met members=%d edges=%d",
                        session_id,
                        action.flower_id or "new",
                        len(member_ids),
                        edge_count,
                    )
                    continue
                if action.stem_node_id not in member_ids:
                    logger.warning(
                        "gardener.flower_rejected session=%s reason=stem_not_in_members",
                        session_id
                    )
                    continue

                if action.action == "create":
                    flower = Flower(
                        id=f"flower_{uuid4().hex}",
                        label=action.label,
                        stem_node_id=action.stem_node_id,
                        member_ids=member_ids,
                        created_at=datetime.now(timezone.utc),
                    )
                    await upsert_flower(session_id, flower)
                    # Mark nodes as belonging to this flower
                    for node_id in member_ids:
                        await set_node_flower(session_id, node_id, flower.id)
                    
                    await sse_manager.broadcast(session_id, FlowerCreatedEvent(payload=flower))
                    logger.info("gardener.flower_created session=%s id=%s label=%s", session_id, flower.id, flower.label)
                
                elif action.action == "update" and action.flower_id:
                    if action.flower_id not in flowers_by_id:
                        continue
                    flower = flowers_by_id[action.flower_id]
                    flower.label = action.label
                    flower.member_ids = member_ids
                    flower.stem_node_id = action.stem_node_id
                    await upsert_flower(session_id, flower)
                    
                    # Update node memberships
                    # Note: strict implementation would clear old members, but valid for now
                    for node_id in member_ids:
                        await set_node_flower(session_id, node_id, flower.id)

                    await sse_manager.broadcast(session_id, FlowerUpdatedEvent(payload=flower))

            elif action.action == "dissolve" and action.flower_id:
                if action.flower_id in flowers_by_id:
                    flower = flowers_by_id[action.flower_id]
                    await delete_flower(session_id, action.flower_id)
                    # Clear flower_id from members
                    for node_id in flower.member_ids:
                        if node_id in nodes_by_id: # Only clean up if node still exists
                            await set_node_flower(session_id, node_id, None)
                    
                    await sse_manager.broadcast(session_id, FlowerDissolvedEvent(payload={"id": action.flower_id}))
                    logger.info("gardener.flower_dissolved session=%s id=%s", session_id, action.flower_id)

    async def _publish_research_actions(
        self,
        session_id: str,
        actions: Sequence,
    ) -> None:
        """Publish research triggers to Redis."""
        for action in actions:
            try:
                await publish_node_needs_research(
                    session_id=session_id,
                    node_id=action.node_id,
                    label=action.label or "unknown",  # Fallback if label missing
                    entity_type=action.entity_type,
                    research_reason=action.reason,
                    priority=action.priority,
                )
                logger.info(
                    "gardener.research_triggered session=%s node=%s type=%s reason=%s",
                    session_id, action.node_id, action.entity_type, action.reason
                )
            except Exception as exc:
                logger.warning(
                    "gardener.research_publish_failed session=%s node=%s error=%s",
                    session_id, action.node_id, exc
                )



def _count_internal_edges(member_ids: Iterable[str], relationships: Sequence[Relationship]) -> int:
    member_set = set(member_ids)
    return sum(
        1
        for rel in relationships
        if rel.source_id in member_set and rel.target_id in member_set
    )


gardener_scheduler = GardenerScheduler()

__all__ = ["gardener_scheduler", "GardenerScheduler"]


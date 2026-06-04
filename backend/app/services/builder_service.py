"""Builder service for chunk processing orchestration.

This module handles the orchestration of Builder agent calls, following
the same pattern as GardenerScheduler but for request-driven processing.

Key difference from Gardener:
- Builder is REQUEST-DRIVEN: processes each chunk immediately when received
- Gardener is EVENT-DRIVEN: batches and debounces based on Redis events

Future agents (Researcher, Librarian) will follow the Gardener pattern.
"""

from __future__ import annotations

import asyncio
import logging
from time import perf_counter
from typing import List, Sequence
from uuid import uuid4

from ..agents import BuilderAgent, BuilderAgentError, BuilderAgentResult, UnresolvedRelationship
from ..config import get_settings
from ..models import Node, Relationship, RelationshipSource, TranscriptChunk
from .embeddings import generate_embedding, is_fake_embeddings_enabled
from .graph_db import create_node, create_relationship, list_nodes, list_relationships, save_chunk, record_node_mention, get_node
from .redis_streams import publish_chunk_added
from .sse_manager import sse_manager
from ..models import (
    ChunkProcessedEvent,
    ChunkProcessedPayload,
    NodeAddedEvent,
    NodeUpdatedEvent,
    RelationshipAddedEvent,
)
from .similarity import _query_best_match, types_compatible
from .graph_schema import NODE_EMBEDDING_INDEX
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class _SimilarityCheckResult:
    """Result of pre-creation similarity check for a single node."""
    is_match: bool
    node: Node  # Either matched existing node or newly created node
    original_label: str  # LLM-extracted label (for relationship rewiring)


class BuilderService:
    """Orchestrates Builder agent with persistence and event publishing.
    
    Usage:
        service = BuilderService()
        await service.process_chunk(session_id, chunk)
    
    The service handles:
    - LLM invocation via BuilderAgent
    - Embedding generation
    - Neo4j persistence
    - SSE broadcasting
    - Redis event publishing (ratio-based Gardener triggering)
    
    Ratio-based triggering:
    - Gardener is triggered every N Builder runs (configurable via builder_gardener_ratio)
    - This paces Gardener work relative to actual chunk processing
    - Prevents over-calling Gardener on rapid chunk uploads
    """

    def __init__(
        self,
        *,
        timeout_seconds: float = 90.0,
        skip_neo4j: bool = False,
    ) -> None:
        self._agent = BuilderAgent()
        self._timeout = timeout_seconds
        self._skip_neo4j = skip_neo4j
        # Ratio-based Gardener triggering: count Builder runs per session
        self._builder_runs: dict[str, int] = {}

    async def process_chunk(
        self,
        session_id: str,
        chunk: TranscriptChunk,
    ) -> BuilderResult:
        """Process a transcript chunk through the full Builder pipeline.
        
        Returns:
            BuilderResult with nodes/relationships created and timing info.
        
        Raises:
            BuilderServiceError on failure (timeout, LLM error, persistence error).
        """
        start = perf_counter()
        
        try:
            async with asyncio.timeout(self._timeout):
                return await self._process(session_id, chunk, start)
        except asyncio.TimeoutError:
            await self._broadcast_error(session_id, chunk.id, "timeout")
            raise BuilderServiceError(
                f"Builder timed out after {self._timeout}s",
                code="timeout",
            )
        except BuilderAgentError as exc:
            await self._broadcast_error(session_id, chunk.id, "llm_error")
            raise BuilderServiceError(str(exc), code=exc.code) from exc
        except Exception as exc:
            await self._broadcast_error(session_id, chunk.id, "error")
            raise BuilderServiceError(str(exc), code="unknown") from exc

    async def _process(
        self,
        session_id: str,
        chunk: TranscriptChunk,
        start: float,
    ) -> "BuilderResult":
        """Internal processing pipeline with pre-creation similarity check (ADR-011)."""
        
        settings = get_settings()
        
        # 1. Load existing nodes and relationships for deduplication (used in LLM prompt)
        if self._skip_neo4j:
            existing_nodes: List[Node] = []
            existing_relationships: List[Relationship] = []
        else:
            existing_nodes = await list_nodes(session_id)
            existing_relationships = await list_relationships(session_id)
        
        logger.debug(
            "builder.existing_loaded session=%s chunk=%s nodes=%d rels=%d",
            session_id, chunk.id, len(existing_nodes), len(existing_relationships),
        )

        # 2. Run Builder LLM
        agent_result = await self._invoke_with_retry(existing_nodes, existing_relationships, chunk)
        llm_ms = agent_result.llm_duration_ms
        
        logger.info(
            "builder.llm_complete session=%s chunk=%s nodes=%d rels=%d",
            session_id, chunk.id,
            len(agent_result.nodes),
            len(agent_result.relationships),
        )

        # 3. Pre-creation similarity check OR legacy persist (ADR-011)
        if self._skip_neo4j:
            # Skip all persistence in test mode
            new_nodes = agent_result.nodes
            matched_nodes: List[Node] = []
            label_to_id: dict[str, str] = {n.label.lower(): n.id for n in new_nodes}
        elif settings.similarity_check_enabled:
            # NEW: Pre-creation similarity check
            check_results = await self._check_similarity_and_persist(
                session_id, agent_result.nodes, chunk.start_time
            )
            new_nodes = [r.node for r in check_results if not r.is_match]
            matched_nodes = [r.node for r in check_results if r.is_match]
            # Build label-to-id mapping for relationship rewiring
            label_to_id = {r.original_label.lower(): r.node.id for r in check_results}
        else:
            # LEGACY: Create all nodes as GHOST (Gardener handles deduplication)
            await self._populate_embeddings(agent_result.nodes)
            new_nodes = await self._persist_nodes(session_id, agent_result.nodes)
            matched_nodes = []
            label_to_id = {n.label.lower(): n.id for n in new_nodes}

        # 4. Resolve and persist relationships using canonical node IDs
        resolved_rels = self._resolve_relationships(
            agent_result.relationships, label_to_id, existing_nodes
        )
        if self._skip_neo4j:
            persisted_rels = resolved_rels
        else:
            persisted_rels = await self._persist_relationships(session_id, resolved_rels)
            await save_chunk(chunk)

        # 5. Broadcast SSE events
        await self._broadcast_nodes(session_id, new_nodes)
        await self._broadcast_matched_nodes(session_id, matched_nodes)
        await self._broadcast_relationships(session_id, persisted_rels)
        await self._broadcast_success(session_id, chunk.id)

        # 6. Publish to Redis (triggers Gardener)
        all_nodes = new_nodes + matched_nodes
        await self._publish_to_redis(
            session_id, chunk,
            nodes_created=len(new_nodes),
            rels_created=len(persisted_rels),
        )

        elapsed_ms = (perf_counter() - start) * 1000
        
        logger.info(
            "builder.complete session=%s chunk=%s new=%d matched=%d elapsed_ms=%.0f llm_ms=%.0f",
            session_id, chunk.id, len(new_nodes), len(matched_nodes), elapsed_ms, llm_ms,
        )

        return BuilderResult(
            nodes=all_nodes,
            relationships=persisted_rels,
            llm_duration_ms=llm_ms,
            total_duration_ms=elapsed_ms,
        )

    async def _invoke_with_retry(
        self,
        existing_nodes: Sequence[Node],
        existing_relationships: Sequence[Relationship],
        chunk: TranscriptChunk,
        max_retries: int = 2,
    ) -> BuilderAgentResult:
        """Invoke Builder with retry on parse errors."""
        last_error: BuilderAgentError | None = None
        
        for attempt in range(max_retries):
            try:
                return await self._agent.build(
                    chunk_text=chunk.text,
                    chunk_timestamp=chunk.start_time,
                    existing_nodes=existing_nodes,
                    existing_relationships=existing_relationships,
                )
            except BuilderAgentError as exc:
                last_error = exc
                if exc.code == "invalid_payload" and attempt < max_retries - 1:
                    logger.warning(
                        "builder.parse_retry session=%s chunk=%s attempt=%d",
                        chunk.session_id, chunk.id, attempt + 1,
                    )
                    continue
                raise
        
        raise last_error if last_error else BuilderAgentError("Builder failed")

    async def _populate_embeddings(self, nodes: List[Node]) -> None:
        """Generate embeddings for all nodes."""
        if is_fake_embeddings_enabled():
            for node in nodes:
                node.embedding = None
            return

        tasks = [generate_embedding(node.label) for node in nodes]
        vectors = await asyncio.gather(*tasks)
        for node, vector in zip(nodes, vectors, strict=False):
            node.embedding = vector

    async def _check_similarity_and_persist(
        self,
        session_id: str,
        nodes: List[Node],
        chunk_timestamp: float,
    ) -> List[_SimilarityCheckResult]:
        """Pre-creation similarity check: match or create for each node (ADR-011).
        
        For each extracted node:
        1. Generate embedding
        2. Query vector index for similar nodes
        3. If match (score >= threshold, types compatible, confidence >= 0.7):
           - Increment mentions on existing node
           - Return match result
        4. If no match:
           - Create new GHOST node with embedding
           - Return create result
        """
        settings = get_settings()
        results: List[_SimilarityCheckResult] = []
        
        for node in nodes:
            original_label = node.label
            
            try:
                # Generate embedding
                if is_fake_embeddings_enabled():
                    embedding = None
                else:
                    embedding = await generate_embedding(node.label)
                    node.embedding = embedding
                
                # Query for similar nodes
                candidate = None
                if embedding is not None:
                    candidate = await _query_best_match(
                        session_id, embedding, settings.similarity_top_k
                    )
                
                # Check if we have a match
                is_match = False
                matched_node_for_type_check = None
                if candidate and candidate.score >= settings.similarity_threshold:
                    # Check confidence threshold
                    if node.confidence >= 0.7:
                        # Get existing node for type compatibility check (ADR-013)
                        existing_node = await get_node(session_id, candidate.node_id)
                        if existing_node:
                            matched_node_for_type_check = existing_node
                            # Check type compatibility using embedding similarity
                            is_compatible = await types_compatible(
                                node.inferred_type, existing_node.inferred_type
                            )
                            if is_compatible:
                                is_match = True
                            else:
                                logger.info(
                                    "builder.type_mismatch label=%s type=%s existing_type=%s",
                                    node.label, node.inferred_type, existing_node.inferred_type,
                                )
                
                if is_match and candidate:
                    # Match found - increment mentions on existing node
                    updated_node = await record_node_mention(
                        session_id, candidate.node_id, chunk_timestamp
                    )
                    logger.info(
                        "builder.similarity_match label=%s matched=%s score=%.3f",
                        original_label, candidate.node_id, candidate.score,
                    )
                    results.append(_SimilarityCheckResult(
                        is_match=True,
                        node=updated_node,
                        original_label=original_label,
                    ))
                else:
                    # No match - create new GHOST node
                    created_node = await create_node(session_id, node)
                    logger.debug(
                        "builder.similarity_create label=%s node_id=%s",
                        original_label, created_node.id,
                    )
                    results.append(_SimilarityCheckResult(
                        is_match=False,
                        node=created_node,
                        original_label=original_label,
                    ))
                    
            except Exception as exc:
                # Fallback: create node on any error (Gardener handles edge cases)
                logger.warning(
                    "builder.similarity_check_failed label=%s error=%s, creating anyway",
                    node.label, exc,
                )
                created_node = await create_node(session_id, node)
                results.append(_SimilarityCheckResult(
                    is_match=False,
                    node=created_node,
                    original_label=original_label,
                ))
        
        return results

    def _resolve_relationships(
        self,
        unresolved_relationships: List[UnresolvedRelationship],
        label_to_id: dict[str, str],
        existing_nodes: Sequence[Node],
    ) -> List[Relationship]:
        """Resolve relationship labels to canonical node IDs after similarity checks.
        
        Takes UnresolvedRelationship objects (with labels) and converts them to
        Relationship objects (with node IDs). The label_to_id mapping contains
        the canonical node IDs after similarity matching.
        
        Args:
            unresolved_relationships: Relationships with source/target labels
            label_to_id: Mapping from normalized labels to canonical node IDs
            existing_nodes: Nodes that existed before this chunk (for fallback lookup)
        
        Returns:
            List of fully resolved Relationship objects ready for persistence
        """
        # Build lookup from existing nodes as fallback
        existing_lookup = {n.label.lower(): n.id for n in existing_nodes}
        
        resolved: List[Relationship] = []
        for unresolved in unresolved_relationships:
            source_label = unresolved.source_label.lower()
            target_label = unresolved.target_label.lower()
            
            # Map labels to canonical node IDs (post-similarity-check)
            source_id = label_to_id.get(source_label) or existing_lookup.get(source_label)
            target_id = label_to_id.get(target_label) or existing_lookup.get(target_label)
            
            if source_id and target_id and source_id != target_id:
                # Create resolved relationship with proper node IDs
                relationship = Relationship(
                    id=f"rel_{uuid4().hex}",
                    source_id=source_id,
                    target_id=target_id,
                    category=unresolved.category,
                    description=unresolved.description,
                    confidence=unresolved.confidence,
                    evidence=unresolved.evidence,
                    source=RelationshipSource.BUILDER,
                    created_at=unresolved.created_at,
                )
                resolved.append(relationship)
            else:
                logger.debug(
                    "builder.relationship_skipped source=%s target=%s (missing node)",
                    unresolved.source_label, unresolved.target_label,
                )
        
        return resolved

    async def _broadcast_matched_nodes(
        self,
        session_id: str,
        nodes: List[Node],
    ) -> None:
        """Broadcast node_updated SSE events for matched nodes."""
        for node in nodes:
            await sse_manager.broadcast(session_id, NodeUpdatedEvent(payload=node))

    async def _persist_nodes(self, session_id: str, nodes: List[Node]) -> List[Node]:
        """Persist nodes to Neo4j."""
        persisted: List[Node] = []
        for node in nodes:
            persisted.append(await create_node(session_id, node))
        return persisted

    async def _persist_relationships(
        self,
        session_id: str,
        relationships: List[Relationship],
    ) -> List[Relationship]:
        """Persist relationships to Neo4j."""
        persisted: List[Relationship] = []
        for rel in relationships:
            try:
                persisted.append(await create_relationship(session_id, rel))
            except RuntimeError as e:
                logger.error(
                    "builder.relationship_failed id=%s source=%s target=%s error=%s",
                    rel.id, rel.source_id, rel.target_id, e,
                )
                raise
        return persisted

    async def _broadcast_nodes(self, session_id: str, nodes: List[Node]) -> None:
        """Broadcast node_added SSE events."""
        for node in nodes:
            await sse_manager.broadcast(session_id, NodeAddedEvent(payload=node))

    async def _broadcast_relationships(
        self,
        session_id: str,
        relationships: List[Relationship],
    ) -> None:
        """Broadcast relationship_added SSE events."""
        for rel in relationships:
            await sse_manager.broadcast(session_id, RelationshipAddedEvent(payload=rel))

    async def _broadcast_success(self, session_id: str, chunk_id: str) -> None:
        """Broadcast chunk_processed success event."""
        await sse_manager.broadcast(
            session_id,
            ChunkProcessedEvent(
                payload=ChunkProcessedPayload(chunk_id=chunk_id, error=None)
            ),
        )

    async def _broadcast_error(
        self,
        session_id: str,
        chunk_id: str,
        error: str,
    ) -> None:
        """Broadcast chunk_processed error event."""
        await sse_manager.broadcast(
            session_id,
            ChunkProcessedEvent(
                payload=ChunkProcessedPayload(chunk_id=chunk_id, error=error)
            ),
        )

    async def _publish_to_redis(
        self,
        session_id: str,
        chunk: TranscriptChunk,
        nodes_created: int,
        rels_created: int,
    ) -> None:
        """Publish chunk.added event to Redis using ratio-based triggering.
        
        Gardener is only triggered every N Builder runs (builder_gardener_ratio).
        This paces Gardener relative to actual work, not time.
        """
        from ..config import get_settings
        settings = get_settings()
        ratio = settings.builder_gardener_ratio
        
        # Increment Builder run counter for this session
        self._builder_runs[session_id] = self._builder_runs.get(session_id, 0) + 1
        current_count = self._builder_runs[session_id]
        
        # Only publish (trigger Gardener) when ratio threshold is reached
        if current_count >= ratio:
            logger.info(
                "builder.gardener_trigger session=%s after=%d chunks (ratio=%d)",
                session_id, current_count, ratio,
            )
            try:
                await publish_chunk_added(
                    session_id=session_id,
                    chunk_id=chunk.id,
                    text=chunk.text,
                    nodes_created=nodes_created,
                    relationships_created=rels_created,
                )
                # Reset counter after successful publish
                self._builder_runs[session_id] = 0
            except Exception as exc:
                # Redis failure shouldn't block Builder, but don't reset counter
                logger.warning(
                    "builder.redis_publish_failed session=%s chunk=%s error=%s",
                    session_id, chunk.id, exc,
                )
        else:
            logger.debug(
                "builder.gardener_skipped session=%s count=%d/%d",
                session_id, current_count, ratio,
            )

    def get_builder_count(self, session_id: str) -> int:
        """Get current Builder run count for a session (for debugging)."""
        return self._builder_runs.get(session_id, 0)

    def reset_builder_count(self, session_id: str) -> None:
        """Reset Builder run count for a session (call on session end)."""
        self._builder_runs.pop(session_id, None)

    def get_all_counts(self) -> dict[str, int]:
        """Get all session Builder counts (for debugging)."""
        return dict(self._builder_runs)


class BuilderServiceError(RuntimeError):
    """Raised when Builder service fails."""

    def __init__(self, message: str, *, code: str = "unknown"):
        super().__init__(message)
        self.code = code


class BuilderResult:
    """Result of a successful Builder run."""

    def __init__(
        self,
        *,
        nodes: List[Node],
        relationships: List[Relationship],
        llm_duration_ms: float,
        total_duration_ms: float,
    ):
        self.nodes = nodes
        self.relationships = relationships
        self.llm_duration_ms = llm_duration_ms
        self.total_duration_ms = total_duration_ms


# Module-level singleton for simple usage
_builder_service: BuilderService | None = None


def get_builder_service() -> BuilderService:
    """Get or create the Builder service singleton."""
    global _builder_service
    if _builder_service is None:
        import os
        timeout = float(os.getenv("BUILDER_TASK_TIMEOUT", "90"))
        skip_neo4j = os.getenv("PLASTICFLOWER_SKIP_NEO4J", "").lower() in {"1", "true", "yes"}
        _builder_service = BuilderService(timeout_seconds=timeout, skip_neo4j=skip_neo4j)
    return _builder_service


__all__ = [
    "BuilderService",
    "BuilderServiceError", 
    "BuilderResult",
    "get_builder_service",
]



"""Service layer package (Gate 3 persistence components)."""

from .chunk_store import chunk_store
from .embeddings import EmbeddingError, generate_embedding, is_fake_embeddings_enabled
from .graph_db import (
    create_node,
    get_node,
    update_node,
    delete_node,
    list_nodes,
    record_node_mention,
    create_relationship,
    update_relationship,
    get_relationship,
    delete_relationship,
    list_relationships,
    list_references,
    upsert_flower,
    delete_flower,
    list_flowers,
    fetch_graph_state,
    # Session CRUD (Gate 6)
    create_session_record,
    get_session_record,
    list_session_records,
    update_session_record,
    delete_session_record,
    # Chunk persistence (Gate 6)
    save_chunk,
    list_chunks_for_session,
    delete_chunks_for_session,
)
from .llm import (
    LLMError, 
    generate_structured_json, 
    is_fake_llm_enabled,
    get_call_count,
    reset_call_count,
    get_next_fallback_model,
)
from .graph_schema import ensure_graph_schema
from .neo4j import close_driver, get_driver, run_healthcheck
from .scheduler import GardenerScheduler, gardener_scheduler
from .researcher_service import ResearcherService, researcher_service
from .builder_service import (
    BuilderService,
    BuilderServiceError,
    BuilderResult,
    get_builder_service,
)
from .sse_manager import SSEManager, sse_manager
from .similarity import (
    run_similarity,
    SimilarityResult,
    SimilarityMatchResult,
    SimilarityCreateResult,
)
from .redis_streams import (
    # Connection
    get_redis,
    close_redis,
    redis_health_check,
    # Publishing
    publish_chunk_added,
    publish_gardener_complete,
    publish_node_needs_research,
    # Consuming
    consume_events,
    ack_event,
    # Stream names
    STREAM_CHUNKS_ADDED,
    STREAM_GARDENER_COMPLETE,
    GROUP_GARDENER,
)

__all__ = [
    "close_driver",
    "get_driver",
    "run_healthcheck",
    "ensure_graph_schema",
    "generate_embedding",
    "EmbeddingError",
    "generate_structured_json",
    "LLMError",
    "is_fake_llm_enabled",
    "get_call_count",
    "reset_call_count",
    "get_next_fallback_model",
    "chunk_store",
    "create_node",
    "get_node",
    "update_node",
    "delete_node",
    "list_nodes",
    "record_node_mention",
    "create_relationship",
    "update_relationship",
    "get_relationship",
    "delete_relationship",
    "list_relationships",
    "upsert_flower",
    "delete_flower",
    "list_flowers",
    "fetch_graph_state",
    "run_similarity",
    "SimilarityResult",
    "SimilarityMatchResult",
    "SimilarityCreateResult",
    "gardener_scheduler",
    "GardenerScheduler",
    # Builder service
    "BuilderService",
    "BuilderServiceError",
    "BuilderResult",
    "get_builder_service",
    "sse_manager",
    "SSEManager",
    "is_fake_embeddings_enabled",
    # Session CRUD (Gate 6)
    "create_session_record",
    "get_session_record",
    "list_session_records",
    "update_session_record",
    "delete_session_record",
    # Chunk persistence (Gate 6)
    "save_chunk",
    "list_chunks_for_session",
    "delete_chunks_for_session",
    # Redis Streams (Phase D.5)
    "get_redis",
    "close_redis",
    "redis_health_check",
    "publish_chunk_added",
    "publish_gardener_complete",
    "publish_node_needs_research",
    "consume_events",
    "ack_event",
    "STREAM_CHUNKS_ADDED",
    "STREAM_GARDENER_COMPLETE",
    "GROUP_GARDENER",
    "GROUP_GARDENER",
    "ResearcherService",
    "researcher_service",
]

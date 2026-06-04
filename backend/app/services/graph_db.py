"""Neo4j CRUD helpers for Gate 3 persistence."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from neo4j.graph import Node as Neo4jNode
from neo4j.graph import Relationship as Neo4jRelationship
from neo4j.time import DateTime as Neo4jDateTime

from ..models import (
    Flower,
    GraphState,
    Node,
    NodeStatus,
    Relationship,
    RelationshipCategory,
    RelationshipSource,
    SessionSummary,
    TranscriptChunk,
    ReferenceNode,
)
from .neo4j import get_driver

SESSION_KEY = "session_id"
import json


async def create_node(session_id: str, node: Node) -> Node:
    """Persist a new node under the specified session."""

    driver = await get_driver()
    node_props = _node_to_properties(node, session_id)
    query = """
    CREATE (n:Node)
    SET n = $node
    RETURN n AS node
    """

    async with driver.session() as session:
        async def _work(tx, cypher: str, props: Dict[str, Any]) -> Node:
            result = await tx.run(cypher, node=props)
            record = await result.single()
            if record is None:
                raise RuntimeError("Neo4j did not return created node")
            return _node_from_value(record["node"])

        return await session.execute_write(_work, query, node_props)


async def get_node(session_id: str, node_id: str) -> Optional[Node]:
    """Fetch a single node by id, or None if it does not exist for the session."""

    driver = await get_driver()
    query = """
    MATCH (n:Node {id: $node_id, session_id: $session_id})
    OPTIONAL MATCH (n)-[:BELONGS_TO]->(f:Flower)
    RETURN n AS node, f.id AS flower_id
    """

    async with driver.session() as session:
        async def _work(tx, cypher: str, params: Dict[str, Any]) -> Optional[Node]:
            result = await tx.run(cypher, **params)
            record = await result.single()
            if record is None:
                return None
            node = _node_from_value(record["node"])
            node.flower_id = record.get("flower_id")
            return node

        return await session.execute_read(
            _work, query, {"node_id": node_id, "session_id": session_id}
        )


async def update_node(session_id: str, node: Node) -> Node:
    """Replace a node's stored properties with the provided representation."""

    driver = await get_driver()
    node_props = _node_to_properties(node, session_id)
    query = """
    MATCH (n:Node {id: $node_id, session_id: $session_id})
    SET n = $node
    RETURN n AS node
    """

    async with driver.session() as session:
        async def _work(tx, cypher: str, params: Dict[str, Any]) -> Node:
            result = await tx.run(cypher, **params)
            record = await result.single()
            if record is None:
                raise ValueError(f"Node {params['node_id']} not found")
            return _node_from_value(record["node"])

        params = {"node_id": node.id, "session_id": session_id, "node": node_props}
        return await session.execute_write(_work, query, params)


async def delete_node(session_id: str, node_id: str) -> bool:
    """Remove a node and its attached relationships.
    
    Returns True if node was deleted, False if it didn't exist (idempotent).
    """

    driver = await get_driver()
    query = """
    MATCH (n:Node {id: $node_id, session_id: $session_id})
    DETACH DELETE n
    RETURN count(n) AS deleted
    """

    async with driver.session() as session:
        async def _work(tx, cypher: str, params: Dict[str, Any]) -> int:
            result = await tx.run(cypher, **params)
            record = await result.single()
            return record["deleted"] if record else 0

        deleted = await session.execute_write(_work, query, {"node_id": node_id, "session_id": session_id})
        if deleted == 0:
            _logger.warning("delete_node: node not found session=%s node=%s (already deleted?)", session_id, node_id)
        return deleted > 0


async def set_node_flower(
    session_id: str,
    node_id: str,
    flower_id: Optional[str]
) -> None:
    """
    Assign node to flower via BELONGS_TO relationship.
    If flower_id is None, removes node from any flower.
    """
    driver = await get_driver()
    
    if flower_id is None:
        # Remove from any flower
        query = """
        MATCH (n:Node {id: $node_id, session_id: $session_id})
        OPTIONAL MATCH (n)-[r:BELONGS_TO]->(:Flower)
        DELETE r
        """
        params = {"node_id": node_id, "session_id": session_id}
    else:
        # Set flower membership (replace any existing)
        query = """
        MATCH (n:Node {id: $node_id, session_id: $session_id})
        MATCH (f:Flower {id: $flower_id, session_id: $session_id})
        
        // Remove any existing membership
        OPTIONAL MATCH (n)-[old:BELONGS_TO]->(:Flower)
        DELETE old
        
        // Create new membership
        CREATE (n)-[:BELONGS_TO]->(f)
        """
        params = {
            "node_id": node_id,
            "session_id": session_id,
            "flower_id": flower_id
        }
    
    async with driver.session() as session:
        async def _work(tx, cypher: str, parameters: Dict[str, Any]) -> None:
            result = await tx.run(cypher, **parameters)
            await result.consume()
        
        await session.execute_write(_work, query, params)


async def list_nodes(
    session_id: str,
    *,
    status: Optional[NodeStatus] = None,
    flower_id: Optional[str] = None,
) -> List[Node]:
    """Return all nodes for a session, optionally filtered by status/flower."""
    import logging
    _logger = logging.getLogger(__name__)
    
    # DIAGNOSTIC: Verify session_id is being used correctly
    _logger.debug("list_nodes called with session_id=%s status=%s", session_id, status)

    driver = await get_driver()
    params: Dict[str, Any] = {"session_id": session_id}
    
    if flower_id:
        # Filter by flower membership using relationship
        where_clauses: List[str] = []
        if status:
            where_clauses.append("n.status = $status")
            params["status"] = status.value if isinstance(status, NodeStatus) else status
        
        where_sql = f"AND {' AND '.join(where_clauses)}" if where_clauses else ""
        params["flower_id"] = flower_id
        query = f"""
        MATCH (n:Node {{session_id: $session_id}})-[:BELONGS_TO]->(f:Flower {{id: $flower_id}})
        {where_sql}
        RETURN n AS node, f.id AS flower_id
        ORDER BY n.created_at
        """
    else:
        # List all nodes with optional flower membership
        where_clauses: List[str] = []
        if status:
            where_clauses.append("n.status = $status")
            params["status"] = status.value if isinstance(status, NodeStatus) else status
        
        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        query = f"""
        MATCH (n:Node {{session_id: $session_id}})
        {where_sql}
        OPTIONAL MATCH (n)-[:BELONGS_TO]->(f:Flower)
        RETURN n AS node, f.id AS flower_id
        ORDER BY n.created_at
        """

    async with driver.session() as session:
        async def _work(tx, cypher: str, parameters: Dict[str, Any]) -> List[Node]:
            result = await tx.run(cypher, **parameters)
            nodes: List[Node] = []
            async for record in result:
                node = _node_from_value(record["node"])
                node.flower_id = record.get("flower_id")
                nodes.append(node)
            return nodes

        return await session.execute_read(_work, query, params)


async def record_node_mention(session_id: str, node_id: str, timestamp: float) -> Node:
    """Increment mentions and append a timestamp for a duplicate detection hit."""

    driver = await get_driver()
    query = """
    MATCH (n:Node {id: $node_id, session_id: $session_id})
    SET n.mentions = coalesce(n.mentions, 0) + 1,
        n.timestamps = coalesce(n.timestamps, []) + $new_timestamp
    RETURN n AS node
    """
    params = {
        "node_id": node_id,
        "session_id": session_id,
        "new_timestamp": [timestamp],
    }

    async with driver.session() as session:
        async def _work(tx, cypher: str, parameters: Dict[str, Any]) -> Node:
            result = await tx.run(cypher, **parameters)
            record = await result.single()
            if record is None:
                raise ValueError(f"Node {parameters['node_id']} not found")
            return _node_from_value(record["node"])

        return await session.execute_write(_work, query, params)


async def create_relationship(session_id: str, relationship: Relationship) -> Optional[Relationship]:
    """Persist a relationship between two nodes within the same session.
    
    Returns None if either source or target node doesn't exist (prevents creating corrupt nodes).
    """
    import logging
    _logger = logging.getLogger(__name__)

    driver = await get_driver()
    rel_props = _relationship_to_properties(relationship, session_id)
    # Use MATCH (not MERGE) to prevent creating empty nodes
    query = """
    MATCH (source:Node {id: $source_id, session_id: $session_id})
    MATCH (target:Node {id: $target_id, session_id: $session_id})
    MERGE (source)-[rel:RELATIONSHIP {id: $relationship_id}]->(target)
    SET rel = $relationship
    RETURN rel AS relationship
    """
    params = {
        "source_id": relationship.source_id,
        "target_id": relationship.target_id,
        "relationship_id": relationship.id,
        "session_id": session_id,
        "relationship": rel_props,
    }

    async with driver.session() as session:
        async def _work(tx, cypher: str, parameters: Dict[str, Any]) -> Optional[Relationship]:
            result = await tx.run(cypher, **parameters)
            record = await result.single()
            if record is None:
                # Nodes don't exist - log and return None instead of creating corrupt nodes
                _logger.warning(
                    "relationship.skipped_missing_nodes source=%s target=%s",
                    parameters["source_id"],
                    parameters["target_id"],
                )
                return None
            return _relationship_from_value(record["relationship"])

        return await session.execute_write(_work, query, params)


async def update_relationship(session_id: str, relationship: Relationship) -> Relationship:
    """Replace stored relationship properties."""

    driver = await get_driver()
    rel_props = _relationship_to_properties(relationship, session_id)
    query = """
    MATCH ()-[rel:RELATIONSHIP {id: $relationship_id, session_id: $session_id}]->()
    SET rel = $relationship
    RETURN rel AS relationship
    """
    params = {
        "relationship_id": relationship.id,
        "session_id": session_id,
        "relationship": rel_props,
    }

    async with driver.session() as session:
        async def _work(tx, cypher: str, parameters: Dict[str, Any]) -> Relationship:
            result = await tx.run(cypher, **parameters)
            record = await result.single()
            if record is None:
                raise ValueError(f"Relationship {parameters['relationship_id']} not found")
            return _relationship_from_value(record["relationship"])

        return await session.execute_write(_work, query, params)


async def get_relationship(session_id: str, relationship_id: str) -> Optional[Relationship]:
    """Fetch a relationship by id for the given session."""

    driver = await get_driver()
    query = """
    MATCH ()-[rel:RELATIONSHIP {id: $relationship_id, session_id: $session_id}]->()
    RETURN rel AS relationship
    """
    params = {"relationship_id": relationship_id, "session_id": session_id}

    async with driver.session() as session:
        async def _work(tx, cypher: str, parameters: Dict[str, Any]) -> Optional[Relationship]:
            result = await tx.run(cypher, **parameters)
            record = await result.single()
            if record is None:
                return None
            return _relationship_from_value(record["relationship"])

        return await session.execute_read(_work, query, params)


async def delete_relationship(session_id: str, relationship_id: str) -> None:
    """Delete a relationship by id."""

    driver = await get_driver()
    query = """
    MATCH ()-[rel:RELATIONSHIP {id: $relationship_id, session_id: $session_id}]->()
    DELETE rel
    RETURN count(rel) AS deleted
    """
    params = {"relationship_id": relationship_id, "session_id": session_id}

    async with driver.session() as session:
        async def _work(tx, cypher: str, parameters: Dict[str, Any]) -> None:
            result = await tx.run(cypher, **parameters)
            record = await result.single()
            if not record or record["deleted"] == 0:
                raise ValueError(f"Relationship {parameters['relationship_id']} not found")

        await session.execute_write(_work, query, params)


async def list_relationships(
    session_id: str,
    *,
    category: Optional[RelationshipCategory] = None,
    source: Optional[RelationshipSource] = None,
) -> List[Relationship]:
    """List relationships for a session with optional filters."""

    driver = await get_driver()
    where_clauses: List[str] = []
    params: Dict[str, Any] = {"session_id": session_id}
    if category:
        where_clauses.append("rel.category = $category")
        params["category"] = (
            category.value if isinstance(category, RelationshipCategory) else category
        )
    if source:
        where_clauses.append("rel.source = $source")
        params["source"] = source.value if isinstance(source, RelationshipSource) else source

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    query = f"""
    MATCH ()-[rel:RELATIONSHIP {{session_id: $session_id}}]->()
    {where_sql}
    RETURN rel AS relationship
    ORDER BY rel.created_at
    """

    async with driver.session() as session:
        async def _work(tx, cypher: str, parameters: Dict[str, Any]) -> List[Relationship]:
            result = await tx.run(cypher, **parameters)
            relationships: List[Relationship] = []
            async for record in result:
                relationships.append(_relationship_from_value(record["relationship"]))
            return relationships

        return await session.execute_read(_work, query, params)


async def upsert_flower(session_id: str, flower: Flower) -> Flower:
    """Create or update a Flower node."""

    driver = await get_driver()
    flower_props = _flower_to_properties(flower, session_id)
    query = """
    MERGE (f:Flower {id: $flower_id, session_id: $session_id})
    SET f = $flower
    RETURN f AS flower
    """
    params = {
        "flower_id": flower.id,
        "session_id": session_id,
        "flower": flower_props,
    }

    async with driver.session() as session:
        async def _work(tx, cypher: str, parameters: Dict[str, Any]) -> Flower:
            result = await tx.run(cypher, **parameters)
            record = await result.single()
            if record is None:
                raise RuntimeError("Neo4j did not return upserted Flower")
            return _flower_from_value(record["flower"])

        return await session.execute_write(_work, query, params)


async def delete_flower(session_id: str, flower_id: str) -> None:
    """Delete a Flower node and its BELONGS_TO relationships."""

    driver = await get_driver()
    query = """
    MATCH (f:Flower {id: $flower_id, session_id: $session_id})
    
    // Delete relationships first (explicit cleanup)
    OPTIONAL MATCH (n:Node)-[r:BELONGS_TO]->(f)
    DELETE r
    
    // Then delete flower
    DELETE f
    RETURN count(f) AS deleted
    """
    params = {"flower_id": flower_id, "session_id": session_id}

    async with driver.session() as session:
        async def _work(tx, cypher: str, parameters: Dict[str, Any]) -> None:
            result = await tx.run(cypher, **parameters)
            record = await result.single()
            if not record or record["deleted"] == 0:
                raise ValueError(f"Flower {parameters['flower_id']} not found")

        await session.execute_write(_work, query, params)


async def list_flowers(session_id: str) -> List[Flower]:
    """Return Flower nodes for a session."""

    driver = await get_driver()
    query = """
    MATCH (f:Flower {session_id: $session_id})
    RETURN f AS flower
    ORDER BY f.created_at
    """

    async with driver.session() as session:
        async def _work(tx, cypher: str, parameters: Dict[str, Any]) -> List[Flower]:
            result = await tx.run(cypher, **parameters)
            flowers: List[Flower] = []
            async for record in result:
                flowers.append(_flower_from_value(record["flower"]))
            return flowers

        return await session.execute_read(_work, query, {"session_id": session_id})


async def fetch_graph_state(session_id: str) -> GraphState:
    """Convenience helper returning the combined graph state for a session."""

    nodes, relationships, flowers = await asyncio.gather(
        list_nodes(session_id),
        list_relationships(session_id),
        list_flowers(session_id),
    )
    return GraphState(nodes=nodes, relationships=relationships, flowers=flowers)


def _node_to_properties(node: Node, session_id: str) -> Dict[str, Any]:
    data = node.model_dump()
    data.pop("flower_id", None)  # Never store - it's a relationship now
    if data.get("embedding") is None:
        data.pop("embedding", None)
    data[SESSION_KEY] = session_id
    return data


def _relationship_to_properties(relationship: Relationship, session_id: str) -> Dict[str, Any]:
    data = relationship.model_dump()
    data[SESSION_KEY] = session_id
    return data


def _flower_to_properties(flower: Flower, session_id: str) -> Dict[str, Any]:
    data = flower.model_dump()
    data[SESSION_KEY] = session_id
    return data


def _node_from_value(value: Neo4jNode) -> Node:
    props = dict(value)
    props.pop(SESSION_KEY, None)
    # Exclude embedding from returned data (768 floats per node is expensive)
    props.pop("embedding", None)
    props.setdefault("timestamps", [])
    props["created_at"] = _convert_datetime(props.get("created_at"))
    return Node.model_validate(props)


def _relationship_from_value(value: Neo4jRelationship) -> Relationship:
    props = dict(value)
    props.pop(SESSION_KEY, None)
    props["created_at"] = _convert_datetime(props.get("created_at"))
    return Relationship.model_validate(props)


def _flower_from_value(value: Neo4jNode) -> Flower:
    props = dict(value)
    props.pop(SESSION_KEY, None)
    props["created_at"] = _convert_datetime(props.get("created_at"))
    return Flower.model_validate(props)


def _convert_datetime(value: Any) -> Any:
    if isinstance(value, Neo4jDateTime):
        return value.to_native()
    return value


# -----------------------------------------------------------------------------
# Session CRUD (Gate 6)
# -----------------------------------------------------------------------------


async def create_session_record(
    session_id: str, name: str, created_at: datetime, language_variant: str = "en-GB"
) -> SessionSummary:
    """Create a Session node in Neo4j."""

    driver = await get_driver()
    query = """
    CREATE (s:Session {id: $id, name: $name, language_variant: $language_variant, created_at: $created_at})
    RETURN s AS session
    """
    params = {"id": session_id, "name": name, "language_variant": language_variant, "created_at": created_at}

    async with driver.session() as session:
        async def _work(tx, cypher: str, parameters: Dict[str, Any]) -> SessionSummary:
            result = await tx.run(cypher, **parameters)
            record = await result.single()
            if record is None:
                raise RuntimeError("Neo4j did not return created session")
            return _session_from_value(record["session"])

        return await session.execute_write(_work, query, params)


async def get_session_record(session_id: str) -> Optional[SessionSummary]:
    """Fetch a Session by id, or None if it does not exist."""

    driver = await get_driver()
    query = """
    MATCH (s:Session {id: $id})
    RETURN s AS session
    """

    async with driver.session() as session:
        async def _work(tx, cypher: str, parameters: Dict[str, Any]) -> Optional[SessionSummary]:
            result = await tx.run(cypher, **parameters)
            record = await result.single()
            if record is None:
                return None
            return _session_from_value(record["session"])

        return await session.execute_read(_work, query, {"id": session_id})


async def list_session_records() -> List[SessionSummary]:
    """List all Session nodes ordered by creation time (newest first)."""

    driver = await get_driver()
    query = """
    MATCH (s:Session)
    RETURN s AS session
    ORDER BY s.created_at DESC
    """

    async with driver.session() as session:
        async def _work(tx, cypher: str) -> List[SessionSummary]:
            result = await tx.run(cypher)
            sessions: List[SessionSummary] = []
            async for record in result:
                sessions.append(_session_from_value(record["session"]))
            return sessions

        return await session.execute_read(_work, query)


async def update_session_record(
    session_id: str,
    *,
    name: Optional[str] = None,
    ended_at: Optional[datetime] = None,
) -> SessionSummary:
    """Update Session properties (name and/or ended_at)."""

    driver = await get_driver()
    set_clauses: List[str] = []
    params: Dict[str, Any] = {"id": session_id}

    if name is not None:
        set_clauses.append("s.name = $name")
        params["name"] = name
    if ended_at is not None:
        set_clauses.append("s.ended_at = $ended_at")
        params["ended_at"] = ended_at

    if not set_clauses:
        # Nothing to update, just fetch and return
        existing = await get_session_record(session_id)
        if existing is None:
            raise ValueError(f"Session {session_id} not found")
        return existing

    query = f"""
    MATCH (s:Session {{id: $id}})
    SET {', '.join(set_clauses)}
    RETURN s AS session
    """

    async with driver.session() as session:
        async def _work(tx, cypher: str, parameters: Dict[str, Any]) -> SessionSummary:
            result = await tx.run(cypher, **parameters)
            record = await result.single()
            if record is None:
                raise ValueError(f"Session {parameters['id']} not found")
            return _session_from_value(record["session"])

        return await session.execute_write(_work, query, params)


async def delete_session_record(session_id: str) -> None:
    """Delete a Session and all associated data (nodes, relationships, flowers, chunks)."""

    driver = await get_driver()

    # Delete in order: relationships first, then nodes, flowers, chunks, session
    queries = [
        # Delete relationships for session
        """
        MATCH ()-[r:RELATIONSHIP {session_id: $session_id}]->()
        DELETE r
        """,
        # Delete nodes for session
        """
        MATCH (n:Node {session_id: $session_id})
        DETACH DELETE n
        """,
        # Delete flowers for session
        """
        MATCH (f:Flower {session_id: $session_id})
        DELETE f
        """,
        # Delete chunks for session
        """
        MATCH (c:TranscriptChunk {session_id: $session_id})
        DELETE c
        """,
        # Delete session itself
        """
        MATCH (s:Session {id: $session_id})
        DELETE s
        """,
    ]

    async with driver.session() as session:
        async def _work(tx, cypher_list: List[str], parameters: Dict[str, Any]) -> None:
            for cypher in cypher_list:
                result = await tx.run(cypher, **parameters)
                await result.consume()

        await session.execute_write(_work, queries, {"session_id": session_id})


def _session_from_value(value: Neo4jNode) -> SessionSummary:
    """Convert Neo4j Session node to SessionSummary model."""
    props = dict(value)
    props["created_at"] = _convert_datetime(props.get("created_at"))
    props["ended_at"] = _convert_datetime(props.get("ended_at"))
    # Default for sessions created before language_variant was added
    if "language_variant" not in props:
        props["language_variant"] = "en-GB"
    return SessionSummary.model_validate(props)


# -----------------------------------------------------------------------------
# Transcript Chunk Persistence (Gate 6)
# -----------------------------------------------------------------------------


async def save_chunk(chunk: TranscriptChunk) -> TranscriptChunk:
    """Persist a TranscriptChunk to Neo4j and link to Session.
    
    Raises:
        ValueError: If the session does not exist.
        RuntimeError: If Neo4j fails to create the chunk.
    """

    driver = await get_driver()
    chunk_props = chunk.model_dump()
    query = """
    MATCH (s:Session {id: $session_id})
    MERGE (c:TranscriptChunk {id: $chunk_id})
    ON CREATE SET c = $chunk
    ON MATCH SET c = $chunk
    MERGE (s)-[:HAS_CHUNK]->(c)
    RETURN c AS chunk
    """
    params = {"session_id": chunk.session_id, "chunk_id": chunk.id, "chunk": chunk_props}

    async with driver.session() as session:
        async def _work(tx, cypher: str, parameters: Dict[str, Any]) -> TranscriptChunk:
            result = await tx.run(cypher, **parameters)
            record = await result.single()
            if record is None:
                raise ValueError(
                    f"Session {parameters['session_id']} not found - cannot save chunk. "
                    "Ensure session is created before submitting chunks."
                )
            return _chunk_from_value(record["chunk"])

        return await session.execute_write(_work, query, params)


async def list_chunks_for_session(session_id: str) -> List[TranscriptChunk]:
    """List all TranscriptChunks for a session, ordered by start_time."""

    driver = await get_driver()
    query = """
    MATCH (c:TranscriptChunk {session_id: $session_id})
    RETURN c AS chunk
    ORDER BY c.start_time
    """

    async with driver.session() as session:
        async def _work(tx, cypher: str, parameters: Dict[str, Any]) -> List[TranscriptChunk]:
            result = await tx.run(cypher, **parameters)
            chunks: List[TranscriptChunk] = []
            async for record in result:
                chunks.append(_chunk_from_value(record["chunk"]))
            return chunks

        return await session.execute_read(_work, query, {"session_id": session_id})


async def get_chunks_after(
    session_id: str, 
    after_chunk_id: Optional[str] = None, 
    limit: int = 10
) -> List[TranscriptChunk]:
    """Get TranscriptChunks after a given chunk ID (for incremental proofreading).
    
    Args:
        session_id: Session to query
        after_chunk_id: Return chunks created after this one (by start_time).
                       If None, returns the first `limit` chunks.
        limit: Maximum number of chunks to return (default: 10)
    
    Returns:
        List of TranscriptChunks ordered by start_time.
    """
    driver = await get_driver()
    
    if after_chunk_id:
        # Get chunks after the specified one
        query = """
        MATCH (ref:TranscriptChunk {id: $after_chunk_id, session_id: $session_id})
        MATCH (c:TranscriptChunk {session_id: $session_id})
        WHERE c.start_time > ref.start_time
        RETURN c AS chunk
        ORDER BY c.start_time
        LIMIT $limit
        """
        params = {
            "session_id": session_id,
            "after_chunk_id": after_chunk_id,
            "limit": limit,
        }
    else:
        # Get first N chunks
        query = """
        MATCH (c:TranscriptChunk {session_id: $session_id})
        RETURN c AS chunk
        ORDER BY c.start_time
        LIMIT $limit
        """
        params = {"session_id": session_id, "limit": limit}

    async with driver.session() as session:
        async def _work(tx, cypher: str, parameters: Dict[str, Any]) -> List[TranscriptChunk]:
            result = await tx.run(cypher, **parameters)
            chunks: List[TranscriptChunk] = []
            async for record in result:
                chunks.append(_chunk_from_value(record["chunk"]))
            return chunks

        return await session.execute_read(_work, query, params)


async def delete_chunks_for_session(session_id: str) -> None:
    """Delete all TranscriptChunks for a session."""

    driver = await get_driver()
    query = """
    MATCH (c:TranscriptChunk {session_id: $session_id})
    DELETE c
    """

    async with driver.session() as session:
        async def _work(tx, cypher: str, parameters: Dict[str, Any]) -> None:
            result = await tx.run(cypher, **parameters)
            await result.consume()

        await session.execute_write(_work, query, {"session_id": session_id})


def _chunk_from_value(value: Neo4jNode) -> TranscriptChunk:
    """Convert Neo4j TranscriptChunk node to model."""
    props = dict(value)
    return TranscriptChunk.model_validate(props)


async def get_chunk(chunk_id: str) -> Optional[TranscriptChunk]:
    """Fetch a single chunk by id, or None if it does not exist."""

    driver = await get_driver()
    query = """
    MATCH (c:TranscriptChunk {id: $chunk_id})
    RETURN c AS chunk
    """

    async with driver.session() as session:
        async def _work(tx, cypher: str, parameters: Dict[str, Any]) -> Optional[TranscriptChunk]:
            result = await tx.run(cypher, **parameters)
            record = await result.single()
            if record is None:
                return None
            return _chunk_from_value(record["chunk"])

        return await session.execute_read(_work, query, {"chunk_id": chunk_id})


async def get_recent_transcript(session_id: str, word_limit: int = 3000) -> str:
    """Fetch recent chunks and concatenate text up to word_limit.
    
    Returns most recent transcript content in chronological order.
    
    Optimisation: Uses LIMIT to prevent Neo4j over-planning.
    Conservative estimate of 20 words/chunk ensures we never under-fetch.
    (Actual average is ~60 words/chunk based on production data.)
    """
    driver = await get_driver()
    
    # Calculate chunk limit: conservative 20 words/chunk, cap at 500 chunks
    chunk_limit = min((word_limit // 20) + 10, 500)
    
    query = """
    MATCH (c:TranscriptChunk {session_id: $session_id})
    RETURN c.text AS text, c.start_time AS start_time
    ORDER BY c.start_time DESC
    LIMIT $chunk_limit
    """
    
    async with driver.session() as session:
        async def _work(tx, cypher: str, parameters: Dict[str, Any]) -> str:
            result = await tx.run(cypher, **parameters)
            chunks: List[str] = []
            word_count = 0
            
            async for record in result:
                text = record["text"]
                words = text.split()
                if word_count + len(words) > word_limit:
                    # Take partial chunk to reach limit
                    remaining = word_limit - word_count
                    chunks.append(" ".join(words[:remaining]))
                    break
                chunks.append(text)
                word_count += len(words)
            
            # Reverse to chronological order (oldest first)
            return " ".join(reversed(chunks))
        
        return await session.execute_read(
            _work, query, {"session_id": session_id, "chunk_limit": chunk_limit}
        )


async def get_session_vocabulary(session_id: str) -> Optional[Dict[str, str]]:
    """
    Load session vocabulary corrections map.
    
    Returns dict of {phonetic_error: correct_term} or None if no vocabulary exists.
    Corrections are stored as JSON string in Neo4j (Maps not supported as properties).
    """
    import json
    
    driver = await get_driver()
    query = """
    MATCH (v:SessionVocabulary {session_id: $session_id})
    RETURN v.corrections_json as corrections_json
    """
    
    async with driver.session() as session:
        async def _work(tx, cypher: str, params: Dict[str, Any]):
            result = await tx.run(cypher, **params)
            record = await result.single()
            if not record or not record["corrections_json"]:
                return None
            try:
                return json.loads(record["corrections_json"])
            except json.JSONDecodeError:
                return None
        
        return await session.execute_read(_work, query, {"session_id": session_id})


async def update_session_vocabulary(
    session_id: str, 
    corrections: Dict[str, str],
    language_variant: str = "en-GB"
) -> None:
    """
    Update session vocabulary with new corrections.
    
    Merges with existing corrections (doesn't overwrite).
    Stores as JSON string (Neo4j properties don't support Maps).
    """
    import json
    
    # First load existing corrections
    existing = await get_session_vocabulary(session_id) or {}
    
    # Merge new corrections into existing
    merged = {**existing, **corrections}
    merged_json = json.dumps(merged)
    
    driver = await get_driver()
    query = """
    MERGE (v:SessionVocabulary {session_id: $session_id})
    SET v.corrections_json = $corrections_json,
        v.language_variant = $language_variant,
        v.updated_at = datetime()
    """
    
    async with driver.session() as session:
        async def _work(tx, cypher: str, params: Dict[str, Any]):
            result = await tx.run(cypher, **params)
            await result.consume()
        
        await session.execute_write(
            _work, 
            query, 
            {
                "session_id": session_id,
                "corrections_json": merged_json,
                "language_variant": language_variant
            }
        )


async def get_proofread_checkpoint(session_id: str) -> Optional[str]:
    """
    Get the ID of the last proofread TranscriptChunk for this session.
    
    Returns None if no proofreading has been done yet.
    """
    driver = await get_driver()
    query = """
    MATCH (p:ProofreadCheckpoint {session_id: $session_id})
    RETURN p.last_chunk_id as last_chunk_id
    """
    
    async with driver.session() as session:
        async def _work(tx, cypher: str, params: Dict[str, Any]):
            result = await tx.run(cypher, **params)
            record = await result.single()
            return record["last_chunk_id"] if record else None
        
        return await session.execute_read(_work, query, {"session_id": session_id})


async def update_proofread_checkpoint(session_id: str, last_chunk_id: str) -> None:
    """Update the proofread checkpoint to the given chunk ID."""
    driver = await get_driver()
    query = """
    MERGE (p:ProofreadCheckpoint {session_id: $session_id})
    SET p.last_chunk_id = $last_chunk_id,
        p.last_run = datetime(),
        p.chunks_processed = coalesce(p.chunks_processed, 0) + 1
    """
    
    async with driver.session() as session:
        async def _work(tx, cypher: str, params: Dict[str, Any]):
            result = await tx.run(cypher, **params)
            await result.consume()
        
        await session.execute_write(
            _work,
            query,
            {"session_id": session_id, "last_chunk_id": last_chunk_id}
        )


async def get_session_context(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the session context for incremental proofreading.
    
    Returns None if no context has been stored yet.
    """
    driver = await get_driver()
    query = """
    MATCH (c:SessionContext {session_id: $session_id})
    RETURN c.theme_summary AS theme_summary,
           c.key_entities AS key_entities,
           c.speaker_names AS speaker_names,
           c.domain_terms AS domain_terms
    """
    
    async with driver.session() as session:
        async def _work(tx, cypher: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            result = await tx.run(cypher, **params)
            record = await result.single()
            if record is None:
                return None
            return {
                "theme_summary": record["theme_summary"] or "",
                "key_entities": record["key_entities"] or [],
                "speaker_names": record["speaker_names"] or [],
                "domain_terms": record["domain_terms"] or [],
            }
        
        return await session.execute_read(_work, query, {"session_id": session_id})


async def update_session_context(
    session_id: str,
    *,
    theme_summary: Optional[str] = None,
    key_entities: Optional[List[str]] = None,
    speaker_names: Optional[List[str]] = None,
    domain_terms: Optional[List[str]] = None,
) -> None:
    """
    Update the session context with new or additional information.
    
    Lists are merged with existing values (no duplicates).
    Theme summary is replaced if provided.
    """
    driver = await get_driver()
    
    # Build SET clause dynamically based on provided values
    set_clauses = ["c.updated_at = datetime()"]
    params: Dict[str, Any] = {"session_id": session_id}
    
    if theme_summary is not None:
        set_clauses.append("c.theme_summary = $theme_summary")
        params["theme_summary"] = theme_summary
    
    if key_entities is not None:
        # Merge with existing (unique values only)
        set_clauses.append(
            "c.key_entities = [x IN coalesce(c.key_entities, []) + $key_entities WHERE x IS NOT NULL | x]"
        )
        params["key_entities"] = key_entities
    
    if speaker_names is not None:
        set_clauses.append(
            "c.speaker_names = [x IN coalesce(c.speaker_names, []) + $speaker_names WHERE x IS NOT NULL | x]"
        )
        params["speaker_names"] = speaker_names
    
    if domain_terms is not None:
        set_clauses.append(
            "c.domain_terms = [x IN coalesce(c.domain_terms, []) + $domain_terms WHERE x IS NOT NULL | x]"
        )
        params["domain_terms"] = domain_terms
    
    query = f"""
    MERGE (c:SessionContext {{session_id: $session_id}})
    SET {", ".join(set_clauses)}
    """
    
    async with driver.session() as session:
        async def _work(tx, cypher: str, parameters: Dict[str, Any]) -> None:
            result = await tx.run(cypher, **parameters)
            await result.consume()
        
        await session.execute_write(_work, query, params)


async def apply_corrections_to_graph(
    session_id: str,
    corrections: List[tuple[str, str]]
) -> Dict[str, Any]:
    """
    Apply corrections to node labels, relationship descriptions, and transcript chunks.
    
    Args:
        session_id: Session to apply corrections in
        corrections: List of (original_text, corrected_text) tuples
    
    Returns:
        Dict with counts and affected IDs: 
        {nodes_updated, relationships_updated, chunks_updated, affected_node_ids}
    """
    driver = await get_driver()
    counts: Dict[str, Any] = {
        "nodes_updated": 0, 
        "relationships_updated": 0, 
        "chunks_updated": 0,
        "affected_node_ids": [],
    }
    
    for original, corrected in corrections:
        # Update node labels and collect affected IDs (case-insensitive)
        node_query = """
        MATCH (n:Node {session_id: $session_id})
        WHERE toLower(n.label) = toLower($original)
        SET n.label = $corrected
        RETURN n.id as node_id
        """
        
        # Update relationship descriptions (contains match)
        rel_query = """
        MATCH ()-[r:RELATIONSHIP]->()
        WHERE r.session_id = $session_id
          AND r.description CONTAINS $original
        SET r.description = replace(r.description, $original, $corrected)
        RETURN count(r) as updated
        """
        
        # Update transcript chunk text (preserve original_text for audit)
        chunk_query = """
        MATCH (c:TranscriptChunk {session_id: $session_id})
        WHERE c.text CONTAINS $original
        SET c.original_text = coalesce(c.original_text, c.text),
            c.text = replace(c.text, $original, $corrected)
        RETURN count(c) as updated
        """
        
        async with driver.session() as session:
            # Node update - collect IDs
            async def _node_work(tx, cypher: str, params: Dict[str, Any]):
                result = await tx.run(cypher, **params)
                node_ids = []
                async for record in result:
                    node_ids.append(record["node_id"])
                return node_ids
            
            async def _count_work(tx, cypher: str, params: Dict[str, Any]):
                result = await tx.run(cypher, **params)
                record = await result.single()
                return record["updated"] if record else 0
            
            affected_ids = await session.execute_write(
                _node_work, node_query, 
                {"session_id": session_id, "original": original, "corrected": corrected}
            )
            counts["nodes_updated"] += len(affected_ids)
            counts["affected_node_ids"].extend(affected_ids)
            
            counts["relationships_updated"] += await session.execute_write(
                _count_work, rel_query,
                {"session_id": session_id, "original": original, "corrected": corrected}
            )
            counts["chunks_updated"] += await session.execute_write(
                _count_work, chunk_query,
                {"session_id": session_id, "original": original, "corrected": corrected}
            )
    
    return counts


async def apply_temporal_decay(session_id: str, threshold_minutes: int = 5) -> int:
    """
    Mark nodes older than threshold as LEGACY status for visual de-emphasis.
    
    Nodes are considered "old" if their last_active timestamp (or created_at if no
    last_active) is more than threshold_minutes ago.
    
    Args:
        session_id: Session to apply decay in
        threshold_minutes: Minutes after which nodes become LEGACY (default 5)
    
    Returns:
        Number of nodes transitioned to LEGACY status
    """
    driver = await get_driver()
    
    query = """
    MATCH (n:Node {session_id: $session_id})
    WHERE n.status = 'solid'
      AND (
        (n.last_active IS NOT NULL AND n.last_active < datetime() - duration({minutes: $threshold}))
        OR (n.last_active IS NULL AND n.created_at < datetime() - duration({minutes: $threshold}))
      )
    SET n.status = 'legacy'
    RETURN count(n) as decayed_count
    """
    
    async with driver.session() as session:
        async def _work(tx, cypher: str, params: Dict[str, Any]) -> int:
            result = await tx.run(cypher, **params)
            record = await result.single()
            return record["decayed_count"] if record else 0
        
        return await session.execute_write(
            _work, query, {"session_id": session_id, "threshold": threshold_minutes}
        )


# -----------------------------------------------------------------------------
# Reference (Researcher) CRUD
# -----------------------------------------------------------------------------

async def create_reference(session_id: str, reference: ReferenceNode) -> ReferenceNode:
    """Persist a new reference node and link it to the graph node.
    
    Refactored in Phase 5.2 to support (:Source) nodes.
    """
    driver = await get_driver()
    
    # Serialize complex types
    props = reference.model_dump(exclude={"sources"})

    
    # Convert enums to strings
    if "entity_type" in props:
        props["entity_type"] = props["entity_type"].value
    if "search_provider" in props:
        props["search_provider"] = props["search_provider"].value
        
    query = """
    MATCH (n:Node {id: $node_id, session_id: $session_id})
    CREATE (r:Reference)
    SET r = $props
    CREATE (n)-[:HAS_REFERENCE]->(r)
    
    WITH r
    UNWIND $sources AS source_data
    MERGE (s:Source {url: source_data.url})
    ON CREATE SET s.title = source_data.title, s.content = source_data.content
    MERGE (r)-[:CITED_BY]->(s)
    
    RETURN r
    """
    
    # Prepare sources list for UNWIND
    sources_data = [s.model_dump() for s in reference.sources]
    
    async with driver.session() as session:
        async def _work(tx, cypher: str, params: Dict[str, Any]) -> ReferenceNode:
            result = await tx.run(cypher, **params)
            record = await result.single()
            if record is None:
                raise RuntimeError(f"Failed to create Reference for node {params['node_id']}")
            
            # Since we return just 'r', we need to re-attach sources for the return object
            # Ideally we query them back or just trust inputs. 
            # Trusting inputs for now to match interface.
            return reference

        return await session.execute_write(
            _work, query, {
                "session_id": session_id, 
                "node_id": reference.node_id, 
                "props": props,
                "sources": sources_data
            }
        )


async def get_reference(session_id: str, node_id: str) -> Optional[ReferenceNode]:
    """Get the reference associated with a node, if any.
    
    Refactored in Phase 5.2 to fetch linked (:Source) nodes.
    """
    driver = await get_driver()
    query = """
    MATCH (n:Node {id: $node_id, session_id: $session_id})-[:HAS_REFERENCE]->(r:Reference)
    OPTIONAL MATCH (r)-[:CITED_BY]->(s:Source)
    RETURN r, collect(s) AS sources
    """
    
    async with driver.session() as session:
        async def _work(tx, cypher: str, params: Dict[str, Any]) -> Optional[ReferenceNode]:
            result = await tx.run(cypher, **params)
            record = await result.single()
            if record is None:
                return None
            
            reference_node = record["r"]
            sources_nodes = record["sources"]
            
            return _reference_from_value(reference_node, sources_nodes)

        return await session.execute_read(
            _work, query, {"session_id": session_id, "node_id": node_id}
        )


def _reference_from_value(node: Neo4jNode, sources: List[Neo4jNode] = None) -> ReferenceNode:
    """Convert Neo4j node to ReferenceNode model."""
    props = dict(node)
    
    # Phase 5.2 Migration Support
    # If "sources_json" exists (legacy), use it.
    # If `sources` arg is provided (new), use it.
    
    from ..models import ReferenceSource

    source_objects = []
    
    
    # Strictly use new Graph Schema (Phase 5.2+)
    if sources:
        for s in sources:
            s_props = dict(s)
            source_objects.append(ReferenceSource(**s_props))
            
    props["sources"] = source_objects
    
    return ReferenceNode(**props)


async def list_references(session_id: str) -> List[ReferenceNode]:
    """List all references for a session (Gate 6 Librarian)."""
    driver = await get_driver()
    query = """
    MATCH (n:Node {session_id: $session_id})-[:HAS_REFERENCE]->(r:Reference)
    OPTIONAL MATCH (r)-[:CITED_BY]->(s:Source)
    RETURN r, collect(s) AS sources
    """

    async with driver.session() as session:
        async def _work(tx, cypher: str, params: Dict[str, Any]) -> List[ReferenceNode]:
            result = await tx.run(cypher, **params)
            references: List[ReferenceNode] = []
            async for record in result:
                references.append(_reference_from_value(record["r"], record["sources"]))
            return references

        return await session.execute_read(_work, query, {"session_id": session_id})


__all__ = [
    "create_reference",
    "get_reference",
    "list_references",
    "create_node",
    "get_node",
    "update_node",
    "delete_node",
    "list_nodes",
    "record_node_mention",
    "set_node_flower",
    "create_relationship",
    "update_relationship",
    "get_relationship",
    "delete_relationship",
    "list_relationships",
    "upsert_flower",
    "delete_flower",
    "list_flowers",
    "fetch_graph_state",
    # Session CRUD (Gate 6)
    "create_session_record",
    "get_session_record",
    "list_session_records",
    "update_session_record",
    "delete_session_record",
    # Chunk persistence (Gate 6)
    "save_chunk",
    "get_chunk",
    "list_chunks_for_session",
    "get_chunks_after",
    "delete_chunks_for_session",
    # Chunk transcript retrieval (Gate 7)
    "get_recent_transcript",
    # Vocabulary and proofreading (Phase D)
    "get_session_vocabulary",
    "apply_temporal_decay",
    "update_session_vocabulary",
    "get_proofread_checkpoint",
    "update_proofread_checkpoint",
    "get_session_context",
    "update_session_context",
    "apply_corrections_to_graph",
]

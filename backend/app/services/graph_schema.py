"""Neo4j schema + vector index enforcement helpers for Gate 3.

All statements are idempotent so the FastAPI startup hook can call them on
every boot without risking failures.
"""

from __future__ import annotations

import logging
from typing import Iterable

from neo4j import AsyncDriver

from ..config import get_settings

logger = logging.getLogger(__name__)

NODE_EMBEDDING_INDEX = "node_embedding_index"

CONSTRAINT_QUERIES: tuple[tuple[str, str], ...] = (
    (
        "node_id_unique",
        "CREATE CONSTRAINT node_id_unique IF NOT EXISTS FOR (n:Node) REQUIRE n.id IS UNIQUE",
    ),
    (
        "relationship_id_unique",
        "CREATE CONSTRAINT relationship_id_unique IF NOT EXISTS FOR ()-[r:RELATIONSHIP]->() "
        "REQUIRE r.id IS UNIQUE",
    ),
    (
        "flower_id_unique",
        "CREATE CONSTRAINT flower_id_unique IF NOT EXISTS FOR (f:Flower) REQUIRE f.id IS UNIQUE",
    ),
    (
        "session_id_unique",
        "CREATE CONSTRAINT session_id_unique IF NOT EXISTS FOR (s:Session) REQUIRE s.id IS UNIQUE",
    ),
    (
        "chunk_id_unique",
        "CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS FOR (c:TranscriptChunk) REQUIRE c.id IS UNIQUE",
    ),
)


async def ensure_graph_schema(driver: AsyncDriver) -> None:
    """Ensure unique constraints and vector index exist."""

    await _apply_statements(driver, CONSTRAINT_QUERIES)
    await _ensure_vector_index(driver)


async def _apply_statements(
    driver: AsyncDriver, statements: Iterable[tuple[str, str]]
) -> None:
    async def _execute(tx, query: str) -> None:
        result = await tx.run(query)
        await result.consume()

    async with driver.session() as session:
        for name, query in statements:
            await session.execute_write(_execute, query)
            logger.debug("Neo4j schema ensured: %s", name)


async def _ensure_vector_index(driver: AsyncDriver) -> None:
    settings = get_settings()
    query = f"""
CREATE VECTOR INDEX {NODE_EMBEDDING_INDEX} IF NOT EXISTS
FOR (n:Node) ON (n.embedding)
OPTIONS {{
  indexConfig: {{
    `vector.dimensions`: {settings.embedding_dimensions},
    `vector.similarity_function`: '{settings.embedding_similarity_function}'
  }}
}}
"""

    async def _execute(tx, statement: str) -> None:
        result = await tx.run(statement)
        await result.consume()

    async with driver.session() as session:
        await session.execute_write(_execute, query)
        logger.debug("Neo4j schema ensured: %s", NODE_EMBEDDING_INDEX)


__all__ = ["ensure_graph_schema", "NODE_EMBEDDING_INDEX"]

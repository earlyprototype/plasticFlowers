"""Async Neo4j driver management utilities.

Gate 3 requires an operational persistence layer before Builder integration.
This module exposes helper functions to initialise, reuse, health check, and
gracefully shut down the Neo4j AsyncDriver instance.
"""

from __future__ import annotations

from neo4j import AsyncDriver, AsyncGraphDatabase

from ..config import get_settings

_driver: AsyncDriver | None = None


async def get_driver() -> AsyncDriver:
    """Return the global AsyncDriver, creating it lazily on first access."""

    global _driver
    if _driver is None:
        settings = get_settings()
        _driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=settings.neo4j_auth,
            max_connection_pool_size=settings.neo4j_max_connection_pool_size,
            max_connection_lifetime=settings.neo4j_max_connection_lifetime,
        )
    return _driver


async def close_driver() -> None:
    """Close and reset the global AsyncDriver reference (used on shutdown)."""

    global _driver
    if _driver is not None:
        await _driver.close()
        _driver = None


async def run_healthcheck() -> None:
    """Execute a no-op Cypher query to ensure the driver can reach Neo4j."""

    driver = await get_driver()

    async def _ping(tx) -> int:
        result = await tx.run("RETURN 1 AS ok")
        record = await result.single()
        return record["ok"]

    async with driver.session() as session:
        ok_value = await session.execute_read(_ping)
        if ok_value != 1:
            raise RuntimeError("Neo4j healthcheck failed: unexpected response")

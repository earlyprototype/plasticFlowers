"""PlasticFlower backend FastAPI application."""

# Force IPv4 to avoid Windows IPv6 fallback delays (~21s per connection)
import socket
_original_getaddrinfo = socket.getaddrinfo
def _ipv4_only_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    return _original_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
socket.getaddrinfo = _ipv4_only_getaddrinfo

import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from contextlib import asynccontextmanager
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import api_router
from .services import (
    close_driver,
    close_redis,
    ensure_graph_schema,
    gardener_scheduler,
    get_driver,
    get_redis,
    redis_health_check,
    run_healthcheck,
    researcher_service,
)

logger = logging.getLogger(__name__)

_SKIP_NEO4J = os.getenv("PLASTICFLOWER_SKIP_NEO4J", "").strip().lower() in {"1", "true", "yes", "on"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise shared resources (Neo4j driver, Redis) before serving requests."""

    if _SKIP_NEO4J:
        logger.warning("PLASTICFLOWER_SKIP_NEO4J enabled - skipping Neo4j and Gardener startup")
        app.state.neo4j_driver = None
        yield
        return

    # Initialize Neo4j
    driver = await get_driver()
    app.state.neo4j_driver = driver
    await ensure_graph_schema(driver)
    await run_healthcheck()
    
    # Initialize Redis (Phase D.5)
    try:
        redis_client = await get_redis()
        app.state.redis_client = redis_client
        redis_status = await redis_health_check()
        logger.info("redis.startup status=%s", redis_status.get("status"))
    except Exception as exc:
        logger.warning("redis.startup_failed error=%s (continuing without Redis)", exc)
        app.state.redis_client = None
    
    await gardener_scheduler.start()
    await researcher_service.start()
    try:
        yield
    finally:
        await gardener_scheduler.stop()
        await researcher_service.stop()
        await close_redis()
        await close_driver()


app = FastAPI(title="plasticFlower API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["system"])
async def read_health() -> dict[str, str]:
    """Readiness probe that verifies Neo4j connectivity."""

    await run_healthcheck()
    return {"status": "ok"}


# Gate 2 routers -------------------------------------------------------------
app.include_router(api_router)

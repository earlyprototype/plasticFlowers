"""API router wiring for FastAPI application."""

from __future__ import annotations

from fastapi import APIRouter

from . import chunks, export, graph, sessions, stream

api_router = APIRouter(prefix="/api")
api_router.include_router(sessions.router)
api_router.include_router(chunks.router)
api_router.include_router(graph.router)
api_router.include_router(export.router)
api_router.include_router(stream.router)

__all__ = ["api_router"]

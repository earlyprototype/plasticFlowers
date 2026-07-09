"""/health endpoint tests (T7): structured degraded response, skip mode."""

from __future__ import annotations

import json

import pytest

from app import main as main_module


@pytest.mark.asyncio
async def test_health_ok_when_neo4j_reachable(monkeypatch):
    monkeypatch.setattr(main_module, "_SKIP_NEO4J", False)

    async def fake_healthcheck():
        return None

    monkeypatch.setattr(main_module, "run_healthcheck", fake_healthcheck)

    result = await main_module.read_health()

    assert result == {"status": "ok", "neo4j": "ok"}


@pytest.mark.asyncio
async def test_health_degraded_when_neo4j_down(monkeypatch):
    """Neo4j failures must yield a structured 503, not a raw 500."""
    monkeypatch.setattr(main_module, "_SKIP_NEO4J", False)

    async def failing_healthcheck():
        raise ConnectionError("neo4j unreachable")

    monkeypatch.setattr(main_module, "run_healthcheck", failing_healthcheck)

    response = await main_module.read_health()

    assert response.status_code == 503
    body = json.loads(response.body)
    assert body["status"] == "degraded"
    assert body["neo4j"] == "unavailable"
    assert "neo4j unreachable" in body["detail"]


@pytest.mark.asyncio
async def test_health_skips_neo4j_when_flag_set(monkeypatch):
    """Under PLASTICFLOWER_SKIP_NEO4J the check is skipped and reported."""
    monkeypatch.setattr(main_module, "_SKIP_NEO4J", True)

    async def failing_healthcheck():
        raise AssertionError("Neo4j must not be checked under PLASTICFLOWER_SKIP_NEO4J")

    monkeypatch.setattr(main_module, "run_healthcheck", failing_healthcheck)

    result = await main_module.read_health()

    assert result == {"status": "ok", "neo4j": "skipped"}

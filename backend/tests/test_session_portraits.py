from unittest.mock import AsyncMock

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
import pytest

from app.api import sessions
from app.services import graph_db
from .fakes import FakeNeo4jDriver


LEGACY = {"id": "session_a", "name": "Seminar", "created_at": "2026-07-10T10:00:00Z"}
TITLED = {**LEGACY, "portrait_title": "Coastal gardens"}


@pytest.fixture
async def client():
    app = FastAPI()
    app.include_router(sessions.router)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


async def test_save_title_then_reopen_from_list_and_detail(client, monkeypatch):
    driver = FakeNeo4jDriver([
        [{"session": LEGACY}], [{"session": TITLED}],  # PATCH
        [{"session": TITLED}],                        # list
        [{"session": TITLED}], [],                    # detail and its chunks
    ])
    monkeypatch.setattr(graph_db, "get_driver", AsyncMock(return_value=driver))
    saved = await client.patch("/sessions/session_a", json={"portrait_title": "  Coastal gardens  "})
    assert saved.status_code == 200, saved.text
    assert saved.json()["portrait_title"] == "Coastal gardens"
    write = driver.calls[1]
    assert "MATCH (s:Session {id: $id})" in write["query"]
    assert "s.portrait_title = $portrait_title" in write["query"]
    assert write["params"] == {"id": "session_a", "portrait_title": "Coastal gardens"}
    listed = await client.get("/sessions")
    reopened = await client.get("/sessions/session_a")
    assert listed.json()["sessions"][0]["portrait_title"] == "Coastal gardens"
    assert reopened.json()["portrait_title"] == "Coastal gardens"


async def test_clear_title_and_reopen_legacy_record(client, monkeypatch):
    driver = FakeNeo4jDriver([
        [{"session": TITLED}], [{"session": LEGACY}],
        [{"session": LEGACY}], [],
    ])
    monkeypatch.setattr(graph_db, "get_driver", AsyncMock(return_value=driver))
    cleared = await client.patch("/sessions/session_a", json={"portrait_title": None})
    assert cleared.status_code == 200, cleared.text
    assert driver.calls[1]["params"] == {"id": "session_a", "portrait_title": None}
    record = (await client.get("/sessions/session_a")).json()
    assert record["portrait_title"] is None
    assert record["name"] == "Seminar"


async def test_renaming_preserves_the_portrait_title(client, monkeypatch):
    driver = FakeNeo4jDriver([[{"session": TITLED}], [{"session": {**TITLED, "name": "Day two"}}]])
    monkeypatch.setattr(graph_db, "get_driver", AsyncMock(return_value=driver))
    response = await client.patch("/sessions/session_a", json={"name": "Day two"})
    assert response.status_code == 200, response.text
    assert response.json()["name"] == "Day two"
    assert driver.calls[1]["params"] == {"id": "session_a", "name": "Day two"}
    assert "s.portrait_title" not in driver.calls[1]["query"]

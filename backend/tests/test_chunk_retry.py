from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api import chunks
from app.models import ChunkSubmissionRequest, SessionSummary, TranscriptChunk
from app.services import graph_db
from .fakes import FakeNeo4jDriver, FakeResult


@pytest.mark.asyncio
async def test_retry_after_lost_response_keeps_one_chunk_and_one_builder_task(monkeypatch):
    sessions = {
        key: SessionSummary(id=key, name=key, created_at="2026-01-01T00:00:00Z")
        for key in ("session-a", "session-b")
    }
    stored = {}

    async def insert_once(chunk):
        created = chunk.id not in stored
        return stored.setdefault(chunk.id, chunk), created

    monkeypatch.setattr(chunks, "get_session_record", AsyncMock(side_effect=sessions.get))
    monkeypatch.setattr(chunks.chunk_store, "insert_once", insert_once)
    queue = Mock()
    monkeypatch.setattr(chunks, "_queue_processing", queue)
    first = ChunkSubmissionRequest(
        client_request_id=uuid4(), text="first", start_time=1.0, end_time=2.0
    )
    second = first.model_copy(update={"client_request_id": uuid4(), "text": "second"})

    accepted = await chunks.submit_chunk(first, "session-a")
    await chunks.submit_chunk(second, "session-a")
    retry = await chunks.submit_chunk(first, "session-a")
    other = await chunks.submit_chunk(first, "session-b")

    assert retry.chunk_id == accepted.chunk_id
    assert other.chunk_id != accepted.chunk_id
    assert [(c.session_id, c.text) for c in stored.values()] == [
        ("session-a", "first"), ("session-a", "second"), ("session-b", "first")
    ]
    assert queue.call_count == 3

    sessions["session-a"].ended_at = datetime.now(timezone.utc)
    monkeypatch.setattr(chunks.chunk_store, "get", AsyncMock(side_effect=stored.get))
    # The Gardener can correct a transcript before the client retries.
    stored[accepted.chunk_id].original_text = "first"
    stored[accepted.chunk_id].text = "First."
    assert (await chunks.submit_chunk(first, "session-a")).chunk_id == accepted.chunk_id
    with pytest.raises(HTTPException) as conflict:
        await chunks.submit_chunk(first.model_copy(update={"text": "different"}), "session-a")
    assert conflict.value.status_code == 409
    assert queue.call_count == 3


@pytest.mark.asyncio
async def test_legacy_submissions_without_request_id_still_get_distinct_ids(monkeypatch):
    session = SessionSummary(id="s", name="s", created_at="2026-01-01T00:00:00Z")
    monkeypatch.setattr(chunks, "get_session_record", AsyncMock(return_value=session))
    monkeypatch.setattr(
        chunks.chunk_store, "insert_once", AsyncMock(side_effect=lambda c: (c, True))
    )
    monkeypatch.setattr(chunks, "_queue_processing", Mock())
    payload = ChunkSubmissionRequest(text="again", start_time=1, end_time=2)

    first = await chunks.submit_chunk(payload, session.id)
    second = await chunks.submit_chunk(payload, session.id)
    assert first.chunk_id != second.chunk_id


@pytest.mark.asyncio
@pytest.mark.parametrize("nodes_created", [0, 1])
async def test_insert_once_uses_neo4j_unique_chunk_id_without_overwriting(monkeypatch, nodes_created):
    chunk = TranscriptChunk(id="chunk-1", session_id="s", text="hello", start_time=1, end_time=2)
    driver = FakeNeo4jDriver([[{"chunk": chunk.model_dump()}]])
    monkeypatch.setattr(graph_db, "get_driver", AsyncMock(return_value=driver))
    counters = SimpleNamespace(nodes_created=nodes_created)
    monkeypatch.setattr(FakeResult, "consume", AsyncMock(return_value=SimpleNamespace(counters=counters)))

    assert await chunks.chunk_store.insert_once(chunk) == (chunk, bool(nodes_created))
    query = driver.calls[0]["query"]
    assert "MERGE (c:TranscriptChunk {id: $chunk_id}) ON CREATE SET c = $chunk" in query
    assert "ON MATCH SET" not in query
    assert "MERGE (s)-[:HAS_CHUNK]->(c)" in query

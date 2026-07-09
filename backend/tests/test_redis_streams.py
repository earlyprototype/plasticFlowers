"""Redis stream recovery tests: claim_pending_events / flush_stale_events.

Restart durability contract:
- Pending (delivered-but-unACKed) entries left by a crash are RECLAIMED at
  startup, not destroyed: stale ones (older than the threshold) are ACKed and
  discarded, fresh ones are returned for normal processing.
- flush_stale_events no longer destroys/recreates the consumer group (which
  silently threw away pending work and the group's read position).
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple

import pytest
from redis import ResponseError

from app.services import redis_streams
from app.services.redis_streams import (
    _message_age_seconds,
    claim_pending_events,
    flush_stale_events,
)


def _entry_id(age_seconds: float, seq: int = 0) -> str:
    return f"{int((time.time() - age_seconds) * 1000)}-{seq}"


class FakeRedis:
    """Minimal async Redis stub for group-recovery flows."""

    def __init__(
        self,
        *,
        stream_exists: bool = True,
        group_exists: bool = True,
        autoclaim_batches: Optional[List[Tuple[str, List[Tuple[str, Optional[Dict[str, Any]]]]]]] = None,
        pending_entries: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        self.stream_exists = stream_exists
        self.group_exists = group_exists
        self.autoclaim_batches = list(autoclaim_batches or [])
        self.pending_entries = list(pending_entries or [])
        self.acked: List[str] = []
        self.groups_created: List[Tuple[str, str]] = []
        self.groups_destroyed: List[Tuple[str, str]] = []
        self.autoclaim_calls: List[Dict[str, Any]] = []

    async def exists(self, stream: str) -> int:
        return 1 if self.stream_exists else 0

    async def xgroup_create(self, stream: str, group: str, id: str = "$", mkstream: bool = False):
        if self.group_exists:
            raise ResponseError("BUSYGROUP Consumer Group name already exists")
        self.group_exists = True
        self.groups_created.append((stream, group))

    async def xgroup_destroy(self, stream: str, group: str):  # pragma: no cover - must not run
        self.groups_destroyed.append((stream, group))

    async def xautoclaim(self, stream, group, consumer, min_idle_time=0, start_id="0-0", count=100):
        self.autoclaim_calls.append(
            {"consumer": consumer, "min_idle_time": min_idle_time, "start_id": start_id}
        )
        if not self.autoclaim_batches:
            return ["0-0", []]
        return list(self.autoclaim_batches.pop(0))

    async def xack(self, stream: str, group: str, message_id: str):
        self.acked.append(message_id)

    async def xpending_range(self, stream, group, min="-", max="+", count=1000):
        return list(self.pending_entries)


@pytest.fixture
def patch_redis(monkeypatch):
    def _patch(fake: FakeRedis) -> FakeRedis:
        async def fake_get_redis():
            return fake

        monkeypatch.setattr(redis_streams, "get_redis", fake_get_redis)
        return fake

    return _patch


def test_message_age_derived_from_entry_id():
    assert _message_age_seconds(_entry_id(120)) == pytest.approx(120, abs=2)
    assert _message_age_seconds(_entry_id(0)) == pytest.approx(0, abs=2)
    assert _message_age_seconds("garbage") == 0.0


@pytest.mark.asyncio
async def test_claim_pending_discards_stale_returns_fresh(patch_redis):
    stale_id = _entry_id(120)
    fresh_id = _entry_id(1)
    fake = patch_redis(FakeRedis(
        autoclaim_batches=[
            ("0-0", [
                (stale_id, {"session_id": "dead", "chunk_id": "c0"}),
                (fresh_id, {"session_id": "alive", "chunk_id": "c1"}),
            ]),
        ],
    ))

    fresh = await claim_pending_events("stream", "group", "worker-1", max_age_seconds=30)

    assert fresh == [(fresh_id, {"session_id": "alive", "chunk_id": "c1"})], (
        "fresh pending entries are handed back for normal processing"
    )
    assert fake.acked == [stale_id], "stale entries are ACKed (discarded), fresh are NOT"
    assert fake.groups_destroyed == [], "recovery must never destroy the group"
    assert fake.autoclaim_calls[0]["consumer"] == "worker-1"


@pytest.mark.asyncio
async def test_claim_pending_acks_trimmed_entries(patch_redis):
    """Entries trimmed from the stream linger in the PEL with None data —
    they must be ACKed away, not returned."""
    fresh_id = _entry_id(1)
    fake = patch_redis(FakeRedis(
        autoclaim_batches=[("0-0", [(fresh_id, None)])],
    ))

    fresh = await claim_pending_events("stream", "group", "worker-1", max_age_seconds=30)

    assert fresh == []
    assert fake.acked == [fresh_id]


@pytest.mark.asyncio
async def test_claim_pending_paginates_until_cursor_wraps(patch_redis):
    first_id = _entry_id(2)
    second_id = _entry_id(1)
    fake = patch_redis(FakeRedis(
        autoclaim_batches=[
            (second_id, [(first_id, {"session_id": "s1", "chunk_id": "c1"})]),
            ("0-0", [(second_id, {"session_id": "s1", "chunk_id": "c2"})]),
        ],
    ))

    fresh = await claim_pending_events("stream", "group", "worker-1", max_age_seconds=30)

    assert [mid for mid, _ in fresh] == [first_id, second_id]
    assert [call["start_id"] for call in fake.autoclaim_calls] == ["0-0", second_id]


@pytest.mark.asyncio
async def test_claim_pending_missing_stream_returns_empty(patch_redis):
    fake = patch_redis(FakeRedis(stream_exists=False))

    assert await claim_pending_events("stream", "group", "worker-1") == []
    assert fake.autoclaim_calls == []


@pytest.mark.asyncio
async def test_claim_pending_creates_group_when_missing(patch_redis):
    fake = patch_redis(FakeRedis(group_exists=False))

    assert await claim_pending_events("stream", "group", "worker-1") == []
    assert fake.groups_created == [("stream", "group")]


@pytest.mark.asyncio
async def test_flush_stale_events_acks_only_old_entries(patch_redis):
    """flush_stale_events keeps fresh pending entries and never destroys the
    group — previously it XGROUP-DESTROYed, losing all pending work."""
    stale_id = _entry_id(120)
    fresh_id = _entry_id(1)
    fake = patch_redis(FakeRedis(
        pending_entries=[
            {"message_id": stale_id, "consumer": "w1"},
            {"message_id": fresh_id, "consumer": "w1"},
        ],
    ))

    discarded = await flush_stale_events("stream", "group", max_age_seconds=60)

    assert discarded == 1
    assert fake.acked == [stale_id]
    assert fake.groups_destroyed == [], "no destroy-recreate: pending work survives"


@pytest.mark.asyncio
async def test_flush_stale_events_missing_stream(patch_redis):
    fake = patch_redis(FakeRedis(stream_exists=False))

    assert await flush_stale_events("stream", "group") == 0
    assert fake.acked == []

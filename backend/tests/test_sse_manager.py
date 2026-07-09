"""SSE manager overflow tests: resync_required control signal.

When a bounded subscriber queue overflows, silently dropping the oldest event
leaves the client with a permanently incomplete stream. The manager must:
- enqueue exactly ONE `resync_required` control event (payload
  {"reason": "event_overflow"}) at the start of an overflow episode, ahead of
  the newest message;
- NOT re-signal while the episode continues;
- re-arm once the queue drains below half capacity, so a later overflow
  produces a second signal.
"""

from __future__ import annotations

import asyncio
import json

import pytest

from app.models import NodeRemovedEvent
from app.services.sse_manager import SSEManager


def _subscribe_small(manager: SSEManager, session_id: str, maxsize: int) -> asyncio.Queue:
    """Register a small bounded queue (overflow logic keys off queue.maxsize)."""
    queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=maxsize)
    manager._connections[session_id].add(queue)
    return queue


def _event(idx: int) -> NodeRemovedEvent:
    return NodeRemovedEvent(payload={"id": f"node-{idx}"})


def _drain(queue) -> list[dict]:
    items = []
    while not queue.empty():
        items.append(queue.get_nowait())
        queue.task_done()
    return items


def _resync_messages(messages: list[dict]) -> list[dict]:
    return [m for m in messages if m["event"] == "resync_required"]


@pytest.mark.asyncio
async def test_overflow_enqueues_exactly_one_resync_required():
    manager = SSEManager()
    queue = _subscribe_small(manager, "s1", maxsize=4)

    for idx in range(4):  # fill to capacity
        await manager.broadcast("s1", _event(idx))
    assert queue.full()

    # Overflow twice: one episode -> exactly one resync signal.
    await manager.broadcast("s1", _event(4))
    await manager.broadcast("s1", _event(5))

    messages = _drain(queue)
    resyncs = _resync_messages(messages)
    assert len(resyncs) == 1, "exactly one resync_required per overflow episode"
    assert resyncs[0]["event"] == "resync_required", "frontend subscribes to this literal type"
    assert json.loads(resyncs[0]["data"]) == {"reason": "event_overflow"}

    # The control event precedes the message that triggered the overflow.
    types_and_ids = [(m["event"], json.loads(m["data"]).get("id")) for m in messages]
    resync_pos = next(i for i, (t, _) in enumerate(types_and_ids) if t == "resync_required")
    node4_pos = next(i for i, (_, nid) in enumerate(types_and_ids) if nid == "node-4")
    assert resync_pos < node4_pos, "resync signal is enqueued ahead of the new message"


@pytest.mark.asyncio
async def test_resync_rearms_after_drain_below_half_capacity():
    manager = SSEManager()
    queue = _subscribe_small(manager, "s1", maxsize=4)

    # First overflow episode.
    for idx in range(5):
        await manager.broadcast("s1", _event(idx))
    first_batch = _drain(queue)
    assert len(_resync_messages(first_batch)) == 1

    # Queue fully drained (below half capacity) -> episode ends on the next
    # broadcast; a subsequent overflow must signal again.
    for idx in range(10, 15):
        await manager.broadcast("s1", _event(idx))
    second_batch = _drain(queue)
    assert len(_resync_messages(second_batch)) == 1, "drain + re-overflow re-signals"


@pytest.mark.asyncio
async def test_no_resignal_while_queue_stays_above_half_capacity():
    manager = SSEManager()
    queue = _subscribe_small(manager, "s1", maxsize=4)

    for idx in range(5):  # trigger the first overflow
        await manager.broadcast("s1", _event(idx))

    # Consume ONE item (queue stays above half capacity), then overflow again.
    queue.get_nowait()
    queue.task_done()
    await manager.broadcast("s1", _event(6))
    await manager.broadcast("s1", _event(7))

    messages = _drain(queue)
    total_resyncs = len(_resync_messages(messages))
    assert total_resyncs == 1, "no re-signal until the queue drains below half capacity"


@pytest.mark.asyncio
async def test_unsubscribe_clears_resync_state():
    manager = SSEManager()
    queue = _subscribe_small(manager, "s1", maxsize=2)

    for idx in range(3):
        await manager.broadcast("s1", _event(idx))
    assert queue in manager._resync_signalled

    await manager.unsubscribe("s1", queue)
    assert queue not in manager._resync_signalled
    assert manager._connections == {}

# ADR-0009: Redis-Only Agent Scheduling

## Status

Accepted

## Date

2025-12-27

## Context

The Gardener scheduler originally had **two parallel trigger mechanisms**:

1. **Timer loop** - polling every 60 seconds, checking `mark_activity` timestamps
2. **Redis consumer** - event-driven, triggered by `chunks.added` events

This dual approach caused problems:
- Both could trigger Gardener for the same session (duplicate work)
- Timer loop ran even when Redis had already triggered Gardener
- Hard-coded debounce values (5 seconds) scattered in code
- `mark_activity()` was called twice in `chunks.py` (redundant)
- Complex debugging when issues occurred

Additionally, Builder orchestration logic was mixed into the API endpoint (`chunks.py`), making it hard to test and inconsistent with Gardener's cleaner service-layer pattern.

## Decision

1. **Remove timer-based polling entirely** - Gardener is now Redis-only
2. **Make debounce configurable** - `GARDENER_DEBOUNCE_SECONDS` in config (default 60s)
3. **Create BuilderService** - Extract Builder orchestration from `chunks.py` into `services/builder_service.py`
4. **Thin API endpoints** - `chunks.py` now only validates and queues (100 lines vs 295)

### New Architecture

```
[HTTP Request] --> [API: validate + queue] --> [BuilderService: orchestrate]
                                                      |
                                                      v
                                               [Redis: publish]
                                                      |
                                                      v
                                         [GardenerScheduler: consume + run]
```

### Configuration

```env
GARDENER_DEBOUNCE_SECONDS=60  # Adjustable 5-300
BUILDER_TASK_TIMEOUT=90       # Existing
```

## Consequences

### Positive

- **Simpler debugging** - Single trigger path, clear event flow
- **Configurable timing** - Easy to experiment with debounce values
- **Consistent pattern** - Builder and Gardener both follow service-layer orchestration
- **Testable** - BuilderService can be unit tested without HTTP
- **Future-ready** - Researcher/Librarian will follow same Redis consumer pattern

### Negative

- **Redis dependency** - Gardener won't run if Redis is down (acceptable for our use case)
- **No fallback** - If Redis events are lost, Gardener won't process (rare edge case)

### Neutral

- `mark_activity()` still exists but only tracks active SSE clients (monitoring)
- Builder remains request-driven (not batched) - appropriate for real-time speech

## Alternatives Considered

### Alternative 1: Keep Both Timer + Redis

- Description: Timer as fallback, Redis as primary
- Why rejected: Added complexity, hard to debug, timer would still run redundant checks

### Alternative 2: Timer-Only (Remove Redis)

- Description: Revert to simple polling
- Why rejected: Slower response, can't scale to multiple workers, doesn't prepare for Researcher/Librarian

### Alternative 3: Builder Scheduler (Batch Chunks)

- Description: Create a scheduler for Builder like Gardener
- Why rejected: Over-engineering for now - Builder's request-driven nature is appropriate for real-time speech

## Related

- `backend/app/services/scheduler.py` - Gardener scheduler (Redis consumer)
- `backend/app/services/builder_service.py` - NEW Builder service
- `backend/app/services/redis_streams.py` - Event publishing/consuming
- `backend/app/api/chunks.py` - Thin HTTP endpoint
- `backend/app/config.py` - `gardener_debounce_seconds` setting
- ADR-006: Async event-driven agents (foundational decision)

## Notes

Future agents (Researcher, Librarian) should follow the Gardener pattern:

```python
class ResearcherScheduler:
    async def _redis_consumer_loop(self):
        async for message_id, data in consume_events(
            STREAM_NODES_NEEDS_RESEARCH,
            GROUP_RESEARCHER,
            ...
        ):
            await self._run_researcher(data["node_id"])
```

The Redis streams infrastructure (`redis_streams.py`) already defines:
- `STREAM_NODES_NEEDS_RESEARCH`
- `GROUP_RESEARCHER`
- `publish_node_needs_research()`



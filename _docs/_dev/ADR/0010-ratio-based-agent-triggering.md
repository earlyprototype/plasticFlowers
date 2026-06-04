# ADR-010: Ratio-Based Agent Triggering

**Status:** Accepted  
**Date:** 2025-12-27  
**Deciders:** User + LLM  
**Context:** Phase D.5 - Redis Streams (Event Bus)

## Context

The original event-driven architecture triggered Gardener on every chunk event (with a 30-second debounce). This caused issues:

1. **Decoupling confusion:** Debounce was conflated with UI animation debounce (1.2s in Cytoscape)
2. **Unpredictable timing:** Time-based debounce didn't relate to actual work done
3. **Over-triggering:** Rapid chunk uploads could queue multiple Gardener runs

User insight: "Gardener was NEVER supposed to run on every chunk - it should tie Builder turns to Gardener on a ratio like 2/3/4/5:1"

## Decision

Implement **ratio-based agent triggering** where Gardener runs after every N Builder completions (default: 5:1).

```python
# config.py
builder_gardener_ratio: int = Field(
    5,  # Every 5 Builder runs = 1 Gardener run
    ge=1,
    le=20,
)
```

Builder maintains a per-session counter and only publishes to Redis when threshold is reached:

```python
# builder_service.py
if current_count >= ratio:
    await publish_chunk_added(...)
    self._builder_runs[session_id] = 0  # Reset
```

## Alternatives Considered

### Option A: Time-Based Debounce (Previous)
- **Pros:** Simple, guaranteed minimum interval
- **Cons:** Not related to actual work, confusing with UI debounce

### Option B: Event-Driven with Batching
- **Pros:** Process multiple chunks at once
- **Cons:** Complex, unpredictable batch sizes

### Option C: Ratio-Based (Chosen)
- **Pros:** Predictable, relates to actual work, extensible to future agents
- **Cons:** Slightly more state to track (counter per session)

## Consequences

### Positive
- **Predictable:** Every 5 chunks = 1 Gardener run (configurable)
- **Extensible:** Future agents can use same pattern with different ratios
- **Paced:** Natural throttling based on actual work, not time
- **Clear separation:** UI debounce (1.2s) handles animation, ratio handles API calls

### Negative
- **State tracking:** Builder must maintain per-session counter
- **Session cleanup:** Counter must be reset on session end

### Future Extensions

```python
# Potential future config
AGENT_RATIOS = {
    "gardener": 5,      # Every 5 Builder runs
    "researcher": 10,   # Every 10 Builder runs
    "summarizer": 20,   # Every 20 Builder runs
}
```

## Implementation

Files changed:
- `backend/app/config.py` - Added `builder_gardener_ratio`
- `backend/app/services/builder_service.py` - Added counter and ratio logic
- `backend/app/services/scheduler.py` - Simplified to process each Redis event

## Related

- **ADR-009:** Redis-only agent scheduling (this builds on it)
- **Frontend debounce:** `ANIMATION_CONFIG.debounceDelay` (1.2s) - separate concern for UI animation batching


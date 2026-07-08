# Gate 5 — Director's Report

> **Gate:** Gardener Refinement Loop
> **Date:** 16 December 2025
> **Status:** READY FOR SIGN-OFF

---

## Executive Summary

Gate 5 implements the Gardener refinement loop — the 90-second periodic agent that confirms/prunes/merges ghost nodes and forms Flowers. All core components have been implemented and verified.

**Key achievement:** Identified and resolved a critical Windows IPv6 fallback issue that was causing 90-second Neo4j timeouts. After fixing, full Builder → Neo4j → Gardener pipeline operates in <1 second per chunk.

---

## Deliverables Status

| Deliverable | Status | Location |
|-------------|--------|----------|
| `GardenerAgent` class | ✅ Complete | `backend/app/agents/gardener.py` |
| `GardenerScheduler` | ✅ Complete | `backend/app/services/scheduler.py` |
| 90-second fixed interval | ✅ Implemented | Per `_ALIGNMENT.md` |
| Activity tracking | ✅ Implemented | Builder marks activity on chunk submit |
| Node actions (confirm/prune/merge) | ✅ Implemented | `scheduler.py` |
| Flower actions (create/update/dissolve) | ✅ Implemented | `scheduler.py` |
| SSE event broadcasting | ✅ Implemented | All Gardener events broadcast |
| Neo4j persistence | ✅ Working | After IPv4 fix |

---

## Verification Results

### Replay Test Results

| Test | Result |
|------|--------|
| Chunks dispatched | 3/3 ✅ |
| Builder processing | Complete in <1s each |
| Neo4j persistence | Working |
| SSE events | Broadcasting |

**Console output (with Neo4j):**
```
builder.complete ... round_trip_ms=885.52 llm_call_ms=0.39 nodes_created=5 relationships_created=4 ... timed_out=False errored=False
builder.complete ... round_trip_ms=174.51 llm_call_ms=0.54 nodes_created=5 relationships_created=4 ... timed_out=False errored=False
builder.complete ... round_trip_ms=227.30 llm_call_ms=0.25 nodes_created=5 relationships_created=4 ... timed_out=False errored=False
```

### Without Neo4j (Pipeline Only)
```
builder.complete ... round_trip_ms=2.35 llm_call_ms=0.43 ... timed_out=False errored=False
builder.complete ... round_trip_ms=1.44 llm_call_ms=0.30 ... timed_out=False errored=False
builder.complete ... round_trip_ms=0.88 llm_call_ms=0.23 ... timed_out=False errored=False
```

---

## Non-Negotiable Compliance

| Rule | Implementation | Status |
|------|----------------|--------|
| Gardener cadence = 90 seconds fixed | `GARDENER_INTERVAL = 90` in scheduler | ✅ |
| Uncertainty → prune (not confirm) | Gardener prompt + noise policy | ✅ |
| Merge = true duplicates only | Prompt explicit: synonyms/acronyms/spelling only | ✅ |
| Flower = 3+ nodes AND 2+ internal connections | `_count_internal_edges()` helper enforces both | ✅ |
| `inferred_type` remains freeform | No enum constraints in models | ✅ |
| Relationship `id` required | Model validation + SSE payloads | ✅ |

---

## Issue Encountered & Resolved

### Windows IPv6 Fallback Timeout

**Symptom:** All Neo4j operations taking exactly 21-22 seconds, causing 90-second Builder timeouts.

**Root Cause:** Neo4j driver using `neo4j://localhost:7687` was attempting IPv6 connection first (`::1`), timing out, then falling back to IPv4 (`127.0.0.1`). Each fallback added ~21 seconds.

**Diagnosis Method:** Created `backend/scripts/neo4j_diag.py` diagnostic script that tested each Neo4j operation with timing.

**Evidence:**
```
# With localhost:
[2] Verifying connectivity...  42,118ms
[3] Running simple query...     21,107ms

# With 127.0.0.1:
[2] Verifying connectivity...   18ms
[3] Running simple query...     4.78ms
```

**Resolution:** Changed default `neo4j_uri` in `backend/app/config.py`:
```python
# Before
neo4j_uri: str = Field("neo4j://localhost:7687", ...)

# After  
neo4j_uri: str = Field("neo4j://127.0.0.1:7687", ...)
```

**Impact:** 1000x+ performance improvement on Windows.

---

## Code Artefacts

### New Files Created

| File | Purpose | Lines |
|------|---------|-------|
| `backend/app/agents/gardener.py` | Gardener agent: prompt, LLM call, parsing | ~300 |
| `backend/app/services/scheduler.py` | 90-second scheduler, action application | ~250 |
| `backend/scripts/neo4j_diag.py` | Neo4j diagnostic tool | ~80 |

### Modified Files

| File | Change |
|------|--------|
| `backend/app/config.py` | Default `neo4j_uri` to `127.0.0.1` |
| `backend/app/services/__init__.py` | Export `GardenerScheduler` |
| `backend/app/agents/__init__.py` | Export `GardenerAgent` |
| `backend/app/main.py` | Integrate scheduler into lifespan |
| `backend/app/api/chunks.py` | Mark activity for Gardener |

---

## Architecture Compliance

| Requirement | Implementation |
|-------------|----------------|
| Gardener runs only if activity or ghost nodes | `_should_run()` checks both conditions |
| Gardener output: JSON schema | `GardenerLLMResponse` Pydantic model |
| Node actions: confirm, prune, merge | Individual methods in scheduler |
| Flower actions: form, update membership | `_apply_flower_actions()` |
| Cross-chunk relationships | `_apply_new_relationships()` |
| SSE broadcast per action | Events emitted for each mutation |

---

## Testing Environment

| Component | Version/Config |
|-----------|----------------|
| Neo4j | 5.22 (Docker) |
| Python | 3.12 |
| Backend | FastAPI + Uvicorn |
| LLM | Fake mode (heuristic responses) |
| Embeddings | Fake mode (synthetic vectors) |

---

## Outstanding Items for Gate 6

| Item | Notes |
|------|-------|
| Frontend Gardener SSE handlers | Gate 6 scope |
| Cytoscape compound nodes (Flowers) | Gate 6 scope |
| End-to-end visual demo | Gate 6 scope |
| Real LLM integration | Gate 7 scope |

---

## Sign-Off Checklist

- [x] `GardenerAgent` implemented with prompt rendering
- [x] `GardenerScheduler` triggers every 90 seconds
- [x] Activity tracking from Builder
- [x] Node actions (confirm/prune/merge) implemented
- [x] Flower actions (form/update/dissolve) implemented
- [x] SSE events broadcast for all Gardener actions
- [x] Neo4j persistence working
- [x] Non-negotiables enforced in code
- [x] IPv6 timeout issue diagnosed and resolved
- [x] Replay test passes with real Neo4j

---

## Recommendation

**APPROVE Gate 5.**

All backend Gardener infrastructure is complete. The pipeline successfully processes chunks, persists to Neo4j, and the Gardener scheduler is operational. Frontend integration (Gate 6) can now proceed.

---

**Prepared by:** AI Development Assistant
**Date:** 16 December 2025


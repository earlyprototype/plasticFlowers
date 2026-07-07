# plasticFlower — Progress Log

> Tracks work completed since initial handover.

---

## Session: 13 December 2025

**Starting point:** Handover complete, specification in progress
**Completed:** All specifications, document review, implementation handoff

---

### Work Completed

| Item | Output | Status |
|------|--------|--------|
| Builder Agent prompt | `_prompts/01_builder.md` | ✓ Complete |
| Gardener Agent prompt | `_prompts/02_gardener.md` | ✓ Complete |

---

### Key Decisions Made

#### 1. What Should Builder Extract?

| Decision | **Entities + chunk-local relationships** |
|----------|------------------------------------------|
| Alternatives | Entities only (Gardener infers relationships) |
| Reasoning | Relationships like "X enables Y" are clearest when both appear in the same chunk. Waiting 90 seconds loses that immediate context. "Chunk-local" constraint naturally limits scope. |

#### 2. How to Structure Category Prompt?

| Decision | **Definitions + 1 example each** |
|----------|----------------------------------|
| Alternatives | Labels only; Definitions only |
| Reasoning | Most guidance for consistent categorisation. Examples anchor the LLM's interpretation. Token cost (~50 tokens) is negligible. |

#### 3. What Output Format?

| Decision | **Strict JSON schema** |
|----------|------------------------|
| Alternatives | Free-form text; Markdown structure |
| Reasoning | Reliable parsing, easy validation. Gemini 3 Pro supports structured output mode. Failed parses can be logged and retried. |

#### 4. How to Pass Graph Context?

| Decision | **Labels only, grouped by type** |
|----------|----------------------------------|
| Alternatives | No context; Full node details; Embedding similarity search |
| Reasoning | Compact (~50 nodes in ~200 tokens). Sufficient for matching duplicates. Type grouping helps Builder infer types consistently. Scales to ~500 nodes before needing similarity search (post-MVP). |

---

### Specifications Produced

**Builder Agent** (`01_builder.md`)

- Processes each chunk in real-time
- Extracts nodes + chunk-local relationships
- Outputs strict JSON
- Creates "ghost" nodes for Gardener review
- Token budget: ~900-1300 per invocation

**Gardener Agent** (`02_gardener.md`)

- Runs every 90 seconds
- Reviews ghost nodes → confirm/prune/merge
- Forms and updates Flowers (thematic clusters)
- Creates cross-chunk relationships
- Assigns stem nodes
- Token budget: ~4000-4600 per invocation

---

### Post-Completion Review

A co-founder review identified three specification drifts from agreed decisions:

| Issue | Error | Correction |
|-------|-------|------------|
| Emergent schema | `inferred_type` constrained to 6 predefined types | Changed to freeform string |
| Flower threshold | Only "3+ nodes" specified | Added "AND 2+ internal connections" |
| Merge criteria | Example showed hierarchy flattening | Fixed to show true duplicate merge only |

**Root cause:** Specification work prioritised parsing reliability over design intent, defaulting to "safe" patterns without re-verifying against Decision Log.

**Outputs:**

- `_DRIFT_REPORT_001.md` — Full analysis of issues
- `_ALIGNMENT.md` — Principles and checklist for future work
- Corrected `01_builder.md` and `02_gardener.md`

---

### Continued Work (Same Session)

Following drift review and alignment confirmation:

| Item | Output | Status |
|------|--------|--------|
| API contracts | `_api/01_contracts.md` | ✓ Complete |
| Frontend data flow | `_frontend/01_data_flow.md` | ✓ Complete |
| Project structure | `_structure/01_project_structure.md` | ✓ Complete |

**API Contracts** covers:
- Session management endpoints
- Transcript chunk submission
- SSE event types
- Graph data endpoints
- Export endpoints (JSON, transcript, VTT, Markdown)
- Data schemas
- Error responses

**Frontend Data Flow** covers:
- Architecture diagram
- Speech capture → chunk dispatch flow
- SSE event processing
- Graph state management
- Cytoscape.js integration
- Visual states (ghost/solid, categories)
- Z-level filtering
- Auto-reconnect logic

**Project Structure** covers:
- Directory layout (frontend + backend)
- Module responsibilities
- Configuration
- Docker Compose for local deployment
- Dependencies

---

### Current State

| Phase | Status |
|-------|--------|
| Discovery | ✓ Complete |
| Core specifications | ✓ Complete |
| Agent prompts | ✓ Complete |
| API contracts | ✓ Complete |
| Frontend data flow | ✓ Complete |
| Project structure | ✓ Complete |
| Implementation | **Next** |

---

### Document Review (End of Session)

All documents reviewed and updated for implementation handoff:

| Document | Update |
|----------|--------|
| `_DECISION_LOG.md` | Added DEC-016 through DEC-019 (Builder prompt decisions) |
| `_CONVERSATIONS.md` | Added Conv-006 (Builder decisions), Conv-007 (Drift review) |
| `_HANDOVER.md` | Updated to v3.0, reflects completed state |
| `_IMPLEMENTATION_BRIEF.md` | Added full document tree, reading order, quick links |
| `_PROGRESS.md` | Updated date, added this section |

**Document tree is now water-tight for implementation handoff.**

---

### Pre-Implementation Review

A final review checkpoint was completed, resulting in `_PRE_IMPLEMENTATION_REPORT.md`:

| Clarification | Resolution |
|---------------|------------|
| Contradiction detection | Post-MVP (removed from MVP scope) |
| Gardener trigger | Fixed at 90 seconds only |
| Uncertainty policy | Prune/expel rather than confirm |
| Local-only meaning | Hosting constraint, not privacy guarantee |
| Pre-Builder similarity | >= 0.85 threshold, deterministic behaviour |
| Relationship identity | Required `id` field, `relationship_removed` uses `{ id }` |

All spec files updated. Sign-off checklist ready.

---

### Next Steps

1. Sign off `_PRE_IMPLEMENTATION_REPORT.md`
2. Begin implementation

---

## Session: 16 December 2025

**Starting point:** Gate 4 complete (Builder loop working)
**Completed:** Gate 5 — Gardener Refinement Loop

---

### Gate 5 Work Completed

| Item | Output | Status |
|------|--------|--------|
| GardenerAgent class | `backend/app/agents/gardener.py` | ✓ Complete |
| GardenerScheduler | `backend/app/services/scheduler.py` | ✓ Complete |
| Activity tracking | Builder marks activity on chunk submit | ✓ Complete |
| Node actions | Confirm, prune, merge in scheduler | ✓ Complete |
| Flower actions | Form, update, dissolve in scheduler | ✓ Complete |
| SSE broadcasting | All Gardener events | ✓ Complete |
| Neo4j IPv4 fix | `config.py` default URI updated | ✓ Complete |
| Diagnostic tool | `backend/scripts/neo4j_diag.py` | ✓ Complete |

---

### Critical Issue Resolved

**Windows IPv6 Fallback Timeout**

| Issue | All Neo4j operations taking 21-22 seconds |
|-------|-------------------------------------------|
| Root Cause | `localhost` → IPv6 fallback → IPv4 on Windows |
| Diagnosis | Custom `neo4j_diag.py` script with per-operation timing |
| Resolution | Changed default `neo4j_uri` to `127.0.0.1` |
| Impact | **1000x performance improvement** |

Evidence:
- `localhost`: 21,107ms per query
- `127.0.0.1`: 4.78ms per query

---

### Verification Results

| Test | Result |
|------|--------|
| Replay with Neo4j | ✓ 3/3 chunks, <1s each |
| Replay without Neo4j | ✓ 3/3 chunks, <3ms each |
| Neo4j diagnostics | ✓ All 7 tests pass |

Console output (with Neo4j):
```
builder.complete round_trip_ms=885.52 timed_out=False errored=False
builder.complete round_trip_ms=174.51 timed_out=False errored=False
builder.complete round_trip_ms=227.30 timed_out=False errored=False
```

---

### Non-Negotiable Compliance

| Rule | Status |
|------|--------|
| Gardener cadence = 90 seconds fixed | ✓ Enforced |
| Uncertainty → prune (not confirm) | ✓ Enforced |
| Merge = true duplicates only | ✓ Enforced |
| Flower = 3+ nodes AND 2+ internal connections | ✓ Enforced |
| `inferred_type` freeform | ✓ Enforced |

---

### Gate 5 Sign-Off

**Director Report:** `_docs/_evidence/gate5/director_report.md`
**Status:** READY FOR SIGN-OFF
**Recommendation:** APPROVE

---

### Current State

| Phase | Status |
|-------|--------|
| Gate 1 — Project Setup | ✓ Complete |
| Gate 2 — Session & Chunk Endpoint | ✓ Complete |
| Gate 3 — Graph Persistence | ✓ Complete |
| Gate 4 — Builder Loop | ✓ Complete |
| Gate 5 — Gardener Loop | ✓ Complete |
| Gate 6 — Frontend Integration | **Next** |
| Gate 7 — Real LLM Integration | Pending |


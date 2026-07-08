# Gate 2 — Contracts Locked (Integration-Safe)

> **Objective:** API shapes + SSE event payloads are final; frontend/backend can integrate safely
> **Entry:** Gate 1 passed (dev environment green)
> **Exit:** Contracts match spec; Relationship `id` exists; frontend keying strategy confirmed

---

## Serial Dependencies (must complete in order)

1. **Schema extraction** — Re-read `_docs/_dev/_MVP/_api/01_contracts.md`, `_docs/_dev/_MVP/_schema/01_data_model.md`, `_docs/_dev/_MVP/_ALIGNMENT.md`, `_docs/_dev/_MVP/_PRE_IMPLEMENTATION_REPORT.md` and compile a contract table covering every entity + SSE payload.
2. **Pydantic models** — Define Node, Relationship, Flower, Session, Chunk, and SSE payload models exactly as specified (relationship `id` required, `inferred_type` freeform string).
3. **API route stubs** — All endpoints from `_api/01_contracts.md` exist and return typed placeholder responses (`HTTP_501` acceptable) wired through FastAPI routers.
4. **Frontend types** — TypeScript interfaces and SSE discriminated unions match backend models 1:1, plus typed fetch helpers for every endpoint.

---

## Parallel Lanes (can run simultaneously)

| Lane | Work | Owner | Notes |
|------|------|-------|-------|
| A | Backend: Contract table → Pydantic models → API route stubs → SSE payload classes | Backend dev | Share contract snapshot with Lane B before they generate types |
| B | Frontend: Mirror types → SSE unions → API client wrappers | Frontend dev | Must block until Lane A publishes snapshot; any drift triggers Decision Request |

**Sync point:** After Lane A publishes the contract snapshot, Lane B mirrors it exactly. A joint review (or automated diff) must confirm parity before declaring Gate 2 complete.

---

## Deliverables

| Deliverable | Acceptance Criteria |
|-------------|---------------------|
| `backend/app/models/` | Pydantic models for all entities + SSE payloads (with spec references in docstrings) |
| `backend/app/api/` | Route stubs for all endpoints (can return 501) wired via FastAPI routers |
| Contract snapshot | Table/JSON mapping backend models → frontend types (used during review) |
| `frontend/src/lib/types.ts` | TypeScript interfaces + SSE unions match backend models exactly |
| `frontend/src/lib/api.ts` | Typed fetch wrappers for all endpoints using the new interfaces |

---

## Critical Contract Points

| Contract | Spec Reference | Must Match |
|----------|----------------|------------|
| Relationship `id` | `_schema/01_data_model.md` | Required field |
| `relationship_removed` | `_api/01_contracts.md` | Payload is `{ id }` |
| `inferred_type` | `_ALIGNMENT.md` | Freeform string (no enum) |
| Relationship categories | `_ALIGNMENT.md` | Exactly 5: CAUSAL, STRUCTURAL, COMPARATIVE, TEMPORAL, ASSOCIATIVE |

---

## Implementation Plan

1. **Contract Table (Pre-work)**
   1. Read `_docs/_dev/_MVP/_api/01_contracts.md`, `_schema/01_data_model.md`, `_ALIGNMENT.md`, `_PRE_IMPLEMENTATION_REPORT.md`.
   2. Build a table per entity (Node/Relationship/Flower/Session/Chunk + SSE events) listing property → type → required? → spec reference.
   3. Use this table as the single source throughout Gate 2. Any ambiguity is escalated via Decision Request before coding.

2. **Lane A — Backend**
   1. Implement BaseModels under `backend/app/models/` (one file per entity + `events.py`).
   2. Enforce non-negotiables: `inferred_type: str` (no enums), `Relationship.category` literal union with the 5 allowed values, `Relationship.id` required, `relationship_removed` payload `{ "id": str }`.
   3. Add FastAPI routers under `backend/app/api/{sessions,chunks,graph,export,stream}.py` registering every endpoint; return mock data or `HTTPException(501)` referencing the relevant model.
   4. Document SSE payloads in docstrings referencing `_api/01_contracts.md` sections.
   5. Run `uvicorn` + import tests (`python -c "from app.models import Node"`) to satisfy verification items 1–2.

3. **Lane B — Frontend**
   1. Generate `frontend/src/lib/types.ts` mirroring each backend model; include literal unions for `RelationshipCategory`, `NodeStatus`, etc.
   2. Create discriminated unions for SSE events (`type` + `payload`) ensuring `relationship_removed` is `{ id: string }`.
   3. Build `frontend/src/lib/api.ts` typed wrappers for every endpoint; compile with `tsc --noEmit` and `npm run lint` to confirm success.

4. **Cross-Lane Validation**
   1. Produce a “contract snapshot” mapping backend → frontend definitions (markdown table or JSON).
   2. Conduct a joint review of the snapshot; any mismatch is resolved immediately.
   3. Update plan doc / report with snapshot link for Director review.

5. **Verification & Reporting**
   1. Run Gate 2 checklist (below) and record results in Gate 2 Work Completion Report per `_dev/LLM_DEVELOPMENT_GUIDE.md`.
   2. Confirm SSE payload comments exist, TypeScript types compile, and `relationship.id` + `inferred_type` requirements remain intact.
   3. Provide readiness summary + contract snapshot when requesting approval to enter Gate 3.

---

## Verification Checklist

- [ ] All Pydantic models defined and importable
- [ ] All API routes exist (even if stubbed)
- [ ] SSE event payloads documented in code comments
- [ ] TypeScript types match Pydantic models 1:1
- [ ] Relationship `id` is a required field everywhere
- [ ] `inferred_type` is `str` (not enum)

---

## Handover to Gate 3

**Pass when:**
1. All verification items checked
2. Frontend dev confirms types match
3. No type mismatches between frontend and backend

**Handover artefact:** Locked contracts; integration can proceed safely

---

## Reference

- [API Contracts](../../_docs/_dev/_MVP/_api/01_contracts.md)
- [Data Model](../../_docs/_dev/_MVP/_schema/01_data_model.md)
- [Alignment](../../_docs/_dev/_MVP/_ALIGNMENT.md)
- [Pre-Implementation Report](../../_docs/_dev/_MVP/_PRE_IMPLEMENTATION_REPORT.md)
- [High-Level Plan](../overview/highplan.md)


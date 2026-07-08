# Proposal Response: Gate 2 — Contracts Locked

**Date:** 13 December 2025
**Submitted by:** Gate 2 Development Team
**Status:** ✅ Approved

---

## Alignment Check

| Gate 2 Requirement | Proposed Approach | Status |
|-------------------|-------------------|--------|
| Schema extraction | Contract Extraction & Snapshot (Section 1) | ✓ |
| Pydantic models | Lane A — Backend Contracts (Section 2) | ✓ |
| API route stubs | Lane A — FastAPI routers with 501 stubs | ✓ |
| Frontend types | Lane B — `types.ts` mirroring backend | ✓ |
| SSE event payloads | Lane A — SSE dataclasses/Pydantic models | ✓ |
| Cross-lane validation | Section 4 — parity review | ✓ |
| Contract snapshot | Deliverable 1 | ✓ |

---

## Non-Negotiables Check

| Non-Negotiable | How Proposal Addresses It | Status |
|----------------|---------------------------|--------|
| `inferred_type: str` | Explicitly stated: "Enforce non-negotiables directly in models" | ✓ |
| Relationship categories (5) | "`RelationshipCategory` Literal of the 5 values" | ✓ |
| `relationship_removed` payload `{ id: str }` | Explicitly stated in Section 2 | ✓ |
| Relationship `id` required | Verification: "assert `Relationship.id`" | ✓ |

**Result:** All non-negotiables explicitly addressed.

---

## What's Good

1. Contract snapshot before frontend work — prevents drift
2. Mermaid diagram — clear lane coordination visualisation
3. Risks & mitigations section — proactive risk management
4. Spec references in docstrings — traceability built in
5. Verification evidence specified — uvicorn, pytest, tsc, lint

---

## Notes

| Item | Note |
|------|------|
| Next.js security advisory | Deferred from Gate 1. Address during frontend work if patch available. Not blocking. |
| `backend/app/services/sse.py` | Reasonable location. Ensure alignment with `_structure/01_project_structure.md`. |
| pytest for model imports | Acceptable as smoke test. |

---

## Approved Plan (Final)

1. **Contract Extraction & Snapshot**
   - Read governing specs
   - Build contract table (entity, property, type, required, spec reference)
   - Store as `_dev/_plan/02_gate_contracts/contract_snapshot.md`

2. **Lane A — Backend Contracts**
   - Pydantic models under `backend/app/models/`
   - Enforce non-negotiables in models
   - FastAPI routers under `backend/app/api/` — all endpoints stubbed with 501
   - SSE event models with payload documentation
   - Verify: uvicorn import smoke test

3. **Lane B — Frontend Type Surface** (after snapshot published)
   - Mirror types in `frontend/src/lib/types.ts`
   - Discriminated unions for SSE events
   - Typed fetch helpers in `frontend/src/lib/api.ts`
   - Verify: `tsc --noEmit`, `npm run lint`

4. **Cross-Lane Validation**
   - Produce parity check
   - Verify SSE payloads match spec
   - Update snapshot with validation outcome

5. **Verification & Reporting**
   - Run Gate 2 checklist
   - Submit Work Completion Report

---

## Deliverables Confirmed

| # | Deliverable | Location |
|---|-------------|----------|
| 1 | Contract snapshot | `_dev/_plan/02_gate_contracts/contract_snapshot.md` |
| 2 | Backend models | `backend/app/models/*.py` |
| 3 | Backend route stubs | `backend/app/api/*.py` |
| 4 | Frontend types | `frontend/src/lib/types.ts` |
| 5 | Frontend API helpers | `frontend/src/lib/api.ts` |
| 6 | Work Completion Report | Per `_dev/LLM_DEVELOPMENT_GUIDE.md` |

---

## Next Steps

1. Begin with Contract Extraction (serial prerequisite)
2. Publish snapshot before Lane B starts
3. Run parity review before declaring complete
4. Submit Work Completion Report when done

---

*Proposal approved by Director of Development*


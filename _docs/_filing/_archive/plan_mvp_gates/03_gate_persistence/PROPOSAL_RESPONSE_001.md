# Proposal Response: Gate 3 — Graph Persistence Operational

**Date:** 13 December 2025
**Submitted by:** Gate 2 Development Team (continuing to Gate 3)
**Status:** ✅ Approved

---

## Alignment Check

| Gate 3 Plan Requirement | Proposed Approach | Status |
|------------------------|-------------------|--------|
| Neo4j connection + pooling | 2.1.1: Driver + smoke test | ✓ |
| Schema constraints (unique ids) | 2.1.2: CREATE CONSTRAINT with idempotent syntax | ✓ |
| Core CRUD | 2.1.3: `graph_db.py` with Cypher patterns | ✓ |
| Vector index | 2.1.4: CREATE VECTOR INDEX | ✓ |
| Similarity query (≥0.85) | 2.1.5: Query pipeline + threshold enforcement | ✓ |
| Embedding generation (Lane B) | 2.2.1: `embeddings.py` with caching | ✓ |
| Unit tests | 2.3.1–2.3.2: `test_graph_db.py`, `test_similarity.py` | ✓ |
| Verification evidence | 2.3.3: Document SHOW CONSTRAINTS/INDEXES | ✓ |

---

## Non-Negotiables Check

| Non-Negotiable | Relevance to Gate 3 | Status |
|----------------|---------------------|--------|
| `inferred_type` freeform | Stored as string in Neo4j | Ensure no enum constraint |
| Relationship `id` required | Unique constraint on Relationship.id | ✓ Planned |
| Pre-Builder similarity (≥0.85) | Core deliverable | ✓ Planned |

---

## Clarifications / Notes

| Item | Note |
|------|------|
| **Embedding model** | Use Google embedding model (user preference). Gemini 3 Pro is for LLM inference, not embeddings. |
| **Idempotent constraints** | Good — `IF NOT EXISTS` syntax allows re-runs without errors. |
| **Caching for embeddings** | Good — avoids duplicate API calls for same labels. |
| **Unit tests** | Good addition — Gate 3 introduces real logic worth testing. |

---

## Approved Plan (Final)

**Serial Lane (in order):**

1. **Neo4j driver + config** — `backend/app/config.py` or equivalent, smoke test
2. **Schema constraints** — Unique constraints on Node.id, Relationship.id, Flower.id, Session.id (idempotent)
3. **CRUD helpers** — `backend/app/services/graph_db.py` with transactional handling
4. **Vector index** — `CREATE VECTOR INDEX node_embedding ...` (idempotent)
5. **Similarity query** — Pipeline: embed → query → threshold check → mentions/timestamp update

**Parallel Lane (once driver exists):**

1. **Embeddings service** — `backend/app/services/embeddings.py` using Google embedding model, with caching
2. **Embedding unit tests** — Mock LLM for CI

**Verification:**

1. `tests/test_graph_db.py` — CRUD round-trips, constraint violations
2. `tests/test_similarity.py` — Threshold check with synthetic vectors
3. Document `SHOW CONSTRAINTS` and `SHOW INDEXES` output in Work Completion Report

---

## Deliverables Confirmed

| # | Deliverable | Location |
|---|-------------|----------|
| 1 | Neo4j driver + config | `backend/app/config.py` or services |
| 2 | Graph CRUD | `backend/app/services/graph_db.py` |
| 3 | Embedding generation | `backend/app/services/embeddings.py` |
| 4 | CRUD tests | `tests/test_graph_db.py` |
| 5 | Similarity tests | `tests/test_similarity.py` |
| 6 | Work Completion Report | With constraint/index evidence |

---

## Decision Logged

| Date | Decision | Rationale | Gate |
|------|----------|-----------|------|
| 13 Dec 2025 | Use Google embedding model (not Gemini 3 Pro) for embeddings | User preference; Gemini 3 Pro is for inference | 3 |

---

## Next Steps

1. Begin with Neo4j driver configuration (serial prerequisite)
2. Parallel lane can start once driver is operational
3. Submit Work Completion Report with SHOW CONSTRAINTS/INDEXES evidence when done

---

*Proposal approved by Director of Development*


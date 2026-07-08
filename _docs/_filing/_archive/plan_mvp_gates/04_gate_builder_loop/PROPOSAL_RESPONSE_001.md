# Proposal Response: Gate 4 — Builder End-to-End Loop

**Date:** 13 December 2025
**Submitted by:** Gate 4 Development Team
**Status:** ✅ Approved with Decisions

---

## Alignment Check

| Gate 4 Requirement | Proposed Approach | Status |
|-------------------|-------------------|--------|
| LLM client (Gemini JSON mode) | Step 1.1: `llm.py` with retry/backoff | ✓ |
| Builder agent | Step 1.2: `builder.py` from prompt spec | ✓ |
| Chunk endpoint triggers Builder | Step 2.1: Extended `/chunks` | ✓ |
| SSE manager broadcasts | Step 2.2: Connection registry + broadcast | ✓ |
| Frontend SSE handler | Step 3.1: `useSSE.ts` with reconnect | ✓ |
| State manager (Maps) | Step 3.2: `useGraphState.ts` | ✓ |
| Cytoscape rendering | Step 4.1: `GraphCanvas.tsx` | ✓ |
| FCose incremental layout | Step 4.1: No viewport reset | ✓ |
| Ghost node styling | Step 4.2: 50% opacity, dashed border | ✓ |
| Speech capture | Step 5.1: `useSpeechRecognition.ts` | ✓ |
| Chunk dispatcher | Step 5.2: `useChunkDispatcher.ts` | ✓ |
| Replay harness | Step 5.2 + 6.1: Recorded chunks | ✓ |

**Result:** Full alignment with Gate 4 plan.

---

## Decisions Made

### Question 1: Queueing Strategy

**Decision:** Direct invocation with `asyncio.create_task` is acceptable for MVP.

| Factor | Assessment |
|--------|------------|
| MVP scope | Keep simple — no additional infrastructure |
| Local-only constraint | Redis adds deployment complexity |
| Latency | `asyncio.create_task` decouples response from Builder work |
| Future-proofing | Can add queue post-MVP if needed |

**Implementation:** Chunk endpoint responds immediately with `{ chunk_id, status: "queued" }`, then `asyncio.create_task` runs Builder + SSE broadcast.

---

### Question 2: Speech UX Priority

**Decision:** Replay harness first, live speech second.

| Priority | Rationale |
|----------|-----------|
| 1. Replay harness | Deterministic testing, faster iteration, reliable demos |
| 2. Live speech | Validates real UX but harder to debug |

**Implementation:**
1. Build replay harness early
2. Validate full loop with recorded chunks
3. Then wire live speech
4. Gate 4 acceptance uses replay harness

---

## Non-Negotiables Check

| Non-Negotiable | Status |
|----------------|--------|
| `inferred_type` freeform | Ensure prompt matches spec |
| Pre-Builder similarity (≥0.85) | ✓ Calls Gate 3 service |
| Relationship `id` required | Ensure Builder generates IDs |
| Ghost node status | ✓ Builder creates ghost |

---

## Approved Plan (Final)

**Lane A: LLM Client + Builder Agent**
1. `backend/app/services/llm.py` — Gemini 3 Pro JSON mode
2. `backend/app/agents/builder.py` — Prompt + validation
3. Unit tests with mocked Gemini

**Lane B: Builder Execution Path**
1. Extended `POST /chunks`
2. `services/sse_manager.py`
3. Use `asyncio.create_task` (no Redis)

**Lane C: Frontend SSE + State**
1. `useSSE.ts` with reconnect
2. `useGraphState.ts` with Maps
3. Jest tests

**Lane D: Cytoscape Integration**
1. `GraphCanvas.tsx`
2. FCose incremental layout
3. Ghost styling

**Lane E: Speech Capture + Dispatch**
1. `useSpeechRecognition.ts`
2. `useChunkDispatcher.ts`
3. **Replay harness first**
4. Live speech after validation

---

## Deliverables Confirmed

| # | Deliverable | Location |
|---|-------------|----------|
| 1 | LLM client | `backend/app/services/llm.py` |
| 2 | Builder agent | `backend/app/agents/builder.py` |
| 3 | Chunk endpoint | `backend/app/api/chunks.py` |
| 4 | SSE manager | `backend/app/services/sse_manager.py` |
| 5 | SSE hook | `frontend/src/hooks/useSSE.ts` |
| 6 | Graph state hook | `frontend/src/hooks/useGraphState.ts` |
| 7 | Speech hook | `frontend/src/hooks/useSpeechRecognition.ts` |
| 8 | Chunk dispatcher | `frontend/src/hooks/useChunkDispatcher.ts` |
| 9 | Graph canvas | `frontend/src/components/graph/GraphCanvas.tsx` |
| 10 | Replay harness | Script/CLI |
| 11 | Tests | pytest + Jest |
| 12 | Demo recording | For handover |

---

## Decisions Logged

| Date | Decision | Rationale | Gate |
|------|----------|-----------|------|
| 13 Dec 2025 | Direct invocation + asyncio.create_task | MVP simplicity; local-only | 4 |
| 13 Dec 2025 | Replay harness first, live speech second | Deterministic testing | 4 |

---

## Next Steps

1. Proceed with implementation
2. Build replay harness early
3. Gate 4 acceptance = replay harness demo
4. Submit Work Completion Report when done

---

*Proposal approved by Director of Development*


# plasticFlower — Development Sign-Off Report

> **Historical planning document** — describes the pre-implementation design, not the current system. See [_docs/_audit/2026-07-08_audit_report.md](../../_audit/2026-07-08_audit_report.md) for current state.

> **Purpose:** Co-founder review and approval before development begins
> **Date:** 13 December 2025
> **Status:** Awaiting sign-off

---

## Executive Summary

plasticFlower is ready for implementation. All specifications are complete, the plan pack has been created, and the development approach is documented.

This report summarises:

1. What we're building
2. Locked decisions and non-negotiables
3. Development approach (gates, parallel lanes, handovers)
4. Risk acknowledgements
5. Sign-off checklist

---

## 1. What We're Building

A **local web application** that:

1. Listens to a talk/lecture via microphone
2. Transcribes speech in real-time (Web Speech API)
3. Extracts concepts and relationships using Gemini 3 Pro
4. Visualises an emergent knowledge graph that grows live
5. Organises related concepts into "Flowers" (thematic clusters)

**Key differentiator:** No predefined schema — the LLM discovers what matters.

### Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js |
| Backend | FastAPI |
| Database | Neo4j (local) |
| LLM | Gemini 3 Pro |
| Visualisation | Cytoscape.js + FCose |
| STT | Web Speech API (browser-native) |
| Real-time | SSE (server → client) |
| Hosting | Local only |

---

## 2. Locked Decisions (Non-Negotiables)

These principles were established during specification and **must not change** during implementation:

| # | Principle | Rule |
|---|-----------|------|
| 1 | **Emergent schema** | `inferred_type` is freeform (no enum constraints) |
| 2 | **Flower formation** | Requires 3+ nodes AND 2+ internal connections |
| 3 | **Merge rules** | Only true duplicates (synonyms/acronyms/spelling), never hierarchy flattening |
| 4 | **Relationship categories** | Exactly 5: CAUSAL, STRUCTURAL, COMPARATIVE, TEMPORAL, ASSOCIATIVE |
| 5 | **Gardener cadence** | Fixed every 90 seconds (not adaptive) |
| 6 | **Relationship identity** | Relationship objects include stable `id`; removal uses `{ id }` |
| 7 | **Graph noise policy** | Uncertainty biases towards prune/expel, not confirm |
| 8 | **Pre-Builder similarity** | >= 0.85 threshold; match → increment mentions, not create |

### Explicitly Deferred (Post-MVP)

| Feature | Reason |
|---------|--------|
| Contradiction detection | Complexity; not core to MVP value |
| Historian Agent | For long talks; MVP targets single sessions |
| Linker Agent | Real-time cross-chunk; Gardener handles this for MVP |
| Advanced exports | GraphML, Mermaid, CSV |
| Full density metrics | Simple edge count sufficient for MVP |

---

## 3. Development Approach

### Gate-Based Delivery

Development proceeds through **7 gates**, each with explicit entry/exit criteria and handover checkpoints.

| Gate | Objective | Entry | Exit |
|------|-----------|-------|------|
| 1 | Dev environment green | Gate 0 signed off | All services start locally |
| 2 | Contracts locked | Gate 1 passed | API + SSE payloads final |
| 3 | Graph persistence operational | Gate 2 passed | Neo4j CRUD + similarity works |
| 4 | Builder end-to-end loop | Gate 3 passed | Speech → graph → Cytoscape live |
| 5 | Gardener refinement loop | Gate 4 passed | 90s cycles; Flowers form |
| 6 | Exports + session lifecycle | Gate 5 passed | All exports work; sessions persist |
| 7 | MVP readiness | Gate 6 passed | Edge cases pass; non-negotiables verified |

### Parallel vs Serial

```
Gate 1 (Dev Env)
    │
    ▼
Gate 2 (Contracts) ─────────────────────┐
    │                                   │
    ▼                                   ▼
Gate 3 (Persistence)           Frontend Scaffold
    │                                   │
    └───────────────┬───────────────────┘
                    ▼
              Gate 4 (Builder Loop)
                    │
                    ▼
              Gate 5 (Gardener Loop)
                    │
                    ▼
              Gate 6 (Exports)
                    │
                    ▼
              Gate 7 (MVP Ready)
```

**Key parallel opportunity:** After Gate 2, backend persistence work and frontend UI work can proceed simultaneously.

### Plan Pack Location

All detailed plans are in `_dev/_plan/`:

> **Note (2026-07):** the `_dev/_plan/` tree referenced below was never committed to this repository. The plan pack was salvaged to `_docs/_filing/_archive/plan_mvp_gates/` — use the "Salvaged location" column.

| Document | Path | Salvaged location |
|----------|------|-------------------|
| High-level plan | `_dev/_plan/overview/highplan.md` | `_docs/_filing/_archive/plan_mvp_gates/overview/highplan.md` |
| Gate 1 plan | `_dev/_plan/01_gate_dev_env/plan.md` | `_docs/_filing/_archive/plan_mvp_gates/01_gate_dev_env/plan.md` |
| Gate 2 plan | `_dev/_plan/02_gate_contracts/plan.md` | `_docs/_filing/_archive/plan_mvp_gates/02_gate_contracts/plan.md` |
| Gate 3 plan | `_dev/_plan/03_gate_persistence/plan.md` | `_docs/_filing/_archive/plan_mvp_gates/03_gate_persistence/plan.md` |
| Gate 4 plan | `_dev/_plan/04_gate_builder_loop/plan.md` | `_docs/_filing/_archive/plan_mvp_gates/04_gate_builder_loop/plan.md` |
| Gate 5 plan | `_dev/_plan/05_gate_gardener_loop/plan.md` | `_docs/_filing/_archive/plan_mvp_gates/05_gate_gardener_loop/plan.md` |
| Gate 6 plan | `_dev/_plan/06_gate_exports/plan.md` | `_docs/_filing/_archive/plan_mvp_gates/06_gate_exports/plan.md` |
| Gate 7 plan | `_dev/_plan/07_gate_mvp_ready/plan.md` | `_docs/_filing/_archive/plan_mvp_gates/07_gate_mvp_ready/plan.md` |

---

## 4. Specification Documents (Complete)

All specifications are finalised and located in `_docs/_dev/_MVP/`:

| Category | Documents | Status |
|----------|-----------|--------|
| **Tier 1: Start Here** | Implementation Brief, Alignment | ✓ Complete |
| **Tier 2: Design** | Concept, Scope, Data Model, Schema Rationale, Architecture | ✓ Complete |
| **Tier 3: Implementation** | Builder Prompt, Gardener Prompt, API Contracts, Frontend Data Flow, Project Structure | ✓ Complete |
| **Tier 4: History** | Decision Log (19 decisions), Conversations (7 key discussions), Drift Report, Pre-Implementation Report | ✓ Complete |

---

## 5. Risk Acknowledgements

| Risk | Mitigation |
|------|------------|
| **Web Speech API quality** | Deepgram abstracted as upgrade path; acceptable for MVP |
| **LLM output reliability** | Strict JSON validation; invalid outputs logged and discarded |
| **Graph noise (too many nodes)** | Pre-Builder similarity check; Gardener prunes under uncertainty |
| **FCose performance at scale** | Z-filtering reduces visible nodes; scaling optimisations post-MVP |
| **SSE connection drops** | Auto-reconnect with exponential backoff; full state replace on reconnect |

---

## 6. Success Criteria

MVP is complete when:

| # | Criterion |
|---|-----------|
| 1 | User can start a session and speak into microphone |
| 2 | Speech is transcribed and displayed |
| 3 | Concepts appear as nodes in real-time (ghost state) |
| 4 | Relationships appear between concepts |
| 5 | Every 90 seconds, Gardener refines the graph |
| 6 | Ghost nodes become solid after Gardener review |
| 7 | Flowers form around thematic clusters |
| 8 | User can filter the view (Z-level) |
| 9 | User can export session data |
| 10 | Session persists and can be restored |

---

## 7. Open Decision Points

These decisions should be made early in development but are not blockers to starting:

| Decision | Options | Recommendation |
|----------|---------|----------------|
| **Embedding provider** | Google Embedding API vs local model | Google API (simpler, aligns with Gemini) |
| **Relationship ID format** | UUID vs deterministic | UUID (simpler, no collision risk) |

---

## 8. Co-Founder Sign-Off

By signing below, I confirm:

### Specifications

- [ ] I have reviewed the Implementation Brief (`_docs/_dev/_MVP/_IMPLEMENTATION_BRIEF.md`)
- [ ] I have reviewed the Alignment document (`_docs/_dev/_MVP/_ALIGNMENT.md`)
- [ ] I have reviewed the Pre-Implementation Report (`_docs/_dev/_MVP/_PRE_IMPLEMENTATION_REPORT.md`)

### Non-Negotiables

- [ ] I confirm `inferred_type` must remain freeform (no enum)
- [ ] I confirm Flower formation requires 3+ nodes AND 2+ internal connections
- [ ] I confirm merge is only for true duplicates, not hierarchies
- [ ] I confirm relationship categories are exactly: CAUSAL, STRUCTURAL, COMPARATIVE, TEMPORAL, ASSOCIATIVE
- [ ] I confirm Gardener cadence is fixed at 90 seconds
- [ ] I confirm uncertainty should bias towards prune/expel
- [ ] I confirm Relationship `id` is required and `relationship_removed` uses `{ id }`

### Scope

- [ ] I confirm contradiction detection is post-MVP
- [ ] I confirm the deferred features list is acceptable
- [ ] I confirm MVP success criteria are correct

### Development Approach

- [ ] I have reviewed the gate-based plan pack in `_dev/_plan/` *(salvaged to `_docs/_filing/_archive/plan_mvp_gates/`)*
- [ ] I approve the parallel vs serial development approach
- [ ] I understand handover gates require explicit sign-off

### Approval

**Signed:** ___________________________

**Date:** ___________________________

**Comments:**

> 
> 
> 

---

## Reference Documents

| Document | Path |
|----------|------|
| Implementation Brief | `_docs/_dev/_MVP/_IMPLEMENTATION_BRIEF.md` |
| Alignment | `_docs/_dev/_MVP/_ALIGNMENT.md` |
| Pre-Implementation Report | `_docs/_dev/_MVP/_PRE_IMPLEMENTATION_REPORT.md` |
| Handover | `_docs/_dev/_MVP/_HANDOVER.md` |
| Decision Log | `_docs/_dev/_MVP/_DECISION_LOG.md` |
| Plan Pack | `_dev/_plan/README.md` *(salvaged to `_docs/_filing/_archive/plan_mvp_gates/README.md`)* |

---

*Development may begin once this report is signed off.*


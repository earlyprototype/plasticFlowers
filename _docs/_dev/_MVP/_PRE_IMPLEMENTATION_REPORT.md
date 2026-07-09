# plasticFlower — Pre-Implementation Report

> **Historical planning document** — describes the pre-implementation design, not the current system. See [_docs/_audit/2026-07-08_audit_report.md](../../_audit/2026-07-08_audit_report.md) for current state.

> **Purpose:** Final review checkpoint before implementation begins
> **Status:** Ready for sign-off
> **Date:** 13 December 2025
> **Version:** 1.0

---

## Executive Summary

plasticFlower is specified as a **local-only** Next.js + FastAPI application that captures live speech, extracts an emergent knowledge graph using Gemini 3 Pro, and renders it in real time via SSE into Cytoscape.js with FCose layout.

This report records the final pre-build clarifications agreed during review:

1. Contradiction detection is **post-MVP**
2. Gardener cadence is **fixed at 90 seconds**
3. Graph noise management biases towards **expulsion (prune) under uncertainty**
4. Relationship identity is hardened via a required **Relationship `id`**, with unambiguous SSE removal
5. Pre-Builder similarity check follows a single deterministic rule to prevent duplicates

---

## Locked MVP Decisions (Clarifications)

1. **Contradiction detection**
   1. Status: **Post-MVP**
   2. Action: Removed from MVP scope and architecture narratives (kept as a post-MVP objective)

2. **Gardener trigger**
   1. Status: **Fixed**
   2. Rule: Runs every **90 seconds** only (no secondary trigger such as “every N new nodes”)

3. **Graph noise policy**
   1. Rule: Under uncertainty, Gardener should **prune/expel** rather than confirm
   2. Constraint: Merge remains **true duplicates only** (no hierarchy flattening)

4. **Local-only clarification**
   1. “Local only” is a **hosting/deployment** constraint (localhost services)
   2. It is **not** a blanket privacy guarantee (notably STT behaviour depends on browser/provider)

5. **Pre-Builder similarity check**
   1. Threshold: **>= 0.85 similarity**
   2. If match found: **do not create** a new node; increment `mentions`; append timestamp; use matched id for relationships

6. **Relationship identity**
   1. Relationship objects include a required **`id`**
   2. `relationship_removed` SSE payload is `{ id }` (unambiguous delete)
   3. Frontend relationship Map is keyed by `rel.id` (not derived composite keys)

---

## Spec Delta Summary (Files Updated)

1. `_docs/_dev/_MVP/_overview/02_scope.md`
   1. Removed contradiction detection from MVP scope line item
   2. Added contradiction detection as post-MVP

2. `_docs/_dev/_MVP/_architecture/01_system_overview.md`
   1. Removed “detect contradictions” from Gardener responsibilities in the flow diagram

3. `_docs/_dev/_MVP/_architecture/02_agents.md`
   1. Removed “contradiction flags” from Gardener output responsibilities
   2. Locked Gardener trigger to fixed 90 seconds
   3. Tightened pre-Builder similarity rule with deterministic behaviour

4. `_docs/_dev/_MVP/_prompts/02_gardener.md`
   1. Clarified PRUNE vs MERGE wording (duplicates are MERGE, not PRUNE)
   2. Flipped uncertainty guidance to prune under uncertainty

5. `_docs/_dev/_MVP/_api/01_contracts.md`
   1. Added Relationship `id` to the Relationship schema
   2. Changed `relationship_removed` SSE payload to `{ id }`

6. `_docs/_dev/_MVP/_frontend/01_data_flow.md`
   1. Key relationships by `rel.id`
   2. Update/remove relationships by id (including `relationship_removed`)
   3. Use `rel.id` for Cytoscape edge ids

7. `_docs/_dev/_MVP/_schema/01_data_model.md`
   1. Added Relationship `id` as a core property

---

## Implementation Readiness Checklist (Pre-Code)

1. **Alignment**
   1. Read `_ALIGNMENT.md`
   2. Confirm emergent schema, Flower criteria, and merge rules are treated as non-negotiable

2. **Contracts**
   1. Review `_api/01_contracts.md` for endpoint + SSE payload accuracy
   2. Review `_frontend/01_data_flow.md` for state/keying expectations

3. **Infrastructure**
   1. Neo4j local instance available (Docker Compose recommended)
   2. Environment variables planned:
      1. `NEO4J_PASSWORD`
      2. `GEMINI_API_KEY`

---

## Verification Checklist (Must Pass)

1. **Emergent schema**
   1. `inferred_type` remains freeform (no enum constraints anywhere)

2. **Flowers**
   1. Flower formation requires **3+ nodes AND 2+ internal connections**

3. **Merge**
   1. Merge only true duplicates (synonyms, acronyms/expansions, spelling variants)
   2. Do not merge hierarchical relationships (preserve specificity)

4. **Relationships**
   1. Relationship categories are exactly: CAUSAL, STRUCTURAL, COMPARATIVE, TEMPORAL, ASSOCIATIVE
   2. Relationship objects include a stable `id`
   3. `relationship_removed` deletes by `{ id }` and is handled by the frontend without ambiguity

5. **Scheduler**
   1. Gardener runs every **90 seconds** (fixed cadence)

6. **SSE recovery**
   1. Frontend reconnects with exponential backoff
   2. On reconnect, frontend fetches full graph and **replaces state**

7. **Exports**
   1. JSON export includes graph + transcript + metadata
   2. Transcript exports include plain text + VTT
   3. Markdown export produces a summary aligned with Flowers

---

## Edge Cases & Tests (Integrate During Build)

1. STT instability (interim vs final transcript changes)
2. Long pauses (no chunks for extended periods)
3. Invalid/partial LLM outputs (JSON parsing failures, timeouts)
4. Duplicate labels (punctuation/hyphenation/plurals)
5. Graph size growth (200–500 nodes) and FCose incremental layout performance
6. SSE drop and state recovery correctness
7. Multi-tab subscriptions to the same session
8. Export while session is live vs ended

---

## Post-MVP (Explicitly Deferred)

1. Contradiction detection (flag/surface contradictory claims)
2. Historian Agent
3. Linker Agent
4. Advanced exports and full density metrics

---

## Sign-off

- [ ] I confirm contradiction detection is post-MVP
- [ ] I confirm Gardener cadence is fixed at 90 seconds
- [ ] I confirm uncertainty biases towards prune/expel
- [ ] I confirm Relationship `id` is required and `relationship_removed` uses `{ id }`
- [ ] I confirm the pre-Builder similarity check behaviour (>= 0.85) is correct
- [ ] I confirm the non-negotiables in `_ALIGNMENT.md` are unchanged



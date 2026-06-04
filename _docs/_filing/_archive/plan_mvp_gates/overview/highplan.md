plasticFlower — High-Level Development Plan (MVP)
Purpose
This plan is the top-level delivery map that will be decomposed into higher‑resolution plans per phase/workstream.

Non‑negotiables (must remain true throughout)
Emergent schema: inferred_type is freeform (no enum constraints).
Flowers: form only when 3+ nodes AND 2+ internal connections.
Merge: only true duplicates (synonyms/acronyms/spelling variants), never hierarchy flattening.
Relationship categories: exactly CAUSAL, STRUCTURAL, COMPARATIVE, TEMPORAL, ASSOCIATIVE.
Gardener cadence: fixed every 90 seconds.
Contradiction detection: post‑MVP.
Relationship identity: Relationship objects include a stable id; relationship_removed removes by { id }.
Workstreams (parallelisable)
Backend/API workstream (FastAPI)
Session CRUD + chunk ingestion + SSE + graph read + export endpoints
Scheduler + SSE manager
Graph/DB workstream (Neo4j)
Data models + constraints/indexes
Vector index + similarity query path
Bridge derivation queries
LLM/Agents workstream (Gemini 3 Pro)
LLM client + structured JSON validation
Builder integration (per chunk)
Gardener integration (90s cycles)
Frontend workstream (Next.js + Cytoscape/FCose)
Session list + live session page skeleton
Speech capture + chunk dispatcher
SSE handling + state manager (Maps)
Cytoscape rendering + incremental layout + UI panels + Z‑filters
QA/Acceptance workstream
Replay harness (recorded transcript chunks) for repeatable runs
Edge-case tests integrated per milestone (SSE drop, invalid JSON, scaling, exports, etc.)
Serial dependencies (must occur in sequence)
Contracts first
API shapes + SSE event payloads must be final before frontend integration.
Relationship id must exist before implementing add/remove flows.
Persistence before intelligence
Neo4j schema + core graph operations must exist before Builder/Gardener can safely mutate state.
Builder before Gardener
Gardener depends on graph state produced by Builder and stable merge/prune semantics.
End‑to‑end before exports polishing
Exports should be validated against a stable, end‑to‑end session lifecycle.
Dependency map (high level)
Gate0_SignedOff
DevEnv_RepoAndRuntime
Backend_ScaffoldAndContracts
Frontend_Scaffold
Neo4j_SchemaAndIndexes
SSE_StableContract
GraphOps_CRUDAndQueries
Similarity_PreBuilderCheck
Builder_Integration
Frontend_SSEIntegration
LiveLoop_SpeechToGraph
Gardener_Integration_90s
Flowers_FormationAndUpdates
Exports_JSON_VTT_MD
GateFinal_MVPReady
Handover gates (review checkpoints)
Gate 0 — Sign-off (done)
Pre‑implementation report accepted.
Gate 1 — Dev environment green
Backend starts locally.
Frontend starts locally.
Neo4j reachable (docker compose or equivalent).
Minimal “hello” endpoint + basic page render confirmed.
Gate 2 — Contracts locked (integration-safe)
SSE event list and payloads are final, including relationship_removed: { id }.
Frontend state keying strategy matches contracts (rel.id).
Gate 3 — Graph persistence operational
Create/read/update/delete nodes and relationships against Neo4j.
Vector index exists; similarity query returns stable results.
Gate 4 — Builder end-to-end loop
Speech (or replay) produces chunks.
Chunk triggers Builder.
Nodes/relationships persist.
SSE updates render live in Cytoscape.
Gate 5 — Gardener refinement loop
Gardener runs every 90 seconds (fixed).
Merge rules preserve specificity; uncertainty biases to prune.
Flowers form only when dual criteria met.
Gate 6 — Exports + session lifecycle
Exports match: JSON, transcript (plain + VTT), Markdown.
Session end/restore works.
Gate 7 — MVP readiness
Edge cases pass (SSE drop/reconnect, invalid JSON, scaling smoke).
Non‑negotiables pass checklist.
Parallel development opportunities (where to split work)
Backend scaffolding can proceed in parallel with frontend scaffolding once Gate 2 contracts are locked.
Neo4j schema/index work can run in parallel with frontend UI work, provided the contract is stable.
LLM client + JSON validation can run in parallel with SSE manager + API skeleton, provided models are agreed.
Replay harness can start immediately and continue alongside all phases (it reduces iteration cost).
High-level deliverables per phase (feed into higher-resolution plans)
Phase A (Foundation): dev environment + repo skeleton + docker compose alignment.
Phase B (Contracts + Core API): sessions/chunks/stream/graph endpoints + SSE manager.
Phase C (Graph/DB): Neo4j CRUD + vector index + bridge queries.
Phase D (Frontend loop): speech → chunks → SSE → Cytoscape live render.
Phase E (Agents): Builder integration first, then Gardener integration.
Phase F (Exports + hardening): export endpoints + UI + edge-case pass.
Open decision points (must be chosen early, but not blockers to planning)
Embedding provider for similarity check (API-based vs local), while keeping “local-only” as deployment constraint.
Relationship id generation (UUID vs deterministic id) aligned with desired dedup/evidence strategy.

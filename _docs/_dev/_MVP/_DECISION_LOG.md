# plasticFlower — Decision Log

> Chronological record of key decisions with context.

---

## DEC-001: Project Name

| | |
|---|---|
| **Decision** | plasticFlower |
| **Date** | Dec 2024 |
| **Context** | User proposed rename from "Live Innovation Literacy Mapper" |
| **Rationale** | Domain-agnostic, evocative of growth/emergence |

---

## DEC-002: Domain Agnostic Schema

| | |
|---|---|
| **Decision** | Emergent schema — LLM determines node types |
| **Date** | Dec 2024 |
| **Alternatives** | Predefined types (like knowledge-graph-kit) |
| **Rationale** | User wanted system to work for any talk topic without configuration |

---

## DEC-003: Two-Agent Architecture

| | |
|---|---|
| **Decision** | Builder (fast, per-chunk) + Gardener (slow, periodic) |
| **Date** | Dec 2024 |
| **Alternatives** | Single agent, three agents (with Linker) |
| **Rationale** | Balance immediate feedback with quality review. Linker deferred to post-MVP. |

---

## DEC-004: Gardener Interval

| | |
|---|---|
| **Decision** | 90 seconds |
| **Date** | Dec 2024 |
| **Alternatives** | 3-5 minutes (original proposal), adaptive triggering |
| **Rationale** | User wanted specific number for MVP. Adaptive deferred. |

---

## DEC-005: Relationship Type Constraint

| | |
|---|---|
| **Decision** | 5 abstract categories + natural language description |
| **Date** | Dec 2024 |
| **Alternatives** | Unconstrained (LLM chooses freely), predefined list of 20+ |
| **Problem** | User concerned unconstrained devolves to meaningless fragmentation |
| **Rationale** | Abstract categories enable analysis; natural language preserves nuance; ASSOCIATIVE catches uncertainty |

**Categories:** CAUSAL, STRUCTURAL, COMPARATIVE, TEMPORAL, ASSOCIATIVE

---

## DEC-006: Flower Clustering Approach

| | |
|---|---|
| **Decision** | LLM semantic clustering + algorithmic density (edge count) |
| **Date** | Dec 2024 |
| **Alternatives** | LLM only, Algorithm only (Leiden) |
| **Discussion** | User identified these as complementary dimensions, not alternatives |
| **Rationale** | Semantic = meaning, Density = connectivity. Both matter independently. |

---

## DEC-007: STT Provider

| | |
|---|---|
| **Decision** | Web Speech API (primary), Deepgram (abstracted upgrade path) |
| **Date** | Dec 2024 |
| **Alternatives** | Deepgram only, Whisper local |
| **Rationale** | Free, zero setup, streaming. Quality acceptable for MVP. |

---

## DEC-008: Graph Visualisation Library

| | |
|---|---|
| **Decision** | Cytoscape.js with FCose layout |
| **Date** | Dec 2024 |
| **Alternatives** | React Flow, vis-network |
| **Rationale** | FCose handles compound nodes (Flowers) and stable live updates |

---

## DEC-009: Hosting

| | |
|---|---|
| **Decision** | Local only |
| **Date** | Dec 2024 |
| **Alternatives** | Cloud (Vercel + Railway) |
| **Rationale** | User preference |

---

## DEC-010: Session Naming

| | |
|---|---|
| **Decision** | User-provided with timestamp fallback |
| **Date** | Dec 2024 |
| **Alternatives** | Auto-generated only |
| **Rationale** | User preference |

---

## DEC-011: MVP Export Formats

| | |
|---|---|
| **Decision** | JSON, transcript (plain + VTT), Markdown summary |
| **Date** | Dec 2024 |
| **Deferred** | GraphML, Mermaid, CSV (post-MVP) |
| **Rationale** | Essential formats only for MVP |

---

## DEC-012: Flower Bridges

| | |
|---|---|
| **Decision** | Derived at query-time, not stored |
| **Date** | Dec 2024 |
| **Alternatives** | Explicit storage |
| **Rationale** | Query is simple, storage requires maintenance |

---

## DEC-013: Node Status in Database

| | |
|---|---|
| **Decision** | Store ghost/solid status in database |
| **Date** | Dec 2024 |
| **Alternatives** | Frontend-only state |
| **Rationale** | Persistence across sessions, Gardener can change status |

---

## DEC-014: Diarisation

| | |
|---|---|
| **Decision** | Excluded from all phases |
| **Date** | Dec 2024 |
| **Rationale** | Single speaker use case only |

---

## DEC-015: Alignment Process

| | |
|---|---|
| **Decision** | Mandatory reading + checklist before specification work |
| **Date** | Dec 2024 |
| **Trigger** | Post-handover drift identified (Drift Report 001) |
| **Problem** | Specifications violated emergent schema, Flower criteria, merge rules |
| **Solution** | `_ALIGNMENT.md` created with non-negotiable principles and verification checklist |
| **Rationale** | Summary documents are not sufficient; LLMs must read source decisions |

**Related:** `_docs/_dev/_MVP/_ALIGNMENT.md`, `_docs/_dev/_MVP/_DRIFT_REPORT_001.md`

---

## DEC-016: Builder Extraction Scope

| | |
|---|---|
| **Decision** | Entities + chunk-local relationships |
| **Date** | Dec 2025 |
| **Alternatives** | Entities only (Gardener infers relationships) |
| **Rationale** | Relationships like "X enables Y" are clearest when both appear in the same chunk. Waiting 90s loses immediate context. "Chunk-local" constraint naturally limits scope. |

---

## DEC-017: Category Prompt Structure

| | |
|---|---|
| **Decision** | Definitions + 1 example each |
| **Date** | Dec 2025 |
| **Alternatives** | Labels only, Definitions only |
| **Rationale** | Most guidance for consistent categorisation. Examples anchor LLM interpretation. Token cost negligible (~50 tokens). |

---

## DEC-018: Agent Output Format

| | |
|---|---|
| **Decision** | Strict JSON schema |
| **Date** | Dec 2025 |
| **Alternatives** | Free-form text, Markdown structure |
| **Rationale** | Reliable parsing, easy validation. Gemini 3 Pro supports structured output mode. Failed parses can be logged and retried. |

---

## DEC-019: Graph Context Passing

| | |
|---|---|
| **Decision** | Labels only, grouped by inferred type |
| **Date** | Dec 2025 |
| **Alternatives** | No context, Full node details, Embedding similarity search |
| **Rationale** | Compact (~50 nodes in ~200 tokens). Sufficient for duplicate matching. Type grouping aids consistency. Scales to ~500 nodes before needing similarity search (post-MVP). |

---

## DEC-020: Builder Latency Target

| | |
|---|---|
| **Decision** | <10 seconds (speech to node visible) |
| **Date** | Dec 2025 |
| **Previous** | <3 seconds (initial specification) |
| **Trigger** | Technical risk assessment identified <3s as aggressive |
| **Rationale** | 10s provides headroom for embedding + similarity + LLM chain while maintaining "live" feel. P90 target. P99 may reach ~15s. |

**Related:** `_docs/_dev/_MVP/_TECHNICAL_CHALLENGES.md`


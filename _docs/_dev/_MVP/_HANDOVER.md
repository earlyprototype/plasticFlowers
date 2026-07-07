# plasticFlower — Development Handover

> **Version:** 3.0
> **Created:** December 2024
> **Updated:** December 2025
> **Purpose:** Context preservation for continued development
> **Status:** All specifications complete, ready for implementation

---

## How to Use This Document

1. **Read Section A (Essential)** — Required before any work
2. **Read Section B (Context)** — For understanding decisions
3. **Reference Section C** — As needed during work
4. **Check Section D** — For unresolved items and next steps

---

# SECTION A: ESSENTIAL READING

> **Read these files IN ORDER before continuing work.**

## A1. Reading Order

| Order | Document | Path | Why Essential |
|-------|----------|------|---------------|
| 1 | **This handover** | `_docs/_dev/_MVP/_HANDOVER.md` | Entry point |
| 2 | **Alignment Document** | `_docs/_dev/_MVP/_ALIGNMENT.md` | Non-negotiable principles and checklist |
| 3 | **Concept** | `_docs/_dev/_MVP/_overview/01_concept.md` | What we're building |
| 4 | **Data Model** | `_docs/_dev/_MVP/_schema/01_data_model.md` | Core schema (everything depends on this) |
| 5 | **Decision Log** | `_docs/_dev/_MVP/_DECISION_LOG.md` | All choices with rationale |
| 6 | **Technical Challenges** | `_docs/_dev/_MVP/_TECHNICAL_CHALLENGES.md` | Risk assessment and mitigations |
| 7 | **Conversations** | `_docs/_dev/_MVP/_CONVERSATIONS.md` | Key discussions that shaped decisions |

**Estimated read time:** 15-20 minutes

## A2. Document Dependency Map

```
                    ┌─────────────────┐
                    │   HANDOVER      │
                    │   (start here)  │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │    CONCEPT      │
                    │  (what we build)│
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
      ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
      │  DATA MODEL  │ │   AGENTS     │ │   SCOPE      │
      │  (schema)    │ │  (how)       │ │  (what)      │
      └──────┬───────┘ └──────┬───────┘ └──────────────┘
             │                │
             └───────┬────────┘
                     ▼
             ┌──────────────┐
             │  DECISIONS   │
             │  (why)       │
             └──────────────┘
```

## A3. Key Terminology

| Term | Definition |
|------|------------|
| **plasticFlower** | The project name. A live knowledge graph from speech. |
| **Node** | A concept/term extracted from speech |
| **Flower** | A thematic cluster of related nodes |
| **Builder Agent** | Fast LLM that extracts nodes from each chunk |
| **Gardener Agent** | Slow LLM that reviews, merges, clusters every 90s |
| **Chunk** | ~3-5 sentences of transcribed speech |
| **Ghost node** | Newly created, not yet reviewed by Gardener |
| **Solid node** | Confirmed by Gardener review |
| **Stem node** | The central/highest-connectivity node in a Flower |
| **Bridge** | A relationship connecting two different Flowers |
| **Emergent schema** | Types discovered by LLM, not predefined |

---

# SECTION B: CONTEXT & DECISIONS

> **Read for understanding WHY decisions were made.**

## B1. Critical Decisions with Rationale

### Relationship Categories (Important)

**Problem:** Unconstrained LLM relationship types fragment into meaninglessness ("enables", "allows", "permits" as separate types).

**Solution:** 5 abstract categories + natural language description

| Category | Captures | Example |
|----------|----------|---------|
| CAUSAL | A influences B | "enables", "blocks", "causes" |
| STRUCTURAL | A is part of B | "contains", "belongs to" |
| COMPARATIVE | A relates to B by similarity | "contrasts", "extends" |
| TEMPORAL | A before/after B | "precedes", "triggers" |
| ASSOCIATIVE | Unclear relationship (fallback) | "relates to" |

**Why this works:** Broad enough to accommodate reality, narrow enough to enable analysis.

---

### Flower Clustering (Important)

**Problem:** Are Flowers algorithmic (density) or semantic (meaning)?

**Resolution:** Both dimensions matter independently.

| Dimension | Method | What it measures |
|-----------|--------|------------------|
| Semantic coherence | LLM | Do these concepts share meaning? |
| Structural density | Edge count | Are they interconnected? |

**Implications:**
- High semantic + high density = confident Flower
- High semantic + low density = emerging theme
- Low semantic + high density = potential conflation

**MVP:** LLM for themes + simple edge count for density.

---

### Why Web Speech API

**Decision:** Use free browser-native STT for MVP.

**Why:** Zero cost, zero setup, streaming capable.

**Trade-off:** Quality not as good as Deepgram. Acceptable for MVP.

**Abstraction:** STT provider is abstracted, easy to swap later.

---

## B2. What We Learned from Research

| Source | Confidence | What We're Using |
|--------|------------|------------------|
| GraphRAG (Microsoft) | 10/10 | Prompt patterns for extraction |
| Graphiti (Zep) | 8/10 | Streaming architecture, Neo4j patterns |
| knowledge-graph-kit (internal) | 7/10 | Merge/validation logic |
| Visualisation repos | 6/10 | UX reference only |

**Full analysis:** `_discovery/_repo/_LEVERAGE_GUIDE.md`

---

# SECTION C: REFERENCE MATERIALS

> **Consult as needed during work.**

## C1. All Documentation

### Core Specifications

| Document | Path | Status |
|----------|------|--------|
| Concept | `_docs/_dev/_MVP/_overview/01_concept.md` | ✓ Complete |
| Scope | `_docs/_dev/_MVP/_overview/02_scope.md` | ✓ Complete |
| Decisions | `_docs/_dev/_MVP/_overview/03_decisions.md` | ✓ Complete |
| System Architecture | `_docs/_dev/_MVP/_architecture/01_system_overview.md` | ✓ Complete |
| Agent Architecture | `_docs/_dev/_MVP/_architecture/02_agents.md` | ✓ Complete |
| Data Model | `_docs/_dev/_MVP/_schema/01_data_model.md` | ✓ Complete |
| Schema Rationale | `_docs/_dev/_MVP/_schema/02_design_rationale.md` | ✓ Complete |

### Discovery Materials

| Document | Path | Purpose |
|----------|------|---------|
| Repository Index | `_discovery/_repo/_INDEX.md` | All reference repos |
| Leverage Guide | `_discovery/_repo/_LEVERAGE_GUIDE.md` | What to extract |
| Clone Script | `_discovery/_repo/_CLONE.ps1` | Get the repos |

### Implementation Specifications

| Folder | Path | Status |
|--------|------|--------|
| Prompts | `_docs/_dev/_MVP/_prompts/` | ✓ Complete |
| API | `_docs/_dev/_MVP/_api/` | ✓ Complete |
| Frontend | `_docs/_dev/_MVP/_frontend/` | ✓ Complete |
| Structure | `_docs/_dev/_MVP/_structure/` | ✓ Complete |

### Process Documents

| Document | Path | Purpose |
|----------|------|---------|
| Progress Log | `_docs/_dev/_MVP/_PROGRESS.md` | Tracks completed work |
| Drift Report | `_docs/_dev/_MVP/_DRIFT_REPORT_001.md` | Quality issues found/fixed |
| Alignment | `_docs/_dev/_MVP/_ALIGNMENT.md` | Non-negotiable principles |
| Technical Challenges | `_docs/_dev/_MVP/_TECHNICAL_CHALLENGES.md` | Risk assessment, mitigations, metrics |
| Implementation Brief | `_docs/_dev/_MVP/_IMPLEMENTATION_BRIEF.md` | Handoff for implementation |

## C2. Technology Choices

| Component | Choice |
|-----------|--------|
| STT (primary) | Web Speech API |
| STT (upgrade) | Deepgram |
| LLM | Gemini 3 Pro |
| Graph store | Neo4j (local) |
| Visualisation | Cytoscape.js + FCose |
| Frontend | Next.js |
| Backend | FastAPI |
| Hosting | Local only |

## C3. User Preferences

| Preference | Detail |
|------------|--------|
| Communication | Step-by-step discussion, not document dumps |
| ADHD | Needs clear, broken-down steps |
| Confirmation | Ask before making changes |
| Involvement | Consult on decisions |
| Language | UK English only |
| Environment | Windows PowerShell |

---

# SECTION D: CONTINUATION GUIDE

> **What to do next.**

## D1. Current State

**All specifications complete.** Ready for implementation.

| Phase | Status |
|-------|--------|
| Discovery | ✓ Complete |
| Core specifications | ✓ Complete |
| Agent prompts | ✓ Complete |
| API contracts | ✓ Complete |
| Frontend data flow | ✓ Complete |
| Project structure | ✓ Complete |
| Implementation | **Next** |

## D2. Resolved Questions (Decisions Made)

| Question | Resolution | Reference |
|----------|------------|-----------|
| What should Builder extract? | Entities + chunk-local relationships | DEC-016 |
| How to structure category prompt? | Definitions + 1 example each | DEC-017 |
| What output format? | Strict JSON schema | DEC-018 |
| How to pass graph context? | Labels only, grouped by type | DEC-019 |

## D3. Next Steps

1. **Read `_IMPLEMENTATION_BRIEF.md`** — comprehensive handoff for implementation
2. **Begin implementation** — follow project structure in `_structure/01_project_structure.md`

## D4. How to Continue This Session

**Say to the new context:**

> "I'm continuing plasticFlower development. Read `_docs/_dev/_MVP/_IMPLEMENTATION_BRIEF.md` first — it contains everything needed to begin implementation. Then read `_docs/_dev/_MVP/_ALIGNMENT.md` for non-negotiable principles."

---

# SECTION E: FOLDER STRUCTURE

```
_plasticFlower/
├── _docs/
│   └── _dev/
│       └── _MVP/
│           ├── _HANDOVER.md              ← Context document
│           ├── _IMPLEMENTATION_BRIEF.md  ← START HERE for implementation
│           ├── _ALIGNMENT.md             ← Non-negotiable principles
│           ├── _DECISION_LOG.md          ← All 20 decisions
│           ├── _TECHNICAL_CHALLENGES.md  ← Risk assessment
│           ├── _CONVERSATIONS.md         ← 7 key discussions
│           ├── _PROGRESS.md              ← Work completed
│           ├── _DRIFT_REPORT_001.md      ← Quality review
│           │
│           ├── _overview/
│           │   ├── 01_concept.md         ✓
│           │   ├── 02_scope.md           ✓
│           │   └── 03_decisions.md       ✓
│           │
│           ├── _architecture/
│           │   ├── 01_system_overview.md ✓
│           │   └── 02_agents.md          ✓
│           │
│           ├── _schema/
│           │   ├── 01_data_model.md      ✓
│           │   └── 02_design_rationale.md ✓
│           │
│           ├── _discovery/
│           │   ├── 01_repositories.md    ✓
│           │   └── 02_what_we_learned.md ✓
│           │
│           ├── _prompts/
│           │   ├── 01_builder.md         ✓
│           │   └── 02_gardener.md        ✓
│           │
│           ├── _api/
│           │   └── 01_contracts.md       ✓
│           │
│           ├── _frontend/
│           │   └── 01_data_flow.md       ✓
│           │
│           └── _structure/
│               └── 01_project_structure.md ✓
│
└── _discovery/
    ├── _repo/
    │   ├── _INDEX.md
    │   ├── _LEVERAGE_GUIDE.md
    │   └── [repository analyses]
    │
    └── knowledge-graph-kit/              (user's existing project)
```

---

*End of handover document v3.0*


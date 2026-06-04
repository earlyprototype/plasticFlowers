# plasticFlower — Implementation Brief

> **Purpose:** Handoff document for implementation planning
> **Status:** All specifications complete, ready for build
> **Version:** 1.1

---

## Document Tree

This is the master reference for all project documentation.

### Tier 1: Start Here

| Document | Path | Purpose |
|----------|------|---------|
| **This Brief** | `_IMPLEMENTATION_BRIEF.md` | Implementation overview and requirements |
| **Alignment** | `_ALIGNMENT.md` | Non-negotiable principles — READ BEFORE CODING |

### Tier 2: Design Foundations

| Document | Path | Purpose |
|----------|------|---------|
| Concept | `_overview/01_concept.md` | What we're building |
| Scope | `_overview/02_scope.md` | What's in/out of MVP |
| Data Model | `_schema/01_data_model.md` | Core entities and properties |
| Schema Rationale | `_schema/02_design_rationale.md` | Why the schema is designed this way |
| System Architecture | `_architecture/01_system_overview.md` | High-level flow |
| Agent Architecture | `_architecture/02_agents.md` | Builder/Gardener model |

### Tier 3: Implementation Specifications

| Document | Path | Purpose |
|----------|------|---------|
| Builder Prompt | `_prompts/01_builder.md` | Full prompt, I/O schema, examples |
| Gardener Prompt | `_prompts/02_gardener.md` | Full prompt, I/O schema, examples |
| API Contracts | `_api/01_contracts.md` | All endpoints, schemas, SSE events |
| Frontend Data Flow | `_frontend/01_data_flow.md` | State management, Cytoscape integration |
| Project Structure | `_structure/01_project_structure.md` | Directory layout, module responsibilities |

### Tier 4: Decision History & Quality

| Document | Path | Purpose |
|----------|------|---------|
| Decision Log | `_DECISION_LOG.md` | All 19 decisions with rationale |
| Conversations | `_CONVERSATIONS.md` | 7 key discussions that shaped decisions |
| Drift Report | `_DRIFT_REPORT_001.md` | Quality issues found and corrected |
| Pre-Implementation Report | `_PRE_IMPLEMENTATION_REPORT.md` | Final review checkpoint, locked clarifications |
| Progress Log | `_PROGRESS.md` | Work completed to date |

### Tier 5: Discovery (Reference Only)

| Document | Path | Purpose |
|----------|------|---------|
| Repository Index | `_discovery/_repo/_INDEX.md` | External repos analysed |
| Leverage Guide | `_discovery/_repo/_LEVERAGE_GUIDE.md` | What to extract from each repo |
| Handover | `_HANDOVER.md` | Original context document |

---

## What Is plasticFlower?

A local web application that:

1. Listens to a talk/lecture via microphone
2. Transcribes speech in real-time (Web Speech API)
3. Extracts concepts and relationships using Gemini 3 Pro
4. Visualises an emergent knowledge graph that grows live
5. Organises related concepts into "Flowers" (thematic clusters)

**Key differentiator:** No predefined schema — the LLM discovers what matters.

---

## Technology Stack

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

## Specification Documents

All specifications are complete and located in `_docs/_dev/_MVP/`:

| Document | Path | Contents |
|----------|------|----------|
| **Data Model** | `_schema/01_data_model.md` | Node, Relationship, Flower, Session, Chunk schemas |
| **Schema Rationale** | `_schema/02_design_rationale.md` | Why the schema is designed this way |
| **System Architecture** | `_architecture/01_system_overview.md` | High-level flow diagram |
| **Agent Architecture** | `_architecture/02_agents.md` | Builder/Gardener model |
| **Builder Prompt** | `_prompts/01_builder.md` | Full prompt, I/O schema, examples |
| **Gardener Prompt** | `_prompts/02_gardener.md` | Full prompt, I/O schema, examples |
| **API Contracts** | `_api/01_contracts.md` | All endpoints, request/response schemas |
| **Frontend Data Flow** | `_frontend/01_data_flow.md` | State management, SSE handling, Cytoscape integration |
| **Project Structure** | `_structure/01_project_structure.md` | Directory layout, module responsibilities |
| **Decision Log** | `_DECISION_LOG.md` | All decisions with rationale |
| **Alignment** | `_ALIGNMENT.md` | Non-negotiable principles, verification checklist |

---

## Core Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                       │
│                                                                 │
│   Microphone → Web Speech API → Chunk Dispatcher → POST /chunks │
│                                                                 │
│   SSE Handler ← Graph State Manager → Cytoscape.js Renderer     │
└─────────────────────────────────────────────────────────────────┘
                              │
                    SSE stream + REST
                              │
┌─────────────────────────────────────────────────────────────────┐
│                        BACKEND (FastAPI)                        │
│                                                                 │
│   Chunk received → Builder Agent → Neo4j → SSE broadcast        │
│                                                                 │
│   Every 90s: Gardener Agent → Neo4j → SSE broadcast             │
└─────────────────────────────────────────────────────────────────┘
                              │
                           Neo4j
```

---

## Implementation Requirements

### Backend

#### 1. API Endpoints (FastAPI)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/sessions` | POST | Create session |
| `/sessions` | GET | List sessions |
| `/sessions/{id}` | GET | Get session |
| `/sessions/{id}` | PATCH | Rename session |
| `/sessions/{id}` | DELETE | Delete session |
| `/sessions/{id}/end` | POST | End session |
| `/sessions/{id}/chunks` | POST | Submit transcript chunk |
| `/sessions/{id}/stream` | GET | SSE subscription |
| `/sessions/{id}/graph` | GET | Full graph state |
| `/sessions/{id}/nodes` | GET | Nodes (filterable) |
| `/sessions/{id}/relationships` | GET | Relationships (filterable) |
| `/sessions/{id}/flowers` | GET | Flowers + bridges |
| `/sessions/{id}/export/json` | GET | Export JSON |
| `/sessions/{id}/export/transcript` | GET | Export plain transcript |
| `/sessions/{id}/export/vtt` | GET | Export VTT |
| `/sessions/{id}/export/markdown` | GET | Export Markdown summary |

Full schemas in `_api/01_contracts.md`.

#### 2. Builder Agent

- Triggered on each chunk submission
- Input: chunk text + existing node labels (grouped by type)
- Output: JSON with nodes and relationships
- Creates "ghost" status nodes
- Full prompt and schema in `_prompts/01_builder.md`

#### 3. Gardener Agent

- Triggered every 90 seconds (if activity)
- Input: full graph state (ghost nodes, solid nodes, relationships, flowers)
- Output: JSON with node_actions, flower_actions, new_relationships
- Confirms/prunes/merges nodes, forms/updates Flowers
- Full prompt and schema in `_prompts/02_gardener.md`

#### 4. SSE Manager

Broadcast events to connected clients:

| Event | Trigger |
|-------|---------|
| `node_added` | Builder extracts node |
| `node_updated` | Gardener confirms/updates |
| `node_removed` | Gardener prunes |
| `node_merged` | Gardener merges |
| `relationship_added` | Builder/Gardener |
| `relationship_removed` | Gardener |
| `flower_created` | Gardener |
| `flower_updated` | Gardener |
| `flower_dissolved` | Gardener |

#### 5. Neo4j Integration

- Store nodes, relationships, flowers, sessions, chunks
- Vector index for similarity search (embeddings on nodes)
- Query for bridges (cross-flower relationships) at runtime

---

### Frontend

#### 1. Speech Capture

- Web Speech API (`webkitSpeechRecognition`)
- Continuous mode, interim results
- UK English
- Buffer into chunks (~3-5 sentences)
- POST to `/sessions/{id}/chunks`

#### 2. SSE Handling

- Connect to `/sessions/{id}/stream`
- Parse events, route to state manager
- Auto-reconnect with exponential backoff (1s, 2s, 4s... max 30s)
- On reconnect: fetch full state via `/sessions/{id}/graph`

#### 3. Graph State

- Local state: `Map<id, Node>`, `Map<id, Relationship>`, `Map<id, Flower>`
- Update on SSE events
- Trigger Cytoscape re-render on change

#### 4. Cytoscape.js Rendering

- FCose layout for compound nodes (Flowers)
- Incremental layout (don't reset viewport)
- Visual styles:
  - Ghost nodes: 50% opacity, dashed border
  - Solid nodes: 100% opacity, solid border
  - Relationship categories: colour-coded
  - Stem nodes: larger, highlighted
  - Flowers: light background container

#### 5. Z-Level Filtering

- Filter by: status (ghost/solid), confidence threshold, Flower, inferred_type
- Hide filtered nodes and their edges
- UI controls for filter selection

#### 6. UI Components

- Session list (home page)
- Live session view (graph canvas + controls)
- Transcript panel (collapsible)
- Node/edge/flower detail panels
- Start/stop/export controls
- Connection status indicator

---

## Critical Constraints

### Emergent Schema (Non-Negotiable)

`inferred_type` on nodes is a **freeform string**. The LLM determines types based on content. Do NOT constrain to an enum.

### Flower Formation (Non-Negotiable)

Flowers require **both**:
- 3+ nodes with shared semantic theme
- 2+ internal connections between members

### Merge Rules (Non-Negotiable)

Merge only **true duplicates**:
- Synonyms
- Acronyms / expansions
- Spelling variants

Do NOT merge hierarchically related concepts (e.g., "self-attention" into "attention mechanism").

### Relationship Categories (Fixed)

Exactly 5 categories, no more, no less:
- CAUSAL
- STRUCTURAL
- COMPARATIVE
- TEMPORAL
- ASSOCIATIVE

---

## MVP Scope

### Included

- Web Speech API transcription
- Deepgram option (abstracted, switchable)
- Builder + Gardener agents
- Neo4j storage
- Cytoscape.js + FCose visualisation
- Ghost/solid node states
- Flower clustering
- Session save/restore
- Auto-reconnect
- Export: JSON, transcript (plain + VTT), Markdown summary
- Z-level filtering

### Excluded (Post-MVP)

- Historian Agent (meta-flowers for long talks)
- Linker Agent (real-time cross-chunk relationships)
- Advanced exports (GraphML, Mermaid, CSV)
- Full density metrics (beyond edge count)
- Accessibility features
- Offline mode

### Excluded (All Phases)

- Multi-speaker diarisation (single speaker use case only)

---

## Reference Documents

| Purpose | Path |
|---------|------|
| All decisions | `_DECISION_LOG.md` |
| Non-negotiable principles | `_ALIGNMENT.md` |
| What we learned from research | `_discovery/_repo/_LEVERAGE_GUIDE.md` |
| Repository analysis | `_discovery/_repo/_INDEX.md` |

---

## Verification Checklist

Before completing any implementation:

- [ ] `inferred_type` allows any value (not constrained)
- [ ] Flower formation requires 3+ nodes AND 2+ connections
- [ ] Merge only true duplicates, not hierarchies
- [ ] Relationship categories exactly: CAUSAL, STRUCTURAL, COMPARATIVE, TEMPORAL, ASSOCIATIVE
- [ ] Gardener runs every 90 seconds
- [ ] SSE events match documented types
- [ ] Export formats match: JSON, plain transcript, VTT, Markdown

---

## Success Criteria

MVP is complete when:

1. User can start a session and speak into microphone
2. Speech is transcribed and displayed
3. Concepts appear as nodes in real-time (ghost state)
4. Relationships appear between concepts
5. Every 90 seconds, Gardener refines the graph
6. Ghost nodes become solid after Gardener review
7. Flowers form around thematic clusters
8. User can filter the view (Z-level)
9. User can export session data
10. Session persists and can be restored

---

## Reading Order for Implementation

**Before writing any code:**

1. `_ALIGNMENT.md` — Non-negotiable principles (emergent schema, Flower criteria, merge rules)
2. `_schema/01_data_model.md` — Core entities
3. `_prompts/01_builder.md` — Builder Agent specification
4. `_prompts/02_gardener.md` — Gardener Agent specification
5. `_api/01_contracts.md` — API endpoints and schemas
6. `_frontend/01_data_flow.md` — Frontend architecture
7. `_structure/01_project_structure.md` — Directory layout

**Reference as needed:**

- `_DECISION_LOG.md` — When you need to understand WHY something is designed a certain way
- `_CONVERSATIONS.md` — When you need deeper context on a decision
- `_discovery/_repo/_LEVERAGE_GUIDE.md` — When implementing patterns from reference repos

---

## Quick Links

| Need | Document |
|------|----------|
| Data model | `_schema/01_data_model.md` |
| Builder prompt | `_prompts/01_builder.md` |
| Gardener prompt | `_prompts/02_gardener.md` |
| API endpoints | `_api/01_contracts.md` |
| Frontend flow | `_frontend/01_data_flow.md` |
| Project layout | `_structure/01_project_structure.md` |
| Design principles | `_ALIGNMENT.md` |
| All decisions | `_DECISION_LOG.md` |

---

*Document version 1.1 — Ready for implementation planning*


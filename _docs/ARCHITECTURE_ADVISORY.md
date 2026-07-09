# Architectural Advisory: plasticFlower

> **Historical planning document** — describes a target architecture, not the current system; GraphRAG Q&A and the Librarian agent are NOT implemented. See [_docs/_audit/2026-07-08_audit_report.md](./_audit/2026-07-08_audit_report.md) for current state.

**Date:** 30 December 2025  
**Version:** 8.2 (Event-Driven Agents)  
**Context:** Complete system design incorporating GraphRAG, Research Augmentation, and STT Correction  
**Learning Guide:** [LEARNING_GUIDE.md](./LEARNING_GUIDE.md) - Structured curriculum for Neo4j and Semantic Knowledge Graphs  
**Session State:** [_START_SESSION_STATE.md](./_START_SESSION_STATE.md) - Cross-session progress tracking (attach to every coding session)  
**ADR Index:** [_dev/ADR/INDEX.md](./_dev/ADR/INDEX.md) - Architecture Decision Records (critical process)  
**Lite Version:** [LITE_ARCHITECTURE.md](./_archive/LITE_ARCHITECTURE.md) - Browser-only implementation for demos (separate project)

---

## 1. Vision & Problem Statement

### The Problem: Conference Content is Underutilised

| Reality | Impact |
|---------|--------|
| 50 talks at a conference | Attendees watch 5-10 live |
| Recordings exist | Few people watch 90-minute replays |
| Intent to catch up later | Rarely happens |
| Knowledge trapped in linear video | No way to search, navigate, or connect |

**Thousands of hours of valuable conference content go unwatched because:**
- Linear video is time-consuming
- No way to know if a talk is relevant without watching it
- Can't jump to "the bit about X"
- Can't ask "what did they say about Y?"
- Can't see connections across talks

### The Solution: A Navigable Knowledge Graph

**plasticFlower transforms conference recordings into explorable knowledge maps.**

Inspired by **RSA Animate** (where an artist draws concepts as a speaker talks), plasticFlower automatically creates a spatial visual representation of any talk - showing entities, relationships, and themes as a navigable graph.

### Temporal Views

| View | User Need | What plasticFlower Provides |
|------|-----------|----------------------------|
| **Live** | Engaged attendee, visual aid | Graph forming in real-time (RSA Animate style) |
| **Post-talk** | Missed it, want the gist | Completed graph + Q&A + jump to timestamps |
| **Conference-wide** | Which talks matter to me? | Cross-session semantic map |
| **Deep dive** | I care about topic X | Find all mentions, click to research, jump to moments |

### The Core Value

> "After a talk, you have a navigable map of what was discussed, showing how concepts connect, that you can search, explore, ask questions about, and reference later."

---

## 2. Executive Summary

**plasticFlower** is a **knowledge capture and retrieval system** that transforms spoken content into navigable knowledge graphs. Key capabilities:

1. **Live Visualisation:** Real-time graph formation as entities and relationships are mentioned
2. **Retrospective Q&A:** Query sessions using GraphRAG (Hybrid Vector + Graph search)
3. **External Research:** Enrich unfamiliar terms with web search (automatic or on-demand)
4. **STT Correction:** Intelligent proofreading to fix speech-to-text errors
5. **Multi-Session Navigation:** Cross-session knowledge linking and semantic discovery

### Key Shifts in v8.0

| Capability | v7.0 | v8.0 |
|------------|------|------|
| **Live Visualisation** | Core focus | Preserved |
| **Retrospective Q&A** | Not addressed | Librarian Agent + GraphRAG |
| **External Enrichment** | Ghost Nodes concept | Researcher Agent + Web Search |
| **STT Correction** | Not addressed | Merged into Gardener |
| **Multi-Session** | Session isolation | Global nodes + vocabulary |

### The Four Agents

```
Builder ───────────────────────────────────────────► (continuous)
    │   Fast extraction, creates GHOST nodes
    │
Gardener ──────●──────────●──────────●─────────────► (every 60-90s)
    │   Proofread → Confirm → Merge → Cluster
    │
Researcher ────○─────○─────○─────○─────○───────────► (on-demand)
    │   Enriches unfamiliar terms via web search
    │
Librarian ─────────────────────────────────────────► (on-demand)
        Answers questions about past sessions
```

---

## 2. Core Architecture: "Stream & Soil"

We maintain the decoupling of ingestion and intelligence to ensure robustness.

### The Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                          plasticFlower v8                           │
│                                                                     │
│   AUDIO IN ───► STT ───► Chunks ───► Builder ───► Neo4j            │
│                                          │           │              │
│                                          ▼           ▼              │
│                                    [Redis Bus]   [Vector Index]     │
│                                          │           │              │
│                              ┌───────────┴───────────┤              │
│                              │                       │              │
│                              ▼                       ▼              │
│                         Gardener              Researcher            │
│                    (Proofread/Merge/          (External             │
│                     Cluster)                   Enrichment)          │
│                              │                       │              │
│                              ▼                       ▼              │
│                         [SSE Stream] ◄───────────────┘              │
│                              │                                      │
│                              ▼                                      │
│                      Cytoscape.js UI                                │
│                                                                     │
│   USER QUERY ───► Librarian ───► GraphRAG ───► Response            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Tech Stack

| Component | Technology | Role |
|-----------|------------|------|
| **Ingestion** | FastAPI WebSockets | Real-time bi-directional comms |
| **Messaging** | Redis Streams | Decoupling & backpressure |
| **Persistence** | Neo4j 5.x | Graph storage + Vector Index |
| **Clustering** | LLM semantic reasoning | Community detection (GDS optional at scale) |
| **Significance** | LLM reasoning | Keystone identification (GDS optional at scale) |
| **Search** | Neo4j Vector Index (native) | Semantic deduplication; neo4j-graphrag deferred to Phase 7 |
| **LLM** | Gemini 2.0 Flash / 1.5 Pro | Extraction, reasoning, Q&A |
| **Orchestration** | Python asyncio + Redis Streams | Event-driven agent coordination ([ADR-006](./_dev/ADR/0006-async-agents-over-langgraph.md)) |
| **Visualisation** | Cytoscape.js | Live graph rendering |

### Configuration

**Key Settings (`backend/app/config.py`):**

| Setting | Default | Description |
|---------|---------|-------------|
| `similarity_threshold` | 0.92 | Vector similarity threshold for deduplication (ADR-008) |
| `builder_gardener_ratio` | 5 | Builder runs before Gardener trigger (ADR-010) |
| `gemini_request_timeout` | 90.0 | LLM request timeout in seconds |
| `embedding_dimensions` | 768 | Vector dimensions (text-embedding-004) |
| `embedding_similarity_function` | cosine | Neo4j similarity function |

**Gemini 2.5 Configuration (Critical):**

Gemini 2.5 models have "thinking mode" enabled by default, which adds 60+ seconds of internal reasoning. This must be disabled for structured output tasks:

```python
config = types.GenerateContentConfig(
    response_mime_type="application/json",
    response_schema=schema,
    thinking_config=types.ThinkingConfig(thinking_budget=0),  # Disable thinking
)
```

Also use `Literal` types instead of regex patterns in Pydantic schemas for better Gemini compatibility:
```python
# Good: Literal types
action: Literal["confirm", "prune", "merge"] = Field(...)

# Bad: Regex patterns (may cause issues with structured output)
action: str = Field(..., pattern="^(?i)(confirm|prune|merge)$")
```

**Agent Enable Flags (Architectural Pattern):**

All agents support enable/disable flags for debugging and graceful degradation:

```python
# In config.py
builder_enabled: bool = Field(True, description="Enable Builder agent processing")
gardener_enabled: bool = Field(True, description="Enable Gardener scheduling")
researcher_enabled: bool = Field(True, description="Enable Researcher agent")
librarian_enabled: bool = Field(True, description="Enable Librarian Q&A")
```

**Usage:** Set `BUILDER_ENABLED=false` in environment to disable specific agents during debugging or if an agent is causing issues.

---

## 3. Agent Architecture

### 3.1 The Builder (Fast Extraction)

**Purpose:** Real-time entity and relationship extraction from speech chunks with pre-creation deduplication.

| Attribute | Value |
|-----------|-------|
| **Trigger** | Each new transcript chunk |
| **Model** | `gemini-2.5-flash` (speed priority) |
| **Output** | GHOST nodes (new) or updated mentions (existing), relationships |
| **Latency Target** | < 3 seconds (includes similarity check) |

**Responsibilities:**
1. Extract entities (concepts, people, organisations, terms)
2. Extract chunk-local relationships
3. **For each extracted entity:**
   - Compute embedding
   - Check similarity against existing nodes (threshold: 0.92, see ADR-008)
   - **If match found:** Increment `mentions` count on existing node, accumulate confidence
   - **If no match:** Create new GHOST node
4. Rewire relationships to use canonical node IDs (matching or newly created)
5. Broadcast via SSE: `node_added` (new), `node_updated` (matched), `relationship_added`

**Pre-Creation Similarity Check Flow:**

```
1. Receive Chunk
   └─ POST /sessions/{id}/chunks

2. LLM Extraction
   └─ Gemini extracts entities + relationships
   └─ Returns: nodes[], relationships[] (with label references)

3. For Each Extracted Node
   ├─ Generate embedding (Google text-embedding-004)
   ├─ Query vector index: db.index.vector.queryNodes()
   └─ Decision:
       ├─ score >= 0.92 AND types compatible AND confidence >= 0.7
       │   └─ MATCH: Increment existing node mentions
       │   └─ Map: extracted_label -> existing_node.id
       │   └─ SSE: node_updated (mentions++)
       └─ Otherwise
           └─ CREATE: New GHOST node with embedding
           └─ Map: extracted_label -> new_node.id
           └─ SSE: node_added

4. Create Relationships
   └─ Use label-to-ID mapping from step 3
   └─ Relationships point to canonical nodes (matched or new)
   └─ SSE: relationship_added

5. Publish to Redis
   └─ chunks.added event (triggers Gardener per ratio)
```

**Disambiguation Mitigations (ADR-013):**

To prevent false positive matches (e.g., "Apple" company vs "apple" fruit):

| Mitigation | Description | Status |
|------------|-------------|--------|
| **Type matching** | Use embedding similarity of type names (threshold: 0.80) - respects emergent types | Required |
| **Confidence threshold** | Require label similarity >= 0.92 AND LLM confidence >= 0.7 | Required |
| **Phrase length filter** | Skip similarity check for labels < 2 words | Future |
| **Context embedding** | Include chunk context in embedding | Future |

**Why embedding-based type matching:** The system uses emergent, freeform types (see `Node.inferred_type`). The LLM can return "organisation", "org", "company", etc. A hardcoded dictionary would fail on variations. Embedding similarity handles this flexibly.

**Fallback Behaviour:**

If embedding generation or similarity query fails, Builder falls back to creating a new GHOST node. Gardener handles deduplication in subsequent cycles.

**Benefits of Pre-Creation Check:**
- Fewer GHOST nodes created (cleaner graph state)
- Accurate mention counts from the start
- Relationships concentrate on canonical nodes immediately
- Smoother UI experience (fewer node_added + node_merged sequences)
- Reduced Gardener workload

---

### 3.2 The Gardener (Graph Hygiene + Proofreading)

**Purpose:** Periodic maintenance, correction, and structuring of the knowledge graph.

| Attribute | Value |
|-----------|-------|
| **Trigger** | Ratio-based (every N chunks via Redis, default 5:1) |
| **Model** | `gemini-2.5-flash` (using flash for higher rate limits) |
| **Context** | Full graph + Extended transcript (3000 words) + Session context |
| **Timeout** | 90 seconds |

**Tasks (Executed in Order):**

#### Task 1: Proofread (STT Correction)
- Scan incremental chunks (10 at a time with checkpoint - see ProofreadCheckpoint)
- Load session context for consistent understanding
- Identify phonetic STT errors (e.g., "see dare" -> "CeADAR")
- Correct transcript chunks AND node labels
- Update session vocabulary for instant future corrections
- Broadcast: `node_corrected`

**Session Context Persistence:**

To maintain understanding across incremental proofreading, Gardener uses SessionContext:

```python
class SessionContext(BaseModel):
    session_id: str
    theme_summary: str       # "Enterprise Ireland on EDIH network"
    key_entities: list[str]  # Recurring important entities
    speaker_names: list[str] # For name recognition
    domain_terms: list[str]  # Technical vocabulary
```

This is generated during early cycles and included in every Gardener prompt.

#### Task 2: Confirm or Remove
- Promote valid GHOST nodes to SOLID
- Remove noise/hallucination nodes
- Broadcast: `node_confirmed`, `node_removed`

#### Task 3: Merge (Reduced Workload)
- Handle edge cases missed by Builder's pre-creation similarity check
- Merge nodes with different labels but same meaning (synonyms, abbreviations)
- Use embeddings (similarity > 0.92) + textual context
- Merge into canonical node, preserve mention counts
- Broadcast: `node_merged`

**Note:** With pre-creation similarity checking in Builder, merge workload is significantly reduced. Gardener focuses on semantic merges that require LLM reasoning (e.g., "ML" and "Machine Learning" with different embeddings).

#### Task 4: Form Flowers (Structural Clustering)

**Flowers are formed based on actual relationships, not semantic imposition.**

A Flower is created when a group of validated nodes have 2+ relationships between them. This emerges from what the speaker actually said, not from the LLM deciding what "belongs together."

**Formation Process:**

```
1. Identify Cluster
   └─ Find nodes with 2+ relationships to other nodes in session

2. Create Flower Node
   └─ (:Flower {session_id, created_at})

3. Link Members
   └─ (n:Node)-[:BELONGS_TO]->(f:Flower)

4. Name the Flower (Optional)
   └─ LLM generates 3-5 word summary based on member nodes/relationships
   └─ e.g., "Irish AI Funding Ecosystem"

5. Identify Keystones
   └─ Nodes that bridge multiple Flowers or have high connection count
   └─ Mark with `is_keystone: true` for visual prominence
```

**Flower vs Semantic Clustering:**

| Approach | Basis | Result |
|----------|-------|--------|
| **Flower formation** | Actual relationships from transcript | Honest structural grouping |
| **Semantic clustering** | LLM decides what's thematically similar | Imposed abstraction |

**At Scale (GDS - Future):**
- Run Leiden for algorithmic community detection
- Run Betweenness Centrality for keystone identification
- Still based on structure, just faster computation

- Broadcast: `flower_formed`, `flower_updated`

#### Task 5: Temporal Decay
- Update `last_active` timestamps
- Mark nodes older than 5 minutes as `status: LEGACY`

**Context Strategy:**

| Data Type | Scope | Purpose |
|-----------|-------|---------|
| Graph Structure | Full (all nodes/relationships) | Merge and cluster decisions |
| Transcript | Extended (3000 words, ~10 min) | Textual context for reasoning |
| Proofread Chunks | Incremental (10 new chunks) | Sequential error detection |
| Vocabulary | Session-specific dictionary | Instant correction lookup |
| Similarity Hints | Embedding clusters > 0.85 | Pre-computed merge candidates |

**Proofread Checkpoint:**
```python
class ProofreadCheckpoint:
    session_id: str
    last_proofread_chunk_id: str
    last_run: datetime
```

**Session Vocabulary:**
```python
class SessionVocabulary:
    session_id: str
    language_variant: str  # "en-GB" (default) or "en-US"
    corrections: Dict[str, str]  # {"see dare": "CeADAR", "you carry": "UKRI"}
    preferred_spellings: Dict[str, str]  # {"color": "colour"} for en-GB
```

---

### 3.3 The Researcher (External Enrichment)

**Purpose:** Enrich entities with external information so viewers can learn about unfamiliar terms without leaving the experience.

| Attribute | Value |
|-----------|-------|
| **Model** | `gemini-2.5-flash` with Google Search grounding |
| **Output** | ReferenceNode linked to source concept |
| **Fallback** | Tavily API, Wikipedia, Semantic Scholar |

**Two Modes:**

| Mode | Trigger | Use Case |
|------|---------|----------|
| **Automatic** | Gardener flags entity as unfamiliar/important | Background enrichment during live session |
| **On-Demand** | User clicks node in UI | User-driven exploration anytime |

**Automatic Mode (Live):**
- Gardener validates Ghost node, flags it as `needs_research: true`
- Criteria: first mention of organisation, funding scheme, or complex term
- Researcher runs in background, enriches node
- SSE pushes update, node gains "enriched" indicator in UI

**On-Demand Mode (User Click):**
- User sees a node they don't recognise
- Clicks node, UI shows "Research this?"
- Frontend calls `/api/nodes/{id}/research`
- Researcher runs, results displayed in sidebar/modal
- User can click through to sources or save to node

**Workflow:**

```
1. Receive Request
   └─ Via Redis (automatic) OR API call (on-demand)

2. Classify Entity Type
   └─ LLM determines: person, organisation, funding_scheme, concept, paper

3. Search Strategy
   ├─ Organisation/Funding → Web search (Gemini grounding or Tavily API)
   ├─ Academic concept → Semantic Scholar + Wikipedia API
   ├─ Person → Web search (careful with rate limits)
   └─ Paper/Research → arXiv, Semantic Scholar

4. Extract Structured Data
   └─ LLM parses results into: title, url, summary, type, source

5. Create ReferenceNode
   └─ (:Node)-[:HAS_REFERENCE]->(:ReferenceNode)

6. Notify Frontend
   └─ SSE: reference_added event with node_id and summary

6. Broadcast via SSE
   └─ "reference_added" event → UI shows enrichment icon on node
```

**Why Web Search:**
- Local organisations (e.g., "CeADAR", "Creative Scotland") won't be in structured APIs
- Funding schemes are often region-specific and change frequently
- Web search (via Gemini grounding) handles these cases well

**Search Strategy (Default: Gemini Grounding):**

| Priority | Method | When Used |
|----------|--------|-----------|
| 1 (Default) | Gemini with Google Search grounding | Most cases - no extra API key needed |
| 2 (Fallback) | Tavily API | Quota exceeded OR low-confidence results |
| 3 (Structured) | Wikipedia/Semantic Scholar APIs | Academic concepts, well-known entities |

```python
async def research_entity(entity: str, context: str) -> ReferenceNode:
    try:
        # Default: Gemini with grounding (simpler, no extra API)
        return await gemini_grounded_search(entity, context)
    except (QuotaExceeded, LowConfidenceResult):
        # Fallback: Tavily for better/different results
        return await tavily_search(entity, context)
```

**Rationale:** Start with Gemini grounding (simpler setup, shared quota). Add Tavily later if search quality is insufficient for your domain.

---

### 3.4 The Librarian (Q&A)

**Purpose:** Answer questions about sessions.

| Attribute | Value |
|-----------|-------|
| **Trigger** | User query via API |
| **Model** | `gemini-2.5-pro` (reasoning priority) |
| **Retrieval** | Full context (single session) / GraphRAG (multi-session, Phase 7) |

**Two-Phase Approach (see [ADR-004](./_dev/ADR/0004-full-context-qa.md)):**

#### Phase 4: Single-Session Q&A (Full Context)

No neo4j-graphrag needed. Load entire session into LLM context:

```
1. Load Full Context
   └─ Transcript chunks + All nodes + All relationships (~25k tokens)

2. Generate Answer
   └─ LLM answers with complete visibility

3. Stream Response
   └─ SSE stream for real-time token display
```

**Implementation (Phase 4):**

```python
async def librarian_single_session(question: str, session_id: str):
    # Load full session context
    transcript = await get_full_transcript(session_id)
    nodes = await get_all_nodes(session_id)
    relationships = await get_all_relationships(session_id)
    
    prompt = f"""
    You are answering questions about a recorded session.
    
    TRANSCRIPT:
    {transcript}
    
    KNOWLEDGE GRAPH:
    Nodes: {nodes}
    Relationships: {relationships}
    
    QUESTION: {question}
    
    Answer with citations to specific moments in the transcript.
    """
    
    return await gemini.generate(prompt)
```

#### Phase 7: Multi-Session Q&A (GraphRAG - Future)

When querying across sessions, neo4j-graphrag provides efficient retrieval:

```python
# Future implementation - Phase 7
from neo4j_graphrag import GraphRAG
from neo4j_graphrag.retrievers import HybridRetriever

retriever = HybridRetriever(
    driver=driver,
    index_name="node_embeddings",
    vector_top_k=10,
    graph_depth=2
)

rag = GraphRAG(llm=gemini_client, retriever=retriever)

answer = rag.query(
    "What do we know about machine learning across all sessions?"
)
```

---

## 4. Agent Coordination Patterns

Multiple agents operating on the same graph require coordination to avoid conflicts.

### Safe by Design

| Pattern | Why It Works |
|---------|--------------|
| Relationships use `MATCH` for nodes | Prevents creating corrupt empty nodes if node doesn't exist |
| Nodes use `CREATE` with unique IDs | Builder generates UUIDs, no collision risk |
| Gardener uses transactions | Atomic operations prevent partial updates |
| SSE is append-only | Events stream in order, no conflicts |
| Similarity check before create | Prevents Builder creating duplicates |

**Critical Pattern (2025-12-28 fix):**
```cypher
-- CORRECT: MATCH nodes, MERGE relationship only
MATCH (source:Node {id: $source_id, session_id: $session_id})
MATCH (target:Node {id: $target_id, session_id: $session_id})
MERGE (source)-[rel:RELATIONSHIP {id: $rel_id}]->(target)

-- WRONG: MERGE on nodes creates empty nodes if they don't exist
MERGE (source:Node {id: $source_id}) -- Creates corrupt node!
```

### Conflict Scenarios and Solutions

| Scenario | Risk | Solution |
|----------|------|----------|
| Gardener deletes node while Builder references it | Orphaned relationship | Gardener checks node existence before delete |
| Builder creates duplicate while Gardener merging | Two nodes for same concept | Similarity threshold catches this |
| Both agents write to same node | Data inconsistency | Neo4j transaction isolation handles this |
| Correction applied mid-extraction | Label mismatch | Builder re-checks label before persist |

### Scheduling Strategy

```
Time:     0s    30s    60s    90s    120s   150s
          |      |      |      |       |      |
Builder:  ████████████████████████████████████  (continuous, per-chunk)
Gardener:        [████]        [████]          (60-90s cycles, ~5s duration)
Researcher:         ○              ○            (triggered, non-blocking)
Librarian:                                      (on-demand, user-initiated)
```

- **Builder** runs continuously but each chunk is independent
- **Gardener** runs in discrete cycles; Neo4j transactions ensure atomicity
- **Researcher** is fire-and-forget; doesn't block other agents
- **Librarian** is read-only; no coordination needed

### No Locking Required

Neo4j's transaction isolation (READ COMMITTED by default) handles concurrent writes. The key is designing operations to be **idempotent**:

```python
# Good: Idempotent - safe to retry
MERGE (n:Node {id: $id}) SET n.label = $label

# Risky: Not idempotent - could create duplicates
CREATE (n:Node {id: $id, label: $label})
```

### Redis Streams: The Event Bus Explained

**What is Redis Streams doing here?**

Redis Streams acts as an **asynchronous event bus** that decouples agent operations and enables non-blocking coordination.

**Why not just call functions directly?**

| Direct Function Calls | Redis Streams Event Bus |
|----------------------|-------------------------|
| Builder waits for Gardener response | Builder publishes event and continues |
| If Gardener crashes, Builder fails | Events queue reliably until consumed |
| Tight coupling between agents | Agents are independent services |
| No backpressure handling | Events queue when consumers are busy |
| Restart loses in-flight operations | Messages persist until acknowledged |

**Event Types and Flow:**

| Event Stream | Published By | Consumed By | Payload | Purpose |
|--------------|--------------|-------------|---------|---------|
| `chunks.added` | Ingestion | Builder, Gardener | chunk_id, session_id, text | Trigger extraction and proofread queue |
| `nodes.created` | Builder | Gardener | node_id, label, confidence | Queue for validation/merge cycle |
| `nodes.needs_research` | Gardener | Researcher | node_id, entity_type, context | Trigger automatic enrichment |
| `research.requested` | API | Researcher | node_id, user_id | User-triggered enrichment |
| `corrections.applied` | Gardener | Builder | old_label, new_label, node_ids | Sync vocabulary updates |

**Example Flow:**

```python
# Builder publishes without blocking
await redis.xadd('nodes.created', {
    'node_id': node.id,
    'label': node.label,
    'confidence': node.confidence
})
# Builder continues processing next chunk immediately

# Gardener consumes when ready
async for event in redis.xread('nodes.created'):
    await process_for_validation(event['node_id'])
```

**Key Benefits:**
1. **Non-blocking:** Builder doesn't wait for Gardener's 5-second cycle
2. **Reliable:** Messages persist even if Researcher is rate-limited
3. **Scalable:** Can run multiple Researcher instances consuming same stream
4. **Observable:** Can monitor event queues for debugging/metrics

---

## 5. Data Model (Extended)

### 4.1 Core Entities (Existing)

#### Node
| Property | Type | Purpose |
|----------|------|---------|
| `id` | string | Unique identifier |
| `label` | string | Display name |
| `status` | enum | GHOST, SOLID, LEGACY |
| `confidence` | float | 0.0-1.0 |
| `mentions` | int | Reference count |
| `timestamps` | float[] | When mentioned |
| `inferred_type` | string | concept, person, organisation, etc. |
| `embedding` | float[] | 768-dim vector |
| `created_at` | datetime | Creation time |
| `last_active` | datetime | Last mention time |
| `centrality_score` | float | Betweenness centrality (GDS) |
| `community_id` | string | Leiden community (GDS) |

#### Relationship
| Property | Type | Purpose |
|----------|------|---------|
| `id` | string | Unique identifier |
| `source_id` | string | Source node |
| `target_id` | string | Target node |
| `category` | enum | CAUSAL, STRUCTURAL, COMPARATIVE, TEMPORAL, ASSOCIATIVE |
| `description` | string | Natural language (2-4 words) |
| `confidence` | float | LLM confidence |
| `evidence` | string | Quote from transcript |
| `source` | enum | builder, gardener |
| `created_at` | datetime | Discovery time |

#### Flower (Cluster)
| Property | Type | Purpose |
|----------|------|---------|
| `id` | string | Unique identifier |
| `label` | string | LLM-generated theme name |
| `stem_node_id` | string | Highest-centrality node |
| `edge_count` | int | Internal connection density |
| `created_at` | datetime | Formation time |

#### TranscriptChunk
| Property | Type | Purpose |
|----------|------|---------|
| `id` | string | Unique identifier |
| `session_id` | string | Parent session |
| `text` | string | Chunk content (corrected) |
| `original_text` | string | Original STT output (for audit) |
| `start_time` | float | Seconds from session start |
| `end_time` | float | Seconds from session start |

#### Session
| Property | Type | Purpose |
|----------|------|---------|
| `id` | string | Unique identifier |
| `language_variant` | string | Language variant (default: "en-GB", alternative: "en-US") |
| `created_at` | datetime | Session start time |
| `title` | string | Session title (optional) |
| `status` | enum | active, completed, archived |

**Critical: Full Transcript Persistence**

**The complete transcript is permanently stored in Neo4j as TranscriptChunk nodes.** This is foundational to the architecture:

| What | Why | Enables |
|------|-----|---------|
| **Every chunk stored** | Complete session record | Timeline reconstruction, export |
| **Corrected text preserved** | Proofreading improves quality | Accurate Q&A, clean exports |
| **Original text preserved** | Audit trail | Debug STT issues, verify corrections |
| **Timestamps stored** | Temporal navigation | "Jump to 5:32", timeline view |

**Storage Flow:**

```
1. STT produces chunk → Stored immediately in Neo4j
2. Builder extracts from it → Creates nodes/relationships  
3. Gardener proofreads later → Updates text field, preserves original_text
4. Librarian reads it → Loads full context for Q&A
```

**This is why Phase 4 Q&A doesn't need RAG:** The entire session (transcript + graph) fits in Gemini's 1M token context window.

**This enables:**
- Full-context Q&A without retrieval (Phase 4)
- Re-running clustering algorithms on historical sessions (Phase 6)
- Complete session exports with corrected transcripts (Phase 5)
- Provenance: every node links back to source chunks via MENTIONS relationships

**Relationship:** `(:Session)-[:HAS_CHUNK]->(:TranscriptChunk)`

### 4.2 New Entities (v8.0)

#### ReferenceNode (External Enrichment)
| Property | Type | Purpose |
|----------|------|---------|
| `id` | string | Unique identifier |
| `type` | enum | definition, organisation, funding, paper, person |
| `title` | string | Display title |
| `url` | string | Source URL |
| `summary` | string | LLM-generated summary (2-3 sentences) |
| `source` | string | wikipedia, google, semantic_scholar, etc. |
| `fetched_at` | datetime | When retrieved |

**Relationship:** `(:Node)-[:HAS_REFERENCE]->(:ReferenceNode)`

#### SessionVocabulary
| Property | Type | Purpose |
|----------|------|---------|
| `session_id` | string | Session identifier |
| `language_variant` | string | Language variant (default: "en-GB") |
| `corrections` | map | Phonetic -> Correct mapping |
| `preferred_spellings` | map | Variant normalization (e.g., "color" -> "colour" for en-GB) |
| `updated_at` | datetime | Last update |

#### ProofreadCheckpoint
| Property | Type | Purpose |
|----------|------|---------|
| `session_id` | string | Session identifier |
| `last_chunk_id` | string | Last proofread chunk |
| `last_run` | datetime | Checkpoint time |

#### TranscriptCorrection (Audit Trail)
| Property | Type | Purpose |
|----------|------|---------|
| `id` | string | Unique identifier |
| `session_id` | string | Session identifier |
| `original` | string | Original text |
| `correction` | string | Corrected text |
| `confidence` | float | LLM confidence |
| `applied_at` | datetime | When applied |
| `affected_nodes` | string[] | Updated node IDs |
| `affected_chunks` | string[] | Updated chunk IDs |

### 4.3 New Relationships

| Relationship | Purpose |
|--------------|---------|
| `(:TranscriptChunk)-[:MENTIONS {position: int}]->(:Node)` | Provenance trail |
| `(:Node)-[:HAS_REFERENCE]->(:ReferenceNode)` | External enrichment |
| `(:Node)-[:BELONGS_TO]->(:Flower)` | Cluster membership |
| `(:Session)-[:HAS_CHUNK]->(:TranscriptChunk)` | Session structure |

### 4.4 Future: Multi-Session Entities

#### GlobalNode (Cross-Session)
| Property | Type | Purpose |
|----------|------|---------|
| `id` | string | Canonical identifier |
| `canonical_label` | string | Authoritative label |
| `total_mentions` | int | Across all sessions |
| `sessions` | string[] | Sessions where mentioned |
| `first_seen` | datetime | Earliest mention |

**Relationship:** `(:Node)-[:INSTANCE_OF]->(:GlobalNode)`

This enables queries like: "What do we know about Neo4j across all sessions?"

### 4.5 Language Settings

**Purpose:** Maintain consistent language variant (UK vs US English) across all generated text in the system.

#### Impact Areas

Language settings affect multiple components:

| Component | Impact | Example |
|-----------|--------|---------|
| **STT Output** | Pronunciation interpretation | "organise" vs "organize" |
| **Builder Extraction** | Entity label generation | "colour" vs "color" |
| **Gardener Proofreading** | Correctness validation | Is "organisation" an error? |
| **Gardener Summaries** | Flower labels, descriptions | "Analysing ML" vs "Analyzing ML" |
| **Researcher Enrichment** | Summary text generation | "centre" vs "center" |
| **Librarian Responses** | Q&A answer text | "whilst" vs "while" |

#### Implementation Strategy

**Session-Level Configuration:**

Each session has an optional `language_variant` field (default: "en-GB") that cascades to all agent operations.

**Agent Prompt Integration:**

All agents receive language instructions in their system prompts:

```python
# In config.py or session context
LANGUAGE_INSTRUCTIONS = {
    "en-GB": "Use British English spelling and grammar throughout (organisation, analyse, whilst, etc.)",
    "en-US": "Use American English spelling and grammar throughout (organization, analyze, while, etc.)",
}

# In each agent prompt
system_prompt = f"""
You are the [Builder/Gardener/Researcher/Librarian]...

LANGUAGE: {LANGUAGE_INSTRUCTIONS[session.language_variant]}

[rest of prompt...]
"""
```

**Consistency Enforcement:**

The Gardener enforces consistency during its proofread cycle:

1. Check node labels against session's language variant
2. Normalise mixed variants to session default
3. Update SessionVocabulary with preferred spellings

**SessionVocabulary Enhancement:**

The `preferred_spellings` map stores variant normalization rules:

```python
# For en-GB session
preferred_spellings = {
    "color": "colour",
    "organization": "organisation",
    "analyzing": "analysing"
}

# For en-US session
preferred_spellings = {
    "colour": "color",
    "organisation": "organization",
    "analysing": "analyzing"
}
```

**Mixed-Variant Handling:**

When a speaker uses one variant but the system expects another:

- **Quoted speech:** Preserve speaker's variant (authenticity)
- **Entity labels:** Normalise to session variant (consistency)
- **Summaries/descriptions:** Use session variant (clarity)

**Rationale:**

- **Session-level granularity:** Conference speakers might be American (respect their variant)
- **Default to en-GB:** User preference, most usage
- **Gardener as enforcer:** Shared context means consistency checks happen naturally
- **Vocabulary-based:** Efficient lookup, no LLM calls for known variants

---

## 6. Visualisation

### 5.1 Live Experience (Preserved)

The core "watching the graph grow" experience remains unchanged:

| Event | Animation |
|-------|-----------|
| Node created (GHOST) | Fade in, dashed border, 60% opacity |
| Node confirmed (SOLID) | 400ms transition to solid border, full opacity |
| Node corrected | Brief highlight flash, label text swap |
| Relationship added | 2000ms draw + fade effect |
| Flower formed | 1200ms nodes animate to fan layout around stem |
| Camera adjustment | 2500ms smooth pan/zoom after changes settle |

### 5.2 New Visual Elements (v8.0)

| Element | Visual Treatment |
|---------|------------------|
| **Temporal Decay** | Older nodes (>5min) fade to 20% opacity |
| **Keystone Nodes** | Size scaled by `centrality_score` |
| **Reference Icon** | Small link icon on nodes with external references |
| **Correction Indicator** | Brief "sparkle" animation when STT corrected |
| **Legacy Status** | Very faded, slightly smaller, non-interactive |

### 5.3 Semantic Zoom

| Zoom Level | Display |
|------------|---------|
| < 50% | Flowers (clusters) + Keystones only |
| > 50% | Full detail (all nodes and relationships) |

### 5.4 SSE Events (Extended)

| Event | Payload | UI Action | Source |
|-------|---------|-----------|--------|
| `node_added` | Node data | Render ghost node | Builder |
| `node_updated` | Node data | Update node (mentions++, confidence) | Builder (similarity match), Gardener |
| `node_confirmed` | node_id | Transition to solid | Gardener |
| `node_corrected` | node_id, old_label, new_label | Flash + update label | Gardener |
| `node_merged` | keep_id, absorbed_ids | Animate merge | Gardener |
| `node_removed` | node_id | Fade out and remove | Gardener |
| `relationship_added` | Relationship data | Draw edge | Builder, Gardener |
| `relationship_removed` | relationship_id | Remove edge | Gardener |
| `flower_formed` | Flower data + member_ids | Fan layout animation | Gardener |
| `flower_updated` | Flower data | Update positions | Gardener |
| `flower_dissolved` | flower_id | Remove flower, release nodes | Gardener |
| `reference_added` | node_id, reference_data | Add icon to node | Researcher |
| `chunk_processed` | chunk_id, error? | Acknowledge processing | Builder |
| `gardener_cycle` | timestamp | Heartbeat/sync | Gardener |

**Note on `node_updated`:** With pre-creation similarity checking, Builder broadcasts `node_updated` when an extracted entity matches an existing node (mentions incremented). This replaces the previous pattern of `node_added` followed by `node_merged` in Gardener.

---

## 7. API Endpoints (Extended)

### 6.1 Existing Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/sessions` | Create session |
| GET | `/api/sessions/{id}` | Get session details |
| POST | `/api/sessions/{id}/chunks` | Submit transcript chunk |
| GET | `/api/sessions/{id}/stream` | SSE event stream |
| GET | `/api/sessions/{id}/graph` | Full graph state |

### 6.2 New Endpoints (v8.0)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/sessions/{id}/ask` | Q&A about specific session |
| POST | `/api/ask` | Q&A across all sessions |
| POST | `/api/nodes/{id}/research` | Trigger external research |
| GET | `/api/sessions/{id}/summary` | LLM-generated session summary |
| GET | `/api/sessions/{id}/export` | Export as Markdown/JSON |
| GET | `/api/sessions/{id}/timeline` | Timeline reconstruction |
| POST | `/api/sessions/{id}/correct` | Manual STT correction |
| GET | `/api/sessions/{id}/vocabulary` | Session vocabulary |

---

## 8. Context Window Strategy

### 7.1 Gardener Context (Per Cycle)

| Data | Scope | Tokens (approx) | Purpose |
|------|-------|-----------------|---------|
| Graph Structure | All nodes + relationships | ~1500 | Merge/cluster decisions |
| Extended Transcript | 3000 words (~10 min) | ~4500 | Textual context |
| Proofread Chunks | 10 new chunks | ~1500 | Error detection |
| Vocabulary | Session dictionary | ~200 | Instant corrections |
| Similarity Hints | Embedding clusters | ~300 | Merge candidates |
| **Total** | | ~8000 | Per cycle |

### 7.2 Why 3000 Words (Not 1000)

1000 words = ~3-4 minutes of speech = too narrow for:
- Catching co-references ("that centre" -> "CeADAR" from 10min ago)
- Understanding topic evolution
- Merging concepts discussed far apart

3000 words = ~10 minutes = sufficient for most merge decisions while keeping costs manageable.

### 7.3 Token Cost Estimate (30min Session)

| Component | Tokens/Cycle | Cycles | Total | Cost (Gemini Pro) |
|-----------|--------------|--------|-------|-------------------|
| Gardener | 8000 | 20 | 160,000 | $0.05 |
| Builder | 1500 | 40 | 60,000 | $0.02 |
| Researcher | 3000 | 5 | 15,000 | $0.005 |
| **Total** | | | 235,000 | **~$0.08/session** |

---

## 9. Implementation Roadmap

### Phase 1: Infrastructure (The Soil)

**Goal:** Set up the enhanced infrastructure.

- [ ] Docker: Add Redis, enable GDS plugin (already done in docker-compose)
- [ ] Neo4j: Create Vector Index for embeddings
- [ ] Neo4j: Create indexes for new entity types
- [ ] Schema: Add ReferenceNode, SessionVocabulary, ProofreadCheckpoint

### Phase 2: Gardener Enhancement

**Goal:** Merge proofreading into Gardener with tiered context.

- [ ] Implement `get_extended_transcript(session_id, word_limit=3000)`
- [ ] Implement ProofreadCheckpoint persistence
- [ ] Implement SessionVocabulary CRUD (including language_variant and preferred_spellings)
- [ ] Add language_variant field to Session model
- [ ] Update agent prompts with language instructions
- [ ] Update Gardener prompt with multi-task structure (including variant normalization)
- [ ] Add `node_corrected` SSE event
- [ ] Add Chunk `original_text` field for audit trail

### Phase 3: Researcher Agent

**Goal:** External enrichment for unfamiliar terms.

- [ ] Implement Researcher as async Redis Streams consumer
- [ ] Integrate Gemini grounding (Google Search)
- [ ] Add fallback to structured APIs (Wikipedia, Semantic Scholar)
- [ ] Implement ReferenceNode creation and linking
- [ ] Add `reference_added` SSE event
- [ ] Frontend: Add reference icon and detail panel

### Phase 4: Librarian Agent (Single-Session Q&A)

**Goal:** Q&A capability for single session retrospective analysis.
**Approach:** Full context loading (no neo4j-graphrag needed) - see [ADR-004](./_dev/ADR/0004-full-context-qa.md)

- [ ] Implement Librarian as async function loading full session context
- [ ] Load: transcript chunks + nodes + relationships into LLM prompt
- [ ] Add `/api/sessions/{id}/ask` endpoint
- [ ] Frontend: Add Q&A panel component

**Note:** Cross-session Q&A (GraphRAG) deferred to Phase 7.

### Phase 5: Export & Summary

**Goal:** Documentation generation for sessions.

- [ ] Implement LLM-based session summary generation
- [ ] Implement Markdown export (nodes, relationships, timeline)
- [ ] Implement JSON export (full graph structure)
- [ ] Add `/api/sessions/{id}/summary` endpoint
- [ ] Add `/api/sessions/{id}/export` endpoint

### Phase 6: GDS Algorithms (Optional - Scale)

**Goal:** Graph algorithm acceleration for large graphs (100+ nodes).

**When to implement:** If/when sessions regularly exceed 100 nodes and LLM clustering becomes slow or expensive.

- [ ] Set up GDS graph projections per session
- [ ] Implement Leiden community detection
- [ ] Implement Betweenness centrality for keystones
- [ ] Add automatic scaling (LLM < 100 nodes, GDS >= 100)

**Note:** All TranscriptChunks are permanently stored. You can always re-run clustering algorithms on historical data later.

### Phase 7: Multi-Session + GraphRAG (Future)

**Goal:** Cross-session knowledge linking and Q&A.
**Dependency:** This is when neo4j-graphrag becomes necessary.

- [ ] Install and configure neo4j-graphrag
- [ ] Implement HybridRetriever for cross-session search
- [ ] Add `/api/ask` endpoint for multi-session queries
- [ ] Design GlobalNode schema and linking strategy
- [ ] Implement session vocabulary merging
- [ ] Implement cross-session query routing
- [ ] Design UI for multi-session exploration

---

## 10. QA Strategy

### 9.1 The Golden Run

- **Golden Input:** `tests/data/golden_speech.txt`
- **Baseline:** `tests/data/baseline_graph.json`
- **Metrics:**
  - Node Count
  - Flower Count
  - Modularity Score (GDS)
  - STT Correction Count
  - Merge Accuracy

### 9.2 Proofreading Tests

- **Input:** Transcript with known STT errors
- **Expected:** All errors corrected, vocabulary updated
- **Edge cases:**
  - Multiple spellings of same term
  - Acronyms (UKRI, CeADAR)
  - Proper nouns with unusual phonetics

### 9.3 Researcher Tests

- **Input:** Node with low confidence, known entity
- **Expected:** ReferenceNode created with valid URL and summary
- **Edge cases:**
  - Obscure local organisations
  - Ambiguous terms (multiple meanings)
  - Rate limiting handling

### 9.4 Librarian Tests

- **Input:** User questions about test session
- **Expected:** Accurate answers with source citations
- **Edge cases:**
  - Questions about non-existent topics
  - Cross-session queries
  - Follow-up questions (context retention)

---

## 11. Architecture Decision Records

All significant architectural decisions are documented in ADRs stored in `_docs/_dev/ADR/`.

### Current ADRs

| # | Decision | Rationale |
|---|----------|-----------|
| [001](./_dev/ADR/0001-llm-clustering-over-gds.md) | LLM-only clustering | 1M context fits entire session; GDS optional at scale |
| [002](./_dev/ADR/0002-proofreading-in-gardener.md) | Proofreading in Gardener | Shared context, simpler architecture |
| [003](./_dev/ADR/0003-gemini-grounding-for-research.md) | Gemini grounding for research | Simpler setup, Tavily as fallback |
| [004](./_dev/ADR/0004-full-context-qa.md) | Full context Q&A | GraphRAG unnecessary for single session |
| [005](./_dev/ADR/0005-lite-architecture.md) | Lite architecture for POC | Browser-only demo without backend |
| [006](./_dev/ADR/0006-async-agents-over-langgraph.md) | Async event-driven agents | Redis Streams over LangGraph orchestration |
| [007](./_dev/ADR/0007-limit-based-transcript-retrieval.md) | LIMIT-based transcript retrieval | Efficient word-count limiting |
| [008](./_dev/ADR/0008-similarity-threshold.md) | Similarity threshold 0.92 | Balanced precision/recall for dedup |
| [009](./_dev/ADR/0009-redis-only-agent-scheduling.md) | Redis-only agent scheduling | Single trigger path, simpler debugging |
| [010](./_dev/ADR/0010-ratio-based-triggering.md) | Ratio-based agent triggering | 5:1 Builder:Gardener, paces API calls |

### ADR Process

**When to create an ADR:**
- Choosing between technical approaches
- Deciding NOT to implement something
- Changing a previous decision
- Any choice affecting system structure

**How to create:**
1. Copy `_dev/ADR/_TEMPLATE.md`
2. Fill in Context, Decision, Consequences, Alternatives
3. Add to `_dev/ADR/INDEX.md`
4. Reference in this document if significant

**Status flow:** Proposed -> Accepted -> [Deprecated | Superseded]

---

## 12. Open Questions

1. **Vocabulary Sharing:** Should corrections be shared across sessions for the same user/project?
2. **Reference Caching:** How long should ReferenceNode data be considered fresh?
3. **Global Node Threshold:** When does a concept become "global" (3+ sessions? 10+ mentions?)?
4. **Human-in-the-Loop:** Should corrections/merges require user approval for high-value sessions?
5. **Streaming Q&A:** Should Librarian responses stream token-by-token?

---

## Appendix A: Gardener Prompt Template

```
You are the Gardener for a live knowledge graph. Analyse the current state 
and recommend actions.

LANGUAGE: {language_instruction}
(e.g., "Use British English spelling and grammar throughout (organisation, 
analyse, whilst, etc.)")

## CURRENT STATE
Nodes: {nodes}
Relationships: {relationships}
Recent Transcript (last 10 minutes): {transcript}
Session Vocabulary: {vocabulary}
Preferred Spellings: {preferred_spellings}
New Chunks to Proofread: {proofread_chunks}
Similarity Candidates: {similarity_hints}

## YOUR TASKS (in order)

### 1. PROOFREAD
Identify speech-to-text errors in the new chunks and node labels.
Focus on:
- Phonetic spellings of proper nouns (e.g., "see dare" -> "CeADAR")
- Technical terms that look garbled (e.g., "graph queue L" -> "GraphQL")
- Organisation names that seem wrong (e.g., "you carry" -> "UKRI")
- Inconsistent spellings of the same entity
- Language variant normalization (use preferred_spellings map for known variants)

### 2. CONFIRM OR REMOVE
For each GHOST node, decide:
- CONFIRM: Valid concept, make SOLID
- REMOVE: Noise, hallucination, or STT artifact

### 3. MERGE
Identify nodes that represent the same concept.
Consider:
- Similarity candidates (embedding matches)
- Corrected labels (after proofreading)
- Textual context from transcript

### 4. CLUSTER (FLOWERS)
Group related SOLID nodes into thematic clusters.
Requirements: 3+ nodes AND 2+ internal connections.

## OUTPUT FORMAT
{
  "corrections": [{"original": "...", "correction": "...", "confidence": 0.9}],
  "confirmations": ["node_id_1", "node_id_2"],
  "removals": ["node_id_3"],
  "merges": [{"keep": "node_id_1", "absorb": ["node_id_4", "node_id_5"]}],
  "flowers": [{"id": "...", "label": "...", "stem_node_id": "...", "members": [...]}]
}
```

---

## Appendix B: Researcher Prompt Template

```
You are a Research Assistant. Given a concept from a live talk, find relevant 
external information to help the user understand it better.

## CONCEPT
Label: {node_label}
Type: {inferred_type}
Context from transcript: {context_snippet}

## YOUR TASK
1. Search for authoritative information about this concept
2. Focus on:
   - Official definitions (for technical terms)
   - Organisation websites (for companies/institutions)
   - Funding scheme details (for grants/programmes)
   - Academic papers (for research topics)

3. Extract:
   - Title: Official name
   - URL: Primary source link
   - Summary: 2-3 sentence explanation
   - Type: definition | organisation | funding | paper | person

## OUTPUT FORMAT
{
  "title": "...",
  "url": "https://...",
  "summary": "...",
  "type": "organisation",
  "source": "google",
  "confidence": 0.9
}
```

---

## Appendix C: Librarian Prompt Template

```
You are a Research Librarian. Answer the user's question using the knowledge 
graph and transcript context provided.

## RETRIEVED CONTEXT
Nodes: {relevant_nodes}
Relationships: {relevant_relationships}
Source Chunks: {source_chunks}

## USER QUESTION
{question}

## INSTRUCTIONS
1. Answer based ONLY on the provided context
2. If the context doesn't contain relevant information, say so
3. Cite source chunks using [Chunk: {chunk_id}, Time: {start_time}s] format
4. Be concise but comprehensive

## ANSWER
```

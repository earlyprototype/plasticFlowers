# Codebase review and architecture comparison
_Exported on 12/30/2025 at 23:32:47 GMT from Cursor (2.2.44)_

---

**User**

@_docs/_START_SESSION_STATE.md @_docs/ARCHITECTURE_ADVISORY.md review code base (context in start session state doc) and compare to Archive advisory document

---

**Cursor**

I've reviewed the session state. I understand we maintain:

- **ADR**: Architecture decisions (create when choosing between approaches) - 10 current ADRs
- **SOLUTIONS_LOG**: Bug fixes (update after solving non-trivial issues)
- **VALIDATED_PATTERNS**: Proven code patterns (update when finding good solutions)
- **SESSION_STATE**: Progress tracking (update at end of every session)

**Current status**: Phase D.5 (Redis Streams) COMPLETE, next is Phase E (GraphRAG + Q&A).

---

I'll now systematically review the codebase and compare it against the ARCHITECTURE_ADVISORY.md. Let me explore the key areas:

Let me also check the frontend structure and key components, plus any existing export/Librarian endpoints:

Now I have a comprehensive view. Let me compile my analysis comparing the **ARCHITECTURE_ADVISORY.md** against the actual codebase implementation.

---

## Codebase vs Architecture Analysis

### Overview

I've reviewed the codebase against the ARCHITECTURE_ADVISORY.md. Here's a systematic comparison:

---

### 1. The Four Agents

| Agent | Architecture Says | Implementation Status |
|-------|-------------------|----------------------|
| **Builder** | Fast extraction, GHOST nodes, runs per-chunk | **IMPLEMENTED** - `backend/app/agents/builder.py`, `builder_service.py` |
| **Gardener** | Proofread, Confirm, Merge, Cluster (every 60-90s) | **IMPLEMENTED** - `backend/app/agents/gardener.py`, `scheduler.py` |
| **Researcher** | External enrichment via web search | **NOT IMPLEMENTED** - Only event types defined in `redis_streams.py` |
| **Librarian** | Q&A about sessions (GraphRAG/full context) | **NOT IMPLEMENTED** - No agent or endpoint exists |

---

### 2. API Endpoints

| Endpoint | Architecture Says | Implementation Status |
|----------|-------------------|----------------------|
| `POST /sessions` | Create session | **IMPLEMENTED** |
| `GET /sessions` | List sessions | **IMPLEMENTED** |
| `GET /sessions/{id}` | Get session detail | **IMPLEMENTED** |
| `POST /sessions/{id}/chunks` | Submit chunk | **IMPLEMENTED** |
| `GET /sessions/{id}/stream` | SSE stream | **IMPLEMENTED** |
| `GET /sessions/{id}/graph` | Full graph state | **IMPLEMENTED** |
| `GET /sessions/{id}/nodes` | List nodes | **IMPLEMENTED** |
| `GET /sessions/{id}/relationships` | List relationships | **IMPLEMENTED** |
| `GET /sessions/{id}/flowers` | List flowers | **IMPLEMENTED** |
| `POST /sessions/{id}/ask` | **Q&A (Phase E)** | **NOT IMPLEMENTED** |
| `POST /api/ask` | Cross-session Q&A | **NOT IMPLEMENTED** |
| `POST /nodes/{id}/research` | Trigger research | **NOT IMPLEMENTED** |
| `GET /sessions/{id}/summary` | LLM summary | **PARTIAL** - via `/export/markdown` |
| `GET /sessions/{id}/export` | Export JSON/MD | **IMPLEMENTED** (4 formats) |
| `GET /sessions/{id}/timeline` | Timeline reconstruction | **NOT IMPLEMENTED** |
| `POST /sessions/{id}/correct` | Manual STT correction | **NOT IMPLEMENTED** |
| `GET /sessions/{id}/vocabulary` | Session vocabulary | **NOT IMPLEMENTED** (internal only) |

---

### 3. Data Models

| Model | Architecture Says | Implementation Status |
|-------|-------------------|----------------------|
| **Node** | id, label, status, confidence, mentions, timestamps, inferred_type, flower_id, embedding, created_at, last_active, centrality_score, community_id | **MOSTLY IMPLEMENTED** - Missing: `centrality_score`, `community_id` (GDS features) |
| **Relationship** | Full spec | **IMPLEMENTED** |
| **Flower** | Full spec | **IMPLEMENTED** |
| **TranscriptChunk** | id, session_id, text, original_text, start_time, end_time | **PARTIAL** - Missing: `original_text` field for audit trail |
| **Session** | id, language_variant, created_at, title, status | **PARTIAL** - Has language_variant, missing `status` enum (active/completed/archived) |
| **ReferenceNode** | External enrichment | **NOT IMPLEMENTED** |
| **SessionVocabulary** | Corrections, preferred_spellings | **IMPLEMENTED** |
| **ProofreadCheckpoint** | Incremental proofreading | **IMPLEMENTED** (model exists, not used) |
| **TranscriptCorrection** | Audit trail | **IMPLEMENTED** (model exists) |
| **GlobalNode** | Cross-session (Phase 7) | **NOT IMPLEMENTED** (future) |

---

### 4. Redis Streams (Event Bus)

| Stream | Architecture Says | Implementation Status |
|--------|-------------------|----------------------|
| `chunks.added` | Builder -> Gardener | **IMPLEMENTED** (`pf:chunks:added`) |
| `nodes.created` | Builder -> future agents | **DEFINED** but not published |
| `nodes.needs_research` | Gardener -> Researcher | **IMPLEMENTED** (publisher, no consumer) |
| `research.requested` | API -> Researcher | **NOT IMPLEMENTED** |
| `corrections.applied` | Gardener -> Builder | **NOT IMPLEMENTED** |

---

### 5. SSE Events

| Event | Architecture Says | Implementation Status |
|-------|-------------------|----------------------|
| `node_added` | Render ghost node | **IMPLEMENTED** |
| `node_confirmed` | Transition to solid | **IMPLEMENTED** (via NodeUpdatedEvent) |
| `node_corrected` | Flash + update label | **IMPLEMENTED** |
| `node_merged` | Animate merge | **IMPLEMENTED** |
| `node_removed` | Fade out | **IMPLEMENTED** |
| `relationship_added` | Draw edge | **IMPLEMENTED** |
| `flower_formed` | Fan layout animation | **IMPLEMENTED** (`FlowerCreatedEvent`) |
| `flower_updated` | Update positions | **IMPLEMENTED** |
| `reference_added` | Add icon to node | **NOT IMPLEMENTED** |

---

### 6. Configuration

| Setting | Architecture Says | Implementation Status |
|---------|-------------------|----------------------|
| Model config | gemini-2.5-flash/pro | **IMPLEMENTED** |
| Similarity threshold | 0.92 (ADR-008) | **IMPLEMENTED** |
| Embedding dimensions | 768 | **IMPLEMENTED** |
| Redis URL | Configurable | **IMPLEMENTED** |
| Builder:Gardener ratio | Configurable | **IMPLEMENTED** (5:1 default) |
| Language variant | Session-level | **IMPLEMENTED** |

---

### 7. Phase Completion Summary

| Phase | Architecture Roadmap | Status |
|-------|---------------------|--------|
| **Phase 1: Infrastructure** | Docker, Neo4j, Redis, Vector Index | **COMPLETE** |
| **Phase 2: Gardener Enhancement** | Proofreading, vocabulary, language variant | **COMPLETE** (missing ProofreadCheckpoint usage) |
| **Phase 3: Researcher Agent** | External enrichment | **NOT STARTED** |
| **Phase 4: Librarian Agent** | Single-session Q&A | **NOT STARTED** |
| **Phase 5: Export & Summary** | Markdown, JSON export | **COMPLETE** |
| **Phase 6: GDS Algorithms** | Optional at scale | **NOT STARTED** (intentionally deferred) |
| **Phase 7: Multi-Session + GraphRAG** | Cross-session Q&A | **NOT STARTED** (future) |

---

### 8. Key Gaps (Priority Order)

**High Priority (Phase E is next):**
1. **Librarian Agent + Q&A Endpoint** - `POST /sessions/{id}/ask` not implemented
2. **Full context loading** for single-session Q&A (no neo4j-graphrag needed per ADR-004)

**Medium Priority:**
3. **Researcher Agent** - Event types exist but no consumer/endpoint
4. **ReferenceNode model** - Not in codebase
5. **TranscriptChunk.original_text** - Audit trail field missing
6. **ProofreadCheckpoint** - Model exists but incremental proofreading not used

**Low Priority (Future):**
7. **Manual correction endpoint** - `POST /sessions/{id}/correct`
8. **Vocabulary endpoint** - `GET /sessions/{id}/vocabulary`
9. **Timeline endpoint** - `GET /sessions/{id}/timeline`
10. **GDS integration** - centrality_score, community_id fields

---

### 9. Alignment Observations

**Well Aligned:**
- Builder and Gardener architecture matches spec precisely
- Redis Streams event bus is properly implemented with ratio-based triggering (ADR-010)
- Language variant support is session-level as specified
- SSE events match the spec
- Export functionality exceeds spec (4 formats vs 2)

**Divergences (Acceptable):**
- Gardener runs via ratio-based triggering (ADR-010) rather than fixed 60-90s timer
- Similarity threshold tuned to 0.92 (ADR-008) rather than original 0.85
- `gemini-2.5-flash` used for Gardener instead of `gemini-2.5-pro` (rate limit optimisation)

---

### Recommendation

Based on the SESSION_STATE showing Phase D.5 complete, the next logical step is **Phase E: GraphRAG + Q&A**. This requires:

1. Implementing the Librarian agent (full-context approach per ADR-004)
2. Adding `POST /sessions/{id}/ask` endpoint
3. Frontend Q&A panel component

Shall I proceed with planning Phase E implementation, or would you like me to address any of the identified gaps first?

---

**User**

My notes/questions/feedback:

1. Four Agents

Any areas of concern in Builder or Gardener architecture/design/implementation?

2. API Endpoints

Any areas of concern?

3. Data Models:

Missing 'original_text' for audit train seems like a significant ommission - is this something that has been overlooked or planned? If overlooked, I would like to prioritise Implementation. 

Can you explain about 'status' enum for Session model (what do you mean by 'model' in this context as shown at the top of the table?) - what is status enum important for?

Can you detail the SessionVocabulary - is it well implemented and flexible? Is there a persistance within it or persistant version?

ProofreadCheckpoint being unused seems like a big oversight - can you suggest its intention and how it might be leveraged throughout our system? What are the details of the checkpointing?

How is transcriptcorrection being implemented?

What do you believe GlobalNode is used for?

4. Redis Streams (event bus)

Can you provide more info here, focusing on development robustness and best directional design

5. SSE Events

Any obvious ommissions?

6. Configuration
Any feedback here in terms of best practice or best alignment with project goals?

7. Phase Completion Summary

Phase 2: Missing proofread checkpoint - omission? Need to address immediately if so





---

**Cursor**

Excellent questions. Let me dig deeper into each area to give you thorough answers. I'll need to examine several files to provide accurate details.

I now have a complete view. Let me provide detailed answers to each of your questions:

---

## 1. Builder / Gardener - Areas of Concern

### Builder Agent - Generally Solid

**Strengths:**
- Clean separation: `builder.py` (LLM logic) vs `builder_service.py` (orchestration)
- Retry logic for parse errors (2 attempts)
- Ratio-based Gardener triggering prevents over-calling
- Existing node deduplication in prompt

**Potential Concerns:**

| Area | Issue | Severity |
|------|-------|----------|
| **No similarity check before create** | Builder creates nodes without checking vector similarity. Architecture says "Check similarity against existing nodes (threshold: 0.92)" but this happens post-hoc in Gardener, not pre-create | **Medium** - leads to more GHOST nodes than necessary |
| **Embedding after LLM, not before** | Embeddings generated after Builder LLM returns, so Builder can't use similarity to decide whether to create a node | **Low** - design decision, Gardener cleans up |
| **No context about relationships** | Builder only sees existing node labels, not relationships. May miss context about node roles | **Low** |

### Gardener Agent - One Significant Gap

**Strengths:**
- Comprehensive prompt with proofreading, node actions, flower actions
- Language variant support built into prompt
- Vocabulary pre-application before LLM call
- Temporal decay implemented

**Concerns:**

| Area | Issue | Severity |
|------|-------|----------|
| **ProofreadCheckpoint not used** | Functions `get_proofread_checkpoint()` and `update_proofread_checkpoint()` exist in `graph_db.py` but Gardener never calls them. Entire transcript rescanned each cycle. | **HIGH** - see section 7 |
| **Proofreading targets nodes only** | Architecture says proofread "incremental chunks (10 at a time with checkpoint)". Current implementation proofreads node labels via vocabulary, but doesn't scan chunk text incrementally. | **Medium** |
| **No `chunks_processed` tracking** | Architecture shows `ProofreadCheckpoint.chunks_processed` field, but logic doesn't track which chunks have been proofread | **Medium** |

---

## 2. API Endpoints - Areas of Concern

**Generally well-aligned.** Two observations:

| Area | Status | Recommendation |
|------|--------|----------------|
| **No rate limiting** | No visible rate limiting on `/chunks` endpoint | Consider adding for production |
| **No pagination** | `list_sessions`, `list_nodes` return all records | Fine for MVP, add pagination later |

No blocking concerns - endpoints match architecture well.

---

## 3. Data Models - Detailed Answers

### 3.1 `original_text` for Audit Trail

**Status:** Partially implemented, but inconsistently.

Looking at `graph_db.py` line 1017-1024:

```python
# Update transcript chunk text (preserve original_text for audit)
chunk_query = """
SET c.original_text = coalesce(c.original_text, c.text),
    c.text = replace(c.text, $original, $corrected)
"""
```

**The `original_text` IS preserved in Neo4j when corrections are applied.** However:

1. **Not in the model:** `TranscriptChunk` model (`chunk.py`) does NOT have an `original_text` field
2. **Not retrieved:** `_chunk_from_value()` doesn't map it back
3. **Not exposed:** No API returns it

**Recommendation:** This is a **significant oversight** that should be prioritised. The data IS being stored in Neo4j, but it's invisible to the application layer. Fix requires:
1. Add `original_text: Optional[str]` to `TranscriptChunk` model
2. Update `_chunk_from_value()` to map it
3. Include in export endpoints

---

### 3.2 Session `status` Enum

**What I mean by "model":** The Pydantic `Session` model class that defines the data structure.

**Architecture says Session should have:**
```python
status: enum  # active, completed, archived
```

**Current implementation:** Uses `ended_at: Optional[datetime]` instead.

| Approach | Current | Architecture |
|----------|---------|--------------|
| Check if session is active | `session.ended_at is None` | `session.status == 'active'` |
| Check if ended | `session.ended_at is not None` | `session.status in ['completed', 'archived']` |

**Why status enum matters:**
1. **Archived vs Completed:** `ended_at` can't distinguish between "finished recording" and "archived/hidden from view"
2. **Cleaner API filtering:** `GET /sessions?status=active` vs complex date logic
3. **Future extensibility:** Could add `processing`, `error`, `paused` states

**Recommendation:** Low priority for MVP. The `ended_at` approach works. Add status enum when you need archive functionality.

---

### 3.3 SessionVocabulary - Implementation Details

**Location:** `graph_db.py` lines 860-930

**How it's stored:**
```python
MERGE (v:SessionVocabulary {session_id: $session_id})
SET v.corrections_json = $corrections_json,  # JSON string
    v.language_variant = $language_variant,
    v.updated_at = datetime()
```

**Key points:**

| Aspect | Implementation |
|--------|----------------|
| **Persistence** | **YES** - Stored as Neo4j node `(:SessionVocabulary)` |
| **Format** | JSON string (Neo4j doesn't support Map properties natively) |
| **Merge behaviour** | New corrections merge INTO existing (additive) |
| **Threshold** | Only corrections with `confidence > 0.8` are saved |

**Flexibility Assessment:**

| Feature | Status |
|---------|--------|
| Per-session isolation | Yes |
| Language variant stored | Yes |
| Merge (not replace) semantics | Yes |
| Preferred spellings field | **NOT IMPLEMENTED** - model has it, Neo4j doesn't store it |
| Deletion of corrections | **NOT IMPLEMENTED** - can only add |
| API endpoint | **NOT IMPLEMENTED** - internal only |

**Recommendation:** The core is solid. Missing pieces:
1. Add `preferred_spellings_json` storage for en-GB/en-US variant normalisation
2. Add `DELETE` capability if users need to undo learned corrections
3. Consider an API endpoint for vocabulary inspection/management

---

### 3.4 ProofreadCheckpoint - Intention and Usage

**What it's for (per Architecture):**

The Gardener should proofread **incrementally** - not rescan the entire transcript every cycle:

```
Cycle 1: Proofread chunks 1-10, checkpoint at chunk 10
Cycle 2: Proofread chunks 11-20, checkpoint at chunk 20
Cycle 3: Proofread chunks 21-30, checkpoint at chunk 30
```

**Why this matters:**
1. **Efficiency:** Don't re-proofread chunks you've already corrected
2. **Cost:** LLM tokens wasted on repeated content
3. **Correctness:** Avoid applying same correction twice

**Current State:**

| Component | Status |
|-----------|--------|
| `ProofreadCheckpoint` model | Exists in `vocabulary.py` |
| `get_proofread_checkpoint()` | Exists in `graph_db.py` |
| `update_proofread_checkpoint()` | Exists in `graph_db.py` |
| Neo4j node type | `(:ProofreadCheckpoint)` ready |
| **Usage in Gardener** | **NOT CALLED** |

**How it should work:**

```python
# In scheduler.py _run_gardener():

# 1. Get checkpoint
last_chunk_id = await get_proofread_checkpoint(session_id)

# 2. Get only NEW chunks since checkpoint
new_chunks = await get_chunks_since(session_id, last_chunk_id, limit=10)

# 3. Pass new_chunks to Gardener for proofreading
# (currently passes recent_transcript instead)

# 4. After Gardener completes, update checkpoint
if new_chunks:
    await update_proofread_checkpoint(session_id, new_chunks[-1].id)
```

**This is a significant gap** - see Section 7 for priority.

---

### 3.5 TranscriptCorrection Implementation

**Model exists** in `vocabulary.py`:

```python
class TranscriptCorrection(BaseModel):
    id: str
    session_id: str
    original: str
    correction: str
    confidence: float
    applied_at: datetime
    affected_node_ids: list[str]
    affected_chunk_ids: list[str]
    reason: Optional[str]
```

**However: NOT persisted to Neo4j.**

Looking at `_apply_corrections()` in `scheduler.py`, corrections are:
1. Applied to graph via `apply_corrections_to_graph()`
2. Broadcast via SSE (`NodeCorrectedEvent`)
3. Added to vocabulary via `update_session_vocabulary()`

**What's missing:**
- No `TranscriptCorrection` nodes created in Neo4j
- No audit trail of individual corrections with timestamps
- Can't answer "what corrections were made and when?"

**Recommendation:** Medium priority. Add `save_correction()` call in `_apply_corrections()` for audit trail.

---

### 3.6 GlobalNode Purpose

**What it's for:** Cross-session knowledge linking (Phase 7).

**Example scenario:**
- Session 1: Speaker mentions "Neo4j" (creates Node in session_1)
- Session 2: Different speaker mentions "Neo4j" (creates Node in session_2)
- GlobalNode: Links both session-specific nodes to a canonical `GlobalNode` for "Neo4j"

```
(:Node {session_id: "s1", label: "Neo4j"})-[:INSTANCE_OF]->(:GlobalNode {canonical_label: "Neo4j"})
(:Node {session_id: "s2", label: "neo4j"})-[:INSTANCE_OF]->(:GlobalNode {canonical_label: "Neo4j"})
```

**Enables:**
1. Cross-session Q&A: "What do all speakers say about Neo4j?"
2. Conference-wide trends: "Neo4j mentioned in 12 sessions"
3. Semantic navigation: Click GlobalNode to see all sessions mentioning it

**Not needed until Phase 7** - correctly deferred.

---

## 4. Redis Streams - Robustness and Design

**Current Implementation Review:**

| Aspect | Implementation | Assessment |
|--------|----------------|------------|
| **Stream naming** | `pf:chunks:added` namespaced | Good - avoids collisions |
| **Consumer groups** | `gardener` group defined | Good - enables scaling |
| **Message acknowledgment** | `ack_event()` after processing | Good - at-least-once delivery |
| **Error handling** | Catches `ConnectionError`, `ResponseError` | Good |
| **Startup flush** | `flush_stale_events()` clears old messages | Good - prevents stale processing |
| **Backpressure** | 5-second block on empty stream | Good - prevents busy-wait |

**Robustness Concerns:**

| Issue | Current | Recommendation |
|-------|---------|----------------|
| **No dead letter queue** | Failed messages logged but lost | Consider DLQ for debugging |
| **No message TTL** | `maxlen=10000` caps size, not age | Acceptable for MVP |
| **Single consumer** | `gardener-worker-1` hardcoded | Fine for single instance, parameterise for scaling |
| **No retry with exponential backoff** | Immediate retry on error | Add backoff for sustained failures |

**Best Directional Design:**

The current design follows Redis Streams best practices:
1. **Consumer groups** for reliable delivery
2. **Explicit acknowledgment** prevents message loss
3. **Startup flush** prevents zombie processing
4. **Ratio-based publishing** prevents message flooding

**One improvement:** The `STREAM_NODES_CREATED` is defined but never published. Either use it (for future agents) or remove it to avoid confusion.

---

## 5. SSE Events - Obvious Omissions

Comparing against Architecture:

| Event | Architecture | Implemented |
|-------|--------------|-------------|
| `node_added` | Yes | Yes |
| `node_confirmed` | Yes | **Partial** - uses `NodeUpdatedEvent` |
| `node_corrected` | Yes | Yes (`NodeCorrectedEvent`) |
| `node_merged` | Yes | Yes |
| `node_removed` | Yes | Yes |
| `relationship_added` | Yes | Yes |
| `relationship_removed` | Not explicit | Yes (exists) |
| `flower_formed` | Yes | Yes (`FlowerCreatedEvent`) |
| `flower_updated` | Yes | Yes |
| `flower_dissolved` | Not explicit | Yes (exists) |
| `reference_added` | Yes | **NOT IMPLEMENTED** (Phase 3) |
| `gardener_cycle` | Not explicit | Yes (heartbeat) |

**Minor observation:** `node_confirmed` uses generic `NodeUpdatedEvent` rather than a specific confirmation event. Frontend must check `status` field to distinguish confirmation from other updates. Acceptable design.

**Missing (expected):** `reference_added` - correctly not implemented as Researcher isn't built yet.

---

## 6. Configuration - Best Practice Feedback

**Review of `config.py`:**

| Setting | Value | Assessment |
|---------|-------|------------|
| `similarity_threshold: 0.92` | Tuned via ADR-008 | Excellent - documented decision |
| `gemini_request_timeout: 180.0` | 3 minutes | High but justified in comments |
| `builder_gardener_ratio: 5` | Every 5 chunks | Good default, documented in ADR-010 |
| `gardener_debounce_seconds: 30` | Marked deprecated | Clean deprecation |

**Suggestions:**

| Area | Current | Recommendation |
|------|---------|----------------|
| **Secrets** | `SecretStr` for API key | Good |
| **Defaults** | Sensible values | Good |
| **Validation** | `ge`, `le` constraints | Good |
| **Documentation** | `description` on every field | Excellent |
| **Model auto-correction** | Fixes `gemini-3-flash` -> `gemini-3-flash-preview` | Nice touch |

**One suggestion:** Consider adding `GARDENER_ENABLED: bool = True` to allow disabling Gardener entirely for debugging Builder in isolation.

---

## 7. Phase 2 - ProofreadCheckpoint Omission

**Yes, this is a significant omission that should be addressed.**

**Impact:**
1. Every Gardener cycle re-processes the entire recent transcript
2. Wasted LLM tokens on already-proofread content
3. Risk of re-applying corrections (though vocabulary prevents duplicates)

**The infrastructure exists** - functions are implemented in `graph_db.py`:
- `get_proofread_checkpoint(session_id)` - line 933
- `update_proofread_checkpoint(session_id, last_chunk_id)` - line 954

**What's missing:** Integration in `scheduler.py`.

**Recommended Fix (Small scope):**

```python
# In scheduler.py _run_gardener(), after loading nodes:

# Get checkpoint
checkpoint = await get_proofread_checkpoint(session_id)

# Get chunks for proofreading (only unproofread ones)
if checkpoint:
    # Get chunks created after checkpoint
    chunks_to_proofread = await get_chunks_after(session_id, checkpoint)
else:
    # First run - get all chunks (or limit to recent N)
    chunks_to_proofread = await list_chunks_for_session(session_id)[-10:]

# After successful Gardener run:
if chunks_to_proofread:
    await update_proofread_checkpoint(session_id, chunks_to_proofread[-1].id)
```

**Missing helper:** Need `get_chunks_after(session_id, chunk_id)` function in `graph_db.py`.

---

## Summary: Priority Actions

| Priority | Item | Effort |
|----------|------|--------|
| **HIGH** | Add `original_text` to TranscriptChunk model and retrieval | Small |
| **HIGH** | Integrate ProofreadCheckpoint into Gardener | Medium |
| **MEDIUM** | Add `preferred_spellings` storage to SessionVocabulary | Small |
| **MEDIUM** | Persist TranscriptCorrection for audit trail | Small |
| **LOW** | Add Session status enum | Small |
| **LOW** | Remove unused `STREAM_NODES_CREATED` or implement | Tiny |

Would you like me to implement the HIGH priority items now, or proceed with Phase E planning first?

```python
# Update transcript chunk text (preserve original_text for audit)
chunk_query = """
SET c.original_text = coalesce(c.original_text, c.text),
    c.text = replace(c.text, $original, $corrected)
"""
```

```python
status: enum  # active, completed, archived
```

```python
MERGE (v:SessionVocabulary {session_id: $session_id})
SET v.corrections_json = $corrections_json,  # JSON string
    v.language_variant = $language_variant,
    v.updated_at = datetime()
```

```plaintext
Cycle 1: Proofread chunks 1-10, checkpoint at chunk 10
Cycle 2: Proofread chunks 11-20, checkpoint at chunk 20
Cycle 3: Proofread chunks 21-30, checkpoint at chunk 30
```

```python
# In scheduler.py _run_gardener():

# 1. Get checkpoint
last_chunk_id = await get_proofread_checkpoint(session_id)

# 2. Get only NEW chunks since checkpoint
new_chunks = await get_chunks_since(session_id, last_chunk_id, limit=10)

# 3. Pass new_chunks to Gardener for proofreading
# (currently passes recent_transcript instead)

# 4. After Gardener completes, update checkpoint
if new_chunks:
    await update_proofread_checkpoint(session_id, new_chunks[-1].id)
```

```python
class TranscriptCorrection(BaseModel):
    id: str
    session_id: str
    original: str
    correction: str
    confidence: float
    applied_at: datetime
    affected_node_ids: list[str]
    affected_chunk_ids: list[str]
    reason: Optional[str]
```

```plaintext
(:Node {session_id: "s1", label: "Neo4j"})-[:INSTANCE_OF]->(:GlobalNode {canonical_label: "Neo4j"})
(:Node {session_id: "s2", label: "neo4j"})-[:INSTANCE_OF]->(:GlobalNode {canonical_label: "Neo4j"})
```

```python
# In scheduler.py _run_gardener(), after loading nodes:

# Get checkpoint
checkpoint = await get_proofread_checkpoint(session_id)

# Get chunks for proofreading (only unproofread ones)
if checkpoint:
    # Get chunks created after checkpoint
    chunks_to_proofread = await get_chunks_after(session_id, checkpoint)
else:
    # First run - get all chunks (or limit to recent N)
    chunks_to_proofread = await list_chunks_for_session(session_id)[-10:]

# After successful Gardener run:
if chunks_to_proofread:
    await update_proofread_checkpoint(session_id, chunks_to_proofread[-1].id)
```

---

**User**

[GENERAL NOTE: 1) When detailling an issue please detail more on the effect or implications of said issue, and what benefits a fix would bring. 2) Create a document markdown to document our entire discussions and discovery here - Thank you]

Builder Agent:
- When you say builder creates nodes without checking vector similarity - does that mean we are creating vector db in parallel (ie, there is something to check against?). I note your second point about embedding occuring after LLM - Im assuming this answers my question. Would embedding first offer significant value at builder stage? How long would embedding first delay builder run?
- No relationship/edge context seems like an oversignt. We should ammend. 

Gardener Agent (addressing concerns)
- Is checkpoint a timestamp or time since last checkpoint? Does this enable curating text for proofreading if implemented?
- Chunk processing tracking need implemented.

2. API endpoints
- Make notes on both, include implications. 

3. Data Models
3.1 original_text - Lets make the data visible in the application layer. What benefits will this bring to the application layer? Are we doing things the hard way currently but not exposing, or does this just add value?

3.2 status enum - session management is important for overall stability of app, correct? Maybe we should promote importance of this implementation? Im assuming this will promote robustness? How robust in session management currently? What does fragile session management threaten functionally in current app?

3.3 SessionVocabulary - agree with recommendations

3.4 ProofreadCheckpoint - the issue we have here is we might lose context related to the overall theming of the session (eg, 'talk by Enterprise Ireland on the EDIH network') - do we have a way to persist this? SessionVocabulary perhaps or seperate function? I agree with suggested implmentation but we need to feed context of session.

3.5 TranscriptionCorrection - agree with recommendations

4. Redis Steams - note all concerns in doc. I agree with recommentations

5. SSE Events

node_confirmed - we should update
Reference_added - we should implement with Researcher agent

We should update documentation for existing event types that are used but not mentioned in architecture/docs

6. Configuration
Gemini_request_timeout - should be brought back down to 90 sec since we fixed LLM call length issue.

Suggestions: agree to add gardener_enabled variable - we should make that architectural practice for all agents. Document.

7. agree - see earlier notes on persistant context of session theme

Summary: Priority Actions
Good!

Please create document as requested at start of my reply here and then provide response to my questions and then we will begin preparing to implement priority actions via a plan



---

**Cursor**

I'll create the discovery document first, then answer your questions.

```markdown
# Architecture Review: Codebase vs ARCHITECTURE_ADVISORY.md

**Date:** 30 December 2025  
**Session:** Architecture alignment review and gap analysis  
**Reviewers:** User + LLM Assistant  
**Scope:** Full codebase comparison against ARCHITECTURE_ADVISORY.md v8.1

---

## Executive Summary

This document captures a comprehensive review of the plasticFlower codebase against the architectural specification. The review identified several gaps, implementation concerns, and priority actions for alignment.

**Key Findings:**
- Builder and Gardener agents are well-implemented with minor gaps
- Phase D.5 (Redis Streams) is complete and robust
- Several data model fields exist in spec but not exposed in application layer
- ProofreadCheckpoint infrastructure exists but is not utilised
- Phase E (Librarian/Q&A) and Phase 3 (Researcher) are not started

---

## 1. Agent Architecture Review

### 1.1 Builder Agent

**Files reviewed:** `backend/app/agents/builder.py`, `backend/app/services/builder_service.py`

#### Strengths
- Clean separation: `builder.py` (LLM logic) vs `builder_service.py` (orchestration)
- Retry logic for parse errors (2 attempts)
- Ratio-based Gardener triggering prevents API over-calling
- Existing node deduplication in prompt context

#### Concerns

| Issue | Description | Implications | Recommended Fix |
|-------|-------------|--------------|-----------------|
| **No pre-create similarity check** | Builder creates nodes without checking vector similarity first. Architecture specifies "Check similarity against existing nodes (threshold: 0.92)" but this happens post-hoc in Gardener | More GHOST nodes created than necessary; Gardener has more cleanup work; higher LLM costs for merge decisions | Evaluate embedding-first approach (see analysis below) |
| **Embedding after LLM** | Embeddings generated after Builder LLM returns, so Builder can't use similarity to decide whether to create a node | Builder cannot make informed deduplication decisions; relies entirely on Gardener | Same as above |
| **No relationship context in prompt** | Builder only sees existing node labels, not relationships. Misses context about node roles and connections | May create nodes that would be better understood in relationship context; e.g., "Enterprise Ireland" without knowing it's already connected to "EDIH" | Add relationship summary to Builder prompt |

#### Embedding-First Analysis

**Current flow:**
```
1. Receive chunk
2. Load existing node labels (for prompt)
3. Call LLM -> extract nodes
4. Generate embeddings for new nodes
5. Persist to Neo4j
```

**Proposed flow with pre-check:**
```
1. Receive chunk
2. Load existing nodes + embeddings
3. For each extracted entity mention in chunk:
   a. Generate embedding
   b. Check similarity against existing
   c. If match > 0.92: skip (existing node)
4. Call LLM with remaining entities only
5. Persist new nodes
```

**Trade-offs:**

| Aspect | Current | With Pre-check |
|--------|---------|----------------|
| Latency | ~2-3s per chunk | +200-500ms for embeddings |
| LLM tokens | Full extraction every time | Potentially fewer (skip known entities) |
| Accuracy | Gardener cleans up | Earlier deduplication |
| Complexity | Simple | More complex orchestration |

**Recommendation:** Document as ADR. The current approach (Gardener cleans up) is acceptable for MVP. Pre-check would add latency for every chunk. Revisit if duplicate GHOST nodes become problematic.

---

### 1.2 Gardener Agent

**Files reviewed:** `backend/app/agents/gardener.py`, `backend/app/services/scheduler.py`

#### Strengths
- Comprehensive prompt with proofreading, node actions, flower actions
- Language variant support built into prompt
- Vocabulary pre-application before LLM call
- Temporal decay implemented
- Redis-based event-driven triggering (ADR-009, ADR-010)

#### Concerns

| Issue | Description | Implications | Recommended Fix |
|-------|-------------|--------------|-----------------|
| **ProofreadCheckpoint not used** | Functions `get_proofread_checkpoint()` and `update_proofread_checkpoint()` exist in `graph_db.py` but Gardener never calls them | Entire transcript rescanned each cycle; wasted LLM tokens; risk of re-applying corrections; longer processing time | Integrate checkpoint into Gardener cycle |
| **No incremental chunk proofreading** | Architecture says proofread "incremental chunks (10 at a time with checkpoint)". Current implementation proofreads node labels via vocabulary, but doesn't scan chunk text incrementally | Same as above | Implement chunk-based proofreading with checkpoint |
| **No session context persistence** | When using checkpoints, Gardener may lose understanding of overall session theme (e.g., "Enterprise Ireland talk about EDIH network") | Proofreading decisions may lack context; corrections might be inconsistent with session theme | Add session context summary to Gardener prompt |

#### ProofreadCheckpoint Details

**What checkpoint stores:**
```python
class ProofreadCheckpoint(BaseModel):
    session_id: str           # Session identifier
    last_chunk_id: str        # ID of last processed TranscriptChunk
    last_run: datetime        # Timestamp of last proofread cycle
    chunks_processed: int     # Total chunks proofread in session
```

**How it enables incremental proofreading:**
1. First Gardener cycle: Process chunks 1-10, save checkpoint pointing to chunk 10
2. Second cycle: Query for chunks AFTER chunk 10, process chunks 11-20
3. Continue until caught up with live ingestion

**Session Context Solution:**
Create a `SessionContext` or extend `SessionVocabulary` to store:
```python
session_theme: str  # "Enterprise Ireland presentation on EDIH network"
key_entities: list[str]  # ["Enterprise Ireland", "EDIH", "digital innovation"]
speaker_names: list[str]  # For name recognition
```

This context would be:
1. Extracted by first Gardener cycle (or manually set)
2. Persisted in Neo4j
3. Included in every Gardener prompt for consistent understanding

---

## 2. API Endpoints Review

### 2.1 Implemented Endpoints

| Endpoint | Purpose | Status |
|----------|---------|--------|
| `POST /sessions` | Create session | Implemented |
| `GET /sessions` | List sessions | Implemented |
| `GET /sessions/{id}` | Get session detail | Implemented |
| `POST /sessions/{id}/chunks` | Submit chunk | Implemented |
| `GET /sessions/{id}/stream` | SSE stream | Implemented |
| `GET /sessions/{id}/graph` | Full graph state | Implemented |
| `GET /sessions/{id}/nodes` | List nodes | Implemented |
| `GET /sessions/{id}/relationships` | List relationships | Implemented |
| `GET /sessions/{id}/flowers` | List flowers | Implemented |
| `GET /sessions/{id}/export/*` | Export (4 formats) | Implemented |
| `POST /sessions/{id}/end` | End session | Implemented |
| `PATCH /sessions/{id}` | Rename session | Implemented |
| `DELETE /sessions/{id}` | Delete session | Implemented |

### 2.2 Missing Endpoints (Per Architecture)

| Endpoint | Purpose | Phase |
|----------|---------|-------|
| `POST /sessions/{id}/ask` | Single-session Q&A | Phase E |
| `POST /api/ask` | Cross-session Q&A | Phase 7 |
| `POST /nodes/{id}/research` | Trigger research | Phase 3 |
| `GET /sessions/{id}/timeline` | Timeline reconstruction | Future |
| `POST /sessions/{id}/correct` | Manual STT correction | Future |
| `GET /sessions/{id}/vocabulary` | Session vocabulary | Future |

### 2.3 Concerns

| Issue | Description | Implications | Recommended Fix |
|-------|-------------|--------------|-----------------|
| **No rate limiting** | No visible rate limiting on `/chunks` endpoint | Malicious or runaway clients could flood the system; API costs could spike; could exhaust LLM quota rapidly | Add rate limiting middleware for production |
| **No pagination** | `list_sessions`, `list_nodes` return all records | Memory pressure with large datasets; slow responses; potential timeouts at scale | Add `limit` and `offset` query parameters |

**Rate Limiting Implications:**
- Without limits, a single client could submit 100 chunks/second
- Each chunk triggers Builder LLM call + embedding generation
- Could exhaust Gemini API quota in minutes
- Could overwhelm Neo4j with write operations

**Pagination Implications:**
- Currently fine for MVP (< 1000 nodes per session)
- At scale (10k+ nodes), responses become unwieldy
- Frontend must load all data into memory
- No way to progressively load large graphs

---

## 3. Data Models Review

### 3.1 TranscriptChunk.original_text

**Architecture specifies:**
```python
class TranscriptChunk:
    text: str           # Chunk content (corrected)
    original_text: str  # Original STT output (for audit)
```

**Current implementation:**
- Model (`chunk.py`) does NOT have `original_text` field
- Neo4j DOES store it when corrections applied (line 1017-1024 in graph_db.py)
- `_chunk_from_value()` doesn't retrieve it
- No API exposes it

**Implications of current state:**
- Audit trail exists in database but invisible to application
- Cannot show users "before/after" of corrections
- Cannot export original uncorrected transcript
- Cannot analyse STT error patterns
- Cannot roll back corrections if needed

**Benefits of exposing:**
- Complete audit trail accessible via API
- Export can include both original and corrected text
- Debugging STT errors becomes possible
- User confidence in correction quality
- Enables "show changes" UI feature

**Fix required:**
1. Add `original_text: Optional[str] = None` to `TranscriptChunk` model
2. Update `_chunk_from_value()` to map it
3. Include in export endpoints

---

### 3.2 Session Status Enum

**Architecture specifies:**
```python
class Session:
    status: enum  # active, completed, archived
```

**Current implementation:**
Uses `ended_at: Optional[datetime]` only.

**Session Management Robustness Assessment:**

| Aspect | Current State | Risk Level |
|--------|---------------|------------|
| Detecting active sessions | Check `ended_at is None` | Low - works |
| Ending sessions | Sets `ended_at` timestamp | Low - works |
| Archiving sessions | Not possible | Medium |
| Session lifecycle states | Binary (active/ended) | Medium |
| Concurrent session limits | Not enforced | Medium |
| Orphaned sessions | No cleanup mechanism | Medium |

**What fragile session management threatens:**

1. **Resource leaks:** SSE connections for "ended" sessions might not be cleaned up properly if status isn't explicit
2. **Gardener confusion:** Gardener might process ended sessions if `ended_at` check is missed
3. **UI inconsistency:** No way to hide archived sessions without deleting them
4. **State ambiguity:** Is a session with no activity for 1 hour "ended" or "paused"?
5. **Multi-session conflicts:** No way to mark sessions as "processing" to prevent concurrent modifications

**Recommendation:** Promote to MEDIUM priority. Add status enum for robustness:
```python
class SessionStatus(str, Enum):
    ACTIVE = "active"        # Currently receiving chunks
    PAUSED = "paused"        # Temporarily stopped (future)
    COMPLETED = "completed"  # Ended normally
    ARCHIVED = "archived"    # Hidden from default views
    ERROR = "error"          # Failed processing (future)
```

---

### 3.3 SessionVocabulary

**Implementation location:** `graph_db.py` lines 860-930

**Storage mechanism:**
- Persisted as Neo4j node `(:SessionVocabulary)`
- Corrections stored as JSON string (Neo4j limitation)
- Merge semantics (new corrections add to existing)

**Current capabilities:**
- Per-session isolation
- Language variant stored
- Additive merge behaviour
- Confidence threshold (> 0.8 to save)

**Missing capabilities:**
- `preferred_spellings` field not stored (model has it, Neo4j doesn't)
- No deletion of corrections
- No API endpoint for inspection/management

**Recommendations:**
1. Add `preferred_spellings_json` column for en-GB/en-US normalisation
2. Add deletion capability for incorrect corrections
3. Consider API endpoint for vocabulary management

---

### 3.4 ProofreadCheckpoint

**Status:** Infrastructure exists, not utilised.

**Functions available:**
- `get_proofread_checkpoint(session_id)` - retrieves last chunk ID
- `update_proofread_checkpoint(session_id, last_chunk_id)` - saves progress

**What checkpoint tracks:**
- `last_chunk_id`: ID of last proofread chunk (not a timestamp)
- `last_run`: When checkpoint was updated
- `chunks_processed`: Running count

**Missing implementation:** Integration in `scheduler.py`

**Session Context Concern:**
When using incremental proofreading, Gardener loses visibility of earlier chunks. This could cause:
- Inconsistent corrections (different style in chunk 50 vs chunk 5)
- Missed co-references ("that system" referring to something mentioned 20 chunks ago)
- Theme drift

**Recommended solution: Session Context Store**

```python
class SessionContext(BaseModel):
    session_id: str
    theme_summary: str  # "Enterprise Ireland on EDIH network"
    key_entities: list[str]  # Important recurring entities
    speaker_names: list[str]  # For name recognition
    domain_terms: list[str]  # Technical vocabulary
    updated_at: datetime
```

This would be:
1. Generated/updated by Gardener during first few cycles
2. Persisted in Neo4j
3. Included in every Gardener prompt
4. Separate from SessionVocabulary (which is for corrections)

---

### 3.5 TranscriptCorrection

**Status:** Model exists, not persisted.

**Current flow:**
1. Gardener returns corrections
2. Applied to graph via `apply_corrections_to_graph()`
3. Broadcast via SSE
4. Added to vocabulary

**Missing:** No `TranscriptCorrection` nodes created in Neo4j

**Implications:**
- Cannot audit when specific corrections were made
- Cannot analyse correction quality over time
- Cannot show correction history to users
- Cannot roll back specific corrections

**Recommendation:** Add `save_correction()` function and call it in `_apply_corrections()`

---

### 3.6 GlobalNode

**Purpose:** Cross-session knowledge linking (Phase 7)

**Use case:**
- Session 1: Node "Neo4j" created
- Session 2: Node "neo4j" created (different case)
- GlobalNode: Links both to canonical representation

**Benefits when implemented:**
- Cross-session Q&A: "What do all speakers say about Neo4j?"
- Conference-wide trends: "Neo4j mentioned in 12 sessions"
- Semantic navigation across sessions

**Status:** Correctly deferred to Phase 7

---

## 4. Redis Streams (Event Bus) Review

**Files reviewed:** `backend/app/services/redis_streams.py`

### 4.1 Implementation Assessment

| Aspect | Implementation | Assessment |
|--------|----------------|------------|
| Stream naming | `pf:chunks:added` namespaced | Good |
| Consumer groups | `gardener` group defined | Good |
| Message acknowledgment | `ack_event()` after processing | Good |
| Error handling | Catches `ConnectionError`, `ResponseError` | Good |
| Startup flush | `flush_stale_events()` clears old messages | Good |
| Backpressure | 5-second block on empty stream | Good |

### 4.2 Concerns

| Issue | Description | Implications | Recommended Fix |
|-------|-------------|--------------|-----------------|
| **No dead letter queue** | Failed messages logged but lost | Cannot debug recurring failures; no retry mechanism for persistent errors | Add DLQ stream for failed messages |
| **No message TTL** | `maxlen=10000` caps size, not age | Old messages may persist indefinitely if not consumed; potential confusion | Acceptable for MVP; consider XTRIM by time later |
| **Single consumer name** | `gardener-worker-1` hardcoded | Cannot scale to multiple Gardener instances easily | Parameterise consumer name |
| **No exponential backoff** | Immediate retry on error | Could hammer failing service; no graceful degradation | Add exponential backoff for sustained failures |
| **Unused stream defined** | `STREAM_NODES_CREATED` defined but never published | Code confusion; suggests incomplete implementation | Either implement or remove |

### 4.3 Defined Streams

| Stream | Publisher | Consumer | Status |
|--------|-----------|----------|--------|
| `pf:chunks:added` | Builder | Gardener | Active |
| `pf:nodes:created` | (none) | (none) | Defined, unused |
| `pf:nodes:needs_research` | Gardener | Researcher | Publisher only |
| `pf:gardener:complete` | Gardener | SSE | Active |

---

## 5. SSE Events Review

### 5.1 Event Coverage

| Event | Architecture | Implemented | Notes |
|-------|--------------|-------------|-------|
| `node_added` | Yes | Yes | Via `NodeAddedEvent` |
| `node_confirmed` | Yes | Partial | Uses generic `NodeUpdatedEvent` |
| `node_corrected` | Yes | Yes | Via `NodeCorrectedEvent` |
| `node_merged` | Yes | Yes | Via `NodeMergedEvent` |
| `node_removed` | Yes | Yes | Via `NodeRemovedEvent` |
| `relationship_added` | Yes | Yes | Via `RelationshipAddedEvent` |
| `relationship_removed` | Not specified | Yes | Via `RelationshipRemovedEvent` |
| `flower_formed` | Yes | Yes | Via `FlowerCreatedEvent` |
| `flower_updated` | Yes | Yes | Via `FlowerUpdatedEvent` |
| `flower_dissolved` | Not specified | Yes | Via `FlowerDissolvedEvent` |
| `reference_added` | Yes | No | Requires Researcher agent |
| `gardener_cycle` | Not specified | Yes | Via `GardenerCycleEvent` |
| `chunk_processed` | Not specified | Yes | Via `ChunkProcessedEvent` |

### 5.2 Actions Required

| Action | Description | Priority |
|--------|-------------|----------|
| Create `NodeConfirmedEvent` | Distinct from generic update for clearer frontend handling | Low |
| Implement `reference_added` | Add when Researcher agent is built | Phase 3 |
| Document existing events | `relationship_removed`, `flower_dissolved`, `gardener_cycle`, `chunk_processed` not in ARCHITECTURE_ADVISORY.md | Medium |

---

## 6. Configuration Review

**File reviewed:** `backend/app/config.py`

### 6.1 Current Settings Assessment

| Setting | Value | Assessment |
|---------|-------|------------|
| `similarity_threshold: 0.92` | Tuned via ADR-008 | Excellent |
| `gemini_request_timeout: 180.0` | 3 minutes | **Should reduce to 90s** |
| `builder_gardener_ratio: 5` | Every 5 chunks | Good default |
| `gardener_debounce_seconds: 30` | Marked deprecated | Clean deprecation |

### 6.2 Recommendations

| Recommendation | Rationale |
|----------------|-----------|
| Reduce `gemini_request_timeout` to 90s | Thinking mode issue fixed; 180s no longer needed |
| Add `GARDENER_ENABLED: bool = True` | Allow disabling for debugging |
| Add `BUILDER_ENABLED: bool = True` | Consistent pattern |
| Add `RESEARCHER_ENABLED: bool = True` | For future agent |
| Document agent enable pattern | Architectural practice for all agents |

### 6.3 Proposed Agent Configuration Pattern

```python
# Agent enable flags (allows disabling for debugging/testing)
builder_enabled: bool = Field(True, description="Enable Builder agent processing")
gardener_enabled: bool = Field(True, description="Enable Gardener scheduling")
researcher_enabled: bool = Field(True, description="Enable Researcher agent (Phase 3)")
librarian_enabled: bool = Field(True, description="Enable Librarian Q&A (Phase E)")
```

---

## 7. Phase Completion Summary

| Phase | Description | Status | Notes |
|-------|-------------|--------|-------|
| Phase 1 | Infrastructure | Complete | Docker, Neo4j, Redis, Vector Index |
| Phase 2 | Gardener Enhancement | **Partial** | ProofreadCheckpoint not integrated |
| Phase 3 | Researcher Agent | Not started | - |
| Phase 4 | Librarian Agent | Not started | Next priority |
| Phase 5 | Export & Summary | Complete | 4 formats implemented |
| Phase 6 | GDS Algorithms | Deferred | Intentionally - scale feature |
| Phase 7 | Multi-Session | Not started | Future |

---

## 8. Priority Actions

### 8.1 HIGH Priority

| Item | Description | Effort | Impact |
|------|-------------|--------|--------|
| Expose `original_text` | Add to model, retrieval, and API | Small | Enables audit trail |
| Integrate ProofreadCheckpoint | Connect existing functions to Gardener | Medium | Efficiency, cost reduction |
| Add session context persistence | Store theme/entities for Gardener context | Medium | Quality of proofreading |

### 8.2 MEDIUM Priority

| Item | Description | Effort | Impact |
|------|-------------|--------|--------|
| Add `preferred_spellings` storage | Extend SessionVocabulary | Small | Language variant support |
| Persist TranscriptCorrection | Add audit trail | Small | Debugging, rollback |
| Add Session status enum | Lifecycle management | Small | Robustness |
| Add relationship context to Builder | Include edges in prompt | Small | Better extraction |
| Update SSE event types | Create specific confirmation event | Small | Cleaner frontend |
| Reduce timeout to 90s | Config change | Tiny | Resource efficiency |
| Add agent enable flags | Config pattern | Small | Debugging capability |
| Document undocumented SSE events | Update ARCHITECTURE_ADVISORY.md | Small | Clarity |

### 8.3 LOW Priority (Future)

| Item | Description | Phase |
|------|-------------|-------|
| Add rate limiting | Production hardening | Pre-production |
| Add pagination | Scale handling | When needed |
| Dead letter queue | Redis robustness | Production |
| Embedding-first deduplication | Optimisation | If duplicates problematic |

---

## 9. Next Steps

1. Implement HIGH priority items
2. Begin Phase E (Librarian/Q&A) planning
3. Update ARCHITECTURE_ADVISORY.md with discoveries
4. Create ADRs for new decisions

---

## Appendix A: Files Reviewed

- `backend/app/agents/builder.py`
- `backend/app/agents/gardener.py`
- `backend/app/services/builder_service.py`
- `backend/app/services/scheduler.py`
- `backend/app/services/graph_db.py`
- `backend/app/services/redis_streams.py`
- `backend/app/models/chunk.py`
- `backend/app/models/session.py`
- `backend/app/models/vocabulary.py`
- `backend/app/models/node.py`
- `backend/app/api/chunks.py`
- `backend/app/api/sessions.py`
- `backend/app/api/graph.py`
- `backend/app/api/export.py`
- `backend/app/config.py`
- `_docs/ARCHITECTURE_ADVISORY.md`
- `_docs/_START_SESSION_STATE.md`

```

Document created at `_docs/_evidence/architecture_review_2025-12-30.md`. Now let me answer your specific questions:

---

## Your Questions Answered

### Builder Agent Questions

**Q: When you say Builder creates nodes without checking vector similarity - does that mean we are creating vector db in parallel?**

The vector index exists in Neo4j and contains embeddings for existing nodes. **However**, the Builder doesn't query it before creating new nodes.

Current flow:
1. Builder receives chunk text
2. Builder loads existing node *labels* (not embeddings)
3. Builder calls LLM with labels as context
4. LLM extracts new entities
5. **AFTER** LLM returns: embeddings generated for new nodes
6. New nodes persisted to Neo4j with embeddings

The problem: By the time embeddings exist, the node is already created. There's nothing to check against *before* creation because the new node's embedding doesn't exist yet.

**Q: Would embedding first offer significant value at builder stage? How long would embedding first delay Builder run?**

**Timing estimate:**
- Current Builder latency: ~2-3 seconds per chunk
- Embedding generation: ~100-200ms per entity (Google API call)
- Pre-check similarity query: ~50ms per entity

For a typical chunk extracting 3-5 entities:
- Additional latency: 300-1000ms (15-30% increase)

**Value assessment:**

| Scenario | Benefit | Cost |
|----------|---------|------|
| Many duplicate entities | Fewer GHOST nodes, less Gardener work | +300-1000ms per chunk |
| Few duplicates (common) | Minimal benefit | Same latency cost |
| High-velocity chunks | Latency compounds | Could bottleneck pipeline |

**My recommendation:** The current approach (Gardener cleans up) is acceptable for MVP. The Gardener already handles deduplication well via the merge action. Adding pre-check would:
- Add complexity to Builder
- Add latency to every chunk (even when no duplicates)
- Require entity extraction before embedding (needs partial LLM call or regex)

Document as ADR and revisit if duplicate GHOST nodes become problematic in practice.

---

**Q: No relationship/edge context seems like an oversight. We should amend.**

Agreed. Currently Builder only sees:
```
## EXISTING NODES
- concept: transformer, attention, neural network
- organisation: openai, google
```

It should also see:
```
## EXISTING RELATIONSHIPS
- "transformer" -> "attention" [STRUCTURAL] "core mechanism"
- "openai" -> "gpt-4" [STRUCTURAL] "developed by"
```

**Benefits:**
1. Builder can create more informed relationships
2. Avoids creating redundant relationships
3. Better understanding of entity roles (is "attention" a technique or a concept?)

**Implementation:** Add relationship summary to `_render_prompt()` in `builder.py`. Low effort, medium value.

---

### Gardener Agent Questions

**Q: Is checkpoint a timestamp or time since last checkpoint? Does this enable curating text for proofreading if implemented?**

**Checkpoint stores a chunk ID**, not a timestamp (though it also records `last_run` timestamp for diagnostics):

```python
class ProofreadCheckpoint:
    session_id: str
    last_chunk_id: str      # "chunk_abc123" - ID of last processed chunk
    last_run: datetime      # When checkpoint was updated
    chunks_processed: int   # Running count
```

**How it enables curated proofreading:**

```python
# Query: Get chunks AFTER the checkpoint
query = """
MATCH (c:TranscriptChunk {session_id: $session_id})
WHERE c.start_time > (
    MATCH (prev:TranscriptChunk {id: $last_chunk_id})
    RETURN prev.start_time
)
RETURN c ORDER BY c.start_time LIMIT 10
"""
```

This returns exactly the 10 chunks that haven't been proofread yet. Gardener processes only these, then updates checkpoint.

**Q: Chunk processing tracking need implemented.**

Agreed. The `chunks_processed` field exists but isn't incremented. We need to:
1. Call `update_proofread_checkpoint()` after each Gardener cycle
2. Track which chunks were processed
3. Optionally expose via API for debugging

---

### API Endpoints

**Rate Limiting Implications (expanded):**

Without rate limiting, the following attack vectors exist:
- **Cost attack:** Malicious client submits 1000 chunks/minute, exhausts Gemini API quota (costs money, breaks system)
- **Resource exhaustion:** Flood of chunks overwhelms Neo4j write capacity
- **Memory pressure:** Each chunk spawns background tasks that consume memory
- **Cascading failure:** Redis streams fill with events, Gardener falls behind, system degrades

**Pagination Implications (expanded):**

Current behaviour with 10,000 nodes:
- `GET /sessions/{id}/nodes` returns ~2MB JSON response
- Frontend must parse and hold entire response in memory
- Network transfer takes seconds
- UI may freeze during processing
- No way to progressively render

---

### Data Models

**3.1 original_text - Benefits of exposing:**

Currently we're doing the hard work (storing in Neo4j) but not reaping benefits. Exposing enables:

| Feature | Benefit |
|---------|---------|
| **Before/after UI** | Show users what was corrected |
| **Export both versions** | Complete audit trail in exports |
| **Correction quality analysis** | Measure how much STT output changes |
| **Rollback capability** | Restore original if correction was wrong |
| **STT error pattern analysis** | Identify common STT failure modes |
| **Confidence building** | Users can verify corrections are sensible |

**3.2 Session status - Robustness implications:**

**Current robustness assessment:**

| Aspect | Robustness | Issue |
|--------|------------|-------|
| Starting sessions | Good | Simple create |
| Ending sessions | Good | Sets `ended_at` |
| Detecting ended | Fragile | Requires null check on every access |
| Cleaning up ended | Fragile | SSE connections not explicitly closed |
| Preventing zombie sessions | None | No mechanism to detect abandoned sessions |
| Archiving | None | Cannot hide without deleting |

**Functional threats from fragile session management:**

1. **Gardener processing ended sessions:** If `ended_at` check is missed anywhere, Gardener might process an ended session, wasting resources
2. **Memory leaks:** SSE connections for ended sessions might persist, consuming server memory
3. **UI confusion:** Users see ended sessions mixed with active without clear distinction
4. **Data corruption risk:** Without clear states, concurrent modifications could corrupt session data
5. **No graceful degradation:** No way to mark a session as "errored" if something fails mid-processing

**Recommendation:** Promote to MEDIUM-HIGH priority. Explicit status enum makes session lifecycle crystal clear throughout codebase.

---

**3.4 ProofreadCheckpoint - Session context persistence:**

You raise an excellent point. When Gardener only sees chunks 41-50, it loses context from chunks 1-40.

**Solution: SessionContext store** (separate from SessionVocabulary)

```python
class SessionContext(BaseModel):
    session_id: str
    theme_summary: str           # "Enterprise Ireland on EDIH network"
    key_entities: list[str]      # ["Enterprise Ireland", "EDIH", "digital innovation"]
    speaker_names: list[str]     # For name recognition
    domain_terms: list[str]      # Technical vocabulary specific to session
    language_register: str       # "formal", "technical", "casual"
    updated_at: datetime
```

**How it would work:**

1. **First Gardener cycle:** Extract theme from first 10 chunks, persist SessionContext
2. **Subsequent cycles:** Load SessionContext into Gardener prompt
3. **Gardener prompt includes:**
   ```
   ## SESSION CONTEXT
   Theme: Enterprise Ireland presentation on the EDIH network
   Key entities: Enterprise Ireland, EDIH, digital innovation hubs
   Speaker: John Murphy (CEO)
   Domain: EU funding, innovation policy
   
   ## NEW CHUNKS TO PROOFREAD (41-50)
   ...
   ```

4. **Context updates:** Gardener can suggest updates to SessionContext if new key entities emerge

**Why separate from SessionVocabulary:**
- Vocabulary = corrections (phonetic -> correct)
- Context = semantic understanding (what is this session about)

They serve different purposes and should be distinct.

---

### SSE Events

**node_confirmed - Agreed.** Create distinct `NodeConfirmedEvent` rather than using generic `NodeUpdatedEvent`. Frontend can then:
- Show specific animation for confirmation
- Play audio cue
- Update UI state cleanly

**reference_added - Agreed.** Implement with Researcher agent in Phase 3.

**Documentation update - Agreed.** Will update ARCHITECTURE_ADVISORY.md to include:
- `relationship_removed`
- `flower_dissolved`
- `gardener_cycle` (heartbeat)
- `chunk_processed`

---

### Configuration

**gemini_request_timeout - Agreed.** Reduce to 90s now that thinking mode is disabled. The 180s was a workaround for the 60+ second thinking delays.

**Agent enable flags - Agreed.** Establish as architectural pattern:

```python
# Agent enable flags
builder_enabled: bool = True
gardener_enabled: bool = True
researcher_enabled: bool = True   # Phase 3
librarian_enabled: bool = True    # Phase E
```

Each agent startup checks its flag:
```python
if not settings.builder_enabled:
    logger.info("Builder disabled via config")
    return
```

This enables:
- Debugging one agent in isolation
- Graceful degradation if agent is problematic
- Feature flags for gradual rollout

---

## Summary: Ready for Implementation Planning

The document is created at `_docs/_evidence/architecture_review_2025-12-30.md`.

**Confirmed HIGH priority items:**
1. Expose `original_text` in TranscriptChunk model and API
2. Integrate ProofreadCheckpoint into Gardener
3. Add SessionContext persistence for session theme

**Additional items from discussion:**
4. Add relationship context to Builder prompt
5. Reduce `gemini_request_timeout` to 90s
6. Add agent enable flags to config
7. Update ARCHITECTURE_ADVISORY.md with undocumented SSE events

Shall I create an implementation plan for these priority items?

```plaintext
## EXISTING NODES
- concept: transformer, attention, neural network
- organisation: openai, google
```

```plaintext
## EXISTING RELATIONSHIPS
- "transformer" -> "attention" [STRUCTURAL] "core mechanism"
- "openai" -> "gpt-4" [STRUCTURAL] "developed by"
```

```python
class ProofreadCheckpoint:
    session_id: str
    last_chunk_id: str      # "chunk_abc123" - ID of last processed chunk
    last_run: datetime      # When checkpoint was updated
    chunks_processed: int   # Running count
```

```python
# Query: Get chunks AFTER the checkpoint
query = """
MATCH (c:TranscriptChunk {session_id: $session_id})
WHERE c.start_time > (
    MATCH (prev:TranscriptChunk {id: $last_chunk_id})
    RETURN prev.start_time
)
RETURN c ORDER BY c.start_time LIMIT 10
"""
```

```python
class SessionContext(BaseModel):
    session_id: str
    theme_summary: str           # "Enterprise Ireland on EDIH network"
    key_entities: list[str]      # ["Enterprise Ireland", "EDIH", "digital innovation"]
    speaker_names: list[str]     # For name recognition
    domain_terms: list[str]      # Technical vocabulary specific to session
    language_register: str       # "formal", "technical", "casual"
    updated_at: datetime
```

```plaintext
   ## SESSION CONTEXT
   Theme: Enterprise Ireland presentation on the EDIH network
   Key entities: Enterprise Ireland, EDIH, digital innovation hubs
   Speaker: John Murphy (CEO)
   Domain: EU funding, innovation policy
   
   ## NEW CHUNKS TO PROOFREAD (41-50)
   ...
```

```python
# Agent enable flags
builder_enabled: bool = True
gardener_enabled: bool = True
researcher_enabled: bool = True   # Phase 3
librarian_enabled: bool = True    # Phase E
```

```python
if not settings.builder_enabled:
    logger.info("Builder disabled via config")
    return
```

---

**User**

Can you help me understand how the vector index is being created in the context of the chunks, builder agent and general timeline? Maybe create a simple architecture diagram for this section of the app

---

**Cursor**

Let me trace through the vector index flow by examining the relevant files:

Now let me check where similarity is being called (or not) in the flow:

Interesting - `run_similarity` exists but is only used in tests, not in the actual Builder flow. Let me create the architecture diagram and explanation:

```markdown
# Vector Index Architecture: Chunks, Builder, and Embeddings

**Date:** 30 December 2025  
**Context:** Understanding how the vector index is created and used in plasticFlower

---

## Overview

The vector index enables semantic similarity search for node deduplication. This document explains how embeddings flow through the system.

---

## Architecture Diagram

```
                                 INGESTION FLOW
    ============================================================================
    
    Frontend (Browser)
           |
           | WebSpeech API produces text
           v
    +------------------+
    | POST /chunks     |  Transcript chunk submitted
    +------------------+
           |
           v
    +------------------+
    | TranscriptChunk  |  Stored in Neo4j (text, timestamps)
    | (Neo4j Node)     |
    +------------------+
           |
           v
    +------------------+
    | BuilderService   |  Orchestrates extraction
    +------------------+
           |
           +---> 1. Load existing nodes (labels only, no embeddings)
           |
           v
    +------------------+
    | Builder Agent    |  Calls Gemini LLM
    | (LLM Call)       |  Extracts entities & relationships
    +------------------+
           |
           | Returns: nodes[] and relationships[]
           v
    +------------------+
    | Embedding Gen    |  Calls Google text-embedding-004
    | (Google API)     |  768 dimensions per node label
    +------------------+
           |
           | ~100-200ms per embedding
           v
    +------------------+
    | Neo4j Persist    |  Node stored WITH embedding vector
    | (CREATE Node)    |  embedding property = float[768]
    +------------------+
           |
           v
    +------------------+
    | Vector Index     |  Automatically indexes new embedding
    | (Neo4j Native)   |  node_embedding_index
    +------------------+
    
    
                              SIMILARITY SEARCH FLOW
    ============================================================================
    
    +------------------+
    | Gardener Agent   |  During merge/dedup decision
    +------------------+
           |
           | Needs to find similar nodes
           v
    +------------------+
    | Vector Query     |  db.index.vector.queryNodes()
    | (Neo4j API)      |  Returns top-K similar nodes
    +------------------+
           |
           | Threshold: 0.92 (ADR-008)
           v
    +------------------+
    | Merge Decision   |  If score >= 0.92: same concept
    | (Gardener LLM)   |  LLM confirms/overrides
    +------------------+
```

---

## Timeline: What Happens When a Chunk Arrives

```
Time    Event                                    Duration
----    -----                                    --------
0ms     Frontend submits chunk via POST          ~10ms
        
10ms    Chunk saved to Neo4j                     ~20ms
        TranscriptChunk node created
        
30ms    BuilderService.process_chunk() starts
        
35ms    Load existing nodes from Neo4j           ~50ms
        (labels only, for LLM context)
        
85ms    Builder LLM call                         ~2000ms
        Gemini extracts entities
        
2085ms  Embedding generation begins              ~300ms
        (parallel for all extracted nodes)
        Each embedding: 100-200ms Google API
        
2385ms  Persist nodes to Neo4j                   ~100ms
        Node + embedding stored together
        Vector index auto-updates
        
2485ms  SSE broadcast: node_added events         ~10ms

2495ms  Publish to Redis (ratio-based)           ~5ms
        Triggers Gardener every 5 chunks
        
        [CHUNK PROCESSING COMPLETE]

        
        ... 4 more chunks processed ...
        

~15s    Gardener triggered (after 5 chunks)      ~10-20s
        
        Gardener loads all nodes + embeddings
        Gardener queries vector index for hints
        Gardener LLM decides: confirm/merge/prune
        
        [GARDENER CYCLE COMPLETE]
```

---

## Key Components Explained

### 1. Vector Index Creation (Startup)

**File:** `backend/app/services/graph_schema.py`

```python
CREATE VECTOR INDEX node_embedding_index IF NOT EXISTS
FOR (n:Node) ON (n.embedding)
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 768,
    `vector.similarity_function`: 'cosine'
  }
}
```

**When:** Application startup (`main.py` -> `ensure_graph_schema()`)

**What it does:** Creates a Neo4j native vector index on the `embedding` property of all `Node` labels. This index enables fast approximate nearest neighbour (ANN) search.

---

### 2. Embedding Generation

**File:** `backend/app/services/embeddings.py`

```python
async def generate_embedding(text: str) -> List[float]:
    # Calls Google text-embedding-004
    # Returns 768-dimensional vector
    response = client.models.embed_content(
        model="models/text-embedding-004",
        contents=text,
        config={'task_type': 'retrieval_document'}
    )
    return response.embeddings[0].values
```

**When:** After Builder LLM returns, before persisting nodes

**What it does:** 
1. Takes node label (e.g., "machine learning")
2. Calls Google embedding API
3. Returns 768 floats representing semantic meaning
4. Caches result (LRU cache, 512 entries)

---

### 3. Node Persistence with Embedding

**File:** `backend/app/services/builder_service.py`

```python
async def _populate_embeddings(self, nodes: List[Node]) -> None:
    tasks = [generate_embedding(node.label) for node in nodes]
    vectors = await asyncio.gather(*tasks)
    for node, vector in zip(nodes, vectors):
        node.embedding = vector  # Attached to node model

async def _persist_nodes(self, session_id: str, nodes: List[Node]) -> List[Node]:
    for node in nodes:
        await create_node(session_id, node)  # Includes embedding
```

**When:** After LLM extraction, before SSE broadcast

**What it does:**
1. Generates embeddings in parallel (async)
2. Attaches vector to each node
3. Persists node to Neo4j (embedding included)
4. Vector index automatically picks up new embedding

---

### 4. Similarity Search (Exists but NOT Used by Builder)

**File:** `backend/app/services/similarity.py`

```python
async def run_similarity(session_id: str, label: str, timestamp: float):
    embedding = await generate_embedding(label)
    candidate = await _query_best_match(session_id, embedding, top_k=5)
    
    if candidate and candidate.score >= 0.92:
        # Found existing node - increment mentions
        return SimilarityMatchResult(...)
    else:
        # No match - caller should create new node
        return SimilarityCreateResult(...)
```

**IMPORTANT:** This function exists but is **NOT called by BuilderService**.

The Builder creates all extracted nodes regardless of similarity. Deduplication happens later in the Gardener.

---

## The Gap: Pre-Create Similarity Check

### Current Flow (No Pre-Check)

```
Chunk arrives
    |
    v
Builder LLM extracts ["machine learning", "ML", "AI"]
    |
    v
Generate embeddings for ALL 3 labels
    |
    v
Create 3 GHOST nodes (even though ML and machine learning might be same concept)
    |
    v
[Later] Gardener merges duplicates
```

### Alternative Flow (With Pre-Check)

```
Chunk arrives
    |
    v
Builder LLM extracts ["machine learning", "ML", "AI"]
    |
    v
For each label:
  - Generate embedding
  - Query vector index: "Is there a similar node?"
  - If score >= 0.92: Skip (increment existing)
  - If score < 0.92: Create new node
    |
    v
Create only 1-2 GHOST nodes (duplicates caught early)
    |
    v
[Later] Gardener has less work
```

### Trade-off Analysis

| Approach | Pros | Cons |
|----------|------|------|
| Current (Gardener cleanup) | Simpler Builder, faster per-chunk | More GHOST nodes, Gardener does more work |
| Pre-check | Fewer duplicates, less Gardener work | +200-500ms latency per chunk, more complex |

**Current decision:** Keep current approach. Gardener handles deduplication well. Revisit if duplicates become problematic.

---

## Neo4j Vector Query Details

**Query used for similarity search:**

```cypher
CALL db.index.vector.queryNodes('node_embedding_index', 5, $embedding)
YIELD node, score
WHERE node.session_id = $session_id
RETURN node.id AS node_id, score
ORDER BY score DESC
LIMIT 1
```

**Parameters:**
- `index_name`: "node_embedding_index"
- `top_k`: 5 (fetch 5 candidates)
- `embedding`: 768-float vector
- `session_id`: Current session (scope to session)

**Returns:**
- `node_id`: ID of most similar node
- `score`: Cosine similarity (0.0 to 1.0)

**Threshold:** 0.92 (per ADR-008)
- Score >= 0.92: Same concept (merge/increment)
- Score < 0.92: Different concept (create new)

---

## Summary

1. **Vector index** is created at app startup (idempotent)
2. **Embeddings** are generated AFTER Builder LLM returns, before persist
3. **Nodes are stored** with their embedding attached
4. **Index auto-updates** when new nodes are created
5. **Similarity search** exists but is NOT used pre-creation
6. **Gardener uses** vector index for merge hint suggestions

The `run_similarity()` function exists for potential future use (pre-check) but the current architecture relies on Gardener for deduplication.

```

I've created a detailed architecture document at `_docs/_evidence/vector_index_architecture.md`. Here's the key insight:

---

## Vector Index Flow Summary

```
                    CURRENT ARCHITECTURE
    ====================================================
    
    1. STARTUP
       main.py → ensure_graph_schema() → CREATE VECTOR INDEX
       
    2. CHUNK ARRIVES
       POST /chunks → BuilderService starts
       
    3. BUILDER LLM (no embeddings yet)
       Load existing node LABELS → LLM extracts entities
       
    4. AFTER LLM RETURNS
       For each extracted node:
         → generate_embedding(node.label)    [Google API, ~100-200ms]
         → node.embedding = vector
         → create_node(session_id, node)     [Neo4j, includes embedding]
         → Vector index auto-updates
         
    5. GARDENER (later)
       Queries vector index for merge hints
       LLM decides: confirm/merge/prune
```

---

## Key Discovery

**The `run_similarity()` function exists but is NOT used by Builder.**

It's only called in tests. The current design:
1. Builder creates ALL extracted nodes as GHOST
2. Embeddings attached AFTER LLM extraction
3. Gardener later uses vector index to find merge candidates

This means:
- There's no pre-creation deduplication
- If LLM extracts "machine learning" and "ML" in same chunk, both become GHOST nodes
- Gardener merges them later

---

## Why This Matters

| Aspect | Current Approach | With Pre-Check |
|--------|------------------|----------------|
| GHOST node count | Higher (all extracted) | Lower (skip duplicates) |
| Gardener work | More merging | Less merging |
| Builder latency | ~2.5s | ~3s (+embedding before LLM) |
| Complexity | Simple | More orchestration |

The `run_similarity()` function was likely designed for pre-check but not integrated. This is a design decision, not a bug - the Gardener approach works, just with more intermediate nodes.

---

## Visual Timeline

```
0s        2s        4s        6s        8s       10s      ...    15s
|---------|---------|---------|---------|---------|---------|---------|
|                                                                     |
|  Chunk 1: Builder LLM → Embed → Persist                            |
|         [==========|====|==]                                        |
|                                                                     |
|           Chunk 2: Builder LLM → Embed → Persist                   |
|                   [==========|====|==]                              |
|                                                                     |
|                    ... chunks 3, 4, 5 ...                          |
|                                                                     |
|                                                    Gardener Cycle  |
|                                                    [==============]|
|                                                    (merges dupes)  |
```

The vector index exists from startup. Each node gets an embedding attached before persistence. The index auto-updates. Gardener queries it for merge hints.

Does this clarify the flow? Would you like me to explore implementing pre-creation similarity checking, or is the current Gardener-based approach acceptable?

```plaintext
                    CURRENT ARCHITECTURE
    ====================================================
    
    1. STARTUP
       main.py → ensure_graph_schema() → CREATE VECTOR INDEX
       
    2. CHUNK ARRIVES
       POST /chunks → BuilderService starts
       
    3. BUILDER LLM (no embeddings yet)
       Load existing node LABELS → LLM extracts entities
       
    4. AFTER LLM RETURNS
       For each extracted node:
         → generate_embedding(node.label)    [Google API, ~100-200ms]
         → node.embedding = vector
         → create_node(session_id, node)     [Neo4j, includes embedding]
         → Vector index auto-updates
         
    5. GARDENER (later)
       Queries vector index for merge hints
       LLM decides: confirm/merge/prune
```

```plaintext
0s        2s        4s        6s        8s       10s      ...    15s
|---------|---------|---------|---------|---------|---------|---------|
|                                                                     |
|  Chunk 1: Builder LLM → Embed → Persist                            |
|         [==========|====|==]                                        |
|                                                                     |
|           Chunk 2: Builder LLM → Embed → Persist                   |
|                   [==========|====|==]                              |
|                                                                     |
|                    ... chunks 3, 4, 5 ...                          |
|                                                                     |
|                                                    Gardener Cycle  |
|                                                    [==============]|
|                                                    (merges dupes)  |
```

---

**User**

It feels like pre-creation similarity checking has value - what are the possible implications in terms of overall app functionality, if any? I'm inclined to go ahead with it - are we considering all maximal value add with pre-creation similartiy check (anything we might have not considered yet)

---

**Cursor**

Excellent question. Let me think through this comprehensively - there are several implications we haven't fully explored yet.

---

## Pre-Creation Similarity Check: Full Implications Analysis

### What It Enables (Direct Benefits)

| Benefit | Description | Impact |
|---------|-------------|--------|
| **Fewer GHOST nodes** | Duplicates caught before creation | Cleaner graph state |
| **Accurate mention counts** | Incremented immediately, not after merge | Better real-time analytics |
| **Cleaner SSE stream** | Fewer `node_added` + later `node_merged` sequences | Smoother UI experience |
| **Reduced Gardener load** | Less merge work per cycle | Faster Gardener, lower LLM costs |
| **Relationship density** | Relationships accumulate on canonical nodes from start | Flowers form earlier |

---

### What We Haven't Fully Considered

#### 1. Relationship Rewiring at Extraction Time

**Current flow (no pre-check):**
```
LLM extracts:
  nodes: ["ML", "training data"]
  relationships: ["ML" -> "training data"]

Create node "ML" (new)
Create node "training data" (new)
Create relationship: ML.id -> training_data.id
```

**With pre-check:**
```
LLM extracts:
  nodes: ["ML", "training data"]  
  relationships: ["ML" -> "training data"]

Check "ML": matches existing "machine learning" (0.95)
  -> Skip creation, increment mentions on "machine learning"
  -> Map: "ML" label -> machine_learning.id

Check "training data": no match
  -> Create new GHOST node
  -> Map: "training data" label -> new_node.id

Create relationship: machine_learning.id -> new_node.id
```

**Implication:** We need a label-to-ID mapping that accounts for similarity matches. This is a small but important change to relationship creation logic.

---

#### 2. SSE Event Differentiation

With pre-check, we need to broadcast **different events** for matches vs creates:

| Scenario | Current SSE | With Pre-check SSE |
|----------|-------------|-------------------|
| New concept | `node_added` | `node_added` (same) |
| Duplicate detected | `node_added` then later `node_merged` | `node_updated` (mentions++) |
| Near-match (0.85-0.92) | `node_added` | `node_added` (still create) |

**Benefit:** UI shows mention count incrementing in real-time rather than showing a node appear and later disappear via merge.

---

#### 3. Confidence Accumulation

When a duplicate is detected, should we update the existing node's confidence?

```python
if match.score >= threshold:
    existing_node.mentions += 1
    existing_node.timestamps.append(chunk_timestamp)
    existing_node.confidence = max(existing_node.confidence, extracted_confidence)  # ?
```

**Consideration:** A concept mentioned multiple times with high confidence should be more trusted than one mentioned once. Pre-check enables this from the start.

---

#### 4. Context-Dependent Disambiguation

**Risk scenario:**
- Chunk 1: "Apple released the new iPhone" -> Node "Apple" (company)
- Chunk 5: "The apple fell from the tree" -> LLM extracts "apple"

Embedding similarity might be 0.93 (above threshold) because embeddings capture general semantics, not context.

**Mitigation options:**
1. **Phrase length filter**: Only check similarity for labels > 2 words
2. **Type matching**: Compare `inferred_type` as well as embedding
3. **Context window**: Include chunk context in embedding (embed "apple in context: fruit")
4. **Confidence threshold**: Require both similarity AND confidence to match

**Recommendation:** Start simple, add mitigations if false matches occur in practice.

---

#### 5. LLM Extraction Optimisation (Future)

With pre-check infrastructure, we could later tell the LLM what already exists:

**Current prompt:**
```
## EXISTING NODES
- concept: transformer, attention, neural network
```

**Enhanced prompt:**
```
## EXISTING NODES (with semantic clusters)
- concept: transformer, attention (related: self-attention, multi-head)
- framework: pytorch, tensorflow (related: keras)
```

This could reduce LLM extracting near-synonyms in the first place. Not required for initial implementation but enabled by the pre-check pattern.

---

#### 6. Performance at Scale

| Nodes in Session | Vector Query Time | Embeddings per Chunk | Added Latency |
|------------------|-------------------|---------------------|---------------|
| 10 | ~5ms | 3-5 | ~150-350ms |
| 100 | ~10ms | 3-5 | ~160-370ms |
| 500 | ~20ms | 3-5 | ~180-400ms |
| 1000+ | ~30ms | 3-5 | ~200-450ms |

**Neo4j vector index uses HNSW** (Hierarchical Navigable Small World) - O(log n) query time. Scales well.

**Optimisation opportunity:** Batch the similarity queries instead of sequential:
```python
# Instead of:
for label in extracted_labels:
    result = await run_similarity(label)

# Do:
embeddings = await asyncio.gather(*[generate_embedding(l) for l in extracted_labels])
matches = await batch_similarity_query(session_id, embeddings)
```

---

#### 7. Failure Mode Consideration

**What if similarity service fails mid-extraction?**

Current: All nodes created, Gardener handles later
With pre-check: Need graceful fallback

```python
try:
    result = await run_similarity(session_id, label, timestamp)
    if isinstance(result, SimilarityMatchResult):
        # Match found - use existing
    else:
        # Create new
except EmbeddingError:
    # Fallback: create node anyway, let Gardener handle
    logger.warning("similarity_check_failed label=%s, creating anyway", label)
```

---

### Maximum Value-Add Summary

| Feature | Enabled by Pre-Check | Notes |
|---------|---------------------|-------|
| Real-time deduplication | Yes | Core benefit |
| Accurate mention counts | Yes | Core benefit |
| Cleaner UI experience | Yes | Core benefit |
| Relationship concentration | Yes | Core benefit |
| Reduced Gardener work | Yes | Core benefit |
| Confidence accumulation | Yes | Small addition |
| Type-aware matching | Possible | Enhancement |
| LLM prompt optimization | Future | Enabled by infrastructure |
| Batch similarity queries | Possible | Performance optimization |

---

### Recommendation

**Yes, implement pre-creation similarity checking.** The value is significant:

1. **User-facing:** Cleaner UI, accurate counts, smoother experience
2. **System:** Less Gardener work, lower LLM costs, better relationship density
3. **Foundation:** Enables future optimizations (LLM hint passing, batch queries)

**Implementation scope (S-M):**
1. Call `run_similarity()` before node creation (function already exists)
2. Build label-to-ID mapping accounting for matches
3. Update relationship creation to use mapping
4. Broadcast `node_updated` for matches instead of `node_added`
5. Add fallback for embedding failures

**Estimated effort:** 2-3 hours

Shall I add this to the priority implementation plan and draft the changes?

```plaintext
LLM extracts:
  nodes: ["ML", "training data"]
  relationships: ["ML" -> "training data"]

Create node "ML" (new)
Create node "training data" (new)
Create relationship: ML.id -> training_data.id
```

```plaintext
LLM extracts:
  nodes: ["ML", "training data"]  
  relationships: ["ML" -> "training data"]

Check "ML": matches existing "machine learning" (0.95)
  -> Skip creation, increment mentions on "machine learning"
  -> Map: "ML" label -> machine_learning.id

Check "training data": no match
  -> Create new GHOST node
  -> Map: "training data" label -> new_node.id

Create relationship: machine_learning.id -> new_node.id
```

```python
if match.score >= threshold:
    existing_node.mentions += 1
    existing_node.timestamps.append(chunk_timestamp)
    existing_node.confidence = max(existing_node.confidence, extracted_confidence)  # ?
```

```plaintext
## EXISTING NODES
- concept: transformer, attention, neural network
```

```plaintext
## EXISTING NODES (with semantic clusters)
- concept: transformer, attention (related: self-attention, multi-head)
- framework: pytorch, tensorflow (related: keras)
```

```python
# Instead of:
for label in extracted_labels:
    result = await run_similarity(label)

# Do:
embeddings = await asyncio.gather(*[generate_embedding(l) for l in extracted_labels])
matches = await batch_similarity_query(session_id, embeddings)
```

```python
try:
    result = await run_similarity(session_id, label, timestamp)
    if isinstance(result, SimilarityMatchResult):
        # Match found - use existing
    else:
        # Create new
except EmbeddingError:
    # Fallback: create node anyway, let Gardener handle
    logger.warning("similarity_check_failed label=%s, creating anyway", label)
```

---

**User**

I think as long as we are tracking occurance (including confidence accumulation), then pre-check makes sense to me. Agree with disambiguation mitigation ideas - I think we will need to have at least 1 or 2 from first implementation. Make sure to document this in review. 5. LLM extraction Optimisation - this is an excellent suggestion. 

This is excellent work - update documentation report with all details discussed, and update Architecture Advisory document@_docs/ARCHITECTURE_ADVISORY.md  to reflect new architecture and advice (this is project canonical record). Then create a new document that focuses only on our agreed recommendations for immediate attention for updating the current project

---

**Cursor**

I'll update all three documents systematically.

```markdown
# Architecture Review: Codebase vs ARCHITECTURE_ADVISORY.md

**Date:** 30 December 2025  
**Session:** Architecture alignment review and gap analysis  
**Reviewers:** User + LLM Assistant  
**Scope:** Full codebase comparison against ARCHITECTURE_ADVISORY.md v8.1

---

## Executive Summary

This document captures a comprehensive review of the plasticFlower codebase against the architectural specification. The review identified several gaps, implementation concerns, and priority actions for alignment.

**Key Findings:**
- Builder and Gardener agents are well-implemented with minor gaps
- Phase D.5 (Redis Streams) is complete and robust
- Several data model fields exist in spec but not exposed in application layer
- ProofreadCheckpoint infrastructure exists but is not utilised
- Phase E (Librarian/Q&A) and Phase 3 (Researcher) are not started

---

## 1. Agent Architecture Review

### 1.1 Builder Agent

**Files reviewed:** `backend/app/agents/builder.py`, `backend/app/services/builder_service.py`

#### Strengths
- Clean separation: `builder.py` (LLM logic) vs `builder_service.py` (orchestration)
- Retry logic for parse errors (2 attempts)
- Ratio-based Gardener triggering prevents API over-calling
- Existing node deduplication in prompt context

#### Concerns

| Issue | Description | Implications | Recommended Fix |
|-------|-------------|--------------|-----------------|
| **No pre-create similarity check** | Builder creates nodes without checking vector similarity first. Architecture specifies "Check similarity against existing nodes (threshold: 0.92)" but this happens post-hoc in Gardener | More GHOST nodes created than necessary; Gardener has more cleanup work; higher LLM costs for merge decisions | Evaluate embedding-first approach (see analysis below) |
| **Embedding after LLM** | Embeddings generated after Builder LLM returns, so Builder can't use similarity to decide whether to create a node | Builder cannot make informed deduplication decisions; relies entirely on Gardener | Same as above |
| **No relationship context in prompt** | Builder only sees existing node labels, not relationships. Misses context about node roles and connections | May create nodes that would be better understood in relationship context; e.g., "Enterprise Ireland" without knowing it's already connected to "EDIH" | Add relationship summary to Builder prompt |

#### Embedding-First Analysis

**Current flow:**
```
1. Receive chunk
2. Load existing node labels (for prompt)
3. Call LLM -> extract nodes
4. Generate embeddings for new nodes
5. Persist to Neo4j
```

**Proposed flow with pre-check:**
```
1. Receive chunk
2. Load existing nodes + embeddings
3. For each extracted entity mention in chunk:
   a. Generate embedding
   b. Check similarity against existing
   c. If match > 0.92: skip (existing node)
4. Call LLM with remaining entities only
5. Persist new nodes
```

**Trade-offs:**

| Aspect | Current | With Pre-check |
|--------|---------|----------------|
| Latency | ~2-3s per chunk | +200-500ms for embeddings |
| LLM tokens | Full extraction every time | Potentially fewer (skip known entities) |
| Accuracy | Gardener cleans up | Earlier deduplication |
| Complexity | Simple | More complex orchestration |

#### Decision: Implement Pre-Creation Similarity Check

**Status:** APPROVED for implementation

After detailed analysis, pre-creation similarity checking provides significant value:

**Direct Benefits:**
1. **Fewer GHOST nodes** - Duplicates caught before creation
2. **Accurate mention counts** - Incremented immediately, not after merge
3. **Cleaner SSE stream** - Fewer `node_added` + later `node_merged` sequences
4. **Reduced Gardener load** - Less merge work per cycle
5. **Relationship density** - Relationships accumulate on canonical nodes from start
6. **Confidence accumulation** - Matched nodes gain confidence from repeated mentions

**Implementation Details:**

```
REVISED BUILDER FLOW:
1. Receive chunk
2. Load existing nodes (labels for LLM context)
3. Call LLM -> extract nodes and relationships
4. For each extracted node:
   a. Generate embedding
   b. Query vector index for similarity match
   c. If score >= 0.92: 
      - Skip creation
      - Increment mentions on existing node
      - Map: extracted_label -> existing_node.id
   d. If score < 0.92:
      - Create new GHOST node
      - Map: extracted_label -> new_node.id
5. Create relationships using label-to-ID mapping
6. Persist to Neo4j
7. SSE broadcast:
   - node_added for new nodes
   - node_updated for matched nodes (mentions incremented)
```

**Relationship Rewiring:**
When a duplicate is detected, relationships extracted by the LLM must be rewired:
- LLM extracts: "ML" -> "training data"
- "ML" matches existing "machine learning"
- Create relationship: machine_learning.id -> training_data.id

**SSE Event Changes:**
| Scenario | Current SSE | With Pre-check SSE |
|----------|-------------|-------------------|
| New concept | `node_added` | `node_added` (same) |
| Duplicate detected | `node_added` then later `node_merged` | `node_updated` (mentions++) |

**Disambiguation Mitigations:**
To prevent false positive matches (e.g., "Apple" company vs "apple" fruit):

1. **Type matching (Recommended - Implement first):** Compare `inferred_type` as well as embedding score. Only match if types are compatible.

2. **Confidence threshold (Recommended - Implement first):** Require both similarity score >= 0.92 AND LLM confidence >= 0.7 to match.

3. **Phrase length filter (Future):** Only apply similarity check to labels > 2 words (skip generic terms).

4. **Context-aware embedding (Future):** Include chunk context in embedding: embed("apple in context: fruit farming").

**Fallback Behaviour:**
```python
try:
    result = await run_similarity(session_id, label, timestamp)
    if isinstance(result, SimilarityMatchResult):
        # Match found - use existing node
    else:
        # Create new GHOST node
except EmbeddingError:
    # Fallback: create node anyway, let Gardener handle
    logger.warning("similarity_check_failed label=%s, creating anyway", label)
```

**Future Enhancement: LLM Extraction Optimisation**
With pre-check infrastructure, we can later pass existing semantic clusters to the LLM:

```
## EXISTING NODES (with semantic clusters)
- concept: transformer, attention (related: self-attention, multi-head)
- framework: pytorch, tensorflow (related: keras)
```

This could reduce LLM extracting near-synonyms at the source.

**Effort Estimate:** Medium (2-3 hours)

**Files to modify:**
- `backend/app/services/builder_service.py` - Add similarity check loop
- `backend/app/services/similarity.py` - Already exists, minor updates
- `backend/app/models/events.py` - Ensure `node_updated` event suitable
- `backend/app/config.py` - Add `similarity_check_enabled` flag

---

### 1.2 Gardener Agent

**Files reviewed:** `backend/app/agents/gardener.py`, `backend/app/services/scheduler.py`

#### Strengths
- Comprehensive prompt with proofreading, node actions, flower actions
- Language variant support built into prompt
- Vocabulary pre-application before LLM call
- Temporal decay implemented
- Redis-based event-driven triggering (ADR-009, ADR-010)

#### Concerns

| Issue | Description | Implications | Recommended Fix |
|-------|-------------|--------------|-----------------|
| **ProofreadCheckpoint not used** | Functions `get_proofread_checkpoint()` and `update_proofread_checkpoint()` exist in `graph_db.py` but Gardener never calls them | Entire transcript rescanned each cycle; wasted LLM tokens; risk of re-applying corrections; longer processing time | Integrate checkpoint into Gardener cycle |
| **No incremental chunk proofreading** | Architecture says proofread "incremental chunks (10 at a time with checkpoint)". Current implementation proofreads node labels via vocabulary, but doesn't scan chunk text incrementally | Same as above | Implement chunk-based proofreading with checkpoint |
| **No session context persistence** | When using checkpoints, Gardener may lose understanding of overall session theme (e.g., "Enterprise Ireland talk about EDIH network") | Proofreading decisions may lack context; corrections might be inconsistent with session theme | Add session context summary to Gardener prompt |

#### ProofreadCheckpoint Details

**What checkpoint stores:**
```python
class ProofreadCheckpoint(BaseModel):
    session_id: str           # Session identifier
    last_chunk_id: str        # ID of last processed TranscriptChunk
    last_run: datetime        # Timestamp of last proofread cycle
    chunks_processed: int     # Total chunks proofread in session
```

**How it enables incremental proofreading:**
1. First Gardener cycle: Process chunks 1-10, save checkpoint pointing to chunk 10
2. Second cycle: Query for chunks AFTER chunk 10, process chunks 11-20
3. Continue until caught up with live ingestion

**Session Context Solution:**
Create a `SessionContext` or extend `SessionVocabulary` to store:
```python
session_theme: str  # "Enterprise Ireland presentation on EDIH network"
key_entities: list[str]  # ["Enterprise Ireland", "EDIH", "digital innovation"]
speaker_names: list[str]  # For name recognition
```

This context would be:
1. Extracted by first Gardener cycle (or manually set)
2. Persisted in Neo4j
3. Included in every Gardener prompt for consistent understanding

---

## 2. API Endpoints Review

### 2.1 Implemented Endpoints

| Endpoint | Purpose | Status |
|----------|---------|--------|
| `POST /sessions` | Create session | Implemented |
| `GET /sessions` | List sessions | Implemented |
| `GET /sessions/{id}` | Get session detail | Implemented |
| `POST /sessions/{id}/chunks` | Submit chunk | Implemented |
| `GET /sessions/{id}/stream` | SSE stream | Implemented |
| `GET /sessions/{id}/graph` | Full graph state | Implemented |
| `GET /sessions/{id}/nodes` | List nodes | Implemented |
| `GET /sessions/{id}/relationships` | List relationships | Implemented |
| `GET /sessions/{id}/flowers` | List flowers | Implemented |
| `GET /sessions/{id}/export/*` | Export (4 formats) | Implemented |
| `POST /sessions/{id}/end` | End session | Implemented |
| `PATCH /sessions/{id}` | Rename session | Implemented |
| `DELETE /sessions/{id}` | Delete session | Implemented |

### 2.2 Missing Endpoints (Per Architecture)

| Endpoint | Purpose | Phase |
|----------|---------|-------|
| `POST /sessions/{id}/ask` | Single-session Q&A | Phase E |
| `POST /api/ask` | Cross-session Q&A | Phase 7 |
| `POST /nodes/{id}/research` | Trigger research | Phase 3 |
| `GET /sessions/{id}/timeline` | Timeline reconstruction | Future |
| `POST /sessions/{id}/correct` | Manual STT correction | Future |
| `GET /sessions/{id}/vocabulary` | Session vocabulary | Future |

### 2.3 Concerns

| Issue | Description | Implications | Recommended Fix |
|-------|-------------|--------------|-----------------|
| **No rate limiting** | No visible rate limiting on `/chunks` endpoint | Malicious or runaway clients could flood the system; API costs could spike; could exhaust LLM quota rapidly | Add rate limiting middleware for production |
| **No pagination** | `list_sessions`, `list_nodes` return all records | Memory pressure with large datasets; slow responses; potential timeouts at scale | Add `limit` and `offset` query parameters |

**Rate Limiting Implications:**
- Without limits, a single client could submit 100 chunks/second
- Each chunk triggers Builder LLM call + embedding generation
- Could exhaust Gemini API quota in minutes
- Could overwhelm Neo4j with write operations

**Pagination Implications:**
- Currently fine for MVP (< 1000 nodes per session)
- At scale (10k+ nodes), responses become unwieldy
- Frontend must load all data into memory
- No way to progressively load large graphs

---

## 3. Data Models Review

### 3.1 TranscriptChunk.original_text

**Architecture specifies:**
```python
class TranscriptChunk:
    text: str           # Chunk content (corrected)
    original_text: str  # Original STT output (for audit)
```

**Current implementation:**
- Model (`chunk.py`) does NOT have `original_text` field
- Neo4j DOES store it when corrections applied (line 1017-1024 in graph_db.py)
- `_chunk_from_value()` doesn't retrieve it
- No API exposes it

**Implications of current state:**
- Audit trail exists in database but invisible to application
- Cannot show users "before/after" of corrections
- Cannot export original uncorrected transcript
- Cannot analyse STT error patterns
- Cannot roll back corrections if needed

**Benefits of exposing:**
- Complete audit trail accessible via API
- Export can include both original and corrected text
- Debugging STT errors becomes possible
- User confidence in correction quality
- Enables "show changes" UI feature

**Fix required:**
1. Add `original_text: Optional[str] = None` to `TranscriptChunk` model
2. Update `_chunk_from_value()` to map it
3. Include in export endpoints

---

### 3.2 Session Status Enum

**Architecture specifies:**
```python
class Session:
    status: enum  # active, completed, archived
```

**Current implementation:**
Uses `ended_at: Optional[datetime]` only.

**Session Management Robustness Assessment:**

| Aspect | Current State | Risk Level |
|--------|---------------|------------|
| Detecting active sessions | Check `ended_at is None` | Low - works |
| Ending sessions | Sets `ended_at` timestamp | Low - works |
| Archiving sessions | Not possible | Medium |
| Session lifecycle states | Binary (active/ended) | Medium |
| Concurrent session limits | Not enforced | Medium |
| Orphaned sessions | No cleanup mechanism | Medium |

**What fragile session management threatens:**

1. **Resource leaks:** SSE connections for "ended" sessions might not be cleaned up properly if status isn't explicit
2. **Gardener confusion:** Gardener might process ended sessions if `ended_at` check is missed
3. **UI inconsistency:** No way to hide archived sessions without deleting them
4. **State ambiguity:** Is a session with no activity for 1 hour "ended" or "paused"?
5. **Multi-session conflicts:** No way to mark sessions as "processing" to prevent concurrent modifications

**Recommendation:** Promote to MEDIUM priority. Add status enum for robustness:
```python
class SessionStatus(str, Enum):
    ACTIVE = "active"        # Currently receiving chunks
    PAUSED = "paused"        # Temporarily stopped (future)
    COMPLETED = "completed"  # Ended normally
    ARCHIVED = "archived"    # Hidden from default views
    ERROR = "error"          # Failed processing (future)
```

---

### 3.3 SessionVocabulary

**Implementation location:** `graph_db.py` lines 860-930

**Storage mechanism:**
- Persisted as Neo4j node `(:SessionVocabulary)`
- Corrections stored as JSON string (Neo4j limitation)
- Merge semantics (new corrections add to existing)

**Current capabilities:**
- Per-session isolation
- Language variant stored
- Additive merge behaviour
- Confidence threshold (> 0.8 to save)

**Missing capabilities:**
- `preferred_spellings` field not stored (model has it, Neo4j doesn't)
- No deletion of corrections
- No API endpoint for inspection/management

**Recommendations:**
1. Add `preferred_spellings_json` column for en-GB/en-US normalisation
2. Add deletion capability for incorrect corrections
3. Consider API endpoint for vocabulary management

---

### 3.4 ProofreadCheckpoint

**Status:** Infrastructure exists, not utilised.

**Functions available:**
- `get_proofread_checkpoint(session_id)` - retrieves last chunk ID
- `update_proofread_checkpoint(session_id, last_chunk_id)` - saves progress

**What checkpoint tracks:**
- `last_chunk_id`: ID of last proofread chunk (not a timestamp)
- `last_run`: When checkpoint was updated
- `chunks_processed`: Running count

**Missing implementation:** Integration in `scheduler.py`

**Session Context Concern:**
When using incremental proofreading, Gardener loses visibility of earlier chunks. This could cause:
- Inconsistent corrections (different style in chunk 50 vs chunk 5)
- Missed co-references ("that system" referring to something mentioned 20 chunks ago)
- Theme drift

**Recommended solution: Session Context Store**

```python
class SessionContext(BaseModel):
    session_id: str
    theme_summary: str  # "Enterprise Ireland on EDIH network"
    key_entities: list[str]  # Important recurring entities
    speaker_names: list[str]  # For name recognition
    domain_terms: list[str]  # Technical vocabulary
    updated_at: datetime
```

This would be:
1. Generated/updated by Gardener during first few cycles
2. Persisted in Neo4j
3. Included in every Gardener prompt
4. Separate from SessionVocabulary (which is for corrections)

---

### 3.5 TranscriptCorrection

**Status:** Model exists, not persisted.

**Current flow:**
1. Gardener returns corrections
2. Applied to graph via `apply_corrections_to_graph()`
3. Broadcast via SSE
4. Added to vocabulary

**Missing:** No `TranscriptCorrection` nodes created in Neo4j

**Implications:**
- Cannot audit when specific corrections were made
- Cannot analyse correction quality over time
- Cannot show correction history to users
- Cannot roll back specific corrections

**Recommendation:** Add `save_correction()` function and call it in `_apply_corrections()`

---

### 3.6 GlobalNode

**Purpose:** Cross-session knowledge linking (Phase 7)

**Use case:**
- Session 1: Node "Neo4j" created
- Session 2: Node "neo4j" created (different case)
- GlobalNode: Links both to canonical representation

**Benefits when implemented:**
- Cross-session Q&A: "What do all speakers say about Neo4j?"
- Conference-wide trends: "Neo4j mentioned in 12 sessions"
- Semantic navigation across sessions

**Status:** Correctly deferred to Phase 7

---

## 4. Redis Streams (Event Bus) Review

**Files reviewed:** `backend/app/services/redis_streams.py`

### 4.1 Implementation Assessment

| Aspect | Implementation | Assessment |
|--------|----------------|------------|
| Stream naming | `pf:chunks:added` namespaced | Good |
| Consumer groups | `gardener` group defined | Good |
| Message acknowledgment | `ack_event()` after processing | Good |
| Error handling | Catches `ConnectionError`, `ResponseError` | Good |
| Startup flush | `flush_stale_events()` clears old messages | Good |
| Backpressure | 5-second block on empty stream | Good |

### 4.2 Concerns

| Issue | Description | Implications | Recommended Fix |
|-------|-------------|--------------|-----------------|
| **No dead letter queue** | Failed messages logged but lost | Cannot debug recurring failures; no retry mechanism for persistent errors | Add DLQ stream for failed messages |
| **No message TTL** | `maxlen=10000` caps size, not age | Old messages may persist indefinitely if not consumed; potential confusion | Acceptable for MVP; consider XTRIM by time later |
| **Single consumer name** | `gardener-worker-1` hardcoded | Cannot scale to multiple Gardener instances easily | Parameterise consumer name |
| **No exponential backoff** | Immediate retry on error | Could hammer failing service; no graceful degradation | Add exponential backoff for sustained failures |
| **Unused stream defined** | `STREAM_NODES_CREATED` defined but never published | Code confusion; suggests incomplete implementation | Either implement or remove |

### 4.3 Defined Streams

| Stream | Publisher | Consumer | Status |
|--------|-----------|----------|--------|
| `pf:chunks:added` | Builder | Gardener | Active |
| `pf:nodes:created` | (none) | (none) | Defined, unused |
| `pf:nodes:needs_research` | Gardener | Researcher | Publisher only |
| `pf:gardener:complete` | Gardener | SSE | Active |

---

## 5. SSE Events Review

### 5.1 Event Coverage

| Event | Architecture | Implemented | Notes |
|-------|--------------|-------------|-------|
| `node_added` | Yes | Yes | Via `NodeAddedEvent` |
| `node_confirmed` | Yes | Partial | Uses generic `NodeUpdatedEvent` |
| `node_corrected` | Yes | Yes | Via `NodeCorrectedEvent` |
| `node_merged` | Yes | Yes | Via `NodeMergedEvent` |
| `node_removed` | Yes | Yes | Via `NodeRemovedEvent` |
| `relationship_added` | Yes | Yes | Via `RelationshipAddedEvent` |
| `relationship_removed` | Not specified | Yes | Via `RelationshipRemovedEvent` |
| `flower_formed` | Yes | Yes | Via `FlowerCreatedEvent` |
| `flower_updated` | Yes | Yes | Via `FlowerUpdatedEvent` |
| `flower_dissolved` | Not specified | Yes | Via `FlowerDissolvedEvent` |
| `reference_added` | Yes | No | Requires Researcher agent |
| `gardener_cycle` | Not specified | Yes | Via `GardenerCycleEvent` |
| `chunk_processed` | Not specified | Yes | Via `ChunkProcessedEvent` |

### 5.2 Actions Required

| Action | Description | Priority |
|--------|-------------|----------|
| Create `NodeConfirmedEvent` | Distinct from generic update for clearer frontend handling | Low |
| Implement `reference_added` | Add when Researcher agent is built | Phase 3 |
| Document existing events | `relationship_removed`, `flower_dissolved`, `gardener_cycle`, `chunk_processed` not in ARCHITECTURE_ADVISORY.md | Medium |

---

## 6. Configuration Review

**File reviewed:** `backend/app/config.py`

### 6.1 Current Settings Assessment

| Setting | Value | Assessment |
|---------|-------|------------|
| `similarity_threshold: 0.92` | Tuned via ADR-008 | Excellent |
| `gemini_request_timeout: 180.0` | 3 minutes | **Should reduce to 90s** |
| `builder_gardener_ratio: 5` | Every 5 chunks | Good default |
| `gardener_debounce_seconds: 30` | Marked deprecated | Clean deprecation |

### 6.2 Recommendations

| Recommendation | Rationale |
|----------------|-----------|
| Reduce `gemini_request_timeout` to 90s | Thinking mode issue fixed; 180s no longer needed |
| Add `GARDENER_ENABLED: bool = True` | Allow disabling for debugging |
| Add `BUILDER_ENABLED: bool = True` | Consistent pattern |
| Add `RESEARCHER_ENABLED: bool = True` | For future agent |
| Document agent enable pattern | Architectural practice for all agents |

### 6.3 Proposed Agent Configuration Pattern

```python
# Agent enable flags (allows disabling for debugging/testing)
builder_enabled: bool = Field(True, description="Enable Builder agent processing")
gardener_enabled: bool = Field(True, description="Enable Gardener scheduling")
researcher_enabled: bool = Field(True, description="Enable Researcher agent (Phase 3)")
librarian_enabled: bool = Field(True, description="Enable Librarian Q&A (Phase E)")
```

---

## 7. Phase Completion Summary

| Phase | Description | Status | Notes |
|-------|-------------|--------|-------|
| Phase 1 | Infrastructure | Complete | Docker, Neo4j, Redis, Vector Index |
| Phase 2 | Gardener Enhancement | **Partial** | ProofreadCheckpoint not integrated |
| Phase 3 | Researcher Agent | Not started | - |
| Phase 4 | Librarian Agent | Not started | Next priority |
| Phase 5 | Export & Summary | Complete | 4 formats implemented |
| Phase 6 | GDS Algorithms | Deferred | Intentionally - scale feature |
| Phase 7 | Multi-Session | Not started | Future |

---

## 8. Priority Actions

### 8.1 HIGH Priority

| Item | Description | Effort | Impact |
|------|-------------|--------|--------|
| Expose `original_text` | Add to model, retrieval, and API | Small | Enables audit trail |
| Integrate ProofreadCheckpoint | Connect existing functions to Gardener | Medium | Efficiency, cost reduction |
| Add session context persistence | Store theme/entities for Gardener context | Medium | Quality of proofreading |

### 8.2 MEDIUM Priority

| Item | Description | Effort | Impact |
|------|-------------|--------|--------|
| Add `preferred_spellings` storage | Extend SessionVocabulary | Small | Language variant support |
| Persist TranscriptCorrection | Add audit trail | Small | Debugging, rollback |
| Add Session status enum | Lifecycle management | Small | Robustness |
| Add relationship context to Builder | Include edges in prompt | Small | Better extraction |
| Update SSE event types | Create specific confirmation event | Small | Cleaner frontend |
| Reduce timeout to 90s | Config change | Tiny | Resource efficiency |
| Add agent enable flags | Config pattern | Small | Debugging capability |
| Document undocumented SSE events | Update ARCHITECTURE_ADVISORY.md | Small | Clarity |

### 8.3 LOW Priority (Future)

| Item | Description | Phase |
|------|-------------|-------|
| Add rate limiting | Production hardening | Pre-production |
| Add pagination | Scale handling | When needed |
| Dead letter queue | Redis robustness | Production |
| Embedding-first deduplication | Optimisation | If duplicates problematic |

---

## 9. Next Steps

1. Implement HIGH priority items
2. Begin Phase E (Librarian/Q&A) planning
3. Update ARCHITECTURE_ADVISORY.md with discoveries
4. Create ADRs for new decisions

---

## Appendix A: Files Reviewed

- `backend/app/agents/builder.py`
- `backend/app/agents/gardener.py`
- `backend/app/services/builder_service.py`
- `backend/app/services/scheduler.py`
- `backend/app/services/graph_db.py`
- `backend/app/services/redis_streams.py`
- `backend/app/models/chunk.py`
- `backend/app/models/session.py`
- `backend/app/models/vocabulary.py`
- `backend/app/models/node.py`
- `backend/app/api/chunks.py`
- `backend/app/api/sessions.py`
- `backend/app/api/graph.py`
- `backend/app/api/export.py`
- `backend/app/config.py`
- `_docs/ARCHITECTURE_ADVISORY.md`
- `_docs/_START_SESSION_STATE.md`


```

```markdown
# Architecture Review: Codebase vs ARCHITECTURE_ADVISORY.md

**Date:** 30 December 2025  
**Session:** Architecture alignment review and gap analysis  
**Reviewers:** User + LLM Assistant  
**Scope:** Full codebase comparison against ARCHITECTURE_ADVISORY.md v8.1

---

## Executive Summary

This document captures a comprehensive review of the plasticFlower codebase against the architectural specification. The review identified several gaps, implementation concerns, and priority actions for alignment.

**Key Findings:**
- Builder and Gardener agents are well-implemented with minor gaps
- Phase D.5 (Redis Streams) is complete and robust
- Several data model fields exist in spec but not exposed in application layer
- ProofreadCheckpoint infrastructure exists but is not utilised
- Phase E (Librarian/Q&A) and Phase 3 (Researcher) are not started

---

## 1. Agent Architecture Review

### 1.1 Builder Agent

**Files reviewed:** `backend/app/agents/builder.py`, `backend/app/services/builder_service.py`

#### Strengths
- Clean separation: `builder.py` (LLM logic) vs `builder_service.py` (orchestration)
- Retry logic for parse errors (2 attempts)
- Ratio-based Gardener triggering prevents API over-calling
- Existing node deduplication in prompt context

#### Concerns

| Issue | Description | Implications | Recommended Fix |
|-------|-------------|--------------|-----------------|
| **No pre-create similarity check** | Builder creates nodes without checking vector similarity first. Architecture specifies "Check similarity against existing nodes (threshold: 0.92)" but this happens post-hoc in Gardener | More GHOST nodes created than necessary; Gardener has more cleanup work; higher LLM costs for merge decisions | Evaluate embedding-first approach (see analysis below) |
| **Embedding after LLM** | Embeddings generated after Builder LLM returns, so Builder can't use similarity to decide whether to create a node | Builder cannot make informed deduplication decisions; relies entirely on Gardener | Same as above |
| **No relationship context in prompt** | Builder only sees existing node labels, not relationships. Misses context about node roles and connections | May create nodes that would be better understood in relationship context; e.g., "Enterprise Ireland" without knowing it's already connected to "EDIH" | Add relationship summary to Builder prompt |

#### Embedding-First Analysis

**Current flow:**
```
1. Receive chunk
2. Load existing node labels (for prompt)
3. Call LLM -> extract nodes
4. Generate embeddings for new nodes
5. Persist to Neo4j
```

**Proposed flow with pre-check:**
```
1. Receive chunk
2. Load existing nodes + embeddings
3. For each extracted entity mention in chunk:
   a. Generate embedding
   b. Check similarity against existing
   c. If match > 0.92: skip (existing node)
4. Call LLM with remaining entities only
5. Persist new nodes
```

**Trade-offs:**

| Aspect | Current | With Pre-check |
|--------|---------|----------------|
| Latency | ~2-3s per chunk | +200-500ms for embeddings |
| LLM tokens | Full extraction every time | Potentially fewer (skip known entities) |
| Accuracy | Gardener cleans up | Earlier deduplication |
| Complexity | Simple | More complex orchestration |

#### Decision: Implement Pre-Creation Similarity Check

**Status:** APPROVED for implementation

After detailed analysis, pre-creation similarity checking provides significant value:

**Direct Benefits:**
1. **Fewer GHOST nodes** - Duplicates caught before creation
2. **Accurate mention counts** - Incremented immediately, not after merge
3. **Cleaner SSE stream** - Fewer `node_added` + later `node_merged` sequences
4. **Reduced Gardener load** - Less merge work per cycle
5. **Relationship density** - Relationships accumulate on canonical nodes from start
6. **Confidence accumulation** - Matched nodes gain confidence from repeated mentions

**Implementation Details:**

```
REVISED BUILDER FLOW:
1. Receive chunk
2. Load existing nodes (labels for LLM context)
3. Call LLM -> extract nodes and relationships
4. For each extracted node:
   a. Generate embedding
   b. Query vector index for similarity match
   c. If score >= 0.92: 
      - Skip creation
      - Increment mentions on existing node
      - Map: extracted_label -> existing_node.id
   d. If score < 0.92:
      - Create new GHOST node
      - Map: extracted_label -> new_node.id
5. Create relationships using label-to-ID mapping
6. Persist to Neo4j
7. SSE broadcast:
   - node_added for new nodes
   - node_updated for matched nodes (mentions incremented)
```

**Relationship Rewiring:**
When a duplicate is detected, relationships extracted by the LLM must be rewired:
- LLM extracts: "ML" -> "training data"
- "ML" matches existing "machine learning"
- Create relationship: machine_learning.id -> training_data.id

**SSE Event Changes:**
| Scenario | Current SSE | With Pre-check SSE |
|----------|-------------|-------------------|
| New concept | `node_added` | `node_added` (same) |
| Duplicate detected | `node_added` then later `node_merged` | `node_updated` (mentions++) |

**Disambiguation Mitigations:**
To prevent false positive matches (e.g., "Apple" company vs "apple" fruit):

1. **Type matching (Recommended - Implement first):** Compare `inferred_type` as well as embedding score. Only match if types are compatible.

2. **Confidence threshold (Recommended - Implement first):** Require both similarity score >= 0.92 AND LLM confidence >= 0.7 to match.

3. **Phrase length filter (Future):** Only apply similarity check to labels > 2 words (skip generic terms).

4. **Context-aware embedding (Future):** Include chunk context in embedding: embed("apple in context: fruit farming").

**Fallback Behaviour:**
```python
try:
    result = await run_similarity(session_id, label, timestamp)
    if isinstance(result, SimilarityMatchResult):
        # Match found - use existing node
    else:
        # Create new GHOST node
except EmbeddingError:
    # Fallback: create node anyway, let Gardener handle
    logger.warning("similarity_check_failed label=%s, creating anyway", label)
```

**Future Enhancement: LLM Extraction Optimisation**
With pre-check infrastructure, we can later pass existing semantic clusters to the LLM:

```
## EXISTING NODES (with semantic clusters)
- concept: transformer, attention (related: self-attention, multi-head)
- framework: pytorch, tensorflow (related: keras)
```

This could reduce LLM extracting near-synonyms at the source.

**Effort Estimate:** Medium (2-3 hours)

**Files to modify:**
- `backend/app/services/builder_service.py` - Add similarity check loop
- `backend/app/services/similarity.py` - Already exists, minor updates
- `backend/app/models/events.py` - Ensure `node_updated` event suitable
- `backend/app/config.py` - Add `similarity_check_enabled` flag

---

### 1.2 Gardener Agent

**Files reviewed:** `backend/app/agents/gardener.py`, `backend/app/services/scheduler.py`

#### Strengths
- Comprehensive prompt with proofreading, node actions, flower actions
- Language variant support built into prompt
- Vocabulary pre-application before LLM call
- Temporal decay implemented
- Redis-based event-driven triggering (ADR-009, ADR-010)

#### Concerns

| Issue | Description | Implications | Recommended Fix |
|-------|-------------|--------------|-----------------|
| **ProofreadCheckpoint not used** | Functions `get_proofread_checkpoint()` and `update_proofread_checkpoint()` exist in `graph_db.py` but Gardener never calls them | Entire transcript rescanned each cycle; wasted LLM tokens; risk of re-applying corrections; longer processing time | Integrate checkpoint into Gardener cycle |
| **No incremental chunk proofreading** | Architecture says proofread "incremental chunks (10 at a time with checkpoint)". Current implementation proofreads node labels via vocabulary, but doesn't scan chunk text incrementally | Same as above | Implement chunk-based proofreading with checkpoint |
| **No session context persistence** | When using checkpoints, Gardener may lose understanding of overall session theme (e.g., "Enterprise Ireland talk about EDIH network") | Proofreading decisions may lack context; corrections might be inconsistent with session theme | Add session context summary to Gardener prompt |

#### ProofreadCheckpoint Details

**What checkpoint stores:**
```python
class ProofreadCheckpoint(BaseModel):
    session_id: str           # Session identifier
    last_chunk_id: str        # ID of last processed TranscriptChunk
    last_run: datetime        # Timestamp of last proofread cycle
    chunks_processed: int     # Total chunks proofread in session
```

**How it enables incremental proofreading:**
1. First Gardener cycle: Process chunks 1-10, save checkpoint pointing to chunk 10
2. Second cycle: Query for chunks AFTER chunk 10, process chunks 11-20
3. Continue until caught up with live ingestion

**Session Context Solution:**
Create a `SessionContext` or extend `SessionVocabulary` to store:
```python
session_theme: str  # "Enterprise Ireland presentation on EDIH network"
key_entities: list[str]  # ["Enterprise Ireland", "EDIH", "digital innovation"]
speaker_names: list[str]  # For name recognition
```

This context would be:
1. Extracted by first Gardener cycle (or manually set)
2. Persisted in Neo4j
3. Included in every Gardener prompt for consistent understanding

---

## 2. API Endpoints Review

### 2.1 Implemented Endpoints

| Endpoint | Purpose | Status |
|----------|---------|--------|
| `POST /sessions` | Create session | Implemented |
| `GET /sessions` | List sessions | Implemented |
| `GET /sessions/{id}` | Get session detail | Implemented |
| `POST /sessions/{id}/chunks` | Submit chunk | Implemented |
| `GET /sessions/{id}/stream` | SSE stream | Implemented |
| `GET /sessions/{id}/graph` | Full graph state | Implemented |
| `GET /sessions/{id}/nodes` | List nodes | Implemented |
| `GET /sessions/{id}/relationships` | List relationships | Implemented |
| `GET /sessions/{id}/flowers` | List flowers | Implemented |
| `GET /sessions/{id}/export/*` | Export (4 formats) | Implemented |
| `POST /sessions/{id}/end` | End session | Implemented |
| `PATCH /sessions/{id}` | Rename session | Implemented |
| `DELETE /sessions/{id}` | Delete session | Implemented |

### 2.2 Missing Endpoints (Per Architecture)

| Endpoint | Purpose | Phase |
|----------|---------|-------|
| `POST /sessions/{id}/ask` | Single-session Q&A | Phase E |
| `POST /api/ask` | Cross-session Q&A | Phase 7 |
| `POST /nodes/{id}/research` | Trigger research | Phase 3 |
| `GET /sessions/{id}/timeline` | Timeline reconstruction | Future |
| `POST /sessions/{id}/correct` | Manual STT correction | Future |
| `GET /sessions/{id}/vocabulary` | Session vocabulary | Future |

### 2.3 Concerns

| Issue | Description | Implications | Recommended Fix |
|-------|-------------|--------------|-----------------|
| **No rate limiting** | No visible rate limiting on `/chunks` endpoint | Malicious or runaway clients could flood the system; API costs could spike; could exhaust LLM quota rapidly | Add rate limiting middleware for production |
| **No pagination** | `list_sessions`, `list_nodes` return all records | Memory pressure with large datasets; slow responses; potential timeouts at scale | Add `limit` and `offset` query parameters |

**Rate Limiting Implications:**
- Without limits, a single client could submit 100 chunks/second
- Each chunk triggers Builder LLM call + embedding generation
- Could exhaust Gemini API quota in minutes
- Could overwhelm Neo4j with write operations

**Pagination Implications:**
- Currently fine for MVP (< 1000 nodes per session)
- At scale (10k+ nodes), responses become unwieldy
- Frontend must load all data into memory
- No way to progressively load large graphs

---

## 3. Data Models Review

### 3.1 TranscriptChunk.original_text

**Architecture specifies:**
```python
class TranscriptChunk:
    text: str           # Chunk content (corrected)
    original_text: str  # Original STT output (for audit)
```

**Current implementation:**
- Model (`chunk.py`) does NOT have `original_text` field
- Neo4j DOES store it when corrections applied (line 1017-1024 in graph_db.py)
- `_chunk_from_value()` doesn't retrieve it
- No API exposes it

**Implications of current state:**
- Audit trail exists in database but invisible to application
- Cannot show users "before/after" of corrections
- Cannot export original uncorrected transcript
- Cannot analyse STT error patterns
- Cannot roll back corrections if needed

**Benefits of exposing:**
- Complete audit trail accessible via API
- Export can include both original and corrected text
- Debugging STT errors becomes possible
- User confidence in correction quality
- Enables "show changes" UI feature

**Fix required:**
1. Add `original_text: Optional[str] = None` to `TranscriptChunk` model
2. Update `_chunk_from_value()` to map it
3. Include in export endpoints

---

### 3.2 Session Status Enum

**Architecture specifies:**
```python
class Session:
    status: enum  # active, completed, archived
```

**Current implementation:**
Uses `ended_at: Optional[datetime]` only.

**Session Management Robustness Assessment:**

| Aspect | Current State | Risk Level |
|--------|---------------|------------|
| Detecting active sessions | Check `ended_at is None` | Low - works |
| Ending sessions | Sets `ended_at` timestamp | Low - works |
| Archiving sessions | Not possible | Medium |
| Session lifecycle states | Binary (active/ended) | Medium |
| Concurrent session limits | Not enforced | Medium |
| Orphaned sessions | No cleanup mechanism | Medium |

**What fragile session management threatens:**

1. **Resource leaks:** SSE connections for "ended" sessions might not be cleaned up properly if status isn't explicit
2. **Gardener confusion:** Gardener might process ended sessions if `ended_at` check is missed
3. **UI inconsistency:** No way to hide archived sessions without deleting them
4. **State ambiguity:** Is a session with no activity for 1 hour "ended" or "paused"?
5. **Multi-session conflicts:** No way to mark sessions as "processing" to prevent concurrent modifications

**Recommendation:** Promote to MEDIUM priority. Add status enum for robustness:
```python
class SessionStatus(str, Enum):
    ACTIVE = "active"        # Currently receiving chunks
    PAUSED = "paused"        # Temporarily stopped (future)
    COMPLETED = "completed"  # Ended normally
    ARCHIVED = "archived"    # Hidden from default views
    ERROR = "error"          # Failed processing (future)
```

---

### 3.3 SessionVocabulary

**Implementation location:** `graph_db.py` lines 860-930

**Storage mechanism:**
- Persisted as Neo4j node `(:SessionVocabulary)`
- Corrections stored as JSON string (Neo4j limitation)
- Merge semantics (new corrections add to existing)

**Current capabilities:**
- Per-session isolation
- Language variant stored
- Additive merge behaviour
- Confidence threshold (> 0.8 to save)

**Missing capabilities:**
- `preferred_spellings` field not stored (model has it, Neo4j doesn't)
- No deletion of corrections
- No API endpoint for inspection/management

**Recommendations:**
1. Add `preferred_spellings_json` column for en-GB/en-US normalisation
2. Add deletion capability for incorrect corrections
3. Consider API endpoint for vocabulary management

---

### 3.4 ProofreadCheckpoint

**Status:** Infrastructure exists, not utilised.

**Functions available:**
- `get_proofread_checkpoint(session_id)` - retrieves last chunk ID
- `update_proofread_checkpoint(session_id, last_chunk_id)` - saves progress

**What checkpoint tracks:**
- `last_chunk_id`: ID of last proofread chunk (not a timestamp)
- `last_run`: When checkpoint was updated
- `chunks_processed`: Running count

**Missing implementation:** Integration in `scheduler.py`

**Session Context Concern:**
When using incremental proofreading, Gardener loses visibility of earlier chunks. This could cause:
- Inconsistent corrections (different style in chunk 50 vs chunk 5)
- Missed co-references ("that system" referring to something mentioned 20 chunks ago)
- Theme drift

**Recommended solution: Session Context Store**

```python
class SessionContext(BaseModel):
    session_id: str
    theme_summary: str  # "Enterprise Ireland on EDIH network"
    key_entities: list[str]  # Important recurring entities
    speaker_names: list[str]  # For name recognition
    domain_terms: list[str]  # Technical vocabulary
    updated_at: datetime
```

This would be:
1. Generated/updated by Gardener during first few cycles
2. Persisted in Neo4j
3. Included in every Gardener prompt
4. Separate from SessionVocabulary (which is for corrections)

---

### 3.5 TranscriptCorrection

**Status:** Model exists, not persisted.

**Current flow:**
1. Gardener returns corrections
2. Applied to graph via `apply_corrections_to_graph()`
3. Broadcast via SSE
4. Added to vocabulary

**Missing:** No `TranscriptCorrection` nodes created in Neo4j

**Implications:**
- Cannot audit when specific corrections were made
- Cannot analyse correction quality over time
- Cannot show correction history to users
- Cannot roll back specific corrections

**Recommendation:** Add `save_correction()` function and call it in `_apply_corrections()`

---

### 3.6 GlobalNode

**Purpose:** Cross-session knowledge linking (Phase 7)

**Use case:**
- Session 1: Node "Neo4j" created
- Session 2: Node "neo4j" created (different case)
- GlobalNode: Links both to canonical representation

**Benefits when implemented:**
- Cross-session Q&A: "What do all speakers say about Neo4j?"
- Conference-wide trends: "Neo4j mentioned in 12 sessions"
- Semantic navigation across sessions

**Status:** Correctly deferred to Phase 7

---

## 4. Redis Streams (Event Bus) Review

**Files reviewed:** `backend/app/services/redis_streams.py`

### 4.1 Implementation Assessment

| Aspect | Implementation | Assessment |
|--------|----------------|------------|
| Stream naming | `pf:chunks:added` namespaced | Good |
| Consumer groups | `gardener` group defined | Good |
| Message acknowledgment | `ack_event()` after processing | Good |
| Error handling | Catches `ConnectionError`, `ResponseError` | Good |
| Startup flush | `flush_stale_events()` clears old messages | Good |
| Backpressure | 5-second block on empty stream | Good |

### 4.2 Concerns

| Issue | Description | Implications | Recommended Fix |
|-------|-------------|--------------|-----------------|
| **No dead letter queue** | Failed messages logged but lost | Cannot debug recurring failures; no retry mechanism for persistent errors | Add DLQ stream for failed messages |
| **No message TTL** | `maxlen=10000` caps size, not age | Old messages may persist indefinitely if not consumed; potential confusion | Acceptable for MVP; consider XTRIM by time later |
| **Single consumer name** | `gardener-worker-1` hardcoded | Cannot scale to multiple Gardener instances easily | Parameterise consumer name |
| **No exponential backoff** | Immediate retry on error | Could hammer failing service; no graceful degradation | Add exponential backoff for sustained failures |
| **Unused stream defined** | `STREAM_NODES_CREATED` defined but never published | Code confusion; suggests incomplete implementation | Either implement or remove |

### 4.3 Defined Streams

| Stream | Publisher | Consumer | Status |
|--------|-----------|----------|--------|
| `pf:chunks:added` | Builder | Gardener | Active |
| `pf:nodes:created` | (none) | (none) | Defined, unused |
| `pf:nodes:needs_research` | Gardener | Researcher | Publisher only |
| `pf:gardener:complete` | Gardener | SSE | Active |

---

## 5. SSE Events Review

### 5.1 Event Coverage

| Event | Architecture | Implemented | Notes |
|-------|--------------|-------------|-------|
| `node_added` | Yes | Yes | Via `NodeAddedEvent` |
| `node_confirmed` | Yes | Partial | Uses generic `NodeUpdatedEvent` |
| `node_corrected` | Yes | Yes | Via `NodeCorrectedEvent` |
| `node_merged` | Yes | Yes | Via `NodeMergedEvent` |
| `node_removed` | Yes | Yes | Via `NodeRemovedEvent` |
| `relationship_added` | Yes | Yes | Via `RelationshipAddedEvent` |
| `relationship_removed` | Not specified | Yes | Via `RelationshipRemovedEvent` |
| `flower_formed` | Yes | Yes | Via `FlowerCreatedEvent` |
| `flower_updated` | Yes | Yes | Via `FlowerUpdatedEvent` |
| `flower_dissolved` | Not specified | Yes | Via `FlowerDissolvedEvent` |
| `reference_added` | Yes | No | Requires Researcher agent |
| `gardener_cycle` | Not specified | Yes | Via `GardenerCycleEvent` |
| `chunk_processed` | Not specified | Yes | Via `ChunkProcessedEvent` |

### 5.2 Actions Required

| Action | Description | Priority |
|--------|-------------|----------|
| Create `NodeConfirmedEvent` | Distinct from generic update for clearer frontend handling | Low |
| Implement `reference_added` | Add when Researcher agent is built | Phase 3 |
| Document existing events | `relationship_removed`, `flower_dissolved`, `gardener_cycle`, `chunk_processed` not in ARCHITECTURE_ADVISORY.md | Medium |

---

## 6. Configuration Review

**File reviewed:** `backend/app/config.py`

### 6.1 Current Settings Assessment

| Setting | Value | Assessment |
|---------|-------|------------|
| `similarity_threshold: 0.92` | Tuned via ADR-008 | Excellent |
| `gemini_request_timeout: 180.0` | 3 minutes | **Should reduce to 90s** |
| `builder_gardener_ratio: 5` | Every 5 chunks | Good default |
| `gardener_debounce_seconds: 30` | Marked deprecated | Clean deprecation |

### 6.2 Recommendations

| Recommendation | Rationale |
|----------------|-----------|
| Reduce `gemini_request_timeout` to 90s | Thinking mode issue fixed; 180s no longer needed |
| Add `GARDENER_ENABLED: bool = True` | Allow disabling for debugging |
| Add `BUILDER_ENABLED: bool = True` | Consistent pattern |
| Add `RESEARCHER_ENABLED: bool = True` | For future agent |
| Document agent enable pattern | Architectural practice for all agents |

### 6.3 Proposed Agent Configuration Pattern

```python
# Agent enable flags (allows disabling for debugging/testing)
builder_enabled: bool = Field(True, description="Enable Builder agent processing")
gardener_enabled: bool = Field(True, description="Enable Gardener scheduling")
researcher_enabled: bool = Field(True, description="Enable Researcher agent (Phase 3)")
librarian_enabled: bool = Field(True, description="Enable Librarian Q&A (Phase E)")
```

---

## 7. Phase Completion Summary

| Phase | Description | Status | Notes |
|-------|-------------|--------|-------|
| Phase 1 | Infrastructure | Complete | Docker, Neo4j, Redis, Vector Index |
| Phase 2 | Gardener Enhancement | **Partial** | ProofreadCheckpoint not integrated |
| Phase 3 | Researcher Agent | Not started | - |
| Phase 4 | Librarian Agent | Not started | Next priority |
| Phase 5 | Export & Summary | Complete | 4 formats implemented |
| Phase 6 | GDS Algorithms | Deferred | Intentionally - scale feature |
| Phase 7 | Multi-Session | Not started | Future |

---

## 8. Priority Actions

### 8.1 HIGH Priority

| Item | Description | Effort | Impact |
|------|-------------|--------|--------|
| **Implement pre-creation similarity check** | Add similarity check before node creation in Builder | Medium | Real-time dedup, fewer GHOST nodes, accurate counts |
| **Add disambiguation mitigations** | Type matching + confidence threshold for similarity | Small | Prevent false positive matches |
| Expose `original_text` | Add to model, retrieval, and API | Small | Enables audit trail |
| Integrate ProofreadCheckpoint | Connect existing functions to Gardener | Medium | Efficiency, cost reduction |
| Add session context persistence | Store theme/entities for Gardener context | Medium | Quality of proofreading |

### 8.2 MEDIUM Priority

| Item | Description | Effort | Impact |
|------|-------------|--------|--------|
| Add `preferred_spellings` storage | Extend SessionVocabulary | Small | Language variant support |
| Persist TranscriptCorrection | Add audit trail | Small | Debugging, rollback |
| Add Session status enum | Lifecycle management | Small | Robustness |
| Add relationship context to Builder | Include edges in prompt | Small | Better extraction |
| Update SSE event types | Create specific confirmation event | Small | Cleaner frontend |
| Reduce timeout to 90s | Config change | Tiny | Resource efficiency |
| Add agent enable flags | Config pattern | Small | Debugging capability |
| Document undocumented SSE events | Update ARCHITECTURE_ADVISORY.md | Small | Clarity |

### 8.3 LOW Priority (Future)

| Item | Description | Phase |
|------|-------------|-------|
| Add rate limiting | Production hardening | Pre-production |
| Add pagination | Scale handling | When needed |
| Dead letter queue | Redis robustness | Production |
| LLM extraction optimisation | Pass semantic clusters to LLM prompt | Future enhancement |

---

## 9. Next Steps

1. Implement HIGH priority items
2. Begin Phase E (Librarian/Q&A) planning
3. Update ARCHITECTURE_ADVISORY.md with discoveries
4. Create ADRs for new decisions

---

## Appendix A: Files Reviewed

- `backend/app/agents/builder.py`
- `backend/app/agents/gardener.py`
- `backend/app/services/builder_service.py`
- `backend/app/services/scheduler.py`
- `backend/app/services/graph_db.py`
- `backend/app/services/redis_streams.py`
- `backend/app/models/chunk.py`
- `backend/app/models/session.py`
- `backend/app/models/vocabulary.py`
- `backend/app/models/node.py`
- `backend/app/api/chunks.py`
- `backend/app/api/sessions.py`
- `backend/app/api/graph.py`
- `backend/app/api/export.py`
- `backend/app/config.py`
- `_docs/ARCHITECTURE_ADVISORY.md`
- `_docs/_START_SESSION_STATE.md`


```

Now let me update the ARCHITECTURE_ADVISORY.md with the new Builder architecture:

```markdown
# Architectural Advisory: plasticFlower

**Date:** 26 December 2025  
**Version:** 8.1 (Navigable Knowledge)  
**Context:** Complete system design incorporating GraphRAG, Research Augmentation, and STT Correction  
**Learning Guide:** [LEARNING_GUIDE.md](./LEARNING_GUIDE.md) - Structured curriculum for Neo4j and Semantic Knowledge Graphs  
**Session State:** [_START_SESSION_STATE.md](./_START_SESSION_STATE.md) - Cross-session progress tracking (attach to every coding session)  
**ADR Index:** [_dev/ADR/INDEX.md](./_dev/ADR/INDEX.md) - Architecture Decision Records (critical process)  
**Lite Version:** [LITE_ARCHITECTURE.md](./LITE_ARCHITECTURE.md) - Browser-only implementation for demos (separate project)

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

**Disambiguation Mitigations:**

To prevent false positive matches (e.g., "Apple" company vs "apple" fruit):

| Mitigation | Description | Status |
|------------|-------------|--------|
| **Type matching** | Compare `inferred_type` - only match if types are compatible | Required |
| **Confidence threshold** | Require similarity >= 0.92 AND LLM confidence >= 0.7 | Required |
| **Phrase length filter** | Skip similarity check for labels < 2 words | Future |
| **Context embedding** | Include chunk context in embedding | Future |

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
| **Trigger** | Every 60-90 seconds |
| **Model** | `gemini-2.5-pro` (reasoning priority) |
| **Context** | Full graph + Extended transcript (3000 words) |

**Tasks (Executed in Order):**

#### Task 1: Proofread (STT Correction)
- Scan incremental chunks (10 at a time with checkpoint)
- Identify phonetic STT errors (e.g., "see dare" -> "CeADAR")
- Correct transcript chunks AND node labels
- Update session vocabulary for instant future corrections
- Broadcast: `node_corrected`

#### Task 2: Confirm or Remove
- Promote valid GHOST nodes to SOLID
- Remove noise/hallucination nodes
- Broadcast: `node_confirmed`, `node_removed`

#### Task 3: Merge
- Identify duplicate/synonymous nodes
- Use embeddings (similarity > 0.92) + textual context
- Merge into canonical node, preserve mention counts
- Broadcast: `node_merged`

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
| Builder uses `MERGE` | Idempotent - won't fail if node already exists |
| Gardener uses transactions | Atomic operations prevent partial updates |
| SSE is append-only | Events stream in order, no conflicts |
| Similarity check before create | Prevents Builder creating duplicates |

### Conflict Scenarios and Solutions

| Scenario | Risk | Solution |
|----------|------|----------|
| Gardener deletes node while Builder references it | Orphaned relationship | Gardener checks node existence before delete |
| Builder creates duplicate while Gardener merging | Two nodes for same concept | Similarity threshold catches this |
| Both agents write to same node | Data inconsistency | Neo4j transaction isolation handles this |
| Correction applied mid-extraction | Label mismatch | Builder re-checks after MERGE |

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

| Event | Payload | UI Action |
|-------|---------|-----------|
| `node_added` | Node data | Render ghost node |
| `node_confirmed` | node_id | Transition to solid |
| `node_corrected` | node_id, old_label, new_label | Flash + update label |
| `node_merged` | keep_id, absorbed_ids | Animate merge |
| `node_removed` | node_id | Fade out and remove |
| `relationship_added` | Relationship data | Draw edge |
| `flower_formed` | Flower data + member_ids | Fan layout animation |
| `flower_updated` | Flower data | Update positions |
| `reference_added` | node_id, reference_data | Add icon to node |

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
| [001](/_dev/ADR/0001-llm-clustering-over-gds.md) | LLM-only clustering | 1M context fits entire session; GDS optional at scale |
| [002](/_dev/ADR/0002-proofreading-in-gardener.md) | Proofreading in Gardener | Shared context, simpler architecture |
| [003](/_dev/ADR/0003-gemini-grounding-for-research.md) | Gemini grounding for research | Simpler setup, Tavily as fallback |
| [004](/_dev/ADR/0004-full-context-qa.md) | Full context Q&A | GraphRAG unnecessary for single session |

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

```

Now let me update the Gardener section and add the new SSE events to the architecture:

```markdown
# Architectural Advisory: plasticFlower

**Date:** 26 December 2025  
**Version:** 8.1 (Navigable Knowledge)  
**Context:** Complete system design incorporating GraphRAG, Research Augmentation, and STT Correction  
**Learning Guide:** [LEARNING_GUIDE.md](./LEARNING_GUIDE.md) - Structured curriculum for Neo4j and Semantic Knowledge Graphs  
**Session State:** [_START_SESSION_STATE.md](./_START_SESSION_STATE.md) - Cross-session progress tracking (attach to every coding session)  
**ADR Index:** [_dev/ADR/INDEX.md](./_dev/ADR/INDEX.md) - Architecture Decision Records (critical process)  
**Lite Version:** [LITE_ARCHITECTURE.md](./LITE_ARCHITECTURE.md) - Browser-only implementation for demos (separate project)

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

**Disambiguation Mitigations:**

To prevent false positive matches (e.g., "Apple" company vs "apple" fruit):

| Mitigation | Description | Status |
|------------|-------------|--------|
| **Type matching** | Compare `inferred_type` - only match if types are compatible | Required |
| **Confidence threshold** | Require similarity >= 0.92 AND LLM confidence >= 0.7 | Required |
| **Phrase length filter** | Skip similarity check for labels < 2 words | Future |
| **Context embedding** | Include chunk context in embedding | Future |

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
| Builder uses `MERGE` | Idempotent - won't fail if node already exists |
| Gardener uses transactions | Atomic operations prevent partial updates |
| SSE is append-only | Events stream in order, no conflicts |
| Similarity check before create | Prevents Builder creating duplicates |

### Conflict Scenarios and Solutions

| Scenario | Risk | Solution |
|----------|------|----------|
| Gardener deletes node while Builder references it | Orphaned relationship | Gardener checks node existence before delete |
| Builder creates duplicate while Gardener merging | Two nodes for same concept | Similarity threshold catches this |
| Both agents write to same node | Data inconsistency | Neo4j transaction isolation handles this |
| Correction applied mid-extraction | Label mismatch | Builder re-checks after MERGE |

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

| Event | Payload | UI Action |
|-------|---------|-----------|
| `node_added` | Node data | Render ghost node |
| `node_confirmed` | node_id | Transition to solid |
| `node_corrected` | node_id, old_label, new_label | Flash + update label |
| `node_merged` | keep_id, absorbed_ids | Animate merge |
| `node_removed` | node_id | Fade out and remove |
| `relationship_added` | Relationship data | Draw edge |
| `flower_formed` | Flower data + member_ids | Fan layout animation |
| `flower_updated` | Flower data | Update positions |
| `reference_added` | node_id, reference_data | Add icon to node |

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
| [001](/_dev/ADR/0001-llm-clustering-over-gds.md) | LLM-only clustering | 1M context fits entire session; GDS optional at scale |
| [002](/_dev/ADR/0002-proofreading-in-gardener.md) | Proofreading in Gardener | Shared context, simpler architecture |
| [003](/_dev/ADR/0003-gemini-grounding-for-research.md) | Gemini grounding for research | Simpler setup, Tavily as fallback |
| [004](/_dev/ADR/0004-full-context-qa.md) | Full context Q&A | GraphRAG unnecessary for single session |

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

```

```markdown
# Architectural Advisory: plasticFlower

**Date:** 26 December 2025  
**Version:** 8.1 (Navigable Knowledge)  
**Context:** Complete system design incorporating GraphRAG, Research Augmentation, and STT Correction  
**Learning Guide:** [LEARNING_GUIDE.md](./LEARNING_GUIDE.md) - Structured curriculum for Neo4j and Semantic Knowledge Graphs  
**Session State:** [_START_SESSION_STATE.md](./_START_SESSION_STATE.md) - Cross-session progress tracking (attach to every coding session)  
**ADR Index:** [_dev/ADR/INDEX.md](./_dev/ADR/INDEX.md) - Architecture Decision Records (critical process)  
**Lite Version:** [LITE_ARCHITECTURE.md](./LITE_ARCHITECTURE.md) - Browser-only implementation for demos (separate project)

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

**Disambiguation Mitigations:**

To prevent false positive matches (e.g., "Apple" company vs "apple" fruit):

| Mitigation | Description | Status |
|------------|-------------|--------|
| **Type matching** | Compare `inferred_type` - only match if types are compatible | Required |
| **Confidence threshold** | Require similarity >= 0.92 AND LLM confidence >= 0.7 | Required |
| **Phrase length filter** | Skip similarity check for labels < 2 words | Future |
| **Context embedding** | Include chunk context in embedding | Future |

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
| Builder uses `MERGE` | Idempotent - won't fail if node already exists |
| Gardener uses transactions | Atomic operations prevent partial updates |
| SSE is append-only | Events stream in order, no conflicts |
| Similarity check before create | Prevents Builder creating duplicates |

### Conflict Scenarios and Solutions

| Scenario | Risk | Solution |
|----------|------|----------|
| Gardener deletes node while Builder references it | Orphaned relationship | Gardener checks node existence before delete |
| Builder creates duplicate while Gardener merging | Two nodes for same concept | Similarity threshold catches this |
| Both agents write to same node | Data inconsistency | Neo4j transaction isolation handles this |
| Correction applied mid-extraction | Label mismatch | Builder re-checks after MERGE |

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
| [001](/_dev/ADR/0001-llm-clustering-over-gds.md) | LLM-only clustering | 1M context fits entire session; GDS optional at scale |
| [002](/_dev/ADR/0002-proofreading-in-gardener.md) | Proofreading in Gardener | Shared context, simpler architecture |
| [003](/_dev/ADR/0003-gemini-grounding-for-research.md) | Gemini grounding for research | Simpler setup, Tavily as fallback |
| [004](/_dev/ADR/0004-full-context-qa.md) | Full context Q&A | GraphRAG unnecessary for single session |

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

```

Now let me update the configuration section and add agent enable flags pattern:

```markdown
# Architectural Advisory: plasticFlower

**Date:** 26 December 2025  
**Version:** 8.1 (Navigable Knowledge)  
**Context:** Complete system design incorporating GraphRAG, Research Augmentation, and STT Correction  
**Learning Guide:** [LEARNING_GUIDE.md](./LEARNING_GUIDE.md) - Structured curriculum for Neo4j and Semantic Knowledge Graphs  
**Session State:** [_START_SESSION_STATE.md](./_START_SESSION_STATE.md) - Cross-session progress tracking (attach to every coding session)  
**ADR Index:** [_dev/ADR/INDEX.md](./_dev/ADR/INDEX.md) - Architecture Decision Records (critical process)  
**Lite Version:** [LITE_ARCHITECTURE.md](./LITE_ARCHITECTURE.md) - Browser-only implementation for demos (separate project)

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

**Disambiguation Mitigations:**

To prevent false positive matches (e.g., "Apple" company vs "apple" fruit):

| Mitigation | Description | Status |
|------------|-------------|--------|
| **Type matching** | Compare `inferred_type` - only match if types are compatible | Required |
| **Confidence threshold** | Require similarity >= 0.92 AND LLM confidence >= 0.7 | Required |
| **Phrase length filter** | Skip similarity check for labels < 2 words | Future |
| **Context embedding** | Include chunk context in embedding | Future |

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
| Builder uses `MERGE` | Idempotent - won't fail if node already exists |
| Gardener uses transactions | Atomic operations prevent partial updates |
| SSE is append-only | Events stream in order, no conflicts |
| Similarity check before create | Prevents Builder creating duplicates |

### Conflict Scenarios and Solutions

| Scenario | Risk | Solution |
|----------|------|----------|
| Gardener deletes node while Builder references it | Orphaned relationship | Gardener checks node existence before delete |
| Builder creates duplicate while Gardener merging | Two nodes for same concept | Similarity threshold catches this |
| Both agents write to same node | Data inconsistency | Neo4j transaction isolation handles this |
| Correction applied mid-extraction | Label mismatch | Builder re-checks after MERGE |

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
| [001](/_dev/ADR/0001-llm-clustering-over-gds.md) | LLM-only clustering | 1M context fits entire session; GDS optional at scale |
| [002](/_dev/ADR/0002-proofreading-in-gardener.md) | Proofreading in Gardener | Shared context, simpler architecture |
| [003](/_dev/ADR/0003-gemini-grounding-for-research.md) | Gemini grounding for research | Simpler setup, Tavily as fallback |
| [004](/_dev/ADR/0004-full-context-qa.md) | Full context Q&A | GraphRAG unnecessary for single session |

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

```

Now let me create the focused recommendations document for immediate implementation:

```markdown
# Immediate Implementation Recommendations

**Date:** 30 December 2025  
**Source:** Architecture Review Session  
**Status:** Ready for Implementation  
**Estimated Total Effort:** 6-8 hours

---

## Overview

This document contains the agreed recommendations from the architecture review session, prioritised for immediate implementation. All items are derived from the comprehensive review in `architecture_review_2025-12-30.md`.

---

## Priority 1: Pre-Creation Similarity Check (HIGH)

### Summary
Implement vector similarity checking in Builder BEFORE creating nodes. This reduces GHOST node count, provides accurate mention counts, and improves UI experience.

### Files to Modify
- `backend/app/services/builder_service.py` - Main implementation
- `backend/app/services/similarity.py` - Already exists, minor updates
- `backend/app/config.py` - Add `similarity_check_enabled` flag

### Implementation Steps

1. **Update `builder_service.py`:**
   ```python
   async def _process(self, session_id, chunk, start):
       # ... existing LLM extraction ...
       
       # NEW: For each extracted node, check similarity before create
       label_to_node: Dict[str, Tuple[Node, bool]] = {}  # label -> (node, is_new)
       
       for extracted_node in agent_result.nodes:
           result = await run_similarity(
               session_id, 
               extracted_node.label, 
               chunk.start_time
           )
           
           if isinstance(result, SimilarityMatchResult):
               # Disambiguation check
               if self._types_compatible(extracted_node.inferred_type, result.node.inferred_type):
                   if extracted_node.confidence >= 0.7:
                       # MATCH: Use existing node
                       label_to_node[extracted_node.label] = (result.node, False)
                       continue
           
           # CREATE: New GHOST node
           extracted_node.embedding = result.embedding
           persisted = await create_node(session_id, extracted_node)
           label_to_node[extracted_node.label] = (persisted, True)
       
       # Create relationships using label mapping
       for rel in agent_result.relationships:
           source_node, _ = label_to_node.get(rel.source, (None, False))
           target_node, _ = label_to_node.get(rel.target, (None, False))
           if source_node and target_node:
               # Use actual node IDs
               rel.source_id = source_node.id
               rel.target_id = target_node.id
               await create_relationship(session_id, rel)
   ```

2. **Add disambiguation helper:**
   ```python
   def _types_compatible(self, type1: str, type2: str) -> bool:
       """Check if inferred types are compatible for merging."""
       if not type1 or not type2:
           return True  # Allow if either is missing
       
       # Exact match
       if type1.lower() == type2.lower():
           return True
       
       # Compatible groups (extend as needed)
       compatible_groups = [
           {"concept", "idea", "term", "topic"},
           {"person", "speaker", "author"},
           {"organisation", "company", "institution"},
           {"technology", "framework", "tool", "library"},
       ]
       
       type1_lower, type2_lower = type1.lower(), type2.lower()
       for group in compatible_groups:
           if type1_lower in group and type2_lower in group:
               return True
       
       return False
   ```

3. **Update SSE broadcasting:**
   ```python
   # For matched nodes (is_new=False):
   await sse_manager.broadcast(session_id, NodeUpdatedEvent(payload=node))
   
   # For new nodes (is_new=True):
   await sse_manager.broadcast(session_id, NodeAddedEvent(payload=node))
   ```

4. **Add config flag:**
   ```python
   # In config.py
   similarity_check_enabled: bool = Field(
       True, 
       description="Enable pre-creation similarity check in Builder"
   )
   ```

### Acceptance Criteria
- [ ] Duplicate entities in same chunk don't create duplicate GHOST nodes
- [ ] Mention counts increment in real-time for matched nodes
- [ ] Relationships point to correct (matched or new) node IDs
- [ ] Type compatibility prevents false matches (e.g., Apple company vs fruit)
- [ ] Fallback to creation if embedding fails

### Effort: Medium (2-3 hours)

---

## Priority 2: Expose original_text in TranscriptChunk (HIGH)

### Summary
The `original_text` field IS stored in Neo4j but not exposed in the model or API. Make it visible.

### Files to Modify
- `backend/app/models/chunk.py` - Add field to model
- `backend/app/services/graph_db.py` - Update `_chunk_from_value()`

### Implementation Steps

1. **Update model (`chunk.py`):**
   ```python
   class TranscriptChunk(BaseModel):
       id: str
       text: str
       original_text: Optional[str] = Field(
           None, 
           description="Original STT output before corrections (audit trail)"
       )
       start_time: float
       end_time: float
       session_id: str
   ```

2. **Update retrieval (`graph_db.py`):**
   ```python
   def _chunk_from_value(value: Neo4jNode) -> TranscriptChunk:
       props = dict(value)
       # Include original_text if present
       return TranscriptChunk.model_validate(props)
   ```

### Acceptance Criteria
- [ ] `original_text` visible in chunk retrieval
- [ ] Export endpoints include `original_text`
- [ ] Existing chunks without `original_text` work (field is optional)

### Effort: Small (30 minutes)

---

## Priority 3: Integrate ProofreadCheckpoint (HIGH)

### Summary
The checkpoint infrastructure exists but is not used. Integrate it to enable incremental proofreading.

### Files to Modify
- `backend/app/services/scheduler.py` - Add checkpoint usage
- `backend/app/services/graph_db.py` - Add `get_chunks_after()` helper

### Implementation Steps

1. **Add helper function (`graph_db.py`):**
   ```python
   async def get_chunks_after(
       session_id: str, 
       after_chunk_id: str, 
       limit: int = 10
   ) -> List[TranscriptChunk]:
       """Get chunks created after the given chunk ID."""
       driver = await get_driver()
       query = """
       MATCH (ref:TranscriptChunk {id: $after_chunk_id, session_id: $session_id})
       MATCH (c:TranscriptChunk {session_id: $session_id})
       WHERE c.start_time > ref.start_time
       RETURN c AS chunk
       ORDER BY c.start_time
       LIMIT $limit
       """
       # ... execute and return
   ```

2. **Update Gardener (`scheduler.py`):**
   ```python
   async def _run_gardener(self, session_id: str) -> None:
       # Get checkpoint
       checkpoint = await get_proofread_checkpoint(session_id)
       
       if checkpoint:
           chunks_to_proofread = await get_chunks_after(
               session_id, checkpoint, limit=10
           )
       else:
           # First run - get recent chunks
           chunks_to_proofread = await list_chunks_for_session(session_id)[-10:]
       
       # ... existing Gardener logic ...
       
       # After successful run, update checkpoint
       if chunks_to_proofread:
           await update_proofread_checkpoint(
               session_id, 
               chunks_to_proofread[-1].id
           )
   ```

### Acceptance Criteria
- [ ] Gardener processes only new chunks since last checkpoint
- [ ] Checkpoint persists across server restarts
- [ ] First Gardener cycle processes initial chunks
- [ ] Subsequent cycles skip already-proofread chunks

### Effort: Medium (1-2 hours)

---

## Priority 4: Add Session Context Persistence (HIGH)

### Summary
Store session theme and key entities to maintain context during incremental proofreading.

### Files to Modify
- `backend/app/models/vocabulary.py` - Add SessionContext model
- `backend/app/services/graph_db.py` - Add CRUD functions
- `backend/app/services/scheduler.py` - Use context in Gardener prompt

### Implementation Steps

1. **Add model (`vocabulary.py`):**
   ```python
   class SessionContext(BaseModel):
       session_id: str
       theme_summary: str = Field(
           "", 
           description="Brief description of session topic"
       )
       key_entities: list[str] = Field(
           default_factory=list,
           description="Important recurring entities"
       )
       speaker_names: list[str] = Field(
           default_factory=list,
           description="Identified speaker names"
       )
       domain_terms: list[str] = Field(
           default_factory=list,
           description="Domain-specific vocabulary"
       )
       updated_at: datetime = Field(default_factory=datetime.now)
   ```

2. **Add persistence (`graph_db.py`):**
   ```python
   async def get_session_context(session_id: str) -> Optional[SessionContext]:
       # Query SessionContext node
       
   async def update_session_context(session_id: str, context: SessionContext) -> None:
       # MERGE SessionContext node
   ```

3. **Update Gardener prompt:**
   ```python
   # In scheduler.py
   context = await get_session_context(session_id)
   if context:
       prompt_sections.append(f"""
       ## SESSION CONTEXT
       Theme: {context.theme_summary}
       Key Entities: {', '.join(context.key_entities)}
       Speakers: {', '.join(context.speaker_names)}
       """)
   ```

4. **Gardener extracts/updates context:**
   - During first few cycles, Gardener identifies theme and key entities
   - LLM returns context suggestions in response
   - Context persisted for subsequent cycles

### Acceptance Criteria
- [ ] Session context persisted in Neo4j
- [ ] Gardener prompt includes context when available
- [ ] Context updated as session progresses
- [ ] Incremental proofreading maintains consistent understanding

### Effort: Medium (1.5-2 hours)

---

## Priority 5: Configuration Updates (MEDIUM)

### Summary
Update configuration for production readiness and debugging capability.

### Files to Modify
- `backend/app/config.py`

### Implementation Steps

1. **Reduce timeout:**
   ```python
   gemini_request_timeout: float = Field(
       90.0,  # Changed from 180.0
       ge=1.0,
       description="Seconds before a Gemini request is cancelled.",
   )
   ```

2. **Add agent enable flags:**
   ```python
   builder_enabled: bool = Field(
       True, 
       description="Enable Builder agent processing"
   )
   gardener_enabled: bool = Field(
       True, 
       description="Enable Gardener scheduling"
   )
   researcher_enabled: bool = Field(
       True, 
       description="Enable Researcher agent (Phase 3)"
   )
   librarian_enabled: bool = Field(
       True, 
       description="Enable Librarian Q&A (Phase E)"
   )
   similarity_check_enabled: bool = Field(
       True,
       description="Enable pre-creation similarity check in Builder"
   )
   ```

3. **Update agent startup to check flags:**
   ```python
   # In scheduler.py
   async def start(self) -> None:
       settings = get_settings()
       if not settings.gardener_enabled:
           logger.info("Gardener disabled via config")
           return
       # ... existing start logic
   ```

### Acceptance Criteria
- [ ] Timeout reduced to 90s
- [ ] Agent enable flags configurable via environment
- [ ] Agents check their flag before processing

### Effort: Small (30 minutes)

---

## Priority 6: Add Relationship Context to Builder (MEDIUM)

### Summary
Include existing relationships in Builder prompt for better extraction context.

### Files to Modify
- `backend/app/agents/builder.py`

### Implementation Steps

1. **Update prompt rendering:**
   ```python
   def _render_prompt(chunk_text: str, nodes: Sequence[Node], relationships: Sequence[Relationship]) -> str:
       sections = [PROMPT_PREAMBLE]
       
       existing_nodes = _format_existing_nodes(nodes)
       if existing_nodes:
           sections.append("## EXISTING NODES")
           sections.append(existing_nodes)
       
       # NEW: Add relationship context
       existing_rels = _format_existing_relationships(relationships, nodes)
       if existing_rels:
           sections.append("## EXISTING RELATIONSHIPS")
           sections.append(existing_rels)
       
       sections.append("## TRANSCRIPT CHUNK")
       sections.append(chunk_text.strip())
       # ...
   
   def _format_existing_relationships(
       relationships: Sequence[Relationship], 
       nodes: Sequence[Node]
   ) -> str:
       # Map node IDs to labels
       id_to_label = {n.id: n.label for n in nodes}
       
       lines = []
       for rel in relationships[:20]:  # Limit to avoid prompt bloat
           source = id_to_label.get(rel.source_id, "?")
           target = id_to_label.get(rel.target_id, "?")
           lines.append(f"- {source} -> {target} [{rel.category.value}]")
       
       return "\n".join(lines) if lines else ""
   ```

2. **Update Builder service to pass relationships:**
   ```python
   # In builder_service.py
   existing_nodes = await list_nodes(session_id)
   existing_rels = await list_relationships(session_id)
   
   agent_result = await self._agent.build(
       chunk_text=chunk.text,
       chunk_timestamp=chunk.start_time,
       existing_nodes=existing_nodes,
       existing_relationships=existing_rels,  # NEW
   )
   ```

### Acceptance Criteria
- [ ] Builder prompt includes relationship context
- [ ] Relationship limit prevents prompt bloat
- [ ] Better extraction context improves node/relationship quality

### Effort: Small (45 minutes)

---

## Priority 7: Document Updates (MEDIUM)

### Summary
Update documentation to reflect all changes.

### Files to Update
- `_docs/ARCHITECTURE_ADVISORY.md` - Already updated in this session
- `_docs/_START_SESSION_STATE.md` - Update progress tracker
- `_docs/_dev/ADR/` - Create ADR for pre-creation similarity check

### New ADR Required
Create `_docs/_dev/ADR/0011-pre-creation-similarity-check.md`:
- Decision: Implement similarity check before node creation
- Rationale: Fewer duplicates, accurate counts, better UX
- Mitigations: Type matching, confidence threshold
- Consequences: +200-500ms latency, reduced Gardener workload

### Effort: Small (30 minutes)

---

## Implementation Order

Recommended sequence for implementation:

1. **Configuration Updates (Priority 5)** - Quick wins, enables debugging
2. **Expose original_text (Priority 2)** - Quick win, no dependencies
3. **Pre-Creation Similarity Check (Priority 1)** - Core improvement
4. **ProofreadCheckpoint Integration (Priority 3)** - Requires testing
5. **Session Context Persistence (Priority 4)** - Builds on checkpoint
6. **Relationship Context in Builder (Priority 6)** - Enhancement
7. **Document Updates (Priority 7)** - Capture all changes

---

## Testing Checklist

After implementation, verify:

- [ ] Submit chunk with duplicate entity mention - only one GHOST node created
- [ ] Mention count increments correctly for matched nodes
- [ ] Relationships point to correct node IDs after similarity matching
- [ ] "Apple" (company) doesn't match "apple" (fruit) if types differ
- [ ] Gardener processes only new chunks since last checkpoint
- [ ] Session context persists and appears in Gardener prompt
- [ ] Export includes `original_text` where available
- [ ] Agent enable flags work (disable Gardener, verify no processing)
- [ ] Timeout correctly set to 90s

---

## Summary

| Priority | Item | Effort | Impact |
|----------|------|--------|--------|
| 1 | Pre-creation similarity check + disambiguation | Medium | High |
| 2 | Expose original_text | Small | High |
| 3 | Integrate ProofreadCheckpoint | Medium | High |
| 4 | Session context persistence | Medium | High |
| 5 | Configuration updates | Small | Medium |
| 6 | Relationship context in Builder | Small | Medium |
| 7 | Documentation updates | Small | Medium |

**Total estimated effort:** 6-8 hours

```

Let me also update the vector index architecture document to reflect the approved pre-creation check:

```markdown
# Vector Index Architecture: Chunks, Builder, and Embeddings

**Date:** 30 December 2025  
**Context:** Understanding how the vector index is created and used in plasticFlower

---

## Overview

The vector index enables semantic similarity search for node deduplication. This document explains how embeddings flow through the system.

---

## Architecture Diagram

```
                                 INGESTION FLOW
    ============================================================================
    
    Frontend (Browser)
           |
           | WebSpeech API produces text
           v
    +------------------+
    | POST /chunks     |  Transcript chunk submitted
    +------------------+
           |
           v
    +------------------+
    | TranscriptChunk  |  Stored in Neo4j (text, timestamps)
    | (Neo4j Node)     |
    +------------------+
           |
           v
    +------------------+
    | BuilderService   |  Orchestrates extraction
    +------------------+
           |
           +---> 1. Load existing nodes (labels only, no embeddings)
           |
           v
    +------------------+
    | Builder Agent    |  Calls Gemini LLM
    | (LLM Call)       |  Extracts entities & relationships
    +------------------+
           |
           | Returns: nodes[] and relationships[]
           v
    +------------------+
    | Embedding Gen    |  Calls Google text-embedding-004
    | (Google API)     |  768 dimensions per node label
    +------------------+
           |
           | ~100-200ms per embedding
           v
    +------------------+
    | Neo4j Persist    |  Node stored WITH embedding vector
    | (CREATE Node)    |  embedding property = float[768]
    +------------------+
           |
           v
    +------------------+
    | Vector Index     |  Automatically indexes new embedding
    | (Neo4j Native)   |  node_embedding_index
    +------------------+
    
    
                              SIMILARITY SEARCH FLOW
    ============================================================================
    
    +------------------+
    | Gardener Agent   |  During merge/dedup decision
    +------------------+
           |
           | Needs to find similar nodes
           v
    +------------------+
    | Vector Query     |  db.index.vector.queryNodes()
    | (Neo4j API)      |  Returns top-K similar nodes
    +------------------+
           |
           | Threshold: 0.92 (ADR-008)
           v
    +------------------+
    | Merge Decision   |  If score >= 0.92: same concept
    | (Gardener LLM)   |  LLM confirms/overrides
    +------------------+
```

---

## Timeline: What Happens When a Chunk Arrives

```
Time    Event                                    Duration
----    -----                                    --------
0ms     Frontend submits chunk via POST          ~10ms
        
10ms    Chunk saved to Neo4j                     ~20ms
        TranscriptChunk node created
        
30ms    BuilderService.process_chunk() starts
        
35ms    Load existing nodes from Neo4j           ~50ms
        (labels only, for LLM context)
        
85ms    Builder LLM call                         ~2000ms
        Gemini extracts entities
        
2085ms  Embedding generation begins              ~300ms
        (parallel for all extracted nodes)
        Each embedding: 100-200ms Google API
        
2385ms  Persist nodes to Neo4j                   ~100ms
        Node + embedding stored together
        Vector index auto-updates
        
2485ms  SSE broadcast: node_added events         ~10ms

2495ms  Publish to Redis (ratio-based)           ~5ms
        Triggers Gardener every 5 chunks
        
        [CHUNK PROCESSING COMPLETE]

        
        ... 4 more chunks processed ...
        

~15s    Gardener triggered (after 5 chunks)      ~10-20s
        
        Gardener loads all nodes + embeddings
        Gardener queries vector index for hints
        Gardener LLM decides: confirm/merge/prune
        
        [GARDENER CYCLE COMPLETE]
```

---

## Key Components Explained

### 1. Vector Index Creation (Startup)

**File:** `backend/app/services/graph_schema.py`

```python
CREATE VECTOR INDEX node_embedding_index IF NOT EXISTS
FOR (n:Node) ON (n.embedding)
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 768,
    `vector.similarity_function`: 'cosine'
  }
}
```

**When:** Application startup (`main.py` -> `ensure_graph_schema()`)

**What it does:** Creates a Neo4j native vector index on the `embedding` property of all `Node` labels. This index enables fast approximate nearest neighbour (ANN) search.

---

### 2. Embedding Generation

**File:** `backend/app/services/embeddings.py`

```python
async def generate_embedding(text: str) -> List[float]:
    # Calls Google text-embedding-004
    # Returns 768-dimensional vector
    response = client.models.embed_content(
        model="models/text-embedding-004",
        contents=text,
        config={'task_type': 'retrieval_document'}
    )
    return response.embeddings[0].values
```

**When:** After Builder LLM returns, before persisting nodes

**What it does:** 
1. Takes node label (e.g., "machine learning")
2. Calls Google embedding API
3. Returns 768 floats representing semantic meaning
4. Caches result (LRU cache, 512 entries)

---

### 3. Node Persistence with Embedding

**File:** `backend/app/services/builder_service.py`

```python
async def _populate_embeddings(self, nodes: List[Node]) -> None:
    tasks = [generate_embedding(node.label) for node in nodes]
    vectors = await asyncio.gather(*tasks)
    for node, vector in zip(nodes, vectors):
        node.embedding = vector  # Attached to node model

async def _persist_nodes(self, session_id: str, nodes: List[Node]) -> List[Node]:
    for node in nodes:
        await create_node(session_id, node)  # Includes embedding
```

**When:** After LLM extraction, before SSE broadcast

**What it does:**
1. Generates embeddings in parallel (async)
2. Attaches vector to each node
3. Persists node to Neo4j (embedding included)
4. Vector index automatically picks up new embedding

---

### 4. Similarity Search (Exists but NOT Used by Builder)

**File:** `backend/app/services/similarity.py`

```python
async def run_similarity(session_id: str, label: str, timestamp: float):
    embedding = await generate_embedding(label)
    candidate = await _query_best_match(session_id, embedding, top_k=5)
    
    if candidate and candidate.score >= 0.92:
        # Found existing node - increment mentions
        return SimilarityMatchResult(...)
    else:
        # No match - caller should create new node
        return SimilarityCreateResult(...)
```

**IMPORTANT:** This function exists but is **NOT called by BuilderService**.

The Builder creates all extracted nodes regardless of similarity. Deduplication happens later in the Gardener.

---

## Pre-Creation Similarity Check (APPROVED)

### Decision: Implement Pre-Check

After architecture review (30 December 2025), pre-creation similarity checking was approved for implementation. The benefits significantly outweigh the latency cost.

### Previous Flow (No Pre-Check)

```
Chunk arrives
    |
    v
Builder LLM extracts ["machine learning", "ML", "AI"]
    |
    v
Generate embeddings for ALL 3 labels
    |
    v
Create 3 GHOST nodes (even though ML and machine learning might be same concept)
    |
    v
[Later] Gardener merges duplicates
```

### New Flow (With Pre-Check) - APPROVED

```
Chunk arrives
    |
    v
Builder LLM extracts ["machine learning", "ML", "AI"]
    |
    v
For each label:
  - Generate embedding
  - Query vector index for similar nodes
  - Apply disambiguation checks:
    * Score >= 0.92?
    * Types compatible?
    * Confidence >= 0.7?
  - If all pass: MATCH (increment existing node)
  - Otherwise: CREATE new GHOST node
    |
    v
Create only 1-2 GHOST nodes (duplicates caught early)
Matched nodes get mentions incremented
    |
    v
Relationships rewired to use correct node IDs
    |
    v
SSE: node_added (new) or node_updated (matched)
    |
    v
[Later] Gardener has reduced merge workload
```

### Trade-off Analysis

| Approach | Pros | Cons |
|----------|------|------|
| Previous (Gardener cleanup) | Simpler Builder, faster per-chunk | More GHOST nodes, Gardener does more work |
| **New (Pre-check) APPROVED** | Fewer duplicates, accurate counts, better UX, less Gardener work | +200-500ms latency per chunk |

### Disambiguation Mitigations (Required)

To prevent false positive matches:

1. **Type matching:** Compare `inferred_type` - only match if types are compatible
2. **Confidence threshold:** Require similarity >= 0.92 AND LLM confidence >= 0.7

### Future Enhancements (Optional)

1. **Phrase length filter:** Skip similarity check for labels < 2 words
2. **Context embedding:** Include chunk context in embedding
3. **LLM prompt optimisation:** Pass semantic clusters to LLM to reduce duplicate extraction at source

---

## Neo4j Vector Query Details

**Query used for similarity search:**

```cypher
CALL db.index.vector.queryNodes('node_embedding_index', 5, $embedding)
YIELD node, score
WHERE node.session_id = $session_id
RETURN node.id AS node_id, score
ORDER BY score DESC
LIMIT 1
```

**Parameters:**
- `index_name`: "node_embedding_index"
- `top_k`: 5 (fetch 5 candidates)
- `embedding`: 768-float vector
- `session_id`: Current session (scope to session)

**Returns:**
- `node_id`: ID of most similar node
- `score`: Cosine similarity (0.0 to 1.0)

**Threshold:** 0.92 (per ADR-008)
- Score >= 0.92: Same concept (merge/increment)
- Score < 0.92: Different concept (create new)

---

## Summary

1. **Vector index** is created at app startup (idempotent)
2. **Embeddings** are generated AFTER Builder LLM returns, before persist
3. **Nodes are stored** with their embedding attached
4. **Index auto-updates** when new nodes are created
5. **Similarity search** exists but is NOT used pre-creation
6. **Gardener uses** vector index for merge hint suggestions

The `run_similarity()` function exists for potential future use (pre-check) but the current architecture relies on Gardener for deduplication.


```

```markdown
# Vector Index Architecture: Chunks, Builder, and Embeddings

**Date:** 30 December 2025  
**Context:** Understanding how the vector index is created and used in plasticFlower

---

## Overview

The vector index enables semantic similarity search for node deduplication. This document explains how embeddings flow through the system.

---

## Architecture Diagram

```
                                 INGESTION FLOW
    ============================================================================
    
    Frontend (Browser)
           |
           | WebSpeech API produces text
           v
    +------------------+
    | POST /chunks     |  Transcript chunk submitted
    +------------------+
           |
           v
    +------------------+
    | TranscriptChunk  |  Stored in Neo4j (text, timestamps)
    | (Neo4j Node)     |
    +------------------+
           |
           v
    +------------------+
    | BuilderService   |  Orchestrates extraction
    +------------------+
           |
           +---> 1. Load existing nodes (labels only, no embeddings)
           |
           v
    +------------------+
    | Builder Agent    |  Calls Gemini LLM
    | (LLM Call)       |  Extracts entities & relationships
    +------------------+
           |
           | Returns: nodes[] and relationships[]
           v
    +------------------+
    | Embedding Gen    |  Calls Google text-embedding-004
    | (Google API)     |  768 dimensions per node label
    +------------------+
           |
           | ~100-200ms per embedding
           v
    +------------------+
    | Neo4j Persist    |  Node stored WITH embedding vector
    | (CREATE Node)    |  embedding property = float[768]
    +------------------+
           |
           v
    +------------------+
    | Vector Index     |  Automatically indexes new embedding
    | (Neo4j Native)   |  node_embedding_index
    +------------------+
    
    
                              SIMILARITY SEARCH FLOW
    ============================================================================
    
    +------------------+
    | Gardener Agent   |  During merge/dedup decision
    +------------------+
           |
           | Needs to find similar nodes
           v
    +------------------+
    | Vector Query     |  db.index.vector.queryNodes()
    | (Neo4j API)      |  Returns top-K similar nodes
    +------------------+
           |
           | Threshold: 0.92 (ADR-008)
           v
    +------------------+
    | Merge Decision   |  If score >= 0.92: same concept
    | (Gardener LLM)   |  LLM confirms/overrides
    +------------------+
```

---

## Timeline: What Happens When a Chunk Arrives

```
Time    Event                                    Duration
----    -----                                    --------
0ms     Frontend submits chunk via POST          ~10ms
        
10ms    Chunk saved to Neo4j                     ~20ms
        TranscriptChunk node created
        
30ms    BuilderService.process_chunk() starts
        
35ms    Load existing nodes from Neo4j           ~50ms
        (labels only, for LLM context)
        
85ms    Builder LLM call                         ~2000ms
        Gemini extracts entities
        
2085ms  Embedding generation begins              ~300ms
        (parallel for all extracted nodes)
        Each embedding: 100-200ms Google API
        
2385ms  Persist nodes to Neo4j                   ~100ms
        Node + embedding stored together
        Vector index auto-updates
        
2485ms  SSE broadcast: node_added events         ~10ms

2495ms  Publish to Redis (ratio-based)           ~5ms
        Triggers Gardener every 5 chunks
        
        [CHUNK PROCESSING COMPLETE]

        
        ... 4 more chunks processed ...
        

~15s    Gardener triggered (after 5 chunks)      ~10-20s
        
        Gardener loads all nodes + embeddings
        Gardener queries vector index for hints
        Gardener LLM decides: confirm/merge/prune
        
        [GARDENER CYCLE COMPLETE]
```

---

## Key Components Explained

### 1. Vector Index Creation (Startup)

**File:** `backend/app/services/graph_schema.py`

```python
CREATE VECTOR INDEX node_embedding_index IF NOT EXISTS
FOR (n:Node) ON (n.embedding)
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 768,
    `vector.similarity_function`: 'cosine'
  }
}
```

**When:** Application startup (`main.py` -> `ensure_graph_schema()`)

**What it does:** Creates a Neo4j native vector index on the `embedding` property of all `Node` labels. This index enables fast approximate nearest neighbour (ANN) search.

---

### 2. Embedding Generation

**File:** `backend/app/services/embeddings.py`

```python
async def generate_embedding(text: str) -> List[float]:
    # Calls Google text-embedding-004
    # Returns 768-dimensional vector
    response = client.models.embed_content(
        model="models/text-embedding-004",
        contents=text,
        config={'task_type': 'retrieval_document'}
    )
    return response.embeddings[0].values
```

**When:** After Builder LLM returns, before persisting nodes

**What it does:** 
1. Takes node label (e.g., "machine learning")
2. Calls Google embedding API
3. Returns 768 floats representing semantic meaning
4. Caches result (LRU cache, 512 entries)

---

### 3. Node Persistence with Embedding

**File:** `backend/app/services/builder_service.py`

```python
async def _populate_embeddings(self, nodes: List[Node]) -> None:
    tasks = [generate_embedding(node.label) for node in nodes]
    vectors = await asyncio.gather(*tasks)
    for node, vector in zip(nodes, vectors):
        node.embedding = vector  # Attached to node model

async def _persist_nodes(self, session_id: str, nodes: List[Node]) -> List[Node]:
    for node in nodes:
        await create_node(session_id, node)  # Includes embedding
```

**When:** After LLM extraction, before SSE broadcast

**What it does:**
1. Generates embeddings in parallel (async)
2. Attaches vector to each node
3. Persists node to Neo4j (embedding included)
4. Vector index automatically picks up new embedding

---

### 4. Similarity Search (Exists but NOT Used by Builder)

**File:** `backend/app/services/similarity.py`

```python
async def run_similarity(session_id: str, label: str, timestamp: float):
    embedding = await generate_embedding(label)
    candidate = await _query_best_match(session_id, embedding, top_k=5)
    
    if candidate and candidate.score >= 0.92:
        # Found existing node - increment mentions
        return SimilarityMatchResult(...)
    else:
        # No match - caller should create new node
        return SimilarityCreateResult(...)
```

**IMPORTANT:** This function exists but is **NOT called by BuilderService**.

The Builder creates all extracted nodes regardless of similarity. Deduplication happens later in the Gardener.

---

## Pre-Creation Similarity Check (APPROVED)

### Decision: Implement Pre-Check

After architecture review (30 December 2025), pre-creation similarity checking was approved for implementation. The benefits significantly outweigh the latency cost.

### Previous Flow (No Pre-Check)

```
Chunk arrives
    |
    v
Builder LLM extracts ["machine learning", "ML", "AI"]
    |
    v
Generate embeddings for ALL 3 labels
    |
    v
Create 3 GHOST nodes (even though ML and machine learning might be same concept)
    |
    v
[Later] Gardener merges duplicates
```

### New Flow (With Pre-Check) - APPROVED

```
Chunk arrives
    |
    v
Builder LLM extracts ["machine learning", "ML", "AI"]
    |
    v
For each label:
  - Generate embedding
  - Query vector index for similar nodes
  - Apply disambiguation checks:
    * Score >= 0.92?
    * Types compatible?
    * Confidence >= 0.7?
  - If all pass: MATCH (increment existing node)
  - Otherwise: CREATE new GHOST node
    |
    v
Create only 1-2 GHOST nodes (duplicates caught early)
Matched nodes get mentions incremented
    |
    v
Relationships rewired to use correct node IDs
    |
    v
SSE: node_added (new) or node_updated (matched)
    |
    v
[Later] Gardener has reduced merge workload
```

### Trade-off Analysis

| Approach | Pros | Cons |
|----------|------|------|
| Previous (Gardener cleanup) | Simpler Builder, faster per-chunk | More GHOST nodes, Gardener does more work |
| **New (Pre-check) APPROVED** | Fewer duplicates, accurate counts, better UX, less Gardener work | +200-500ms latency per chunk |

### Disambiguation Mitigations (Required)

To prevent false positive matches:

1. **Type matching:** Compare `inferred_type` - only match if types are compatible
2. **Confidence threshold:** Require similarity >= 0.92 AND LLM confidence >= 0.7

### Future Enhancements (Optional)

1. **Phrase length filter:** Skip similarity check for labels < 2 words
2. **Context embedding:** Include chunk context in embedding
3. **LLM prompt optimisation:** Pass semantic clusters to LLM to reduce duplicate extraction at source

---

## Neo4j Vector Query Details

**Query used for similarity search:**

```cypher
CALL db.index.vector.queryNodes('node_embedding_index', 5, $embedding)
YIELD node, score
WHERE node.session_id = $session_id
RETURN node.id AS node_id, score
ORDER BY score DESC
LIMIT 1
```

**Parameters:**
- `index_name`: "node_embedding_index"
- `top_k`: 5 (fetch 5 candidates)
- `embedding`: 768-float vector
- `session_id`: Current session (scope to session)

**Returns:**
- `node_id`: ID of most similar node
- `score`: Cosine similarity (0.0 to 1.0)

**Threshold:** 0.92 (per ADR-008)
- Score >= 0.92: Same concept (merge/increment)
- Score < 0.92: Different concept (create new)

---

## Summary

1. **Vector index** is created at app startup (idempotent)
2. **Embeddings** are generated AFTER Builder LLM returns
3. **Pre-creation similarity check** queries index before node creation (APPROVED)
4. **Matched nodes** get mentions incremented instead of creating duplicates
5. **New nodes** are stored with embedding attached
6. **Index auto-updates** when new nodes are created
7. **Gardener** handles edge cases missed by pre-check (synonyms, abbreviations)

The `run_similarity()` function is now integrated into Builder flow for pre-creation deduplication.

---

## Implementation Status

| Component | Status |
|-----------|--------|
| Vector index creation | Implemented |
| Embedding generation | Implemented |
| `run_similarity()` function | Implemented (was unused) |
| Pre-creation check in Builder | **PENDING** (approved for implementation) |
| Disambiguation mitigations | **PENDING** (type matching, confidence threshold) |
| SSE event updates | **PENDING** (`node_updated` for matches) |


```

All documents have been updated. Here's a summary of what was created/modified:

---

## Documents Updated

### 1. `_docs/_evidence/architecture_review_2025-12-30.md`
**Updated with:**
- Full pre-creation similarity check decision and implementation details
- Disambiguation mitigations (type matching, confidence threshold)
- Revised priority actions table with similarity check as HIGH priority
- Relationship rewiring requirements
- SSE event changes for matched vs new nodes
- Future LLM extraction optimisation notes

### 2. `_docs/ARCHITECTURE_ADVISORY.md` (Canonical Record)
**Updated sections:**
- **Section 3.1 Builder:** Completely revised with pre-creation similarity check flow, disambiguation mitigations, and benefits
- **Section 3.2 Gardener:** Updated to reflect reduced merge workload, session context, and ratio-based triggering
- **Section 5.4 SSE Events:** Added all implemented events with source agent, including `node_updated` for similarity matches
- **New Configuration section:** Added agent enable flags pattern and key settings table

### 3. `_docs/_evidence/vector_index_architecture.md`
**Updated with:**
- Decision status changed from "revisit later" to "APPROVED"
- New flow diagram showing pre-check with disambiguation
- Implementation status table
- Future enhancements section

### 4. `_docs/_evidence/IMMEDIATE_RECOMMENDATIONS.md` (NEW)
**Created as focused implementation guide containing:**
- 7 prioritised recommendations with effort estimates
- Detailed implementation steps with code examples
- Acceptance criteria for each item
- Recommended implementation order
- Testing checklist
- Total effort estimate: 6-8 hours

---

## Next Steps

The `IMMEDIATE_RECOMMENDATIONS.md` document is ready to guide implementation. The recommended order is:

1. **Configuration Updates** (30 min) - Quick wins
2. **Expose original_text** (30 min) - Quick win
3. **Pre-Creation Similarity Check** (2-3 hours) - Core improvement
4. **ProofreadCheckpoint Integration** (1-2 hours) - Efficiency
5. **Session Context Persistence** (1.5-2 hours) - Quality
6. **Relationship Context in Builder** (45 min) - Enhancement
7. **Documentation/ADR** (30 min) - Capture decisions

Would you like to proceed with implementation, or would you prefer to review any of the documents first?

---

**User**

Some recent updates of @_docs/ARCHITECTURE_ADVISORY.md by dev team - can you review and ensure your understanding of project is aligned - note any areas of concern or high interest/impact to future dev -[4 tools called]

Good - the Gardener section (lines 245-254) has already been updated with:
- Ratio-based triggering (5:1)
- `gemini-2.5-flash` model
- 90 second timeout

**One remaining update needed** - line 541 still says "Builder uses `MERGE`" but we now use `MATCH` for node lookup in relationship creation:

[1 tool called]

Now let me add the Gemini configuration note (thinking mode is a significant discovery):

[7 tools called]

**ARCHITECTURE_ADVISORY.md updated:**

| Change | Section |
|--------|---------|
| Version 8.1 -> 8.2 | Header |
| Date updated to 30 Dec 2025 | Header |
| Added Gemini 2.5 thinking mode config note | Configuration section |
| Added Literal vs regex pattern guidance | Configuration section |
| Fixed "Builder uses MERGE" -> MATCH pattern | Safe by Design |
| Added critical Cypher pattern example | Safe by Design |
| Updated ADR list (added 005-010) | Current ADRs |

Architecture doc now accurately reflects:
- Ratio-based triggering (already updated)
- Flash model usage (already updated)
- MATCH over MERGE pattern (new)
- Thinking mode disabled (new)
- All 10 ADRs (new)

---

**Cursor**

I've reviewed the updates from the dev team. Let me confirm my understanding is aligned and note areas of concern:

**Understanding Confirmed - Updates Aligned**

I've reviewed the ARCHITECTURE_ADVISORY.md updates. My understanding is now aligned with the v8.2 architecture.

---

## Summary of Critical Updates

| Update | Impact Level | Notes |
|--------|--------------|-------|
| **Gemini 2.5 thinking mode** | HIGH | Must disable with `thinking_budget=0` or face 60+ second delays |
| **MATCH over MERGE pattern** | HIGH | Prevents corrupt empty nodes in graph - date-stamped fix (2025-12-28) |
| **Literal types for Pydantic** | MEDIUM | Better structured output compatibility with Gemini |
| **ADRs 005-010 added** | LOW | Documentation completeness |

---

## Areas of Concern / High Impact for Future Dev

### 1. Gemini 2.5 Thinking Mode (CRITICAL)
Any new agent development or LLM service changes **must** include `thinking_budget=0` in the config. This is easy to forget when:
- Adding new agent (Researcher, Librarian)
- Modifying existing agent prompts
- Testing with different Gemini models

**Recommendation:** Consider adding a shared helper function that enforces this config pattern across all agents.

### 2. MATCH vs MERGE Pattern (CRITICAL)
The corrupt node issue is now documented, but line 586 still references:
> "Builder re-checks after MERGE"

This may need rewording for consistency since we now use MATCH for node lookups. Minor documentation alignment.

### 3. Agent Enable Flags Pattern (MEDIUM)
Lines 170-182 show the pattern but these flags don't appear to be implemented in `config.py` yet. This is forward-looking documentation - needs implementation to match.

### 4. Pre-creation Similarity Check (HIGH IMPACT)
The Builder section (lines 190-262) documents pre-creation similarity checking, but I should verify this is fully implemented in the codebase. This directly affects:
- GHOST node volume
- Gardener merge workload
- UI smoothness (fewer node_added + node_merged sequences)

---

**Shall I verify the codebase implementation matches the documented patterns (particularly agent enable flags and pre-creation similarity)?** This would ensure documentation and code are in sync.

---

**User**

1. agree (add to Immediate development plan)
2. agree, please update
3. agree add to dev plan
4. agree - not implemented - part of development plan

Please do final check, update docs including @_docs/_evidence/IMMEDIATE_RECOMMENDATIONS.md then revert

---

**Cursor**

I'll address each item. First, let me check line 586 for the MERGE reference that needs updating:

Now I'll update both documents. First, fixing line 586 in ARCHITECTURE_ADVISORY.md:

```markdown
# Architectural Advisory: plasticFlower

**Date:** 30 December 2025  
**Version:** 8.2 (Event-Driven Agents)  
**Context:** Complete system design incorporating GraphRAG, Research Augmentation, and STT Correction  
**Learning Guide:** [LEARNING_GUIDE.md](./LEARNING_GUIDE.md) - Structured curriculum for Neo4j and Semantic Knowledge Graphs  
**Session State:** [_START_SESSION_STATE.md](./_START_SESSION_STATE.md) - Cross-session progress tracking (attach to every coding session)  
**ADR Index:** [_dev/ADR/INDEX.md](./_dev/ADR/INDEX.md) - Architecture Decision Records (critical process)  
**Lite Version:** [LITE_ARCHITECTURE.md](./LITE_ARCHITECTURE.md) - Browser-only implementation for demos (separate project)

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

**Disambiguation Mitigations:**

To prevent false positive matches (e.g., "Apple" company vs "apple" fruit):

| Mitigation | Description | Status |
|------------|-------------|--------|
| **Type matching** | Compare `inferred_type` - only match if types are compatible | Required |
| **Confidence threshold** | Require similarity >= 0.92 AND LLM confidence >= 0.7 | Required |
| **Phrase length filter** | Skip similarity check for labels < 2 words | Future |
| **Context embedding** | Include chunk context in embedding | Future |

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

```

Now let me update IMMEDIATE_RECOMMENDATIONS.md to add the Gemini config helper function and ensure agent enable flags verification is included:

```markdown
# Immediate Implementation Recommendations

**Date:** 30 December 2025  
**Source:** Architecture Review Session  
**Status:** Ready for Implementation  
**Estimated Total Effort:** 6-8 hours

---

## Overview

This document contains the agreed recommendations from the architecture review session, prioritised for immediate implementation. All items are derived from the comprehensive review in `architecture_review_2025-12-30.md`.

---

## Priority 1: Pre-Creation Similarity Check (HIGH)

### Summary
Implement vector similarity checking in Builder BEFORE creating nodes. This reduces GHOST node count, provides accurate mention counts, and improves UI experience.

### Files to Modify
- `backend/app/services/builder_service.py` - Main implementation
- `backend/app/services/similarity.py` - Already exists, minor updates
- `backend/app/config.py` - Add `similarity_check_enabled` flag

### Implementation Steps

1. **Update `builder_service.py`:**
   ```python
   async def _process(self, session_id, chunk, start):
       # ... existing LLM extraction ...
       
       # NEW: For each extracted node, check similarity before create
       label_to_node: Dict[str, Tuple[Node, bool]] = {}  # label -> (node, is_new)
       
       for extracted_node in agent_result.nodes:
           result = await run_similarity(
               session_id, 
               extracted_node.label, 
               chunk.start_time
           )
           
           if isinstance(result, SimilarityMatchResult):
               # Disambiguation check
               if self._types_compatible(extracted_node.inferred_type, result.node.inferred_type):
                   if extracted_node.confidence >= 0.7:
                       # MATCH: Use existing node
                       label_to_node[extracted_node.label] = (result.node, False)
                       continue
           
           # CREATE: New GHOST node
           extracted_node.embedding = result.embedding
           persisted = await create_node(session_id, extracted_node)
           label_to_node[extracted_node.label] = (persisted, True)
       
       # Create relationships using label mapping
       for rel in agent_result.relationships:
           source_node, _ = label_to_node.get(rel.source, (None, False))
           target_node, _ = label_to_node.get(rel.target, (None, False))
           if source_node and target_node:
               # Use actual node IDs
               rel.source_id = source_node.id
               rel.target_id = target_node.id
               await create_relationship(session_id, rel)
   ```

2. **Add disambiguation helper:**
   ```python
   def _types_compatible(self, type1: str, type2: str) -> bool:
       """Check if inferred types are compatible for merging."""
       if not type1 or not type2:
           return True  # Allow if either is missing
       
       # Exact match
       if type1.lower() == type2.lower():
           return True
       
       # Compatible groups (extend as needed)
       compatible_groups = [
           {"concept", "idea", "term", "topic"},
           {"person", "speaker", "author"},
           {"organisation", "company", "institution"},
           {"technology", "framework", "tool", "library"},
       ]
       
       type1_lower, type2_lower = type1.lower(), type2.lower()
       for group in compatible_groups:
           if type1_lower in group and type2_lower in group:
               return True
       
       return False
   ```

3. **Update SSE broadcasting:**
   ```python
   # For matched nodes (is_new=False):
   await sse_manager.broadcast(session_id, NodeUpdatedEvent(payload=node))
   
   # For new nodes (is_new=True):
   await sse_manager.broadcast(session_id, NodeAddedEvent(payload=node))
   ```

4. **Add config flag:**
   ```python
   # In config.py
   similarity_check_enabled: bool = Field(
       True, 
       description="Enable pre-creation similarity check in Builder"
   )
   ```

### Acceptance Criteria
- [ ] Duplicate entities in same chunk don't create duplicate GHOST nodes
- [ ] Mention counts increment in real-time for matched nodes
- [ ] Relationships point to correct (matched or new) node IDs
- [ ] Type compatibility prevents false matches (e.g., Apple company vs fruit)
- [ ] Fallback to creation if embedding fails

### Effort: Medium (2-3 hours)

---

## Priority 2: Expose original_text in TranscriptChunk (HIGH)

### Summary
The `original_text` field IS stored in Neo4j but not exposed in the model or API. Make it visible.

### Files to Modify
- `backend/app/models/chunk.py` - Add field to model
- `backend/app/services/graph_db.py` - Update `_chunk_from_value()`

### Implementation Steps

1. **Update model (`chunk.py`):**
   ```python
   class TranscriptChunk(BaseModel):
       id: str
       text: str
       original_text: Optional[str] = Field(
           None, 
           description="Original STT output before corrections (audit trail)"
       )
       start_time: float
       end_time: float
       session_id: str
   ```

2. **Update retrieval (`graph_db.py`):**
   ```python
   def _chunk_from_value(value: Neo4jNode) -> TranscriptChunk:
       props = dict(value)
       # Include original_text if present
       return TranscriptChunk.model_validate(props)
   ```

### Acceptance Criteria
- [ ] `original_text` visible in chunk retrieval
- [ ] Export endpoints include `original_text`
- [ ] Existing chunks without `original_text` work (field is optional)

### Effort: Small (30 minutes)

---

## Priority 3: Integrate ProofreadCheckpoint (HIGH)

### Summary
The checkpoint infrastructure exists but is not used. Integrate it to enable incremental proofreading.

### Files to Modify
- `backend/app/services/scheduler.py` - Add checkpoint usage
- `backend/app/services/graph_db.py` - Add `get_chunks_after()` helper

### Implementation Steps

1. **Add helper function (`graph_db.py`):**
   ```python
   async def get_chunks_after(
       session_id: str, 
       after_chunk_id: str, 
       limit: int = 10
   ) -> List[TranscriptChunk]:
       """Get chunks created after the given chunk ID."""
       driver = await get_driver()
       query = """
       MATCH (ref:TranscriptChunk {id: $after_chunk_id, session_id: $session_id})
       MATCH (c:TranscriptChunk {session_id: $session_id})
       WHERE c.start_time > ref.start_time
       RETURN c AS chunk
       ORDER BY c.start_time
       LIMIT $limit
       """
       # ... execute and return
   ```

2. **Update Gardener (`scheduler.py`):**
   ```python
   async def _run_gardener(self, session_id: str) -> None:
       # Get checkpoint
       checkpoint = await get_proofread_checkpoint(session_id)
       
       if checkpoint:
           chunks_to_proofread = await get_chunks_after(
               session_id, checkpoint, limit=10
           )
       else:
           # First run - get recent chunks
           chunks_to_proofread = await list_chunks_for_session(session_id)[-10:]
       
       # ... existing Gardener logic ...
       
       # After successful run, update checkpoint
       if chunks_to_proofread:
           await update_proofread_checkpoint(
               session_id, 
               chunks_to_proofread[-1].id
           )
   ```

### Acceptance Criteria
- [ ] Gardener processes only new chunks since last checkpoint
- [ ] Checkpoint persists across server restarts
- [ ] First Gardener cycle processes initial chunks
- [ ] Subsequent cycles skip already-proofread chunks

### Effort: Medium (1-2 hours)

---

## Priority 4: Add Session Context Persistence (HIGH)

### Summary
Store session theme and key entities to maintain context during incremental proofreading.

### Files to Modify
- `backend/app/models/vocabulary.py` - Add SessionContext model
- `backend/app/services/graph_db.py` - Add CRUD functions
- `backend/app/services/scheduler.py` - Use context in Gardener prompt

### Implementation Steps

1. **Add model (`vocabulary.py`):**
   ```python
   class SessionContext(BaseModel):
       session_id: str
       theme_summary: str = Field(
           "", 
           description="Brief description of session topic"
       )
       key_entities: list[str] = Field(
           default_factory=list,
           description="Important recurring entities"
       )
       speaker_names: list[str] = Field(
           default_factory=list,
           description="Identified speaker names"
       )
       domain_terms: list[str] = Field(
           default_factory=list,
           description="Domain-specific vocabulary"
       )
       updated_at: datetime = Field(default_factory=datetime.now)
   ```

2. **Add persistence (`graph_db.py`):**
   ```python
   async def get_session_context(session_id: str) -> Optional[SessionContext]:
       # Query SessionContext node
       
   async def update_session_context(session_id: str, context: SessionContext) -> None:
       # MERGE SessionContext node
   ```

3. **Update Gardener prompt:**
   ```python
   # In scheduler.py
   context = await get_session_context(session_id)
   if context:
       prompt_sections.append(f"""
       ## SESSION CONTEXT
       Theme: {context.theme_summary}
       Key Entities: {', '.join(context.key_entities)}
       Speakers: {', '.join(context.speaker_names)}
       """)
   ```

4. **Gardener extracts/updates context:**
   - During first few cycles, Gardener identifies theme and key entities
   - LLM returns context suggestions in response
   - Context persisted for subsequent cycles

### Acceptance Criteria
- [ ] Session context persisted in Neo4j
- [ ] Gardener prompt includes context when available
- [ ] Context updated as session progresses
- [ ] Incremental proofreading maintains consistent understanding

### Effort: Medium (1.5-2 hours)

---

## Priority 5: Configuration Updates (MEDIUM)

### Summary
Update configuration for production readiness and debugging capability.

### Files to Modify
- `backend/app/config.py`
- `backend/app/services/builder_service.py` - Check builder_enabled
- `backend/app/services/scheduler.py` - Check gardener_enabled

### Implementation Steps

1. **Reduce timeout:**
   ```python
   gemini_request_timeout: float = Field(
       90.0,  # Changed from 180.0
       ge=1.0,
       description="Seconds before a Gemini request is cancelled.",
   )
   ```

2. **Add agent enable flags:**
   ```python
   builder_enabled: bool = Field(
       True, 
       description="Enable Builder agent processing"
   )
   gardener_enabled: bool = Field(
       True, 
       description="Enable Gardener scheduling"
   )
   researcher_enabled: bool = Field(
       True, 
       description="Enable Researcher agent (Phase 3)"
   )
   librarian_enabled: bool = Field(
       True, 
       description="Enable Librarian Q&A (Phase E)"
   )
   similarity_check_enabled: bool = Field(
       True,
       description="Enable pre-creation similarity check in Builder"
   )
   ```

3. **Update agent startup to check flags:**
   ```python
   # In scheduler.py
   async def start(self) -> None:
       settings = get_settings()
       if not settings.gardener_enabled:
           logger.info("Gardener disabled via config")
           return
       # ... existing start logic
   ```

### Acceptance Criteria
- [ ] Timeout reduced to 90s
- [ ] Agent enable flags configurable via environment
- [ ] Agents check their flag before processing

### Effort: Small (30 minutes)

---

## Priority 5b: Gemini Config Helper Function (MEDIUM)

### Summary
Create a shared helper function that enforces Gemini 2.5 configuration patterns (thinking mode disabled, proper schema setup). This prevents future agents from accidentally omitting critical config.

### Files to Modify
- `backend/app/services/llm_utils.py` (new file)
- `backend/app/agents/builder.py` - Use helper
- `backend/app/agents/gardener.py` - Use helper

### Implementation Steps

1. **Create helper (`llm_utils.py`):**
   ```python
   from google.genai import types
   
   def create_gemini_config(
       response_schema: type,
       thinking_budget: int = 0,
   ) -> types.GenerateContentConfig:
       """
       Create Gemini config with correct defaults for structured output.
       
       CRITICAL: Gemini 2.5 has thinking mode ON by default, which adds
       60+ seconds to each call. This helper ensures it's disabled.
       """
       return types.GenerateContentConfig(
           response_mime_type="application/json",
           response_schema=response_schema,
           thinking_config=types.ThinkingConfig(thinking_budget=thinking_budget),
       )
   ```

2. **Update agents to use helper:**
   ```python
   # In builder.py / gardener.py
   from backend.app.services.llm_utils import create_gemini_config
   
   config = create_gemini_config(response_schema=BuilderResult)
   ```

### Acceptance Criteria
- [ ] Helper function enforces thinking_budget=0 by default
- [ ] Builder and Gardener agents use the helper
- [ ] Future agents can import and use consistently
- [ ] Docstring warns about the 60+ second issue

### Effort: Small (30 minutes)

---

## Priority 6: Add Relationship Context to Builder (MEDIUM)

### Summary
Include existing relationships in Builder prompt for better extraction context.

### Files to Modify
- `backend/app/agents/builder.py`

### Implementation Steps

1. **Update prompt rendering:**
   ```python
   def _render_prompt(chunk_text: str, nodes: Sequence[Node], relationships: Sequence[Relationship]) -> str:
       sections = [PROMPT_PREAMBLE]
       
       existing_nodes = _format_existing_nodes(nodes)
       if existing_nodes:
           sections.append("## EXISTING NODES")
           sections.append(existing_nodes)
       
       # NEW: Add relationship context
       existing_rels = _format_existing_relationships(relationships, nodes)
       if existing_rels:
           sections.append("## EXISTING RELATIONSHIPS")
           sections.append(existing_rels)
       
       sections.append("## TRANSCRIPT CHUNK")
       sections.append(chunk_text.strip())
       # ...
   
   def _format_existing_relationships(
       relationships: Sequence[Relationship], 
       nodes: Sequence[Node]
   ) -> str:
       # Map node IDs to labels
       id_to_label = {n.id: n.label for n in nodes}
       
       lines = []
       for rel in relationships[:20]:  # Limit to avoid prompt bloat
           source = id_to_label.get(rel.source_id, "?")
           target = id_to_label.get(rel.target_id, "?")
           lines.append(f"- {source} -> {target} [{rel.category.value}]")
       
       return "\n".join(lines) if lines else ""
   ```

2. **Update Builder service to pass relationships:**
   ```python
   # In builder_service.py
   existing_nodes = await list_nodes(session_id)
   existing_rels = await list_relationships(session_id)
   
   agent_result = await self._agent.build(
       chunk_text=chunk.text,
       chunk_timestamp=chunk.start_time,
       existing_nodes=existing_nodes,
       existing_relationships=existing_rels,  # NEW
   )
   ```

### Acceptance Criteria
- [ ] Builder prompt includes relationship context
- [ ] Relationship limit prevents prompt bloat
- [ ] Better extraction context improves node/relationship quality

### Effort: Small (45 minutes)

---

## Priority 7: Document Updates (MEDIUM)

### Summary
Update documentation to reflect all changes.

### Files to Update
- `_docs/ARCHITECTURE_ADVISORY.md` - Already updated in this session
- `_docs/_START_SESSION_STATE.md` - Update progress tracker
- `_docs/_dev/ADR/` - Create ADR for pre-creation similarity check

### New ADR Required
Create `_docs/_dev/ADR/0011-pre-creation-similarity-check.md`:
- Decision: Implement similarity check before node creation
- Rationale: Fewer duplicates, accurate counts, better UX
- Mitigations: Type matching, confidence threshold
- Consequences: +200-500ms latency, reduced Gardener workload

### Effort: Small (30 minutes)

---

## Implementation Order

Recommended sequence for implementation:

1. **Configuration Updates (Priority 5)** - Quick wins, enables debugging
2. **Expose original_text (Priority 2)** - Quick win, no dependencies
3. **Pre-Creation Similarity Check (Priority 1)** - Core improvement
4. **ProofreadCheckpoint Integration (Priority 3)** - Requires testing
5. **Session Context Persistence (Priority 4)** - Builds on checkpoint
6. **Relationship Context in Builder (Priority 6)** - Enhancement
7. **Document Updates (Priority 7)** - Capture all changes

---

## Testing Checklist

After implementation, verify:

- [ ] Submit chunk with duplicate entity mention - only one GHOST node created
- [ ] Mention count increments correctly for matched nodes
- [ ] Relationships point to correct node IDs after similarity matching
- [ ] "Apple" (company) doesn't match "apple" (fruit) if types differ
- [ ] Gardener processes only new chunks since last checkpoint
- [ ] Session context persists and appears in Gardener prompt
- [ ] Export includes `original_text` where available
- [ ] Agent enable flags work (disable Gardener, verify no processing)
- [ ] Timeout correctly set to 90s

---

## Summary

| Priority | Item | Effort | Impact |
|----------|------|--------|--------|
| 1 | Pre-creation similarity check + disambiguation | Medium | High |
| 2 | Expose original_text | Small | High |
| 3 | Integrate ProofreadCheckpoint | Medium | High |
| 4 | Session context persistence | Medium | High |
| 5 | Configuration updates | Small | Medium |
| 6 | Relationship context in Builder | Small | Medium |
| 7 | Documentation updates | Small | Medium |

**Total estimated effort:** 6-8 hours


```

Now I need to update the Summary table and Implementation Order to include Priority 5b:

```markdown
# Immediate Implementation Recommendations

**Date:** 30 December 2025  
**Source:** Architecture Review Session  
**Status:** Ready for Implementation  
**Estimated Total Effort:** 6-8 hours

---

## Overview

This document contains the agreed recommendations from the architecture review session, prioritised for immediate implementation. All items are derived from the comprehensive review in `architecture_review_2025-12-30.md`.

---

## Priority 1: Pre-Creation Similarity Check (HIGH)

### Summary
Implement vector similarity checking in Builder BEFORE creating nodes. This reduces GHOST node count, provides accurate mention counts, and improves UI experience.

### Files to Modify
- `backend/app/services/builder_service.py` - Main implementation
- `backend/app/services/similarity.py` - Already exists, minor updates
- `backend/app/config.py` - Add `similarity_check_enabled` flag

### Implementation Steps

1. **Update `builder_service.py`:**
   ```python
   async def _process(self, session_id, chunk, start):
       # ... existing LLM extraction ...
       
       # NEW: For each extracted node, check similarity before create
       label_to_node: Dict[str, Tuple[Node, bool]] = {}  # label -> (node, is_new)
       
       for extracted_node in agent_result.nodes:
           result = await run_similarity(
               session_id, 
               extracted_node.label, 
               chunk.start_time
           )
           
           if isinstance(result, SimilarityMatchResult):
               # Disambiguation check
               if self._types_compatible(extracted_node.inferred_type, result.node.inferred_type):
                   if extracted_node.confidence >= 0.7:
                       # MATCH: Use existing node
                       label_to_node[extracted_node.label] = (result.node, False)
                       continue
           
           # CREATE: New GHOST node
           extracted_node.embedding = result.embedding
           persisted = await create_node(session_id, extracted_node)
           label_to_node[extracted_node.label] = (persisted, True)
       
       # Create relationships using label mapping
       for rel in agent_result.relationships:
           source_node, _ = label_to_node.get(rel.source, (None, False))
           target_node, _ = label_to_node.get(rel.target, (None, False))
           if source_node and target_node:
               # Use actual node IDs
               rel.source_id = source_node.id
               rel.target_id = target_node.id
               await create_relationship(session_id, rel)
   ```

2. **Add disambiguation helper:**
   ```python
   def _types_compatible(self, type1: str, type2: str) -> bool:
       """Check if inferred types are compatible for merging."""
       if not type1 or not type2:
           return True  # Allow if either is missing
       
       # Exact match
       if type1.lower() == type2.lower():
           return True
       
       # Compatible groups (extend as needed)
       compatible_groups = [
           {"concept", "idea", "term", "topic"},
           {"person", "speaker", "author"},
           {"organisation", "company", "institution"},
           {"technology", "framework", "tool", "library"},
       ]
       
       type1_lower, type2_lower = type1.lower(), type2.lower()
       for group in compatible_groups:
           if type1_lower in group and type2_lower in group:
               return True
       
       return False
   ```

3. **Update SSE broadcasting:**
   ```python
   # For matched nodes (is_new=False):
   await sse_manager.broadcast(session_id, NodeUpdatedEvent(payload=node))
   
   # For new nodes (is_new=True):
   await sse_manager.broadcast(session_id, NodeAddedEvent(payload=node))
   ```

4. **Add config flag:**
   ```python
   # In config.py
   similarity_check_enabled: bool = Field(
       True, 
       description="Enable pre-creation similarity check in Builder"
   )
   ```

### Acceptance Criteria
- [ ] Duplicate entities in same chunk don't create duplicate GHOST nodes
- [ ] Mention counts increment in real-time for matched nodes
- [ ] Relationships point to correct (matched or new) node IDs
- [ ] Type compatibility prevents false matches (e.g., Apple company vs fruit)
- [ ] Fallback to creation if embedding fails

### Effort: Medium (2-3 hours)

---

## Priority 2: Expose original_text in TranscriptChunk (HIGH)

### Summary
The `original_text` field IS stored in Neo4j but not exposed in the model or API. Make it visible.

### Files to Modify
- `backend/app/models/chunk.py` - Add field to model
- `backend/app/services/graph_db.py` - Update `_chunk_from_value()`

### Implementation Steps

1. **Update model (`chunk.py`):**
   ```python
   class TranscriptChunk(BaseModel):
       id: str
       text: str
       original_text: Optional[str] = Field(
           None, 
           description="Original STT output before corrections (audit trail)"
       )
       start_time: float
       end_time: float
       session_id: str
   ```

2. **Update retrieval (`graph_db.py`):**
   ```python
   def _chunk_from_value(value: Neo4jNode) -> TranscriptChunk:
       props = dict(value)
       # Include original_text if present
       return TranscriptChunk.model_validate(props)
   ```

### Acceptance Criteria
- [ ] `original_text` visible in chunk retrieval
- [ ] Export endpoints include `original_text`
- [ ] Existing chunks without `original_text` work (field is optional)

### Effort: Small (30 minutes)

---

## Priority 3: Integrate ProofreadCheckpoint (HIGH)

### Summary
The checkpoint infrastructure exists but is not used. Integrate it to enable incremental proofreading.

### Files to Modify
- `backend/app/services/scheduler.py` - Add checkpoint usage
- `backend/app/services/graph_db.py` - Add `get_chunks_after()` helper

### Implementation Steps

1. **Add helper function (`graph_db.py`):**
   ```python
   async def get_chunks_after(
       session_id: str, 
       after_chunk_id: str, 
       limit: int = 10
   ) -> List[TranscriptChunk]:
       """Get chunks created after the given chunk ID."""
       driver = await get_driver()
       query = """
       MATCH (ref:TranscriptChunk {id: $after_chunk_id, session_id: $session_id})
       MATCH (c:TranscriptChunk {session_id: $session_id})
       WHERE c.start_time > ref.start_time
       RETURN c AS chunk
       ORDER BY c.start_time
       LIMIT $limit
       """
       # ... execute and return
   ```

2. **Update Gardener (`scheduler.py`):**
   ```python
   async def _run_gardener(self, session_id: str) -> None:
       # Get checkpoint
       checkpoint = await get_proofread_checkpoint(session_id)
       
       if checkpoint:
           chunks_to_proofread = await get_chunks_after(
               session_id, checkpoint, limit=10
           )
       else:
           # First run - get recent chunks
           chunks_to_proofread = await list_chunks_for_session(session_id)[-10:]
       
       # ... existing Gardener logic ...
       
       # After successful run, update checkpoint
       if chunks_to_proofread:
           await update_proofread_checkpoint(
               session_id, 
               chunks_to_proofread[-1].id
           )
   ```

### Acceptance Criteria
- [ ] Gardener processes only new chunks since last checkpoint
- [ ] Checkpoint persists across server restarts
- [ ] First Gardener cycle processes initial chunks
- [ ] Subsequent cycles skip already-proofread chunks

### Effort: Medium (1-2 hours)

---

## Priority 4: Add Session Context Persistence (HIGH)

### Summary
Store session theme and key entities to maintain context during incremental proofreading.

### Files to Modify
- `backend/app/models/vocabulary.py` - Add SessionContext model
- `backend/app/services/graph_db.py` - Add CRUD functions
- `backend/app/services/scheduler.py` - Use context in Gardener prompt

### Implementation Steps

1. **Add model (`vocabulary.py`):**
   ```python
   class SessionContext(BaseModel):
       session_id: str
       theme_summary: str = Field(
           "", 
           description="Brief description of session topic"
       )
       key_entities: list[str] = Field(
           default_factory=list,
           description="Important recurring entities"
       )
       speaker_names: list[str] = Field(
           default_factory=list,
           description="Identified speaker names"
       )
       domain_terms: list[str] = Field(
           default_factory=list,
           description="Domain-specific vocabulary"
       )
       updated_at: datetime = Field(default_factory=datetime.now)
   ```

2. **Add persistence (`graph_db.py`):**
   ```python
   async def get_session_context(session_id: str) -> Optional[SessionContext]:
       # Query SessionContext node
       
   async def update_session_context(session_id: str, context: SessionContext) -> None:
       # MERGE SessionContext node
   ```

3. **Update Gardener prompt:**
   ```python
   # In scheduler.py
   context = await get_session_context(session_id)
   if context:
       prompt_sections.append(f"""
       ## SESSION CONTEXT
       Theme: {context.theme_summary}
       Key Entities: {', '.join(context.key_entities)}
       Speakers: {', '.join(context.speaker_names)}
       """)
   ```

4. **Gardener extracts/updates context:**
   - During first few cycles, Gardener identifies theme and key entities
   - LLM returns context suggestions in response
   - Context persisted for subsequent cycles

### Acceptance Criteria
- [ ] Session context persisted in Neo4j
- [ ] Gardener prompt includes context when available
- [ ] Context updated as session progresses
- [ ] Incremental proofreading maintains consistent understanding

### Effort: Medium (1.5-2 hours)

---

## Priority 5: Configuration Updates (MEDIUM)

### Summary
Update configuration for production readiness and debugging capability.

### Files to Modify
- `backend/app/config.py`
- `backend/app/services/builder_service.py` - Check builder_enabled
- `backend/app/services/scheduler.py` - Check gardener_enabled

### Implementation Steps

1. **Reduce timeout:**
   ```python
   gemini_request_timeout: float = Field(
       90.0,  # Changed from 180.0
       ge=1.0,
       description="Seconds before a Gemini request is cancelled.",
   )
   ```

2. **Add agent enable flags:**
   ```python
   builder_enabled: bool = Field(
       True, 
       description="Enable Builder agent processing"
   )
   gardener_enabled: bool = Field(
       True, 
       description="Enable Gardener scheduling"
   )
   researcher_enabled: bool = Field(
       True, 
       description="Enable Researcher agent (Phase 3)"
   )
   librarian_enabled: bool = Field(
       True, 
       description="Enable Librarian Q&A (Phase E)"
   )
   similarity_check_enabled: bool = Field(
       True,
       description="Enable pre-creation similarity check in Builder"
   )
   ```

3. **Update agent startup to check flags:**
   ```python
   # In scheduler.py
   async def start(self) -> None:
       settings = get_settings()
       if not settings.gardener_enabled:
           logger.info("Gardener disabled via config")
           return
       # ... existing start logic
   ```

### Acceptance Criteria
- [ ] Timeout reduced to 90s
- [ ] Agent enable flags configurable via environment
- [ ] Agents check their flag before processing

### Effort: Small (30 minutes)

---

## Priority 5b: Gemini Config Helper Function (MEDIUM)

### Summary
Create a shared helper function that enforces Gemini 2.5 configuration patterns (thinking mode disabled, proper schema setup). This prevents future agents from accidentally omitting critical config.

### Files to Modify
- `backend/app/services/llm_utils.py` (new file)
- `backend/app/agents/builder.py` - Use helper
- `backend/app/agents/gardener.py` - Use helper

### Implementation Steps

1. **Create helper (`llm_utils.py`):**
   ```python
   from google.genai import types
   
   def create_gemini_config(
       response_schema: type,
       thinking_budget: int = 0,
   ) -> types.GenerateContentConfig:
       """
       Create Gemini config with correct defaults for structured output.
       
       CRITICAL: Gemini 2.5 has thinking mode ON by default, which adds
       60+ seconds to each call. This helper ensures it's disabled.
       """
       return types.GenerateContentConfig(
           response_mime_type="application/json",
           response_schema=response_schema,
           thinking_config=types.ThinkingConfig(thinking_budget=thinking_budget),
       )
   ```

2. **Update agents to use helper:**
   ```python
   # In builder.py / gardener.py
   from backend.app.services.llm_utils import create_gemini_config
   
   config = create_gemini_config(response_schema=BuilderResult)
   ```

### Acceptance Criteria
- [ ] Helper function enforces thinking_budget=0 by default
- [ ] Builder and Gardener agents use the helper
- [ ] Future agents can import and use consistently
- [ ] Docstring warns about the 60+ second issue

### Effort: Small (30 minutes)

---

## Priority 6: Add Relationship Context to Builder (MEDIUM)

### Summary
Include existing relationships in Builder prompt for better extraction context.

### Files to Modify
- `backend/app/agents/builder.py`

### Implementation Steps

1. **Update prompt rendering:**
   ```python
   def _render_prompt(chunk_text: str, nodes: Sequence[Node], relationships: Sequence[Relationship]) -> str:
       sections = [PROMPT_PREAMBLE]
       
       existing_nodes = _format_existing_nodes(nodes)
       if existing_nodes:
           sections.append("## EXISTING NODES")
           sections.append(existing_nodes)
       
       # NEW: Add relationship context
       existing_rels = _format_existing_relationships(relationships, nodes)
       if existing_rels:
           sections.append("## EXISTING RELATIONSHIPS")
           sections.append(existing_rels)
       
       sections.append("## TRANSCRIPT CHUNK")
       sections.append(chunk_text.strip())
       # ...
   
   def _format_existing_relationships(
       relationships: Sequence[Relationship], 
       nodes: Sequence[Node]
   ) -> str:
       # Map node IDs to labels
       id_to_label = {n.id: n.label for n in nodes}
       
       lines = []
       for rel in relationships[:20]:  # Limit to avoid prompt bloat
           source = id_to_label.get(rel.source_id, "?")
           target = id_to_label.get(rel.target_id, "?")
           lines.append(f"- {source} -> {target} [{rel.category.value}]")
       
       return "\n".join(lines) if lines else ""
   ```

2. **Update Builder service to pass relationships:**
   ```python
   # In builder_service.py
   existing_nodes = await list_nodes(session_id)
   existing_rels = await list_relationships(session_id)
   
   agent_result = await self._agent.build(
       chunk_text=chunk.text,
       chunk_timestamp=chunk.start_time,
       existing_nodes=existing_nodes,
       existing_relationships=existing_rels,  # NEW
   )
   ```

### Acceptance Criteria
- [ ] Builder prompt includes relationship context
- [ ] Relationship limit prevents prompt bloat
- [ ] Better extraction context improves node/relationship quality

### Effort: Small (45 minutes)

---

## Priority 7: Document Updates (MEDIUM)

### Summary
Update documentation to reflect all changes.

### Files to Update
- `_docs/ARCHITECTURE_ADVISORY.md` - Already updated in this session
- `_docs/_START_SESSION_STATE.md` - Update progress tracker
- `_docs/_dev/ADR/` - Create ADR for pre-creation similarity check

### New ADR Required
Create `_docs/_dev/ADR/0011-pre-creation-similarity-check.md`:
- Decision: Implement similarity check before node creation
- Rationale: Fewer duplicates, accurate counts, better UX
- Mitigations: Type matching, confidence threshold
- Consequences: +200-500ms latency, reduced Gardener workload

### Effort: Small (30 minutes)

---

## Implementation Order

Recommended sequence for implementation:

1. **Configuration Updates (Priority 5)** - Quick wins, enables debugging
2. **Gemini Config Helper (Priority 5b)** - Prevents future issues, quick win
3. **Expose original_text (Priority 2)** - Quick win, no dependencies
4. **Pre-Creation Similarity Check (Priority 1)** - Core improvement
5. **ProofreadCheckpoint Integration (Priority 3)** - Requires testing
6. **Session Context Persistence (Priority 4)** - Builds on checkpoint
7. **Relationship Context in Builder (Priority 6)** - Enhancement
8. **Document Updates (Priority 7)** - Capture all changes

---

## Testing Checklist

After implementation, verify:

- [ ] Submit chunk with duplicate entity mention - only one GHOST node created
- [ ] Mention count increments correctly for matched nodes
- [ ] Relationships point to correct node IDs after similarity matching
- [ ] "Apple" (company) doesn't match "apple" (fruit) if types differ
- [ ] Gardener processes only new chunks since last checkpoint
- [ ] Session context persists and appears in Gardener prompt
- [ ] Export includes `original_text` where available
- [ ] Agent enable flags work (disable Gardener, verify no processing)
- [ ] Timeout correctly set to 90s

---

## Summary

| Priority | Item | Effort | Impact |
|----------|------|--------|--------|
| 1 | Pre-creation similarity check + disambiguation | Medium | High |
| 2 | Expose original_text | Small | High |
| 3 | Integrate ProofreadCheckpoint | Medium | High |
| 4 | Session context persistence | Medium | High |
| 5 | Configuration updates | Small | Medium |
| 6 | Relationship context in Builder | Small | Medium |
| 7 | Documentation updates | Small | Medium |

**Total estimated effort:** 6-8 hours


```

```markdown
# Immediate Implementation Recommendations

**Date:** 30 December 2025  
**Source:** Architecture Review Session  
**Status:** Ready for Implementation  
**Estimated Total Effort:** 6-8 hours

---

## Overview

This document contains the agreed recommendations from the architecture review session, prioritised for immediate implementation. All items are derived from the comprehensive review in `architecture_review_2025-12-30.md`.

---

## Priority 1: Pre-Creation Similarity Check (HIGH)

### Summary
Implement vector similarity checking in Builder BEFORE creating nodes. This reduces GHOST node count, provides accurate mention counts, and improves UI experience.

### Files to Modify
- `backend/app/services/builder_service.py` - Main implementation
- `backend/app/services/similarity.py` - Already exists, minor updates
- `backend/app/config.py` - Add `similarity_check_enabled` flag

### Implementation Steps

1. **Update `builder_service.py`:**
   ```python
   async def _process(self, session_id, chunk, start):
       # ... existing LLM extraction ...
       
       # NEW: For each extracted node, check similarity before create
       label_to_node: Dict[str, Tuple[Node, bool]] = {}  # label -> (node, is_new)
       
       for extracted_node in agent_result.nodes:
           result = await run_similarity(
               session_id, 
               extracted_node.label, 
               chunk.start_time
           )
           
           if isinstance(result, SimilarityMatchResult):
               # Disambiguation check
               if self._types_compatible(extracted_node.inferred_type, result.node.inferred_type):
                   if extracted_node.confidence >= 0.7:
                       # MATCH: Use existing node
                       label_to_node[extracted_node.label] = (result.node, False)
                       continue
           
           # CREATE: New GHOST node
           extracted_node.embedding = result.embedding
           persisted = await create_node(session_id, extracted_node)
           label_to_node[extracted_node.label] = (persisted, True)
       
       # Create relationships using label mapping
       for rel in agent_result.relationships:
           source_node, _ = label_to_node.get(rel.source, (None, False))
           target_node, _ = label_to_node.get(rel.target, (None, False))
           if source_node and target_node:
               # Use actual node IDs
               rel.source_id = source_node.id
               rel.target_id = target_node.id
               await create_relationship(session_id, rel)
   ```

2. **Add disambiguation helper:**
   ```python
   def _types_compatible(self, type1: str, type2: str) -> bool:
       """Check if inferred types are compatible for merging."""
       if not type1 or not type2:
           return True  # Allow if either is missing
       
       # Exact match
       if type1.lower() == type2.lower():
           return True
       
       # Compatible groups (extend as needed)
       compatible_groups = [
           {"concept", "idea", "term", "topic"},
           {"person", "speaker", "author"},
           {"organisation", "company", "institution"},
           {"technology", "framework", "tool", "library"},
       ]
       
       type1_lower, type2_lower = type1.lower(), type2.lower()
       for group in compatible_groups:
           if type1_lower in group and type2_lower in group:
               return True
       
       return False
   ```

3. **Update SSE broadcasting:**
   ```python
   # For matched nodes (is_new=False):
   await sse_manager.broadcast(session_id, NodeUpdatedEvent(payload=node))
   
   # For new nodes (is_new=True):
   await sse_manager.broadcast(session_id, NodeAddedEvent(payload=node))
   ```

4. **Add config flag:**
   ```python
   # In config.py
   similarity_check_enabled: bool = Field(
       True, 
       description="Enable pre-creation similarity check in Builder"
   )
   ```

### Acceptance Criteria
- [ ] Duplicate entities in same chunk don't create duplicate GHOST nodes
- [ ] Mention counts increment in real-time for matched nodes
- [ ] Relationships point to correct (matched or new) node IDs
- [ ] Type compatibility prevents false matches (e.g., Apple company vs fruit)
- [ ] Fallback to creation if embedding fails

### Effort: Medium (2-3 hours)

---

## Priority 2: Expose original_text in TranscriptChunk (HIGH)

### Summary
The `original_text` field IS stored in Neo4j but not exposed in the model or API. Make it visible.

### Files to Modify
- `backend/app/models/chunk.py` - Add field to model
- `backend/app/services/graph_db.py` - Update `_chunk_from_value()`

### Implementation Steps

1. **Update model (`chunk.py`):**
   ```python
   class TranscriptChunk(BaseModel):
       id: str
       text: str
       original_text: Optional[str] = Field(
           None, 
           description="Original STT output before corrections (audit trail)"
       )
       start_time: float
       end_time: float
       session_id: str
   ```

2. **Update retrieval (`graph_db.py`):**
   ```python
   def _chunk_from_value(value: Neo4jNode) -> TranscriptChunk:
       props = dict(value)
       # Include original_text if present
       return TranscriptChunk.model_validate(props)
   ```

### Acceptance Criteria
- [ ] `original_text` visible in chunk retrieval
- [ ] Export endpoints include `original_text`
- [ ] Existing chunks without `original_text` work (field is optional)

### Effort: Small (30 minutes)

---

## Priority 3: Integrate ProofreadCheckpoint (HIGH)

### Summary
The checkpoint infrastructure exists but is not used. Integrate it to enable incremental proofreading.

### Files to Modify
- `backend/app/services/scheduler.py` - Add checkpoint usage
- `backend/app/services/graph_db.py` - Add `get_chunks_after()` helper

### Implementation Steps

1. **Add helper function (`graph_db.py`):**
   ```python
   async def get_chunks_after(
       session_id: str, 
       after_chunk_id: str, 
       limit: int = 10
   ) -> List[TranscriptChunk]:
       """Get chunks created after the given chunk ID."""
       driver = await get_driver()
       query = """
       MATCH (ref:TranscriptChunk {id: $after_chunk_id, session_id: $session_id})
       MATCH (c:TranscriptChunk {session_id: $session_id})
       WHERE c.start_time > ref.start_time
       RETURN c AS chunk
       ORDER BY c.start_time
       LIMIT $limit
       """
       # ... execute and return
   ```

2. **Update Gardener (`scheduler.py`):**
   ```python
   async def _run_gardener(self, session_id: str) -> None:
       # Get checkpoint
       checkpoint = await get_proofread_checkpoint(session_id)
       
       if checkpoint:
           chunks_to_proofread = await get_chunks_after(
               session_id, checkpoint, limit=10
           )
       else:
           # First run - get recent chunks
           chunks_to_proofread = await list_chunks_for_session(session_id)[-10:]
       
       # ... existing Gardener logic ...
       
       # After successful run, update checkpoint
       if chunks_to_proofread:
           await update_proofread_checkpoint(
               session_id, 
               chunks_to_proofread[-1].id
           )
   ```

### Acceptance Criteria
- [ ] Gardener processes only new chunks since last checkpoint
- [ ] Checkpoint persists across server restarts
- [ ] First Gardener cycle processes initial chunks
- [ ] Subsequent cycles skip already-proofread chunks

### Effort: Medium (1-2 hours)

---

## Priority 4: Add Session Context Persistence (HIGH)

### Summary
Store session theme and key entities to maintain context during incremental proofreading.

### Files to Modify
- `backend/app/models/vocabulary.py` - Add SessionContext model
- `backend/app/services/graph_db.py` - Add CRUD functions
- `backend/app/services/scheduler.py` - Use context in Gardener prompt

### Implementation Steps

1. **Add model (`vocabulary.py`):**
   ```python
   class SessionContext(BaseModel):
       session_id: str
       theme_summary: str = Field(
           "", 
           description="Brief description of session topic"
       )
       key_entities: list[str] = Field(
           default_factory=list,
           description="Important recurring entities"
       )
       speaker_names: list[str] = Field(
           default_factory=list,
           description="Identified speaker names"
       )
       domain_terms: list[str] = Field(
           default_factory=list,
           description="Domain-specific vocabulary"
       )
       updated_at: datetime = Field(default_factory=datetime.now)
   ```

2. **Add persistence (`graph_db.py`):**
   ```python
   async def get_session_context(session_id: str) -> Optional[SessionContext]:
       # Query SessionContext node
       
   async def update_session_context(session_id: str, context: SessionContext) -> None:
       # MERGE SessionContext node
   ```

3. **Update Gardener prompt:**
   ```python
   # In scheduler.py
   context = await get_session_context(session_id)
   if context:
       prompt_sections.append(f"""
       ## SESSION CONTEXT
       Theme: {context.theme_summary}
       Key Entities: {', '.join(context.key_entities)}
       Speakers: {', '.join(context.speaker_names)}
       """)
   ```

4. **Gardener extracts/updates context:**
   - During first few cycles, Gardener identifies theme and key entities
   - LLM returns context suggestions in response
   - Context persisted for subsequent cycles

### Acceptance Criteria
- [ ] Session context persisted in Neo4j
- [ ] Gardener prompt includes context when available
- [ ] Context updated as session progresses
- [ ] Incremental proofreading maintains consistent understanding

### Effort: Medium (1.5-2 hours)

---

## Priority 5: Configuration Updates (MEDIUM)

### Summary
Update configuration for production readiness and debugging capability.

### Files to Modify
- `backend/app/config.py`
- `backend/app/services/builder_service.py` - Check builder_enabled
- `backend/app/services/scheduler.py` - Check gardener_enabled

### Implementation Steps

1. **Reduce timeout:**
   ```python
   gemini_request_timeout: float = Field(
       90.0,  # Changed from 180.0
       ge=1.0,
       description="Seconds before a Gemini request is cancelled.",
   )
   ```

2. **Add agent enable flags:**
   ```python
   builder_enabled: bool = Field(
       True, 
       description="Enable Builder agent processing"
   )
   gardener_enabled: bool = Field(
       True, 
       description="Enable Gardener scheduling"
   )
   researcher_enabled: bool = Field(
       True, 
       description="Enable Researcher agent (Phase 3)"
   )
   librarian_enabled: bool = Field(
       True, 
       description="Enable Librarian Q&A (Phase E)"
   )
   similarity_check_enabled: bool = Field(
       True,
       description="Enable pre-creation similarity check in Builder"
   )
   ```

3. **Update agent startup to check flags:**
   ```python
   # In scheduler.py
   async def start(self) -> None:
       settings = get_settings()
       if not settings.gardener_enabled:
           logger.info("Gardener disabled via config")
           return
       # ... existing start logic
   ```

### Acceptance Criteria
- [ ] Timeout reduced to 90s
- [ ] Agent enable flags configurable via environment
- [ ] Agents check their flag before processing

### Effort: Small (30 minutes)

---

## Priority 5b: Gemini Config Helper Function (MEDIUM)

### Summary
Create a shared helper function that enforces Gemini 2.5 configuration patterns (thinking mode disabled, proper schema setup). This prevents future agents from accidentally omitting critical config.

### Files to Modify
- `backend/app/services/llm_utils.py` (new file)
- `backend/app/agents/builder.py` - Use helper
- `backend/app/agents/gardener.py` - Use helper

### Implementation Steps

1. **Create helper (`llm_utils.py`):**
   ```python
   from google.genai import types
   
   def create_gemini_config(
       response_schema: type,
       thinking_budget: int = 0,
   ) -> types.GenerateContentConfig:
       """
       Create Gemini config with correct defaults for structured output.
       
       CRITICAL: Gemini 2.5 has thinking mode ON by default, which adds
       60+ seconds to each call. This helper ensures it's disabled.
       """
       return types.GenerateContentConfig(
           response_mime_type="application/json",
           response_schema=response_schema,
           thinking_config=types.ThinkingConfig(thinking_budget=thinking_budget),
       )
   ```

2. **Update agents to use helper:**
   ```python
   # In builder.py / gardener.py
   from backend.app.services.llm_utils import create_gemini_config
   
   config = create_gemini_config(response_schema=BuilderResult)
   ```

### Acceptance Criteria
- [ ] Helper function enforces thinking_budget=0 by default
- [ ] Builder and Gardener agents use the helper
- [ ] Future agents can import and use consistently
- [ ] Docstring warns about the 60+ second issue

### Effort: Small (30 minutes)

---

## Priority 6: Add Relationship Context to Builder (MEDIUM)

### Summary
Include existing relationships in Builder prompt for better extraction context.

### Files to Modify
- `backend/app/agents/builder.py`

### Implementation Steps

1. **Update prompt rendering:**
   ```python
   def _render_prompt(chunk_text: str, nodes: Sequence[Node], relationships: Sequence[Relationship]) -> str:
       sections = [PROMPT_PREAMBLE]
       
       existing_nodes = _format_existing_nodes(nodes)
       if existing_nodes:
           sections.append("## EXISTING NODES")
           sections.append(existing_nodes)
       
       # NEW: Add relationship context
       existing_rels = _format_existing_relationships(relationships, nodes)
       if existing_rels:
           sections.append("## EXISTING RELATIONSHIPS")
           sections.append(existing_rels)
       
       sections.append("## TRANSCRIPT CHUNK")
       sections.append(chunk_text.strip())
       # ...
   
   def _format_existing_relationships(
       relationships: Sequence[Relationship], 
       nodes: Sequence[Node]
   ) -> str:
       # Map node IDs to labels
       id_to_label = {n.id: n.label for n in nodes}
       
       lines = []
       for rel in relationships[:20]:  # Limit to avoid prompt bloat
           source = id_to_label.get(rel.source_id, "?")
           target = id_to_label.get(rel.target_id, "?")
           lines.append(f"- {source} -> {target} [{rel.category.value}]")
       
       return "\n".join(lines) if lines else ""
   ```

2. **Update Builder service to pass relationships:**
   ```python
   # In builder_service.py
   existing_nodes = await list_nodes(session_id)
   existing_rels = await list_relationships(session_id)
   
   agent_result = await self._agent.build(
       chunk_text=chunk.text,
       chunk_timestamp=chunk.start_time,
       existing_nodes=existing_nodes,
       existing_relationships=existing_rels,  # NEW
   )
   ```

### Acceptance Criteria
- [ ] Builder prompt includes relationship context
- [ ] Relationship limit prevents prompt bloat
- [ ] Better extraction context improves node/relationship quality

### Effort: Small (45 minutes)

---

## Priority 7: Document Updates (MEDIUM)

### Summary
Update documentation to reflect all changes.

### Files to Update
- `_docs/ARCHITECTURE_ADVISORY.md` - Already updated in this session
- `_docs/_START_SESSION_STATE.md` - Update progress tracker
- `_docs/_dev/ADR/` - Create ADR for pre-creation similarity check

### New ADR Required
Create `_docs/_dev/ADR/0011-pre-creation-similarity-check.md`:
- Decision: Implement similarity check before node creation
- Rationale: Fewer duplicates, accurate counts, better UX
- Mitigations: Type matching, confidence threshold
- Consequences: +200-500ms latency, reduced Gardener workload

### Effort: Small (30 minutes)

---

## Implementation Order

Recommended sequence for implementation:

1. **Configuration Updates (Priority 5)** - Quick wins, enables debugging
2. **Gemini Config Helper (Priority 5b)** - Prevents future issues, quick win
3. **Expose original_text (Priority 2)** - Quick win, no dependencies
4. **Pre-Creation Similarity Check (Priority 1)** - Core improvement
5. **ProofreadCheckpoint Integration (Priority 3)** - Requires testing
6. **Session Context Persistence (Priority 4)** - Builds on checkpoint
7. **Relationship Context in Builder (Priority 6)** - Enhancement
8. **Document Updates (Priority 7)** - Capture all changes

---

## Testing Checklist

After implementation, verify:

- [ ] Submit chunk with duplicate entity mention - only one GHOST node created
- [ ] Mention count increments correctly for matched nodes
- [ ] Relationships point to correct node IDs after similarity matching
- [ ] "Apple" (company) doesn't match "apple" (fruit) if types differ
- [ ] Gardener processes only new chunks since last checkpoint
- [ ] Session context persists and appears in Gardener prompt
- [ ] Export includes `original_text` where available
- [ ] Agent enable flags work (disable Gardener, verify no processing)
- [ ] Timeout correctly set to 90s

---

## Summary

| Priority | Item | Effort | Impact |
|----------|------|--------|--------|
| 1 | Pre-creation similarity check + disambiguation | Medium | High |
| 2 | Expose original_text | Small | High |
| 3 | Integrate ProofreadCheckpoint | Medium | High |
| 4 | Session context persistence | Medium | High |
| 5 | Configuration updates | Small | Medium |
| 5b | Gemini config helper function | Small | Medium |
| 6 | Relationship context in Builder | Small | Medium |
| 7 | Documentation updates | Small | Medium |

**Total estimated effort:** 7-9 hours


```

```markdown
# Immediate Implementation Recommendations

**Date:** 30 December 2025  
**Source:** Architecture Review Session  
**Status:** Ready for Implementation  
**Estimated Total Effort:** 7-9 hours

---

## Overview

This document contains the agreed recommendations from the architecture review session, prioritised for immediate implementation. All items are derived from the comprehensive review in `architecture_review_2025-12-30.md`.

---

## Priority 1: Pre-Creation Similarity Check (HIGH)

### Summary
Implement vector similarity checking in Builder BEFORE creating nodes. This reduces GHOST node count, provides accurate mention counts, and improves UI experience.

### Files to Modify
- `backend/app/services/builder_service.py` - Main implementation
- `backend/app/services/similarity.py` - Already exists, minor updates
- `backend/app/config.py` - Add `similarity_check_enabled` flag

### Implementation Steps

1. **Update `builder_service.py`:**
   ```python
   async def _process(self, session_id, chunk, start):
       # ... existing LLM extraction ...
       
       # NEW: For each extracted node, check similarity before create
       label_to_node: Dict[str, Tuple[Node, bool]] = {}  # label -> (node, is_new)
       
       for extracted_node in agent_result.nodes:
           result = await run_similarity(
               session_id, 
               extracted_node.label, 
               chunk.start_time
           )
           
           if isinstance(result, SimilarityMatchResult):
               # Disambiguation check
               if self._types_compatible(extracted_node.inferred_type, result.node.inferred_type):
                   if extracted_node.confidence >= 0.7:
                       # MATCH: Use existing node
                       label_to_node[extracted_node.label] = (result.node, False)
                       continue
           
           # CREATE: New GHOST node
           extracted_node.embedding = result.embedding
           persisted = await create_node(session_id, extracted_node)
           label_to_node[extracted_node.label] = (persisted, True)
       
       # Create relationships using label mapping
       for rel in agent_result.relationships:
           source_node, _ = label_to_node.get(rel.source, (None, False))
           target_node, _ = label_to_node.get(rel.target, (None, False))
           if source_node and target_node:
               # Use actual node IDs
               rel.source_id = source_node.id
               rel.target_id = target_node.id
               await create_relationship(session_id, rel)
   ```

2. **Add disambiguation helper:**
   ```python
   def _types_compatible(self, type1: str, type2: str) -> bool:
       """Check if inferred types are compatible for merging."""
       if not type1 or not type2:
           return True  # Allow if either is missing
       
       # Exact match
       if type1.lower() == type2.lower():
           return True
       
       # Compatible groups (extend as needed)
       compatible_groups = [
           {"concept", "idea", "term", "topic"},
           {"person", "speaker", "author"},
           {"organisation", "company", "institution"},
           {"technology", "framework", "tool", "library"},
       ]
       
       type1_lower, type2_lower = type1.lower(), type2.lower()
       for group in compatible_groups:
           if type1_lower in group and type2_lower in group:
               return True
       
       return False
   ```

3. **Update SSE broadcasting:**
   ```python
   # For matched nodes (is_new=False):
   await sse_manager.broadcast(session_id, NodeUpdatedEvent(payload=node))
   
   # For new nodes (is_new=True):
   await sse_manager.broadcast(session_id, NodeAddedEvent(payload=node))
   ```

4. **Add config flag:**
   ```python
   # In config.py
   similarity_check_enabled: bool = Field(
       True, 
       description="Enable pre-creation similarity check in Builder"
   )
   ```

### Acceptance Criteria
- [ ] Duplicate entities in same chunk don't create duplicate GHOST nodes
- [ ] Mention counts increment in real-time for matched nodes
- [ ] Relationships point to correct (matched or new) node IDs
- [ ] Type compatibility prevents false matches (e.g., Apple company vs fruit)
- [ ] Fallback to creation if embedding fails

### Effort: Medium (2-3 hours)

---

## Priority 2: Expose original_text in TranscriptChunk (HIGH)

### Summary
The `original_text` field IS stored in Neo4j but not exposed in the model or API. Make it visible.

### Files to Modify
- `backend/app/models/chunk.py` - Add field to model
- `backend/app/services/graph_db.py` - Update `_chunk_from_value()`

### Implementation Steps

1. **Update model (`chunk.py`):**
   ```python
   class TranscriptChunk(BaseModel):
       id: str
       text: str
       original_text: Optional[str] = Field(
           None, 
           description="Original STT output before corrections (audit trail)"
       )
       start_time: float
       end_time: float
       session_id: str
   ```

2. **Update retrieval (`graph_db.py`):**
   ```python
   def _chunk_from_value(value: Neo4jNode) -> TranscriptChunk:
       props = dict(value)
       # Include original_text if present
       return TranscriptChunk.model_validate(props)
   ```

### Acceptance Criteria
- [ ] `original_text` visible in chunk retrieval
- [ ] Export endpoints include `original_text`
- [ ] Existing chunks without `original_text` work (field is optional)

### Effort: Small (30 minutes)

---

## Priority 3: Integrate ProofreadCheckpoint (HIGH)

### Summary
The checkpoint infrastructure exists but is not used. Integrate it to enable incremental proofreading.

### Files to Modify
- `backend/app/services/scheduler.py` - Add checkpoint usage
- `backend/app/services/graph_db.py` - Add `get_chunks_after()` helper

### Implementation Steps

1. **Add helper function (`graph_db.py`):**
   ```python
   async def get_chunks_after(
       session_id: str, 
       after_chunk_id: str, 
       limit: int = 10
   ) -> List[TranscriptChunk]:
       """Get chunks created after the given chunk ID."""
       driver = await get_driver()
       query = """
       MATCH (ref:TranscriptChunk {id: $after_chunk_id, session_id: $session_id})
       MATCH (c:TranscriptChunk {session_id: $session_id})
       WHERE c.start_time > ref.start_time
       RETURN c AS chunk
       ORDER BY c.start_time
       LIMIT $limit
       """
       # ... execute and return
   ```

2. **Update Gardener (`scheduler.py`):**
   ```python
   async def _run_gardener(self, session_id: str) -> None:
       # Get checkpoint
       checkpoint = await get_proofread_checkpoint(session_id)
       
       if checkpoint:
           chunks_to_proofread = await get_chunks_after(
               session_id, checkpoint, limit=10
           )
       else:
           # First run - get recent chunks
           chunks_to_proofread = await list_chunks_for_session(session_id)[-10:]
       
       # ... existing Gardener logic ...
       
       # After successful run, update checkpoint
       if chunks_to_proofread:
           await update_proofread_checkpoint(
               session_id, 
               chunks_to_proofread[-1].id
           )
   ```

### Acceptance Criteria
- [ ] Gardener processes only new chunks since last checkpoint
- [ ] Checkpoint persists across server restarts
- [ ] First Gardener cycle processes initial chunks
- [ ] Subsequent cycles skip already-proofread chunks

### Effort: Medium (1-2 hours)

---

## Priority 4: Add Session Context Persistence (HIGH)

### Summary
Store session theme and key entities to maintain context during incremental proofreading.

### Files to Modify
- `backend/app/models/vocabulary.py` - Add SessionContext model
- `backend/app/services/graph_db.py` - Add CRUD functions
- `backend/app/services/scheduler.py` - Use context in Gardener prompt

### Implementation Steps

1. **Add model (`vocabulary.py`):**
   ```python
   class SessionContext(BaseModel):
       session_id: str
       theme_summary: str = Field(
           "", 
           description="Brief description of session topic"
       )
       key_entities: list[str] = Field(
           default_factory=list,
           description="Important recurring entities"
       )
       speaker_names: list[str] = Field(
           default_factory=list,
           description="Identified speaker names"
       )
       domain_terms: list[str] = Field(
           default_factory=list,
           description="Domain-specific vocabulary"
       )
       updated_at: datetime = Field(default_factory=datetime.now)
   ```

2. **Add persistence (`graph_db.py`):**
   ```python
   async def get_session_context(session_id: str) -> Optional[SessionContext]:
       # Query SessionContext node
       
   async def update_session_context(session_id: str, context: SessionContext) -> None:
       # MERGE SessionContext node
   ```

3. **Update Gardener prompt:**
   ```python
   # In scheduler.py
   context = await get_session_context(session_id)
   if context:
       prompt_sections.append(f"""
       ## SESSION CONTEXT
       Theme: {context.theme_summary}
       Key Entities: {', '.join(context.key_entities)}
       Speakers: {', '.join(context.speaker_names)}
       """)
   ```

4. **Gardener extracts/updates context:**
   - During first few cycles, Gardener identifies theme and key entities
   - LLM returns context suggestions in response
   - Context persisted for subsequent cycles

### Acceptance Criteria
- [ ] Session context persisted in Neo4j
- [ ] Gardener prompt includes context when available
- [ ] Context updated as session progresses
- [ ] Incremental proofreading maintains consistent understanding

### Effort: Medium (1.5-2 hours)

---

## Priority 5: Configuration Updates (MEDIUM)

### Summary
Update configuration for production readiness and debugging capability.

### Files to Modify
- `backend/app/config.py`
- `backend/app/services/builder_service.py` - Check builder_enabled
- `backend/app/services/scheduler.py` - Check gardener_enabled

### Implementation Steps

1. **Reduce timeout:**
   ```python
   gemini_request_timeout: float = Field(
       90.0,  # Changed from 180.0
       ge=1.0,
       description="Seconds before a Gemini request is cancelled.",
   )
   ```

2. **Add agent enable flags:**
   ```python
   builder_enabled: bool = Field(
       True, 
       description="Enable Builder agent processing"
   )
   gardener_enabled: bool = Field(
       True, 
       description="Enable Gardener scheduling"
   )
   researcher_enabled: bool = Field(
       True, 
       description="Enable Researcher agent (Phase 3)"
   )
   librarian_enabled: bool = Field(
       True, 
       description="Enable Librarian Q&A (Phase E)"
   )
   similarity_check_enabled: bool = Field(
       True,
       description="Enable pre-creation similarity check in Builder"
   )
   ```

3. **Update agent startup to check flags:**
   ```python
   # In scheduler.py
   async def start(self) -> None:
       settings = get_settings()
       if not settings.gardener_enabled:
           logger.info("Gardener disabled via config")
           return
       # ... existing start logic
   ```

### Acceptance Criteria
- [ ] Timeout reduced to 90s
- [ ] Agent enable flags configurable via environment
- [ ] Agents check their flag before processing

### Effort: Small (30 minutes)

---

## Priority 5b: Gemini Config Helper Function (MEDIUM)

### Summary
Create a shared helper function that enforces Gemini 2.5 configuration patterns (thinking mode disabled, proper schema setup). This prevents future agents from accidentally omitting critical config.

### Files to Modify
- `backend/app/services/llm_utils.py` (new file)
- `backend/app/agents/builder.py` - Use helper
- `backend/app/agents/gardener.py` - Use helper

### Implementation Steps

1. **Create helper (`llm_utils.py`):**
   ```python
   from google.genai import types
   
   def create_gemini_config(
       response_schema: type,
       thinking_budget: int = 0,
   ) -> types.GenerateContentConfig:
       """
       Create Gemini config with correct defaults for structured output.
       
       CRITICAL: Gemini 2.5 has thinking mode ON by default, which adds
       60+ seconds to each call. This helper ensures it's disabled.
       """
       return types.GenerateContentConfig(
           response_mime_type="application/json",
           response_schema=response_schema,
           thinking_config=types.ThinkingConfig(thinking_budget=thinking_budget),
       )
   ```

2. **Update agents to use helper:**
   ```python
   # In builder.py / gardener.py
   from backend.app.services.llm_utils import create_gemini_config
   
   config = create_gemini_config(response_schema=BuilderResult)
   ```

### Acceptance Criteria
- [ ] Helper function enforces thinking_budget=0 by default
- [ ] Builder and Gardener agents use the helper
- [ ] Future agents can import and use consistently
- [ ] Docstring warns about the 60+ second issue

### Effort: Small (30 minutes)

---

## Priority 6: Add Relationship Context to Builder (MEDIUM)

### Summary
Include existing relationships in Builder prompt for better extraction context.

### Files to Modify
- `backend/app/agents/builder.py`

### Implementation Steps

1. **Update prompt rendering:**
   ```python
   def _render_prompt(chunk_text: str, nodes: Sequence[Node], relationships: Sequence[Relationship]) -> str:
       sections = [PROMPT_PREAMBLE]
       
       existing_nodes = _format_existing_nodes(nodes)
       if existing_nodes:
           sections.append("## EXISTING NODES")
           sections.append(existing_nodes)
       
       # NEW: Add relationship context
       existing_rels = _format_existing_relationships(relationships, nodes)
       if existing_rels:
           sections.append("## EXISTING RELATIONSHIPS")
           sections.append(existing_rels)
       
       sections.append("## TRANSCRIPT CHUNK")
       sections.append(chunk_text.strip())
       # ...
   
   def _format_existing_relationships(
       relationships: Sequence[Relationship], 
       nodes: Sequence[Node]
   ) -> str:
       # Map node IDs to labels
       id_to_label = {n.id: n.label for n in nodes}
       
       lines = []
       for rel in relationships[:20]:  # Limit to avoid prompt bloat
           source = id_to_label.get(rel.source_id, "?")
           target = id_to_label.get(rel.target_id, "?")
           lines.append(f"- {source} -> {target} [{rel.category.value}]")
       
       return "\n".join(lines) if lines else ""
   ```

2. **Update Builder service to pass relationships:**
   ```python
   # In builder_service.py
   existing_nodes = await list_nodes(session_id)
   existing_rels = await list_relationships(session_id)
   
   agent_result = await self._agent.build(
       chunk_text=chunk.text,
       chunk_timestamp=chunk.start_time,
       existing_nodes=existing_nodes,
       existing_relationships=existing_rels,  # NEW
   )
   ```

### Acceptance Criteria
- [ ] Builder prompt includes relationship context
- [ ] Relationship limit prevents prompt bloat
- [ ] Better extraction context improves node/relationship quality

### Effort: Small (45 minutes)

---

## Priority 7: Document Updates (MEDIUM)

### Summary
Update documentation to reflect all changes.

### Files to Update
- `_docs/ARCHITECTURE_ADVISORY.md` - Already updated in this session
- `_docs/_START_SESSION_STATE.md` - Update progress tracker
- `_docs/_dev/ADR/` - Create ADR for pre-creation similarity check

### New ADR Required
Create `_docs/_dev/ADR/0011-pre-creation-similarity-check.md`:
- Decision: Implement similarity check before node creation
- Rationale: Fewer duplicates, accurate counts, better UX
- Mitigations: Type matching, confidence threshold
- Consequences: +200-500ms latency, reduced Gardener workload

### Effort: Small (30 minutes)

---

## Implementation Order

Recommended sequence for implementation:

1. **Configuration Updates (Priority 5)** - Quick wins, enables debugging
2. **Gemini Config Helper (Priority 5b)** - Prevents future issues, quick win
3. **Expose original_text (Priority 2)** - Quick win, no dependencies
4. **Pre-Creation Similarity Check (Priority 1)** - Core improvement
5. **ProofreadCheckpoint Integration (Priority 3)** - Requires testing
6. **Session Context Persistence (Priority 4)** - Builds on checkpoint
7. **Relationship Context in Builder (Priority 6)** - Enhancement
8. **Document Updates (Priority 7)** - Capture all changes

---

## Testing Checklist

After implementation, verify:

- [ ] Submit chunk with duplicate entity mention - only one GHOST node created
- [ ] Mention count increments correctly for matched nodes
- [ ] Relationships point to correct node IDs after similarity matching
- [ ] "Apple" (company) doesn't match "apple" (fruit) if types differ
- [ ] Gardener processes only new chunks since last checkpoint
- [ ] Session context persists and appears in Gardener prompt
- [ ] Export includes `original_text` where available
- [ ] Agent enable flags work (disable Gardener, verify no processing)
- [ ] Timeout correctly set to 90s

---

## Summary

| Priority | Item | Effort | Impact |
|----------|------|--------|--------|
| 1 | Pre-creation similarity check + disambiguation | Medium | High |
| 2 | Expose original_text | Small | High |
| 3 | Integrate ProofreadCheckpoint | Medium | High |
| 4 | Session context persistence | Medium | High |
| 5 | Configuration updates | Small | Medium |
| 5b | Gemini config helper function | Small | Medium |
| 6 | Relationship context in Builder | Small | Medium |
| 7 | Documentation updates | Small | Medium |

**Total estimated effort:** 7-9 hours


```

```markdown
# Immediate Implementation Recommendations

**Date:** 30 December 2025  
**Source:** Architecture Review Session  
**Status:** Ready for Implementation  
**Estimated Total Effort:** 7-9 hours

---

## Overview

This document contains the agreed recommendations from the architecture review session, prioritised for immediate implementation. All items are derived from the comprehensive review in `architecture_review_2025-12-30.md`.

---

## Priority 1: Pre-Creation Similarity Check (HIGH)

### Summary
Implement vector similarity checking in Builder BEFORE creating nodes. This reduces GHOST node count, provides accurate mention counts, and improves UI experience.

### Files to Modify
- `backend/app/services/builder_service.py` - Main implementation
- `backend/app/services/similarity.py` - Already exists, minor updates
- `backend/app/config.py` - Add `similarity_check_enabled` flag

### Implementation Steps

1. **Update `builder_service.py`:**
   ```python
   async def _process(self, session_id, chunk, start):
       # ... existing LLM extraction ...
       
       # NEW: For each extracted node, check similarity before create
       label_to_node: Dict[str, Tuple[Node, bool]] = {}  # label -> (node, is_new)
       
       for extracted_node in agent_result.nodes:
           result = await run_similarity(
               session_id, 
               extracted_node.label, 
               chunk.start_time
           )
           
           if isinstance(result, SimilarityMatchResult):
               # Disambiguation check
               if self._types_compatible(extracted_node.inferred_type, result.node.inferred_type):
                   if extracted_node.confidence >= 0.7:
                       # MATCH: Use existing node
                       label_to_node[extracted_node.label] = (result.node, False)
                       continue
           
           # CREATE: New GHOST node
           extracted_node.embedding = result.embedding
           persisted = await create_node(session_id, extracted_node)
           label_to_node[extracted_node.label] = (persisted, True)
       
       # Create relationships using label mapping
       for rel in agent_result.relationships:
           source_node, _ = label_to_node.get(rel.source, (None, False))
           target_node, _ = label_to_node.get(rel.target, (None, False))
           if source_node and target_node:
               # Use actual node IDs
               rel.source_id = source_node.id
               rel.target_id = target_node.id
               await create_relationship(session_id, rel)
   ```

2. **Add disambiguation helper:**
   ```python
   def _types_compatible(self, type1: str, type2: str) -> bool:
       """Check if inferred types are compatible for merging."""
       if not type1 or not type2:
           return True  # Allow if either is missing
       
       # Exact match
       if type1.lower() == type2.lower():
           return True
       
       # Compatible groups (extend as needed)
       compatible_groups = [
           {"concept", "idea", "term", "topic"},
           {"person", "speaker", "author"},
           {"organisation", "company", "institution"},
           {"technology", "framework", "tool", "library"},
       ]
       
       type1_lower, type2_lower = type1.lower(), type2.lower()
       for group in compatible_groups:
           if type1_lower in group and type2_lower in group:
               return True
       
       return False
   ```

3. **Update SSE broadcasting:**
   ```python
   # For matched nodes (is_new=False):
   await sse_manager.broadcast(session_id, NodeUpdatedEvent(payload=node))
   
   # For new nodes (is_new=True):
   await sse_manager.broadcast(session_id, NodeAddedEvent(payload=node))
   ```

4. **Add config flag:**
   ```python
   # In config.py
   similarity_check_enabled: bool = Field(
       True, 
       description="Enable pre-creation similarity check in Builder"
   )
   ```

### Acceptance Criteria
- [ ] Duplicate entities in same chunk don't create duplicate GHOST nodes
- [ ] Mention counts increment in real-time for matched nodes
- [ ] Relationships point to correct (matched or new) node IDs
- [ ] Type compatibility prevents false matches (e.g., Apple company vs fruit)
- [ ] Fallback to creation if embedding fails

### Effort: Medium (2-3 hours)

---

## Priority 2: Expose original_text in TranscriptChunk (HIGH)

### Summary
The `original_text` field IS stored in Neo4j but not exposed in the model or API. Make it visible.

### Files to Modify
- `backend/app/models/chunk.py` - Add field to model
- `backend/app/services/graph_db.py` - Update `_chunk_from_value()`

### Implementation Steps

1. **Update model (`chunk.py`):**
   ```python
   class TranscriptChunk(BaseModel):
       id: str
       text: str
       original_text: Optional[str] = Field(
           None, 
           description="Original STT output before corrections (audit trail)"
       )
       start_time: float
       end_time: float
       session_id: str
   ```

2. **Update retrieval (`graph_db.py`):**
   ```python
   def _chunk_from_value(value: Neo4jNode) -> TranscriptChunk:
       props = dict(value)
       # Include original_text if present
       return TranscriptChunk.model_validate(props)
   ```

### Acceptance Criteria
- [ ] `original_text` visible in chunk retrieval
- [ ] Export endpoints include `original_text`
- [ ] Existing chunks without `original_text` work (field is optional)

### Effort: Small (30 minutes)

---

## Priority 3: Integrate ProofreadCheckpoint (HIGH)

### Summary
The checkpoint infrastructure exists but is not used. Integrate it to enable incremental proofreading.

### Files to Modify
- `backend/app/services/scheduler.py` - Add checkpoint usage
- `backend/app/services/graph_db.py` - Add `get_chunks_after()` helper

### Implementation Steps

1. **Add helper function (`graph_db.py`):**
   ```python
   async def get_chunks_after(
       session_id: str, 
       after_chunk_id: str, 
       limit: int = 10
   ) -> List[TranscriptChunk]:
       """Get chunks created after the given chunk ID."""
       driver = await get_driver()
       query = """
       MATCH (ref:TranscriptChunk {id: $after_chunk_id, session_id: $session_id})
       MATCH (c:TranscriptChunk {session_id: $session_id})
       WHERE c.start_time > ref.start_time
       RETURN c AS chunk
       ORDER BY c.start_time
       LIMIT $limit
       """
       # ... execute and return
   ```

2. **Update Gardener (`scheduler.py`):**
   ```python
   async def _run_gardener(self, session_id: str) -> None:
       # Get checkpoint
       checkpoint = await get_proofread_checkpoint(session_id)
       
       if checkpoint:
           chunks_to_proofread = await get_chunks_after(
               session_id, checkpoint, limit=10
           )
       else:
           # First run - get recent chunks
           chunks_to_proofread = await list_chunks_for_session(session_id)[-10:]
       
       # ... existing Gardener logic ...
       
       # After successful run, update checkpoint
       if chunks_to_proofread:
           await update_proofread_checkpoint(
               session_id, 
               chunks_to_proofread[-1].id
           )
   ```

### Acceptance Criteria
- [ ] Gardener processes only new chunks since last checkpoint
- [ ] Checkpoint persists across server restarts
- [ ] First Gardener cycle processes initial chunks
- [ ] Subsequent cycles skip already-proofread chunks

### Effort: Medium (1-2 hours)

---

## Priority 4: Add Session Context Persistence (HIGH)

### Summary
Store session theme and key entities to maintain context during incremental proofreading.

### Files to Modify
- `backend/app/models/vocabulary.py` - Add SessionContext model
- `backend/app/services/graph_db.py` - Add CRUD functions
- `backend/app/services/scheduler.py` - Use context in Gardener prompt

### Implementation Steps

1. **Add model (`vocabulary.py`):**
   ```python
   class SessionContext(BaseModel):
       session_id: str
       theme_summary: str = Field(
           "", 
           description="Brief description of session topic"
       )
       key_entities: list[str] = Field(
           default_factory=list,
           description="Important recurring entities"
       )
       speaker_names: list[str] = Field(
           default_factory=list,
           description="Identified speaker names"
       )
       domain_terms: list[str] = Field(
           default_factory=list,
           description="Domain-specific vocabulary"
       )
       updated_at: datetime = Field(default_factory=datetime.now)
   ```

2. **Add persistence (`graph_db.py`):**
   ```python
   async def get_session_context(session_id: str) -> Optional[SessionContext]:
       # Query SessionContext node
       
   async def update_session_context(session_id: str, context: SessionContext) -> None:
       # MERGE SessionContext node
   ```

3. **Update Gardener prompt:**
   ```python
   # In scheduler.py
   context = await get_session_context(session_id)
   if context:
       prompt_sections.append(f"""
       ## SESSION CONTEXT
       Theme: {context.theme_summary}
       Key Entities: {', '.join(context.key_entities)}
       Speakers: {', '.join(context.speaker_names)}
       """)
   ```

4. **Gardener extracts/updates context:**
   - During first few cycles, Gardener identifies theme and key entities
   - LLM returns context suggestions in response
   - Context persisted for subsequent cycles

### Acceptance Criteria
- [ ] Session context persisted in Neo4j
- [ ] Gardener prompt includes context when available
- [ ] Context updated as session progresses
- [ ] Incremental proofreading maintains consistent understanding

### Effort: Medium (1.5-2 hours)

---

## Priority 5: Configuration Updates (MEDIUM)

### Summary
Update configuration for production readiness and debugging capability.

### Files to Modify
- `backend/app/config.py`
- `backend/app/services/builder_service.py` - Check builder_enabled
- `backend/app/services/scheduler.py` - Check gardener_enabled

### Implementation Steps

1. **Reduce timeout:**
   ```python
   gemini_request_timeout: float = Field(
       90.0,  # Changed from 180.0
       ge=1.0,
       description="Seconds before a Gemini request is cancelled.",
   )
   ```

2. **Add agent enable flags:**
   ```python
   builder_enabled: bool = Field(
       True, 
       description="Enable Builder agent processing"
   )
   gardener_enabled: bool = Field(
       True, 
       description="Enable Gardener scheduling"
   )
   researcher_enabled: bool = Field(
       True, 
       description="Enable Researcher agent (Phase 3)"
   )
   librarian_enabled: bool = Field(
       True, 
       description="Enable Librarian Q&A (Phase E)"
   )
   similarity_check_enabled: bool = Field(
       True,
       description="Enable pre-creation similarity check in Builder"
   )
   ```

3. **Update agent startup to check flags:**
   ```python
   # In scheduler.py
   async def start(self) -> None:
       settings = get_settings()
       if not settings.gardener_enabled:
           logger.info("Gardener disabled via config")
           return
       # ... existing start logic
   ```

### Acceptance Criteria
- [ ] Timeout reduced to 90s
- [ ] Agent enable flags configurable via environment
- [ ] Agents check their flag before processing

### Effort: Small (30 minutes)

---

## Priority 5b: Gemini Config Helper Function (MEDIUM)

### Summary
Create a shared helper function that enforces Gemini 2.5 configuration patterns (thinking mode disabled, proper schema setup). This prevents future agents from accidentally omitting critical config.

### Files to Modify
- `backend/app/services/llm_utils.py` (new file)
- `backend/app/agents/builder.py` - Use helper
- `backend/app/agents/gardener.py` - Use helper

### Implementation Steps

1. **Create helper (`llm_utils.py`):**
   ```python
   from google.genai import types
   
   def create_gemini_config(
       response_schema: type,
       thinking_budget: int = 0,
   ) -> types.GenerateContentConfig:
       """
       Create Gemini config with correct defaults for structured output.
       
       CRITICAL: Gemini 2.5 has thinking mode ON by default, which adds
       60+ seconds to each call. This helper ensures it's disabled.
       """
       return types.GenerateContentConfig(
           response_mime_type="application/json",
           response_schema=response_schema,
           thinking_config=types.ThinkingConfig(thinking_budget=thinking_budget),
       )
   ```

2. **Update agents to use helper:**
   ```python
   # In builder.py / gardener.py
   from backend.app.services.llm_utils import create_gemini_config
   
   config = create_gemini_config(response_schema=BuilderResult)
   ```

### Acceptance Criteria
- [ ] Helper function enforces thinking_budget=0 by default
- [ ] Builder and Gardener agents use the helper
- [ ] Future agents can import and use consistently
- [ ] Docstring warns about the 60+ second issue

### Effort: Small (30 minutes)

---

## Priority 6: Add Relationship Context to Builder (MEDIUM)

### Summary
Include existing relationships in Builder prompt for better extraction context.

### Files to Modify
- `backend/app/agents/builder.py`

### Implementation Steps

1. **Update prompt rendering:**
   ```python
   def _render_prompt(chunk_text: str, nodes: Sequence[Node], relationships: Sequence[Relationship]) -> str:
       sections = [PROMPT_PREAMBLE]
       
       existing_nodes = _format_existing_nodes(nodes)
       if existing_nodes:
           sections.append("## EXISTING NODES")
           sections.append(existing_nodes)
       
       # NEW: Add relationship context
       existing_rels = _format_existing_relationships(relationships, nodes)
       if existing_rels:
           sections.append("## EXISTING RELATIONSHIPS")
           sections.append(existing_rels)
       
       sections.append("## TRANSCRIPT CHUNK")
       sections.append(chunk_text.strip())
       # ...
   
   def _format_existing_relationships(
       relationships: Sequence[Relationship], 
       nodes: Sequence[Node]
   ) -> str:
       # Map node IDs to labels
       id_to_label = {n.id: n.label for n in nodes}
       
       lines = []
       for rel in relationships[:20]:  # Limit to avoid prompt bloat
           source = id_to_label.get(rel.source_id, "?")
           target = id_to_label.get(rel.target_id, "?")
           lines.append(f"- {source} -> {target} [{rel.category.value}]")
       
       return "\n".join(lines) if lines else ""
   ```

2. **Update Builder service to pass relationships:**
   ```python
   # In builder_service.py
   existing_nodes = await list_nodes(session_id)
   existing_rels = await list_relationships(session_id)
   
   agent_result = await self._agent.build(
       chunk_text=chunk.text,
       chunk_timestamp=chunk.start_time,
       existing_nodes=existing_nodes,
       existing_relationships=existing_rels,  # NEW
   )
   ```

### Acceptance Criteria
- [ ] Builder prompt includes relationship context
- [ ] Relationship limit prevents prompt bloat
- [ ] Better extraction context improves node/relationship quality

### Effort: Small (45 minutes)

---

## Priority 7: Document Updates (MEDIUM)

### Summary
Update documentation to reflect all changes.

### Files to Update
- `_docs/ARCHITECTURE_ADVISORY.md` - Already updated in this session
- `_docs/_START_SESSION_STATE.md` - Update progress tracker
- `_docs/_dev/ADR/` - Create ADR for pre-creation similarity check

### New ADR Required
Create `_docs/_dev/ADR/0011-pre-creation-similarity-check.md`:
- Decision: Implement similarity check before node creation
- Rationale: Fewer duplicates, accurate counts, better UX
- Mitigations: Type matching, confidence threshold
- Consequences: +200-500ms latency, reduced Gardener workload

### Effort: Small (30 minutes)

---

## Implementation Order

Recommended sequence for implementation:

1. **Configuration Updates (Priority 5)** - Quick wins, enables debugging
2. **Gemini Config Helper (Priority 5b)** - Prevents future issues, quick win
3. **Expose original_text (Priority 2)** - Quick win, no dependencies
4. **Pre-Creation Similarity Check (Priority 1)** - Core improvement
5. **ProofreadCheckpoint Integration (Priority 3)** - Requires testing
6. **Session Context Persistence (Priority 4)** - Builds on checkpoint
7. **Relationship Context in Builder (Priority 6)** - Enhancement
8. **Document Updates (Priority 7)** - Capture all changes

---

## Testing Checklist

After implementation, verify:

- [ ] Submit chunk with duplicate entity mention - only one GHOST node created
- [ ] Mention count increments correctly for matched nodes
- [ ] Relationships point to correct node IDs after similarity matching
- [ ] "Apple" (company) doesn't match "apple" (fruit) if types differ
- [ ] Gardener processes only new chunks since last checkpoint
- [ ] Session context persists and appears in Gardener prompt
- [ ] Export includes `original_text` where available
- [ ] Agent enable flags work (disable Gardener, verify no processing)
- [ ] Timeout correctly set to 90s
- [ ] Gemini helper function used by Builder and Gardener (thinking_budget=0)

---

## Summary

| Priority | Item | Effort | Impact |
|----------|------|--------|--------|
| 1 | Pre-creation similarity check + disambiguation | Medium | High |
| 2 | Expose original_text | Small | High |
| 3 | Integrate ProofreadCheckpoint | Medium | High |
| 4 | Session context persistence | Medium | High |
| 5 | Configuration updates | Small | Medium |
| 5b | Gemini config helper function | Small | Medium |
| 6 | Relationship context in Builder | Small | Medium |
| 7 | Documentation updates | Small | Medium |

**Total estimated effort:** 7-9 hours


```

Let me do a final verification of the key sections in both updated files:

---

## Final Check Complete - Updates Summary

### ARCHITECTURE_ADVISORY.md

| Change | Line | Before | After |
|--------|------|--------|-------|
| Conflict table fix | 586 | "Builder re-checks after MERGE" | "Builder re-checks label before persist" |

### IMMEDIATE_RECOMMENDATIONS.md

| Change | Description |
|--------|-------------|
| Added Priority 5b | Gemini Config Helper Function - shared helper enforcing `thinking_budget=0` |
| Updated Implementation Order | Added step 2 for Gemini helper (8 steps total) |
| Updated Testing Checklist | Added Gemini helper verification item |
| Updated Summary Table | Added Priority 5b row |
| Updated Effort Estimate | 6-8 hours -> 7-9 hours |

---

## Final State: Priority Items

| Priority | Item | Effort | Status |
|----------|------|--------|--------|
| 1 | Pre-creation similarity check + disambiguation | Medium | In Plan |
| 2 | Expose original_text | Small | In Plan |
| 3 | Integrate ProofreadCheckpoint | Medium | In Plan |
| 4 | Session context persistence | Medium | In Plan |
| 5 | Configuration updates (timeout, agent flags) | Small | In Plan |
| 5b | Gemini config helper function | Small | **Added** |
| 6 | Relationship context in Builder | Small | In Plan |
| 7 | Documentation updates (ADR for similarity) | Small | In Plan |

---

## Verification Complete

- ARCHITECTURE_ADVISORY.md: v8.2, correctly reflects MATCH pattern, thinking mode config, ADRs 001-010
- IMMEDIATE_RECOMMENDATIONS.md: 8 priorities, 7-9 hours total, testing checklist updated
- Both documents aligned with dev team updates and review findings

**Ready for implementation phase.**

---

**User**

Create Plan


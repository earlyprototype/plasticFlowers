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


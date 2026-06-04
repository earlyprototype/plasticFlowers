# Development Plan: Chunk Persistence & Gardener Context

## 1. Executive Summary
**Objective:** Instantiate persistent storage for transcript chunks and wire retrieval into the Gardener agent's context window.
**Priority:** Critical (Required for Gate 7 MVP Feature Completeness).

### Reason for Need
Currently, the Gardener agent operates **statelessly** regarding the spoken transcript. It receives the current graph structure (Nodes/Edges) but has **zero access** to the actual text spoken by the user in the last few minutes.

**Consequences of Current State:**
*   **Context Blindness:** The Gardener cannot verify if a "Ghost Node" is valid by checking the source text.
*   **Disambiguation Failure:** It cannot tell if "Java" refers to coffee, code, or an island without seeing the sentence context.
*   **Hallucination Risk:** Without grounding in the transcript, the Gardener relies solely on LLM priors, which may diverge from the user's actual intent.
*   **Data Loss:** Transcripts are lost upon backend restart, preventing session replay or post-session analysis.

---

## 2. Current State Analysis

| Component | Status | limitation |
| :--- | :--- | :--- |
| **Data Model** | ✅ Ready | `TranscriptChunk` model exists in `models/chunk.py`. |
| **Storage** | ⚠️ Temporary | `ChunkStore` (`services/chunk_store.py`) is **In-Memory Only**. Data dies when server stops. |
| **Database** | ❌ Missing | No Cypher queries exist to save/load chunks from Neo4j. |
| **Gardener** | ❌ Disconnected | `GardenerScheduler` hardcodes `recent_transcript=""` because retrieval is not implemented. |

---

## 3. Implementation Plan

### Phase 1: Database Layer (Neo4j)
**Goal:** Persist chunks as nodes in the graph database, linked to the Session.

1.  **Schema Update:**
    *   Node Label: `:Chunk`
    *   Properties: `id`, `text`, `start_time`, `end_time`, `created_at`
    *   Relationships: `(:Session)-[:HAS_CHUNK]->(:Chunk)`
    *   Ordering: Link chunks via `[:NEXT_CHUNK]` or rely on `start_time` sorting.

2.  **New Functions in `services/graph_db.py`:**
    *   `save_chunk(session_id, chunk)`: Creates the node and links to Session.
    *   `get_recent_transcript(session_id, word_limit=1000)`: Fetches the most recent chunks by time, concatenates text, and returns string.

### Phase 2: Service Layer Refactor
**Goal:** Replace in-memory store with persistent calls.

1.  **Update `services/chunk_store.py`:**
    *   Remove `self._chunks` dict.
    *   Refactor `save()` to await `graph_db.save_chunk()`.
    *   Refactor `list_for_session()` to await `graph_db.list_chunks()`.

### Phase 3: Gardener Integration
**Goal:** Feed the transcript to the LLM.

1.  **Update `services/scheduler.py`:**
    *   In `_run_gardener()`, call `chunk_store.get_recent_transcript(session_id)`.
    *   Pass the result into `self._agent.run(..., recent_transcript=text)`.

2.  **Upgrade Gardener Model:**
    *   Update `backend/app/config.py` or `.env` to set `GEMINI_MODEL_GARDENER="gemini-3-pro"`.
    *   Ensure `backend/app/agents/gardener.py` uses this specific setting (Dual-Model Architecture).

---

## 4. Verification & Testing

### Verification Steps
1.  **Persistence Test:**
    *   Start Session -> Speak -> Restart Backend -> Load Session.
    *   **Success Criteria:** Transcript is still available in "Export" (JSON/Text) and session history via API.

2.  **Context Test:**
    *   Speak an ambiguous term (e.g., "The bank is eroding").
    *   Wait for Gardener cycle.
    *   **Success Criteria:** Gardener correctly identifies "River Bank" vs "Financial Bank" based on surrounding text (e.g., "water", "flow").

3.  **Model Verification:**
    *   Verify Gardener logs show usage of `gemini-3-pro` (or configured model).

3.  **Performance:**
    *   Ensure fetching last 1000 words adds negligible latency (<50ms) to the 90s Gardener cycle.

---

## 5. Action Items (To-Do)

- [ ] **DB:** Implement `save_chunk` and `get_recent_transcript` Cypher queries.
- [ ] **Service:** Wire `ChunkStore` to use new DB functions.
- [ ] **Agent:** Connect `GardenerScheduler` to `ChunkStore` retrieval.
- [ ] **Test:** Verify persistence across restarts.


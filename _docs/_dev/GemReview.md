# Codebase Review: plasticFlower

## 1. Architecture Overview

**plasticFlower** is a local-first, real-time knowledge graph generation system that converts live speech or text into an interactive, organic mind map. It employs an event-driven, service-oriented architecture designed for low-latency feedback and eventual consistency.

### High-Level Components
*   **Frontend:** A Next.js (React) application acting as the visualization layer. It features a custom "Organic" graph layout engine built on Cytoscape.js and handles continuous speech recognition.
*   **Backend:** A FastAPI (Python) server acting as the orchestration layer. It manages "Sessions", processes text "Chunks", and coordinates the bimodal AI agent system.
*   **AI Engine:** Google's Gemini 3 Pro (via `google-genai` SDK). It powers the **Builder** (fast extraction) and **Gardener** (slow refinement) agents.
*   **Persistence:** Neo4j (Graph Database). It serves as the single source of truth, storing the property graph (Nodes, Relationships, Flowers) and transcript history.

### Data Flow
1.  **Ingestion (Continuous Speech):** 
    *   The Frontend's `useSpeechRecognition` hook captures audio continuously. 
    *   Instead of stopping/starting the microphone, it uses a **"Sent Cursor"** strategy to extract stable text chunks every ~8 seconds or 75 words.
    *   These chunks are posted to the Backend (`POST /api/sessions/{id}/chunks`) without interrupting the audio stream.
2.  **Extraction (Builder Loop):** 
    *   The Backend triggers the `BuilderAgent` for each chunk.
    *   `BuilderAgent` uses Gemini to extract entities and relationships, marking them as **`status: GHOST`** (tentative).
    *   These "Ghost" nodes are immediately persisted to Neo4j and broadcast via SSE (`node_added`, `relationship_added`).
3.  **Refinement (Gardener Loop):**
    *   A background scheduler triggers the `GardenerAgent` periodically.
    *   `GardenerAgent` analyzes the full graph state to:
        *   **Confirm:** Promote high-confidence Ghost nodes to **`SOLID`**.
        *   **Prune:** Remove low-value or hallucinatory Ghost nodes.
        *   **Merge:** Combine duplicate concepts (e.g., "AI" and "Artificial Intelligence").
        *   **Cultivate:** Group related nodes into **"Flowers"** (compound clusters) with a designated "Stem" node.
    *   Mutations are persisted and broadcast via SSE (`node_merged`, `flower_updated`, `flower_dissolved`).
4.  **Visualization (Organic Layout):**
    *   The Frontend's `useSSE` hook receives events and maintains a local graph replica.
    *   `GraphCanvas` renders the graph using a custom physics simulation:
        *   **Flowers:** Rendered as clusters where "Petal" nodes fan out physically around a central "Stem" node.
        *   **Temporal Breathing:** Nodes size and opacity pulse based on their recency (timestamp).
        *   **Animations:** New nodes "grow" in slowly (5s fade-in) to avoid jarring pops.

## 2. Key Functions & Components

### Backend (`backend/`)
*   **`app/agents/builder.py`:**
    *   **Role:** Optimistic extraction.
    *   **Behavior:** Fast, additive updates. Creates "Ghost" nodes. Uses existing graph context to reduce duplicates but prioritizes speed.
*   **`app/agents/gardener.py`:**
    *   **Role:** Graph hygiene and structuring.
    *   **Behavior:** Slow, complex reasoning. Merges nodes, detects communities (Flowers), and removes noise.
*   **`app/services/graph_db.py`:**
    *   **Role:** Neo4j Data Access.
    *   **Schema:** 
        *   Nodes have `status` (GHOST/SOLID) and `flower_id` (for clustering).
        *   Flowers are explicit nodes tracking the `stem_node_id`.
        *   Session-based isolation for multi-tenancy.
*   **`app/services/sse_manager.py`:**
    *   **Role:** Real-time broadcaster.
    *   **Behavior:** Manages per-session subscriber queues and serializes Pydantic events to JSON.

### Frontend (`frontend/`)
*   **`src/hooks/useSpeechRecognition.ts`:**
    *   **Role:** Continuous audio capture.
    *   **Key Logic:** Implements a cursor-based extraction buffer that prevents audio dropouts by never stopping the `SpeechRecognition` engine during a session. Reconstructs transcripts on every event to catch API auto-corrections.
*   **`src/hooks/useSSE.ts`:**
    *   **Role:** Resilient event consumer.
    *   **Key Logic:** Handles `EventSource` connection, implements exponential backoff for reconnects, and includes a **Watchdog** (45s) to detect and reset frozen connections.
*   **`src/components/graph/GraphCanvas.tsx`:**
    *   **Role:** The "Living" Graph UI.
    *   **Key Logic:** 
        *   **`syncGraph`:** Reconciles React state with Cytoscape elements.
        *   **`applyOrganicPositioning`:** A custom layout algorithm that arranges Flower members in a "fan" around their Stem and applies organic jitter to standalone nodes to prevent rigid grids.
        *   **Visual Language:** Ghost nodes are dashed/faint; Solid nodes are bold. Flowers are bounding boxes.

## 3. Recent Changes & Observations

### Continuous Speech Recognition
The switch to a cursor-based chunking mechanism (ref: `continuous_speech_chunking`) has significantly improved user experience. Previously, the "stop-and-start" method caused audio dropouts every 8 seconds. The current implementation streams continuously, ensuring no words are lost at chunk boundaries.

### Graph Visualization
The shift to an "Organic" layout (`applyOrganicPositioning`) rather than a pure force-directed simulation gives the application a distinct feel. The visual metaphor of "Flowers" (clusters) with "Stems" (centroids) helps organize the chaos of unstructured speech into navigable semantic islands.

### Robustness
*   **SSE Watchdog:** The addition of a heartbeat/watchdog mechanism in `useSSE` ensures the client doesn't silently lose sync with the server.
*   **Event Replay:** The architecture supports replaying chunks (`replayChunks.mjs`), which is critical for testing the Gardener's behavior on deterministic datasets.

## 4. Areas for Future Attention
*   **Race Conditions:** The concurrency between Builder (adding) and Gardener (merging) remains a theoretical risk, though the "Ghost" status buffers this significantly.
*   **Context Window:** As sessions grow, the `recent_transcript` passed to the Gardener may need smarter summarization or windowing to stay within token limits.
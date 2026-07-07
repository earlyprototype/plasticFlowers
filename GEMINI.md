# plasticFlower

**plasticFlower** is a local-first, real-time knowledge graph generation system. It captures live speech or text, extracts entities and relationships using **Google Gemini**, and renders an interactive mind map in **Next.js**.

## Project Overview

*   **Goal:** Convert unstructured streaming text (speech) into a structured, visual knowledge graph in real-time.
*   **Architecture:** Event-driven, service-oriented.
    *   **Backend:** FastAPI (Python) handles orchestration, connection to Neo4j, and Gemini agent management.
    *   **Frontend:** Next.js (React) visualizes the graph via Cytoscape.js, receiving updates via Server-Sent Events (SSE).
    *   **AI:** Google Gemini (1.5/2.x/3.x) via the new `google-genai` SDK. It performs entity extraction, semantic deduplication, and graph refinement.
    *   **Persistence:** Neo4j stores the graph topology and vector embeddings.

## Repository Structure

*   `backend/`: Python FastAPI application.
    *   `app/agents/`: `BuilderAgent` (fast extraction) and `GardenerAgent` (slow refinement).
    *   `app/api/`: REST endpoints and SSE stream handler.
    *   `app/services/`: Logic for LLM, Neo4j, and graph management.
*   `frontend/`: Next.js TypeScript application.
    *   `src/components/`: UI components (likely GraphCanvas).
    *   `src/hooks/`: Custom hooks like `useSSE` for real-time updates.
*   `docker/`: Docker Compose configuration for Neo4j.
*   `_docs/`: Comprehensive project documentation, plans, and evidence.
*   `scripts/`: Automation scripts for startup and maintenance.

## Building and Running

### Prerequisites
*   **Docker Desktop** (for Neo4j)
*   **Node.js 18+**
*   **Python 3.11+**
*   **Google Gemini API Key**

### Interactive Startup (Recommended)
Use the provided PowerShell script to launch the full stack (Neo4j, Backend, Frontend):

```powershell
# Run with real Gemini API
.\scripts\start_mvp.ps1

# Run in FAKE mode (mock LLM responses for offline testing)
.\scripts\start_mvp.ps1 -FakeMode
```

### Manual Setup

**1. Database (Neo4j)**
```bash
cd docker
docker compose up -d
```

**2. Backend**
```bash
cd backend
# Create/Activate venv
# Install dependencies
pip install .
# Run Server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload
```
*Note: Ensure `.env` is configured with `NEO4J_URI`, `NEO4J_PASSWORD`, and `GEMINI_API_KEY`.*

**3. Frontend**
```bash
cd frontend
npm install
npm run dev
```
*Access at http://localhost:3000*

## Development Conventions

*   **Architecture Pattern:** "Builder vs. Gardener".
    *   *Builder:* Optimistic, fast, additive updates (keeps up with speech). Uses "Flash" models.
    *   *Gardener:* Asynchronous, slow, refining updates (merges, prunes, clusters). Uses "Pro" models for higher reasoning.
*   **State Management:** The Backend is the source of truth (Neo4j). The Frontend is a projection, kept in sync via SSE.
*   **Code Style:**
    *   **Python:** Typed (Pydantic models), AsyncIO-heavy. Follows PEP 8.
    *   **TypeScript:** Functional React components, Custom Hooks for logic separation.
*   **Testing:**
    *   Backend: `pytest`
    *   Frontend: `vitest`

---

# AI Engine: Gemini Deep Dive

The core of **plasticFlower**'s intelligence is powered by Google Gemini, implemented using the new `google-genai` Python SDK.

## 🤖 Agent Configuration

The system uses a bimodal agent strategy to balance latency and reasoning quality:

| Agent | Purpose | Recommended Model | Characteristics |
|-------|---------|-------------------|-----------------|
| **Builder** | Real-time extraction | `gemini-2.0-flash` | High speed, low latency, additive. |
| **Gardener** | Graph refinement | `gemini-1.5-pro` | Higher reasoning for merging and clustering. |

### Configuration (`config.py`)
Settings are managed via Pydantic:
- `gemini_model_builder`: Defaults to Flash models for speed.
- `gemini_model_gardener`: Defaults to Pro models for complex transcript context analysis.
- `gemini_temperature`: Typically set low (0.2) for deterministic structural extraction.

## 🔌 SDK and Connectivity

The backend (`backend/app/services/llm.py`) uses the `genai.Client` which supports multiple backends:

1.  **AI Studio:** Direct usage via `GEMINI_API_KEY`.
2.  **Vertex AI:** Enabled by setting `VERTEX_PROJECT_ID` and `VERTEX_LOCATION`. This allows using Google Cloud's enterprise infrastructure.
3.  **JSON Mode:** All agent calls use `response_mime_type="application/json"` with Pydantic-based `response_schema` enforcement, ensuring the LLM output is immediately parseable.

## 🧠 Semantic Deduplication

Before creating a new node, the **Builder** performs a similarity check (`backend/app/services/similarity.py`):
- **Model:** `text-embedding-004` (768 dimensions).
- **Process:** The concept label is embedded and compared against existing nodes in the Neo4j vector index.
- **Threshold:** `0.85` (cosine similarity). If a match is found, the system increments the `mentions` count of the existing node instead of creating a duplicate.

## 🛠️ Developer Tools

### Fake LLM Mode
For offline development or to save on token costs, set `PLASTICFLOWER_FAKE_LLM=1`. The system will switch to a heuristic-based "fake" LLM that synthesizes nodes and relationships based on keyword frequency in the transcript.

### Quota and Monitoring
- **Retries:** Implements exponential backoff with jitter for transient API errors.
- **Quota Tracking:** Logs `API call #X` and warns specifically on `429 RESOURCE_EXHAUSTED` errors.
- **Call Counter:** Integrated debugging tools to track API consumption per session.

---

# System Architecture & Component Deep Dive

## 1. Architecture Overview

**plasticFlower** employs an event-driven, service-oriented architecture designed for low-latency feedback and eventual consistency.

### Data Flow
1.  **Ingestion (Continuous Speech):** 
    *   The Frontend's `useSpeechRecognition` hook captures audio continuously. 
    *   It uses a **"Sent Cursor"** strategy to extract stable text chunks every ~8 seconds or 75 words without interrupting the audio stream.
    *   Chunks are posted to the Backend (`POST /api/sessions/{id}/chunks`).
2.  **Extraction (Builder Loop):** 
    *   The Backend triggers the `BuilderAgent` for each chunk.
    *   `BuilderAgent` uses Gemini to extract entities and relationships, marking them as **`status: GHOST`** (tentative).
    *   These "Ghost" nodes are immediately persisted to Neo4j and broadcast via SSE (`node_added`, `relationship_added`).
3.  **Refinement (Gardener Loop):**
    *   A background scheduler triggers the `GardenerAgent` periodically.
    *   `GardenerAgent` analyzes the full graph state to confirm/prune ghosts, merge duplicates, and cultivate **"Flowers"**.
    *   Mutations are persisted and broadcast via SSE (`node_merged`, `flower_updated`, `flower_dissolved`).
4.  **Visualization (Organic Layout):**
    *   The Frontend's `useSSE` hook receives events and maintains a local graph replica.
    *   `GraphCanvas` renders the graph using a custom physics simulation, featuring **Flowers** (clusters) and **Temporal Breathing** animations.

## 2. Key Functions & Components

### Backend (`backend/`)
*   **`app/agents/builder.py`:** Optimistic extraction. Fast, additive updates creating "Ghost" nodes.
*   **`app/agents/gardener.py`:** Graph hygiene and structuring. Slow, complex reasoning to merge nodes and detect communities (Flowers).
*   **`app/services/graph_db.py`:** Neo4j Data Access. Manages schema for Nodes (GHOST/SOLID), Flowers (stem tracking), and session isolation.
*   **`app/services/sse_manager.py`:** Real-time broadcaster managing per-session subscriber queues.

### Frontend (`frontend/`)
*   **`src/hooks/useSpeechRecognition.ts`:** Continuous audio capture using cursor-based chunking.
*   **`src/hooks/useSSE.ts`:** Resilient event consumer with exponential backoff and connection watchdog.
*   **`src/components/graph/GraphCanvas.tsx`:** The "Living" Graph UI using `applyOrganicPositioning` for custom "flower fan" layouts.

---

# The Gardener System

The **Gardener** is the AI curator that runs in the background to tidy up the knowledge graph.

## 🔄 The Gardener Cycle

### Trigger Conditions
Runs every ~24 seconds when recent builder activity has occurred and ghost nodes exist.

### The Process

1.  **Gather Context:** Loads all existing nodes, relationships, flowers, and the last 1000 words of speech context.
2.  **AI Decision Making:** The Gardener AI (Gemini) decides to:
    *   **Confirm:** Valid ghost nodes become solid.
    *   **Merge:** Duplicate ghost nodes are merged into solid ones.
    *   **Remove:** Invalid/nonsense ghosts are pruned.
    *   **Form Flowers:** Related nodes (3+ nodes, 2+ connections) are grouped into thematic clusters.
3.  **Apply Actions:** Mutations are applied to Neo4j in a specific order (Nodes -> Relationships -> Flowers).
4.  **Broadcast:** Events are sent to the UI via SSE.

## 🌸 Flower Formation Logic

Flowers organize nodes by theme. The LLM follows strict rules:
*   **Criteria:** Requires 3+ nodes AND 2+ internal connections.
*   **Structure:** A "stem" node (central hub) and "member" nodes.
*   **Dynamic:** Flowers can be created, updated (adding members), or dissolved (if they lose coherence) over time.

## 🎨 Visual Behaviors

The frontend visualizes Gardener actions through specific animations:
*   **Ghost → Solid:** 400ms smooth transition in color/border.
*   **New Relationships:** 2000ms fade + draw effect.
*   **Flower Formation:** Nodes animate to positions around their "stem" (1200ms), and the stem node grows larger.
*   **Camera:** Smoothly pans/zooms (2500ms) after changes settle.

These animations represent the AI's semantic decisions being applied to the graph in real-time.

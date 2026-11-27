# plasticFlowers

Speak, and watch your thinking take shape. plasticFlowers listens to live speech, uses Gemini to pull out the ideas and the links between them, and grows a knowledge graph on screen in real time — local-first, no cloud.

I wanted the opposite of a transcript. A transcript is a wall of text you have to re-read; I wanted to *see* a conversation's structure emerge as it happens — the islands of thought, the bridges between them — and be left with something worth looking at afterwards.

## What it's trying to be

1. **Context, not a list.** Maps the territory of a conversation, turning scattered facts into coherent islands of thought.
2. **Connections made visible.** Draws the bridges between ideas, surfacing the thread that ties concepts together.
3. **A memory you can navigate.** You end up with an artifact you can come back to — an instant, browseable map of the event, not just a record of it.
4. **Something beautiful.** The graph is meant to read as generative art: organic and physics-driven, inviting exploration rather than a sterile technical diagram.

## Quick start (MVP demo)

From the project root, use Python 3.11+, Node.js 18.17+ with npm, and a running Docker engine with Compose v2. The Windows launcher uses Compose's `up --wait` option to wait for the Neo4j and Redis health checks.

1. Copy `.env.example` to `.env` (PowerShell: `Copy-Item .env.example .env`). Set the Neo4j password to a new password of at least eight characters. Set the Gemini key if using real inference.
   ```
   NEO4J_URI=neo4j://127.0.0.1:7687
   NEO4J_PASSWORD=<your_password>
   GEMINI_API_KEY=<your_key>
   ```
2. On Windows, install the backend and frontend dependencies once. Rerun the install commands when dependencies change.

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -e 'backend[dev]'
   npm.cmd ci --prefix frontend
   ```

3. Start Neo4j and Redis in Docker, the backend on port 8010, and the frontend on port 3000.

   ```bash
   # Linux / macOS
   bash scripts/start_mvp.sh            # add --fake-mode to run offline, no API key needed
   ```
   ```powershell
   # Windows
   .\scripts\start_mvp.ps1 -FakeMode   # synthetic extraction and embeddings
   ```

   On Windows, omit `-FakeMode` for real inference. The launcher opens the frontend once `http://127.0.0.1:8010/health` and `http://127.0.0.1:3000/` both return HTTP 200. Add `-NoBrowser` to keep the browser closed. Press Ctrl+C to stop both app services. To stop the containers, run `docker compose -f docker/docker-compose.yml --env-file .env down`.

   On macOS or Linux the Makefile also provides `make setup`, `make up`, `make backend`, `make frontend`, `make demo-fake`, `make test` and `make down`.
4. Open http://localhost:3000 and start talking.

With the stack running, use `.venv\Scripts\python.exe backend/scripts/smoke_test.py` on Windows or `.venv/bin/python backend/scripts/smoke_test.py` on macOS and Linux for the end-to-end smoke test. The demo walkthrough is in `_docs/_runbook/MVP_DEMO.md`.

To test the Windows launcher itself, stop the app and run `python scripts/tests/test_windows_launcher.py -v`. The tests use local HTTP fixtures on ports 8010 and 3000 and a Docker Compose stand-in.

## How it's built

- **`backend/`** — a FastAPI service running two agents: a **Builder** that extracts entities and relationships from the incoming speech, and a **Gardener** that continuously reorganises the graph as it grows.
- **`frontend/`** — a Next.js app that streams updates live and renders the graph, with filters and exports.
- **`docker/`** — Neo4j and Redis, orchestrated so the whole thing comes up with one command.
- **`scripts/`** — startup helpers for both platforms (`start_mvp.sh`, `start_mvp.ps1`), plus one-off debug utilities kept under `scripts/diagnostics/`. A repo-root `Makefile` wraps the same steps.
- **`_docs/`** — the project's documentation: architecture, ADRs, runbooks, audits, and evidence.
- **`_dev/`** — development notes and working material.
- **`_discovery/`** — prior-art research, including the build-vs-adopt analysis at `_discovery/_repo/_INDEX.md`.

## Decisions, logged as they happen

Architecture choices are written down when they're made, not reconstructed after the fact.

- **`_docs/_dev/ADR/`** — 13 Architecture Decision Records covering clustering, agent scheduling, similarity tuning, and other structural choices, each with its context and consequences.
- **`_discovery/_repo/_INDEX.md`** — the build-vs-adopt analysis weighing plasticFlowers' approach against existing open-source knowledge-graph projects (Graphiti, GraphRAG, and others), so the reasoning for building custom is on record.

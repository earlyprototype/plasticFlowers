# plasticFlowers

Speak, and watch your thinking take shape. plasticFlowers listens to live speech, uses Gemini to pull out the ideas and the links between them, and grows a knowledge graph on screen in real time — local-first, no cloud.

I wanted the opposite of a transcript. A transcript is a wall of text you have to re-read; I wanted to *see* a conversation's structure emerge as it happens — the islands of thought, the bridges between them — and be left with something worth looking at afterwards.

## What it's trying to be

1. **Context, not a list.** Maps the territory of a conversation, turning scattered facts into coherent islands of thought.
2. **Connections made visible.** Draws the bridges between ideas, surfacing the thread that ties concepts together.
3. **A memory you can navigate.** You end up with an artifact you can come back to — an instant, browseable map of the event, not just a record of it.
4. **Something beautiful.** The graph is meant to read as generative art: organic and physics-driven, inviting exploration rather than a sterile technical diagram.

## Quick start (MVP demo)

You'll need Docker Desktop, Node.js 18+, and Python 3.11+.

1. Copy `.env.example` to `.env` and set:
   ```
   NEO4J_URI=neo4j://127.0.0.1:7687
   NEO4J_PASSWORD=<your_password>
   GEMINI_API_KEY=<your_key>
   ```
2. Start everything: `.\scripts\start_mvp.ps1` — add `-FakeMode` to run offline with canned data (no API key needed).
3. Open the frontend and start talking.

To verify the stack end to end, there's a smoke test (`python backend/scripts/smoke_test.py`) and a full walkthrough in the runbook at `_docs/_runbook/MVP_DEMO.md`.

## How it's built

- **`backend/`** — a FastAPI service running two agents: a **Builder** that extracts entities and relationships from the incoming speech, and a **Gardener** that continuously reorganises the graph as it grows.
- **`frontend/`** — a Next.js app that streams updates live and renders the graph, with filters and exports.
- **`docker/`** — Neo4j and the supporting services, orchestrated so the whole thing comes up with one command.

Planning docs, specifications, and prior-art research live under `_docs/`, `_dev/`, and `_discovery/`.

## Decisions, logged as they happen

Architecture choices are written down when they're made, not reconstructed after the fact.

- **`_docs/_dev/ADR/`** — 13 Architecture Decision Records covering clustering, agent scheduling, similarity tuning, and other structural choices, each with its context and consequences.
- **`_discovery/_repo/_INDEX.md`** — the build-vs-adopt analysis weighing plasticFlowers' approach against existing open-source knowledge-graph projects (Graphiti, GraphRAG, and others), so the reasoning for building custom is on record.

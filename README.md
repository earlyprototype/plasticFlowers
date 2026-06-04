# plasticFlower

Local-first live mindmap that captures live speech, extracts an emergent knowledge graph via Gemini 3 Pro, and renders it in real time.

## Vision

The goal of **plasticFlower** is to create a visual representation of spoken thought that:
1.  **Creates Context:** Maps the territory of a conversation, turning lists of facts into coherent "islands" of thought.
2.  **Connects Key Elements:** Actively visualizes the bridges between ideas, revealing the narrative thread that ties concepts together.
3.  **Is Digestible for Reference:** Produces an artifact that serves as an instant, easily navigable memory of the event—not just a transcript, but a structured cognitive map.
4.  **Is Beautiful:** Functions as a piece of generative art. The visualization should be aesthetically pleasing and "organic," inviting exploration rather than feeling like a sterile technical diagram.

## Quick start (MVP demo)
- Ensure Docker Desktop, Node.js 18+, Python 3.11+ are installed.
- Copy `.env.example` to `.env` and set:
  - `NEO4J_URI=neo4j://127.0.0.1:7687`
  - `NEO4J_PASSWORD=<your_password>`
  - `GEMINI_API_KEY=<your_key>` (omit fake mode for real demo)
- Start everything: `.\scripts\start_mvp.ps1` (add `-FakeMode` for offline testing).
- Validate stack: `python backend/scripts/smoke_test.py --base http://127.0.0.1:8010 --output _docs/_evidence/gate7/smoke_test_results.json`.
- Follow the runbook: `_docs/_runbook/MVP_DEMO.md`.

## Repository layout

- `_docs/` — MVP specifications (alignment, architecture, contracts, prompts)
- `_dev/` — Plan packs, gates, and director guidance
- `_discovery/` — Research references and leverage guides
- `backend/` — FastAPI application (MVP endpoints, Builder/Gardener agents)
- `frontend/` — Next.js application (SSE monitor, filters, exports)
- `docker/` — Container orchestration (Neo4j, auxiliary services)

Refer to `_docs/_dev/_MVP/_structure/01_project_structure.md` for full structure expectations and `_docs/_runbook/MVP_DEMO.md` for demo steps.

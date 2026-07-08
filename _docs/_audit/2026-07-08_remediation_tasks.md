# plasticFlower — Remediation Task Briefs

Companion to [`2026-07-08_audit_report.md`](./2026-07-08_audit_report.md). Each task below is **self-contained** — you can paste a single task to an agent without extra context. Work each task on its own branch; run the listed acceptance checks before opening a PR.

**Ordering / dependencies:** T1 unblocks everything backend-side. Do Phase 0 (T1–T4) first and in order where noted. Phases 1–3 tasks are independent of each other unless a `Depends on` line says otherwise.

**Global context for every task:** plasticFlower is a local-first app that captures live speech, extracts a knowledge graph via Gemini, stores it in Neo4j, and renders it live over SSE. Stack: `backend/` = FastAPI + Neo4j + Redis + `google-genai` SDK (the NEW SDK — `from google import genai` — not the legacy `google-generativeai`), Python ≥3.11. `frontend/` = Next.js 14 + TypeScript + Cytoscape (fcose). Backend dev server runs on port **8010** (`backend/scripts/dev_server.py`), frontend on 3000. Backend tests: `cd backend && pytest tests`. Frontend checks: `cd frontend && npx tsc --noEmit && npm run test && npm run build`.

---

## Phase 0 — restore boot and build

### T0 — Salvage the `review/local-backend-additions` snapshot branch onto main  `[P0 — do first]`  ✅ **DONE — executed on PR #3's branch (see report Section G).** Remaining sub-step for a human: after PR #3 merges, delete `neo4j-review-fixes` and `claude/readme-fixes`, and delete or archive-rename `review/local-backend-additions`.

**Problem:** the owner's local working folder — containing real fixes made after `main` was last pushed — was committed as a fresh snapshot (`chore: initial snapshot`) and pushed to `review/local-backend-additions` (and `neo4j-review-fixes`, the same line one commit behind). The branch **shares no git history with `main`**, so `git merge` refuses with "unrelated histories". It mixes three kinds of content:
1. **Real code fixes** (keep): `backend/app/models/graph.py` (ReferenceNode import — fixes the fatal boot bug), `backend/app/agents/researcher.py` (lazy imports breaking the agents↔services cycle + `google_search` grounding + raise-instead-of-stub), `backend/app/services/graph_db.py` (module `_logger` + `SET n +=` merge semantics preserving embeddings), `backend/app/models/node.py` (docstring), `backend/tests/test_llm.py` (new-SDK rewrite — imports still wrong, T2 finishes it).
2. **Content `main` was always missing** (keep, review): `_dev/` and `_discovery/` trees (the directories README references), new docs (`NEO4J_IMPLEMENTATION_SPEC.md` etc.), possibly some diagnostic scripts worth keeping under `backend/scripts/diagnostics/`.
3. **Local debris** (exclude): `backend/plasticflower_backend.egg-info/`, stray `backend/5.0.0` file, `frontend/tsconfig.tsbuildinfo`, `debug_*/blind_*/verify_*` `.txt` logs and one-off `verify_phase*.py` scripts at repo root, `Untitled`, `image.png`, `.cursor/`, `@filing/`, `*_log.txt`.

**Do:** create a branch off `main`; apply the snapshot's changes selectively — `git diff main review/local-backend-additions -- backend/app backend/tests | git apply` for the code, `git checkout review/local-backend-additions -- _dev _discovery <chosen docs/scripts>` for content — excluding all debris. Extend `.gitignore` (`*.egg-info/`, `*.tsbuildinfo`, `.cursor/`) so the debris can't return. Commit with messages crediting the original fix commits. Also merge the small `claude/readme-fixes` branch (two clean README commits, normal history) or fold it into T14. Once merged to `main`, delete the snapshot branches to avoid confusion.

**Accept:** on the new branch: `cd backend && python -c "import app.main; import app.agents; import app.services"` exits 0; `git diff main..HEAD --name-only` contains no egg-info/log/artifact files; `_discovery/_repo/_INDEX.md` exists; snapshot branches documented as superseded.

---

### T1 — Fix the backend's fatal and circular imports  `[P0]`

> **Branch update:** both fixes already exist on `review/local-backend-additions` and land via **T0**. Keep this brief as the specification/verification checklist; skip if T0 is merged.

**Problem:** the backend cannot import at all.
1. `backend/app/models/graph.py:17` does `from .research import ReferenceNode`, but no `research.py` exists — the class lives in `backend/app/models/reference.py`. Every entry point dies with `ModuleNotFoundError: No module named 'app.models.research'`.
2. There is a circular import: `app/agents/__init__.py` imports `researcher.py`, which imports `app.services.llm`; `app/services/__init__.py` imports `researcher_service.py`, which imports `from ..agents import ResearcherAgent`. Anything importing `app.agents` before `app.services` raises `ImportError: cannot import name 'ResearcherAgent' from partially initialized module`.

**Do:**
- Fix the import in `models/graph.py` to `from .reference import ReferenceNode`.
- Break the cycle — preferred: in `researcher_service.py`, import `ResearcherAgent` lazily (inside the function that uses it) or import from the concrete module `..agents.researcher` while making `agents/researcher.py` import `get_gemini_client` lazily/from the concrete `..services.llm` module. Choose the minimal change that makes **both** `import app.agents` and `import app.services` succeed regardless of order.

**Accept:** from `backend/`: `python -c "import app.main"`, `python -c "import app.agents"`, and `python -c "import app.services"` all exit 0.

---

### T2 — Repair the backend test suite  `[P0]` `Depends on: T0/T1`

> **Branch update:** `review/local-backend-additions` already rewrote `tests/test_llm.py` for the new SDK (use that version, landed via T0) — but it still imports `from backend.app...`, so collection still fails (verified: 5 errors). The import fix, pytest config, and loose-file exclusion below are all still required.

**Problem:** `pytest` fails at collection: all 5 modules in `backend/tests/` import `from backend.app...`, which doesn't resolve when running from `backend/`. After fixing imports, `tests/test_llm.py` still can't pass: its autouse fixture does `monkeypatch.setattr(llm, "_MODEL", None)` and tests stub `llm.genai.configure` / `llm.genai.GenerativeModel` — artifacts of the legacy `google-generativeai` SDK. The code now uses the new `google-genai` SDK (`genai.Client`, module global `_CLIENT`, model-rotation list in `llm.py:48-52`). Also: no pytest config exists, so loose script files (`backend/test_embedding_exclusion.py`, `backend/scripts/test_*.py` — live-server scripts, not unit tests) get collected and error.

**Do:**
- Change all `from backend.app...` imports in `backend/tests/` to `from app...`.
- Add `[tool.pytest.ini_options]` to `backend/pyproject.toml`: `testpaths = ["tests"]`, `asyncio_mode = "auto"` (check what `pytest-asyncio` usage the tests assume).
- Rewrite `tests/test_llm.py` against the current `app/services/llm.py` API (stub `genai.Client` / patch `_CLIENT`; test fake mode via `PLASTICFLOWER_FAKE_LLM`).
- Rename the loose `test_*.py` scripts under `backend/` root and `backend/scripts/` (e.g. `manual_check_*.py`) so pytest ignores them, or exclude via config.

**Accept:** `cd backend && pytest` runs with **zero collection errors** and all tests pass.

---

### T3 — Fix the Flower `member_ids` contract end-to-end  `[P0]` `Depends on: T1`

**Problem (the repo's central defect):** both halves were written against a `Flower.member_ids: list[str]` field that the Pydantic model and API response never contained.
- Backend `models/flower.py:19-26` has fields `id, label, stem_node_id, edge_count, created_at` — no `member_ids`, and `edge_count` is required.
- `services/scheduler.py:814-820` constructs `Flower(...)` **without** `edge_count` and **with** `member_ids` → `ValidationError` on every flower creation. `scheduler.py:834` (`flower.member_ids = member_ids`) and `:850` (`for node_id in flower.member_ids`) also crash. `scheduler.py:559-572` (fake mode) builds `FlowerAction(flower_id=None, ...)` but `agents/gardener.py:55` types it `str` → `ValidationError`. All of these are currently swallowed by broad `except Exception:` handlers — flowers have never worked.
- Frontend `src/lib/types.ts:40-46` `Flower` also lacks `member_ids`, yet `stemPetalPositioning.ts:42,97` and `layoutEngine.ts:90-97` use it → ~20 of the 37 tsc errors, and a guaranteed runtime `TypeError` in `GraphCanvas.tsx:339-341` the moment a flower exists.

**Do:**
- Add `member_ids: list[str] = []` to the backend `Flower` model; make scheduler construct flowers with a correct `edge_count` (or default it); fix the update/dissolve paths; make `FlowerAction.flower_id` `Optional[str]` (None = create-new) and handle it.
- Ensure the flower API responses and SSE flower events (`models/events.py`, `api/graph.py` flower endpoints, `graph_db.py` flower persistence/read-back) actually populate `member_ids` from the BELONGS_TO relationships.
- Add `member_ids: string[]` to the frontend `Flower` type in `src/lib/types.ts`.
- Add a backend test that creates/updates/dissolves a flower through the scheduler's code path (fake mode) to lock the contract.

**Accept:** `cd backend && pytest` green incl. new flower test; a fake-mode run (`PLASTICFLOWER_FAKE_LLM=1`, live Neo4j+Redis, ≥5 chunks posted) produces a `flower_created` SSE event with non-empty `member_ids` and **no** swallowed exceptions in logs; frontend `member_ids`-related tsc errors gone.

---

### T4 — Make the frontend compile, and fix the 4 failing tests  `[P0]` `Depends on: T3 (for the member_ids type)`

**Problem:** `next build` fails; `npx tsc --noEmit` = 37 errors; `vitest run` = 4 failures out of 72.
Error clusters:
1. `GraphCanvas.tsx:287` — `LAYOUT_CONFIG` (`config/layoutConfig.ts:7-40`, fcose options: `name`, `numIter`, …) doesn't satisfy the hand-rolled `LayoutOptions` interface (`layout/layoutEngine.ts:9-19`, which demands `algorithm`/`iterations` that fcose configs don't have). Reconcile the type with the real fcose option shape (`@types/cytoscape-fcose` is installed but shadowed — see 4).
2. `member_ids` errors — resolved by T3's type addition; then clean the ~12 cascading implicit-`any` parameters in `stemPetalPositioning.ts` / `layoutEngine.ts`.
3. `graphRenderer.ts:206-208` — `.id()`/`.hasClass()` called on `NodeCollection` returned by `.parent()`; use `.first()` / proper singular typing.
4. `src/types/cytoscape-fcose.d.ts` declares the module as `any`, shadowing the installed `@types/cytoscape-fcose` — delete the local stub and use the real typings.
Failing tests: `stemPetalPositioning.test.ts:25,33,38` expect the old orbit formula `max(180, 140 + n*25)` but `stemPetalPositioning.ts:74-77` now implements `80 + n*15` (decide which is intended — the newer code formula is presumed current; update tests to it). `organicGrowth.test.ts:146-162` passes `hubAttractionMultiplier: 0.1` as a "custom" value but 0.1 IS the default (`organicGrowth.ts:23`) — use a genuinely different value. (If T16 deletes organicGrowth, drop that test instead.)

**Accept:** `cd frontend && npx tsc --noEmit` → 0 errors; `npm run test` → 0 failures; `npm run build` → succeeds.

---

## Phase 1 — revive the broken subsystems

### T5 — Repair the Researcher pipeline (5 independent breaks)  `[P1]` `Depends on: T0/T1`

> **Branch update:** points 3 and 4 below are fixed on `review/local-backend-additions` (landed via T0): the Gemini fallback now uses the `google_search` tool and raises `ResearcherAgentError` instead of returning a confidence-0 stub. Points 1, 2, 5 and the persistence bugs remain.

**Problem:** no research ever completes, automatically or manually. Breaks, in pipeline order:
1. `services/scheduler.py:868` — `action.label` but `ResearchAction` (`agents/gardener.py:78-97`) has no `label` field (has `action/node_id/entity_type/reason/priority`). `AttributeError` swallowed at `scheduler.py:877`.
2. `agents/researcher.py:163-168` — calls `tavily_search(..., include_answer=True)`; that kwarg is commented out of the signature in `services/tavily_mcp.py:52` → `TypeError`.
3. `researcher.py:107` — only catches `TavilyMCPError`, so the `TypeError` from (2) bypasses the Gemini fallback entirely.
4. `researcher.py:203-211` — Gemini fallback uses retired `google_search_retrieval` / `GoogleSearchRetrieval` (Gemini-1.5-era); gemini-2.5 models require the `google_search` tool → API 400 → confidence-0 stub.
5. `api/graph.py:107` — manual endpoint `POST /sessions/{id}/nodes/{node_id}/research` does `str(node.entity_type)`; the field is `inferred_type` (`models/node.py:19-54`) → 500 every call.
Plus persistence would fail after all that: `graph_db.py:1252` writes `vocabulary_suggestion` (a dict) as a Neo4j property — Neo4j rejects map properties; and `_reference_from_value` (`graph_db.py:1330-1351`) never converts the Neo4j `DateTime` for `fetched_at` back to a Python datetime.
Also fix root-cause masking: the broad `except Exception` at `scheduler.py:877` should at minimum `logger.exception`.

**Do:** fix all six points (use the node's label where `action.label` was intended — look up the node or extend `ResearchAction`; reinstate or drop `include_answer` consistently; serialize `vocabulary_suggestion` to JSON string or flatten; convert DateTime like `_convert_datetime` elsewhere in the file). Add unit tests with stubbed Tavily/Gemini covering auto-trigger and the manual endpoint.

**Accept:** `pytest` green incl. new tests; with fake/stubbed search, a Gardener cycle that flags a node produces a persisted `Reference` and a `node_needs_research`→reference SSE flow without swallowed exceptions; `POST .../research` returns 200.

---

### T6 — Fix Gardener scheduling, metrics, and dropped batches  `[P1]` `Depends on: T1`

**Problem:**
1. `services/scheduler.py:447-448` counts actions named `"solidify"`/`"remove"`, but `NodeAction.action` literals are `"confirm"/"prune"/"merge"` (`agents/gardener.py:40`) — `nodes_solidified`/`nodes_removed` in the `gardener.complete` event are permanently 0.
2. `scheduler.py:241-248` — the 5s "safety debounce" **ACKs and discards** Redis events arriving early; those batches are permanently lost. It should defer/requeue, not drop.
3. `services/builder_service.py:494-512` — Builder publishes to the Gardener stream only every 5th chunk (`builder_gardener_ratio`); sessions with <5 chunks never get a Gardener pass, so their nodes stay GHOST forever. Add a flush trigger on session end (`POST /sessions/{id}/end` handler in `api/sessions.py`) and/or a time-based fallback.
4. Fake mode: `scheduler.py:500` — the `GardenerCycleEvent` broadcast is skipped when the fake path raises; put cycle-complete broadcasting in a `finally` or equivalent so the UI counter reflects reality. (The fake-path flower crash itself is T3.)

**Accept:** unit test asserting correct solidified/removed counts from a synthetic action list; test that an early event is deferred not dropped; ending a 2-chunk session triggers a Gardener pass (fake mode) and ghosts get confirmed.

---

### T7 — Fix graph_db query/persistence bugs  `[P1]` `Depends on: T0/T1`

> **Branch update:** point 1 (module `_logger`) is fixed on `review/local-backend-additions` (via T0), which also improved `update_node` to `SET n +=` (merge, preserving embeddings). Points 2–6 remain.

**Problem (all in `backend/app/services/graph_db.py`):**
1. `:122` — `_logger` is referenced in `delete_node`'s error branch but only defined locally inside other functions → `NameError` whenever deleting a missing node. Add a module-level `logger = logging.getLogger(__name__)` and use it consistently.
2. `:195-202` — filtering nodes by BOTH `flower_id` and `status` builds `... (f:Flower {...}) AND n.status = $status` — an `AND` with no `WHERE` → Cypher syntax error → endpoint 500s. (`tests/test_graph_db.py:46-66` passes because its fake driver never parses Cypher — improve the test to assert the generated Cypher string is valid, at least that `WHERE` precedes `AND`.)
3. `services/builder_service.py:431,452` — `create_relationship` returns `None` when an endpoint node is missing (`graph_db.py:286-297`); the `None` is appended and later crashes `RelationshipAddedEvent(payload=None)`, failing the whole chunk after nodes were persisted. Skip `None`s (and log).
4. `services/similarity.py:71-78` — vector search takes global top-k(5) THEN filters by session, so other sessions' nodes crowd out true matches. Overfetch (e.g. k=50) and filter, or use a session-scoped query.
5. `:659-699` — `delete_session_record` orphans `SessionVocabulary`, `ProofreadCheckpoint`, `SessionContext`, `Reference`, `Source` nodes; extend the delete.
6. `app/main.py:89-94` — `/health` lets Neo4j exceptions propagate as raw 500s and still checks Neo4j under `PLASTICFLOWER_SKIP_NEO4J`; return a structured degraded response instead.

**Accept:** `pytest` green with new/updated tests for 1–3; manual: `GET /sessions/{id}/nodes?status=ghost&flower_id=X` returns 200 against live Neo4j.

---

### T8 — Fix frontend SSE + chunk-dispatch reliability  `[P1]`

**Problem (frontend `src/`):**
1. `hooks/useSSE.ts:28-29` — `"gardener_cycle"` appears twice in `EVENT_TYPES`, registering two listeners; every Gardener cycle double-increments `gardenerCount` (`useGraphState.ts:88-89`). De-dupe.
2. `useSSE.ts:17-32` — backend emits `node_corrected` (`backend/app/services/scheduler.py:603-610`, name literal in `backend/app/models/events.py:76`) but the frontend never subscribes — STT corrections are dropped. Add the event type, payload type in `lib/types.ts`, and a state handler that relabels the node.
3. `useSSE.ts` — `ConnectionState` declares `"reconnecting"` (line 6) and the UI styles it, but it's never set. Set it when scheduling a reconnect after an error.
4. `hooks/useChunkDispatcher.ts:35-41,80-84` — dispatch gate requires ≥3 sentences (regex `[.!?]`) or 1000 chars, but Web Speech transcripts are mostly unpunctuated; the 15s staleness flush is only evaluated on the next `append` — no timer — so the final utterance of a session can sit in the buffer forever. Add a real interval/timeout that flushes stale buffers, and flush the buffer to the API (not just into the buffer) when speech recognition ends.
5. `useSSE.ts:59-60` + `useGraphState.ts:105` — events with empty `data` produce `payload: undefined` and handlers then dereference it → guard.
6. `GraphCanvas.tsx:281-357` — the debounced-sync async callback keeps using `cy` after the component may have unmounted and `cy.destroy()`ed (`:265`); add a cancelled/destroyed guard around the awaits.
7. Fix the 3 `react-hooks/exhaustive-deps` warnings (`GraphCanvas.tsx:264`, `useChunkDispatcher.ts:41`, `useSSE.ts:184`) properly, not by suppression.

**Accept:** `npm run lint` clean; `npm run test` green (add tests for the dispatcher timer flush and gardener single-increment); manual replay run shows gardener counter incrementing by 1 per cycle and buffered tail-text flushing within ~15s of silence.

---

### T9 — Fix rendering/animation defects  `[P1]` `Depends on: T4`

**Problem (frontend `src/components/graph/`):**
1. `rendering/graphRenderer.ts:157-159` — for parentless nodes, `(existing.parent() as any)?.id()` is `undefined` and `parentId` is `null`; `undefined !== null` → every unclustered node is `move()`d (remove+re-add in Cytoscape) on **every** sync. Normalize both sides (e.g. `?? null`).
2. `animation/animationController.ts:102-115` — fade-in sets inline `opacity` 0→1 on new nodes, permanently overriding the `node.ghost { opacity: 0.15 }` stylesheet rule (`config/layoutConfig.ts:93`) — ghosts render fully opaque. After the animation, `removeStyle('opacity')` (or animate to the class-appropriate value).
3. `animationController.ts:181-220` — float animation recurses forever via `complete:`, captures `startPos` once (drifts/fights layout after re-runs), and only stops on node removal or flower membership. Stop it when a node gains ≥2 connections, re-anchor after layout runs, and cap concurrent float animations.
4. `config/layoutConfig.ts:161,196` — Cytoscape.js has no `:hover` pseudo-class; the `node.flower:hover` / `edge:hover` styles never apply. Implement hover via `mouseover`/`mouseout` events toggling a `.hovered` class.
5. `GraphCanvas.tsx:68` — `useRef(new AnimationController())` constructs a throwaway instance every render; use lazy init. Also `GraphCanvas.tsx:16-20`'s module-level `fcoseRegistered` guard is a no-op; register once at module scope.
6. Known-issue doc `frontend/_docs/_knownIssues/layout-optimization.md` (status DEFERRED, still true): any flower structural change re-runs full fcose over the whole graph (`GraphCanvas.tsx:295-334`). With T3 fixing `previousFlowersRef` updates, verify layout no longer re-runs on every sync; further optimization can stay deferred but document current behavior.

**Accept:** `tsc`/`build`/tests green; manual run: ghosts visibly transparent, hover styles work, no continuous `move()` churn (spot-check with cytoscape event logging), float animations stop for connected nodes.

---

## Phase 2 — dependencies, config, infra

### T10 — Unify Python dependency manifests  `[P2]` `Depends on: T1`

**Problem:** `backend/pyproject.toml` and `backend/requirements.txt` contradict each other and the code:
- pyproject pins `fastapi==0.115.2` while requirements has `fastapi>=0.115.6` and `starlette>=0.49.1` — installing pyproject's pin with requirements' starlette is `ResolutionImpossible` (verified).
- pyproject declares the **legacy** `google-generativeai` SDK; the code exclusively uses the new `google-genai` (`from google import genai` in `llm.py`, `embeddings.py`, `export.py`, `researcher.py`). requirements.txt correctly lists `google-genai` but **unpinned** (today resolves 2.10.0, fastapi 0.139, starlette 1.3 — silent drift).
- pyproject omits `sse-starlette`, `redis`, `numpy`, `httpx`, `httpx-sse`, `requests` — `pip install -e .` yields an unimportable app.

**Do:** make `pyproject.toml` the single source of truth: full dependency list matching actual imports, compatible pins (pick current-tested versions), `google-genai` pinned with a range, dev extra with pytest/pytest-asyncio (+ the pytest config from T2 if not already merged). Either delete requirements.txt or reduce it to `-e .[dev]` / generate it as a lock. Update README/scripts to the chosen install command.

**Accept:** in a fresh venv: `pip install -e backend[dev]` (or documented equivalent) succeeds; `python -c "import app.main"` and `pytest` pass; no conflicting pins remain anywhere in the repo.

---

### T11 — Cross-platform startup + Docker fixes  `[P2]`

**Problem:** the only startup path is Windows PowerShell (`scripts/start_mvp.ps1`, `restart_clean.ps1`); README quick start references `.\scripts\start_mvp.ps1`, never installs dependencies, and macOS/Linux users have no path at all. Docker: `docker/docker-compose.yml` reads `${NEO4J_PASSWORD}` from the shell env or `docker/.env` — NOT the root `.env` — yet every doc says plain `cd docker && docker compose up -d`, silently yielding an **empty Neo4j password** and a failing healthcheck. Also: obsolete `version: "3.9"` key; `NEO4J_PLUGINS` still loads `graph-data-science` though ADR-0001 abandoned GDS; `docker/README.md` is one content-free line; `start_mvp.ps1:57-67` auto-copies `.env.example`→`.env` and proceeds with the placeholder password; `scripts/START_SERVERS.md:48` recommends `taskkill /F /IM node.exe; taskkill /F /IM python.exe` (kills unrelated processes) and documents `NEO4J_USER` (real var: `NEO4J_USERNAME`).

**Do:**
- Add a POSIX path: `scripts/start_mvp.sh` (or a Makefile with `make up / make backend / make frontend / make demo-fake`) mirroring the .ps1 logic: check prereqs, create venv + pip install, npm install, docker compose up with the password wired, start uvicorn on 8010 + next dev on 3000.
- Wire compose to the root `.env` explicitly (run compose with `--env-file ../.env` from scripts, or add `env_file` docs) so one `.env` is the single source; make the compose file fail loudly if `NEO4J_PASSWORD` is empty (e.g. `${NEO4J_PASSWORD:?set in .env}`).
- Remove the obsolete `version:` key and the `graph-data-science` plugin; write a real `docker/README.md` (what runs, ports, password source, reset instructions).
- Fix `START_SERVERS.md` (targeted kill commands, `NEO4J_USERNAME`); make `start_mvp.ps1` halt with a clear message when `.env` still has placeholder values.
- Update README quick start to include dependency installation and both platforms.

**Accept:** on a clean Linux/macOS machine with Docker: following ONLY the README gets Neo4j+Redis up with the configured password, backend on 8010 (`/health` 200), frontend on 3000, fake-mode demo works.

---

### T12 — Secrets and environment hygiene  `[P2]`

**Problem:**
1. A real-looking Neo4j password `pfNeo4j2025!` is committed in `backend/scripts/dev_server.py:15` (`os.environ.setdefault("NEO4J_PASSWORD", "pfNeo4j2025!")`) and `backend/scripts/explore_graph.py:8`. It's also a third conflicting default alongside `config.py:27` (`plasticflower`) and docker-compose's `${NEO4J_PASSWORD}`.
2. `.env.example` is missing vars the code reads: `PLASTICFLOWER_FAKE_LLM`, `PLASTICFLOWER_FAKE_EMBEDDINGS`, `PLASTICFLOWER_SKIP_NEO4J`, `BUILDER_TASK_TIMEOUT`, and any frontend vars — notably `NEXT_PUBLIC_API_URL` (read in `frontend/src/lib/api.ts:22`). It still contains the deprecated `GARDENER_DEBOUNCE_SECONDS`.
3. `frontend/scripts/replayChunks.mjs:6` defaults to port **8000**; the backend is 8010.
4. `backend/app/main.py:82` CORS allows only `http://localhost:3000` — visiting via `http://127.0.0.1:3000` breaks all fetches and SSE. Add `http://127.0.0.1:3000`.
5. `Settings` loads `env_file=".env"` relative to CWD (`config.py:19`) — document/normalize (point it at the repo-root `.env` via an absolute anchor or document that servers must run from repo root; note `dev_server.py` currently papers over this).

**Do:** remove the hardcoded password (require env, fail with a clear message); align on one documented default password story; fix `.env.example` (add missing incl. a `NEXT_PUBLIC_API_URL` note, drop deprecated); fix replay port; widen CORS to 127.0.0.1. **Note to owner:** if `pfNeo4j2025!` was ever used on a reachable instance, rotate it — removing it from HEAD does not remove it from git history.

**Accept:** `grep -r "pfNeo4j2025" .` (excluding `.git`) → empty; every env var read in code (`grep -rE "os.environ|getenv|NEXT_PUBLIC_" backend/app frontend/src`) appears in `.env.example` or is documented; `npm run replay` hits 8010; app works from `127.0.0.1:3000`.

---

### T13 — Add CI  `[P2]` `Depends on: T2, T4 (must be green first)`

**Problem:** no `.github/workflows`, Makefile, or pre-commit — nothing runs the existing pytest/vitest/eslint/tsc suites, which is how a repo that doesn't import got committed.

**Do:** add `.github/workflows/ci.yml` with two jobs:
- **backend**: Python 3.11, install per T10's manifest, `python -c "import app.main"` (cheap boot check), `pytest`.
- **frontend**: Node 20, `npm ci`, `npx tsc --noEmit`, `npm run lint`, `npm run test`, `npm run build`.
Trigger on push + PR to main. No services needed (unit tests use fakes). Optionally add a `ruff check` step for the backend (add config if so).

**Accept:** workflow file passes on the repo's CI for a branch where Phase 0 is merged.

---

## Phase 3 — docs and dead code

### T14 — Make README and GEMINI.md tell the truth  `[P3]`

**Problem:**
- `README.md:26-27` lists top-level `_dev/` and `_discovery/` directories. **Branch update:** these exist in the `review/local-backend-additions` snapshot and land via T0 — after T0, verify the paths resolve (including `_discovery/_repo/_INDEX.md`) instead of deleting the references. Quick start is Windows-only and skips dependency installation (coordinates with T11). Also fold in or reconcile the `claude/readme-fixes` branch (README voice rewrite + name fix) to avoid conflicting edits.
- `GEMINI.md` (AI-assistant context, so errors actively mislead every agent session): `:96-99` says Builder=`gemini-2.0-flash`, Gardener=`gemini-1.5-pro` — actual: `gemini-2.5-flash` for both (`backend/app/config.py:54-61`); `:120` says similarity threshold 0.85 — actual 0.92 (`config.py:110`, ADR-0008); `:179` says Gardener runs "every ~24 seconds" — actual: ratio-based, 1 Gardener run per 5 Builder chunks with a 5s debounce (`scheduler.py`, ADR-0010). `_docs/_runbook/MVP_DEMO.md:134,197,213` says 90 seconds — also wrong, fix to ratio-based wording.

**Do:** rewrite the README repository-layout section to the real tree; fix the quick start (both platforms, includes installs — coordinate with T11's final commands); correct all GEMINI.md numbers/models/scheduling against `config.py` and the ADRs; fix the runbook's 90s claims.

**Accept:** every path referenced in README/GEMINI.md exists (`grep` the doc for paths and check); every config number quoted matches `config.py` defaults.

---

### T15 — Docs restructure: archive stale, delete duplicates, fix links, corral loose files  `[P3]`

**Problem/Do:**
1. **Pure duplicates:** `_docs/_research/01–04/overview.md` are whitespace-identical to `frontend/_docs/_research/aesthetics/<same>/overview.md`. Delete `_docs/_research/`.
2. **Broken links:** `_docs/LEARNING_GUIDE.md` links `SESSION_STATE.md` five times (lines 15,27,41,45,57) — real file is `_docs/_START_SESSION_STATE.md`; `_docs/_dev/_MVP/SIGN_OFF_REPORT.md:127-133,220` references a `_dev/_plan/...` gate pack absent from the repo — annotate as not-committed.
3. **Mark historical:** add a one-line banner ("Historical planning doc — does not describe the current system, see <link>") to: `_docs/_dev/_MVP/_structure/01_project_structure.md` (describes a never-built structure: Gemini 3 Pro, `agents/prompts/`, `utils/validators.py`, `session/[id]` route, app containers in compose), the `_MVP` planning reports, and `_docs/ARCHITECTURE_ADVISORY.md` (GraphRAG Q&A / Librarian not implemented). Move `_docs/LITE_ARCHITECTURE.md` (separate browser-only project, 3,146 lines, no code here) to `_docs/_archive/`.
4. **Misleading frontend docs:** `frontend/STEM_PETAL_POSITIONING_FIX.md` claims COMPLETE for a feature that was broken (pre-T3/T4) and cites obsolete constants; `ORGANIC_GROWTH.md`/`INTELLIGENT_CLUSTERING.md` document dead code (see T16); `IMPLEMENTATION_PLAN_SAFE_FIXES.md` plans fixes for deleted code and cites a nonexistent `CLEANUP_BLAST_RADIUS_ANALYSIS.md`. Move the 11 loose `frontend/*.md` fix/summary docs into `frontend/_docs/_history/` with a banner, or delete.
5. **Misfiled:** `scripts/manual_test_checklist.md` (a dated test record) → `_docs/_evidence/`. Also update `SIGN_OFF_REPORT.md`'s `_dev/_plan/...` references to the salvaged location `_docs/_filing/_archive/plan_mvp_gates/...`, and triage the 31 diagnostic scripts salvaged into `scripts/` (T0) — most are one-off `debug_*`/`diagnose_*` drivers that belong in `scripts/diagnostics/` or can be deleted.
6. Backend root clutter: move the debug one-offs (`check_*.py`, `demo_10min.py`, `list_models.py`, `setup_vertex.py`, `verify_models_strict.py`, `test_embedding_exclusion.py`) into `backend/scripts/diagnostics/` — delete the ones that are machine-specific/dead: hardcoded `c:\Users\Fab2\...` paths (`check_quota.py:3`, `verify_models_strict.py:4`, `demo_10min.py:143`), old-SDK import (`check_quota.py:6`), hardcoded dead session IDs (`check_ghosts.py`, `check_session.py`, `check_sessions.py`), wrong stream name `'chunks:added'` vs real `'pf:chunks:added'` (`check_redis.py:11,23`).

**Accept:** no broken relative links in `_docs/` (check with a link-checking pass); frontend root contains only README + config; backend root contains only the package, manifests, and `scripts/`/`tests/` dirs; every kept historical doc carries a banner.

---

### T16 — Dead code removal  `[P3]` `Depends on: T4 (keep build green)`

**Problem/Do (verify each with grep before deleting; git preserves history):**
- **Frontend — decision applied: delete** the three unimported layout modules (imported by nothing but their own tests, verified): `src/components/graph/layout/organicGrowth.ts` (303 lines), `intelligentClustering.ts` (205), `collisionDetection.ts` (62) + their tests + the docs claiming they're live (`ORGANIC_GROWTH.md`, `INTELLIGENT_CLUSTERING.md` — coordinate with T15). *If the owner wants them reintegrated instead, stop and split out a design task.*
- Frontend misc: unused `flowerMap` (`graphRenderer.ts:37`); edges recorded into `updatedNodeIds` (`graphRenderer.ts:227`); write-only `isListeningRef` (`useSpeechRecognition.ts:31`); strip the per-event `console.log`s in `useSSE.ts:130-147` / `useGraphState.ts:83` (or gate behind a debug flag); redundant stale-closure `void refreshGraph()` in `page.tsx:143`.
- Backend: dead config flags `builder_enabled`/`gardener_enabled`/`researcher_enabled`/`librarian_enabled` (`config.py:140-163`, never read — either wire them up or delete flags + their `.env.example` lines; there is no Librarian code at all); unused Redis streams `STREAM_GARDENER_COMPLETE` consumer-less / `STREAM_NODES_CREATED` unused (`redis_streams.py:29-30`); unused imports (`requests` in `llm.py:16` and `embeddings.py:15`, `types` in `llm.py:15`); duplicate `__all__` entries (`services/__init__.py:140-141`, `models/__init__.py:68-69`); copy-pasted duplicate parse block `tavily_mcp.py:155-187`; unused `relationships_after_nodes` (`scheduler.py:417`) and write-only `_active_sessions` (`scheduler.py:137-146`); unused `run_similarity`/`SimilarityResult` exports; no-op branch `llm.py:136-139`; `print()` → logger in `sse_manager.py:80` and downgrade the DIAGNOSTIC/TIMING `logger.warning` spam in `scheduler.py:289-391` to `debug`; double chunk-save (`api/chunks.py:84` + `builder_service.py:177` — keep one); `export.py:264-279` builds a fresh Gemini client per export — reuse the `llm.py` singleton, and `export.py:355` hardcodes the model — use settings.

**Accept:** backend `pytest` + import checks green; frontend `tsc`/`test`/`build` green; `grep` confirms no references to deleted symbols remain.

---

## Suggested agent batches

- **Batch 1 (serial):** T0 → T2 → T3 → T4 (T1 is subsumed by T0)
- **Batch 2 (parallel after Batch 1):** T5, T6, T7, T8, T9
- **Batch 3 (parallel):** T10, T11, T12 → then T13
- **Batch 4 (parallel, last — touches files others edit):** T14, T15, T16

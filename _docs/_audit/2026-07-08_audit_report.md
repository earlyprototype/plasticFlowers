# plasticFlower — Full Repository Audit

**Date:** 2026-07-08
**Scope:** entire repository — backend, frontend, docker, scripts, docs, git hygiene
**Method:** every finding below was verified empirically, not just read: backend installed into a clean Python 3.11 venv and imported/exercised; frontend `npm install` + `tsc --noEmit` + `vitest run` + `next build`; docs cross-checked against code with grep/diff.

**Companion file:** [`2026-07-08_remediation_tasks.md`](./2026-07-08_remediation_tasks.md) — self-contained task briefs (T1–T16) ready to hand to agents.

---

## Executive summary

The idea is sound and a real working core exists — but **neither half of the app currently runs**:

1. **The backend cannot start at all.** `app/models/graph.py:17` imports `from .research import ReferenceNode`; the module is actually `reference.py`. Every entry point (API server, all tests, most scripts) dies on this one line. `research.py` never existed in git history, so this was committed broken.
2. **The frontend cannot be built for production.** `next build` fails; `tsc --noEmit` reports 37 errors. 4 of 72 unit tests fail.
3. **The single biggest structural problem is a phantom API contract:** large parts of both halves were written against a `Flower.member_ids` field that **neither the backend Pydantic model nor the API response has ever contained**. On the backend, flower creation/update/dissolve all raise (`edge_count` required, no `member_ids` field). On the frontend, it causes most of the type errors and a guaranteed runtime `TypeError` the moment a flower appears.
4. **Two whole subsystems are dead code walking:** the Gardener→Researcher pipeline is broken at five independent points, and the flower feature at three — all masked by broad `except Exception:` handlers, so the app *looks* like it's working while features silently never fire.
5. **The dependency manifests contradict each other and the code** (`pyproject.toml` pins the *old* Gemini SDK and an uninstallable FastAPI/starlette combo; the code uses the new `google-genai` SDK).
6. **A credential is committed to git** (`pfNeo4j2025!` in two backend scripts) and the documented startup path is Windows-only.
7. **No CI whatsoever** — which is how items 1–3 got committed.

**What genuinely works** (verified): the Builder slice — chunk ingestion → Gemini extraction (incl. fake mode) → Neo4j persistence → SSE broadcast → frontend rendering. REST endpoints/ports/SSE event names match between frontend and backend (with exceptions noted). Git hygiene is clean (no node_modules/caches/secrets in `.env`; `.gitignore` correct). The 13 ADRs are accurate and the best docs in the repo.

---

## A. Backend (FastAPI / Neo4j / Redis / Gemini)

### Critical — app cannot run

| # | Defect | Evidence |
|---|--------|----------|
| B1 | App cannot import: `from .research import ReferenceNode` but the module is `reference.py` | `app/models/graph.py:17`; `import app.main` → `ModuleNotFoundError` |
| B2 | Circular import `app.agents` ↔ `app.services` (researcher.py → services.llm → services/__init__ → researcher_service → agents) | `agents/__init__.py:14`, `researcher.py:27`, `services/__init__.py:44`, `researcher_service.py:13`; anything importing `app.agents` first raises `ImportError` |
| B3 | Gardener can never create a Flower: constructor omits required `edge_count` and passes nonexistent `member_ids` | `scheduler.py:814-820` vs `models/flower.py:19-26`; verified `ValidationError` |
| B4 | Flower update & dissolve also crash on `member_ids` | `scheduler.py:834` (`ValueError: no field`), `scheduler.py:850` (`AttributeError`) |
| B5 | Fake-mode Gardener crashes on first flower: `FlowerAction.flower_id: str` given `None` | `scheduler.py:559-572` vs `gardener.py:55`; verified `ValidationError` |
| B6 | Auto-research never fires: `ResearchAction` has no `.label` attribute | `scheduler.py:868` vs `gardener.py:78-97`; `AttributeError` swallowed at `scheduler.py:877` |
| B7 | All research calls raise before any network I/O: `tavily_search(include_answer=True)` but the kwarg was removed from the signature; `TypeError` bypasses the `TavilyMCPError`-only fallback | `researcher.py:163-168` vs `tavily_mcp.py:52`; `researcher.py:107` |
| B8 | Manual research endpoint always 500s: `node.entity_type` doesn't exist (field is `inferred_type`) | `api/graph.py:107` vs `models/node.py:19-54` |

### Major

- **B9** `NameError: _logger` in `delete_node` error branch (no module-level logger) — `graph_db.py:122`.
- **B10** Invalid Cypher when filtering by flower **and** status: `AND` clause injected with no `WHERE` — `graph_db.py:195-202`. The unit test passes because it uses a fake driver.
- **B11** `create_relationship` can return `None`, which gets appended and later fed to `RelationshipAddedEvent(payload=None)` → whole chunk marked failed *after* nodes persisted — `builder_service.py:431,452`.
- **B12** Dependency manifests broken three ways: `pyproject.toml` pins `fastapi==0.115.2` + requirements' `starlette>=0.49.1` = **ResolutionImpossible** (verified); pyproject declares legacy `google-generativeai` while the code exclusively uses `google-genai`; pyproject omits `sse-starlette`, `redis`, `numpy`, `httpx`, `httpx-sse`, `requests`. requirements.txt is unpinned and silently drifts (resolves fastapi 0.139 / starlette 1.3 today).
- **B13** Test suite: cannot even be collected (tests import `backend.app...`, which doesn't resolve; plus B1/B2). After patching in a copy: 20 pass, but all 3 `test_llm.py` tests target the **old** SDK (`llm._MODEL`, `genai.configure`, `genai.GenerativeModel` — none exist) and can never pass. No pytest config (`testpaths`, `asyncio_mode`), so loose `test_*.py` scripts get collected too.
- **B14** Gardener completion metrics permanently 0: counts actions `"solidify"`/`"remove"` but the literals are `"confirm"/"prune"/"merge"` — `scheduler.py:447-448` vs `gardener.py:40`.
- **B15** Gardener never runs for sessions with <5 chunks (ratio gate, `builder_service.py:494-512`) so their nodes stay GHOST forever; and the 5s "debounce" **ACKs and discards** batches instead of deferring them — `scheduler.py:241-248`.
- **B16** Reference persistence would fail even if research worked: map-typed property (`vocabulary_suggestion`) rejected by Neo4j; `fetched_at` DateTime never converted on read-back — `graph_db.py:1252,1330-1351`.
- **B17** Gemini research fallback uses retired `google_search_retrieval` API shape (1.5-era); gemini-2.5 needs the `google_search` tool → 400 → confidence-0 stub — `researcher.py:203-211`.
- **B18** **Committed credential** `pfNeo4j2025!` in `backend/scripts/dev_server.py:15` and `backend/scripts/explore_graph.py:8` (git-tracked). Also a third password source-of-truth vs `config.py:27` (`plasticflower`) and docker-compose.
- **B19** Similarity dedup leaks across sessions: vector top-k(5) taken over the **global** index, session filter applied after — dedup quality degrades as DB grows — `similarity.py:71-78`.
- **B20** `print()` on the SSE broadcast hot path; unbounded per-client queues — `sse_manager.py:80,59`.

### Fake/offline mode — traced end-to-end

Builder path works (`PLASTICFLOWER_FAKE_LLM` + `PLASTICFLOWER_FAKE_EMBEDDINGS`), **but still requires live Neo4j and Redis**: `PLASTICFLOWER_SKIP_NEO4J` only skips *startup* — every handler (including `/health`) still calls Neo4j and 500s. Gardener fake path crashes at flower synthesis (B5→B3). Research is bypassed. None of the fake-mode env vars are documented in `.env.example`.

### Minor (selection — full list in task briefs)

Dead config flags (`builder_enabled`, `gardener_enabled`, `researcher_enabled`, `librarian_enabled` — never read; no Librarian exists); dead Redis streams; duplicate `__all__` entries; copy-pasted duplicate parse block in `tavily_mcp.py:155-187`; chunks persisted twice per request; session delete orphans Vocabulary/Checkpoint/Context/Reference/Source nodes; process-wide IPv4 `socket.getaddrinfo` monkey-patch (`main.py:4-8`); `status` parameter shadows `fastapi.status` (`api/graph.py:49`); hardcoded model in `export.py:355` + a fresh Gemini client per export; `gemini_max_output_tokens=131072` exceeds gemini-2.5-flash's 65k cap; naive datetimes in vocabulary.py; a dozen machine-specific debug scripts at backend root (some with hardcoded `c:\Users\Fab2\...` paths and old-SDK imports); `check_redis.py` inspects the wrong stream name; god files (`graph_db.py` 1,417 lines, `scheduler.py` 897).

---

## B. Frontend (Next.js / Cytoscape)

### Critical

| # | Defect | Evidence |
|---|--------|----------|
| F1 | `next build` fails; 37 `tsc` errors. Clusters: `LAYOUT_CONFIG` (has `name`/`numIter`) vs local `LayoutOptions` type (demands `algorithm`/`iterations`); `Flower.member_ids` doesn't exist (≈20 errors incl. cascading implicit-`any`); `.id()`/`.hasClass()` on `NodeCollection` | Verified by running the build; `GraphCanvas.tsx:287`, `layoutConfig.ts:7-40` vs `layoutEngine.ts:9-19`, `stemPetalPositioning.ts:42,97`, `graphRenderer.ts:206-208` |
| F2 | Runtime crash whenever a flower exists: `flower.member_ids.filter(...)` on a field the backend never sends (its Pydantic model strips it). The crash also aborts sync steps 4–5, so the expensive 150k-repulsion layout re-runs on every subsequent sync | `GraphCanvas.tsx:339-341`, `stemPetalPositioning.ts:97`, `backend/app/models/flower.py:19-26` |
| F3 | Flower-membership change detection permanently inert for the same reason (`prev.member_ids \|\| []` always `[]`) | `layoutEngine.ts:90-97` |

### Major

- **F4** `node_corrected` SSE event (backend emits it: `scheduler.py:603-610`) is never subscribed — STT corrections silently dropped — `useSSE.ts:17-32`.
- **F5** `"gardener_cycle"` listed **twice** in `EVENT_TYPES` → two listeners → Gardener counter double-increments — `useSSE.ts:28-29`.
- **F6** `"reconnecting"` connection state is declared, styled, and described on the page, but never set — `useSSE.ts` only sets idle/connecting/open/error.
- **F7** Chunk dispatch can stall forever: needs ≥3 sentences (`[.!?]`) or 1000 chars, but Web Speech output is unpunctuated; the 15s staleness flush only runs on the *next* append (no timer), so a session's final utterance sits in the buffer indefinitely — `useChunkDispatcher.ts:35-41,80-84`.
- **F8** Three whole layout modules are dead code (~570 lines: `organicGrowth.ts`, `intelligentClustering.ts`, `collisionDetection.ts` — imported only by their own tests) while `ORGANIC_GROWTH.md` / `IMPLEMENTATION_SUMMARY_2025-12-31.md` present them as shipped.
- **F9** 4/72 tests fail: orbit-radius tests expect `max(180, 140 + n·25)`; code is `80 + n·15`; an organicGrowth test passes the default value as its "custom" input. Note vitest doesn't type-check, so green tests mask the broken types.
- **F10** Every parentless node is `move()`d (remove+re-add) on **every** sync: `undefined !== null` comparison always true — `graphRenderer.ts:157-159`.
- **F11** Fade-in animation's inline `opacity` style permanently overrides the ghost-node `opacity: 0.15` stylesheet — every new ghost renders fully opaque — `animationController.ts:102-115` vs `layoutConfig.ts:93`.
- **F12** Float animations leak and drift: infinite recursion via `complete:`, captures a stale start position, only stops on removal or flower membership — `animationController.ts:181-220`. (The perf roadmap lists this as HIGH/PLANNED.)
- **F13** Debounced sync races unmount: cleanup only clears the pending timer; an in-flight async callback keeps operating on a possibly-`destroy()`ed cy instance — `GraphCanvas.tsx:281-357,265`.
- **F14** `npm run replay` targets port **8000**; backend is 8010 — `scripts/replayChunks.mjs:6`.
- **F15** `NEXT_PUBLIC_API_URL` is read by the app but absent from `.env.example` (which has zero frontend vars).

### Minor (selection)

Cytoscape stylesheets use `:hover`, which Cytoscape.js doesn't support — hover styles never fire (`layoutConfig.ts:161,196`); malformed SSE event with empty data → `event.payload.id` crash (`useSSE.ts:59-60`); stale-closure `refreshGraph()` on connect (`page.tsx:143`); buffer display reads refs inside `useMemo` so it's perpetually stale (`MicControl.tsx:66-69`); chunk timestamps are seconds-since-page-load, not session start, skewing VTT exports; ExportPanel active with empty `sessionId` → requests to `/api/sessions//export/...`; backend CORS allows only `localhost:3000` so `127.0.0.1:3000` breaks everything; no-op module-level fcose registration guard; local `cytoscape-fcose.d.ts` `any`-shadows the real installed typings; 3 `react-hooks/exhaustive-deps` warnings; `console.log` on every SSE event in production; no auto-restart when Chrome ends continuous speech recognition.

---

## C. Infra, scripts, docs, git

### Critical

- **I1 — Startup is Windows-only.** `scripts/` contains only PowerShell (`start_mvp.ps1`, `restart_clean.ps1`); no bash/Make equivalent; README's quick start never installs dependencies. A fresh clone on macOS/Linux cannot start the project by following any documented path. `scripts/START_SERVERS.md:48` even recommends `taskkill /F /IM node.exe; taskkill /F /IM python.exe` — kills every node/python process on the machine.
- **I2 — Documented Docker startup launches Neo4j with an empty password.** Compose reads `${NEO4J_PASSWORD}` from the environment or `docker/.env`, never the root `.env`; every doc says plain `cd docker && docker compose up -d` → `NEO4J_AUTH=neo4j/` and a broken healthcheck. `start_mvp.ps1` also auto-copies `.env.example` → `.env` and proceeds with the placeholder password.

### Major

- **I3** README describes top-level `_dev/` and `_discovery/` directories that don't exist; cites `_discovery/_repo/_INDEX.md` (no such path).
- **I4** **Zero CI/automation** — no `.github/workflows`, no Makefile, no pre-commit — despite real pytest/vitest/eslint suites existing.
- **I5** `GEMINI.md` (the AI-assistant context file) contradicts the code: says models `gemini-2.0-flash`/`gemini-1.5-pro` (actual: `gemini-2.5-flash` both, `config.py:54-61`); threshold 0.85 (actual 0.92); Gardener "every ~24s" (actual: ratio 1:5 + 5s debounce; the runbook says 90s — three docs, three answers, none matching the code).
- **I6** `_docs/_dev/_MVP/_structure/01_project_structure.md` — the file README points to for "structure expectations" — is a pre-implementation spec that was never built (Gemini 3 Pro, `agents/prompts/*.txt`, `utils/validators.py`, `session/[id]` route, app containers in compose…).
- **I7** Broken internal links: `LEARNING_GUIDE.md` → nonexistent `SESSION_STATE.md`; `SIGN_OFF_REPORT.md` → an entire `_dev/_plan/` gate pack that isn't in the repo.

### Minor

Duplicated research docs (`_docs/_research/*` ≡ `frontend/_docs/_research/aesthetics/*`, whitespace-only diff); `START_SERVERS.md` documents `NEO4J_USER` (real var: `NEO4J_USERNAME`); obsolete compose `version:` key; compose still loads the GDS plugin that ADR-0001 decided against; content-free `docker/README.md`; deprecated `GARDENER_DEBOUNCE_SECONDS` still in `.env.example`; ~12 debug one-offs at backend root and 11 loose fix/summary MDs at frontend root.

### Git hygiene — clean ✅

No secrets in tracked files beyond B18; `.gitignore` correct (`.env` excluded with working `!.env.example`, no node_modules/`__pycache__`/`.next` tracked); MIT license fine; short clean history.

### Docs inventory

- **Keep (accurate, valuable):** `_docs/_dev/ADR/` (13 ADRs — verified against code, they match), `_docs/_runbook/MVP_DEMO.md` (minor fixes needed), `CYPHER_PATTERNS.md`, `VALIDATED_PATTERNS.md`, `SOLUTIONS_LOG.md`, fixtures, `.env.example` (mostly), the `_docs/_evidence/` review records.
- **Stale/misleading (label as historical or fix):** README layout+quickstart, `GEMINI.md` specifics, `_MVP` planning tree, `ARCHITECTURE_ADVISORY.md` (describes GraphRAG Q&A / Librarian — none implemented), `frontend/STEM_PETAL_POSITIONING_FIX.md` + `ORGANIC_GROWTH.md` + `INTELLIGENT_CLUSTERING.md` (claim shipped features that are broken or dead code), `IMPLEMENTATION_PLAN_SAFE_FIXES.md` (plans fixes for code that no longer exists).
- **Duplicates:** `_docs/_research/` — delete in favour of `frontend/_docs/_research/aesthetics/`.
- **Separate project:** `LITE_ARCHITECTURE.md` (3,146 lines, browser-only design with no code here) — archive or move to its own repo.

---

## D. How did it get this broken? (root causes)

1. **No CI.** The fatal import typo, the failed build, and the failing tests would all have been caught by a 5-minute pipeline.
2. **Broad `except Exception:` handlers** around every agent cycle turned hard crashes into silent no-ops — flowers and research have likely *never* worked post-refactor, without any visible error.
3. **Contract drift without a source of truth:** the `member_ids` field exists in scheduler-internal dicts, was designed into the frontend, but never added to the Pydantic model or API — and nothing (types, tests, schema) spans the boundary to catch it.
4. **Docs written before/instead of code** (aspirational specs presented as current truth) plus refactors that didn't update tests, docs, or manifests.

## E. Decisions needed from the owner

These change the task list, so they're flagged rather than assumed (tasks note the default taken):

1. **Dead layout modules** (`organicGrowth`, `intelligentClustering`, `collisionDetection`, ~570 lines + tests + docs): delete, or reintegrate? *Default in tasks: delete (git preserves them).*
2. **Researcher/Tavily feature:** fix (T5) or feature-flag off for v1? It's 5 independent bugs deep. *Default: fix.*
3. **Primary dev platform:** keep PowerShell as first-class and add bash, or move to a cross-platform Makefile/compose-based flow? *Default: add bash + Make targets alongside the .ps1.*
4. **`LITE_ARCHITECTURE.md`:** archive here or split to its own repo? *Default: move under `_docs/_archive/`.*
5. **Neo4j password `pfNeo4j2025!`:** if this was ever used on a reachable instance, rotate it. Removal from code is in T12 regardless.

# DrJones Recon Brief: `earlyprototype/plasticFlowers`
*Scout: Ranger Elytra (Paused-Repo Survey Detachment) | State: `paused_prototype` | Recorded: 2026-11-26T21:48:39Z*

## Summary
plasticFlowers turns live speech into a knowledge graph. A Next.js canvas streams updates from a FastAPI backend. Builder extracts ideas and links, Gardener groups them into flowers, and Researcher adds references. Neo4j stores sessions and Redis coordinates background work. The last 15 commits added cartography and exportable session portraits, then fixed shared configuration, Redis idle timeouts, and references with zero sources. The inspected history ends at `93e6396` on 2026-07-13.

- **CI / Test Command:** `From the repo root after `make setup`, run `make test`. It runs `../.venv/bin/python -m pytest` from `backend/` and `npm run test` (`vitest run`) from `frontend/`. GitHub Actions uses Python 3.11 and Node 20. Its backend sequence is `pip install -e '.[dev]'`, `python -c "import app.main; import app.agents; import app.services"`, then `pytest`. Its frontend sequence is `npm ci`, `npx tsc --noEmit`, `npm run lint`, `npm run test`, then `npm run build`. The separate live-stack check is `python backend/scripts/smoke_test.py --base http://127.0.0.1:8010`.`
- **Risks / Blockers:** This was a read-only inspection of the detached checkout. I inspected the test suites and CI definitions without running them. The live smoke test creates and deletes a session and writes a JSON evidence file. Test results and live-stack behavior at this commit remain unverified. The final working tree was clean.

## Recommended Actions
### [tier1_deterministic_fix] Keep buffered speech with the session that recorded it
- **Rationale:** The microphone stays mounted when the user switches sessions. The dispatcher keeps its buffer but reads the current session ID at send time. A sentence recorded in session A can therefore land in session B when the 15-second timer fires. [Dispatcher](/C:/gant-ops/readonly_refs/earlyprototype__plasticFlowers/frontend/src/hooks/useChunkDispatcher.ts:165)
- **Acceptance Criteria:** A regression test records a short utterance in A, switches to B before the timer fires, then records another utterance. Each session receives only its own text.

### [tier1_deterministic_fix] Keep failed transcript submissions available for retry
- **Rationale:** The dispatcher clears a chunk before awaiting the POST. On failure it displays an error and discards the text. The existing tests cover buffer timing and draining, but stop before the network call. [Submission path](/C:/gant-ops/readonly_refs/earlyprototype__plasticFlowers/frontend/src/hooks/useChunkDispatcher.ts:173)
- **Acceptance Criteria:** A test rejects the first submission while new speech arrives. The failed chunk stays recoverable with its original session and timestamps. Retrying preserves both chunks and produces one stored copy of each.

### [tier1_deterministic_fix] Make the Windows quick start report actual readiness
- **Rationale:** The README sends Windows users straight to the PowerShell launcher. It invokes `python -m uvicorn` and `npm run dev` without installing project dependencies, catches a failed backend health check, then prints `MVP Ready!` without checking the frontend. [Windows launcher](/C:/gant-ops/readonly_refs/earlyprototype__plasticFlowers/scripts/start_mvp.ps1:128)
- **Acceptance Criteria:** On a clean Windows checkout, the documented setup and `-FakeMode` launch bring up both the backend health endpoint and the frontend. A failed child process produces a nonzero exit and identifies the failed service.

### [tier2_discretionary_finish] Save the portrait title with its session
- **Rationale:** A user can title and export a session portrait, but reopening the session clears the title. The page explicitly marks persistence as unfinished. [Portrait state](/C:/gant-ops/readonly_refs/earlyprototype__plasticFlowers/frontend/src/app/page.tsx:120)
- **Acceptance Criteria:** Rename a portrait, reload the app, reopen the session, and export a PNG. The saved title appears on both the canvas and the PNG. Older untitled sessions keep their generated titles.

### [human_decision_required] Decide whether fully offline live capture is a product requirement
- **Rationale:** The README promises “no cloud.” Normal extraction sends transcript-derived prompts to Gemini, and Researcher uses Tavily with a Gemini fallback. Local graph storage and a fake inference demo are already implemented. The open choice is whether real speech-to-graph processing must also work offline. [README](/C:/gant-ops/readonly_refs/earlyprototype__plasticFlowers/README.md:3) · [Research providers](/C:/gant-ops/readonly_refs/earlyprototype__plasticFlowers/backend/app/agents/researcher.py:102)
- **Acceptance Criteria:** The author records which capture, extraction, and research steps may contact a provider. The README states what leaves the machine in each supported mode.

> **Field Dispatch:** HQ, the microphone can deliver yesterday’s sentence to the next briefing. Ranger Elytra has marked the fault while the General defends democracy in Project Zomboid.

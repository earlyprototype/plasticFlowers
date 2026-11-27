# Capture and portrait verification

Tested on Windows on 27 November 2026 with Python 3.11.3, Node.js 24.15.0 and Windows PowerShell. The worktree initially had no virtual environment, frontend dependencies or root `.env`.

## Setup and regression tests

| Working directory | Command | Outcome |
| --- | --- | --- |
| Root | `python -m venv .venv` | Created the virtual environment. |
| Root | `.\.venv\Scripts\python.exe -m pip install -e 'backend[dev]'` | Installed the declared dependencies. The first attempt could not fetch the build dependencies inside the sandbox. |
| Root | `npm.cmd ci --prefix frontend --no-audit --no-fund` | Installed 380 packages from the lockfile. |
| Root | `.\.venv\Scripts\python.exe -m pytest backend/tests/test_chunk_retry.py -q` | 4 passed. Replaying an accepted request originally produced a different chunk ID. |
| Root | `.\.venv\Scripts\python.exe -m pytest backend/tests/test_session_portraits.py -q` | 3 passed. A title-only PATCH originally returned HTTP 422. |
| Frontend | `npm.cmd test -- src/hooks/useChunkDispatcher.test.ts src/hooks/useSpeechRecognition.test.ts` | 17 passed, including late recognizer results, independent sessions and retry timestamps. |
| Frontend | `npm.cmd test -- src/components/graph/rendering/portraitOverlay.test.ts` | 12 passed, including the title drawn to the display and export canvases. |
| Root | `python scripts/tests/test_windows_launcher.py -v` | 5 passed. The launcher waited through HTTP 503 responses, reported child and Compose failures, rejected the placeholder password and stopped the sibling after a child exit. |
| Backend | `..\.venv\Scripts\python.exe -c "import app.main; import app.agents; import app.services"` | Exit 0. |
| Backend | `..\.venv\Scripts\python.exe -m pytest -q` | 99 passed. |
| Frontend | `npm.cmd test` | 181 passed across 11 files. |
| Frontend | `node node_modules/typescript/bin/tsc --noEmit --incremental false` | Exit 0. |
| Frontend | `npm.cmd run lint` | Exit 0 with no warnings or errors. |
| Frontend | `npm.cmd run build` | Exit 0. Next.js generated five static pages. The sandbox first blocked worker creation with `spawn EPERM`. |

## Windows launcher

Ran `powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/start_mvp.ps1 -FakeMode -NoBrowser` with a disposable root configuration. Docker Compose returned HTTP 500 inspecting the Neo4j image. The launcher identified Compose, Neo4j and Redis, exited 1 and withheld the ready message. `docker desktop start --timeout 90` timed out and `wsl --status` reported that WSL was absent. A successful launch with the declared Docker containers remains unverified.

Ran the same command with a Compose stand-in, an in-memory session repository and the backend's Neo4j skip switch. The actual Uvicorn health endpoint returned HTTP 200 with `neo4j: skipped`. The actual Next.js homepage returned HTTP 200. The launcher then printed `MVP Ready!`. Terminating the test backend after readiness made the launcher identify the backend, stop the frontend and exit 1.

## Browser checks

In Chrome, a simulated microphone recorded a sentence in A. The page switched to B with A still buffered and recorded a second sentence. The transport fixture accepted A and dropped its response. Retrying in the UI produced three POSTs with two distinct request IDs. A's retry carried its original session, text and timestamps.

Using the live app processes and the in-memory session repository, Chrome saved `Glasshouse notes`, reloaded, reopened the session and downloaded a 1740-by-1276 PNG. The canvas and the export drew the saved title. A separate legacy session had no stored title and drew `Session legacy` in both outputs.

The repeatable browser test uses an HTTP fixture for sessions and the installed Chrome browser. These commands passed against the production build.

1. From the root, run `.\.venv\Scripts\python.exe -m pip install playwright`.
2. From `frontend`, run `node node_modules/next/dist/bin/next start --hostname 127.0.0.1 --port 3000` after the build.
3. From the root, run `.\.venv\Scripts\python.exe scripts/tests/portrait_browser.py`. Both title checks and both PNG downloads passed.

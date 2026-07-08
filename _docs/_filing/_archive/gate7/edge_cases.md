# Gate 7 Edge Case Validation

> **Purpose:** Track execution of the Gate 7 edge-case suite.
> **Mode:** Intended for real Gemini + running stack (backend, frontend, Neo4j).

## How to run
- Start stack via `.\scripts\start_mvp.ps1` (real mode).
- Use browser at `http://localhost:3000` unless noted.
- Capture notes inline and keep artefacts (exports, console logs) alongside this file.

## Results

| Edge Case | Steps | Expected | Result | Notes |
|-----------|-------|----------|--------|-------|
| SSE reconnect badge transition | Start session → stop backend → restart → observe badge `open → reconnecting → open` | Badge transitions and graph resync | Pending |  |
| Chunk to ended session (409) | End session then POST chunk | HTTP 409 | Pending |  |
| Empty-session exports | New session, no chunks, export JSON/VTT/MD | 200 responses, empty transcript, empty graph | Pending |  |
| VTT timestamp format | Inspect VTT export after 1–2 chunks | Lines use `HH:MM:SS.mmm` | Pending |  |
| Malformed LLM payloads | Temporarily set `PLASTICFLOWER_FAKE_LLM=1`, submit chunk | No crash; SSE shows chunk_processed (error null) | Pending |  |
| Multi-tab sync | Open two tabs on same session, submit chunks | Both tabs receive SSE updates | Pending |  |
| 200+ nodes FCose perf | Replay/load large session (200–500 nodes) | Canvas remains responsive; layout < 5s | Pending |  |

## Follow-up
- Attach console logs or HAR files for SSE reconnect and multi-tab steps.
- Keep any failing artefacts (screenshots, exports) in this folder for director review.




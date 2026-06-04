# Gate 4 — Builder End-to-End Loop

> **Objective:** Speech (or replay) produces chunks; Builder extracts nodes/relationships; SSE renders live in Cytoscape
> **Entry:** Gate 3 passed (graph persistence operational)
> **Exit:** Full loop works: speech → chunk → Builder → Neo4j → SSE → Cytoscape

---

## Serial Dependencies (must complete in order)

1. **LLM client** — Gemini 3 Pro client with structured JSON output
2. **Builder agent** — Prompt + JSON validation + error handling
3. **Chunk endpoint** — `POST /sessions/{id}/chunks` triggers Builder
4. **SSE manager** — Broadcast `node_added`, `relationship_added` events
5. **Frontend SSE handler** — Connect, parse, route to state manager
6. **Cytoscape rendering** — Nodes/edges appear live

---

## Parallel Lanes (can run simultaneously)

| Lane | Work | Owner |
|------|------|-------|
| A | LLM client + Builder agent implementation | Backend dev |
| B | SSE manager + chunk endpoint | Backend dev |
| C | Frontend SSE handler + state manager | Frontend dev |
| D | Cytoscape integration + FCose layout | Frontend dev |
| E | Speech capture + chunk dispatcher | Frontend dev |

**Sync points:**
- Lane A must complete before chunk endpoint can trigger Builder
- Lanes B + C must align on SSE event payloads (locked in Gate 2)
- Lane D depends on Lane C for state updates

---

## Deliverables

| Deliverable | Acceptance Criteria |
|-------------|---------------------|
| `backend/app/services/llm.py` | Gemini 3 Pro client, JSON mode |
| `backend/app/agents/builder.py` | Builder prompt + output parsing |
| `backend/app/services/sse_manager.py` | Broadcast to connected clients |
| `backend/app/api/chunks.py` | Accepts chunk, triggers Builder, broadcasts |
| `frontend/src/hooks/useSSE.ts` | SSE connection + reconnect logic |
| `frontend/src/hooks/useGraphState.ts` | State Maps + update handlers |
| `frontend/src/components/graph/GraphCanvas.tsx` | Cytoscape + FCose |
| `frontend/src/hooks/useSpeechRecognition.ts` | Web Speech API wrapper |
| `frontend/src/hooks/useChunkDispatcher.ts` | Buffer + dispatch chunks |

---

## Builder Agent Requirements

Per `_docs/_dev/_MVP/_prompts/01_builder.md`:

| Requirement | Implementation |
|-------------|----------------|
| Input | Chunk text + existing node labels (grouped by type) |
| Output | JSON: `{ nodes: [...], relationships: [...] }` |
| Node status | All new nodes created as `ghost` |
| Relationship scope | Chunk-local only (both endpoints in same chunk or existing) |
| Error handling | Invalid JSON → log, discard, continue |

---

## SSE Events (Builder-triggered)

| Event | Payload | When |
|-------|---------|------|
| `node_added` | Full Node object | Builder extracts new node |
| `relationship_added` | Full Relationship object | Builder extracts relationship |
| `chunk_processed` | `{ chunk_id }` | Builder completes chunk |

---

## Verification Checklist

- [ ] LLM client returns valid JSON
- [ ] Builder extracts nodes from sample chunk
- [ ] Builder extracts relationships from sample chunk
- [ ] Pre-Builder similarity check prevents duplicates
- [ ] SSE events broadcast correctly
- [ ] Frontend receives and parses SSE events
- [ ] State manager updates Maps on events
- [ ] Cytoscape renders nodes/edges (per `02_visual_design.md`)
- [ ] FCose layout runs incrementally (no viewport reset)
- [ ] White canvas background (RSA Animate aesthetic)
- [ ] Ghost nodes: 70% opacity, grey dashed border
- [ ] Solid nodes: black solid border
- [ ] Node entry animation (scale + fade)
- [ ] Edge entry animation (draw-in effect)
- [ ] Speech capture works in Chrome (en-GB)
- [ ] Chunk dispatcher buffers ~3-5 sentences

---

## Handover to Gate 5

**Pass when:**
1. All verification items checked
2. End-to-end demo: speak → see nodes appear
3. Replay harness can feed recorded chunks

**Handover artefact:** Working Builder loop; graph grows live from speech

---

## Technical Decisions (from Challenges Report)

Per Director review of `_docs/_dev/_MVP/_TECHNICAL_CHALLENGES.md`:

| Decision | Detail |
|----------|--------|
| **Similarity check** | Option B — relaxed. Builder creates optimistically; Gardener deduplicates. |
| **Latency target** | P90 <10s, hard cap 15s. Skip chunk gracefully if exceeded. |
| **Layout priority** | Stability over speed. Use `fit: false`, pin existing nodes, 400-500ms animations. |
| **Instrumentation** | Required from day one. Track roundTrip, llmCall, parseFailure, timeout. |

### Required Mitigations

| Mitigation | Priority |
|------------|----------|
| Gemini structured output mode | **Critical** |
| Schema validation before persist | **Critical** |
| Retry on parse failure (1x) | High |
| Failure logging for prompt tuning | High |
| FCose `fit: false` + pinning | **Critical** |
| 15s timeout with graceful skip | High |

---

## Tools to Leverage (Mandatory)

Gate 4 involves LLM integration and real-time streaming — use available tools aggressively.

### Before Implementation

| Task | Tool | Query |
|------|------|-------|
| Gemini JSON mode | `get-library-docs` | "Gemini structured output JSON mode" |
| SSE in FastAPI | `get-library-docs` | "FastAPI SSE streaming sse-starlette" |
| Cytoscape basics | `get-library-docs` | "Cytoscape.js adding nodes edges" |
| FCose layout | `web_search` | "Cytoscape FCose incremental layout" |
| Web Speech API | `web_search` | "Web Speech API continuous recognition" |

### During Implementation

| Situation | Tool | Action |
|-----------|------|--------|
| LLM output parsing issues | `web_search` | Search for "Gemini JSON parsing errors" |
| SSE not connecting | `web_search` | Search error message |
| Cytoscape layout jumps | `web_search` | "FCose fit false animate" |
| Speech recognition stops | `web_search` | "webkitSpeechRecognition continuous mode" |

### Reference Patterns

| Pattern | Source |
|---------|--------|
| LLM extraction prompts | `_discovery/_repo/graphrag/_relevance.md` |
| Real-time streaming | `_discovery/_repo/graphiti/_relevance.md` |
| Builder prompt template | `_docs/_dev/_MVP/_prompts/01_builder.md` |

### Replay Harness (Recommended)

Build a replay harness early in Gate 4 to allow testing without live speech:
- Record transcript chunks from a real session
- Replay them via `POST /chunks` at controlled intervals
- Enables repeatable testing and demos

---

## Reference

- [Builder Prompt](../../_docs/_dev/_MVP/_prompts/01_builder.md)
- [API Contracts](../../_docs/_dev/_MVP/_api/01_contracts.md)
- [Frontend Data Flow](../../_docs/_dev/_MVP/_frontend/01_data_flow.md)
- [**Visual Design Spec**](../../_docs/_dev/_MVP/_frontend/02_visual_design.md) ← **Required for Cytoscape styling**
- [High-Level Plan](../overview/highplan.md)


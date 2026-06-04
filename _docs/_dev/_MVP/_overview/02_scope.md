# plasticFlower — MVP Scope

---

## In MVP

| Feature | Notes |
|---------|-------|
| Web Speech API transcription | Free, browser-native |
| Deepgram option (switchable) | Abstracted provider |
| Builder Agent | Gemini 3 Pro, low thinking |
| Pre-Builder similarity check | Reduces duplicates |
| Gardener Agent (90s interval) | Periodic review, merge, cluster, prune |
| Neo4j storage | Local instance |
| Cytoscape.js + FCose visualisation | Live updates via SSE |
| Flower clustering | LLM semantic + edge count density |
| Ghost/Solid node states | Visual feedback |
| Session save/restore | User-named sessions |
| Auto-reconnect | On connection drop |
| Export | JSON, transcript (plain + timestamped), Markdown summary |
| Z-level filtering | Manage visual complexity |

---

## Post-MVP

| Feature | Notes |
|---------|-------|
| Historian Agent | Meta-Flowers for long talks |
| Linker Agent | Real-time cross-chunk relationships |
| Contradiction detection | Flag and surface contradictions (post-MVP) |
| Accessibility | Screen reader support |
| Offline mode | Local-first operation |
| Advanced exports | GraphML, Mermaid, CSV |
| Full density metrics | Beyond simple edge count |

---

## Excluded (All Phases)

| Feature | Reason |
|---------|--------|
| Multi-speaker diarisation | Single speaker use case |



# plasticFlower — Key Decisions

---

## Technology Choices

| Component | Choice | Rationale |
|-----------|--------|-----------|
| STT (primary) | Web Speech API | Free, zero setup, browser-native |
| STT (upgrade) | Deepgram | Better quality when needed |
| LLM | Gemini 3 Pro | Thinking levels, large context |
| Graph store | Neo4j (local) | Native vectors, real-time queries |
| Visualisation | Cytoscape.js + FCose | Compound nodes, stable live layout |
| Frontend | Next.js | React ecosystem |
| Backend | FastAPI | Python async, WebSocket support |

---

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Schema | Emergent (LLM-determined) | Domain-agnostic flexibility |
| Gardener interval | 90 seconds | Balance responsiveness vs cost |
| Flower threshold | 3+ nodes, 2+ internal connections | Meaningful clusters |
| Confidence decay | -0.1 per cycle, prune at ≤0.2 | Noise removal |
| Latency target | ≤10 seconds | Acceptable for MVP |
| Relationship types | 5 abstract categories + natural language | Balance constraint vs flexibility |
| Flower density | LLM semantic + simple edge count | Both dimensions matter |
| Flower bridges | Derived at query-time | Simpler, always accurate |
| Hosting | Local | No cloud dependencies |
| Session naming | User-provided | With timestamp fallback |

---

## UI Decisions

| Aspect | Choice |
|--------|--------|
| Aesthetic | Clean, modern, ultra visual typography |
| Theme | TBD |
| Density | Low — information breathes |



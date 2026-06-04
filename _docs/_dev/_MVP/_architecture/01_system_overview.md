# plasticFlower — System Architecture

---

## High-Level Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                          plasticFlower                              │
│                                                                     │
│   AUDIO IN                                                          │
│      ↓                                                              │
│   ┌─────────────────┐                                               │
│   │ STT Provider    │  Web Speech API / Deepgram (abstracted)       │
│   └────────┬────────┘                                               │
│            ↓ text chunks                                            │
│   ┌─────────────────┐                                               │
│   │ Similarity      │  Check Neo4j vector index before creating     │
│   │ Check           │                                               │
│   └────────┬────────┘                                               │
│            ↓                                                        │
│   ┌─────────────────┐                                               │
│   │ Builder Agent   │  Gemini 3 Pro (low thinking)                  │
│   │                 │  → Extract nodes, chunk-local relationships   │
│   └────────┬────────┘                                               │
│            ↓                                                        │
│        NEO4J ←───────────────────────────────────────┐              │
│            ↑                                         │              │
│   ┌────────┴────────┐                                │              │
│   │ Gardener Agent  │  Gemini 3 Pro (high thinking)  │              │
│   │                 │  Every 90 seconds              │              │
│   │                 │  → Merge, cluster, prune       │              │
│   └─────────────────┘                               │              │
│            │                                                        │
│            ↓ SSE updates                                            │
│   ┌─────────────────┐                                               │
│   │ Cytoscape.js    │  FCose layout                                 │
│   │ Visualisation   │  Ghost → Solid node states                    │
│   └─────────────────┘                                               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| **STT Provider** | Convert audio to text chunks |
| **Similarity Check** | Prevent duplicate node creation |
| **Builder Agent** | Fast extraction of nodes and relationships |
| **Gardener Agent** | Periodic review, merge, cluster, prune |
| **Neo4j** | Graph storage with vector index |
| **SSE Stream** | Push updates to frontend |
| **Cytoscape.js** | Render and animate the graph |

---

## Data Flow

1. User speaks → Browser captures audio
2. STT converts to text chunk (~3-5 sentences)
3. Similarity check against existing nodes
4. Builder Agent extracts concepts and relationships
5. New data written to Neo4j
6. Change triggers SSE event
7. Frontend updates visualisation
8. Every 90s: Gardener reviews full graph



# plasticFlower - Reference Repository Index

> **Purpose:** Curated list of open-source projects relevant to plasticFlower development
> **Last Updated:** December 2024

---

## Priority Matrix

| Priority | Repository | Tag | Key Value |
|----------|------------|-----|-----------|
| **HIGH** | Graphiti | real-time-kg | Real-time KG updates, entity extraction |
| **HIGH** | GraphRAG | llm-extraction | LLM prompts, community detection |
| **MEDIUM** | knowledge-graph-kit | internal | Merge logic, validation patterns |
| **MEDIUM** | KinGVisher | visualization | Web-based KG exploration UX |
| **MEDIUM** | Open Semantic Explorer | visualization | Entity-centric navigation |
| **MEDIUM-LOW** | Graphster | llm-extraction | Schema patterns (reference only) |
| **LOW** | Pykg2vec | embeddings | Post-MVP embedding enhancement |

> **Note:** knowledge-graph-kit is evaluated as a peer project. Author familiarity is considered only as a tiebreaker.

---

## Directory Structure

```
_discovery/_repo/
├── _INDEX.md                    # This file
├── _CLONE.ps1                   # PowerShell script to clone external repos
│
├── internal/                    # YOUR EXISTING PROJECTS
│   └── knowledge-graph-kit/
│       └── _relevance.md        # Analysis (HIGH priority)
│
├── real-time-kg/
│   └── graphiti/
│       └── _relevance.md        # Analysis document
│
├── llm-extraction/
│   ├── graphrag/
│   │   └── _relevance.md
│   └── graphster/
│       └── _relevance.md
│
├── visualization/
│   ├── kingvisher/
│   │   └── _relevance.md
│   └── open-semantic-graph-explorer/
│       └── _relevance.md
│
└── embeddings/
    └── pykg2vec/
        └── _relevance.md
```

---

## Peer Project: knowledge-graph-kit

> **Location:** `_discovery/knowledge-graph-kit/`
> **Priority:** MEDIUM (evaluated objectively as peer)
> **Familiarity:** Author knows codebase (tiebreaker only)

### Strengths
- Clean merge/deduplication implementation
- Well-structured YAML configuration
- Proven provenance tracking

### Weaknesses
- Batch-oriented (no streaming)
- Schema-first (not emergent)
- File-based storage (no vectors)
- No clustering/community detection

### vs Other HIGH Priority Projects

| Comparison | Result |
|------------|--------|
| vs **Graphiti** | Graphiti has real-time streaming; knowledge-graph-kit is batch |
| vs **GraphRAG** | GraphRAG has community detection; knowledge-graph-kit has none |

### What to Extract

| Component | File | Value |
|-----------|------|-------|
| Merge logic | `core/graph_manager.py:148-204` | Gardener deduplication |
| Validation | `core/graph_manager.py:218-235` | Graph integrity |

### What to Skip

Architecture, storage layer, entity type system, visualisation library — all misaligned with plasticFlower's streaming/emergent paradigm.

---

## What to Study First

### For Builder Agent Development
1. **Graphiti** → Entity extraction patterns, Neo4j operations
2. **GraphRAG** → LLM prompt engineering for entity/relationship extraction

### For Gardener Agent Development
1. **GraphRAG** → Community detection, hierarchical summarisation
2. **Graphiti** → Deduplication logic, temporal handling

### For Frontend Development
1. **KinGVisher** → Details panel UX, search/filter patterns
2. **Open Semantic Explorer** → Entity-centric navigation, relationship paths

---

## Quick Reference: Clone Commands

```powershell
# HIGH PRIORITY
git clone https://github.com/getzep/graphiti.git _discovery/_repo/real-time-kg/graphiti/repo
git clone https://github.com/microsoft/graphrag.git _discovery/_repo/llm-extraction/graphrag/repo

# MEDIUM PRIORITY
git clone https://github.com/WSE-research/KinGVisher-Knowledge-Graph-Visualizer.git _discovery/_repo/visualization/kingvisher/repo
git clone https://github.com/opensemanticsearch/open-semantic-visual-graph-explorer.git _discovery/_repo/visualization/open-semantic-graph-explorer/repo

# LOW PRIORITY (optional)
git clone https://github.com/wisecubeai/graphster.git _discovery/_repo/llm-extraction/graphster/repo
git clone https://github.com/Sujit-O/pykg2vec.git _discovery/_repo/embeddings/pykg2vec/repo
```

---

## Relevance Summary by plasticFlower Component

### STT Layer
- No direct references (Web Speech API is browser-native; Deepgram has own SDK)

### Builder Agent
| Repo | Relevant Component | What to Extract |
|------|-------------------|-----------------|
| Graphiti | `llm/extraction.py` | Entity extraction prompts |
| GraphRAG | `prompt_tune/` | Relationship extraction prompts |

### Gardener Agent
| Repo | Relevant Component | What to Extract |
|------|-------------------|-----------------|
| GraphRAG | `index/community/` | Clustering concepts |
| Graphiti | `core/graph_ops.py` | Merge/dedup patterns |

### Graph Store (Neo4j)
| Repo | Relevant Component | What to Extract |
|------|-------------------|-----------------|
| Graphiti | `core/` | Schema design, Cypher patterns |

### Frontend (Cytoscape.js)
| Repo | Relevant Component | What to Extract |
|------|-------------------|-----------------|
| KinGVisher | UI components | Interaction patterns |
| Open Semantic | Navigation | Entity-centric UX |

---

## Not Included (Evaluated but Rejected)

| Project | Reason for Exclusion |
|---------|---------------------|
| Gephi | Desktop app, not web-based |
| Graphia | Desktop app, static analysis focus |
| ViziQuer | SPARQL/RDF focus, not property graphs |
| NeuralKG | Too academic, training overhead |
| Leonata | Offline document processing, not streaming |



# Graphiti - Relevance Analysis for plasticFlower

> **Repository:** https://github.com/getzep/graphiti
> **Tag:** real-time-kg
> **Priority:** HIGH

---

## 1. Relevance to plasticFlower Development

Graphiti is the **most directly relevant** project identified. It builds real-time knowledge graphs specifically designed for AI agent memory and context management.

### Key Alignments

| Graphiti Feature | plasticFlower Requirement | Alignment |
|------------------|---------------------------|-----------|
| Real-time graph updates | Live transcription → graph | ✓ Direct |
| Temporal knowledge tracking | Timestamp-linked nodes | ✓ Direct |
| Entity extraction from text | Builder Agent function | ✓ Direct |
| Relationship inference | Gardener Agent function | ✓ Direct |
| Neo4j integration | Proposed graph store | ✓ Direct |
| LLM-powered extraction | Gemini 3 Pro integration | ✓ Direct |

### Why Include

Graphiti solves the exact problem of incrementally building a knowledge graph from streaming text input. Its architecture (episodic memory → entity extraction → graph update) mirrors plasticFlower's Builder Agent pattern.

---

## 2. Comparative Analysis

| Aspect | Graphiti | plasticFlower |
|--------|----------|---------------|
| **Input Source** | AI agent conversations | Live speech transcription |
| **Update Trigger** | Per message/episode | Per transcript chunk |
| **Graph Structure** | Flat entities + relationships | Hierarchical Flowers (clusters) |
| **Review Mechanism** | Continuous refinement | Periodic Gardener (90s) |
| **Visualisation** | None (API only) | Cytoscape.js with FCose |
| **Schema** | Semi-structured | Fully emergent (LLM-determined) |

### Key Differences

1. **No visual layer** — Graphiti is backend-only; plasticFlower needs live visualisation
2. **No clustering** — Graphiti stores flat graphs; plasticFlower needs Flower formation
3. **Different input cadence** — Graphiti handles chat turns; plasticFlower handles continuous speech chunks

---

## 3. What to Leverage

### Recommended for Adoption

| Component | What It Does | How to Use in plasticFlower |
|-----------|--------------|------------------------------|
| **Entity extraction pipeline** | Extracts entities from text using LLM | Adapt for Builder Agent |
| **Temporal edge handling** | Tracks when relationships were established | Use for timestamp arrays on nodes |
| **Neo4j schema patterns** | Efficient graph storage structure | Reference for our schema design |
| **Deduplication logic** | Prevents duplicate entities | Pre-Builder similarity check |

### Code to Study

```
graphiti/
├── core/
│   ├── entities.py      # Entity extraction patterns
│   ├── edges.py         # Relationship handling
│   └── graph_ops.py     # Neo4j operations
├── llm/
│   └── extraction.py    # LLM prompt patterns for extraction
```

### Not Recommended

- **Episode-based architecture** — Too chat-focused; we need chunk-based
- **Memory retrieval patterns** — Designed for agent recall, not human visualisation

---

## 4. Integration Approach

**Don't fork/import directly.** Instead:

1. Study the entity extraction prompts and adapt for domain-agnostic use
2. Reference the Neo4j schema for our node/relationship structure
3. Adapt the deduplication approach for our pre-Builder similarity check
4. Ignore the retrieval/memory aspects (not relevant to our use case)

---

## 5. Clone Command

```powershell
git clone https://github.com/getzep/graphiti.git
```



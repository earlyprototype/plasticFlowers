# Microsoft GraphRAG - Relevance Analysis for plasticFlower

> **Repository:** https://github.com/microsoft/graphrag
> **Tag:** llm-extraction
> **Priority:** HIGH

---

## 1. Relevance to plasticFlower Development

GraphRAG is Microsoft's approach to combining LLMs with knowledge graphs for retrieval-augmented generation. It demonstrates proven patterns for LLM-based entity and relationship extraction at scale.

### Key Alignments

| GraphRAG Feature | plasticFlower Requirement | Alignment |
|------------------|---------------------------|-----------|
| LLM entity extraction | Builder Agent extraction | ✓ Direct |
| Community detection | Flower clustering | ✓ Direct |
| Hierarchical summarisation | Meta-Flower abstraction | ✓ Relevant |
| Graph-based retrieval | Session review/export | ○ Partial |

### Why Include

GraphRAG's **community detection and hierarchical clustering** is directly relevant to plasticFlower's Flower formation. Their approach to creating "communities" of related entities and generating summaries at each level maps to our Flower/Meta-Flower concept.

---

## 2. Comparative Analysis

| Aspect | GraphRAG | plasticFlower |
|--------|----------|---------------|
| **Processing Mode** | Batch (document corpus) | Streaming (live audio) |
| **Input Type** | Static documents | Real-time transcript chunks |
| **Graph Purpose** | Improve RAG retrieval | Live knowledge visualisation |
| **Update Frequency** | One-time build | Continuous updates |
| **Clustering** | Leiden algorithm | LLM-determined Flowers |
| **Output** | Enhanced Q&A | Visual knowledge map |

### Key Differences

1. **Batch vs streaming** — GraphRAG processes entire corpora; plasticFlower needs incremental updates
2. **Retrieval focus** — GraphRAG optimises for Q&A; plasticFlower optimises for visual understanding
3. **Algorithmic clustering** — GraphRAG uses Leiden; plasticFlower uses LLM-based semantic clustering

---

## 3. What to Leverage

### Recommended for Adoption

| Component | What It Does | How to Use in plasticFlower |
|-----------|--------------|------------------------------|
| **Entity extraction prompts** | Structured prompts for NER | Adapt for Builder Agent |
| **Relationship extraction prompts** | Prompts for edge detection | Adapt for Builder Agent |
| **Community detection concept** | Groups related entities | Inform Flower formation logic |
| **Hierarchical summarisation** | Creates summaries at cluster levels | Potential Historian Agent feature |

### Prompt Patterns to Study

GraphRAG's prompts are well-engineered for:
- Extracting entities without predefined schema
- Inferring relationship types from context
- Generating community summaries

### Code to Study

```
graphrag/
├── index/
│   ├── graph/
│   │   └── extractors/     # Entity/relationship extraction
│   └── community/          # Clustering logic
├── prompt_tune/            # Prompt templates
```

### Not Recommended

- **Indexing pipeline** — Too batch-oriented for streaming use
- **Vector store integration** — We use Neo4j's native vectors instead
- **Query engine** — Not relevant to live visualisation

---

## 4. Integration Approach

**Extract prompt patterns only.** The architecture is fundamentally batch-oriented.

1. Study `prompt_tune/` for entity extraction prompt engineering
2. Reference community detection for Gardener's clustering logic
3. Adapt hierarchical summarisation concept for potential Historian Agent
4. Ignore the indexing/query pipeline (wrong paradigm)

---

## 5. Clone Command

```powershell
git clone https://github.com/microsoft/graphrag.git
```



# plasticFlower — What to Leverage from Reference Projects

> **Purpose:** Specific, actionable guidance on what to extract from each repository
> **Confidence Scale:** 1-10 (10 = highly trustworthy/proven, 1 = experimental/risky)

---

## HIGH Priority

### 1. GraphRAG (Microsoft)

| | |
|---|---|
| **Confidence** | **10/10** — Microsoft Research, production-tested, well-documented |
| **Repository** | https://github.com/microsoft/graphrag |

#### What to Leverage

| Component | Location | Use in plasticFlower | Confidence |
|-----------|----------|---------------------|------------|
| **Entity extraction prompt** | `graphrag/index/graph/extractors/graph_extractor.py` | Adapt for Builder Agent | 10 |
| **Relationship extraction prompt** | Same file | Adapt for Builder Agent | 10 |
| **Community detection concept** | `graphrag/index/operations/cluster_graph.py` | Inform Flower formation logic | 9 |
| **Hierarchical summarisation** | `graphrag/index/operations/summarize_descriptions.py` | Potential Historian Agent | 8 |

#### Specific Prompts to Study

```
# Their entity extraction approach:
- Uses structured output format
- Asks for entity TYPE (we want LLM to infer this)
- Asks for entity DESCRIPTION (we want this)
- Asks for RELATIONSHIPS with evidence (we want this)
```

#### What NOT to Use

| Component | Reason |
|-----------|--------|
| Indexing pipeline | Batch-oriented, not streaming |
| Vector store integration | We use Neo4j native |
| Query engine | Wrong paradigm (retrieval vs construction) |
| Leiden clustering algorithm | We want LLM-based semantic clustering |

---

### 2. Graphiti (Zep)

| | |
|---|---|
| **Confidence** | **8/10** — Production use in Zep, real-time focused, active development |
| **Repository** | https://github.com/getzep/graphiti |

#### What to Leverage

| Component | Location | Use in plasticFlower | Confidence |
|-----------|----------|---------------------|------------|
| **Streaming entity extraction** | `graphiti/llm/` | Builder Agent pattern | 9 |
| **Neo4j schema design** | `graphiti/core/nodes.py`, `edges.py` | Reference for our schema | 8 |
| **Deduplication logic** | `graphiti/core/search.py` | Pre-Builder similarity check | 8 |
| **Temporal tracking** | `graphiti/core/edges.py` | Timestamp array handling | 7 |

#### Specific Patterns to Study

```python
# Their approach to incremental updates:
- Episode-based processing (adapt to chunk-based)
- Entity resolution before creation
- Edge weight accumulation over time
```

#### What NOT to Use

| Component | Reason |
|-----------|--------|
| Episode/memory architecture | Too chat-agent focused |
| Retrieval patterns | Designed for agent recall, not human visualisation |
| Fact extraction | More rigid than our emergent approach |

---

## MEDIUM Priority

### 3. knowledge-graph-kit (Internal)

| | |
|---|---|
| **Confidence** | **7/10** — Your own code, proven for batch use, familiar patterns |
| **Location** | `_discovery/knowledge-graph-kit/` |

#### What to Leverage

| Component | Location | Use in plasticFlower | Confidence |
|-----------|----------|---------------------|------------|
| **Merge logic** | `core/graph_manager.py:148-204` | Gardener node consolidation | 8 |
| **Validation logic** | `core/graph_manager.py:218-235` | Graph integrity checking | 8 |
| **YAML config pattern** | `core/config_loader.py` | Configuration approach | 7 |

#### Specific Code to Port

```python
# _merge_entity pattern - directly useful:
def _merge_entity(self, existing: Dict, new: Dict):
    for field in provenance_fields:
        if field in new:
            for item in new[field]:
                if item not in existing[field]:
                    existing[field].append(item)
```

#### What NOT to Use

| Component | Reason |
|-----------|--------|
| JSON file storage | Need Neo4j |
| Entity type system | Predefined vs emergent |
| vis-network viewer | Using Cytoscape.js |
| Batch build scripts | Need streaming |

---

### 4. KinGVisher

| | |
|---|---|
| **Confidence** | **6/10** — Academic project, good UX patterns, limited scope |
| **Repository** | https://github.com/WSE-research/KinGVisher-Knowledge-Graph-Visualizer |

#### What to Leverage

| Component | Use in plasticFlower | Confidence |
|-----------|---------------------|------------|
| **Details panel layout** | Reference for our node details | 7 |
| **Search/filter UI pattern** | Adapt for our filtering | 6 |
| **Node selection highlighting** | Interaction pattern | 6 |

#### What NOT to Use

| Component | Reason |
|-----------|--------|
| SPARQL/RDF integration | We use Neo4j property graph |
| vis.js library | We use Cytoscape.js |
| Static data model | We need streaming |

---

### 5. Open Semantic Visual Graph Explorer

| | |
|---|---|
| **Confidence** | **6/10** — Open source, good entity navigation, different tech stack |
| **Repository** | https://github.com/opensemanticsearch/open-semantic-visual-graph-explorer |

#### What to Leverage

| Component | Use in plasticFlower | Confidence |
|-----------|---------------------|------------|
| **Entity-centric navigation** | "Follow the thread" interaction | 7 |
| **Expand/collapse pattern** | Dense graph handling | 6 |
| **Relationship path display** | "How does X relate to Y?" | 6 |

#### What NOT to Use

| Component | Reason |
|-----------|--------|
| Solr/Elasticsearch backend | We use Neo4j |
| Document-centric model | We're transcript-centric |

---

## LOW Priority

### 6. Graphster

| | |
|---|---|
| **Confidence** | **5/10** — Spark-based, enterprise scale, paradigm mismatch |
| **Repository** | https://github.com/wisecubeai/graphster |

#### Limited Value

| Component | Consideration |
|-----------|---------------|
| Schema patterns | Reference only if needed |

**Recommendation:** Skip unless specific schema questions arise.

---

### 7. Pykg2vec

| | |
|---|---|
| **Confidence** | **5/10** — Academic, training overhead, post-MVP only |
| **Repository** | https://github.com/Sujit-O/pykg2vec |

#### Post-MVP Only

| Component | When to Consider |
|-----------|------------------|
| KG embedding algorithms | If Neo4j vectors prove insufficient |
| Link prediction | "Suggested connections" feature |

**Recommendation:** Defer. Neo4j native vectors sufficient for MVP.

---

## Summary: What to Extract

### For Builder Agent

| Source | Component | Priority |
|--------|-----------|----------|
| GraphRAG | Entity extraction prompt | **Extract** |
| GraphRAG | Relationship extraction prompt | **Extract** |
| Graphiti | Streaming extraction pattern | **Study** |
| Graphiti | Entity resolution approach | **Adapt** |

### For Gardener Agent

| Source | Component | Priority |
|--------|-----------|----------|
| GraphRAG | Community detection concept | **Study** |
| GraphRAG | Hierarchical summarisation | **Study** |
| knowledge-graph-kit | Merge logic | **Port** |
| knowledge-graph-kit | Validation logic | **Port** |

### For Visualisation

| Source | Component | Priority |
|--------|-----------|----------|
| KinGVisher | Details panel UX | **Reference** |
| KinGVisher | Search/filter pattern | **Reference** |
| Open Semantic | Entity navigation | **Reference** |

### For Graph Store

| Source | Component | Priority |
|--------|-----------|----------|
| Graphiti | Neo4j schema patterns | **Reference** |
| Graphiti | Deduplication queries | **Adapt** |

---

## Confidence Summary

| Repository | Overall Confidence | Primary Value |
|------------|-------------------|---------------|
| **GraphRAG** | 10/10 | Prompt engineering, community concept |
| **Graphiti** | 8/10 | Real-time patterns, Neo4j integration |
| **knowledge-graph-kit** | 7/10 | Merge/validation logic |
| **KinGVisher** | 6/10 | UX patterns |
| **Open Semantic** | 6/10 | Navigation patterns |
| **Graphster** | 5/10 | Reference only |
| **Pykg2vec** | 5/10 | Post-MVP |



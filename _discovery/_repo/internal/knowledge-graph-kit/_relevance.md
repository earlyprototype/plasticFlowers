# knowledge-graph-kit - Relevance Analysis for plasticFlower

> **Repository:** `_discovery/knowledge-graph-kit/` (local)
> **Tag:** internal
> **Priority:** MEDIUM
> **Familiarity Bonus:** Author is familiar with codebase (tiebreaker only)

---

## 1. Relevance to plasticFlower Development

knowledge-graph-kit is a configurable knowledge graph toolkit with web visualisation, YAML-driven configuration, and optional Gemini chat integration.

### Key Alignments

| Feature | plasticFlower Requirement | Alignment |
|---------|---------------------------|-----------|
| YAML-driven configuration | Domain-agnostic config | ✓ Direct |
| Merge/deduplication logic | Gardener Agent merges | ✓ Direct |
| Provenance tracking | Timestamp/mention arrays | ✓ Direct |
| GraphManager CRUD | Builder Agent writes | ○ Partial (needs streaming adaptation) |
| vis-network visualisation | Cytoscape.js frontend | ✗ Different library |
| Gemini chat integration | LLM agent integration | ○ Partial (chat vs agent paradigm) |
| Predefined entity types | Emergent node types | ✗ Architectural mismatch |
| JSON file storage | Neo4j graph database | ✗ Architectural mismatch |

### Why Include

Provides **proven merge/validation patterns** and demonstrates YAML-driven graph configuration. The merge logic for handling duplicate entities with provenance tracking is directly applicable to Gardener operations.

---

## 2. Comparative Analysis

| Aspect | knowledge-graph-kit | plasticFlower |
|--------|---------------------|---------------|
| **Processing Mode** | Batch (build scripts) | Streaming (live audio) |
| **Input Type** | Documents/manual entry | Real-time transcript chunks |
| **Schema Approach** | Predefined in YAML | Emergent (LLM-determined) |
| **Storage** | JSON files | Neo4j + vector index |
| **Update Frequency** | Manual rebuild | Continuous real-time |
| **Visualisation** | vis-network (static) | Cytoscape.js + FCose (live) |
| **AI Role** | Post-hoc chat assistant | Active Builder/Gardener agents |
| **Clustering** | None | Flower formation |

### Key Differences

1. **Batch vs streaming** — Fundamentally different data flow paradigm
2. **Schema-first vs schema-emergent** — knowledge-graph-kit requires predefined types; plasticFlower discovers them
3. **File vs database** — JSON files don't support vector similarity or real-time queries
4. **Passive vs active AI** — Chat assistant vs constructive agents

---

## 3. What to Leverage

### Recommended for Adoption

| Component | Location | How to Use |
|-----------|----------|------------|
| **Merge logic** | `core/graph_manager.py:148-204` | Adapt `_merge_entity()` for Gardener node consolidation |
| **Validation** | `core/graph_manager.py:218-235` | Port `validate()` for graph integrity checks |
| **Config loader pattern** | `core/config_loader.py` | Reference for YAML configuration approach |

### Code Worth Studying

```
knowledge-graph-kit/
├── core/
│   ├── graph_manager.py    # Merge, validate, stats
│   └── config_loader.py    # YAML config pattern
```

### Not Recommended

| Component | Reason |
|-----------|--------|
| **JSON storage layer** | Need Neo4j for vectors and real-time |
| **Entity type system** | Predefined types conflict with emergent schema |
| **Relationship enumeration** | plasticFlower uses natural language relationships |
| **vis-network viewer** | Different library (Cytoscape.js) |
| **Gemini chat architecture** | Chat paradigm differs from agent paradigm |
| **Build script patterns** | Batch model doesn't fit streaming use case |

---

## 4. Integration Approach

**Extract specific utilities only.** The overall architecture is not aligned with plasticFlower's streaming/emergent paradigm.

1. Port the merge logic algorithm (not the surrounding code)
2. Reference the validation approach for integrity checking
3. Consider the YAML config pattern (but with different schema)
4. Do not attempt to adapt the overall architecture

---

## 5. Objective Assessment

### Strengths
- Clean merge/deduplication implementation
- Well-structured configuration system
- Proven provenance tracking pattern

### Weaknesses
- Batch-oriented architecture (fundamental mismatch)
- Schema-first approach (opposite to plasticFlower)
- File-based storage (insufficient for real-time + vectors)
- No streaming support
- No clustering/community detection

### Comparison to Peer Projects

| vs Graphiti | knowledge-graph-kit lacks real-time updates and streaming architecture |
| vs GraphRAG | knowledge-graph-kit lacks community detection and LLM extraction prompts |
| vs KinGVisher | Similar web visualisation quality; knowledge-graph-kit uses vis-network vs RDF |

---

## 6. Priority Justification

**MEDIUM** priority because:
- ✓ Merge logic is directly useful
- ✓ Validation patterns are portable
- ✗ Architecture doesn't align with streaming model
- ✗ No community detection or clustering
- ✗ No real-time capabilities

Lower than Graphiti (which has real-time) and GraphRAG (which has clustering).
Comparable to visualisation references (KinGVisher, Open Semantic Explorer).

**Tiebreaker consideration:** Author familiarity means faster comprehension and adaptation of the merge/validation patterns.

---

## 7. Summary

| Aspect | Value to plasticFlower |
|--------|------------------------|
| **Overall architecture** | Low |
| **Merge/validation utilities** | High |
| **Config system** | Medium |
| **Visualisation patterns** | Low |
| **Streaming capabilities** | None |
| **Clustering/Flowers** | None |


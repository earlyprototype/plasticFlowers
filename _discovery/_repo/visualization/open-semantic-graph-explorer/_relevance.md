# Open Semantic Visual Graph Explorer - Relevance Analysis for plasticFlower

> **Repository:** https://github.com/opensemanticsearch/open-semantic-visual-graph-explorer
> **Tag:** visualization
> **Priority:** MEDIUM

---

## 1. Relevance to plasticFlower Development

Open Semantic Visual Graph Explorer provides entity-centric graph exploration with focus on discovering relationships between people, organisations, and locations. Its entity relationship visualisation is relevant to plasticFlower's knowledge mapping.

### Key Alignments

| Feature | plasticFlower Requirement | Alignment |
|---------|---------------------------|-----------|
| Entity relationship mapping | Concept → Concept connections | ✓ Direct |
| Web-based exploration | Browser interface | ✓ Direct |
| Faceted filtering | Filter by entity type | ✓ Direct |
| Path discovery | Show how concepts connect | ○ Partial |

### Why Include

This project demonstrates **entity-centric navigation** — starting from one concept and exploring its connections. This "follow the thread" interaction model is valuable for plasticFlower's exploratory use case.

---

## 2. Comparative Analysis

| Aspect | Open Semantic Explorer | plasticFlower |
|--------|------------------------|---------------|
| **Entity Types** | Predefined (Person, Org, Location) | Emergent (LLM-determined) |
| **Data Source** | Solr/Elasticsearch | Neo4j |
| **Focus** | Document entity extraction | Live speech extraction |
| **Graph Purpose** | Investigation/research | Meeting comprehension |

### Key Differences

1. **Predefined vs emergent schema** — They have fixed entity types; we let LLM decide
2. **Post-hoc vs real-time** — They analyse existing documents; we process live speech
3. **Investigation focus** — Designed for research/journalism; we focus on knowledge capture

---

## 3. What to Leverage

### Recommended for Adoption

| Component | What It Does | How to Use in plasticFlower |
|-----------|--------------|------------------------------|
| **Entity-centric navigation** | Click entity → see all connections | Core interaction pattern |
| **Faceted filters** | Filter by type, date, etc. | Adapt for Flower/node type filtering |
| **Relationship path display** | Shows how entities connect | "How does X relate to Y?" feature |

### UX Patterns to Study

- Entity cards with key properties
- Relationship strength indicators
- Expand/collapse for dense graphs
- Breadcrumb navigation through exploration

### Not Recommended

- **Solr/Elasticsearch backend** — We use Neo4j
- **Document-centric data model** — We're transcript-centric
- **Fixed entity schema** — We need emergent types

---

## 4. Integration Approach

**Extract interaction patterns only.**

1. Study the entity card design
2. Reference the "expand connections" interaction
3. Consider the relationship path visualisation for post-MVP
4. Ignore the search/indexing backend

---

## 5. Clone Command

```powershell
git clone https://github.com/opensemanticsearch/open-semantic-visual-graph-explorer.git
```



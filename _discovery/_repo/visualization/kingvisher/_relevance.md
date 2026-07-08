# KinGVisher - Relevance Analysis for plasticFlower

> **Repository:** https://github.com/WSE-research/KinGVisher-Knowledge-Graph-Visualizer
> **Tag:** visualization
> **Priority:** MEDIUM

---

## 1. Relevance to plasticFlower Development

KinGVisher is a web-based knowledge graph visualiser that provides interactive exploration of RDF-based graphs. Its frontend patterns are relevant to plasticFlower's visualisation layer.

### Key Alignments

| KinGVisher Feature | plasticFlower Requirement | Alignment |
|--------------------|---------------------------|-----------|
| Web-based graph rendering | Browser-based UI | ✓ Direct |
| Interactive node exploration | Click-to-explore Flowers | ✓ Direct |
| Filter/search capabilities | Node filtering | ✓ Direct |
| Details panel on selection | Node context display | ✓ Direct |

### Why Include

KinGVisher demonstrates **production-quality UX patterns** for knowledge graph exploration in a web browser. Its interaction model (click node → show details → explore connections) aligns with plasticFlower's needs.

---

## 2. Comparative Analysis

| Aspect | KinGVisher | plasticFlower |
|--------|------------|---------------|
| **Data Source** | RDF triplestore (SPARQL) | Neo4j + SSE stream |
| **Update Mode** | Static (query-refresh) | Real-time (live updates) |
| **Graph Library** | vis.js | Cytoscape.js + FCose |
| **Node Types** | RDF classes | Emergent (LLM-determined) |
| **Clustering** | None | Flower formation |

### Key Differences

1. **Static vs live** — KinGVisher queries existing data; plasticFlower receives streaming updates
2. **RDF vs property graph** — Different data models (we use Neo4j property graphs)
3. **No clustering** — KinGVisher shows flat graphs; we need hierarchical Flowers

---

## 3. What to Leverage

### Recommended for Adoption

| Component | What It Does | How to Use in plasticFlower |
|-----------|--------------|------------------------------|
| **Details panel UX** | Shows node properties on click | Reference for our details panel |
| **Search/filter UI** | Text search across nodes | Adapt for our search feature |
| **Loading states** | Handles async data loading | Reference for streaming UX |
| **Responsive layout** | Graph + panel side-by-side | Inform our layout design |

### UI Patterns to Study

- Node selection highlighting
- Edge label rendering
- Zoom/pan controls
- Filter dropdown design

### Not Recommended

- **SPARQL integration** — We use Neo4j, not RDF
- **vis.js library** — We're using Cytoscape.js
- **Static data model** — We need streaming support

---

## 4. Integration Approach

**Reference for UX only.** The tech stack differs significantly.

1. Study the interaction patterns (click, hover, select)
2. Reference the details panel layout
3. Adapt the search/filter UI concepts
4. Ignore the backend (SPARQL/RDF)

---

## 5. Clone Command

```powershell
git clone https://github.com/WSE-research/KinGVisher-Knowledge-Graph-Visualizer.git
```



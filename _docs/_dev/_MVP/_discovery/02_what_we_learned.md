# plasticFlower — Discovery: Key Learnings

---

## From GraphRAG (Microsoft)

**What it is:** Batch pipeline extracting entities from documents, grouping into communities.

**Learned:**
- Well-engineered prompts for entity/relationship extraction
- Community detection groups related entities
- Hierarchical summaries at cluster levels

**Using:** Prompt patterns for Builder Agent

**Not using:** Batch pipeline, Leiden algorithm (we use LLM-based semantic clustering)

---

## From Graphiti (Zep)

**What it is:** Real-time knowledge graph for AI agent memory.

**Learned:**
- Streaming architecture processes input as it arrives
- Entity resolution checks existence before creating
- Neo4j patterns for temporal data

**Using:** Streaming pattern, pre-creation similarity check, Neo4j schema reference

**Not using:** Episode/memory architecture (too chat-focused)

---

## From knowledge-graph-kit (Internal)

**What it is:** Configurable batch toolkit for knowledge graphs.

**Learned:**
- Clean merge logic for duplicate entities
- Validation for graph integrity
- YAML-driven configuration

**Using:** Merge logic, validation pattern

**Not using:** JSON storage, predefined types, vis-network, batch model

---

## Algorithmic vs LLM Clustering

**Discussion outcome:**

Both dimensions matter:
- **Structural density** (algorithmic) — how interconnected nodes are
- **Semantic coherence** (LLM) — how conceptually related nodes are

For MVP:
- LLM handles theme identification
- Simple edge count as density proxy
- Full density metrics post-MVP



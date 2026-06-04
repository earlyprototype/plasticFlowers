# Gate 3 — Graph Persistence Operational

> **Objective:** Neo4j CRUD works; vector index exists; similarity queries return stable results
> **Entry:** Gate 2 passed (contracts locked)
> **Exit:** Create/read/update/delete nodes and relationships against Neo4j; similarity check functional; Google embedding model integrated with caching

---

## Serial Dependencies (must complete in order)

1. **Neo4j driver + config** — `backend/app/config.py` (or equivalent) configures driver + pooling; smoke query proves connectivity
2. **Schema constraints** — Idempotent unique constraints on Node.id, Relationship.id, Flower.id, Session.id
3. **Core CRUD** — Transactional create/read/update/delete for nodes and relationships in `graph_db.py`
4. **Vector index** — Idempotent index creation on `Node.embedding`
5. **Similarity query** — Query path for pre-Builder duplicate check (>= 0.85 threshold) including mentions/timestamp update

---

## Parallel Lanes (can run simultaneously)

| Lane | Work | Owner | Notes |
|------|------|-------|-------|
| A | Serial lane tasks above | Backend dev | Must complete steps 1–5 in order |
| B | Embedding generation utility + unit tests | Backend dev | Uses Google embedding model with caching to avoid duplicate calls |

**Sync point:** Lane B can begin once the driver is operational; similarity pipeline requires both lanes.

---

## Deliverables

| Deliverable | Acceptance Criteria |
|-------------|---------------------|
| `backend/app/config.py` (or equivalent settings) | Connection string, pooling, and smoke test documented |
| `backend/app/services/graph_db.py` | Transactional CRUD operations implementing Cypher patterns below |
| `backend/app/services/embeddings.py` | Google embedding model integration + memoised caching |
| Neo4j constraints | `SHOW CONSTRAINTS` output includes unique constraints for Node/Relationship/Flower/Session ids |
| Neo4j vector index | `SHOW INDEXES` lists vector index on `Node.embedding` |
| Tests | `tests/test_graph_db.py` + `tests/test_similarity.py` pass in CI |

---

## Key Operations (must work)

| Operation | Cypher Pattern |
|-----------|----------------|
| Create node | `CREATE (n:Node {id: $id, label: $label, ...})` |
| Read node | `MATCH (n:Node {id: $id}) RETURN n` |
| Update node | `MATCH (n:Node {id: $id}) SET n += $props` |
| Delete node | `MATCH (n:Node {id: $id}) DETACH DELETE n` |
| Create relationship | `MATCH (a:Node {id: $src}), (b:Node {id: $tgt}) CREATE (a)-[r:REL {id: $id, ...}]->(b)` |
| Similarity search | `CALL db.index.vector.queryNodes(...)` |

---

## Pre-Builder Similarity Check Rule

Per `_PRE_IMPLEMENTATION_REPORT.md`:

1. Compute embedding for proposed node label
2. Query vector index for nearest neighbours (session-scoped)
3. If top match similarity >= 0.85:
   1. Do NOT create new node
   2. Increment `mentions`, append timestamp
   3. Use matched node id for relationships
4. Else: create new ghost node

---

## Verification Checklist

- [ ] Neo4j connection works (driver test)
- [ ] Unique constraints exist on all id fields
- [ ] Vector index exists on Node.embedding
- [ ] CRUD operations work (`tests/test_graph_db.py`)
- [ ] Similarity query returns results with scores (`tests/test_similarity.py`)
- [ ] Similarity threshold (0.85) is configurable
- [ ] Embedding service uses Google embedding model and caches repeated labels

---

## Handover to Gate 4

**Pass when:**
1. All verification items checked (including embedding service requirements)
2. Unit tests for CRUD and similarity pass
3. Similarity query tested with sample embeddings + threshold enforcement

**Handover artefact:** Operational graph persistence layer; ready for Builder integration

---

## Tools to Leverage (Mandatory)

Gate 3 involves Neo4j and embeddings — use available tools to get current syntax.

### Before Implementation

| Task | Tool | Query |
|------|------|-------|
| Neo4j Python driver | `get-library-docs` | "Neo4j Python async driver" |
| Vector index creation | `web_search` | "Neo4j 5 CREATE VECTOR INDEX syntax" |
| Vector similarity query | `web_search` | "Neo4j db.index.vector.queryNodes" |
| Google embeddings API | `web_search` | "Google text-embedding-004 API Python" |

### During Implementation

| Situation | Tool | Action |
|-----------|------|--------|
| Driver connection errors | `web_search` | Search error message |
| Vector index not working | `web_search` | "Neo4j vector index troubleshooting" |
| Embedding API errors | `web_search` | "Google AI embeddings rate limit" |
| Cypher syntax issues | `get-library-docs` | Query Neo4j docs |

### Reference Patterns

| Pattern | Source |
|---------|--------|
| Similarity threshold | `_docs/_dev/_MVP/_PRE_IMPLEMENTATION_REPORT.md` (>= 0.85) |
| Node schema | `_docs/_dev/_MVP/_schema/01_data_model.md` |
| Embedding dimension | Google docs (768 for text-embedding-004) |

---

## Reference

- [Data Model](../../_docs/_dev/_MVP/_schema/01_data_model.md)
- [Agent Architecture](../../_docs/_dev/_MVP/_architecture/02_agents.md) (similarity check)
- [Pre-Implementation Report](../../_docs/_dev/_MVP/_PRE_IMPLEMENTATION_REPORT.md)
- [High-Level Plan](../overview/highplan.md)
- [Proposal Response](PROPOSAL_RESPONSE_001.md) — approved scope & decisions


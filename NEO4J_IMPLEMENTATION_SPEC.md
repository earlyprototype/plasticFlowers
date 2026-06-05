# plasticFlower — Neo4j Implementation Spec Sheet

**Subject:** The graph-persistence + vector-similarity layer of the `plasticFlower` backend.
**Purpose:** A code-grounded specification and technical breakdown, written to assess **transferability to a similar project** and to benchmark the implementation against standard Neo4j / GraphRAG practice.
**Basis:** Read directly from source (`backend/app/...`), cross-checked against the project's design docs/ADRs. Every claim is cited `file:line`.

> Scope note: this documents the **persistence/graph layer**, not the LLM agents themselves except where they drive graph behaviour.

---

## 1. At a glance

| Dimension | Implementation | Reference |
|---|---|---|
| Database | Neo4j 5.x (single instance, Docker) | `docker/docker-compose.yml`, `.venv/.../neo4j-5.23.1` |
| Driver | Official `neo4j` Python driver **5.23.1**, **async-only** (`AsyncGraphDatabase`) | `services/neo4j.py:10,23` |
| Connection mgmt | Lazy global singleton `AsyncDriver`; pool size 10; conn lifetime 3600s | `services/neo4j.py:14-29`, `config.py:30-37` |
| Schema mgmt | Idempotent `IF NOT EXISTS` constraints + vector index, applied on every startup | `services/graph_schema.py`, `main.py:54` |
| Transactions | **Managed transactions only** (`session.execute_read/execute_write`) → automatic retry | throughout `graph_db.py` |
| Query safety | Fully **parameterized** Cypher (no value interpolation) | throughout |
| Vector search | Native `db.index.vector.queryNodes` over a **single global index**, **post-filtered by `session_id`** | `services/similarity.py:71-78` |
| Embeddings | Google `text-embedding-004`, **768-dim**, **cosine** | `config.py:91-109` |
| Multi-tenancy | **Property-based**: every node/edge carries a `session_id`; no DB- or label-level isolation | `graph_db.py` (`SESSION_KEY`, l.27) |
| Data mapping | Hand-rolled Pydantic ⇄ Neo4j property hydration helpers | `graph_db.py:496-544` |
| Runtime | Python **3.11+** (uses `asyncio.timeout`), FastAPI, async lifespan | `main.py`, `builder_service.py:98` |

**One-line characterization:** a *real-time, incremental knowledge-graph builder* that resolves entities at write-time via vector similarity, partitions tenants by property, and deliberately favors small per-session graphs (LLM clustering + full-context Q&A) over classic large-corpus GraphRAG.

---

## 2. Where Neo4j sits (layering)

```
FastAPI (main.py, lifespan) ── async driver init → ensure_graph_schema → healthcheck
        │
   api/ routers (sessions, chunks, graph, stream, export)
        │
   services/
     builder_service.py   ← orchestration: LLM extract → dedup → persist → SSE/Redis
     similarity.py        ← embed → vector ANN → threshold decision (the dedup brain)
     chunk_store.py       ← thin class wrapper over graph_db chunk funcs
     graph_db.py          ← THE persistence layer: ~40 async CRUD functions (1417 LOC)
     graph_schema.py      ← constraints + vector index
     neo4j.py             ← driver lifecycle (get/close/healthcheck)
        │
   Neo4j (bolt 127.0.0.1:7687)
```

The graph layer is **functional, not object-oriented**: `graph_db.py` exposes free `async def` functions keyed by `session_id` rather than a repository class. The only class wrapper is `ChunkStore` (`chunk_store.py:14`), and it is thin/partial (its `delete` is a documented no-op, `chunk_store.py:23-26`).

---

## 3. Connection & driver lifecycle

- **Single lazily-created global driver** (`services/neo4j.py:14-29`): `_driver` module global, created on first `get_driver()`, configured with `max_connection_pool_size` and `max_connection_lifetime` from settings.
- **Graceful shutdown** `close_driver()` (`neo4j.py:32-38`) nulls the global; wired into FastAPI `lifespan` teardown (`main.py:75`).
- **Healthcheck** `run_healthcheck()` runs `RETURN 1` via a managed read tx (`neo4j.py:41-54`); exposed at `/health` (`main.py:89-94`) and run at startup (`main.py:55`).
- **Windows-specific hardening:** `main.py` monkeypatches `socket.getaddrinfo` to force IPv4 (avoids ~21s IPv6 fallback, `main.py:3-8`) and sets `WindowsSelectorEventLoopPolicy` (`main.py:13-14`); the Neo4j URI is pinned to `127.0.0.1` for the same reason (`config.py:23`). *Pragmatic, but platform-coupled — see §11.*
- **Secrets:** credentials via `pydantic.SecretStr`, exposed as a tuple for the driver (`config.py:26-29,186-189`). The default password is hardcoded (`"plasticflower"`) as a dev fallback.

**Verdict:** textbook driver lifecycle. Single-instance assumption only (no clustering/routing config beyond URI scheme).

---

## 4. Schema: labels, relationships, constraints, indexes

### Node labels (9 observed)
| Label | Role | Created in |
|---|---|---|
| `Node` | A concept/entity (the graph's atom) | `graph_db.py:36-50` |
| `Flower` | A thematic cluster of Nodes | `graph_db.py:410-434` |
| `Session` | Tenant/container | `graph_db.py:552-572` |
| `TranscriptChunk` | Raw speech segment (Builder input) | `graph_db.py:718-749` |
| `Reference` | External enrichment (Researcher) | `graph_db.py:1244-1298` |
| `Source` | A cited URL (deduped by url) | `graph_db.py:1269-1271` |
| `SessionVocabulary` | STT correction map (JSON-string) | `graph_db.py:966-971` |
| `ProofreadCheckpoint` | Incremental-proofread cursor | `graph_db.py:1013-1018` |
| `SessionContext` | Rolling theme/entity context | `graph_db.py:1106-1108` |

### Relationships
| Type | Pattern | Notes |
|---|---|---|
| `RELATIONSHIP` | `(:Node)-[:RELATIONSHIP]->(:Node)` | **Single generic type**; semantics live in a `category` property — see §9 |
| `BELONGS_TO` | `(:Node)-[:BELONGS_TO]->(:Flower)` | Flower membership (replaces stored `flower_id`) |
| `HAS_CHUNK` | `(:Session)-[:HAS_CHUNK]->(:TranscriptChunk)` | |
| `HAS_REFERENCE` | `(:Node)-[:HAS_REFERENCE]->(:Reference)` | |
| `CITED_BY` | `(:Reference)-[:CITED_BY]->(:Source)` | |

### Constraints (all `IF NOT EXISTS`, `graph_schema.py:20-42`)
Uniqueness on `Node.id`, `RELATIONSHIP.id`, `Flower.id`, `Session.id`, `TranscriptChunk.id`. (Each unique constraint also provisions a backing range index.)

### Vector index (`graph_schema.py:65-76`)
```cypher
CREATE VECTOR INDEX node_embedding_index IF NOT EXISTS
FOR (n:Node) ON (n.embedding)
OPTIONS { indexConfig: {
  `vector.dimensions`: 768,
  `vector.similarity_function`: 'cosine' }}
```
Dimensions and function are injected from settings (`config.py:91-109`). **One global index over all `:Node` rows regardless of session.**

---

## 5. Logical data model

**Node** (`models/node.py`): `id`, `label`, `confidence` (0–1), `mentions`, `timestamps[]`, `inferred_type` (freeform "emergent" type — never enum), `flower_id` (derived from `BELONGS_TO`, **not stored**, `graph_db.py:498`), `embedding` (opt 768-float), `created_at`, `last_active`, `status`.
**NodeStatus** lifecycle (`models/enums.py:13-18`): `ghost` → `solid` → `legacy`.

**Relationship** (`models/relationship.py`): `id`, `source_id`, `target_id`, `category`, `description` (2–80 chars), `confidence`, `evidence`, `source` (builder|gardener), `created_at`.
**RelationshipCategory** (`enums.py:21-28`): exactly **CAUSAL, STRUCTURAL, COMPARATIVE, TEMPORAL, ASSOCIATIVE**.

**Flower** (`models/flower.py`): `id`, `label`, `stem_node_id` (highest-centrality node), `edge_count` (density proxy), `created_at`. `FlowerBridge` is **query-time only**, never persisted (`flower.py:29-37`).

**ReferenceNode** (`models/reference.py`): canonical summary + 1–5 embedded `ReferenceSource` citations, `entity_type`, `search_provider`, ambiguity/confirmation flags, and a `vocabulary_suggestion` map feeding STT correction.

---

## 6. Query & transaction patterns (the idioms)

The whole layer follows one consistent shape:

```python
driver = await get_driver()
async with driver.session() as session:
    async def _work(tx, cypher, params):
        result = await tx.run(cypher, **params)
        ...                      # .single() / async-for / .consume()
    return await session.execute_read|write(_work, query, params)
```

Notable, idiomatic patterns:
- **Managed transactions everywhere** → free transient-error retry (`execute_read`/`execute_write`).
- **MATCH-before-MERGE to avoid phantom nodes:** `create_relationship` matches both endpoints first and returns `None` if missing, rather than `MERGE`-creating empty nodes (`graph_db.py:269-299`).
- **Upserts** via `MERGE ... ON CREATE/ON MATCH SET` (`save_chunk`, `graph_db.py:728-735`).
- **`DETACH DELETE`** for nodes; **single-transaction cascade delete** of a whole session in ordered steps (`graph_db.py:659-699`).
- **Read fan-out:** `fetch_graph_state` runs nodes/rels/flowers concurrently via `asyncio.gather` (`graph_db.py:488-493`).
- **Payload hygiene:** the 768-float `embedding` is stripped from every read result (`graph_db.py:520-521`); datetimes hydrated via `Neo4jDateTime.to_native()` (`graph_db.py:541-544`).
- **Map workaround:** Neo4j can't store nested maps as properties, so the vocabulary map is serialized to a JSON **string** (`graph_db.py:916-986`).
- **Planner guard:** `get_recent_transcript` adds a computed `LIMIT` (conservative 20 words/chunk) to stop Neo4j over-planning (`graph_db.py:870-913`, ADR-0007).

Mild smells (safe but worth noting): dynamic Cypher assembled with f-strings for optional `WHERE`/`SET` clauses (`list_nodes`, `list_relationships`, `update_session_*`) — **values stay parameterized so there's no injection**, but clause names are string-built; and repeated function-local `import logging`/`import json`.

---

## 7. The dedup + vector-similarity pipeline (the heart)

This is the most distinctive and most reusable subsystem. Per extracted node, **at write time** (`builder_service.py:249-350`, `similarity.py:45-94`):

1. **Embed** the node label (`text-embedding-004`).
2. **ANN query** the global vector index for top-K (default 5) (`similarity.py:71-78`).
3. **Post-filter** the candidates by `session_id` and take the best (`similarity.py:74-77`).
4. **Triple-gate match decision** — a candidate becomes a *match* (increment `mentions`, no new node) only if **all** hold:
   - vector score **≥ 0.92** (`config.py:110`, ADR-0008),
   - extracted `confidence` **≥ 0.7** (`builder_service.py:293`),
   - **type compatibility** of `inferred_type` strings **≥ 0.80** via *their own* embedding cosine (`similarity.py:147-187`, `config.py:168`, ADR-0013).
5. Else **create a new `ghost` node** with its embedding. Any error → fail-open to node creation (`builder_service.py:337-348`).

Supporting detail: type-name embeddings are memoized in a manual `OrderedDict` LRU (256 entries, `similarity.py:100-125`); type cosine is computed in NumPy (`similarity.py:128-144`). The match-vs-create result drives relationship rewiring to **canonical** node IDs (`builder_service.py:352-404`).

**Why it's interesting:** entity resolution happens *before* the write, not as a later batch merge. The third gate (semantic type compatibility via embeddings, not a hardcoded synonym dict) is a genuinely elegant way to keep "emergent types" while preventing e.g. an *organisation* "Apple" from merging with a *fruit* "Apple."

---

## 8. Agent coupling (how the graph is driven)

- **Builder** (request-driven): one chunk → extract → dedup → persist → SSE broadcast → maybe trigger Gardener (`builder_service.py`).
- **Gardener / Researcher** run as background schedulers started in `lifespan` (`main.py:67-68`).
- **Ratio-based pacing:** Gardener fires every *N* Builder runs via an **in-process per-session counter** `_builder_runs` (`builder_service.py:80,494-512`) rather than a timer. Effective, but **in-memory** (see §11 scaling note).
- Documented design choices (ADRs): **LLM clustering over GDS** (0001), **full-context Q&A over GraphRAG retrieval** (0004), **plain async + Redis Streams over LangGraph** (0006). These are deliberate "small-graph" bets.

---

## 9. Notable / interesting design elements

1. **Single generic `:RELATIONSHIP` type, category-as-property.** Semantics (CAUSAL/STRUCTURAL/…) live in a property, not the edge type. Buys uniform constraints + schema-free flexibility for LLM output; **costs** idiomatic traversal (`-[:CAUSAL]->`), per-type indexing, and Cypher expressiveness. (See §10.)
2. **Write-time entity resolution via vector ANN** (§7) — unusual; most KG pipelines dedup in a later pass.
3. **Embedding-similarity *type* compatibility** (ADR-0013) instead of a synonym dictionary — scales to unseen types for free.
4. **Botanical lifecycle model**: `ghost → solid → legacy`, with **temporal decay** that flips `solid → legacy` after 5 min of inactivity via `datetime() - duration({minutes})` (`graph_db.py:1202-1237`). The graph is treated as a *living* artifact, not a static store.
5. **Membership as relationship, not property** (`BELONGS_TO`, `flower_id` never stored) — clean, normalized, and avoids dual-write drift.
6. **Derived-not-stored bridges** (`FlowerBridge`) — inter-cluster edges are computed at query time, keeping the persisted model minimal.
7. **Global vector index + session post-filter** — a single index serves all tenants (§10 discusses the tradeoff).

---

## 10. Best-practice scorecard

**Idiomatic / strong (keep as-is):**
- ✅ Async driver + **managed transactions** with retry — exactly per Neo4j guidance.
- ✅ **Parameterized** queries throughout — no injection surface.
- ✅ Correct **lifecycle** (lazy singleton, graceful close, startup healthcheck).
- ✅ **Idempotent** startup schema (`IF NOT EXISTS`); uniqueness constraints on all ids.
- ✅ Defensive writes (MATCH-before-MERGE, `DETACH DELETE`, single-tx cascade).
- ✅ Native **vector index** (cosine, 768) — the modern Neo4j 5.x approach.
- ✅ Read **payload hygiene** (drop embeddings) and **datetime** hydration.

**Debatable / non-idiomatic (revisit before scaling or porting):**
- ⚠️ **Generic relationship type.** Standard practice favors typed edges for traversal performance and readable Cypher. Acceptable here given LLM-emergent categories and a tiny per-session graph; reconsider if traversals or analytics matter.
- ⚠️ **Property-based multitenancy + one global vector index.** The ANN returns top-K *globally*, then filters by `session_id` (`similarity.py:71-78`). At multi-tenant scale this **hurts recall** (a true same-session match can be crowded out of the top-K by other sessions) and wastes compute. Best-practice alternatives: Neo4j **multi-database** per tenant, a **per-tenant label**, or **filtered vector search** (newer Neo4j) / a larger K with overfetch.
- ⚠️ **No bulk batching.** Nodes and relationships are persisted one-await-at-a-time (`builder_service.py:_check_similarity_and_persist`, `_persist_nodes`, `_persist_relationships`) → N+1 round-trips per chunk. `UNWIND`-based batch writes (already used for `Source`, `graph_db.py:1268-1271`) would cut latency.
- ⚠️ **No repository abstraction/Protocol** — functions import-coupled; swap/mock relies on a `skip_neo4j` flag and `tests/fakes.py` rather than an interface.

---

## 11. Transferability assessment

The codebase splits cleanly into a **portable graph/vector core** and a **domain-coupled live-transcription shell**.

### Portable as-is (the crown jewels for a similar project)
1. **Driver lifecycle module** (`neo4j.py`) — domain-agnostic; copy verbatim.
2. **Idempotent schema-ensure pattern** (`graph_schema.py`) — swap labels/dims/function.
3. **Managed-transaction CRUD idiom** (the `_work` + `execute_read/write` closure) — reusable boilerplate.
4. **Vector dedup pipeline** (`similarity.run_similarity` + `_query_best_match`) — a generic *embed → ANN → threshold → match/create* engine usable for **any** entity-resolution / dedup problem. This is the highest-value transfer.
5. **Embedding-based compatibility gate** (`types_compatible`) — generic synonym-free matching technique.
6. **Pydantic ⇄ Neo4j hydration helpers** and the **JSON-string map** workaround — generic idioms.
7. **Single-transaction cascade delete** — generic tenant-teardown.

### Coupled / domain-specific (rework when porting)
- Flower/ghost/solid/legacy lifecycle + 5-minute temporal decay → tied to the live-transcription "garden" UX.
- Builder/Gardener/Researcher/Librarian split + ratio triggering → specific orchestration.
- `session_id`-as-tenant threaded through **every** function signature → generalize if your tenancy model differs.
- 5 fixed relationship categories + transcript/chunk/proofreading/vocabulary nodes → speech-domain semantics.

### Changes to make on transfer
1. **Pick a tenancy strategy deliberately.** If you need real isolation or many tenants, move off global-index-post-filter to multi-DB / per-tenant label / filtered vector search.
2. **Batch writes (`UNWIND`)** if throughput matters.
3. **Externalize in-memory counters** (`_builder_runs`) to Redis if you run >1 backend instance — today they're per-process and lost on restart.
4. **Decide typed vs generic edges** based on whether you traverse/aggregate by relationship semantics.
5. **Fix the two correctness issues in §12 first** — they travel with the copy-paste.

### vs. standard GraphRAG
This is **not** classic retrieval-GraphRAG (Microsoft GraphRAG / `neo4j-graphrag` / LlamaIndex KG), which batch-ingests, runs **GDS community detection (Leiden)**, and **retrieves** subgraphs at query time. Here the deliberate bets (ADR-0001/0004) are **LLM clustering** and **full-context Q&A** because per-session graphs are small (~50–100 nodes) and fit a 1M context window. **Implication for transfer:** the design is near-optimal for *small, ephemeral, per-session* graphs and ports cleanly to projects with the same shape; for *large or cross-session corpora* you'd graft on GDS clustering + real graph retrieval, and the global-index tenancy choice becomes a liability.

---

## 12. Risks, bugs & doc drift found (code-grounded)

| Sev | Finding | Location | Note |
|---|---|---|---|
| **HIGH** | Latent `NameError`: `_logger` used but never defined in `delete_node`'s scope (no module-level `_logger`; other funcs define it locally) | `graph_db.py:122` | Only fires on the "node already deleted" warning path, so it lurks. Add a module logger. |
| **MED** | `update_node`/`create_node` do `SET n = $node` (full overwrite) while `_node_to_properties` drops `embedding` when `None` → updating a node without a populated embedding **erases the stored vector** | `graph_db.py:78-98,496-502` | Use `SET n += $node`, or always carry the embedding. Matters because the vector index depends on it. |
| **MED** | Global-index ANN + session post-filter can drop valid same-session matches when other sessions crowd the top-K | `similarity.py:71-78` | Recall risk grows with tenant count; see §10/§11. |
| **LOW** | In-memory `_builder_runs` counter is non-durable and not multi-instance safe | `builder_service.py:80,494` | Move to Redis for scale-out. |
| **LOW** | N+1 write round-trips per chunk | `builder_service.py:415-438` | `UNWIND` batch. |
| **DOC** | Architecture report states similarity threshold **0.85**; real value is **0.92** | `NEO4J_ARCHITECTURE_REPORT.md:40` vs `config.py:110` | Also echoed stale in `models/node.py:28` ("≥0.85"). |
| **DOC** | Architecture report lists a `hierarchical` relationship category that **does not exist**; the enum is `COMPARATIVE` | report vs `models/enums.py:25` | Update the report. |
| **DOC** | `NEO4J_ARCHITECTURE_REPORT.md` (dated 20 Dec) predates ADR-0008/0011/0013 and is partly superseded | report header | Refresh or mark historical. |

---

## 13. Per-file technical breakdown

| File | LOC | Responsibility | Highlights |
|---|---|---|---|
| `services/neo4j.py` | 54 | Driver lifecycle | Lazy singleton, close, healthcheck. Clean, portable. |
| `services/graph_schema.py` | 87 | Constraints + vector index | Idempotent; settings-driven dims/function. |
| `services/graph_db.py` | 1417 | All persistence (≈40 funcs) | Node/Rel/Flower/Session/Chunk/Reference/Vocabulary/Context CRUD; hydration helpers; temporal decay; cascade delete. Contains the §12 HIGH/MED bugs. |
| `services/similarity.py` | 202 | Embed → ANN → decision | `run_similarity`, `_query_best_match` (global index + session filter), `types_compatible` + LRU. The reusable core. |
| `services/builder_service.py` | 585 | Write-path orchestration | Triple-gate dedup, relationship rewiring, SSE, ratio-based Gardener trigger, timeout/retry. |
| `services/chunk_store.py` | 38 | Chunk repo wrapper | Thin class over `graph_db`; `delete` is a no-op. |
| `config.py` | 196 | Settings | Connection, pool, embedding, thresholds (0.92/0.80), agent flags. |
| `main.py` | 98 | App lifespan | Driver+schema+healthcheck boot, scheduler start/stop, IPv4/Windows hardening. |
| `models/{node,relationship,flower,enums,chunk,reference}.py` | — | Pydantic contracts | Emergent `inferred_type`; 5 fixed rel categories; ghost/solid/legacy; derived `flower_id`. |

---

*Spec compiled from source on the working tree; citations are to the repository at the time of analysis. Treat the docs flagged in §12 as historical until refreshed.*

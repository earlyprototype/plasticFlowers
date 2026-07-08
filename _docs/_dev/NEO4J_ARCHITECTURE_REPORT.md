# Neo4j Architecture Report - PlasticFlower

**Generated:** 20 December 2025  
**Status:** Operational  
**Version:** Gate 7 (Continuous Speech & Organic Layout)

---

## Executive Summary

Neo4j serves as the primary persistence layer for the PlasticFlower application, providing graph database capabilities for storing transcript-derived knowledge graphs, performing semantic similarity searches via vector indices, and managing session-based data isolation.

**Current Status:** Fully functional and operational
- Container: `plasticflower-neo4j` (healthy)
- Ports: 7474 (browser), 7687 (Bolt protocol)
- Connection: `neo4j://localhost:7687`

---

## 1. Configuration

### Environment Variables

Neo4j configuration is centralised in `backend/app/config.py` with environment variable overrides:

| Parameter | Default | Current Value | Description |
|-----------|---------|---------------|-------------|
| `NEO4J_URI` | `neo4j://127.0.0.1:7687` | `neo4j://localhost:7687` | Bolt protocol connection URI |
| `NEO4J_USERNAME` | `neo4j` | `neo4j` | Authentication username |
| `NEO4J_PASSWORD` | `plasticflower` | `pfNeo4j2025!` | Authentication password |
| `NEO4J_MAX_CONNECTION_POOL_SIZE` | `10` | `10` | Maximum concurrent connections |
| `NEO4J_MAX_CONNECTION_LIFETIME` | `3600` | `3600` | Connection recycling interval (seconds) |

### Vector Index Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| `EMBEDDING_DIMENSIONS` | `768` | Vector dimensions (Google text-embedding-004) |
| `EMBEDDING_SIMILARITY_FUNCTION` | `cosine` | Similarity metric for vector search |
| `SIMILARITY_THRESHOLD` | `0.92` | Deduplication threshold |
| `SIMILARITY_TOP_K` | `5` | Top candidates fetched before filtering |

---

## 2. Data Model

### Node Types

Neo4j stores five primary node types in the PlasticFlower graph:

#### 2.1 Node (Concepts)
Represents concepts extracted from transcripts.

**Properties:**
- `id` (string, unique): Stable identifier
- `label` (string): Display label from transcript
- `confidence` (float, 0-1): LLM certainty score
- `mentions` (int): Reference count (similarity ≥0.92)
- `timestamps` (float[]): Session-relative mention times
- `inferred_type` (string): Emergent, freeform type
- `embedding` (float[768]): Vector for similarity search
- `created_at` (datetime): Creation timestamp
- `status` (enum): `ghost` (Builder) or `solid` (Gardener)
- `session_id` (string): Session isolation key

**Note:** The `flower_id` field exposed in the API `Node` model is **not stored as a property**. It is derived at query time from the `BELONGS_TO` relationship.

#### 2.2 Relationship
Connections between nodes with semantic metadata.

**Properties:**
- `id` (string, unique): Stable identifier
- `source_id` (string): Source node ID
- `target_id` (string): Target node ID
- `category` (enum): `causal`, `structural`, `temporal`, `comparative`, `associative`
- `source` (enum): `builder` or `gardener`
- `label` (string, optional): Edge label (not currently used by LLM)
- `description` (string): Natural language description of the relationship
- `confidence` (float, 0-1): LLM certainty
- `evidence` (string): Supporting text snippet
- `created_at` (datetime): Creation timestamp
- `session_id` (string): Session isolation key

#### 2.3 Flower (Clusters)
Thematic groupings of related nodes.

**Properties:**
- `id` (string, unique): Stable identifier
- `label` (string): Theme name (2-5 words)
- `stem_node_id` (string): ID of the central "hub" node
- `edge_count` (int): Simple density proxy
- `created_at` (datetime): Creation timestamp
- `session_id` (string): Session isolation key

**Membership Model:**
Flower membership is stored exclusively via `(:Node)-[:BELONGS_TO]->(:Flower)` relationships. This structure:
- Supports native graph queries for cluster analysis
- Allows efficient filtering
- Removes data duplication (no `flower_id` property sync needed)

**Query Patterns:**
```cypher
// Get all nodes in a flower
MATCH (n:Node)-[:BELONGS_TO]->(f:Flower {id: $flower_id})
RETURN n

// Get flower for a specific node
MATCH (n:Node {id: $node_id})-[:BELONGS_TO]->(f:Flower)
RETURN f

// List nodes with their flowers (API Response Construction)
MATCH (n:Node {session_id: $session_id})
OPTIONAL MATCH (n)-[:BELONGS_TO]->(f:Flower)
RETURN n, f.id AS flower_id
```

#### 2.4 Session
User sessions containing all graph data.

**Properties:**
- `id` (string, unique): Session identifier
- `name` (string): Display name
- `created_at` (datetime): Session start time
- `ended_at` (datetime, nullable): Session end time

#### 2.5 TranscriptChunk
Raw transcript segments linked to sessions.

**Properties:**
- `id` (string, unique): Chunk identifier
- `session_id` (string): Parent session
- `text` (string): Transcript content
- `start_time` (float): Session-relative start time
- `end_time` (float): Session-relative end time

### Relationship Types

- `RELATIONSHIP`: Generic edge type connecting `Node` entities (properties stored on edge)
- `BELONGS_TO`: Node → Flower (cluster membership)
- `HAS_CHUNK`: Session → TranscriptChunk (ownership)

---

## 3. Schema Enforcement

The application ensures database schema integrity on startup via `services/graph_schema.py`.

### Unique Constraints

```cypher
CREATE CONSTRAINT node_id_unique IF NOT EXISTS 
FOR (n:Node) REQUIRE n.id IS UNIQUE

CREATE CONSTRAINT relationship_id_unique IF NOT EXISTS 
FOR ()-[r:RELATIONSHIP]->() REQUIRE r.id IS UNIQUE

CREATE CONSTRAINT flower_id_unique IF NOT EXISTS 
FOR (f:Flower) REQUIRE f.id IS UNIQUE

CREATE CONSTRAINT session_id_unique IF NOT EXISTS 
FOR (s:Session) REQUIRE s.id IS UNIQUE

CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS 
FOR (c:TranscriptChunk) REQUIRE c.id IS UNIQUE
```

### Vector Index

```cypher
CREATE VECTOR INDEX node_embedding_index IF NOT EXISTS
FOR (n:Node) ON (n.embedding)
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 768,
    `vector.similarity_function`: 'cosine'
  }
}
```

This index enables semantic similarity search for deduplication and concept matching.

---

## 4. Component Architecture

### 4.1 Driver Management (`services/neo4j.py`)

**Purpose:** Centralised async Neo4j driver lifecycle management.

**Key Functions:**
- `get_driver()`: Lazy initialisation with connection pooling
- `close_driver()`: Graceful shutdown
- `run_healthcheck()`: Connectivity verification

**Features:**
- Global singleton pattern
- IPv4-only resolution (Windows optimisation)
- Connection pooling (max 10 concurrent)
- Connection recycling (3600s lifetime)

### 4.2 CRUD Layer (`services/graph_db.py`)

**Purpose:** Data access abstraction for all Neo4j operations.

**Modules:**
1. **Node Operations**
   - `create_node`, `get_node`, `update_node`, `delete_node`
   - `list_nodes`: Fetches nodes and OPTIONALLY matches `:BELONGS_TO` to populate the `flower_id` field for the API.
   - `record_node_mention`: Atomic increment + timestamp append.
   - `set_node_flower`: Manages the `:BELONGS_TO` relationship (create/delete).

2. **Relationship Operations**
   - Full CRUD: `create_relationship`, `get_relationship`, `update_relationship`, `delete_relationship`
   - `list_relationships`

3. **Flower Operations**
   - `upsert_flower`, `delete_flower`, `list_flowers`

4. **Session Management**
   - `create_session_record`, `get_session_record`, `list_session_records`
   - `update_session_record`, `delete_session_record` (cascading delete)

5. **Chunk Persistence**
   - `save_chunk`, `get_chunk`, `list_chunks_for_session`, `delete_chunks_for_session`

6. **Transcript Retrieval**
   - `get_recent_transcript`: Fetches chunks in reverse chronological order and returns the most recent 1000 words. This provides context for the Gardener without overloading the context window.

7. **Graph State**
   - `fetch_graph_state`: Parallel fetch of nodes, relationships, and flowers using `asyncio.gather`.

### 4.3 Similarity Pipeline (`services/similarity.py`)

**Purpose:** Semantic deduplication via vector similarity search.

**Flow:**
1. Generate embedding for incoming node label
2. Query Neo4j vector index for top-K similar nodes (session-scoped)
3. If best match ≥ 0.92 threshold:
   - Increment `mentions` counter
   - Append timestamp to existing node
   - Return `SimilarityMatchResult`
4. Else:
   - Return `SimilarityCreateResult` (signal new ghost node)

### 4.4 API Layer (`api/graph.py`)

**Purpose:** RESTful endpoints for graph data access.

**Endpoints:**
- `GET /sessions/{id}/graph` → Full graph state (nodes, relationships, flowers)
- `GET /sessions/{id}/nodes` → Filtered node list
- `GET /sessions/{id}/relationships` → Filtered relationships
- `GET /sessions/{id}/flowers` → Flower clusters

---

## 5. Integration Points

### 5.1 Application Startup (`main.py`)

Neo4j initialisation sequence:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Get/create async driver
    driver = await get_driver()
    
    # 2. Ensure schema (constraints + vector index)
    await ensure_graph_schema(driver)
    
    # 3. Verify connectivity
    await run_healthcheck()
    
    # 4. Start Gardener scheduler
    await gardener_scheduler.start()
    
    yield
    
    # Shutdown: stop scheduler, close driver
    await gardener_scheduler.stop()
    await close_driver()
```

### 5.2 Builder Agent Integration (`agents/builder.py`)
- **Writes:** Creates new "Ghost" nodes and relationships.
- **Reads:** Uses vector similarity (via `similarity.py`) to avoid creating duplicates of existing nodes.
- **Latency:** Must be fast (<500ms DB ops) to support continuous speech.

### 5.3 Gardener Agent Integration (`agents/gardener.py`)
- **Reads:** Fetches full graph state + recent transcript context.
- **Writes:**
    - Promotes Ghost → Solid (`update_node`)
    - Merges nodes (`delete_node` + `update_relationship`)
    - Form/Update/Dissolve Flowers (`upsert_flower`, `delete_flower`, `set_node_flower`)
- **Latency:** Asynchronous background task; transaction times are less critical.

### 5.4 Frontend Integration (SSE + API)
- **Data Flow:** Neo4j → API/SSE → React State → Cytoscape.
- **Visuals:**
    - `flower_id` (derived from Neo4j relationships) determines cluster rendering.
    - `timestamps` (stored in Neo4j) drive the "temporal breathing" animation.

---

## 6. Data Flow Diagram

```
┌─────────────────┐
│ User Transcript │
└────────┬────────┘
         │
         v
  ┌─────────────┐
  │   Builder   │─────┐
  │    Agent    │     │ 1. Generate embedding
  └─────────────┘     │ 2. Vector similarity search
         │            v
         │      ┌──────────────────┐
         │      │ Neo4j Vector     │
         │      │ Index Search     │
         │      └──────────────────┘
         │            │
         │            v
         │      [Match ≥0.92?]
         │       /          \
         │    Yes            No
         │     │              │
         │     v              v
         │  [Increment]  [Create Ghost]
         │     │              │
         └─────┴──────────────┘
               │
               v
        ┌─────────────┐
        │   Neo4j DB  │
        │ (Nodes + tx)│
        └─────────────┘
               │
               v
        ┌─────────────┐
        │  Gardener   │ (Scheduled)
        │   Agent     │
        └─────────────┘
               │
               v
        ┌─────────────┐
        │   Neo4j DB  │
        │ (Refinement,│
        │  Flowers)   │
        └─────────────┘
```

---

## 7. Performance Optimisations

### 7.1 Connection Pooling
- Max 10 concurrent connections
- Connection lifetime: 3600s
- Async driver for non-blocking I/O

### 7.2 Vector Index
- Dedicated HNSW index for 768-dimensional embeddings
- Session-scoped queries (reduces search space)
- Top-K filtering (5 candidates) before threshold check

### 7.3 Batch Operations
- `fetch_graph_state()` uses `asyncio.gather()` for parallel fetches
- Gardener processes multiple ghosts in single transaction

---

## 8. Health Monitoring

### 8.1 Startup Healthcheck
Executed during FastAPI lifespan startup:
```python
await run_healthcheck()  # RETURN 1 AS ok query
```

### 8.2 Runtime Healthcheck
Available via REST endpoint:
```bash
GET /health
```

### 8.3 Docker Container Status
```bash
docker ps --filter "name=neo4j"
```

---

## 9. Session Isolation

All data is scoped to sessions via the `session_id` property.

**Session Deletion:**
Cascade order: Relationships → Nodes → Flowers → Chunks → Session

---

## 10. Known Limitations

1. **No Cross-Session Queries:** Current architecture isolates sessions completely.
2. **Vector Index Session Filtering:** Session filtering happens post-search.
3. **Single Vector Index:** All nodes share one embedding space.

---

## 11. Future Considerations

### 11.1 Scaling
- Read replicas for query-heavy workloads
- Sharding by session_id

### 11.2 Advanced Queries
- Graph algorithms (PageRank) for flower generation
- Full-text search indices on node labels

---

## 12. Conclusion

Neo4j is the **critical persistence backbone** of PlasticFlower. The schema is robust, the vector index enables effective deduplication, and the graph model (particularly the `Flower` and `BELONGS_TO` structure) directly supports the application's unique "organic" visualization needs.

**Operational Status:** Healthy and functional.

---

**Report End**
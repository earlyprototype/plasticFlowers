# Vector Index Architecture: Chunks, Builder, and Embeddings

**Date:** 30 December 2025  
**Context:** Understanding how the vector index is created and used in plasticFlower

---

## Overview

The vector index enables semantic similarity search for node deduplication. This document explains how embeddings flow through the system.

---

## Architecture Diagram

```
                                 INGESTION FLOW
    ============================================================================
    
    Frontend (Browser)
           |
           | WebSpeech API produces text
           v
    +------------------+
    | POST /chunks     |  Transcript chunk submitted
    +------------------+
           |
           v
    +------------------+
    | TranscriptChunk  |  Stored in Neo4j (text, timestamps)
    | (Neo4j Node)     |
    +------------------+
           |
           v
    +------------------+
    | BuilderService   |  Orchestrates extraction
    +------------------+
           |
           +---> 1. Load existing nodes (labels only, no embeddings)
           |
           v
    +------------------+
    | Builder Agent    |  Calls Gemini LLM
    | (LLM Call)       |  Extracts entities & relationships
    +------------------+
           |
           | Returns: nodes[] and relationships[]
           v
    +------------------+
    | Embedding Gen    |  Calls Google text-embedding-004
    | (Google API)     |  768 dimensions per node label
    +------------------+
           |
           | ~100-200ms per embedding
           v
    +------------------+
    | Neo4j Persist    |  Node stored WITH embedding vector
    | (CREATE Node)    |  embedding property = float[768]
    +------------------+
           |
           v
    +------------------+
    | Vector Index     |  Automatically indexes new embedding
    | (Neo4j Native)   |  node_embedding_index
    +------------------+
    
    
                              SIMILARITY SEARCH FLOW
    ============================================================================
    
    +------------------+
    | Gardener Agent   |  During merge/dedup decision
    +------------------+
           |
           | Needs to find similar nodes
           v
    +------------------+
    | Vector Query     |  db.index.vector.queryNodes()
    | (Neo4j API)      |  Returns top-K similar nodes
    +------------------+
           |
           | Threshold: 0.92 (ADR-008)
           v
    +------------------+
    | Merge Decision   |  If score >= 0.92: same concept
    | (Gardener LLM)   |  LLM confirms/overrides
    +------------------+
```

---

## Timeline: What Happens When a Chunk Arrives

```
Time    Event                                    Duration
----    -----                                    --------
0ms     Frontend submits chunk via POST          ~10ms
        
10ms    Chunk saved to Neo4j                     ~20ms
        TranscriptChunk node created
        
30ms    BuilderService.process_chunk() starts
        
35ms    Load existing nodes from Neo4j           ~50ms
        (labels only, for LLM context)
        
85ms    Builder LLM call                         ~2000ms
        Gemini extracts entities
        
2085ms  Embedding generation begins              ~300ms
        (parallel for all extracted nodes)
        Each embedding: 100-200ms Google API
        
2385ms  Persist nodes to Neo4j                   ~100ms
        Node + embedding stored together
        Vector index auto-updates
        
2485ms  SSE broadcast: node_added events         ~10ms

2495ms  Publish to Redis (ratio-based)           ~5ms
        Triggers Gardener every 5 chunks
        
        [CHUNK PROCESSING COMPLETE]

        
        ... 4 more chunks processed ...
        

~15s    Gardener triggered (after 5 chunks)      ~10-20s
        
        Gardener loads all nodes + embeddings
        Gardener queries vector index for hints
        Gardener LLM decides: confirm/merge/prune
        
        [GARDENER CYCLE COMPLETE]
```

---

## Key Components Explained

### 1. Vector Index Creation (Startup)

**File:** `backend/app/services/graph_schema.py`

```python
CREATE VECTOR INDEX node_embedding_index IF NOT EXISTS
FOR (n:Node) ON (n.embedding)
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 768,
    `vector.similarity_function`: 'cosine'
  }
}
```

**When:** Application startup (`main.py` -> `ensure_graph_schema()`)

**What it does:** Creates a Neo4j native vector index on the `embedding` property of all `Node` labels. This index enables fast approximate nearest neighbour (ANN) search.

---

### 2. Embedding Generation

**File:** `backend/app/services/embeddings.py`

```python
async def generate_embedding(text: str) -> List[float]:
    # Calls Google text-embedding-004
    # Returns 768-dimensional vector
    response = client.models.embed_content(
        model="models/text-embedding-004",
        contents=text,
        config={'task_type': 'retrieval_document'}
    )
    return response.embeddings[0].values
```

**When:** After Builder LLM returns, before persisting nodes

**What it does:** 
1. Takes node label (e.g., "machine learning")
2. Calls Google embedding API
3. Returns 768 floats representing semantic meaning
4. Caches result (LRU cache, 512 entries)

---

### 3. Node Persistence with Embedding

**File:** `backend/app/services/builder_service.py`

```python
async def _populate_embeddings(self, nodes: List[Node]) -> None:
    tasks = [generate_embedding(node.label) for node in nodes]
    vectors = await asyncio.gather(*tasks)
    for node, vector in zip(nodes, vectors):
        node.embedding = vector  # Attached to node model

async def _persist_nodes(self, session_id: str, nodes: List[Node]) -> List[Node]:
    for node in nodes:
        await create_node(session_id, node)  # Includes embedding
```

**When:** After LLM extraction, before SSE broadcast

**What it does:**
1. Generates embeddings in parallel (async)
2. Attaches vector to each node
3. Persists node to Neo4j (embedding included)
4. Vector index automatically picks up new embedding

---

### 4. Similarity Search (Exists but NOT Used by Builder)

**File:** `backend/app/services/similarity.py`

```python
async def run_similarity(session_id: str, label: str, timestamp: float):
    embedding = await generate_embedding(label)
    candidate = await _query_best_match(session_id, embedding, top_k=5)
    
    if candidate and candidate.score >= 0.92:
        # Found existing node - increment mentions
        return SimilarityMatchResult(...)
    else:
        # No match - caller should create new node
        return SimilarityCreateResult(...)
```

**IMPORTANT:** This function exists but is **NOT called by BuilderService**.

The Builder creates all extracted nodes regardless of similarity. Deduplication happens later in the Gardener.

---

## Pre-Creation Similarity Check (APPROVED)

### Decision: Implement Pre-Check

After architecture review (30 December 2025), pre-creation similarity checking was approved for implementation. The benefits significantly outweigh the latency cost.

### Previous Flow (No Pre-Check)

```
Chunk arrives
    |
    v
Builder LLM extracts ["machine learning", "ML", "AI"]
    |
    v
Generate embeddings for ALL 3 labels
    |
    v
Create 3 GHOST nodes (even though ML and machine learning might be same concept)
    |
    v
[Later] Gardener merges duplicates
```

### New Flow (With Pre-Check) - APPROVED

```
Chunk arrives
    |
    v
Builder LLM extracts ["machine learning", "ML", "AI"]
    |
    v
For each label:
  - Generate embedding
  - Query vector index for similar nodes
  - Apply disambiguation checks:
    * Score >= 0.92?
    * Types compatible?
    * Confidence >= 0.7?
  - If all pass: MATCH (increment existing node)
  - Otherwise: CREATE new GHOST node
    |
    v
Create only 1-2 GHOST nodes (duplicates caught early)
Matched nodes get mentions incremented
    |
    v
Relationships rewired to use correct node IDs
    |
    v
SSE: node_added (new) or node_updated (matched)
    |
    v
[Later] Gardener has reduced merge workload
```

### Trade-off Analysis

| Approach | Pros | Cons |
|----------|------|------|
| Previous (Gardener cleanup) | Simpler Builder, faster per-chunk | More GHOST nodes, Gardener does more work |
| **New (Pre-check) APPROVED** | Fewer duplicates, accurate counts, better UX, less Gardener work | +200-500ms latency per chunk |

### Disambiguation Mitigations (Required)

To prevent false positive matches:

1. **Type matching:** Compare `inferred_type` - only match if types are compatible
2. **Confidence threshold:** Require similarity >= 0.92 AND LLM confidence >= 0.7

### Future Enhancements (Optional)

1. **Phrase length filter:** Skip similarity check for labels < 2 words
2. **Context embedding:** Include chunk context in embedding
3. **LLM prompt optimisation:** Pass semantic clusters to LLM to reduce duplicate extraction at source

---

## Neo4j Vector Query Details

**Query used for similarity search:**

```cypher
CALL db.index.vector.queryNodes('node_embedding_index', 5, $embedding)
YIELD node, score
WHERE node.session_id = $session_id
RETURN node.id AS node_id, score
ORDER BY score DESC
LIMIT 1
```

**Parameters:**
- `index_name`: "node_embedding_index"
- `top_k`: 5 (fetch 5 candidates)
- `embedding`: 768-float vector
- `session_id`: Current session (scope to session)

**Returns:**
- `node_id`: ID of most similar node
- `score`: Cosine similarity (0.0 to 1.0)

**Threshold:** 0.92 (per ADR-008)
- Score >= 0.92: Same concept (merge/increment)
- Score < 0.92: Different concept (create new)

---

## Summary

1. **Vector index** is created at app startup (idempotent)
2. **Embeddings** are generated AFTER Builder LLM returns
3. **Pre-creation similarity check** queries index before node creation (APPROVED)
4. **Matched nodes** get mentions incremented instead of creating duplicates
5. **New nodes** are stored with embedding attached
6. **Index auto-updates** when new nodes are created
7. **Gardener** handles edge cases missed by pre-check (synonyms, abbreviations)

The `run_similarity()` function is now integrated into Builder flow for pre-creation deduplication.

---

## Implementation Status

| Component | Status |
|-----------|--------|
| Vector index creation | Implemented |
| Embedding generation | Implemented |
| `run_similarity()` function | Implemented (was unused) |
| Pre-creation check in Builder | **PENDING** (approved for implementation) |
| Disambiguation mitigations | **PENDING** (type matching, confidence threshold) |
| SSE event updates | **PENDING** (`node_updated` for matches) |


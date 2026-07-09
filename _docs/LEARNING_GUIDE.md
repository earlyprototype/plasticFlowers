# plasticFlower Learning Guide

**Purpose:** Structured curriculum for learning Neo4j and Semantic Knowledge Graphs through plasticFlower development  
**Companion to:** [ARCHITECTURE_ADVISORY.md](./ARCHITECTURE_ADVISORY.md)  
**Last Updated:** 26 December 2025

---

## Using This Guide with AI Assistance

This guide is designed for **LLM-assisted development** with **cross-session persistence**.

### The Session State System

A single file tracks everything across coding sessions: **[_START_SESSION_STATE.md](./_START_SESSION_STATE.md)**

This file:
- Persists your progress when conversations end
- Gives any new LLM instant context
- Tracks decisions, blockers, and next steps
- Reduces cognitive load (no need to remember where you left off)

### Starting Any Coding Session

**Step 1:** Attach these files to your conversation:
```
@_START_SESSION_STATE.md
@LEARNING_GUIDE.md  (optional - for phase details)
@ARCHITECTURE_ADVISORY.md  (optional - for design questions)
```

**Step 2:** Say what you want to work on:
```
"Continue where I left off"
or
"Start Phase A, Exercise A.1"
or
"I have 2 hours, what can I accomplish?"
```

The LLM will read _START_SESSION_STATE.md and know exactly where you are.

### Ending Any Coding Session

Say: **"Update _START_SESSION_STATE.md with today's progress"**

The LLM will:
- Check off completed items
- Update the "Last Session" section
- Add a session log entry
- Note any blockers or decisions

### Quick Commands

| Say This | Get This |
|----------|----------|
| "Where was I?" | Reads _START_SESSION_STATE.md, tells you next step |
| "Phase [X] status" | Progress check against deliverables |
| "Explain [concept]" | ELI5 explanation with examples |
| "Exercise [X.Y] help" | Guided walkthrough |
| "Review my code" | Check against requirements |
| "What's next?" | Next logical task from your progress |
| "Update progress" | Updates _START_SESSION_STATE.md |
| "I'm stuck" | Adds blocker to _START_SESSION_STATE.md, helps debug |

### ADHD-Friendly Tips

1. **Always start by attaching _START_SESSION_STATE.md** - It's your external memory
2. **One exercise at a time** - Don't look ahead
3. **Time-box sessions** - "I have 90 minutes" helps scope work
4. **End sessions cleanly** - Update the state file before stopping
5. **It's OK to context-switch** - The state file remembers for you
6. **Ask for ELI5** - No shame in needing simpler explanations

---

## Learning Philosophy

This guide follows a **"build to learn"** approach:

1. Each phase delivers **working features** while teaching specific concepts
2. Complexity increases progressively - no deep-end moments
3. Hands-on exercises accompany each topic
4. You can pause between phases without breaking anything

---

## Curriculum Overview

| Phase | Focus | Duration | Key Concepts |
|-------|-------|----------|--------------|
| A | Neo4j Fundamentals | 1-2 weeks | Cypher, Nodes, Relationships, CRUD |
| B | Vector Embeddings | 1 week | Semantic similarity, Vector indexes |
| C | LLM Clustering | 1-2 weeks | Semantic grouping, Flower formation |
| D | Proofreading System | 1 week | Text correction, Vocabulary learning |
| E | GraphRAG + Q&A | 2 weeks | Hybrid retrieval, Context expansion |
| F | GDS Algorithms (Optional) | 2 weeks | Leiden, Betweenness, Graph science |
| G | Research Agent | 1 week | Web search, External enrichment |

**Core Curriculum (A-E, G):** 7-9 weeks  
**With Optional GDS (F):** 9-11 weeks

**Note:** Phase F is optional - add when sessions regularly exceed 100 nodes. All transcript data is permanently stored, so you can re-cluster with GDS algorithms retroactively.

---

## Phase A: Neo4j Fundamentals (Week 1-2)

### What You'll Build
- Extended transcript retrieval (3000 words)
- Improved graph state queries
- Session management improvements

### Concepts to Learn

#### A.1 Cypher Query Language Basics

**Cypher** is Neo4j's declarative query language. It uses ASCII-art patterns to describe graph structures.

```cypher
// Basic pattern: Find all nodes
MATCH (n:Node)
RETURN n

// Pattern with relationship
MATCH (a:Node)-[r:RELATIONSHIP]->(b:Node)
RETURN a, r, b

// Pattern with properties
MATCH (n:Node {session_id: "abc123"})
WHERE n.status = "SOLID"
RETURN n.label, n.confidence
```

**Key Syntax:**
| Element | Meaning |
|---------|---------|
| `(n)` | A node, optionally named `n` |
| `(n:Label)` | A node with label `Label` |
| `{prop: val}` | Property filter |
| `-[r]->` | A directed relationship |
| `-[:TYPE]->` | Relationship of type `TYPE` |
| `*1..3` | Variable path length (1 to 3 hops) |

#### A.2 CRUD Operations

```cypher
// CREATE - Add new data
CREATE (n:Node {id: "node1", label: "Machine Learning"})

// READ - Query existing data
MATCH (n:Node {id: "node1"})
RETURN n

// UPDATE - Modify data
MATCH (n:Node {id: "node1"})
SET n.confidence = 0.95, n.mentions = n.mentions + 1

// DELETE - Remove data
MATCH (n:Node {id: "node1"})
DETACH DELETE n  // DETACH removes connected relationships first
```

#### A.3 MERGE (Idempotent Create)

`MERGE` is crucial for plasticFlower - it creates if not exists, matches if exists.

```cypher
// Safe to run multiple times - won't create duplicates
MERGE (n:Node {id: $node_id, session_id: $session_id})
ON CREATE SET n.label = $label, n.created_at = datetime()
ON MATCH SET n.mentions = n.mentions + 1
RETURN n
```

### Hands-On Exercises

**Exercise A.1: Explore Your Graph**

Open Neo4j Browser (http://localhost:7474) and run:

```cypher
// 1. Count nodes per session
MATCH (n:Node)
RETURN n.session_id, count(n) as node_count
ORDER BY node_count DESC

// 2. Find nodes with most mentions
MATCH (n:Node)
RETURN n.label, n.mentions
ORDER BY n.mentions DESC
LIMIT 10

// 3. See relationship distribution
MATCH ()-[r:RELATIONSHIP]->()
RETURN r.category, count(r) as count
ORDER BY count DESC
```

**Exercise A.2: Query Optimisation**

Your current `get_recent_transcript` uses word counting in Python. Rewrite it to do more work in Cypher:

```cypher
// Task: Get last 3000 words efficiently
// Hint: Use string functions and aggregation
MATCH (c:TranscriptChunk {session_id: $session_id})
RETURN c.text, c.start_time
ORDER BY c.start_time DESC
// Your Python code then processes until 3000 words reached
```

**Exercise A.3: Create the Extended Transcript Query**

Modify `graph_db.py` to implement extended transcript retrieval with 3000-word default.

> **Note (2025-12-26):** This functionality is provided by the existing `get_recent_transcript()` 
> function in `graph_db.py`. The function was optimised in A.2 to default to 3000 words and 
> includes a LIMIT clause for query efficiency. No separate function needed.

```python
# Existing function signature (already implemented):
async def get_recent_transcript(session_id: str, word_limit: int = 3000) -> str:
    """Fetch recent chunks up to word_limit with LIMIT optimisation."""
```

### Deliverable
- [x] Extended transcript function working with 3000-word limit (`get_recent_transcript`)
- [x] Understand MATCH, WHERE, RETURN, ORDER BY, LIMIT
- [x] Comfortable running queries in Neo4j Browser

---

## Phase B: Vector Embeddings (Week 3)

### What You'll Build
- Verify/create vector index
- Improve similarity detection
- Test embedding-based deduplication

### Concepts to Learn

#### B.1 What Are Embeddings?

Embeddings convert text into numerical vectors that capture **semantic meaning**. Similar concepts have vectors that are close together in high-dimensional space.

```
"Machine Learning"  → [0.23, -0.45, 0.12, ..., 0.89]  (768 numbers)
"AI Training"       → [0.21, -0.43, 0.14, ..., 0.87]  (similar vector)
"Kitchen Sink"      → [-0.56, 0.12, -0.78, ..., 0.01] (very different)
```

**Cosine Similarity:** Measures angle between vectors (0 to 1)
- 1.0 = identical meaning
- 0.85+ = very similar (good merge candidate)
- 0.5 = somewhat related
- 0.0 = unrelated

#### B.2 Neo4j Vector Index

Neo4j 5.x has native vector indexing:

```cypher
// Create vector index (run once)
CREATE VECTOR INDEX node_embeddings IF NOT EXISTS
FOR (n:Node)
ON n.embedding
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 768,
    `vector.similarity_function`: 'cosine'
  }
}

// Query similar nodes
CALL db.index.vector.queryNodes(
    'node_embeddings',  // index name
    10,                 // top K results
    $query_vector       // 768-dim array
)
YIELD node, score
WHERE node.session_id = $session_id
RETURN node.label, score
ORDER BY score DESC
```

#### B.3 Embedding Models

plasticFlower uses Gemini's `text-embedding-004`:
- 768 dimensions
- Good semantic understanding
- Task-specific variants (RETRIEVAL_DOCUMENT, RETRIEVAL_QUERY)

```python
from google import genai

client = genai.Client(api_key=API_KEY)

# Embed a concept label
result = client.models.embed_content(
    model="text-embedding-004",
    contents="Machine Learning",
    config={"task_type": "RETRIEVAL_DOCUMENT"}
)
embedding = result.embeddings[0].values  # 768-dim list
```

### Hands-On Exercises

**Exercise B.1: Check Your Vector Index**

```cypher
// List all indexes
SHOW INDEXES

// Check if vector index exists
SHOW INDEXES WHERE type = 'VECTOR'
```

**Exercise B.2: Test Similarity Search**

```python
# In your backend, create a test script:
async def test_similarity():
    # 1. Pick a node with known similar concepts
    test_label = "artificial intelligence"
    
    # 2. Get its embedding
    embedding = await get_embedding(test_label)
    
    # 3. Query similar nodes
    similar = await find_similar_nodes(session_id, embedding, threshold=0.8)
    
    # 4. Print results
    for node, score in similar:
        print(f"{node.label}: {score:.3f}")
```

**Exercise B.3: Tune the Threshold**

Create test cases to find the optimal similarity threshold:

| Test Case | Node A | Node B | Expected | Your Threshold |
|-----------|--------|--------|----------|----------------|
| Obvious match | "ML" | "Machine Learning" | MERGE | ? |
| Subtle match | "AI" | "Artificial Intelligence" | MERGE | ? |
| Different | "AI" | "Artificial Sweetener" | NO MERGE | ? |
| Edge case | "Graph DB" | "Neo4j" | MERGE? | ? |

### Deliverable
- [ ] Vector index verified/created
- [ ] Understand cosine similarity
- [ ] Optimal threshold documented (probably 0.82-0.88)

---

## Phase C: LLM Clustering (Week 4-5)

### What You'll Build
- Semantic Flower formation using LLM reasoning
- Keystone node identification
- Cluster labeling

### Concepts to Learn

#### C.1 Semantic vs Structural Clustering

**Structural Clustering (GDS):**
- Groups nodes by connection patterns
- "These nodes have many edges between them"
- Fast, deterministic, scalable

**Semantic Clustering (LLM):**
- Groups nodes by meaning
- "These nodes are all about funding opportunities"
- Context-aware, intuitive, works with few edges

For < 100 nodes, semantic clustering is better because:
- Nodes might not have many relationships yet
- LLM understands domain context
- Results are more intuitive

#### C.2 Flower Formation Criteria

A Flower (cluster) should have:
- 3+ nodes minimum
- 2+ internal connections
- Thematic coherence (LLM judges this)
- A "stem" node (most central concept)

#### C.3 LLM Prompt for Clustering

```
Given these nodes and relationships, identify thematic clusters.

Nodes: ["Machine Learning", "Neural Networks", "Python", "TensorFlow", 
        "Funding Opportunity", "Arts Council", "Grant Application"]

Relationships: 
- "Neural Networks" -> "Machine Learning" (STRUCTURAL)
- "TensorFlow" -> "Python" (STRUCTURAL)
- "Grant Application" -> "Funding Opportunity" (CAUSAL)

Group nodes that belong together thematically. Each group needs:
- A name (2-4 words)
- A stem node (the central concept)
- Member nodes

Output JSON:
{
  "clusters": [
    {"name": "AI/ML Technology", "stem": "Machine Learning", 
     "members": ["Neural Networks", "Python", "TensorFlow"]},
    {"name": "Funding & Grants", "stem": "Funding Opportunity",
     "members": ["Arts Council", "Grant Application"]}
  ]
}
```

### Hands-On Exercises

**Exercise C.1: Manual Clustering**

Load your test session graph and manually identify clusters. Document:
- Which nodes group together?
- What would you name each group?
- Which node is the "stem"?

**Exercise C.2: Implement LLM Clustering**

Add to Gardener:

```python
async def cluster_with_llm(nodes: List[Node], relationships: List[Relationship]) -> List[Flower]:
    prompt = CLUSTERING_PROMPT.format(
        nodes=[n.label for n in nodes],
        relationships=[f"{r.source_id} -> {r.target_id}" for r in relationships]
    )
    
    result = await llm.generate(prompt, response_format="json")
    
    flowers = []
    for cluster in result.clusters:
        flower = Flower(
            id=generate_id(),
            label=cluster.name,
            stem_node_id=find_node_id(cluster.stem, nodes)
        )
        flowers.append(flower)
        
        # Set membership
        for member_label in cluster.members:
            node_id = find_node_id(member_label, nodes)
            await set_node_flower(session_id, node_id, flower.id)
    
    return flowers
```

**Exercise C.3: Test Edge Cases**

- What happens with only 2 related nodes? (Should not form Flower)
- What happens with 50+ nodes? (Should still work)
- What happens with no relationships? (Might form single-node "clusters")

### Deliverable
- [ ] LLM-based Flower formation working
- [ ] Understand semantic clustering
- [ ] Edge cases handled

---

## Phase D: Proofreading System (Week 6)

### What You'll Build
- STT error detection merged into Gardener
- Session vocabulary persistence
- Correction propagation

### Concepts to Learn

#### D.1 STT Error Patterns

Speech-to-text errors follow predictable patterns:

| Pattern | Example | Correction |
|---------|---------|------------|
| Phonetic | "see dare" | "CeADAR" |
| Acronym | "you carry" | "UKRI" |
| Technical | "graph queue L" | "GraphQL" |
| Name | "She Vaughn" | "Siobhan" |

#### D.2 Incremental Processing

Rather than scanning all text every cycle, use checkpoints:

```python
class ProofreadCheckpoint:
    session_id: str
    last_chunk_id: str  # Last processed chunk
    last_run: datetime

# Each cycle:
# 1. Get chunks after checkpoint
# 2. Proofread those chunks only
# 3. Update checkpoint
```

#### D.3 Correction Propagation

When correcting "see dare" -> "CeADAR":

```cypher
// 1. Update node labels (case-insensitive match)
MATCH (n:Node {session_id: $session_id})
WHERE toLower(n.label) = toLower($original)
SET n.label = $correction

// 2. Update relationship descriptions
MATCH ()-[r:RELATIONSHIP {session_id: $session_id}]->()
WHERE r.description CONTAINS $original
SET r.description = replace(r.description, $original, $correction)

// 3. Update transcript chunks
MATCH (c:TranscriptChunk {session_id: $session_id})
WHERE c.text CONTAINS $original
SET c.text = replace(c.text, $original, $correction)
```

### Hands-On Exercises

**Exercise D.1: Create Test Errors**

Manually insert STT errors into a test transcript:

```python
test_chunks = [
    "The see dare centre in Dublin is doing amazing work",
    "They collaborate with you carry on AI funding",
    "Using neo for jay for graph storage"
]
```

Run proofreading and verify corrections.

**Exercise D.2: Implement Vocabulary**

```python
# Schema in Neo4j
# (:SessionVocabulary {session_id, corrections: map})

async def get_vocabulary(session_id: str) -> Dict[str, str]:
    """Load learned corrections for instant lookup."""
    query = """
    MATCH (v:SessionVocabulary {session_id: $session_id})
    RETURN v.corrections as corrections
    """
    # ...

async def update_vocabulary(session_id: str, original: str, correction: str):
    """Add new correction to vocabulary."""
    query = """
    MERGE (v:SessionVocabulary {session_id: $session_id})
    SET v.corrections[$original] = $correction
    """
    # ...
```

**Exercise D.3: Pre-Proofread Pass**

Before sending to LLM, apply known vocabulary corrections:

```python
def apply_vocabulary(text: str, vocabulary: Dict[str, str]) -> str:
    """Apply instant corrections from vocabulary."""
    for original, correction in vocabulary.items():
        text = re.sub(re.escape(original), correction, text, flags=re.IGNORECASE)
    return text
```

#### D.4 Language Variant Normalization

Sessions have a `language_variant` field (default: "en-GB"). The Gardener enforces consistency:

```python
# Session-level setting
class Session:
    language_variant: str = "en-GB"  # or "en-US"

# Gardener prompt includes language instructions
LANGUAGE_INSTRUCTIONS = {
    "en-GB": "Use British English (organisation, analyse, colour)",
    "en-US": "Use American English (organization, analyze, color)",
}

# SessionVocabulary includes preferred spellings
preferred_spellings = {
    "color": "colour",      # en-GB normalizes US -> UK
    "organization": "organisation",
}
```

#### D.5 Temporal Decay

Nodes older than 5 minutes get marked as LEGACY status for visual de-emphasis:

```python
async def apply_temporal_decay(session_id: str, threshold_minutes: int = 5):
    """Mark old nodes as LEGACY."""
    query = """
    MATCH (n:Node {session_id: $session_id})
    WHERE n.status = 'SOLID'
      AND n.last_active < datetime() - duration({minutes: $threshold})
    SET n.status = 'LEGACY'
    RETURN count(n) as decayed_count
    """
    # Run at end of each Gardener cycle
```

### Deliverable
- [ ] Proofreading integrated into Gardener
- [ ] SessionVocabulary CRUD working
- [ ] Corrections propagate to nodes and chunks
- [ ] `node_corrected` SSE event broadcasting
- [ ] Language variant normalization working
- [ ] Temporal decay marking old nodes as LEGACY

---

## Phase D.5: Redis Streams - Event Bus (Week 6.5) **CRITICAL**

### What You'll Build
- Redis Streams integration for agent coordination
- Event-driven communication between Builder, Gardener, and future agents
- Foundation for Researcher and Librarian agents

### Why This Matters

The architecture specifies Redis Streams as the **asynchronous event bus** that decouples agent operations. Without this:
- Builder blocks waiting for downstream operations
- Agent failures cascade
- No backpressure handling
- Researcher/Librarian cannot be triggered reliably

### Concepts to Learn

#### D.5.1 Redis Streams vs Direct Calls

| Direct Function Calls | Redis Streams Event Bus |
|----------------------|-------------------------|
| Builder waits for Gardener | Builder publishes and continues |
| If Gardener crashes, Builder fails | Events queue reliably |
| Tight coupling | Agents are independent |
| Restart loses in-flight ops | Messages persist until ack |

#### D.5.2 Event Types

| Stream | Publisher | Consumer | Payload |
|--------|-----------|----------|---------|
| `chunks.added` | Ingestion | Builder, Gardener | chunk_id, session_id, text |
| `nodes.created` | Builder | Gardener | node_id, label, confidence |
| `nodes.needs_research` | Gardener | Researcher | node_id, entity_type, context |
| `research.requested` | API | Researcher | node_id, user_id |

### Hands-On Exercises

**Exercise D.5.1: Add Redis to Docker**

```yaml
# docker/docker-compose.yml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes
```

**Exercise D.5.2: Implement Redis Client**

```python
# backend/app/services/redis_streams.py
import redis.asyncio as redis

class RedisStreams:
    def __init__(self, url: str = "redis://localhost:6379"):
        self.client = redis.from_url(url)
    
    async def publish(self, stream: str, data: dict) -> str:
        """Publish event to stream, returns message ID."""
        return await self.client.xadd(stream, data)
    
    async def consume(self, stream: str, group: str, consumer: str):
        """Consume events from stream with consumer group."""
        while True:
            messages = await self.client.xreadgroup(
                group, consumer, {stream: ">"}, count=10, block=1000
            )
            for stream_name, entries in messages:
                for msg_id, data in entries:
                    yield msg_id, data
                    await self.client.xack(stream, group, msg_id)
```

**Exercise D.5.3: Refactor Builder to Publish**

```python
# After successful extraction
await redis_streams.publish("nodes.created", {
    "node_id": node.id,
    "label": node.label,
    "session_id": session_id,
    "confidence": str(node.confidence)
})
# Builder continues immediately - doesn't wait
```

**Exercise D.5.4: Gardener Consumes Events**

```python
async def gardener_worker():
    async for msg_id, data in redis_streams.consume(
        "nodes.created", "gardener_group", "gardener_1"
    ):
        await process_for_validation(data["node_id"])
```

### Deliverable
- [ ] Redis running in Docker
- [ ] Redis Streams client implemented
- [ ] Builder publishes events
- [ ] Gardener consumes events
- [ ] Event-driven coordination working

---

## Phase E: GraphRAG + Q&A (Week 7-8)

### What You'll Build
- Librarian agent for answering questions
- Hybrid retrieval (vector + graph)
- Citation system

### Concepts to Learn

#### E.1 What is GraphRAG?

**RAG (Retrieval Augmented Generation):** LLM answers questions using retrieved context.

**GraphRAG:** RAG enhanced with graph structure. Instead of just finding similar text, we also traverse relationships to gather richer context.

```
Traditional RAG:
Query → Vector Search → Top K chunks → LLM → Answer

GraphRAG:
Query → Vector Search → Top K nodes → Graph Expand (2 hops) → LLM → Answer
```

#### E.2 Hybrid Retrieval

Combine vector similarity with graph traversal:

```cypher
// Step 1: Vector search for starting nodes
CALL db.index.vector.queryNodes('node_embeddings', 10, $query_vector)
YIELD node as start_node, score as vector_score

// Step 2: Expand to connected nodes (2 hops)
MATCH (start_node)-[r*1..2]-(context:Node)
WHERE context.session_id = $session_id

// Step 3: Get source chunks for citations
OPTIONAL MATCH (c:TranscriptChunk)-[:MENTIONS]->(start_node)

RETURN start_node, collect(DISTINCT context) as context_nodes, 
       vector_score, collect(DISTINCT c) as sources
```

#### E.3 Context Formatting

Format retrieved information for LLM:

```python
def format_context(nodes, relationships, chunks):
    context = "## Retrieved Knowledge\n\n"
    
    context += "### Key Concepts\n"
    for node in nodes:
        context += f"- **{node.label}** ({node.inferred_type})\n"
    
    context += "\n### Relationships\n"
    for rel in relationships:
        context += f"- {rel.source_label} {rel.description} {rel.target_label}\n"
    
    context += "\n### Source Transcripts\n"
    for chunk in chunks:
        context += f"[Time: {chunk.start_time}s] {chunk.text}\n\n"
    
    return context
```

### Hands-On Exercises

**Exercise E.1: Build Basic Retrieval**

```python
async def retrieve_context(session_id: str, question: str) -> RetrievalResult:
    # 1. Embed the question
    query_embedding = await embed_text(question)
    
    # 2. Vector search for relevant nodes
    similar_nodes = await vector_search(session_id, query_embedding, top_k=10)
    
    # 3. Expand context via graph traversal
    expanded = await expand_context(session_id, similar_nodes, hops=2)
    
    # 4. Get source chunks for citations
    sources = await get_source_chunks(session_id, similar_nodes)
    
    return RetrievalResult(
        nodes=expanded.nodes,
        relationships=expanded.relationships,
        sources=sources
    )
```

**Exercise E.2: Implement Q&A Endpoint**

```python
@router.post("/api/sessions/{session_id}/ask")
async def ask_question(session_id: str, question: str):
    # 1. Retrieve context
    context = await retrieve_context(session_id, question)
    
    # 2. Format for LLM
    formatted = format_context(context)
    
    # 3. Generate answer
    answer = await llm.generate(
        LIBRARIAN_PROMPT.format(context=formatted, question=question)
    )
    
    # 4. Return with citations
    return {
        "answer": answer,
        "sources": [{"chunk_id": c.id, "time": c.start_time} for c in context.sources]
    }
```

**Exercise E.3: Test Retrieval Quality**

Create test questions and expected answers:

| Question | Expected Topics Retrieved | Expected Answer Contains |
|----------|---------------------------|-------------------------|
| "What funding was mentioned?" | Funding nodes | Grant names, amounts |
| "Who is the speaker's collaborator?" | Person nodes | Names, organisations |
| "What technology stack was discussed?" | Tech nodes | Tools, frameworks |

### Deliverable
- [ ] `/api/sessions/{id}/ask` endpoint working
- [ ] Hybrid retrieval implemented
- [ ] Citations included in responses

---

## Phase F: GDS Algorithms (Optional - Week 9-10)

**When to do this phase:** If your sessions regularly produce 100+ nodes and LLM clustering is too slow or expensive. Skip this initially - you can always come back later since transcripts are permanently stored.

### What You'll Build
- Leiden community detection for large graphs
- Betweenness centrality for keystones
- Automatic scaling based on graph size

### Concepts to Learn

#### F.1 Graph Projections

GDS operates on in-memory graph projections, not the stored graph directly:

```cypher
// Create projection
CALL gds.graph.project(
    'my_session_graph',  // Name for this projection
    'Node',              // Node labels to include
    'RELATIONSHIP'       // Relationship types
)

// Run algorithm
CALL gds.leiden.stream('my_session_graph')
YIELD nodeId, communityId

// Clean up (important!)
CALL gds.graph.drop('my_session_graph')
```

#### F.2 Leiden Algorithm

Leiden finds communities by maximising **modularity** - the density of edges inside groups vs between groups.

```cypher
// Run Leiden and write results back
CALL gds.leiden.write('session_graph', {
    writeProperty: 'community_id',
    maxLevels: 10,
    gamma: 1.0  // Resolution parameter (higher = smaller communities)
})
YIELD communityCount, modularity
```

**Parameters:**
- `gamma`: Higher values = more, smaller communities
- `maxLevels`: How deep to refine communities

#### F.3 Betweenness Centrality

Identifies "bridge" nodes that connect different parts of the graph:

```cypher
CALL gds.betweenness.write('session_graph', {
    writeProperty: 'centrality_score'
})
```

High centrality = keystone node (important for understanding flow of ideas).

### Hands-On Exercises

**Exercise F.1: Project and Analyse**

```cypher
// 1. Project a session graph
CALL gds.graph.project(
    'test_session',
    {Node: {properties: ['session_id']}},
    {RELATIONSHIP: {orientation: 'UNDIRECTED'}}
)

// 2. Run Leiden
CALL gds.leiden.stream('test_session')
YIELD nodeId, communityId
RETURN gds.util.asNode(nodeId).label as label, communityId
ORDER BY communityId

// 3. Run Betweenness
CALL gds.betweenness.stream('test_session')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).label as label, score
ORDER BY score DESC
LIMIT 5

// 4. Clean up
CALL gds.graph.drop('test_session')
```

**Exercise F.2: Compare LLM vs GDS Clustering**

For the same session:
1. Run LLM clustering (Phase C)
2. Run GDS Leiden clustering
3. Compare results:
   - How many clusters each found?
   - Which groupings make more sense?
   - Which is faster?

**Exercise F.3: Implement Hybrid Scaling**

```python
async def cluster_session(session_id: str):
    node_count = await count_nodes(session_id)
    
    if node_count < 100:
        # Small graph: LLM reasoning is better
        return await cluster_with_llm(session_id)
    else:
        # Large graph: GDS for structure, LLM for labels
        communities = await run_leiden(session_id)
        labeled = await label_communities_with_llm(communities)
        return labeled
```

### Deliverable
- [ ] GDS projection/algorithm workflow understood
- [ ] Leiden + Betweenness implemented
- [ ] Automatic scaling based on graph size

---

## Phase G: Research Agent (Week 11)

### What You'll Build
- External enrichment via web search
- ReferenceNode creation and linking
- Fallback strategies

### Concepts to Learn

#### G.1 Gemini Grounding

Gemini can search the web and cite sources:

```python
from google import genai

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=f"What is {entity_name}? Provide a brief definition and official website.",
    config={
        "tools": [{"google_search": {}}],
    }
)

# Response includes grounding metadata with sources
```

#### G.2 Fallback Strategy

```python
async def research_entity(entity: str) -> ReferenceNode:
    try:
        # Try Gemini grounding first
        result = await gemini_grounded_search(entity)
        if result.confidence > 0.7:
            return result
    except QuotaExceeded:
        pass
    
    # Fallback to Tavily
    try:
        return await tavily_search(entity)
    except Exception:
        pass
    
    # Last resort: return low-confidence result
    return ReferenceNode(
        title=entity,
        summary="Could not find external information",
        confidence=0.0
    )
```

#### G.3 ReferenceNode Schema

```cypher
// Create reference
CREATE (ref:ReferenceNode {
    id: $id,
    type: "organisation",  // or "funding", "definition", "paper"
    title: "CeADAR - Ireland's National Centre for AI",
    url: "https://ceadar.ie",
    summary: "CeADAR is Ireland's National Centre for Applied AI...",
    source: "google",
    fetched_at: datetime()
})

// Link to concept node
MATCH (n:Node {id: $node_id})
CREATE (n)-[:HAS_REFERENCE]->(ref)
```

### Hands-On Exercises

**Exercise G.1: Test Gemini Grounding**

```python
async def test_grounding():
    test_entities = [
        "CeADAR Ireland",        # Local org
        "Creative Scotland",     # Funding body
        "GraphRAG",              # Technical term
        "UKRI",                  # Acronym
    ]
    
    for entity in test_entities:
        result = await gemini_grounded_search(entity)
        print(f"{entity}: {result.title} ({result.confidence})")
        print(f"  URL: {result.url}")
        print(f"  Summary: {result.summary[:100]}...")
```

**Exercise G.2: Implement Trigger Logic**

When should Researcher activate?

```python
def should_research(node: Node, transcript_context: str) -> bool:
    # Low confidence extraction
    if node.confidence < 0.7:
        return True
    
    # Entity types that benefit from research
    if node.inferred_type in ["organisation", "funding", "person"]:
        return True
    
    # Explicit patterns in transcript
    research_patterns = ["what is", "who is", "I don't know", "unfamiliar"]
    if any(p in transcript_context.lower() for p in research_patterns):
        return True
    
    return False
```

**Exercise G.3: Add SSE Event**

When reference is added, notify the UI:

```python
async def add_reference(session_id: str, node_id: str, reference: ReferenceNode):
    # Save to Neo4j
    await create_reference_node(session_id, node_id, reference)
    
    # Notify UI
    await sse_manager.broadcast(session_id, "reference_added", {
        "node_id": node_id,
        "reference": reference.model_dump()
    })
```

### Deliverable
- [ ] Gemini grounding integration working
- [ ] ReferenceNode creation and linking
- [ ] UI shows reference indicator on enriched nodes

---

## Quick Reference: Neo4j Cypher Cheatsheet

### Basic Patterns

```cypher
// All nodes
MATCH (n) RETURN n

// Nodes with label
MATCH (n:Node) RETURN n

// Nodes with property
MATCH (n:Node {status: "SOLID"}) RETURN n

// WHERE clause
MATCH (n:Node)
WHERE n.confidence > 0.8
RETURN n
```

### Relationships

```cypher
// Outgoing relationship
MATCH (a)-[r]->(b) RETURN a, r, b

// Specific type
MATCH (a)-[:BELONGS_TO]->(b) RETURN a, b

// Variable length (1-3 hops)
MATCH (a)-[*1..3]->(b) RETURN a, b

// Undirected
MATCH (a)-[r]-(b) RETURN a, r, b
```

### Aggregation

```cypher
// Count
MATCH (n:Node) RETURN count(n)

// Group by
MATCH (n:Node) RETURN n.status, count(n)

// Collect into list
MATCH (n:Node)-[:BELONGS_TO]->(f:Flower)
RETURN f.label, collect(n.label) as members
```

### Updates

```cypher
// Set property
MATCH (n:Node {id: $id})
SET n.label = $new_label

// Set multiple
SET n.label = $label, n.updated_at = datetime()

// Increment
SET n.mentions = coalesce(n.mentions, 0) + 1

// Remove property
REMOVE n.temporary_flag
```

### Vector Search

```cypher
// Query similar nodes
CALL db.index.vector.queryNodes('index_name', $top_k, $vector)
YIELD node, score
RETURN node, score
```

### GDS

```cypher
// Check GDS version
RETURN gds.version()

// List projections
CALL gds.graph.list()

// Project graph
CALL gds.graph.project('name', 'Label', 'TYPE')

// Drop projection
CALL gds.graph.drop('name')
```

---

## Resources

### Official Documentation
- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/current/)
- [Neo4j GDS Documentation](https://neo4j.com/docs/graph-data-science/current/)
- [Neo4j Vector Index Guide](https://neo4j.com/docs/cypher-manual/current/indexes-for-vector-search/)

### Learning Platforms
- [Neo4j GraphAcademy](https://graphacademy.neo4j.com/) - Free courses
- [Cypher Fundamentals](https://graphacademy.neo4j.com/courses/cypher-fundamentals/)
- [GDS Fundamentals](https://graphacademy.neo4j.com/courses/gds-product-introduction/)

### Project Documentation
- [ARCHITECTURE_ADVISORY.md](./ARCHITECTURE_ADVISORY.md) - Full system design
- [neo4j_docs.md](./_dev/_libraries_docs/databases_graph/neo4j_docs.md) - Neo4j reference
- [neo4j_gds_docs.md](./_dev/_libraries_docs/nlp_graph_libs/neo4j_gds_docs.md) - GDS reference
- [neo4j_graphrag_docs.md](./_dev/_libraries_docs/nlp_graph_libs/neo4j_graphrag_docs.md) - GraphRAG reference

---

## Progress Tracker

Use this to track your learning journey:

| Phase | Started | Completed | Notes |
|-------|---------|-----------|-------|
| A: Neo4j Fundamentals | [ ] | [ ] | |
| B: Vector Embeddings | [ ] | [ ] | |
| C: LLM Clustering | [ ] | [ ] | |
| D: Proofreading System | [ ] | [ ] | |
| E: GraphRAG + Q&A | [ ] | [ ] | |
| F: GDS Algorithms (Optional) | [ ] | [ ] | Add if 100+ nodes common |
| G: Research Agent | [ ] | [ ] | |

**Remember:** Each phase builds working features. Take breaks between phases - the system will work with whatever you've completed.

**Re-processing:** All `TranscriptChunk` data is permanently stored. You can re-run Builder/Gardener on historical sessions anytime to apply new algorithms or corrections retroactively.


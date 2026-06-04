# Cypher Quick Reference

**Purpose:** Common Cypher patterns for plasticFlower development.  
**Usage:** Quick lookup when writing Neo4j queries.

---

## Basic Operations

### Create Node

```cypher
CREATE (n:Node {id: $id, label: $label, session_id: $session_id})
RETURN n
```

### Read Node

```cypher
MATCH (n:Node {id: $id, session_id: $session_id})
RETURN n
```

### Update Node

```cypher
MATCH (n:Node {id: $id})
SET n.label = $label, n.updated_at = datetime()
RETURN n
```

### Delete Node

```cypher
MATCH (n:Node {id: $id})
DETACH DELETE n
```

---

## MERGE vs CREATE

### CREATE - Always creates new

```cypher
-- Creates duplicate if called twice with same id!
CREATE (n:Node {id: "node1"})
```

### MERGE - Creates if not exists

```cypher
-- Safe to call multiple times
MERGE (n:Node {id: "node1"})
ON CREATE SET n.created_at = datetime()
ON MATCH SET n.updated_at = datetime()
RETURN n
```

**Rule:** Use MERGE for upserts, CREATE only when ID is guaranteed unique.

---

## Relationships

### Create Relationship

```cypher
MATCH (a:Node {id: $source_id})
MATCH (b:Node {id: $target_id})
CREATE (a)-[r:RELATES_TO {description: $desc}]->(b)
RETURN r
```

### Create with MERGE (safer)

```cypher
MERGE (a:Node {id: $source_id})
MERGE (b:Node {id: $target_id})
MERGE (a)-[r:RELATES_TO]->(b)
SET r.description = $desc
RETURN r
```

### Delete Relationship

```cypher
MATCH (a)-[r:RELATES_TO]->(b)
WHERE r.id = $rel_id
DELETE r
```

---

## Filtering

### WHERE clause

```cypher
MATCH (n:Node {session_id: $session_id})
WHERE n.status = 'solid' AND n.confidence > 0.8
RETURN n
```

### Multiple labels

```cypher
MATCH (n:Node:ImportantNode {session_id: $session_id})
RETURN n
```

### Pattern matching

```cypher
MATCH (a:Node)-[:RELATES_TO]->(b:Node)
WHERE a.session_id = $session_id
RETURN a, b
```

---

## Aggregation

### Count

```cypher
MATCH (n:Node {session_id: $session_id})
RETURN count(n) AS node_count
```

### Group by

```cypher
MATCH (n:Node {session_id: $session_id})
RETURN n.status, count(n) AS count
ORDER BY count DESC
```

### Collect into list

```cypher
MATCH (f:Flower {id: $flower_id})<-[:BELONGS_TO]-(n:Node)
RETURN f.label, collect(n.label) AS members
```

---

## Graph Traversal

### Variable length path

```cypher
-- 1 to 3 hops
MATCH (start:Node {id: $id})-[*1..3]-(connected:Node)
RETURN connected
```

### Shortest path

```cypher
MATCH p = shortestPath(
  (a:Node {id: $from})-[*]-(b:Node {id: $to})
)
RETURN p
```

### All paths

```cypher
MATCH p = (a:Node {id: $from})-[*..5]-(b:Node {id: $to})
RETURN p
LIMIT 10
```

---

## Vector Index (Neo4j 5.x)

### Create vector index

```cypher
CREATE VECTOR INDEX node_embeddings IF NOT EXISTS
FOR (n:Node) ON n.embedding
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 768,
    `vector.similarity_function`: 'cosine'
  }
}
```

### Query by similarity

```cypher
CALL db.index.vector.queryNodes('node_embeddings', 10, $query_embedding)
YIELD node, score
WHERE node.session_id = $session_id
RETURN node, score
ORDER BY score DESC
```

---

## Transcript Retrieval

### Get recent transcript with LIMIT (optimised)

```cypher
-- Fetch most recent chunks up to a limit for word processing
-- Conservative estimate: 20 words/chunk (actual avg ~60)
-- For 3000 words: LIMIT 160 (3000/20 + 10 safety margin)
MATCH (c:TranscriptChunk {session_id: $session_id})
RETURN c.text AS text, c.start_time AS start_time
ORDER BY c.start_time DESC
LIMIT $chunk_limit
```

**Why LIMIT matters:** Without LIMIT, Neo4j plans to return all chunks even if Python stops early. With hundreds of chunks, this wastes query planning time.

### Get all chunks for session (chronological)

```cypher
MATCH (c:TranscriptChunk {session_id: $session_id})
RETURN c.text AS text, c.start_time AS start_time, c.end_time AS end_time
ORDER BY c.start_time ASC
```

### Chunk statistics

```cypher
MATCH (c:TranscriptChunk {session_id: $session_id})
WITH c, size(split(c.text, ' ')) AS word_count
RETURN count(c) AS chunks, sum(word_count) AS total_words,
       avg(word_count) AS avg_words, max(word_count) AS max_words
```

---

## Session Patterns

### Get session with counts

```cypher
MATCH (s:Session {id: $session_id})
OPTIONAL MATCH (n:Node {session_id: $session_id})
OPTIONAL MATCH ()-[r:RELATIONSHIP {session_id: $session_id}]->()
OPTIONAL MATCH (f:Flower {session_id: $session_id})
RETURN s, count(DISTINCT n) AS nodes, count(DISTINCT r) AS rels, count(DISTINCT f) AS flowers
```

### Cascade delete session

```cypher
-- Must be in order: relationships, nodes, flowers, chunks, session
MATCH ()-[r:RELATIONSHIP {session_id: $session_id}]->()
DELETE r;

MATCH (n:Node {session_id: $session_id})
DETACH DELETE n;

MATCH (f:Flower {session_id: $session_id})
DELETE f;

MATCH (c:TranscriptChunk {session_id: $session_id})
DELETE c;

MATCH (s:Session {id: $session_id})
DELETE s;
```

---

## Useful Functions

| Function | Purpose | Example |
|----------|---------|---------|
| `datetime()` | Current timestamp | `SET n.created_at = datetime()` |
| `coalesce(a, b)` | Null fallback | `coalesce(n.mentions, 0) + 1` |
| `size(list)` | List length | `WHERE size(n.timestamps) > 2` |
| `collect(x)` | Aggregate to list | `collect(n.label)` |
| `head(list)` | First element | `head(n.timestamps)` |
| `last(list)` | Last element | `last(n.timestamps)` |
| `toString(x)` | Convert to string | `toString(n.confidence)` |

---

## Constraints and Indexes

### Unique constraint

```cypher
CREATE CONSTRAINT node_id_unique IF NOT EXISTS
FOR (n:Node) REQUIRE n.id IS UNIQUE
```

### Index for faster lookups

```cypher
CREATE INDEX node_session_idx IF NOT EXISTS
FOR (n:Node) ON (n.session_id)
```

### Show all indexes

```cypher
SHOW INDEXES
```

### Drop index

```cypher
DROP INDEX node_session_idx IF EXISTS
```

---

## Debugging

### Show all data

```cypher
MATCH (n) RETURN n LIMIT 100
```

### Count all nodes by label

```cypher
CALL db.labels() YIELD label
MATCH (n) WHERE label IN labels(n)
RETURN label, count(n) AS count
ORDER BY count DESC
```

### Check for orphaned nodes

```cypher
MATCH (n:Node)
WHERE NOT (n)-[]-()
RETURN n
```

### Find duplicate labels

```cypher
MATCH (n:Node {session_id: $session_id})
WITH n.label AS label, collect(n.id) AS ids
WHERE size(ids) > 1
RETURN label, ids
```


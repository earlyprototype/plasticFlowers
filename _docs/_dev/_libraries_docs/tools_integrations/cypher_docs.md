# Cypher Query Language Documentation

## Overview
Cypher is Neo4j's declarative graph query language. Inspired by SQL but designed specifically for graphs, Cypher uses ASCII-art syntax to represent patterns, making queries intuitive and readable. It's the primary way to create, read, update, and delete data in Neo4j.

## Core Concepts

### Nodes

Nodes represent entities (nouns):

```cypher
// Node with label
(p:Person)

// Node with multiple labels
(u:User:Admin)

// Node with properties
(p:Person {name: "Alice", age: 30})

// Node with variable
(alice:Person {name: "Alice"})
```

### Relationships

Relationships connect nodes (verbs):

```cypher
// Directed relationship
(a)-[:KNOWS]->(b)

// Undirected (for matching only)
(a)-[:KNOWS]-(b)

// Relationship with properties
(a)-[:KNOWS {since: 2020}]->(b)

// Relationship with variable
(a)-[r:KNOWS]->(b)
```

### Patterns

Combine nodes and relationships:

```cypher
// Simple pattern
(alice:Person)-[:KNOWS]->(bob:Person)

// Chain
(a)-[:KNOWS]->(b)-[:KNOWS]->(c)

// Variable length
(a)-[:KNOWS*1..3]->(b)  // 1 to 3 hops

// Multiple patterns
(a)-[:KNOWS]->(b), (b)-[:LIKES]->(c)
```

## Basic Operations (CRUD)

### CREATE - Add Data

**Create Nodes:**
```cypher
// Single node
CREATE (p:Person {name: "Alice", age: 30})

// Multiple nodes
CREATE 
  (a:Person {name: "Alice"}),
  (b:Person {name: "Bob"}),
  (c:Company {name: "TechCorp"})
```

**Create Relationships:**
```cypher
// With existing nodes
MATCH (a:Person {name: "Alice"}), (b:Person {name: "Bob"})
CREATE (a)-[:KNOWS {since: 2020}]->(b)

// Create nodes and relationships together
CREATE (a:Person {name: "Alice"})-[:WORKS_AT]->(c:Company {name: "TechCorp"})
```

### MATCH - Read Data

**Basic Matching:**
```cypher
// All persons
MATCH (p:Person)
RETURN p

// Specific person
MATCH (p:Person {name: "Alice"})
RETURN p

// With relationships
MATCH (a:Person)-[:KNOWS]->(b:Person)
RETURN a.name, b.name
```

**WHERE Clause:**
```cypher
MATCH (p:Person)
WHERE p.age > 25 AND p.name STARTS WITH "A"
RETURN p.name, p.age
```

### MERGE - Create or Match

Ensures uniqueness:

```cypher
// Create if doesn't exist, match if does
MERGE (p:Person {name: "Alice"})
RETURN p

// With ON CREATE / ON MATCH
MERGE (p:Person {name: "Alice"})
  ON CREATE SET p.created = timestamp(), p.visits = 1
  ON MATCH SET p.visits = p.visits + 1
RETURN p
```

### SET - Update Properties

```cypher
// Set property
MATCH (p:Person {name: "Alice"})
SET p.age = 31
RETURN p

// Set multiple properties
MATCH (p:Person {name: "Alice"})
SET p.age = 31, p.city = "London"

// Add label
MATCH (p:Person {name: "Alice"})
SET p:Admin

// Copy properties from map
MATCH (p:Person {name: "Alice"})
SET p += {email: "alice@example.com", phone: "123-456"}
```

### DELETE & REMOVE

**DELETE Nodes/Relationships:**
```cypher
// Delete node (must delete relationships first)
MATCH (p:Person {name: "Alice"})
DELETE p

// Delete node and relationships
MATCH (p:Person {name: "Alice"})
DETACH DELETE p

// Delete relationship only
MATCH (a:Person)-[r:KNOWS]->(b:Person)
WHERE a.name = "Alice"
DELETE r
```

**REMOVE Properties/Labels:**
```cypher
// Remove property
MATCH (p:Person {name: "Alice"})
REMOVE p.age

// Remove label
MATCH (p:Person {name: "Alice"})
REMOVE p:Admin
```

## Advanced Querying

### Variable-Length Paths

```cypher
// Friends of friends (1-2 hops)
MATCH (a:Person {name: "Alice"})-[:KNOWS*1..2]->(friend)
RETURN DISTINCT friend.name

// All paths up to 3 hops
MATCH path = (a:Person {name: "Alice"})-[:KNOWS*..3]->(b)
RETURN path

// Shortest path
MATCH path = shortestPath(
  (a:Person {name: "Alice"})-[:KNOWS*]-(b:Person {name: "Zara"})
)
RETURN path
```

### Aggregations

```cypher
// Count
MATCH (p:Person)
RETURN count(p) AS personCount

// Group by and count
MATCH (p:Person)
RETURN p.city, count(*) AS population
ORDER BY population DESC

// Average, sum, min, max
MATCH (p:Person)
RETURN 
  avg(p.age) AS avgAge,
  sum(p.salary) AS totalSalary,
  min(p.age) AS youngest,
  max(p.age) AS oldest

// Collect into list
MATCH (p:Person)-[:WORKS_AT]->(c:Company)
RETURN c.name, collect(p.name) AS employees
```

### ORDER BY & LIMIT

```cypher
// Order by property
MATCH (p:Person)
RETURN p.name, p.age
ORDER BY p.age DESC

// Multiple sort keys
MATCH (p:Person)
RETURN p
ORDER BY p.city ASC, p.age DESC

// Limit results
MATCH (p:Person)
RETURN p
ORDER BY p.age DESC
LIMIT 10

// Skip and limit (pagination)
MATCH (p:Person)
RETURN p
ORDER BY p.name
SKIP 20 LIMIT 10
```

### OPTIONAL MATCH

Like SQL LEFT JOIN:

```cypher
// Find persons and their companies (if any)
MATCH (p:Person)
OPTIONAL MATCH (p)-[:WORKS_AT]->(c:Company)
RETURN p.name, c.name
```

### WITH (Chaining Queries)

```cypher
// Pipeline queries
MATCH (p:Person)
WITH p
ORDER BY p.age DESC
LIMIT 5
MATCH (p)-[:KNOWS]->(friend)
RETURN p.name, collect(friend.name) AS friends
```

### UNION

```cypher
// Combine results
MATCH (p:Person) RETURN p.name AS name
UNION
MATCH (c:Company) RETURN c.name AS name

// UNION ALL (includes duplicates)
MATCH (p:Person) RETURN p.name
UNION ALL
MATCH (c:Company) RETURN c.name
```

## Pattern Matching

### Complex Patterns

```cypher
// Friends who work at same company
MATCH (a:Person)-[:KNOWS]->(b:Person),
      (a)-[:WORKS_AT]->(c:Company)<-[:WORKS_AT]-(b)
RETURN a.name, b.name, c.name

// Triangle pattern (mutual friends)
MATCH (a:Person)-[:KNOWS]->(b:Person)-[:KNOWS]->(c:Person)-[:KNOWS]->(a)
RETURN a, b, c
```

### Negation (NOT)

```cypher
// Persons who DON'T know Alice
MATCH (p:Person)
WHERE NOT (p)-[:KNOWS]->(:Person {name: "Alice"})
RETURN p.name

// Using WHERE NOT EXISTS
MATCH (p:Person)
WHERE NOT EXISTS((p)-[:WORKS_AT]->())
RETURN p.name AS unemployed
```

### Quantified Path Patterns (Neo4j 5+)

```cypher
// All persons where ALL friends are developers
MATCH (p:Person)
WHERE ALL(friend IN [(p)-[:KNOWS]->(f) | f] WHERE 'Developer' IN labels(friend))
RETURN p.name

// At least one friend is a manager
MATCH (p:Person)
WHERE ANY(friend IN [(p)-[:KNOWS]->(f) | f] WHERE 'Manager' IN labels(friend))
RETURN p.name
```

## Functions

### String Functions

```cypher
MATCH (p:Person)
WHERE p.name STARTS WITH "A"  // OR: ENDS WITH, CONTAINS
RETURN p.name

// Case conversion
RETURN toLower("HELLO"), toUpper("hello")

// Substring
RETURN substring("Hello World", 0, 5)  // "Hello"

// Replace
RETURN replace("Hello World", "World", "Neo4j")

// Split
RETURN split("a,b,c", ",")  // ["a", "b", "c"]
```

### List Functions

```cypher
// Range
RETURN range(1, 10)  // [1, 2, ..., 10]

// Size
RETURN size([1, 2, 3, 4])  // 4

// Head, tail, last
RETURN head([1, 2, 3])  // 1
RETURN tail([1, 2, 3])  // [2, 3]
RETURN last([1, 2, 3])  // 3

// List comprehension
MATCH (p:Person)
RETURN [person IN collect(p) WHERE person.age > 30 | person.name]
```

### Math Functions

```cypher
RETURN 
  round(3.14159, 2),     // 3.14
  floor(3.9),            // 3
  ceil(3.1),             // 4
  abs(-5),               // 5
  sqrt(16),              // 4
  rand()                 // Random float 0-1
```

### Date/Time Functions

```cypher
// Current timestamp
RETURN timestamp()  // Milliseconds since epoch

// Date/time objects (Neo4j 3.4+)
RETURN date(), datetime(), time()

// Format
RETURN datetime({year: 2025, month: 12, day: 21})

// Parse
RETURN date("2025-12-21")

// Arithmetic
RETURN date() + duration({days: 7})
```

### Relationship Functions

```cypher
MATCH (a)-[r]->(b)
RETURN 
  type(r),              // Relationship type
  startNode(r),         // Start node
  endNode(r),           // End node
  id(r),                // Relationship ID
  properties(r)         // All properties
```

## Indexes & Constraints

### Create Indexes

```cypher
// Single property index
CREATE INDEX person_name_index FOR (p:Person) ON (p.name)

// Composite index
CREATE INDEX person_composite FOR (p:Person) ON (p.name, p.age)

// Full-text index
CREATE FULLTEXT INDEX person_fulltext FOR (p:Person) ON EACH [p.name, p.bio]
```

### Create Constraints

```cypher
// Unique constraint
CREATE CONSTRAINT person_email_unique FOR (p:Person) REQUIRE p.email IS UNIQUE

// Node property existence (Enterprise only)
CREATE CONSTRAINT person_name_exists FOR (p:Person) REQUIRE p.name IS NOT NULL

// Relationship property existence
CREATE CONSTRAINT knows_since_exists FOR ()-[k:KNOWS]-() REQUIRE k.since IS NOT NULL
```

### List Indexes/Constraints

```cypher
SHOW INDEXES
SHOW CONSTRAINTS
```

## Performance Optimization

### EXPLAIN & PROFILE

```cypher
// Show query plan (doesn't execute)
EXPLAIN
MATCH (p:Person {name: "Alice"})-[:KNOWS]->(friend)
RETURN friend.name

// Execute and show metrics
PROFILE
MATCH (p:Person {name: "Alice"})-[:KNOWS]->(friend)
RETURN friend.name
```

### Hints

```cypher
// Use specific index
MATCH (p:Person)
USING INDEX p:Person(name)
WHERE p.name = "Alice"
RETURN p

// Scan hint
MATCH (p:Person)
USING SCAN p:Person
WHERE p.age > 30
RETURN p

// Join hint
MATCH (a:Person), (b:Person)
USING JOIN ON a
WHERE a.name = b.manager
RETURN a, b
```

### Best Practices

1. **Use Labels**: Always specify labels to narrow search
2. **Index Lookups**: Create indexes on frequently queried properties
3. **Avoid Large Cartesian Products**: Be specific with patterns
4. **Limit Early**: Apply WHERE and LIMIT early in query
5. **Use PROFILE**: Identify bottlenecks with db hits
6. **Parameterized Queries**: Use parameters for security and caching

```cypher
// Bad: Cartesian product
MATCH (a:Person), (b:Person)
WHERE a.name = "Alice" AND b.name = "Bob"

// Good: Specific pattern
MATCH (a:Person {name: "Alice"}), (b:Person {name: "Bob"})
```

## Procedures (APOC & GDS)

### CALL Procedures

```cypher
// APOC: Generate UUIDs
CALL apoc.create.uuid() YIELD uuid
RETURN uuid

// GDS: PageRank
CALL gds.pageRank.stream('myGraph')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name AS name, score
ORDER BY score DESC
LIMIT 10
```

## Subqueries (Neo4j 4+)

```cypher
// CALL subquery
MATCH (p:Person)
CALL {
  WITH p
  MATCH (p)-[:KNOWS]->(friend)
  RETURN count(friend) AS friendCount
}
RETURN p.name, friendCount
ORDER BY friendCount DESC
```

## Resources

- **Cypher Manual**: https://neo4j.com/docs/cypher-manual/current/
- **Cypher Refcard**: https://neo4j.com/docs/cypher-refcard/current/
- **GraphAcademy**: https://graphacademy.neo4j.com/
- **Neo4j Browser**: Interactive query environment
- **APOC Docs**: https://neo4j.com/labs/apoc/






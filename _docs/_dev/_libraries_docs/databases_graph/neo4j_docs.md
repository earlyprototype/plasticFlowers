# Neo4j Documentation

## Overview
Neo4j is a leading open-source graph database that stores and manages data in a graph structure, consisting of nodes, relationships, and properties. It provides powerful capabilities for vector indexing, Cypher query language, and Graph Data Science.

## Vector Indexing

### Create Vector Index on Nodes

Creates a vector index for node properties to enable efficient similarity searches based on vector embeddings.

```cypher
CREATE VECTOR INDEX moviePlots IF NOT EXISTS 
FOR (m:Movie)
ON m.embedding
OPTIONS { indexConfig: { 
 `vector.dimensions`: 1536,
 `vector.similarity_function`: 'cosine'
}}
```

### Create Vector Index on Relationships

Creates a vector index for relationship properties:

```cypher
CREATE VECTOR INDEX `review-embeddings`
FOR ()-[r:REVIEWED]-() ON (r.embedding)
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 256,
    `vector.similarity_function`: 'cosine'
  }
}
```

### Query Vector Index

Find nearest neighbors using vector similarity:

```cypher
MATCH (m:Movie {title: 'Godfather, The'})
CALL db.index.vector.queryNodes('moviePlots', 5, m.embedding)
YIELD node AS movie, score
RETURN movie.title AS title, movie.plot AS plot, score
```

### Manage Vector Indexes

```cypher
-- Show all vector indexes
SHOW VECTOR INDEXES

-- Drop an index
DROP INDEX `abstract-embeddings`
```

## Cypher Query Language

### Basic Graph Creation

```cypher
CREATE (:Person:Actor {name: 'Tom Hanks', born: 1956})
  -[:ACTED_IN {roles: ['Forrest']}]->
  (:Movie {title: 'Forrest Gump', released: 1994})
  <-[:DIRECTED]-
  (:Person {name: 'Robert Zemeckis', born: 1951})
```

### Pattern Matching

```cypher
MATCH (tom:Person {name: 'Tom Hanks'})-[r:ACTED_IN]->(movie:Movie)
RETURN tom, r, movie
```

### Data Types

```cypher
-- String and boolean properties
CREATE (:Example {c: 'This is an example string', d: true, e: false})

-- Numeric properties
CREATE (:Example {a: 1, b: 3.14})

-- List properties
CREATE (:Example {f: [1, 2, 3], g: [2.71, 3.14], h: ['abc', 'example']})
```

## Graph Data Science

### Python Client Setup

```python
import os
from graphdatascience import GraphDataScience

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_AUTH = None
if os.environ.get("NEO4J_USER") and os.environ.get("NEO4J_PASSWORD"):
    NEO4J_AUTH = (
        os.environ.get("NEO4J_USER"),
        os.environ.get("NEO4J_PASSWORD"),
    )

gds = GraphDataScience(NEO4J_URI, auth=NEO4J_AUTH)
```

### Project Graph

```python
G, result = gds.graph.project("airline", "City", "HAS_FLIGHT_TO")

print(f"The projection took {result['projectMillis']} ms")
print(f"Graph '{G.name()}' node count: {G.node_count()}")
print(f"Graph '{G.name()}' relationship count: {G.relationship_count()}")
```

### Centrality Algorithms

#### Eigenvector Centrality

```python
eigenvector_centrality_result = gds.eigenvector.mutate(
    G, 
    maxIterations=100, 
    mutateProperty="eigenvectorCentrality"
)

# Write to database
gds.graph.nodeProperties.write(G, ["eigenvectorCentrality"])
```

#### Degree Centrality

```python
degree_centrality_result = gds.degree.mutate(G, mutateProperty="degreeCentrality")
gds.graph.nodeProperties.write(G, ["degreeCentrality"])
```

#### Betweenness Centrality

```python
betweenness_centrality_result = gds.betweenness.mutate(
    G, 
    mutateProperty="betweennessCentrality"
)
gds.graph.nodeProperties.write(G, ["betweennessCentrality"])
```

### Query Results

```python
def display_top_20_cities(centrality_measure):
    query = f"""
    MATCH (n:City)
    RETURN n.node_id AS node_id, n.name AS name, 
           n.population AS population, 
           n.{centrality_measure} AS {centrality_measure}
    ORDER BY n.{centrality_measure} DESC
    LIMIT 20
    """
    result = gds.run_cypher(query)
    print(result)
```

## Data Import

### Load CSV Data

```cypher
LOAD CSV WITH HEADERS FROM 'https://example.com/data.csv' AS row
MERGE (c:Category {categoryID: row.CategoryID})
  ON CREATE SET c.categoryName = row.CategoryName, 
                c.description = row.Description
```

### Python DataFrame Import

```python
# Create nodes from DataFrame
gds.run_cypher(
    "UNWIND $nodes AS node CREATE (n:City {node_id: node.node_id, name: node.name})",
    params={"nodes": nodes_df.to_dict("records")},
)

# Create relationships
gds.run_cypher(
    """
    UNWIND $rels AS rel
    MATCH (source:City {node_id: rel.Origin}), 
          (target:City {node_id: rel.Destination})
    CREATE (source)-[:HAS_FLIGHT_TO]->(target)
    """,
    params={"rels": routes_df.to_dict("records")},
)
```

## Driver Usage

### JavaScript

```javascript
let { records, summary } = await driver.executeQuery(`
  MATCH (p:Person)-[:KNOWS]->(:Person)
  RETURN p.name AS name
  `,
  {},
  { database: '<database-name>' })

for(let record of records) {
  console.log(`Person with name: ${record.get('name')}`)
}
```

### Java

```java
var result = driver.executableQuery("""
    MATCH (p:Person)-[:KNOWS]->(:Person)
    RETURN p.name AS name
    """)
    .withConfig(QueryConfig.builder().withDatabase("<database-name>").build())
    .execute();

var records = result.records();
records.forEach(r -> {
    System.out.println(r.get("name").asString());
});
```

### Python

```python
result = driver.execute_query("""
    MATCH (p:Person)-[:KNOWS]->(:Person)
    RETURN p.name AS name
    """,
    database_="<database-name>"
)

for record in result.records:
    print(record["name"])
```

## Full-Text Indexes

### Create Full-Text Index

```cypher
CREATE FULLTEXT INDEX node_fulltext_index
FOR (n:Friend) ON EACH [n.name]
OPTIONS {
  indexConfig: {
    `fulltext.analyzer`: 'swedish'
  }
}
```

### Query Full-Text Index

```cypher
CALL db.index.fulltext.queryNodes("node_fulltext_index", "Alice") 
YIELD node, score
```

## Neo4j Aura

Neo4j Aura is a fully managed cloud database service providing:
- Secure and scalable graph data storage
- Automated backups and updates
- Global availability
- Vector index support for similarity search

## GraphQL Integration

### Define Vector-Enabled Types

```graphql
type Product @vector(indexes: [{
  indexName: "productDescriptionIndex",
  embeddingProperty: "descriptionVector",
  queryName: "searchByDescription"
}]) {
  id: ID!
  name: String!
  description: String!
}
```

### Query for Similar Items

```graphql
query FindSimilarProducts($vector: [Float]!) {
  searchByDescription(vector: $vector) {
    edges {
      cursor
      score
      node {
          id
          name
          description
      }
    }
  }
}
```

## Performance Optimization

### Enable Java Vector API

For improved vector index performance, add to your Neo4j configuration:

```ini
server.jvm.additional=--add-modules=jdk.incubator.vector
```

### Index Management

```cypher
-- Show all indexes
SHOW INDEXES

-- Filter for vector indexes
SHOW INDEXES
WHERE type = 'VECTOR'

-- Show create statements
SHOW INDEXES YIELD type, createStatement
WHERE type = 'VECTOR'
RETURN createStatement
```

## Resources

- **Official Documentation**: https://neo4j.com/docs/
- **Graph Data Science**: https://neo4j.com/docs/graph-data-science/
- **Cypher Manual**: https://neo4j.com/docs/cypher-manual/
- **Aura Documentation**: https://neo4j.com/docs/aura/
- **GraphQL Integration**: https://neo4j.com/docs/graphql/

## Key Features for PlasticFlower

1. **Vector Indexing**: Essential for semantic search and similarity matching
2. **Graph Algorithms**: PageRank, Louvain community detection, centrality measures
3. **Cypher Query Language**: Powerful pattern matching for complex relationships
4. **Python GDS Client**: Seamless integration with your Python backend
5. **Scalability**: Aura cloud service for production deployment






# Neo4j Documentation

## Overview
Neo4j is a graph database management system that stores data in nodes and relationships, rather than tables and rows. It is designed for highly interconnected data and provides a query language called Cypher.

## Key Concepts
*   **Nodes**: The entities in the graph (e.g., `Person`, `Movie`).
*   **Relationships**: The connections between nodes (e.g., `ACTED_IN`, `DIRECTED`).
*   **Properties**: Key-value pairs stored on nodes and relationships (e.g., `name`, `released`).
*   **Labels**: Tags used to group nodes (e.g., `:Person`, `:Movie`).

## Cypher Query Language
Cypher is ASCII-art style query language.

### Creating Data
```cypher
CREATE (matrix:Movie {title: 'The Matrix', released: 1997})
CREATE (keanu:Person {name: 'Keanu Reeves', born: 1964})
CREATE (keanu)-[:ACTED_IN {roles:['Neo']}]->(matrix)
```

### Matching Data
```cypher
MATCH (p:Person {name: 'Keanu Reeves'})-[:ACTED_IN]->(m:Movie)
RETURN m.title
```

### Loading Data (CSV)
```cypher
LOAD CSV WITH HEADERS FROM "movies.csv" AS line
CREATE (m:Movie {id: line.id, title: line.title, released: toInteger(line.year)})
```

## Java API (Embedded)
```java
try (Transaction tx = graphDb.beginTx()) {
    Node node = tx.createNode();
    node.setProperty("message", "Hello, World!");
    tx.commit();
}
```

## Indexing
Indices improve lookup performance.
```cypher
CREATE INDEX FOR (a:Actor) ON (a.name)
```

## Vector Search (GraphRAG)
Neo4j supports vector indexing for semantic search, often used with LLMs.
*   **Vector Index**: Stores embeddings on nodes.
*   **Similarity Search**: Finds nodes with similar embeddings (cosine, euclidean).

## Graph Data Science (GDS)
Neo4j GDS library provides algorithms for graph analysis:
*   **PageRank**: Node importance.
*   **Community Detection**: Clustering (Louvain, Leiden).
*   **Betweenness Centrality**: Finding bridge nodes.






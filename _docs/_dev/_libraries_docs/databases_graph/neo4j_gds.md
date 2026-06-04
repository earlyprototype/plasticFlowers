# Neo4j Graph Data Science (GDS) Documentation

## Overview
The Neo4j Graph Data Science (GDS) library provides graph algorithms and machine learning features efficiently within Neo4j. It enables analytics on graph data to find communities, central nodes, and similar patterns.

## Key Concepts

### 1. Graph Projections
*   **Named Graph**: An in-memory projection of the graph optimized for speed. Algorithms run on these projections, not the direct database storage.
*   **Native Projection**: `gds.graph.project('myGraph', 'NodeLabel', 'REL_TYPE', {nodeProperties:..., relationshipProperties:...})`.
*   **Cypher Projection**: Uses Cypher queries to define nodes and relationships for the projection.

### 2. Execution Modes
*   **Stream**: Returns algorithm results directly to the user (does not modify graph).
    *   `CALL gds.algo.stream(...)`
*   **Stats**: Returns performance metrics and statistics (no results, no graph mod).
    *   `CALL gds.algo.stats(...)`
*   **Mutate**: Writes results to the in-memory graph projection (fast for chaining algorithms).
    *   `CALL gds.algo.mutate(...)`
*   **Write**: Writes results back to the Neo4j database as properties or relationships.
    *   `CALL gds.algo.write(...)`

### 3. Algorithm Categories
*   **Centrality**: PageRank, Betweenness, Closeness (identify important nodes).
*   **Community Detection**: Louvain, Leiden, Label Propagation, Triangle Count (find clusters).
*   **Path Finding**: Dijkstra, A*, BFS, DFS (shortest paths).
*   **Similarity**: Node Similarity, K-Nearest Neighbors (KNN).
*   **Machine Learning**: Node Classification, Link Prediction, GraphSAGE.

## Usage Examples

### Graph Projection
```cypher
CALL gds.graph.project(
  'myGraph',
  'User',
  'FRIEND',
  { relationshipProperties: 'weight' }
)
```

### PageRank (Stream)
```cypher
CALL gds.pageRank.stream('myGraph')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name AS name, score
ORDER BY score DESC
```

### Louvain Community Detection (Write)
```cypher
CALL gds.louvain.write(
  'myGraph',
  { writeProperty: 'community' }
)
YIELD communityCount, modularity, nodePropertiesWritten
```

### Triangle Count (Stats)
```cypher
CALL gds.triangleCount.stats('myGraph')
YIELD globalTriangleCount, nodeCount
```

## Detailed Reference (Code Snippets)

### Run Delta-Stepping Algorithm in Stats Mode (Cypher)
Source: https://github.com/neo4j/graph-data-science/blob/2.13/doc/modules/ROOT/partials/algorithms/shortest-path/path-syntax.adoc

```cypher
CALL {procedure-name}.stats(
  graphName: String,
  configuration: Map
)
YIELD
  preProcessingMillis: Integer,
  computeMillis: Integer,
  postProcessingMillis: Integer,
  configuration: Map
----
```

### Bridges Algorithm
Source: https://github.com/neo4j/graph-data-science/blob/2.13/doc/modules/ROOT/pages/algorithms/bridges.adoc

```cypher
CALL gds.bridges.stream(
  graphName = 'myGraph'
)
YIELD from, to
RETURN from, to
```

### Stream Mode Algorithm Execution
Source: https://github.com/neo4j/graph-data-science/blob/2.13/doc/modules/ROOT/partials/algorithms/shortest-path/path-syntax.adoc

```cypher
CALL gds.shortestPath.dijkstra.stream(
  "myGraph",
  {sourceNode: 1, targetNode: 5, relationshipWeightProperty: "cost"}
)
YIELD 
  index, sourceNode, targetNode, totalCost, nodeIds, costs, path
```

### Algorithm Write Mode
Source: https://github.com/neo4j/graph-data-science/blob/2.13/doc/modules/ROOT/partials/algorithms/shortest-path/path-syntax.adoc

```cypher
CALL myGraph.write(
  graphName: 'myGraph',
  configuration: {
    relationshipWeightProperty: 'weight',
    sourceNode: 1,
    targetNodes: [2, 3],
    k: 5,
    writeNodeIds: true
  }
)
YIELD relationshipsWritten, preProcessingMillis, computeMillis, writeMillis, configuration
```

### Algorithm Stats Mode
Source: https://github.com/neo4j/graph-data-science/blob/2.13/doc/modules/ROOT/partials/algorithms/shortest-path/path-syntax.adoc

```cypher
CALL myGraph.stats(
  graphName: 'myGraph',
  configuration: {
    relationshipWeightProperty: 'weight',
    sourceNode: 1,
    targetNodes: [2, 3],
    k: 5
  }
)
YIELD preProcessingMillis, computeMillis, configuration
```

### Mutate Mode Algorithm Execution
Source: https://github.com/neo4j/graph-data-science/blob/2.13/doc/modules/ROOT/partials/algorithms/shortest-path/path-syntax.adoc

```cypher
CALL gds.shortestPath.dijkstra.mutate(
  "myGraph",
  {sourceNode: 1, targetNode: 5, relationshipWeightProperty: "cost", mutateRelationshipType: "PATH"}
)
YIELD 
  relationshipsWritten, preProcessingMillis, computeMillis, postProcessingMillis, mutateMillis, configuration
```

### Louvain Algorithm Example
Source: https://github.com/neo4j/graph-data-science/blob/2.13/doc/modules/ROOT/pages/algorithms/louvain.adoc

```cypher
CALL gds.louvain.write(
  'myGraph',
  {
    nodeLabels: ['User'],
    relationshipTypes: ['LINK'],
    orientation: 'UNDIRECTED',
    writeProperty: 'louvainCommunity'
  }
) YIELD
  preProcessingMillis,
  computeMillis,
  writeMillis,
  postProcessingMillis,
  nodePropertiesWritten,
  communityCount,
  ranLevels,
  modularity,
  modularities,
  communityDistribution,
  configuration
```

### Run Algorithm in Stats Mode
Source: https://github.com/neo4j/graph-data-science/blob/2.13/doc/modules/ROOT/partials/algorithms/shortest-path/bellman-ford/bellman-ford-syntax.adoc

```json
{
  "graphName": "myGraph",
  "configuration": {
    "writeNegativeCycles": true,
    "sourceNode": 123
  }
}
```

### Get Random Walk Algorithm Statistics
Source: https://github.com/neo4j/graph-data-science/blob/2.13/doc/modules/ROOT/pages/algorithms/random-walk.adoc

```cypher
CALL gds.randomWalk.stats(
  'myGraph',
  {
    walkLength: 3,
    walksPerNode: 1,
    randomSeed: 42,
    concurrency: 1
  }
)
```

### Triangle Count Algorithm
Source: https://github.com/neo4j/graph-data-science/blob/2.13/doc/modules/ROOT/pages/algorithms/triangle-count.adoc

```cypher
CALL gds.triangleCount.stream(
  graphName: 'myGraph',
  configuration: {
    nodeProjection: 'User',
    relationshipProjection: {
      FRIENDS: { type: 'FRIENDS', orientation: 'UNDIRECTED' }
    }
  }
)
YIELD nodeId, triangleCount
RETURN nodeId, triangleCount
```

### GDS Leiden Algorithm
Source: https://github.com/neo4j/graph-data-science/blob/2.13/doc/modules/ROOT/pages/algorithms/leiden.adoc

```cypher
CALL gds.leiden.stream('myGraph', {
  nodeLabels: ['User'],
  relationshipTypes: ['LINK'],
  includeWeightProperty: 'weight'
})
YIELD nodeId, communityId, communityTotal, communityDistribution
```

### Run Algorithm in Stream Mode
Source: https://github.com/neo4j/graph-data-science/blob/2.13/doc/modules/ROOT/partials/algorithms/shortest-path/bellman-ford/bellman-ford-syntax.adoc

```cypher
CALL myAlgorithm.stream(
  "myGraph",
  {
    sourceNode: 1,
    relationshipWeightProperty: "weight"
  }
)
YIELD index, sourceNode, targetNode, totalCost, nodeIds, costs, route, isNegativeCycle
```

### Memory Estimation for Bridges Algorithm
Source: https://github.com/neo4j/graph-data-science/blob/2.13/doc/modules/ROOT/pages/algorithms/bridges.adoc

```cypher
CALL gds.bridges.stream.estimate(graphName = 'myGraph', configuration = {})
YIELD nodeCount, relationshipCount, bytesMin, bytesMax, requiredMemory
```

### HITS Algorithm - Stats Mode
Source: https://github.com/neo4j/graph-data-science/blob/2.13/doc/modules/ROOT/pages/algorithms/hits.adoc

```cypher
CALL gds.hits.stats(
  graphName: String,
  configuration: Map
)
YIELD
  ranIterations: Integer,
  didConverge: Boolean,
  preProcessingMillis: Integer,
  computeMillis: Integer,
  configuration: Map
```



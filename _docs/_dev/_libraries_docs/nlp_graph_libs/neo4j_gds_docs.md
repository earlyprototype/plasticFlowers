# Neo4j Graph Data Science Documentation

## Overview
Neo4j Graph Data Science (GDS) is a library of graph algorithms optimised for Neo4j. It provides production-ready implementations of PageRank, Louvain community detection, shortest paths, centrality measures, similarity algorithms, and machine learning pipelines—all executed within Neo4j for high performance.

## Core Capabilities

### Graph Algorithms
- **Centrality**: PageRank, Betweenness, Degree, Eigenvector, Closeness
- **Community Detection**: Louvain, Label Propagation, Weakly Connected Components
- **Path Finding**: Dijkstra, A*, Yen's K-Shortest Paths, Minimum Weight Spanning Tree
- **Similarity**: Node Similarity, K-Nearest Neighbors, Cosine, Jaccard
- **Link Prediction**: Adamic Adar, Common Neighbors, Preferential Attachment
- **Node Embeddings**: Node2Vec, GraphSAGE, FastRP

### Graph ML Pipelines
- **Node Classification**: Predict node properties
- **Link Prediction**: Predict missing relationships
- **Node Regression**: Predict continuous values
- **Training & Model Management**: Built-in ML pipelines

## Basic Workflow

### 1. Project a Graph

```cypher
// Create named graph projection
CALL gds.graph.project(
    'myGraph',                           // Graph name
    ['Person', 'Company'],               // Node labels
    {
        WORKS_AT: {orientation: 'NATURAL'},
        KNOWS: {orientation: 'UNDIRECTED'}
    }
)
YIELD graphName, nodeCount, relationshipCount
```

### 2. Run Algorithm

```cypher
// Run PageRank
CALL gds.pageRank.stream('myGraph')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name AS name, score
ORDER BY score DESC
LIMIT 10
```

### 3. Write Results

```cypher
// Write PageRank scores back to database
CALL gds.pageRank.write('myGraph', {
    writeProperty: 'pagerank'
})
YIELD nodePropertiesWritten
```

## Graph Projections

### Native Projection

```cypher
CALL gds.graph.project(
    'nativeGraph',
    'Person',
    'KNOWS',
    {
        nodeProperties: 'age',
        relationshipProperties: 'weight'
    }
)
```

### Cypher Projection

```cypher
CALL gds.graph.project.cypher(
    'cypherGraph',
    'MATCH (n:Person) WHERE n.age > 18 RETURN id(n) AS id, labels(n) AS labels',
    'MATCH (a:Person)-[r:KNOWS]->(b:Person) RETURN id(a) AS source, id(b) AS target, r.weight AS weight'
)
```

## Centrality Algorithms

### PageRank

```cypher
// Stream mode
CALL gds.pageRank.stream('myGraph', {
    maxIterations: 20,
    dampingFactor: 0.85
})
YIELD nodeId, score

// Write mode
CALL gds.pageRank.write('myGraph', {
    maxIterations: 20,
    writeProperty: 'pagerank'
})
```

### Betweenness Centrality

```cypher
CALL gds.betweenness.stream('myGraph')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name, score
ORDER BY score DESC
```

### Degree Centrality

```cypher
CALL gds.degree.stream('myGraph', {
    orientation: 'NATURAL'  // or 'REVERSE', 'UNDIRECTED'
})
YIELD nodeId, score
```

## Community Detection

### Louvain

```cypher
// Find communities
CALL gds.louvain.write('myGraph', {
    writeProperty: 'community',
    includeIntermediateCommunities: true
})
YIELD communityCount, modularity, modularities

// Analyse community distribution
MATCH (n)
RETURN n.community AS community, count(*) AS size
ORDER BY size DESC
```

### Label Propagation

```cypher
CALL gds.labelPropagation.write('myGraph', {
    writeProperty: 'label',
    maxIterations: 10
})
YIELD communityCount
```

### Weakly Connected Components

```cypher
CALL gds.wcc.write('myGraph', {
    writeProperty: 'componentId'
})
YIELD componentCount, componentDistribution
```

## Path Finding

### Shortest Path (Dijkstra)

```cypher
MATCH (start:Location {name: 'A'}), (end:Location {name: 'B'})
CALL gds.shortestPath.dijkstra.stream('myGraph', {
    sourceNode: start,
    targetNode: end,
    relationshipWeightProperty: 'distance'
})
YIELD nodeIds, costs
RETURN [nodeId IN nodeIds | gds.util.asNode(nodeId).name] AS path, costs
```

### All Shortest Paths

```cypher
CALL gds.allShortestPaths.stream('myGraph', {
    sourceNode: id(startNode),
    relationshipWeightProperty: 'weight'
})
YIELD sourceNodeId, targetNodeId, distance
```

## Similarity Algorithms

### Node Similarity

```cypher
CALL gds.nodeSimilarity.write('myGraph', {
    writeRelationshipType: 'SIMILAR',
    writeProperty: 'score',
    similarityCutoff: 0.5
})
YIELD nodesCompared, relationshipsWritten
```

### K-Nearest Neighbors

```cypher
CALL gds.knn.write('myGraph', {
    nodeProperties: ['age', 'income'],
    topK: 5,
    writeRelationshipType: 'NEIGHBOR',
    writeProperty: 'score'
})
```

## Node Embeddings

### FastRP (Fast Random Projection)

```cypher
CALL gds.fastRP.write('myGraph', {
    embeddingDimension: 128,
    iterationWeights: [0.0, 1.0, 1.0],
    writeProperty: 'embedding'
})
```

### Node2Vec

```cypher
CALL gds.node2vec.write('myGraph', {
    embeddingDimension: 128,
    walkLength: 80,
    walksPerNode: 10,
    writeProperty: 'embedding'
})
```

## Machine Learning Pipelines

### Node Classification Pipeline

```cypher
// Create pipeline
CALL gds.beta.pipeline.nodeClassification.create('myPipeline')

// Add node properties
CALL gds.beta.pipeline.nodeClassification.addNodeProperty('myPipeline', 'fastRP', {
    embeddingDimension: 128
})

// Select features
CALL gds.beta.pipeline.nodeClassification.selectFeatures('myPipeline', ['fastRP'])

// Add model
CALL gds.beta.pipeline.nodeClassification.addLogisticRegression('myPipeline')

// Train
CALL gds.beta.pipeline.nodeClassification.train('myGraph', {
    pipeline: 'myPipeline',
    targetProperty: 'category',
    modelName: 'myModel',
    metrics: ['ACCURACY', 'F1_WEIGHTED']
})

// Predict
CALL gds.beta.pipeline.nodeClassification.predict.stream('myGraph', {
    modelName: 'myModel'
})
YIELD nodeId, predictedClass, probabilities
```

## Python Client

### Installation

```bash
pip install graphdatascience
```

### Basic Usage

```python
from graphdatascience import GraphDataScience

# Connect to Neo4j
gds = GraphDataScience("bolt://localhost:7687", auth=("neo4j", "password"))

# Project graph
G = gds.graph.project(
    "myGraph",
    {"Person": {"properties": "age"}},
    {"KNOWS": {"orientation": "UNDIRECTED"}}
)

# Run PageRank
result = gds.pageRank.write(G, writeProperty="pagerank")
print(f"Computed PageRank for {result['nodePropertiesWritten']} nodes")

# Stream results
df = gds.pageRank.stream(G)
print(df.head())

# Drop projection
gds.graph.drop(G)
```

## Best Practices

1. **Graph Projections**: Use native projections for performance; Cypher for flexibility
2. **Algorithm Modes**: Use `stream` for exploration, `write` for production
3. **Memory Management**: Drop projections when done to free memory
4. **Parameter Tuning**: Test with `estimate` mode before running on large graphs
5. **Parallel Execution**: Leverage GDS concurrency settings
6. **Result Validation**: Always validate algorithm outputs before using downstream
7. **Monitoring**: Use `gds.graph.list()` to track active projections
8. **Version Compatibility**: Check GDS version matches Neo4j version

## Resources

- **Documentation**: https://neo4j.com/docs/graph-data-science/
- **Python Client**: https://github.com/neo4j/graph-data-science-client
- **GitHub**: https://github.com/neo4j/graph-data-science






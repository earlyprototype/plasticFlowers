# Neo4j GraphRAG Python Documentation

## Overview
The official Neo4j GraphRAG package for Python enables developers to build graph retrieval augmented generation (GraphRAG) applications using Neo4j and Python. It provides a robust, feature-rich solution for combining knowledge graphs with LLM-powered question answering.

## Core Capabilities

### Hybrid Retrieval
- **Vector Search**: Semantic similarity using embeddings
- **Full-Text Search**: Keyword-based retrieval
- **Graph Traversal**: Relationship-aware context gathering
- **Hybrid Queries**: Combine multiple retrieval strategies

### LLM Integration
- **Multiple Providers**: OpenAI, Anthropic, Google, Azure
- **Prompt Templates**: Customisable RAG prompts
- **Context Window Management**: Intelligent context pruning
- **Streaming**: Real-time response generation

## Installation

```bash
pip install neo4j-graphrag
```

## Basic Usage

### Setup Connection

```python
from neo4j_graphrag import Neo4jGraphRAG
from neo4j import GraphDatabase

# Initialize Neo4j driver
driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "password")
)

# Create GraphRAG instance
graphrag = Neo4jGraphRAG(
    driver=driver,
    llm_provider="openai",
    llm_model="gpt-4o",
    api_key="your-openai-key"
)
```

### Simple Query

```python
# Ask a question
response = graphrag.query(
    "What products did Apple announce in 2023?"
)

print(response.answer)
print(f"Retrieved {len(response.contexts)} context chunks")
```

## Vector Search

### Create Vector Index

```cypher
// In Neo4j
CREATE VECTOR INDEX product_embeddings IF NOT EXISTS
FOR (n:Product)
ON n.embedding
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 1536,
    `vector.similarity_function`: 'cosine'
  }
}
```

### Generate and Store Embeddings

```python
from neo4j_graphrag.embeddings import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(api_key="your-key")

# Generate embeddings for documents
docs = ["Product description 1", "Product description 2"]
vectors = embeddings.embed_documents(docs)

# Store in Neo4j
with driver.session() as session:
    for doc, vector in zip(docs, vectors):
        session.run(
            """
            CREATE (p:Product {description: $doc, embedding: $vector})
            """,
            doc=doc,
            vector=vector
        )
```

### Vector Similarity Search

```python
query_vector = embeddings.embed_query("Find innovative tech products")

with driver.session() as session:
    result = session.run(
        """
        CALL db.index.vector.queryNodes('product_embeddings', 5, $vector)
        YIELD node, score
        RETURN node.description, score
        """,
        vector=query_vector
    )
    
    for record in result:
        print(f"{record['node.description']}: {record['score']}")
```

## Hybrid Retrieval

### Vector + Graph Traversal

```python
from neo4j_graphrag.retrievers import HybridRetriever

retriever = HybridRetriever(
    driver=driver,
    index_name="product_embeddings",
    vector_top_k=5,
    graph_depth=2  # Traverse 2 hops from retrieved nodes
)

# Retrieve context
contexts = retriever.retrieve(
    query="What are Apple's AI-powered products?",
    query_vector=embeddings.embed_query("Apple AI products")
)

for ctx in contexts:
    print(ctx.content)
    print(f"Score: {ctx.score}, Hops: {ctx.depth}")
```

## RAG Pipeline

### Complete RAG Workflow

```python
from neo4j_graphrag import GraphRAG
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.retrievers import VectorRetriever

# Setup components
llm = OpenAILLM(api_key="your-key", model="gpt-4o")

retriever = VectorRetriever(
    driver=driver,
    index_name="product_embeddings",
    embeddings=embeddings,
    top_k=10
)

# Create RAG pipeline
rag = GraphRAG(
    llm=llm,
    retriever=retriever,
    system_prompt="""You are a helpful assistant. Use the provided context 
    from the knowledge graph to answer questions accurately."""
)

# Query
response = rag.query("Explain Apple's chip architecture evolution")
print(response.answer)
print(f"\nSources: {response.source_nodes}")
```

## Advanced Retrieval Strategies

### Multi-Hop Graph Retrieval

```python
from neo4j_graphrag.retrievers import GraphRetriever

graph_retriever = GraphRetriever(
    driver=driver,
    retrieval_query="""
    MATCH (start:Product)-[:MANUFACTURED_BY]->(company:Company)
    WHERE start.name = $entity
    MATCH (company)-[:RELEASED]->(other:Product)
    RETURN other.name, other.description
    """,
    top_k=5
)

contexts = graph_retriever.retrieve(
    query="What other products does Apple make?",
    parameters={"entity": "iPhone"}
)
```

### Custom Retriever

```python
from neo4j_graphrag.retrievers import BaseRetriever

class CustomRetriever(BaseRetriever):
    def retrieve(self, query: str, **kwargs):
        # Custom retrieval logic
        with self.driver.session() as session:
            result = session.run(
                """
                // Your custom Cypher query
                MATCH (n:Node)
                WHERE n.property CONTAINS $query
                RETURN n.content AS content
                LIMIT 10
                """,
                query=query
            )
            
            contexts = [
                {"content": record["content"], "score": 1.0}
                for record in result
            ]
            return contexts
```

## Prompt Engineering

### Custom Prompts

```python
custom_prompt = """
Context from knowledge graph:
{context}

Based on the above context, answer the following question.
If the context doesn't contain relevant information, say so.

Question: {question}

Answer:
"""

rag = GraphRAG(
    llm=llm,
    retriever=retriever,
    prompt_template=custom_prompt
)
```

### Dynamic Context Formatting

```python
def format_context(contexts):
    """Custom context formatting"""
    formatted = []
    for ctx in contexts:
        formatted.append(f"Source: {ctx.source}\nContent: {ctx.content}\n")
    return "\n---\n".join(formatted)

rag.set_context_formatter(format_context)
```

## Knowledge Graph Construction

### Document to Graph

```python
from neo4j_graphrag.knowledge_graph import GraphBuilder

builder = GraphBuilder(
    driver=driver,
    llm=llm,
    schema={
        "entities": ["Person", "Company", "Product"],
        "relationships": ["WORKS_AT", "MANUFACTURES", "COMPETES_WITH"]
    }
)

# Extract entities and relationships from text
text = """
Apple CEO Tim Cook announced the new iPhone 15. 
The device features Apple's A17 chip and competes with Samsung's Galaxy S23.
"""

graph_data = builder.extract(text)

# Store in Neo4j
builder.store(graph_data)
```

## Evaluation

### RAG Metrics

```python
from neo4j_graphrag.evaluation import RAGEvaluator

evaluator = RAGEvaluator(
    metrics=["relevance", "faithfulness", "answer_similarity"]
)

# Evaluate responses
test_cases = [
    {"question": "What is Apple's latest chip?", "expected": "A17 Bionic"},
    {"question": "Who is Apple's CEO?", "expected": "Tim Cook"}
]

results = []
for case in test_cases:
    response = rag.query(case["question"])
    score = evaluator.evaluate(
        question=case["question"],
        answer=response.answer,
        contexts=response.contexts,
        expected=case["expected"]
    )
    results.append(score)

print(f"Average relevance: {sum(r['relevance'] for r in results) / len(results)}")
```

## Streaming Responses

```python
# Stream tokens as they're generated
for chunk in rag.query_stream("Explain Apple's ecosystem"):
    print(chunk, end="", flush=True)
```

## Best Practices

1. **Index Strategy**: Create vector indexes on frequently queried node properties
2. **Embedding Models**: Choose embedding dimension based on data size (1536 for large datasets)
3. **Retrieval K**: Start with top_k=5-10 for balanced precision/recall
4. **Graph Depth**: Limit traversal depth to 2-3 hops to avoid noise
5. **Prompt Design**: Include instructions for handling missing context
6. **Hybrid Search**: Combine vector + keyword search for better coverage
7. **Context Management**: Prune contexts to fit within LLM token limits
8. **Evaluation**: Regularly evaluate RAG quality with test datasets

## Resources

- **Documentation**: https://neo4j.com/docs/graphrag-python/
- **GitHub**: https://github.com/neo4j/neo4j-graphrag-python
- **Examples**: https://github.com/neo4j/neo4j-graphrag-python/tree/main/examples






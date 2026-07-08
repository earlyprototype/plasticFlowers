# Cohere API Documentation

## Overview
Cohere provides enterprise-grade language models specialising in embeddings, semantic search, retrieval, and reranking. Their models are optimised for production use cases requiring high-quality vector representations and search relevance.

## Core Capabilities

### Embeddings
- **Multi-language support**: 100+ languages
- **Multimodal**: Text and image embeddings
- **Semantic search**: High-quality vector representations
- **Batch processing**: Efficient large-scale embedding generation

### Reranking
- **Relevance optimisation**: Improve search result ordering
- **Cross-encoder architecture**: More accurate than embeddings alone
- **Fine-tuning support**: Customise for specific domains

## Embeddings API

### Models

- **embed-v4.0**: Latest, highest quality, 1024 dimensions
- **embed-english-v3.0**: English-optimised, fast performance
- **embed-multilingual-v3.0**: 100+ languages
- **embed-english-light-v2.0**: Lightweight, cost-effective

### Generate Embeddings

```python
import cohere

co = cohere.Client(api_key="your-api-key")

# Single document
response = co.embed(
    texts=["Your text to embed"],
    model="embed-v4.0",
    input_type="search_document",  # or "search_query", "classification", "clustering"
    embedding_types=["float"]
)

embeddings = response.embeddings.float
```

### Input Types

- **search_document**: For documents in a search corpus
- **search_query**: For user search queries
- **classification**: For text classification tasks
- **clustering**: For clustering/grouping tasks

### Semantic Search Example

```python
# Define documents
documents = [
    "Joining Slack Channels: You will receive an invite via email.",
    "Finding Coffee Spots: Head to the break room's coffee machine.",
    "Team-Building Activities: Monthly outings and weekly game nights.",
    "Working Hours Flexibility: Core hours are 9 AM to 5 PM."
]

# Embed documents
doc_emb = co.embed(
    texts=documents,
    model="embed-v4.0",
    input_type="search_document",
    embedding_types=["float"]
).embeddings.float

# Embed query
query = "How to connect with my teammates?"
query_emb = co.embed(
    texts=[query],
    model="embed-v4.0",
    input_type="search_query",
    embedding_types=["float"]
).embeddings.float

# Calculate similarity
import numpy as np
scores = np.dot(query_emb, np.transpose(doc_emb))[0]

# Get top results
top_n = 2
top_doc_idxs = np.argsort(-scores)[:top_n]

for idx, doc_idx in enumerate(top_doc_idxs):
    print(f"Rank {idx+1}: {documents[doc_idx]}")
```

## Rerank API

### Basic Reranking

```python
query = "What is the capital of France?"

documents = [
    "Paris is the capital of France.",
    "Berlin is the capital of Germany.",
    "The Eiffel Tower is in Paris.",
    "France is a country in Europe."
]

results = co.rerank(
    query=query,
    documents=documents,
    model="rerank-english-v2.0",
    top_n=3
)

for result in results:
    print(f"Score: {result.relevance_score:.4f} - {documents[result.index]}")
```

### Advanced Reranking with Metadata

```python
results = co.rerank(
    query="Tell me about machine learning",
    documents=[
        {"text": "Machine learning is a subset of AI.", "id": "doc1"},
        {"text": "Deep learning uses neural networks.", "id": "doc2"}
    ],
    model="rerank-english-v3.0",
    top_n=5,
    return_documents=True
)
```

## Multimodal Embeddings

### Text and Image Embeddings

```python
# Embed text
text_emb = co.embed(
    inputs=[{"content": [{"type": "text", "text": "A photo of a cat"}]}],
    model="embed-v4.0",
    input_type="search_document",
    embedding_types=["float"]
).embeddings.float

# Embed image (base64 encoded)
image_emb = co.embed(
    inputs=[{
        "content": [{
            "type": "image",
            "data": base64_image_data,
            "mime_type": "image/jpeg"
        }]
    }],
    model="embed-v4.0",
    input_type="search_document",
    embedding_types=["float"]
).embeddings.float

# Calculate cross-modal similarity
similarity = np.dot(text_emb, np.transpose(image_emb))[0][0]
```

## Batch Embedding Jobs

For large-scale embedding generation:

```
POST https://api.cohere.ai/v1/embed-jobs
```

```python
job = co.create_embed_job(
    dataset_id="your-dataset-id",
    model="embed-v4.0",
    input_type="search_document"
)

# Check job status
status = co.get_embed_job(job.id)

# Retrieve results when complete
if status.status == "complete":
    results = co.get_embed_job_results(job.id)
```

## API Endpoints

### Embeddings
```
POST https://api.cohere.ai/v1/embed
```

### Rerank
```
POST https://api.cohere.ai/v1/rerank
```

### Batch Jobs
```
POST https://api.cohere.ai/v1/embed-jobs
GET https://api.cohere.ai/v1/embed-jobs/{job_id}
```

## Integration with Vector Databases

### Example: Using with Neo4j

```python
# Generate embeddings
embeddings = co.embed(
    texts=knowledge_snippets,
    model="embed-v4.0",
    input_type="search_document"
).embeddings.float

# Store in Neo4j
from neo4j import GraphDatabase

driver = GraphDatabase.driver(uri, auth=(user, password))

with driver.session() as session:
    for i, emb in enumerate(embeddings):
        session.run("""
            MERGE (n:Document {id: $id})
            SET n.embedding = $embedding,
                n.text = $text
        """, id=i, embedding=emb, text=knowledge_snippets[i])

# Query with vector similarity
query_emb = co.embed(
    texts=[user_query],
    model="embed-v4.0",
    input_type="search_query"
).embeddings.float[0]

results = session.run("""
    CALL db.index.vector.queryNodes('doc_embeddings', 10, $query_vector)
    YIELD node, score
    RETURN node.text, score
""", query_vector=query_emb)
```

## Pricing (Approximate)

### Embeddings
- **embed-v4.0**: $0.10 per 1M tokens
- **embed-english-v3.0**: $0.10 per 1M tokens
- **embed-multilingual-v3.0**: $0.10 per 1M tokens

### Rerank
- **rerank-english-v3.0**: $2.00 per 1M search units
- **rerank-multilingual-v3.0**: $2.00 per 1M search units

## Best Practices

### Embedding Optimization
- Use appropriate `input_type` for your use case
- Consider compression options for storage (`int8` embeddings)
- Batch requests for better throughput

### Reranking Strategy
- Use embeddings for initial retrieval (fast, scalable)
- Apply rerank to top-k candidates (precise, but slower)
- Typical pattern: Retrieve 100 with embeddings, rerank top 20

### Multimodal Search
- Embed both text and images in the same vector space
- Enable cross-modal search (text query → find images)
- Use for visual knowledge graph applications

## PlasticFlower Integration Use Cases

1. **Semantic Search**: High-quality embeddings for knowledge retrieval
2. **Cross-Modal Search**: Connect text descriptions with visual content
3. **Reranking**: Improve relevance of graph traversal results
4. **Multilingual Support**: 100+ languages for global knowledge graphs
5. **Batch Processing**: Efficient embedding generation for large graphs
6. **Clustering**: Group related knowledge nodes automatically

## Resources

- **Documentation**: https://docs.cohere.com/
- **API Reference**: https://docs.cohere.com/reference/
- **Embed API**: https://docs.cohere.com/docs/embeddings
- **Rerank API**: https://docs.cohere.com/docs/reranking

## Client Libraries

### Python
```bash
pip install cohere
```

### JavaScript/TypeScript
```bash
npm install cohere-ai
```

## Key Advantages for PlasticFlower

1. **Specialised for Search**: Purpose-built for retrieval tasks
2. **Multimodal**: Unified vector space for text and images
3. **Reranking**: Best-in-class relevance optimisation
4. **Multilingual**: Support 100+ languages out of the box
5. **Production-Ready**: Enterprise-grade reliability and performance
6. **Cost-Effective**: Competitive pricing for embeddings and rerank

## Comparison with Other Providers

### vs OpenAI Embeddings
- **Cohere**: Better for retrieval, multilingual
- **OpenAI**: Better for general-purpose, wider ecosystem

### vs Claude
- **Cohere**: Specialised embeddings and rerank APIs
- **Claude**: No native embeddings, stronger at generation

### vs Gemini
- **Cohere**: Superior reranking, production-focused
- **Gemini**: Free tier, multimodal generation

## Use Case: RAG Pipeline with Cohere

```python
# 1. Embed knowledge base
docs_emb = co.embed(texts=documents, model="embed-v4.0", 
                    input_type="search_document").embeddings.float

# 2. Embed user query
query_emb = co.embed(texts=[query], model="embed-v4.0",
                     input_type="search_query").embeddings.float

# 3. Vector similarity search (top 100)
scores = np.dot(query_emb, np.transpose(docs_emb))[0]
top_100_idxs = np.argsort(-scores)[:100]

# 4. Rerank top 100 to get best 5
rerank_docs = [documents[i] for i in top_100_idxs]
reranked = co.rerank(query=query, documents=rerank_docs,
                     model="rerank-english-v3.0", top_n=5)

# 5. Use top 5 as context for generation
context = "\n".join([rerank_docs[r.index] for r in reranked])
```






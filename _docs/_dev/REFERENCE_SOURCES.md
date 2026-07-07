# External Reference Sources

**Purpose:** Curated, high-trust external resources for plasticFlower development.  
**Last Updated:** 2025-12-26 (GitHub patterns + YouTube transcripts)  
**Usage:** Reference when implementing features or learning concepts.

---

## Quick Reference

| Need | Primary Resource | Backup |
|------|-----------------|--------|
| **Entity Extraction** | YouTube Tutorial 2 + GitHub code | `/neo4j/neo4j-graphrag-python` |
| **Pipeline Architecture** | `neo4j-labs/llm-graph-builder` | YouTube Tutorial 3 |
| **GraphRAG Querying** | `/neo4j/neo4j-graphrag-python` | GraphAcademy courses |
| **GDS Clustering** | `/neo4j/graph-data-science-client` | Community detection notebook |
| **SSE Streaming** | `docker/genai-stack` | `zer0pool/graph-viz` stability doc |
| **FastAPI + Neo4j** | `neo4j-labs/llm-graph-builder` | Docker GenAI Stack |
| **Event Replay/Sync** | `zer0pool/graph-viz` SSE doc | Redis Streams docs |
| **Cypher Patterns** | Neo4j Cypher Manual | Building a GraphRAG App video |
| **Cost Optimization** | GraphRAG vs LightRAG video | ADR-001 |

---

## Official Neo4j Resources (Trust Score: 8-10)

### 1. Neo4j GraphRAG Python Package

**ID:** `/neo4j/neo4j-graphrag-python`  
**Trust Score:** 8.8  
**Snippets:** 182  
**URL:** https://github.com/neo4j/neo4j-graphrag-python

**Key Features:**
- VectorRetriever for similarity search
- Text2CypherRetriever for NL to Cypher
- SimpleKGPipeline for knowledge graph construction
- MessageHistory for conversation context
- Multiple LLM integrations (OpenAI, Anthropic, Cohere, Ollama)

**Most Relevant Examples:**

```python
# Quickstart GraphRAG Query
from neo4j import GraphDatabase
from neo4j_graphrag.retrievers import VectorRetriever
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.embeddings import OpenAIEmbeddings

driver = GraphDatabase.driver(URI, auth=AUTH)
embedder = OpenAIEmbeddings(model="text-embedding-3-large")
retriever = VectorRetriever(driver, INDEX_NAME, embedder)
llm = OpenAILLM(model_name="gpt-4o", model_params={"temperature": 0})
rag = GraphRAG(retriever=retriever, llm=llm)
response = rag.search(query_text="Your question", retriever_config={"top_k": 5})
```

**When to Use:** Librarian agent implementation, Q&A functionality

---

### 2. Neo4j Graph Data Science Client

**ID:** `/neo4j/graph-data-science-client`  
**Trust Score:** 8.8  
**Snippets:** 755  
**URL:** https://github.com/neo4j/graph-data-science-client

**Key Algorithms for plasticFlower:**

| Algorithm | Purpose | Code |
|-----------|---------|------|
| **Louvain** | Community detection (Flowers) | `gds.louvain.mutate(G, mutateProperty="communityId")` |
| **WCC** | Find connected components | `gds.wcc.mutate(G, mutateProperty="componentId")` |
| **PageRank** | Identify important nodes | `gds.pageRank.write(G, writeProperty="pagerank")` |
| **FastRP** | Generate embeddings | `gds.fastRP.write(G, embeddingDimension=256)` |

**Community Detection Pattern:**

```python
from graphdatascience import GraphDataScience

gds = GraphDataScience(NEO4J_URI, auth=NEO4J_AUTH)

# Project graph
G, result = gds.graph.project("session_graph", "Node", "RELATIONSHIP")

# Run Louvain for clustering
gds.louvain.mutate(G, mutateProperty="communityId")

# Query community sizes
query = """
    CALL gds.graph.nodeProperties.stream($graph_name, 'communityId')
    YIELD nodeId, propertyValue
    WITH propertyValue AS communityId, collect(nodeId) AS members
    RETURN communityId, size(members) AS size
    ORDER BY size DESC
"""
communities = gds.run_cypher(query, params={"graph_name": G.name()})

# Write back to database
gds.graph.nodeProperties.write(G, ["communityId"])

# Cleanup
G.drop()
```

**When to Use:** Phase F (GDS Algorithms) - optional future enhancement

---

### 3. Neo4j GraphAcademy (Free Courses)

**URL:** https://graphacademy.neo4j.com  
**Trust Score:** Official

| Course | Duration | Relevance |
|--------|----------|-----------|
| Neo4j Fundamentals | 2 hours | Phase A |
| Cypher Fundamentals | 1 hour | Phase A |
| Graph Data Modeling | 3 hours | Data model design |
| Building Neo4j Applications with Python | 4 hours | Backend integration |
| Introduction to Vector Indexes | 1 hour | Phase B |

---

### 4. Neo4j Documentation

**Cypher Manual ID:** `/websites/neo4j_cypher-manual_25`  
**Snippets:** 2032  
**Trust Score:** 7.5

**Key Sections:**
- Vector index creation and querying
- Full-text search indexes
- Transaction management
- MERGE patterns

---

## Research Papers (2024-2025)

### GraphRAG Survey (Aug 2024)

**Title:** Graph Retrieval-Augmented Generation: A Survey  
**Link:** https://hf.co/papers/2408.08921  
**Upvotes:** 4

**Key Insights:**
- GraphRAG workflow: Graph-Based Indexing -> Graph-Guided Retrieval -> Graph-Enhanced Generation
- Addresses RAG limitations through structural knowledge representation
- Covers industrial use cases

**Relevance:** Foundational understanding of GraphRAG paradigm

---

### GraphRAG-Bench (Jun 2025)

**Title:** When to use Graphs in RAG  
**Link:** https://hf.co/papers/2506.05690  
**Upvotes:** 2

**Key Insights:**
- Benchmark for evaluating when GraphRAG outperforms vanilla RAG
- Tasks: fact retrieval, complex reasoning, contextual summarization
- Guidelines for practical application

**Relevance:** Decision making on when to use graph vs vector retrieval

---

### HuixiangDou2 (Mar 2025)

**Title:** A Robustly Optimized GraphRAG Approach  
**Link:** https://hf.co/papers/2503.06474  
**GitHub:** https://github.com/tpoisonooo/huixiangdou2

**Key Insights:**
- Dual-level retrieval optimisation
- Multi-stage verification mechanism
- Score improvement from 60 to 74.5 on test set

**Relevance:** Optimisation patterns for retrieval quality

---

### Youtu-GraphRAG (Aug 2025)

**Title:** Vertically Unified Agents for Graph Retrieval-Augmented Complex Reasoning  
**Link:** https://hf.co/papers/2508.19855  
**Upvotes:** 7

**Key Insights:**
- Seed graph schema for targeted extraction
- Dually-perceived community detection (topology + semantics)
- Hierarchical knowledge tree for reasoning
- 90.71% token cost savings

**Relevance:** Advanced agent architecture patterns

---

## GitHub Repositories

### 1. Neo4j GraphRAG Tutorial Series (From YouTube)

**URL:** https://github.com/ronidas39/neo4j-graphRag-Tutorial  
**Trust:** Practitioner (matches video tutorials)  
**Last Updated:** December 2025

Contains working code from the Total Technology Zone tutorial series:
- `tutorial1/` - Schema extraction
- `tutorial2/` - Entity extraction, Neo4j writing
- `tutorial3/` - Pipeline architecture

**Best for:** Copy-paste code patterns that match video explanations.

---

### 2. neo4j-examples (Official)

**URL:** https://github.com/neo4j-examples  
**Trust:** Official Neo4j

Contains example applications for various languages and frameworks.

---

### 3. Awesome-GraphRAG (Community Curated)

**URL:** https://github.com/DEEP-PolyU/Awesome-GraphRAG  
**From:** GraphRAG Survey paper

Curated list of GraphRAG papers, datasets, and projects.

---

### 4. LangChain Neo4j Integration

**ID:** `/langchain-ai/langchain-neo4j`  
**Trust Score:** 9.2  
**Snippets:** 12

Official LangChain integration for Neo4j.

---

### 5. LLM Graph Builder (Neo4j Labs)

**URL:** https://github.com/neo4j-labs/llm-graph-builder  
**Live Demo:** https://llm-graph-builder.neo4jlabs.com/  
**Trust:** Neo4j Labs (8/10)  
**Files:** 58k lines backend, React frontend

Production-quality LLM-to-graph app with:
- FastAPI backend with SSE streaming
- Multi-LLM support (GPT, Gemini, etc.)
- PDF/YouTube/Web ingestion
- Integration testing patterns

**Key Files for plasticFlower:**
- `backend/score.py` - Main FastAPI app with chat endpoints
- `backend/src/` - Extraction, graph writing, embeddings

---

### 6. Docker GenAI Stack

**URL:** https://github.com/docker/genai-stack  
**Trust:** Docker Official (9/10)  
**Stars:** 4k+

LangChain + Neo4j + Ollama stack with:
- SSE streaming pattern for Q&A
- Vector index setup
- RAG chain configuration

**Why it matters:** Clean FastAPI + SSE + Neo4j pattern to copy.

---

### 7. Flexible GraphRAG

**URL:** https://github.com/stevereiner/flexible-graphrag  
**Trust:** Practitioner (7/10)  
**Updated:** December 2024

Full stack with 8 graph databases, 10 vector databases support:
- React/Vue/Angular frontends
- FastAPI backend
- MCP Server included
- Docker Compose setup

**Why it matters:** Multi-frontend patterns, comparison of graph DB options.

---

### 8. Graph-Viz (SSE Stability)

**URL:** https://github.com/zer0pool/graph-viz  
**Trust:** Production app (8/10)  
**Relevance:** Real-time Cytoscape + Neo4j

Contains detailed SSE stability spec with:
- Event replay from Redis Streams
- Polling fallback for sync
- Multi-browser consistency
- Reconnection patterns

**Key Doc:** `docs/04.development-notes/2025-12-03_sse-realtime-event-stability.md`

---

## YouTube Videos (With Transcripts)

All transcripts extracted December 2025 - verified working code patterns.

---

### 1. Neo4j GraphRAG Schema Extraction - Tutorial 1 (Dec 2025)

**URL:** https://www.youtube.com/watch?v=y-pj0fM9PK8  
**Channel:** Total Technology Zone  
**Duration:** ~25 min  
**GitHub:** https://github.com/ronidas39/neo4j-graphRag-Tutorial

**What it covers:**
- Schema extraction from text using `neo4j-graphrag` Python
- 5 use cases: basic, with prompts, predefined node types, export JSON/YAML, visualisation

**Key code pattern:**

```python
from neo4j_graphrag.experimental.components.schema import SchemaFromTextExtractor
from neo4j_graphrag.llm import OpenAILLM

schema_extractor = SchemaFromTextExtractor(
    llm=OpenAILLM(
        model_name="gpt-4o",
        model_params={
            "max_tokens": 5000,
            "response_format": {"type": "json_object"}
        }
    )
)

extracted_schema = await schema_extractor.run(text="Your text here")
extracted_schema.save("my_schema.json")  # Export to JSON
```

**Relevance:** Builder agent schema extraction

---

### 2. Entity Extraction & Graph Construction - Tutorial 2 (Dec 2025)

**URL:** https://www.youtube.com/watch?v=zFj07hcKZx4  
**Channel:** Total Technology Zone  
**Duration:** ~50 min  
**GitHub:** https://github.com/ronidas39/neo4j-graphRag-Tutorial/tree/main/tutorial2

**5 Progressive Topics:**
1. Basic entity extraction (no schema)
2. Custom prompt engineering
3. Writing to Neo4j database
4. Schema-guided extraction
5. Automatic schema discovery (combines Tutorial 1 + 2)

**Key code pattern - Entity Extraction:**

```python
from neo4j_graphrag.experimental.components.entity_relation_extractor import LLMEntityRelationExtractor
from neo4j_graphrag.experimental.components.types import TextChunks, TextChunk
from neo4j_graphrag.llm import OpenAILLM

extractor = LLMEntityRelationExtractor(
    llm=OpenAILLM(
        model_name="gpt-4o",
        model_params={
            "max_tokens": 5000,
            "response_format": {"type": "json_object"}
        }
    )
)

chunks = TextChunks(chunks=[
    TextChunk(text="Your text content here", index=0)
])

graph = await extractor.run(chunks=chunks)

# Access results
for node in graph.nodes:
    print(f"{node.label}: {node.properties}")
for rel in graph.relationships:
    print(f"{rel.type}: {rel.start_node_id} -> {rel.end_node_id}")
```

**Key code pattern - Writing to Neo4j:**

```python
from neo4j import GraphDatabase
from neo4j_graphrag.experimental.components.kg_writer import Neo4jWriter

driver = GraphDatabase.driver("neo4j+s://your-uri", auth=("neo4j", "password"))
writer = Neo4jWriter(driver=driver)
await writer.run(graph=graph)
```

**Relevance:** Builder agent entity extraction, Gardener merge operations

---

### 3. GraphRAG Pipeline - Tutorial 3 (Dec 2025)

**URL:** https://www.youtube.com/watch?v=AVG7AEOrNOs  
**Channel:** Total Technology Zone  
**Duration:** ~53 min

**What it covers:**
- Building scalable KG ingestion pipeline
- Text splitter component for large documents
- Pipeline architecture with connected components
- Production-ready patterns

**Key code pattern - Pipeline with Components:**

```python
from neo4j_graphrag.experimental.pipeline import Pipeline, Component, DataModel
from neo4j_graphrag.experimental.components.text_splitters.fixed_size_splitter import FixedSizeSplitter
from neo4j_graphrag.experimental.components.entity_relation_extractor import LLMEntityRelationExtractor
from neo4j_graphrag.experimental.components.kg_writer import Neo4jWriter

# Create pipeline
pipeline = Pipeline()

# Add components
pipeline.add_component(FixedSizeSplitter(chunk_size=8000, chunk_overlap=100), "splitter")
pipeline.add_component(LLMEntityRelationExtractor(llm=llm), "extractor")
pipeline.add_component(Neo4jWriter(driver=driver), "writer")

# Connect components
pipeline.connect("splitter", "extractor", input_config={"chunks": "splitter.value"})
pipeline.connect("extractor", "writer", input_config={"graph": "extractor.value"})

# Run pipeline
result = await pipeline.run(data={"splitter": {"text": large_text}})
```

**Relevance:** Backend pipeline architecture, handling large transcripts

---

### 4. Agentic Patterns: Graph RAG Explained (Dec 2025)

**URL:** https://www.youtube.com/watch?v=0P-jlsHxVmY  
**Channel:** AI TL;DR  
**Duration:** 6 min

**Key Analogy:**
- **Librarian (Vector RAG):** Finds relevant documents, gives you clues - you connect the dots
- **Genealogist (Graph RAG):** Traces actual paths between entities, gives direct answers

**Key insight:**
> "Vector search gives you all the puzzle pieces scattered on the table, but it's still your job to put the puzzle together. Graph RAG traces the actual path between concepts."

**When GraphRAG wins:**
- "How is X related to Y?" questions
- Multi-hop reasoning
- Synthesising facts from multiple sources

**Relevance:** Architectural understanding, Librarian vs Builder roles

---

### 5. Building a GraphRAG App: Concepts & Demo (Dec 2025)

**URL:** https://www.youtube.com/watch?v=qqhvzq24WqE  
**Duration:** ~25 min

**Architecture covered:**
- LLM container (Llama 3 18B)
- Neo4j container
- FastAPI backend
- Next.js frontend

**Query Processing Flow:**
1. User asks natural language question
2. LLM analyzes question → extracts entities/relationships
3. Backend queries Neo4j graph with Cypher
4. Graph returns matching data (sub-millisecond)
5. LLM generates natural language response from graph data

**Key insight - Graph query speed:**
> "The time to query the graph is so fast it doesn't show up to 100th of a second. Super quick - that's the advantage of graph RAG versus relational joins."

**Cypher Pattern for Actor-Genre Query:**

```cypher
MATCH (a:Person)-[:ACTED_IN]->(m:Movie)-[:HAS_GENRE]->(g:Genre)
WHERE a.name = $actor AND g.name = $genre
RETURN m.title, m.description, m.vote
ORDER BY m.vote DESC
```

**Relevance:** Full stack architecture validation, Cypher patterns

---

### 6. GraphRAG vs LightRAG Cost Comparison (Dec 2025)

**URL:** https://www.youtube.com/watch?v=mGqpqPBEf-8  
**Channel:** Tech with Homayoun  
**Duration:** ~10 min

**Cost Comparison:**

| Aspect | GraphRAG (Microsoft) | LightRAG |
|--------|---------------------|----------|
| Query tokens | 610,000 | ~100 |
| API calls per query | Hundreds | 1 |
| Token savings | Baseline | **6,000x less** |
| Indexing cost | High | High (same) |
| Incremental updates | Rebuild everything | Append only |

**Key insight:**
> "The 6,000x token saving is in the QUERY phase, not indexing. Both need LLM calls for indexing."

**When to choose GraphRAG:**
- Budget is flexible
- Data is static
- Need global thematic queries

**When to choose LightRAG:**
- Cost matters (MVP, startup)
- Data changes frequently
- Need fast responses

**Relevance:** ADR-001 validation - LLM-only clustering makes sense for our scale

---

### 7. Knowledge-Centric Architectures for AI Agents (Dec 2025)

**URL:** https://www.youtube.com/watch?v=R9pK0OAsd78  
**Speaker:** Philip Rathle, CTO @ Neo4j  
**Event:** AI Conference 2025

**Top AI Challenges (Still True):**
1. AI hallucinates
2. AI is a black box
3. AI lacks discernment (access controls)
4. AI lacks context

**Knowledge Graph Types:**
- **Domain Graph:** Digital twin of real world (people, companies, products)
- **Lexical Graph:** Topology of vectors/chunks
- **Ontology Graph:** Meaning and categories
- **Memory Graph:** Working memory for agents (episodic, temporal)

**Key insight on LLMs + Cypher:**
> "Models are better at writing Cypher than SQL even though trained on more SQL - because Cypher is more terse and easier to write accurate queries."

**Enterprise Examples Mentioned:**
- **Walmart:** Career journey for 1.6M employees using graph pathfinding
- **Uber:** Business configuration graph for driver/service matching
- **LinkedIn:** 30% increased accuracy in customer service with graph RAG

**Knowledge Layer Concept:**
> "The knowledge layer turns raw silo data into connected, contextualized knowledge. Any agent has access to this knowledge."

**Free Tools Mentioned:**
- **LLM Graph Builder:** Free online tool for creating graphs from Wikipedia/PDF/YouTube
- **graphacademy.com:** Free courses
- **graphrag.com:** Definitions and examples

**Relevance:** Strategic validation of our architecture, enterprise patterns

---

## Training Courses (Free)

### Neo4j GraphAcademy

| Course | URL | Duration | Relevance |
|--------|-----|----------|-----------|
| Neo4j Fundamentals | graphacademy.neo4j.com | 2 hours | Phase A |
| Cypher Fundamentals | graphacademy.neo4j.com | 1 hour | Phase A |
| Intro to Vector Indexes | graphacademy.neo4j.com | 1 hour | Phase B |
| Building Apps with Python | graphacademy.neo4j.com/courses/app-python | 4 hours | Backend |

### Neo4j Official Videos

| Title | URL | Topics |
|-------|-----|--------|
| Full Stack GraphQL in the Cloud | neo4j.com/videos/training-series-full-stack-graphql-in-the-cloud | Next.js, Neo4j, Vercel |
| Building Neo4j-backed Chatbot | neo4j.com/developer/languages/javascript/tutorials | LangChain, TypeScript |

### Free eBook

**Full Stack GraphQL Applications**  
**URL:** https://go.neo4j.com/rs/710-RRC-335/images/Full_Stack_GraphQL_Applications_Neo4j.pdf  
**Topics:** GraphQL, React, Node.js, Neo4j integration

---

## Context7 Library IDs for Quick Access

When using Context7 MCP tools, use these IDs:

```
/neo4j/neo4j-graphrag-python     - GraphRAG implementation
/neo4j/graph-data-science-client - GDS algorithms
/neo4j/neo4j-python-driver       - Core driver
/langchain-ai/langchain-neo4j    - LangChain integration
/neo4j/neo4j-documentation       - General docs
/websites/neo4j_cypher-manual_25 - Cypher reference
```

---

## How to Use These Resources

### During Implementation

1. **Copy code from YouTube tutorials** - Tutorial 2 for entity extraction, Tutorial 3 for pipeline
2. **Reference GitHub repo** - https://github.com/ronidas39/neo4j-graphRag-Tutorial
3. **Use neo4j-graphrag-python Context7 ID** - For additional patterns

### During Learning

1. **Watch videos in order:** Tutorial 1 -> 2 -> 3 (progressive complexity)
2. **Complete GraphAcademy courses** - Neo4j Fundamentals, Cypher
3. **Read Neo4j CTO talk insights** - Enterprise architecture patterns

### During Architecture Decisions

1. **Reference GraphRAG vs LightRAG video** - Cost/performance trade-offs
2. **Check Neo4j CTO talk** - Knowledge layer concept, enterprise patterns
3. **Read research papers** - For advanced optimization

### Video Transcripts Available

All transcripts were extracted using MCP tools and contain:
- Actual working code (tested December 2025)
- Step-by-step implementation details
- Debugging tips from real coding sessions
- Architecture explanations with diagrams described

**To request a new transcript:** Ask the assistant to use `mcp_MCP_DOCKER_get_transcript` with the YouTube URL.

---

## Neo4j Implementation Examples (Session 2025-12-26)

Resources discovered during architecture validation. Useful for understanding patterns even though we're not using LangGraph ([ADR-006](./ADR/0006-async-agents-over-langgraph.md)).

### GitHub Repositories

| Repository | Focus | Relevance |
|------------|-------|-----------|
| [ps-genai-agents](https://github.com/neo4j-field/ps-genai-agents) | Generalised agent architecture with LangChain + Neo4j GraphRAG | Agent patterns (adapt for async) |
| [rag-demo](https://github.com/neo4j-examples/rag-demo) | Streamlit + LangChain + Neo4jVector | RAG pipeline patterns |
| [graphrag-customer-experience](https://github.com/neo4j-product-examples/graphrag-customer-experience) | GraphRAG for customer touchpoints | Multi-use-case patterns |
| [graphrag-kyc-agent](https://github.com/neo4j-product-examples/graphrag-kyc-agent) | OpenAI Agent SDK + Neo4j + MCP | Agent orchestration |
| [supply-chain-demo](https://github.com/neo4j-examples/supply-chain-demo) | Full app with complex relationships | Data modelling patterns |
| [nodejs-neo4j-realworld-example](https://github.com/neo4j-examples/nodejs-neo4j-realworld-example) | Express.js + Neo4j full-stack | CRUD, auth patterns |

### Neo4j Blog Articles

| Article | Topic | Relevance |
|---------|-------|-----------|
| [Function Calling in Agentic Workflows](https://neo4j.com/blog/developer/function-calling-agentic-workflows/) | Agentic workflow patterns | Tool selection, error handling |
| [Build Context-Aware GraphRAG Agent](https://neo4j.com/blog/genai/build-context-aware-graphrag-agent/) | Neo4j Aura Agent | GraphRAG agent patterns |
| [Building Graph-Aware Agents with MS Agent Framework](https://neo4j.com/labs/genai-ecosystem/ms-agent-framework/) | Agent integration patterns | SDK patterns, MCP server |

### GraphRAG Research Papers

| Paper | Key Insight | Link |
|-------|-------------|------|
| Graph Retrieval-Augmented Generation: A Survey (Aug 2024) | Foundational GraphRAG overview | [hf.co/papers/2408.08921](https://hf.co/papers/2408.08921) |
| HuixiangDou2 (Mar 2025) | Dual-level retrieval optimisation | [github.com/tpoisonooo/huixiangdou2](https://github.com/tpoisonooo/huixiangdou2) |
| Youtu-GraphRAG (Aug 2025) | 90% token cost savings | [hf.co/papers/2508.19855](https://hf.co/papers/2508.19855) |

### Redis Streams Resources

| Resource | Topic | Relevance |
|----------|-------|-----------|
| [redis-py streams notebook](https://github.com/redis/redis-py/blob/master/docs/examples/redis-stream-example.ipynb) | Consumer groups, XADD/XREAD | Core messaging pattern |
| [Redis Streams docs](https://redis.io/docs/data-types/streams/) | Official documentation | Reference |

---

## Updating This Document

When you find a useful resource:

```markdown
### [Resource Name]

**URL/ID:** [link or Context7 ID]
**Trust Score:** [if available]

**Key Insights:**
- [Point 1]
- [Point 2]

**Relevance:** [How it helps plasticFlower]
```


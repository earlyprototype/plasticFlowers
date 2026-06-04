# Neo4j GraphRAG and AI Development Investigation
**Date:** 31 December 2025  
**Sources:** YouTube video, Neo4j blog, Context7 documentation

---

## Executive Summary

This investigation covers Neo4j's new AI agent infrastructure, focusing on **Aura Agent** (GraphRAG platform) and the **Model Context Protocol (MCP)** server for Neo4j. These tools enable rapid development of knowledge-graph-backed AI agents with production-ready deployment capabilities.

---

## Key Topics Discovered

### 1. Neo4j Aura Agent Platform

**What it is:** An end-to-end, low-code/no-code platform for building, testing, and deploying GraphRAG agents in minutes.

**Status:** Early Access Program (EAP) - experimental, moving to GA later in 2025

**Key Features:**
- **Low-code agent creation** with visual UI
- **Built-in retrieval tools:**
  - Vector similarity search
  - Cypher templates (pre-defined graph queries)
  - Text-to-Cypher (natural language to query generation using fine-tuned Gemini 2.5)
- **Testing playground** with full observability
- **Secure REST API deployment** via Aura API
- **Multi-agent system support** (can be used as standalone or component)
- **Infrastructure managed** - no need to configure LLM providers, embeddings, or orchestration

**Supported Models:**
- Default: Gemini 2.5 Flash (provided out-of-the-box)
- Embeddings: OpenAI (text-embedding-ada), Google Gemini

**Availability:** Aura Free, Professional, and Business Critical tiers

**Blog Reference:** https://neo4j.com/blog/genai/build-context-aware-graphrag-agent/

---

### 2. Model Context Protocol (MCP) for Neo4j

**What it is:** An official, production-ready MCP server (written in Go, open source) that exposes Neo4j graph databases as tools to AI agents through the MCP standard.

**Status:** Beta (officially supported by Neo4j core engineering)

**Key Capabilities:**
- **Schema retrieval** - get graph structure
- **Cypher query execution** (read and write)
- **Pattern matching** capabilities
- **Multiple transport modes:**
  - `stdio` (for local/desktop use)
  - `http` (for web deployments)
  - `sse` (Server-Sent Events for legacy web clients)

**Repository:** https://github.com/neo4j-contrib/mcp-neo4j

**Integration Examples:**
- Claude Desktop (via stdio or HTTP)
- Docker deployments
- Multi-database namespaces

---

### 3. Context Engineering with Knowledge Graphs

**Core Concept from Video:** Graphs help manage context to boost accuracy, improve explainability, and future-proof AI systems.

**The Problem:**
- Vector search alone cannot scale for complex queries
- Generic semantic search hits limits (only retrieves top-k documents)
- No structured understanding of relationships
- Cannot perform aggregations or multi-hop reasoning

**The Solution:**
- **Knowledge graphs** organize data with explicit relationships
- **Pattern matching** (Cypher) enables precise, logical data retrieval
- **Entity extraction** from unstructured data creates structured knowledge
- **Combination of vector + graph** = optimal context fitting

**Example from Video:**
- Query: "How many Python developers do I have?"
- Vector-only: Returns 5 (just the limit of retrieved documents)
- Graph-based: Returns 28 (actual count from structured data)

---

### 4. GraphRAG Architecture Pattern

```
┌─────────────────┐
│   UI Layer      │  ← Enterprise search, knowledge assistant
│  (User facing)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Agent/LLM      │  ← OpenAI, Bedrock, Vertex AI
│  (Reasoning)    │  ← Aura Agent sits here
└────────┬────────┘
         │
         │  Tools (MCP)
         ▼
┌─────────────────┐
│ Knowledge Graph │  ← Neo4j
│  (Context Mgmt) │  ← Vector + Cypher + Schema
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Data Sources  │  ← Unstructured (docs) + Structured (CSV, SQL)
│  (Raw data)     │
└─────────────────┘
```

**Key Benefits:**
1. **Context optimization** - efficient retrieval
2. **Multi-hop reasoning** - complex relationship traversal
3. **Explainability** - clear retrieval logic
4. **Flexibility** - adaptable schema
5. **Accuracy** - structured understanding

---

### 5. Cypher Query Language & Templates

**Cypher:** Neo4j's declarative graph query language (similar to SQL for graphs)

**Pattern Matching Examples:**

```cypher
// Find people who built projects in specific domains
MATCH (person:Person)-[:BUILT]->(project:Project)-[:IN_DOMAIN]->(domain:Domain)
RETURN person, project, domain
LIMIT 20
```

```cypher
// Count Python developers
MATCH (person:Person)-[:KNOWS]->(skill:Skill {name: 'Python'})
RETURN count(person) AS pythonDevCount
```

```cypher
// Find similar people (skill overlap, project domains, work types)
MATCH (p1:Person), (p2:Person)
WHERE p1 <> p2
MATCH path = (p1)-[*1..4]-(p2)
WHERE NONE(r IN relationships(path) WHERE type(r) = 'KNOWS_PERSON')
RETURN p1, p2, count(path) AS similarityScore
ORDER BY similarityScore DESC
```

**Cypher Templates in Aura Agent:**
- Pre-defined patterns with parameters
- Subject-matter expertise encoded as graph logic
- Example: "Find similar employees for backfill"

**Text-to-Cypher:**
- Fine-tuned Gemini 2.5 model
- Converts natural language → Cypher
- Embedded in Aura Agent as a retrieval tool

---

### 6. Graph Schema Design for AI

**Best Practice from Video:** Start simple, iterate later

**Example Schema (Employee/Resume Data):**

```
(Person)
  ├─[:KNOWS]→(Skill)
  ├─[:BUILT|PUBLISHED|WON|MANAGED]→(Project)
  │                                    ├─[:IN_DOMAIN]→(WorkDomain)
  │                                    └─[:OF_TYPE]→(WorkType)
```

**Node Properties:**
- Text content (for embedding)
- Vector embeddings (for similarity search)
- Metadata (dates, identifiers, etc.)

**Design Principles:**
1. Don't migrate everything at once
2. Start with key entities and relationships
3. Add complexity as needed
4. Use consistent naming (snake_case for properties)
5. Define key properties for unique identification

---

### 7. Entity Extraction Process

**Pipeline:** Unstructured Documents → Entities → Knowledge Graph

**Steps:**
1. Parse documents (PDFs, résumés, etc.)
2. Use LLM to extract entities (people, skills, projects)
3. Identify relationships
4. Generate embeddings
5. Load into Neo4j

**From Documentation (Data Modeling MCP):**
```python
# Create nodes
node = Node(
    label="Person",
    properties=[
        Property(name="name", type="STRING", is_unique=True),
        Property(name="email", type="STRING"),
        Property(name="resume_text", type="STRING"),
        Property(name="embedding", type="LIST")
    ]
)

# Create relationships
relationship = Relationship(
    type="KNOWS",
    start_node_label="Person",
    end_node_label="Skill",
    properties=[
        Property(name="proficiency_level", type="STRING")
    ]
)
```

---

### 8. Aura Agent Implementation Details

**Creating an Agent (from video demo):**

1. **Navigate to Aura Console** → Agent Preview → Create
2. **Configure basics:**
   - Name
   - Description
   - Target database instance
   - Deployment type (internal/external)
3. **Add system prompt:**
   - Instructions on tool usage
   - Context about the knowledge graph
   - Guidelines for behaviour
4. **Add retrieval tools:**
   - **Vector similarity search**
     - Index name
     - Embedding model
     - Top-k results
   - **Text-to-Cypher**
     - Generic or task-specific prompts
   - **Cypher templates**
     - Pre-defined parameterised queries
     - Subject-matter expertise
5. **Test in playground:**
   - See full reasoning traces
   - View tool calls and results
   - Validate responses
6. **Deploy via API:**
   - OAuth2 authentication
   - REST endpoint
   - Full observability

**Example Agent Configuration:**

```json
{
  "name": "employee-agent",
  "description": "Conduct skills and talent search",
  "system_prompt": "You are an employee agent...",
  "target_instance": "employee-graph",
  "tools": [
    {
      "type": "vector_similarity",
      "name": "resume_search",
      "index": "text_embeddings",
      "embedding_model": "text-embedding-ada-002",
      "top_k": 5
    },
    {
      "type": "text_to_cypher",
      "name": "query_graph",
      "prompt": "Answer free-form questions and aggregations"
    },
    {
      "type": "cypher_template",
      "name": "find_similar_persons",
      "query": "MATCH (p1:Person {name: $person_name}), (p2:Person)..."
    }
  ]
}
```

---

### 9. MCP Server Integration Patterns

**Local Development (Claude Desktop):**

```json
{
  "mcpServers": {
    "neo4j-cypher": {
      "command": "uvx",
      "args": ["mcp-neo4j-cypher@0.3.0", "--transport", "stdio"],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "password",
        "NEO4J_DATABASE": "neo4j"
      }
    }
  }
}
```

**Docker Deployment:**

```yaml
services:
  neo4j:
    image: neo4j:5.26.1
    environment:
      - NEO4J_AUTH=neo4j/password
      - NEO4J_PLUGINS=["apoc"]
    ports:
      - "7474:7474"
      - "7687:7687"

  mcp-neo4j-cypher:
    image: mcp/neo4j-cypher:latest
    ports:
      - "8000:8000"
    environment:
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USERNAME=neo4j
      - NEO4J_PASSWORD=password
      - NEO4J_TRANSPORT=http
      - NEO4J_MCP_SERVER_HOST=0.0.0.0
      - NEO4J_MCP_SERVER_PORT=8000
```

**Multi-Agent System (from video):**
- Claude Desktop can call Aura Agent via wrapped MCP server
- Allows orchestration layer above specialised graph agents
- Example: Claude → Expert Agent Selector → Aura Agent (Employee DB)

---

### 10. LangChain Neo4j Integration

**Key Components:**

1. **Neo4jVector** - Vector store with hybrid search
2. **Neo4jGraph** - Graph database wrapper
3. **Neo4jChatMessageHistory** - Conversation memory
4. **GraphCypherQAChain** - Natural language → Cypher → Answer

**Example Usage:**

```python
from langchain_neo4j import Neo4jVector, Neo4jGraph, GraphCypherQAChain
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

# Vector store
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
vector_store = Neo4jVector.from_documents(
    docs,
    embeddings,
    url="bolt://localhost:7687",
    username="neo4j",
    password="password"
)

# Graph QA
graph = Neo4jGraph(url="bolt://localhost:7687", username="neo4j", password="password")
llm = ChatOpenAI(temperature=0)
chain = GraphCypherQAChain.from_llm(
    llm=llm,
    graph=graph,
    allow_dangerous_requests=True
)
response = chain.run("Who starred in Top Gun?")
```

---

### 11. Production Considerations

**From Video & Blog:**

**Aura Agent Advantages:**
- ✅ Fully managed infrastructure
- ✅ OAuth2 authentication
- ✅ Auto-scaling
- ✅ Built-in observability
- ✅ No LLM provider configuration needed
- ✅ Fast deployment (minutes vs weeks)

**MCP Server Advantages:**
- ✅ Official support
- ✅ Open source
- ✅ Multiple transport modes
- ✅ Docker-ready
- ✅ Multi-database support
- ✅ Integration with any MCP-compatible client

**Use Cases:**
- **Enterprise search** - knowledge assistants
- **Vertical AI** - pharma, legal, healthcare (specialised domains)
- **SaaS knowledge layers** - customer data understanding
- **Semantic retrieval** - enhanced context for LLMs
- **Long-term memory** - persistent agent memory in graphs

---

### 12. Comparison: Vector Search vs GraphRAG

| Aspect | Vector-Only | GraphRAG (Graph + Vector) |
|--------|-------------|---------------------------|
| **Retrieval** | Top-k semantic similarity | Pattern matching + similarity |
| **Aggregation** | ❌ Cannot count/aggregate | ✅ Full aggregation support |
| **Multi-hop** | ❌ No relationship traversal | ✅ Complex path queries |
| **Explainability** | ⚠️ Opaque (why these results?) | ✅ Clear query logic |
| **Accuracy** | ⚠️ Limited by context window | ✅ Structured understanding |
| **Flexibility** | ⚠️ Fixed embeddings | ✅ Evolving schema |
| **Context Optimisation** | ⚠️ Brute force retrieval | ✅ Intelligent graph patterns |

---

### 13. Key Takeaways from Video

**Zach Blumenfeld (Neo4j AI/ML Product Specialist):**

1. **"Regardless of how sophisticated your LLM or framework is, you won't scale with just vector search."**
   - Core problem: not managing context efficiently
   - Solution: Knowledge graphs organise data for optimal LLM consumption

2. **"You can start small with a simple schema and build on it later."**
   - No need to migrate everything immediately
   - Begin with key entities, iterate as requirements evolve

3. **"With Aura Agent, what took weeks can be done in hours or days."**
   - Low-code platform eliminates infrastructure complexity
   - Focus on building tools, not plumbing

4. **"Chain of thought reasoning naturally leads to multiple cipher queries."**
   - LLMs sequence queries logically
   - Graph structure supports this naturally

5. **"All the explanability component is there because everything is symbolically represented."**
   - Graph patterns are interpretable
   - Clear audit trail of reasoning

---

### 14. Learning Resources

**Official Documentation:**
- Neo4j Aura Agent tutorials: https://github.com/neo4j/docs-aura
- MCP Neo4j server: https://github.com/neo4j-contrib/mcp-neo4j
- Neo4j Aura API: https://neo4j.com/docs/aura/platform/api/specification/

**Events (from blog):**
- LinkedIn Live Event: 21 Oct 2025
- Workshop (Road to NODES): 23 Oct 2025
- NODES 2025 (graph community conference)

**GraphAcademy:**
- Free online courses
- Certifications
- 100K+ Neo4j experts

**Video Series:**
- Neo4j YouTube: https://www.youtube.com/@neo4j
- Playlist: "Build Reliable AI Faster With Aura Agent & Our New MCP Server"

**Community:**
- Neo4j Community Forum
- Data Science Community (for GDS)

---

### 15. Technical Specifications

**Aura Agent:**
- **Model:** Gemini 2.5 Flash (default, managed)
- **Embeddings:** OpenAI, Google Gemini
- **API:** REST with OAuth2
- **Deployment:** Aura API endpoints
- **Observability:** Full trace logs, tool calls, reasoning

**MCP Server:**
- **Language:** Go
- **License:** Open source
- **Transport:** stdio, http, sse
- **Tools:** `read_neo4j_cypher`, `write_neo4j_cypher`, `get_neo4j_schema`
- **Namespaces:** Multi-database support

**Neo4j Aura:**
- **Tiers:** Free, Professional, Business Critical
- **Regions:** Multi-cloud (GCP, AWS, Azure)
- **Features:** Fully managed, auto-scaling, enterprise security

---

### 16. Next Steps for Exploration

**For PlasticFlower Project:**

1. **Evaluate Aura Agent for transcript analysis:**
   - Could replace current agent orchestration
   - Built-in observability would simplify debugging
   - Consider EAP limitations (experimental status)

2. **Investigate MCP integration:**
   - Could expose transcript graph via MCP
   - Enable external tools (Claude, etc.) to query directly
   - Useful for development/debugging

3. **Schema design review:**
   - Current schema: `Session → Agent → Events → Transcript`
   - Consider: `Session → Conversation → Topics → Entities`
   - Add vector embeddings for hybrid search

4. **Cypher template patterns:**
   - "Find all reasoning traces for a session"
   - "Get agent collaboration patterns"
   - "Identify knowledge gaps in conversations"

5. **Text-to-Cypher exploration:**
   - Would enable natural language queries over transcript data
   - Could be valuable for user-facing features
   - Requires schema to be stable and well-documented

---

## Conclusion

Neo4j's Aura Agent and MCP server represent a significant step toward making GraphRAG accessible and production-ready. The combination of:

- **Managed infrastructure** (no LLM/embedding provider setup)
- **Low-code tooling** (visual agent builder)
- **Production-ready APIs** (OAuth2, observability)
- **Open standards** (MCP)
- **Flexible integration** (standalone or multi-agent)

...makes knowledge-graph-backed AI systems feasible for rapid prototyping and enterprise deployment.

The key insight: **Graphs don't replace vectors; they complement them.** Vector search finds semantically similar content, while graphs provide structure, relationships, and context that enable accurate, explainable, and scalable AI systems.

---

**Document Version:** 1.0  
**Last Updated:** 31 December 2025  
**Investigator:** AI Assistant (Claude Sonnet 4.5)


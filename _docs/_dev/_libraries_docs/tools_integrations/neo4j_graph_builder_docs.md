# Neo4j LLM Graph Builder Documentation

## Overview
The Neo4j LLM Graph Builder is a no-code tool that transforms unstructured data (text, PDFs, web pages) into structured knowledge graphs in Neo4j using Large Language Models (LLMs). It provides an intuitive interface for extracting entities, relationships, and properties from documents without writing code.

## Core Capabilities

### Supported Data Sources
- **PDFs**: Technical docs, research papers, books
- **Text Files**: Plain text, Markdown
- **Web Pages**: URLs, HTML content
- **Wikipedia**: Articles via URL
- **YouTube**: Video metadata and transcripts

### LLM Providers
- **OpenAI**: GPT-4, GPT-4o, GPT-3.5-turbo
- **Azure OpenAI**: Enterprise deployments
- **Anthropic**: Claude models
- **Google**: Gemini models
- **Vertex AI**: Google Cloud AI Platform
- **Bedrock**: AWS managed AI services
- **Groq**: Fast inference

### Extraction Features
- **Entity Recognition**: People, organizations, locations, concepts
- **Relationship Extraction**: Connections between entities
- **Property Extraction**: Attributes and metadata
- **Schema Enforcement**: Predefined or dynamic schemas
- **Batch Processing**: Handle multiple documents

## Getting Started

### Prerequisites
- **Neo4j Database**: Local instance, Aura, or server
- **API Keys**: For chosen LLM provider (OpenAI, etc.)
- **Browser**: Modern web browser

### Installation

#### Option 1: Neo4j Desktop
1. Open Neo4j Desktop
2. Go to Graph Apps tab
3. Search "LLM Graph Builder"
4. Install application
5. Select database and launch

#### Option 2: Docker

```bash
git clone https://github.com/neo4j-labs/llm-graph-builder.git
cd llm-graph-builder
docker-compose up
```

Access at `http://localhost:8080`

#### Option 3: Local Development

```bash
git clone https://github.com/neo4j-labs/llm-graph-builder.git
cd llm-graph-builder

# Install frontend dependencies
cd frontend
npm install
npm run dev

# Install backend dependencies (separate terminal)
cd backend
pip install -r requirements.txt
python main.py
```

### Configuration

**Environment Variables:**
```bash
# Neo4j Connection
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password

# LLM Provider (choose one)
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GOOGLE_API_KEY=your_google_key

# Optional
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-4o
```

## User Interface Workflow

### 1. Connect to Database

On launch:
- Enter Neo4j connection details
- Test connection
- Select or create database

### 2. Choose LLM Provider

Configure:
- **Provider**: OpenAI, Anthropic, Google, etc.
- **Model**: gpt-4o, claude-3-opus, gemini-pro
- **Temperature**: 0.0 (precise) to 1.0 (creative)
- **Max Tokens**: Response length limit

### 3. Upload Documents

**Supported Methods:**
- **File Upload**: Drag & drop PDFs, text files
- **URL Input**: Paste web page or Wikipedia URL
- **YouTube**: Enter video URL for transcript extraction

### 4. Define Schema (Optional)

**Predefined Schema:**
```json
{
  "entities": [
    {"label": "Person", "properties": ["name", "role", "email"]},
    {"label": "Company", "properties": ["name", "industry", "founded"]},
    {"label": "Product", "properties": ["name", "description", "price"]}
  ],
  "relationships": [
    {"type": "WORKS_AT", "from": "Person", "to": "Company"},
    {"type": "MANUFACTURES", "from": "Company", "to": "Product"}
  ]
}
```

**Dynamic Schema:**
- Let LLM infer entities and relationships
- Review and refine after initial extraction

### 5. Process & Extract

Click "Generate Graph":
- LLM analyses documents
- Extracts entities and relationships
- Displays progress and logs
- Shows entity counts by type

### 6. Visualise & Explore

**Graph View:**
- Interactive Cytoscape-based visualisation
- Click nodes/edges to view properties
- Expand/collapse subgraphs
- Apply layout algorithms

**Data Table:**
- Tabular view of extracted entities
- Filter by type, properties
- Edit/delete entities
- Export to CSV

### 7. Refine & Iterate

**Edit Entities:**
- Modify properties
- Merge duplicate entities
- Delete incorrect extractions

**Re-process:**
- Adjust LLM parameters
- Refine schema
- Re-run extraction on selected docs

## Features in Detail

### Schema Management

**Create Custom Schema:**
1. Schema Editor tab
2. Define entity labels and properties
3. Define relationship types
4. Save schema template

**Example Schema:**
```json
{
  "entities": [
    {
      "label": "Author",
      "properties": ["name", "affiliation", "email"]
    },
    {
      "label": "Paper",
      "properties": ["title", "abstract", "year", "doi"]
    },
    {
      "label": "Concept",
      "properties": ["term", "definition"]
    }
  ],
  "relationships": [
    {"type": "AUTHORED", "from": "Author", "to": "Paper"},
    {"type": "REFERENCES", "from": "Paper", "to": "Paper"},
    {"type": "DISCUSSES", "from": "Paper", "to": "Concept"}
  ]
}
```

### Batch Processing

**Process Multiple Documents:**
1. Upload multiple files simultaneously
2. Select all or specific docs
3. Click "Process All"
4. Monitor individual document progress

**Benefits:**
- Consistent schema across documents
- Entity deduplication across docs
- Relationship linking between documents

### Post-Processing

**Entity Resolution:**
- Detect and merge duplicate entities
- Fuzzy matching on names
- Manual merge interface

**Relationship Validation:**
- Review extracted relationships
- Confirm or reject suggestions
- Add manual relationships

**Property Enrichment:**
- Add missing properties
- Normalise values (dates, numbers)
- Categorise entities

## Use Cases

### 1. Research Literature Review

**Input:**
- PDFs of academic papers

**Schema:**
- Entities: `Author`, `Paper`, `Concept`, `Method`, `Dataset`
- Relationships: `AUTHORED`, `REFERENCES`, `USES_METHOD`, `EVALUATES_ON`

**Workflow:**
1. Upload 20 research PDFs
2. Define schema with research entities
3. Process all documents
4. Explore citation network
5. Identify key concepts and methods

### 2. Company Knowledge Base

**Input:**
- Internal documents, wikis, meeting notes

**Schema:**
- Entities: `Employee`, `Project`, `Department`, `Technology`
- Relationships: `WORKS_ON`, `BELONGS_TO`, `USES_TECH`, `REPORTS_TO`

**Workflow:**
1. Upload company documentation
2. Extract organizational structure
3. Map project dependencies
4. Create company knowledge graph

### 3. Legal Document Analysis

**Input:**
- Contracts, case files, statutes

**Schema:**
- Entities: `Person`, `Company`, `Clause`, `Obligation`, `Date`
- Relationships: `PARTY_TO`, `CONTAINS_CLAUSE`, `REFERENCES`

**Workflow:**
1. Upload legal documents
2. Extract parties and obligations
3. Link related contracts
4. Analyse compliance requirements

### 4. Customer Support Knowledge Graph

**Input:**
- Support tickets, documentation, FAQs

**Schema:**
- Entities: `Customer`, `Issue`, `Product`, `Solution`
- Relationships: `REPORTED`, `RELATED_TO`, `RESOLVED_BY`

**Workflow:**
1. Import ticket history and docs
2. Extract common issues and solutions
3. Link products to frequent problems
4. Build searchable knowledge base

## Advanced Features

### Chat Interface

Ask questions about extracted graph:

**Example Queries:**
- "Who are the top 5 authors by paper count?"
- "What concepts are most discussed in 2023 papers?"
- "Find papers connecting machine learning and healthcare"

**Behind the Scenes:**
- Natural language → Cypher query
- Execute on Neo4j
- Return results in conversational format

### Vector Embeddings

Enable semantic search:

**Setup:**
1. Enable "Generate Embeddings" option
2. Choose embedding model (OpenAI, Vertex AI)
3. Create vector index on entities

**Usage:**
```cypher
// Semantic search
CALL db.index.vector.queryNodes('entity_embeddings', 5, $query_vector)
YIELD node, score
RETURN node.name, score
```

### Export Options

**Export Formats:**
- **Cypher Script**: Recreate graph in another Neo4j instance
- **GraphML**: For use in other graph tools (Gephi, Cytoscape)
- **JSON**: Graph structure as JSON
- **CSV**: Tabular entity/relationship data

**Example Export:**
```cypher
// Export to Cypher
MATCH (n)-[r]->(m)
RETURN n, r, m
```

### API Integration

**Programmatic Access:**

```python
import requests

# Submit document for processing
response = requests.post('http://localhost:8080/api/process', json={
    'file_url': 'https://example.com/document.pdf',
    'schema': {...},
    'llm_model': 'gpt-4o'
})

job_id = response.json()['job_id']

# Check processing status
status = requests.get(f'http://localhost:8080/api/status/{job_id}')
print(status.json())
```

## Best Practices

1. **Schema Design**: Define schema upfront for consistent extraction
2. **LLM Selection**: Use GPT-4 for complex docs; GPT-3.5 for simple text
3. **Chunk Size**: Break large PDFs into sections for better extraction
4. **Validation**: Always review and validate LLM-extracted data
5. **Embeddings**: Enable for semantic search use cases
6. **Batching**: Process related documents together for cross-linking
7. **Deduplication**: Regularly merge duplicate entities
8. **Backup**: Export graphs before major re-processing

## Limitations

1. **LLM Accuracy**: Not 100% accurate; requires validation
2. **Cost**: API costs for large document sets (OpenAI/Anthropic)
3. **Complex Schemas**: Deep nested structures may be challenging
4. **Language Support**: Best with English; varies for other languages
5. **PDF Quality**: OCR issues with scanned/low-quality PDFs
6. **Rate Limits**: LLM API rate limits may slow processing

## Troubleshooting

### Common Issues

**"Failed to extract entities":**
- Check LLM API key validity
- Verify API quota/rate limits
- Try simpler schema or smaller document

**"Duplicate entities created":**
- Enable entity resolution
- Use stricter matching rules
- Manually merge via UI

**"Graph not visible":**
- Check Neo4j connection
- Verify database has data: `MATCH (n) RETURN count(n)`
- Refresh browser

**"Slow processing":**
- Reduce chunk size
- Use faster LLM model (GPT-3.5 vs GPT-4)
- Process fewer documents simultaneously

## Resources

- **GitHub**: https://github.com/neo4j-labs/llm-graph-builder
- **Demo Video**: https://www.youtube.com/neo4j
- **Neo4j Community**: https://community.neo4j.com/
- **Documentation**: https://neo4j.com/labs/llm-graph-builder/






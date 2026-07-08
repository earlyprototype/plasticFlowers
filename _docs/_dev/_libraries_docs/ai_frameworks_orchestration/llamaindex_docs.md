# LlamaIndex Python Documentation

## Overview
LlamaIndex is a data framework for building LLM-powered applications, specialising in Retrieval-Augmented Generation (RAG) and agentic workflows. It provides tools for data ingestion, indexing, querying, and building sophisticated agents that can interact with external data sources.

## Core Capabilities

### Data Ingestion & Document Loading
- **SimpleDirectoryReader**: Load documents from local directories
- **DoclingReader**: Advanced document parsing with Markdown export
- **WebPageReader**: Extract content from web pages
- **DatabaseReader**: Connect to SQL databases, Elasticsearch, Redis
- **Cloud Storage**: Google Drive, S3, Azure Blob

### Indexing & Vector Stores
- **VectorStoreIndex**: Primary index for semantic search
- **SummaryIndex**: For summarisation tasks
- **Knowledge Graphs**: Neo4j property graph integration
- **Multi-Modal**: Image and text indexing

### Query Engines
- **Basic Query Engine**: Single-index querying
- **SubQuestionQueryEngine**: Break complex queries into sub-questions
- **RetrieverQueryEngine**: Custom retrievers with LLM synthesis
- **Multi-Document Agents**: Agent-based document routing

## RAG Workflows

### Basic RAG Pipeline

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

# Load documents
documents = SimpleDirectoryReader("./data").load_data()

# Create index
index = VectorStoreIndex.from_documents(documents)

# Query
query_engine = index.as_query_engine()
response = query_engine.query("What is the main topic?")
print(response)
```

### Advanced RAG with Metadata Extraction

```python
from llama_index.core import VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.ingestion import IngestionPipeline

# Setup ingestion pipeline
pipeline = IngestionPipeline(
    transformations=[
        SentenceSplitter(chunk_size=512, chunk_overlap=20),
        # Add metadata extractors here
    ]
)

# Process documents
nodes = pipeline.run(documents=documents)

# Build index
index = VectorStoreIndex(nodes)
query_engine = index.as_query_engine(similarity_top_k=3)
```

### RAG with Custom Retriever

```python
from llama_index.core.query_engine import CustomQueryEngine
from llama_index.core.retrievers import BaseRetriever
from llama_index.core import get_response_synthesizer

class RAGQueryEngine(CustomQueryEngine):
    """Custom RAG Query Engine."""
    
    retriever: BaseRetriever
    response_synthesizer: BaseSynthesizer
    
    def custom_query(self, query_str: str):
        nodes = self.retriever.retrieve(query_str)
        response_obj = self.response_synthesizer.synthesize(query_str, nodes)
        return response_obj
```

## Agents

### ReAct Agent with Tools

```python
from llama_index.core.agent.workflow import ReActAgent
from llama_index.core.workflow import Context
from llama_index.core.tools import QueryEngineTool

# Create query engine tools
lyft_tool = QueryEngineTool.from_defaults(
    query_engine=lyft_engine,
    name="lyft_10k",
    description="Provides Lyft financials for 2021"
)

uber_tool = QueryEngineTool.from_defaults(
    query_engine=uber_engine,
    name="uber_10k",
    description="Provides Uber financials for 2021"
)

# Setup agent
agent = ReActAgent(
    tools=[lyft_tool, uber_tool],
    llm=OpenAI(model="gpt-4o-mini"),
    system_prompt="You are a financial analyst assistant."
)

# Run agent
ctx = Context(agent)
handler = agent.run("Compare Lyft and Uber revenue growth in 2021", ctx=ctx)

async for ev in handler.stream_events():
    if isinstance(ev, AgentStream):
        print(f"{ev.delta}", end="", flush=True)

response = await handler
```

### Multi-Document Agents

```python
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core import VectorStoreIndex, SummaryIndex
from llama_index.core.tools import QueryEngineTool

async def build_agent_per_doc(nodes, file_base):
    # Build vector and summary indexes
    vector_index = VectorStoreIndex(nodes)
    summary_index = SummaryIndex(nodes)
    
    # Define query engines
    vector_query_engine = vector_index.as_query_engine(llm=llm)
    summary_query_engine = summary_index.as_query_engine(
        response_mode="tree_summarize", 
        llm=llm
    )
    
    # Create tools
    query_engine_tools = [
        QueryEngineTool.from_defaults(
            query_engine=vector_query_engine,
            name=f"vector_tool_{file_base}",
            description="Useful for specific facts"
        ),
        QueryEngineTool.from_defaults(
            query_engine=summary_query_engine,
            name=f"summary_tool_{file_base}",
            description="Useful for summarisation"
        )
    ]
    
    # Build agent
    agent = FunctionAgent(
        tools=query_engine_tools,
        llm=OpenAI(model="gpt-4"),
        system_prompt=f"You are specialized in {file_base}"
    )
    
    return agent
```

## Data Connectors

### Google Drive Integration

```python
from llama_index.readers.google import GoogleDriveReader

reader = GoogleDriveReader()
documents = reader.load_data(folder_id="your-folder-id")

# Build index
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()
```

### SQL Database Integration

```python
from llama_index.core import SQLDatabase
from sqlalchemy import create_engine

engine = create_engine("postgresql://user:password@localhost/dbname")
sql_database = SQLDatabase(engine, include_tables=["users", "orders"])

# Query using natural language
query_engine = sql_database.as_query_engine()
response = query_engine.query("How many users signed up last month?")
```

## Ingestion Pipelines

### Basic Pipeline

```python
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import TokenTextSplitter

pipeline = IngestionPipeline(
    transformations=[
        TokenTextSplitter(chunk_size=1024, chunk_overlap=20),
        # Add embeddings, metadata extractors
    ]
)

nodes = pipeline.run(documents=documents)
```

### Pipeline with Caching

```python
from llama_index.storage.kvstore.redis import RedisCache
from llama_index.core.ingestion import IngestionCache, IngestionPipeline

# Set up caching
cache = IngestionCache(
    cache=RedisCache.from_host_and_port("localhost", 6379),
    collection="redis_cache"
)

pipeline = IngestionPipeline(
    transformations=[SentenceSplitter()],
    cache=cache
)

# Incremental processing
nodes = pipeline.run(documents=docs)
```

### Direct Vector Store Ingestion

```python
from llama_index.core.ingestion import IngestionPipeline
from llama_index.vector_stores.qdrant import QdrantVectorStore

vector_store = QdrantVectorStore(client=client, collection_name="docs")

pipeline = IngestionPipeline(
    transformations=[SentenceSplitter()],
    vector_store=vector_store
)

# Documents ingested directly to vector store
pipeline.run(documents=documents)
```

## Vector Stores

### Qdrant

```python
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6333)

vector_store = QdrantVectorStore(
    client=client,
    collection_name="documents"
)

index = VectorStoreIndex.from_vector_store(vector_store)
```

### Pinecone

```python
from llama_index.vector_stores.pinecone import PineconeVectorStore
import pinecone

pc = pinecone.Pinecone(api_key="your-api-key")
index = pc.Index("quickstart")

vector_store = PineconeVectorStore(pinecone_index=index)
index = VectorStoreIndex.from_vector_store(vector_store)
```

### PostgreSQL (pgvector)

```python
from llama_index.vector_stores.postgres import PGVectorStore

vector_store = PGVectorStore.from_params(
    database="vector_db",
    host="localhost",
    password="password",
    port=5432,
    user="postgres",
    table_name="embeddings",
    embed_dim=1536
)
```

## Query Engines

### Sub-Question Query Engine

```python
from llama_index.core.query_engine import SubQuestionQueryEngine
from llama_index.core.tools import QueryEngineTool

# Define individual query engines
vector_tool = QueryEngineTool.from_defaults(
    query_engine=vector_query_engine,
    name="documents",
    description="Paul Graham essays"
)

# Combine into sub-question engine
query_engine = SubQuestionQueryEngine.from_defaults(
    query_engine_tools=[vector_tool],
    use_async=True
)

response = query_engine.query(
    "How was Paul Graham's life different before, during, and after YC?"
)
```

### Custom Query Engine

```python
from llama_index.core.query_engine import CustomQueryEngine

class MyQueryEngine(CustomQueryEngine):
    def custom_query(self, query_str: str):
        # Custom query logic
        nodes = self.retriever.retrieve(query_str)
        response = self.response_synthesizer.synthesize(query_str, nodes)
        return response
```

## Multi-Modal RAG

### Image and Text Indexing

```python
from llama_index.multi_modal_llms.openai import OpenAIMultiModal
from llama_index.core import PromptTemplate

# Define QA prompt
qa_tmpl_str = (
    "Images are provided.\n"
    "---------------------\n"
    "{context_str}\n"
    "---------------------\n"
    "Query: {query_str}\n"
    "Answer: "
)
qa_tmpl = PromptTemplate(qa_tmpl_str)

# Define multimodal LLM
openai_mm_llm = OpenAIMultiModal(
    model="gpt-4o",
    max_new_tokens=300
)

# Create query engine
query_engine = index.as_query_engine(
    llm=openai_mm_llm,
    text_qa_template=qa_tmpl
)
```

## Knowledge Graphs

### Neo4j Property Graph

```python
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore
from llama_index.core import PropertyGraphIndex

# Setup Neo4j connection
graph_store = Neo4jPropertyGraphStore(
    username="neo4j",
    password="password",
    url="bolt://localhost:7687"
)

# Build property graph index
index = PropertyGraphIndex.from_documents(
    documents,
    property_graph_store=graph_store,
    show_progress=True
)

# Query with graph reasoning
query_engine = index.as_query_engine(include_text=True)
response = query_engine.query("What happened at Interleaf?")
```

## Evaluation

### RAGChecker

```python
from llama_index.core.evaluation import RAGChecker

# Load documents and create query engine
documents = SimpleDirectoryReader("docs/").load_data()
index = VectorStoreIndex.from_documents(documents)
rag_application = index.as_query_engine()

# Setup evaluator
evaluator = RAGChecker()

# Evaluate responses
queries = ["What is the main topic?", "Summarise the key points"]
for query in queries:
    response = rag_application.query(query)
    eval_result = evaluator.evaluate(response)
    print(f"Score: {eval_result.score}")
```

## Workflows

### LongRAG Workflow

```python
from llama_index.core.workflow import Workflow, step, StartEvent, StopEvent

class LongRAGWorkflow(Workflow):
    @step
    async def ingest(self, ev: StartEvent):
        # Load and chunk documents
        docs = load_documents(ev.get("data_dir"))
        nodes = split_documents(docs, ev.get("chunk_size"))
        
        # Build index
        index = VectorStoreIndex(nodes)
        return LoadNodeEvent(nodes=nodes, index=index)
    
    @step
    async def make_query_engine(self, ctx: Context, ev: LoadNodeEvent):
        # Create retriever and query engine
        retriever = LongRAGRetriever(ev.nodes, ev.index.vector_store)
        query_eng = RetrieverQueryEngine.from_args(retriever, llm)
        return StopEvent(result={"query_engine": query_eng})
```

## Multi-Tenancy

### User-Specific Filtering

```python
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter

# Add user metadata to documents
for document in documents_jerry:
    document.metadata["user"] = "Jerry"

# Ingest documents
nodes = pipeline.run(documents=documents_jerry)
index.insert_nodes(nodes)

# Create user-specific query engine
jerry_query_engine = index.as_query_engine(
    filters=MetadataFilters(
        filters=[ExactMatchFilter(key="user", value="Jerry")]
    ),
    similarity_top_k=3
)

response = jerry_query_engine.query("What papers do I have access to?")
```

## Embeddings

### OpenAI

```python
from llama_index.embeddings.openai import OpenAIEmbedding

embed_model = OpenAIEmbedding(model="text-embedding-3-large")
```

### HuggingFace Local

```python
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

embed_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/all-mpnet-base-v2"
)
```

### Voyage AI

```python
from llama_index.embeddings.voyageai import VoyageAIEmbedding

embed_model = VoyageAIEmbedding(model="voyage-3")
```

## Persistence

### Save and Load Index

```python
from llama_index.core import StorageContext, load_index_from_storage

# Save index
index.storage_context.persist("./storage")

# Load index
storage_context = StorageContext.from_defaults(persist_dir="./storage")
index = load_index_from_storage(storage_context)
query_engine = index.as_query_engine()
```

## Observability

### LangSmith Integration

```python
import os

os.environ["LANGSMITH_API_KEY"] = "your-key"
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "LlamaIndex Project"

# All queries automatically traced
query_engine = index.as_query_engine()
response = query_engine.query("What is the main topic?")
```

### Uprain Evaluation

```python
from llama_index.core.evaluation.uptrain import UpTrainEvaluator

evaluator = UpTrainEvaluator()

# Evaluate context relevance, factual accuracy, response completeness
queries = ["What did Paul Graham do growing up?"]
for query in queries:
    response = query_engine.query(query)
    # Automatic evaluation logged via callback
```

## Best Practices

1. **Chunk Size**: Start with 512-1024 characters; adjust based on domain
2. **Overlap**: 10-20% overlap prevents context loss at boundaries
3. **Top-K**: Use 3-5 for most queries; higher values add noise
4. **Metadata**: Rich metadata enables powerful filtering and routing
5. **Caching**: Use Redis/file cache for incremental ingestion
6. **Persistence**: Always persist indexes for production use
7. **Multi-Document**: Use agent-based routing for large document collections
8. **Evaluation**: Regularly evaluate RAG quality with multiple metrics

## Installation

```bash
pip install llama-index
pip install llama-index-vector-stores-qdrant  # Vector store
pip install llama-index-embeddings-openai      # Embeddings
pip install llama-index-readers-google         # Google Drive
pip install llama-index-graph-stores-neo4j     # Neo4j integration
```

## Resources

- **Documentation**: https://docs.llamaindex.ai/
- **GitHub**: https://github.com/run-llama/llama_index
- **Community**: https://discord.gg/llamaindex






# LangChain Python Documentation

## Overview
LangChain is a framework for developing applications powered by large language models (LLMs). It simplifies every stage of the LLM application lifecycle with open-source components, third-party integrations, and tools for building agents, RAG pipelines, and complex workflows.

## Core Capabilities

### Retrieval-Augmented Generation (RAG)
- **Document Loading**: WebBaseLoader, SimpleDirectoryReader
- **Text Splitting**: RecursiveCharacterTextSplitter with configurable chunk sizes
- **Vector Stores**: Qdrant, Pinecone, ChromaDB, PostgreSQL, Neo4j
- **Embedding Models**: OpenAI, Voyage AI, Azure OpenAI, Cohere, HuggingFace

### Agents & Tools
- **ReAct Agents**: Reasoning and action loops
- **Function Calling**: Structured tool use with LLMs
- **Multi-Agent Systems**: Supervisor patterns, agent delegation
- **Tool Decorators**: `@tool` for defining custom tools

### Memory & State Management
- **Short-term Memory**: InMemorySaver checkpointer for conversation context
- **Long-term Memory**: InMemoryStore, PostgreSQL for persistent storage
- **State Updates**: AgentState customization, Command for state mutations

## RAG Implementation Patterns

### Basic RAG Pipeline

```python
from langchain.agents import create_agent
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.tools import tool

# Load and chunk documents
loader = WebBaseLoader(web_paths=("https://example.com/doc",))
docs = loader.load()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
all_splits = text_splitter.split_documents(docs)

# Index chunks in vector store
_ = vector_store.add_documents(documents=all_splits)

# Define retrieval tool
@tool(response_format="content_and_artifact")
def retrieve_context(query: str):
    """Retrieve information to help answer a query."""
    retrieved_docs = vector_store.similarity_search(query, k=2)
    serialized = "\n\n".join(
        f"Source: {doc.metadata}\nContent: {doc.page_content}"
        for doc in retrieved_docs
    )
    return serialized, retrieved_docs

# Create RAG agent
agent = create_agent(
    model,
    tools=[retrieve_context],
    system_prompt="Use the tool to retrieve context and answer queries."
)
```

### Advanced RAG with Agentic Retrieval

```python
@tool
def fetch_documentation(url: str) -> str:
    """Fetch and convert documentation from a URL"""
    if not any(url.startswith(domain) for domain in ALLOWED_DOMAINS):
        return "Error: URL not allowed"
    response = requests.get(url, timeout=10.0)
    return markdownify(response.text)

agent = create_agent(
    model="claude-sonnet-4-0",
    tools=[fetch_documentation],
    system_prompt="""
    You are an expert assistant. When unsure about technical details,
    use fetch_documentation to consult official sources before answering.
    """
)
```

## Agent Creation & Tools

### Defining Custom Tools

```python
from langchain.tools import tool, ToolRuntime

@tool
def search(query: str) -> str:
    """Search for information."""
    return f"Results for: {query}"

@tool
def get_user_info(runtime: ToolRuntime[Context]) -> str:
    """Look up user info using runtime context."""
    user_id = runtime.context.user_id
    store = runtime.store
    user_info = store.get(("users",), user_id)
    return str(user_info.value) if user_info else "Unknown user"

agent = create_agent(
    model="gpt-4o",
    tools=[search, get_user_info],
    store=InMemoryStore(),
    context_schema=Context
)
```

### Multi-Agent Systems

#### Tool Calling Pattern

```python
# Define sub-agents
calendar_agent = create_agent(model, tools=[create_calendar_event])
email_agent = create_agent(model, tools=[send_email])

# Wrap sub-agents as tools
@tool
def schedule_event(request: str) -> str:
    """Schedule calendar events using natural language."""
    result = calendar_agent.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    return result["messages"][-1].text

@tool
def manage_email(request: str) -> str:
    """Send emails using natural language."""
    result = email_agent.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    return result["messages"][-1].text

# Create supervisor
supervisor = create_agent(
    model,
    tools=[schedule_event, manage_email],
    system_prompt="You are a helpful personal assistant."
)
```

## Memory & State

### Short-term Memory (Checkpointers)

```python
from langgraph.checkpoint.memory import InMemorySaver

agent = create_agent(
    "gpt-4o",
    tools=[get_user_info],
    checkpointer=InMemorySaver()
)

# First conversation
agent.invoke(
    {"messages": [{"role": "user", "content": "Hi! My name is Bob."}]},
    {"configurable": {"thread_id": "1"}}
)

# Continue conversation
agent.invoke(
    {"messages": [{"role": "user", "content": "What's my name?"}]},
    {"configurable": {"thread_id": "1"}}
)
```

### Long-term Memory (Store)

```python
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()

# Write to store
store.put(
    ("users",),  # namespace
    "user_123",  # key
    {"name": "John Smith", "language": "English"}  # value
)

@tool
def get_user_info(runtime: ToolRuntime[Context]) -> str:
    """Look up user info."""
    user_id = runtime.context.user_id
    user_info = runtime.store.get(("users",), user_id)
    return str(user_info.value) if user_info else "Unknown user"

agent = create_agent(
    model="gpt-4o",
    tools=[get_user_info],
    store=store,
    context_schema=Context
)
```

### State Updates from Tools

```python
from langgraph.types import Command

@tool
def update_user_info(runtime: ToolRuntime[Context, CustomState]) -> Command:
    """Look up and update user info."""
    user_id = runtime.context.user_id
    name = "John Smith" if user_id == "user_123" else "Unknown user"
    return Command(update={
        "user_name": name,
        "messages": [ToolMessage("Successfully looked up user", tool_call_id=runtime.tool_call_id)]
    })

agent = create_agent(
    model="gpt-4o",
    tools=[update_user_info],
    state_schema=CustomState,
    context_schema=Context
)
```

## Middleware

### Dynamic Tool Selection

```python
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse

@wrap_model_call
def select_tools(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Select relevant tools based on context."""
    relevant_tools = select_relevant_tools(request.state, request.runtime)
    return handler(request.override(tools=relevant_tools))

agent = create_agent(
    model="gpt-4o",
    tools=all_tools,
    middleware=[select_tools]
)
```

### Human-in-the-Loop

```python
from langchain.agents.middleware import HumanInTheLoopMiddleware

agent = create_agent(
    model="gpt-4o",
    tools=[search_tool, send_email_tool, delete_database_tool],
    middleware=[
        HumanInTheLoopMiddleware(
            interrupt_on={
                "send_email": True,
                "delete_database": True,
                "search": False
            }
        )
    ],
    checkpointer=InMemorySaver()
)

# Will pause before executing sensitive tools
config = {"configurable": {"thread_id": "1"}}
result = agent.invoke(
    {"messages": [{"role": "user", "content": "Send an email"}]},
    config=config
)

# Resume with approval
agent.invoke(
    Command(resume={"decisions": [{"type": "approve"}]}),
    config=config
)
```

### Tool Call Monitoring

```python
from langchain.agents.middleware import wrap_tool_call

@wrap_tool_call
def monitor_tool(request: ToolCallRequest, handler: Callable) -> ToolMessage | Command:
    print(f"Executing: {request.tool_call['name']}")
    print(f"Arguments: {request.tool_call['args']}")
    try:
        result = handler(request)
        print("Tool completed successfully")
        return result
    except Exception as e:
        print(f"Tool failed: {e}")
        raise
```

## Vector Stores

### Qdrant Setup

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from langchain_qdrant import QdrantVectorStore

client = QdrantClient(":memory:")

vector_size = len(embeddings.embed_query("sample text"))

client.create_collection(
    collection_name="test",
    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
)

vector_store = QdrantVectorStore(
    client=client,
    collection_name="test",
    embedding=embeddings
)
```

## Embeddings

### OpenAI

```python
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
```

### Voyage AI

```python
from langchain_voyageai import VoyageAIEmbeddings

embeddings = VoyageAIEmbeddings(model="voyage-3")
```

### Azure OpenAI

```python
from langchain_openai import AzureOpenAIEmbeddings

embeddings = AzureOpenAIEmbeddings(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
    openai_api_version=os.environ["AZURE_OPENAI_API_VERSION"]
)
```

## Structured Output

```python
from pydantic import BaseModel
from langchain.agents.structured_output import ToolStrategy

class ContactInfo(BaseModel):
    name: str
    email: str
    phone: str

agent = create_agent(
    model="gpt-4o-mini",
    tools=[search_tool],
    response_format=ToolStrategy(ContactInfo)
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "Extract: John Doe, john@example.com, (555) 123-4567"}]
})

contact = result["structured_response"]
# ContactInfo(name='John Doe', email='john@example.com', phone='(555) 123-4567')
```

## Observability

### LangSmith Tracing

```bash
export LANGSMITH_API_KEY=<your-api-key>
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_PROJECT="My Project"
```

All agent execution steps, tool calls, and model interactions are automatically traced without code changes.

## Testing

### In-Memory Checkpointer for Tests

```python
from langgraph.checkpoint.memory import InMemorySaver

agent = create_agent(
    model,
    tools=[],
    checkpointer=InMemorySaver()
)

# Test state persistence
agent.invoke(HumanMessage(content="I live in Sydney"))
response = agent.invoke(HumanMessage(content="What's my local time?"))
# Agent remembers location from previous message
```

## SQL Agents

```python
from llama_index.core import SQLDatabase

sql_database = SQLDatabase(engine, include_tables=["city_stats"])

agent = create_agent(
    model="gpt-4o",
    tools=[sql_query_tool],
    system_prompt="You can query a SQL database to answer questions."
)

for step in agent.stream(
    {"messages": [{"role": "user", "content": "Which genre has the longest tracks?"}]},
    stream_mode="values"
):
    step["messages"][-1].pretty_print()
```

## Context Engineering

### Filter Tools by User Role

```python
@wrap_model_call
def context_based_tools(request: ModelRequest, handler: Callable) -> ModelResponse:
    """Filter tools based on user permissions."""
    user_role = request.runtime.context.user_role
    
    if user_role == "admin":
        pass  # All tools
    elif user_role == "editor":
        tools = [t for t in request.tools if t.name != "delete_data"]
        request = request.override(tools=tools)
    else:
        tools = [t for t in request.tools if t.name.startswith("read_")]
        request = request.override(tools=tools)
    
    return handler(request)

agent = create_agent(
    model="gpt-4o",
    tools=[read_data, write_data, delete_data],
    middleware=[context_based_tools],
    context_schema=Context
)
```

## Best Practices

1. **Tool Descriptions**: Write clear, detailed docstrings - they guide the LLM's tool selection
2. **Chunk Size**: Optimal chunk_size depends on your data; 1000 chars with 200 overlap is a good start
3. **Retrieval Quality**: Use k=2-5 for most queries; higher values add noise
4. **Memory Management**: Use checkpointers for conversation history, stores for long-term facts
5. **Error Handling**: Tools should return descriptive error messages, not raise exceptions
6. **Middleware Order**: Monitoring → Tool Selection → Human-in-the-Loop
7. **Production Storage**: Use PostgreSQL checkpointer instead of InMemorySaver
8. **Testing**: Use InMemorySaver in tests for reproducibility

## Installation

```bash
pip install langchain langchain-text-splitters langchain-community
pip install langchain-openai  # For OpenAI models
pip install langchain-voyageai  # For Voyage embeddings
pip install langchain-qdrant  # For Qdrant vector store
pip install langgraph-checkpoint-postgres  # For production memory
```

## Resources

- **Documentation**: https://docs.langchain.com/
- **GitHub**: https://github.com/langchain-ai/langchain
- **Community**: https://discord.gg/langchain






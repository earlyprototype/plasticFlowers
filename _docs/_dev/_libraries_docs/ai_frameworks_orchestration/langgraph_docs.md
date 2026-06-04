# LangGraph Documentation

## Overview
LangGraph is a low-level orchestration framework for building, managing, and deploying long-running, stateful agents and workflows. It provides durable execution, human-in-the-loop capabilities, and comprehensive memory management for complex agent systems.

## Core Capabilities

### State Management
- **MessagesState**: Built-in state for conversation history
- **Custom State**: Define your own state schemas
- **Persistence**: Checkpointers for durable execution
- **Streaming**: Real-time state updates

### Agent Orchestration
- **Graph-Based Workflows**: Define agent logic as directed graphs
- **Conditional Edges**: Dynamic routing based on state
- **Human-in-the-Loop**: Interrupts for approval workflows
- **Multi-Agent**: Coordinate multiple agents

## Basic Concepts

### Hello World Example

```python
from langgraph.graph import StateGraph, MessagesState, START, END

def mock_llm(state: MessagesState):
    return {"messages": [{"role": "ai", "content": "hello world"}]}

graph = StateGraph(MessagesState)
graph.add_node(mock_llm)
graph.add_edge(START, "mock_llm")
graph.add_edge("mock_llm", END)
graph = graph.compile()

result = graph.invoke({"messages": [{"role": "user", "content": "hi!"}]})
```

## State Management

### MessagesState

```python
from langgraph.graph import MessagesState

# Built-in state for conversations
state = MessagesState()
state["messages"] = [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"}
]
```

### Custom State

```python
from typing import TypedDict, Annotated
from langgraph.graph import add_messages

class CustomState(TypedDict):
    messages: Annotated[list, add_messages]
    user_id: str
    session_data: dict
```

## Graph Construction

### Basic Graph

```python
from langgraph.graph import StateGraph

def process_message(state):
    # Process state
    return {"messages": [...]}

graph = StateGraph(MessagesState)
graph.add_node("processor", process_message)
graph.add_edge(START, "processor")
graph.add_edge("processor", END)
app = graph.compile()
```

### Conditional Routing

```python
def should_continue(state):
    """Determine next node based on state"""
    if len(state["messages"]) > 10:
        return "summarize"
    return "continue"

graph.add_conditional_edges(
    "processor",
    should_continue,
    {
        "summarize": "summarizer",
        "continue": "responder"
    }
)
```

## Persistence

### In-Memory Checkpointer

```python
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()

graph = graph.compile(checkpointer=checkpointer)

# Run with thread ID for persistence
config = {"configurable": {"thread_id": "conversation-1"}}
result = graph.invoke({"messages": [...]}, config=config)
```

### PostgreSQL Checkpointer

```python
from langgraph.checkpoint.postgres import PostgresSaver

DB_URI = "postgresql://user:password@localhost:5432/dbname"

with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
    checkpointer.setup()
    graph = graph.compile(checkpointer=checkpointer)
```

## Human-in-the-Loop

### Interrupts

```python
from langgraph.graph import StateGraph

def approval_required(state):
    return state  # Execution pauses here

graph = StateGraph(CustomState)
graph.add_node("processor", process_data)
graph.add_node("approval", approval_required, interrupt=True)
graph.add_node("finalizer", finalize)

graph.add_edge(START, "processor")
graph.add_edge("processor", "approval")
graph.add_edge("approval", "finalizer")
graph.add_edge("finalizer", END)

app = graph.compile(checkpointer=checkpointer)
```

### Resume After Interrupt

```python
config = {"configurable": {"thread_id": "1"}}

# First run - pauses at approval
result = app.invoke(input_data, config=config)

# Resume after approval
result = app.invoke(None, config=config)  # Continue from interrupt
```

## Streaming

### Stream Mode: Values

```python
for state in graph.stream(
    {"messages": [{"role": "user", "content": "Hello"}]},
    stream_mode="values"
):
    print(state["messages"][-1])
```

### Stream Mode: Updates

```python
for update in graph.stream(
    {"messages": [...]},
    stream_mode="updates"
):
    node_name = list(update.keys())[0]
    print(f"Update from {node_name}: {update[node_name]}")
```

## Multi-Agent Workflows

### Agent Coordination

```python
def agent_1(state):
    # Agent 1 logic
    return {"messages": [...], "agent_1_complete": True}

def agent_2(state):
    # Agent 2 logic
    return {"messages": [...], "agent_2_complete": True}

def coordinator(state):
    if not state.get("agent_1_complete"):
        return "agent_1"
    elif not state.get("agent_2_complete"):
        return "agent_2"
    return "finish"

graph = StateGraph(CustomState)
graph.add_node("agent_1", agent_1)
graph.add_node("agent_2", agent_2)
graph.add_node("finish", lambda s: s)

graph.add_conditional_edges(START, coordinator)
graph.add_conditional_edges("agent_1", coordinator)
graph.add_conditional_edges("agent_2", coordinator)
graph.add_edge("finish", END)
```

## Memory Management

### Session Memory

```python
from langgraph.checkpoint.memory import InMemorySaver

# Persist across multiple invocations
checkpointer = InMemorySaver()
graph = graph.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "session-123"}}

# First message
graph.invoke({"messages": [{"role": "user", "content": "My name is Alice"}]}, config)

# Later message - remembers context
graph.invoke({"messages": [{"role": "user", "content": "What's my name?"}]}, config)
```

### Store Integration

```python
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()

# Write to store
store.put(("users",), "user_123", {"name": "Alice", "preferences": {...}})

# Read from store in node
def process_with_store(state, store):
    user_data = store.get(("users",), state["user_id"])
    return {"messages": [...]}
```

## Error Handling

### Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def api_call_node(state):
    # API call that might fail
    response = external_api.call(state["query"])
    return {"messages": [response]}

graph.add_node("api_call", api_call_node)
```

### Error Nodes

```python
def error_handler(state):
    error = state.get("error")
    return {"messages": [{"role": "assistant", "content": f"Error occurred: {error}"}]}

def process_with_error_handling(state):
    try:
        result = risky_operation(state)
        return {"messages": [result]}
    except Exception as e:
        return {"error": str(e), "route": "error"}

graph.add_node("processor", process_with_error_handling)
graph.add_node("error_handler", error_handler)

graph.add_conditional_edges(
    "processor",
    lambda s: "error_handler" if "error" in s else "success"
)
```

## Subgraphs

### Nested Workflows

```python
# Define subgraph
sub_graph = StateGraph(SubState)
sub_graph.add_node("sub_step_1", step_1)
sub_graph.add_node("sub_step_2", step_2)
sub_graph.add_edge(START, "sub_step_1")
sub_graph.add_edge("sub_step_1", "sub_step_2")
sub_graph.add_edge("sub_step_2", END)
sub_app = sub_graph.compile()

# Use in main graph
def run_subgraph(state):
    sub_result = sub_app.invoke(state["sub_input"])
    return {"sub_output": sub_result}

main_graph.add_node("subprocess", run_subgraph)
```

## Deployment

### LangGraph Studio

```bash
# Install
pip install langgraph-studio

# Run locally
langgraph-studio serve
```

### LangGraph Cloud

```python
# Deploy to LangGraph Cloud
from langgraph.cloud import deploy

deploy(
    graph=app,
    name="my-agent",
    description="Production agent workflow"
)
```

## Best Practices

1. **State Design**: Keep state minimal and well-typed
2. **Checkpointing**: Always use checkpointers in production
3. **Error Handling**: Add error nodes for graceful degradation
4. **Streaming**: Use streaming for better UX on long operations
5. **Testing**: Test individual nodes before full graph integration
6. **Conditional Logic**: Keep routing functions simple and testable
7. **Memory Management**: Clean up old checkpoints periodically
8. **Observability**: Add logging at key decision points

## Installation

```bash
pip install -U langgraph
pip install langgraph-checkpoint-postgres  # For production persistence
```

## Resources

- **Documentation**: https://python.langchain.com/docs/langgraph/
- **GitHub**: https://github.com/langchain-ai/langgraph
- **Examples**: https://github.com/langchain-ai/langgraph/tree/main/examples






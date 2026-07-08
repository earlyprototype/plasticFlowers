# LangChain Documentation

## Overview
LangChain is a framework for developing applications powered by language models. It provides modular components for chaining together LLMs with other sources of computation or knowledge.

## Key Components

### 1. Models & Embeddings
Wrappers for various LLM providers (OpenAI, Anthropic, HuggingFace, etc.).
```python
from langchain_openai import ChatOpenAI
model = ChatOpenAI(model="gpt-4o")
```

### 2. Prompts
Templates for managing and optimizing prompts.
```python
from langchain_core.prompts import PromptTemplate
prompt = PromptTemplate.from_template("Tell me a joke about {topic}")
```

### 3. Chains
Sequences of calls (LLM -> Output Parser, or LLM -> Tool).
```python
chain = prompt | model | output_parser
```

### 4. Vector Stores (Memory / RAG)
Integrations with vector databases (including Neo4j, Pinecone, MemoryDB) for RAG.
```python
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Neo4jVector

vector_store = Neo4jVector.from_existing_graph(
    embedding=OpenAIEmbeddings(),
    url=url,
    username=user,
    password=password
)
```

### 5. Agents (LangGraph)
Systems that use LLMs to decide what actions to take and in what order.
`LangGraph` is the orchestration framework for stateful agents.
```python
from langgraph.graph import StateGraph, START, END
# Define nodes and edges to create cyclic graphs
```

## JavaScript/TypeScript Support
LangChain has a full JS/TS implementation (`langchain.js`).
```typescript
import { ChatOpenAI } from "@langchain/openai";
const model = new ChatOpenAI({ temperature: 0 });
```

## Use Cases
*   **RAG (Retrieval Augmented Generation)**: Chat over documents.
*   **Chatbots**: Conversational agents with memory.
*   **Extraction**: Structured data extraction from text.
*   **Agents**: Autonomous tools usage.

## Detailed Reference (Code Snippets)

### Retrieval-Augmented Generation (RAG) Pipeline
Source: https://context7.com/langchain-ai/langchain/llms.txt

```python
from operator import itemgetter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

documents = [
    "LangChain is a framework for developing LLM applications.",
    "It provides tools for prompt management, chains, and agents.",
    "LCEL (LangChain Expression Language) enables declarative composition."
]

text_splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)
splits = text_splitter.create_documents(documents)

vectorstore = Chroma.from_documents(
    documents=splits,
    embedding=OpenAIEmbeddings()
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

prompt = ChatPromptTemplate.from_template("""
Answer the question based only on the following context:

{context}

Question: {question}
""")

rag_chain = (
    RunnablePassthrough.assign(
        context=itemgetter("question") | retriever | (lambda docs: "\n\n".join(doc.page_content for doc in docs))
    )
    | prompt
    | ChatOpenAI(model="gpt-4")
    | StrOutputParser()
)

answer = rag_chain.invoke({"question": "What is LCEL?"})
print(answer)
```

### Basic Chain with Prompt, Model, and Parser in Python
Source: https://context7.com/langchain-ai/langchain/llms.txt

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Initialize model
model = ChatOpenAI(model="gpt-4", temperature=0.7)

# Create prompt template
prompt = ChatPromptTemplate.from_template("Tell me a joke about {topic}")

# Chain components with | operator
chain = prompt | model | StrOutputParser()

# Invoke synchronously
result = chain.invoke({"topic": "programmers"})
print(result)  # "Why do programmers prefer dark mode? Because light attracts bugs!"

# Stream response
for chunk in chain.stream({"topic": "cats"}):
    print(chunk, end="", flush=True)

# Batch multiple inputs
results = chain.batch([
    {"topic": "dogs"},
    {"topic": "birds"}
])

# Async invocation
import asyncio
async_result = await chain.ainvoke({"topic": "fish"})
```

### Define and Bind Tools with @tool Decorator
Source: https://context7.com/langchain-ai/langchain/llms.txt

```python
from typing import Annotated
from langchain_core.tools import tool
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, ToolMessage

@tool
def get_weather(
    location: Annotated[str, "City name or address"],
    units: Annotated[str, "Temperature units: celsius or fahrenheit"] = "celsius"
) -> str:
    """Get current weather for a location."""
    return f"Weather in {location}: 22°{units[0].upper()}, partly cloudy"

@tool
def calculator(expression: str) -> float:
    """Evaluate a mathematical expression safely."""
    return eval(expression)

model = ChatAnthropic(model="claude-3-5-sonnet-latest")
model_with_tools = model.bind_tools([get_weather, calculator])

response = model_with_tools.invoke([
    HumanMessage(content="What's the weather in Paris and what's 15 * 23?")
])

tool_results = []
for tool_call in response.tool_calls:
    if tool_call["name"] == "get_weather":
        result = get_weather.invoke(tool_call["args"])
    elif tool_call["name"] == "calculator":
        result = calculator.invoke(tool_call["args"])

    tool_results.append(ToolMessage(
        content=str(result),
        tool_call_id=tool_call["id"]
    ))

final_response = model_with_tools.invoke([
    HumanMessage(content="What's the weather in Paris and what's 15 * 23?"),
    response,
    *tool_results
])
print(final_response.content)
```

### Structured Output with Pydantic Models in Python
Source: https://context7.com/langchain-ai/langchain/llms.txt

```python
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# Define output structure
class Person(BaseModel):
    name: str = Field(description="Person's full name")
    age: int = Field(description="Person's age in years")
    occupation: str = Field(description="Person's job or profession")
    interests: list[str] = Field(description="List of hobbies or interests")

model = ChatOpenAI(model="gpt-4")
structured_model = model.with_structured_output(Person)

prompt = ChatPromptTemplate.from_template(
    "Extract person information from: {text}"
)

chain = prompt | structured_model
```

### Conversational Chain with Message History in Python
Source: https://context7.com/langchain-ai/langchain/llms.txt

```python
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_anthropic import ChatAnthropic

model = ChatAnthropic(model="claude-3-5-sonnet-latest")

# Prompt with placeholder for chat history
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful AI assistant. Answer concisely."),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}")
])

chain = prompt | model | StrOutputParser()

# First turn
chat_history = []
response1 = chain.invoke({
    "input": "My name is Alice and I love Python programming",
    "chat_history": chat_history
})
print(response1)  # "Nice to meet you, Alice! Python is a great language..."

# Add to history
chat_history.extend([
    HumanMessage(content="My name is Alice and I love Python programming"),
    AIMessage(content=response1)
])

# Second turn - model remembers context
response2 = chain.invoke({
    "input": "What's my name and what do I like?",
    "chat_history": chat_history
})
print(response2)  # "Your name is Alice and you love Python programming."
```

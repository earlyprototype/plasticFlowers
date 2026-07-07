# Validated Code Patterns

**Purpose:** Proven code patterns from the plasticFlower codebase.  
**Usage:** Reference when implementing similar functionality.  
**Update:** Add patterns as you solve problems.

---

## Neo4j / Cypher Patterns

### Pattern: Upsert Node with Session Scope

**File:** `backend/app/services/graph_db.py:create_node()`  
**Validated:** Gate 3

```cypher
CREATE (n:Node)
SET n = $node
RETURN n AS node
```

**Notes:**
- Uses CREATE (not MERGE) because we generate unique IDs
- Session ID is embedded in node properties
- Full property replacement with SET n = $props

---

### Pattern: MATCH Nodes + MERGE Relationship (Safe Upsert)

**File:** `backend/app/services/graph_db.py:create_relationship()`  
**Validated:** 2025-12-28

```cypher
MATCH (source:Node {id: $source_id, session_id: $session_id})
MATCH (target:Node {id: $target_id, session_id: $session_id})
MERGE (source)-[rel:RELATIONSHIP {id: $relationship_id}]->(target)
SET rel = $relationship
RETURN rel AS relationship
```

**Why it works:**
- MATCH (not MERGE) on nodes prevents creating corrupt empty nodes
- Returns no rows if either node doesn't exist (handle gracefully in Python)
- MERGE on relationship prevents duplicates
- Idempotent - safe to retry on failure

**Anti-pattern to avoid:**
```cypher
-- DON'T DO THIS - creates empty nodes if they don't exist
MERGE (source:Node {id: $source_id, session_id: $session_id})
```

---

### Pattern: List with Optional Filters

**File:** `backend/app/services/graph_db.py:list_nodes()`  
**Validated:** Gate 3

```python
where_clauses: List[str] = []
params: Dict[str, Any] = {"session_id": session_id}

if status:
    where_clauses.append("n.status = $status")
    params["status"] = status.value

where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
query = f"""
MATCH (n:Node {{session_id: $session_id}})
{where_sql}
RETURN n AS node
"""
```

**Why it works:**
- Dynamic query building
- Uses parameterised queries (prevents injection)
- Empty filters = no WHERE clause

---

### Pattern: Cascade Delete Session

**File:** `backend/app/services/graph_db.py:delete_session_record()`  
**Validated:** Gate 6

```cypher
-- Delete relationships first
MATCH ()-[r:RELATIONSHIP {session_id: $session_id}]->()
DELETE r

-- Delete nodes
MATCH (n:Node {session_id: $session_id})
DETACH DELETE n

-- Delete flowers
MATCH (f:Flower {session_id: $session_id})
DELETE f

-- Delete chunks
MATCH (c:TranscriptChunk {session_id: $session_id})
DELETE c

-- Delete session
MATCH (s:Session {id: $session_id})
DELETE s
```

**Why it works:**
- Order matters: relationships before nodes
- DETACH DELETE handles remaining edges
- Transaction wraps all queries

---

### Pattern: Recent Transcript with Word Limit (Optimised)

**File:** `backend/app/services/graph_db.py:get_recent_transcript()`  
**Validated:** Phase A (2025-12-26)

```python
# Calculate chunk limit: conservative 20 words/chunk, cap at 500 chunks
chunk_limit = min((word_limit // 20) + 10, 500)

query = """
MATCH (c:TranscriptChunk {session_id: $session_id})
RETURN c.text AS text, c.start_time AS start_time
ORDER BY c.start_time DESC
LIMIT $chunk_limit
"""

# Collect in reverse order, counting words
chunks = []
word_count = 0
async for record in result:
    text = record["text"]
    words = text.split()
    if word_count + len(words) > word_limit:
        remaining = word_limit - word_count
        chunks.append(" ".join(words[:remaining]))
        break
    chunks.append(text)
    word_count += len(words)

# Reverse back to chronological
return " ".join(reversed(chunks))
```

**Why it works:**
- LIMIT prevents Neo4j over-planning (key optimisation)
- Conservative estimate (20 words/chunk) ensures we never under-fetch
- Actual average is ~60 words/chunk based on production data
- Default 3000 words for Gardener context
- Fetches newest first (DESC), returns in chronological order

---

### Pattern: Flower Membership via Relationship

**File:** `backend/app/services/graph_db.py:set_node_flower()`  
**Validated:** Gate 5

```cypher
MATCH (n:Node {id: $node_id, session_id: $session_id})
MATCH (f:Flower {id: $flower_id, session_id: $session_id})

// Remove any existing membership
OPTIONAL MATCH (n)-[old:BELONGS_TO]->(:Flower)
DELETE old

// Create new membership
CREATE (n)-[:BELONGS_TO]->(f)
```

**Why it works:**
- Relationship-based membership (not property)
- Ensures single flower per node
- Atomic in transaction

---

## Python / FastAPI Patterns

### Pattern: Async Session Execute

**File:** `backend/app/services/graph_db.py` (all functions)  
**Validated:** Gate 3

```python
async with driver.session() as session:
    async def _work(tx, cypher: str, params: Dict[str, Any]) -> Node:
        result = await tx.run(cypher, **params)
        record = await result.single()
        if record is None:
            raise ValueError("Not found")
        return _node_from_value(record["node"])

    return await session.execute_write(_work, query, params)
```

**Why it works:**
- Inner function pattern for transactions
- Proper async/await throughout
- Clean separation of query and execution

---

### Pattern: Pydantic Model Validation for LLM Response

**File:** `backend/app/agents/builder.py`  
**Validated:** Gate 4

```python
try:
    payload = await self._llm_fn(prompt, BuilderLLMResponse)
except LLMError as exc:
    raise BuilderAgentError("Gemini request failed", code="llm_error") from exc

try:
    response = BuilderLLMResponse.model_validate(payload)
except ValidationError as exc:
    raise BuilderAgentError("Invalid payload", code="invalid_payload") from exc
```

**Why it works:**
- Separates LLM errors from validation errors
- Custom error types with codes
- Chain exceptions for debugging

---

### Pattern: Disable Gemini 2.5 Thinking Mode for Speed

**File:** `backend/app/services/llm.py`  
**Validated:** 2025-12-28

```python
from google.genai import types

config = types.GenerateContentConfig(
    temperature=0.7,
    max_output_tokens=8192,
    response_mime_type="application/json",
    response_schema=MyPydanticModel,
    # Disable thinking mode - saves 60+ seconds on 2.5 models
    thinking_config=types.ThinkingConfig(thinking_budget=0),
)
```

**Why it works:**
- Gemini 2.5 models have "thinking mode" enabled by default
- Thinking adds internal reasoning before output (60+ seconds overhead)
- For structured output tasks, thinking is unnecessary
- Setting `thinking_budget=0` disables it

---

### Pattern: Literal Types for Structured Output Enums

**File:** `backend/app/agents/gardener.py`  
**Validated:** 2025-12-28

```python
from typing import Literal
from pydantic import BaseModel, Field

class NodeAction(BaseModel):
    # Use Literal instead of regex pattern
    action: Literal["confirm", "prune", "merge"] = Field(
        ..., 
        description="confirm=promote, prune=remove, merge=combine"
    )
    node_id: str = Field(..., min_length=1)
```

**Why it works:**
- Gemini structured output works better with Literal types than regex patterns
- Regex patterns with flags like `(?i)` may not be supported
- Literal creates an enum-style constraint that's clearly communicated to the model
- Pydantic converts Literal to JSON Schema `enum` which Gemini understands

**Anti-pattern to avoid:**
```python
# DON'T DO THIS - regex with flags may cause issues
action: str = Field(..., pattern="^(?i)(confirm|prune|merge)$")
```

---

### Pattern: Label Normalisation for Deduplication

**File:** `backend/app/agents/builder.py:_normalise_label()`  
**Validated:** Gate 4

```python
def _normalise_label(label: str) -> str:
    return " ".join(label.strip().split()).lower()
```

**Why it works:**
- Collapses whitespace
- Case-insensitive matching
- Safe for empty strings

---

## Frontend Patterns

### Pattern: Speech Recognition Chunking

**File:** `frontend/src/hooks/useSpeechRecognition.ts`  
**Validated:** Gate 2

```typescript
// Check word count threshold (75 words)
const wordCount = pendingText.trim().split(/\s+/).length;
if (wordCount >= 75) {
    extractAndSendChunk();
}

// Also check time (8 seconds)
forceFinalizationTimerRef.current = setTimeout(() => {
    extractAndSendChunk();
}, 8000);
```

**Why it works:**
- Word-based (75) catches fast speakers
- Time-based (8s) catches slow speakers
- Both triggers prevent stale buffers

---

---

## Agent Coordination Patterns (Planned - ADR-006)

Patterns from architecture planning. Validate during implementation.

### Pattern: Redis Streams Consumer Group

**Reference:** [ADR-006](./ADR/0006-async-agents-over-langgraph.md)  
**File:** `backend/app/services/redis_streams.py:consume_events()`  
**Status:** PENDING VALIDATION - Code implemented, awaiting test

```python
import redis.asyncio as redis

async def consume_chunks(group_name: str, consumer_name: str):
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    
    # Create consumer group (once)
    try:
        await r.xgroup_create('chunks', group_name, id='0', mkstream=True)
    except redis.ResponseError:
        pass  # Group exists
    
    while True:
        # Block for new messages
        messages = await r.xreadgroup(
            groupname=group_name,
            consumername=consumer_name,
            streams={'chunks': '>'},  # '>' = new messages only
            count=10,
            block=5000
        )
        
        for stream_name, stream_messages in messages:
            for message_id, data in stream_messages:
                try:
                    await process_chunk(data)
                    await r.xack('chunks', group_name, message_id)
                except Exception as e:
                    # Message stays pending for retry
                    logger.error(f"Failed to process {message_id}: {e}")
```

**Why it works:**
- Consumer groups enable multiple workers
- Block prevents busy-waiting
- XACK confirms processing (unacked = retry)
- Fire-and-forget for Researcher triggers

---

### Pattern: Async Agent Without LangGraph

**Reference:** [ADR-006](./ADR/0006-async-agents-over-langgraph.md), [ADR-009](./ADR/0009-redis-only-agent-scheduling.md)  
**File:** `backend/app/services/scheduler.py:_redis_consumer_loop()`  
**Status:** PENDING VALIDATION - Code implemented, awaiting test

```python
import asyncio

# Builder - request-driven (via BuilderService)
# Publishes to Redis after processing
async def process_chunk(session_id: str, chunk: TranscriptChunk):
    result = await builder_agent.build(chunk)
    await persist_to_neo4j(result)
    await broadcast_sse("node_added", result.nodes)
    await publish_chunk_added(session_id, chunk.id)  # Triggers Gardener

# Gardener - Redis-only consumer (no timer loop)
async def gardener_consumer_loop():
    async for message_id, data in consume_events(STREAM_CHUNKS_ADDED, ...):
        if debounce_ok(data["session_id"]):
            await run_gardener(data["session_id"])
        await ack_event(message_id)

# Researcher - event-triggered (future)
async def researcher_consumer_loop():
    async for message_id, data in consume_events(STREAM_NODES_NEEDS_RESEARCH, ...):
        await run_researcher(data["node_id"])
        await ack_event(message_id)

# Coordination - Redis is the event bus
async def main():
    asyncio.create_task(gardener_consumer_loop())   # Gardener via Redis
    asyncio.create_task(researcher_consumer_loop()) # Researcher via Redis
    # Builder is request-driven, not a consumer
```

**Why it works:**
- Agents run independently (no handoffs needed)
- Redis Streams provides event coordination with debounce
- Single trigger path per agent (simpler debugging)
- Configurable timing via environment variables
- Simpler than LangGraph for this use case

---

### Pattern: Service Layer Separation

**Reference:** [ADR-009](./ADR/0009-redis-only-agent-scheduling.md)  
**File:** `backend/app/services/builder_service.py`  
**Status:** PENDING VALIDATION - Code implemented, awaiting test

```python
# API Layer - thin, validation only
@router.post("/chunks")
async def submit_chunk(payload: ChunkRequest, session_id: str):
    # Validate
    session = await get_session_record(session_id)
    if not session:
        raise HTTPException(404)
    
    # Queue background processing
    asyncio.create_task(service.process_chunk(session_id, chunk))
    return {"chunk_id": chunk.id}

# Service Layer - orchestration + persistence + events
class BuilderService:
    async def process_chunk(self, session_id: str, chunk: TranscriptChunk):
        # 1. Run LLM agent
        result = await self._agent.build(chunk.text)
        
        # 2. Persist to database
        await self._persist_nodes(session_id, result.nodes)
        
        # 3. Broadcast SSE events
        await self._broadcast_nodes(session_id, result.nodes)
        
        # 4. Publish to Redis (trigger downstream agents)
        await publish_chunk_added(session_id, chunk.id)

# Agent Layer - pure LLM logic, no I/O
class BuilderAgent:
    async def build(self, chunk_text: str) -> BuilderResult:
        prompt = self._render_prompt(chunk_text)
        response = await self._llm(prompt)
        return self._parse_response(response)
```

**Why it works:**
- API layer is testable without mocking services
- Service layer is testable without HTTP
- Agent layer is testable without any I/O
- Clear responsibilities: validate -> orchestrate -> LLM
- Consistent pattern for all agents (Builder, Gardener, Researcher)

---

### Pattern: Full Context Q&A (Librarian)

**Reference:** [ADR-004](./ADR/0004-full-context-qa.md)  
**Status:** Planned (not yet implemented)

```python
async def librarian_single_session(question: str, session_id: str) -> str:
    """Answer questions about a single session using full context."""
    
    # Load full session (~25k tokens for 90min session)
    transcript = await get_full_transcript(session_id)
    nodes = await get_all_nodes(session_id)
    relationships = await get_all_relationships(session_id)
    
    # Format context
    nodes_text = "\n".join([f"- {n.label} ({n.inferred_type})" for n in nodes])
    rels_text = "\n".join([f"- {r.source} -> {r.description} -> {r.target}" for r in relationships])
    
    prompt = f"""You are answering questions about a recorded talk.

TRANSCRIPT:
{transcript}

KNOWLEDGE GRAPH:
Entities:
{nodes_text}

Relationships:
{rels_text}

QUESTION: {question}

Answer with specific citations to moments in the transcript where relevant.
"""
    
    return await gemini.generate(prompt, model="gemini-2.5-pro")
```

**Why it works:**
- 25k tokens << 1M context window
- No retrieval tuning needed
- LLM sees everything (no missed context)
- Simple implementation
- GraphRAG only needed for multi-session (Phase 7)

---

---

## External Reference Patterns (From GitHub)

These patterns are from high-trust external repositories and have been validated in production systems.

### Pattern: LLM Entity Extraction with neo4j-graphrag-python

**Source:** [neo4j/neo4j-graphrag-python](https://github.com/neo4j/neo4j-graphrag-python/blob/main/examples/kg_builder.py)  
**Trust:** Official Neo4j (9/10)  
**Relevance:** Builder agent entity extraction

```python
from neo4j_graphrag.experimental.components.entity_relation_extractor import (
    LLMEntityRelationExtractor,
    OnError,
)
from neo4j_graphrag.experimental.components.kg_writer import Neo4jWriter
from neo4j_graphrag.experimental.components.schema import (
    SchemaBuilder,
    NodeType,
    RelationshipType,
)
from neo4j_graphrag.experimental.pipeline import Pipeline

# Define schema constraints
node_types = [
    NodeType(label="PERSON", description="An individual human being."),
    NodeType(label="ORGANIZATION", description="A structured group."),
]
relationship_types = [
    RelationshipType(label="WORKS_FOR", description="Employment relationship."),
]
patterns = [("PERSON", "WORKS_FOR", "ORGANIZATION")]

# Set up pipeline
pipe = Pipeline()
pipe.add_component(FixedSizeSplitter(chunk_size=4000, chunk_overlap=200), "splitter")
pipe.add_component(SchemaBuilder(), "schema")
pipe.add_component(
    LLMEntityRelationExtractor(llm=llm, on_error=OnError.RAISE),
    "extractor",
)
pipe.add_component(Neo4jWriter(neo4j_driver), "writer")

# Connect components
pipe.connect("splitter", "extractor", input_config={"chunks": "splitter"})
pipe.connect("schema", "extractor", input_config={"schema": "schema"})
pipe.connect("extractor", "writer", input_config={"graph": "extractor"})
```

**Why it works:**
- Pipeline architecture decouples components
- Schema constraints improve extraction quality
- Neo4jWriter handles MERGE patterns automatically
- OnError.RAISE surfaces issues early

---

### Pattern: Custom Entity Extraction Prompt

**Source:** [ronidas39/neo4j-graphRag-Tutorial](https://github.com/ronidas39/neo4j-graphRag-Tutorial/blob/main/tutorial2/usecase2.py)  
**Trust:** Tutorial (matches video) (7/10)  
**Relevance:** Builder agent customisation

```python
from neo4j_graphrag.generation.prompts import ERExtractionTemplate

prompt = ERExtractionTemplate(
    template="""
You are an expert in extracting entities and relationships from text.

## Text to analyze:
{text}

## Required JSON Output Format:
Return a JSON object with this EXACT structure:

{{
  "nodes": [
    {{
      "id": "0",
      "label": "Person",
      "properties": {{"name": "Player Name"}}
    }}
  ],
  "relationships": [
    {{
      "type": "PLAYS_FOR",
      "start_node_id": "0",
      "end_node_id": "1"
    }}
  ]
}}

CRITICAL RULES:
1. Each node MUST have: "id" (unique string), "label", and "properties"
2. Each relationship MUST have: "type", "start_node_id", "end_node_id"
3. Relationship types in UPPER_SNAKE_CASE

Return ONLY valid JSON.
""",
    expected_inputs=["text"]
)

extractor = LLMEntityRelationExtractor(
    llm=OpenAILLM(
        model_name="gpt-4o",
        model_params={
            "max_tokens": 5000,
            "response_format": {"type": "json_object"}
        }
    ),
    prompt_template=prompt
)
```

**Why it works:**
- Custom prompt tailors extraction to domain
- JSON schema in prompt improves structure
- `response_format: json_object` enforces JSON output
- `expected_inputs` validates template variables

---

### Pattern: SSE Streaming with FastAPI

**Source:** [docker/genai-stack](https://github.com/docker/genai-stack/blob/main/api.py)  
**Trust:** Docker Official (9/10)  
**Relevance:** Real-time graph updates to frontend

```python
from fastapi import FastAPI
from sse_starlette.sse import EventSourceResponse
from threading import Thread
from queue import Queue, Empty
from collections.abc import Generator
import json

class QueueCallback(BaseCallbackHandler):
    """Stream LLM tokens to a queue."""
    def __init__(self, q):
        self.q = q

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.q.put(token)

    def on_llm_end(self, *args, **kwargs) -> None:
        return self.q.empty()

def stream(cb, q) -> Generator:
    job_done = object()

    def task():
        cb()
        q.put(job_done)

    t = Thread(target=task)
    t.start()

    while True:
        try:
            next_token = q.get(True, timeout=1)
            if next_token is job_done:
                break
            yield next_token
        except Empty:
            continue

@app.get("/query-stream")
def qstream(question: Question = Depends()):
    q = Queue()
    
    def cb():
        output_function.invoke(question.text, config={"callbacks": [QueueCallback(q)]})

    def generate():
        yield json.dumps({"init": True})
        for token in stream(cb, q):
            yield json.dumps({"token": token})

    return EventSourceResponse(generate(), media_type="text/event-stream")
```

**Why it works:**
- Queue-based streaming decouples LLM from HTTP
- Thread handles blocking LLM call
- EventSourceResponse provides proper SSE headers
- Timeout prevents hanging on slow responses

---

### Pattern: SSE Reconnection with Event Replay

**Source:** [zer0pool/graph-viz](https://github.com/zer0pool/graph-viz/blob/develop/docs/04.development-notes/2025-12-03_sse-realtime-event-stability.md)  
**Trust:** Production app (8/10)  
**Relevance:** Multi-browser sync, network interruptions

**Backend (event buffer):**
```python
# Store events with IDs in Redis Streams
await redis.xadd("events", {"type": "node_added", "data": json.dumps(node)})

# SSE endpoint with replay
@app.get("/events")
async def events(last_event_id: str = None):
    async def generate():
        # Replay missed events
        if last_event_id:
            missed = await redis.xrange("events", min=last_event_id, count=100)
            for event_id, data in missed:
                yield {"id": event_id, "data": json.dumps(data)}
        
        # Continue with live stream
        async for event in subscribe_events():
            yield {"id": event.id, "data": json.dumps(event.data)}
    
    return EventSourceResponse(generate())
```

**Frontend (reconnection):**
```javascript
let lastEventId = localStorage.getItem('lastEventId');

function connect() {
    const url = lastEventId 
        ? `/events?lastEventId=${lastEventId}` 
        : '/events';
    
    const source = new EventSource(url);
    
    source.onmessage = (e) => {
        lastEventId = e.lastEventId;
        localStorage.setItem('lastEventId', lastEventId);
        handleEvent(JSON.parse(e.data));
    };
    
    source.onerror = () => {
        source.close();
        setTimeout(connect, 1000);  // Reconnect after 1s
    };
}
```

**Why it works:**
- Redis Streams provides persistent event log
- Event IDs enable precise replay after disconnect
- localStorage persists across page refreshes
- Auto-reconnect handles network blips

---

## Testing Patterns

### Pattern: Integration Test for Config Flag Enforcement

**File:** `backend/tests/test_builder_service.py`  
**Validated:** 2025-12-31

```python
@pytest.mark.asyncio
async def test_similarity_check_disabled_creates_all_ghost_nodes(monkeypatch):
    """Test that config flag controls feature at the correct architectural layer."""
    from backend.app.config import Settings
    from backend.app.services import builder_service
    
    # Mock config with flag DISABLED
    disabled_settings = Settings(
        similarity_check_enabled=False,
        neo4j_uri="bolt://localhost:7687",
        neo4j_username="neo4j",
        neo4j_password="test",
        redis_url="redis://localhost:6379",
    )
    monkeypatch.setattr(builder_service, "get_settings", lambda: disabled_settings)
    
    # Mock the functions that SHOULD NOT BE CALLED when flag is disabled
    similarity_called = {"count": 0}
    
    async def fake_query_best_match(*args, **kwargs):
        similarity_called["count"] += 1
        raise AssertionError("Should not be called when disabled!")
    
    monkeypatch.setattr(builder_service, "_query_best_match", fake_query_best_match)
    
    # ... mock other dependencies ...
    
    # Run the service
    service = BuilderService()
    result = await service.process_chunk("session-1", chunk)
    
    # Verify flag was respected
    assert similarity_called["count"] == 0, "Feature should be bypassed"
```

**Why it works:**
- Tests at the correct architectural layer (service, not low-level function)
- Uses monkeypatch to inject test config without environment variables
- Mock functions raise AssertionError if called (catches incorrect enforcement)
- Verifies actual behavior change, not just config value
- Proper integration test - exercises full code path

**Anti-pattern to avoid:**
```python
# DON'T test flag enforcement in the wrong layer
async def test_similarity_respects_flag():
    # similarity.py doesn't check the flag - builder_service does!
    result = await similarity.run_similarity(...)
    # This test will fail because flag is enforced elsewhere
```

---

## Frontend Architecture Patterns

### Pattern: Separation of Concerns in Graph Visualisation

**Files:** `frontend/src/components/graph/` (layout/, rendering/, animation/, config/)  
**Validated:** 2025-12-31 (GraphCanvas refactor)

**Problem:** Single 2017-line component with competing animation systems causing flickering, edge errors, and maintenance nightmares.

**Solution:** Split into focused modules with single responsibilities.

**Architecture:**
```
layout/layoutEngine.ts       - Pure functions, zero side effects
rendering/graphRenderer.ts    - Cytoscape sync, no layout/animation
animation/animationController - Single animation strategy  
config/layoutConfig.ts        - Centralized settings
GraphCanvas.tsx               - Orchestration only (400 lines)
```

**Why it works:**
- Testability: Pure functions (no DOM, no mocks needed)
- Maintainability: Each module <220 lines, single responsibility
- Performance: Lock existing nodes, only new nodes positioned
- No conflicts: Single animation system (no competing timers)
- Extensibility: Swap components independently

**Results:**
- 2017 lines → 1060 lines (47% reduction)
- Zero "invalid endpoints" errors
- 7 unit tests passing
- Draggable flowers free with compound nodes

---

### Pattern: Camera-First Animation Sequencing

**File:** `frontend/src/components/graph/animation/animationController.ts`  
**Validated:** 2025-12-31

```typescript
async executeAnimationSequence(cy, syncResult, isolatedNodeIds) {
  // STEP 1: Camera moves FIRST (non-blocking)
  this.startCameraFit(cy);
  
  // STEP 2: While camera moving, fade in elements (400ms delay)
  await Promise.all([
    this.fadeInNewNodes(cy, syncResult.addedNodeIds),
    this.fadeInNewEdges(cy, syncResult.addedEdgeIds),
  ]);
  
  // STEP 3: Float effects after fade
  this.applyFloatEffects(cy, isolatedNodeIds);
}
```

**Timing:**
```
0ms    400ms   1200ms
|      |       |
Camera starts (1200ms)
|-------------|
       Elements fade (800ms)
       |-------|
```

**Why it works:**
- User sees big picture first (camera frames the action)
- Elements fade during camera movement (feels smooth)
- Total perceived time: 1200ms vs 2000ms sequential
- No waiting for elements before seeing context

---

### Pattern: Float Effect for Isolated Nodes

**File:** `frontend/src/components/graph/animation/animationController.ts`  
**Validated:** 2025-12-31

```typescript
private startFloatAnimation(cy: Core, nodeId: string): void {
  const seed = nodeId.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0);
  const angle = (seed % 360) * (Math.PI / 180);
  
  const animate = () => {
    // Stop if removed or joined flower
    if (!node.nonempty() || node.parent().nonempty()) {
      this.activeFloatAnimations.delete(nodeId);
      return;
    }
    
    // Gentle sine-wave orbit
    const offset = Math.sin(Date.now() / 3000 + seed) * 15;
    node.animate({
      position: {
        x: startPos.x + Math.cos(angle) * offset,
        y: startPos.y + Math.sin(angle) * offset,
      }
    }, {
      duration: 3000,
      easing: 'ease-in-out',
      complete: animate, // Loop forever
    });
  };
  
  animate();
}
```

**Criteria for float:**
- Node not in flower
- Has ≤1 connection (truly isolated)
- Stops when node gains connections or joins cluster

**Why it works:**
- Per-node seed creates varied motion (not identical orbits)
- 15px radius is subtle (not distracting)
- 3-second cycle is calming (not frenetic)
- Stops automatically when node joins cluster

---

### Pattern: Draggable Compound Nodes

**File:** `frontend/src/components/graph/rendering/graphRenderer.ts`  
**Validated:** 2025-12-31

```typescript
// Create compound node (flower)
cy.add({
  group: 'nodes',
  data: { id: flower.id, label: flower.label },
  classes: 'flower',
  grabbable: true, // Makes entire cluster draggable
});

// Assign children (petals)
members.forEach(node => {
  cy.getElementById(node.id).move({ parent: flower.id });
});

// Styling shows affordance
{
  selector: 'node.flower:hover',
  style: {
    cursor: 'grab', // Shows it's draggable
  }
}
```

**Why it works:**
- Cytoscape compound nodes are draggable by default
- When parent dragged, all children move automatically
- No custom drag handlers needed
- Hover state shows affordance

**Configuration:**
```typescript
nestingFactor: 0.2,        // How tightly members cluster
gravityCompound: 1.2,       // Pull members toward flower center
gravityRangeCompound: 2.0,  // Range of compound gravity
```

---

## Adding New Patterns

When you solve a problem, add it here:

```markdown
### Pattern: [Name]

**File:** `path/to/file.py:function_name()`  
**Validated:** [Date or Gate]

\`\`\`[language]
[Code snippet]
\`\`\`

**Why it works:**
- [Reason 1]
- [Reason 2]
```


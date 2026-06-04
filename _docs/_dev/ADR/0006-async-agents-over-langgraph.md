# ADR-006: Async Event-Driven Agents over LangGraph

## Status

Accepted

## Date

2025-12-26

## Context

The plasticFlower architecture defines four agents (Builder, Gardener, Researcher, Librarian) that need to coordinate around a shared Neo4j knowledge graph. We evaluated LangGraph as an orchestration framework for these agents.

LangGraph provides:
- State management across agent steps
- Graph-based workflow definition with handoffs
- Checkpointing/persistence
- Human-in-the-loop interrupts
- Multi-agent coordination patterns

However, analysing our agent design revealed:

1. **Agents operate independently** - They don't hand off to each other mid-process
2. **Neo4j is the shared state store** - No need for LangGraph's checkpointing
3. **Redis Streams already provides message passing** - Event coordination is handled
4. **neo4j-graphrag handles the RAG pipeline** - Librarian doesn't need LangGraph wrapper
5. **Human-in-the-loop not required initially** - Key LangGraph feature unused

```
Builder ───────────────────────────────────────────► (continuous, per-chunk)
Gardener ──────●──────────●──────────●─────────────► (scheduled, every 60-90s)
Researcher ────○─────○─────○─────○─────○───────────► (event-triggered)
Librarian ─────────────────────────────────────────► (on-demand, user query)
```

The agents are **independent workers on shared state**, not a **complex agent graph requiring handoffs**.

## Decision

Use plain Python async functions with Redis Streams for agent coordination instead of LangGraph.

### Agent Implementation Pattern

```python
# Builder - async function consuming Redis Streams
async def builder(chunk: TranscriptChunk, session_id: str):
    entities = await extract_entities(chunk)
    await write_to_neo4j(entities)
    
    # Trigger Researcher for low-confidence entities (non-blocking)
    for entity in entities:
        if entity.confidence < 0.7 or entity.type == "organisation":
            await redis.xadd("research_queue", {"node_id": entity.id})
    
    await broadcast_sse("node_added", entities)

# Gardener - scheduled task
async def gardener_loop():
    while True:
        await asyncio.sleep(60)
        graph_state = await get_graph_state()
        actions = await garden_graph(graph_state)
        await apply_actions(actions)

# Researcher - event-triggered consumer
async def researcher_loop():
    while True:
        messages = await redis.xreadgroup("research_group", "researcher_1", 
                                          {"research_queue": ">"}, block=5000)
        for msg in messages:
            await enrich_node(msg["node_id"])
            await redis.xack("research_queue", "research_group", msg.id)

# Librarian - uses neo4j-graphrag directly
async def librarian(query: str, session_id: str):
    return await rag.search(query)
```

### Coordination Architecture

```
                          ┌─────────────────┐
Audio ──► STT ──► Chunks ─┤ Redis Streams   ├──► Builder ──► Neo4j
                          │   (chunks)      │                 │
                          └────────┬────────┘                 │
                                   │                          ▼
                          ┌────────▼────────┐            ┌────────┐
                          │ Redis Streams   │◄───────────│ SSE    │
                          │   (research)    │            │ Stream │
                          └────────┬────────┘            └────────┘
                                   │
                                   ▼
                              Researcher ──► Neo4j
```

## Consequences

### Positive
- **Simpler architecture** - No LangGraph abstraction layer to learn/debug
- **Fewer dependencies** - One less major library
- **Easier debugging** - Standard Python async, no state machine traces
- **Dynamic enrichment preserved** - Builder can still trigger Researcher via events
- **Same functionality** - All agent behaviours achievable

### Negative
- **Must implement retry logic ourselves** - LangGraph provides this
- **No built-in checkpointing** - If needed, must use Redis/Neo4j explicitly
- **Revisit if requirements change** - Human-in-the-loop would benefit from LangGraph

### Neutral
- **Different mental model** - Event-driven vs graph-based workflows
- **Redis Streams becomes more critical** - Central coordination point

## Alternatives Considered

### Alternative 1: LangGraph for All Agents
- Description: Use LangGraph StateGraph for full agent orchestration
- Why rejected: Adds complexity without solving problems we have; agents don't need handoffs

### Alternative 2: LangGraph for Gardener Only
- Description: Use LangGraph just for Gardener's multi-step task sequence
- Why rejected: Gardener's tasks are sequential and simple; a `for` loop suffices

### Alternative 3: Celery Task Queue
- Description: Use Celery for distributed task execution
- Why rejected: Overkill for single-instance deployment; Redis Streams simpler

## Related

- [ARCHITECTURE_ADVISORY.md](../../ARCHITECTURE_ADVISORY.md) - Main architecture document
- [ADR-001](./0001-llm-clustering-over-gds.md) - Related simplification decision
- [neo4j-graphrag docs](../_libraries_docs/nlp_graph_libs/neo4j_graphrag_docs.md) - Librarian uses this directly

## Notes

**Revisit triggers:**
- If human-in-the-loop approval for merges becomes a requirement
- If agent handoffs become necessary (e.g., Builder must wait for Researcher)
- If debugging async flows becomes too complex

**Future consideration:** If we do need LangGraph later, the transition would be straightforward since each agent is already a discrete async function.


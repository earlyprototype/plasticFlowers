# ADR-004: Full Context Q&A (No GraphRAG for Single Session)

## Status

Accepted

## Date

2025-12-26

## Context

The Librarian agent needs to answer questions about recorded sessions. Two approaches:

1. **GraphRAG Pipeline** - Vector search -> Graph expansion -> LLM answer
2. **Full Context** - Load entire session into LLM context -> Direct answer

Key observations:
- 90-minute session = ~25,000 tokens (transcript + nodes + relationships)
- Gemini 2.5/3 Pro has 1M token context window
- 25,000 tokens = 2.5% of available context
- GraphRAG adds complexity (vector index, retrieval tuning)

## Decision

Use **Full Context Q&A** for single-session queries.

```
User Question
    |
    v
Load: Full transcript + All nodes + All relationships
    |
    v
LLM answers with complete visibility
```

GraphRAG will be used only for:
- Cross-session queries ("What have I learned about X across all talks?")
- When single-session context exceeds practical limits

## Consequences

### Positive
- Simpler implementation (no vector index tuning)
- Better answers (LLM sees everything)
- No retrieval failures (nothing is filtered out)
- Faster to ship

### Negative
- Higher cost per query (~$0.05 vs ~$0.01)
- Slower response time (~2-3s vs ~1s)
- Won't scale to very long sessions

### Neutral
- Neo4j still stores all data (just loaded fully)
- GraphRAG can be added for cross-session later

## Alternatives Considered

### Alternative 1: GraphRAG (Hybrid Retrieval)
- Vector search for relevant nodes
- Graph expansion for context
- More efficient at scale
- Rejected: Unnecessary complexity for single-session

### Alternative 2: Chunked Retrieval
- Split session into chunks
- Retrieve most relevant chunks
- Lower cost
- Rejected: May miss important context

### Alternative 3: Summary-Based
- Pre-compute session summaries
- Answer from summaries
- Very fast
- Rejected: Loses detail, can't cite specific moments

## Related

- `@_docs/ARCHITECTURE_ADVISORY.md` - Section 3.4: Librarian
- `@_docs/LITE_ARCHITECTURE.md` - Section 5.2: GeminiClient.askQuestion()
- `@_docs/_dev/_libraries_docs/nlp_graph_libs/neo4j_graphrag_docs.md`

## Notes

Cost comparison:
- Full context: ~$0.05 per query
- GraphRAG: ~$0.01 per query
- For 10 queries/session: $0.50 vs $0.10

Break-even point: When you're asking 50+ questions per session, GraphRAG becomes worthwhile.

Future consideration: Implement GraphRAG when:
- Cross-session Q&A is needed
- Sessions regularly exceed 2 hours
- Cost becomes a concern


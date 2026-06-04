# ADR-001: LLM-Only Clustering (No GDS Initially)

## Status

Accepted

## Date

2025-12-26

## Context

plasticFlower needs to cluster related nodes into "Flowers" (semantic groups). Two approaches were considered:

1. **Neo4j Graph Data Science (GDS)** - Use Leiden algorithm for community detection
2. **LLM Reasoning** - Use Gemini to semantically cluster nodes based on context

Key factors:
- Sessions produce ~50-100 nodes (small graphs)
- Gemini 2.5/3 Pro has 1M token context window
- Full session (~25,000 tokens) fits easily in context
- GDS requires additional setup and learning curve
- LLM can use semantic understanding, not just graph structure

## Decision

Use **LLM-only clustering** for initial implementation. The Gardener agent will:
1. Receive full graph state (nodes, relationships) in context
2. Use semantic reasoning to identify clusters
3. Return Flower definitions with stem nodes and members

GDS will be added later if:
- Graphs exceed 100+ nodes regularly
- Performance becomes an issue
- Cross-session clustering is needed

## Consequences

### Positive
- Simpler implementation (no GDS setup)
- Semantic clustering (understands meaning, not just connections)
- Flexible (LLM can reason about edge cases)
- Faster to ship

### Negative
- Higher API cost per Gardener cycle (~$0.02 vs ~$0.005)
- Slower than algorithm-based clustering
- Less reproducible (LLM may vary)

### Neutral
- Neo4j still required for persistence
- Can add GDS later without breaking changes

## Alternatives Considered

### Alternative 1: GDS Leiden Algorithm
- Uses graph structure for community detection
- Very fast and reproducible
- Rejected: Overkill for small graphs, steeper learning curve

### Alternative 2: Hybrid (GDS + LLM)
- GDS for initial clustering, LLM for refinement
- Best of both worlds
- Rejected: Too complex for initial implementation

## Related

- `@_docs/ARCHITECTURE_ADVISORY.md` - Section 8: Implementation Roadmap
- `@_docs/LEARNING_GUIDE.md` - Phase F (GDS, now optional)
- `@_docs/_dev/_libraries_docs/nlp_graph_libs/neo4j_gds_docs.md`

## Notes

Revisit this decision when:
- Average session produces 100+ nodes
- Cross-session clustering becomes a priority
- Cost of Gardener cycles becomes significant


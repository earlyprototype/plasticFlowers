# ADR-0011: Pre-Creation Similarity Check in Builder

## Status

Accepted

## Date

2025-12-30

## Context

Currently, Builder creates GHOST nodes for every extracted entity without checking if similar entities already exist. Gardener then handles deduplication in subsequent cycles by merging similar nodes. This creates several issues:

1. **Excess GHOST nodes:** The graph accumulates many temporary duplicates before Gardener runs
2. **Inaccurate mention counts:** The `mentions` property doesn't increment until Gardener merges
3. **UI churn:** Users see `node_added` followed by `node_merged` events, causing visual instability
4. **Wasted Gardener effort:** Gardener spends LLM tokens on deduplication that could be prevented

The vector index and similarity infrastructure already exist (`run_similarity()` in `similarity.py`), but are only used in tests, not in the live Builder flow.

## Decision

**Implement pre-creation similarity checking in Builder before creating nodes.**

For each extracted entity:
1. Generate embedding using Google text-embedding-004
2. Query Neo4j vector index for similar nodes (threshold: 0.92)
3. If match found AND types compatible AND confidence >= 0.7:
   - Increment `mentions` on existing node
   - Map extracted label to existing node ID for relationships
   - Broadcast `node_updated` SSE event
4. If no match:
   - Create new GHOST node with embedding
   - Broadcast `node_added` SSE event
5. Create relationships using the label-to-ID mapping (pointing to canonical nodes)

**Disambiguation mitigations:**
- **Type matching:** Only match if `inferred_type` values are compatible (e.g., both "organisation" or both in compatible group like {"technology", "framework", "tool"})
- **Confidence threshold:** Require LLM extraction confidence >= 0.7 to match
- **Fallback:** If embedding or similarity query fails, create new GHOST node (Gardener handles edge cases)

## Consequences

### Positive
- Fewer GHOST nodes created (cleaner graph state from the start)
- Accurate mention counts in real-time
- Relationships concentrate on canonical nodes immediately
- Smoother UI experience (fewer node_added + node_merged sequences)
- Reduced Gardener workload (less deduplication needed)
- More efficient use of LLM tokens

### Negative
- Additional latency per chunk (+200-500ms for embedding + vector query)
- Risk of false positive matches (mitigated by type checking and confidence threshold)
- More complex Builder logic (but follows established patterns)

### Neutral
- Gardener still handles edge cases (synonyms, abbreviations with different embeddings)
- Similarity threshold (0.92) already tuned in ADR-008

## Alternatives Considered

### Alternative 1: Keep Current Approach (Gardener-Only Deduplication)
- Description: Continue letting Gardener handle all deduplication
- Why rejected: Causes UI churn, wastes tokens, inaccurate mention counts

### Alternative 2: Synchronous Batch Similarity Check
- Description: Collect all extracted entities, check similarity in one batch query
- Why rejected: More complex, marginal performance gain, harder to debug

### Alternative 3: LLM-Based Pre-Creation Check
- Description: Ask LLM to compare extracted entity against existing nodes
- Why rejected: Much slower, more expensive, vector similarity is sufficient for most cases

## Related

- [ADR-008](./0008-similarity-threshold-tuning.md) - Similarity threshold tuned to 0.92
- [ADR-010](./0010-ratio-based-agent-triggering.md) - Ratio-based triggering (affects Gardener frequency)
- `backend/app/services/similarity.py` - Existing similarity infrastructure
- `backend/app/services/builder_service.py` - Implementation location
- `_docs/_evidence/vector_index_architecture.md` - Detailed architecture documentation

## Rollback Strategy

If pre-creation similarity checking causes issues in production:

1. **Immediate disable:** Set `SIMILARITY_CHECK_ENABLED=false` in environment
2. **No code changes required** - Builder reverts to creating all nodes as GHOST
3. **Gardener handles cleanup** - Deduplication continues via Gardener merge cycles
4. **No data loss** - Worst case is more GHOST nodes than optimal

This makes the feature safe to deploy incrementally.

## Notes

Implementation should include:
- Config flag `similarity_check_enabled` for easy disable during debugging
- Type compatibility helper function `_types_compatible()`
- Fallback to node creation if embedding fails
- Logging for match/no-match decisions

Future enhancements (not in initial implementation):
- Phrase length filter (skip similarity for very short labels)
- Context embedding (include surrounding chunk text)
- LLM disambiguation for ambiguous high-similarity matches


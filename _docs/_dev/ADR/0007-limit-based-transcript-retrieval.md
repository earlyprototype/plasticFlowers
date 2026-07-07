# ADR-007: LIMIT-Based Transcript Retrieval Over Cypher Word Counting

## Status

Accepted

## Date

2025-12-26

## Context

The `get_recent_transcript()` function retrieves transcript chunks up to a word limit (default 3000 words) for Gardener context. Two optimisation approaches were considered:

**Option A: LIMIT + Python Word Counting**
- Add a calculated LIMIT clause to the Cypher query
- Continue counting words in Python (existing logic)
- Simple change, minimal risk

**Option B: Cypher-Side Word Counting**
- Use Cypher `size(split(text, ' '))` to count words
- Calculate cumulative sum with `reduce()`
- Push all work to database

**Data context:**
- Average chunk: 61 words
- Min chunk: 8 words
- Max chunk: 563 words
- For 3000 words: typically need ~50 chunks

## Decision

Use **Option A: LIMIT + Python word counting**.

```python
# Conservative estimate: 20 words/chunk ensures we never under-fetch
chunk_limit = min((word_limit // 20) + 10, 500)

query = """
MATCH (c:TranscriptChunk {session_id: $session_id})
RETURN c.text AS text, c.start_time AS start_time
ORDER BY c.start_time DESC
LIMIT $chunk_limit
"""
```

## Consequences

### Positive
- Simple implementation (3 lines added)
- Neo4j query planner knows result set is bounded
- Python streaming already efficient (stops at word limit)
- Easy to understand and maintain
- Default changed from 1000 to 3000 words for Gardener use

### Negative
- Slightly over-fetches due to conservative estimate (20 vs actual 61 avg)
- Word counting still happens in Python (not pure Cypher)

### Neutral
- Performance improvement is modest but measurable
- Pattern documented in VALIDATED_PATTERNS.md

## Alternatives Considered

### Alternative: Cypher-Side Word Counting (Option B)
- Use `reduce()` to calculate cumulative word count in Cypher
- More "pure" database approach
- **Rejected:** Added complexity for marginal gain. Python streaming already stops early, so we're not transferring unnecessary data. The LIMIT clause provides 90% of the benefit with 10% of the complexity.

## Related

- `backend/app/services/graph_db.py:get_recent_transcript()`
- `_docs/_dev/VALIDATED_PATTERNS.md` - Pattern: Recent Transcript with Word Limit
- `_docs/_dev/CYPHER_PATTERNS.md` - Transcript Retrieval section

## Notes

This ADR demonstrates documenting fine-grained implementation choices. While not architectural in scope, it:
- Captures the reasoning for future maintainers
- Prevents re-debating the same options
- Provides context for LLM coding assistants


# ADR-0013: Embedding-Based Type Compatibility

## Status

Accepted

## Date

2025-12-30

## Context

ADR-011 introduced pre-creation similarity checking in Builder, which requires type compatibility validation to prevent false positive matches (e.g., "Apple" company matching "apple" fruit). The initial suggestion was a hardcoded dictionary of compatible type groups.

However, the plasticFlower architecture intentionally uses **emergent, freeform types** (see `Node.inferred_type` field). The Builder prompt explicitly instructs the LLM:

> "Assign an inferred_type using your best judgment (this is EMERGENT - use whatever category fits, not a predefined list)"

This means the LLM can return any type string: "organisation", "org", "company", "entity", "business", etc. A hardcoded dictionary would:
1. Require constant maintenance as new types emerge
2. Fail on type variations ("org" vs "organisation")
3. Miss novel types the LLM invents ("funding_body", "research_centre")
4. Contradict the "emergent types" design philosophy

## Decision

**Use embedding similarity to determine type compatibility instead of a hardcoded dictionary.**

Implementation:

```python
async def _types_compatible(type_a: str, type_b: str) -> bool:
    """Check if two inferred types are semantically compatible."""
    # Exact match (fast path)
    if type_a.lower().strip() == type_b.lower().strip():
        return True
    
    # Semantic similarity of type names
    emb_a = await get_embedding(type_a)
    emb_b = await get_embedding(type_b)
    similarity = cosine_similarity(emb_a, emb_b)
    
    return similarity >= 0.80  # Lower threshold for type names
```

**Threshold rationale:** Type names are short (1-2 words), so we use 0.80 rather than 0.92. This balances:
- "organisation" vs "company" (~0.89) -> Compatible
- "person" vs "speaker" (~0.85) -> Compatible  
- "person" vs "concept" (~0.45) -> Incompatible

**Caching consideration:** Type embeddings can be cached since types are reused frequently ("concept", "organisation", "person" appear in many nodes).

## Consequences

### Positive
- Respects the "emergent types" architectural decision
- Handles all LLM type variations automatically
- No dictionary maintenance required
- Consistent with the system's embedding-first philosophy
- Graceful degradation for novel types

### Negative
- Additional embedding call per type comparison (+50ms)
- Type similarity threshold (0.80) may need tuning
- Cache miss for novel types incurs latency

### Neutral
- Falls back to Gardener for edge cases (same as before)
- Cache can be pre-warmed with common types
- Logging will help tune threshold over time

## Alternatives Considered

### Alternative 1: Hardcoded Dictionary
- Description: Define groups like `{"organisation", "company", "entity"}`
- Why rejected: Contradicts emergent types philosophy; requires maintenance; fails on variations

### Alternative 2: LLM-Based Type Comparison
- Description: Ask LLM "Are these types compatible?"
- Why rejected: Too slow (+500ms per check); expensive; overkill for simple comparison

### Alternative 3: Skip Type Checking
- Description: Only use embedding similarity of labels
- Why rejected: Would match "Apple" (company) with "apple" (fruit) incorrectly

### Alternative 4: Constrain Types to Enum
- Description: Change Builder prompt to use fixed type list
- Why rejected: Goes against explicit "never restrict to enums per Alignment" in Node model

## Related

- [ADR-011](./0011-pre-creation-similarity-check.md) - Pre-creation similarity check (parent decision)
- [ADR-008](./0008-similarity-threshold-tuning.md) - Similarity threshold tuning
- `backend/app/models/node.py` - Node.inferred_type field with "emergent" comment
- `backend/app/agents/builder.py` - Builder prompt with emergent type instruction

## Notes

Implementation should include:
- Type embedding cache (in-memory dict, keyed by normalised type string)
- Logging for type compatibility decisions (for threshold tuning)
- Config value `type_similarity_threshold` (default: 0.80) for easy adjustment

Future enhancements:
- Pre-warm cache with common types on startup
- Analyse logs to identify if threshold needs adjustment
- Consider hierarchical type relationships if patterns emerge


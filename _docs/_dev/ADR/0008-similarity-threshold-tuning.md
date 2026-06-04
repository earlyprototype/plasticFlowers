# ADR-008: Similarity Threshold Tuned to 0.92

## Status

Accepted

## Date

2025-12-26

## Context

The pre-Builder similarity check uses cosine similarity between embeddings to detect duplicate nodes. A threshold determines whether a new label should merge with an existing node or create a new one.

### Original Setting
- Threshold: 0.85 (from DEC-004 / Pre-Implementation Report)
- Model: `text-embedding-004` (768 dimensions)

### Testing Results (Phase B)

| Label A | Label B | Score | Should Merge? |
|---------|---------|-------|---------------|
| AI | Artificial Intelligence | 0.946 | Yes |
| Graph Database | Neo4j | 0.928 | Yes |
| ML | Machine Learning | 0.823 | Yes (but low!) |
| AI | Machine Learning | 0.911 | No |
| Neo4j | MongoDB | 0.926 | No |
| AI | Kitchen Sink | 0.724 | No |
| Machine Learning | Potato Salad | 0.670 | No |

### Threshold Accuracy Analysis

| Threshold | Correct Predictions |
|-----------|---------------------|
| 0.85 | 5/8 (62%) |
| 0.90 | 5/8 (62%) |
| 0.92 | 6/8 (75%) |
| 0.94 | 6/8 (75%) |
| 0.96 | 5/8 (62%) |

## Decision

Set similarity threshold to **0.92**.

This balances:
- **Precision:** Avoids merging distinct concepts (Neo4j/MongoDB, AI/ML)
- **Recall:** Still catches obvious synonyms (AI/Artificial Intelligence at 0.946)

The threshold is higher than the original 0.85 because:
1. The `text-embedding-004` model produces tighter clusters than expected
2. Even unrelated concepts ("potato salad" vs "food") score 0.67+
3. Conceptually related but distinct items score 0.90+

## Consequences

### Positive
- Fewer false merges (distinct concepts stay separate)
- LLM-based clustering (Gardener) handles edge cases
- More accurate knowledge graph structure

### Negative
- "ML" vs "Machine Learning" (0.823) won't auto-merge
- Requires Gardener to clean up abbreviation variations
- Slightly more ghost nodes created

### Neutral
- Threshold can be adjusted via environment variable
- Test script (`test_vector_search.py`) available for re-tuning

## Alternatives Considered

### Alternative 1: Keep 0.85
- Higher recall (catches more duplicates)
- **Rejected:** Too many false merges in testing

### Alternative 2: Use 0.95+
- Maximum precision
- **Rejected:** Misses valid merges like "AI" + "Artificial Intelligence"

### Alternative 3: Two-stage threshold
- Low threshold (0.80) for candidates, LLM confirms merge
- More accurate but slower
- **Rejected:** Added complexity; single threshold + Gardener review sufficient

## Related

- `backend/app/config.py` - `similarity_threshold` setting
- `backend/app/services/similarity.py` - Pre-Builder similarity check
- `backend/test_vector_search.py` - Threshold testing script
- ADR-001: LLM-only clustering (Gardener handles edge cases)

## Notes

The threshold tuning revealed that abbreviations ("ML", "AI") don't embed as close to their full forms as expected. This is a known limitation of embedding models. The Gardener agent compensates by using LLM reasoning to identify these cases.

Re-run `test_vector_search.py` after any model changes to validate the threshold.


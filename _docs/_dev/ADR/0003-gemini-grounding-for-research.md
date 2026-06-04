# ADR-003: Gemini Grounding for Research (Tavily Fallback)

## Status

Accepted

## Date

2025-12-26

## Context

The Researcher agent needs to enrich unfamiliar terms with external information:
- Organisation websites
- Funding scheme details
- Definitions of technical concepts

Two primary options for web search integration:
1. **Gemini Grounding** - Built-in Google Search within Gemini API
2. **Tavily API** - Dedicated search API designed for LLM applications

## Decision

Use **Gemini Grounding** as the default search mechanism, with Tavily as a fallback.

```
Primary: Gemini 2.0 Flash with Google Search grounding
Fallback: Tavily API (if grounding fails or for specific use cases)
```

## Consequences

### Positive
- Single API (Gemini) for most operations
- Simpler implementation (no additional API key)
- Google Search quality for general queries
- Native integration (no result parsing needed)

### Negative
- Less control over search parameters
- May not find niche/local organisations
- Dependent on Google's grounding implementation

### Neutral
- Tavily can be added later for specific needs
- Both options have similar cost profiles

## Alternatives Considered

### Alternative 1: Tavily Only
- Dedicated search API, designed for LLM use
- Rich metadata, good for citations
- Rejected: Additional API key, more complexity for initial build

### Alternative 2: Multiple Search APIs
- Use different APIs for different entity types
- Best coverage
- Rejected: Over-engineering for POC

### Alternative 3: No Web Search (APIs Only)
- Use structured APIs (Wikipedia, Semantic Scholar, etc.)
- More reliable, structured data
- Rejected: Won't find local organisations or funding schemes

## Related

- `@_docs/ARCHITECTURE_ADVISORY.md` - Section 3.3: Researcher
- `@_docs/LITE_ARCHITECTURE.md` - Section 6: Research
- Gemini grounding docs: https://ai.google.dev/gemini-api/docs/grounding

## Notes

When to consider adding Tavily:
- Gemini grounding fails frequently for local entities
- Need more control over search depth/filters
- Citations become important (Tavily provides better source metadata)

Integration pattern for fallback:
```python
try:
    result = await gemini_with_grounding(query)
except GroundingFailedError:
    result = await tavily_search(query)
```


# ADR-002: Proofreading Merged into Gardener

## Status

Accepted

## Date

2025-12-26

## Context

Speech-to-text (STT) introduces errors, especially for:
- Proper nouns ("CeADAR" transcribed as "see dare")
- Technical terms ("UKRI" as "you carry")
- Acronyms and abbreviations

These errors propagate to node labels and remain visible throughout the session.

Two approaches were considered:
1. **Separate Proofreader Agent** - Dedicated agent running on a different cycle
2. **Merged into Gardener** - Proofreading as first step of Gardener cycle

## Decision

Merge proofreading into the **Gardener agent** as its first task.

The Gardener will:
1. Review transcript chunks for STT errors
2. Identify corrections with confidence scores
3. Update session vocabulary (learned corrections)
4. Apply corrections to nodes and chunks
5. Then proceed with confirm/merge/cluster tasks

## Consequences

### Positive
- Single agent with full transcript context (no context duplication)
- Shared vocabulary state
- Simpler architecture (fewer agents)
- Corrections applied before clustering decisions

### Negative
- Gardener cycle is longer (~500ms extra)
- Single point of failure for proofreading
- Gardener prompt is more complex

### Neutral
- Vocabulary persists per-session
- Corrections are incremental (new chunks only)

## Alternatives Considered

### Alternative 1: Separate Proofreader Agent
- Dedicated agent on faster cycle (30s vs 60s)
- Focused prompt, smaller context
- Rejected: Context duplication, more coordination complexity

### Alternative 2: Real-time Proofreading (per chunk)
- Proofread immediately when chunk arrives
- Fastest corrections
- Rejected: Too expensive (API call per chunk), less context for decisions

### Alternative 3: Pre-process with Vocabulary Only
- Apply known vocabulary before LLM extraction
- No new error detection
- Rejected: Can't catch new errors, vocabulary bootstrap problem

## Related

- `@_docs/ARCHITECTURE_ADVISORY.md` - Section 3.2: Gardener
- `@_docs/_archive/LITE_ARCHITECTURE.md` - Section 5.3: SessionController.runGardener()
- `@backend/app/agents/gardener.py`

## Notes

The vocabulary learning aspect is critical:
- Once "see dare" -> "CeADAR" is learned, it's applied to all future chunks
- Vocabulary should persist across sessions (future enhancement)
- Consider confidence threshold for auto-apply (0.9+)


# ADR-0012: Centralised Gemini Config Helper Pattern

## Status

Accepted

## Date

2025-12-30

## Context

Gemini 2.5 models have "thinking mode" enabled by default, which adds 60+ seconds of internal reasoning before producing output. This was discovered during debugging (2025-12-28) and documented in VALIDATED_PATTERNS.

The fix (`thinking_budget=0`) must be applied to every agent that uses Gemini for structured output. Currently, each agent (Builder, Gardener) configures Gemini inline. As we add more agents (Researcher, Librarian), we risk:

1. **Forgetting the fix:** New agents might omit `thinking_budget=0` and suffer 60s+ delays
2. **Inconsistent configuration:** Different agents might use different settings
3. **Scattered knowledge:** The critical config is buried in each agent's code
4. **Repeated debugging:** Future developers might re-discover this issue the hard way

## Decision

**Create a centralised helper function for Gemini configuration that enforces critical defaults.**

```python
# backend/app/services/llm_utils.py

from google.genai import types

def create_gemini_config(
    response_schema: type,
    thinking_budget: int = 0,  # Disabled by default - saves 60s+
    temperature: float = 0.7,
    max_output_tokens: int = 8192,
) -> types.GenerateContentConfig:
    """
    Create Gemini config with correct defaults for structured output.
    
    CRITICAL: Gemini 2.5 has thinking mode ON by default, adding 60+ seconds
    to each call. This helper ensures it's disabled unless explicitly needed.
    """
    return types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        response_mime_type="application/json",
        response_schema=response_schema,
        thinking_config=types.ThinkingConfig(thinking_budget=thinking_budget),
    )
```

**All agents MUST use this helper instead of configuring Gemini directly.**

## Consequences

### Positive
- Single source of truth for Gemini configuration
- Critical fix (`thinking_budget=0`) cannot be forgotten
- New agents automatically inherit correct defaults
- Docstring warns developers about the 60s+ issue
- Easy to update configuration globally if Gemini behaviour changes

### Negative
- Additional indirection (minor)
- Must update existing agents to use helper (one-time cost)

### Neutral
- Helper is optional for non-structured-output uses (e.g., streaming Q&A)
- Thinking mode can still be enabled via parameter if genuinely needed

## Alternatives Considered

### Alternative 1: Document in VALIDATED_PATTERNS Only
- Description: Keep the pattern documented but let each agent copy it
- Why rejected: Risk of forgetting, inconsistent implementation, scattered knowledge

### Alternative 2: Global Config Object
- Description: Single config object imported by all agents
- Why rejected: Less flexible - agents need different schemas and sometimes different parameters

### Alternative 3: Decorator Pattern
- Description: Decorator that wraps agent methods with correct Gemini config
- Why rejected: Over-engineered for this use case, helper function is simpler

## Related

- VALIDATED_PATTERNS.md: "Disable Gemini 2.5 Thinking Mode for Speed" pattern
- SOLUTIONS_LOG.md: 2025-12-28 entry on 68-second LLM calls
- `backend/app/agents/builder.py` - Will use helper
- `backend/app/agents/gardener.py` - Will use helper
- Future: Researcher, Librarian agents will use helper

## Notes

Implementation checklist:
- [ ] Create `backend/app/services/llm_utils.py`
- [ ] Update Builder to use `create_gemini_config()`
- [ ] Update Gardener to use `create_gemini_config()`
- [ ] Add to agent development checklist in LLM_DEVELOPMENT_GUIDE.md

This pattern should be extended for any future "must not forget" configuration across agents.


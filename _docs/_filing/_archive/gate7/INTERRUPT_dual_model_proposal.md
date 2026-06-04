# Gate 7 Interrupt: Dual LLM Model Architecture Proposal

**Date:** 2024-12-17  
**Author:** LLM Assistant  
**Status:** Awaiting Director Approval  
**Blocking:** Gate 7 completion (smoke test, 10-minute demo)

---

## Executive Summary

Gate 7 testing revealed that the current single-model LLM architecture is hitting API quota limits during development. This proposal recommends a small architectural change (~30 lines of code) to support separate models for the Builder and Gardener agents, enabling optimal model selection based on each agent's usage patterns and requirements.

---

## Problem Statement

### Immediate Blockers

1. **API Quota Exhaustion (429 Rate Limit)**
   - Current model `gemini-2.0-flash` has 200 requests/day free tier limit
   - Exhausted during Gate 7 testing on 2024-12-17
   - Blocks smoke test and 10-minute real Gemini demo

2. **Model Deprecation**
   - Original model `gemini-1.5-flash` returned HTTP 404
   - Discovered to be deprecated as of November 2025
   - Required emergency switch to `gemini-2.0-flash`

3. **Windows IPv6 Fallback (Separate Issue)**
   - 21-second delay per HTTP request on Windows
   - Documented workaround: disable IPv6 on network adapter
   - Not addressed by this proposal

---

## Google Gemini API Models - Complete Analysis (December 2025)

### Gemini 3 Series (NEW - Released 17 December 2025)

| Model | API Name | RPM | TPM | RPD | Strengths |
|-------|----------|-----|-----|-----|-----------|
| Gemini 3 Pro | `gemini-3-pro` | 5-10 | 250K | 50 | Advanced reasoning, multimodal, agentic coding |
| Gemini 3 Flash | `gemini-3-flash` | TBD | TBD | TBD | Speed + cost efficiency, reasoning from 3 Pro |

### Gemini 2.5 Series

| Model | API Name | RPM | TPM | RPD | Strengths |
|-------|----------|-----|-----|-----|-----------|
| Gemini 2.5 Pro | `gemini-2.5-pro` | 5 | 250K | 100 | ❌ **Paid tier only** - no longer free |
| Gemini 2.5 Flash | `gemini-2.5-flash` | 10 | 250K | 250 | Good quality, moderate volume |
| Gemini 2.5 Flash-Lite | `gemini-2.5-flash-lite` | 15 | 250K | **1,000** | ⭐ **Best free tier volume** |
| Gemini 2.5 Flash Native Audio | `gemini-2.5-flash-native-audio` | - | - | - | Voice interactions |

### Gemini 2.0 Series

| Model | API Name | RPM | TPM | RPD | Strengths |
|-------|----------|-----|-----|-----|-----------|
| Gemini 2.0 Flash | `gemini-2.0-flash` | 15 | 1M | 200 | **Current default** - good TPM |
| Gemini 2.0 Flash-Lite | `gemini-2.0-flash-lite` | 30 | 1M | 200 | Fastest RPM |

### Gemini 1.5 Series (Legacy)

| Model | API Name | RPM | TPM | RPD | Status |
|-------|----------|-----|-----|-----|--------|
| Gemini 1.5 Pro | `gemini-1.5-pro` | 2 | 32K | 50 | Available, 2M context |
| Gemini 1.5 Flash | `gemini-1.5-flash` | - | - | - | ⚠️ **DEPRECATED Nov 2025** |
| Gemini 1.5 Flash-8B | `gemini-1.5-flash-8b` | - | - | - | Small/cheap |

### Embedding Model

| Model | API Name | RPM | TPM | RPD |
|-------|----------|-----|-----|-----|
| Text Embedding 004 | `models/text-embedding-004` | 100 | 30K | 1,000 |

### Key Observations

1. **Free tier limits have been reduced** - Google cut limits in late November 2025
2. **Gemini 2.5 Pro removed from free tier** - now paid only
3. **Gemini 3 series just launched** - limits still being established
4. **Best free tier option:** `gemini-2.5-flash-lite` with 1,000 RPD

---

## Current Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      config.py                               │
│  gemini_model = "gemini-2.0-flash"  (single model)          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       llm.py                                 │
│  _MODEL: GenerativeModel | None  (single cached instance)   │
│  generate_structured_json(prompt, schema)                    │
└─────────────────────────────────────────────────────────────┘
                    │                   │
                    ▼                   ▼
            ┌───────────┐       ┌─────────────┐
            │  Builder  │       │  Gardener   │
            │  Agent    │       │  Agent      │
            └───────────┘       └─────────────┘
                    │                   │
                    └───────┬───────────┘
                            ▼
                   Same model, same quota
```

### Problem

- Builder runs on **every chunk** (high frequency)
- Gardener runs **periodically** (lower frequency, needs reasoning)
- Both compete for the same 200 RPD quota
- No way to optimise model selection per agent

---

## Proposed Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      config.py                               │
│  gemini_model_builder = "gemini-2.5-flash-lite"  (1000 RPD) │
│  gemini_model_gardener = "gemini-3-pro"          (50 RPD)   │
└─────────────────────────────────────────────────────────────┘
                    │                   │
                    ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│                       llm.py                                 │
│  _MODELS: dict[str, GenerativeModel]  (cached by name)      │
│  generate_structured_json(prompt, schema, model=None)        │
└─────────────────────────────────────────────────────────────┘
                    │                   │
                    ▼                   ▼
            ┌───────────┐       ┌─────────────┐
            │  Builder  │       │  Gardener   │
            │  (flash)  │       │  (pro)      │
            └───────────┘       └─────────────┘
                    │                   │
                    ▼                   ▼
            1,000 RPD quota      50 RPD quota
            Fast, high volume    Smart, periodic
```

---

## Implementation Plan

### Files to Modify

| File | Changes | Lines |
|------|---------|-------|
| `backend/app/config.py` | Add `gemini_model_builder` and `gemini_model_gardener` fields | +10 |
| `backend/app/services/llm.py` | Change `_MODEL` to `_MODELS` dict, add `model` param to `generate_structured_json` | +15 |
| `backend/app/agents/builder.py` | Pass `model=settings.gemini_model_builder` | +3 |
| `backend/app/agents/gardener.py` | Pass `model=settings.gemini_model_gardener` | +3 |
| `.env.example` | Document new config options | +4 |

**Total: ~35 lines of code**

### Config Changes

```python
# backend/app/config.py

# Builder: high volume, fast extraction
gemini_model_builder: str = Field(
    "gemini-2.5-flash-lite",
    description="Model for Builder agent (high volume, fast).",
)

# Gardener: periodic review, needs reasoning
gemini_model_gardener: str = Field(
    "gemini-3-pro",
    description="Model for Gardener agent (periodic, smart reasoning).",
)

# Keep legacy field for backward compatibility
gemini_model: str = Field(
    "gemini-2.5-flash-lite",
    description="Default model (deprecated, use agent-specific fields).",
)
```

### LLM Service Changes

```python
# backend/app/services/llm.py

_MODELS: dict[str, genai.GenerativeModel] = {}
_MODELS_LOCK = threading.Lock()

async def generate_structured_json(
    prompt: str,
    *,
    schema: SchemaInput,
    model: str | None = None,  # NEW: optional model override
) -> Mapping[str, Any]:
    ...

def _get_model(settings, model_name: str | None = None) -> genai.GenerativeModel:
    name = model_name or settings.gemini_model
    if name in _MODELS:
        return _MODELS[name]
    
    with _MODELS_LOCK:
        if name in _MODELS:
            return _MODELS[name]
        
        api_key = settings.gemini_api_key.get_secret_value()
        if not api_key:
            raise LLMError("GEMINI_API_KEY is not configured")
        
        genai.configure(api_key=api_key)
        _MODELS[name] = genai.GenerativeModel(model_name=name)
        return _MODELS[name]
```

---

## Recommended Model Configuration

### Option A: Maximum Free Tier Volume (Recommended for Development)

| Agent | Model | RPD | Reasoning |
|-------|-------|-----|-----------|
| Builder | `gemini-2.5-flash-lite` | 1,000 | High volume extraction, fast |
| Gardener | `gemini-2.5-flash` | 250 | Moderate reasoning, good volume |
| **Combined** | | **1,250** | 6× more than current |

### Option B: Best Quality (Recommended for Production)

| Agent | Model | RPD | Reasoning |
|-------|-------|-----|-----------|
| Builder | `gemini-2.5-flash` | 250 | Better extraction quality |
| Gardener | `gemini-3-pro` | 50 | Best reasoning for deduplication |
| **Combined** | | **300** | Higher quality outputs |

### Option C: Balanced

| Agent | Model | RPD | Reasoning |
|-------|-------|-----|-----------|
| Builder | `gemini-2.5-flash-lite` | 1,000 | Volume for development |
| Gardener | `gemini-3-pro` | 50 | Smart reasoning |
| **Combined** | | **1,050** | Best of both |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Different models produce incompatible outputs | Low | High | Both use same JSON schema; Pydantic validates |
| Gemini 3 Pro limits change | Medium | Low | Easy to swap models via config |
| Implementation introduces bugs | Low | Medium | Existing tests cover agent outputs |
| Config migration breaks existing setups | Low | Low | Backward compatible with `gemini_model` fallback |

---

## Decision Required

**Director approval needed to proceed with implementation.**

### Questions for Director

1. **Approve dual-model architecture?** (Yes/No)
2. **Which configuration option?** (A: Volume / B: Quality / C: Balanced)
3. **Proceed immediately or after Gate 7 completion?**

---

## Appendix: Code Fixes Already Applied This Session

| File | Change | Status |
|------|--------|--------|
| `backend/app/config.py` | `gemini_model` → `gemini-2.0-flash` | ✅ Applied |
| `backend/app/config.py` | `embedding_model` → `models/text-embedding-004` | ✅ Applied |
| `backend/app/config.py` | `embedding_dimensions` → `768` | ✅ Applied |
| `backend/app/services/llm.py` | Added `_resolve_refs()` for Pydantic `$ref` | ✅ Applied |
| `backend/app/services/llm.py` | Updated `_clean_schema()` for `required` fields | ✅ Applied |
| `backend/scripts/smoke_test.py` | Switched to `requests` library | ✅ Applied |

---

## Appendix: Session Timeline

| Time | Event |
|------|-------|
| Session start | Gate 7 implementation resumed |
| +15min | Smoke test failing with 21s IPv6 delays |
| +30min | Discovered `gemini-1.5-flash` deprecated (404) |
| +45min | Switched to `gemini-2.0-flash` |
| +60min | Hit 429 quota exhaustion |
| +75min | Discovered embedding model name format change |
| +90min | Fixed schema `$ref` compatibility issues |
| +105min | Researched Gemini API free tier limits |
| +120min | Identified dual-model architecture as solution |
| Now | Proposal document created |


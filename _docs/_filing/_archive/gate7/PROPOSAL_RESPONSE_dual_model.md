# Proposal Response: Dual LLM Model Architecture

**Date:** 17 December 2025  
**Proposal:** `INTERRUPT_dual_model_proposal.md`  
**Director Decision:** ✅ **APPROVED (Modified)**

---

## Decision Summary

| Item | Proposed | Approved |
|------|----------|----------|
| Dual-model architecture | Yes | ✅ Yes |
| Configuration option | A, B, or C | **B (Quality)** |
| Builder model | Various | `gemini-2.5-flash` |
| Gardener model | Various | `gemini-3-pro` |
| Immediate implementation | Yes | ✅ Yes |

---

## Approved Configuration

| Agent | Model | RPD | RPM | Rationale |
|-------|-------|-----|-----|-----------|
| Builder | `gemini-2.5-flash` | 250 | 10 | Quality extraction — Builder does critical concept extraction; "lite" models risk poor graph quality |
| Gardener | `gemini-3-pro` | 50 | 5-10 | Best reasoning — Gardener needs strong deduplication/merge logic |
| **Combined** | | **300** | | 50% improvement over current 200 RPD |

---

## Implementation Instructions

### 1. Config Changes (`backend/app/config.py`)

Add two new fields:

```python
# Builder: quality extraction, moderate volume
gemini_model_builder: str = Field(
    default="gemini-2.5-flash",
    description="Model for Builder agent (quality extraction).",
)

# Gardener: periodic review, best reasoning
gemini_model_gardener: str = Field(
    default="gemini-3-pro",
    description="Model for Gardener agent (reasoning, deduplication).",
)
```

Keep legacy `gemini_model` for backward compatibility but deprecate it.

### 2. LLM Service Changes (`backend/app/services/llm.py`)

Change single model cache to dictionary:

```python
_MODELS: dict[str, genai.GenerativeModel] = {}
_MODELS_LOCK = threading.Lock()

async def generate_structured_json(
    prompt: str,
    *,
    schema: SchemaInput,
    model: str | None = None,  # NEW: optional model override
) -> Mapping[str, Any]:
    ...
```

Add `_get_model(model_name)` helper that caches by model name.

### 3. Agent Changes

**`backend/app/agents/builder.py`:**
```python
from app.config import get_settings

settings = get_settings()
result = await generate_structured_json(
    prompt=...,
    schema=...,
    model=settings.gemini_model_builder,  # NEW
)
```

**`backend/app/agents/gardener.py`:**
```python
from app.config import get_settings

settings = get_settings()
result = await generate_structured_json(
    prompt=...,
    schema=...,
    model=settings.gemini_model_gardener,  # NEW
)
```

### 4. Environment Example (`.env.example`)

```env
# LLM Models (dual-model architecture)
GEMINI_MODEL_BUILDER=gemini-2.5-flash
GEMINI_MODEL_GARDENER=gemini-3-pro

# Legacy (deprecated, use agent-specific fields)
# GEMINI_MODEL=gemini-2.0-flash
```

---

## Verification Checklist

After implementation, verify:

- [ ] Builder uses `gemini-2.5-flash` (check logs or add model name to SSE events)
- [ ] Gardener uses `gemini-3-pro`
- [ ] Fallback to legacy `gemini_model` works if new fields not set
- [ ] Smoke test passes with new configuration
- [ ] No schema/output format differences between models

---

## Risk Acknowledgement

| Risk | Mitigation |
|------|------------|
| Different models produce different outputs | Both use same JSON schema; Pydantic validates |
| 300 RPD still insufficient for heavy dev | Acceptable for MVP; can adjust post-launch |
| Model name typos cause 404 | Validate on startup; fail fast |

---

## Rationale for Rejecting Option A/C

| Option | Why Rejected |
|--------|--------------|
| A (Volume with flash-lite) | "Lite" models have reduced reasoning; Builder needs quality extraction |
| C (Balanced with flash-lite) | Same concern — Builder quality takes priority over volume |

Option B prioritises **extraction quality** over raw request volume. A high-quality graph from 250 requests is more valuable than a noisy graph from 1,000 requests.

---

## Next Steps

1. Implement dual-model changes (~35 lines)
2. Apply IPv6 workaround (see below)
3. Re-run smoke test with new configuration
4. Complete 10-minute real Gemini demo
5. Capture evidence and close Gate 7

---

## IPv6 Workaround (Windows)

The Windows IPv6 fallback causes ~21 second delays per HTTP request. This affects all outbound calls (Gemini API, Neo4j).

### Option A: Disable IPv6 on Network Adapter (Recommended)

1. Open **Control Panel** → **Network and Sharing Centre**
2. Click your active network connection
3. Click **Properties**
4. **Uncheck** "Internet Protocol Version 6 (TCP/IPv6)"
5. Click **OK**
6. Restart the backend

### Option B: Prefer IPv4 via Registry (System-wide)

```powershell
# Run as Administrator
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip6\Parameters" -Name "DisabledComponents" -Value 0x20 -PropertyType DWord -Force

# Restart required
Restart-Computer
```

### Option C: Force IPv4 in Code (Already Applied)

The `neo4j_uri` default was changed from `localhost` to `127.0.0.1` in `backend/app/config.py`. This forces IPv4 for Neo4j but doesn't help with Gemini API calls.

### Verification

After applying workaround, HTTP requests should complete in <5 seconds instead of 21+ seconds:

```powershell
# Test Gemini API latency
Measure-Command { Invoke-WebRequest -Uri "https://generativelanguage.googleapis.com" -Method Head }
```

Expected: ~200-500ms, not 21,000ms

---

## Approval

**Approved by:** Director of Development  
**Date:** 17 December 2025

*Proceed with implementation immediately. This unblocks Gate 7 completion.*


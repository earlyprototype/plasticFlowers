# Model Rotation Strategy for API Quota Management

**Date:** 2025-12-27  
**Issue:** Flash model timing out / hitting quota limits  
**Solution:** Automatic round-robin model rotation

## Problem Analysis

The timeout issue was NOT a token limit problem (Gemini supports 1M tokens). The actual issue was:

1. **Rate Limiting (RPM)** - Free tier has strict requests-per-minute limits:
   - `gemini-2.5-pro`: 2 RPM (very restrictive)
   - `gemini-2.5-flash`: 15 RPM
   - `gemini-2.0-flash`: ~15 RPM
   - `gemini-2.0-flash-exp`: Higher (experimental)

2. **No artificial limits** - Our config doesn't restrict token count:
   - `gemini_request_timeout: 60s` - reasonable for large graphs
   - `gemini_max_output_tokens: 131072` - well within model limits

## Solution: Automatic Model Rotation

Implemented in `backend/app/services/llm.py`:

### Three-Model Rotation Pool

```python
_FALLBACK_MODELS = [
    "gemini-2.5-flash",      # 15 RPM free tier
    "gemini-2.0-flash-exp",  # Experimental, likely higher limits
    "gemini-2.0-flash",      # Stable, similar to 2.5-flash
]
```

### Automatic Switching Logic

1. **On Quota Error Detection:**
   - Detects `429`, `quota`, or `RESOURCE_EXHAUSTED` errors
   - Automatically switches to next model in rotation
   - Logs the switch for visibility

2. **Round-Robin Cycling:**
   - Each quota error triggers rotation to next model
   - Effectively triples available request capacity
   - No manual intervention required

3. **Retry Logic:**
   - Model switches don't count as retry attempts
   - Only genuine failures increment retry counter
   - Can cycle through all 3 models before giving up

## Benefits

1. **3x Request Capacity:**
   - 15 + 15 + 15 = ~45 RPM effective capacity
   - Distributes load across multiple model quotas

2. **Automatic Failover:**
   - No manual config changes needed
   - System self-heals on quota exhaustion

3. **Testing Efficiency:**
   - Maximises testing call availability
   - Reduces downtime waiting for quota refresh

## Monitoring

Use the monitoring script:

```powershell
cd backend
python check_model_rotation.py
```

Shows:
- Current rotation status
- API call count
- Which model is next
- Rate limit information

## Edge Cases

1. **All Models Hit Quota:**
   - System will retry with backoff
   - Eventually fails with comprehensive error message
   - User sees which models were attempted

2. **Model-Specific Errors:**
   - Non-quota errors (e.g., safety blocks) don't trigger rotation
   - Uses standard retry logic with exponential backoff

3. **Model Availability:**
   - If a model is removed/deprecated, can easily update `_FALLBACK_MODELS`
   - Rotation logic is model-agnostic

## Configuration

Current settings in `config.py`:
- `gemini_model_gardener: "gemini-2.5-flash"` - Starting model
- `gemini_model_builder: "gemini-2.5-flash"` - Builder also uses flash
- `gemini_request_timeout: 60.0` - Adequate for Gardener
- `gardener_debounce_seconds: 30` - Prevents over-calling

## Next Steps

If issues persist:
1. Check actual error in logs (quota vs timeout vs other)
2. Verify API key is valid and not expired
3. Consider increasing `gardener_debounce_seconds` to 60+ 
4. Monitor with `check_model_rotation.py` to see rotation patterns


# Gemini 3 Flash Model Note

## Issue

`gemini-3-flash` exists in the API limits but returns 404 error:

```
404 models/gemini-3-flash is not found for API version v1beta, or is not supported for generateContent
```

## Root Cause

The model is too new for the current `google-generativeai` SDK version (0.8.5) which uses `v1beta1` API endpoint.

## Temporary Solution

Using `gemini-2.5-flash` instead, which:
- Is available and working
- Has higher limits (0/1K vs 0/1M tokens)
- Is the latest stable Flash model
- Provides excellent performance

## Future Fix

To use `gemini-3-flash`:

1. **Update SDK** (when available):
   ```bash
   pip install --upgrade google-generativeai
   ```

2. **Or use REST API directly** with correct endpoint

3. **Or wait for SDK support** for this model

## Current Configuration

- **Builder**: `gemini-2.5-flash`
- **Gardener**: `gemini-2.5-pro`  
- **Export**: `gemini-2.5-flash`

All using latest stable Gemini 2.5 family models.

---

**Date:** 19 December 2025  
**Status:** Resolved with gemini-2.5-flash




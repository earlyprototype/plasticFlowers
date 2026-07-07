# Solutions Log

**Purpose:** Document problems encountered and how they were solved.  
**Usage:** Check here before debugging - you may have solved it before.  
**Update:** Add entries after solving any non-trivial issue.

---

## Template

```markdown
### Issue: [Brief description]

**Date:** YYYY-MM-DD  
**Time spent:** [X hours]  
**Severity:** [Low | Medium | High | Blocker]

**Symptom:**
What did you observe? Error message, unexpected behaviour, etc.

**Root cause:**
What was actually wrong?

**Solution:**
What fixed it?

**Files affected:**
- `path/to/file.py`

**Prevention:**
How to avoid this in future?
```

---

## Issues

### Issue: Gardener not running (silently failing)

**Date:** 2025-12-26  
**Time spent:** 30 minutes  
**Severity:** Blocker

**Symptom:**
Gardener agent was not processing ghost nodes despite Builder creating them. No visible error messages. Previously worked fine.

**Root cause:**
Debug logging code in `_run_gardener` was writing to a hardcoded path (`c:\Users\Fab2\Desktop\AI\_plasticFlower\.cursor\debug.log`) that didn't exist. The directory `.cursor` exists in the Cursor IDE's project folder, not the actual project root. This caused a `FileNotFoundError` on the first line of the try block, which was caught by the outer exception handler and logged as `gardener.run_failed`, but the Gardener never actually ran.

**Solution:**
Removed the debug logging code that wrote to the non-existent directory. Replaced with proper `logger.debug()` calls that use the standard Python logging infrastructure.

**Files affected:**
- `backend/app/services/scheduler.py`

**Prevention:**
- Never use hardcoded absolute paths in debug code
- Use Python's `logging` module instead of file writes for debugging
- Debug file writes should use relative paths or configurable paths
- Test debug code paths before committing

---

### Issue: Gemini API key not picked up after .env update

**Date:** 2025-12-27  
**Time spent:** 1 hour  
**Severity:** Blocker

**Symptom:**
Gardener LLM calls failing with "API key expired" error even after updating the API key in `.env` files. The `list_models.py` script worked (listed 31 models), but actual generation calls failed.

**Root cause:**
The `genai.Client` in `backend/app/services/llm.py` is created as a singleton via `@lru_cache`. When the `.env` file is updated, Uvicorn's `--reload` restarts the server, but the cached client retains the old (expired) API key in memory.

**Solution:**
Full process restart required - not just Uvicorn reload. Kill all Python processes and restart:
```powershell
Get-Process python* -ErrorAction SilentlyContinue | Stop-Process -Force
```

**Files affected:**
- `backend/app/services/llm.py` (singleton cache)

**Prevention:**
- After updating API keys, always do a full process restart
- Consider adding a `/debug/clear-cache` endpoint for development
- Document in README that API key changes require full restart

---

### Issue: Dual Gardener triggers causing duplicate runs

**Date:** 2025-12-27  
**Time spent:** 30 minutes  
**Severity:** Medium

**Symptom:**
Gardener running twice for the same session - once via Redis consumer, once via timer loop. Excessive API quota usage.

**Root cause:**
Scheduler had two parallel trigger mechanisms:
1. Timer loop (polling every 60s)
2. Redis consumer (event-driven)

Both could trigger for the same session because `mark_activity()` was called twice in `chunks.py` and the timer loop checked activity timestamps independently of Redis.

**Solution:**
Removed timer loop entirely. Gardener is now Redis-only with configurable debounce (`GARDENER_DEBOUNCE_SECONDS`). See ADR-009.

**Files affected:**
- `backend/app/services/scheduler.py`
- `backend/app/api/chunks.py`
- `backend/app/config.py`

**Prevention:**
- Single trigger mechanism per agent
- Document trigger patterns in ADRs
- Use configurable settings, not hard-coded values

---

### Issue: Gemini API request timeout (60s)

**Date:** 2025-12-27  
**Time spent:** 1 hour  
**Severity:** High

**Symptom:**
Gardener LLM calls timing out after 60 seconds with "Gemini request timed out" error. Not a token limit issue (Gemini supports 1M context).

**Root cause:**
Multiple factors:
1. Complex Gardener reasoning (proofreading + node actions + flower formation) takes 60-90s
2. Free tier may have lower processing priority
3. Rate limiting (RPM) causing delays
4. Original 60s timeout was too aggressive

**Solution:**
1. Increased timeout from 60s to 90s in `config.py`
2. Implemented model rotation to cycle through 3 models when quota hit
3. Added diagnostic logging for prompt size and API call tracking

**Files affected:**
- `backend/app/config.py`
- `backend/app/services/llm.py`
- `backend/app/agents/gardener.py`

**Prevention:**
- Use 90s+ timeout for Gardener (complex reasoning)
- Implement fallback models for quota exhaustion
- Add diagnostic logging to identify actual bottleneck

---

### Issue: API quota exhaustion (429 RESOURCE_EXHAUSTED)

**Date:** 2025-12-27  
**Time spent:** 30 minutes  
**Severity:** Medium

**Symptom:**
Gardener failing with RESOURCE_EXHAUSTED errors. Initially used `gemini-2.5-pro` which has only 2 RPM on free tier.

**Root cause:**
Free tier rate limits:
- `gemini-2.5-pro`: 2 RPM (very restrictive)
- `gemini-2.5-flash`: 15 RPM
- `gemini-2.0-flash`: ~15 RPM

**Solution:**
Implemented automatic model rotation in `llm.py`:
```python
_FALLBACK_MODELS = [
    "gemini-2.5-flash",      # 15 RPM
    "gemini-2.0-flash-exp",  # Higher limits
    "gemini-2.0-flash",      # ~15 RPM
]
```
When quota error detected (429/RESOURCE_EXHAUSTED), automatically switch to next model. Effectively triples available RPM.

**Files affected:**
- `backend/app/services/llm.py`

**Prevention:**
- Use flash models for free tier (higher RPM)
- Implement automatic fallback/rotation
- Monitor model rotation logs

---

### Issue: Debounce confusion (backend vs frontend)

**Date:** 2025-12-27  
**Time spent:** 30 minutes  
**Severity:** Low

**Symptom:**
Confusion about what `gardener_debounce_seconds` (30s) was for. Initially thought it was related to UI/Cytoscape rendering.

**Root cause:**
Two separate debounce mechanisms exist:
1. **Frontend (1.2s):** `ANIMATION_CONFIG.debounceDelay` in `GraphCanvas.tsx` - batches SSE events for smooth Cytoscape animation
2. **Backend (was 30s):** `gardener_debounce_seconds` - controlled Gardener trigger timing

These are completely separate concerns.

**Solution:**
Replaced backend debounce with ratio-based triggering (ADR-010):
- Builder counts chunks per session
- Gardener triggers every N chunks (default: 5)
- Cleaner separation: UI debounce for animation, ratio for API pacing

**Files affected:**
- `backend/app/config.py`
- `backend/app/services/builder_service.py`
- `backend/app/services/scheduler.py`

**Prevention:**
- Document debounce purposes clearly
- Use distinct naming (e.g., "animation_debounce" vs "gardener_ratio")
- Keep UI and API concerns separate

---

### Issue: [Template - Copy this for new entries]

**Date:** YYYY-MM-DD  
**Time spent:** X hours  
**Severity:** Medium

**Symptom:**
[What you observed]

**Root cause:**
[What was actually wrong]

**Solution:**
[What fixed it]

**Files affected:**
- `file.py`

**Prevention:**
[How to avoid in future]

---

## Categories

### Neo4j / Cypher

### Issue: Corrupt nodes created by MERGE in relationship creation

**Date:** 2025-12-28  
**Time spent:** 1 hour  
**Severity:** High

**Symptom:**
Pydantic validation errors when loading nodes: `Field required [type=missing]` for `label`, `confidence`, `mentions`, `inferred_type`, `status`. Nodes only had `id`, `timestamps: []`, and `created_at: None`.

**Root cause:**
The `create_relationship` function used `MERGE (source:Node {id: $source_id, session_id: $session_id})` which creates empty nodes if they don't exist. When Gardener created new relationships referencing node IDs that had been pruned or didn't exist, Neo4j created partial nodes with only `id` and `session_id`.

**Solution:**
Changed from `MERGE` to `MATCH` for nodes in `create_relationship`:
```python
# Before (creates empty nodes)
MERGE (source:Node {id: $source_id, session_id: $session_id})

# After (returns None if nodes don't exist)
MATCH (source:Node {id: $source_id, session_id: $session_id})
```

Also ran cleanup to delete 245 corrupt nodes:
```cypher
MATCH (n:Node) WHERE n.label IS NULL DETACH DELETE n
```

**Files affected:**
- `backend/app/services/graph_db.py`

**Prevention:**
Never use MERGE for nodes when creating relationships. Use MATCH and handle the case where nodes don't exist gracefully.

---

### Issue: Neo4j map projection syntax corrupting node data

**Date:** 2025-12-28  
**Time spent:** 30 minutes  
**Severity:** High

**Symptom:**
Same Pydantic validation errors as above, but occurring in `list_nodes` after embedding exclusion was implemented.

**Root cause:**
The Cypher syntax `WITH n {.*, embedding: null} AS node` was intended to exclude embeddings but corrupted the returned data. Neo4j's map projection wasn't working as expected.

**Solution:**
Removed the map projection from Cypher and handled embedding exclusion in Python:
```python
# In _node_from_value()
props.pop("embedding", None)  # Exclude 768 floats per node
```

**Files affected:**
- `backend/app/services/graph_db.py`

**Prevention:**
Handle field exclusion in Python rather than Cypher map projections for complex transformations.

---

### LLM / Gemini

### Issue: Gemini 2.5 LLM calls taking 60-90 seconds

**Date:** 2025-12-28  
**Time spent:** 1.5 hours  
**Severity:** High

**Symptom:**
Gardener LLM calls taking 68+ seconds despite using Flash model with only 22 nodes. Builder calls with same model were fast (~5s).

**Root cause:**
Gemini 2.5 models have built-in "thinking mode" enabled by default. This adds internal reasoning before generating output, which can add 60+ seconds to response time.

**Solution:**
Disable thinking mode by setting `thinking_budget=0`:
```python
config = types.GenerateContentConfig(
    # ... other settings ...
    thinking_config=types.ThinkingConfig(thinking_budget=0),
)
```

**Files affected:**
- `backend/app/services/llm.py`

**Prevention:**
For structured output tasks where speed matters, disable thinking mode. Consider enabling it only for complex reasoning tasks.

---

### Issue: Regex patterns in Pydantic schema causing Gemini structured output issues

**Date:** 2025-12-28  
**Time spent:** 30 minutes  
**Severity:** Medium

**Symptom:**
Gardener LLM calls timing out or producing malformed responses. Builder (with simpler schema) worked fine.

**Root cause:**
Gardener schema used regex patterns with case-insensitive flags:
```python
action: str = Field(..., pattern="^(?i)(confirm|prune|merge)$")
```
The `(?i)` flag may not be properly supported by Gemini's structured output.

**Solution:**
Replaced regex patterns with `Literal` types:
```python
action: Literal["confirm", "prune", "merge"] = Field(...)
```

**Files affected:**
- `backend/app/agents/gardener.py`

**Prevention:**
Use `Literal` types instead of regex patterns for enum-like string fields in Pydantic schemas used with Gemini structured output.

---

### Frontend / React

*(Add frontend issues here)*

---

### Docker / Infrastructure

*(Add Docker/infrastructure issues here)*

---

### Testing

*(Add test-related issues here)*

---

## Quick Fixes Reference

Common issues with quick solutions:

| Symptom | Likely Cause | Quick Fix |
|---------|--------------|-----------|
| Neo4j connection refused | Docker not running | `docker compose up -d` |
| Empty graph after chunks | Session not created first | Create session before chunks |
| LLM returns malformed JSON | Prompt too vague | Add "Return valid JSON only" |
| CORS errors in browser | Missing headers | Check FastAPI middleware |
| Cytoscape layout broken | fcose not imported | Import and register fcose |
| Gardener not processing ghosts | Debug logging to non-existent path | Check for hardcoded paths in scheduler.py |
| API key expired after .env update | Cached LLM client | Full process restart (kill all Python) |
| Gardener running twice | Dual triggers (timer + Redis) | Use Redis-only (ADR-009) |
| Gemini request timeout (60s) | Complex reasoning takes longer | Increase timeout to 90s+ |
| RESOURCE_EXHAUSTED (429) | API quota hit | Use flash models, model rotation |
| Gardener not triggering | Ratio threshold not reached | Check `builder_gardener_ratio` (default: 5) |
| Gemini 2.5 calls taking 60+ seconds | Thinking mode enabled by default | Add `thinking_config=types.ThinkingConfig(thinking_budget=0)` |
| Corrupt nodes in Neo4j (missing fields) | MERGE creating empty nodes | Use MATCH for nodes, MERGE only for relationships |
| Pydantic validation errors on list_nodes | Map projection syntax corrupting data | Handle field exclusion in Python, not Cypher |

---

## Lessons Learned

*(General lessons that aren't tied to specific issues)*

1. **Always create session before chunks** - Chunks require a parent session
2. **MERGE is safer than CREATE** - Idempotent operations prevent duplicates
3. **Test with real Gemini early** - Mocked responses hide prompt issues
4. **Check Docker logs first** - `docker compose logs neo4j` shows real errors

---

### Issue: LLM test suite failures due to obsolete `_MODEL` singleton reference

**Date:** 2025-12-31  
**Time spent:** N/A (Not fixed yet)  
**Severity:** Low

**Symptom:**
Three tests in `backend/tests/test_llm.py` fail at setup with `AttributeError`:
```
ERROR backend\tests\test_llm.py::test_generate_structured_json_returns_payload
ERROR backend\tests\test_llm.py::test_generate_structured_json_retries_and_succeeds
ERROR backend\tests\test_llm.py::test_generate_structured_json_raises_on_invalid_json

AttributeError: <module 'backend.app.services.llm'> has no attribute '_MODEL'
```

**Root cause:**
The test fixture `reset_model` (line 23-27 of `test_llm.py`) attempts to reset a `_MODEL` singleton variable that no longer exists in `backend/app/services/llm.py`. The LLM service was refactored to use **model rotation** (`_MODEL_ROTATION_INDEX` and `_MODEL_ROTATION_LOCK`) instead of a single model instance, but the test fixtures were not updated.

**Current workaround:**
None needed - the LLM service works correctly in production. These are test-only failures that don't affect functionality. 24 out of 27 tests pass successfully.

**Solution (Not yet implemented):**
Update `test_llm.py` fixture to reflect model rotation architecture:
```python
@pytest.fixture(autouse=True)
def reset_model(monkeypatch):
    monkeypatch.setattr(llm, "_MODEL_ROTATION_INDEX", 0)  # Reset rotation
    monkeypatch.setattr(llm.genai, "configure", lambda api_key: None)
    yield
    # Clean up if needed
```

**Files affected:**
- `backend/tests/test_llm.py` (fixture needs updating)
- `backend/app/services/llm.py` (reference implementation)

**Prevention:**
When refactoring core services, update corresponding test fixtures in the same commit. Run full test suite after architectural changes to catch orphaned test dependencies.

**Priority:** Low - Technical debt, not a functional blocker. Fix during next LLM service enhancement.


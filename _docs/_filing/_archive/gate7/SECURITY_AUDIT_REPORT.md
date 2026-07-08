# Security Audit Report: Backend Dependencies

**Date:** 19 December 2025  
**Tool:** pip-audit v2.10.0  
**Scope:** plasticFlower Backend Python Dependencies

---

## Executive Summary

Security audit identified **46 known vulnerabilities** across 23 packages in the Python environment. Of these, **3 packages** are direct dependencies of plasticFlower and require immediate attention:

1. **starlette** (HIGH severity) - 2 CVEs affecting SSE/FastAPI
2. **urllib3** (HIGH severity) - 4 CVEs affecting HTTP client
3. **requests** (MEDIUM severity) - 1 CVE

---

## Critical Findings

### 1. Starlette (FastAPI Foundation)

| Current Version | Vulnerable | Fix Version | CVEs |
|-----------------|------------|-------------|------|
| 0.40.0 | ✅ Yes | 0.49.1 | CVE-2025-54121, CVE-2025-62727 |

**Impact:** Starlette is the ASGI framework underlying FastAPI. SSE streaming (core to plasticFlower) is handled by starlette.

**Recommendation:** Upgrade to starlette >= 0.49.1

**Action:**
```bash
pip install "starlette>=0.49.1"
```

---

### 2. urllib3 (HTTP Client)

| Current Version | Vulnerable | Fix Version | CVEs |
|-----------------|------------|-------------|------|
| 2.2.3 | ✅ Yes | 2.6.0 | CVE-2025-50182, CVE-2025-50181, CVE-2025-66418, CVE-2025-66471 |

**Impact:** urllib3 is used by `requests` for HTTP connections to Gemini API and Neo4j.

**Recommendation:** Upgrade to urllib3 >= 2.6.0

**Action:**
```bash
pip install "urllib3>=2.6.0"
```

---

### 3. Requests

| Current Version | Vulnerable | Fix Version | CVE |
|-----------------|------------|-------------|-----|
| 2.32.3 | ✅ Yes | 2.32.4 | CVE-2024-47081 |

**Impact:** Used for HTTP calls to Gemini API.

**Recommendation:** Upgrade to requests >= 2.32.4

**Action:**
```bash
pip install "requests>=2.32.4"
```

---

## Transitive Dependencies (Non-Critical for plasticFlower)

The following vulnerabilities exist in packages that are **not directly used** by plasticFlower but are installed as dependencies of `google-generativeai`:

- **transformers** (14 CVEs) - ML model library, not invoked by plasticFlower
- **torch** (1 CVE) - Deep learning framework, not used
- **langchain** (3 CVEs) - LLM orchestration, not used
- **aiohttp, cryptography, flask, jinja2, litellm** - Indirect dependencies

**Recommendation:** Monitor but defer action. These are pulled in by `google-generativeai` but plasticFlower does not directly invoke them.

---

## Recommended requirements.txt Updates

```txt
fastapi==0.115.2
uvicorn[standard]==0.30.1
python-dotenv==1.0.1
pydantic-settings==2.6.1
neo4j==5.23.1
google-generativeai>=0.3.0
sse-starlette==1.8.2
requests>=2.32.4           # UPDATED: was 2.31.0
urllib3>=2.6.0             # NEW: explicit pin for security
starlette>=0.49.1          # NEW: explicit pin (FastAPI dependency)
```

---

## Implementation Plan

### Phase 1: Immediate (Pre-Production)

1. Update `backend/requirements.txt` with fixed versions above
2. Run `pip install -r backend/requirements.txt --upgrade`
3. Re-run smoke tests to verify no regressions
4. Re-run `pip-audit` to confirm fixes

### Phase 2: Monitoring (Post-MVP)

1. Schedule monthly `pip-audit` runs
2. Subscribe to security advisories for FastAPI/Starlette
3. Consider adding `safety` or `pip-audit` to CI/CD pipeline

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| SSE stream hijacking (starlette CVEs) | Medium | High | Upgrade starlette to 0.49.1 |
| HTTP request manipulation (urllib3 CVEs) | Medium | High | Upgrade urllib3 to 2.6.0 |
| Dependency conflicts after upgrade | Low | Medium | Test in staging environment first |
| Transitive vulns exploited | Low | Low | Monitor, defer action for MVP |

---

## Sign-Off

**Prepared By:** Director of Development  
**Date:** 19 December 2025  
**Status:** READY FOR ACTION

**Recommendation:** Apply fixes before production deployment. Acceptable risk for local MVP testing if network is trusted.




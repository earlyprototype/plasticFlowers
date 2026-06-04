---
name: gate-7-mvp-ready
overview: MVP readiness with robustness guarantees — bug fixes, real Gemini demo, Z-filters, runbook, evidence pack.
todos:
  - id: fix-gardener-fake
    content: Fix fake Gardener mismatch (scheduler.py)
    status: pending
  - id: fix-markdown-fields
    content: Fix Markdown export field names (export.py)
    status: pending
  - id: z-filters
    content: Implement Z-filter controls (status/confidence/Flower/type)
    status: pending
  - id: smoke-test-script
    content: Create smoke_test.py automated validation
    status: pending
  - id: runbook-verify
    content: Verify MVP runbook works end-to-end
    status: pending
  - id: edge-cases
    content: Execute edge-case tests (SSE, exports, Gardener)
    status: pending
  - id: non-negotiables
    content: Audit non-negotiables checklist
    status: pending
  - id: real-gemini-demo
    content: Run 10-minute demo with real Gemini
    status: pending
  - id: evidence-capture
    content: Capture evidence pack to _docs/_evidence/gate7/
    status: pending
  - id: handover-docs
    content: Update README, .env.example, caveats
    status: pending
  - id: director-signoff
    content: Director final sign-off
    status: pending
---

# Gate 7 — MVP Readiness (Robustness Pack)

## Scope

- Bug fixes for known issues (fake Gardener, export fields)
- Z-filters (deferred from Gate 6)
- Runbook + startup helpers
- Real Gemini 10-minute demo (not fake mode)
- Evidence capture for sign-off

## Serial Dependencies

1. Bug fixes (fake Gardener, export fields)
2. Runbook verification
3. Edge case testing
4. Non-negotiables audit
5. 10-minute real Gemini demo
6. Evidence capture
7. Director sign-off

## Robustness Fixes

| Issue | Location | Fix |
|-------|----------|-----|
| Fake Gardener mismatch | `scheduler.py:97` | Add fake Gardener output instead of skipping |
| Markdown export fields | `export.py:200` | `flower.theme` → `flower.label`, `flower.stem_id` → `flower.stem_node_id` |
| Z-filters | Frontend | Implement status/confidence/Flower/type filters |

## Deliverables

| Deliverable | Location |
|-------------|----------|
| Robustness fixes | `scheduler.py`, `export.py` |
| Z-filter controls | `frontend/src/components/filters/` |
| Smoke test script | `backend/scripts/smoke_test.py` |
| Startup helper | `scripts/start_mvp.ps1` (already created) |
| MVP runbook | `_docs/_runbook/MVP_DEMO.md` (already created) |
| Evidence pack | `_docs/_evidence/gate7/` |

## Evidence Required

| Artefact | Description |
|----------|-------------|
| `smoke_test_results.json` | Automated test output |
| `10min_session_export.json` | Full export from real Gemini demo |
| `gardener_cycles.log` | Log showing 90s heartbeats |
| `non_negotiables_checklist.md` | Signed checklist |
| `director_report.md` | Final sign-off report |

## Edge Cases

- SSE reconnect badge transition
- Chunk to ended session (409)
- Empty-session exports
- VTT timestamp format
- Malformed LLM payloads
- Multi-tab sync
- 200+ nodes FCose performance

## Non-Negotiables Audit

- [ ] `inferred_type` freeform (no enum)
- [ ] Flower = 3+ nodes AND 2+ edges
- [ ] Merge = synonyms/acronyms only
- [ ] Relationship categories = exactly 5
- [ ] Gardener cadence = 90s fixed
- [ ] Relationship `id` required
- [ ] Uncertainty → prune (not confirm)

## Success Criteria

- [ ] Smoke test passes with real Gemini
- [ ] 10-minute demo completes without errors
- [ ] All exports work (JSON, transcript, VTT, markdown)
- [ ] Z-filters hide/show nodes correctly
- [ ] Gardener confirms/prunes/merges with real LLM
- [ ] Evidence pack complete

## Key Files

- `backend/app/services/scheduler.py` — fake Gardener fix
- `backend/app/api/export.py` — field name fix
- `frontend/src/components/filters/` — Z-filter UI
- `backend/scripts/smoke_test.py` — automated validation
- `scripts/start_mvp.ps1` — startup helper
- `_docs/_runbook/MVP_DEMO.md` — demo runbook
- `_docs/_evidence/gate7/` — evidence artefacts
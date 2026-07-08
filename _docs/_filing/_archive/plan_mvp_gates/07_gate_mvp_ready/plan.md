# Gate 7 — MVP Readiness

> **Objective:** Edge cases pass; non-negotiables verified; MVP complete with robustness guarantees
> **Entry:** Gate 6 passed (exports + lifecycle work)
> **Exit:** MVP ready for real-world demo with Gemini

---

## Serial Dependencies (must complete in order)

1. **Bug fixes** — Address known issues (see Robustness Fixes below)
2. **Runbook creation** — Scripted startup + preflight checks
3. **Edge case testing** — Run all documented edge cases
4. **Non-negotiables verification** — Check alignment checklist
5. **End-to-end smoke test** — Full 10-minute session with real Gemini
6. **Evidence capture** — Record results to `_docs/_evidence/gate7/`
7. **Final review** — Sign-off

---

## Parallel Lanes (can run simultaneously after bug fixes)

| Lane | Work | Owner |
|------|------|-------|
| A | Edge case testing (SSE, JSON, scaling) | QA / Dev |
| B | Non-negotiables verification | Dev |
| C | Documentation check (README, .env.example) | Dev |
| D | Runbook + startup helpers | Dev |

---

## Robustness Pack (NEW)

### 1. Robustness Fixes (Lane A prerequisite)

| Issue | Location | Fix |
|-------|----------|-----|
| Fake Gardener mismatch | `scheduler.py:97` | Add fake Gardener output when `PLASTICFLOWER_FAKE_LLM=1` instead of skipping entirely |
| Markdown export field names | `export.py:200` | Change `flower.theme` → `flower.label`, `flower.stem_id` → `flower.stem_node_id` |
| Z-filters deferred from Gate 6 | Frontend | Implement status/confidence/Flower/type filters |

### 2. MVP Runbook (`_docs/_runbook/MVP_DEMO.md`)

Create a step-by-step runbook covering:

| Section | Content |
|---------|---------|
| **Preflight Checks** | Neo4j reachable, `127.0.0.1` URI, `.env` vars present, Gemini API key valid |
| **Startup Helper** | Single PowerShell script to launch Neo4j + backend + frontend |
| **Demo Flow** | Create session → speak → watch nodes appear → wait for Gardener → export |
| **Expected Signals** | SSE badge "Live", nodes fade in, 90s Gardener heartbeat, Flowers form |
| **Troubleshooting** | Common issues (IPv6 timeout, missing API key, SSE disconnect) |

### 3. Smoke Test Script (`backend/scripts/smoke_test.py`)

Automated end-to-end validation:

```
1. Create session via POST /sessions
2. Submit 3 sample chunks via POST /sessions/{id}/chunks
3. Wait 5 seconds for Builder processing
4. Verify nodes exist via GET /sessions/{id}/nodes
5. Verify relationships exist via GET /sessions/{id}/relationships
6. Export JSON, transcript, VTT, markdown — all return 200
7. End session via POST /sessions/{id}/end
8. Delete session via DELETE /sessions/{id}
9. Output: PASS/FAIL + timings + counts to stdout and JSON file
```

### 4. Startup Helper Script (`scripts/start_mvp.ps1`)

PowerShell script for Windows:

```powershell
# Start all services for MVP demo
# Usage: .\scripts\start_mvp.ps1 [-FakeMode]

param([switch]$FakeMode)

# 1. Start Neo4j (if not running)
# 2. Start backend (with or without fake mode)
# 3. Start frontend
# 4. Open browser to http://localhost:3000
# 5. Display status and instructions
```

### 5. Evidence Requirements

Gate 7 exit requires these artefacts in `_docs/_evidence/gate7/`:

| Artefact | Description |
|----------|-------------|
| `smoke_test_results.json` | Automated test output |
| `10min_session_export.json` | Full export from 10-minute demo |
| `gardener_cycles.log` | Log showing 90s heartbeats |
| `non_negotiables_checklist.md` | Signed checklist |
| `director_report.md` | Final sign-off report |

---

## Edge Cases to Test

Per `_PRE_IMPLEMENTATION_REPORT.md`:

| Edge Case | Test | Pass |
|-----------|------|------|
| STT instability | Interim vs final transcript changes handled | [ ] |
| Long pauses | No chunks for minutes doesn't break state | [ ] |
| Invalid LLM output | JSON parsing failures logged, not crashed | [ ] |
| Duplicate labels | Punctuation/hyphenation/plurals merged correctly | [ ] |
| Graph size | 200-500 nodes doesn't freeze FCose | [ ] |
| SSE drop | Reconnect recovers full state | [ ] |
| Multi-tab | Two tabs on same session both update | [ ] |
| Export while live | Export works during active session | [ ] |
| Gardener with real LLM | Confirm/prune/merge actions execute correctly | [ ] |
| Flower formation | 3+ nodes AND 2+ edges triggers Flower | [ ] |

---

## Non-Negotiables Verification

Per `_ALIGNMENT.md`:

| Principle | Verification | Pass |
|-----------|--------------|------|
| Emergent schema | `inferred_type` accepts any string value | [ ] |
| Flower criteria | Flower only forms with 3+ nodes AND 2+ connections | [ ] |
| Merge rules | Merge only synonyms/acronyms/spelling; not hierarchies | [ ] |
| Relationship categories | Exactly 5: CAUSAL, STRUCTURAL, COMPARATIVE, TEMPORAL, ASSOCIATIVE | [ ] |
| Gardener cadence | Runs every 90 seconds (not adaptive) | [ ] |
| Relationship identity | `id` is required; removal uses `{ id }` | [ ] |
| Uncertainty → prune | Gardener prunes ambiguous nodes, not confirms | [ ] |

---

## Success Criteria

Per `_IMPLEMENTATION_BRIEF.md`:

| # | Criterion | Pass |
|---|-----------|------|
| 1 | User can start a session and speak into microphone | [ ] |
| 2 | Speech is transcribed and displayed | [ ] |
| 3 | Concepts appear as nodes in real-time (ghost state) | [ ] |
| 4 | Relationships appear between concepts | [ ] |
| 5 | Every 90 seconds, Gardener refines the graph | [ ] |
| 6 | Ghost nodes become solid after Gardener review | [ ] |
| 7 | Flowers form around thematic clusters | [ ] |
| 8 | User can filter the view (Z-level) | [ ] |
| 9 | User can export session data | [ ] |
| 10 | Session persists and can be restored | [ ] |

---

## Final Verification Checklist

- [ ] All robustness fixes applied
- [ ] Runbook created and tested
- [ ] Smoke test passes with real Gemini
- [ ] All edge cases tested and passing
- [ ] All non-negotiables verified
- [ ] All success criteria met
- [ ] No critical bugs outstanding
- [ ] README.md documents setup and usage
- [ ] `.env.example` documents required variables
- [ ] 10-minute end-to-end session runs without errors (real Gemini)
- [ ] Evidence artefacts captured in `_docs/_evidence/gate7/`

---

## Deliverables Summary

| Deliverable | Type | Location |
|-------------|------|----------|
| Robustness fixes | Code | Various (see fixes table) |
| MVP runbook | Doc | `_docs/_runbook/MVP_DEMO.md` |
| Smoke test script | Script | `backend/scripts/smoke_test.py` |
| Startup helper | Script | `scripts/start_mvp.ps1` |
| Z-filter controls | Frontend | `frontend/src/components/filters/` |
| Evidence pack | Docs | `_docs/_evidence/gate7/` |

---

## MVP Sign-Off

**Pass when:**
1. All verification items checked
2. Smoke test passes with real Gemini (not fake mode)
3. 10-minute demo completed successfully
4. Stakeholder demo completed
5. No blockers identified
6. Evidence pack complete

**Handover artefact:** MVP ready for real-world use

---

## Reference

- [Alignment](../../_docs/_dev/_MVP/_ALIGNMENT.md)
- [Implementation Brief](../../_docs/_dev/_MVP/_IMPLEMENTATION_BRIEF.md)
- [Pre-Implementation Report](../../_docs/_dev/_MVP/_PRE_IMPLEMENTATION_REPORT.md)
- [High-Level Plan](../overview/highplan.md)
- [Gate 5 Director Report](../../_docs/_evidence/gate5/director_report.md)

---

## Appendix: Environment Variables for Real Gemini

```env
# .env for MVP demo (real Gemini)
NEO4J_URI=neo4j://127.0.0.1:7687
NEO4J_PASSWORD=your_password
GEMINI_API_KEY=your_api_key

# Do NOT set these for real demo:
# PLASTICFLOWER_FAKE_LLM=1
# PLASTICFLOWER_FAKE_EMBEDDINGS=1
```

---

*Updated 16 December 2025 — Robustness pack added per Director request*

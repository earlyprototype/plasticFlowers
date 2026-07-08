# Gate 6 — Exports + Session Lifecycle

> **Objective:** Export endpoints work; session end/restore works; Z-filtering works
> **Entry:** Gate 5 passed (Gardener loop works)
> **Exit:** All export formats correct; session lifecycle complete

---

## Serial Dependencies (must complete in order)

1. **Session end** — `POST /sessions/{id}/end` sets `ended_at`
2. **Session restore** — `GET /sessions/{id}/graph` returns full state
3. **Export endpoints** — JSON, transcript, VTT, Markdown
4. **Frontend export UI** — Buttons trigger downloads
5. **Z-level filtering** — Filter controls work

---

## Parallel Lanes (can run simultaneously)

| Lane | Work | Owner |
|------|------|-------|
| A | Backend: Session end + restore logic | Backend dev |
| B | Backend: Export endpoints (JSON, transcript, VTT, Markdown) | Backend dev |
| C | Frontend: Export UI + download triggers | Frontend dev |
| D | Frontend: Z-filter controls + implementation | Frontend dev |

**Note:** All lanes can proceed in parallel once Gate 5 is passed.

---

## Deliverables

| Deliverable | Acceptance Criteria |
|-------------|---------------------|
| `POST /sessions/{id}/end` | Sets `ended_at`, stops Gardener for session |
| `GET /sessions/{id}/export/json` | Returns full graph + transcript + metadata |
| `GET /sessions/{id}/export/transcript` | Returns plain text transcript |
| `GET /sessions/{id}/export/vtt` | Returns WebVTT with timestamps |
| `GET /sessions/{id}/export/markdown` | Returns LLM-generated summary |
| Frontend export buttons | Trigger downloads for each format |
| Z-filter controls | Filter by status, confidence, Flower, type |

---

## Export Format Requirements

| Format | Content |
|--------|---------|
| JSON | `{ session, nodes, relationships, flowers, transcript, chunks }` |
| Transcript | Plain text, concatenated chunks |
| VTT | WebVTT format with `start_time` → `end_time` cues |
| Markdown | Session metadata + Flowers + key concepts + relationships overview |

---

## Z-Level Filtering

| Filter | Effect |
|--------|--------|
| Show all | Display entire graph |
| Solid only | Hide ghost nodes |
| High confidence | Hide nodes below threshold |
| By Flower | Show only selected Flower(s) |
| By type | Show only selected `inferred_type`(s) |

---

## Verification Checklist

- [ ] Session end sets `ended_at` timestamp
- [ ] Ended session can be restored (graph loads)
- [ ] JSON export includes all entities
- [ ] Transcript export is plain text
- [ ] VTT export has correct timestamp format
- [ ] Markdown export has coherent summary
- [ ] Export buttons work in UI
- [ ] Z-filter: "Solid only" hides ghost nodes
- [ ] Z-filter: "By Flower" shows only selected Flower
- [ ] Z-filter: hidden nodes also hide their edges
- [ ] Session list shows ended vs live sessions

---

## Handover to Gate 7

**Pass when:**
1. All verification items checked
2. Export files open correctly in target applications
3. Z-filtering is responsive

**Handover artefact:** Complete session lifecycle; exports work; filtering works

---

## Reference

- [API Contracts](../../_docs/_dev/_MVP/_api/01_contracts.md)
- [Frontend Data Flow](../../_docs/_dev/_MVP/_frontend/01_data_flow.md)
- [High-Level Plan](../overview/highplan.md)


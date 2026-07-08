# Gate 5 — Gardener Refinement Loop

> **Objective:** Gardener runs every 90 seconds; confirms/prunes/merges nodes; forms Flowers
> **Entry:** Gate 4 passed (Builder loop works)
> **Exit:** Gardener refines graph; ghost → solid; Flowers form correctly

---

## Serial Dependencies (must complete in order)

1. **Scheduler** — 90-second fixed interval timer
2. **Gardener agent** — Prompt + JSON validation + action application
3. **Node actions** — Confirm, prune, merge logic in graph_db
4. **Flower actions** — Create, update, dissolve logic in graph_db
5. **SSE events** — Broadcast Gardener-triggered events
6. **Frontend handling** — Update state on Gardener events

---

## Parallel Lanes (can run simultaneously)

| Lane | Work | Owner |
|------|------|-------|
| A | Scheduler + Gardener trigger logic | Backend dev |
| B | Gardener agent prompt + output parsing | Backend dev |
| C | Graph mutation logic (confirm/prune/merge/flowers) | Backend dev |
| D | Frontend: handle Gardener SSE events | Frontend dev |
| E | Frontend: Flower rendering (compound nodes) | Frontend dev |

**Sync points:**
- Lane B must complete before Lane A can trigger useful runs
- Lane C must complete before Gardener actions have effect
- Lanes D + E depend on SSE events being broadcast

---

## Deliverables

| Deliverable | Acceptance Criteria |
|-------------|---------------------|
| `backend/app/services/scheduler.py` | 90-second timer, triggers Gardener |
| `backend/app/agents/gardener.py` | Gardener prompt + output parsing |
| `backend/app/services/graph_db.py` | Confirm, prune, merge, flower CRUD |
| SSE events | `node_updated`, `node_removed`, `node_merged`, `flower_*` |
| Frontend handlers | State updates for all Gardener events |
| Cytoscape compound nodes | Flowers render as containers |

---

## Gardener Agent Requirements

Per `_docs/_dev/_MVP/_prompts/02_gardener.md`:

| Requirement | Implementation |
|-------------|----------------|
| Trigger | Every 90 seconds (fixed) |
| Condition | Only if ghost nodes OR recent Builder activity |
| Input | Ghost nodes, solid nodes, relationships, flowers, recent transcript, SessionVocabulary (including language settings) |
| Output | JSON: `{ node_actions, flower_actions, new_relationships }` |

### Language Settings Integration

Per `_docs/ARCHITECTURE_ADVISORY.md` Section 4.5:

- Session model includes `language_variant` field (default: "en-GB")
- SessionVocabulary includes `language_variant` and `preferred_spellings` map
- Gardener prompt includes language instructions
- Gardener proofreading normalises mixed variants to session default
- Node labels checked against preferred spellings during validation

---

## Non-Negotiables (must enforce)

| Rule | Check |
|------|-------|
| Uncertainty → prune | Gardener prunes when unsure, not confirms |
| Merge = true duplicates only | Synonyms, acronyms, spelling — NOT hierarchies |
| Flower = 3+ nodes AND 2+ internal connections | Both criteria required |
| `inferred_type` remains freeform | No enum constraints added |

---

## SSE Events (Gardener-triggered)

| Event | Payload | When |
|-------|---------|------|
| `node_updated` | Full Node object | Gardener confirms/updates |
| `node_removed` | `{ id }` | Gardener prunes |
| `node_merged` | `{ from_id, into_id }` | Gardener merges |
| `flower_created` | Full Flower object | Gardener forms Flower |
| `flower_updated` | Full Flower object | Gardener updates Flower |
| `flower_dissolved` | `{ id }` | Gardener dissolves Flower |
| `relationship_added` | Full Relationship object | Gardener adds cross-chunk rel |
| `relationship_removed` | `{ id }` | Gardener removes relationship |
| `gardener_cycle` | `{ timestamp }` | Gardener run complete |

---

## Verification Checklist

- [ ] Scheduler triggers Gardener every 90 seconds
- [ ] Gardener only runs if ghost nodes or recent activity
- [ ] Confirm action: ghost → solid, SSE `node_updated`
- [ ] Prune action: node deleted, SSE `node_removed`
- [ ] Merge action: node combined, relationships transferred, SSE `node_merged`
- [ ] Flower creation requires 3+ nodes AND 2+ internal connections
- [ ] Flower renders as compound node in Cytoscape
- [ ] Stem node highlighted (larger, border)
- [ ] Solid nodes show 100% opacity, solid border
- [ ] Merge never flattens hierarchies (test: "self-attention" ≠ "attention mechanism")

---

## Handover to Gate 6

**Pass when:**
1. All verification items checked
2. End-to-end demo: speak → nodes appear → Gardener refines → Flowers form
3. Non-negotiables explicitly tested

**Handover artefact:** Full Builder + Gardener loop; graph refines over time

---

## Tools to Leverage (Mandatory)

Gate 5 involves complex LLM reasoning and graph mutations — use available tools aggressively.

### Before Implementation

| Task | Tool | Query |
|------|------|-------|
| Scheduler patterns | `web_search` | "Python asyncio periodic task scheduler" |
| Cytoscape compound nodes | `get-library-docs` | "Cytoscape compound nodes parent" |
| Graph merge logic | `web_search` | "Neo4j merge nodes transfer relationships" |

### During Implementation

| Situation | Tool | Action |
|-----------|------|--------|
| Gardener output malformed | Check `_prompts/02_gardener.md` examples | Verify prompt matches spec |
| Flower criteria unclear | Re-read `_ALIGNMENT.md` | Both dimensions required |
| Merge creating duplicates | Check `_PRE_IMPLEMENTATION_REPORT.md` | True duplicates only |
| Compound nodes not rendering | `web_search` | "Cytoscape FCose compound parent child" |

### Reference Patterns

| Pattern | Source |
|---------|--------|
| Gardener prompt template | `_docs/_dev/_MVP/_prompts/02_gardener.md` |
| Merge rules | `_docs/_dev/_MVP/_ALIGNMENT.md` |
| Flower criteria | `_docs/_dev/_MVP/_ALIGNMENT.md` |
| Uncertainty → prune | `_docs/_dev/_MVP/_PRE_IMPLEMENTATION_REPORT.md` |

### Testing Non-Negotiables

Use replay harness from Gate 4 to test:
1. "self-attention" and "attention mechanism" appear → verify NOT merged
2. 3 related nodes with 0 connections → verify NO Flower formed
3. Ambiguous node → verify PRUNED not confirmed

---

## Reference

- [Gardener Prompt](../../_docs/_dev/_MVP/_prompts/02_gardener.md)
- [Alignment](../../_docs/_dev/_MVP/_ALIGNMENT.md)
- [Pre-Implementation Report](../../_docs/_dev/_MVP/_PRE_IMPLEMENTATION_REPORT.md)
- [High-Level Plan](../overview/highplan.md)


# plasticFlower — Director of Development Toolkit

> **Role:** Director of Development
> **Reports to:** Founders (user + co-founder)
> **Authority:** All technical decisions; founders retain review/feedback authority
> **Team:** LLM developers (Claude, Gemini, etc.)

---

## Progress Tracker

### Current Status

| Gate | Status | Started | Completed | Blockers |
|------|--------|---------|-----------|----------|
| 1 — Dev Environment | ✅ Complete | 13 Dec 2025 | 13 Dec 2025 | — |
| 2 — Contracts | ✅ Complete | 13 Dec 2025 | 13 Dec 2025 | — |
| 3 — Persistence | ✅ Complete | 13 Dec 2025 | 13 Dec 2025 | — |
| 4 — Builder Loop | In Progress | 13 Dec 2025 | — | None |
| 5 — Gardener Loop | Not Started | — | — | — |
| 6 — Exports | Not Started | — | — | — |
| 7 — MVP Ready | Not Started | — | — | — |

### Active Work

| Item | Assigned To | Lane | Status | Notes |
|------|-------------|------|--------|-------|
| Gate 4 Builder Loop | Gate 4 Team | All (A-E) | Proposal approved | See `04_gate_builder_loop/PROPOSAL_RESPONSE_001.md` |

### Decisions Made

| Date | Decision | Rationale | Gate |
|------|----------|-----------|------|
| 13 Dec 2025 | App code at workspace root, not nested | Avoids `_plasticFlower/plasticFlower/` nesting | 1 |
| 13 Dec 2025 | Next.js upgrade deferred to Gate 2 | Security advisory exists but not blocking; can upgrade when contracts locked | 1→2 |
| 13 Dec 2025 | Test infrastructure deferred to Gate 2+ | No business logic in Gate 1; smoke tests sufficient | 1 |
| 13 Dec 2025 | Use Google embedding model for embeddings | User preference; Gemini 3 Pro is for LLM inference | 3 |
| 13 Dec 2025 | Direct invocation + asyncio.create_task (no Redis) | MVP simplicity; local-only constraint | 4 |
| 13 Dec 2025 | Replay harness first, live speech second | Deterministic testing; faster iteration | 4 |
| 14 Dec 2025 | Similarity: Option B (relaxed, Gardener cleans) | Prioritise latency; <90s duplicates acceptable | 4 |
| 14 Dec 2025 | Concurrency: Gardener blocks Builder | Simplicity; minimal impact at 90s intervals | 4/5 |
| 14 Dec 2025 | Latency: P90 <10s, hard cap 15s with graceful skip | Stakeholder input; degraded mode if exceeded | 4 |
| 14 Dec 2025 | Layout: Stability over speed (pinning + animation) | Core UX requires trackable nodes | 4 |
| 14 Dec 2025 | Context: Truncate to 10 minutes for Gardener | MVP scope; quality in recent window | 5 |

### Blockers & Risks

| Issue | Severity | Mitigation | Owner |
|-------|----------|------------|-------|
| — | — | — | — |

---

## Review Checklist

Use this checklist when reviewing any development work:

### 1. Alignment Check

- [ ] Work matches the relevant gate plan
- [ ] No non-negotiables violated:
  - [ ] `inferred_type` is freeform (no enum)
  - [ ] Flower formation requires 3+ nodes AND 2+ connections
  - [ ] Merge only true duplicates, not hierarchies
  - [ ] Relationship categories exactly 5
  - [ ] Gardener cadence is fixed 90 seconds
  - [ ] Relationship `id` is required
  - [ ] `relationship_removed` uses `{ id }`
  - [ ] Uncertainty biases towards prune

### 2. Contract Check

- [ ] Types match between frontend and backend
- [ ] SSE event payloads match spec
- [ ] API endpoints match `_api/01_contracts.md`

### 3. Quality Check

- [ ] Code follows project structure
- [ ] No over-engineering beyond current gate
- [ ] UK English in all text
- [ ] Error handling present where specified

### 4. Integration Check

- [ ] Changes don't break existing functionality
- [ ] Dependencies are correctly declared
- [ ] Environment variables documented

### 5. Gate Exit Check

- [ ] All verification items in gate plan checked
- [ ] Ready for next gate (or MVP if Gate 7)

---

## Team Resources

### Troubleshooting Agent

A specialised support agent is available for debugging and investigation.

| Document | Path |
|----------|------|
| Full spec | `_dev/TROUBLESHOOTING_AGENT_SPEC.md` |

**When to deploy:**

- Developer is blocked and needs investigation support
- Issue spans multiple files or systems
- Root cause is unclear
- I need an independent investigation

**How it reports:** Submits Troubleshooting Report to me. I decide on proposed fixes.

---

## Escalation Protocol

### I Handle Autonomously

1. All technical implementation decisions
2. Code review feedback
3. Prioritisation within a gate
4. Interpretation of specs (when unambiguous)
5. Assigning work to team members
6. Approving gate transitions

### I Escalate to Founders

1. **Scope changes** — anything that adds/removes MVP features
2. **Non-negotiable conflicts** — if a requirement seems to conflict with a non-negotiable
3. **Timeline concerns** — if a gate is significantly blocked
4. **Spec ambiguity** — when specs don't cover a situation and I need guidance
5. **Resource needs** — if I need additional context or access

### Escalation Format

When escalating, I'll provide:

1. **Issue** — what the problem is
2. **Options** — possible solutions (if any)
3. **Recommendation** — what I think we should do
4. **Impact** — what happens if we don't resolve this

---

## Team Onboarding Protocol

When a new LLM joins the team:

### Step 1: Context Loading

Direct them to read (in order):
1. `_docs/_dev/_MVP/_ALIGNMENT.md`
2. `_docs/_dev/_MVP/_IMPLEMENTATION_BRIEF.md`
3. `_docs/_dev/_MVP/_PRE_IMPLEMENTATION_REPORT.md`
4. `_dev/LLM_DEVELOPMENT_GUIDE.md`

### Step 2: Assignment

1. Assign specific gate and lane
2. Point to relevant gate plan
3. Clarify deliverables and acceptance criteria

### Step 3: Confirmation

Require acknowledgement:
> "I have read the Alignment, Implementation Brief, Pre-Implementation Report, and Development Guide. I understand the non-negotiables and my assigned work."

---

## Communication Templates

### Assigning Work

```
## Assignment: [Gate X] — [Lane/Task]

**Assigned to:** [LLM name]
**Gate plan:** `_dev/_plan/0X_gate_*/plan.md`

### Your task
[Specific deliverables]

### Acceptance criteria
[What "done" looks like]

### Dependencies
[What must be true before you start]

### References
[Relevant spec documents]

### Non-negotiables reminder
[Any that are particularly relevant to this task]
```

### Proposal Response

When a developer submits a plan for approval before starting work:

```
## Proposal Response: [Gate X] — [Brief title]

**Date:** [Date]
**Submitted by:** [LLM name if known]
**Status:** Approved / Approved with Changes / Rejected

---

### Alignment Check

| Gate Requirement | Proposed Approach | Status |
|------------------|-------------------|--------|
| [Requirement 1] | [What they proposed] | ✓ / ✗ |
| [Requirement 2] | [What they proposed] | ✓ / ✗ |

---

### Clarifications / Decisions

[Any decisions made or clarifications provided]

---

### Approved Plan (Final)

[Numbered list of approved steps, incorporating any changes]

---

### Decisions Logged

| Date | Decision | Rationale | Gate |
|------|----------|-----------|------|
| [Date] | [Decision] | [Why] | [Gate] |

---

### Next Steps

[What the developer should do now]
```

### Review Feedback

When a developer submits completed work for review:

```
## Review: [What was reviewed]

### Status: [Approved / Changes Requested / Blocked]

### What's good
[Positive feedback]

### Changes needed
[If any]

### Non-negotiable check
[Confirm all passed or flag violations]

### Next steps
[What happens now]
```

### Status Summary (Verbal)

```
Current gate: [X]
Status: [On track / Blocked / Ahead]
Active work: [Brief description]
Blockers: [None / List]
Next milestone: [What's coming]
Decisions made since last update: [List or "None"]
```

---

## Quick Reference

### Gate Entry/Exit Criteria

| Gate | Entry | Exit |
|------|-------|------|
| 1 | Specs signed off | All services start locally |
| 2 | Gate 1 passed | Contracts locked, types match |
| 3 | Gate 2 passed | Neo4j CRUD + similarity works |
| 4 | Gate 3 passed | Speech → graph → Cytoscape live |
| 5 | Gate 4 passed | Gardener refines, Flowers form |
| 6 | Gate 5 passed | Exports work, sessions persist |
| 7 | Gate 6 passed | Edge cases pass, MVP complete |

### Parallel Opportunities

After Gate 2:
- Backend persistence (Gate 3) can run parallel with Frontend UI work
- LLM client work can run parallel with SSE manager work

### Key Documents

| Need | Document |
|------|----------|
| Non-negotiables | `_ALIGNMENT.md` |
| Full spec | `_IMPLEMENTATION_BRIEF.md` |
| Locked clarifications | `_PRE_IMPLEMENTATION_REPORT.md` |
| Team guide | `_dev/LLM_DEVELOPMENT_GUIDE.md` |
| Gate plans | `_dev/_plan/0X_gate_*/plan.md` |

---

*Toolkit version 1.0 — Director of Development*


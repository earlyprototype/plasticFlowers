# plasticFlower — LLM Development Guide

> **Purpose:** Instructions for LLM team members implementing this project
> **Audience:** Any LLM (Claude, Gemini, GPT, etc.) contributing to development
> **Version:** 1.0

---

## Before You Start

### Mandatory Reading (in order)

1. `_docs/_dev/_MVP/_ALIGNMENT.md` — Non-negotiable principles (READ FIRST)
2. `_docs/_dev/_MVP/_IMPLEMENTATION_BRIEF.md` — Full implementation overview
3. `_docs/_dev/_MVP/_PRE_IMPLEMENTATION_REPORT.md` — Locked clarifications
4. `_dev/_plan/README.md` — Plan pack index
5. The specific gate plan for your current task

**Do not begin implementation until you have read documents 1-3.**

---

## Key Context Documents

### Tier 1: Always Read First (Before Any Work)

| Document | Path | Summary | When to Use |
|----------|------|---------|-------------|
| **Alignment** | `_docs/_dev/_MVP/_ALIGNMENT.md` | Defines the 3 non-negotiable principles: emergent schema, dual-dimension Flowers, merge preserves specificity. Includes verification checklist and anti-patterns. | **Before every task.** Reference when making any decision that touches node types, Flower formation, or merge logic. |
| **Implementation Brief** | `_docs/_dev/_MVP/_IMPLEMENTATION_BRIEF.md` | Master reference document. Contains document tree, technology stack, architecture diagram, all endpoints, success criteria, and reading order. | **At session start.** Reference when you need to understand where something is documented or how components connect. |
| **Pre-Implementation Report** | `_docs/_dev/_MVP/_PRE_IMPLEMENTATION_REPORT.md` | Final clarifications locked before build: contradiction detection → post-MVP, Gardener = fixed 90s, uncertainty → prune, Relationship `id` required. | **When implementing contracts or agent logic.** Reference when you're unsure if something was clarified after the main specs. |

### Tier 2: Design Foundations (Reference During Implementation)

| Document | Path | Summary | When to Use |
|----------|------|---------|-------------|
| **Concept** | `_docs/_dev/_MVP/_overview/01_concept.md` | What plasticFlower is: live knowledge graph from speech, emergent schema, Flowers as thematic clusters. | When explaining the product or onboarding. |
| **Scope** | `_docs/_dev/_MVP/_overview/02_scope.md` | What's in MVP vs post-MVP vs excluded entirely. Lists all features with notes. | When deciding whether to implement something. |
| **Data Model** | `_docs/_dev/_MVP/_schema/01_data_model.md` | Core entities: Node, Relationship, Flower, Session, Chunk. All properties with types and purposes. | **When writing models, schemas, or database queries.** |
| **Schema Rationale** | `_docs/_dev/_MVP/_schema/02_design_rationale.md` | Why the schema is designed this way: emergent types, 5 categories + description, Flower membership on Node, bridges derived. | When you need to understand WHY a schema decision was made. |
| **System Architecture** | `_docs/_dev/_MVP/_architecture/01_system_overview.md` | High-level flow diagram: STT → similarity check → Builder → Neo4j → SSE → Cytoscape. Component responsibilities. | When understanding how data flows through the system. |
| **Agent Architecture** | `_docs/_dev/_MVP/_architecture/02_agents.md` | Builder (fast, per-chunk) vs Gardener (slow, 90s). Pre-Builder similarity check rule. | **When implementing Builder, Gardener, or similarity check.** |

### Tier 3: Implementation Specifications (Reference During Coding)

| Document | Path | Summary | When to Use |
|----------|------|---------|-------------|
| **Builder Prompt** | `_docs/_dev/_MVP/_prompts/01_builder.md` | Full Builder system prompt, input/output JSON schema, validation rules, example, error handling, token budget. | **When implementing Builder agent.** Copy prompt template from here. |
| **Gardener Prompt** | `_docs/_dev/_MVP/_prompts/02_gardener.md` | Full Gardener system prompt, input/output JSON schema, Flower quality assessment, stem node selection, scaling considerations. | **When implementing Gardener agent.** Copy prompt template from here. |
| **API Contracts** | `_docs/_dev/_MVP/_api/01_contracts.md` | All endpoints with request/response schemas. SSE event types and payloads. Data schemas. Error responses. Auto-reconnect spec. | **When implementing any endpoint or SSE logic.** |
| **Frontend Data Flow** | `_docs/_dev/_MVP/_frontend/01_data_flow.md` | Frontend architecture diagram, SSE event processing, state management (Maps), Cytoscape integration, FCose config, visual states, Z-filtering, auto-reconnect logic. | **When implementing frontend components.** |
| **Project Structure** | `_docs/_dev/_MVP/_structure/01_project_structure.md` | Directory layout, module responsibilities, configuration, Docker Compose, dependencies. | **When creating files or folders.** Follow this structure exactly. |

### Tier 4: Decision History (Reference When Uncertain)

| Document | Path | Summary | When to Use |
|----------|------|---------|-------------|
| **Decision Log** | `_docs/_dev/_MVP/_DECISION_LOG.md` | All 19 decisions with context, alternatives considered, and rationale. DEC-001 through DEC-019. | **When you need to understand WHY something is the way it is.** |
| **Conversations** | `_docs/_dev/_MVP/_CONVERSATIONS.md` | 7 key discussions that shaped decisions: clustering approach, relationship constraints, agreeableness check, knowledge-graph-kit assessment, Gemini verification, Builder decisions, drift review. | When you need deeper context on a specific decision. |
| **Drift Report** | `_docs/_dev/_MVP/_DRIFT_REPORT_001.md` | Documents 3 specification errors found and corrected: enum on inferred_type, missing Flower connection requirement, incorrect merge example. Root cause analysis. | When you want to understand what mistakes to avoid. |
| **Handover** | `_docs/_dev/_MVP/_HANDOVER.md` | Original context document for session continuity. Section A (essential), B (context), C (reference), D (next steps). | When starting a completely new context or onboarding. |

### Tier 5: Development Plans (Reference During Each Gate)

| Document | Path | Summary | When to Use |
|----------|------|---------|-------------|
| **Plan Pack Index** | `_dev/_plan/README.md` | Index of all gate plans with links. | At session start to see available gates. |
| **High-Level Plan** | `_dev/_plan/overview/highplan.md` | Top-level delivery map: workstreams, serial dependencies, handover gates, parallel opportunities. | When understanding overall approach. |
| **Gate 1: Dev Env** | `_dev/_plan/01_gate_dev_env/plan.md` | Repo skeleton, Docker Compose, backend/frontend scaffolds. | **When working on Gate 1.** |
| **Gate 2: Contracts** | `_dev/_plan/02_gate_contracts/plan.md` | Pydantic models, route stubs, TypeScript types, SSE event definitions. | **When working on Gate 2.** |
| **Gate 3: Persistence** | `_dev/_plan/03_gate_persistence/plan.md` | Neo4j connection, schema constraints, CRUD operations, vector index, similarity query. | **When working on Gate 3.** |
| **Gate 4: Builder Loop** | `_dev/_plan/04_gate_builder_loop/plan.md` | LLM client, Builder agent, chunk endpoint, SSE manager, frontend SSE, Cytoscape, speech capture. | **When working on Gate 4.** |
| **Gate 5: Gardener Loop** | `_dev/_plan/05_gate_gardener_loop/plan.md` | Scheduler, Gardener agent, node actions, Flower actions, SSE events, compound nodes. | **When working on Gate 5.** |
| **Gate 6: Exports** | `_dev/_plan/06_gate_exports/plan.md` | Session end/restore, export endpoints, export UI, Z-filtering. | **When working on Gate 6.** |
| **Gate 7: MVP Ready** | `_dev/_plan/07_gate_mvp_ready/plan.md` | Edge case testing, non-negotiables verification, success criteria, final sign-off. | **When working on Gate 7.** |

### Tier 6: Discovery (Reference Only)

| Document | Path | Summary | When to Use |
|----------|------|---------|-------------|
| **Repository Index** | `_discovery/_repo/_INDEX.md` | External repos analysed during research. | If you need to look at reference implementations. |
| **Leverage Guide** | `_discovery/_repo/_LEVERAGE_GUIDE.md` | What to extract from each external repo: GraphRAG prompts, Graphiti streaming patterns, etc. | When implementing patterns from reference repos. |

---

## Working Style Expectations

### Communication

| Expectation | Meaning |
|-------------|---------|
| **Step-by-step** | Discuss approach before implementing |
| **Ask before changing** | Get confirmation before modifying code or specs |
| **Consult on decisions** | Involve the user in choices |
| **React to feedback** | Adjust based on user input before proceeding |
| **UK English only** | All code comments, docs, and UI text |

### Development Approach

| Expectation | Meaning |
|-------------|---------|
| **Verify, don't assume** | Read source documents, not summaries |
| **Preserve intent** | Understand WHY, not just WHAT |
| **Flag drift immediately** | If you notice inconsistency, raise it |
| **Ask before simplifying** | Simplification may lose critical nuance |
| **Examples must be correct** | Wrong examples teach wrong patterns |

### Code Quality

| Expectation | Meaning |
|-------------|---------|
| **Incremental** | Small, testable changes |
| **Confirm before commit** | Get approval before finalising |
| **No over-engineering** | Only build what's needed for the current gate |
| **Follow existing patterns** | Match the codebase style |

---

## Non-Negotiables (Must Enforce)

These rules **must not be violated** during implementation:

| # | Principle | Rule | Consequence of Violation |
|---|-----------|------|--------------------------|
| 1 | **Emergent schema** | `inferred_type` is freeform string | No enum constraints anywhere |
| 2 | **Flower formation** | Requires 3+ nodes AND 2+ internal connections | Both criteria must be checked |
| 3 | **Merge rules** | Only true duplicates (synonyms/acronyms/spelling) | Never merge hierarchies |
| 4 | **Relationship categories** | Exactly 5: CAUSAL, STRUCTURAL, COMPARATIVE, TEMPORAL, ASSOCIATIVE | No additions or removals |
| 5 | **Gardener cadence** | Fixed every 90 seconds | Not adaptive, not configurable |
| 6 | **Relationship identity** | `id` is required; `relationship_removed` uses `{ id }` | No composite keys |
| 7 | **Graph noise policy** | Uncertainty → prune/expel | Never confirm when unsure |
| 8 | **Pre-Builder similarity** | >= 0.85 threshold | Match → increment, not create |

### Anti-Patterns (Do Not Do)

| Anti-Pattern | Why It's Wrong |
|--------------|----------------|
| `inferred_type: "concept" \| "person" \| "framework"` | Violates emergent schema |
| Flower with 3 nodes but 0 connections | Violates dual criteria |
| Merging "self-attention" into "attention mechanism" | Hierarchy flattening |
| Adding `DEFINITIONAL` relationship category | Only 5 categories allowed |
| Gardener runs "when needed" | Must be fixed 90 seconds |
| `relationship_removed: { source_id, target_id }` | Must use `{ id }` |

---

## Gate-Based Development

### How It Works

1. Development proceeds through **7 gates**
2. Each gate has **entry criteria** (what must be true before starting)
3. Each gate has **exit criteria** (what must be true before passing)
4. **Do not skip gates** — they exist to prevent integration failures
5. **Get sign-off** at each gate handover

### Current Gate Plans

| Gate | Plan Location | Objective |
|------|---------------|-----------|
| 1 | `_dev/_plan/01_gate_dev_env/plan.md` | Dev environment green |
| 2 | `_dev/_plan/02_gate_contracts/plan.md` | Contracts locked |
| 3 | `_dev/_plan/03_gate_persistence/plan.md` | Graph persistence operational |
| 4 | `_dev/_plan/04_gate_builder_loop/plan.md` | Builder end-to-end loop |
| 5 | `_dev/_plan/05_gate_gardener_loop/plan.md` | Gardener refinement loop |
| 6 | `_dev/_plan/06_gate_exports/plan.md` | Exports + session lifecycle |
| 7 | `_dev/_plan/07_gate_mvp_ready/plan.md` | MVP readiness |

### Before Starting a Gate

1. Read the gate's `plan.md` fully
2. Confirm entry criteria are met
3. Identify which lane you're working on (if parallel)
4. Understand serial dependencies within the gate

### After Completing Work

1. Run the verification checklist in the gate plan
2. Report what was done
3. Wait for sign-off before proceeding to next gate

---

## Project Structure

### Documentation

```
_docs/_dev/_MVP/
├── _ALIGNMENT.md             ← Non-negotiables (read first)
├── _IMPLEMENTATION_BRIEF.md  ← Full overview
├── _PRE_IMPLEMENTATION_REPORT.md ← Locked clarifications
├── _DECISION_LOG.md          ← All 19 decisions with rationale
├── _CONVERSATIONS.md         ← Key discussions
├── _schema/                   ← Data model
├── _prompts/                  ← Builder + Gardener prompts
├── _api/                      ← API contracts
├── _frontend/                 ← Frontend data flow
└── _structure/                ← Project structure
```

### Plans

```
_dev/_plan/
├── README.md                  ← Plan pack index
├── overview/highplan.md       ← High-level delivery map
├── 01_gate_dev_env/plan.md
├── 02_gate_contracts/plan.md
├── 03_gate_persistence/plan.md
├── 04_gate_builder_loop/plan.md
├── 05_gate_gardener_loop/plan.md
├── 06_gate_exports/plan.md
└── 07_gate_mvp_ready/plan.md
```

### Source Code (to be created)

```
plasticFlower/
├── frontend/                  ← Next.js app
│   └── src/
├── backend/                   ← FastAPI app
│   └── app/
└── docker/                    ← Docker Compose
```

---

## Technology Stack

| Component | Technology | Documentation |
|-----------|------------|---------------|
| Frontend | Next.js 14 | nextjs.org/docs |
| Backend | FastAPI | fastapi.tiangolo.com |
| Database | Neo4j 5 | neo4j.com/docs |
| LLM | Gemini 3 Pro | ai.google.dev |
| Visualisation | Cytoscape.js + FCose | js.cytoscape.org |
| STT | Web Speech API | MDN Web Docs |
| Real-time | SSE (sse-starlette) | PyPI |

---

## Available Tools (Use Aggressively)

You have access to tools that accelerate development. **Use them proactively** — don't struggle with stale knowledge or guesswork.

### Documentation Lookup

| Tool | When to Use | Example |
|------|-------------|---------|
| `get-library-docs` | Need current API for any library | "How do I create a vector index in Neo4j 5?" |
| `hf_doc_search` | Need HuggingFace/Gradio docs | "How do I use sentence-transformers?" |

**Mandatory usage:** Before implementing anything with FastAPI, Next.js, Neo4j, or Cytoscape — query docs first. Don't rely on training data.

### Research & Discovery

| Tool | When to Use | Example |
|------|-------------|---------|
| `web_search` | Error messages, recent library changes | "Neo4j vector index queryNodes syntax" |
| `paper_search` | Academic approaches to a problem | "knowledge graph extraction from speech" |
| `model_search` | Find embedding models | "text embedding models for semantic similarity" |

**Mandatory usage:** When implementing LLM prompts or embedding logic — search for current best practices.

### Codebase Analysis

| Tool | When to Use | Example |
|------|-------------|---------|
| `codebase_search` | Find how something is done in project | "How is SSE handled in this project?" |
| `grep` | Find exact text/symbols | Search for `inferred_type` usage |
| `read_file` | Read specific files | Read the contract snapshot |

**Mandatory usage:** Before modifying any file — read it first. Before adding new patterns — search for existing patterns.

### Quick Reference: Tool by Situation

| Situation | Tool to Use First |
|-----------|-------------------|
| "How do I do X in FastAPI?" | `get-library-docs` (FastAPI) |
| "How do I do X in Next.js?" | `get-library-docs` (Next.js) |
| "How do I do X in Neo4j?" | `get-library-docs` (Neo4j) → `web_search` |
| "How do I do X in Cytoscape?" | `get-library-docs` (Cytoscape) |
| "This error message..." | `web_search` (paste error) |
| "Best approach for..." | `paper_search` or `web_search` |
| "Is there existing code for..." | `codebase_search` or `grep` |
| "What embedding model..." | `model_search` |
| "Similar projects..." | `_discovery/_repo/` folder or `web_search` |

### Discovery Assets (Already in Project)

The `_discovery/_repo/` folder contains pre-analysed reference repositories:

| Repository | What to Leverage |
|------------|------------------|
| `graphiti` | Real-time KG streaming patterns |
| `graphrag` | LLM extraction prompt structures |
| `graphster` | Graph construction approaches |
| `knowledge-graph-kit` | Local tool patterns (already explored) |

**When to use:** Before implementing Builder/Gardener prompts or streaming logic — check `_discovery/_repo/_LEVERAGE_GUIDE.md`.

### Tool Usage Protocol

1. **Before implementing:** Query docs for current syntax/patterns
2. **When stuck:** Search web for error messages or approaches
3. **Before modifying:** Read existing code to match patterns
4. **When unsure:** Search for prior art (papers, repos, models)
5. **After implementing:** Verify against current docs

**Anti-pattern:** Implementing from memory without checking current docs — libraries change, training data is stale.

---

## Common Tasks

### Starting a New Session

When you're a new LLM picking up this project:

```
I'm continuing plasticFlower development. 

Read these files first:
1. _docs/_dev/_MVP/_ALIGNMENT.md
2. _docs/_dev/_MVP/_IMPLEMENTATION_BRIEF.md
3. _docs/_dev/_MVP/_PRE_IMPLEMENTATION_REPORT.md

Then tell me which gate you want to work on.
```

### Checking Non-Negotiables

Before completing any implementation, verify:

- [ ] `inferred_type` allows any string value (no enum)
- [ ] Flower formation requires 3+ nodes AND 2+ connections
- [ ] Merge only true duplicates, not hierarchies
- [ ] Relationship categories exactly: CAUSAL, STRUCTURAL, COMPARATIVE, TEMPORAL, ASSOCIATIVE
- [ ] Gardener runs every 90 seconds (fixed)
- [ ] `relationship_removed` uses `{ id }`
- [ ] Uncertainty biases towards prune

### Handling Ambiguity

If a specification decision isn't clearly covered:

1. **State the ambiguity** — "The spec doesn't clarify X"
2. **Propose options** — "Options are A, B, or C"
3. **Recommend with rationale** — "I recommend B because..."
4. **Wait for confirmation** — Do not proceed without user input

Do not default to "safe" patterns (enums, simplifications) without explicit approval.

---

## Reporting to Director of Development

All development work is reviewed by the Director of Development. Use these formats when reporting.

### 0. Plan Proposal (Before Starting Work)

Before beginning a gate or significant task, submit a proposal for approval:

```
## Proposed Plan: [Gate X] — [Brief title]

**Gate:** [1-7]
**Lanes involved:** [A/B/C or "All"]

### Proposed approach
[Numbered list of steps you plan to take]

### Deliverables
[What you'll produce]

### Dependencies
[What must be true before you start]

### Questions / Uncertainties
[Anything you're unsure about]

Please confirm before I start.
```

**You will receive:** A Proposal Response document with:
- Alignment check against gate requirements
- Any clarifications or decisions
- Approved plan (final version)
- Next steps

**Do not begin work until you receive approval.**

---

### 1. Work Completion Report

When you finish a deliverable, submit this:

```
## Work Complete: [Brief title]

**Gate:** [1-7]
**Lane:** [A/B/C or "Serial"]
**Deliverable:** [What was built]

### What was done
[Bullet list of changes made]

### Files created/modified
[List of file paths]

### Self-check against non-negotiables
- [ ] inferred_type is freeform (if applicable)
- [ ] Flower criteria enforced (if applicable)
- [ ] Merge rules followed (if applicable)
- [ ] Relationship categories correct (if applicable)
- [ ] Gardener cadence = 90s (if applicable)
- [ ] Relationship id used (if applicable)

### Ready for review
[Yes / No - if no, explain what's pending]
```

### 2. Blocker Report

When you're stuck, submit this:

```
## Blocker: [Brief title]

**Gate:** [1-7]
**Severity:** [High / Medium / Low]

### What's blocked
[Description]

### Why it's blocked
[Root cause]

### What I've tried
[Attempts made]

### What I need
[Specific ask - decision, access, clarification]
```

### 3. Decision Request

When you need a technical decision, submit this:

```
## Decision Needed: [Brief title]

**Gate:** [1-7]
**Blocking:** [Yes / No]

### Context
[What prompted this]

### Options
1. [Option A] — [Pros/cons]
2. [Option B] — [Pros/cons]
3. [Option C] — [Pros/cons]

### My recommendation
[Which option and why]

### Impact if delayed
[What happens if we don't decide]
```

### What You'll Receive Back

The Director will respond with a Review:

```
## Review: [What was reviewed]

**Status:** Approved / Changes Requested / Blocked

### Alignment check
[Pass / Fail with details]

### Non-negotiables check
[All passed / Violations found]

### Quality notes
[Feedback]

### Decision
[Approved to proceed / Changes required before proceeding]

### Next steps
[What happens now]
```

### Summary

| When | Format | Submit To | Response |
|------|--------|-----------|----------|
| Before starting work | Plan Proposal | Director for approval | Proposal Response |
| Finished work | Work Completion Report | Director for review | Review Feedback |
| Hit a blocker | Blocker Report | Director to unblock | Resolution |
| Need a decision | Decision Request | Director to decide | Decision |

---

## Troubleshooting Agent

If you encounter a complex issue and need investigation support, you can request the Troubleshooting Agent.

**What it does:**
- Investigates issues across files and systems
- Uses MCP tools to diagnose problems
- Proposes fixes (does not implement)
- Reports findings to Director

**When to request:**
- Root cause is unclear
- Issue spans multiple components
- You've tried basic debugging without success

**How to request:**

```
## Troubleshooting Request

**Gate:** [1-7]
**Issue type:** [Error / Unexpected behaviour / Performance / Integration / Other]

### What's happening
[Description of the issue]

### Expected behaviour
[What should happen]

### Error messages / logs
[Paste relevant output]

### What I've tried
[Attempts made]

### Relevant files
[List of files involved]
```

The Director will deploy the Troubleshooting Agent and you'll receive a report with proposed resolutions.

---

## Environment

### User's Setup

| Setting | Value |
|---------|-------|
| OS | Windows 10/11 |
| Shell | PowerShell |
| Language | UK English |
| IDE | Cursor |

### Required Environment Variables

```
NEO4J_PASSWORD=<password>
GEMINI_API_KEY=<api_key>
```

Document these in `.env.example` (never commit actual values).

---

## User Preferences (Remembered)

These preferences apply across all sessions:

| Preference | Detail |
|------------|--------|
| Ask before changes | Confirm before modifying code |
| Step-by-step discussion | Don't dump large changes |
| Numbered lists | No `>` or `-` characters |
| Concise system language | Brief, direct |
| UK English | All text |
| No hyperbole | Factual tone |
| ADHD support | Break tasks into clear steps |

---

## Quick Reference

### By Task: Which Document to Read

| Task | Primary Document | Secondary |
|------|------------------|-----------|
| **Starting a session** | `_IMPLEMENTATION_BRIEF.md` | `_ALIGNMENT.md` |
| **Writing Pydantic models** | `_schema/01_data_model.md` | `_api/01_contracts.md` |
| **Implementing Builder** | `_prompts/01_builder.md` | `_architecture/02_agents.md` |
| **Implementing Gardener** | `_prompts/02_gardener.md` | `_architecture/02_agents.md` |
| **Creating API endpoints** | `_api/01_contracts.md` | `_PRE_IMPLEMENTATION_REPORT.md` |
| **Building frontend** | `_frontend/01_data_flow.md` | `_api/01_contracts.md` |
| **Creating files/folders** | `_structure/01_project_structure.md` | — |
| **Understanding a decision** | `_DECISION_LOG.md` | `_CONVERSATIONS.md` |
| **Checking if something is in scope** | `_overview/02_scope.md` | `_PRE_IMPLEMENTATION_REPORT.md` |
| **Avoiding past mistakes** | `_DRIFT_REPORT_001.md` | `_ALIGNMENT.md` |

### Key Decisions Quick Lookup

| Decision | ID | Summary |
|----------|-----|---------|
| Emergent schema | DEC-002 | LLM determines types, not predefined |
| 5 relationship categories | DEC-005 | CAUSAL, STRUCTURAL, COMPARATIVE, TEMPORAL, ASSOCIATIVE + description |
| 90-second Gardener | DEC-004 | Fixed interval, not adaptive |
| Web Speech API | DEC-007 | Free, browser-native, quality acceptable for MVP |
| Cytoscape + FCose | DEC-008 | Handles compound nodes (Flowers) and stable live updates |
| Builder extracts relationships | DEC-016 | Chunk-local relationships, not entities only |
| Strict JSON output | DEC-018 | Reliable parsing, easy validation |
| Labels-only context | DEC-019 | Compact (~200 tokens for 50 nodes), grouped by type |

### Non-Negotiables Checklist (Copy This)

```
Before completing any implementation, verify:

- [ ] `inferred_type` allows any string value (no enum)
- [ ] Flower formation requires 3+ nodes AND 2+ connections
- [ ] Merge only true duplicates, not hierarchies
- [ ] Relationship categories exactly: CAUSAL, STRUCTURAL, COMPARATIVE, TEMPORAL, ASSOCIATIVE
- [ ] Gardener runs every 90 seconds (fixed)
- [ ] Relationship `id` is required
- [ ] `relationship_removed` uses `{ id }`
- [ ] Uncertainty biases towards prune/expel
```

---

## Acknowledgement

Before beginning implementation work, confirm:

> "I have read the Alignment Document, Implementation Brief, and Pre-Implementation Report. I understand the non-negotiables and will verify my work against the checklist before completion. I will ask before making changes and wait for sign-off at gate handovers."

---

*This guide should be referenced at the start of every development session.*


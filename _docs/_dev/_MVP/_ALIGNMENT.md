# plasticFlower — Development Alignment Document

> **For:** Development LLM (any context continuing this project)
> **From:** Project co-founders
> **Purpose:** Ensure specification fidelity and prevent design drift

---

## Why This Document Exists

A review of work completed after initial handover identified significant drift from agreed decisions. Three core design principles were violated despite being documented in the Decision Log and Conversations files.

This document establishes alignment expectations for all future development work.

---

## Core Principle

**The handover documents are the source of truth.**

When you read a summary or progress file, you are reading someone else's interpretation. When you create specifications, you must verify against the original decision documents.

---

## Mandatory Reading Before Any Specification Work

| Document | Path | Contains |
|----------|------|----------|
| **Decision Log** | `_docs/_dev/_MVP/_DECISION_LOG.md` | Every decision with rationale |
| **Conversations** | `_docs/_dev/_MVP/_CONVERSATIONS.md` | Discussions that shaped decisions |
| **Data Model** | `_docs/_dev/_MVP/_schema/01_data_model.md` | Agreed schema |
| **Schema Rationale** | `_docs/_dev/_MVP/_schema/02_design_rationale.md` | Why the schema is designed this way |

Do not proceed with specification work until you have read these files.

---

## Key Design Principles (Non-Negotiable)

### 1. Emergent Schema

**Principle:** The LLM discovers types; we do not predefine them.

**Why:** plasticFlower is domain-agnostic. A talk on biology produces different types than a talk on business. Predefined types force content into ill-fitting categories.

**Implementation:**
- `inferred_type` is a freeform string
- No enum constraints on node types
- Examples may show common types, but must not imply constraint

**Anti-pattern:** `"inferred_type": "concept|person|framework|method"` — this violates emergent schema.

---

### 2. Dual-Dimension Flowers

**Principle:** Flowers require both semantic coherence AND structural density.

**Why:** Semantic coherence alone allows thin clusters (3 related concepts with no connections). Structural density alone allows meaningless clusters (highly connected but semantically incoherent). Both dimensions are necessary.

**Implementation:**
- Flower formation: 3+ nodes AND 2+ internal connections
- Both criteria must be met

**Anti-pattern:** "3+ nodes share a clear theme" without connection requirement — this drops half the criteria.

---

### 3. Merge Preserves Specificity

**Principle:** Merge only true duplicates. Do not flatten hierarchies.

**Why:** "Self-attention" and "attention mechanism" are related but distinct. Merging them loses information the speaker deliberately distinguished.

**Implementation:**
- Merge: synonyms, acronyms, spelling variants
- Do not merge: subset/superset relationships, related but distinct concepts

**Anti-pattern:** Merging "self-attention" into "attention mechanism" because one is "a form of" the other — this flattens knowledge.

---

## Before Completing Any Specification

Run this checklist:

### Schema Alignment
- [ ] Does `inferred_type` allow any value (not constrained to enum)?
- [ ] Are node properties consistent with `_schema/01_data_model.md`?
- [ ] Are relationship categories exactly: CAUSAL, STRUCTURAL, COMPARATIVE, TEMPORAL, ASSOCIATIVE?

### Flower Alignment
- [ ] Does Flower formation require 3+ nodes?
- [ ] Does Flower formation require 2+ internal connections?
- [ ] Is semantic coherence evaluated by LLM?
- [ ] Is structural density measured (edge count)?

### Merge Alignment
- [ ] Does merge criteria specify TRUE DUPLICATES ONLY?
- [ ] Does merge criteria explicitly exclude subset/superset relationships?
- [ ] Do examples demonstrate correct merge (synonyms, not hierarchies)?

### Decision Alignment
- [ ] Have I re-read `_DECISION_LOG.md` for relevant decisions?
- [ ] Have I checked `_CONVERSATIONS.md` for context on why decisions were made?
- [ ] Does my specification match the stated rationale, not just the summary?

---

## When Uncertain

If a specification decision isn't clearly covered by existing documents:

1. **State the ambiguity** — "The handover doesn't specify X"
2. **Propose options** — "Options are A, B, or C"
3. **Recommend with rationale** — "I recommend B because..."
4. **Wait for confirmation** — Do not proceed without user input

Do not default to "safe" patterns (enums, simplifications) without explicit approval.

---

## Working Style Expectations

| Expectation | Meaning |
|-------------|---------|
| **Verify, don't assume** | Read source documents, not summaries |
| **Preserve intent, not just form** | Understand WHY, not just WHAT |
| **Flag drift immediately** | If you notice inconsistency, raise it |
| **Ask before simplifying** | Simplification may lose critical nuance |
| **Examples must be correct** | Wrong examples teach wrong patterns |

---

## What Happens If You Drift

Your specifications will be reviewed. If drift is identified:

1. Work will be corrected
2. A drift report will be filed
3. Alignment document will be updated

This is not punitive — it's quality control. The goal is a coherent product, not perfect performance.

---

## Summary

| Principle | Correct | Incorrect |
|-----------|---------|-----------|
| Schema | Emergent, freeform types | Constrained enum |
| Flowers | 3+ nodes AND 2+ connections | 3+ nodes only |
| Merge | True duplicates only | Hierarchy flattening |
| Process | Read Decision Log first | Work from summaries |

---

## Acknowledgment

Before proceeding with development work, confirm:

> "I have read the Alignment Document, Decision Log, and Conversations file. I understand the three core principles and will verify my specifications against the checklist before completion."

---

*Document version 1.0 — Created following Drift Report 001*



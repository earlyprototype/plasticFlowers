# Drift Report 001: Post-Handover Specification Errors

> **Date:** December 2024
> **Reviewer:** Co-founder (Claude)
> **Severity:** High
> **Status:** Corrected

---

## Summary

Three significant drifts from agreed decisions were identified in the prompt specifications created after handover. All have been corrected.

---

## Issue 1: Emergent Schema Violation (CRITICAL)

### What Was Agreed

**DEC-002 (Decision Log):**
> "Emergent schema — LLM determines node types"

**_CONVERSATIONS.md Conv-004:**
> knowledge-graph-kit was downgraded in priority due to "predefined types" conflicting with emergent schema

**Schema Rationale Document:**
> "Nodes have `inferred_type` (LLM's guess) rather than predefined categories."

### What Was Implemented

Builder spec line 54:
```
"inferred_type": "string (concept|person|framework|method|term|other)"
```

Six predefined types — the exact opposite of emergent schema.

### Correction Applied

Changed to:
```
"inferred_type": "string (your best categorisation — emergent, not constrained)"
```

Validation rules updated to specify freeform string.

### Root Cause Analysis

The post-handover LLM likely:
1. Prioritised parsing reliability over design intent
2. Defaulted to common patterns (enums are "safer" for JSON parsing)
3. Did not re-read the Decision Log or Conversations document
4. Missed the explicit "emergent, not predefined" principle

---

## Issue 2: Flower Threshold Incomplete (MAJOR)

### What Was Agreed

Multiple documents state: **"3+ nodes with 2+ internal connections"**

This dual requirement ensures Flowers are both:
- Meaningfully sized (3+ nodes)
- Actually connected (2+ internal edges)

### What Was Implemented

Gardener spec line 207:
> "3+ nodes share a clear theme"

The connection requirement was completely omitted.

### Correction Applied

Added:
> "3+ nodes share a clear theme"
> "Nodes have 2+ internal connections (relationships between members)"

Validation rules updated.

### Root Cause Analysis

The post-handover LLM likely:
1. Focused on semantic coherence (LLM's strength)
2. Overlooked the structural requirement (algorithmic check)
3. Did not recall the discussion about "both dimensions matter"
4. Simplified unintentionally

---

## Issue 3: Merge Criteria Too Broad (SIGNIFICANT)

### What Was Agreed

Merge should consolidate **true duplicates**:
- Synonyms
- Acronyms/expansions
- Spelling variants

Merge should NOT flatten **hierarchical relationships** where specificity matters.

### What Was Implemented

Example showed merging "self-attention" into "attention mechanism" with reason:
> "Self-attention is a specific form of attention mechanism"

This explicitly demonstrates subset-flattening — the opposite of preserving specificity.

### Correction Applied

1. Added explicit "DO NOT MERGE" criteria
2. Fixed example to show legitimate merge (hyphenation variant)

### Root Cause Analysis

The post-handover LLM likely:
1. Interpreted "merge similar concepts" too broadly
2. Did not distinguish synonymy from hyponymy
3. Used an intuitive but incorrect example

---

## Why Did This Happen?

### Handover Gaps

| Gap | Impact |
|-----|--------|
| Decision rationale not emphasised | LLM didn't understand WHY emergent schema mattered |
| Flower threshold stated but not explained | Connection requirement seemed optional |
| No explicit "anti-patterns" in handover | LLM didn't know what to avoid |

### LLM Behaviour Patterns

| Pattern | Effect |
|---------|--------|
| Default to "safe" structures | Enums over freeform strings |
| Simplify when uncertain | Dropped connection requirement |
| Example-driven reasoning | Created intuitive but incorrect merge example |

---

## Recommendations for Future Handovers

### 1. Add "Anti-Pattern" Section

Document what NOT to do, not just what to do.

```markdown
## Anti-Patterns (Do Not Do This)

- Do NOT constrain inferred_type to a predefined list
- Do NOT form Flowers without connection requirement
- Do NOT merge hierarchically related concepts
```

### 2. Include "Why" for Every Decision

Not just "emergent schema" but "emergent schema BECAUSE domain-agnostic requires unknown types."

### 3. Add Validation Checklist

Before completing work:
- [ ] Does inferred_type allow any value?
- [ ] Does Flower formation require 3+ nodes AND 2+ connections?
- [ ] Does merge criteria exclude subset relationships?

### 4. Require Decision Log Review

First instruction: "Read _DECISION_LOG.md before creating specifications."

---

## Corrections Summary

| File | Line(s) | Change |
|------|---------|--------|
| `01_builder.md` | 54 | Removed type constraint |
| `01_builder.md` | 77 | Changed validation to freeform |
| `01_builder.md` | 101-105 | Added emergent type instruction |
| `02_gardener.md` | 163 | Fixed member validation |
| `02_gardener.md` | 207-209 | Added connection requirement |
| `02_gardener.md` | 196-203 | Added DO NOT MERGE criteria |
| `02_gardener.md` | 249-253 | Fixed example (ghost nodes) |
| `02_gardener.md` | 285-288 | Fixed example (merge reason) |

---

## Status

All issues corrected. Specifications now align with pre-handover decisions.

---

*Report filed by co-founder review process.*



# Architecture Decision Records

This folder contains Architecture Decision Records (ADRs) for the plasticFlower project.

## What is an ADR?

An ADR captures an important architectural decision along with its context and consequences. They serve as a decision log that helps current and future team members (including LLMs) understand why the system is built the way it is.

## When to Create an ADR

**Always create an ADR when:**
- Choosing between 2+ technical approaches (even implementation-level options)
- Deciding NOT to implement something
- Changing a previous decision
- Any choice affecting system structure

**Include fine-grained decisions.** When presented with options (e.g., "Option A vs Option B"), document the choice even if it seems minor. This:
- Prevents re-debating the same options in future sessions
- Provides context for LLM coding assistants
- Captures reasoning that would otherwise be lost

**Examples of ADR-worthy decisions:**
- Major: "LLM clustering vs GDS algorithms" (ADR-001)
- Medium: "Async agents vs LangGraph" (ADR-006)
- Fine-grained: "LIMIT + Python vs Cypher word counting" (ADR-007)

**Err on the side of documenting.** A short ADR takes 2 minutes to create but saves hours of re-discussion.

## Quick Reference

| # | Title | Status | Date |
|---|-------|--------|------|
| [001](./0001-llm-clustering-over-gds.md) | LLM-Only Clustering (No GDS Initially) | Accepted | 2025-12-26 |
| [002](./0002-proofreading-in-gardener.md) | Proofreading Merged into Gardener | Accepted | 2025-12-26 |
| [003](./0003-gemini-grounding-for-research.md) | Gemini Grounding for Research | Accepted | 2025-12-26 |
| [004](./0004-full-context-qa.md) | Full Context Q&A (No GraphRAG for Single Session) | Accepted | 2025-12-26 |
| [005](./0005-lite-architecture-for-poc.md) | Lite Architecture for POC | Accepted | 2025-12-26 |
| [006](./0006-async-agents-over-langgraph.md) | Async Event-Driven Agents over LangGraph | Accepted | 2025-12-26 |
| [007](./0007-limit-based-transcript-retrieval.md) | LIMIT-Based Transcript Retrieval | Accepted | 2025-12-26 |
| [008](./0008-similarity-threshold-tuning.md) | Similarity Threshold Tuned to 0.92 | Accepted | 2025-12-26 |
| [009](./0009-redis-only-agent-scheduling.md) | Redis-Only Agent Scheduling | Accepted | 2025-12-27 |
| [010](./0010-ratio-based-agent-triggering.md) | Ratio-Based Agent Triggering | Accepted | 2025-12-27 |
| [011](./0011-pre-creation-similarity-check.md) | Pre-Creation Similarity Check in Builder | Accepted | 2025-12-30 |
| [012](./0012-gemini-config-helper-pattern.md) | Centralised Gemini Config Helper Pattern | Accepted | 2025-12-30 |
| [013](./0013-embedding-based-type-compatibility.md) | Embedding-Based Type Compatibility | Accepted | 2025-12-30 |

## Status Definitions

| Status | Meaning |
|--------|---------|
| **Proposed** | Under discussion, not yet decided |
| **Accepted** | Decision made and in effect |
| **Deprecated** | No longer recommended, but still in codebase |
| **Superseded** | Replaced by a newer ADR |

## Creating New ADRs

1. Copy `_TEMPLATE.md` to a new file: `NNNN-short-title.md`
2. Fill in all sections
3. Update this INDEX.md
4. Commit with message: `docs(adr): Add ADR-NNNN [title]`

Or ask the LLM: "Create an ADR for [decision]" with the template attached.

## LLM Usage

When starting a session that involves architectural decisions, attach:
- This INDEX.md (for context on existing decisions)
- Relevant individual ADRs (for specific context)

When a decision is made, say: "Create an ADR for this decision" and the LLM will generate it.

## Related Development Aids

These companion documents support ADRs:

| Document | Purpose |
|----------|---------|
| [`../VALIDATED_PATTERNS.md`](../VALIDATED_PATTERNS.md) | Proven code patterns from the codebase |
| [`../SOLUTIONS_LOG.md`](../SOLUTIONS_LOG.md) | Problem/solution log for debugging |
| [`../CYPHER_PATTERNS.md`](../CYPHER_PATTERNS.md) | Neo4j Cypher quick reference |
| [`../TEST_FIXTURES.md`](../TEST_FIXTURES.md) | Sample transcripts and test data |
| [`../fixtures/`](../fixtures/) | JSON fixture files for testing |
| [`../REFERENCE_SOURCES.md`](../REFERENCE_SOURCES.md) | External learning resources and references |

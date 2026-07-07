# plasticFlower Development Session State

**Purpose:** Persistent context for LLM-assisted development across sessions  
**How to use:** Attach this file at the start of each coding session

---

## Quick Start for New Session

### Minimum Context (Always Attach)

```
I'm continuing plasticFlower development.

Context: @_docs/_START_SESSION_STATE.md

[Describe what you want to work on today]
```

### Full Context (Architecture Work)

```
I'm continuing plasticFlower development.

Context files:
- @_docs/_START_SESSION_STATE.md (progress)
- @_docs/ARCHITECTURE_ADVISORY.md (full stack design)
- @_docs/LEARNING_GUIDE.md (phase exercises)
- @_docs/_dev/ADR/INDEX.md (decisions)

[Describe what you want to work on today]
```

### Coding Session (Implementation Work)

```
I'm continuing plasticFlower development.

Context files:
- @_docs/_START_SESSION_STATE.md (progress)
- @_docs/LEARNING_GUIDE.md (phase exercises)
- @_docs/_dev/VALIDATED_PATTERNS.md (code patterns)
- @_docs/_dev/CYPHER_PATTERNS.md (Neo4j reference)

Working on: [specific task]
```

### Debugging Session

```
I'm debugging a plasticFlower issue.

Context files:
- @_docs/_START_SESSION_STATE.md (progress)
- @_docs/_dev/SOLUTIONS_LOG.md (past solutions)
- @_docs/_dev/VALIDATED_PATTERNS.md (working patterns)

Issue: [describe problem]
```

### Lite Version Work

```
I'm working on plasticFlower Lite (browser-only version).

Context files:
- @_docs/_START_SESSION_STATE.md (progress)
- @_docs/LITE_ARCHITECTURE.md (Lite design)

[Describe what you want to work on]
```

---

## Project Process Documentation Requirements

### Critical: LLM Session Validation

**When starting ANY session, the LLM MUST validate understanding of project processes in their first response by stating:**

1. **Which process documents exist** (ADR, SOLUTIONS_LOG, etc.)
2. **Their purpose** (what each tracks)
3. **When to update them** (triggers for documentation)

**This validates the LLM has read and understood the project's documentation culture.**

### The Four Process Documents

plasticFlower maintains rigorous process documentation to prevent knowledge loss across sessions:

#### 1. Architecture Decision Records (ADR)

**Location:** `_docs/_dev/ADR/`  
**Purpose:** Document significant architectural decisions with context, rationale, and consequences  
**Format:** Individual numbered markdown files (`0001-short-title.md`) + `INDEX.md`

**When to create:**
- Choosing between 2+ technical approaches (even implementation-level options)
- Deciding NOT to implement something
- Changing a previous decision
- Any choice affecting system structure

**Include fine-grained decisions.** When the LLM presents options (e.g., "Option A vs Option B"), document the choice even if it seems minor. This prevents re-debating and provides context for future LLM sessions.

**Current ADRs:**
- 001: LLM-only clustering (no GDS initially)
- 002: Proofreading merged into Gardener
- 003: Gemini grounding for research
- 004: Full context Q&A (no GraphRAG for single session)
- 005: Lite architecture for POC
- 006: Async event-driven agents over LangGraph
- 007: LIMIT-based transcript retrieval
- 008: Similarity threshold tuned to 0.92
- 009: Redis-only agent scheduling
- 010: Ratio-based agent triggering
- 011: Pre-creation similarity check in Builder
- 012: Centralised Gemini config helper pattern
- 013: Embedding-based type compatibility

See full list: `@_docs/_dev/ADR/INDEX.md`

#### 2. Solutions Log

**Location:** `_docs/_dev/SOLUTIONS_LOG.md`  
**Purpose:** Problem/solution pairs from debugging sessions to prevent re-solving issues  
**Format:** Structured entries with symptom, root cause, solution, affected files, prevention

**When to update:**
- After solving any non-trivial bug
- After discovering a workaround for a known issue
- When finding the root cause of unexpected behaviour

**Before debugging:** Search this file - you may have solved it before.

#### 3. Validated Patterns

**Location:** `_docs/_dev/VALIDATED_PATTERNS.md`  
**Purpose:** Proven code patterns from our codebase AND external GitHub repositories  
**Format:** Code snippets with "Why it works" explanations

**When to update:**
- After implementing a tricky solution that works well
- When copying a useful pattern from an external source
- When establishing a new coding standard

**Before implementing:** Search this file for similar patterns to copy/adapt.

#### 4. Session State (This File)

**Location:** `_docs/_START_SESSION_STATE.md`  
**Purpose:** Cross-session progress tracking and context for LLM handoffs  
**Format:** Structured sections for current state, progress tracker, session log

**When to update:**
- End of EVERY session
- When completing a phase or exercise
- When making key decisions
- When encountering blockers

### LLM Responsibilities

When starting a session, the LLM must:

1. **Read** this file to understand current progress
2. **Validate** understanding by listing the four process documents and their purposes
3. **Ask** if any additional context is needed for the current task
4. **Update** relevant process documents as work progresses
5. **Update** this file at session end

**Example validation in first response:**

```
I've reviewed the project state. I understand we maintain:

- ADR: Architecture decisions (create when choosing between approaches)
- SOLUTIONS_LOG: Bug fixes (update after solving non-trivial issues)
- VALIDATED_PATTERNS: Proven code patterns (update when finding good solutions)
- SESSION_STATE: Progress tracking (update at end of every session)

Current status: Phase A (Neo4j Fundamentals), completed A.1, working on A.2.

Ready to proceed. Do you need additional context for today's work?
```

### Documentation Culture

**Why this matters:**
- LLMs don't persist memory - documents are the only continuity
- Future sessions inherit past decisions without re-debating
- Patterns prevent reinventing solutions
- Session logs show what actually worked vs what was planned

**Keep it lean:**
- Only document decisions/solutions that matter
- Templates make it fast (ADR_TEMPLATE, SOLUTIONS_LOG template)
- Update at natural boundaries (end of session, after solving issue)

---

## LLM-Assisted Development Workflow

### Core Principle: One Phase, One Session

LLMs degrade over long conversations - context gets polluted, responses slow down. Use LEARNING_GUIDE phases as natural session boundaries.

```
Session 1: Phase A (Neo4j Fundamentals)
Session 2: Phase B (Vector Embeddings)
Session 3: Phase C (LLM Clustering)
...
```

**Don't try to do everything in one session.** Fresh session = fresh context = better results.

---

### Session Structure

#### 1. Start (5 min)

Use one of the Quick Start templates above. The LLM reads your progress, knows the architecture, knows what's next.

#### 2. Plan and Execute Together (Same Session)

**Do NOT separate planning and execution into different sessions:**

| Approach | Problem |
|----------|---------|
| Session 1: Plan, Session 2: Execute | Context lost. LLM 2 doesn't understand LLM 1's reasoning. |
| Same session: Plan then Execute | LLM maintains reasoning. Can adapt as it learns. |

**Recommended flow within a session:**

```
1. "Let's plan Phase A. What are the steps?"
2. LLM proposes steps
3. You review, adjust
4. "Ok, let's do step 1"
5. LLM implements
6. You test
7. "Step 1 works. Let's do step 2"
8. ...continue...
9. "Update SESSION_STATE with today's progress"
```

#### 3. Session Length: 2-3 Hours Max

After ~3 hours or ~50 exchanges:
- Context window fills up
- LLM starts "forgetting" earlier context
- Responses get slower

**When to end:** After completing a logical chunk, even if you have energy left.

#### 4. End (5 min)

```
"Update _START_SESSION_STATE.md with today's progress"
```

LLM updates: phase, accomplishments, where you stopped, what's next.

---

### Context Loading Strategy

#### Minimal Context (Default)

Only load what you need for the current task:

| Working on... | Load these files |
|---------------|-----------------|
| Phase A (Neo4j) | `_START_SESSION_STATE.md` + `CYPHER_PATTERNS.md` |
| Phase C (Clustering) | `_START_SESSION_STATE.md` + `VALIDATED_PATTERNS.md` |
| Debugging | `_START_SESSION_STATE.md` + `SOLUTIONS_LOG.md` |
| Architecture question | `_START_SESSION_STATE.md` + `ARCHITECTURE_ADVISORY.md` |

**Don't load everything.** It's expensive and the LLM gets confused with too much context.

#### When to Load More

If the LLM says "I need more context about X", then add it:
```
"Here's the relevant section: @_docs/_dev/REFERENCE_SOURCES.md"
```

---

### ADHD-Friendly Tips

#### 1. Visible Progress = Dopamine

Check boxes in Progress Tracker give completion hits:
```
- [x] A.1: Explore existing graph  <-- DONE!
- [ ] A.2: Query optimisation
```

#### 2. Clear Stopping Points

End sessions at natural boundaries, not mid-task. Easier to resume.

#### 3. If You Get Stuck

Say:
```
"I'm stuck on this. Let's step back. What are we trying to achieve and what are our options?"
```

The LLM will re-orient. You don't have to push through.

#### 4. If You Want to Switch Tasks

**It's fine.** Just capture state first:
```
"Actually, I want to work on something else. Let's pause this and update SESSION_STATE before switching."
```

Don't lose progress - update the file, then switch.

#### 5. Hyperfocus Mode

If you're in flow and want to keep going past a phase boundary:
- That's fine, but consider starting a fresh session
- Copy-paste the current context summary to the new session
- Fresh context = better quality responses

---

### When to Start a Fresh Session

| Situation | Action |
|-----------|--------|
| Completed a phase | New session |
| 3+ hours elapsed | New session |
| LLM seems confused/repetitive | New session |
| Major context switch (e.g., backend to frontend) | New session |
| Everything going well, under 2 hours | Continue |

---

### Recommended First Session

```
I'm starting plasticFlower development.

Context: @_docs/_START_SESSION_STATE.md

I want to begin Phase A (Neo4j Fundamentals), Exercise A.1:
"Explore existing graph in Neo4j Browser"

Let's start by reviewing what's already in the database.
```

Simple, focused, achievable. Just start.

---

### Overview Plan

You already have one: **LEARNING_GUIDE.md** contains 7 phases (A-G) with exercises and deliverables.

**You don't need another plan.** Work through phases sequentially.

Rough timeline (adjust to your pace):
```
Week 1: Phase A + B (foundations)
Week 2: Phase C + D (core agents)
Week 3: Phase E + G (Q&A + research)
```

---

## Current State

### Active Phase
**Phase:** Code Review Fixes & Quality Improvements  
**Started:** 2025-12-31  
**Status:** All code review issues resolved, tests passing

### Last Session
**Date:** 2025-12-31  
**Duration:** ~3 hours  
**Accomplished:** 
- **CRITICAL BUG FIX:** Resolved relationship generation failure
  - Root cause: Premature node ID assignment before similarity checks
  - Solution: Created `UnresolvedRelationship` dataclass storing labels instead of IDs
  - Refactored Builder agent to defer ID resolution to service layer
  - Fixed circular imports in builder.py and gardener.py (lazy imports)
  - Updated all tests to work with new UnresolvedRelationship architecture
- Test results: 24/27 tests passing
  - 6/6 Builder agent & service tests passing
  - 11/11 Similarity tests passing
  - 6/6 Graph DB tests passing
  - 3 LLM tests failing (pre-existing issue documented in SOLUTIONS_LOG)
- Updated documentation:
  - Added SOLUTIONS_LOG entry for failing LLM tests (obsolete `_MODEL` singleton)
  - Fixed verbose relationship descriptions in Builder prompt (1-3 word verb phrases)
**Stopped at:** Relationship generation fully functional, all relevant tests passing  
**Next step:** User testing of relationship creation, then Phase E (Librarian agent)

### Blockers
- None currently

### Open Questions
- None currently

### Technical Debt
- **LLM Test Suite**: 3 tests in `test_llm.py` fail due to obsolete `_MODEL` singleton reference (documented in SOLUTIONS_LOG). LLM service works correctly; tests need updating to reflect model rotation architecture. Priority: Low.

### Resolved Questions
- 243 nodes had NULL labels - these were corrupt nodes created by MERGE. Fixed by changing to MATCH and cleaning database.
- 68-second LLM calls - caused by Gemini 2.5 "thinking mode" enabled by default. Fixed with `thinking_budget=0`.

---

## Progress Tracker

### Phase A: Neo4j Fundamentals
- [x] A.1: Explore existing graph in Neo4j Browser
- [x] A.2: Query optimisation for transcript retrieval
- [x] A.3: Implement `get_extended_transcript()` (satisfied by existing `get_recent_transcript`)
- [x] Deliverable: Extended transcript working (3000 words)

### Phase B: Vector Embeddings
- [x] B.1: Check/create vector index (fixed: was 3072 dims, now 768)
- [x] B.2: Test similarity search (working with corrected index)
- [x] B.3: Tune similarity threshold (0.85 -> 0.92, see ADR-008)
- [x] Deliverable: Optimal threshold documented in ADR-008

### Phase C: LLM Clustering
- [x] C.1: Manual clustering exercise
- [x] C.2: Implement LLM clustering (already implemented - verified working)
- [x] C.3: Test edge cases (4 tests passed)
- [x] Deliverable: Semantic Flower formation working

### Phase D: Proofreading System
- [x] D.1: Create test errors (fixtures already existed)
- [x] D.2: Implement vocabulary (SessionVocabulary CRUD already existed)
- [x] D.3: Pre-proofread pass (apply vocabulary before LLM call)
- [x] D.4: Implement language variant normalization (Session.language_variant, Gardener prompt)
- [x] D.5: Implement `node_corrected` SSE event
- [x] D.6: Implement temporal decay (nodes >5min -> LEGACY status)
- [x] Deliverable: STT correction integrated with language consistency

### Phase D.5: Redis Streams (Event Bus) **COMPLETE**
- [x] D.5.1: Add Redis to docker-compose (already present)
- [x] D.5.2: Implement Redis Streams client in backend (`redis_streams.py`)
- [x] D.5.3: Refactor Builder to publish `chunks.added` events
- [x] D.5.4: Refactor Gardener to consume events via Redis (Redis-only, removed timer)
- [x] D.5.5: Create BuilderService for clean separation of concerns
- [x] D.5.6: Add configurable debounce (ratio-based triggering, 3:1 default)
- [x] D.5.7: Test event-driven agent coordination
- [x] Deliverable: Agents communicate via Redis Streams (enables Researcher/Librarian)

### Phase G: Research Agent (Moved Forward)
- [/] G.1: Audit existing infrastructure + create implementation plan
- [ ] G.2: Implement ReferenceNode model + DB functions
- [ ] G.3: Create Researcher agent with Gemini grounding
- [ ] G.4: Add Gardener trigger + API endpoint
- [ ] G.5: Add SSE event + verification
- [ ] Deliverable: External enrichment working

### Phase E: GraphRAG + Q&A
- [ ] E.1: Build basic retrieval
- [ ] E.2: Implement Q&A endpoint
- [ ] E.3: Test retrieval quality
- [ ] Deliverable: Librarian agent working

### Phase F: GDS Algorithms (Optional)
- [ ] Skipped - Add when 100+ nodes common

---

## Session Log

### Session Template
```
### Session: [DATE]
**Duration:** [X hours]
**Phase:** [X]
**Goal:** [What you aimed to do]
**Accomplished:**
- [Task 1]
- [Task 2]
**Stopped at:** [Specific point]
**Next time:** [What to do next]
**Notes:** [Any observations, blockers, decisions]
```

### Sessions

### Session: 2025-12-31
**Duration:** ~2 hours  
**Phase:** Code Review Fixes & Quality Improvements  
**Goal:** Address all code review issues from architecture review session  
**Accomplished:**
- Fixed 3 WARNING issues: type hints (SchemaType alias), integration tests (5 new), cache bounds (OrderedDict LRU)
- Fixed 3 SUGGESTION issues: UK English audit, SessionContext verification, numpy optimization
- Created comprehensive integration tests in test_builder_service.py for rollback flag enforcement
- Added numpy dependency for 10-100x faster cosine similarity
- All tests passing: 12 in test_similarity.py, 2 in test_builder_service.py
- Verified proper architectural layering (flag enforcement in builder_service, not similarity)
**Stopped at:** All code review issues resolved, ready for next phase  
**Next time:** Begin Phase E (GraphRAG + Q&A - Librarian agent)  
**Notes:** Key learning: Test fuckery detected and corrected by creating proper integration tests at correct architectural layer. Code review process validated quality improvements.

### Session: 2025-12-30
**Duration:** ~1 hour  
**Phase:** Architecture Review + Implementation Planning  
**Goal:** Align understanding with dev team updates, prepare implementation plan  
**Accomplished:**
- Reviewed ARCHITECTURE_ADVISORY.md updates (v8.1 -> v8.2)
- Confirmed critical updates: Gemini thinking mode, MATCH pattern, Literal types
- Identified 4 areas of concern for future development
- Fixed line 586 wording in ARCHITECTURE_ADVISORY.md
- Added Priority 5b (Gemini config helper) to IMMEDIATE_RECOMMENDATIONS.md
- Created ADR-0011: Pre-Creation Similarity Check in Builder
- Updated ADR INDEX with ADR-011
- Created implementation plan: 8 priorities, 4 phases, 7-9 hours total
**Stopped at:** All documentation updated, implementation plan ready  
**Next time:** Execute implementation plan - start with Phase 1 (Quick Wins)  
**Notes:** Key documentation created this session: `_docs/_evidence/architecture_review_2025-12-30.md`, `_docs/_evidence/IMMEDIATE_RECOMMENDATIONS.md`, `_docs/_evidence/vector_index_architecture.md`. Implementation plan in `.cursor/plans/`.

---

### Session: 2025-12-28
**Duration:** ~3 hours  
**Phase:** D.5 - Redis Streams (Event Bus)  
**Goal:** Debug and fix Gardener issues, complete Phase D.5  
**Accomplished:**
- Diagnosed Gemini 2.5 "thinking mode" as cause of 60+ second delays
- Disabled thinking with `thinking_budget=0` in GenerateContentConfig
- Replaced regex patterns with Literal types in Gardener schema
- Fixed MERGE creating corrupt nodes (changed to MATCH for node lookup)
- Fixed Neo4j map projection syntax corrupting returned data
- Deleted 245 corrupt nodes from database
- Added stale event flush on Redis consumer startup
- Added detailed timing logs (DB load: 113ms, Prep: 160ms, LLM: ~10-20s now)
- Verified complete flow: Builder creates nodes -> Gardener confirms/flowers
- Updated SOLUTIONS_LOG with 4 new issues and quick fixes
**Stopped at:** Phase D.5 complete, system working  
**Next time:** Begin Phase E (GraphRAG + Q&A)  
**Notes:** Key learnings: (1) Gemini 2.5 thinking mode adds huge latency, (2) MERGE creates empty nodes if match fails, (3) Literal types work better than regex patterns for structured output.

---

### Session: 2025-12-27 (Session 2)
**Duration:** ~2 hours  
**Phase:** D.5 - Redis Streams (Event Bus)  
**Goal:** Fix timeout issues and implement clean triggering model  
**Accomplished:**
- Diagnosed timeout as API processing time (not token limit)
- Increased timeout from 60s to 90s for Gardener
- Implemented model rotation (3 models) for API quota management
- Added diagnostic logging (prompt size, API call tracking)
- Implemented ratio-based agent triggering (5:1 Builder:Gardener) - ADR-010
- Clarified debounce separation: frontend (1.2s for Cytoscape) vs backend (ratio-based)
- Updated SOLUTIONS_LOG with 3 new issues
- Updated ADR INDEX with ADR-010
**Stopped at:** Ready for final testing  
**Next time:** Test ratio-based triggering, verify de-ghosting and flower formation, then Phase E  
**Notes:** Ratio-based triggering is extensible to future agents (researcher: 10:1, summarizer: 20:1). Frontend debounce unchanged.

---

### Session: 2025-12-27
**Duration:** ~2 hours  
**Phase:** D.5 - Redis Streams (Event Bus)  
**Goal:** Complete Redis-only agent architecture and clean up Builder  
**Accomplished:**
- Debugged API key expiry issues (LLM client singleton caching old key)
- Confirmed Gemini 2.5 models available (list_models.py script)
- Removed timer loop from Gardener - now Redis-only
- Added configurable debounce (`GARDENER_DEBOUNCE_SECONDS` in config)
- Created `BuilderService` for clean separation of concerns
- Simplified `chunks.py` from 295 lines to 100 lines
- Removed redundant `mark_activity()` calls
- Created ADR-009 (Redis-only agent scheduling)
- Updated SOLUTIONS_LOG with API key and dual trigger issues
**Stopped at:** Phase D.5 architecture complete, ready for testing  
**Next time:** Test event-driven coordination, then Phase E (GraphRAG + Q&A)  
**Notes:** Builder is request-driven (different from event-driven Gardener). Future agents (Researcher, Librarian) will follow Gardener's Redis consumer pattern.

---

### Session: 2025-12-26
**Duration:** ~2 hours  
**Phase:** A + B - Neo4j Fundamentals + Vector Embeddings  
**Goal:** Complete Phase A and B  
**Accomplished:**
- A.1: Started Neo4j, explored database (1602 nodes, 102 flowers, 19 sessions, 8910 relationships)
- A.2: Optimised `get_recent_transcript()` with LIMIT clause, changed default to 3000 words
- A.3: Confirmed existing function satisfies requirement (no new function needed)
- B.1: Fixed vector index (was 3072 dims, recreated with 768 dims)
- B.2: Tested similarity search with real embeddings
- B.3: Tuned threshold from 0.85 to 0.92 based on pair-wise analysis
- Created ADR-007 (LIMIT-based retrieval) and ADR-008 (threshold tuning)
- Updated ADR process docs to include fine-grained decisions
- Added LLM session validation requirements to SESSION_STATE
**Stopped at:** Phase B complete  
**Next time:** Begin Phase C - LLM Clustering (C.1: Manual clustering exercise)  
**Notes:** Key insight: abbreviations like "ML" don't embed close to "Machine Learning" (0.823). Gardener handles these edge cases via LLM reasoning.

---

## Key Decisions Made

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-12-26 | LLM-only clustering (no GDS) | 1M context fits entire session |
| 2025-12-26 | Gemini grounding default | Simpler, Tavily as fallback |
| 2025-12-26 | 3000-word extended context | Balance of coverage and cost |
| 2025-12-26 | Proofreading in Gardener | Shared context, fewer agents |
| 2025-12-26 | Session-level language settings | Flexibility for mixed speakers, default UK English, Gardener enforces consistency |
| 2025-12-27 | Redis-only agent scheduling | Single trigger path, simpler debugging, configurable timing (ADR-009) |
| 2025-12-27 | BuilderService separation | Thin API endpoints, testable service layer, consistent with Gardener pattern |
| 2025-12-27 | Ratio-based agent triggering | 5:1 Builder:Gardener ratio, paces API calls, extensible to future agents (ADR-010) |
| 2025-12-27 | Model rotation for quota | 3 models in round-robin, triples effective RPM |
| 2025-12-28 | Disable Gemini thinking mode | `thinking_budget=0` reduces LLM latency from 60s to ~10s |
| 2025-12-28 | Literal types over regex patterns | Better compatibility with Gemini structured output |
| 2025-12-28 | MATCH over MERGE for node lookup | Prevents creating corrupt empty nodes |
| 2025-12-30 | Pre-creation similarity check in Builder | Reduce GHOST nodes, accurate mentions, smoother UI (ADR-011) |
| 2025-12-30 | Gemini config helper function pattern | Centralise `thinking_budget=0` to prevent future 60s+ delays |
| 2025-12-30 | Embedding-based type compatibility | Respects emergent types, no dictionary maintenance, flexible (ADR-013) |

---

## Files Reference

### Core Documentation (Always Available)

| File | Purpose | When to Load |
|------|---------|--------------|
| `_START_SESSION_STATE.md` | This file - progress tracking | **Every session** |
| `ARCHITECTURE_ADVISORY.md` | Full stack system design | Architecture questions |
| `LITE_ARCHITECTURE.md` | Browser-only POC design | Lite version work |
| `LEARNING_GUIDE.md` | Curriculum details | Working on specific phase |

### Development Aids (Load When Coding)

| File | Purpose | When to Load |
|------|---------|--------------|
| `_dev/ADR/INDEX.md` | Architecture decisions log | Making/reviewing decisions |
| `_dev/VALIDATED_PATTERNS.md` | Proven code patterns (internal + **GitHub refs**) | Implementing similar code |
| `_dev/SOLUTIONS_LOG.md` | Problem/solution history | Debugging issues |
| `_dev/CYPHER_PATTERNS.md` | Neo4j Cypher reference | Writing queries |
| `_dev/TEST_FIXTURES.md` | Sample transcripts & test data | Testing features |
| `_dev/REFERENCE_SOURCES.md` | External resources: **GitHub patterns, 7 YouTube transcripts**, papers | Learning new concepts |

### Code Files (Load When Editing)

| File | Purpose | When to Load |
|------|---------|--------------|
| `backend/app/services/graph_db.py` | Neo4j operations | Phase A, D |
| `backend/app/agents/gardener.py` | Gardener agent | Phase C, D |
| `backend/app/services/llm.py` | LLM integration | Phase C, E, G |

### Test Fixtures (JSON files)

| File | Purpose |
|------|---------|
| `_dev/fixtures/ml_lecture.json` | Full integration tests (8 chunks) |
| `_dev/fixtures/transformers_quick.json` | Quick smoke tests (3 chunks) |
| `_dev/fixtures/stt_errors.json` | Proofreading testing |
| `_dev/fixtures/duplicate_detection.json` | Merge/dedup testing |
| `_dev/fixtures/research_testing.json` | Research agent testing |

---

## How to Use Development Resources

### VALIDATED_PATTERNS.md - Copy-Paste Code

**What it is:** Proven code patterns from our codebase AND external GitHub repositories.

**Why it matters:** Saves time - don't reinvent patterns that already work.

**How to use:**
1. Before implementing something, search this file for similar patterns
2. Copy the pattern, adapt variable names
3. The "Why it works" notes explain the reasoning
4. External patterns (from GitHub) include source links if you need more context

**When to update:** After solving a tricky problem, add the pattern here.

---

### REFERENCE_SOURCES.md - External Learning

**What it is:** Curated external resources with trust scores:
- **GitHub repositories** with working code (neo4j-labs, docker, tutorials)
- **YouTube transcripts** from Neo4j tutorials (actual code shown)
- **Research papers** for conceptual understanding
- **Context7 library IDs** for fetching documentation via MCP

**Why it matters:** These are high-trust sources. Random Google results are risky; these are vetted.

**How to use:**
1. Look at the "Quick Reference" table at the top - matches need to resource
2. For implementation: check GitHub repos first (they have runnable code)
3. For learning concepts: YouTube transcripts explain the "why"
4. Tell the LLM: "Fetch documentation for `/neo4j/neo4j-graphrag-python`" to pull live docs

**When to update:** When you find a useful resource, add it with a trust score.

---

### TEST_FIXTURES.md + fixtures/ - Test Data

**What it is:** 
- `TEST_FIXTURES.md` - Documentation explaining the test data and expected outputs
- `fixtures/*.json` - Actual JSON files you can load in tests

**Why it matters:** Consistent test data means reproducible results across sessions.

**How to use:**

```python
# In Python tests
import json
from pathlib import Path

FIXTURES = Path("_docs/_dev/fixtures")
chunks = json.loads((FIXTURES / "ml_lecture.json").read_text())

# Each chunk has: text, start_time, end_time
for chunk in chunks:
    result = await builder_agent.process(chunk)
```

```javascript
// In frontend tests
import mlLecture from '../_docs/_dev/fixtures/ml_lecture.json';
```

**Which fixture for which test:**
| Testing... | Use this fixture |
|------------|------------------|
| Full pipeline | `ml_lecture.json` (8 chunks, ~4 min) |
| Quick smoke test | `transformers_quick.json` (3 chunks) |
| STT proofreading | `stt_errors.json` (has expected corrections) |
| Node deduplication | `duplicate_detection.json` (has merge notes) |
| Research agent | `research_testing.json` (has expected URLs) |

---

### CYPHER_PATTERNS.md - Query Reference

**What it is:** Neo4j Cypher query patterns organised by operation type.

**Why it matters:** Cypher syntax is tricky - this is a quick reference.

**How to use:**
1. Find the operation type (CREATE, MATCH, MERGE, etc.)
2. Copy the pattern
3. Each pattern explains when to use it vs alternatives

---

### SOLUTIONS_LOG.md - Debug History

**What it is:** Problem/solution pairs from past debugging sessions.

**Why it matters:** Same bugs often recur. This prevents re-solving.

**How to use:**
1. Search for keywords related to your issue
2. If you find a match, the solution is documented
3. After solving a new issue, add it here

**When to update:** Every time you fix a non-trivial bug.

---

## Architecture Decision Records (Critical Process)

**When to create an ADR:**
- Choosing between two or more technical approaches
- Deciding NOT to do something
- Changing a previous decision
- Any choice that affects system structure

**How to create:**
1. Say: "Create an ADR for [decision]"
2. LLM generates from template at `_dev/ADR/_TEMPLATE.md`
3. Review and save to `_dev/ADR/NNNN-short-title.md`
4. Update `_dev/ADR/INDEX.md`

**Current ADRs:**
| # | Decision |
|---|----------|
| 001 | LLM-only clustering (no GDS initially) |
| 002 | Proofreading merged into Gardener |
| 003 | Gemini grounding for research |
| 004 | Full context Q&A (no GraphRAG for single session) |
| 005 | Lite architecture for POC |
| 006 | Async event-driven agents over LangGraph |
| 007 | LIMIT-based transcript retrieval |
| 008 | Similarity threshold tuned to 0.92 |
| 009 | Redis-only agent scheduling |
| 010 | Ratio-based agent triggering |
| 011 | Pre-creation similarity check in Builder |
| 012 | Centralised Gemini config helper pattern |
| 013 | Embedding-based type compatibility |

See full list: `@_docs/_dev/ADR/INDEX.md`

---

## Context for New LLM

If starting a fresh conversation, here's the essential context:

### Vision: The Problem We Solve

**Conference content is underutilised.** Thousands of hours of talks go unwatched because linear video is time-consuming and impossible to navigate. plasticFlower transforms spoken content into explorable knowledge maps.

**Inspired by RSA Animate** - where an artist draws concepts as a speaker talks - plasticFlower automatically creates a spatial visual representation showing entities, relationships, and themes as a navigable graph.

### What plasticFlower Does

| Temporal View | User Need | What We Provide |
|---------------|-----------|-----------------|
| **Live** | Engaged attendee, visual aid | Graph forming in real-time |
| **Post-talk** | Missed it, want the gist | Completed graph + Q&A + timestamps |
| **Conference-wide** | Which talks matter? | Cross-session semantic navigation |
| **Deep dive** | I care about topic X | Click nodes to research, jump to moments |

### The Four Agents

- **Builder:** Fast extraction from each chunk, creates GHOST nodes (request-driven)
- **Gardener:** Validates ghosts, checks naming, validates connections, forms Flowers (every 5 chunks via ratio-based triggering)
- **Researcher:** External enrichment via web search (automatic + user-triggered)
- **Librarian:** Q&A about sessions (on-demand)

### Key Concepts

- **Ghost Node:** Tentative entity from Builder, awaiting validation
- **Flower:** Meta-node representing a cluster of nodes with 2+ relationships
- **ReferenceNode:** External research results linked to an entity

### Active Development
Currently in Phase: [see Current State above]
Working on: [see Last Session above]

### Key Design Decisions
- Flowers form from actual relationships (structural), not semantic imposition
- Researcher has two modes: automatic (Gardener-triggered) + on-demand (user click)
- LLM reasoning for small graphs (GDS optional for scale)
- Gemini grounding for web search (Tavily fallback)
- 3000-word extended transcript context for Gardener
- Full transcript stored permanently for re-processing
- Session-level language settings (default: UK English, Gardener enforces consistency)

---

## How to Update This File

At the end of each session, update:

1. **Current State** section - Update phase, status, last session
2. **Progress Tracker** - Check off completed items
3. **Session Log** - Add new session entry
4. **Key Decisions** - Add any new decisions made

Or just say: "Update SESSION_STATE.md with today's progress" and the LLM will do it.


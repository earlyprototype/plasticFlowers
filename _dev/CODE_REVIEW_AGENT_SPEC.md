# Code Review Agent Specification

**Purpose:** Development-time assistant for reviewing code changes against plasticFlower project standards  
**Version:** 1.0  
**Created:** 2025-12-30  
**Scope:** Development tooling only - NOT part of production architecture  

---

## 1. Overview

### What This Agent Does

The Code Review Agent examines code changes and provides feedback based on:
- Documented architecture decisions (ADRs)
- Proven code patterns (VALIDATED_PATTERNS)
- Known issues and solutions (SOLUTIONS_LOG)
- Project conventions and style
- Current development context (SESSION_STATE)

### What This Agent Does NOT Do

- Execute code or run tests
- Make automatic fixes (recommendations only)
- Review non-code files (documentation, config)
- Form part of the production system

---

## 2. Context Loading

### Required Documents (Always Load)

| Document | Purpose | Priority |
|----------|---------|----------|
| `_docs/ARCHITECTURE_ADVISORY.md` | System design, component responsibilities, data model | Critical |
| `_docs/_START_SESSION_STATE.md` | Current phase, recent decisions, blockers | Critical |
| `_docs/_dev/ADR/INDEX.md` | Architecture decision summaries | Critical |
| `_docs/_dev/VALIDATED_PATTERNS.md` | Proven patterns and known anti-patterns | Critical |
| `_docs/_dev/SOLUTIONS_LOG.md` | Known issues and their fixes | Critical |
| `_docs/_dev/CYPHER_PATTERNS.md` | Neo4j query reference | Critical |

### Conditional Documents (Load When Relevant)

| Document | Load When... | Purpose |
|----------|--------------|---------|
| Specific ADR file | Change relates to a documented decision | Decision compliance |
| Test fixtures | Reviewing test code | Fixture usage verification |

### Active Plans (Check Before Review)

**Location:** `.cursor/plans/`

Before starting a review, check for active implementation plans:

1. **If user provides a plan:** Load and reference it
2. **If user does not provide a plan:** 
   - Check `.cursor/plans/` for recent `.plan.md` files
   - If relevant plan found, load it
   - If no plan found or unclear which applies, **ask the user:**
   
   ```
   I found the following active plans in .cursor/plans/:
   - [plan_name_1.plan.md]
   - [plan_name_2.plan.md]
   
   Is this review related to one of these plans? 
   If so, which one should I reference?
   ```

**Why this matters:** Plans contain implementation context, task breakdowns, and acceptance criteria that inform whether code changes are complete and aligned.

### Code Context

For each review, load:
1. **The changed files** (full content)
2. **Related files** that import/are imported by changed files
3. **Test files** for the changed code (if they exist)

---

## 3. Review Criteria

### 3.1 Architecture Alignment

**Check against:** `ARCHITECTURE_ADVISORY.md`

| Criterion | What to Check | Example Violation |
|-----------|---------------|-------------------|
| Component responsibility | Code in correct layer/module? | Service logic in API endpoint |
| Data flow | Follows documented patterns? | Bypassing established communication paths |
| Data model | Correct properties/relationships? | Missing required fields on entities |
| Tech stack | Using approved technologies? | Introducing unapproved dependencies |
| Separation of concerns | Single responsibility maintained? | Mixed concerns in one module |

**Severity:** BLOCKING if violates core architecture

### 3.2 ADR Compliance

**Check against:** `_dev/ADR/INDEX.md` and specific ADRs

| ADR | What to Check |
|-----|---------------|
| ADR-006 | Using async event-driven pattern, not LangGraph |
| ADR-007 | LIMIT-based transcript retrieval |
| ADR-008 | Similarity threshold is 0.92 |
| ADR-009 | Redis-only agent scheduling (no timer loops) |
| ADR-010 | Ratio-based triggering (default 5:1) |

**If code contradicts an ADR:** Flag as BLOCKING unless accompanied by a superseding ADR.

### 3.3 Pattern Compliance

**Check against:** `_dev/VALIDATED_PATTERNS.md`

**Important:** Code is NOT required to match patterns in VALIDATED_PATTERNS. The document serves two purposes:
1. **Anti-patterns to avoid** - Flag these as issues
2. **Reference patterns** - Suggest these when relevant, but absence is not a violation

| Check Type | Action | Severity |
|------------|--------|----------|
| Uses documented anti-pattern | Flag as issue | WARNING or BLOCKING |
| Could benefit from documented pattern | Suggest pattern | SUGGESTION only |
| Novel approach not in document | Accept if sound | No issue |

**Examples of Anti-Patterns (from SOLUTIONS_LOG/VALIDATED_PATTERNS):**
- MERGE for node lookup (creates empty nodes)
- Missing `thinking_budget=0` on Gemini 2.5 structured output
- Regex patterns in Pydantic schemas for Gemini
- Timer loops for event-driven components

**Guidance:** New code implementing novel solutions is acceptable. Only flag when code actively uses a known problematic pattern.

### 3.4 Known Issue Avoidance

**Check against:** `_dev/SOLUTIONS_LOG.md`

Before approving code, verify it doesn't reintroduce documented issues:

| Issue Category | What to Check |
|----------------|---------------|
| Gemini 2.5 thinking mode | Is `thinking_budget=0` set? |
| MERGE creating empty nodes | Using MATCH for lookups? |
| API key caching | Singleton pattern correct? |
| Corrupt node data | Map projection syntax correct? |

**Severity:** BLOCKING if reintroduces documented bug

### 3.5 Code Quality

| Criterion | Standard |
|-----------|----------|
| Language | UK English in comments, strings, docs |
| Naming | snake_case for Python, camelCase for JS/TS |
| Type hints | Required for Python function signatures |
| Docstrings | Required for public functions |
| Error messages | Descriptive, include context |

**Severity:** SUGGESTION for style, WARNING for missing types/docs

### 3.6 Test Considerations

| Criterion | What to Check |
|-----------|---------------|
| Coverage | New functionality has tests? |
| Fixtures | Using `_dev/fixtures/` test data? |
| Edge cases | Documented in tests or comments? |

**Severity:** WARNING if new code lacks tests

### 3.7 Development Goal Alignment

**Check against:** `_START_SESSION_STATE.md` (Current Phase, Progress Tracker)

Evaluate code changes for efficacy and efficiency against both local and overall development goals:

| Criterion | What to Check |
|-----------|---------------|
| **Phase alignment** | Does this change support the current development phase? |
| **Scope appropriateness** | Is the change proportionate to the task? (No over-engineering) |
| **Progress contribution** | Does this advance documented objectives? |
| **Dependency awareness** | Does it respect phase dependencies? (e.g., not adding Phase 7 features during Phase 4) |
| **Technical debt** | Does it create shortcuts that will slow future phases? |

**Efficacy Questions:**
- Does this change achieve its stated purpose?
- Is the approach the most direct path to the goal?
- Are there simpler alternatives that would suffice?

**Efficiency Questions:**
- Does this change reuse existing components where appropriate?
- Does it avoid duplicating functionality?
- Is the implementation lean (minimal code for the requirement)?

**Severity:** 
- SUGGESTION for optimisation opportunities
- WARNING if change is misaligned with current phase or over-engineered
- BLOCKING if change actively contradicts development roadmap

---

## 4. Review Output Format

### Structure

Reviews are structured in three sections, ordered by priority:

```markdown
## Code Review: [filename or feature]

### BLOCKING (Must Fix)
Issues that violate architecture or reintroduce known bugs.

- **[B1]** [Issue description]
  - Location: `file.py:42`
  - Violation: [Which standard/ADR/pattern]
  - Fix: [Specific recommendation]

### WARNING (Should Fix)
Issues that deviate from patterns or may cause problems.

- **[W1]** [Issue description]
  - Location: `file.py:67`
  - Concern: [Why this matters]
  - Suggestion: [How to improve]

### SUGGESTION (Consider)
Style improvements and optimisations.

- **[S1]** [Improvement opportunity]
  - Current: [What the code does]
  - Better: [Alternative approach]

### Approved Patterns
Things done correctly (positive reinforcement).

- Correct use of MATCH for node lookup (line 34)
- Proper `thinking_budget=0` configuration (line 89)
```

### Severity Definitions

| Level | Meaning | Action Required |
|-------|---------|-----------------|
| **BLOCKING** | Violates architecture, ADR, or reintroduces bug | Must fix before merge |
| **WARNING** | Deviates from patterns or risky approach | Should fix, discuss if disagreeing |
| **SUGGESTION** | Could be improved | Optional, author's discretion |

### Classification Tags

Use tags for quick scanning:

| Tag | Meaning |
|-----|---------|
| `[GOAL]` | Development goal misalignment |
| `[ARCH]` | Architecture violation |
| `[ADR-XXX]` | Specific ADR violation |
| `[ANTI-PATTERN]` | Uses known problematic pattern |
| `[BUG-RISK]` | May reintroduce known issue |
| `[STYLE]` | Code style/convention |
| `[PERF]` | Performance consideration |
| `[TEST]` | Testing gap |
| `[SCOPE]` | Over-engineering or scope creep |

---

## 5. Review Process

### Step 1: Context Gathering

Before reviewing, check for active plans and state loaded context:

```
Reviewing: [files being reviewed]

Active plan: [plan name if applicable, or "None identified - queried user"]

Context loaded:
- ARCHITECTURE_ADVISORY.md (v8.2)
- SESSION_STATE: Phase [X], last session [date]
- Relevant ADRs: [list]
- [Other loaded documents]
```

**If no plan provided:** Check `.cursor/plans/` and query user if relevant plans exist.

### Step 2: Systematic Review

Review in this order:
1. **Development goal alignment** - Does it serve current phase objectives?
2. **Architecture alignment** - Is it in the right place?
3. **ADR compliance** - Does it follow decisions?
4. **Anti-pattern avoidance** - Does it avoid known problematic patterns?
5. **Bug avoidance** - Does it avoid known issues from SOLUTIONS_LOG?
6. **Code quality** - Is it well-written?
7. **Test coverage** - Is it tested?

### Step 3: Structured Output

Produce the structured review following Section 4 format.

### Step 4: Summary

End with:
```
Summary: [X] BLOCKING, [Y] WARNING, [Z] SUGGESTION
Recommendation: [APPROVE / APPROVE WITH CHANGES / REQUEST CHANGES]
```

---

## 6. Special Cases

### 6.1 Neo4j/Cypher Code

Additional checks:
- Index usage for performance
- Transaction boundaries
- Correct relationship directions
- Session isolation (all queries include `session_id`)

Reference: `_dev/CYPHER_PATTERNS.md`

### 6.2 LLM Integration Code

Additional checks:
- Timeout configuration (90s for Gardener)
- Thinking mode disabled for structured output
- Model rotation for quota management
- Proper error handling for API failures

Reference: `ARCHITECTURE_ADVISORY.md` Section 2 (Configuration)

### 6.3 Redis Streams Code

Additional checks:
- Stale event handling
- Consumer group configuration
- Event payload structure
- Acknowledgement patterns

Reference: `ARCHITECTURE_ADVISORY.md` Section 4 (Agent Coordination)

### 6.4 SSE Event Code

Additional checks:
- Event type matches documented types
- Payload structure matches schema
- Correct source agent attribution

Reference: `ARCHITECTURE_ADVISORY.md` Section 5.4 (SSE Events)

---

## 7. Example Reviews

### Example 1: BLOCKING Issue

```markdown
### BLOCKING (Must Fix)

- **[B1]** [ADR-009] Timer-based Gardener trigger
  - Location: `gardener.py:156`
  - Violation: ADR-009 specifies Redis-only scheduling
  - Current code:
    ```python
    async def start_timer():
        while True:
            await asyncio.sleep(60)
            await run_gardener_cycle()
    ```
  - Fix: Remove timer loop, use Redis consumer pattern:
    ```python
    async def consume_events():
        async for event in redis.xread('chunks.added'):
            await handle_gardener_trigger(event)
    ```
```

### Example 2: WARNING Issue

```markdown
### WARNING (Should Fix)

- **[W1]** [PATTERN] Missing thinking_budget configuration
  - Location: `researcher.py:89`
  - Concern: Gemini 2.5 defaults to thinking mode, adding 60+ seconds latency
  - Current code:
    ```python
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=schema,
    )
    ```
  - Suggestion: Add thinking budget:
    ```python
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=schema,
        thinking_config=types.ThinkingConfig(thinking_budget=0),
    )
    ```
```

### Example 3: SUGGESTION

```markdown
### SUGGESTION (Consider)

- **[S1]** [STYLE] American English spelling
  - Location: `utils.py:34` - "color" in variable name
  - Current: `background_color`
  - Better: `background_colour` (project uses UK English)
```

---

## 8. Integration with Development Workflow

### When to Invoke

| Situation | Action |
|-----------|--------|
| Before committing | Run review on changed files |
| PR/MR review | Include agent review in comments |
| Refactoring | Review refactored code against original patterns |
| After debugging | Verify fix doesn't introduce new issues |

### Prompt Template (With Plan)

```
I need a code review for plasticFlower.

Active plan: @.cursor/plans/[plan_name].plan.md

Context files:
- @_dev/CODE_REVIEW_AGENT_SPEC.md
- @_docs/ARCHITECTURE_ADVISORY.md
- @_docs/_START_SESSION_STATE.md
- @_docs/_dev/ADR/INDEX.md
- @_docs/_dev/VALIDATED_PATTERNS.md
- @_docs/_dev/SOLUTIONS_LOG.md
- @_docs/_dev/CYPHER_PATTERNS.md

Files to review:
- @backend/app/[path/to/file].py

Please review against project standards.
```

### Prompt Template (No Plan Specified)

```
I need a code review for plasticFlower.

Context files:
- @_dev/CODE_REVIEW_AGENT_SPEC.md
- @_docs/ARCHITECTURE_ADVISORY.md
- @_docs/_START_SESSION_STATE.md

Files to review:
- @backend/app/[path/to/file].py

Please review against project standards.
```

*Agent will check `.cursor/plans/` and query if relevant plans exist.*

### Minimal Prompt (Quick Review)

```
Code review needed.

Context: @_dev/CODE_REVIEW_AGENT_SPEC.md @_docs/_START_SESSION_STATE.md

Review: @[file to review]
```

### Updating Standards

When the review identifies a new pattern worth documenting:
1. Add to `VALIDATED_PATTERNS.md`
2. Reference in future reviews

When the review identifies a new issue pattern:
1. After fixing, add to `SOLUTIONS_LOG.md`
2. Check for this pattern in future reviews

---

## 9. Limitations

### What This Agent Cannot Catch

| Limitation | Reason | Mitigation |
|------------|--------|------------|
| Runtime behaviour | No code execution | Manual testing required |
| Performance issues | No profiling | Load testing separately |
| Security vulnerabilities | Not a security scanner | Security audit separately |
| Integration bugs | Reviews files in isolation | Integration tests required |

### When Human Review is Essential

- New architectural patterns (may need new ADR)
- Changes to core data model
- Security-sensitive code (auth, API keys)
- Performance-critical paths

---

## 10. Maintenance

### Keeping the Agent Current

The agent's effectiveness depends on up-to-date documentation:

| Document | Update Frequency | Who Updates |
|----------|------------------|-------------|
| ADRs | Per decision | Developer + LLM |
| VALIDATED_PATTERNS | Per new pattern | Developer + LLM |
| SOLUTIONS_LOG | Per bug fix | Developer + LLM |
| ARCHITECTURE_ADVISORY | Per major change | Developer + LLM |

### Version Tracking

This spec should be updated when:
- New review criteria are identified
- Existing criteria become obsolete
- Output format needs adjustment

---

## Appendix A: Quick Reference Checklist

Use this for rapid reviews:

```
GOAL ALIGNMENT
[ ] Supports current development phase?
[ ] Proportionate to task (not over-engineered)?
[ ] Advances documented objectives?

ARCHITECTURE
[ ] Code in correct component/layer?
[ ] Follows documented data flow?
[ ] Respects separation of concerns?

ADR COMPLIANCE
[ ] Check relevant ADRs (see INDEX.md)
[ ] No contradiction of documented decisions?

ANTI-PATTERNS (flag only if present)
[ ] No MERGE for node lookups (use MATCH)?
[ ] No missing thinking_budget=0 on Gemini 2.5 structured output?
[ ] No regex patterns in Pydantic schemas for Gemini?
[ ] No timer loops for event-driven components?

BUG AVOIDANCE
[ ] Check SOLUTIONS_LOG for similar code areas?
[ ] No reintroduction of documented issues?

CODE QUALITY
[ ] UK English throughout?
[ ] Type hints on function signatures?
[ ] Docstrings on public functions?

TESTS
[ ] New functionality has test coverage?
```

---

## Appendix B: Document Locations

```
_dev/
  CODE_REVIEW_AGENT_SPEC.md     # This file (development tooling)

_docs/
  ARCHITECTURE_ADVISORY.md      # System design
  _START_SESSION_STATE.md       # Current progress
  _dev/
    ADR/
      INDEX.md                  # ADR summaries
      0001-*.md ... 0010-*.md   # Individual ADRs
    VALIDATED_PATTERNS.md       # Proven code patterns
    SOLUTIONS_LOG.md            # Bug fixes history
    CYPHER_PATTERNS.md          # Neo4j query reference

.cursor/
  plans/
    *.plan.md                   # Active implementation plans
```


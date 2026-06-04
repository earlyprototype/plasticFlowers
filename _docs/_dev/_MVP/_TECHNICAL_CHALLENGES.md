# plasticFlower: Technical Challenges Report

> **Document Purpose:** Risk assessment and mitigation guidance for MVP development
> **Audience:** Development Director / Implementation Team
> **Created:** 2025-12-14
> **Status:** For Review

---

## Executive Summary

This report identifies the primary technical challenges likely to impede plasticFlower MVP development. The analysis is ordered by risk tier, with Tier 1 representing the highest likelihood of causing development delays or functional failures.

**Key Finding:** Gate 4 (Builder Loop) is the critical path. If Builder extraction + visualisation works smoothly, subsequent gates are refinement. If it fails, the core value proposition is compromised.

**Updated Target:** Builder round-trip latency target revised from <3s to **<10s** based on stakeholder input. This provides more headroom but still requires careful optimisation.

---

## Agreed Parameters (Reference)

| Parameter | Value | Notes |
|-----------|-------|-------|
| Builder round-trip target | **<10 seconds** | Speech → node visible |
| Gardener interval | 90 seconds | May need tuning |
| Flower threshold | 3+ nodes, 2+ internal connections | |
| Vector similarity threshold | ≥0.92 | For deduplication (tuned per ADR-008) |
| Session scale target | 30-60 minutes | ~500 nodes maximum |

---

## Tier 1: Critical Risks (High Likelihood, High Impact)

### 1.1 LLM JSON Output Reliability

**What:** The Builder agent must return valid, schema-compliant JSON on every invocation. Malformed responses break the extraction pipeline.

**Why It's Risky:**
- LLMs occasionally hallucinate field names
- Complex nested structures increase failure probability
- A single failure interrupts the live experience
- Silent failures accumulate corrupt data

**Failure Modes:**

```json
// EXPECTED
{
  "nodes": [{"label": "innovation", "confidence": 0.85, "inferred_type": "concept"}],
  "relationships": []
}

// FAILURE MODE 1: Wrong field name
{
  "nodes": [{"name": "innovation", "score": 0.85}]  // "name" not "label"
}

// FAILURE MODE 2: Missing required field
{
  "nodes": [{"label": "innovation"}]  // No confidence
}

// FAILURE MODE 3: Malformed JSON
{
  "nodes": [{"label": "innovation",}]  // Trailing comma
}
```

**Mitigation Strategies:**

| Strategy | Effort | Effectiveness | Recommendation |
|----------|--------|---------------|----------------|
| Gemini structured output mode | Low | High | **Implement** |
| Schema validation before persist | Low | High | **Implement** |
| Retry on parse failure (1x) | Low | Medium | **Implement** |
| Graceful degradation (skip chunk) | Medium | Medium | Implement |
| Failure logging for prompt tuning | Low | High | **Implement** |

**Testing Requirements:**
1. Fuzz test with malformed transcript chunks
2. Test with edge cases: empty chunks, very long chunks, special characters
3. Measure parse failure rate over 100+ chunks
4. Verify retry logic recovers gracefully

**Success Criteria:** <1% parse failure rate after retry logic

---

### 1.2 Builder Latency Chain

**What:** The Builder pipeline involves multiple sequential async operations. Total latency must remain under 10 seconds.

**Latency Budget:**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        10,000ms BUDGET                                  │
├─────────────┬────────────┬─────────────┬──────────────┬────────────────┤
│ Embed       │ Similarity │ LLM Call    │ Neo4j Write  │ SSE Broadcast  │
│ Generation  │ Search     │ (Builder)   │              │                │
│ ~200ms      │ ~100ms     │ ~2000-6000ms│ ~100ms       │ ~50ms          │
├─────────────┴────────────┴─────────────┴──────────────┴────────────────┤
│ TOTAL: ~2450-6450ms (within budget)                                     │
│ BUFFER: ~3550-7550ms                                                    │
└─────────────────────────────────────────────────────────────────────────┘
```

**Risk Factors:**
- Gemini API latency varies (cold starts, load)
- Embedding API adds network round-trip
- Multiple similarity checks compound
- Database connection overhead

**Mitigation Strategies:**

| Strategy | Effort | Effectiveness | Recommendation |
|----------|--------|---------------|----------------|
| Use `thinking_level="low"` | None | High | **Implement** |
| Fire embedding async (non-blocking) | Medium | Medium | Implement |
| Cache embeddings for repeated terms | Medium | Medium | Post-MVP |
| Batch similarity checks | Medium | Medium | Implement if needed |
| Connection pooling (Neo4j) | Low | Medium | **Implement** |
| Timeout with graceful skip | Low | High | **Implement** |

**Testing Requirements:**
1. Measure end-to-end latency for 50+ chunks
2. Test under "rapid speech" conditions (3 chunks in 10s)
3. Identify P50, P90, P99 latencies
4. Test with cold LLM (first call of session)

**Success Criteria:** P90 latency <10s, P99 <15s

---

### 1.3 Pre-Builder Similarity Check Performance

**What:** Before creating a node, the system must check if a semantically similar node exists. This prevents duplicates but adds latency.

**The Dilemma:**
- Skip check → duplicate nodes proliferate
- Slow check → latency budget exceeded
- Inaccurate check → false merges or missed duplicates

**Current Design:**

```
CHUNK ARRIVES
     │
     ▼
┌─────────────────┐
│ Extract terms   │ (LLM)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ For each term:  │
│  1. Generate    │ ← ~200ms per term
│     embedding   │
│  2. Vector      │ ← ~100ms per search
│     search      │
│  3. If match    │
│     ≥0.85:      │
│     UPDATE      │
│     else:       │
│     CREATE      │
└─────────────────┘
```

**Problem:** If a chunk extracts 5 terms, that's 5 × (200ms + 100ms) = 1500ms just for dedup.

**Mitigation Strategies:**

| Strategy | Effort | Effectiveness | Recommendation |
|----------|--------|---------------|----------------|
| Batch embedding calls | Low | High | **Implement** |
| Parallel similarity searches | Low | High | **Implement** |
| Cache recent embeddings | Medium | Medium | Implement |
| Skip check for high-confidence new | Medium | Medium | Consider |
| Relax to Gardener (accept dups) | Low | High | **Fallback option** |

**Decision Point:**

The team should decide between:

**Option A: Strict (current design)**
- Check every term before creation
- Higher latency, better data quality
- Risk: may exceed latency budget

**Option B: Relaxed**
- Builder creates optimistically
- Gardener handles deduplication at 90s intervals
- Lower latency, temporary duplicates visible
- Risk: user sees duplicates briefly

**Recommendation:** Start with Option B for MVP. Accept temporary duplicates; let Gardener clean up. Simpler, faster, and duplicates are visible for <90 seconds.

---

## Tier 2: Significant Risks (Medium Likelihood, Medium-High Impact)

### 2.1 FCose Layout Stability

**What:** As nodes are added in real-time, the graph layout algorithm (FCose) recalculates positions. This can cause existing nodes to jump, disorienting the user.

**User Experience Impact:**

```
GOOD: Node D added, A/B/C stay put    BAD: Everything shifts
     
     A───B                                 B
     │        →   A───B                    │
     C            │                    A───C───D
                  C───D                (user loses context)
```

**Why It Matters:** The "live drawing" experience is core to plasticFlower's value proposition. If the graph feels unstable, the product feels broken.

**Mitigation Strategies:**

| Strategy | Effort | Effectiveness | Recommendation |
|----------|--------|---------------|----------------|
| `fit: false` (no auto-zoom) | None | Medium | **Implement** |
| Pin existing node positions | Medium | High | **Implement** |
| Run full layout only on Gardener | Low | High | **Implement** |
| Animate transitions (300-500ms) | Low | High | **Implement** |
| Incremental layout mode | High | High | Post-MVP |

**Implementation Guidance:**

```javascript
// Recommended FCose configuration for stability
const layoutOptions = {
  name: 'fcose',
  animate: true,
  animationDuration: 400,
  fit: false,                    // Don't auto-zoom
  padding: 50,
  randomize: false,              // Use existing positions as starting point
  nodeRepulsion: 4500,
  idealEdgeLength: 100,
  
  // Only reposition new nodes
  fixedNodeConstraint: existingNodes.map(n => ({
    nodeId: n.id,
    position: { x: n.position.x, y: n.position.y }
  }))
};
```

**Testing Requirements:**
1. Add 10 nodes in rapid succession, observe stability
2. Verify Flower (compound node) formation doesn't cause major shifts
3. User test: can they track a specific node during updates?

**Success Criteria:** Existing nodes move <20px during incremental updates

---

### 2.2 Gardener Context Window Management

**What:** The Gardener receives the full transcript and current graph state. At 30+ minutes, this may exceed Gemini's context window or become prohibitively expensive.

**Scale Analysis:**

| Session Length | Est. Words | Est. Tokens | Context Usage |
|----------------|------------|-------------|---------------|
| 5 minutes | 750 | ~1,000 | Comfortable |
| 15 minutes | 2,250 | ~3,000 | Comfortable |
| 30 minutes | 4,500 | ~6,000 | Approaching limit |
| 60 minutes | 9,000 | ~12,000 | Risk zone |

**Note:** Graph state JSON adds additional tokens. A 200-node graph with relationships could be 5,000+ tokens.

**Mitigation Strategies:**

| Strategy | Effort | Effectiveness | Recommendation |
|----------|--------|---------------|----------------|
| Windowed transcript (recent N minutes) | Low | High | **Implement** |
| Summarise older transcript sections | Medium | High | Post-MVP |
| Compact graph JSON representation | Low | Medium | **Implement** |
| Multiple Gardener passes (partial) | High | High | Post-MVP |
| Use context caching (KV cache) | Medium | High | Implement if available |

**Recommended Approach for MVP:**

```
GARDENER INPUT STRUCTURE
├── Recent transcript (last 10 minutes) — full text
├── Older transcript (>10 minutes) — summarised or omitted
├── Current graph state (compact JSON)
└── Specific instructions
```

**Testing Requirements:**
1. Test Gardener with 30-minute transcript
2. Measure token count at various session lengths
3. Verify quality doesn't degrade with truncated context

---

### 2.3 Builder/Gardener Concurrency

**What:** Both agents write to the same Neo4j graph. Without proper handling, race conditions can cause data corruption or conflicts.

**Conflict Scenarios:**

```
Timeline:
─────────────────────────────────────────────────────────────►
    │                    │                    │
    │   Builder creates  │   Gardener merges  │
    │   node "AI"        │   "AI" + "A.I."    │
    │                    │   into "AI"        │
    │                    │                    │
    └────────────────────┼────────────────────┘
                         │
              POTENTIAL CONFLICT:
              Builder references "A.I." 
              which Gardener just deleted
```

**Mitigation Strategies:**

| Strategy | Effort | Effectiveness | Recommendation |
|----------|--------|---------------|----------------|
| Optimistic locking (version field) | Medium | High | **Implement** |
| Gardener pauses Builder during run | Low | High | **Implement for MVP** |
| Transaction isolation | Medium | High | Implement |
| Conflict resolution logic | High | High | Post-MVP |

**Recommended Approach for MVP:**

Simplest solution: **Gardener blocks Builder**

```
NORMAL OPERATION:
Builder → runs on every chunk
Gardener → sleeps

EVERY 90 SECONDS:
1. Signal Builder to pause after current chunk
2. Wait for Builder to acknowledge pause
3. Gardener runs (typically 5-15 seconds)
4. Signal Builder to resume
```

This avoids all concurrency issues at the cost of brief pauses. Given the 90-second interval and <15-second Gardener runtime, impact is minimal.

---

## Tier 3: Manageable Risks (Lower Likelihood or Impact)

### 3.1 Web Speech API Quirks

**Risks:**
- Browser-specific behaviour (Chrome vs Edge)
- Interim results change retroactively
- Occasional connection drops
- Accuracy varies by accent/environment

**Mitigations:**
- Handle interim→final result transitions gracefully
- Implement reconnection logic
- Test across Chrome and Edge
- Document known limitations

**Assessment:** Well-understood, documented solutions exist. Low risk.

---

### 3.2 SSE Connection Management

**Risks:**
- Connection drops (network, sleep, etc.)
- State desync after reconnection
- Multiple tabs cause issues

**Mitigations:**
- Heartbeat mechanism
- Full state fetch on reconnect
- Single-session enforcement (MVP)

**Assessment:** Standard patterns apply. Low risk.

---

### 3.3 Neo4j Performance

**Risks:**
- Slow vector index at scale
- Connection pool exhaustion
- Query performance degradation

**Mitigations:**
- Proper indexing from start
- Connection pooling
- Monitor query times

**Assessment:** Unlikely to be an issue at MVP scale (500 nodes). Low risk.

---

## Risk Timeline by Development Gate

| Gate | Primary Focus | Primary Risk | Risk Level |
|------|---------------|--------------|------------|
| **Gate 1** | Project setup | None significant | 🟢 Low |
| **Gate 2** | STT integration | Web Speech quirks | 🟢 Low |
| **Gate 3** | Graph infrastructure | Neo4j setup | 🟢 Low |
| **Gate 4** | Builder loop | **LLM reliability + Latency** | 🔴 High |
| **Gate 5** | Gardener loop | Context window + Concurrency | 🟡 Medium |
| **Gate 6** | Session management | Edge cases | 🟢 Low |
| **Gate 7** | MVP polish | Accumulated issues | 🟡 Medium |

---

## Recommended Early Warning Metrics

Implement instrumentation to surface problems early:

| Metric | Collection Point | Healthy | Warning | Critical |
|--------|------------------|---------|---------|----------|
| Builder round-trip (ms) | End-to-end | <5000 | 5000-8000 | >10000 |
| JSON parse failures (%) | After LLM call | <0.5% | 0.5-2% | >2% |
| Similarity check (ms) | Per term | <300 | 300-500 | >500 |
| Gardener cycle (ms) | Full cycle | <10000 | 10000-20000 | >20000 |
| Layout animation | Visual | Smooth | Slight jank | Jumping |
| SSE reconnections/hr | Connection layer | 0-1 | 2-5 | >5 |

---

## Testing Recommendations

### Critical Path Tests (Must Pass for MVP)

1. **Builder JSON Reliability**
   - 100 varied transcript chunks
   - Target: <1% parse failure rate
   
2. **Builder Latency**
   - 50 chunks, measure P50/P90/P99
   - Target: P90 <10s

3. **Rapid Speech Handling**
   - 5 chunks in 15 seconds
   - Verify no dropped chunks, acceptable latency

4. **30-Minute Session**
   - Full session simulation
   - Verify Gardener still functions

5. **Reconnection Recovery**
   - Kill SSE mid-session
   - Verify full state recovery

### Stress Tests (Informative, Not Blocking)

1. **60-minute session** — Find breaking point
2. **500 nodes** — Verify visualisation performance
3. **Concurrent chunks** — Simulated overlapping speech

---

## Questions for Development Director

1. **Similarity Check Approach:** Do you prefer Option A (strict, slower) or Option B (relaxed, Gardener cleans up) for MVP?

2. **Gardener Blocking:** Is the "pause Builder during Gardener" approach acceptable, or do you want true concurrency?

3. **Latency Tolerance:** Is 10s P90 acceptable, or should we target tighter? What's the maximum acceptable?

4. **Layout Priority:** How important is perfect layout stability vs. speed? Would you accept some jank for faster updates?

5. **Context Truncation:** For 30+ minute sessions, is truncating older transcript acceptable? Should we warn the user?

---

## Summary

| Risk | Likelihood | Impact | Gate | Mitigation Confidence |
|------|------------|--------|------|----------------------|
| LLM JSON reliability | Medium | High | 4 | High (structured output) |
| Builder latency | Medium | High | 4 | Medium (dependent on Gemini) |
| Similarity check latency | Medium | Medium | 4 | High (can relax to Gardener) |
| FCose layout jank | Medium | Medium | 4 | High (known solutions) |
| Gardener context | Medium | Medium | 5 | High (windowing) |
| Concurrency | Low-Medium | Medium | 5 | High (blocking approach) |

**Overall Assessment:** Risks are identifiable and have known mitigations. Gate 4 is the critical validation point. If Builder loop works reliably within latency targets, MVP success likelihood is high.

---

## Appendix: Decision Log Updates

The following decisions should be logged if adopted:

| ID | Decision | Rationale |
|----|----------|-----------|
| DEC-0XX | Builder latency target: <10s | Stakeholder input; provides headroom while maintaining "live" feel |
| DEC-0XX | Similarity check: Option B (relaxed) | Prioritise latency; Gardener handles cleanup |
| DEC-0XX | Concurrency: Gardener blocks Builder | Simplest approach; minimal impact at 90s intervals |

---

*End of Technical Challenges Report*








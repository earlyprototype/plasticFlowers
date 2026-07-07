# GraphCanvas Performance Optimization Roadmap

**Date:** 2025-12-21  
**Status:** Planning Phase  
**Related Documents:**
- `CYTOSCAPE_CODE_REVIEW.md` - Original code review
- `CLEANUP_BLAST_RADIUS_ANALYSIS.md` - Risk assessment
- `IMPLEMENTATION_PLAN_SAFE_FIXES.md` - Implementation plan for safe fixes
- `_knownIssues/layout-optimization.md` - Deferred layout optimization details

---

## Overview

Three performance issues identified in code review, categorised by risk/reward:

| Issue | Priority | Risk | Benefit | Status |
|-------|----------|------|---------|--------|
| Temporal O(n²) | LOW | Low | Medium | **PLANNED** |
| Animation cleanup | HIGH | Medium | High | **PLANNED** |
| Layout optimization | MEDIUM | **High** | High | **DEFERRED** |

---

## Phase 1: Safe Optimizations (CURRENT)

**Timeline:** 1-2 days  
**Effort:** 3-5 hours  
**Risk:** LOW-MEDIUM

### 1. Temporal Style Calculation Optimization

**Problem:** O(n²) complexity calculating node timestamps  
**Solution:** Memoize min/max calculation  
**Expected improvement:** 20-30ms at 100 nodes  
**Blast radius:** LOW - purely computational

**Changes:**
- New `createTemporalStyler()` function
- Update 9 callsites to use memoized version
- Keep backwards compatibility

**Testing:** Visual regression + performance measurement

---

### 2. Animation Reference Tracking

**Problem:** Memory leak from untracked `.animation().play()` calls  
**Solution:** Track references, cleanup on unmount  
**Expected improvement:** Eliminates memory leak  
**Blast radius:** MEDIUM - affects 2 animation callsites

**Changes:**
- New `useAnimationTracker()` hook
- Replace 2 animation calls with tracked versions
- Add cleanup logging

**Testing:** Memory profiler + mount/unmount cycles

---

## Phase 2: Deferred Optimizations

### Layout Optimization (DEFERRED)

**Why deferred:**
- High blast radius (5 interconnected systems)
- High risk of breaking graph appearance
- Requires 3-4 day focused sprint
- Need production data to justify effort

**Alternative approaches considered:**
1. **Incremental layout** - Use fCoSe incremental mode for minor updates
2. **Web Worker** - Move layout calculation off main thread (PREFERRED)
3. **Layout throttling** - Debounce more aggressively (quick win)
4. **Algorithm change** - Try cola/euler instead of fCoSe

**See:** `_knownIssues/layout-optimization.md` for full analysis

**Revisit when:**
- Safe optimizations complete
- Users report lag with 50+ node graphs
- Team has 3-4 days for focused work
- Performance monitoring shows layout as bottleneck

---

## Implementation Sequence

```
┌─────────────────────────────────────────────────────────────┐
│ Phase 1: Safe Fixes (1-2 days)                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Day 1: Temporal Optimization                              │
│  ├─ Add memoization function                               │
│  ├─ Update callsites (9 locations)                         │
│  ├─ Visual regression testing                              │
│  └─ Performance measurement                                │
│                                                             │
│  Day 2: Animation Cleanup                                  │
│  ├─ Add tracking hook                                      │
│  ├─ Update animation calls (2 locations)                   │
│  ├─ Memory leak testing                                    │
│  └─ React StrictMode verification                          │
│                                                             │
│  Outcome:                                                   │
│  ✅ Memory leak fixed                                      │
│  ✅ 20-30ms performance improvement at 100 nodes           │
│  ✅ No functional changes                                  │
│  ✅ Ready for production                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ User data shows layout is bottleneck
                              │ Team has 3-4 days available
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 2: Layout Optimization (FUTURE - when justified)     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Option A: Web Worker Layout (RECOMMENDED)                 │
│  ├─ Move fCoSe calculation off main thread                 │
│  ├─ Keep graph appearance identical                        │
│  ├─ UI remains responsive during layout                    │
│  └─ 20-25 hours effort                                     │
│                                                             │
│  Option B: Incremental Layout                              │
│  ├─ Use fCoSe incremental mode for minor updates           │
│  ├─ Graph appearance may differ                            │
│  ├─ Complex integration with organic positioning           │
│  └─ 18-24 hours effort                                     │
│                                                             │
│  Quick Win: Layout Throttling                              │
│  ├─ More aggressive debouncing                             │
│  ├─ Batch rapid updates                                    │
│  ├─ Simple implementation (1-2 hours)                      │
│  └─ Do this first while planning larger change             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Risk Management

### Mitigation Strategies

**For each change:**
1. ✅ Feature flags where applicable
2. ✅ Comprehensive testing plan
3. ✅ Clear rollback procedure
4. ✅ Incremental implementation
5. ✅ Backwards compatibility maintained

**Rollback times:**
- Temporal optimization: < 3 minutes
- Animation cleanup: < 5 minutes
- Layout optimization: Instant (feature flag)

---

## Success Metrics

### Phase 1 (Safe Fixes)

**Must achieve:**
- [ ] No visual regressions
- [ ] Memory stable over 50 mount/unmount cycles
- [ ] >10ms performance improvement at 100 nodes
- [ ] All tests passing
- [ ] No new console warnings

**Nice to have:**
- [ ] >20ms performance improvement
- [ ] Measurable memory reduction in long sessions
- [ ] Code cleaner and more maintainable

### Phase 2 (Layout Optimization - Future)

**Must achieve:**
- [ ] Graph appearance acceptable (may differ slightly)
- [ ] >100ms improvement at 100 nodes
- [ ] No animation jankiness
- [ ] All systems integrated correctly

**Nice to have:**
- [ ] >200ms improvement at 200 nodes
- [ ] Identical appearance to full layout
- [ ] UI remains responsive during layout

---

## Documentation Updates Needed

**After Phase 1 completion:**
- [ ] Update CYTOSCAPE_CODE_REVIEW.md with resolved issues
- [ ] Document new `createTemporalStyler()` function
- [ ] Document animation tracking pattern
- [ ] Add performance benchmark results
- [ ] Update README with performance characteristics

**After Phase 2 (if undertaken):**
- [ ] Document layout strategy selection logic
- [ ] Add architectural decision record (ADR)
- [ ] Update troubleshooting guide
- [ ] Document performance tuning options

---

## Communication Plan

### Stakeholder Updates

**Before starting:**
- Team meeting to review plan
- Confirm timeline and resource allocation
- Identify dependencies

**During implementation:**
- Daily standup updates
- Document any blockers or discoveries
- Share preliminary test results

**After completion:**
- Demo working changes
- Share performance measurements
- Deploy to staging for QA
- Production deployment plan

---

## Dependencies & Blockers

**Phase 1:**
- ✅ No external dependencies
- ✅ No API changes needed
- ✅ No infrastructure changes
- ✅ Can start immediately

**Phase 2 (future):**
- ⚠️ Requires production performance data
- ⚠️ Requires 3-4 day availability
- ⚠️ Requires feature flag infrastructure
- ⚠️ Requires comprehensive test plan

---

## Decision Log

**2025-12-21: Initial Planning**
- ✅ Defer layout optimization (high risk, unproven need)
- ✅ Proceed with temporal optimization (low risk, clear benefit)
- ✅ Proceed with animation cleanup (addresses HIGH priority issue)
- ✅ Document layout issue for future reference

**Next decision point:** After Phase 1 completion
- Review performance improvements
- Analyse production data
- Decide if Phase 2 justified

---

## Quick Reference

### What to do now
1. Read `IMPLEMENTATION_PLAN_SAFE_FIXES.md`
2. Start with temporal optimization (Day 1)
3. Follow with animation cleanup (Day 2)
4. Deploy and monitor

### What NOT to do
- ❌ Don't touch layout optimization yet
- ❌ Don't change graph appearance
- ❌ Don't introduce breaking changes
- ❌ Don't skip testing

### When to revisit layout optimization
- Users report specific lag issues
- Performance data shows layout bottleneck
- Team has dedicated time available
- After gathering production metrics

### Emergency contacts
- Rollback procedures in implementation plan
- Test checklists in implementation plan
- Risk assessment in blast radius analysis
- Detailed issue docs in _knownIssues/

---

## Appendix: Performance Baseline

### Current State (Before Optimization)

**Small graphs (10-25 nodes):**
- Layout time: ~20-45ms
- Temporal calculation: ~5ms
- Total render: ~25-50ms
- **Status:** Acceptable

**Medium graphs (50-100 nodes):**
- Layout time: ~80-200ms
- Temporal calculation: ~20-40ms
- Total render: ~100-240ms
- **Status:** Slight lag noticeable

**Large graphs (200+ nodes):**
- Layout time: ~600ms+
- Temporal calculation: ~80-120ms
- Total render: ~680-720ms
- **Status:** Noticeable freeze

### Expected After Phase 1

**Small graphs (10-25 nodes):**
- Layout time: ~20-45ms (unchanged)
- Temporal calculation: ~2ms (**60% faster**)
- Total render: ~22-47ms
- **Improvement:** Minor

**Medium graphs (50-100 nodes):**
- Layout time: ~80-200ms (unchanged)
- Temporal calculation: ~5ms (**75% faster**)
- Total render: ~85-205ms
- **Improvement:** ~15-35ms faster

**Large graphs (200+ nodes):**
- Layout time: ~600ms+ (unchanged)
- Temporal calculation: ~10ms (**88% faster**)
- Total render: ~610ms
- **Improvement:** ~70-110ms faster

**Note:** Layout time unchanged in Phase 1 (deferred to Phase 2)

---

**Status:** Ready for implementation  
**Next action:** Begin temporal optimization (Day 1)  
**Owner:** Development team  
**Review date:** After Phase 1 completion



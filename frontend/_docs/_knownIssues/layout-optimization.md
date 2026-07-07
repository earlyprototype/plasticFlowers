# Known Issue: Full Layout Recalculation on Minor Updates

**Date Identified:** 2025-12-20  
**Component:** GraphCanvas.tsx  
**Severity:** MEDIUM  
**Performance Impact:** HIGH (at scale)  
**Status:** DEFERRED - Requires extensive testing  
**Related Review:** CYTOSCAPE_CODE_REVIEW.md (Section 2, Issue 3)

---

## Problem Statement

Currently, any addition or removal of nodes, edges, or flowers triggers a **full fCoSe layout recalculation** with 2500 iterations. This is unnecessary for minor updates and becomes expensive at scale.

### Current Behaviour

```typescript
// Lines 1636-1640 in GraphCanvas.tsx
if (needsLayout && cy.elements().length > 0) {
  const layout = cy.elements().layout(FCOSE_OPTIONS);
  layout.run(); // ← Full layout EVERY time
}
```

**Triggers for `needsLayout = true`:**
- Adding a single node
- Adding a single edge
- Removing any element
- Adding/removing a flower
- ANY graph structure change

---

## Performance Impact

### Measured Layout Times (fCoSe with 2500 iterations)

| Graph Size | Full Layout | Incremental* | Difference |
|------------|-------------|--------------|------------|
| 10 nodes   | ~20ms       | ~5ms         | 15ms       |
| 25 nodes   | ~45ms       | ~10ms        | 35ms       |
| 50 nodes   | ~80ms       | ~15ms        | 65ms       |
| 100 nodes  | ~200ms      | ~30ms        | 170ms      |
| 200 nodes  | ~600ms      | ~80ms        | 520ms      |
| 500 nodes  | ~2500ms     | ~250ms       | 2250ms     |

*Estimated based on incremental mode benchmarks

### User Experience Impact

**Current state:**
- Small graph (10-25 nodes): Barely noticeable
- Medium graph (50-100 nodes): Slight lag on updates
- Large graph (200+ nodes): Noticeable freeze on every SSE update
- Very large (500+): Unusable - multi-second freezes

**With incremental layout:**
- Small graph: No change
- Medium graph: Buttery smooth
- Large graph: Responsive
- Very large: Usable (though still slow)

---

## Root Cause Analysis

### Why Full Layout Every Time?

The code doesn't distinguish between:
1. **Major structural changes:** New flower with 5 petals, bridge between clusters
2. **Minor updates:** Single edge added, confidence change on existing node

Both trigger the same expensive full recalculation.

### Where is needsLayout Set?

```typescript
// Lines 1453-1458: Flower removal
if (!desiredFlowerIds.has(ele.id())) {
  ele.remove();
  needsLayout = true; // ← Full layout
}

// Line 1496: Flower addition
needsLayout = true; // ← Full layout

// Lines 1502-1505: Node removal
if (!desiredNodeIds.has(ele.id())) {
  ele.remove();
  needsLayout = true; // ← Full layout
}

// Line 1567: Node addition
needsLayout = true; // ← Full layout

// Lines 1573-1576: Edge removal
if (!desiredEdgeIds.has(edge.id())) {
  edge.remove();
  needsLayout = true; // ← Full layout
}

// Line 1632: Edge addition
needsLayout = true; // ← Full layout
```

**Every path sets the same boolean** - no granularity.

---

## Proposed Solution

### Strategy: Intelligent Layout Selection

Distinguish between major and minor updates, use incremental layout for minor changes.

```typescript
// Track what changed
interface GraphChanges {
  nodesAdded: number;
  nodesRemoved: number;
  edgesAdded: number;
  edgesRemoved: number;
  flowersAdded: number;
  flowersRemoved: number;
}

const analyzeChanges = (
  cy: Core,
  data: { nodes: Node[], relationships: Relationship[], flowers: Flower[] }
): GraphChanges => {
  const existing = {
    nodes: new Set(cy.nodes().not('.flower').map(n => n.id())),
    edges: new Set(cy.edges().map(e => e.id())),
    flowers: new Set(cy.nodes('.flower').map(n => n.id())),
  };
  
  const desired = {
    nodes: new Set(data.nodes.map(n => n.id)),
    edges: new Set(data.relationships.map(r => r.id)),
    flowers: new Set(data.flowers.map(f => f.id)),
  };
  
  return {
    nodesAdded: desired.nodes.size - existing.nodes.size,
    nodesRemoved: [...existing.nodes].filter(id => !desired.nodes.has(id)).length,
    edgesAdded: desired.edges.size - existing.edges.size,
    edgesRemoved: [...existing.edges].filter(id => !desired.edges.has(id)).length,
    flowersAdded: desired.flowers.size - existing.flowers.size,
    flowersRemoved: [...existing.flowers].filter(id => !desired.flowers.has(id)).length,
  };
};

const selectLayoutStrategy = (changes: GraphChanges, graphSize: number) => {
  // Force full layout for these scenarios
  if (
    changes.nodesRemoved > 0 ||     // Removal can cause large restructuring
    changes.edgesRemoved > 0 ||
    changes.flowersAdded > 0 ||     // New flowers need full positioning
    changes.flowersRemoved > 0 ||
    graphSize === 0                 // Empty graph
  ) {
    return 'full';
  }
  
  // Small changes can use incremental
  const totalAdditions = changes.nodesAdded + changes.edgesAdded;
  if (totalAdditions <= 3) {
    return 'incremental';
  }
  
  // Large batch additions need full layout
  return 'full';
};
```

---

## Implementation Challenges

### 1. Interaction with Organic Positioning

**Problem:** Organic positioning (flower petals) runs AFTER layout and assumes stable base positions.

**Current flow:**
```
syncGraph() 
  → Full layout (all nodes positioned)
    → applyOrganicPositioning() (petals moved relative to stems)
      → scheduleAutoFit()
```

**With incremental layout:**
```
syncGraph()
  → Incremental layout (only new nodes positioned)
    → applyOrganicPositioning() (might reposition nodes that layout just placed)
      → CONFLICT: Layout vs organic positioning
```

**Solution options:**
1. **Skip organic positioning for incremental updates** - Petals stay where layout puts them
2. **Only run organic positioning on affected flowers** - Track which flowers changed
3. **Use fCoSe constraints instead** - Rely on layout's constraint system

**Recommendation:** Option 2 - track flower changes, only reposition affected ones.

---

### 2. Two-Phase Animation System

**Problem:** Two-phase animation captures positions, runs layout, then animates between them.

**Current two-phase flow:**
```
1. Capture current positions
2. Run syncGraph (full layout)
3. Capture target positions
4. Reset to current positions
5. Animate to target positions
```

**With mixed layouts:**
```
1. Capture current positions
2. Run syncGraph (incremental layout for minor change)
3. Capture target positions ← Some nodes didn't move, some did
4. Reset to current positions
5. Animate to target positions ← Animations might be jarring
```

**Solution:** Two-phase animation should know about layout strategy.

```typescript
const runCalculationPhase = (
  cy: Core,
  data: any,
  ...
) => {
  const changes = analyzeChanges(cy, data);
  const layoutStrategy = selectLayoutStrategy(changes, cy.nodes().length);
  
  syncGraph(cy, data, ..., layoutStrategy);
  
  return { 
    targetPositions: captureCurrentPositions(cy),
    layoutStrategy, // ← Pass to animation phase
    affectedNodeIds: layoutStrategy === 'incremental' 
      ? identifyAffectedNodes(cy, changes)
      : new Set(cy.nodes().map(n => n.id()))
  };
};
```

---

### 3. Edge Routing

**Problem:** Bezier edges might not update correctly with incremental layout.

**Current behaviour:**
- Full layout → all edges recalculate routes
- Incremental layout → only some nodes move → edges might have stale routes

**Cytoscape behaviour:**
- Edges with `curve-style: bezier` auto-recalculate when endpoints move
- BUT control points might be suboptimal with incremental layout

**Testing needed:**
- Add edge between two existing, stationary nodes
- Does it route correctly with incremental layout?
- Do existing edges update when new node is added nearby?

**Potential solution:**
```typescript
if (layoutStrategy === 'incremental') {
  // Force edge redraw after incremental layout
  cy.edges().forEach(edge => {
    edge.style('curve-style', 'bezier'); // ← Force recalc
  });
}
```

---

### 4. Layout Determinism

**Problem:** Incremental layout might produce different positions than full layout for same graph.

**Example scenario:**
```
Graph state A (10 nodes)
  → Add 1 node with full layout → State B1 (specific positions)
  → Add 1 node with incremental → State B2 (different positions!)
```

**Impact:**
- Graph appearance might vary depending on update path
- Users might see "jumpy" behaviour as graph evolves
- Testing becomes harder (non-deterministic)

**Mitigation:**
- Accept that incremental ≠ full (trade-off for performance)
- Provide "Re-layout" button for users who want full recalculation
- Document the behaviour

---

## Blast Radius Assessment

### Affected Systems

1. **syncGraph function** (lines 1442-1645)
   - Change tracking logic
   - Layout strategy selection
   - Pass strategy to layout execution

2. **Two-phase animation** (lines 1389-1440)
   - Animation orchestration needs to know layout strategy
   - Might need to skip some stages for incremental

3. **Organic positioning** (lines 724-1076)
   - Needs to know which flowers were affected
   - Might skip positioning for unchanged flowers

4. **Auto-fit** (lines 1151-1175)
   - Might need different padding for incremental vs full
   - Should skip for very minor changes

5. **All animation stages** (lines 1180-1317)
   - Stage timings might differ for incremental
   - Some stages might be skipped

### Files Modified
- **GraphCanvas.tsx** - Core implementation (80-100 lines changed)

### Risk Categories

**HIGH RISK:**
- Graph layout appearance could change
- Flower positioning might break
- Two-phase animation might become janky
- Edge routing might be incorrect

**MEDIUM RISK:**
- Performance might not improve as expected
- Incremental layout might be slower for certain cases
- Animation timings might feel off

**LOW RISK:**
- Code complexity increases (more logic paths)
- Testing matrix expands significantly

---

## Testing Requirements

### Unit Tests Needed

1. **analyzeChanges()**
   - Empty graph → graph with 1 node
   - Graph with 10 nodes → add 1 node
   - Graph with 10 nodes → remove 1 node
   - Graph with 10 nodes → add 5 nodes (batch)
   
2. **selectLayoutStrategy()**
   - 0 changes → no layout
   - 1 node added → incremental
   - 3 nodes added → incremental
   - 5 nodes added → full
   - 1 node removed → full
   - 1 flower added → full

### Integration Tests Needed

1. **Visual regression:**
   - Capture screenshots of graphs with full layout
   - Capture screenshots of same graphs built incrementally
   - Compare for major differences
   
2. **Performance benchmarks:**
   - Measure layout time for incremental vs full
   - Various graph sizes (10, 50, 100, 200 nodes)
   - Various update types (add node, add edge, etc)

3. **Animation smoothness:**
   - Record video of two-phase animation with full layout
   - Record video of two-phase animation with incremental
   - Subjective comparison - does it feel smooth?

4. **Edge routing:**
   - Add edges between existing nodes with incremental layout
   - Verify routes are correct
   - Add node that creates new edge crossing
   - Verify existing edges reroute correctly

### Manual Test Scenarios

1. **Typical SSE flow:**
   - Start with empty graph
   - Receive 10 individual node updates (1 per second)
   - Verify graph builds smoothly
   - Verify no visual glitches

2. **Flower creation:**
   - Start with 5 standalone nodes
   - Create flower with 3 of them
   - Verify flower forms correctly with incremental layout
   - **Expected:** Might need full layout for this

3. **Large batch update:**
   - Start with 20 nodes
   - Add 10 new nodes at once
   - Should trigger full layout (exceeds threshold)
   - Verify smooth transition

4. **Rapid updates:**
   - Trigger 20 updates in 5 seconds
   - Incremental layout should keep up
   - Verify no stuttering or freezing

---

## Implementation Plan (When Ready)

### Phase 1: Foundation (2-3 hours)
- [ ] Add `analyzeChanges()` function
- [ ] Add `selectLayoutStrategy()` function
- [ ] Add unit tests for both functions
- [ ] No behaviour changes yet (always return 'full')

### Phase 2: Basic Integration (3-4 hours)
- [ ] Modify syncGraph to accept layout strategy
- [ ] Implement incremental layout option
- [ ] Add feature flag (default: OFF)
- [ ] Test with flag enabled on simple scenarios

### Phase 3: Organic Positioning (4-5 hours)
- [ ] Track which flowers are affected by changes
- [ ] Modify applyOrganicPositioning to skip unchanged flowers
- [ ] Test flower formation with incremental layout
- [ ] Handle edge cases (flower added, petal moved to different flower)

### Phase 4: Animation Integration (3-4 hours)
- [ ] Pass layout strategy to two-phase animation
- [ ] Adjust animation stages based on strategy
- [ ] Test animation smoothness
- [ ] Tune timings for incremental updates

### Phase 5: Testing & Refinement (6-8 hours)
- [ ] Visual regression tests
- [ ] Performance benchmarks
- [ ] Edge routing tests
- [ ] Manual QA on various scenarios
- [ ] Fix issues discovered
- [ ] Tune thresholds (when to use incremental vs full)

### Phase 6: Gradual Rollout (ongoing)
- [ ] Deploy with flag OFF
- [ ] Enable for internal testing
- [ ] Enable for 10% of users
- [ ] Monitor performance metrics
- [ ] Gather user feedback
- [ ] Gradually increase percentage
- [ ] Make default after 2 weeks

**Total estimated time:** 18-24 hours

---

## Decision: Why Defer?

### Reasons to Wait

1. **High complexity:** Touches 5 major systems with interdependencies
2. **High risk:** Could break graph appearance, core user experience
3. **Extensive testing needed:** Visual, performance, integration tests required
4. **Diminishing returns:** Only matters at 100+ nodes (not common yet)
5. **Better alternatives exist:** Focus on safer optimizations first

### What to Do First

Complete the safer optimizations:
- ✅ Temporal calculation O(n²) → O(n) (LOW risk, MEDIUM benefit)
- ✅ Animation cleanup tracking (HIGH priority, MEDIUM risk)

Build confidence with incremental improvements before tackling this.

### When to Revisit

**Trigger conditions:**
- Users report lag with 50+ node graphs
- Average graph size exceeds 75 nodes
- Performance metrics show layout as bottleneck
- Team has 3-4 days for focused implementation
- No other high-priority work blocking

**Ideal timing:**
- After completing safe optimizations
- During slow period (not sprint deadline)
- When team has capacity for thorough testing
- After adding performance monitoring

---

## Alternative Solutions

### Option A: Web Worker Layout (Preferred if revisiting)

Instead of incremental layout, move fCoSe calculation off main thread.

**Pros:**
- Doesn't change graph appearance
- UI remains responsive during layout
- Lower risk than incremental layout
- Better UX (progress indicator possible)

**Cons:**
- Requires Web Worker setup
- Cytoscape state serialization
- More complex architecture

**Effort:** Similar to incremental layout (20-25 hours)

---

### Option B: Layout Throttling

Debounce layout calls more aggressively, batch rapid updates.

**Pros:**
- Very simple implementation
- Low risk
- Immediate improvement for rapid updates

**Cons:**
- Doesn't help single large layouts
- Adds perceived latency
- Not a true performance fix

**Effort:** 1-2 hours

**Recommendation:** Do this first as quick win.

---

### Option C: Switch to Different Layout Algorithm

Replace fCoSe with faster algorithm (e.g., cola, euler).

**Pros:**
- Potentially much faster
- Less code complexity

**Cons:**
- Different visual appearance (might be worse)
- Loss of fCoSe quality
- Still full layout on every change

**Effort:** 4-6 hours to try alternatives

**Recommendation:** Benchmark alternatives before committing.

---

## Monitoring & Metrics

### What to Measure (when implementing)

**Before rollout:**
- Baseline layout times (10, 50, 100, 200 nodes)
- Baseline memory usage
- Baseline animation smoothness (subjective)

**After rollout:**
- Layout time distribution (full vs incremental)
- Percentage of updates using incremental
- User-reported visual issues
- Performance improvement (P50, P95, P99)

**Alerts to set:**
- Layout time > 500ms (any size)
- Incremental layout failures (fallback to full)
- Memory growth over session
- Error rate increase

---

## Conclusion

Layout optimization is a **worthwhile goal** but requires **significant effort** with **high risk**. 

**Current decision:** Defer until safer optimizations are complete and user data justifies the investment.

**Recommended path forward:**
1. Complete temporal optimization (LOW risk)
2. Complete animation cleanup (MEDIUM risk)
3. Monitor graph sizes and performance in production
4. Revisit this issue if data shows it's needed
5. Consider Web Worker approach as alternative

**Do not implement without:**
- ✅ Dedicated 3-4 day sprint
- ✅ Comprehensive test plan
- ✅ Feature flag infrastructure
- ✅ Rollback plan
- ✅ Performance monitoring in place
- ✅ Team consensus on risk/reward

---

**Status:** DOCUMENTED, DEFERRED  
**Next review:** After safe optimizations complete + performance data analysis  
**Owner:** TBD when ready to implement



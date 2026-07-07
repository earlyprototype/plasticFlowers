# Implementation Plan: Safe Performance Fixes
**Date:** 2025-12-21  
**Component:** GraphCanvas.tsx  
**Scope:** Temporal Optimization + Animation Cleanup  
**Risk Level:** LOW-MEDIUM  
**Estimated Time:** 3-5 hours

---

## Executive Summary

This plan addresses two issues from the Cytoscape code review:
- **LOW Priority:** Temporal calculation O(n²) → memoized O(n)
- **HIGH Priority:** Animation cleanup tracking → memory leak prevention

Both changes are low-to-medium risk and can be implemented incrementally with clear rollback paths.

---

## Part 1: Temporal Style Optimization

### Current State

**Problem:** `getTemporalStyle()` recalculates min/max timestamps for EVERY node on EVERY call.

**Location:** Lines 242-263

```typescript
const getTemporalStyle = (node: Node, allNodes: Node[]) => {
  const allTimestamps = allNodes.flatMap((n) => n.timestamps); // ← O(n)
  const newest = Math.max(...allTimestamps);                   // ← O(n)
  const oldest = Math.min(...allTimestamps);                   // ← O(n)
  // ... per-node calculation
};
```

**Called from:** 9 locations
- syncGraph: line 1523 (once per node)
- calculateOrganicPositions: lines 498, 550, 674 (once per petal)
- applyOrganicPositioning: lines 812, 873, 938, 993, 1036 (once per petal)

**Complexity:** O(n²) - for each of n nodes, we iterate all n nodes to find min/max

**Impact at scale:**
- 10 nodes: ~100 operations (negligible)
- 50 nodes: ~2,500 operations (minor)
- 100 nodes: ~10,000 operations (noticeable lag)
- 200 nodes: ~40,000 operations (significant lag)

---

### Solution: Memoized Calculation

**Strategy:** Calculate min/max once per sync, return closure function.

```typescript
/**
 * Create a memoized temporal style calculator
 * Calculates min/max timestamps once, returns function for per-node styling
 */
const createTemporalStyler = (nodes: Node[]) => {
  // Calculate global time range once
  const allTimestamps = nodes.flatMap((n) => n.timestamps);
  
  if (allTimestamps.length === 0) {
    // Early return: all nodes get default styling
    return (_node: Node) => ({ size: 1, opacity: 1 });
  }
  
  const newest = Math.max(...allTimestamps);
  const oldest = Math.min(...allTimestamps);
  const range = newest - oldest || 1;
  
  // Return closure that uses cached values
  return (node: Node) => {
    const nodeTime = node.timestamps.length > 0 
      ? Math.max(...node.timestamps) 
      : oldest;
    
    const recency = 1 - (newest - nodeTime) / range;
    
    return {
      size: 1 + recency * 0.4,   // 1.0x to 1.4x size
      opacity: 0.6 + recency * 0.4, // 0.6 to 1.0 opacity
    };
  };
};

// Keep original function for backwards compatibility (mark deprecated)
/**
 * @deprecated Use createTemporalStyler instead for better performance
 */
const getTemporalStyle = (node: Node, allNodes: Node[]) => {
  return createTemporalStyler(allNodes)(node);
};
```

---

### Implementation Steps

#### Step 1: Add New Function (Non-Breaking)
- Insert `createTemporalStyler` function above `getTemporalStyle`
- Mark `getTemporalStyle` as deprecated
- No existing code changes yet
- **Test:** Existing functionality unchanged

#### Step 2: Update syncGraph
```typescript
// In syncGraph function, before node loop:
const getNodeTemporalStyle = createTemporalStyler(data.nodes);

// Replace line 1523:
// OLD: const temporal = getTemporalStyle(node, data.nodes);
// NEW: const temporal = getNodeTemporalStyle(node);
```
- **Test:** Verify node sizing/opacity unchanged
- **Measure:** Log syncGraph execution time before/after

#### Step 3: Update calculateOrganicPositions
```typescript
// In calculateOrganicPositions function, early in function:
const getNodeTemporalStyle = createTemporalStyler(data.nodes);

// Replace lines 498, 550, 674:
// OLD: const temporal = getTemporalStyle(node, data.nodes);
// NEW: const temporal = getNodeTemporalStyle(node);
```
- **Test:** Verify petal sizing unchanged
- **Test:** Verify flower positioning unchanged

#### Step 4: Update applyOrganicPositioning
```typescript
// In applyOrganicPositioning function, early in function:
const getNodeTemporalStyle = createTemporalStyler(data.nodes);

// Replace lines 812, 873, 938, 993, 1036:
// OLD: const temporal = getTemporalStyle(stemNodeData, data.nodes);
// NEW: const temporal = getNodeTemporalStyle(stemNodeData);
```
- **Test:** Verify organic positioning unchanged
- **Test:** Verify stem/petal sizing unchanged

#### Step 5: Remove Deprecated Function (Optional)
- Once all callsites updated, can remove `getTemporalStyle`
- Or keep it for external use/tests

---

### Testing Checklist

**Visual Regression:**
- [ ] Graph with varying timestamps renders identically
- [ ] Newest node is largest/brightest
- [ ] Oldest node is smallest/most faded
- [ ] Gradient of sizes/opacities is smooth

**Edge Cases:**
- [ ] Empty timestamps array → all nodes size 1.0, opacity 1.0
- [ ] Single node → size 1.4, opacity 1.0 (newest)
- [ ] All same timestamp → all nodes size 1.4, opacity 1.0
- [ ] Mix of timestamped and non-timestamped nodes

**Performance:**
- [ ] 10 nodes: No measurable change
- [ ] 50 nodes: ~5-10ms improvement in syncGraph
- [ ] 100 nodes: ~20-30ms improvement in syncGraph
- [ ] Console log timings: before/after comparison

**Correctness:**
- [ ] Recency calculation matches original
- [ ] Size multiplier correct (1.0 to 1.4)
- [ ] Opacity range correct (0.6 to 1.0)

---

### Rollback Plan

**If issues found:**
1. Revert all callsites to use `getTemporalStyle(node, data.nodes)`
2. Remove `createTemporalStyler` function
3. Remove deprecated tag

**Files to revert:** 1 file (GraphCanvas.tsx)  
**Lines to revert:** ~9 lines  
**Time to rollback:** < 3 minutes

---

## Part 2: Animation Cleanup Tracking

### Current State

**Problem:** `.animation().play()` calls never cleaned up on unmount.

**Location:** 2 instances
- Lines 1560-1566: New node fade-in (5000ms)
- Lines 1622-1631: New edge fade-in (2000ms)

```typescript
// Node fade-in
newNode
  .animation({
    style: { opacity: targetOpacity },
    duration: 5000,
    easing: 'ease-in-out',
  })
  .play(); // ← No reference kept, can't stop on unmount

// Edge fade-in
newEdge
  .animation({
    style: { 'line-dash-offset': 0, 'opacity': 1 },
    duration: 2000,
    easing: 'ease-in-out',
  })
  .play(); // ← No reference kept, can't stop on unmount
```

**Issue:** If component unmounts during animation:
- Animation continues on removed elements (memory leak)
- References prevent garbage collection
- Over time, accumulation causes performance degradation

**Risk level:** HIGH - memory leak in long-running sessions

---

### Solution: Animation Reference Tracking

**Strategy:** Track active `.animation().play()` calls, stop them on unmount.

```typescript
/**
 * Track and play Cytoscape animations with automatic cleanup
 * Only use for .animation().play() - .animate() handles itself
 */
const useAnimationTracker = () => {
  const activeAnimationsRef = useRef<Set<cytoscape.Animation>>(new Set());
  
  const playTrackedAnimation = useCallback(
    (element: cytoscape.SingularElementReturnValue, config: any) => {
      if (!element.nonempty()) {
        console.warn('Attempted to animate non-existent element');
        return null;
      }
      
      const anim = element.animation(config);
      activeAnimationsRef.current.add(anim);
      
      // Auto-cleanup on completion
      anim.play()
        .promise('complete')
        .then(() => {
          activeAnimationsRef.current.delete(anim);
        })
        .catch((err) => {
          // Animation stopped or interrupted
          activeAnimationsRef.current.delete(anim);
          console.debug('Animation stopped:', err);
        });
      
      return anim;
    },
    []
  );
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      console.log(`[Animation Cleanup] Stopping ${activeAnimationsRef.current.size} active animations`);
      activeAnimationsRef.current.forEach(anim => {
        try {
          anim.stop();
        } catch (e) {
          // Ignore errors for already-completed animations
        }
      });
      activeAnimationsRef.current.clear();
    };
  }, []);
  
  return { playTrackedAnimation };
};
```

---

### Implementation Steps

#### Step 1: Add Animation Tracker Hook
- Add `useAnimationTracker` hook to GraphCanvas component
- Place near other hooks (after cyRef, before useEffect)
- No existing code changes yet
- **Test:** Component renders normally

```typescript
export function GraphCanvas({ nodes, relationships, flowers, ... }) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const cyRef = useRef<Core | null>(null);
  const autoFitTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isAnimatingRef = useRef(false);
  
  // NEW: Animation tracking
  const { playTrackedAnimation } = useAnimationTracker();
  
  // ... rest of component
}
```

#### Step 2: Pass Tracker to syncGraph
```typescript
// Update syncGraph signature:
const syncGraph = (
  cy: Core,
  data: { nodes: Node[]; relationships: Relationship[]; flowers: Flower[] },
  autoFitTimeoutRef: React.MutableRefObject<NodeJS.Timeout | null>,
  isAnimatingRef: React.MutableRefObject<boolean>,
  playTrackedAnimation: (element: any, config: any) => any | null, // NEW
): void => {
  // ... function body
};

// Update callsite:
syncGraph(cy, data, autoFitTimeoutRef, isAnimatingRef, playTrackedAnimation);
```

#### Step 3: Replace Node Animation
```typescript
// Replace lines 1560-1566:
// OLD:
newNode
  .animation({
    style: { opacity: targetOpacity },
    duration: 5000,
    easing: 'ease-in-out',
  } as any)
  .play();

// NEW:
playTrackedAnimation(newNode, {
  style: { opacity: targetOpacity },
  duration: 5000,
  easing: 'ease-in-out',
});
```
- **Test:** Node fade-in still works
- **Test:** Rapid add/remove doesn't cause errors

#### Step 4: Replace Edge Animation
```typescript
// Replace lines 1622-1631:
// OLD:
newEdge
  .animation({
    style: { 
      'line-dash-offset': 0,
      'opacity': 1,
    },
    duration: 2000,
    easing: 'ease-in-out',
  } as any)
  .play();

// NEW:
playTrackedAnimation(newEdge, {
  style: { 
    'line-dash-offset': 0,
    'opacity': 1,
  },
  duration: 2000,
  easing: 'ease-in-out',
});
```
- **Test:** Edge fade-in still works
- **Test:** Drawing animation smooth

#### Step 5: Add Logging (Temporary)
```typescript
// In cleanup useEffect, add:
console.log(`[Animation Cleanup] Stopping ${activeAnimationsRef.current.size} active animations`);
```
- **Test:** Mount component, add nodes, unmount
- **Verify:** Console shows cleanup count
- **Verify:** Count matches expectations

---

### Testing Checklist

**Memory Leak Tests:**
- [ ] Create/destroy component 50 times
- [ ] Check Chrome DevTools Memory profiler
- [ ] Verify heap size doesn't grow unbounded
- [ ] Take heap snapshot: check for detached Cytoscape elements

**Animation Continuity:**
- [ ] New node fade-in completes normally (5s)
- [ ] New edge draw completes normally (2s)
- [ ] Multiple nodes added in sequence animate correctly
- [ ] No visual glitches or sudden stops

**Unmount During Animation:**
- [ ] Add node, immediately navigate away
- [ ] No console errors
- [ ] No React warnings
- [ ] Verify cleanup log appears

**Rapid Updates:**
- [ ] Send 10 SSE updates in 2 seconds
- [ ] All nodes appear correctly
- [ ] No animation conflicts
- [ ] Performance remains smooth

**React StrictMode:**
- [ ] Enable StrictMode in layout.tsx
- [ ] Verify double-mount doesn't break animations
- [ ] Verify cleanup happens correctly

---

### Rollback Plan

**If issues found:**
1. Remove `useAnimationTracker` hook
2. Remove `playTrackedAnimation` parameter from syncGraph
3. Restore original `.animation().play()` calls
4. Remove cleanup logging

**Files to revert:** 1 file (GraphCanvas.tsx)  
**Lines to revert:** ~40 lines added, 2 modified  
**Time to rollback:** < 5 minutes

---

## Implementation Schedule

### Day 1: Temporal Optimization (1-2 hours)
- [ ] 09:00 - Add `createTemporalStyler` function
- [ ] 09:15 - Update syncGraph
- [ ] 09:30 - Test visual regression
- [ ] 09:45 - Update calculateOrganicPositions
- [ ] 10:00 - Update applyOrganicPositioning
- [ ] 10:15 - Run full test suite
- [ ] 10:30 - Measure performance improvement
- [ ] 10:45 - Code review and commit

### Day 2: Animation Cleanup (2-3 hours)
- [ ] 09:00 - Add `useAnimationTracker` hook
- [ ] 09:30 - Update syncGraph signature
- [ ] 09:45 - Replace node animation callsite
- [ ] 10:00 - Test node animations
- [ ] 10:15 - Replace edge animation callsite
- [ ] 10:30 - Test edge animations
- [ ] 10:45 - Memory leak testing (50 mount/unmount cycles)
- [ ] 11:15 - React StrictMode testing
- [ ] 11:30 - Code review and commit

### Day 3: Verification (1 hour)
- [ ] 09:00 - Deploy to staging
- [ ] 09:15 - Smoke test all functionality
- [ ] 09:30 - Run automated test suite
- [ ] 09:45 - Monitor for errors/warnings
- [ ] 10:00 - Production deployment decision

---

## Success Criteria

### Temporal Optimization
- ✅ No visual changes to graph rendering
- ✅ Temporal styling calculations correct
- ✅ Performance improvement measurable (>10ms at 100 nodes)
- ✅ All edge cases handled
- ✅ No new console warnings/errors

### Animation Cleanup
- ✅ Animations still smooth and complete
- ✅ No memory leaks (50 cycles, heap stable)
- ✅ Unmount during animation doesn't error
- ✅ Cleanup logging shows correct count
- ✅ React StrictMode compatible

### Overall
- ✅ No regressions in existing functionality
- ✅ Code is cleaner and more maintainable
- ✅ Documentation updated
- ✅ Tests pass
- ✅ Ready for production

---

## Notes

**Why not do layout optimization?**
- High blast radius (affects core layout system)
- Requires extensive testing and feature flagging
- Risk of changing graph appearance completely
- Needs separate planning and phased rollout
- Documented separately in `_knownIssues/layout-optimization.md`

**Why do these fixes first?**
- Low risk with clear benefits
- Addresses HIGH priority memory leak
- Improves performance at scale
- Builds confidence for larger changes
- Can be done independently and incrementally

**Dependencies:**
- No external dependencies
- No API changes
- No breaking changes
- Backwards compatible during transition

**Monitoring after deployment:**
- Watch for console warnings about animations
- Monitor browser memory usage in long sessions
- Check performance metrics (graph render time)
- User reports of visual issues



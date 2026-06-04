---
name: Safe Performance Fixes
overview: "Implement two low-risk performance optimizations in GraphCanvas.tsx: (1) Temporal calculation memoization to eliminate O(n²) complexity, and (2) Animation reference tracking to prevent memory leaks from untracked animations."
todos:
  - id: add-temporal-styler
    content: Add createTemporalStyler function before getTemporalStyle (line ~242)
    status: pending
  - id: update-syncgraph-temporal
    content: Update syncGraph to use memoized temporal styler (line ~1523)
    status: pending
    dependencies:
      - add-temporal-styler
  - id: update-calc-organic-temporal
    content: Update calculateOrganicPositions temporal calls (lines ~498, 550, 674)
    status: pending
    dependencies:
      - add-temporal-styler
  - id: update-apply-organic-temporal
    content: Update applyOrganicPositioning temporal calls (lines ~812, 873, 938, 993, 1036)
    status: pending
    dependencies:
      - add-temporal-styler
  - id: test-temporal-visual
    content: "Test temporal fix: visual regression and correctness"
    status: pending
    dependencies:
      - update-syncgraph-temporal
      - update-calc-organic-temporal
      - update-apply-organic-temporal
  - id: test-temporal-perf
    content: Measure performance improvement from temporal optimization
    status: pending
    dependencies:
      - test-temporal-visual
  - id: add-animation-tracker
    content: Add useAnimationTracker hook before GraphCanvas component (line ~1647)
    status: pending
  - id: use-tracker-in-component
    content: Add playTrackedAnimation to GraphCanvas component hooks (line ~1658)
    status: pending
    dependencies:
      - add-animation-tracker
  - id: update-syncgraph-signature
    content: Update syncGraph signature and callsite to accept playTrackedAnimation
    status: pending
    dependencies:
      - use-tracker-in-component
  - id: replace-node-animation
    content: Replace node fade-in animation with tracked version (lines 1560-1566)
    status: pending
    dependencies:
      - update-syncgraph-signature
  - id: replace-edge-animation
    content: Replace edge fade-in animation with tracked version (lines 1622-1631)
    status: pending
    dependencies:
      - update-syncgraph-signature
  - id: test-animation-visual
    content: "Test animations: verify smooth completion and no visual glitches"
    status: pending
    dependencies:
      - replace-node-animation
      - replace-edge-animation
  - id: test-animation-memory
    content: "Test memory leak: 50 mount/unmount cycles with heap profiling"
    status: pending
    dependencies:
      - test-animation-visual
  - id: test-strictmode
    content: Verify React StrictMode compatibility
    status: pending
    dependencies:
      - test-animation-memory
  - id: final-verification
    content: Run full test suite and verify all success criteria met
    status: pending
    dependencies:
      - test-temporal-perf
      - test-strictmode
---

# Safe Performance Fixes Implementation

## Objective

Fix two performance issues identified in the Cytoscape code review without touching the high-risk layout optimization system.

## Files to Modify

- [`frontend/src/components/graph/GraphCanvas.tsx`](frontend/src/components/graph/GraphCanvas.tsx) - All changes in this file

---

## Part 1: Temporal Style Optimization (O(n²) → O(n))

### Problem

The `getTemporalStyle()` function (lines 242-263) recalculates min/max timestamps for every node on every call. With 100 nodes, this results in ~10,000 unnecessary operations.

### Solution

Create a memoized version that calculates min/max once and returns a closure function.

### Implementation

**Add new memoized function** (insert before line 242):

```typescript
const createTemporalStyler = (nodes: Node[]) => {
  const allTimestamps = nodes.flatMap((n) => n.timestamps);
  if (allTimestamps.length === 0) {
    return (_node: Node) => ({ size: 1, opacity: 1 });
  }
  
  const newest = Math.max(...allTimestamps);
  const oldest = Math.min(...allTimestamps);
  const range = newest - oldest || 1;
  
  return (node: Node) => {
    const nodeTime = node.timestamps.length > 0 
      ? Math.max(...node.timestamps) 
      : oldest;
    const recency = 1 - (newest - nodeTime) / range;
    return {
      size: 1 + recency * 0.4,
      opacity: 0.6 + recency * 0.4,
    };
  };
};
```

**Update callsites** (9 locations):

- Line ~1523 in `syncGraph`: Create styler once before node loop, use it for each node
- Lines ~498, 550, 674 in `calculateOrganicPositions`: Create styler once, use for all petals
- Lines ~812, 873, 938, 993, 1036 in `applyOrganicPositioning`: Create styler once, use for all nodes

**Pattern for each function**:

```typescript
// Add at start of function
const getNodeTemporalStyle = createTemporalStyler(data.nodes);

// Replace each call:
// OLD: const temporal = getTemporalStyle(node, data.nodes);
// NEW: const temporal = getNodeTemporalStyle(node);
```

---

## Part 2: Animation Cleanup Tracking

### Problem

Lines 1560-1566 (node fade) and 1622-1631 (edge fade) use `.animation().play()` without keeping references. If component unmounts during animation, references leak.

### Solution

Track animation references in a ref and stop them on unmount.

### Implementation

**Add animation tracker hook** (insert before GraphCanvas component, around line 1647):

```typescript
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
      
      anim.play()
        .promise('complete')
        .then(() => activeAnimationsRef.current.delete(anim))
        .catch(() => activeAnimationsRef.current.delete(anim));
      
      return anim;
    },
    []
  );
  
  useEffect(() => {
    return () => {
      console.log(`[Animation Cleanup] Stopping ${activeAnimationsRef.current.size} active animations`);
      activeAnimationsRef.current.forEach(anim => {
        try { anim.stop(); } catch (e) {}
      });
      activeAnimationsRef.current.clear();
    };
  }, []);
  
  return { playTrackedAnimation };
};
```

**Use tracker in GraphCanvas** (around line 1658):

```typescript
// Add after other useRef hooks
const { playTrackedAnimation } = useAnimationTracker();
```

**Update syncGraph signature** (line 1442):

```typescript
const syncGraph = (
  cy: Core,
  data: { nodes: Node[]; relationships: Relationship[]; flowers: Flower[] },
  autoFitTimeoutRef: React.MutableRefObject<NodeJS.Timeout | null>,
  isAnimatingRef: React.MutableRefObject<boolean>,
  playTrackedAnimation: (element: any, config: any) => any | null, // ADD THIS
): void => {
```

**Update syncGraph callsite** (around line 1864):

```typescript
syncGraph(cy, { nodes, relationships, flowers }, autoFitTimeoutRef, isAnimatingRef, playTrackedAnimation);
```

**Replace node animation** (lines 1560-1566):

```typescript
// OLD:
newNode.animation({
  style: { opacity: targetOpacity },
  duration: 5000,
  easing: 'ease-in-out',
} as any).play();

// NEW:
playTrackedAnimation(newNode, {
  style: { opacity: targetOpacity },
  duration: 5000,
  easing: 'ease-in-out',
});
```

**Replace edge animation** (lines 1622-1631):

```typescript
// OLD:
newEdge.animation({
  style: { 'line-dash-offset': 0, 'opacity': 1 },
  duration: 2000,
  easing: 'ease-in-out',
} as any).play();

// NEW:
playTrackedAnimation(newEdge, {
  style: { 'line-dash-offset': 0, 'opacity': 1 },
  duration: 2000,
  easing: 'ease-in-out',
});
```

---

## Testing Strategy

### Visual Regression

- Graph with varying timestamps renders identically
- Node sizes/opacities display correct temporal gradient
- Animations remain smooth and complete

### Performance

- Measure syncGraph execution time before/after temporal fix
- Expected: 20-30ms improvement at 100 nodes

### Memory Leak

- Mount/unmount component 50 times
- Verify heap size stable in Chrome DevTools Memory profiler
- Confirm cleanup log shows correct animation count

### Edge Cases

- Empty graph
- Single node
- Rapid SSE updates (10 in 2 seconds)
- Unmount during active animation
- React StrictMode enabled

---

## Rollback Plan

Both changes are in a single file with clear rollback paths:**Temporal fix**: Revert 9 callsites to use `getTemporalStyle(node, data.nodes)`, remove new function (< 3 min)**Animation fix**: Remove hook, revert syncGraph signature, restore `.animation().play()` calls (< 5 min)---

## Success Criteria

- No visual changes to graph rendering
- 10-30ms performance improvement at 100+ nodes
- No memory leaks (stable heap after 50 cycles)
- All animations complete smoothly
- No console errors or warnings
- Tests pass

---

## Notes

- Layout optimization deliberately excluded (high risk, requires feature flagging)
- Both fixes are backwards compatible during transition
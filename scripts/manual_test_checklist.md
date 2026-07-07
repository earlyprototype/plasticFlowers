# Graph Density Improvements - Manual Testing Checklist

**Date:** 19 December 2025  
**Tester:** _________________  
**Test Session:** _________________

---

## Prerequisites

- [ ] Backend running on port 8010
- [ ] Frontend running on port 3000
- [ ] Browser DevTools open (F12)
- [ ] Console tab visible
- [ ] Have this checklist ready

---

## Test Session 1: Small Graph (5 nodes)

**Objective:** Verify spacing improvements don't make small graphs too sparse

### Setup
1. Open http://localhost:3000
2. Create new session
3. Start speaking (30-60 seconds)
4. Stop when ~5 nodes appear

### Verification

**Visual:**
- [ ] Nodes have clear spacing (not bunched up)
- [ ] Graph doesn't look too sparse or disconnected
- [ ] No excessive white space
- [ ] Can see all nodes without zooming

**Console:**
- [ ] No "invalid endpoints" errors
- [ ] No JavaScript errors

**Screenshot:** (Take screenshot and save as `test1-small-graph.png`)

**Notes:**
```
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________
```

---

## Test Session 2: Medium Graph with Flower Formation (20 nodes)

**Objective:** Verify edge hiding prevents console errors during flower formation

### Setup
1. Continue from Test Session 1
2. Keep speaking to reach ~20 nodes
3. Wait for Gardener cycle (watch for "Gardener cycle starting" in backend logs)
4. **Watch console carefully during flower formation**

### Verification

**Console (CRITICAL):**
- [ ] **ZERO "invalid endpoints" errors appear**
- [ ] See message: `[Organic Positioning] Hiding X edges during animation`
- [ ] See message: `[Organic Positioning] Restored X edges`
- [ ] No JavaScript errors

**Visual (Edge Animation):**
- [ ] Edges fade out smoothly before nodes move into flowers
- [ ] Edges fade back in smoothly after nodes settle
- [ ] Transition feels smooth and intentional (not jarring)
- [ ] Can see the fade effect (300ms out, 600ms in)

**Layout:**
- [ ] Individual nodes clearly separated
- [ ] Flowers clearly separated from each other
- [ ] Edges distinguishable (not hairball)
- [ ] Hub nodes present but not pulling everything to center

**Performance:**
- [ ] Animations feel smooth (no stuttering)
- [ ] No lag during Gardener cycle

**Screenshot:** (Take screenshot mid-animation and after completion)
- Save as `test2-medium-before.png` (during fade)
- Save as `test2-medium-after.png` (after complete)

**Console Output:** (Copy/paste relevant messages)
```
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________
```

**Notes:**
```
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________
```

---

## Test Session 3: Large Graph Density (50+ nodes)

**Objective:** Compare to original crowded screenshot, verify readability at scale

### Setup
1. Continue speaking or import more data to reach 50+ nodes
2. Allow multiple Gardener cycles (5-10 minutes)
3. Take screenshot of full graph

### Verification

**Layout (Compare to original crowded screenshot):**
- [ ] Graph occupies 2-3x more canvas area
- [ ] NO massive center clustering (star-burst pattern)
- [ ] Hub nodes visible but NOT pulling everything to center
- [ ] Can distinguish individual nodes and edges
- [ ] Flowers well-separated

**Console:**
- [ ] Still zero "invalid endpoints" errors after multiple cycles
- [ ] Edge hiding/restoration messages appear for each cycle
- [ ] No accumulating errors

**Navigation:**
- [ ] Auto-fit works correctly
- [ ] Can zoom in/out smoothly
- [ ] Can pan to explore different areas
- [ ] Graph remains readable at default zoom

**Screenshot:** (Take full graph screenshot)
- Save as `test3-large-graph.png`
- Compare side-by-side with original crowded screenshot

**Notes on comparison:**
```
BEFORE (original screenshot):
_________________________________________________________________

AFTER (new spacing):
_________________________________________________________________

Improvement level (1-10): _____
```

---

## Test Session 4: Performance Verification

**Objective:** Ensure changes don't impact performance

### Setup
1. Open Browser DevTools → Performance tab
2. Click "Record" button
3. Wait for a Gardener cycle with flower formation
4. Stop recording after cycle completes

### Verification

**FPS (Frames Per Second):**
- [ ] Maintains 30+ FPS during animations
- [ ] No significant FPS drops
- [ ] Smooth visual experience

**JavaScript Performance:**
- [ ] No long tasks (yellow/red blocks > 50ms)
- [ ] Memory usage stable (check Memory tab)
- [ ] No memory leaks after multiple cycles

**DevTools Screenshots:**
- Save Performance recording: `test4-performance.json` (export)
- Screenshot of FPS graph: `test4-fps.png`

**Performance Metrics:**
- Average FPS during animation: _____ fps
- Lowest FPS observed: _____ fps
- Memory at start: _____ MB
- Memory after 10 minutes: _____ MB
- Memory leak detected: YES / NO

**Notes:**
```
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________
```

---

## Test Session 5: Edge Cases

**Objective:** Test unusual scenarios

### Edge Case 1: Very Dense Hub Node
- [ ] Create scenario with one node having 15+ connections
- [ ] Verify it doesn't pull everything to center
- [ ] Edges still hide/restore correctly

### Edge Case 2: Multiple Simultaneous Flowers
- [ ] Create scenario where Gardener forms 3+ flowers at once
- [ ] Verify all edge animations work correctly
- [ ] No console errors

### Edge Case 3: Rapid Node Addition
- [ ] Speak continuously for 2-3 minutes without pause
- [ ] Verify graph remains stable
- [ ] Layout updates smoothly

**Notes:**
```
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________
```

---

## Overall Assessment

### Critical Success Criteria
- [ ] **Zero "invalid endpoints" console errors** (MUST PASS)
- [ ] **Edges fade during flower formation** (MUST PASS)
- [ ] **Graph 2-3x more spacious than original screenshot** (MUST PASS)
- [ ] **30+ FPS maintained** (MUST PASS)

### Nice-to-Have
- [ ] Edge fade timing feels natural
- [ ] Small graphs still look cohesive
- [ ] Hub nodes well-handled
- [ ] Auto-fit works perfectly

### Overall Rating
Graph density improvements are:
- [ ] Excellent - Deploy immediately
- [ ] Good - Minor tweaks needed
- [ ] Acceptable - Some issues but usable
- [ ] Poor - Needs rework

### Issues Found
```
Priority | Issue Description                        | Severity
---------|------------------------------------------|----------
         |                                          |
         |                                          |
         |                                          |
```

### Recommendations
```
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________
```

---

## Sign-off

**Tester Name:** _________________  
**Date Completed:** _________________  
**Total Test Duration:** _________________  

**Ready for Production:** YES / NO

**Architect Review Needed:** YES / NO

**Notes for Developer:**
```
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________
```


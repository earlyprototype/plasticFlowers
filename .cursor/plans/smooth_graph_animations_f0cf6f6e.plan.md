---
name: Smooth Graph Animations
overview: "Fix remaining animation issues in GraphCanvas: eliminate snappy repositioning by converting instant position changes to smooth animations, consolidate multiple auto-fit triggers to prevent repetitive camera movements, and improve flower collapse/expand UX with clearer visual affordances."
todos:
  - id: smooth-position-jitter
    content: Convert applyOrganicJitter to use .animate() instead of instant .position() for smooth initial placement (800ms duration)
    status: completed
  - id: smooth-position-petals
    content: Update petal positioning in applyOrganicPositioning to animate position and style together (1200ms duration)
    status: completed
  - id: smooth-position-hubs
    content: Update implicit hub connection positioning to animate position and style together (1200ms duration)
    status: completed
  - id: create-autofit-helper
    content: Create scheduleAutoFit helper function to consolidate and debounce auto-fit logic
    status: completed
  - id: replace-autofit-triggers
    content: Replace all three auto-fit blocks with single scheduleAutoFit calls (1500ms delay)
    status: completed
  - id: enhance-flower-styles
    content: Add cursor pointer, hover state, and collapsed state styles to flower nodes in CYTOSCAPE_STYLE
    status: completed
  - id: add-flower-icons
    content: Add collapse/expand icons (▶/▼) to flower labels to indicate interactivity and state
    status: completed
  - id: improve-flower-click
    content: Enhance flower click handler with smooth fade animations and label updates
    status: completed
  - id: test-smooth-animations
    content: Test with rapid node additions to verify smooth positioning and single camera movement
    status: in_progress
  - id: verify-performance
    content: Profile with Chrome DevTools to ensure 60fps during animations and no overlapping transitions
    status: pending
---

# Smooth Graph Animation System

## Overview

Based on Cytoscape.js best practices research (documented in [`frontend/cytoscape.md`](frontend/cytoscape.md)), we've identified three core animation issues causing the "snappy" behavior and repetitive transitions. This plan systematically fixes each issue using proper Cytoscape.js APIs.---

## Root Causes Identified

### 1. Position Animation Conflict

**Problem:** Using instant `.position()` changes while animating styles separately creates jarring, snappy movements.**Locations in [`frontend/src/components/graph/GraphCanvas.tsx`](frontend/src/components/graph/GraphCanvas.tsx):**

- Line 294: `applyOrganicJitter` function
- Line 485: Petal positioning in `applyOrganicPositioning`
- Line 640: Connected node positioning for implicit hubs

**Cytoscape.js Best Practice:** Position changes should use `.animate({ position: {...} }, { duration })` for smooth transitions, not instant `.position()` calls.

### 2. Multiple Auto-Fit Triggers

**Problem:** Three separate auto-fit timeout chains fire independently, causing repetitive camera movements (up to 5x as user reported).**Locations:**

- Lines 896-905: After layout completes
- Lines 923-933: When organic positioning updates without layout
- Lines 945-966: Safety net check after updates settle

**Issue:** These overlap and cascade, triggering multiple concurrent camera animations.

### 3. Unclear Flower Interaction

**Problem:** Clicking anywhere on flower background collapses/expands it unexpectedly (line 708).**UX Issue:** No visual indicator that flowers are interactive or what clicking will do.---

## Implementation Strategy

### Phase 1: Smooth Position Animations

**File:** [`frontend/src/components/graph/GraphCanvas.tsx`](frontend/src/components/graph/GraphCanvas.tsx)

#### 1.1 Update `applyOrganicJitter` (Line ~273)

```javascript
// BEFORE (instant):
node.position(jitteredPos);

// AFTER (smooth):
node.animate({
  position: jitteredPos,
}, {
  duration: 800,
  easing: 'ease-out',
});
```

**Rationale:** Jitter should be subtle and smooth, not instant. Use shorter duration (800ms) since this is initial placement.

#### 1.2 Update Petal Positioning (Line ~485)

```javascript
// BEFORE (instant position + separate style animation):
cy.batch(() => {
  cyPetal.position(targetPos);
  cyPetal.animate({ style: {...} }, { duration: 1500 });
});

// AFTER (combined position + style animation):
cyPetal.animate({
  position: targetPos,
  style: {
    width: `${petalSize * temporal.size * 100}%`,
    height: `${petalSize * temporal.size * 100}%`,
  },
}, {
  duration: 1200,
  easing: 'ease-in-out',
});
```

**Rationale:** Animate position and style together for coordinated, smooth movement. Use 1200ms for flower petal choreography.

#### 1.3 Update Implicit Hub Connections (Line ~640)

```javascript
// BEFORE (instant position + separate style animation):
cy.batch(() => {
  cyNode.position(targetPos);
  cyNode.animate({ style: {...} }, { duration: 1500 });
});

// AFTER (combined animation):
cyNode.animate({
  position: targetPos,
  style: {
    width: `${connectedSize * connectedTemporal.size * 100}%`,
    height: `${connectedSize * connectedTemporal.size * 100}%`,
  },
}, {
  duration: 1200,
  easing: 'ease-in-out',
});
```

**Note:** Remove `cy.batch()` wrapper since we're using single `.animate()` call now.---

### Phase 2: Consolidate Auto-Fit System

**File:** [`frontend/src/components/graph/GraphCanvas.tsx`](frontend/src/components/graph/GraphCanvas.tsx)

#### 2.1 Create Single Auto-Fit Helper Function (Add after `applyOrganicPositioning`)

```javascript
/**
    * Debounced auto-fit to ensure all elements stay visible
    * Prevents multiple concurrent camera animations
 */
const scheduleAutoFit = (
  cy: Core,
  autoFitTimeoutRef: React.MutableRefObject<NodeJS.Timeout | null>,
  isAnimatingRef: React.MutableRefObject<boolean>,
  delay: number = 300,
) => {
  if (autoFitTimeoutRef.current) {
    clearTimeout(autoFitTimeoutRef.current);
  }
  
  autoFitTimeoutRef.current = setTimeout(() => {
    if (!isAnimatingRef.current && cy.elements().length > 0) {
      isAnimatingRef.current = true;
      
      cy.animate({
        fit: { eles: cy.elements(), padding: 50 },
        duration: 2500,
        easing: 'ease-in-out',
        complete: () => {
          isAnimatingRef.current = false;
        },
      });
    }
  }, delay);
};
```



#### 2.2 Replace All Three Auto-Fit Blocks

**Location 1 (Lines 893-907):** After layout completes

```javascript
// AFTER layout + organic positioning
scheduleAutoFit(cy, autoFitTimeoutRef, isAnimatingRef, 1500);
```

**Location 2 (Lines 920-935):** After organic positioning without layout

```javascript
// AFTER organic positioning update
scheduleAutoFit(cy, autoFitTimeoutRef, isAnimatingRef, 1500);
```

**Location 3 (Lines 942-966):** Remove entirely - no longer needed with consolidated system.**Rationale:** Single debounced function prevents cascade. Longer delay (1500ms) allows position animations to complete first.---

### Phase 3: Enhance Flower Interaction UX

**File:** [`frontend/src/components/graph/GraphCanvas.tsx`](frontend/src/components/graph/GraphCanvas.tsx)

#### 3.1 Update Flower Stylesheet (Add to `CYTOSCAPE_STYLE`)

```javascript
{
  selector: 'node.flower',
  style: {
    // ... existing styles ...
    'cursor': 'pointer', // Visual affordance
  },
},
{
  selector: 'node.flower:hover',
  style: {
    'border-width': 3,
    'border-color': '#4a90e2',
  },
},
{
  selector: 'node.flower.collapsed',
  style: {
    'border-style': 'dashed',
    'border-width': 2,
  },
},
```



#### 3.2 Improve Flower Label (Lines ~682)

```javascript
// Add collapse state indicator to label
const memberCount = data.nodes.filter((n) => n.flower_id === flower.id).length;
const isCollapsed = existing?.data('collapsed') ?? false;
const collapseIcon = isCollapsed ? '▶' : '▼';
const labelWithCount = `${collapseIcon} ${flower.label} (${memberCount})`;
```



#### 3.3 Refine Click Handler (Line ~708)

```javascript
// Add click handler with visual feedback
newFlower.on('tap', (evt) => {
  const node = evt.target;
  const isCollapsed = node.data('collapsed');
  const newState = !isCollapsed;
  node.data('collapsed', newState);
  
  // Update label with new state
  const flower = flowerMap.get(node.id());
  if (flower) {
    const memberCount = data.nodes.filter((n) => n.flower_id === flower.id).length;
    const icon = newState ? '▶' : '▼';
    node.data('label', `${icon} ${flower.label} (${memberCount})`);
  }
  
  // Toggle visibility of child nodes
  const children = node.children();
  if (newState) {
    // Collapse: hide children with fade-out
    children.animate({
      style: { opacity: 0 },
    }, {
      duration: 600,
      complete: () => {
        children.style('display', 'none');
      },
    });
    node.animate({
      style: { 'border-width': 2, 'border-style': 'dashed' },
    }, {
      duration: 600,
      easing: 'ease-in-out',
    });
  } else {
    // Expand: show children with fade-in
    children.style('display', 'element');
    children.style('opacity', 0);
    children.animate({
      style: { opacity: 1 },
    }, {
      duration: 800,
    });
    node.animate({
      style: { 'border-width': 1, 'border-style': 'solid' },
    }, {
      duration: 800,
      easing: 'ease-in-out',
    });
  }
});
```

**Rationale:** Visual icon (▶/▼) clearly indicates state and interactivity. Hover state shows clickability. Smooth fade animations prevent jarring visibility changes.---

## Testing Strategy

### Visual Verification

1. **Smooth Positioning:** Add 3-5 nodes rapidly, observe no snappy movements
2. **Single Camera Movement:** Verify auto-fit only triggers once per update cycle
3. **Flower Interaction:** Click flower multiple times, verify smooth collapse/expand with clear visual state

### Performance Check

1. Open Chrome DevTools Performance tab
2. Record while adding 20+ nodes
3. Verify animations run at 60fps
4. Check that position animations don't overlap with auto-fit

### Edge Cases

1. **Rapid SSE Updates:** Verify debouncing prevents animation pileup
2. **Very Small Graphs:** Ensure auto-fit doesn't over-zoom (1-3 nodes)
3. **Collapsed Flowers:** Verify children remain hidden on page refresh

---

## Expected Outcomes

**Before:**

- Nodes snap/jump to positions instantly
- Camera moves 3-5 times per update
- Flowers disappear unexpectedly on click
- "Breathing" effect from conflicting animations

**After:**

- All position changes animate smoothly (800-1200ms)
- Single, coordinated camera movement per update cycle (2500ms)
- Clear visual affordance for flower interaction (▶/▼ icons, hover state)
- No conflicting animations (width/height already fixed in CSS)

**Performance Impact:**

- Minimal - animations are GPU-accelerated (`opacity`, `transform`)
- Better perceived performance due to smooth transitions
- Reduced layout thrashing from consolidated auto-fit

---

## Future Enhancements (Not in This Plan)

1. **fCoSE Placement Constraints:** Replace manual petal positioning with native fCoSE alignment constraints
2. **Per-Element Layout Parameters:** Customize repulsion/gravity for stems vs petals
3. **Animation Queue Manager:** Limit concurrent animations to <100 elements for very large graphs
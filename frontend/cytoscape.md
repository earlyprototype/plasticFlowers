# Cytoscape.js Research & Best Practices

## What is Cytoscape?

**Cytoscape.js** is an open-source JavaScript library for **interactive network visualization**. Originally designed for complex biological networks (molecular interactions, gene regulation, protein networks), it's domain-independent and powerful for any complex network analysis.

**Primary Use Cases:**
- Biology: Molecular/genetic interactions, pathway analysis (WikiPathways, Reactome, KEGG)
- Social Science: Social networks, interpersonal relationships, web interactions
- General Network Analysis: Any complex relational data requiring visualization

**Core Strengths:**
- Force-directed layouts for organic network positioning
- Compound/hierarchical nodes (nodes containing other nodes)
- Real-time streaming data integration
- Extensible with 100+ community apps
- Rich API for styling, animation, and interaction

**Website:** https://cytoscape.org/

---

## Key Capabilities We Should Leverage

### 1. Compound Nodes (Our "Flowers")
- **What they are:** Nodes that contain other nodes, forming hierarchical structures
- **Best layouts for compounds:**
  - **fCoSE** (Fast Compound Spring Embedder) - What we're using! Excellent choice.
  - CoSE-Bilkent - Original compound layout
  - Klay - Discrete hierarchical approach
  
**fCoSE Features We're Underusing:**
- **Placement constraints:** Fixed positions, alignment, relative placement with gaps
- **Per-element parameters:** Can customize `nodeRepulsion`, `idealEdgeLength`, `edgeElasticity` per node/edge
- **Multi-level nesting:** Supports deeply nested structures

### 2. Animation System

**Two Animation Types:**
1. **CSS Transitions** (Declarative)
   - Defined in stylesheet with `transition-property`, `transition-duration`, `transition-timing-function`
   - GPU-accelerated for `opacity`, `transform` properties
   - **AVOID** animating `width`, `height`, `background-image` via CSS (expensive)
   
2. **Programmatic Animations** (Imperative)
   - Using `.animate()` method
   - Chainable with `.delay()`
   - Callbacks with `complete` function

**CRITICAL RULE:** Never animate the same property with both CSS transitions AND programmatic animations - they conflict and cause snapping/jittering effects.

### 3. Performance Best Practices

**Batch Operations:**
```javascript
cy.batch(function() {
  // Multiple operations here
  // Triggers single redraw
});

// Or manual control
cy.startBatch();
// operations
cy.endBatch();
```

**Animation Limits:**
- Keep concurrent animations under 100 elements
- Use `eles.flashClass(className, duration)` for simple animations (leverages CSS)
- Only define `transition-property` for specific states (e.g., `:selected`)
- Restrict `transition-property` to only what needs animating

**GPU Acceleration:**
- Animate `transform` and `opacity` (GPU-handled, no layout recalculation)
- Use `will-change` sparingly (overuse degrades performance)
- Avoid animating `width`, `height`, complex backgrounds

### 4. Real-Time Data Streaming

**We're doing this right!** Using SSE (Server-Sent Events) with dynamic updates.

**Best practices:**
- Batch multiple incoming updates together
- Use efficient layout algorithms (fCoSE is good for this)
- Limit concurrent animations during rapid updates

---

## What We're Doing Right

1. **Using fCoSE layout** - Excellent for compound nodes and real-time updates
2. **SSE integration** - Proper approach for streaming data
3. **Compound nodes for "flowers"** - Correct use of hierarchy
4. **Slow, tranquil animations** - Good UX for knowledge exploration
5. **Batch operations** - Using `cy.batch()` in organic positioning

---

## What We're Doing Wrong (Issues Identified)

### 1. **Animation Conflicts** - JUST FIXED
- Had BOTH CSS transitions AND programmatic animations on `width`/`height`
- Caused breathing/snapping effect
- **Fix:** Removed `width`/`height` from CSS `transition-property`

### 2. **Position Animation Approach**
- Currently using instant `.position()` changes
- Creates "snappy" repositioning
- **Should use:** `.animate({ position: {...} }, { duration: 1200 })` for smooth movement

### 3. **Multiple Animation Triggers**
- Auto-fit fires multiple times (repeating behaviors)
- Need better debouncing/coordination

### 4. **Not Using fCoSE Constraints**
- We're manually positioning "petals" around "stems"
- Could leverage fCoSE's built-in **placement constraints** instead:
  - Alignment constraints for radial arrangement
  - Relative placement constraints for petal-to-stem relationships
  - Would be more efficient and natural

### 5. **Compound Node Click Behavior**
- Clicking flower area collapses it unexpectedly
- Need clearer visual affordance or different interaction model

---

## Recommendations for Our Use Case

### Short-Term Fixes (Low-Hanging Fruit)

1. **Position Animations:**
   - Change all `.position()` calls to `.animate({ position: {...} }, { duration: 1200, easing: 'ease-in-out' })`
   - Use longer durations for new nodes (~1800ms), shorter for adjustments (~800ms)

2. **Auto-Fit Coordination:**
   - Single debounced auto-fit with proper animation sequencing
   - Wait for position animations to complete before camera movement

3. **Flower Click Behavior:**
   - Add visual indicator (icon) for collapse/expand
   - Or: Require click on flower border/label, not interior space
   - Or: Use hover to show controls

### Medium-Term Improvements

1. **Leverage fCoSE Constraints:**
   - Define alignment constraints for petal arrangement
   - Use relative placement constraints instead of manual positioning
   - Let fCoSE handle the organic flow natively

2. **Optimize Animation Cascade:**
   - Stagger animations for related elements
   - Use animation callbacks to chain dependent animations
   - Reduce concurrent animations under 100 elements

3. **Performance Monitoring:**
   - Add FPS counter in dev mode
   - Profile with Chrome DevTools during rapid updates
   - Ensure 60fps during animations

### Long-Term Vision

1. **3D Implementation (Plan 2):**
   - Keep Cytoscape.js for 2D view
   - Build parallel R3F implementation for temporal/spatial exploration
   - Allow toggling between 2D (relational) and 3D (temporal) views

2. **Advanced fCoSE Features:**
   - Per-element layout parameters based on node properties
   - Incremental layout for smooth real-time additions
   - Tiling for very large graphs

---

## fCoSE Parameter Tuning for Our Aesthetic

**Current Settings Analysis:**
```javascript
nodeRepulsion: 8000        // Good - keeps nodes spread
idealEdgeLength: 160       // Good - comfortable spacing
edgeElasticity: 0.35      // Good - flexible edges
gravity: 0.3              // Good - gentle clustering
nodeSeparation: 100       // Good - prevents overlap
numIter: 2500             // High - thorough layout
randomize: true           // Good - organic initial placement
```

**Recommendations:**
- Consider **per-element parameters** for stems vs petals
- Stems: Higher `nodeRepulsion`, lower `gravity` (stand out)
- Petals: Lower `nodeRepulsion`, higher `gravity` (cluster to stem)
- Use `animate: 'end'` for smoother incremental layouts

---

## Resources

- **Official Docs:** https://js.cytoscape.org/
- **GitHub:** https://github.com/cytoscape/cytoscape.js
- **fCoSE Layout:** https://github.com/iVis-at-Bilkent/cytoscape.js-fcose
- **Interactive Demos:** https://js.cytoscape.org/demos/
- **Performance Guide:** https://deepwiki.com/cytoscape/cytoscape.js/8-performance-optimization

---

## Next Steps

1. Fix position animations to use `.animate()` instead of instant `.position()`
2. Audit all animation triggers for conflicts/repetition
3. Improve flower interaction UX
4. Consider migrating custom organic positioning to fCoSE constraints
5. Add performance monitoring for optimization validation

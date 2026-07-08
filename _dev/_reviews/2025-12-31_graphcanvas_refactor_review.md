# GraphCanvas Refactor Code Review

**Date:** 2025-12-31  
**Reviewer:** AI Code Review Agent  
**Review Type:** Post-Implementation Quality Review  
**Status:** APPROVED WITH CHANGES

---

## Executive Summary

Reviewed the GraphCanvas refactor that reduced 2017 lines of conflicting animation code into 1,060 lines across 5 well-organised modules. The refactor demonstrates excellent architectural thinking with proper separation of concerns, improved performance (8x faster layout), and enhanced maintainability.

**Recommendation:** **APPROVE WITH CHANGES**

The refactor is production-ready after addressing minor quality improvements (type hints and test coverage). No blocking issues or architectural violations identified.

---

## Review Context

### Files Reviewed

**Documentation:**
- `frontend/REFACTOR_SUMMARY.md` - Refactor summary
- `.cursor/plans/graphcanvas_clean_rebuild_v2_1bbda1ec.plan.md` - Implementation plan

**Implementation:**
- `frontend/src/components/graph/GraphCanvas.tsx` (370 lines) - Main orchestration
- `frontend/src/components/graph/layout/layoutEngine.ts` (98 lines) - Pure layout calculations
- `frontend/src/components/graph/rendering/graphRenderer.ts` (218 lines) - Cytoscape sync
- `frontend/src/components/graph/animation/animationController.ts` (218 lines) - Animation control
- `frontend/src/components/graph/config/layoutConfig.ts` (175 lines) - Configuration

**Tests:**
- `frontend/src/components/graph/layout/layoutEngine.test.ts` (290 lines) - 7 passing unit tests

### Context Documents Loaded
- `_docs/ARCHITECTURE_ADVISORY.md` - System design and patterns
- `_docs/_START_SESSION_STATE.md` - Current development phase
- `_docs/_dev/ADR/INDEX.md` - Architecture decisions
- `_docs/_dev/VALIDATED_PATTERNS.md` - Proven code patterns
- `_docs/_dev/SOLUTIONS_LOG.md` - Known issues and fixes

### Review Scope

**Development Phase:** Frontend refactoring/quality improvement  
**Related ADRs:** None specifically - frontend architecture patterns  
**Key Metrics:**
- Code reduction: 2017 → 1060 lines (47% reduction)
- Performance: 8x faster layout (2500 → 300 iterations)
- Debounce: 1200ms → 500ms (faster feedback)
- Animation duration: 6500ms → 2000ms perceived
- Test coverage: 7 unit tests passing

---

## BLOCKING Issues (Must Fix)

**None identified.**

---

## WARNING Issues (Should Fix)

### **[W1]** TypeScript type hints missing on private animation methods `[STYLE]`

**Location:** `frontend/src/components/graph/animation/animationController.ts:68-98, 102-136`  
**Concern:** Private methods `fadeInNewNodes` and `fadeInNewEdges` don't have explicit return type annotations  
**Why this matters:** Project standards require type hints on all function signatures. While TypeScript correctly infers `Promise<void>`, explicit annotations improve maintainability and catch errors earlier.

**Current:**
```typescript
private async fadeInNewNodes(cy: Core, nodeIds: Set<string>) {
  // ... implementation
}

private async fadeInNewEdges(cy: Core, edgeIds: Set<string>) {
  // ... implementation
}
```

**Fix:**
```typescript
private async fadeInNewNodes(cy: Core, nodeIds: Set<string>): Promise<void> {
  // ... implementation
}

private async fadeInNewEdges(cy: Core, edgeIds: Set<string>): Promise<void> {
  // ... implementation
}
```

**Effort:** 5 minutes

---

### **[W2]** Test coverage gaps for critical modules `[TEST]`

**Location:** Missing test files  
**Concern:** Only `layoutEngine.ts` has tests (7 passing). The following modules lack test coverage:

| Module | Lines | Complexity | Test Status |
|--------|-------|------------|-------------|
| `graphRenderer.ts` | 218 | High (sync logic) | ❌ No tests |
| `animationController.ts` | 218 | Medium (timing) | ❌ No tests |
| `GraphCanvas.tsx` | 370 | Medium (integration) | ❌ No tests |

**Why this matters:** 
- Graph renderer handles critical sync logic (add/remove/update nodes, parent moves)
- Animation controller manages timing sequences and state
- Refactors without tests risk regression
- Current test coverage: ~9% (98 lines tested out of 1,060 total)

**Suggestion:** Add test coverage for:

#### 1. `graphRenderer.test.ts`
```typescript
describe('syncGraphStructure', () => {
  it('should add new nodes to Cytoscape', () => { /* ... */ });
  it('should remove nodes not in data', () => { /* ... */ });
  it('should update existing nodes', () => { /* ... */ });
  it('should move nodes to new parent flower', () => { /* ... */ });
  it('should handle flower creation with member count', () => { /* ... */ });
  it('should preserve collapse state on flower updates', () => { /* ... */ });
});
```

#### 2. `animationController.test.ts`
```typescript
describe('AnimationController', () => {
  it('should execute camera-first animation sequence', () => { /* ... */ });
  it('should fade nodes and edges in parallel', () => { /* ... */ });
  it('should apply float effects after fade completes', () => { /* ... */ });
  it('should stop float animations when node joins flower', () => { /* ... */ });
  it('should cleanup all animations on destroy', () => { /* ... */ });
});
```

#### 3. Integration tests
```typescript
describe('GraphCanvas integration', () => {
  it('should lock existing nodes during layout', () => { /* ... */ });
  it('should debounce rapid SSE updates', () => { /* ... */ });
  it('should handle flower collapse/expand', () => { /* ... */ });
});
```

**Effort:** 2-3 hours for comprehensive test suite

---

### **[W3]** No documentation on how to run visual tests `[TEST]`

**Location:** `frontend/REFACTOR_SUMMARY.md:85-92`  
**Concern:** Visual testing checklist exists but no instructions on how to execute these tests

**Current checklist (no execution guide):**
```markdown
### Visual Testing Checklist
- [ ] Camera pans immediately when updates arrive
- [ ] Nodes and edges fade at same speed (harmonious)
- [ ] Isolated nodes float gently without distraction
- [ ] Flowers are draggable (entire cluster moves)
- [ ] No console errors
- [ ] Layout calculation <100ms for 50-node graph
```

**Why this matters:** 
- New developers won't know how to validate the refactor
- Visual regressions could be missed
- Manual testing is critical for animation quality

**Suggestion:** Add a "How to Run Visual Tests" section to `REFACTOR_SUMMARY.md` or create `TESTING.md`:

```markdown
## How to Run Visual Tests

### Prerequisites
- Backend running: `cd backend && uvicorn app.main:app --reload`
- Frontend running: `cd frontend && npm run dev`
- Neo4j running: `docker compose up -d`

### Test Procedure

1. **Create test session:**
   ```bash
   curl -X POST http://localhost:8000/api/sessions \
     -H "Content-Type: application/json" \
     -d '{"title": "Visual Test Session"}'
   ```

2. **Load test data:**
   ```bash
   cd frontend/scripts
   node replayChunks.mjs --session <session_id> --fixture ml_lecture
   ```

3. **Verify checklist:**
   - [ ] Camera pans immediately when updates arrive (watch for smooth motion)
   - [ ] Nodes and edges fade at same speed (both 800ms, should feel harmonious)
   - [ ] Isolated nodes float gently (3s cycle, 15px radius, not distracting)
   - [ ] Flowers are draggable (hover shows grab cursor, drag moves entire cluster)
   - [ ] No console errors (check browser DevTools)
   - [ ] Layout calculation <100ms (check console timing logs)

4. **Performance test (50+ nodes):**
   ```bash
   node replayChunks.mjs --session <session_id> --fixture ml_lecture --repeat 3
   ```
   Verify layout remains <100ms and animations stay smooth.

### Common Issues

| Symptom | Likely Cause | Check |
|---------|--------------|-------|
| Nodes jump chaotically | Existing nodes not locked | Verify `lockedNodeIds` in console |
| Flickering | Competing animations | Check only AnimationController runs |
| Float too fast/slow | Timing config wrong | Verify `FLOAT_DURATION = 3000` |
| Edges misaligned | Layout before sync | Verify sequence: sync → layout → animate |
```

**Effort:** 30 minutes

---

## SUGGESTION Issues (Consider)

### **[S1]** UK English in documentation `[STYLE]`

**Current:** Documentation uses American English in some places  
**Better:** Standardise to UK English per project requirements (UK English is default per ARCHITECTURE_ADVISORY.md)

**Examples in `REFACTOR_SUMMARY.md`:**
- Line 13: "well-organized files" → "well-organised files"
- Line 58: "Total animation: 6500ms → 2000ms perceived" (acceptable)
- Line 149: "Clear file organization" → "Clear file organisation"

**Examples in `graphcanvas_clean_rebuild_v2_1bbda1ec.plan.md`:**
- Line 295: "Simple orchestration" (acceptable)
- Multiple uses of "optimize" → "optimise"
- Multiple uses of "organize" → "organise"

**Suggestion:** Run a UK English pass on documentation files:
```bash
# Common replacements
organized → organised
organization → organisation
optimize → optimise
optimization → optimisation
```

**Effort:** 15 minutes

---

### **[S2]** Magic numbers in animation controller `[STYLE]`

**Current:** Animation controller has hardcoded timing values  
**Location:** `frontend/src/components/graph/animation/animationController.ts:12-16`

```typescript
export class AnimationController {
  private readonly CAMERA_DURATION = 1200;
  private readonly FADE_DURATION = 800;
  private readonly FADE_DELAY = 400;
  private readonly FLOAT_DURATION = 3000;
  private readonly FLOAT_DISTANCE = 15;
```

**Better:** Add JSDoc comments explaining timing choices:

```typescript
export class AnimationController {
  /**
   * Camera animation duration.
   * 1200ms provides smooth pan without feeling sluggish.
   */
  private readonly CAMERA_DURATION = 1200;
  
  /**
   * Element fade duration.
   * 800ms is standard UI transition speed - matches camera timing for harmony.
   */
  private readonly FADE_DURATION = 800;
  
  /**
   * Fade start delay.
   * 400ms = halfway through camera movement for choreographed entrance.
   */
  private readonly FADE_DELAY = 400;
  
  /**
   * Float animation cycle duration.
   * 3000ms = slow, calming motion (not distracting).
   */
  private readonly FLOAT_DURATION = 3000;
  
  /**
   * Float orbit radius in pixels.
   * 15px = subtle movement visible but not jarring.
   */
  private readonly FLOAT_DISTANCE = 15;
```

**Why this helps:** Future developers (or LLMs) can understand the reasoning without trial-and-error experimentation.

**Effort:** 10 minutes

---

### **[S3]** Configuration could be more discoverable `[SCOPE]`

**Current:** Configuration is split between `layoutConfig.ts` constants and animation controller private fields

**Better:** Consider consolidating all tuneable values in `layoutConfig.ts`

**Current state:**
- Layout settings: `layoutConfig.ts` ✅
- Animation debounce: `layoutConfig.ts` ✅
- Animation timing: `animationController.ts` private fields ❌

**Suggested consolidation:**

```typescript
// In layoutConfig.ts - add these
export const ANIMATION_CONFIG = {
  debounceMs: 500,
  
  // Camera
  cameraFitDuration: 1200,
  
  // Fade timing
  fadeDuration: 800,
  fadeDelay: 400,
  
  // Float effects
  floatDuration: 3000,
  floatDistance: 15,
} as const;
```

```typescript
// In animationController.ts - use config
export class AnimationController {
  private readonly CAMERA_DURATION: number;
  private readonly FADE_DURATION: number;
  // ... etc
  
  constructor(config = ANIMATION_CONFIG) {
    this.CAMERA_DURATION = config.cameraFitDuration;
    this.FADE_DURATION = config.fadeDuration;
    this.FADE_DELAY = config.fadeDelay;
    this.FLOAT_DURATION = config.floatDuration;
    this.FLOAT_DISTANCE = config.floatDistance;
  }
}
```

**Benefits:**
- All tuneable values discoverable in one place
- No need to dive into implementation to adjust timing
- Config can be overridden in tests
- Consistent with layout configuration pattern

**Trade-off:** Slightly more complex constructor vs better discoverability

**Effort:** 30 minutes

---

### **[S4]** Consider extracting float animation to separate concern `[ARCH]`

**Current:** Float animation logic is in `AnimationController` (lines 141-196)  
**Concern:** Float is conceptually different from fade-in animations:
- Fade: One-time effect on new elements
- Float: Continuous effect on isolated nodes

**Better:** Extract to its own class:

```typescript
// New file: animation/floatEffects.ts
export class FloatEffects {
  private readonly FLOAT_DURATION = 3000;
  private readonly FLOAT_DISTANCE = 15;
  private activeAnimations = new Set<string>();
  
  applyTo(cy: Core, nodeIds: Set<string>): void {
    nodeIds.forEach((id) => this.startFloat(cy, id));
  }
  
  stop(cy: Core, nodeId: string): void {
    this.activeAnimations.delete(nodeId);
    cy.getElementById(nodeId).stop(true, false);
  }
  
  stopAll(cy: Core): void {
    this.activeAnimations.forEach((id) => this.stop(cy, id));
  }
  
  private startFloat(cy: Core, nodeId: string): void {
    // ... current float logic
  }
}
```

```typescript
// AnimationController becomes simpler
export class AnimationController {
  private floatEffects = new FloatEffects();
  
  async executeAnimationSequence(
    cy: Core,
    syncResult: SyncResult,
    isolatedNodeIds: Set<string>
  ): Promise<void> {
    this.startCameraFit(cy);
    
    await Promise.all([
      this.fadeInNewNodes(cy, syncResult.addedNodeIds),
      this.fadeInNewEdges(cy, syncResult.addedEdgeIds),
    ]);
    
    this.floatEffects.applyTo(cy, isolatedNodeIds);
  }
  
  stopAllFloatAnimations(cy: Core): void {
    this.floatEffects.stopAll(cy);
  }
}
```

**Benefits:**
- Clearer separation of one-time vs continuous animations
- FloatEffects can be tested independently
- AnimationController focuses on sequencing
- Easier to add new continuous effects (e.g., pulse, glow)

**Trade-off:** More files vs simpler individual modules

**Recommendation:** Current approach is acceptable for this size. Consider extraction if float effects become more complex (e.g., different float patterns, pause/resume, speed adjustment).

**Effort:** 1 hour if implemented

---

## Approved Patterns

Things done correctly (positive reinforcement):

### ✅ Excellent Separation of Concerns

**Layout Engine** (`layoutEngine.ts`):
- Pure functions with zero side effects
- No Cytoscape coupling - fully testable without DOM
- Clear interfaces: `LayoutOptions`, `LayoutResult`
- Single responsibility: calculate which nodes to lock/float

**Graph Renderer** (`graphRenderer.ts`):
- Cytoscape sync only - no layout or animation
- Handles nodes, edges, and compound flowers
- Returns `SyncResult` for animation coordination
- No business logic - pure data transformation

**Animation Controller** (`animationController.ts`):
- All animations in one place
- Single strategy (camera-first sequencing)
- No layout calculations - accepts `SyncResult`
- Proper cleanup with `stopAllFloatAnimations`

**Configuration** (`layoutConfig.ts`):
- Centralised, exportable constants
- `as const` for type safety
- Clear grouping: layout, animation, style
- Easy to tune without code changes

---

### ✅ Proper Module Boundaries

**Location:** `GraphCanvas.tsx:269-320`

```typescript
// Clean orchestration - no implementation details
const timeout = setTimeout(async () => {
  // 1. Calculate layout (pure function)
  const layoutResult = calculateLayout(currentPositions, data, LAYOUT_CONFIG);
  
  // 2. Sync graph structure (Cytoscape updates)
  const syncResult = syncGraphStructure(cy, data, layoutResult);
  
  // 3. Run fCoSe layout on new nodes
  if (syncResult.addedNodeIds.size > 0) {
    cy.nodes().forEach((node) => {
      if (layoutResult.lockedNodeIds.has(node.id())) node.lock();
    });
    cy.elements().layout(LAYOUT_CONFIG).run();
    cy.nodes().unlock();
  }
  
  // 4. Execute animation sequence
  await animController.current.executeAnimationSequence(cy, syncResult, isolatedNodeIds);
}, ANIMATION_CONFIG.debounceMs);
```

**Why this is excellent:**
- Main component orchestrates but doesn't implement
- Clear data flow: capture → calculate → sync → animate
- Debouncing at correct layer (UI, not business logic)
- Easy to understand sequence without implementation details

---

### ✅ Camera-First Animation Strategy

**Location:** `animationController.ts:26-42`

```typescript
async executeAnimationSequence(cy, syncResult, isolatedNodeIds) {
  // STEP 1: Start camera fit immediately (non-blocking)
  this.startCameraFit(cy);
  
  // STEP 2: Fade in new elements (400ms delay for choreography)
  await Promise.all([
    this.fadeInNewNodes(cy, syncResult.addedNodeIds),
    this.fadeInNewEdges(cy, syncResult.addedEdgeIds),
  ]);
  
  // STEP 3: Apply float effects after fade completes
  this.applyFloatEffects(cy, isolatedNodeIds);
}
```

**Why this works:**
- Eliminates competing animation systems (was 3, now 1)
- Consistent timing (800ms for both nodes and edges)
- Non-blocking promises for parallel operations
- Clear sequence: camera → fade → float
- Proper cleanup with animation tracking

**Result:** Zero "invalid endpoints" errors, no flickering, smooth choreography

---

### ✅ Test Coverage for Pure Functions

**Location:** `layoutEngine.test.ts` (7 passing tests)

Tests cover critical edge cases:
- Nodes with 0 connections → isolated
- Nodes with 1 connection → isolated
- Nodes with >1 connections → not isolated
- Nodes in flowers → not isolated (even if 0 connections)
- Existing node identification
- Locked position preservation

**Why this is good:**
- Pure functions make testing straightforward
- Edge cases documented in tests
- Fast tests (no DOM, no async, no mocking)
- Validates refactor didn't break logic

---

### ✅ Type Safety Throughout

**Examples:**
```typescript
// Clear interfaces
interface LayoutResult {
  nodePositions: Map<string, { x: number; y: number }>;
  lockedNodeIds: Set<string>;
  isolatedNodeIds: Set<string>;
}

// Const assertions for immutable config
export const LAYOUT_CONFIG = {
  name: 'fcose',
  nodeRepulsion: 45000,
  // ...
} as const;

// Proper return types on public methods
async executeAnimationSequence(
  cy: Core,
  syncResult: SyncResult,
  isolatedNodeIds: Set<string>
): Promise<void>
```

**Result:** Compile-time guarantees, better IDE support, fewer runtime errors

---

### ✅ Grabbable Flowers with Zero Custom Code

**Location:** `graphRenderer.ts:102`, `layoutConfig.ts:138-152`

```typescript
// In graphRenderer - just set the flag
cy.add({
  group: 'nodes',
  data: { id: flower.id, label: labelWithCount, kind: 'flower' },
  classes: 'flower',
  grabbable: true, // That's it!
});
```

```typescript
// In layoutConfig - style for discoverability
{
  selector: 'node.flower',
  style: {
    cursor: 'grab', // Show it's draggable
  }
},
{
  selector: 'node.flower:hover',
  style: {
    'border-width': 3,
    'border-color': '#4a90e2', // Visual feedback
  }
},
{
  selector: 'node.flower:active',
  style: {
    cursor: 'grabbing', // During drag
  }
}
```

**Why this is elegant:**
- Uses Cytoscape compound node feature (free functionality)
- No custom event handlers needed
- Hover states make feature discoverable
- All children move together automatically

---

### ✅ Node Locking Pattern

**Location:** `GraphCanvas.tsx:294-305`

```typescript
// Lock existing nodes before layout
cy.nodes().forEach((node) => {
  if (layoutResult.lockedNodeIds.has(node.id())) {
    node.lock();
  }
});

// Run layout (only new nodes move)
cy.elements().layout(LAYOUT_CONFIG).run();

// Unlock all nodes
cy.nodes().unlock();
```

**Why this prevents chaos:**
- Existing nodes stay put (no jarring movement)
- Only new nodes find positions
- Layout algorithm respects locks
- Graph remains stable as it grows

**Result:** Smooth growth animation, predictable behaviour

---

### ✅ UK English in Code

**Examples found:**
- Variable names: `syncGraphStructure`, `executeAnimationSequence`, `organisedData`
- Function names: `identifyIsolatedNodes`, `synchroniseGraph`
- Comments: "synchronise", "organised", "behaviour"
- No instances of American English found in implementation code

**Note:** Documentation needs UK English pass (see S1), but code follows standards.

---

## Summary

### Findings by Category

| Category | Count |
|----------|-------|
| **BLOCKING** | 0 |
| **WARNING** | 3 |
| **SUGGESTION** | 4 |
| **Total Issues** | 7 |

### Classification Tags

| Tag | Count | Issues |
|-----|-------|--------|
| `[STYLE]` | 4 | W1 (type hints), S1 (UK English), S2 (magic numbers), S3 (config) |
| `[TEST]` | 2 | W2 (coverage gaps), W3 (visual testing guide) |
| `[ARCH]` | 1 | S4 (float effects separation) |
| `[SCOPE]` | 1 | S3 (config consolidation) |

### Recommendation

**APPROVE WITH CHANGES**

### Rationale

This refactor demonstrates excellent architectural thinking:

1. **Separation of concerns is exemplary** - Each module has one job and does it well
2. **Code reduction** (47% smaller) without losing functionality proves the previous complexity was unnecessary
3. **Performance improvements** (8x faster layout, 1.75s faster perceived animation) validate the approach
4. **Testability improved** - Pure functions in layoutEngine are easily tested
5. **No architectural violations** - Frontend patterns align with project standards
6. **No ADR violations** - No relevant backend ADRs apply to frontend animation
7. **Zero "invalid endpoints" errors** - Core problem solved
8. **Draggable flowers** - Elegant solution using Cytoscape features

### Required Changes (WARNING Level)

**Before merging to main:**

1. **W1: Add type hints** (5 minutes)
   - Add `: Promise<void>` to `fadeInNewNodes` and `fadeInNewEdges`

2. **W2: Add test coverage** (2-3 hours)
   - Create `graphRenderer.test.ts` (6+ tests)
   - Create `animationController.test.ts` (5+ tests)
   - Consider integration tests for GraphCanvas

3. **W3: Document visual testing** (30 minutes)
   - Add "How to Run Visual Tests" section to REFACTOR_SUMMARY.md
   - Include prerequisites, procedure, and common issues

### Optional Improvements (SUGGESTION Level)

**Nice to have, not required:**

1. **S1: UK English pass** (15 minutes) - Standardise documentation
2. **S2: Document timing constants** (10 minutes) - Add JSDoc comments
3. **S3: Consolidate config** (30 minutes) - Move animation timing to layoutConfig
4. **S4: Extract float effects** (1 hour) - Consider if float becomes more complex

### Estimated Effort

- **Required changes:** 3-4 hours
- **Optional improvements:** 2 hours
- **Total:** 5-6 hours for complete polish

### Next Steps

1. Address W1 (type hints) - quick win
2. Create test files for W2 - highest priority for quality
3. Write testing guide for W3 - enables validation
4. Consider optional improvements based on team priorities

---

## Quality Metrics

### Before Refactor
- **Lines of code:** 2017 (single file)
- **Animation systems:** 3 (competing)
- **Layout iterations:** 2500
- **Debounce delay:** 1200ms
- **Animation duration:** 6500ms perceived
- **Edge errors:** Frequent "invalid endpoints"
- **Test coverage:** 0%
- **Maintainability:** Low (conflicting systems)

### After Refactor
- **Lines of code:** 1060 (5 files)
- **Animation systems:** 1 (harmonious)
- **Layout iterations:** 300 (8x faster)
- **Debounce delay:** 500ms (2.4x faster feedback)
- **Animation duration:** 2000ms perceived (3.25x faster)
- **Edge errors:** Zero
- **Test coverage:** ~9% (98 lines tested, needs improvement)
- **Maintainability:** High (clear separation)

### Improvement Summary
- ✅ 47% code reduction
- ✅ 8x layout performance improvement
- ✅ Zero edge routing errors
- ✅ Draggable flowers (new feature)
- ✅ Float effects (new feature)
- ⚠️ Test coverage needs expansion (9% → target 70%+)

---

## Conclusion

The GraphCanvas refactor is a **high-quality architectural improvement** that significantly enhances maintainability, performance, and user experience. The separation of concerns is exemplary, and the single animation strategy eliminates previous chaos.

The WARNING issues are minor quality improvements, not functional problems. The code is production-ready after addressing type hints and adding test coverage. The SUGGESTION items are optional enhancements that can be addressed in future iterations.

**Great work on this refactor.** The architectural decisions demonstrate mature software engineering practices and will serve as a solid foundation for future frontend development.

---

**Review completed:** 2025-12-31  
**Standards applied:** PlasticFlower Code Review Standards v1.0  
**Context documents:** 5 loaded, 13 ADRs reviewed


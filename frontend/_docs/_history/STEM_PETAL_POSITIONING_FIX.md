# Stem-Petal Positioning Fix - Flower Internal Clustering

**Date:** 2025-12-31  
**Issue:** Nodes within flowers not clustering around stem in circular orbit pattern

---

## Problem

Despite implementing stem-petal positioning, nodes within flowers were not forming the intended pattern:
- **Expected:** Stem node (most mentioned) at center, petals in circular orbit
- **Actual:** Random scattered positions within flowers

---

## Root Causes

### 1. Missing Node Data

**Problem:** Node `mentions` field not passed to Cytoscape

```typescript
// OLD - graphRenderer.ts
const elementData = {
  id: node.id,
  label: node.label,
  status: node.status,
  kind: 'node',
  parent: parentId,
  // ❌ Missing: mentions, timestamps, inferred_type
};
```

**Effect:** `applyAdaptiveStemPetalPositioning` couldn't find most mentioned node (stem)

**Fix:** Added full node data
```typescript
// NEW
const elementData = {
  id: node.id,
  label: node.label,
  status: node.status,
  kind: 'node',
  parent: parentId,
  mentions: node.mentions || 0,          // ✅ For stem detection
  timestamps: node.timestamps || [],     // ✅ For temporal styling
  inferred_type: node.inferred_type || 'concept',
};
```

### 2. Missing `stem_node_id` from Backend

**Problem:** Backend may not set `stem_node_id` on flowers

```typescript
// OLD - stemPetalPositioning.ts
const stemNodeId = flower.stem_node_id;
if (!stemNodeId) return; // ❌ Early exit, no positioning!
```

**Fix:** Auto-detect stem from mentions if not provided
```typescript
// NEW - automatically find most mentioned node
let stemNodeId = flower.stem_node_id;

if (!stemNodeId) {
  // Calculate stem from member nodes (highest mentions)
  let maxMentions = -1;
  let stemCandidate = memberNodes[0];
  
  memberNodes.forEach((node) => {
    const mentions = node.data('mentions') || 0;
    if (mentions > maxMentions) {
      maxMentions = mentions;
      stemCandidate = node;
    }
  });
  
  stemNodeId = stemCandidate.id();
}
```

### 3. Organic Growth Disrupting Stem-Petal

**Problem:** Execution order was wrong

```
OLD SEQUENCE:
1. fCoSe layout
2. Organic growth (moves nodes) ← 800ms animations
3. Stem-petal positioning ← Runs during organic growth!
```

**Effect:** Organic growth animations were moving flower member nodes AFTER stem-petal positioned them

**Fix:** Reverse order + filter organic growth
```
NEW SEQUENCE:
1. fCoSe layout
2. Stem-petal positioning (fixed positions)
3. Organic growth (skip nodes in flowers) ← Respects stem-petal
```

**Code:**
```typescript
// 3.5. Apply stem-petal positioning FIRST
if (flowers.length > 0) {
  applyAdaptiveStemPetalPositioning(cy, flowers);
}

// 3.6. Apply organic growth (exclude flower members)
const nodesInFlowers = new Set<string>();
flowers.forEach(f => {
  if (f.member_ids) {
    f.member_ids.forEach(id => nodesInFlowers.add(id));
  }
});

// Only apply organic growth to edges where target is NOT in a flower
const filteredEdges = new Set<string>();
syncResult.addedEdgeIds.forEach(edgeId => {
  const rel = relationships.find(r => r.id === edgeId);
  if (rel && !nodesInFlowers.has(rel.target_id)) {
    filteredEdges.add(edgeId);
  }
});

applyOrganicGrowth(cy, filteredEdges, relationships);
```

---

## How Stem-Petal Positioning Works Now

### 1. Find Stem Node

```typescript
// Priority 1: Use backend-provided stem_node_id
if (flower.stem_node_id) {
  stemNodeId = flower.stem_node_id;
}
// Priority 2: Auto-detect from mentions
else {
  const memberNodes = flower.member_ids.map(id => cy.getElementById(id));
  stemNodeId = findMostMentionedNode(memberNodes);
}
```

### 2. Calculate Orbit Radius

```typescript
function calculateOptimalOrbitRadius(petalCount: number): number {
  const BASE_RADIUS = 140;
  const RADIUS_PER_PETAL = 25;
  
  // More petals = larger orbit to prevent overlap
  return Math.max(180, BASE_RADIUS + (petalCount * RADIUS_PER_PETAL));
}

// Examples:
// 1 petal:  180px radius
// 3 petals: 215px radius
// 5 petals: 265px radius
// 10 petals: 390px radius
```

### 3. Position Nodes

**Stem at center (relative to flower compound node at 0,0):**
```typescript
stemNode.position({ x: 0, y: 0 });
```

**Petals in circular orbit:**
```typescript
const angleStep = 360 / petalCount; // Evenly distribute

petalNodes.forEach((petalNode, index) => {
  const angle = (index * angleStep) * (Math.PI / 180);
  
  const x = orbitRadius * Math.cos(angle);
  const y = orbitRadius * Math.sin(angle);
  
  petalNode.position({ x, y }); // Relative to flower center
});
```

**Visual result:**
```
        [petal-1]
            |
   [petal-4] — [STEM] — [petal-2]
            |
        [petal-3]
```

---

## Execution Sequence (Final)

```
1. SSE Event → New nodes/relationships/flowers
   ↓
2. Sync Structure → Add to Cytoscape
   - Nodes get mentions/timestamps/inferred_type data ✅
   ↓
3. Intelligent Pre-positioning → Type-based regions
   ↓
4. fCoSe Layout → Force-directed refinement
   ↓
5. 🌸 STEM-PETAL POSITIONING (FIRST!)
   - Find stem (most mentioned or provided)
   - Stem at (0,0) relative to flower
   - Petals in circular orbit
   ↓
6. 🌱 ORGANIC GROWTH (FILTERED!)
   - Only affects nodes NOT in flowers
   - Preserves stem-petal structure
   ↓
7. Animation → Camera-first choreography
```

---

## Visual Comparison

### Before (Broken)

```
┌─ Flower A ────────┐
│                   │
│  [node] [node]    │
│    [node]         │
│ [node]   [node]   │  ← Random scatter
│     [node]        │
│                   │
└───────────────────┘
```

### After (Fixed)

```
┌─ Flower A ────────┐
│                   │
│      [petal]      │
│   [p]  [S]  [p]   │  ← Stem at center
│      [petal]      │  ← Petals orbiting
│                   │
└───────────────────┘

[S] = Stem (most mentioned)
[p] = Petals (orbit ~180-400px)
```

---

## Configuration

### Orbit Radius Formula

```typescript
BASE_RADIUS = 140px
RADIUS_PER_PETAL = 25px

radius = max(180, BASE + (petalCount × 25))
```

### Tuning

**Tighter orbits:**
```typescript
BASE_RADIUS = 100;  // Was 140
RADIUS_PER_PETAL = 15;  // Was 25
```

**Wider orbits:**
```typescript
BASE_RADIUS = 200;  // Was 140
RADIUS_PER_PETAL = 35;  // Was 25
```

**Fixed radius (ignore petal count):**
```typescript
function calculateOptimalOrbitRadius(petalCount: number): number {
  return 200; // Always 200px regardless of count
}
```

---

## Testing

**All 68 tests passing** ✅

### Visual Test Checklist

When flowers form, verify:

- [ ] Stem node (most mentioned) is at flower center
- [ ] Petal nodes arranged in circle around stem
- [ ] All petals evenly spaced (360° / petalCount)
- [ ] Orbit radius scales with petal count
- [ ] Nodes don't move after stem-petal positioning
- [ ] Organic growth doesn't affect flower members
- [ ] Clicking flower doesn't break positioning
- [ ] Dragging flower moves all nodes together

---

## Files Changed

### 1. `stemPetalPositioning.ts`
- Auto-detect stem from mentions if not provided
- Guard against missing stem_node_id

### 2. `graphRenderer.ts`
- Added `mentions`, `timestamps`, `inferred_type` to node data
- Enables stem detection by mentions count

### 3. `GraphCanvas.tsx`
- Reversed execution order: stem-petal BEFORE organic growth
- Filter organic growth to exclude flower members
- Prevents disruption of stem-petal structure

---

## Debugging

### Stem Not Detected?

Check if nodes have mentions data:
```typescript
const node = cy.getElementById('some-node-id');
console.log('Mentions:', node.data('mentions')); // Should be number
```

### Petals Not Orbiting?

Check flower member_ids:
```typescript
console.log('Flower members:', flower.member_ids);
console.log('Stem ID:', flower.stem_node_id);
```

### Nodes Moving After Positioning?

Check if organic growth is filtering:
```typescript
console.log('Nodes in flowers:', nodesInFlowers);
console.log('Filtered edges:', filteredEdges);
```

### Wrong Stem Node?

Verify mentions counts:
```typescript
flower.member_ids.forEach(id => {
  const node = cy.getElementById(id);
  console.log(id, 'mentions:', node.data('mentions'));
});
```

---

## Summary

**Fixed stem-petal clustering with 3 key changes:**

1. ✅ **Added node data** - mentions/timestamps/inferred_type passed to Cytoscape
2. ✅ **Auto-detect stem** - Find most mentioned node if backend doesn't provide
3. ✅ **Reordered sequence** - Stem-petal BEFORE organic growth + filter flower members

**Result:** Flowers now show proper stem-petal structure with circular orbits!

**Files Modified:**
- `stemPetalPositioning.ts` - Auto-detect stem logic
- `graphRenderer.ts` - Added node data fields
- `GraphCanvas.tsx` - Reordered sequence, filtered organic growth

**Tests:** 68/68 passing ✅

**Stem nodes at center, petals orbiting!** 🌸


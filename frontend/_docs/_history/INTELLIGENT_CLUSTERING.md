# Intelligent Node Clustering

**Date:** 2025-12-31  
**Feature:** Semantic pre-positioning for meaningful graph layout

---

## Overview

Instead of random initial positions, nodes are intelligently pre-positioned based on their **semantic attributes** before fCoSe layout runs. This creates meaningful spatial groupings that reflect the conceptual structure of your knowledge graph.

---

## How It Works

### 1. **Pre-Positioning** (Before Layout)
New nodes receive intelligent starting positions based on three factors:
- **Type** (concept, entity, event, process, etc.)
- **Importance** (mention count)
- **Recency** (how recently mentioned)

### 2. **Force-Directed Refinement** (During Layout)
fCoSe refines these positions while respecting:
- Relationships (connected nodes pull together)
- Repulsion forces (prevent overlap)
- Compound constraints (flowers stay grouped)

### 3. **Result**
Meaningful spatial organization where position encodes semantic information.

---

## Spatial Layout Philosophy

Nodes are arranged in **semantic space**:

```
                 ABSTRACT IDEAS
                   (Concepts)
                       ↑
                       |
    CONCRETE ← ─ ─ ─ ─ + ─ ─ ─ ─ → ACTIONS
    (Entities)      CENTER      (Events)
                       |
                       ↓
                   PROCEDURES
                   (Processes)
```

### Type-Based Regions

| Type | Region | Position | Rationale |
|------|--------|----------|-----------|
| **concept** | Top | (0, -1000) | Abstract ideas "float above" |
| **entity** | Left | (-1000, 0) | Concrete things are "grounded" |
| **event** | Right | (1000, 0) | Actions happen "outward" |
| **process** | Bottom | (0, 1000) | Procedures are "foundational" |
| **attribute** | Top-left | (-700, -700) | Properties of entities |
| **relation** | Bottom-right | (700, 700) | Connections between elements |
| **state** | Top-right | (700, -700) | Conditions/status |
| **agent** | Bottom-left | (-700, 700) | Actors/performers |

### Importance Influence

High-mention nodes pull toward center:
- **1 mention:** +800px from center (periphery)
- **5 mentions:** +400px from center (mid-range)
- **10+ mentions:** Near center (core concepts)

### Recency Influence

Recent mentions pull toward center:
- **Just mentioned:** Near center (active topic)
- **10 minutes ago:** +200px from center
- **30+ minutes ago:** +600px from center (fading relevance)

---

## Clustering Strategies

Four preset strategies for different use cases:

### 1. **SEMANTIC** (Default)
Emphasizes type-based clustering.

```typescript
{
  typeWeight: 0.8,       // Primary factor
  importanceWeight: 0.15, // Secondary
  recencyWeight: 0.05,    // Subtle influence
}
```

**Use when:** You want clear semantic regions (concepts vs entities vs events)

**Visual result:**
```
     [Concepts cluster]
            
[Entities]     [Events]
    cluster    cluster
            
    [Processes cluster]
```

### 2. **IMPORTANCE**
Emphasizes frequently-mentioned nodes.

```typescript
{
  typeWeight: 0.2,
  importanceWeight: 0.7,  // Primary factor
  recencyWeight: 0.1,
}
```

**Use when:** You want expert/key concepts at the center

**Visual result:**
```
       periphery
         ↓
    [minor topics]
         ↓
  [intermediate topics]
         ↓
   [CORE CONCEPTS]  ← center
```

### 3. **TEMPORAL**
Emphasizes conversation flow over time.

```typescript
{
  typeWeight: 0.2,
  importanceWeight: 0.1,
  recencyWeight: 0.7,     // Primary factor
}
```

**Use when:** You want to see how the conversation evolved

**Visual result:**
```
    [30 min ago]
         ↓
    [20 min ago]
         ↓
    [10 min ago]
         ↓
   [CURRENT TOPIC]  ← center
```

### 4. **BALANCED**
Equal weighting of all factors.

```typescript
{
  typeWeight: 0.6,
  importanceWeight: 0.3,
  recencyWeight: 0.1,
}
```

**Use when:** You want nuanced positioning

---

## Implementation Details

### Sequence

1. **Node added** → SSE event received
2. **Sync structure** → Node created in Cytoscape
3. **Calculate intelligent position** → Based on type/importance/recency
4. **Apply pre-position** → Set node.position() before layout
5. **Lock existing nodes** → Stability
6. **Run fCoSe layout** → Refines positions with forces
7. **Apply stem-petal** → Organic flower arrangement
8. **Animate** → Camera-first choreography

### Code Integration

```typescript
// In GraphCanvas.tsx
if (syncResult.addedNodeIds.size > 0) {
  const newNodes = nodes.filter(n => syncResult.addedNodeIds.has(n.id));
  
  // Calculate intelligent positions
  const intelligentPositions = calculateIntelligentPositions(
    newNodes,
    CLUSTERING_PRESETS.SEMANTIC // or IMPORTANCE, TEMPORAL, BALANCED
  );
  
  // Apply before layout
  applyIntelligentPositions(cy, intelligentPositions);
}

// Then run fCoSe layout (which refines these positions)
cy.elements().layout(LAYOUT_CONFIG).run();
```

---

## Examples

### Example 1: Machine Learning Lecture

**Input nodes:**
- "neural networks" (concept, 10 mentions, recent)
- "dataset" (entity, 5 mentions, recent)
- "training" (process, 8 mentions, recent)
- "gradient descent" (process, 3 mentions, old)

**Semantic clustering result:**
```
        [neural networks]  ← Top (concept) + center (important + recent)
               |
               |
    [dataset] ─┴─ [training]  ← Left (entity), bottom (process)
                     |
              [gradient descent]  ← Bottom (process) + periphery (older)
```

### Example 2: Project Planning

**Input nodes:**
- "deadline" (event, 8 mentions, very recent)
- "requirements" (concept, 6 mentions, recent)
- "stakeholder" (agent, 4 mentions, old)
- "API endpoint" (entity, 2 mentions, recent)

**Importance clustering result:**
```
       [deadline]  ← Center (most important)
          |
     [requirements]  ← Mid-range
          |
    [stakeholder]  ← Periphery (less important)
          |
    [API endpoint]  ← Far periphery (least mentioned)
```

---

## Configuration

### Changing Strategy

**In GraphCanvas.tsx:**
```typescript
const intelligentPositions = calculateIntelligentPositions(
  newNodes,
  CLUSTERING_PRESETS.SEMANTIC  // Change this!
);
```

Options:
- `CLUSTERING_PRESETS.SEMANTIC` - Type-based (default)
- `CLUSTERING_PRESETS.IMPORTANCE` - Mention-based
- `CLUSTERING_PRESETS.TEMPORAL` - Recency-based
- `CLUSTERING_PRESETS.BALANCED` - Mixed

### Custom Strategy

```typescript
const myStrategy = {
  typeWeight: 0.5,
  importanceWeight: 0.3,
  recencyWeight: 0.2,
};

const positions = calculateIntelligentPositions(newNodes, myStrategy);
```

### Adding New Type Regions

**In intelligentClustering.ts:**
```typescript
const TYPE_REGIONS: Record<string, { x: number; y: number }> = {
  // ...existing regions...
  
  // Add your custom type
  'custom_type': { x: 500, y: -500 },  // Top-right quadrant
};
```

---

## Benefits

### 1. **Semantic Meaning**
Position encodes information - you can understand node relationships spatially.

### 2. **Predictable Layout**
Similar nodes cluster predictably based on their attributes.

### 3. **No Random Chaos**
Starting positions are meaningful, not random scattering.

### 4. **Better Convergence**
fCoSe reaches stable layouts faster with good initial positions.

### 5. **Visual Hierarchy**
Important/recent nodes naturally gravitate to center.

---

## Performance

- **Pre-positioning:** O(n) where n = new nodes only
- **No layout cost:** Runs before fCoSe, doesn't add iterations
- **Memory:** Map<nodeId, position> - minimal overhead

---

## Testing

**All 15 tests passing:**
- Position assignment
- Type-based regions
- Importance gradients
- Recency gradients
- Preset strategies
- Edge cases (unknown types, zero weights, empty timestamps)

Run tests:
```bash
npm test intelligentClustering.test.ts
```

---

## Troubleshooting

### Nodes Still Clustering in Center

**Cause:** Layout forces overriding pre-positions  
**Fix:** Reduce gravity in `LAYOUT_CONFIG`:
```typescript
gravity: 0.04  // Lower = less pull to center
```

### Type Regions Not Visible

**Cause:** Other weights too high  
**Fix:** Use SEMANTIC preset or increase typeWeight:
```typescript
CLUSTERING_PRESETS.SEMANTIC  // typeWeight: 0.8
```

### All Nodes Same Position

**Cause:** All weights are zero  
**Fix:** System auto-defaults to type-only clustering (safe fallback)

---

## Future Enhancements

### Possible Additions

1. **Relationship-based clustering**
   - Nodes with many shared connections cluster together
   
2. **Confidence-based sizing**
   - Higher confidence = larger initial radius
   
3. **User-defined regions**
   - Custom semantic space via UI
   
4. **Dynamic strategy switching**
   - Toggle between presets in real-time
   
5. **Cluster labels**
   - Show "Entities →" "Concepts ↑" directional hints

---

## Summary

**Intelligent clustering gives your graph semantic spatial structure:**

- **Types** define regions (concepts top, entities left, etc.)
- **Importance** pulls to center (key concepts)
- **Recency** fades to periphery (conversation flow)
- **fCoSe refines** while respecting connections
- **Result:** Beautiful, meaningful, readable layouts

**Default: SEMANTIC clustering** - emphasizes type-based regions for clear conceptual organization.


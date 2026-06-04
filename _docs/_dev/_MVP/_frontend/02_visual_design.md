# plasticFlower — Visual Design Specification

> **Date:** December 2025
> **Purpose:** Define the RSA Animate-inspired visual aesthetic
> **Status:** Required reading before Gate 4 implementation

---

## Design Philosophy

### The Inspiration: RSA Animate

RSA Animate videos feature an artist drawing a talk in real-time:
- **White background** — Clean canvas
- **Bold black strokes** — High contrast, memorable
- **Hand-drawn feel** — Organic, not clinical
- **Ideas emerge and connect** — Visual storytelling
- **Simple, not cluttered** — Focus on concepts

plasticFlower automates this experience. The visual output should feel like a **whiteboard sketch**, not a **database diagram**.

---

## Core Aesthetic Principles

| Principle | Application |
|-----------|-------------|
| **White canvas** | Light background, not dark mode |
| **Bold strokes** | Dark lines, high contrast |
| **Organic shapes** | Rounded, soft edges |
| **Minimal colour** | Primarily black + one accent |
| **Drawing feel** | Animations mimic pen strokes |
| **Readable** | Large labels, clear typography |

---

## Colour Palette

### Primary Colours

| Colour | Hex | Usage |
|--------|-----|-------|
| **Canvas** | `#FFFFFF` | Background |
| **Stroke** | `#1A1A1A` | Node borders, edge lines |
| **Text** | `#1A1A1A` | Labels, UI text |
| **Node Fill** | `#FFFFFF` | Node background |
| **Ghost** | `#9CA3AF` | Unconfirmed nodes (grey stroke) |

### Accent Colour

Choose ONE accent colour for highlights:

| Option | Hex | Feel |
|--------|-----|------|
| **Coral** | `#F97316` | Warm, energetic |
| **Teal** | `#14B8A6` | Fresh, modern |
| **Violet** | `#8B5CF6` | Creative, distinctive |

**Recommended:** Coral (`#F97316`) — warm, visible, memorable

### Accent Usage

| Element | Colour |
|---------|--------|
| Stem node (Flower centre) | Accent stroke |
| Active/selected node | Accent highlight |
| New node animation | Brief accent flash |
| UI buttons (primary) | Accent background |

---

## Typography

### Font Choice

**Primary:** `Nunito` or `Quicksand`
- Rounded, friendly
- Highly readable
- Hand-drawn feel without being gimmicky

**Fallback:** `system-ui, -apple-system, sans-serif`

### Font Sizes

| Element | Size | Weight |
|---------|------|--------|
| Node label | 14px | 600 (semibold) |
| Flower label | 16px | 700 (bold) |
| Edge description | 11px | 400 (normal) |
| UI headings | 18px | 700 |
| UI body | 14px | 400 |

---

## Node Design

### Shape

```
╭─────────────────╮
│                 │
│   concept       │
│                 │
╰─────────────────╯
```

- **Shape:** Rounded rectangle (border-radius: 12px)
- **Padding:** 12px horizontal, 8px vertical
- **Min width:** 80px
- **Max width:** 160px (truncate with ellipsis)

### States

| State | Stroke | Fill | Opacity | Border Style |
|-------|--------|------|---------|--------------|
| **Ghost** | `#9CA3AF` | `#FFFFFF` | 0.7 | Dashed (4px dash) |
| **Solid** | `#1A1A1A` | `#FFFFFF` | 1.0 | Solid |
| **Stem** | Accent | `#FFFFFF` | 1.0 | Solid, 3px width |
| **Selected** | Accent | `#FFF7ED` | 1.0 | Solid, 3px width |

### Visual Example (ASCII)

```
GHOST NODE                    SOLID NODE                    STEM NODE
┌ ─ ─ ─ ─ ─ ─ ┐              ╭─────────────╮              ╭━━━━━━━━━━━━━╮
╎             ╎              │             │              ┃             ┃
╎  concept    ╎              │  concept    │              ┃  concept    ┃
╎             ╎              │             │              ┃             ┃
└ ─ ─ ─ ─ ─ ─ ┘              ╰─────────────╯              ╰━━━━━━━━━━━━━╯
   (grey, dashed)               (black, solid)              (accent, bold)
```

---

## Edge Design

### Style

| Property | Value |
|----------|-------|
| **Colour** | `#6B7280` (grey-500) |
| **Width** | 2px |
| **Style** | Solid |
| **Curve** | Bezier (curved, not straight) |
| **Arrow** | Small, at target end |

### Edge Labels (Relationship Description)

| Property | Value |
|----------|-------|
| **Font size** | 11px |
| **Colour** | `#6B7280` |
| **Background** | `#FFFFFF` with 80% opacity |
| **Position** | Centre of edge |

### No Category Colours

**Important:** Unlike the original spec, we do NOT colour-code edges by relationship category.

**Rationale:** RSA Animate uses simple black/grey strokes. Colour-coding adds visual noise and feels like a database diagram, not a sketch.

Category information is preserved in the data — it just doesn't drive visual differentiation.

---

## Flower (Cluster) Design

### Container

Flowers are compound nodes in Cytoscape — a container holding member nodes.

| Property | Value |
|----------|-------|
| **Background** | `#F9FAFB` (grey-50) — very subtle |
| **Border** | `#E5E7EB` (grey-200), 1px, dashed |
| **Border radius** | 16px |
| **Padding** | 20px |
| **Label position** | Top, outside the container |

### Flower Label

| Property | Value |
|----------|-------|
| **Font size** | 16px |
| **Font weight** | 700 (bold) |
| **Colour** | `#374151` (grey-700) |
| **Transform** | Uppercase |

### Visual Example

```
        INNOVATION
    ╭┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄╮
    ┆                       ┆
    ┆  ╭───────────╮        ┆
    ┆  │ disruption│        ┆
    ┆  ╰─────┬─────╯        ┆
    ┆        │              ┆
    ┆  ╭─────┴─────╮        ┆
    ┆  │ iteration │        ┆
    ┆  ╰───────────╯        ┆
    ┆                       ┆
    ╰┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄╯
```

---

## Animation

### Philosophy

Animations should feel like **drawing**, not **appearing**.

### Node Entry Animation

When a new node is added:

```
Frame 0:   scale(0), opacity(0)
Frame 1-5: scale(0 → 1.1), opacity(0 → 1)   [overshoot]
Frame 6-8: scale(1.1 → 1.0)                  [settle]
```

**Duration:** 300ms
**Easing:** `cubic-bezier(0.34, 1.56, 0.64, 1)` (spring-like)

### Edge Entry Animation

When a new edge is added:

```
Frame 0:   stroke-dashoffset: 100%
Frame 1-n: stroke-dashoffset: 100% → 0%     [draws in]
```

**Duration:** 400ms
**Easing:** `ease-out`

This creates the effect of a pen drawing the connection.

### Node State Change (Ghost → Solid)

```
Stroke colour: grey → black
Border style: dashed → solid
Duration: 200ms
```

### Flower Formation

When nodes cluster into a Flower:

```
1. Flower container fades in (200ms)
2. Nodes animate to new positions (500ms, FCose layout)
3. Flower label fades in (200ms)
```

---

## Layout (FCose)

### Updated Configuration

```javascript
{
  name: 'fcose',
  quality: 'proof',
  animate: true,
  animationDuration: 500,
  animationEasing: 'ease-out',
  fit: false,
  randomize: false,
  
  // Spacing for cleaner visual
  nodeRepulsion: 5500,        // Increased from 4500
  idealEdgeLength: 120,       // Increased from 100
  edgeElasticity: 0.45,
  
  // Compound node (Flower) handling
  nestingFactor: 0.1,
  gravity: 0.2,               // Slightly reduced
  gravityRangeCompound: 1.5,
  gravityCompound: 1.0,
  
  // Iterations
  numIter: 2500,
  
  // Padding
  tilingPaddingVertical: 20,  // Increased
  tilingPaddingHorizontal: 20
}
```

### Incremental Layout

On new nodes/edges, run layout with `fit: false` to preserve viewport position.

---

## Cytoscape Stylesheet (Complete)

```javascript
const stylesheet = [
  // Base node style
  {
    selector: 'node',
    style: {
      'shape': 'roundrectangle',
      'width': 'label',
      'height': 'label',
      'padding': '12px',
      'background-color': '#FFFFFF',
      'border-width': 2,
      'border-color': '#1A1A1A',
      'border-style': 'solid',
      'label': 'data(label)',
      'text-valign': 'center',
      'text-halign': 'center',
      'font-family': 'Nunito, system-ui, sans-serif',
      'font-size': '14px',
      'font-weight': 600,
      'color': '#1A1A1A',
      'text-max-width': '140px',
      'text-wrap': 'ellipsis'
    }
  },
  
  // Ghost node (unconfirmed)
  {
    selector: 'node.ghost',
    style: {
      'opacity': 0.7,
      'border-color': '#9CA3AF',
      'border-style': 'dashed'
    }
  },
  
  // Solid node (confirmed)
  {
    selector: 'node.solid',
    style: {
      'opacity': 1,
      'border-color': '#1A1A1A',
      'border-style': 'solid'
    }
  },
  
  // Stem node (Flower centre)
  {
    selector: 'node.stem',
    style: {
      'border-color': '#F97316',  // Accent
      'border-width': 3
    }
  },
  
  // Selected node
  {
    selector: 'node:selected',
    style: {
      'border-color': '#F97316',
      'border-width': 3,
      'background-color': '#FFF7ED'
    }
  },
  
  // Flower (compound node container)
  {
    selector: 'node.flower',
    style: {
      'shape': 'roundrectangle',
      'background-color': '#F9FAFB',
      'border-color': '#E5E7EB',
      'border-width': 1,
      'border-style': 'dashed',
      'padding': '20px',
      'text-valign': 'top',
      'text-halign': 'center',
      'text-margin-y': -10,
      'font-size': '16px',
      'font-weight': 700,
      'color': '#374151',
      'text-transform': 'uppercase'
    }
  },
  
  // Edge style
  {
    selector: 'edge',
    style: {
      'width': 2,
      'line-color': '#6B7280',
      'target-arrow-color': '#6B7280',
      'target-arrow-shape': 'triangle',
      'arrow-scale': 0.8,
      'curve-style': 'bezier',
      'label': 'data(description)',
      'font-size': '11px',
      'font-family': 'Nunito, system-ui, sans-serif',
      'color': '#6B7280',
      'text-background-color': '#FFFFFF',
      'text-background-opacity': 0.8,
      'text-background-padding': '2px'
    }
  },
  
  // Bridge edge (cross-flower)
  {
    selector: 'edge.bridge',
    style: {
      'width': 3,
      'line-style': 'dashed'
    }
  }
];
```

---

## Global CSS Updates

### `globals.css`

```css
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&display=swap');

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: 'Nunito', system-ui, -apple-system, sans-serif;
  background-color: #FFFFFF;
  color: #1A1A1A;
}

/* Canvas container */
.graph-canvas {
  background-color: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
}
```

---

## UI Components

### Buttons

| Type | Background | Text | Border |
|------|------------|------|--------|
| Primary | `#F97316` (accent) | `#FFFFFF` | None |
| Secondary | `#FFFFFF` | `#1A1A1A` | `#E5E7EB` |
| Ghost | Transparent | `#6B7280` | None |

### Cards/Panels

| Property | Value |
|----------|-------|
| Background | `#FFFFFF` |
| Border | `#E5E7EB`, 1px |
| Border radius | 8px |
| Shadow | `0 1px 3px rgba(0,0,0,0.1)` |

---

## Summary: Key Differences from Original Spec

| Original Spec | Updated (RSA Animate) |
|---------------|----------------------|
| Dark background | **White canvas** |
| 5 edge colours by category | **Single grey for all edges** |
| Standard node appearance | **Rounded, hand-drawn feel** |
| Nodes appear instantly | **Draw-in animation** |
| Clinical graph look | **Whiteboard sketch feel** |

---

## Checklist for Gate 4 Implementation

- [ ] Import Nunito font
- [ ] Update `globals.css` to white theme
- [ ] Implement Cytoscape stylesheet as specified
- [ ] Node entry animation (scale + fade)
- [ ] Edge entry animation (draw-in effect)
- [ ] Ghost/solid state transitions
- [ ] Flower container styling
- [ ] Stem node highlighting
- [ ] FCose layout with updated parameters

---

## Reference

- **RSA Animate YouTube:** Search "RSA Animate" for inspiration
- **Excalidraw:** Reference for hand-drawn aesthetic
- **Accent colour tool:** coolors.co for palette generation

---

*Visual design specification for plasticFlower. December 2025.*



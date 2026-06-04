# AntV G6 Graph Visualization Documentation

## Overview
AntV G6 is a high-performance graph visualization engine developed by AntV (Ant Group). It provides comprehensive capabilities for rendering, analyzing, and interacting with graph data, supporting everything from simple network diagrams to complex relationship visualizations with thousands of nodes.

## Core Capabilities

### Visualization Features
- **High Performance**: WebGL-powered rendering for large graphs (10,000+ nodes)
- **Rich Layouts**: 15+ built-in layout algorithms (force, tree, circular, etc.)
- **Custom Rendering**: Flexible node/edge styling with data-driven properties
- **Animations**: Smooth transitions for layout changes and interactions
- **Responsive**: Auto-fit and viewport management

### Interaction
- **Drag & Drop**: Canvas panning, node dragging, zoom control
- **Selection**: Single/multi-select nodes and edges
- **Hover States**: Dynamic styling on mouse events
- **Context Menus**: Right-click interactions
- **Keyboard Shortcuts**: Accessibility support

### Analysis
- **Graph Algorithms**: Shortest path, clustering, centrality
- **Data Filtering**: Show/hide based on properties
- **Hierarchical Visualization**: Collapsible tree structures
- **Combo Nodes**: Group related nodes visually

## Installation

### NPM

```bash
npm install @antv/g6
```

### CDN

```html
<script src="https://unpkg.com/@antv/g6/dist/g6.min.js"></script>
```

## Basic Usage

### Initialize a Simple Graph

```typescript
import { Graph } from '@antv/g6';

const graph = new Graph({
  container: 'container',
  width: 800,
  height: 600,
  data: {
    nodes: [
      { id: 'node-1', data: { name: 'Alice' }, style: { x: 100, y: 100 } },
      { id: 'node-2', data: { name: 'Bob' }, style: { x: 300, y: 100 } },
      { id: 'node-3', data: { name: 'Charlie' }, style: { x: 200, y: 300 } }
    ],
    edges: [
      { source: 'node-1', target: 'node-2', data: { weight: 5 } },
      { source: 'node-2', target: 'node-3', data: { weight: 3 } }
    ]
  },
  node: {
    type: 'circle',
    style: {
      size: 40,
      fill: '#5B8FF9',
      stroke: '#5B8FF9',
      lineWidth: 2,
      labelText: (datum) => datum.data.name,
      labelFill: '#000',
      labelFontSize: 12
    }
  },
  edge: {
    type: 'line',
    style: {
      stroke: '#e2e2e2',
      lineWidth: 2,
      endArrow: true
    }
  },
  layout: {
    type: 'force',
    animated: true,
    linkDistance: 100
  },
  behaviors: ['drag-canvas', 'zoom-canvas', 'drag-element']
});

await graph.render();
```

### HTML Container

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>G6 Graph</title>
</head>
<body>
  <div id="container"></div>
  <script type="module" src="./graph.js"></script>
</body>
</html>
```

## Layout Algorithms

### Force-Directed Layout

```typescript
graph.setLayout({
  type: 'force',
  animated: true,
  linkDistance: 100,
  nodeStrength: 30,
  edgeStrength: 0.1,
  collideStrength: 0.8,
  alpha: 0.3,
  alphaDecay: 0.028,
  alphaMin: 0.01,
  onTick: () => {
    console.log('Layout tick');
  }
});
await graph.layout();
```

**Use Cases:**
- Social networks
- Dependency graphs
- General network visualization

### Hierarchical (Dagre) Layout

```typescript
graph.setLayout({
  type: 'dagre',
  rankdir: 'TB', // Top to bottom: TB, BT, LR, RL
  align: 'UL',
  nodesep: 20,
  ranksep: 50,
  controlPoints: true
});
await graph.layout();
```

**Use Cases:**
- Flowcharts
- Organizational charts
- Directed acyclic graphs (DAGs)

### Circular Layout

```typescript
graph.setLayout({
  type: 'circular',
  radius: 200,
  startAngle: 0,
  endAngle: 2 * Math.PI,
  divisions: 5,
  ordering: 'topology'
});
await graph.layout();
```

**Use Cases:**
- Cycle detection
- Periodic relationships
- Evenly distributed networks

### Radial Layout

```typescript
graph.setLayout({
  type: 'radial',
  unitRadius: 100,
  linkDistance: 100,
  focusNode: 'node-1',
  preventOverlap: true,
  nodeSize: 40,
  nodeSpacing: 10
});
await graph.layout();
```

**Use Cases:**
- Ego networks (focus on single node)
- Hub-and-spoke visualizations
- Social circles

### Grid Layout

```typescript
graph.setLayout({
  type: 'grid',
  begin: [0, 0],
  preventOverlap: true,
  preventOverlapPadding: 10,
  rows: 5,
  cols: 5,
  sortBy: 'degree'
});
await graph.layout();
```

**Use Cases:**
- Matrix visualizations
- Regular structures
- Categorical grouping

### Tree Layouts

```typescript
// Compact Box (Standard Tree)
graph.setLayout({
  type: 'compactBox',
  direction: 'TB',
  getHeight: () => 32,
  getWidth: () => 32,
  getVGap: () => 10,
  getHGap: () => 50
});

// Indented Tree
graph.setLayout({
  type: 'indented',
  direction: 'LR',
  isHorizontal: true,
  indent: 40,
  getHeight: () => 20,
  getVGap: () => 10
});

// Mindmap Layout
graph.setLayout({
  type: 'mindmap',
  direction: 'H',
  getHeight: () => 32,
  getWidth: () => 32,
  getVGap: () => 10,
  getHGap: () => 50,
  getSide: (node) => node.data.side || 'right'
});
```

**Use Cases:**
- File systems
- Organization hierarchies
- Decision trees
- Mind maps

### D3 Force Layout

```javascript
import { Graph } from '@antv/g6';

fetch('https://assets.antv.antgroup.com/g6/cluster.json')
  .then((res) => res.json())
  .then((data) => {
    const graph = new Graph({
      container: 'container',
      data,
      node: {
        style: {
          labelText: (d) => d.id,
          ports: [],
        },
        palette: {
          type: 'group',
          field: 'cluster',
        },
      },
      layout: {
        type: 'd3-force',
        collide: {
          strength: 0.5,
        },
      },
      behaviors: ['zoom-canvas', 'drag-canvas'],
    });

    graph.render();
  });
```

### Combined Layouts

```typescript
// Apply different layouts to different node groups
graph.setLayout([
  {
    type: 'grid',
    nodeFilter: (node) => node.data.type === 'main',
    rows: 1,
  },
  {
    type: 'circle',
    nodeFilter: (node) => node.data.type === 'sub',
    radius: 100,
  },
]);

await graph.layout();
```

### Pipeline Layouts

```typescript
// Execute layouts in sequence
graph.setLayout([
  { type: 'circular', radius: 200 },
  { type: 'force', iterations: 100, animated: true }
]);
await graph.layout();
```

### Layout Control

```typescript
// Stop iterative layouts (force, fruchterman)
graph.stopLayout();

// Get current layout config
const layoutConfig = graph.getLayout();
```

## Styling

### Node Styling

```typescript
const graph = new Graph({
  node: {
    type: 'circle',
    style: {
      size: 40,
      fill: '#5B8FF9',
      stroke: '#fff',
      lineWidth: 2,
      
      // Label
      labelText: (datum) => datum.data.name,
      labelFill: '#000',
      labelFontSize: 12,
      labelBackground: true,
      labelBackgroundFill: '#fff',
      labelBackgroundRadius: 4,
      labelPadding: [2, 4],
      
      // Icons/Badges
      iconText: '👤',
      iconFontSize: 20,
      
      // Data-driven styling
      fill: (datum) => datum.data.category === 'vip' ? '#FF4136' : '#5B8FF9',
      size: (datum) => datum.data.importance * 10,
    },
    
    // State styles
    state: {
      selected: {
        lineWidth: 4,
        stroke: '#FFD700',
      },
      active: {
        fill: '#FF6B6B',
      },
      inactive: {
        opacity: 0.3,
      },
    }
  }
});
```

### Edge Styling

```typescript
const graph = new Graph({
  edge: {
    type: 'line', // line, polyline, cubic, quadratic
    style: {
      stroke: '#e2e2e2',
      lineWidth: 2,
      
      // Arrows
      endArrow: true,
      startArrow: false,
      endArrowType: 'triangle', // triangle, circle, diamond
      
      // Labels
      labelText: (datum) => datum.data.weight,
      labelFill: '#666',
      labelFontSize: 10,
      labelBackground: true,
      
      // Data-driven
      stroke: (datum) => datum.data.type === 'strong' ? '#FF4136' : '#e2e2e2',
      lineWidth: (datum) => datum.data.weight || 1,
      lineDash: (datum) => datum.data.style === 'dashed' ? [5, 5] : undefined,
    },
    
    state: {
      active: {
        stroke: '#1890FF',
        lineWidth: 3,
      },
    }
  }
});
```

### Color Palettes

```typescript
node: {
  palette: {
    type: 'group',
    field: 'cluster', // Color by cluster
    color: 'tableau', // tableau, pastel, bright, dark, etc.
  }
}
```

### Custom Shapes

```typescript
import { Graph, Extensions } from '@antv/g6';

// Register custom node type
Extensions.registerNode(
  'custom-node',
  {
    draw(model, shapeMap, diffData, diffState) {
      const { data, id } = model;
      const container = this.upsertShape(
        'group',
        'container',
        {},
        {
          shapeMap,
          model,
        }
      );
      
      // Draw circle
      this.upsertShape(
        'circle',
        'key-shape',
        {
          r: 20,
          fill: data.color,
          stroke: '#fff',
          lineWidth: 2,
        },
        {
          shapeMap,
          model,
          parent: container,
        }
      );
      
      // Draw label
      this.upsertShape(
        'text',
        'label-shape',
        {
          text: data.name,
          y: 30,
          textAlign: 'center',
          fill: '#000',
        },
        {
          shapeMap,
          model,
          parent: container,
        }
      );
      
      return container;
    },
  },
  'circle'
);

// Use custom node
const graph = new Graph({
  node: {
    type: 'custom-node',
  },
});
```

## Interactions & Events

### Node Events

```typescript
import { GraphEvent, NodeEvent } from '@antv/g6';

// Click event
graph.on('node:click', (event) => {
  const nodeId = event.target.id;
  console.log('Node clicked:', nodeId);
  graph.setElementState(nodeId, 'selected', true);
});

// Double-click to focus
graph.on('node:dblclick', async (event) => {
  await graph.focusElement(event.target.id, { duration: 300 });
});

// Hover effects
graph.on('node:pointerover', (event) => {
  graph.setElementState(event.target.id, 'active', true);
  event.view.style.cursor = 'pointer';
});

graph.on('node:pointerout', (event) => {
  graph.setElementState(event.target.id, [], true);
  event.view.style.cursor = 'default';
});

// Drag events
graph.on('node:dragstart', (event) => {
  console.log('Drag started:', event.target.id);
});

graph.on('node:drag', (event) => {
  console.log('Dragging:', event.target.id, event.dx, event.dy);
});

graph.on('node:dragend', (event) => {
  console.log('Drag ended:', event.target.id);
  // Update position in data
  const position = graph.getElementPosition(event.target.id);
  graph.updateNodeData({
    id: event.target.id,
    style: { x: position[0], y: position[1] }
  });
});
```

### Edge Events

```typescript
graph.on('edge:click', (event) => {
  const edge = event.target;
  console.log('Edge clicked:', edge.id, edge.source, edge.target);
});

graph.on('edge:pointerover', (event) => {
  graph.setElementState(event.target.id, 'active', true);
});
```

### Canvas Events

```typescript
graph.on('canvas:click', (event) => {
  console.log('Canvas clicked at:', event.canvas.x, event.canvas.y);
  // Clear all selections
  const selected = graph.getElementDataByState('node', 'selected');
  selected.forEach(node => {
    graph.setElementState(node.id, [], false);
  });
});

graph.on('canvas:contextmenu', (event) => {
  event.preventDefault();
  console.log('Right-clicked canvas');
});
```

### Graph Lifecycle Events

```typescript
graph.on(GraphEvent.BEFORE_RENDER, () => {
  console.log('About to render...');
});

graph.on(GraphEvent.AFTER_RENDER, () => {
  console.log('Rendering complete');
});

graph.on(GraphEvent.BEFORE_LAYOUT, () => {
  console.log('Layout starting...');
});

graph.on(GraphEvent.AFTER_LAYOUT, () => {
  console.log('Layout complete');
});

graph.on(GraphEvent.AFTER_TRANSFORM, () => {
  const zoom = graph.getZoom();
  console.log('Viewport changed, zoom:', zoom);
});
```

### Remove Event Listeners

```typescript
// Remove specific handler
const handler = (event) => console.log('Node clicked:', event.target.id);
graph.on('node:click', handler);
graph.off('node:click', handler);

// Remove all listeners for an event
graph.off('node:click');

// Remove all event listeners
graph.off();
```

### One-Time Events

```typescript
graph.once('afterrender', () => {
  console.log('First render complete');
  graph.fitView();
});
```

## Behaviors

### Built-in Behaviors

```typescript
const graph = new Graph({
  behaviors: [
    'drag-canvas',      // Pan canvas
    'zoom-canvas',      // Zoom with mouse wheel
    'drag-element',     // Drag nodes
    'click-select',     // Select on click
    'hover-activate',   // Hover to activate
    'brush-select',     // Box selection
    'collapse-expand',  // Collapse/expand combos
    'scroll-canvas',    // Scroll to pan
  ]
});
```

### Custom Behavior Configuration

```typescript
behaviors: [
  {
    type: 'drag-canvas',
    enableOptimize: true, // Performance optimization
  },
  {
    type: 'zoom-canvas',
    sensitivity: 0.5,
    minZoom: 0.1,
    maxZoom: 10,
  },
  {
    type: 'click-select',
    multiple: true, // Allow multi-select with Ctrl/Cmd
    trigger: 'shift', // Require Shift key
  },
]
```

## Data Operations

### Add Data

```typescript
// Add nodes
graph.addData({
  nodes: [
    { id: 'new-node-1', data: { name: 'New Node 1' } },
    { id: 'new-node-2', data: { name: 'New Node 2' } }
  ]
});

// Add edges
graph.addData({
  edges: [
    { source: 'node-1', target: 'new-node-1' }
  ]
});

// Render changes
await graph.draw();
await graph.layout();
```

### Update Data

```typescript
// Update node properties
graph.updateNodeData({
  id: 'node-1',
  data: { name: 'Updated Name', value: 100 },
  style: { fill: '#FF4136' }
});

// Update edge properties
graph.updateEdgeData({
  id: 'edge-1',
  data: { weight: 10 },
  style: { lineWidth: 3 }
});

await graph.draw();
```

### Remove Data

```typescript
// Remove nodes (also removes connected edges)
graph.removeData({
  nodes: ['node-1', 'node-2']
});

// Remove edges
graph.removeData({
  edges: ['edge-1']
});

await graph.draw();
```

### Get Data

```typescript
// Get all data
const data = graph.getData();

// Get node data
const nodeData = graph.getNodeData('node-1');

// Get edge data
const edgeData = graph.getEdgeData('edge-1');

// Get nodes by state
const selectedNodes = graph.getElementDataByState('node', 'selected');
```

## Viewport Control

### Zoom

```typescript
// Zoom to specific level
graph.zoomTo(1.5);

// Zoom by factor
graph.zoomBy(1.2); // Zoom in 20%

// Zoom with animation
graph.zoomBy(1.2, { duration: 500, easing: 'linear' });

// Get current zoom
const zoom = graph.getZoom();
```

### Pan

```typescript
// Pan to coordinates
graph.panTo(100, 200);

// Pan by offset
graph.panBy(50, 50);

// Get current pan
const [x, y] = graph.getPan();
```

### Fit View

```typescript
// Fit all elements to viewport
graph.fitView();

// Fit with padding
graph.fitView({ padding: 20 });

// Fit specific elements
graph.fitView({
  ids: ['node-1', 'node-2', 'edge-1'],
  padding: 40
});
```

### Focus Element

```typescript
// Center on specific element
await graph.focusElement('node-1', {
  duration: 300,
  easing: 'ease-in-out'
});
```

## Combos (Grouping)

### Define Combos

```typescript
const graph = new Graph({
  data: {
    nodes: [
      { id: 'node1', combo: 'combo1' },
      { id: 'node2', combo: 'combo1' },
      { id: 'node3', combo: 'combo2' },
    ],
    combos: [
      { id: 'combo1', data: { label: 'Group 1' } },
      { id: 'combo2', data: { label: 'Group 2' } },
    ]
  },
  combo: {
    type: 'circle',
    style: {
      fill: '#F0F0F0',
      stroke: '#999',
      lineWidth: 2,
      labelText: (d) => d.data.label,
      labelFill: '#000',
    }
  },
  behaviors: ['drag-element', 'collapse-expand']
});
```

### Nested Combos

```typescript
combos: [
  { id: 'combo1', data: { label: 'Parent Group' } },
  { id: 'combo2', combo: 'combo1', data: { label: 'Child Group' } },
]
```

### Collapse/Expand

```typescript
// Collapse combo
graph.collapseCombo('combo1');

// Expand combo
graph.expandCombo('combo1');

// Toggle
graph.toggleCombo('combo1');
```

## Plugins

### Built-in Plugins

```typescript
import { Graph } from '@antv/g6';

const graph = new Graph({
  plugins: [
    {
      type: 'grid-line',
      follow: true, // Grid follows viewport
    },
    {
      type: 'minimap',
      container: 'minimap-container',
      size: [200, 150],
    },
    {
      type: 'toolbar',
      position: 'top-left',
      items: [
        { id: 'zoomIn', value: 'zoom-in', icon: '🔍+' },
        { id: 'zoomOut', value: 'zoom-out', icon: '🔍-' },
        { id: 'fitView', value: 'fit-view', icon: '📐' },
      ],
    },
    {
      type: 'tooltip',
      getContent: (event, items) => {
        return `<div>Node: ${items[0].data.name}</div>`;
      },
    },
  ]
});
```

## Performance Optimization

### Large Graphs

```typescript
const graph = new Graph({
  // Enable WebGL renderer for 1000+ nodes
  renderer: 'webgl',
  
  // Optimize rendering
  enableOptimize: true,
  
  // LOD (Level of Detail)
  enableLod: true,
  
  // Disable animations for large datasets
  animation: false,
  
  // Limit edge rendering during interaction
  modes: {
    default: [{
      type: 'drag-canvas',
      enableOptimize: true, // Hide edges while dragging
    }]
  }
});
```

### Lazy Rendering

```typescript
// Load data incrementally
async function loadLargeGraph() {
  const batchSize = 100;
  for (let i = 0; i < totalNodes; i += batchSize) {
    const batch = fetchBatch(i, batchSize);
    graph.addData(batch);
    await graph.draw();
    await delay(10); // Prevent UI blocking
  }
  await graph.layout();
}
```

## React Integration

### React Component

```tsx
import React, { useEffect, useRef } from 'react';
import { Graph } from '@antv/g6';

interface G6GraphProps {
  data: any;
  layout?: any;
}

const G6Graph: React.FC<G6GraphProps> = ({ data, layout }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<Graph | null>(null);
  
  useEffect(() => {
    if (!containerRef.current) return;
    
    const graph = new Graph({
      container: containerRef.current,
      width: containerRef.current.offsetWidth,
      height: containerRef.current.offsetHeight,
      data,
      layout: layout || { type: 'force' },
      node: {
        style: {
          labelText: (d: any) => d.id,
        }
      },
      behaviors: ['drag-canvas', 'zoom-canvas', 'drag-element']
    });
    
    graph.render();
    graphRef.current = graph;
    
    return () => {
      graph.destroy();
    };
  }, []);
  
  useEffect(() => {
    if (graphRef.current) {
      graphRef.current.updateData(data);
      graphRef.current.render();
    }
  }, [data]);
  
  return <div ref={containerRef} style={{ width: '100%', height: '600px' }} />;
};

export default G6Graph;
```

## Best Practices

1. **Layout Selection**: Use force layouts for general networks, tree layouts for hierarchies, circular for cycles
2. **Performance**: Enable WebGL renderer for 1000+ nodes
3. **Interactions**: Always provide drag-canvas and zoom-canvas behaviors
4. **Responsiveness**: Use `autoFit: 'view'` for automatic sizing
5. **State Management**: Use `setElementState` for temporary visual changes, `updateNodeData` for persistent changes
6. **Memory**: Call `graph.destroy()` when unmounting components
7. **Animation**: Disable for large graphs to improve performance
8. **Labels**: Truncate or hide labels for dense graphs

## Resources

- **Official Website**: https://g6.antv.antgroup.com/
- **Documentation**: https://g6.antv.antgroup.com/manual/introduction
- **API Reference**: https://g6.antv.antgroup.com/api
- **Examples**: https://g6.antv.antgroup.com/examples
- **GitHub**: https://github.com/antvis/g6
- **Community**: https://github.com/antvis/g6/discussions






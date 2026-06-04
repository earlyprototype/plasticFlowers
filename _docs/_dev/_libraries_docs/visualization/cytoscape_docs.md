# Cytoscape.js Documentation

## Overview
Cytoscape.js is a fully-featured graph theory library for visualising and analysing relational data. Written in JavaScript, it provides a robust foundation for building interactive network visualisations in web applications, supporting everything from biological networks to social graphs.

## Core Capabilities

### Graph Visualisation
- **Flexible Layout Algorithms**: Grid, circle, concentric, breadthfirst, cose (force-directed), and more
- **Styling Engine**: CSS-like selectors for nodes and edges
- **Interactive**: Pan, zoom, tap, grab, and custom gestures
- **Extensible**: Plugin architecture for custom layouts and features
- **Mobile Optimised**: Touch event support

### Data Model
- **Nodes & Edges**: First-class graph primitives
- **Collections**: Powerful API for querying graph elements
- **Data Binding**: Associate arbitrary data with elements
- **Classes**: Dynamic styling via CSS-like classes

## Installation

### NPM

```bash
npm install cytoscape
```

### Usage in Node.js/React

```javascript
import cytoscape from 'cytoscape';

const cy = cytoscape({
  container: document.getElementById('cy'),
  elements: [
    { data: { id: 'a' } },
    { data: { id: 'b' } },
    { data: { id: 'ab', source: 'a', target: 'b' } }
  ],
  style: [
    {
      selector: 'node',
      style: {
        'background-color': '#666',
        'label': 'data(id)'
      }
    }
  ]
});
```

### CDN

```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.28.1/cytoscape.min.js"></script>

<div id="cy" style="width: 100%; height: 600px;"></div>

<script>
  const cy = cytoscape({
    container: document.getElementById('cy'),
    elements: [...],
    style: [...]
  });
</script>
```

## Basic Usage

### Create Graph

```javascript
const cy = cytoscape({
  container: document.getElementById('cy'),
  
  elements: {
    nodes: [
      { data: { id: 'j', name: 'Jerry' } },
      { data: { id: 'e', name: 'Elaine' } },
      { data: { id: 'k', name: 'Kramer' } },
      { data: { id: 'g', name: 'George' } }
    ],
    edges: [
      { data: { source: 'j', target: 'e' } },
      { data: { source: 'j', target: 'k' } },
      { data: { source: 'j', target: 'g' } },
      { data: { source: 'e', target: 'k' } }
    ]
  },
  
  style: [
    {
      selector: 'node',
      style: {
        'background-color': '#0074D9',
        'label': 'data(name)',
        'color': '#fff',
        'text-valign': 'center',
        'text-halign': 'center'
      }
    },
    {
      selector: 'edge',
      style: {
        'width': 3,
        'line-color': '#ccc',
        'target-arrow-color': '#ccc',
        'target-arrow-shape': 'triangle',
        'curve-style': 'bezier'
      }
    }
  ],
  
  layout: {
    name: 'circle'
  }
});
```

### Add Elements Dynamically

```javascript
// Add nodes
cy.add([
  { group: 'nodes', data: { id: 'n1' } },
  { group: 'nodes', data: { id: 'n2' } }
]);

// Add edges
cy.add({
  group: 'edges',
  data: { id: 'e1', source: 'n1', target: 'n2' }
});

// Batch operations
cy.batch(() => {
  cy.add({ data: { id: 'n3' } });
  cy.add({ data: { id: 'n4' } });
  cy.add({ data: { id: 'e2', source: 'n3', target: 'n4' } });
});
```

## Layouts

### Built-in Layouts

```javascript
// Grid layout
cy.layout({
  name: 'grid',
  rows: 3
}).run();

// Circle layout
cy.layout({
  name: 'circle'
}).run();

// Force-directed (CoSE)
cy.layout({
  name: 'cose',
  idealEdgeLength: 100,
  nodeOverlap: 20,
  refresh: 20,
  fit: true,
  padding: 30,
  randomize: false,
  componentSpacing: 100,
  nodeRepulsion: 400000,
  edgeElasticity: 100,
  nestingFactor: 5
}).run();

// Breadthfirst (hierarchical)
cy.layout({
  name: 'breadthfirst',
  directed: true,
  padding: 10
}).run();

// Concentric circles
cy.layout({
  name: 'concentric',
  concentric: function(node) {
    return node.degree();
  },
  levelWidth: function(nodes) {
    return 2;
  }
}).run();
```

### Custom Layout Animation

```javascript
const layout = cy.layout({
  name: 'cose',
  animate: true,
  animationDuration: 1000,
  animationEasing: 'ease-out'
});

layout.on('layoutstop', () => {
  console.log('Layout complete');
});

layout.run();
```

## Styling

### CSS-like Selectors

```javascript
cy.style()
  .selector('node')
    .style({
      'background-color': '#0074D9',
      'label': 'data(name)',
      'width': '40px',
      'height': '40px'
    })
  .selector('node:selected')
    .style({
      'border-width': '3px',
      'border-color': '#FFD700'
    })
  .selector('edge')
    .style({
      'width': 2,
      'line-color': '#ccc',
      'target-arrow-shape': 'triangle',
      'curve-style': 'bezier'
    })
  .selector('.highlighted')
    .style({
      'background-color': '#FF4136',
      'line-color': '#FF4136'
    })
  .update();
```

### Dynamic Styling

```javascript
// Add classes
cy.$('#node1').addClass('highlighted');

// Remove classes
cy.$('#node2').removeClass('highlighted');

// Toggle classes
cy.$('.group').toggleClass('selected');

// Set style directly
cy.$('#node3').style('background-color', 'red');
```

## Selectors & Collections

### Query Elements

```javascript
// All nodes
cy.nodes();

// All edges
cy.edges();

// By ID
cy.$('#node1');

// By class
cy.$('.highlighted');

// By data attribute
cy.$('[name = "Jerry"]');

// Compound selectors
cy.$('node[degree > 2]');

// Edges from specific node
cy.$('#j').connectedEdges();

// Neighbours
cy.$('#j').neighborhood();
```

### Collection Operations

```javascript
const nodes = cy.nodes();

// Filter
const filtered = nodes.filter('[degree > 2]');

// Map
const ids = nodes.map(node => node.id());

// Iterate
nodes.forEach(node => {
  console.log(node.data('name'));
});

// Union
const combined = cy.$('#a').union(cy.$('#b'));

// Difference
const diff = cy.nodes().difference(cy.$('.hidden'));
```

## Events

### Element Events

```javascript
// Tap (click) event
cy.on('tap', 'node', function(evt) {
  const node = evt.target;
  console.log('Tapped ' + node.id());
});

// Mouse over
cy.on('mouseover', 'node', function(evt) {
  evt.target.addClass('highlighted');
});

cy.on('mouseout', 'node', function(evt) {
  evt.target.removeClass('highlighted');
});

// Select/unselect
cy.on('select', 'node', function(evt) {
  console.log('Selected:', evt.target.id());
});
```

### Graph Events

```javascript
// Pan/zoom
cy.on('zoom', function(evt) {
  console.log('Zoom level:', cy.zoom());
});

cy.on('pan', function(evt) {
  console.log('Pan position:', cy.pan());
});

// Add/remove elements
cy.on('add', 'node', function(evt) {
  console.log('Node added:', evt.target.id());
});

cy.on('remove', function(evt) {
  console.log('Element removed');
});
```

## Graph Analysis

### Algorithms

```javascript
// Breadth-first search
const bfs = cy.elements().bfs({
  roots: '#j',
  visit: function(v, e, u, i, depth) {
    console.log('Visited:', v.id(), 'at depth', depth);
  }
});

// Depth-first search
const dfs = cy.elements().dfs({
  roots: '#j',
  visit: function(v, e, u, i, depth) {
    console.log('Visited:', v.id());
  }
});

// Shortest path (Dijkstra)
const dijkstra = cy.elements().dijkstra('#a', function(edge) {
  return edge.data('weight');
});

const pathToB = dijkstra.pathTo(cy.$('#b'));
const distToB = dijkstra.distanceTo(cy.$('#b'));

// A* algorithm
const aStar = cy.elements().aStar({
  root: '#a',
  goal: '#b',
  weight: edge => edge.data('weight')
});

console.log('Path:', aStar.path);
console.log('Distance:', aStar.distance);
```

### Centrality & Metrics

```javascript
// PageRank
const pageRank = cy.elements().pageRank();
cy.nodes().forEach(node => {
  console.log(node.id(), pageRank.rank(node));
});

// Betweenness centrality
const bc = cy.elements().betweennessCentrality();
cy.nodes().forEach(node => {
  console.log(node.id(), bc.betweenness(node));
});

// Degree centrality
cy.nodes().forEach(node => {
  console.log(node.id(), 'degree:', node.degree());
});

// Connected components
const components = cy.elements().components();
console.log('Number of components:', components.length);
```

## React Integration

### React Component

```jsx
import React, { useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';

function CytoscapeGraph({ elements, style, layout }) {
  const cyRef = useRef(null);
  const containerRef = useRef(null);
  
  useEffect(() => {
    cyRef.current = cytoscape({
      container: containerRef.current,
      elements,
      style,
      layout: layout || { name: 'cose' }
    });
    
    return () => {
      cyRef.current.destroy();
    };
  }, []);
  
  useEffect(() => {
    if (cyRef.current) {
      cyRef.current.json({ elements });
      cyRef.current.layout(layout || { name: 'cose' }).run();
    }
  }, [elements, layout]);
  
  return <div ref={containerRef} style={{ width: '100%', height: '600px' }} />;
}

export default CytoscapeGraph;
```

### Usage

```jsx
function App() {
  const elements = [
    { data: { id: 'a', label: 'Node A' } },
    { data: { id: 'b', label: 'Node B' } },
    { data: { id: 'ab', source: 'a', target: 'b' } }
  ];
  
  const style = [
    {
      selector: 'node',
      style: {
        'background-color': '#0074D9',
        'label': 'data(label)'
      }
    }
  ];
  
  return <CytoscapeGraph elements={elements} style={style} />;
}
```

## Extensions & Plugins

### Popular Extensions

```bash
# Layout extensions
npm install cytoscape-dagre  # Hierarchical layout
npm install cytoscape-cola   # Constraint-based layout
npm install cytoscape-elk    # Eclipse Layout Kernel

# UI extensions
npm install cytoscape-context-menus  # Context menus
npm install cytoscape-panzoom        # Pan/zoom UI
npm install cytoscape-navigator      # Bird's eye view

# Analysis
npm install cytoscape-graph-ml       # GraphML import/export
npm install cytoscape-cise           # Circular layout
```

### Using Extensions

```javascript
import cytoscape from 'cytoscape';
import dagre from 'cytoscape-dagre';
import contextMenus from 'cytoscape-context-menus';
import 'cytoscape-context-menus/cytoscape-context-menus.css';

// Register extensions
cytoscape.use(dagre);
cytoscape.use(contextMenus);

const cy = cytoscape({ /* ... */ });

// Use dagre layout
cy.layout({ name: 'dagre' }).run();

// Add context menu
cy.contextMenus({
  menuItems: [
    {
      id: 'remove',
      content: 'Remove',
      selector: 'node, edge',
      onClickFunction: function(event) {
        event.target.remove();
      }
    },
    {
      id: 'hide',
      content: 'Hide',
      selector: 'node',
      onClickFunction: function(event) {
        event.target.style('display', 'none');
      }
    }
  ]
});
```

## Export & Import

### Export Graph Image

```javascript
// Export as PNG
const png64 = cy.png({
  output: 'base64uri',
  bg: 'white',
  full: true,
  scale: 2
});

// Download PNG
const a = document.createElement('a');
a.href = png64;
a.download = 'graph.png';
a.click();

// Export as JPEG
const jpg = cy.jpg({
  output: 'blob',
  bg: '#f0f0f0'
});
```

### Export/Import JSON

```javascript
// Export graph state
const json = cy.json();
localStorage.setItem('graph', JSON.stringify(json));

// Import graph state
const savedJson = JSON.parse(localStorage.getItem('graph'));
cy.json(savedJson);

// Export elements only
const elements = cy.elements().jsons();
```

## Performance Optimisation

### Large Graphs

```javascript
const cy = cytoscape({
  container: document.getElementById('cy'),
  elements: largeDataset,  // 10,000+ elements
  
  // Performance settings
  hideEdgesOnViewport: true,  // Hide edges during pan/zoom
  textureOnViewport: true,     // Render as texture during interaction
  motionBlur: true,            // Smooth motion blur
  pixelRatio: 'auto',
  
  // Disable animations for better performance
  style: [
    {
      selector: 'node',
      style: {
        'transition-duration': '0ms'
      }
    }
  ]
});

// Use viewport events sparingly
let timeout;
cy.on('pan zoom', () => {
  clearTimeout(timeout);
  timeout = setTimeout(() => {
    // Update UI after interaction stops
  }, 100);
});
```

## Best Practices

1. **Batch Operations**: Use `cy.batch()` for multiple element additions/removals
2. **Layout Performance**: Use simpler layouts (grid, circle) for large graphs
3. **Event Delegation**: Use selector-based events instead of attaching to individual elements
4. **Viewport Optimisation**: Enable `hideEdgesOnViewport` and `textureOnViewport` for large graphs
5. **Immutable Data**: When integrating with React/Vue, update via `cy.json()` rather than mutating
6. **Extension Loading**: Only load extensions you need to minimize bundle size
7. **Styling**: Use classes over direct style manipulation for better performance
8. **Memory Management**: Call `cy.destroy()` when unmounting components

## Resources

- **Documentation**: https://js.cytoscape.org/
- **GitHub**: https://github.com/cytoscape/cytoscape.js
- **Demos**: https://js.cytoscape.org/#demos
- **Extensions**: https://js.cytoscape.org/#extensions


# Cytoscape.js Documentation

## Overview
Cytoscape.js is a graph theory library for visualization and analysis. It is used to render interactive graphs in the browser.

## Initialization
```javascript
var cy = cytoscape({
  container: document.getElementById('cy'), // HTML container
  elements: [ // nodes and edges
    { data: { id: 'a' } },
    { data: { id: 'b' } },
    { data: { id: 'ab', source: 'a', target: 'b' } }
  ],
  style: [ // Stylesheet
    {
      selector: 'node',
      style: {
        'background-color': '#666',
        'label': 'data(id)'
      }
    },
    {
      selector: 'edge',
      style: {
        'width': 3,
        'line-color': '#ccc',
        'target-arrow-shape': 'triangle'
      }
    }
  ],
  layout: {
    name: 'grid'
  }
});
```

## Key Concepts
*   **Elements**: Nodes and edges. JSON format.
*   **Style**: CSS-like selectors to define visual appearance.
*   **Layout**: Automatic positioning of nodes (e.g., `grid`, `circle`, `cose`, `fcose`).
*   **Events**: Handling user interactions (tap, mouseover).

## Extensions
Cytoscape has a rich ecosystem of extensions:
*   `cytoscape-fcose`: Force-directed layout (fast compound spring embedder).
*   `cytoscape-cxtmenu`: Context menu.
*   `cytoscape-edgehandles`: Interactive edge creation.

## Integration
*   **React**: `react-cytoscapejs` wrapper.
*   **Streamlit**: `st-cytoscape`.

## Detailed Reference (Code Snippets)

### Cytoscape.js Initialization with Options
Source: https://github.com/cytoscape/cytoscape.js/blob/unstable/documentation/md/core/init.md

```javascript
var cy = cytoscape({
  // very commonly used options
  container: undefined,
  elements: [ /* ... */ ],
  style: [ /* ... */ ],
  layout: { name: 'grid' /* , ... */ },
  data: { /* ... */ },

  // initial viewport state:
  zoom: 1,
  pan: { x: 0, y: 0 },

  // interaction options:
  minZoom: 1e-50,
  maxZoom: 1e50,
  zoomingEnabled: true,
  userZoomingEnabled: true,
  panningEnabled: true,
  userPanningEnabled: true,
  boxSelectionEnabled: true,
  selectionType: 'single',
  touchTapThreshold: 8,
  desktopTapThreshold: 4,
  autolock: false,
  autoungrabify: false,
  autounselectify: false,
  multiClickDebounceTime: 250,

  // rendering options:
  headless: false,
  styleEnabled: true,
  hideEdgesOnViewport: false,
  textureOnViewport: false,
  motionBlur: false,
  motionBlurOpacity: 0.2,
  wheelSensitivity: 1,
  pixelRatio: 'auto'
});
```

### Initialize Cytoscape.js Graph
Source: https://github.com/cytoscape/cytoscape.js/blob/unstable/documentation/webgl.md

```javascript
var cy = cytoscape({
  container: document.getElementById('cy'),

  elements: [
    { data: { id: 'one', label: 'Node 1' } },
    { data: { id: 'two', label: 'Node 2' } },
    { data: { source: 'one', target: 'two', label: 'Edge 1' } }
  ],

  style: [
    {
      selector: 'node',
      style: {
        'background-color': '#666',
        'label': 'data(label)'
      }
    },
    {
      selector: 'edge',
      style: {
        'width': 3,
        'line-color': '#ccc',
        'target-arrow-color': '#ccc',
        'target-arrow-shape': 'triangle',
        'label': 'data(label)'
      }
    }
  ],

  layout: {
    name: 'grid'
  }
});
```

### Cytoscape.js Compound Nodes Initialization (JavaScript)
Source: https://github.com/cytoscape/cytoscape.js/blob/unstable/documentation/webgl.md

```javascript
var cy = cytoscape({
  container: document.getElementById('cy'),
  elements: [
    { data: { id: 'parent', label: 'Parent Node' } },
    { data: { id: 'child1', label: 'Child Node 1', parent: 'parent' } },
    { data: { id: 'child2', label: 'Child Node 2', parent: 'parent' } }
  ],
  style: [
    {
      selector: 'node',
      style: {
        'background-color': '#666',
        'label': 'data(label)'
      }
    },
    {
      selector: '$node > node',
      style: {
        'background-color': '#bbb'
      }
    }
  ],
  layout: {
    name: 'grid'
  }
});
```

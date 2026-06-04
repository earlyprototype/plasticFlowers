# plasticFlower — Frontend Data Flow

---

## Overview

| Component | Technology | Source |
|-----------|------------|--------|
| Framework | Next.js | Handover |
| Visualisation | Cytoscape.js + FCose | DEC-008 |
| Real-time | SSE subscription | Architecture |
| STT | Web Speech API | DEC-007 |

---

## Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Next.js)                         │
│                                                                    │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐      │
│   │ Microphone   │────▶│ Web Speech   │────▶│ Chunk        │      │
│   │ Input        │     │ API          │     │ Dispatcher   │      │
│   └──────────────┘     └──────────────┘     └──────┬───────┘      │
│                                                     │              │
│                                          POST /chunks              │
│                                                     ▼              │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐      │
│   │ Cytoscape.js │◀────│ Graph State  │◀────│ SSE          │      │
│   │ Renderer     │     │ Manager      │     │ Handler      │      │
│   └──────────────┘     └──────────────┘     └──────────────┘      │
│         │                    │                     ▲              │
│         ▼                    ▼                     │              │
│   ┌──────────────┐     ┌──────────────┐      SSE stream           │
│   │ Canvas       │     │ UI Controls  │            │              │
│   │ (FCose)      │     │ (Z-filter,   │            │              │
│   │              │     │  Export)     │            │              │
│   └──────────────┘     └──────────────┘            │              │
│                                                    │              │
└────────────────────────────────────────────────────│──────────────┘
                                                     │
                                          GET /sessions/{id}/stream
                                                     │
                                                     ▼
                                              ┌──────────────┐
                                              │   BACKEND    │
                                              │   (FastAPI)  │
                                              └──────────────┘
```

---

## Data Flow Sequence

### 1. Session Start

```
User clicks "Start Session"
    │
    ├─▶ POST /sessions { name: "..." }
    │       └─▶ Receive session_id
    │
    ├─▶ Connect SSE: GET /sessions/{id}/stream
    │
    └─▶ Start Web Speech API recognition
```

### 2. Speech Capture Loop

```
Web Speech API receives speech
    │
    ├─▶ onresult event fires
    │       └─▶ Extract transcript text
    │
    ├─▶ Chunk Dispatcher buffers text
    │       └─▶ When ~3-5 sentences accumulated
    │
    └─▶ POST /sessions/{id}/chunks
            {
              text: "...",
              start_time: 12.5,
              end_time: 18.2
            }
```

### 3. SSE Event Processing

```
SSE event received
    │
    ├─▶ Parse event type and data
    │
    ├─▶ Route to Graph State Manager
    │       │
    │       ├─▶ node_added: Add to nodes Map
    │       ├─▶ node_updated: Update existing node
    │       ├─▶ node_removed: Remove from nodes Map
    │       ├─▶ node_merged: Remove source, update references
    │       ├─▶ relationship_added: Add to relationships Map
    │       ├─▶ relationship_removed: Remove from relationships Map (by relationship id)
    │       ├─▶ flower_created: Add to flowers Map
    │       ├─▶ flower_updated: Update existing flower
    │       └─▶ flower_dissolved: Remove from flowers Map
    │
    └─▶ Trigger Cytoscape.js update
```

### 4. Graph Rendering

```
Graph State Manager notifies change
    │
    ├─▶ Convert state to Cytoscape elements
    │       │
    │       ├─▶ Nodes → cy.add({ data: {...}, classes: [...] })
    │       ├─▶ Relationships → cy.add({ data: { source, target, ... } })
    │       └─▶ Flowers → cy.add({ data: { parent: flower_id } })
    │
    ├─▶ Apply visual styles based on state
    │       │
    │       ├─▶ ghost nodes: semi-transparent
    │       └─▶ solid nodes: full opacity
    │
    └─▶ Run FCose layout (incremental)
```

---

## State Management

### Local State Structure

```typescript
interface GraphState {
  sessionId: string;
  nodes: Map<string, Node>;
  relationships: Map<string, Relationship>;
  flowers: Map<string, Flower>;
  transcript: string;
  isLive: boolean;
  connectionStatus: 'connected' | 'reconnecting' | 'disconnected';
}
```

### State Update Rules

| Event | State Change |
|-------|--------------|
| `node_added` | `nodes.set(id, node)` |
| `node_updated` | `nodes.set(id, { ...existing, ...updates })` |
| `node_removed` | `nodes.delete(id)` |
| `node_merged` | `nodes.delete(from_id)`, update relationship references |
| `relationship_added` | `relationships.set(rel.id, rel)` |
| `relationship_removed` | `relationships.delete(id)` |
| `flower_created` | `flowers.set(id, flower)` |
| `flower_updated` | `flowers.set(id, { ...existing, ...updates })` |
| `flower_dissolved` | `flowers.delete(id)`, clear node `flower_id` references |

**Relationship key format:** `rel.id`

---

## Cytoscape.js Integration

### Element Conversion

**Node to Cytoscape element:**
```javascript
{
  data: {
    id: node.id,
    label: node.label,
    type: node.inferred_type,
    confidence: node.confidence,
    status: node.status,
    parent: node.flower_id  // Compound node membership
  },
  classes: [node.status]  // 'ghost' or 'solid'
}
```

**Relationship to Cytoscape edge:**
```javascript
{
  data: {
    id: rel.id,
    source: rel.source_id,
    target: rel.target_id,
    category: rel.category,
    description: rel.description
  },
  classes: [rel.category.toLowerCase()]
}
```

**Flower to Cytoscape compound node:**
```javascript
{
  data: {
    id: flower.id,
    label: flower.label,
    isFlower: true
  },
  classes: ['flower']
}
```

### FCose Layout Configuration

```javascript
{
  name: 'fcose',
  quality: 'proof',
  animate: true,
  animationDuration: 500,
  fit: false,  // Don't auto-fit on every update
  randomize: false,
  nodeRepulsion: 4500,
  idealEdgeLength: 100,
  edgeElasticity: 0.45,
  nestingFactor: 0.1,
  gravity: 0.25,
  numIter: 2500,
  tilingPaddingVertical: 10,
  tilingPaddingHorizontal: 10,
  gravityRangeCompound: 1.5,
  gravityCompound: 1.0
}
```

**Incremental updates:** On new nodes, run layout with `fit: false` to preserve user's viewport position.

---

## Visual States

> **See `02_visual_design.md` for complete visual specification (RSA Animate aesthetic).**

### Summary

| State | Visual Treatment |
|-------|------------------|
| `ghost` | 70% opacity, grey dashed border |
| `solid` | 100% opacity, black solid border |
| `stem` | Accent colour border (coral) |

### Key Visual Principles

- **White canvas** — not dark mode
- **Minimal colour** — black strokes, single accent
- **Hand-drawn feel** — rounded shapes, curved edges
- **Draw-in animations** — nodes and edges animate like pen strokes

### Reference

Full Cytoscape stylesheet, animations, and colour palette defined in:
`_docs/_dev/_MVP/_frontend/02_visual_design.md`

---

## Z-Level Filtering (Scope)

Manage visual complexity by filtering what's displayed.

### Filter Options

| Filter | Effect |
|--------|--------|
| Show all | Display entire graph |
| Solid only | Hide ghost nodes |
| High confidence | Hide nodes below threshold |
| By Flower | Show only selected Flower(s) |
| By type | Show only selected inferred_type(s) |

### Implementation

```javascript
function applyZFilter(filter: ZFilter) {
  cy.nodes().forEach(node => {
    const visible = evaluateFilter(node.data(), filter);
    node.style('display', visible ? 'element' : 'none');
  });
  
  // Hide edges where either endpoint is hidden
  cy.edges().forEach(edge => {
    const sourceVisible = edge.source().style('display') !== 'none';
    const targetVisible = edge.target().style('display') !== 'none';
    edge.style('display', sourceVisible && targetVisible ? 'element' : 'none');
  });
}
```

---

## Auto-Reconnect (Scope)

### SSE Reconnection Logic

```javascript
class SSEManager {
  private reconnectAttempts = 0;
  private maxDelay = 30000;
  
  connect(sessionId: string) {
    const eventSource = new EventSource(`/api/sessions/${sessionId}/stream`);
    
    eventSource.onopen = () => {
      this.reconnectAttempts = 0;
      this.updateStatus('connected');
    };
    
    eventSource.onerror = () => {
      eventSource.close();
      this.reconnect(sessionId);
    };
    
    return eventSource;
  }
  
  reconnect(sessionId: string) {
    const delay = Math.min(
      1000 * Math.pow(2, this.reconnectAttempts),
      this.maxDelay
    );
    this.reconnectAttempts++;
    this.updateStatus('reconnecting');
    
    setTimeout(async () => {
      // Fetch full state before reconnecting stream
      const graph = await fetch(`/api/sessions/${sessionId}/graph`);
      this.replaceState(await graph.json());
      this.connect(sessionId);
    }, delay);
  }
}
```

### State Recovery

On reconnect:
1. Fetch full graph via `GET /sessions/{id}/graph`
2. Replace local state entirely (not merge)
3. Re-render Cytoscape
4. Resume SSE subscription

---

## Web Speech API Integration

### Configuration

```javascript
const recognition = new webkitSpeechRecognition();
recognition.continuous = true;
recognition.interimResults = true;
recognition.lang = 'en-GB';  // UK English (user preference)
```

### Chunk Buffering

```javascript
class ChunkDispatcher {
  private buffer: string[] = [];
  private sentenceCount = 0;
  private startTime: number;
  
  onSpeechResult(transcript: string, isFinal: boolean) {
    if (isFinal) {
      this.buffer.push(transcript);
      this.sentenceCount += this.countSentences(transcript);
      
      if (this.sentenceCount >= 3) {
        this.dispatch();
      }
    }
  }
  
  dispatch() {
    const text = this.buffer.join(' ');
    const endTime = performance.now() / 1000;
    
    fetch(`/api/sessions/${sessionId}/chunks`, {
      method: 'POST',
      body: JSON.stringify({
        text,
        start_time: this.startTime,
        end_time: endTime
      })
    });
    
    this.buffer = [];
    this.sentenceCount = 0;
    this.startTime = endTime;
  }
  
  countSentences(text: string): number {
    return (text.match(/[.!?]+/g) || []).length;
  }
}
```

---

## UI Components

### Main Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Header: Session name, Status indicator, Timer             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                                                             │
│                    Graph Canvas                             │
│                    (Cytoscape.js)                           │
│                                                             │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  Controls: Z-filter, Export, Start/Stop                    │
├─────────────────────────────────────────────────────────────┤
│  Transcript panel (collapsible)                            │
└─────────────────────────────────────────────────────────────┘
```

### Key Interactions

| Action | Result |
|--------|--------|
| Click node | Show detail panel (label, type, confidence, mentions) |
| Click edge | Show relationship detail (category, description, evidence) |
| Click Flower | Expand/collapse, show theme summary |
| Drag node | Manual repositioning (FCose respects on next layout) |
| Scroll | Zoom in/out |
| Pan | Move viewport |

---

## Decision Traceability

| Aspect | Decision | Reference |
|--------|----------|-----------|
| Framework | Next.js | Handover |
| Visualisation | Cytoscape.js + FCose | DEC-008 |
| STT | Web Speech API (browser-native) | DEC-007 |
| Real-time | SSE | Architecture |
| Z-filtering | Scope requirement | Scope |
| Auto-reconnect | Scope requirement | Scope |
| Language | UK English | User preference |


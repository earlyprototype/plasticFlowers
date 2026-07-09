# Architectural Advisory: plasticFlower Lite

> **Archived — separate project.** This is the design for a browser-only "plasticFlower Lite" proof of concept; none of this code exists in this repository. Kept for reference only.

**Date:** 26 December 2025  
**Version:** 1.0 (Browser-First)  
**Context:** Lightweight single-session implementation using Gemini + Browser APIs only  
**Companion to:** [ARCHITECTURE_ADVISORY.md](../ARCHITECTURE_ADVISORY.md) (full system)

---

## 1. Executive Summary

**plasticFlower Lite** is a minimal, browser-first implementation that delivers ~95% of single-session functionality without Neo4j or a complex backend.

### Purpose

| Use Case | Lite Version | Full Version |
|----------|--------------|--------------|
| Demos and proof-of-concept | Ideal | Overkill |
| Learning the core concepts | Ideal | Complex |
| Single user, single session | Works well | Better persistence |
| Building knowledge over time | Not suitable | Required |
| Production deployment | Not suitable | Required |

### What's Included

- Live speech transcription (Web Speech API)
- Real-time entity and relationship extraction (Gemini)
- Semantic clustering and keystone detection (Gemini)
- STT proofreading and correction (Gemini)
- Interactive graph visualization (Cytoscape.js)
- Session Q&A (Gemini with full context)
- External research (Gemini with grounding)
- Session export (browser-generated)

### What's NOT Included

- Cross-session memory
- Multi-device sync
- Industrial persistence
- Server-side processing

---

## 1.1 Quick Start (5 Minutes)

### Prerequisites
- Node.js 18+ (or just a browser for CDN version)
- Google AI Studio API key ([get one free](https://aistudio.google.com/apikey))
- Chrome/Edge browser (best Web Speech API support)

### Step 1: Deploy API Proxy (2 min)

Option A: **Cloudflare Workers** (recommended)
```bash
# Install Wrangler CLI
npm install -g wrangler

# Create project
wrangler init pf-proxy
cd pf-proxy

# Add worker.js from Section 12.8
# Then deploy
wrangler secret put GEMINI_API_KEY
wrangler deploy
```

Option B: **Vercel Edge** (alternative)
```bash
# Create project with vercel.json and api/proxy.js
vercel deploy
vercel env add GEMINI_API_KEY
```

### Step 2: Create Project (1 min)

```bash
mkdir plasticflower-lite && cd plasticflower-lite
npm init -y
npm install vite cytoscape cytoscape-fcose
```

### Step 3: Copy Files (2 min)

Copy these from Section 12:
- `index.html` (12.2)
- `style.css` (12.3)
- `src/main.js` (12.4)
- `src/modules/speech.js` (12.9)
- `src/modules/gemini.js` (5.2)
- `src/modules/session.js` (5.3 + 12.5)
- `src/components/graph.js` (12.10)
- `src/components/controls.js` (12.6)
- `src/components/qa-panel.js` (12.7)

### Step 4: Configure and Run

```javascript
// In src/main.js, update CONFIG.proxyUrl:
const CONFIG = {
    proxyUrl: 'https://your-worker.workers.dev', // Your proxy URL
    // ...
};
```

```bash
npx vite
# Open http://localhost:5173
```

### You're Done

Click "Start Recording", speak, and watch nodes form.

---

## 2. Architecture Overview

### System Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                      plasticFlower Lite                             │
│                      (Browser Only)                                 │
│                                                                     │
│   ┌─────────────────┐     ┌─────────────────┐                       │
│   │  Web Speech API │     │  Gemini API     │                       │
│   │  (Browser STT)  │     │  (via Proxy)    │                       │
│   └────────┬────────┘     └────────┬────────┘                       │
│            │                       │                                │
│            ▼                       ▼                                │
│   ┌─────────────────────────────────────────┐                       │
│   │           Session Controller            │                       │
│   │         (JavaScript Module)             │                       │
│   │                                         │                       │
│   │   • Chunk accumulation                  │                       │
│   │   • Gemini orchestration                │                       │
│   │   • State management                    │                       │
│   │   • localStorage I/O                    │                       │
│   └────────────────┬────────────────────────┘                       │
│                    │                                                │
│            ┌───────┴───────┐                                        │
│            ▼               ▼                                        │
│   ┌─────────────┐   ┌─────────────┐                                 │
│   │ localStorage│   │ Cytoscape.js│                                 │
│   │ (Persistence│   │ (Graph UI)  │                                 │
│   └─────────────┘   └─────────────┘                                 │
│                                                                     │
│   ┌─────────────────────────────────────────┐                       │
│   │           API Key Proxy                 │                       │
│   │    (Minimal backend - 20 lines)         │                       │
│   │    Cloudflare Worker / Vercel Edge      │                       │
│   └─────────────────────────────────────────┘                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Tech Stack

| Component | Technology | Role |
|-----------|------------|------|
| **Transcription** | Web Speech API | Browser-native STT |
| **Intelligence** | Gemini 2.0 Flash / 2.5 Pro | All LLM tasks |
| **Visualization** | Cytoscape.js | Graph rendering |
| **Persistence** | localStorage | Session data storage |
| **API Security** | Cloudflare Worker or Vercel Edge | Proxy for API key |
| **Framework** | Vanilla JS or React | UI structure |

---

## 3. Data Flow

### Live Transcription Flow

```
[User Speaks]
      ↓
[Web Speech API]
      ↓
[Text chunks accumulate (every 8s or 75 words)]
      ↓
[Session Controller]
      ↓
[Gemini API: Extract entities + relationships]
      ↓
[Update local state]
      ↓
[Cytoscape.js: Render new nodes/edges]
      ↓
[localStorage: Persist state]
```

### Gardener Cycle (Simplified)

```
[Every 60-90 seconds]
      ↓
[Session Controller: Trigger gardening]
      ↓
[Gemini API: Full context analysis]
      │
      ├─► Proofread transcript
      ├─► Confirm/merge nodes
      ├─► Cluster into Flowers
      └─► Identify keystones
      ↓
[Update local state]
      ↓
[Cytoscape.js: Animate changes]
```

### Q&A Flow

```
[User asks question]
      ↓
[Session Controller: Gather full context]
      │
      ├─ All transcript chunks
      ├─ All nodes
      └─ All relationships
      ↓
[Gemini API: Answer with context]
      ↓
[Display answer with citations]
```

---

## 4. Data Model

### Session State (localStorage)

```javascript
const sessionState = {
    id: "session_uuid",
    name: "My Talk",
    createdAt: "2025-12-26T10:00:00Z",
    
    // Transcript
    chunks: [
        {
            id: "chunk_1",
            text: "The CeADAR centre in Dublin...",
            originalText: "The see dare centre...",  // Before correction
            startTime: 0,
            endTime: 8.5
        }
    ],
    
    // Knowledge Graph
    nodes: [
        {
            id: "node_1",
            label: "CeADAR",
            type: "organisation",
            status: "solid",  // ghost | solid
            confidence: 0.9,
            mentions: 3,
            timestamps: [5.2, 45.8, 120.3],
            flowerId: "flower_1"
        }
    ],
    
    relationships: [
        {
            id: "rel_1",
            sourceId: "node_1",
            targetId: "node_2",
            category: "STRUCTURAL",
            description: "located in",
            confidence: 0.85
        }
    ],
    
    flowers: [
        {
            id: "flower_1",
            label: "Irish AI Ecosystem",
            stemNodeId: "node_1",
            memberIds: ["node_1", "node_2", "node_3"]
        }
    ],
    
    // Learned corrections
    vocabulary: {
        "see dare": "CeADAR",
        "you carry": "UKRI"
    },
    
    // References from research
    references: [
        {
            id: "ref_1",
            nodeId: "node_1",
            type: "organisation",
            title: "CeADAR - Ireland's National Centre for AI",
            url: "https://ceadar.ie",
            summary: "CeADAR is Ireland's centre for applied AI..."
        }
    ]
};
```

### localStorage Keys

```javascript
// Session list
localStorage.setItem('pf_sessions', JSON.stringify(['session_1', 'session_2']));

// Individual session
localStorage.setItem('pf_session_session_1', JSON.stringify(sessionState));

// Current active session
localStorage.setItem('pf_active_session', 'session_1');
```

---

## 5. Core Components

### 5.1 Speech Recognition Module

```javascript
class SpeechRecognitionModule {
    constructor(onChunk) {
        this.recognition = new webkitSpeechRecognition();
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        this.onChunk = onChunk;
        
        this.buffer = '';
        this.lastSentIndex = 0;
        this.startTime = Date.now();
    }
    
    start() {
        this.recognition.start();
        this.recognition.onresult = (event) => {
            let transcript = '';
            for (let i = 0; i < event.results.length; i++) {
                transcript += event.results[i][0].transcript;
            }
            
            this.buffer = transcript;
            this.checkForChunk();
        };
    }
    
    checkForChunk() {
        const newText = this.buffer.slice(this.lastSentIndex);
        const words = newText.trim().split(/\s+/);
        
        // Send chunk every 75 words or 8 seconds
        if (words.length >= 75 || this.timeSinceLastChunk() > 8000) {
            if (newText.trim()) {
                this.onChunk({
                    text: newText.trim(),
                    startTime: this.lastChunkTime || 0,
                    endTime: (Date.now() - this.startTime) / 1000
                });
                this.lastSentIndex = this.buffer.length;
                this.lastChunkTime = (Date.now() - this.startTime) / 1000;
            }
        }
    }
}
```

### 5.2 Gemini Client (via Proxy)

```javascript
class GeminiClient {
    constructor(proxyUrl) {
        this.proxyUrl = proxyUrl;
    }
    
    async extract(chunk, existingNodes) {
        const prompt = `
You are extracting entities and relationships from speech.

Existing nodes: ${JSON.stringify(existingNodes.map(n => n.label))}

New text: "${chunk.text}"

Extract:
1. New entities (not already in existing nodes)
2. Relationships between entities

Return JSON:
{
    "nodes": [{"label": "...", "type": "concept|person|organisation|funding", "confidence": 0.9}],
    "relationships": [{"source": "...", "target": "...", "category": "CAUSAL|STRUCTURAL|COMPARATIVE|TEMPORAL|ASSOCIATIVE", "description": "..."}],
    "duplicates": [{"newLabel": "...", "existingLabel": "...", "confidence": 0.9}]
}
`;
        
        return await this.call(prompt);
    }
    
    async garden(fullState) {
        const prompt = `
You are the Gardener for a knowledge graph. Analyse and improve.

Transcript: ${fullState.chunks.map(c => c.text).join(' ')}

Nodes: ${JSON.stringify(fullState.nodes)}
Relationships: ${JSON.stringify(fullState.relationships)}
Vocabulary: ${JSON.stringify(fullState.vocabulary)}

Tasks:
1. PROOFREAD: Find STT errors (phonetic spellings like "see dare" → "CeADAR")
2. CONFIRM: Which ghost nodes should become solid?
3. MERGE: Which nodes represent the same thing?
4. CLUSTER: Group related nodes into Flowers (3+ nodes, 2+ connections)
5. KEYSTONES: Which nodes are bridges between topics?

Return JSON:
{
    "corrections": [{"original": "...", "correction": "...", "confidence": 0.9}],
    "confirmations": ["node_id"],
    "merges": [{"keep": "node_id", "absorb": ["node_id"]}],
    "flowers": [{"label": "...", "stemNodeId": "...", "memberIds": ["..."]}],
    "keystones": ["node_id"]
}
`;
        
        return await this.call(prompt);
    }
    
    async askQuestion(question, fullState) {
        const context = `
Transcript: ${fullState.chunks.map(c => `[${c.startTime}s] ${c.text}`).join('\n')}

Knowledge Graph:
Nodes: ${fullState.nodes.map(n => `- ${n.label} (${n.type})`).join('\n')}
Relationships: ${fullState.relationships.map(r => `- ${r.sourceId} ${r.description} ${r.targetId}`).join('\n')}
`;
        
        const prompt = `
Based on this session, answer the question.
Cite sources using [Time: Xs] format.

Context:
${context}

Question: ${question}
`;
        
        return await this.call(prompt);
    }
    
    async research(nodeLabel, context) {
        const prompt = `
Research this entity and provide information.

Entity: ${nodeLabel}
Context: ${context}

Find:
- Official definition or description
- Official website if applicable
- Key facts

Return JSON:
{
    "title": "...",
    "url": "...",
    "summary": "2-3 sentence description",
    "type": "organisation|funding|concept|person",
    "confidence": 0.9
}
`;
        
        return await this.call(prompt, { useGrounding: true });
    }
    
    async call(prompt, options = {}) {
        const response = await fetch(this.proxyUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prompt,
                model: options.useGrounding ? 'gemini-2.0-flash' : 'gemini-2.0-flash',
                useGrounding: options.useGrounding || false
            })
        });
        
        const data = await response.json();
        return JSON.parse(data.text);
    }
}
```

### 5.3 Session Controller

```javascript
class SessionController {
    constructor(geminiClient, cytoscapeInstance) {
        this.gemini = geminiClient;
        this.cy = cytoscapeInstance;
        this.state = this.loadState() || this.createNewSession();
        
        // Start gardener cycle
        setInterval(() => this.runGardener(), 60000);
    }
    
    async processChunk(chunk) {
        // Apply vocabulary corrections first
        chunk.originalText = chunk.text;
        chunk.text = this.applyVocabulary(chunk.text);
        
        // Extract entities
        const extracted = await this.gemini.extract(chunk, this.state.nodes);
        
        // Handle duplicates
        for (const dup of extracted.duplicates) {
            const existing = this.state.nodes.find(n => n.label === dup.existingLabel);
            if (existing) {
                existing.mentions++;
                existing.timestamps.push(chunk.endTime);
            }
        }
        
        // Add new nodes (as ghosts)
        for (const node of extracted.nodes) {
            const newNode = {
                id: this.generateId(),
                ...node,
                status: 'ghost',
                mentions: 1,
                timestamps: [chunk.endTime],
                flowerId: null
            };
            this.state.nodes.push(newNode);
            this.cy.add({ data: { id: newNode.id, label: newNode.label } });
        }
        
        // Add relationships
        for (const rel of extracted.relationships) {
            const source = this.findNodeByLabel(rel.source);
            const target = this.findNodeByLabel(rel.target);
            if (source && target) {
                const newRel = {
                    id: this.generateId(),
                    sourceId: source.id,
                    targetId: target.id,
                    ...rel
                };
                this.state.relationships.push(newRel);
                this.cy.add({ 
                    data: { 
                        id: newRel.id, 
                        source: source.id, 
                        target: target.id 
                    } 
                });
            }
        }
        
        // Add chunk
        this.state.chunks.push({
            id: this.generateId(),
            ...chunk
        });
        
        // Persist
        this.saveState();
    }
    
    async runGardener() {
        if (this.state.nodes.length === 0) return;
        
        const result = await this.gemini.garden(this.state);
        
        // Apply corrections
        for (const corr of result.corrections) {
            this.state.vocabulary[corr.original] = corr.correction;
            
            // Update nodes
            for (const node of this.state.nodes) {
                if (node.label.toLowerCase() === corr.original.toLowerCase()) {
                    node.label = corr.correction;
                    this.cy.$(`#${node.id}`).data('label', corr.correction);
                }
            }
            
            // Update chunks
            for (const chunk of this.state.chunks) {
                chunk.text = chunk.text.replace(
                    new RegExp(corr.original, 'gi'), 
                    corr.correction
                );
            }
        }
        
        // Confirm ghosts
        for (const nodeId of result.confirmations) {
            const node = this.state.nodes.find(n => n.id === nodeId);
            if (node) {
                node.status = 'solid';
                this.cy.$(`#${nodeId}`).addClass('solid');
            }
        }
        
        // Merge duplicates
        for (const merge of result.merges) {
            const keepNode = this.state.nodes.find(n => n.id === merge.keep);
            for (const absorbId of merge.absorb) {
                const absorbNode = this.state.nodes.find(n => n.id === absorbId);
                if (keepNode && absorbNode) {
                    keepNode.mentions += absorbNode.mentions;
                    keepNode.timestamps.push(...absorbNode.timestamps);
                    this.state.nodes = this.state.nodes.filter(n => n.id !== absorbId);
                    this.cy.$(`#${absorbId}`).remove();
                }
            }
        }
        
        // Update flowers
        this.state.flowers = result.flowers.map(f => ({
            id: this.generateId(),
            ...f
        }));
        
        // Mark keystones
        for (const node of this.state.nodes) {
            node.isKeystone = result.keystones.includes(node.id);
        }
        
        this.saveState();
        this.updateVisualization();
    }
    
    applyVocabulary(text) {
        for (const [original, correction] of Object.entries(this.state.vocabulary)) {
            text = text.replace(new RegExp(original, 'gi'), correction);
        }
        return text;
    }
    
    saveState() {
        localStorage.setItem(`pf_session_${this.state.id}`, JSON.stringify(this.state));
    }
    
    loadState() {
        const activeId = localStorage.getItem('pf_active_session');
        if (activeId) {
            const data = localStorage.getItem(`pf_session_${activeId}`);
            return data ? JSON.parse(data) : null;
        }
        return null;
    }
    
    createNewSession() {
        const session = {
            id: this.generateId(),
            name: `Session ${new Date().toLocaleDateString()}`,
            createdAt: new Date().toISOString(),
            chunks: [],
            nodes: [],
            relationships: [],
            flowers: [],
            vocabulary: {},
            references: []
        };
        localStorage.setItem('pf_active_session', session.id);
        return session;
    }
    
    generateId() {
        return 'id_' + Math.random().toString(36).substr(2, 9);
    }
}
```

### 5.4 API Key Proxy (Cloudflare Worker)

```javascript
// Deploy to Cloudflare Workers or Vercel Edge
export default {
    async fetch(request, env) {
        if (request.method !== 'POST') {
            return new Response('Method not allowed', { status: 405 });
        }
        
        const { prompt, model, useGrounding } = await request.json();
        
        const geminiUrl = `https://generativelanguage.googleapis.com/v1/models/${model}:generateContent`;
        
        const body = {
            contents: [{ parts: [{ text: prompt }] }],
            generationConfig: {
                responseMimeType: 'application/json'
            }
        };
        
        if (useGrounding) {
            body.tools = [{ google_search: {} }];
        }
        
        const response = await fetch(geminiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-goog-api-key': env.GEMINI_API_KEY
            },
            body: JSON.stringify(body)
        });
        
        const data = await response.json();
        
        return new Response(JSON.stringify({
            text: data.candidates[0].content.parts[0].text
        }), {
            headers: { 
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        });
    }
};
```

---

## 6. Research (External Enrichment)

The Lite version includes the same research capability as the full system, using Gemini's built-in grounding.

### When Research Triggers

| Trigger | Condition |
|---------|-----------|
| Low confidence | Node extracted with `confidence < 0.7` |
| Entity type | Node type is `organisation`, `funding`, or `person` |
| User request | User clicks "Research" on a node |
| Transcript pattern | Phrases like "what is", "I don't know" near the entity |

### Research Flow

```
[Trigger detected]
      ↓
[Gemini with grounding enabled]
      ↓
[Google Search runs automatically]
      ↓
[LLM extracts: title, URL, summary]
      ↓
[ReferenceNode created and linked]
      ↓
[UI shows reference icon on node]
```

### Implementation in SessionController

```javascript
class SessionController {
    // ... existing code ...
    
    async checkForResearch(node) {
        if (this.shouldResearch(node)) {
            const context = this.getNodeContext(node);
            const reference = await this.gemini.research(node.label, context);
            
            if (reference.confidence > 0.7) {
                this.state.references.push({
                    id: this.generateId(),
                    nodeId: node.id,
                    ...reference
                });
                this.saveState();
                this.showReferenceIndicator(node.id);
            }
        }
    }
    
    shouldResearch(node) {
        // Low confidence extraction
        if (node.confidence < 0.7) return true;
        
        // Entity types that benefit from research
        if (['organisation', 'funding', 'person'].includes(node.type)) {
            // Only research if not already researched
            const hasReference = this.state.references.some(r => r.nodeId === node.id);
            if (!hasReference) return true;
        }
        
        return false;
    }
    
    getNodeContext(node) {
        // Find chunks where this node was mentioned
        const relevantChunks = this.state.chunks.filter(c => 
            node.timestamps.some(t => t >= c.startTime && t <= c.endTime)
        );
        return relevantChunks.map(c => c.text).join(' ');
    }
    
    showReferenceIndicator(nodeId) {
        this.cy.$(`#${nodeId}`).addClass('has-reference');
    }
}
```

### UI: Reference Panel

```javascript
// Show reference when node is clicked
cy.on('tap', 'node.has-reference', function(evt) {
    const nodeId = evt.target.id();
    const reference = sessionController.state.references.find(r => r.nodeId === nodeId);
    
    if (reference) {
        showReferencePanel({
            title: reference.title,
            url: reference.url,
            summary: reference.summary,
            type: reference.type
        });
    }
});

function showReferencePanel(reference) {
    const panel = document.getElementById('reference-panel');
    panel.innerHTML = `
        <h3>${reference.title}</h3>
        <p>${reference.summary}</p>
        <a href="${reference.url}" target="_blank">View source</a>
        <span class="type-badge">${reference.type}</span>
    `;
    panel.classList.add('visible');
}
```

### Cytoscape Styling for References

```javascript
// Add to Cytoscape style array
{
    selector: 'node.has-reference',
    style: {
        'border-width': 3,
        'border-color': '#22c55e',  // Green border
        // Or add a badge/icon overlay
    }
}
```

### Research Prompt (in GeminiClient)

```javascript
async research(nodeLabel, context) {
    const prompt = `
You are a research assistant. Find authoritative information about this entity.

Entity: ${nodeLabel}
Context from transcript: ${context}

Search for:
1. Official definition or description
2. Official website (if organisation/funding scheme)
3. Key facts relevant to the context

Return JSON:
{
    "title": "Official name of the entity",
    "url": "Primary official URL",
    "summary": "2-3 sentence description",
    "type": "organisation|funding|concept|person",
    "confidence": 0.0-1.0
}

If you cannot find reliable information, set confidence to 0.
`;

    return await this.call(prompt, { useGrounding: true });
}
```

### When Research Runs

| Timing | Approach |
|--------|----------|
| Immediate | Right after node creation (if low confidence) |
| Batch | During Gardener cycle (check all unresearched nodes) |
| On-demand | User clicks "Research" button on node |

**Recommended:** Batch during Gardener cycle to avoid too many API calls.

```javascript
async runGardener() {
    // ... existing gardening tasks ...
    
    // Check for research opportunities
    const unresearchedNodes = this.state.nodes.filter(n => 
        this.shouldResearch(n) && 
        !this.state.references.some(r => r.nodeId === n.id)
    );
    
    // Research up to 3 nodes per cycle to avoid rate limits
    for (const node of unresearchedNodes.slice(0, 3)) {
        await this.checkForResearch(node);
    }
}
```

---

## 7. Visualization

### Cytoscape.js Configuration

```javascript
const cy = cytoscape({
    container: document.getElementById('graph'),
    
    style: [
        // Ghost nodes
        {
            selector: 'node',
            style: {
                'label': 'data(label)',
                'background-color': '#888',
                'border-width': 2,
                'border-style': 'dashed',
                'border-color': '#666',
                'opacity': 0.6
            }
        },
        // Solid nodes
        {
            selector: 'node.solid',
            style: {
                'background-color': '#4a9eff',
                'border-style': 'solid',
                'opacity': 1
            }
        },
        // Keystone nodes
        {
            selector: 'node.keystone',
            style: {
                'width': 60,
                'height': 60,
                'font-size': 14,
                'font-weight': 'bold'
            }
        },
        // Edges
        {
            selector: 'edge',
            style: {
                'width': 2,
                'line-color': '#ccc',
                'target-arrow-color': '#ccc',
                'target-arrow-shape': 'triangle',
                'curve-style': 'bezier'
            }
        }
    ],
    
    layout: {
        name: 'fcose',
        animate: true,
        animationDuration: 500
    }
});
```

### Animation Helpers

```javascript
function animateNodeConfirmation(nodeId) {
    const node = cy.$(`#${nodeId}`);
    node.animate({
        style: { 'opacity': 1, 'border-style': 'solid' }
    }, { duration: 400 });
    node.addClass('solid');
}

function animateFlowerFormation(flower) {
    const stem = cy.$(`#${flower.stemNodeId}`);
    const members = flower.memberIds.map(id => cy.$(`#${id}`));
    
    // Fan out around stem
    const stemPos = stem.position();
    members.forEach((member, i) => {
        const angle = (2 * Math.PI / members.length) * i;
        const radius = 100;
        member.animate({
            position: {
                x: stemPos.x + radius * Math.cos(angle),
                y: stemPos.y + radius * Math.sin(angle)
            }
        }, { duration: 800 });
    });
}
```

---

## 8. Export Functionality

### Export to Markdown

```javascript
function exportToMarkdown(state) {
    let md = `# Session: ${state.name}\n`;
    md += `**Date:** ${new Date(state.createdAt).toLocaleDateString()}\n\n`;
    
    md += `## Summary\n`;
    md += `- **Nodes:** ${state.nodes.length}\n`;
    md += `- **Relationships:** ${state.relationships.length}\n`;
    md += `- **Clusters:** ${state.flowers.length}\n\n`;
    
    md += `## Key Concepts\n`;
    const keystones = state.nodes.filter(n => n.isKeystone);
    keystones.forEach(n => {
        md += `- **${n.label}** (${n.type}) - ${n.mentions} mentions\n`;
    });
    md += '\n';
    
    md += `## Clusters (Flowers)\n`;
    state.flowers.forEach(f => {
        md += `### ${f.label}\n`;
        const members = state.nodes.filter(n => f.memberIds.includes(n.id));
        members.forEach(m => {
            md += `- ${m.label}\n`;
        });
        md += '\n';
    });
    
    md += `## Transcript\n`;
    state.chunks.forEach(c => {
        md += `[${formatTime(c.startTime)}] ${c.text}\n\n`;
    });
    
    return md;
}

function downloadMarkdown(state) {
    const md = exportToMarkdown(state);
    const blob = new Blob([md], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${state.name.replace(/\s+/g, '_')}.md`;
    a.click();
}
```

### Export to JSON

```javascript
function exportToJSON(state) {
    return JSON.stringify(state, null, 2);
}

function downloadJSON(state) {
    const json = exportToJSON(state);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${state.name.replace(/\s+/g, '_')}.json`;
    a.click();
}
```

---

## 9. Limitations and Mitigations

### Data Persistence

| Risk | Impact | Mitigation |
|------|--------|------------|
| Browser data cleared | All sessions lost | Regular export reminders |
| localStorage quota (5-10MB) | Large sessions fail | Compress or warn user |
| Browser crash mid-session | Current state lost | Auto-save every 30s |

### API Reliability

| Risk | Impact | Mitigation |
|------|--------|------------|
| Gemini rate limits | Extraction fails | Exponential backoff |
| Network failure | Chunk not processed | Queue and retry |
| Proxy downtime | All calls fail | Show offline mode |

### Browser Compatibility

| Feature | Chrome | Firefox | Safari | Edge |
|---------|--------|---------|--------|------|
| Web Speech API | Yes | Limited | Yes | Yes |
| localStorage | Yes | Yes | Yes | Yes |
| Cytoscape.js | Yes | Yes | Yes | Yes |

---

## 10. When to Upgrade to Full Version

Consider upgrading to the full Neo4j architecture when:

| Trigger | Why Upgrade |
|---------|-------------|
| Need cross-session Q&A | localStorage is per-session |
| Data is valuable/irreplaceable | localStorage is fragile |
| Multiple devices | No sync in lite version |
| Team/multi-user | No shared state |
| More than 10 sessions | Management becomes hard |
| Production deployment | Need industrial reliability |

### Migration Path

The data model is compatible. To migrate:

```javascript
// Export from Lite
const sessions = JSON.parse(localStorage.getItem('pf_sessions'));
const allData = sessions.map(id => 
    JSON.parse(localStorage.getItem(`pf_session_${id}`))
);

// Import to Full (POST to API)
for (const session of allData) {
    await fetch('/api/sessions/import', {
        method: 'POST',
        body: JSON.stringify(session)
    });
}
```

---

## 11. Implementation Checklist

### Phase 1: Core Infrastructure
- [ ] Set up project structure (Vite + vanilla JS or React)
- [ ] Deploy API proxy (Cloudflare Worker or Vercel Edge)
- [ ] Implement localStorage wrapper with auto-save
- [ ] Basic HTML/CSS layout

### Phase 2: Speech Recognition
- [ ] Implement SpeechRecognitionModule
- [ ] Chunk accumulation logic (75 words / 8 seconds)
- [ ] Visual feedback for listening state

### Phase 3: Gemini Integration
- [ ] GeminiClient with proxy calls
- [ ] Extract prompt and response parsing
- [ ] Error handling and retries

### Phase 4: Visualization
- [ ] Cytoscape.js setup
- [ ] Node styling (ghost/solid/keystone)
- [ ] Edge styling
- [ ] Layout configuration (fcose)
- [ ] Animation helpers

### Phase 5: Session Controller
- [ ] State management
- [ ] processChunk flow
- [ ] Gardener cycle (60s timer)
- [ ] Vocabulary application

### Phase 6: Q&A and Research
- [ ] Question input UI
- [ ] askQuestion integration
- [ ] Research trigger (low confidence nodes)
- [ ] Reference display

### Phase 7: Export
- [ ] Markdown export
- [ ] JSON export
- [ ] Import from JSON (session restore)

---

## 12. Complete Implementation

This section provides all missing pieces needed to build the POC from scratch.

### 12.1 Dependencies

**Option A: CDN (no build step)**

```html
<!-- In index.html <head> -->
<script src="https://unpkg.com/cytoscape@3.28.1/dist/cytoscape.min.js"></script>
<script src="https://unpkg.com/cytoscape-fcose@2.2.0/cytoscape-fcose.js"></script>
```

**Option B: npm (with Vite/bundler)**

```json
{
  "name": "plasticflower-lite",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "cytoscape": "^3.28.1",
    "cytoscape-fcose": "^2.2.0"
  },
  "devDependencies": {
    "vite": "^5.0.0"
  }
}
```

### 12.2 Complete HTML Template

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>plasticFlower Lite</title>
    <link rel="stylesheet" href="style.css">
    <!-- CDN dependencies (if not using npm) -->
    <script src="https://unpkg.com/cytoscape@3.28.1/dist/cytoscape.min.js"></script>
    <script src="https://unpkg.com/cytoscape-fcose@2.2.0/cytoscape-fcose.js"></script>
</head>
<body>
    <div id="app">
        <!-- Header / Controls -->
        <header id="controls">
            <div class="left">
                <h1>plasticFlower</h1>
                <span id="session-name" contenteditable="true">New Session</span>
            </div>
            <div class="center">
                <button id="btn-start" class="primary">Start Recording</button>
                <button id="btn-stop" class="danger" disabled>Stop</button>
                <span id="status-indicator" class="status idle">Idle</span>
            </div>
            <div class="right">
                <button id="btn-export-md">Export MD</button>
                <button id="btn-export-json">Export JSON</button>
                <select id="session-select">
                    <option value="">-- Sessions --</option>
                </select>
                <button id="btn-new-session">+ New</button>
            </div>
        </header>

        <!-- Main Content -->
        <main>
            <!-- Graph Panel -->
            <section id="graph-panel">
                <div id="graph"></div>
                <div id="graph-stats">
                    <span>Nodes: <strong id="stat-nodes">0</strong></span>
                    <span>Edges: <strong id="stat-edges">0</strong></span>
                    <span>Clusters: <strong id="stat-clusters">0</strong></span>
                </div>
            </section>

            <!-- Side Panel -->
            <aside id="side-panel">
                <!-- Transcript Tab -->
                <div id="transcript-panel" class="tab-content active">
                    <h2>Live Transcript</h2>
                    <div id="transcript-content"></div>
                </div>

                <!-- Q&A Tab -->
                <div id="qa-panel" class="tab-content">
                    <h2>Ask a Question</h2>
                    <div id="qa-input-container">
                        <input type="text" id="qa-input" placeholder="What was discussed about...">
                        <button id="btn-ask">Ask</button>
                    </div>
                    <div id="qa-response"></div>
                </div>

                <!-- Reference Panel (appears on node click) -->
                <div id="reference-panel" class="hidden">
                    <button id="close-reference">x</button>
                    <h3 id="ref-title"></h3>
                    <p id="ref-summary"></p>
                    <a id="ref-url" href="#" target="_blank">View source</a>
                </div>

                <!-- Tab Navigation -->
                <nav id="tab-nav">
                    <button class="tab-btn active" data-tab="transcript-panel">Transcript</button>
                    <button class="tab-btn" data-tab="qa-panel">Q&A</button>
                </nav>
            </aside>
        </main>

        <!-- Loading Overlay -->
        <div id="loading-overlay" class="hidden">
            <div class="spinner"></div>
            <span id="loading-message">Processing...</span>
        </div>

        <!-- Error Toast -->
        <div id="error-toast" class="hidden">
            <span id="error-message"></span>
            <button id="dismiss-error">Dismiss</button>
        </div>
    </div>

    <script type="module" src="src/main.js"></script>
</body>
</html>
```

### 12.3 Complete CSS (style.css)

```css
/* === Variables === */
:root {
    --bg-primary: #0f0f0f;
    --bg-secondary: #1a1a1a;
    --bg-tertiary: #252525;
    --text-primary: #f0f0f0;
    --text-secondary: #888;
    --accent: #4a9eff;
    --accent-hover: #6bb3ff;
    --success: #22c55e;
    --danger: #ef4444;
    --warning: #f59e0b;
    --ghost: #666;
    --solid: #4a9eff;
    --keystone: #f59e0b;
    --flower-border: rgba(74, 158, 255, 0.3);
}

/* === Reset === */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    height: 100vh;
    overflow: hidden;
}

/* === Layout === */
#app {
    display: flex;
    flex-direction: column;
    height: 100vh;
}

header#controls {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 2rem;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--bg-tertiary);
}

header .left, header .center, header .right {
    display: flex;
    align-items: center;
    gap: 1rem;
}

header h1 {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--accent);
}

#session-name {
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    background: var(--bg-tertiary);
    outline: none;
}

#session-name:focus {
    outline: 1px solid var(--accent);
}

main {
    display: flex;
    flex: 1;
    overflow: hidden;
}

/* === Graph Panel === */
#graph-panel {
    flex: 1;
    position: relative;
    background: var(--bg-primary);
}

#graph {
    width: 100%;
    height: 100%;
}

#graph-stats {
    position: absolute;
    bottom: 1rem;
    left: 1rem;
    display: flex;
    gap: 1.5rem;
    padding: 0.5rem 1rem;
    background: rgba(0, 0, 0, 0.7);
    border-radius: 8px;
    font-size: 0.875rem;
    color: var(--text-secondary);
}

#graph-stats strong {
    color: var(--text-primary);
}

/* === Side Panel === */
#side-panel {
    width: 400px;
    background: var(--bg-secondary);
    border-left: 1px solid var(--bg-tertiary);
    display: flex;
    flex-direction: column;
}

.tab-content {
    flex: 1;
    padding: 1rem;
    overflow-y: auto;
    display: none;
}

.tab-content.active {
    display: block;
}

#tab-nav {
    display: flex;
    border-top: 1px solid var(--bg-tertiary);
}

.tab-btn {
    flex: 1;
    padding: 0.75rem;
    background: var(--bg-tertiary);
    border: none;
    color: var(--text-secondary);
    cursor: pointer;
    transition: all 0.2s;
}

.tab-btn.active {
    background: var(--bg-secondary);
    color: var(--accent);
}

/* === Transcript === */
#transcript-content {
    font-size: 0.9rem;
    line-height: 1.6;
}

.transcript-chunk {
    padding: 0.5rem 0;
    border-bottom: 1px solid var(--bg-tertiary);
}

.transcript-chunk .timestamp {
    font-size: 0.75rem;
    color: var(--text-secondary);
    margin-bottom: 0.25rem;
}

.transcript-chunk.corrected {
    background: rgba(34, 197, 94, 0.1);
    border-left: 3px solid var(--success);
    padding-left: 0.5rem;
}

/* === Q&A Panel === */
#qa-input-container {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1rem;
}

#qa-input {
    flex: 1;
    padding: 0.75rem;
    border: 1px solid var(--bg-tertiary);
    border-radius: 8px;
    background: var(--bg-primary);
    color: var(--text-primary);
    font-size: 0.9rem;
}

#qa-response {
    padding: 1rem;
    background: var(--bg-tertiary);
    border-radius: 8px;
    line-height: 1.6;
    white-space: pre-wrap;
}

#qa-response:empty {
    display: none;
}

/* === Reference Panel === */
#reference-panel {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 1rem;
    background: var(--bg-tertiary);
    border-top: 3px solid var(--success);
    transform: translateY(100%);
    transition: transform 0.3s;
}

#reference-panel.visible {
    transform: translateY(0);
}

#reference-panel.hidden {
    display: none;
}

#close-reference {
    position: absolute;
    top: 0.5rem;
    right: 0.5rem;
    background: none;
    border: none;
    color: var(--text-secondary);
    cursor: pointer;
    font-size: 1.25rem;
}

/* === Buttons === */
button {
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 6px;
    background: var(--bg-tertiary);
    color: var(--text-primary);
    cursor: pointer;
    font-size: 0.875rem;
    transition: all 0.2s;
}

button:hover:not(:disabled) {
    background: var(--bg-secondary);
}

button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

button.primary {
    background: var(--accent);
    color: white;
}

button.primary:hover:not(:disabled) {
    background: var(--accent-hover);
}

button.danger {
    background: var(--danger);
    color: white;
}

/* === Status Indicator === */
.status {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.875rem;
}

.status::before {
    content: '';
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--ghost);
}

.status.idle::before { background: var(--ghost); }
.status.recording::before { background: var(--danger); animation: pulse 1s infinite; }
.status.processing::before { background: var(--warning); }
.status.gardening::before { background: var(--success); }

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

/* === Loading Overlay === */
#loading-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.8);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    z-index: 1000;
}

#loading-overlay.hidden {
    display: none;
}

.spinner {
    width: 40px;
    height: 40px;
    border: 3px solid var(--bg-tertiary);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

/* === Error Toast === */
#error-toast {
    position: fixed;
    bottom: 2rem;
    left: 50%;
    transform: translateX(-50%);
    padding: 1rem 2rem;
    background: var(--danger);
    color: white;
    border-radius: 8px;
    display: flex;
    align-items: center;
    gap: 1rem;
    z-index: 1001;
}

#error-toast.hidden {
    display: none;
}

/* === Select === */
select {
    padding: 0.5rem;
    border: 1px solid var(--bg-tertiary);
    border-radius: 6px;
    background: var(--bg-primary);
    color: var(--text-primary);
    font-size: 0.875rem;
}
```

### 12.4 App Initialisation (main.js)

```javascript
import { SpeechRecognitionModule } from './modules/speech.js';
import { GeminiClient } from './modules/gemini.js';
import { SessionController } from './modules/session.js';
import { initGraph } from './components/graph.js';
import { initControls } from './components/controls.js';
import { initQAPanel } from './components/qa-panel.js';

// Configuration
const CONFIG = {
    proxyUrl: 'https://your-worker.your-subdomain.workers.dev', // Replace with your proxy URL
    gardenInterval: 60000,  // 60 seconds
    chunkWordLimit: 75,
    chunkTimeLimit: 8000    // 8 seconds
};

// Initialise app
async function init() {
    // Check browser compatibility
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        showError('Speech recognition not supported. Please use Chrome or Edge.');
        document.getElementById('btn-start').disabled = true;
        return;
    }

    // Initialise Cytoscape
    const cy = initGraph('graph');

    // Initialise Gemini client
    const gemini = new GeminiClient(CONFIG.proxyUrl);

    // Initialise session controller
    const controller = new SessionController(gemini, cy, CONFIG);

    // Initialise speech recognition
    const speech = new SpeechRecognitionModule(
        (chunk) => controller.processChunk(chunk),
        CONFIG.chunkWordLimit,
        CONFIG.chunkTimeLimit
    );

    // Initialise UI components
    initControls(speech, controller);
    initQAPanel(controller);

    // Restore session if exists
    controller.restoreVisualization();
    updateStats(controller);

    // Expose for debugging
    window.pf = { cy, controller, speech, gemini };
    
    console.log('plasticFlower Lite initialised');
}

// Helper: Show error toast
function showError(message) {
    const toast = document.getElementById('error-toast');
    const msg = document.getElementById('error-message');
    msg.textContent = message;
    toast.classList.remove('hidden');
    
    document.getElementById('dismiss-error').onclick = () => {
        toast.classList.add('hidden');
    };
}

// Helper: Update stats display
function updateStats(controller) {
    document.getElementById('stat-nodes').textContent = controller.state.nodes.length;
    document.getElementById('stat-edges').textContent = controller.state.relationships.length;
    document.getElementById('stat-clusters').textContent = controller.state.flowers.length;
}

// Start
init().catch(err => {
    console.error('Failed to initialise:', err);
    showError('Failed to initialise: ' + err.message);
});
```

### 12.5 Missing Helper Methods

Add these to `SessionController`:

```javascript
// In SessionController class

// Time since last chunk was sent
timeSinceLastChunk() {
    if (!this.lastChunkSentAt) return Infinity;
    return Date.now() - this.lastChunkSentAt;
}

// Find node by label (case-insensitive)
findNodeByLabel(label) {
    return this.state.nodes.find(
        n => n.label.toLowerCase() === label.toLowerCase()
    );
}

// Update visualization after gardener runs
updateVisualization() {
    // Update node classes
    for (const node of this.state.nodes) {
        const cyNode = this.cy.$(`#${node.id}`);
        if (!cyNode.length) continue;
        
        // Status classes
        cyNode.removeClass('ghost solid keystone');
        cyNode.addClass(node.status);
        if (node.isKeystone) cyNode.addClass('keystone');
        
        // Update label
        cyNode.data('label', node.label);
    }
    
    // Visualise flowers (compound nodes or background shapes)
    this.visualizeFlowers();
    
    // Re-run layout
    this.cy.layout({ name: 'fcose', animate: true }).run();
    
    // Update stats
    this.updateStats();
}

// Visualise flower clusters
visualizeFlowers() {
    // Remove existing flower backgrounds
    this.cy.$('.flower-bg').remove();
    
    for (const flower of this.state.flowers) {
        const members = flower.memberIds.map(id => this.cy.$(`#${id}`)).filter(n => n.length);
        if (members.length < 2) continue;
        
        // Calculate bounding box
        const positions = members.map(m => m.position());
        const centerX = positions.reduce((sum, p) => sum + p.x, 0) / positions.length;
        const centerY = positions.reduce((sum, p) => sum + p.y, 0) / positions.length;
        
        // Add a background node (visual only)
        this.cy.add({
            group: 'nodes',
            data: {
                id: `flower_bg_${flower.id}`,
                label: flower.label
            },
            classes: 'flower-bg',
            position: { x: centerX, y: centerY }
        });
    }
}

// Restore visualization from loaded state
restoreVisualization() {
    // Clear existing
    this.cy.elements().remove();
    
    // Add nodes
    for (const node of this.state.nodes) {
        this.cy.add({
            data: { id: node.id, label: node.label },
            classes: `${node.status} ${node.isKeystone ? 'keystone' : ''}`
        });
    }
    
    // Add edges
    for (const rel of this.state.relationships) {
        this.cy.add({
            data: {
                id: rel.id,
                source: rel.sourceId,
                target: rel.targetId
            }
        });
    }
    
    // Run layout
    this.cy.layout({ name: 'fcose' }).run();
    
    // Restore transcript display
    this.renderTranscript();
}

// Render transcript to UI
renderTranscript() {
    const container = document.getElementById('transcript-content');
    container.innerHTML = this.state.chunks.map(chunk => `
        <div class="transcript-chunk ${chunk.originalText !== chunk.text ? 'corrected' : ''}">
            <div class="timestamp">${this.formatTime(chunk.startTime)}</div>
            <div class="text">${chunk.text}</div>
        </div>
    `).join('');
    
    // Scroll to bottom
    container.scrollTop = container.scrollHeight;
}

// Format seconds to MM:SS
formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

// Update stats display
updateStats() {
    document.getElementById('stat-nodes').textContent = this.state.nodes.length;
    document.getElementById('stat-edges').textContent = this.state.relationships.length;
    document.getElementById('stat-clusters').textContent = this.state.flowers.length;
}
```

### 12.6 Controls Component (controls.js)

```javascript
export function initControls(speech, controller) {
    const btnStart = document.getElementById('btn-start');
    const btnStop = document.getElementById('btn-stop');
    const btnExportMd = document.getElementById('btn-export-md');
    const btnExportJson = document.getElementById('btn-export-json');
    const btnNewSession = document.getElementById('btn-new-session');
    const sessionSelect = document.getElementById('session-select');
    const sessionName = document.getElementById('session-name');
    const statusIndicator = document.getElementById('status-indicator');

    // Start recording
    btnStart.addEventListener('click', () => {
        speech.start();
        btnStart.disabled = true;
        btnStop.disabled = false;
        updateStatus('recording', 'Recording...');
    });

    // Stop recording
    btnStop.addEventListener('click', () => {
        speech.stop();
        btnStart.disabled = false;
        btnStop.disabled = true;
        updateStatus('idle', 'Idle');
    });

    // Export MD
    btnExportMd.addEventListener('click', () => {
        controller.downloadMarkdown();
    });

    // Export JSON
    btnExportJson.addEventListener('click', () => {
        controller.downloadJSON();
    });

    // New session
    btnNewSession.addEventListener('click', () => {
        if (confirm('Start a new session? Current session will be saved.')) {
            controller.saveState();
            controller.createNewSession();
            controller.restoreVisualization();
            populateSessionSelect();
        }
    });

    // Switch session
    sessionSelect.addEventListener('change', (e) => {
        if (e.target.value) {
            controller.switchSession(e.target.value);
            controller.restoreVisualization();
        }
    });

    // Rename session
    sessionName.addEventListener('blur', () => {
        controller.state.name = sessionName.textContent.trim();
        controller.saveState();
        populateSessionSelect();
    });

    // Populate session dropdown
    function populateSessionSelect() {
        const sessions = JSON.parse(localStorage.getItem('pf_sessions') || '[]');
        sessionSelect.innerHTML = '<option value="">-- Sessions --</option>';
        
        sessions.forEach(id => {
            const data = localStorage.getItem(`pf_session_${id}`);
            if (data) {
                const session = JSON.parse(data);
                const option = document.createElement('option');
                option.value = id;
                option.textContent = session.name;
                if (id === controller.state.id) option.selected = true;
                sessionSelect.appendChild(option);
            }
        });
    }

    // Update status indicator
    function updateStatus(state, text) {
        statusIndicator.className = `status ${state}`;
        statusIndicator.textContent = text;
    }

    // Expose for external use
    window.updateStatus = updateStatus;

    // Initial population
    populateSessionSelect();
    sessionName.textContent = controller.state.name;
}
```

### 12.7 Q&A Panel Component (qa-panel.js)

```javascript
export function initQAPanel(controller) {
    const input = document.getElementById('qa-input');
    const btnAsk = document.getElementById('btn-ask');
    const response = document.getElementById('qa-response');

    async function askQuestion() {
        const question = input.value.trim();
        if (!question) return;

        // Show loading
        btnAsk.disabled = true;
        response.textContent = 'Thinking...';
        window.updateStatus?.('processing', 'Answering...');

        try {
            const answer = await controller.askQuestion(question);
            response.textContent = answer;
        } catch (err) {
            response.textContent = 'Error: ' + err.message;
        } finally {
            btnAsk.disabled = false;
            window.updateStatus?.('idle', 'Idle');
        }
    }

    btnAsk.addEventListener('click', askQuestion);
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') askQuestion();
    });

    // Tab navigation
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            btn.classList.add('active');
            document.getElementById(btn.dataset.tab).classList.add('active');
        });
    });
}
```

### 12.8 Updated Proxy with CORS Preflight

```javascript
// Cloudflare Worker with CORS handling
export default {
    async fetch(request, env) {
        // Handle CORS preflight
        if (request.method === 'OPTIONS') {
            return new Response(null, {
                headers: {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Max-Age': '86400'
                }
            });
        }

        if (request.method !== 'POST') {
            return new Response('Method not allowed', { status: 405 });
        }

        try {
            const { prompt, model = 'gemini-2.0-flash', useGrounding } = await request.json();

            const geminiUrl = `https://generativelanguage.googleapis.com/v1/models/${model}:generateContent`;

            const body = {
                contents: [{ parts: [{ text: prompt }] }],
                generationConfig: {
                    responseMimeType: 'application/json'
                }
            };

            if (useGrounding) {
                body.tools = [{ google_search: {} }];
            }

            const response = await fetch(geminiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'x-goog-api-key': env.GEMINI_API_KEY
                },
                body: JSON.stringify(body)
            });

            const data = await response.json();

            // Handle API errors
            if (data.error) {
                return new Response(JSON.stringify({ error: data.error.message }), {
                    status: 400,
                    headers: {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    }
                });
            }

            return new Response(JSON.stringify({
                text: data.candidates?.[0]?.content?.parts?.[0]?.text || ''
            }), {
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                }
            });
        } catch (err) {
            return new Response(JSON.stringify({ error: err.message }), {
                status: 500,
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                }
            });
        }
    }
};
```

### 12.9 Enhanced SpeechRecognitionModule

```javascript
export class SpeechRecognitionModule {
    constructor(onChunk, wordLimit = 75, timeLimit = 8000) {
        // Check for browser support
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            throw new Error('Speech recognition not supported');
        }

        this.recognition = new SpeechRecognition();
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        this.recognition.lang = 'en-GB';

        this.onChunk = onChunk;
        this.wordLimit = wordLimit;
        this.timeLimit = timeLimit;

        this.buffer = '';
        this.lastSentIndex = 0;
        this.startTime = null;
        this.lastChunkTime = 0;
        this.lastChunkSentAt = null;
        this.checkInterval = null;

        this.setupHandlers();
    }

    setupHandlers() {
        this.recognition.onresult = (event) => {
            let transcript = '';
            for (let i = 0; i < event.results.length; i++) {
                transcript += event.results[i][0].transcript;
            }
            this.buffer = transcript;
            this.checkForChunk();
        };

        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            if (event.error === 'no-speech') {
                // Restart on no-speech error
                this.recognition.stop();
                setTimeout(() => this.recognition.start(), 100);
            }
        };

        this.recognition.onend = () => {
            // Auto-restart if we didn't stop intentionally
            if (this.isRunning) {
                this.recognition.start();
            }
        };
    }

    start() {
        this.startTime = Date.now();
        this.isRunning = true;
        this.recognition.start();

        // Check for time-based chunks every second
        this.checkInterval = setInterval(() => this.checkForChunk(), 1000);
    }

    stop() {
        this.isRunning = false;
        this.recognition.stop();
        if (this.checkInterval) {
            clearInterval(this.checkInterval);
        }

        // Send any remaining buffer
        const remaining = this.buffer.slice(this.lastSentIndex).trim();
        if (remaining) {
            this.sendChunk(remaining);
        }
    }

    checkForChunk() {
        const newText = this.buffer.slice(this.lastSentIndex).trim();
        if (!newText) return;

        const words = newText.split(/\s+/);
        const timeSinceLast = this.lastChunkSentAt ? Date.now() - this.lastChunkSentAt : Infinity;

        if (words.length >= this.wordLimit || timeSinceLast > this.timeLimit) {
            this.sendChunk(newText);
        }
    }

    sendChunk(text) {
        const now = (Date.now() - this.startTime) / 1000;
        this.onChunk({
            text: text,
            startTime: this.lastChunkTime,
            endTime: now
        });

        this.lastSentIndex = this.buffer.length;
        this.lastChunkTime = now;
        this.lastChunkSentAt = Date.now();
    }
}
```

### 12.10 Graph Initialisation (graph.js)

```javascript
import cytoscape from 'cytoscape';
import fcose from 'cytoscape-fcose';

// Register fcose layout
cytoscape.use(fcose);

export function initGraph(containerId) {
    const cy = cytoscape({
        container: document.getElementById(containerId),

        style: [
            // Default node (ghost)
            {
                selector: 'node',
                style: {
                    'label': 'data(label)',
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'background-color': '#666',
                    'color': '#fff',
                    'font-size': '12px',
                    'text-outline-width': 2,
                    'text-outline-color': '#333',
                    'border-width': 2,
                    'border-style': 'dashed',
                    'border-color': '#888',
                    'opacity': 0.7,
                    'width': 40,
                    'height': 40
                }
            },
            // Solid node
            {
                selector: 'node.solid',
                style: {
                    'background-color': '#4a9eff',
                    'border-style': 'solid',
                    'border-color': '#4a9eff',
                    'opacity': 1
                }
            },
            // Keystone node
            {
                selector: 'node.keystone',
                style: {
                    'width': 60,
                    'height': 60,
                    'font-size': 14,
                    'font-weight': 'bold',
                    'background-color': '#f59e0b',
                    'border-color': '#f59e0b'
                }
            },
            // Node with reference
            {
                selector: 'node.has-reference',
                style: {
                    'border-width': 4,
                    'border-color': '#22c55e'
                }
            },
            // Flower background (cluster indicator)
            {
                selector: 'node.flower-bg',
                style: {
                    'background-color': 'rgba(74, 158, 255, 0.1)',
                    'border-width': 1,
                    'border-color': 'rgba(74, 158, 255, 0.3)',
                    'border-style': 'dashed',
                    'width': 200,
                    'height': 200,
                    'shape': 'ellipse',
                    'z-index': -1,
                    'label': 'data(label)',
                    'text-valign': 'bottom',
                    'text-margin-y': 10,
                    'font-size': 10,
                    'color': '#888'
                }
            },
            // Edges
            {
                selector: 'edge',
                style: {
                    'width': 2,
                    'line-color': '#555',
                    'target-arrow-color': '#555',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'opacity': 0.7
                }
            }
        ],

        layout: {
            name: 'fcose',
            animate: true,
            animationDuration: 500,
            fit: true,
            padding: 50
        },

        // Interaction options
        minZoom: 0.3,
        maxZoom: 3,
        wheelSensitivity: 0.3
    });

    // Node click handler for references
    cy.on('tap', 'node', function(evt) {
        const nodeId = evt.target.id();
        // Dispatch custom event for reference display
        window.dispatchEvent(new CustomEvent('nodeSelected', { detail: { nodeId } }));
    });

    return cy;
}
```

---

## 13. File Structure

```
plasticflower-lite/
├── index.html                   # Main HTML (Section 12.2)
├── style.css                    # All styles (Section 12.3)
├── package.json                 # Dependencies (Section 12.1)
├── vite.config.js               # Vite config (optional)
├── src/
│   ├── main.js                  # Entry point (Section 12.4)
│   ├── modules/
│   │   ├── speech.js            # SpeechRecognitionModule (Section 12.9)
│   │   ├── gemini.js            # GeminiClient (Section 5.2)
│   │   ├── session.js           # SessionController (Sections 5.3 + 12.5)
│   │   └── export.js            # Export functions (Section 8)
│   └── components/
│       ├── graph.js             # Cytoscape setup (Section 12.10)
│       ├── controls.js          # UI controls (Section 12.6)
│       └── qa-panel.js          # Q&A interface (Section 12.7)
└── proxy/
    └── worker.js                # Cloudflare Worker (Section 12.8)
```

---

## 14. Robustness (Validation & Error Handling)

This section adds industrial-grade robustness borrowed from the full project.

### 14.1 Schema Validation with Zod

Add Zod for runtime validation (like Pydantic in the backend):

```bash
npm install zod
```

**Create `src/schemas/index.js`:**

```javascript
import { z } from 'zod';

// === Node Schemas ===
export const ExtractedNodeSchema = z.object({
    label: z.string().min(1).max(120),
    type: z.string().min(1).max(120),
    confidence: z.number().min(0).max(1)
});

export const DuplicateSchema = z.object({
    newLabel: z.string().min(1),
    existingLabel: z.string().min(1),
    confidence: z.number().min(0).max(1)
});

// === Relationship Schemas ===
export const RelationshipCategorySchema = z.enum([
    'CAUSAL', 'STRUCTURAL', 'COMPARATIVE', 'TEMPORAL', 'ASSOCIATIVE'
]);

export const ExtractedRelationshipSchema = z.object({
    source: z.string().min(1),
    target: z.string().min(1),
    category: RelationshipCategorySchema,
    description: z.string().min(2).max(80),
    confidence: z.number().min(0).max(1).default(0.7)
});

// === Builder Response ===
export const BuilderResponseSchema = z.object({
    nodes: z.array(ExtractedNodeSchema).default([]),
    relationships: z.array(ExtractedRelationshipSchema).default([]),
    duplicates: z.array(DuplicateSchema).default([])
});

// === Gardener Response ===
export const CorrectionSchema = z.object({
    original: z.string().min(1),
    correction: z.string().min(1),
    confidence: z.number().min(0).max(1)
});

export const MergeActionSchema = z.object({
    keep: z.string().min(1),
    absorb: z.array(z.string().min(1))
});

export const FlowerSchema = z.object({
    label: z.string().min(2).max(60),
    stemNodeId: z.string().min(1),
    memberIds: z.array(z.string().min(1)).min(3)
});

export const GardenerResponseSchema = z.object({
    corrections: z.array(CorrectionSchema).default([]),
    confirmations: z.array(z.string()).default([]),
    merges: z.array(MergeActionSchema).default([]),
    flowers: z.array(FlowerSchema).default([]),
    keystones: z.array(z.string()).default([])
});

// === Research Response ===
export const ReferenceSchema = z.object({
    title: z.string().min(1).max(200),
    url: z.string().url().or(z.literal('')),
    summary: z.string().min(10).max(500),
    type: z.enum(['organisation', 'funding', 'concept', 'person']),
    confidence: z.number().min(0).max(1)
});

// === Q&A Response ===
export const AnswerSchema = z.object({
    answer: z.string().min(1),
    citations: z.array(z.object({
        text: z.string(),
        timestamp: z.number().optional()
    })).default([])
});
```

### 14.2 Custom Error Classes

**Create `src/errors/index.js`:**

```javascript
export class PlasticFlowerError extends Error {
    constructor(message, code = 'unknown') {
        super(message);
        this.name = 'PlasticFlowerError';
        this.code = code;
        this.timestamp = new Date().toISOString();
    }
}

export class LLMError extends PlasticFlowerError {
    constructor(message, { code = 'llm_error', status, retryable = false } = {}) {
        super(message, code);
        this.name = 'LLMError';
        this.status = status;
        this.retryable = retryable;
    }
}

export class ValidationError extends PlasticFlowerError {
    constructor(message, { code = 'validation_error', zodError } = {}) {
        super(message, code);
        this.name = 'ValidationError';
        this.zodError = zodError;
        this.issues = zodError?.issues || [];
    }
}

export class StorageError extends PlasticFlowerError {
    constructor(message, { code = 'storage_error', quota = false } = {}) {
        super(message, code);
        this.name = 'StorageError';
        this.quotaExceeded = quota;
    }
}

export class SpeechError extends PlasticFlowerError {
    constructor(message, { code = 'speech_error', browserError } = {}) {
        super(message, code);
        this.name = 'SpeechError';
        this.browserError = browserError;
    }
}

// Error codes for easy handling
export const ErrorCodes = {
    // LLM errors
    LLM_REQUEST_FAILED: 'llm_request_failed',
    LLM_RATE_LIMITED: 'llm_rate_limited',
    LLM_INVALID_RESPONSE: 'llm_invalid_response',
    LLM_TIMEOUT: 'llm_timeout',
    
    // Validation errors
    SCHEMA_VALIDATION_FAILED: 'schema_validation_failed',
    INVALID_NODE_ID: 'invalid_node_id',
    INVALID_SESSION: 'invalid_session',
    
    // Storage errors
    QUOTA_EXCEEDED: 'quota_exceeded',
    PARSE_ERROR: 'parse_error',
    
    // Speech errors
    NOT_SUPPORTED: 'not_supported',
    PERMISSION_DENIED: 'permission_denied',
    NETWORK_ERROR: 'network_error'
};
```

### 14.3 Validated GeminiClient

**Update `src/modules/gemini.js`:**

```javascript
import { 
    BuilderResponseSchema, 
    GardenerResponseSchema, 
    ReferenceSchema 
} from '../schemas/index.js';
import { LLMError, ValidationError, ErrorCodes } from '../errors/index.js';

export class GeminiClient {
    constructor(proxyUrl, options = {}) {
        this.proxyUrl = proxyUrl;
        this.maxRetries = options.maxRetries || 3;
        this.retryDelayMs = options.retryDelayMs || 1000;
        this.timeoutMs = options.timeoutMs || 30000;
    }

    async extract(chunk, existingNodes) {
        const prompt = this._buildExtractPrompt(chunk, existingNodes);
        const raw = await this._callWithRetry(prompt);
        return this._validateResponse(raw, BuilderResponseSchema, 'extract');
    }

    async garden(fullState) {
        const prompt = this._buildGardenPrompt(fullState);
        const raw = await this._callWithRetry(prompt);
        return this._validateResponse(raw, GardenerResponseSchema, 'garden');
    }

    async research(nodeLabel, context) {
        const prompt = this._buildResearchPrompt(nodeLabel, context);
        const raw = await this._callWithRetry(prompt, { useGrounding: true });
        return this._validateResponse(raw, ReferenceSchema, 'research');
    }

    async askQuestion(question, fullState) {
        const prompt = this._buildQAPrompt(question, fullState);
        // Q&A returns free text, minimal validation
        const raw = await this._callWithRetry(prompt);
        return typeof raw === 'string' ? raw : raw.answer || JSON.stringify(raw);
    }

    // === Private Methods ===

    async _callWithRetry(prompt, options = {}) {
        let lastError;
        
        for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
            try {
                return await this._call(prompt, options);
            } catch (err) {
                lastError = err;
                
                // Don't retry non-retryable errors
                if (err instanceof LLMError && !err.retryable) {
                    throw err;
                }
                
                // Exponential backoff
                if (attempt < this.maxRetries) {
                    const delay = this.retryDelayMs * Math.pow(2, attempt - 1);
                    console.log(`[Gemini] Retry ${attempt}/${this.maxRetries} in ${delay}ms`);
                    await this._sleep(delay);
                }
            }
        }
        
        throw lastError;
    }

    async _call(prompt, options = {}) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeoutMs);

        try {
            const response = await fetch(this.proxyUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompt,
                    model: options.model || 'gemini-2.0-flash',
                    useGrounding: options.useGrounding || false
                }),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                const isRateLimit = response.status === 429;
                throw new LLMError(
                    `API request failed: ${response.status}`,
                    {
                        code: isRateLimit ? ErrorCodes.LLM_RATE_LIMITED : ErrorCodes.LLM_REQUEST_FAILED,
                        status: response.status,
                        retryable: isRateLimit || response.status >= 500
                    }
                );
            }

            const data = await response.json();
            
            if (data.error) {
                throw new LLMError(data.error, { code: ErrorCodes.LLM_REQUEST_FAILED });
            }

            // Parse JSON response
            try {
                return JSON.parse(data.text);
            } catch {
                // If not JSON, return as-is (for Q&A responses)
                return data.text;
            }
        } catch (err) {
            if (err.name === 'AbortError') {
                throw new LLMError('Request timeout', {
                    code: ErrorCodes.LLM_TIMEOUT,
                    retryable: true
                });
            }
            if (err instanceof LLMError) throw err;
            throw new LLMError(err.message, {
                code: ErrorCodes.LLM_REQUEST_FAILED,
                retryable: true
            });
        }
    }

    _validateResponse(data, schema, operation) {
        const result = schema.safeParse(data);
        
        if (!result.success) {
            console.error(`[Gemini] Validation failed for ${operation}:`, result.error.issues);
            throw new ValidationError(
                `Invalid ${operation} response from Gemini`,
                { code: ErrorCodes.SCHEMA_VALIDATION_FAILED, zodError: result.error }
            );
        }
        
        return result.data;
    }

    _sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // === Prompt Builders (unchanged but extracted) ===
    
    _buildExtractPrompt(chunk, existingNodes) {
        return `
You are extracting entities and relationships from speech.

Existing nodes: ${JSON.stringify(existingNodes.map(n => n.label))}

New text: "${chunk.text}"

Extract:
1. New entities (not already in existing nodes)
2. Relationships between entities

Return valid JSON only:
{
    "nodes": [{"label": "...", "type": "concept|person|organisation|funding", "confidence": 0.9}],
    "relationships": [{"source": "...", "target": "...", "category": "CAUSAL|STRUCTURAL|COMPARATIVE|TEMPORAL|ASSOCIATIVE", "description": "..."}],
    "duplicates": [{"newLabel": "...", "existingLabel": "...", "confidence": 0.9}]
}`;
    }

    _buildGardenPrompt(fullState) {
        return `
You are the Gardener for a knowledge graph. Analyse and improve.

Transcript: ${fullState.chunks.map(c => c.text).join(' ')}

Nodes: ${JSON.stringify(fullState.nodes)}
Relationships: ${JSON.stringify(fullState.relationships)}
Vocabulary: ${JSON.stringify(fullState.vocabulary)}

Tasks:
1. PROOFREAD: Find STT errors (phonetic spellings like "see dare" -> "CeADAR")
2. CONFIRM: Which ghost nodes should become solid?
3. MERGE: Which nodes represent the same thing?
4. CLUSTER: Group related nodes into Flowers (3+ nodes, 2+ connections)
5. KEYSTONES: Which nodes are bridges between topics?

Return valid JSON only:
{
    "corrections": [{"original": "...", "correction": "...", "confidence": 0.9}],
    "confirmations": ["node_id"],
    "merges": [{"keep": "node_id", "absorb": ["node_id"]}],
    "flowers": [{"label": "...", "stemNodeId": "...", "memberIds": ["..."]}],
    "keystones": ["node_id"]
}`;
    }

    _buildResearchPrompt(nodeLabel, context) {
        return `
You are a research assistant. Find authoritative information about this entity.

Entity: ${nodeLabel}
Context from transcript: ${context}

Search for:
1. Official definition or description
2. Official website (if organisation/funding scheme)
3. Key facts relevant to the context

Return valid JSON only:
{
    "title": "Official name of the entity",
    "url": "Primary official URL or empty string",
    "summary": "2-3 sentence description",
    "type": "organisation|funding|concept|person",
    "confidence": 0.0-1.0
}

If you cannot find reliable information, set confidence to 0.`;
    }

    _buildQAPrompt(question, fullState) {
        const context = `
Transcript: ${fullState.chunks.map(c => `[${c.startTime}s] ${c.text}`).join('\n')}

Knowledge Graph:
Nodes: ${fullState.nodes.map(n => `- ${n.label} (${n.type})`).join('\n')}
Relationships: ${fullState.relationships.map(r => `- ${r.sourceId} ${r.description} ${r.targetId}`).join('\n')}`;

        return `
Based on this session, answer the question.
Cite sources using [Time: Xs] format.

Context:
${context}

Question: ${question}`;
    }
}
```

### 14.4 Safe localStorage Wrapper

**Create `src/modules/storage.js`:**

```javascript
import { StorageError, ErrorCodes } from '../errors/index.js';

const STORAGE_PREFIX = 'pf_';
const MAX_SESSION_SIZE_BYTES = 4 * 1024 * 1024; // 4MB per session (safe for 5MB quota)

export class StorageManager {
    constructor() {
        this._checkSupport();
    }

    _checkSupport() {
        try {
            const test = '__storage_test__';
            localStorage.setItem(test, test);
            localStorage.removeItem(test);
        } catch {
            throw new StorageError('localStorage not available', { code: 'not_supported' });
        }
    }

    // === Session Operations ===

    saveSession(session) {
        const key = `${STORAGE_PREFIX}session_${session.id}`;
        const data = JSON.stringify(session);
        
        // Check size before saving
        const sizeBytes = new Blob([data]).size;
        if (sizeBytes > MAX_SESSION_SIZE_BYTES) {
            throw new StorageError(
                `Session too large: ${(sizeBytes / 1024 / 1024).toFixed(2)}MB`,
                { code: ErrorCodes.QUOTA_EXCEEDED, quota: true }
            );
        }

        try {
            localStorage.setItem(key, data);
            this._updateSessionList(session.id);
        } catch (err) {
            if (err.name === 'QuotaExceededError') {
                throw new StorageError(
                    'Storage quota exceeded. Export and clear old sessions.',
                    { code: ErrorCodes.QUOTA_EXCEEDED, quota: true }
                );
            }
            throw new StorageError(err.message);
        }
    }

    loadSession(sessionId) {
        const key = `${STORAGE_PREFIX}session_${sessionId}`;
        const data = localStorage.getItem(key);
        
        if (!data) return null;
        
        try {
            return JSON.parse(data);
        } catch {
            throw new StorageError(
                `Failed to parse session ${sessionId}`,
                { code: ErrorCodes.PARSE_ERROR }
            );
        }
    }

    deleteSession(sessionId) {
        const key = `${STORAGE_PREFIX}session_${sessionId}`;
        localStorage.removeItem(key);
        
        const sessions = this.listSessions().filter(id => id !== sessionId);
        localStorage.setItem(`${STORAGE_PREFIX}sessions`, JSON.stringify(sessions));
    }

    listSessions() {
        const data = localStorage.getItem(`${STORAGE_PREFIX}sessions`);
        try {
            return data ? JSON.parse(data) : [];
        } catch {
            return [];
        }
    }

    _updateSessionList(sessionId) {
        const sessions = this.listSessions();
        if (!sessions.includes(sessionId)) {
            sessions.push(sessionId);
            localStorage.setItem(`${STORAGE_PREFIX}sessions`, JSON.stringify(sessions));
        }
    }

    // === Active Session ===

    getActiveSessionId() {
        return localStorage.getItem(`${STORAGE_PREFIX}active_session`);
    }

    setActiveSessionId(sessionId) {
        localStorage.setItem(`${STORAGE_PREFIX}active_session`, sessionId);
    }

    // === Storage Stats ===

    getStorageStats() {
        let totalBytes = 0;
        const sessions = [];

        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key?.startsWith(STORAGE_PREFIX)) {
                const value = localStorage.getItem(key);
                const bytes = new Blob([value]).size;
                totalBytes += bytes;
                
                if (key.includes('session_')) {
                    const id = key.replace(`${STORAGE_PREFIX}session_`, '');
                    sessions.push({ id, bytes });
                }
            }
        }

        return {
            totalBytes,
            totalMB: (totalBytes / 1024 / 1024).toFixed(2),
            sessionCount: sessions.length,
            sessions: sessions.sort((a, b) => b.bytes - a.bytes),
            quotaWarning: totalBytes > 3 * 1024 * 1024 // Warn at 3MB
        };
    }

    // === Cleanup ===

    clearOldSessions(keepCount = 5) {
        const sessions = this.listSessions();
        if (sessions.length <= keepCount) return 0;

        // Sort by last modified (newest first) - would need metadata for this
        // For now, just keep the last N
        const toDelete = sessions.slice(0, sessions.length - keepCount);
        toDelete.forEach(id => this.deleteSession(id));
        
        return toDelete.length;
    }
}

export const storage = new StorageManager();
```

### 14.5 Updated Dependencies

Add to `package.json`:

```json
{
  "dependencies": {
    "cytoscape": "^3.28.1",
    "cytoscape-fcose": "^2.2.0",
    "zod": "^3.22.4"
  }
}
```

### 14.6 Error Display Component

**Create `src/components/error-handler.js`:**

```javascript
import { PlasticFlowerError, LLMError, ValidationError, StorageError } from '../errors/index.js';

class ErrorHandler {
    constructor() {
        this.toastContainer = document.getElementById('error-toast');
        this.messageEl = document.getElementById('error-message');
        this.dismissBtn = document.getElementById('dismiss-error');
        
        this.dismissBtn?.addEventListener('click', () => this.hide());
        
        // Global error handler
        window.addEventListener('unhandledrejection', (event) => {
            this.handle(event.reason);
        });
    }

    handle(error) {
        console.error('[Error]', error);
        
        let message = 'An unexpected error occurred';
        let severity = 'error';
        
        if (error instanceof LLMError) {
            if (error.code === 'llm_rate_limited') {
                message = 'Rate limited. Please wait a moment and try again.';
                severity = 'warning';
            } else if (error.code === 'llm_timeout') {
                message = 'Request timed out. Retrying...';
                severity = 'warning';
            } else {
                message = `AI service error: ${error.message}`;
            }
        } else if (error instanceof ValidationError) {
            message = `Invalid response: ${error.message}`;
            // Log details for debugging
            console.error('Validation issues:', error.issues);
        } else if (error instanceof StorageError) {
            if (error.quotaExceeded) {
                message = 'Storage full! Export your sessions and clear old ones.';
            } else {
                message = `Storage error: ${error.message}`;
            }
        } else if (error instanceof PlasticFlowerError) {
            message = error.message;
        } else if (error instanceof Error) {
            message = error.message;
        }

        this.show(message, severity);
    }

    show(message, severity = 'error') {
        if (!this.toastContainer) return;
        
        this.messageEl.textContent = message;
        this.toastContainer.className = `toast visible ${severity}`;
        
        // Auto-hide warnings after 5s
        if (severity === 'warning') {
            setTimeout(() => this.hide(), 5000);
        }
    }

    hide() {
        this.toastContainer?.classList.remove('visible');
    }
}

export const errorHandler = new ErrorHandler();
```

### 14.7 Summary of Robustness Additions

| Feature | Before | After |
|---------|--------|-------|
| **Schema validation** | `JSON.parse()` only | Zod schemas with type safety |
| **Error types** | Generic `Error` | Custom classes with codes |
| **Retry logic** | None | Exponential backoff (3 attempts) |
| **Timeout handling** | None | 30s timeout with abort |
| **Rate limit handling** | None | Detected and retried |
| **Storage safety** | Raw localStorage | Size checks, quota handling |
| **User feedback** | Alert/console | Toast notifications by severity |
| **Debug info** | Limited | Structured logging with context |

---

## 15. Troubleshooting

### Common Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| "Speech recognition not supported" | Wrong browser | Use Chrome or Edge |
| Microphone not working | Permission denied | Check browser permissions |
| CORS error on API calls | Proxy not deployed | Deploy worker, check URL |
| "No speech" errors | Long silence | Normal - auto-restarts |
| Nodes not appearing | JSON parse error | Check Gemini response format |
| Graph not updating | Cytoscape error | Check browser console |
| localStorage quota exceeded | Too much data | Export and clear old sessions |

### Debug Mode

Add to `main.js` for debugging:

```javascript
// Expose internals for debugging
window.pf = { cy, controller, speech, gemini };

// Log all Gemini calls
const originalCall = gemini.call.bind(gemini);
gemini.call = async (prompt, options) => {
    console.log('Gemini call:', { prompt: prompt.substring(0, 100), options });
    const result = await originalCall(prompt, options);
    console.log('Gemini response:', result);
    return result;
};
```

### Testing Without Microphone

Mock speech input for testing:

```javascript
// In browser console
const mockChunks = [
    "Today we're discussing machine learning and neural networks",
    "The CeADAR centre in Dublin is leading AI research",
    "UKRI provides significant funding for innovation"
];

for (const text of mockChunks) {
    await window.pf.controller.processChunk({
        text,
        startTime: Date.now() / 1000,
        endTime: Date.now() / 1000 + 8
    });
}
```

### Verifying Proxy

Test your proxy endpoint:

```bash
curl -X POST https://your-worker.workers.dev \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Say hello", "model": "gemini-2.0-flash"}'
```

Expected response:
```json
{"text": "Hello!"}
```

---

## 16. Cost Estimate

### Per 90-Minute Session

| Operation | Calls | Tokens/Call | Total Tokens | Cost (Gemini Flash) |
|-----------|-------|-------------|--------------|---------------------|
| Extraction | ~40 | ~2,000 | 80,000 | $0.006 |
| Gardening | ~60 | ~5,000 | 300,000 | $0.023 |
| Q&A | ~5 | ~10,000 | 50,000 | $0.004 |
| Research | ~5 | ~3,000 | 15,000 | $0.001 |
| **Total** | | | **445,000** | **~$0.03** |

### Monthly (10 sessions)

~$0.30/month for Gemini API usage.

---

## Summary

plasticFlower Lite provides a **fast path to a working demo** with minimal infrastructure:

- Browser-native STT
- Gemini for all intelligence
- Cytoscape.js for visualization
- localStorage for persistence
- 20-line proxy for API security

**Trade-offs:**
- No cross-session memory
- Fragile persistence
- Single device only

**Best for:**
- Demos and proof-of-concept
- Learning the core concepts
- Quick experiments
- Situations where full Neo4j stack is overkill

When you need durability and cross-session intelligence, upgrade to the [full architecture](../ARCHITECTURE_ADVISORY.md).


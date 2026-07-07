# The Gardener System - Simple Overview

**Last Updated:** 2025-12-20

---

## 🌱 What is the Gardener?

The **Gardener** is an AI agent that runs in the background (every 24 seconds by default) to:
1. Review "ghost" nodes (unconfirmed ideas from your speech)
2. Decide if they should become "solid" (confirmed) nodes
3. Find new relationships between nodes
4. Organize nodes into "flowers" (thematic clusters)

Think of it as an AI curator that tidies up your knowledge graph while you talk.

---

## 📊 How Data is Stored (Neo4j Graph Database)

### Node Storage
```
Node {
  id: "node_abc123"
  label: "Machine Learning"
  status: "ghost" or "solid"
  timestamps: [1703001234, 1703002345]  // When mentioned
  confidence: 0.85
  flower_id: "flower_xyz" (optional, derived from BELONGS_TO relationship)
}
```

**Two types:**
- **Ghost nodes:** Tentative ideas the Builder agent created from your speech
- **Solid nodes:** Confirmed concepts the Gardener has validated

**Flower Membership:**
- Stored as explicit `(:Node)-[:BELONGS_TO]->(:Flower)` relationships in Neo4j
- The `flower_id` field in API responses is populated from these relationships
- This creates a proper graph structure for traversal and visualization

### Relationship Storage
```
Relationship {
  id: "rel_def456"
  source_id: "node_abc123"
  target_id: "node_xyz789"
  description: "is a subset of"
  category: "hierarchical" | "semantic" | "temporal"
  source: "builder" | "gardener" | "user"
  confidence: 0.9
}
```

### Flower Storage (Clusters)
```
Flower {
  id: "flower_ghi789"
  label: "AI & Technology"
  stem_node_id: "node_abc123"  // Central "hub" node
  criteria: "Nodes related to artificial intelligence"
}
```

**Flowers organize nodes by theme.** The "stem" is the most central/important node in the cluster.

---

## 🔄 The Gardener Cycle (Step-by-Step)

### Trigger Conditions
The Gardener runs when:
1. **Recent Builder activity** (you just spoke)
2. **Ghost nodes exist** (unconfirmed ideas waiting)
3. **Every 24 seconds** (when conditions are met)

### The Process

#### **Step 1: Gather Context** (Lines 151-156)
```python
ghost_nodes = await list_nodes(session_id, status="ghost")
solid_nodes = await list_nodes(session_id, status="solid")
relationships = await list_relationships(session_id)
flowers = await list_flowers(session_id)
recent_transcript = await get_recent_transcript(word_limit=1000)
```

The Gardener loads:
- All existing nodes (ghost and solid)
- All relationships between them
- Current flower groupings
- **Last 1000 words of your speech** (for context, NOT the full transcript!)

**Important:** The Gardener does NOT see your entire conversation history - only the most recent 1000 words. This is a deliberate design choice to:
- Keep LLM context focused on current discussion
- Reduce token costs and latency
- Prevent information overload
- Focus decisions on recent context

**How it works:** The system fetches transcript chunks in reverse chronological order (newest first), concatenates their text, and stops when reaching 1000 words. For a typical speaking rate of ~150 words/minute, this gives the Gardener approximately **6-7 minutes of recent context**.

---

#### **Step 2: AI Decision Making** (Lines 165-171)
```python
result = await gardener_agent.run(
    ghost_nodes=ghost_nodes,
    solid_nodes=solid_nodes,
    relationships=relationships,
    flowers=flowers,
    recent_transcript=recent_transcript,
)
```

The Gardener AI (using Gemini 2.0 Flash) analyzes everything and decides:

**A. Node Actions:**
- **Confirm:** "This ghost node is valid, make it solid"
- **Merge:** "This ghost is a duplicate of solid node X"
- **Remove:** "This ghost doesn't fit or is nonsense"

**B. New Relationships:**
- "Node A 'is related to' Node B"
- "Node C 'is a type of' Node D"
- Includes confidence scores

**C. Flower Actions:**
- **Create:** "These 5 nodes form a cluster about 'Machine Learning'"
- **Update:** "Add node X to existing flower Y"
- **Dissolve:** "This flower no longer makes sense"
- **Assign stem:** "Node X is the hub of this cluster"

---

#### **Step 3: Apply Actions** (Lines 186-200)
Actions are applied in a **specific order** to avoid conflicts:

**3a. Node Actions First:**
```python
await apply_node_actions(...)
```
- Confirms ghosts → solid
- Merges duplicates
- Removes invalid nodes
- **Emits SSE event:** `node_updated` or `node_merged` or `node_removed`

**3b. New Relationships:**
```python
await apply_new_relationships(...)
```
- Creates new edges in the graph
- **Emits SSE event:** `relationship_added`

**3c. Flower Actions:**
```python
await apply_flower_actions(...)
```
- Creates/updates/dissolves clusters
- Assigns stem nodes
- **Emits SSE events:** `flower_created`, `flower_updated`, `flower_dissolved`

**3d. Completion Signal:**
```python
await broadcast(GardenerCycleEvent)
```
- **Emits SSE event:** `gardener_cycle` (tells UI cycle is complete)

---

## 📡 How UI Receives Updates (SSE Stream)

### The Connection

When you open a session, the frontend establishes a **Server-Sent Events (SSE)** connection:

```typescript
// frontend/src/hooks/useSSE.ts
const eventSource = new EventSource(`${API}/sessions/${sessionId}/stream`)
```

This is a **one-way real-time stream** from backend → frontend.

---

### Event Flow

```
Backend Gardener                SSE Stream              Frontend UI
     │                              │                        │
     │ 1. Confirms ghost node       │                        │
     ├─────── node_updated ─────────>                        │
     │                              │                        │
     │ 2. Creates relationship      │                        │
     ├──── relationship_added ──────>                        │
     │                              │                        │
     │ 3. Updates flower            │                        │
     ├───── flower_updated ─────────>                        │
     │                              │                        │
     │ 4. Cycle complete            │                        │
     ├───── gardener_cycle ─────────>                        │
     │                              │        Triggers UI update
     │                              │        ↓
     │                              │   useSSE hook fires
     │                              │   ↓
     │                              │   GraphCanvas receives new data
     │                              │   ↓
     │                              │   syncGraph() runs
     │                              │   ↓
     │                              │   Animations execute
```

---

## 🎨 How UI Handles Updates (GraphCanvas.tsx)

### The Update Pipeline

#### **1. SSE Event Arrives** (page.tsx)
```typescript
// frontend/src/app/sessions/[sessionId]/page.tsx (simplified)
useSSE({
  sessionId,
  onEvent: (event) => {
    if (event.type === 'node_updated') {
      // Trigger re-fetch of nodes
      refetchNodes()
    }
    if (event.type === 'relationship_added') {
      // Trigger re-fetch of relationships
      refetchRelationships()
    }
    if (event.type === 'flower_updated') {
      // Trigger re-fetch of flowers
      refetchFlowers()
    }
  }
})
```

**Each event type triggers a fresh data fetch from the API.**

---

#### **2. React State Updates**
```typescript
const [nodes, setNodes] = useState([...])
const [relationships, setRelationships] = useState([...])
const [flowers, setFlowers] = useState([...])

// When data changes, React re-renders GraphCanvas
<GraphCanvas nodes={nodes} relationships={relationships} flowers={flowers} />
```

---

#### **3. GraphCanvas Processes Changes** (syncGraph function)
```typescript
useEffect(() => {
  syncGraph(cy, { nodes, relationships, flowers }, ...)
}, [nodes, relationships, flowers])
```

When props change, `syncGraph` runs:

**A. Identifies What Changed:**
```typescript
const desiredNodeIds = new Set(data.nodes.map(n => n.id))
const desiredEdgeIds = new Set(data.relationships.map(r => r.id))
```

**B. Updates Existing Elements:**
```typescript
const existing = cy.getElementById(node.id)
if (existing) {
  existing.data({ ...newData })           // Update data
  existing.animate({ style: {...} })      // Animate changes
}
```

**C. Adds New Elements:**
```typescript
const newNode = cy.add({ data: {...} })
newNode.style({ opacity: 0 })            // Start invisible
newNode.animate({ style: { opacity: 1 } }, { duration: 5000 })  // Fade in
```

**D. Removes Deleted Elements:**
```typescript
cy.nodes().forEach(node => {
  if (!desiredNodeIds.has(node.id())) {
    node.remove()
  }
})
```

**E. Triggers Layout (if needed):**
```typescript
if (needsLayout) {
  const layout = cy.elements().layout(FCOSE_OPTIONS)
  layout.run()
  layout.one('layoutstop', () => {
    applyOrganicJitter(cy, data)          // Subtle randomization
    applyOrganicPositioning(cy, data)     // Flower arrangement
    scheduleAutoFit(...)                  // Camera movement
  })
}
```

---

## 🎭 What Behaviors You Might See

### During a Gardener Cycle:

**1. Ghost → Solid Transformation:**
- Node color changes from translucent to solid
- Border style changes from dashed to solid
- Size might adjust based on confidence
- **Animation:** 400ms smooth transition

**2. New Relationships Appear:**
- New edges fade in from invisible
- Dashed line "draws" from source to target
- **Animation:** 2000ms fade + draw effect

**3. Nodes Move to Form/Join Flowers:**
- Nodes animate to new positions around their "stem"
- Curved connectors form between stem and petals
- **Animation:** 1200ms position + style change

**4. Stem Node Grows:**
- The hub node of a flower might get larger
- Border becomes thicker/more prominent
- **Animation:** 400ms size change

**5. Camera Adjusts:**
- After all changes settle, viewport smoothly pans/zooms
- Ensures all nodes stay visible
- **Animation:** 2500ms camera movement

---

## 🐛 Common "Fascinating Behaviors" Explained

### **"Nodes suddenly jump or reposition"**
**Cause:** When a node joins a flower, it moves from its old position to a new position around the stem node.

**Technical:** `applyOrganicPositioning` calculates petal positions in a vertical fan above the stem, using polar coordinates (angle + radius).

---

### **"Multiple animations seem to happen at once"**
**Cause:** A single gardener cycle can:
- Confirm 5 ghost nodes (5 style animations)
- Add 3 new relationships (3 edge fade-ins)
- Update 2 flowers (nodes repositioning)
- All within ~2 seconds

**Technical:** We've now fixed this to ensure each element only animates ONCE per cycle (was a bug causing duplicates).

---

### **"Camera moves after things settle"**
**Cause:** The auto-fit waits 1800ms after organic positioning completes, allowing all animations to finish before adjusting the viewport.

**Technical:** `scheduleAutoFit` is debounced to prevent multiple concurrent camera movements.

---

### **"Stem nodes look different"**
**Cause:** Nodes with `stem_node_id` in flowers get special styling:
- Larger size (based on connections)
- Thicker orange border
- Rounded rectangle shape

**Technical:** CSS class `.stem` applies distinct visual hierarchy.

---

### **"Flowers have dashed borders"**
**Cause:** Compound nodes (flowers) use dashed borders to visually distinguish them as containers, not individual nodes.

**Technical:** Cytoscape compound nodes with `border-style: 'dashed'`.

---

## 🔍 Debugging Tips

### Check Console for Events:
```javascript
// In browser console
window.addEventListener('storage', console.log)  // Won't work for SSE

// Better: Add to useSSE.ts temporarily
console.log('SSE Event:', event.type, event.payload)
```

### Watch Network Tab:
- Filter by "EventStream"
- See real-time SSE events as they arrive
- Check event types and payloads

### Check Cytoscape State:
```javascript
// In browser console (when page is open)
window.cy = cyRef.current  // Expose cy instance

// Then inspect:
cy.nodes().length          // How many nodes
cy.edges().length          // How many edges
cy.nodes('.ghost').length  // How many ghosts
cy.nodes('.solid').length  // How many solids
```

---

## 📈 Performance Characteristics

**Typical Gardener Cycle:**
- **LLM Call:** 1-3 seconds (Gemini 2.0 Flash)
- **Database Ops:** 50-200ms (Neo4j queries)
- **SSE Broadcast:** <10ms (per event)
- **Frontend Processing:** <100ms (syncGraph + data fetch)
- **Animations:** 1200-5000ms (visual transitions)

**What This Means:**
You'll typically see changes **2-4 seconds after the Gardener starts**, with animations completing **5-7 seconds total** for a full cycle.

---

## 🎯 Key Takeaway

The Gardener is a **curation agent** that:
1. **Thinks** (analyzes graph + transcript with AI)
2. **Decides** (confirms/merges/removes nodes; creates relationships; organizes flowers)
3. **Acts** (updates Neo4j database)
4. **Communicates** (broadcasts events via SSE)
5. **Displays** (UI receives events, fetches data, animates changes)

The "fascinating behaviors" you see are the **visual representation** of these AI decisions being applied to the graph in real-time, with smooth animations to make the changes comprehensible rather than jarring.

---

## 📚 Related Files

- **Scheduler:** `backend/app/services/scheduler.py` (orchestrates cycles)
- **Agent:** `backend/app/agents/gardener.py` (AI decision making)
- **Graph DB:** `backend/app/services/graph_db.py` (Neo4j operations)
- **SSE Manager:** `backend/app/services/sse_manager.py` (event broadcasting)
- **UI Hook:** `frontend/src/hooks/useSSE.ts` (receives events)
- **UI Component:** `frontend/src/components/graph/GraphCanvas.tsx` (renders changes)

---

## Next Steps for Describing Behaviors

Now that you understand the system, you can describe what you're seeing in terms of:

1. **What phase?** (Node confirmation? Relationship creation? Flower formation?)
2. **How many elements?** (5 nodes moving? 1 relationship appearing?)
3. **Timing?** (All at once? Staggered? Too fast?)
4. **Expected vs Actual?** (Should this be animated? Should this move?)

This will help me understand if behaviors are:
- **Expected** (working as designed)
- **Bug** (something broken in animation system)
- **UX Issue** (working correctly but confusing/jarring)

---

## 🌸 How the LLM Decides What Becomes a Flower

### The Exact Guidance (from gardener.py)

The Gardener LLM receives these specific instructions:

```
2) FORM OR UPDATE FLOWERS
- Flower requires 3+ nodes AND 2+ internal connections
- Provide label (2-5 words), members, and stem_node_id (must be a member)
- Dissolve Flowers that lose coherence (<2 members or weak theme)
```

**Source:** `backend/app/agents/gardener.py` lines 213-216

---

### Minimum Requirements for Flower Creation

**Structural Requirements:**
1. **At least 3 nodes** must be thematically related
2. **At least 2 connections** between those nodes (internal relationships)
3. **Cohesive theme** describable in 2-5 words

**The LLM Must Provide:**
- **Label:** 2-5 word description (e.g., "Machine Learning Concepts")
- **Member IDs:** List of node IDs that belong to the cluster
- **Stem Node ID:** The central/most important node (must be a member)
- **Reason:** Explanation for the action (max 240 characters)

---

### Context the LLM Receives

When deciding about flowers, the Gardener sees:

```
You are a knowledge graph curator. Your task is to review, refine, 
and organise a growing knowledge graph extracted from a live talk.

## GHOST NODES (Pending Review)
- id=node_123 label="neural networks" type="concept" confidence=0.85 ...

## SOLID NODES (Confirmed)
- id=node_456 label="machine learning" type="concept" confidence=0.95 ...
- id=node_789 label="deep learning" type="concept" confidence=0.92 ...

## RELATIONSHIPS
- node_456 -> node_789 [HIERARCHICAL] "is a parent of" (conf=0.90)
- node_789 -> node_123 [STRUCTURAL] "is implemented using" (conf=0.85)

## CURRENT FLOWERS
- id=flower_abc label="AI Concepts" stem=node_456 members=[node_456, node_789]

## RECENT TRANSCRIPT
"...we talked about neural networks and how they relate to machine learning..."

## INSTRUCTIONS
[The rules shown above]
```

**The LLM uses natural language understanding to identify:**
- Thematic coherence
- Semantic relationships
- Central/hub nodes
- Appropriate labels

---

### Decision Examples

#### **Example 1: Creating a Flower**

**Input:**
- 5 nodes: "Python", "JavaScript", "TypeScript", "React", "FastAPI"
- 4 relationships:
  - JavaScript → TypeScript (is a superset of)
  - React → JavaScript (is written in)
  - FastAPI → Python (is a framework for)
  - TypeScript → JavaScript (compiles to)

**LLM Analysis:**
- 3 nodes meet threshold: "Python", "JavaScript", "TypeScript" ✓
- 3 connections between them ✓
- Clear theme: "Programming Languages" ✓
- Most connected node: "JavaScript" = stem ✓

**LLM Output:**
```json
{
  "action": "create",
  "label": "Programming Languages",
  "member_ids": ["node_python", "node_js", "node_ts"],
  "stem_node_id": "node_js",
  "reason": "Three interconnected programming languages with clear hierarchical relationships"
}
```

**What You See:**
- 3 nodes animate to cluster around "JavaScript" (stem)
- Curved connectors form between stem and other nodes
- Flower boundary appears with label "Programming Languages (3)"

---

#### **Example 2: NOT Creating a Flower**

**Input:**
- 3 nodes: "Dogs", "Neural Networks", "Pizza"
- 0 relationships between them

**LLM Analysis:**
- 3 nodes ✓
- BUT only 0 connections ✗ (needs 2+)
- No coherent theme ✗

**LLM Output:** No flower action (nodes remain standalone)

**What You See:** Nothing changes (no flower formed)

---

#### **Example 3: Updating a Flower**

**Input:**
- Existing flower: "Machine Learning" with 3 members
- New confirmed node: "Convolutional Neural Networks"
- New relationship: CNN → Machine Learning (is a technique in)

**LLM Analysis:**
- CNN clearly belongs to "Machine Learning" theme
- Strong connection to existing member
- Maintains flower coherence

**LLM Output:**
```json
{
  "action": "update",
  "flower_id": "flower_ml",
  "member_ids": ["node_ml", "node_nn", "node_dl", "node_cnn"],
  "stem_node_id": "node_ml",
  "reason": "Adding CNN to ML flower due to strong thematic connection"
}
```

**What You See:**
- CNN node animates to join existing flower cluster
- New curved connector forms to stem
- Flower label updates to "Machine Learning (4)"
- Existing members may adjust positions slightly

---

#### **Example 4: Dissolving a Flower**

**Input:**
- Existing flower: "Tech Tools" with 2 members
- One member was just removed (merged into another node)

**LLM Analysis:**
- Only 1 member left ✗ (needs 3+)
- Theme too weak with so few members

**LLM Output:**
```json
{
  "action": "dissolve",
  "flower_id": "flower_tools",
  "reason": "Flower no longer meets minimum member threshold"
}
```

**What You See:**
- Flower boundary fades out
- Remaining node(s) become standalone
- Nodes may reposition to fill space

---

### Why Structural Requirements Matter

The requirement for **2+ internal connections** prevents random grouping:

**Valid Flower Structure:**
```
   ML ←→ DL ←→ NN
   (3 nodes, 2 connections)
   Theme: Clear hierarchical relationship
```

**Invalid Grouping:**
```
   ML    DL    NN
   (3 nodes, 0 connections)
   Theme: No actual relationships
```

The LLM can't just group nodes by similarity - they must have **proven relationships** in the graph.

---

### LLM Decision Making Process

**Phase 1: Identify Candidates**
- Scan all solid nodes
- Look for clusters of 3+ with 2+ connections
- Check for thematic coherence

**Phase 2: Evaluate Existing Flowers**
- Should new nodes be added?
- Are members still coherent?
- Should flower be dissolved?

**Phase 3: Determine Actions**
- Create new flowers for valid clusters
- Update flowers with new members
- Dissolve flowers that lost coherence
- Assign/reassign stem nodes based on centrality

**Phase 4: Generate Output**
- Return structured JSON with actions
- Include reasoning for each decision
- Follow strict schema validation

---

### Stem Node Selection

The LLM chooses stem nodes based on:

1. **Centrality:** Most connected node in the cluster
2. **Importance:** Most fundamental/general concept
3. **Coherence:** Best represents the overall theme

**Example in "Machine Learning" flower:**
- "Machine Learning" = stem (broad parent concept)
- "Deep Learning" = petal (specialized technique)
- "Neural Networks" = petal (implementation)
- "CNN" = petal (specific architecture)

The stem is the **hub** from which specialized concepts branch out.

---

### Dynamic Evolution

Flowers are **not static** - they evolve as the graph grows:

**Scenario: Growing Flower**
1. Start: 3 nodes form flower "AI Concepts"
2. Gardener cycle 1: Add 2 more related nodes → 5 members
3. Gardener cycle 2: Split into two flowers: "Machine Learning" and "Computer Vision"

**Scenario: Shrinking Flower**
1. Start: 5 nodes in flower "Project Tools"
2. Gardener cycle 1: Merge duplicates → 3 members
3. Gardener cycle 2: Remove low-confidence node → 2 members
4. Gardener cycle 3: Dissolve flower (below threshold)

**Scenario: Stem Change**
1. Start: "Python" is stem of "Programming" flower
2. New node: "Programming Languages" concept added
3. Gardener cycle: Switch stem to more general "Programming Languages"

---

### Tuning Flower Behavior (Advanced)

If you wanted to adjust clustering, you could modify the prompt:

**More Aggressive Clustering:**
```python
"- Flower requires 2+ nodes AND 1+ internal connection"
```
*Result:* More, smaller flowers form quickly

**Stricter Clustering:**
```python
"- Flower requires 5+ nodes AND 4+ internal connections"
```
*Result:* Fewer, larger, more densely-connected flowers

**Semantic Constraints:**
```python
"- Only create flowers for concept hierarchies, not loose associations"
```
*Result:* More selective flower formation

**Size Limits:**
```python
"- Maximum 12 nodes per flower to avoid overcrowding"
```
*Result:* Large clusters automatically split

**Current Settings (3+ nodes, 2+ connections)** are well-balanced for natural knowledge graph clustering!

---

### Key Insights

**1. Semantic Understanding**
The LLM uses natural language AI, not hard-coded rules. It understands:
- "Machine Learning" and "Deep Learning" are related concepts
- "Pizza" and "Neural Networks" are not thematically connected
- "JavaScript" is more central than "React" in a programming cluster

**2. Relationship-Driven**
Flowers require actual relationships, not just similar labels. The graph structure **proves** the thematic connection.

**3. Contextual Awareness**
The LLM sees your recent speech transcript, helping it understand:
- What concepts you're currently discussing
- How ideas relate in your mental model
- When to merge vs separate themes

**4. Autonomous Curation**
The Gardener makes independent decisions within constraints. You don't manually create flowers - the AI identifies natural clusters.

---

### What This Means for Visual Behaviors

When you see flowers forming, it means:

1. **LLM identified a theme** (2-5 word label)
2. **3+ related nodes** were confirmed
3. **2+ connections** prove the relationships
4. **A stem node** was chosen as the hub

**The visual choreography:**
- Nodes animate to positions around their stem (1200ms)
- Curved connectors form between stem and petals
- Stem node grows larger (visual hierarchy)
- Flower boundary appears with label
- Camera adjusts to show the new cluster (2500ms)

All these animations happen because the **LLM made a semantic decision** about thematic coherence, which triggers the UI to reorganize the visualization accordingly!

---

This explains why flowers feel "intelligent" - they're driven by an AI that understands meaning, not just matching patterns in data.

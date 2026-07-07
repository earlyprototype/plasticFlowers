# plasticFlower — Agent Architecture

---

## Two-Agent Model

| Agent | Job | Speed | Trigger |
|-------|-----|-------|---------|
| **Builder** | Add new nodes quickly | Fast (low thinking) | Each transcript chunk |
| **Gardener** | Clean up, merge, organise | Slow (deep thinking) | Every 90 seconds |

They work on the **same graph** with different responsibilities.

---

## Builder Agent

**Purpose:** Immediate gratification — user sees nodes appear as speaker talks.

**Input:**
- New transcript chunk
- List of existing node labels (for context)

**Output:**
- New nodes to create
- New relationships (chunk-local)

**Configuration:** Gemini 3 Pro with low thinking budget

**Latency target:** < 3 seconds per chunk

---

## Gardener Agent

**Purpose:** Deep reasoning — resolve duplicates, form Flowers, find cross-chunk connections.

**Input:**
- Full transcript so far
- Current graph state (all nodes and relationships)

**Output:**
- Merge operations (combine duplicate nodes)
- Flower assignments (cluster nodes thematically)
- New cross-chunk relationships
- Confidence adjustments
- Prune recommendations

**Configuration:** Gemini 3 Pro with high thinking budget

**Trigger:** Every 90 seconds

---

## Pre-Builder Similarity Check

Before Builder creates a node:

1. Generate embedding for proposed node label
2. Query Neo4j vector index for similar nodes (>= 0.85 similarity)
3. If match found:
   - Do not create a new node
   - Increment `mentions` on the matched node
   - Append a timestamp for this mention
   - Use the matched node id when persisting relationships from this chunk
4. If no match: proceed with creation (ghost node)

This reduces Gardener's merge burden.



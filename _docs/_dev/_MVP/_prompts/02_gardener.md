# plasticFlower — Gardener Agent Prompt

---

## Purpose

The Gardener Agent runs every 90 seconds to review and refine the knowledge graph:

1. **Confirm or prune** ghost nodes
2. **Merge** duplicate or near-duplicate nodes
3. **Form Flowers** — thematic clusters of related nodes
4. **Update Flowers** — reassign nodes, rename themes
5. **Identify bridges** — cross-Flower relationships
6. **Assign stem nodes** — the central node in each Flower

Gardener prioritises quality over speed. It sees the full graph context.

---

## Trigger

- **Interval:** Every 90 seconds
- **Condition:** Only runs if there are ghost nodes OR recent Builder activity

---

## Input

Gardener receives a structured snapshot of the current graph state.

### 1. Ghost Nodes (Pending Review)

Nodes created by Builder since last Gardener run.

```json
{
  "ghost_nodes": [
    {
      "id": "n_001",
      "label": "transformer architecture",
      "inferred_type": "concept",
      "confidence": 0.95,
      "mentions": 3,
      "created_at": "2024-12-12T10:05:32Z"
    }
  ]
}
```

### 2. Solid Nodes (Confirmed)

All previously confirmed nodes.

```json
{
  "solid_nodes": [
    {
      "id": "n_002",
      "label": "neural network",
      "inferred_type": "concept",
      "confidence": 0.9,
      "mentions": 7,
      "flower_id": "f_001"
    }
  ]
}
```

### 3. Current Relationships

All relationships in the graph.

```json
{
  "relationships": [
    {
      "source_id": "n_001",
      "target_id": "n_002",
      "category": "COMPARATIVE",
      "description": "differs from",
      "confidence": 0.85
    }
  ]
}
```

### 4. Current Flowers

Existing thematic clusters.

```json
{
  "flowers": [
    {
      "id": "f_001",
      "label": "Deep Learning Architectures",
      "stem_node_id": "n_002",
      "member_ids": ["n_002", "n_003", "n_004"],
      "edge_count": 12
    }
  ]
}
```

### 5. Recent Transcript Context

Last 2-3 chunks for semantic context (helps with theme detection).

```
"The transformer architecture revolutionised NLP..."
"Attention mechanisms allow the model to focus on relevant parts..."
```

---

## Output

Strict JSON matching this schema:

```json
{
  "node_actions": [
    {
      "action": "confirm | prune | merge",
      "node_id": "string",
      "merge_into": "string (only if action=merge)",
      "reason": "string (brief explanation)"
    }
  ],
  "flower_actions": [
    {
      "action": "create | update | dissolve",
      "flower_id": "string (null if create)",
      "label": "string (theme name, 2-5 words)",
      "member_ids": ["string"],
      "stem_node_id": "string",
      "reason": "string"
    }
  ],
  "new_relationships": [
    {
      "source_id": "string",
      "target_id": "string",
      "category": "CAUSAL | STRUCTURAL | COMPARATIVE | TEMPORAL | ASSOCIATIVE",
      "description": "string (2-4 words)",
      "confidence": "float (0.0-1.0)",
      "reason": "string"
    }
  ]
}
```

### Validation Rules

| Field | Rule |
|-------|------|
| `node_actions` | Array, may be empty |
| `node_actions[].action` | One of: confirm, prune, merge |
| `node_actions[].merge_into` | Required if action=merge, must reference existing solid node |
| `flower_actions` | Array, may be empty |
| `flower_actions[].action` | One of: create, update, dissolve |
| `flower_actions[].label` | 2-5 words describing the theme |
| `flower_actions[].member_ids` | At least 3 nodes with 2+ internal connections |
| `flower_actions[].stem_node_id` | Must be in member_ids |
| `new_relationships` | Cross-chunk relationships Gardener discovers |

---

## Prompt Template

```
You are a knowledge graph curator. Your task is to review, refine, and organise a growing knowledge graph extracted from a live talk.

## GHOST NODES (Pending Review)
{{ghost_nodes}}

## SOLID NODES (Confirmed)
{{solid_nodes}}

## RELATIONSHIPS
{{relationships}}

## CURRENT FLOWERS
{{flowers}}

## RECENT TRANSCRIPT
{{recent_transcript}}

## INSTRUCTIONS

1. REVIEW GHOST NODES
   For each ghost node, decide:
   - CONFIRM: Node is valid and distinct. Promote to solid.
   - PRUNE: Node is too vague or low-value. Remove it.
   - MERGE: Node duplicates an existing solid node. Combine them.

   Merge criteria (TRUE DUPLICATES ONLY):
   - Same concept, different phrasing ("ML" → "machine learning")
   - Acronym and full form ("NLP" → "natural language processing")
   - Singular/plural variants
   - Minor spelling variations
   
   DO NOT MERGE:
   - Subset/superset relationships ("self-attention" is NOT a duplicate of "attention mechanism")
   - Related but distinct concepts
   - Hierarchical relationships (keep specificity)

2. FORM OR UPDATE FLOWERS
   A Flower is a thematic cluster of related nodes.
   
   Create a Flower when:
   - 3+ nodes share a clear theme
   - Nodes have 2+ internal connections (relationships between members)
   - Nodes are semantically related (shared meaning)
   
   Update a Flower when:
   - New confirmed nodes belong to an existing theme
   - Theme label no longer fits the members
   
   Dissolve a Flower when:
   - Fewer than 2 members remain
   - Members no longer share coherent meaning
   
   For each Flower:
   - Assign a stem_node_id (the most central/representative node)
   - Provide a label (2-5 words describing the theme)

3. DISCOVER CROSS-CHUNK RELATIONSHIPS
   Look for relationships between nodes that weren't in the same chunk.
   Only propose high-confidence relationships with clear semantic basis.
   
   Categories:
   
   CAUSAL: A influences B's existence or state.
   STRUCTURAL: A is part of, or contains, B.
   COMPARATIVE: A relates to B by similarity or difference.
   TEMPORAL: A comes before or after B in sequence.
   ASSOCIATIVE: A and B are related, but nature is unclear.

4. OUTPUT FORMAT
   Return valid JSON only. No commentary.
   If no actions needed, return empty arrays.

## OUTPUT
```

---

## Example

### Input (Simplified)

**Ghost nodes:**
```json
[
  {"id": "n_010", "label": "attention mechanism", "inferred_type": "method", "confidence": 0.9},
  {"id": "n_011", "label": "self attention", "inferred_type": "method", "confidence": 0.85},
  {"id": "n_012", "label": "the", "inferred_type": "term", "confidence": 0.3}
]
```

**Solid nodes:**
```json
[
  {"id": "n_001", "label": "transformer architecture", "flower_id": "f_001"},
  {"id": "n_002", "label": "neural network", "flower_id": "f_001"},
  {"id": "n_003", "label": "deep learning", "flower_id": "f_001"}
]
```

**Flowers:**
```json
[
  {"id": "f_001", "label": "Neural Network Foundations", "stem_node_id": "n_002", "member_ids": ["n_001", "n_002", "n_003"]}
]
```

### Output

```json
{
  "node_actions": [
    {
      "action": "confirm",
      "node_id": "n_010",
      "reason": "Distinct method concept, well-defined"
    },
    {
      "action": "merge",
      "node_id": "n_011",
      "merge_into": "n_010",
      "reason": "Same concept, hyphenation variant (self attention = self-attention)"
    },
    {
      "action": "prune",
      "node_id": "n_012",
      "reason": "Article word, not a meaningful concept"
    }
  ],
  "flower_actions": [
    {
      "action": "update",
      "flower_id": "f_001",
      "label": "Neural Network Foundations",
      "member_ids": ["n_001", "n_002", "n_003", "n_010"],
      "stem_node_id": "n_002",
      "reason": "Adding attention mechanism to existing cluster"
    }
  ],
  "new_relationships": [
    {
      "source_id": "n_010",
      "target_id": "n_001",
      "category": "STRUCTURAL",
      "description": "core component of",
      "confidence": 0.9,
      "reason": "Attention is fundamental to transformer architecture"
    }
  ]
}
```

---

## Flower Quality Assessment

Gardener should consider both dimensions when forming Flowers:

| Dimension | How to Assess | Implication |
|-----------|---------------|-------------|
| **Semantic coherence** | Do members share meaning? | High = confident theme |
| **Structural density** | How interconnected are members? | High = tightly coupled |

| Combination | Interpretation | Action |
|-------------|----------------|--------|
| High semantic + high density | Confident Flower | Maintain |
| High semantic + low density | Emerging theme | Keep, may grow |
| Low semantic + high density | Potential conflation | Review, may split |
| Low semantic + low density | Weak cluster | Dissolve |

---

## Stem Node Selection

The stem node is the most representative node in a Flower. Selection criteria:

1. **Highest connectivity** — most relationships to other Flower members
2. **Highest mentions** — referenced most often in transcript
3. **Broadest scope** — encompasses other members semantically

If tied, prefer the node created earliest (more established).

---

## Error Handling

| Scenario | Backend Response |
|----------|------------------|
| Invalid JSON | Log error, skip this cycle, retry next interval |
| Unknown action type | Log warning, ignore that action |
| Invalid node_id reference | Log warning, ignore that action |
| Flower with <2 members | Reject flower_action, log warning |

---

## Token Budget

| Component | Estimated Tokens |
|-----------|------------------|
| System prompt | ~600 |
| Ghost nodes (20 nodes) | ~400 |
| Solid nodes (100 nodes) | ~800 |
| Relationships (150 edges) | ~1200 |
| Flowers (10 clusters) | ~300 |
| Recent transcript | ~300 |
| Output | ~500-1000 |
| **Total per invocation** | **~4000-4600** |

Gemini 3 Pro context: 1M tokens. Budget scales with graph size but remains well within limits for typical sessions.

---

## Scaling Considerations

For large graphs (500+ nodes):

| Strategy | When to Apply |
|----------|---------------|
| Summarise solid nodes | >200 solid nodes |
| Only include relevant relationships | >300 relationships |
| Batch ghost node review | >50 ghost nodes |

These optimisations are post-MVP. Initial implementation passes full context.

---

## Notes

- Gardener is the only agent that can change node status from "ghost" to "solid"
- Gardener is the only agent that creates/modifies Flowers
- Merged nodes: relationships from the pruned node transfer to the merge target
- Pruned nodes: relationships are deleted with the node
- Gardener should be conservative — when uncertain, prune rather than confirm

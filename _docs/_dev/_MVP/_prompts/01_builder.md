# plasticFlower — Builder Agent Prompt

---

## Purpose

The Builder Agent processes each transcript chunk in real-time, extracting:

1. **Nodes** — Concepts, people, frameworks, or terms mentioned
2. **Relationships** — Connections between nodes within the same chunk

Builder prioritises speed over perfection. The Gardener reviews and refines later.

---

## Input

Builder receives two inputs per invocation:

### 1. Transcript Chunk

A segment of transcribed speech (~3-5 sentences, ~50-150 words).

```
"The transformer architecture revolutionised natural language processing. 
Unlike RNNs, transformers process all tokens in parallel using self-attention. 
This enabled models like BERT and GPT to achieve unprecedented performance."
```

### 2. Existing Node Context

Labels of nodes already in the graph, grouped by inferred type.

```
EXISTING NODES:
- concept: neural network, deep learning, backpropagation
- person: Geoffrey Hinton
- framework: TensorFlow
```

If the graph is empty, this section is omitted.

---

## Output

Strict JSON matching this schema:

```json
{
  "nodes": [
    {
      "label": "string (lowercase, 1-4 words)",
      "inferred_type": "string (your best categorisation — emergent, not constrained)",
      "confidence": "float (0.0-1.0)"
    }
  ],
  "relationships": [
    {
      "source": "string (must match a node label)",
      "target": "string (must match a node label)", 
      "category": "string (CAUSAL|STRUCTURAL|COMPARATIVE|TEMPORAL|ASSOCIATIVE)",
      "description": "string (2-4 words, natural language)",
      "confidence": "float (0.0-1.0)",
      "evidence": "string (quote from chunk)"
    }
  ]
}
```

### Validation Rules

| Field | Rule |
|-------|------|
| `nodes` | Array, may be empty if chunk contains no extractable concepts |
| `nodes[].label` | Lowercase, 1-4 words, no articles ("the", "a") |
| `nodes[].inferred_type` | Freeform string — LLM's best categorisation (emergent, not constrained) |
| `nodes[].confidence` | Float 0.0-1.0, higher = more certain |
| `relationships` | Array, may be empty |
| `relationships[].source` | Must match a label from `nodes` or existing context |
| `relationships[].target` | Must match a label from `nodes` or existing context |
| `relationships[].category` | One of: CAUSAL, STRUCTURAL, COMPARATIVE, TEMPORAL, ASSOCIATIVE |
| `relationships[].description` | 2-4 words describing the relationship |
| `relationships[].evidence` | Direct quote from the chunk |

---

## Prompt Template

```
You are a knowledge extraction agent. Your task is to identify concepts and relationships from a transcript chunk.

## EXISTING NODES
{{existing_nodes}}

## TRANSCRIPT CHUNK
{{chunk_text}}

## INSTRUCTIONS

1. EXTRACT NODES
   - Identify noteworthy concepts, people, frameworks, methods, events, organisations, or terms
   - Use lowercase labels (1-4 words)
   - Assign an inferred_type using your best judgment (this is EMERGENT — use whatever category fits, not a predefined list)
   - If a concept matches an existing node, DO NOT create a duplicate
   - Assign a confidence score (0.0-1.0) based on clarity of mention

2. EXTRACT RELATIONSHIPS
   - Only create relationships between nodes mentioned in THIS chunk
   - Assign one of these categories:

   CAUSAL: A influences B's existence or state.
     Example: "machine learning" → ENABLES → "pattern recognition"

   STRUCTURAL: A is part of, or contains, B.
     Example: "neural network" → CONTAINS → "hidden layer"

   COMPARATIVE: A relates to B by similarity or difference.
     Example: "supervised learning" → CONTRASTS_WITH → "unsupervised learning"

   TEMPORAL: A comes before or after B in sequence.
     Example: "data collection" → PRECEDES → "model training"

   ASSOCIATIVE: A and B are related, but the nature is unclear.
     Example: "innovation" → RELATES_TO → "culture"

   - Include a 2-4 word description of the relationship
   - Include the exact quote from the chunk as evidence
   - Assign confidence based on how explicit the relationship is

3. OUTPUT FORMAT
   Return valid JSON only. No commentary.

## OUTPUT
```

---

## Example

### Input

**Existing nodes:**
```
EXISTING NODES:
- concept: neural network, deep learning
- person: Geoffrey Hinton
```

**Chunk:**
```
The transformer architecture revolutionised natural language processing. 
Unlike RNNs, transformers process all tokens in parallel using self-attention. 
This enabled models like BERT and GPT to achieve unprecedented performance.
```

### Output

```json
{
  "nodes": [
    {
      "label": "transformer architecture",
      "inferred_type": "concept",
      "confidence": 0.95
    },
    {
      "label": "natural language processing",
      "inferred_type": "concept",
      "confidence": 0.9
    },
    {
      "label": "rnn",
      "inferred_type": "concept",
      "confidence": 0.85
    },
    {
      "label": "self-attention",
      "inferred_type": "method",
      "confidence": 0.9
    },
    {
      "label": "bert",
      "inferred_type": "framework",
      "confidence": 0.9
    },
    {
      "label": "gpt",
      "inferred_type": "framework",
      "confidence": 0.9
    }
  ],
  "relationships": [
    {
      "source": "transformer architecture",
      "target": "natural language processing",
      "category": "CAUSAL",
      "description": "revolutionised",
      "confidence": 0.9,
      "evidence": "The transformer architecture revolutionised natural language processing"
    },
    {
      "source": "transformer architecture",
      "target": "rnn",
      "category": "COMPARATIVE",
      "description": "differs from",
      "confidence": 0.85,
      "evidence": "Unlike RNNs, transformers process all tokens in parallel"
    },
    {
      "source": "transformer architecture",
      "target": "self-attention",
      "category": "STRUCTURAL",
      "description": "uses",
      "confidence": 0.9,
      "evidence": "transformers process all tokens in parallel using self-attention"
    },
    {
      "source": "transformer architecture",
      "target": "bert",
      "category": "CAUSAL",
      "description": "enabled",
      "confidence": 0.85,
      "evidence": "This enabled models like BERT and GPT"
    },
    {
      "source": "transformer architecture",
      "target": "gpt",
      "category": "CAUSAL",
      "description": "enabled",
      "confidence": 0.85,
      "evidence": "This enabled models like BERT and GPT"
    }
  ]
}
```

---

## Error Handling

| Scenario | Backend Response |
|----------|------------------|
| Invalid JSON | Log error, discard chunk, continue |
| Missing required field | Log warning, use defaults where possible |
| Unknown category | Map to ASSOCIATIVE |
| Confidence out of range | Clamp to 0.0-1.0 |
| Empty nodes array | Valid — chunk may contain no extractable concepts |

---

## Token Budget

| Component | Estimated Tokens |
|-----------|------------------|
| System prompt | ~400 |
| Existing nodes (50 nodes) | ~200 |
| Chunk text | ~100-200 |
| Output | ~200-500 |
| **Total per invocation** | **~900-1300** |

Gemini 3 Pro context: 1M tokens. Budget is well within limits.

---

## Notes

- Builder creates "ghost" nodes (status = "ghost")
- Gardener later confirms nodes to "solid" status
- Builder does NOT create cross-chunk relationships — only Gardener does that
- If Builder is unsure whether to extract something, it should extract with lower confidence rather than omit


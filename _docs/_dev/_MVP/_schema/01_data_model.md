# plasticFlower — Data Model

---

## Entities

### Node

A concept/term extracted from the talk.

| Property | Type | Purpose |
|----------|------|---------|
| `id` | string | Unique identifier |
| `label` | string | Display name |
| `confidence` | float | 0.0–1.0, decays if orphaned |
| `mentions` | int | How many times referenced |
| `timestamps` | float[] | When mentioned (seconds from start) |
| `inferred_type` | string | LLM's guess: "concept", "person", "framework", etc. |
| `flower_id` | string? | Which Flower it belongs to (null = orphan) |
| `embedding` | float[] | Vector for similarity search |
| `created_at` | datetime | When first created |
| `status` | string | "ghost" or "solid" |

---

### Relationship

A connection between two nodes.

| Property | Type | Purpose |
|----------|------|---------|
| `id` | string | Unique identifier |
| `category` | string | One of 5 abstract types (see below) |
| `description` | string | Natural language detail (2-4 words) |
| `confidence` | float | How certain the LLM was |
| `evidence` | string | Quote from transcript |
| `created_at` | datetime | When discovered |
| `source` | string | "builder" or "gardener" |

**Relationship Categories:**

| Category | What It Captures |
|----------|------------------|
| `CAUSAL` | A influences B's existence/state |
| `STRUCTURAL` | A is part of / contains B |
| `COMPARATIVE` | A relates to B by similarity/difference |
| `TEMPORAL` | A comes before/after B |
| `ASSOCIATIVE` | A and B are related (unspecified fallback) |

---

### Flower

A thematic cluster of nodes.

| Property | Type | Purpose |
|----------|------|---------|
| `id` | string | Unique identifier |
| `label` | string | LLM-generated theme name |
| `stem_node_id` | string | Highest-centrality node |
| `edge_count` | int | Simple density proxy |
| `created_at` | datetime | When Gardener formed it |

Flower membership stored on Node (`flower_id`), not as list on Flower.

---

### Session

Container for a talk/meeting.

| Property | Type | Purpose |
|----------|------|---------|
| `id` | string | Unique identifier |
| `name` | string | User-provided name |
| `created_at` | datetime | When started |
| `ended_at` | datetime? | When stopped (null if live) |
| `transcript` | string | Full accumulated text |

---

### Transcript Chunk

A segment of transcribed speech.

| Property | Type | Purpose |
|----------|------|---------|
| `id` | string | Unique identifier |
| `text` | string | The chunk content |
| `start_time` | float | Seconds from session start |
| `end_time` | float | Seconds from session start |
| `session_id` | string | Parent session |



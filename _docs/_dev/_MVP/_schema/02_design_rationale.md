# plasticFlower — Schema Design Rationale

---

## Key Design Decisions

### Emergent Schema

Nodes have `inferred_type` (LLM's guess) rather than predefined categories.

**Why:** Domain-agnostic. A talk on biology and a talk on business produce different node types naturally.

---

### Relationship Categories

5 abstract categories + natural language description.

**Why:** Balances constraint (analysable) with flexibility (not distorting).

| Problem | Solution |
|---------|----------|
| Unconstrained → fragmentation | 5 categories enable grouping |
| Over-constrained → distortion | Natural language preserves nuance |
| Edge case → forced fit | ASSOCIATIVE catches uncertainty |

---

### Flower Membership on Node

`flower_id` stored on Node, not as array on Flower.

**Why:** Neo4j-idiomatic. Easier queries. Node knows its home.

---

### Flower Bridges Derived

Not stored explicitly.

**Why:** Query "relationships where from.flower_id ≠ to.flower_id" is simple and always accurate. Storing would require maintenance.

---

### Ghost/Solid Status

Stored in database, not just frontend state.

**Why:** Persistence across sessions. Gardener can change status.

---

### Two Density Dimensions

Flowers have both:
- Semantic coherence (LLM-determined theme)
- Structural density (edge count)

**Why:** They measure different things. High semantic + low density = emerging theme. High density + low semantic = potential conflation.

---

## What's NOT in MVP

| Omission | Rationale |
|----------|-----------|
| Relationship weights | Adds complexity; can derive from evidence count |
| Chunk → Node linkage | Onerous to maintain; timestamps sufficient |
| Full graph algorithms for density | Simple edge count sufficient for MVP |



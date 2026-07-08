# Gate 2 Contract Snapshot — v2025-12-13

> Source documents: `_docs/_dev/_MVP/_api/01_contracts.md`, `_docs/_dev/_MVP/_schema/01_data_model.md`, `_docs/_dev/_MVP/_ALIGNMENT.md`, `_docs/_dev/_MVP/_PRE_IMPLEMENTATION_REPORT.md`

## Node
| Field | Type | Required | Notes | Spec Reference |
|-------|------|----------|-------|-----------------|
| `id` | `str` | ✅ | Stable identifier used across REST + SSE | `_schema/01_data_model.md` (Node) |
| `label` | `str` | ✅ | Display name extracted by Builder | `_schema/01_data_model.md` (Node) |
| `confidence` | `float (0.0-1.0)` | ✅ | Decays if node stays orphaned | `_schema/01_data_model.md` (Node) |
| `mentions` | `int` | ✅ | Incremented per similarity hit (≥0.85 rule) | `_schema/01_data_model.md` + `_PRE_IMPLEMENTATION_REPORT.md` (Similarity) |
| `timestamps` | `List[float]` | ✅ | Seconds from session start for each mention | `_schema/01_data_model.md` (Node) |
| `inferred_type` | `str` | ✅ | Freeform, emergent type — **never** an enum | `_ALIGNMENT.md` (Emergent schema) |
| `flower_id` | `Optional[str]` | ➖ | `None` until Gardener assigns Flower | `_schema/01_data_model.md` (Node) |
| `embedding` | `List[float]` | ✅ (backend) | Stored for similarity search; not sent over SSE/REST today | `_schema/01_data_model.md` + `_IMPLEMENTATION_BRIEF.md` (Neo4j integration) |
| `created_at` | `datetime` | ✅ | ISO 8601 timestamp of initial creation | `_schema/01_data_model.md` (Node) |
| `status` | `Literal["ghost","solid"]` | ✅ | Builder emits `ghost`, Gardener flips to `solid` | `_schema/01_data_model.md` + `_architecture/02_agents.md` |

## Relationship
| Field | Type | Required | Notes | Spec Reference |
|-------|------|----------|-------|-----------------|
| `id` | `str` | ✅ | Required everywhere (Pre-Implementation lock) | `_schema/01_data_model.md` + `_PRE_IMPLEMENTATION_REPORT.md` |
| `source_id` | `str` | ✅ | Node id (tail of edge) | `_schema/01_data_model.md` |
| `target_id` | `str` | ✅ | Node id (head of edge) | `_schema/01_data_model.md` |
| `category` | `Literal["CAUSAL","STRUCTURAL","COMPARATIVE","TEMPORAL","ASSOCIATIVE"]` | ✅ | Exactly five categories — no extras | `_ALIGNMENT.md` + `_api/01_contracts.md` |
| `description` | `str (2-4 words)` | ✅ | Natural-language qualifier that preserves nuance | `_api/01_contracts.md` (Relationship schema) |
| `confidence` | `float (0.0-1.0)` | ✅ | Builder/Gardener certainty | `_schema/01_data_model.md` |
| `evidence` | `str` | ✅ | Quote or paraphrase supporting relationship | `_schema/01_data_model.md` |
| `source` | `Literal["builder","gardener"]` | ✅ | Which agent produced/confirmed relationship | `_schema/01_data_model.md` + `_architecture/02_agents.md` |
| `created_at` | `datetime` | ✅ | Timestamp for ordering | `_schema/01_data_model.md` |

## Flower
| Field | Type | Required | Notes | Spec Reference |
|-------|------|----------|-------|-----------------|
| `id` | `str` | ✅ | Stable Flower id | `_schema/01_data_model.md` |
| `label` | `str (2-5 words)` | ✅ | Gardener-generated theme name | `_api/01_contracts.md` (Flower schema) |
| `stem_node_id` | `str` | ✅ | Highest-centrality node id | `_schema/01_data_model.md` |
| `edge_count` | `int` | ✅ | Simple density proxy (structural dimension) | `_schema/02_design_rationale.md` |
| `created_at` | `datetime` | ✅ | When Gardener formed Flower | `_schema/01_data_model.md` |
| _Membership_ | `node.flower_id` | — | Stored on Nodes, not list on Flower | `_schema/01_data_model.md` |

## Flower Bridge (derived at query-time)
| Field | Type | Required | Notes | Spec Reference |
|-------|------|----------|-------|-----------------|
| `source_flower_id` | `str` | ✅ | Flower containing relationship source node | `_api/01_contracts.md` (`GET /flowers`) |
| `target_flower_id` | `str` | ✅ | Flower containing relationship target node | `_api/01_contracts.md` |
| `connecting_relationships` | `List[Relationship]` | ✅ | Relationships crossing Flowers (not persisted separately) | `_api/01_contracts.md` + DEC-012 |

## Session
| Field | Type | Required | Notes | Spec Reference |
|-------|------|----------|-------|-----------------|
| `id` | `str` | ✅ | Session identifier returned on creation | `_schema/01_data_model.md` |
| `name` | `str` | ✅ | User-provided or timestamp fallback | `_api/01_contracts.md` (`POST /sessions`) + DEC-010 |
| `language_variant` | `str` | ✅ | Language variant for all generated text (default: "en-GB", alternative: "en-US") | `_docs/ARCHITECTURE_ADVISORY.md` Section 4.5 |
| `created_at` | `datetime` | ✅ | Start timestamp | `_schema/01_data_model.md` |
| `ended_at` | `Optional[datetime]` | ➖ | Null while live | `_schema/01_data_model.md` |
| `transcript` | `str` | ✅ (detail) | Full accumulated text; omitted from list view but stored in Session | `_schema/01_data_model.md` + `_api/01_contracts.md` (`GET /sessions/{id}`) |

## Transcript Chunk (stored entity)
| Field | Type | Required | Notes | Spec Reference |
|-------|------|----------|-------|-----------------|
| `id` | `str` | ✅ | Chunk identifier emitted after POST | `_schema/01_data_model.md` |
| `text` | `str` | ✅ | Raw transcription text | `_schema/01_data_model.md` |
| `start_time` | `float (seconds)` | ✅ | Offset from session start | `_schema/01_data_model.md` |
| `end_time` | `float (seconds)` | ✅ | Offset from session start | `_schema/01_data_model.md` |
| `session_id` | `str` | ✅ | Owning session | `_schema/01_data_model.md` |

## Chunk Submission Ack (`POST /sessions/{id}/chunks` response)
| Field | Type | Required | Notes | Spec Reference |
|-------|------|----------|-------|-----------------|
| `chunk_id` | `str` | ✅ | Mirrors stored chunk id | `_api/01_contracts.md` (Submit Chunk) |
| `status` | `Literal["queued"]` | ✅ | Placeholder until Builder processes chunk | `_api/01_contracts.md` |

## SSE Event Payloads (`GET /sessions/{id}/stream`)
| Event | Payload Schema | Required Fields | Spec Reference |
|-------|----------------|-----------------|-----------------|
| `node_added` | `Node` | All Node fields above | `_api/01_contracts.md` (SSE table) |
| `node_updated` | `Node` | All Node fields | `_api/01_contracts.md` |
| `node_removed` | `{ "id": str }` | `id` (node to prune) | `_api/01_contracts.md` + `_PRE_IMPLEMENTATION_REPORT.md` |
| `node_merged` | `{ "from_id": str, "into_id": str }` | `from_id`, `into_id` | `_api/01_contracts.md` |
| `relationship_added` | `Relationship` | All Relationship fields | `_api/01_contracts.md` |
| `relationship_removed` | `{ "id": str }` | `id` | `_api/01_contracts.md` + `_PRE_IMPLEMENTATION_REPORT.md` |
| `flower_created` | `Flower` | All Flower fields | `_api/01_contracts.md` |
| `flower_updated` | `Flower` | All Flower fields | `_api/01_contracts.md` |
| `flower_dissolved` | `{ "id": str }` | `id` | `_api/01_contracts.md` |
| `chunk_processed` | `{ "chunk_id": str }` | `chunk_id` | `_api/01_contracts.md` |
| `gardener_cycle` | `{ "timestamp": datetime }` | `timestamp` (cycle completion) | `_api/01_contracts.md` |

## Error Shape (shared)
| Field | Type | Required | Notes | Spec Reference |
|-------|------|----------|-------|-----------------|
| `error` | `str` | ✅ | Short code/message | `_api/01_contracts.md` (Error Responses) |
| `detail` | `Optional[str]` | ➖ | Additional context (e.g., validation failures) | `_api/01_contracts.md` |
| `fields` | `Optional[object]` | ➖ | Field-level validation detail (`422` only) | `_api/01_contracts.md` |

## Parity Log
| Date | Scope | Result | Notes |
|------|-------|--------|-------|
| 2025-12-13 | Backend ↔ Frontend types | ✅ | `frontend/src/lib/types.ts` mirrors backend models; validated via `npm run lint` + `tsc --noEmit`. |

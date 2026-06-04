# plasticFlower — API Contracts

---

## Overview

| Component | Technology | Source |
|-----------|------------|--------|
| Backend | FastAPI | Handover |
| Protocol (server→client) | SSE | Architecture |
| Protocol (client→server) | REST | Follows from SSE |
| Graph store | Neo4j (local) | DEC-009 |

---

## Base URL

```
http://localhost:8000/api
```

Local only (DEC-009).

---

## Endpoints

### Session Management

#### Create Session

```
POST /sessions
```

**Request:**
```json
{
  "name": "string (optional)"
}
```

**Response:** `201 Created`
```json
{
  "id": "string",
  "name": "string",
  "created_at": "datetime"
}
```

**Notes:**
- If `name` is omitted, use timestamp fallback (DEC-010)
- Format: `Session_YYYY-MM-DD_HH-MM`

---

#### List Sessions

```
GET /sessions
```

**Response:** `200 OK`
```json
{
  "sessions": [
    {
      "id": "string",
      "name": "string",
      "created_at": "datetime",
      "ended_at": "datetime | null"
    }
  ]
}
```

---

#### Get Session

```
GET /sessions/{session_id}
```

**Response:** `200 OK`
```json
{
  "id": "string",
  "name": "string",
  "created_at": "datetime",
  "ended_at": "datetime | null",
  "transcript": "string"
}
```

---

#### End Session

```
POST /sessions/{session_id}/end
```

**Response:** `200 OK`
```json
{
  "id": "string",
  "ended_at": "datetime"
}
```

---

#### Delete Session

```
DELETE /sessions/{session_id}
```

**Response:** `204 No Content`

---

#### Rename Session

```
PATCH /sessions/{session_id}
```

**Request:**
```json
{
  "name": "string"
}
```

**Response:** `200 OK`
```json
{
  "id": "string",
  "name": "string"
}
```

---

### Transcript Submission

#### Submit Chunk

```
POST /sessions/{session_id}/chunks
```

**Request:**
```json
{
  "text": "string",
  "start_time": "float (seconds from session start)",
  "end_time": "float"
}
```

**Response:** `202 Accepted`
```json
{
  "chunk_id": "string",
  "status": "queued"
}
```

**Notes:**
- Frontend handles STT (Web Speech API, DEC-007)
- Backend queues chunk for Builder Agent processing
- Results delivered via SSE, not in this response

---

### Real-time Updates (SSE)

#### Subscribe to Session Updates

```
GET /sessions/{session_id}/stream
```

**Response:** `200 OK` (text/event-stream)

**Event Types:**

| Event | Payload | Trigger |
|-------|---------|---------|
| `node_added` | Node object | Builder extracts new node |
| `node_updated` | Node object | Gardener confirms/updates |
| `node_removed` | `{ id }` | Gardener prunes |
| `node_merged` | `{ from_id, into_id }` | Gardener merges |
| `relationship_added` | Relationship object | Builder/Gardener |
| `relationship_removed` | `{ id }` | Gardener |
| `flower_created` | Flower object | Gardener |
| `flower_updated` | Flower object | Gardener |
| `flower_dissolved` | `{ id }` | Gardener |
| `chunk_processed` | `{ chunk_id }` | Builder complete |
| `gardener_cycle` | `{ timestamp }` | Gardener run complete |

**Example SSE Message:**
```
event: node_added
data: {"id": "n_001", "label": "transformer", "inferred_type": "architecture", "confidence": 0.9, "status": "ghost"}
```

---

### Graph Data

#### Get Full Graph

```
GET /sessions/{session_id}/graph
```

**Response:** `200 OK`
```json
{
  "nodes": [Node],
  "relationships": [Relationship],
  "flowers": [Flower]
}
```

**Notes:**
- Flower bridges derived at query-time, not stored (DEC-012)
- Response includes computed `bridges` array

---

#### Get Nodes

```
GET /sessions/{session_id}/nodes
```

**Query Parameters:**
- `status` (optional): `ghost` | `solid` | `all` (default: `all`)
- `flower_id` (optional): Filter by Flower membership

**Response:** `200 OK`
```json
{
  "nodes": [Node]
}
```

---

#### Get Relationships

```
GET /sessions/{session_id}/relationships
```

**Query Parameters:**
- `category` (optional): Filter by category
- `source` (optional): Filter by source agent (`builder` | `gardener`)

**Response:** `200 OK`
```json
{
  "relationships": [Relationship]
}
```

---

#### Get Flowers

```
GET /sessions/{session_id}/flowers
```

**Response:** `200 OK`
```json
{
  "flowers": [Flower],
  "bridges": [
    {
      "source_flower_id": "string",
      "target_flower_id": "string",
      "connecting_relationships": [Relationship]
    }
  ]
}
```

**Notes:**
- Bridges computed at query-time (DEC-012)

---

### Export

#### Export JSON

```
GET /sessions/{session_id}/export/json
```

**Response:** `200 OK` (application/json)

Full graph + transcript + metadata.

---

#### Export Transcript (Plain)

```
GET /sessions/{session_id}/export/transcript
```

**Response:** `200 OK` (text/plain)

Plain text transcript.

---

#### Export Transcript (VTT)

```
GET /sessions/{session_id}/export/vtt
```

**Response:** `200 OK` (text/vtt)

WebVTT format with timestamps.

---

#### Export Markdown Summary

```
GET /sessions/{session_id}/export/markdown
```

**Response:** `200 OK` (text/markdown)

LLM-generated summary including:
- Session metadata
- Key themes (Flowers)
- Main concepts
- Relationships overview

---

## Data Schemas

### Node

```json
{
  "id": "string",
  "label": "string",
  "confidence": "float (0.0-1.0)",
  "mentions": "int",
  "timestamps": ["float"],
  "inferred_type": "string (emergent, not constrained)",
  "flower_id": "string | null",
  "status": "ghost | solid",
  "created_at": "datetime"
}
```

**Note:** `inferred_type` is freeform — no enum constraint (DEC-002, Alignment).

---

### Relationship

```json
{
  "id": "string",
  "source_id": "string",
  "target_id": "string",
  "category": "CAUSAL | STRUCTURAL | COMPARATIVE | TEMPORAL | ASSOCIATIVE",
  "description": "string (2-4 words)",
  "confidence": "float (0.0-1.0)",
  "evidence": "string",
  "source": "builder | gardener",
  "created_at": "datetime"
}
```

**Note:** `category` IS constrained to 5 values (DEC-005).

---

### Flower

```json
{
  "id": "string",
  "label": "string (2-5 words)",
  "stem_node_id": "string",
  "edge_count": "int",
  "created_at": "datetime"
}
```

**Note:** Member nodes reference Flower via `flower_id`, not stored as list on Flower (Data Model).

---

### Transcript Chunk

```json
{
  "id": "string",
  "text": "string",
  "start_time": "float",
  "end_time": "float",
  "session_id": "string"
}
```

---

## Error Responses

| Status | Meaning | Response |
|--------|---------|----------|
| `400` | Bad request | `{ "error": "string", "detail": "string" }` |
| `404` | Not found | `{ "error": "string" }` |
| `422` | Validation error | `{ "error": "string", "fields": {} }` |
| `500` | Server error | `{ "error": "string" }` |

---

## Auto-Reconnect

Frontend should implement auto-reconnect for SSE (Scope requirement):

1. On disconnect, attempt reconnect after 1s
2. Exponential backoff: 1s, 2s, 4s, 8s, max 30s
3. On reconnect, fetch full graph state via `GET /sessions/{id}/graph`
4. Resume SSE stream

---

## Decision Traceability

| Aspect | Decision | Reference |
|--------|----------|-----------|
| Local hosting | `localhost:8000` | DEC-009 |
| Session naming | User-provided with timestamp fallback | DEC-010 |
| Export formats | JSON, plain transcript, VTT, Markdown | DEC-011 |
| Flower bridges | Query-time derivation | DEC-012 |
| STT handling | Frontend (Web Speech API) | DEC-007 |
| Relationship categories | 5 fixed categories | DEC-005 |
| Node types | Emergent, freeform | DEC-002 |


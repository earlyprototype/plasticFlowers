# plasticFlower — Project Structure

> **Historical planning document** — describes the pre-implementation design, not the current system. See [_docs/_audit/2026-07-08_audit_report.md](../../../_audit/2026-07-08_audit_report.md) for current state.

---

## Overview

| Layer | Technology | Source |
|-------|------------|--------|
| Frontend | Next.js | Handover |
| Backend | FastAPI | Handover |
| Database | Neo4j (local) | Handover, DEC-009 |
| LLM | Gemini 3 Pro | Handover |

---

## Directory Structure

```
plasticFlower/
├── frontend/                    # Next.js application
│   ├── src/
│   │   ├── app/                 # Next.js App Router
│   │   │   ├── page.tsx         # Home/session list
│   │   │   ├── session/
│   │   │   │   └── [id]/
│   │   │   │       └── page.tsx # Live session view
│   │   │   └── layout.tsx
│   │   │
│   │   ├── components/
│   │   │   ├── graph/
│   │   │   │   ├── GraphCanvas.tsx      # Cytoscape wrapper
│   │   │   │   ├── NodeDetail.tsx       # Node info panel
│   │   │   │   ├── EdgeDetail.tsx       # Relationship info panel
│   │   │   │   └── FlowerDetail.tsx     # Flower info panel
│   │   │   │
│   │   │   ├── controls/
│   │   │   │   ├── SessionControls.tsx  # Start/stop/export
│   │   │   │   ├── ZFilter.tsx          # Z-level filtering
│   │   │   │   └── StatusIndicator.tsx  # Connection status
│   │   │   │
│   │   │   ├── transcript/
│   │   │   │   └── TranscriptPanel.tsx  # Live transcript view
│   │   │   │
│   │   │   └── layout/
│   │   │       ├── Header.tsx
│   │   │       └── MainLayout.tsx
│   │   │
│   │   ├── hooks/
│   │   │   ├── useSSE.ts                # SSE connection management
│   │   │   ├── useGraphState.ts         # Graph state management
│   │   │   ├── useSpeechRecognition.ts  # Web Speech API wrapper
│   │   │   └── useChunkDispatcher.ts    # Chunk buffering logic
│   │   │
│   │   ├── lib/
│   │   │   ├── api.ts                   # API client functions
│   │   │   ├── cytoscape-config.ts      # Cytoscape setup
│   │   │   └── types.ts                 # TypeScript interfaces
│   │   │
│   │   └── styles/
│   │       └── globals.css
│   │
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   └── next.config.js
│
├── backend/                     # FastAPI application
│   ├── app/
│   │   ├── main.py              # FastAPI app entry
│   │   ├── config.py            # Configuration loading
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── sessions.py      # Session endpoints
│   │   │   ├── chunks.py        # Chunk submission
│   │   │   ├── graph.py         # Graph data endpoints
│   │   │   ├── export.py        # Export endpoints
│   │   │   └── stream.py        # SSE endpoint
│   │   │
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── builder.py       # Builder Agent implementation
│   │   │   ├── gardener.py      # Gardener Agent implementation
│   │   │   └── prompts/
│   │   │       ├── builder.txt  # Builder system prompt
│   │   │       └── gardener.txt # Gardener system prompt
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── llm.py           # Gemini 3 Pro client
│   │   │   ├── graph_db.py      # Neo4j operations
│   │   │   ├── sse_manager.py   # SSE broadcast management
│   │   │   └── scheduler.py     # Gardener 90s timer
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── node.py          # Node model
│   │   │   ├── relationship.py  # Relationship model
│   │   │   ├── flower.py        # Flower model
│   │   │   ├── session.py       # Session model
│   │   │   └── chunk.py         # Transcript chunk model
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── validators.py    # JSON validation
│   │
│   ├── tests/
│   │   ├── test_builder.py
│   │   ├── test_gardener.py
│   │   └── test_api.py
│   │
│   ├── requirements.txt
│   └── pyproject.toml
│
├── docker/                      # Local deployment
│   ├── docker-compose.yml       # Neo4j + backend + frontend
│   └── neo4j/
│       └── conf/
│
├── docs/                        # User documentation
│   └── README.md
│
└── README.md                    # Project overview
```

---

## Backend Module Responsibilities

### `api/`

| Module | Responsibility |
|--------|----------------|
| `sessions.py` | CRUD for sessions |
| `chunks.py` | Receive transcript chunks, queue for Builder |
| `graph.py` | Serve graph data (nodes, relationships, flowers) |
| `export.py` | Generate export files (JSON, transcript, VTT, Markdown) |
| `stream.py` | SSE endpoint, broadcast events |

### `agents/`

| Module | Responsibility |
|--------|----------------|
| `builder.py` | Process chunks, extract nodes/relationships |
| `gardener.py` | Periodic review, merge, cluster, prune |
| `prompts/` | System prompts (from spec documents) |

### `services/`

| Module | Responsibility |
|--------|----------------|
| `llm.py` | Gemini 3 Pro API calls, response parsing |
| `graph_db.py` | Neo4j CRUD operations |
| `sse_manager.py` | Track connected clients, broadcast events |
| `scheduler.py` | Run Gardener every 90 seconds (DEC-004) |

### `models/`

Pydantic models matching the data schema. Used for:
- Request/response validation
- Database serialisation
- Type hints

---

## Frontend Module Responsibilities

### `components/`

| Folder | Responsibility |
|--------|----------------|
| `graph/` | Cytoscape rendering, node/edge detail panels |
| `controls/` | Session controls, Z-filter, status display |
| `transcript/` | Live transcript view |
| `layout/` | Page structure |

### `hooks/`

| Hook | Responsibility |
|------|----------------|
| `useSSE` | Connect/reconnect SSE, parse events |
| `useGraphState` | Maintain nodes/relationships/flowers state |
| `useSpeechRecognition` | Web Speech API wrapper |
| `useChunkDispatcher` | Buffer speech into chunks, POST to backend |

### `lib/`

| Module | Responsibility |
|--------|----------------|
| `api.ts` | Typed fetch wrappers for all endpoints |
| `cytoscape-config.ts` | FCose config, stylesheet |
| `types.ts` | TypeScript interfaces matching backend models |

---

## Configuration

### Backend (`config.py`)

```python
class Settings:
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str  # From environment
    
    gemini_api_key: str  # From environment
    gemini_model: str = "gemini-3-pro"
    
    gardener_interval: int = 90  # DEC-004
    
    cors_origins: list = ["http://localhost:3000"]
```

### Environment Variables

```
NEO4J_PASSWORD=<password>
GEMINI_API_KEY=<api_key>
```

---

## Docker Compose (Local Deployment)

```yaml
version: '3.8'

services:
  neo4j:
    image: neo4j:5
    ports:
      - "7474:7474"  # Browser
      - "7687:7687"  # Bolt
    environment:
      - NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}
    volumes:
      - neo4j_data:/data

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=${NEO4J_PASSWORD}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    depends_on:
      - neo4j

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - backend

volumes:
  neo4j_data:
```

---

## Dependencies

### Backend (`requirements.txt`)

```
fastapi>=0.104.0
uvicorn>=0.24.0
neo4j>=5.14.0
google-generativeai>=0.3.0
pydantic>=2.5.0
sse-starlette>=1.8.0
python-dotenv>=1.0.0
```

### Frontend (`package.json` dependencies)

```json
{
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "cytoscape": "^3.26.0",
    "cytoscape-fcose": "^2.2.0"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "@types/react": "^18.2.0",
    "@types/node": "^20.10.0"
  }
}
```

---

## Decision Traceability

| Aspect | Decision | Reference |
|--------|----------|-----------|
| Backend framework | FastAPI | Handover |
| Frontend framework | Next.js | Handover |
| Database | Neo4j (local) | Handover, DEC-009 |
| LLM | Gemini 3 Pro | Handover |
| Visualisation | Cytoscape.js + FCose | DEC-008 |
| Gardener interval | 90 seconds | DEC-004 |
| Local only | No cloud deployment | DEC-009 |








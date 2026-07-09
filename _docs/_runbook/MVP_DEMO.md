# plasticFlower MVP Demo Runbook

> **Purpose:** Step-by-step guide to run a successful MVP demo
> **Audience:** Developer, stakeholder demo presenter
> **Last Updated:** 16 December 2025

---

## Prerequisites

| Requirement | Check |
|-------------|-------|
| Docker Desktop running | `docker ps` returns without error |
| Node.js 18+ | `node --version` |
| Python 3.11+ | `python --version` |
| Gemini API key | Valid key in `.env` |

---

## 1. Preflight Checks

### 1.1 Environment Variables

Verify `.env` in project root contains:

```env
NEO4J_URI=neo4j://127.0.0.1:7687
NEO4J_PASSWORD=your_neo4j_password
GEMINI_API_KEY=your_gemini_api_key
```

> ⚠️ **Windows users:** Use `127.0.0.1`, not `localhost` (avoids IPv6 fallback delays)

### 1.2 Neo4j Connectivity

```powershell
# Check Neo4j is running
docker ps | Select-String "neo4j"

# If not running, start it (from repo root so compose reads the root .env)
docker compose -f docker/docker-compose.yml --env-file .env up -d
```

### 1.3 API Key Validation

```powershell
# Quick test (PowerShell)
$env:GEMINI_API_KEY = (Get-Content .env | Select-String "GEMINI_API_KEY" | ForEach-Object { $_.Line.Split("=")[1] })
Write-Host "API Key present: $($env:GEMINI_API_KEY.Length -gt 10)"
```

---

## 2. Startup (Manual)

### 2.1 Start Neo4j + Redis

```powershell
# From repo root — compose must be pointed at the root .env
docker compose -f docker/docker-compose.yml --env-file .env up -d
```

Wait for Neo4j browser at http://localhost:7474

### 2.2 Start Backend

```powershell
cd backend
# Activate virtual environment if needed
.\.venv\Scripts\Activate.ps1

# Start WITHOUT fake mode (real Gemini)
python -m uvicorn app.main:app --host 127.0.0.1 --port 8010
```

Verify: http://127.0.0.1:8010/health returns `{"status":"ok","neo4j":"ok"}`

### 2.3 Start Frontend

```powershell
# New terminal
cd frontend
$env:NEXT_PUBLIC_API_URL = "http://127.0.0.1:8010"
npm run dev
```

Verify: http://localhost:3000 loads the graph canvas

---

## 3. Startup (Helper Script)

```powershell
# From project root (Windows)
.\scripts\start_mvp.ps1

# Or with fake mode for testing
.\scripts\start_mvp.ps1 -FakeMode
```

```bash
# From project root (Linux / macOS)
bash scripts/start_mvp.sh

# Or with fake mode for testing
bash scripts/start_mvp.sh --fake-mode
```

### 3.1 Quick Smoke Test (pre-demo)

```powershell
# Validate end-to-end before stakeholders arrive
python backend/scripts/smoke_test.py --base http://127.0.0.1:8010 --output _docs/_evidence/gate7/smoke_test_results.json
```

- Expect `ok: true` with non-zero nodes/relationships.
- The JSON artefact is stored for Gate 7 evidence (`_docs/_evidence/gate7/`).

---

## 4. Demo Flow

### 4.1 Create Session

1. Open http://localhost:3000
2. Enter a session name (e.g., "AI Discussion Demo")
3. Click "Create Session"
4. Note the SSE status badge shows "Connecting..." → "Live"

### 4.2 Start Speaking

1. Click "Start Recording" (microphone permission required)
2. Speak naturally about a topic (e.g., AI, machine learning, neural networks)
3. Watch for:
   - Transcript appearing in the panel
   - Nodes fading in on the canvas (ghost state = dashed border)
   - Relationships drawing in (animated lines)

### 4.3 Observe Gardener Cycle

1. Keep talking — the Gardener triggers after every 5 processed chunks (`builder_gardener_ratio`, ADR-0010), with a 5-second safety debounce; there is no fixed wall-clock interval
2. Watch for:
   - `gardener_cycle` event in console/logs
   - Ghost nodes becoming solid (dashed → solid border)
   - Flowers forming around related concepts (compound nodes)
   - Possible node merges (duplicates consolidate)

### 4.4 Test Filters (if implemented)

1. Toggle "Solid only" filter — ghost nodes hide
2. Adjust confidence slider — low-confidence nodes hide
3. Select a Flower — only Flower members visible

### 4.5 Export Session

1. Click "Export JSON" — downloads full graph bundle
2. Click "Export Transcript" — downloads plain text
3. Click "Export VTT" — downloads WebVTT file
4. Click "Export Markdown" — downloads LLM summary

### 4.6 End Session

1. Click "End Session"
2. Confirm the session is marked as ended
3. Verify new chunks are rejected (if tested)

---

## 5. Expected Signals

| Signal | Where | Meaning |
|--------|-------|---------|
| SSE badge "Live" | Top of canvas | Connected to backend |
| Nodes fade in | Canvas | Builder extracted concepts |
| Dashed border | Node | Ghost (unconfirmed) |
| Solid border | Node | Confirmed by Gardener |
| Orange border | Node | Stem node (Flower centre) |
| Compound box | Canvas | Flower (thematic cluster) |
| Console `gardener_cycle` | Browser DevTools | Gardener heartbeat |

---

## 6. Troubleshooting

### SSE Not Connecting

1. Check backend is running on port 8010
2. Check CORS allows `http://localhost:3000`
3. Check browser console for errors

### 21-Second Delays (Windows)

1. Ensure `NEO4J_URI=neo4j://127.0.0.1:7687` (not `localhost`)
2. IPv6 fallback causes this delay

### No Nodes Appearing

1. Check Gemini API key is valid
2. Check backend logs for LLM errors
3. Verify `PLASTICFLOWER_FAKE_LLM` is NOT set

### Gardener Not Running

1. Check enough chunks have been submitted — the Gardener runs once per 5 Builder chunks (ratio-based, ADR-0010), so short sessions may not reach a trigger
2. Check for ghost nodes or recent chunk submissions
3. Check backend logs for scheduler errors

### Export Fails

1. Check session exists
2. Check chunks were persisted (not in fake mode without Neo4j)

---

## 7. Performance Expectations

| Metric | Target | Warning |
|--------|--------|---------|
| Builder round-trip | < 5s | > 10s |
| Gardener trigger | every 5 Builder chunks (+5s debounce) | No run after ≥5 chunks |
| SSE reconnect | < 5s | > 15s |
| FCose layout | < 2s | > 5s (>200 nodes) |

---

## 8. Cleanup

```powershell
# Stop services
# Ctrl+C in backend and frontend terminals

# Stop Neo4j + Redis (from repo root)
docker compose -f docker/docker-compose.yml --env-file .env down

# Clear test data (optional)
# Connect to Neo4j and run: MATCH (n) DETACH DELETE n
```

---

*Runbook created for Gate 7 MVP Readiness*


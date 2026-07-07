# Server Start Configuration

## Official Startup Script
Use the official script (recommended):
```powershell
.\scripts\start_mvp.ps1
```

## Manual Startup (if needed)

### Backend (FastAPI)
```powershell
cd backend
python -m uvicorn app.main:app --reload --port 8010
```
**Port: 8010** ← Always use this port!

### Frontend (Next.js)
```powershell
cd frontend
npm run dev
```
**Port: 3000** (default)

### Neo4j (Docker)
```powershell
cd docker
docker compose up -d
```
**Ports: 7474 (browser), 7687 (bolt)**

## URLs
- Frontend: http://localhost:3000
- Backend API: http://127.0.0.1:8010
- Backend Health: http://127.0.0.1:8010/health
- Backend Docs: http://127.0.0.1:8010/docs
- Neo4j Browser: http://localhost:7474

## Environment Variables
Backend looks for:
- `GEMINI_API_KEY` - Required for LLM
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` - Database connection
- Frontend looks for `.env.local` with `NEXT_PUBLIC_API_URL=http://127.0.0.1:8010`

## Quick Kill & Restart
```powershell
# Kill all processes
taskkill /F /IM node.exe 2>$null; taskkill /F /IM python.exe 2>$null

# Start backend (background)
cd backend; python -m uvicorn app.main:app --reload --port 8010

# Start frontend (background)
cd frontend; npm run dev
```


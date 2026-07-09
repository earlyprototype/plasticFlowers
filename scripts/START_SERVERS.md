# Server Start Configuration

## Official Startup Scripts

```bash
# Linux / macOS
bash scripts/start_mvp.sh            # add --fake-mode for no Gemini API calls
# or via make
make demo-fake
```

```powershell
# Windows
.\scripts\start_mvp.ps1              # add -FakeMode for no Gemini API calls
```

Both scripts halt if `.env` is missing or `NEO4J_PASSWORD` is still the
placeholder — copy `.env.example` to `.env` and fill in real values first.

## Manual Startup (if needed)

### Neo4j + Redis (Docker)

```bash
# from the repo root — --env-file wires the root .env into compose
docker compose -f docker/docker-compose.yml --env-file .env up -d
# or: make up
```

**Ports: 7474 (browser), 7687 (bolt), 6379 (redis)**

### Backend (FastAPI)

Running uvicorn by hand does **not** read the root `.env` — the backend reads
several switches straight from the process environment (fake mode,
`PLASTICFLOWER_SKIP_NEO4J`, ...), so export `.env` first:

```bash
# from the repo root — export .env into the shell, then start uvicorn
set -a; . ./.env; set +a
cd backend
python -m uvicorn app.main:app --reload --port 8010
# or simply from the repo root: make backend
# (runs backend/scripts/dev_server.py, which loads the root .env itself)
```

```powershell
# Windows (PowerShell) — load .env into the session, then start uvicorn
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^#][^=]+)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), 'Process')
    }
}
cd backend
python -m uvicorn app.main:app --reload --port 8010
```

**Port: 8010** ← Always use this port!

### Frontend (Next.js)

```bash
cd frontend
npm run dev
# or from the repo root: make frontend
```

**Port: 3000** (default)

## URLs

- Frontend: http://localhost:3000
- Backend API: http://127.0.0.1:8010
- Backend Health: http://127.0.0.1:8010/health
- Backend Docs: http://127.0.0.1:8010/docs
- Neo4j Browser: http://localhost:7474

## Environment Variables

Backend looks for (root `.env`, see `.env.example`):

- `GEMINI_API_KEY` - Required for LLM
- `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD` - Database connection

Frontend looks for `NEXT_PUBLIC_API_URL=http://127.0.0.1:8010` (root `.env`
or `frontend/.env.local`).

## Quick Kill & Restart

Kill only the plasticFlower processes — target them by port, never
`taskkill /IM node.exe` / `pkill python`, which kills unrelated processes.

```bash
# Linux / macOS — find and kill whatever holds the ports
lsof -ti :8010 | xargs -r kill        # backend
lsof -ti :3000 | xargs -r kill        # frontend
```

```powershell
# Windows — resolve PID by port, then kill that PID only
Get-NetTCPConnection -LocalPort 8010 -State Listen | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }  # backend
Get-NetTCPConnection -LocalPort 3000 -State Listen | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }  # frontend
```

Then restart:

```bash
# backend (export .env first — see "Backend (FastAPI)" above — or use make backend)
set -a; . ./.env; set +a
cd backend && python -m uvicorn app.main:app --reload --port 8010
# frontend
cd frontend && npm run dev
```

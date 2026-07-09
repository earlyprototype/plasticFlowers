#!/usr/bin/env bash
#
# Start all plasticFlower MVP services (Linux/macOS).
#
# Mirrors scripts/start_mvp.ps1: checks prerequisites, validates .env,
# installs backend (venv) + frontend (npm) dependencies, starts Neo4j and
# Redis via Docker Compose wired to the root .env, waits for health, then
# runs the backend (uvicorn, port 8010) and frontend (next dev, port 3000).
#
# Usage:
#   bash scripts/start_mvp.sh              # real Gemini mode
#   bash scripts/start_mvp.sh --fake-mode  # PLASTICFLOWER_FAKE_LLM=1 / FAKE_EMBEDDINGS=1

set -euo pipefail

FAKE_MODE=0
for arg in "$@"; do
    case "$arg" in
        --fake-mode|-f) FAKE_MODE=1 ;;
        -h|--help)
            grep '^#' "$0" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        *)
            echo "Unknown argument: $arg (supported: --fake-mode)" >&2
            exit 1
            ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_ROOT/.venv"
ENV_FILE="$PROJECT_ROOT/.env"
COMPOSE_FILE="$PROJECT_ROOT/docker/docker-compose.yml"

echo ""
echo "========================================"
echo "  plasticFlower MVP Startup"
echo "========================================"
echo ""

# 1. Check prerequisites -----------------------------------------------------
echo "[1/6] Checking prerequisites..."

if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: Docker not found. Please install Docker (https://docs.docker.com/get-docker/)." >&2
    exit 1
fi

if ! command -v node >/dev/null 2>&1; then
    echo "ERROR: Node.js not found. Please install Node.js 18+." >&2
    exit 1
fi

PYTHON_BIN=""
for candidate in python3.13 python3.12 python3.11 python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
        if "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
            PYTHON_BIN="$candidate"
            break
        fi
    fi
done
if [ -z "$PYTHON_BIN" ]; then
    echo "ERROR: Python 3.11+ not found. Please install Python 3.11 or newer." >&2
    exit 1
fi

echo "  Docker, Node.js, Python ($PYTHON_BIN) found."

# 2. Check .env ---------------------------------------------------------------
echo ""
echo "[2/6] Checking environment..."

if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: $ENV_FILE not found." >&2
    echo "  Create it from the template, then fill in real values:" >&2
    echo "    cp .env.example .env" >&2
    echo "  At minimum set NEO4J_PASSWORD (and GEMINI_API_KEY for real mode)." >&2
    exit 1
fi

NEO4J_PASSWORD_VALUE="$(grep -E '^NEO4J_PASSWORD=' "$ENV_FILE" | tail -n 1 | cut -d= -f2- | tr -d '[:space:]')"
if [ -z "$NEO4J_PASSWORD_VALUE" ] || [ "$NEO4J_PASSWORD_VALUE" = "your-neo4j-password-here" ]; then
    echo "ERROR: NEO4J_PASSWORD in .env is empty or still the placeholder value." >&2
    echo "  Edit $ENV_FILE and set NEO4J_PASSWORD to a real password before starting." >&2
    exit 1
fi

# Export .env into this shell (backend/uvicorn and compose both use it).
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

if [ "$FAKE_MODE" -eq 0 ] && { [ -z "${GEMINI_API_KEY:-}" ] || [ "${GEMINI_API_KEY:-}" = "your-gemini-api-key-here" ]; }; then
    echo "WARNING: GEMINI_API_KEY not set. Real Gemini mode may fail (use --fake-mode to run without it)."
fi

echo "  Environment loaded."

# 3. Install dependencies ----------------------------------------------------
echo ""
echo "[3/6] Installing dependencies..."

if [ ! -x "$VENV_DIR/bin/python" ]; then
    echo "  Creating virtualenv at $VENV_DIR..."
    "$PYTHON_BIN" -m venv "$VENV_DIR"
fi
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet -e "$PROJECT_ROOT/backend[dev]"
echo "  Backend dependencies installed (.venv)."

if [ ! -d "$PROJECT_ROOT/frontend/node_modules" ]; then
    echo "  Installing frontend dependencies (npm install)..."
    (cd "$PROJECT_ROOT/frontend" && npm install)
else
    echo "  Frontend dependencies present (frontend/node_modules)."
fi

# 4. Start Neo4j + Redis (Docker) --------------------------------------------
echo ""
echo "[4/6] Starting Neo4j + Redis (Docker Compose)..."

docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d

echo "  Waiting for Neo4j to become healthy..."
NEO4J_READY=0
for _ in $(seq 1 30); do
    STATUS="$(docker inspect --format '{{.State.Health.Status}}' plasticflower-neo4j 2>/dev/null || echo unknown)"
    if [ "$STATUS" = "healthy" ]; then
        NEO4J_READY=1
        break
    fi
    sleep 3
done
if [ "$NEO4J_READY" -eq 1 ]; then
    echo "  Neo4j healthy."
else
    echo "WARNING: Neo4j not healthy yet; continuing anyway. Check: docker logs plasticflower-neo4j"
fi

# 5. Start backend -----------------------------------------------------------
echo ""
echo "[5/6] Starting backend..."

if [ "$FAKE_MODE" -eq 1 ]; then
    export PLASTICFLOWER_FAKE_LLM=1
    export PLASTICFLOWER_FAKE_EMBEDDINGS=1
    echo "  Fake mode enabled (no Gemini API calls)."
else
    unset PLASTICFLOWER_FAKE_LLM PLASTICFLOWER_FAKE_EMBEDDINGS
    echo "  Real Gemini mode."
fi

(cd "$PROJECT_ROOT/backend" && "$VENV_DIR/bin/python" -m uvicorn app.main:app --host 127.0.0.1 --port 8010) &
BACKEND_PID=$!

cleanup() {
    echo ""
    echo "Stopping services..."
    kill "$BACKEND_PID" "${FRONTEND_PID:-}" 2>/dev/null || true
    wait 2>/dev/null || true
    echo "Services stopped. Neo4j/Redis still running (stop with: docker compose -f docker/docker-compose.yml --env-file .env down)"
}
trap cleanup EXIT INT TERM

echo "  Backend starting on http://127.0.0.1:8010..."
BACKEND_READY=0
for _ in $(seq 1 30); do
    if curl -fsS "http://127.0.0.1:8010/health" >/dev/null 2>&1; then
        BACKEND_READY=1
        break
    fi
    sleep 2
done
if [ "$BACKEND_READY" -eq 1 ]; then
    echo "  Backend healthy."
else
    echo "WARNING: Backend not responding yet. Check http://127.0.0.1:8010/health"
fi

# 6. Start frontend ----------------------------------------------------------
echo ""
echo "[6/6] Starting frontend..."

export NEXT_PUBLIC_API_URL="http://127.0.0.1:8010"
(cd "$PROJECT_ROOT/frontend" && npm run dev) &
FRONTEND_PID=$!

echo ""
echo "========================================"
echo "  MVP Ready!"
echo "========================================"
echo ""
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://127.0.0.1:8010"
echo "  Neo4j:    http://localhost:7474"
echo ""
if [ "$FAKE_MODE" -eq 1 ]; then
    echo "  Mode: FAKE (no Gemini API calls)"
else
    echo "  Mode: REAL Gemini"
fi
echo ""
echo "  Press Ctrl+C to stop backend + frontend (Docker services keep running)."
echo ""

wait

# plasticFlower — thin task runner.
# Each target shells out to the same commands the startup scripts use.
#
#   make setup      install backend (.venv) + frontend (npm) dependencies
#   make up         start Neo4j + Redis via Docker Compose (root .env wired)
#   make backend    run FastAPI backend on http://127.0.0.1:8010 (loads root .env)
#   make frontend   run Next.js dev server on http://localhost:3000
#   make demo-fake  full stack in fake mode (no Gemini API calls)
#   make test       backend pytest + frontend vitest
#   make lint       frontend eslint
#   make build      frontend production build
#   make down       stop the Docker services

VENV        := .venv
PYTHON      := $(VENV)/bin/python
PIP         := $(VENV)/bin/pip
COMPOSE     := docker compose -f docker/docker-compose.yml --env-file .env

.PHONY: setup up backend frontend demo-fake test lint build down

setup:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e 'backend[dev]'
	cd frontend && npm install

up:
	$(COMPOSE) up -d

# dev_server.py loads the root .env (python-dotenv) before starting uvicorn,
# so os.getenv-read switches (fake mode, skip-neo4j, ...) are honoured here.
backend:
	$(PYTHON) backend/scripts/dev_server.py

frontend:
	cd frontend && npm run dev

demo-fake:
	bash scripts/start_mvp.sh --fake-mode

test:
	cd backend && ../$(PYTHON) -m pytest
	cd frontend && npm run test

lint:
	cd frontend && npm run lint

build:
	cd frontend && npm run build

down:
	$(COMPOSE) down

# Gate 1 — Dev Environment Green

> **Objective:** Local dev environment runs end-to-end (backend, frontend, Neo4j)
> **Entry:** Gate 0 signed off (pre-implementation report accepted)
> **Exit:** All services start locally; minimal "hello" confirmed

---

## Serial Dependencies (must complete in order)

1. **Repo skeleton** — Create directory structure matching `_docs/_dev/_MVP/_structure/01_project_structure.md`
2. **Docker Compose** — Neo4j container configured and reachable
3. **Backend scaffold** — FastAPI app starts on `localhost:8000`
4. **Frontend scaffold** — Next.js app starts on `localhost:3000`

---

## Parallel Lanes (can run simultaneously)

| Lane | Work | Owner |
|------|------|-------|
| A | Backend: FastAPI skeleton + health endpoint | Backend dev |
| B | Frontend: Next.js skeleton + basic page | Frontend dev |
| C | Infra: Docker Compose + Neo4j config | Either |

**Note:** Lanes A and B can start once repo skeleton exists. Lane C can run in parallel.

---

## Deliverables

| Deliverable | Acceptance Criteria |
|-------------|---------------------|
| `docker-compose.yml` | `docker compose up` starts Neo4j on `localhost:7687` |
| `backend/` folder | `uvicorn app.main:app` returns 200 on `/health` |
| `frontend/` folder | `npm run dev` renders a page at `localhost:3000` |
| `.env.example` | Documents `NEO4J_PASSWORD`, `GEMINI_API_KEY` |

---

## Verification Checklist

- [ ] Neo4j browser accessible at `localhost:7474`
- [ ] Backend `/health` returns `{"status": "ok"}`
- [ ] Frontend page renders without errors
- [ ] Environment variables documented in `.env.example`

---

## Handover to Gate 2

**Pass when:**
1. All verification items checked
2. Repo pushed / committed
3. No blocking errors in console

**Handover artefact:** Working local stack ready for contract implementation

---

## Reference

- [Project Structure](../../_docs/_dev/_MVP/_structure/01_project_structure.md)
- [High-Level Plan](../overview/highplan.md)


# docker

Docker Compose stack for plasticFlower's data services. The app itself
(backend on 8010, frontend on 3000) runs on the host — see
`scripts/start_mvp.sh` / `scripts/start_mvp.ps1` or the root `Makefile`.

## What runs

| Service | Image           | Container             | Ports                            |
| ------- | --------------- | --------------------- | -------------------------------- |
| Neo4j   | `neo4j:5.22`    | `plasticflower-neo4j` | 7474 (HTTP browser), 7687 (Bolt) |
| Redis   | `redis:7.2-alpine` | `plasticflower-redis` | 6379                          |

Neo4j loads the `apoc` plugin (GDS was dropped per ADR-0001). Redis persists
with `--save 60 1`. Data lives in named volumes: `neo4j-data`, `neo4j-logs`,
`redis-data`.

## Where the password comes from

The compose file reads `NEO4J_PASSWORD` and refuses to start if it is unset
(`${NEO4J_PASSWORD:?...}`). Compose does **not** read the repo-root `.env`
automatically from this directory, so wire it explicitly:

```bash
# from the repo root (recommended — single source of truth: root .env)
docker compose -f docker/docker-compose.yml --env-file .env up -d

# or from this directory
docker compose --env-file ../.env up -d

# or export it yourself
export NEO4J_PASSWORD=...   # PowerShell: $env:NEO4J_PASSWORD = "..."
docker compose up -d
```

`make up` / `make down` and both start scripts already pass `--env-file`.
The username is fixed to `neo4j`; the backend reads the same
`NEO4J_USERNAME` / `NEO4J_PASSWORD` pair from the root `.env`.

Note: Neo4j bakes the password into the data volume on **first** start.
Changing `NEO4J_PASSWORD` in `.env` later does not change the database
password — either change it in Neo4j (`ALTER CURRENT USER ...`) or wipe the
volume (below).

## Stop / reset / wipe

```bash
# stop containers, keep data
docker compose -f docker/docker-compose.yml --env-file .env down

# stop and DELETE ALL DATA (graph, logs, redis) — full reset
docker compose -f docker/docker-compose.yml --env-file .env down -v

# then start fresh (new password takes effect here)
docker compose -f docker/docker-compose.yml --env-file .env up -d
```

Health checks: `docker ps` shows `(healthy)` when ready; Neo4j takes ~30 s on
first boot. Logs: `docker logs plasticflower-neo4j` / `docker logs
plasticflower-redis`.

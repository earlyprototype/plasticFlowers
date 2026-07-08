## Gate 4 — Builder Replay Evidence

Use the bundled replay harness to drive deterministic chunks through the live backend while capturing the instrumentation logs added in Lane B.

### Preconditions
- Backend + Neo4j running locally (`uvicorn backend.app.main:app --reload`)
- Frontend optional (for SSE visuals), but not required for this log scrape
- Session created via `POST /api/sessions` (grab the `session_id`)

### Replay Command
```
cd frontend
npm run replay -- --session SESSION_ID --file ../_docs/_evidence/gate4/replay_sample.json --delay 750
```

### Capture Builder Logs
While the replay runs, tail the backend logs (PowerShell example):
```
Get-Content -Path .\backend\builder.log -Wait | Where-Object { $_ -match "builder\.(complete|timeout)" }
```

### Expected Log Shape
```
INFO builder.complete session_id=... chunk_id=... round_trip_ms=... llm_call_ms=... nodes_created=3 relationships_created=2 parse_retries=0 timed_out=False errored=False
```

Paste the actual log snippet below:

```
builder.complete session=gate4-replay chunk=chunk_c49446b4126041f6b74b0857233ab37f round_trip_ms=1.39 llm_call_ms=0.62 nodes_created=5 relationships_created=4 parse_retries=0 timed_out=False errored=False
builder.complete session=gate4-replay chunk=chunk_a49205c9600c46a38ca33760a4b98939 round_trip_ms=1.74 llm_call_ms=0.59 nodes_created=5 relationships_created=4 parse_retries=0 timed_out=False errored=False
builder.complete session=gate4-replay chunk=chunk_f14b25c5257040fc96a6837042f2f1c9 round_trip_ms=0.57 llm_call_ms=0.24 nodes_created=5 relationships_created=4 parse_retries=0 timed_out=False errored=False
```


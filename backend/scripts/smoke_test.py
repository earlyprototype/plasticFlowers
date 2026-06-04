"""
Gate 7 smoke test.

Runs a deterministic end-to-end path against a running backend:
1) health
2) create session
3) submit 3 chunks
4) wait for processing
5) verify nodes and relationships
6) export json / transcript / vtt / markdown
7) end + delete session
8) write PASS/FAIL with timings to JSON for evidence capture

Usage:
    python backend/scripts/smoke_test.py --base http://127.0.0.1:8010
"""

from __future__ import annotations

import argparse
import json
import socket
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Force IPv4 to avoid Windows IPv6 fallback delays (~21s per request)
_original_getaddrinfo = socket.getaddrinfo

def _ipv4_only_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    return _original_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)

socket.getaddrinfo = _ipv4_only_getaddrinfo

import requests

DEFAULT_BASE = "http://127.0.0.1:8010"
# Per-request timeout: 30s base + 21s IPv6 fallback buffer + margin
REQUEST_TIMEOUT = 60
DEFAULT_OUTPUT = Path(__file__).resolve().parents[2] / "_docs" / "_evidence" / "gate7" / "smoke_test_results.json"


def request(method: str, url: str, *, body: Dict[str, Any] | None = None, headers: Dict[str, str] | None = None) -> Tuple[int, str]:
    """Make HTTP request using requests library (better IPv4 on Windows)."""
    headers = headers or {}
    if body:
        headers.setdefault("Content-Type", "application/json")
    try:
        resp = requests.request(method, url, json=body if body else None, headers=headers or None, timeout=60)
        return resp.status_code, resp.text
    except requests.exceptions.RequestException as exc:
        print(f"[ERROR] {method} {url}: {exc}", file=sys.stderr)
        raise


def parse_json(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


@dataclass
class SmokeStep:
    name: str
    ok: bool
    detail: str
    elapsed_ms: float


@dataclass
class SmokeContext:
    base: str
    api: str
    session_id: str | None = None
    steps: List[SmokeStep] = field(default_factory=list)
    node_count: int = 0
    relationship_count: int = 0
    flower_count: int = 0

    def record(self, name: str, ok: bool, detail: str, elapsed_ms: float) -> None:
        self.steps.append(SmokeStep(name=name, ok=ok, detail=detail, elapsed_ms=elapsed_ms))


def run_smoke(base: str, output: Path) -> int:
    ctx = SmokeContext(base=base.rstrip("/"), api=f"{base.rstrip('/')}/api")
    started_at = datetime.now(timezone.utc)
    suite_start = time.perf_counter()

    print(f"Base URL: {ctx.base}")

    def step(name: str, fn) -> None:
        t0 = time.perf_counter()
        ok = True
        detail = "ok"
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 - report any failure
            ok = False
            detail = str(exc)
            raise
        finally:
            ctx.record(name, ok, detail, (time.perf_counter() - t0) * 1000)

    try:
        step("health", lambda: _assert_status(*request("GET", f"{ctx.base}/health"), expected=200))

        def create_session() -> None:
            status_code, payload_raw = request("POST", f"{ctx.api}/sessions", body={"name": "smoke"})
            payload = parse_json(payload_raw)
            _assert_status(status_code, payload_raw, expected=201)
            ctx.session_id = payload["id"]

        step("create_session", create_session)

        step("list_sessions", lambda: _assert_status(*request("GET", f"{ctx.api}/sessions"), expected=200))

        def submit_chunks() -> None:
            if not ctx.session_id:
                raise RuntimeError("session_id missing")
            # Realistic test chunks that will produce nodes and relationships
            test_chunks = [
                "Machine learning is a subset of artificial intelligence. Deep learning uses neural networks to process data.",
                "Python is widely used for data science. TensorFlow and PyTorch are popular deep learning frameworks built in Python.",
                "Natural language processing enables computers to understand human language. GPT models use transformers for NLP tasks.",
            ]
            for idx, text in enumerate(test_chunks):
                status_code, payload_raw = request(
        "POST",
                    f"{ctx.api}/sessions/{ctx.session_id}/chunks",
                    body={
                        "text": text,
                        "start_time": float(idx * 10),
                        "end_time": float(idx * 10 + 9),
                    },
    )
                _assert_status(status_code, payload_raw, expected=202)

        step("submit_chunks", submit_chunks)

        # Allow Builder + Gardener to process
        time.sleep(5)

        def verify_graph() -> None:
            if not ctx.session_id:
                raise RuntimeError("session_id missing")
            status_code, nodes_raw = request("GET", f"{ctx.api}/sessions/{ctx.session_id}/nodes")
            _assert_status(status_code, nodes_raw, expected=200)
            nodes_payload = parse_json(nodes_raw)
            ctx.node_count = len(nodes_payload.get("nodes", [])) if isinstance(nodes_payload, dict) else 0
            if ctx.node_count == 0:
                raise AssertionError("No nodes returned")

            status_code, rels_raw = request("GET", f"{ctx.api}/sessions/{ctx.session_id}/relationships")
            _assert_status(status_code, rels_raw, expected=200)
            rels_payload = parse_json(rels_raw)
            ctx.relationship_count = (
                len(rels_payload.get("relationships", [])) if isinstance(rels_payload, dict) else 0
            )
            if ctx.relationship_count == 0:
                raise AssertionError("No relationships returned")

            status_code, flowers_raw = request("GET", f"{ctx.api}/sessions/{ctx.session_id}/flowers")
            _assert_status(status_code, flowers_raw, expected=200)
            flowers_payload = parse_json(flowers_raw)
            ctx.flower_count = len(flowers_payload.get("flowers", [])) if isinstance(flowers_payload, dict) else 0

        step("verify_graph", verify_graph)

        def export_all() -> None:
            if not ctx.session_id:
                raise RuntimeError("session_id missing")

            export_endpoints = {
                "json": ("application/json", lambda text: len(text) > 0),
                "transcript": ("text/plain", lambda text: len(text.strip()) > 0),
                "vtt": ("text/vtt", lambda text: text.startswith("WEBVTT")),
                "markdown": ("text/markdown", lambda text: len(text.strip()) > 0),
            }
            for name in ["json", "transcript", "vtt", "markdown"]:
                status_code, body = request("GET", f"{ctx.api}/sessions/{ctx.session_id}/export/{name}")
                _assert_status(status_code, body, expected=200)
                validator = export_endpoints[name][1]
                if not validator(body):
                    raise AssertionError(f"{name} export empty")

        step("exports", export_all)

        step(
            "end_session",
            lambda: _assert_status(
                *request("POST", f"{ctx.api}/sessions/{ctx.session_id}/end"), expected=200
            ),
        )

        step(
            "delete_session",
            lambda: _assert_status(
                *request("DELETE", f"{ctx.api}/sessions/{ctx.session_id}"), expected=200
            ),
        )

        ok = all(s.ok for s in ctx.steps)
    except Exception as exc:  # noqa: BLE001
        ok = False
        print(f"Smoke test failed: {exc}", file=sys.stderr)

    total_ms = (time.perf_counter() - suite_start) * 1000
    summary = {
        "base": ctx.base,
        "session_id": ctx.session_id,
        "started_at": started_at.isoformat(),
        "elapsed_ms": round(total_ms, 2),
        "ok": ok,
        "counts": {
            "nodes": ctx.node_count,
            "relationships": ctx.relationship_count,
            "flowers": ctx.flower_count,
        },
        "steps": [
            {
                "name": s.name,
                "ok": s.ok,
                "detail": s.detail,
                "elapsed_ms": round(s.elapsed_ms, 2),
            }
            for s in ctx.steps
        ],
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2))
    status_text = "PASS" if ok else "FAIL"
    print(json.dumps(summary, indent=2))
    print(f"[{status_text}] wrote results to {output}")

    return 0 if ok else 1


def _assert_status(status_code: int, body: str, *, expected: int) -> None:
    if status_code != expected:
        raise AssertionError(f"Expected HTTP {expected}, got {status_code}: {body}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run plasticFlower smoke test against a running backend.")
    parser.add_argument("--base", default=DEFAULT_BASE, help="Backend base URL (default http://127.0.0.1:8010)")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Where to write JSON results (default _docs/_evidence/gate7/smoke_test_results.json)",
    )
    args = parser.parse_args()
    exit_code = run_smoke(args.base, args.output)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()




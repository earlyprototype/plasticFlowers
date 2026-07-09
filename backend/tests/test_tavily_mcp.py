"""Tests for the Tavily MCP client's optional-argument retry behaviour.

Covers tavily_search over a stubbed MCP transport (httpx.MockTransport wired
in via the module's _build_client seam):
- server accepts the full argument set first try
- server rejects the optional args (JSON-RPC invalid params) and the single
  retry without them succeeds, with a warning naming the rejected args
- both the initial call and the retry fail -> TavilyMCPError, no third call
- a non-invalid-params MCP error does not trigger a retry
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import httpx
import pytest

from app.services import tavily_mcp
from app.services.tavily_mcp import TavilyMCPError, tavily_search

# ---------------------------------------------------------------------------
# Stub transport helpers
# ---------------------------------------------------------------------------

_TAVILY_RESULT = {
    "results": [
        {
            "title": "CeADAR - Ireland's Centre for Applied AI",
            "url": "https://ceadar.ie",
            "content": "CeADAR is Ireland's national centre for applied AI.",
            "score": 0.98,
        }
    ],
    "answer": "CeADAR is Ireland's national centre for applied AI.",
}

_SUCCESS_PAYLOAD = {
    "jsonrpc": "2.0",
    "id": 1,
    "result": {
        "content": [{"type": "text", "text": json.dumps(_TAVILY_RESULT)}]
    },
}

_INVALID_PARAMS_PAYLOAD = {
    "jsonrpc": "2.0",
    "id": 1,
    "error": {
        "code": -32602,
        "message": "Invalid params: include_answer is not an accepted argument",
    },
}

_OTHER_ERROR_PAYLOAD = {
    "jsonrpc": "2.0",
    "id": 1,
    "error": {"code": -32000, "message": "internal server error"},
}


def _sse_response(payload: dict) -> httpx.Response:
    """Build an SSE response carrying a single JSON-RPC event."""
    return httpx.Response(
        200,
        headers={"content-type": "text/event-stream"},
        content=f"data: {json.dumps(payload)}\n\n".encode(),
    )


def _stub_transport(monkeypatch, payloads: list[dict]) -> list[dict]:
    """Route tavily_mcp's HTTP client through a MockTransport.

    Each element of ``payloads`` is the JSON-RPC payload returned for the
    n-th request (the last one repeats if more requests arrive). Returns a
    list that accumulates the tool-call ``arguments`` of every request seen.
    """
    seen_arguments: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode())
        assert body["method"] == "tools/call"
        assert body["params"]["name"] == "tavily_search"
        seen_arguments.append(body["params"]["arguments"])
        payload = payloads[min(len(seen_arguments) - 1, len(payloads) - 1)]
        return _sse_response(payload)

    def build_client() -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=httpx.MockTransport(handler))

    monkeypatch.setattr(tavily_mcp, "_build_client", build_client)
    return seen_arguments


@pytest.fixture(autouse=True)
def fake_settings(monkeypatch):
    """Point the client at a fake key/URL so no real config is needed."""
    settings = SimpleNamespace(
        tavily_api_key=SimpleNamespace(get_secret_value=lambda: "test-key"),
        tavily_mcp_url="https://mcp.tavily.example/mcp/",
    )
    monkeypatch.setattr(tavily_mcp, "get_settings", lambda: settings)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


async def test_search_accepted_first_try(monkeypatch):
    seen = _stub_transport(monkeypatch, [_SUCCESS_PAYLOAD])

    response = await tavily_search("CeADAR", max_results=3)

    # Exactly one call, with the full (optional args included) argument set
    assert len(seen) == 1
    assert seen[0] == {
        "query": "CeADAR",
        "max_results": 3,
        "search_depth": "basic",
        "include_answer": True,
    }
    assert response.query == "CeADAR"
    assert [r.url for r in response.results] == ["https://ceadar.ie"]
    assert response.answer == _TAVILY_RESULT["answer"]


async def test_search_rejected_then_retry_succeeds(monkeypatch, caplog):
    seen = _stub_transport(
        monkeypatch, [_INVALID_PARAMS_PAYLOAD, _SUCCESS_PAYLOAD]
    )

    with caplog.at_level("WARNING"):
        response = await tavily_search("CeADAR")

    # First call carried the optional args; the retry dropped them
    assert len(seen) == 2
    assert "include_answer" in seen[0] and "search_depth" in seen[0]
    assert "include_answer" not in seen[1]
    assert "search_depth" not in seen[1]
    assert seen[1] == {"query": "CeADAR", "max_results": 5}

    # The retry result still parses normally
    assert response.answer == _TAVILY_RESULT["answer"]
    assert len(response.results) == 1

    # A warning names the rejected args
    warnings = [r.getMessage() for r in caplog.records if r.levelname == "WARNING"]
    assert any(
        "include_answer" in message and "search_depth" in message
        for message in warnings
    ), f"expected a warning naming the rejected args, got: {warnings}"


async def test_search_raises_when_retry_also_fails(monkeypatch):
    seen = _stub_transport(monkeypatch, [_INVALID_PARAMS_PAYLOAD])

    with pytest.raises(TavilyMCPError):
        await tavily_search("CeADAR")

    # Exactly one retry: two calls total, never a third
    assert len(seen) == 2


async def test_search_does_not_retry_other_errors(monkeypatch):
    seen = _stub_transport(monkeypatch, [_OTHER_ERROR_PAYLOAD])

    with pytest.raises(TavilyMCPError) as excinfo:
        await tavily_search("CeADAR")

    assert len(seen) == 1, "non-invalid-params errors must not trigger a retry"
    assert "internal server error" in str(excinfo.value)

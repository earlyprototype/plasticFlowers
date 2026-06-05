from __future__ import annotations

from types import SimpleNamespace

import pytest
from pydantic import SecretStr

from backend.app.services import llm


class DummySettings:
    def __init__(self) -> None:
        self.gemini_api_key = SecretStr("test-key")
        self.gemini_model = "gemini-test"
        self.gemini_model_builder = "gemini-test"
        self.gemini_temperature = 0.2
        self.gemini_top_p = 0.9
        self.gemini_max_output_tokens = 256
        self.gemini_request_timeout = 5.0
        self.gemini_max_retries = 0
        self.vertex_project_id = ""
        self.vertex_location = "us-central1"


@pytest.fixture(autouse=True)
def reset_client():
    """Reset the module-level _CLIENT singleton before and after each test."""
    llm._CLIENT = None
    yield
    llm._CLIENT = None


def _stub_settings(monkeypatch, **overrides) -> DummySettings:
    settings = DummySettings()
    for key, value in overrides.items():
        setattr(settings, key, value)
    monkeypatch.setattr(llm, "get_settings", lambda: settings)
    return settings


def _stub_client(monkeypatch, response_sequence):
    """Patch llm._get_client to return a fake whose aio.models.generate_content
    pops items from *response_sequence*: raises if item is an Exception, else
    returns it as the response object."""
    calls: list[dict] = []
    responses = list(response_sequence)

    async def fake_generate_content(**kwargs):
        calls.append(kwargs)
        item = responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    # Build fake client with the nested .aio.models path
    fake_models = SimpleNamespace(generate_content=fake_generate_content)
    fake_aio = SimpleNamespace(models=fake_models)
    fake_client = SimpleNamespace(aio=fake_aio)

    monkeypatch.setattr(llm, "_get_client", lambda settings: fake_client)

    # Also stub create_gemini_config so tests don't depend on real genai types
    monkeypatch.setattr(llm, "create_gemini_config", lambda **_: SimpleNamespace())

    return fake_client, calls


@pytest.mark.asyncio
async def test_generate_structured_json_returns_payload(monkeypatch):
    _stub_settings(monkeypatch)
    _, calls = _stub_client(
        monkeypatch,
        [SimpleNamespace(text='{"nodes": [], "relationships": []}')],
    )

    payload = await llm.generate_structured_json("prompt", schema={"type": "object"})

    assert payload == {"nodes": [], "relationships": []}
    assert len(calls) == 1
    assert calls[0]["contents"] == "prompt"
    assert calls[0]["model"] == "gemini-test"


@pytest.mark.asyncio
async def test_generate_structured_json_retries_and_succeeds(monkeypatch):
    _stub_settings(monkeypatch, gemini_max_retries=1)
    _, calls = _stub_client(
        monkeypatch,
        [
            RuntimeError("boom"),
            SimpleNamespace(text='{"ok": true}'),
        ],
    )

    sleep_calls: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleep_calls.append(delay)

    monkeypatch.setattr(llm, "_sleep", fake_sleep)

    payload = await llm.generate_structured_json("prompt", schema={"type": "object"})

    assert payload == {"ok": True}
    assert len(calls) == 2
    assert sleep_calls and sleep_calls[0] >= 0.0


@pytest.mark.asyncio
async def test_generate_structured_json_raises_on_invalid_json(monkeypatch):
    _stub_settings(monkeypatch)
    _stub_client(monkeypatch, [SimpleNamespace(text="not-json")])

    with pytest.raises(llm.LLMError):
        await llm.generate_structured_json("prompt", schema={"type": "object"})

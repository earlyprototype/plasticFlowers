from __future__ import annotations

from types import SimpleNamespace

import pytest
from pydantic import SecretStr

from backend.app.services import llm


class DummySettings:
    def __init__(self) -> None:
        self.gemini_api_key = SecretStr("test-key")
        self.gemini_model = "gemini-pro"
        self.gemini_temperature = 0.2
        self.gemini_top_p = 0.9
        self.gemini_max_output_tokens = 256
        self.gemini_request_timeout = 0.1
        self.gemini_max_retries = 0


@pytest.fixture(autouse=True)
def reset_model(monkeypatch):
    monkeypatch.setattr(llm, "_MODEL", None)
    monkeypatch.setattr(llm.genai, "configure", lambda api_key: None)
    yield
    llm._MODEL = None


def _stub_settings(monkeypatch, **overrides):
    settings = DummySettings()
    for key, value in overrides.items():
        setattr(settings, key, value)
    monkeypatch.setattr(llm, "get_settings", lambda: settings)
    return settings


def _stub_model(monkeypatch, response_sequence):
    class FakeModel:
        def __init__(self):
            self.calls = []
            self._responses = list(response_sequence)

        def generate_content(self, **kwargs):
            self.calls.append(kwargs)
            response = self._responses.pop(0)
            if isinstance(response, Exception):
                raise response
            return response

    fake = FakeModel()
    monkeypatch.setattr(llm.genai, "GenerativeModel", lambda **_: fake)
    return fake


@pytest.mark.asyncio
async def test_generate_structured_json_returns_payload(monkeypatch):
    _stub_settings(monkeypatch)
    fake_model = _stub_model(
        monkeypatch,
        [SimpleNamespace(text='{"nodes": [], "relationships": []}')],
    )

    payload = await llm.generate_structured_json("prompt", schema={"type": "object"})

    assert payload == {"nodes": [], "relationships": []}
    assert fake_model.calls[0]["contents"] == ["prompt"]
    config = fake_model.calls[0]["generation_config"]
    assert config.response_mime_type == "application/json"
    assert config.response_schema == {"type": "object"}


@pytest.mark.asyncio
async def test_generate_structured_json_retries_and_succeeds(monkeypatch):
    _stub_settings(monkeypatch, gemini_max_retries=1)
    fake_model = _stub_model(
        monkeypatch,
        [
            RuntimeError("boom"),
            SimpleNamespace(text='{"ok": true}'),
        ],
    )
    sleep_calls = []

    async def fake_sleep(delay: float):
        sleep_calls.append(delay)

    monkeypatch.setattr(llm, "_sleep", fake_sleep)

    payload = await llm.generate_structured_json("prompt", schema={"type": "object"})

    assert payload == {"ok": True}
    assert len(fake_model.calls) == 2
    assert sleep_calls and sleep_calls[0] >= 0.0


@pytest.mark.asyncio
async def test_generate_structured_json_raises_on_invalid_json(monkeypatch):
    _stub_settings(monkeypatch)
    _stub_model(monkeypatch, [SimpleNamespace(text="not-json")])

    with pytest.raises(llm.LLMError):
        await llm.generate_structured_json("prompt", schema={"type": "object"})

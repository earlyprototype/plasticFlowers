from __future__ import annotations

from types import SimpleNamespace

import pytest
from pydantic import SecretStr

from app.services import llm
from app.services import llm_utils


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


# FIX 2: use monkeypatch so pytest owns the restore, rather than mutating
# the module global directly in a plain fixture.
@pytest.fixture(autouse=True)
def reset_client(monkeypatch):
    """Reset the module-level _CLIENT singleton before and after each test."""
    monkeypatch.setattr(llm, "_CLIENT", None)


def _stub_settings(monkeypatch, **overrides) -> DummySettings:
    settings = DummySettings()
    for key, value in overrides.items():
        setattr(settings, key, value)
    # Patch both the reference in llm and in llm_utils so create_gemini_config
    # (which calls llm_utils.get_settings) also sees the test settings.
    monkeypatch.setattr(llm, "get_settings", lambda: settings)
    monkeypatch.setattr(llm_utils, "get_settings", lambda: settings)
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

    # FIX 1: do NOT stub create_gemini_config — let the real implementation run
    # so that config-wiring is covered by the tests.

    return fake_client, calls


@pytest.mark.asyncio
async def test_generate_structured_json_returns_payload(monkeypatch):
    _stub_settings(monkeypatch)
    _, calls = _stub_client(
        monkeypatch,
        [SimpleNamespace(text='{"nodes": [], "relationships": []}')],
    )

    schema = {"type": "object"}
    payload = await llm.generate_structured_json("prompt", schema=schema)

    assert payload == {"nodes": [], "relationships": []}
    assert len(calls) == 1
    assert calls[0]["contents"] == "prompt"
    assert calls[0]["model"] == "gemini-test"

    # FIX 1: assert the real config object wired by create_gemini_config.
    # create_gemini_config always sets response_mime_type="application/json"
    # and response_schema to the passed schema dict.
    config = calls[0]["config"]
    assert config.response_mime_type == "application/json"
    assert config.response_schema == schema


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
    # FIX 3: _compute_backoff(0) = min(4.0, 0.5 * 2**0) + jitter = 0.5 + jitter,
    # so the floor is 0.5.  Assert real backoff rather than the trivially-true >= 0.0.
    assert sleep_calls and sleep_calls[0] >= 0.5


@pytest.mark.asyncio
async def test_generate_structured_json_raises_on_invalid_json(monkeypatch):
    _stub_settings(monkeypatch)
    _stub_client(monkeypatch, [SimpleNamespace(text="not-json")])

    with pytest.raises(llm.LLMError):
        await llm.generate_structured_json("prompt", schema={"type": "object"})

"""Tests for the Researcher pipeline (T5).

Covers:
- Gardener scheduler dispatch of research actions (label resolution + logging)
- ResearcherAgent: Tavily happy path, Gemini fallback, error degradation
- Manual research endpoint uses Node.inferred_type
- Reference persistence round-trip (vocabulary_suggestion JSON string,
  fetched_at Neo4j DateTime conversion)
"""

from __future__ import annotations

import inspect
import json
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from neo4j.time import DateTime as Neo4jDateTime

from app.agents.gardener import ResearchAction
from app.agents.researcher import ResearcherAgent, ResearcherAgentError
from app.models import Node, NodeStatus
from app.models.reference import (
    EntityType,
    ReferenceNode,
    ReferenceSource,
    ReferenceSourceType,
    SearchProvider,
)
from app.services import graph_db
from app.services import scheduler as scheduler_module
from app.services import tavily_mcp
from app.services.scheduler import GardenerScheduler
from app.services.tavily_mcp import (
    TavilyMCPError,
    TavilySearchResponse,
    TavilySearchResult,
)

from .fakes import FakeNeo4jDriver


def _make_node(node_id: str = "node-1", label: str = "CeADAR") -> Node:
    return Node(
        id=node_id,
        label=label,
        confidence=0.9,
        mentions=1,
        timestamps=[1.0],
        inferred_type="organisation",
        flower_id=None,
        embedding=None,
        created_at=datetime.now(timezone.utc),
        status=NodeStatus.SOLID,
    )


def _make_reference(**overrides) -> ReferenceNode:
    data = dict(
        id="ref_abc123",
        node_id="node-1",
        session_id="session-1",
        entity_type=EntityType.ORGANISATION,
        canonical_summary="CeADAR is Ireland's national centre for applied AI.",
        sources=[
            ReferenceSource(
                title="CeADAR - Ireland's Centre for Applied AI",
                url="https://ceadar.ie",
                snippet="CeADAR is Ireland's centre for Applied AI...",
                source_type=ReferenceSourceType.OFFICIAL,
            )
        ],
        confidence=0.95,
        ambiguity_notes="",
        needs_user_confirmation=False,
        user_confirmed=False,
        vocabulary_suggestion={"see dar": "CeADAR"},
        search_provider=SearchProvider.TAVILY,
        fetched_at=datetime(2026, 1, 7, 11, 30, 0, tzinfo=timezone.utc),
    )
    data.update(overrides)
    return ReferenceNode(**data)


def _canned_tavily_response(query: str = "CeADAR official website about") -> TavilySearchResponse:
    return TavilySearchResponse(
        query=query,
        results=[
            TavilySearchResult(
                title="CeADAR - Ireland's Centre for Applied AI",
                url="https://ceadar.ie",
                content="CeADAR is Ireland's national centre for applied AI research.",
                score=0.98,
            ),
            TavilySearchResult(
                title="CeADAR | UCD",
                url="https://ucd.ie/ceadar",
                content="CeADAR is hosted at University College Dublin.",
                score=0.85,
            ),
            TavilySearchResult(
                title="CeADAR on LinkedIn",
                url="https://linkedin.com/company/ceadar",
                content="CeADAR helps companies adopt AI.",
                score=0.7,
            ),
        ],
        answer="CeADAR is Ireland's national centre for applied AI, based at UCD.",
    )


def _fake_gemini_client(response=None, error: Exception | None = None):
    """Minimal stand-in for genai.Client exposing aio.models.generate_content."""

    calls: list[dict] = []

    async def generate_content(*, model, contents, config):
        calls.append({"model": model, "contents": contents, "config": config})
        if error is not None:
            raise error
        return response

    client = SimpleNamespace(
        aio=SimpleNamespace(models=SimpleNamespace(generate_content=generate_content))
    )
    return client, calls


def _grounded_gemini_response(text: str = "CeADAR is Ireland's applied AI centre."):
    web = SimpleNamespace(title="CeADAR - Applied AI", uri="https://ceadar.ie")
    metadata = SimpleNamespace(grounding_chunks=[SimpleNamespace(web=web)])
    candidate = SimpleNamespace(grounding_metadata=metadata)
    return SimpleNamespace(text=text, candidates=[candidate])


# -----------------------------------------------------------------------------
# (a) Scheduler dispatch: publish_node_needs_research gets a real label
# -----------------------------------------------------------------------------


async def test_publish_research_actions_uses_node_label(monkeypatch):
    published: list[dict] = []

    async def fake_publish(**kwargs):
        published.append(kwargs)
        return "1-0"

    monkeypatch.setattr(scheduler_module, "publish_node_needs_research", fake_publish)

    node = _make_node("node-1", "CeADAR")
    action = ResearchAction(
        node_id="node-1",
        entity_type="organisation",
        reason="first mention",
        priority="high",
    )

    scheduler = GardenerScheduler()
    await scheduler._publish_research_actions(
        "session-1", [action], {node.id: node}
    )

    assert len(published) == 1
    assert published[0]["label"] == "CeADAR"
    assert published[0]["node_id"] == "node-1"
    assert published[0]["entity_type"] == "organisation"
    assert published[0]["research_reason"] == "first mention"
    assert published[0]["priority"] == "high"


async def test_publish_research_actions_falls_back_to_live_lookup(monkeypatch):
    published: list[dict] = []

    async def fake_publish(**kwargs):
        published.append(kwargs)
        return "1-0"

    looked_up: list[str] = []

    async def fake_get_node(session_id: str, node_id: str):
        looked_up.append(node_id)
        return _make_node(node_id, "Enterprise Ireland")

    monkeypatch.setattr(scheduler_module, "publish_node_needs_research", fake_publish)
    monkeypatch.setattr(scheduler_module, "get_node", fake_get_node)

    action = ResearchAction(node_id="node-x", entity_type="funding", reason="")

    scheduler = GardenerScheduler()
    await scheduler._publish_research_actions("session-1", [action], {})

    assert looked_up == ["node-x"]
    assert len(published) == 1
    assert published[0]["label"] == "Enterprise Ireland"


async def test_publish_research_actions_skips_missing_node(monkeypatch):
    published: list[dict] = []

    async def fake_publish(**kwargs):
        published.append(kwargs)
        return "1-0"

    async def fake_get_node(session_id: str, node_id: str):
        return None

    monkeypatch.setattr(scheduler_module, "publish_node_needs_research", fake_publish)
    monkeypatch.setattr(scheduler_module, "get_node", fake_get_node)

    action = ResearchAction(node_id="node-gone", entity_type="organisation", reason="")

    scheduler = GardenerScheduler()
    await scheduler._publish_research_actions("session-1", [action], {})

    assert published == []


async def test_publish_research_actions_survives_publish_failure(monkeypatch, caplog):
    """A failing dispatch is logged with a traceback and does not kill the loop."""
    published: list[dict] = []

    async def fake_publish(**kwargs):
        if kwargs["node_id"] == "node-bad":
            raise RuntimeError("redis down")
        published.append(kwargs)
        return "1-0"

    monkeypatch.setattr(scheduler_module, "publish_node_needs_research", fake_publish)

    nodes = {
        "node-bad": _make_node("node-bad", "Bad"),
        "node-good": _make_node("node-good", "Good"),
    }
    actions = [
        ResearchAction(node_id="node-bad", entity_type="organisation", reason=""),
        ResearchAction(node_id="node-good", entity_type="organisation", reason=""),
    ]

    scheduler = GardenerScheduler()
    with caplog.at_level("ERROR"):
        await scheduler._publish_research_actions("session-1", actions, nodes)

    # Second action still dispatched despite the first failing
    assert [p["label"] for p in published] == ["Good"]
    failure_records = [
        r for r in caplog.records if "research_publish_failed" in r.getMessage()
    ]
    assert failure_records, "dispatch failure should be logged"
    assert failure_records[0].exc_info is not None, "traceback should be included"


async def test_publish_research_actions_respects_researcher_enabled(monkeypatch):
    """RESEARCHER_ENABLED=false must gate automatic dispatch entirely."""
    published: list[dict] = []

    async def fake_publish(**kwargs):
        published.append(kwargs)
        return "1-0"

    monkeypatch.setattr(scheduler_module, "publish_node_needs_research", fake_publish)
    monkeypatch.setattr(
        scheduler_module,
        "get_settings",
        lambda: SimpleNamespace(researcher_enabled=False),
    )

    node = _make_node("node-1", "CeADAR")
    action = ResearchAction(
        node_id="node-1",
        entity_type="organisation",
        reason="first mention",
        priority="high",
    )

    scheduler = GardenerScheduler()
    await scheduler._publish_research_actions("session-1", [action], {node.id: node})

    assert published == [], "no research dispatch when researcher_enabled is false"


# -----------------------------------------------------------------------------
# Manual research endpoint uses Node.inferred_type
# -----------------------------------------------------------------------------


async def test_manual_research_endpoint_uses_inferred_type(monkeypatch):
    from app.api import graph as graph_api

    node = _make_node("node-1", "CeADAR")

    async def fake_get_node(session_id: str, node_id: str):
        return node

    published: list[dict] = []

    async def fake_publish(**kwargs):
        published.append(kwargs)
        return "1-0"

    monkeypatch.setattr(graph_api, "get_node", fake_get_node)
    monkeypatch.setattr(graph_api, "publish_node_needs_research", fake_publish)

    result = await graph_api.trigger_node_research("session-1", "node-1")

    assert result["status"] == "queued"
    assert len(published) == 1
    assert published[0]["entity_type"] == "organisation"  # node.inferred_type
    assert published[0]["label"] == "CeADAR"
    assert published[0]["priority"] == "high"


# -----------------------------------------------------------------------------
# (b) ResearcherAgent with stubbed Tavily
# -----------------------------------------------------------------------------


def test_tavily_search_accepts_include_answer():
    """The kwarg researcher.py passes must exist in the tavily_search signature."""
    params = inspect.signature(tavily_mcp.tavily_search).parameters
    assert "include_answer" in params
    assert params["include_answer"].default is True


async def test_researcher_creates_reference_from_tavily(monkeypatch):
    captured: dict = {}

    async def fake_tavily_search(query, **kwargs):
        captured["query"] = query
        captured["kwargs"] = kwargs
        return _canned_tavily_response(query)

    monkeypatch.setattr(tavily_mcp, "tavily_search", fake_tavily_search)

    agent = ResearcherAgent()
    result = await agent.research(
        session_id="session-1",
        node_id="node-1",
        node_label="ceadar",
        entity_type="organisation",
    )

    assert result.provider_used == SearchProvider.TAVILY
    assert captured["kwargs"].get("include_answer") is True

    ref = result.reference
    assert ref.node_id == "node-1"
    assert ref.session_id == "session-1"
    assert ref.entity_type == EntityType.ORGANISATION
    assert ref.canonical_summary == (
        "CeADAR is Ireland's national centre for applied AI, based at UCD."
    )
    assert len(ref.sources) == 3
    assert ref.sources[0].url == "https://ceadar.ie"
    assert ref.sources[0].source_type == ReferenceSourceType.OFFICIAL
    assert ref.search_provider == SearchProvider.TAVILY
    # Top title contains "CeADAR" with different casing than "ceadar"
    assert ref.vocabulary_suggestion == {"ceadar": "CeADAR"}
    assert ref.confidence > 0.5


# -----------------------------------------------------------------------------
# (c) Tavily failure -> Gemini fallback
# -----------------------------------------------------------------------------


async def test_researcher_falls_back_to_gemini_on_tavily_error(monkeypatch):
    async def failing_tavily(query, **kwargs):
        raise TavilyMCPError("Tavily MCP request timed out after 30s")

    monkeypatch.setattr(tavily_mcp, "tavily_search", failing_tavily)

    client, calls = _fake_gemini_client(response=_grounded_gemini_response())
    from app.services import llm as llm_module

    monkeypatch.setattr(llm_module, "get_gemini_client", lambda: client)

    agent = ResearcherAgent()
    result = await agent.research(
        session_id="session-1",
        node_id="node-1",
        node_label="CeADAR",
        entity_type="organisation",
    )

    assert result.provider_used == SearchProvider.GEMINI
    assert len(calls) == 1, "Gemini fallback should have been invoked"
    ref = result.reference
    assert ref.canonical_summary == "CeADAR is Ireland's applied AI centre."
    assert ref.search_provider == SearchProvider.GEMINI
    assert [s.url for s in ref.sources] == ["https://ceadar.ie"]


async def test_researcher_falls_back_on_unexpected_tavily_exception(monkeypatch):
    """A TypeError-class bug in the Tavily path must not bypass the fallback."""

    async def broken_tavily(query, **kwargs):
        raise TypeError("tavily_search() got an unexpected keyword argument 'include_answer'")

    monkeypatch.setattr(tavily_mcp, "tavily_search", broken_tavily)

    client, calls = _fake_gemini_client(response=_grounded_gemini_response())
    from app.services import llm as llm_module

    monkeypatch.setattr(llm_module, "get_gemini_client", lambda: client)

    agent = ResearcherAgent()
    result = await agent.research(
        session_id="session-1",
        node_id="node-1",
        node_label="CeADAR",
        entity_type="organisation",
    )

    assert result.provider_used == SearchProvider.GEMINI
    assert len(calls) == 1


async def test_researcher_raises_when_gemini_also_fails(monkeypatch):
    async def failing_tavily(query, **kwargs):
        raise TavilyMCPError("boom")

    monkeypatch.setattr(tavily_mcp, "tavily_search", failing_tavily)

    client, _ = _fake_gemini_client(error=RuntimeError("api 400"))
    from app.services import llm as llm_module

    monkeypatch.setattr(llm_module, "get_gemini_client", lambda: client)

    agent = ResearcherAgent()
    with pytest.raises(ResearcherAgentError):
        await agent.research(
            session_id="session-1",
            node_id="node-1",
            node_label="CeADAR",
            entity_type="organisation",
        )


# -----------------------------------------------------------------------------
# (d) Reference persistence round-trip
# -----------------------------------------------------------------------------


async def test_create_reference_serializes_vocabulary_suggestion(monkeypatch):
    reference = _make_reference()
    driver = FakeNeo4jDriver([[{"r": {}}]])

    async def fake_get_driver():
        return driver

    monkeypatch.setattr(graph_db, "get_driver", fake_get_driver)

    created = await graph_db.create_reference("session-1", reference)

    assert created == reference
    params = driver.calls[0]["params"]
    props = params["props"]

    # vocabulary_suggestion must be a JSON string (Neo4j rejects map properties)
    assert isinstance(props["vocabulary_suggestion"], str)
    assert json.loads(props["vocabulary_suggestion"]) == {"see dar": "CeADAR"}

    # Enums serialized as plain strings
    assert props["entity_type"] == "organisation"
    assert props["search_provider"] == "tavily"

    # Sources are flat property maps with string-valued enum and snippet
    assert params["sources"][0]["snippet"].startswith("CeADAR is Ireland's centre")
    assert params["sources"][0]["source_type"] == "official"
    assert "s.snippet = source_data.snippet" in driver.calls[0]["query"]


def test_reference_from_value_parses_json_and_datetime():
    fetched = Neo4jDateTime(2026, 1, 7, 11, 30, 0)
    stored_props = {
        "id": "ref_abc123",
        "node_id": "node-1",
        "session_id": "session-1",
        "entity_type": "organisation",
        "canonical_summary": "CeADAR is Ireland's national centre for applied AI.",
        "confidence": 0.95,
        "ambiguity_notes": "",
        "needs_user_confirmation": False,
        "user_confirmed": False,
        "vocabulary_suggestion": json.dumps({"see dar": "CeADAR"}),
        "search_provider": "tavily",
        "fetched_at": fetched,
    }
    stored_sources = [
        {
            "url": "https://ceadar.ie",
            "title": "CeADAR - Ireland's Centre for Applied AI",
            "snippet": "CeADAR is Ireland's centre for Applied AI...",
            "source_type": "official",
        }
    ]

    reference = graph_db._reference_from_value(stored_props, stored_sources)

    assert reference.vocabulary_suggestion == {"see dar": "CeADAR"}
    assert isinstance(reference.fetched_at, datetime)
    assert reference.fetched_at == fetched.to_native()
    assert reference.entity_type == EntityType.ORGANISATION
    assert reference.search_provider == SearchProvider.TAVILY
    assert len(reference.sources) == 1
    assert reference.sources[0].source_type == ReferenceSourceType.OFFICIAL


def test_reference_from_value_handles_corrupt_vocab_and_legacy_content():
    stored_props = {
        "id": "ref_legacy",
        "node_id": "node-1",
        "session_id": "session-1",
        "entity_type": "organisation",
        "canonical_summary": "Summary.",
        "confidence": 0.5,
        "vocabulary_suggestion": "{not-json",
        "search_provider": "gemini",
        "fetched_at": datetime(2026, 1, 7, 11, 30, 0, tzinfo=timezone.utc),
    }
    # Legacy Source node shape: excerpt stored under `content`, no source_type
    stored_sources = [
        {"url": "https://example.org", "title": "Example", "content": "Legacy excerpt"}
    ]

    reference = graph_db._reference_from_value(stored_props, stored_sources)

    assert reference.vocabulary_suggestion == {}
    assert reference.sources[0].snippet == "Legacy excerpt"
    assert reference.sources[0].source_type == ReferenceSourceType.OTHER


async def test_reference_round_trip_via_create_and_parse(monkeypatch):
    """Write-side props, fed back through _reference_from_value, reproduce the model."""
    reference = _make_reference()
    driver = FakeNeo4jDriver([[{"r": {}}]])

    async def fake_get_driver():
        return driver

    monkeypatch.setattr(graph_db, "get_driver", fake_get_driver)
    await graph_db.create_reference("session-1", reference)

    params = driver.calls[0]["params"]
    stored_props = dict(params["props"])
    # Simulate Neo4j returning its own DateTime type for the temporal property
    stored_props["fetched_at"] = Neo4jDateTime.from_native(reference.fetched_at)

    parsed = graph_db._reference_from_value(stored_props, params["sources"])

    assert parsed == reference

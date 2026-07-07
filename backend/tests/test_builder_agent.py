from __future__ import annotations

from datetime import datetime, timezone
from itertools import count

import pytest

from backend.app.agents import BuilderAgent, BuilderAgentError
from backend.app.models import Node, NodeStatus, RelationshipCategory, RelationshipSource


class FakeLLM:
    def __init__(self, payload):
        self.payload = payload
        self.prompts = []

    async def __call__(self, prompt, schema):
        self.prompts.append(prompt)
        return self.payload


def _existing_node(label: str = "existing concept") -> Node:
    return Node(
        id="node-existing",
        label=label,
        confidence=0.9,
        mentions=3,
        timestamps=[0.5, 1.0],
        inferred_type="concept",
        flower_id=None,
        embedding=None,
        created_at=datetime.now(timezone.utc),
        status=NodeStatus.SOLID,
    )


def _id_generator():
    counter = count(1)

    def factory() -> str:
        return f"id{next(counter)}"

    return factory


@pytest.mark.asyncio
async def test_builder_agent_creates_nodes_and_relationships():
    payload = {
        "nodes": [
            {"label": "graph attention", "inferred_type": "concept", "confidence": 0.91},
        ],
        "relationships": [
            {
                "source": "graph attention",
                "target": "existing concept",
                "category": "CAUSAL",
                "description": "builds on",
                "confidence": 0.88,
                "evidence": "graph attention builds on the existing concept",
            }
        ],
    }
    clock = lambda: datetime(2025, 1, 1, tzinfo=timezone.utc)
    agent = BuilderAgent(llm_fn=FakeLLM(payload), clock=clock, id_factory=_id_generator())
    result = await agent.build(
        chunk_text="Graph attention is important.",
        chunk_timestamp=12.5,
        existing_nodes=[_existing_node()],
    )

    assert len(result.nodes) == 1
    node = result.nodes[0]
    assert node.id == "node_id1"
    assert node.status == NodeStatus.GHOST
    assert node.mentions == 1
    assert node.timestamps == [12.5]

    assert len(result.relationships) == 1
    relationship = result.relationships[0]
    assert relationship.category == RelationshipCategory.CAUSAL
    assert relationship.source_label == "graph attention"
    assert relationship.target_label == "existing concept"
    assert relationship.description == "builds on"
    assert relationship.evidence == "graph attention builds on the existing concept"


@pytest.mark.asyncio
async def test_builder_agent_defaults_unknown_category_to_associative():
    payload = {
        "nodes": [
            {"label": "fresh idea", "inferred_type": "concept", "confidence": 0.7},
            {"label": "fresh idea", "inferred_type": "concept", "confidence": 0.7},
        ],
        "relationships": [
            {
                "source": "fresh idea",
                "target": "existing concept",
                "category": "mystery",
                "description": "relates to",
                "confidence": 0.33,
                "evidence": "fresh idea relates to existing concept",
            }
        ],
    }
    agent = BuilderAgent(llm_fn=FakeLLM(payload), clock=lambda: datetime(2025, 1, 1, tzinfo=timezone.utc), id_factory=_id_generator())
    result = await agent.build(
        chunk_text="Fresh idea relates to previous work.",
        chunk_timestamp=4.2,
        existing_nodes=[_existing_node()],
    )

    assert len(result.nodes) == 1
    relationship = result.relationships[0]
    assert relationship.category == RelationshipCategory.ASSOCIATIVE


@pytest.mark.asyncio
async def test_builder_agent_raises_on_invalid_payload():
    payload = {"nodes": {"label": "bad"}}
    agent = BuilderAgent(llm_fn=FakeLLM(payload))

    with pytest.raises(BuilderAgentError):
        await agent.build(chunk_text="Some text", chunk_timestamp=0.0)


@pytest.mark.asyncio
async def test_builder_agent_creates_new_nodes_even_if_existing_label_present():
    payload = {
        "nodes": [
            {"label": "existing concept", "inferred_type": "concept", "confidence": 0.5},
        ],
        "relationships": [],
    }
    agent = BuilderAgent(llm_fn=FakeLLM(payload))
    result = await agent.build(
        chunk_text="existing concept mentioned again",
        chunk_timestamp=1.2,
        existing_nodes=[_existing_node()],
    )

    assert len(result.nodes) == 1
    assert result.nodes[0].label == "existing concept"
    assert result.nodes[0].id.startswith("node_")

"""Graph response models for Gate 2 GET endpoints.

Spec references:
- `_docs/_dev/_MVP/_api/01_contracts.md` (`/graph`, `/nodes`, `/relationships`, `/flowers`)
- `_docs/_dev/_MVP/_schema/01_data_model.md`
"""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field

from .flower import Flower, FlowerBridge
from .node import Node
from .relationship import Relationship
from .research import ReferenceNode


class GraphState(BaseModel):
    nodes: List[Node] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)
    flowers: List[Flower] = Field(default_factory=list)


class GraphStateResponse(GraphState):
    bridges: List[FlowerBridge] = Field(
        default_factory=list,
        description="Derived Flower bridges (not persisted)",
    )


class NodesResponse(BaseModel):
    nodes: List[Node] = Field(default_factory=list)


class RelationshipsResponse(BaseModel):
    relationships: List[Relationship] = Field(default_factory=list)


class FlowersResponse(BaseModel):
    flowers: List[Flower] = Field(default_factory=list)
    bridges: List[FlowerBridge] = Field(default_factory=list)


class ReferencesResponse(BaseModel):
    references: List[ReferenceNode] = Field(default_factory=list)

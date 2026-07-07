"""Flower schema components (clusters + bridges).

Spec references:
- `_docs/_dev/_MVP/_schema/01_data_model.md`
- `_docs/_dev/_MVP/_api/01_contracts.md` (`GET /flowers`)
- `_docs/_dev/_MVP/_schema/02_design_rationale.md` (dual-dimension Flowers)
"""

from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field

from .relationship import Relationship


class Flower(BaseModel):
    """Gardener-defined thematic cluster (semantic + structural criteria)."""

    id: str = Field(..., description="Flower identifier")
    label: str = Field(..., min_length=2, max_length=64, description="Theme name (2-5 words)")
    stem_node_id: str = Field(..., description="Node with highest centrality for this Flower")
    edge_count: int = Field(..., ge=0, description="Simple density proxy (edge tally)")
    created_at: datetime = Field(..., description="Creation timestamp from Gardener cycle")


class FlowerBridge(BaseModel):
    """Derived relationship between Flowers (query-time only, DEC-012)."""

    source_flower_id: str = Field(..., description="Flower id containing relationship source node")
    target_flower_id: str = Field(..., description="Flower id containing relationship target node")
    connecting_relationships: List[Relationship] = Field(
        default_factory=list,
        description="Relationships whose endpoints live in different Flowers",
    )

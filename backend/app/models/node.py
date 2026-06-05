"""Node model implementation for Gate 2 contracts.

Spec references:
- `_docs/_dev/_MVP/_schema/01_data_model.md` (Node table)
- `_docs/_dev/_MVP/_api/01_contracts.md` (Node payloads)
- `_docs/_dev/_MVP/_ALIGNMENT.md` (emergent schema rules)
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from .enums import NodeStatus


class Node(BaseModel):
    """Canonical representation of a graph node (Builder/Gardener output)."""

    id: str = Field(..., description="Stable identifier shared across REST and SSE events")
    label: str = Field(..., description="Display label captured from the transcript")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="LLM certainty that this node is meaningful"
    )
    mentions: int = Field(
        ..., ge=0, description="How many times the concept has been referenced (similarity ≥0.92)"
    )
    timestamps: List[float] = Field(
        default_factory=list,
        description="Seconds from session start for each mention; used in exports",
    )
    inferred_type: str = Field(
        ..., description="Emergent, freeform type; never restrict to enums per Alignment"
    )
    flower_id: Optional[str] = Field(
        None, description="Flower membership (derived from BELONGS_TO relationship, not stored as property)"
    )
    embedding: Optional[List[float]] = Field(
        default=None,
        description=(
            "Vector representation stored for similarity search. Included here for schema parity, "
            "even if not exposed over REST in Gate 2."
        ),
    )
    created_at: datetime = Field(..., description="Timestamp when the node was first created")
    last_active: Optional[datetime] = Field(
        None, 
        description="Last mention timestamp; used for temporal decay (nodes >5min become LEGACY)"
    )
    status: NodeStatus = Field(
        ..., description="Lifecycle state: Builder adds ghost, Gardener promotes to solid, old nodes become legacy"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "node_a1",
                "label": "transformer attention",
                "confidence": 0.92,
                "mentions": 3,
                "timestamps": [12.4, 48.7, 93.0],
                "inferred_type": "architecture",
                "flower_id": "flower_ml_stack",
                "created_at": "2025-12-13T09:00:00Z",
                "status": "ghost",
            }
        }
    }

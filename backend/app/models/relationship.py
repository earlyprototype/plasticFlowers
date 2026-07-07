"""Relationship model definitions per Gate 2 contracts.

Spec references:
- `_docs/_dev/_MVP/_schema/01_data_model.md`
- `_docs/_dev/_MVP/_api/01_contracts.md`
- `_docs/_dev/_MVP/_ALIGNMENT.md` (category constraint)
- `_docs/_dev/_MVP/_PRE_IMPLEMENTATION_REPORT.md` (relationship id requirement)
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from .enums import RelationshipCategory, RelationshipSource


class Relationship(BaseModel):
    """Directed connection between two nodes (Builder or Gardener output)."""

    id: str = Field(..., description="Required globally unique relationship identifier")
    source_id: str = Field(..., description="Node id at the tail of the edge")
    target_id: str = Field(..., description="Node id at the head of the edge")
    category: RelationshipCategory = Field(
        ..., description="One of the five authorised semantic categories"
    )
    description: str = Field(
        ...,
        min_length=2,
        max_length=80,
        description="2-4 word natural language descriptor",
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="LLM confidence score")
    evidence: str = Field(..., description="Supporting quote or paraphrased snippet")
    source: RelationshipSource = Field(
        ..., description="Builder = chunk-local extraction, Gardener = refinement"
    )
    created_at: datetime = Field(..., description="Timestamp when the edge was first emitted")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "rel_a1",
                "source_id": "node_a1",
                "target_id": "node_b4",
                "category": "CAUSAL",
                "description": "enables fine-tuning",
                "confidence": 0.88,
                "evidence": "The speaker said X enables Y",
                "source": "builder",
                "created_at": "2025-12-13T09:01:30Z",
            }
        }
    }

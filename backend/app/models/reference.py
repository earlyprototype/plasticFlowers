"""Reference models for external enrichment (Phase G: Researcher Agent).

Spec references:
- `_docs/ARCHITECTURE_ADVISORY.md` (Section 3.3: Researcher, Section 4.2: ReferenceNode)
- `_docs/_dev/ADR/0003-gemini-grounding-for-research.md`
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class EntityType(str, Enum):
    """Entity types for research classification.
    
    Note: Start with organisation/funding for testing, expand as needed.
    Full list documented in implementation_plan.md.
    """
    # Core types (enabled for testing)
    ORGANISATION = "organisation"
    FUNDING = "funding"
    
    # Extended types (uncomment when ready)
    PERSON = "person"
    CONCEPT = "concept"
    PAPER = "paper"
    EVENT = "event"
    TOOL = "tool"
    DATASET = "dataset"
    STANDARD = "standard"
    LOCATION = "location"
    PODCAST = "podcast"
    WEBSITE = "website"
    REPO = "repo"


class SearchProvider(str, Enum):
    """Search providers for research routing."""
    TAVILY = "tavily"      # Primary: Web search (1000 free/month)
    GEMINI = "gemini"      # Fallback: Gemini grounding
    GITHUB = "github"      # For repos (MCP - future)
    PAPERS = "papers"      # For papers (MCP - future)


class ReferenceSourceType(str, Enum):
    """Classification of reference source quality/authority."""
    OFFICIAL = "official"      # Official website
    WIKIPEDIA = "wikipedia"    # Wikipedia article
    ACADEMIC = "academic"      # Academic paper/Semantic Scholar
    REPO = "repo"              # GitHub repository
    OTHER = "other"            # General web result


class ReferenceSource(BaseModel):
    """Individual citation within a ReferenceNode."""
    
    title: str = Field(..., description="Title of the source page/document")
    url: str = Field(..., description="URL to the source")
    snippet: str = Field(..., max_length=500, description="Relevant excerpt from the source")
    source_type: ReferenceSourceType = Field(
        ..., description="Classification of source authority"
    )


class ReferenceNode(BaseModel):
    """External enrichment attached to a Node via HAS_REFERENCE relationship.
    
    Design: Single canonical summary with embedded source citations.
    Handles ambiguity with natural language notes and user confirmation.
    """
    
    id: str = Field(..., description="Stable reference identifier (ref_<uuid>)")
    node_id: str = Field(..., description="Parent node this reference enriches")
    session_id: str = Field(..., description="Session scope for the reference")
    
    entity_type: EntityType = Field(..., description="Classified entity type")
    canonical_summary: str = Field(
        ..., 
        max_length=2000,
        description="Single authoritative description synthesised from sources"
    )
    sources: List[ReferenceSource] = Field(
        default_factory=list,
        max_length=5,
        description="1-5 embedded citations supporting the summary"
    )
    
    # Confidence and ambiguity handling
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Overall confidence in the research result"
    )
    ambiguity_notes: str = Field(
        "",
        max_length=500,
        description="Natural language explanation of conflicts/uncertainty (if any)"
    )
    needs_user_confirmation: bool = Field(
        False,
        description="Flag when multiple similar entities found and user should choose"
    )
    user_confirmed: bool = Field(
        False,
        description="User has reviewed and confirmed correctness"
    )
    
    # Vocabulary learning (session-scoped, user-confirmed)
    vocabulary_suggestion: dict = Field(
        default_factory=dict,
        description="Suggested STT corrections from research, e.g., {'see dar': 'CeADAR'}"
    )
    
    # Metadata
    search_provider: SearchProvider = Field(
        ..., description="Which provider returned this result"
    )
    fetched_at: datetime = Field(..., description="When the research was performed")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "ref_abc123",
                "node_id": "node_xyz789",
                "session_id": "session_001",
                "entity_type": "organisation",
                "canonical_summary": "CeADAR is Ireland's national centre for applied AI, based at University College Dublin. It helps companies adopt AI technologies.",
                "sources": [
                    {
                        "title": "CeADAR - Ireland's Centre for Applied AI",
                        "url": "https://ceadar.ie",
                        "snippet": "CeADAR is Ireland's centre for Applied AI...",
                        "source_type": "official"
                    }
                ],
                "confidence": 0.95,
                "ambiguity_notes": "",
                "needs_user_confirmation": False,
                "user_confirmed": False,
                "vocabulary_suggestion": {"see dar": "CeADAR"},
                "search_provider": "tavily",
                "fetched_at": "2026-01-07T11:30:00Z"
            }
        }
    }


# Entity types enabled for testing (subset)
ENABLED_ENTITY_TYPES = [
    EntityType.ORGANISATION,
    EntityType.FUNDING,
]

# Full entity types list for future expansion
ALL_ENTITY_TYPES = list(EntityType)

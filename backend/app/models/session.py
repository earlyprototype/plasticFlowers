"""Session representations (list + detail) per API contracts.

Spec references:
- `_docs/_dev/_MVP/_schema/01_data_model.md`
- `_docs/_dev/_MVP/_api/01_contracts.md` (Session endpoints)
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class SessionSummary(BaseModel):
    """Shape returned by `GET /sessions` (no transcript)."""

    id: str = Field(..., description="Session identifier")
    name: str = Field(..., description="Human-friendly session label")
    language_variant: str = Field(
        "en-GB",
        description="Language variant for spelling consistency (en-GB or en-US)",
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    ended_at: Optional[datetime] = Field(None, description="Null until session ends")


class SessionDetail(SessionSummary):
    """Shape returned by `GET /sessions/{id}` (includes transcript)."""

    transcript: str = Field(
        ...,
        description="Full accumulated transcript text, streamed chunks concatenated",
    )


class SessionListResponse(BaseModel):
    sessions: List[SessionSummary] = Field(default_factory=list)


class SessionCreateRequest(BaseModel):
    name: Optional[str] = Field(
        default=None,
        description="Optional user-provided session name (timestamp fallback when omitted)",
    )
    language_variant: str = Field(
        default="en-GB",
        description="Language variant for spelling consistency (en-GB or en-US)",
    )


class SessionCreateResponse(BaseModel):
    """Response when creating a new session - includes language_variant."""
    id: str
    name: str
    language_variant: str
    created_at: datetime


class SessionRenameRequest(BaseModel):
    name: str = Field(..., description="New session name (required)")


class SessionEndResponse(BaseModel):
    id: str
    ended_at: datetime


class SessionNameResponse(BaseModel):
    """Shape returned by PATCH /sessions/{id}."""

    id: str
    name: str

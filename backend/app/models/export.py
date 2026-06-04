"""Export bundle models (used by Gate 2 export endpoints)."""

from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel, Field

from .graph import GraphStateResponse
from .session import SessionDetail


class SessionExportBundle(BaseModel):
    """JSON export content: graph + transcript + metadata."""

    session: SessionDetail = Field(..., description="Full session detail including transcript")
    graph: GraphStateResponse = Field(..., description="Full graph snapshot")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional run metadata (version, generated_at, etc.)",
    )

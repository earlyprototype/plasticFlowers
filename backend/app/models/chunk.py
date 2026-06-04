"""Transcript chunk models and responses.

Spec references:
- `_docs/_dev/_MVP/_schema/01_data_model.md`
- `_docs/_dev/_MVP/_api/01_contracts.md` (Submit chunk)
- `_docs/_dev/_MVP/_PRE_IMPLEMENTATION_REPORT.md` (pre-Builder similarity rule)
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from .enums import ChunkStatus


class TranscriptChunk(BaseModel):
    """Chunk stored against a session (Builder input)."""

    id: str = Field(..., description="Chunk identifier")
    text: str = Field(..., description="Transcribed text (may be corrected by Gardener)")
    original_text: Optional[str] = Field(
        default=None,
        description="Original STT output before corrections (audit trail)",
    )
    start_time: float = Field(..., description="Seconds from session start (inclusive)")
    end_time: float = Field(..., description="Seconds from session start (exclusive)")
    session_id: str = Field(..., description="Owning session id")


class ChunkSubmissionRequest(BaseModel):
    text: str = Field(..., description="Transcribed content from Web Speech API")
    start_time: float = Field(..., description="Chunk start timestamp (seconds)")
    end_time: float = Field(..., description="Chunk end timestamp (seconds)")


class ChunkSubmissionResponse(BaseModel):
    chunk_id: str = Field(..., description="Identifier that the backend will process")
    status: ChunkStatus = Field(
        ChunkStatus.QUEUED,
        description="Always 'queued' during Gate 2; Builder processing is asynchronous",
    )


class ChunkProcessedPayload(BaseModel):
    """SSE payload acknowledging processing completion."""

    chunk_id: str = Field(..., description="Identifier of the processed chunk")
    error: Optional[str] = Field(
        default=None, description="Optional error detail if Builder processing failed"
    )

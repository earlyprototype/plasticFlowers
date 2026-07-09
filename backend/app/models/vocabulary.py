"""Session vocabulary and correction tracking models (Phase D)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Optional

from pydantic import BaseModel, Field


class SessionVocabulary(BaseModel):
    """
    Stores learned STT corrections for a session.
    
    Enables instant correction lookup for recurring errors without LLM calls.
    """
    session_id: str = Field(..., description="Session this vocabulary belongs to")
    language_variant: str = Field(
        "en-GB", 
        description="Language variant (en-GB or en-US) for spelling consistency"
    )
    corrections: Dict[str, str] = Field(
        default_factory=dict,
        description="Map of phonetic error -> correct term (e.g., 'see dar' -> 'CeADAR')"
    )
    preferred_spellings: Dict[str, str] = Field(
        default_factory=dict,
        description="Variant normalisation (e.g., 'color' -> 'colour' for en-GB)"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last vocabulary update timestamp"
    )


class TranscriptCorrection(BaseModel):
    """
    Audit trail for an individual correction applied during proofreading.
    
    Enables rollback and analysis of correction quality.
    """
    id: str = Field(..., description="Unique correction identifier")
    session_id: str = Field(..., description="Session identifier")
    original: str = Field(..., description="Original text before correction")
    correction: str = Field(..., description="Corrected text")
    confidence: float = Field(..., ge=0.0, le=1.0, description="LLM confidence in correction")
    applied_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When correction was applied"
    )
    affected_node_ids: list[str] = Field(
        default_factory=list,
        description="Node IDs that were updated with this correction"
    )
    affected_chunk_ids: list[str] = Field(
        default_factory=list,
        description="TranscriptChunk IDs that were updated"
    )
    reason: Optional[str] = Field(
        None,
        max_length=240,
        description="LLM explanation for the correction"
    )


class ProofreadCheckpoint(BaseModel):
    """
    Tracks incremental proofreading progress for a session.
    
    Prevents re-scanning already proofread chunks in subsequent Gardener cycles.
    """
    session_id: str = Field(..., description="Session identifier")
    last_chunk_id: str = Field(..., description="ID of last processed TranscriptChunk")
    last_run: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of last proofread cycle"
    )
    chunks_processed: int = Field(
        0,
        ge=0,
        description="Total chunks proofread in this session"
    )


class SessionContext(BaseModel):
    """
    Persistent context for maintaining understanding across incremental proofreading.
    
    When using checkpoints, Gardener may lose visibility of earlier chunks.
    This context stores session-level understanding to ensure consistent
    corrections and decisions.
    """
    session_id: str = Field(..., description="Session identifier")
    theme_summary: str = Field(
        "",
        max_length=500,
        description="Brief summary of session theme (e.g., 'Enterprise Ireland on EDIH network')"
    )
    key_entities: list[str] = Field(
        default_factory=list,
        description="Important recurring entities in this session"
    )
    speaker_names: list[str] = Field(
        default_factory=list,
        description="Names of speakers for name recognition"
    )
    domain_terms: list[str] = Field(
        default_factory=list,
        description="Technical vocabulary specific to this session"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last context update timestamp"
    )

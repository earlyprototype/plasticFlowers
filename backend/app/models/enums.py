"""Shared enumerations derived from Gate 2 contracts.

Reference specs:
- `_docs/_dev/_MVP/_ALIGNMENT.md` (emergent schema + relationship categories)
- `_docs/_dev/_MVP/_PRE_IMPLEMENTATION_REPORT.md` (relationship id + payload rules)
"""

from __future__ import annotations

from enum import Enum


class NodeStatus(str, Enum):
    """Ghost/solid/legacy lifecycle state (Alignment §Non-Negotiables)."""

    GHOST = "ghost"
    SOLID = "solid"
    LEGACY = "legacy"  # Phase D: Temporal decay - nodes >5min become legacy


class RelationshipCategory(str, Enum):
    """Five allowed categories (DEC-005)."""

    CAUSAL = "CAUSAL"
    STRUCTURAL = "STRUCTURAL"
    COMPARATIVE = "COMPARATIVE"
    TEMPORAL = "TEMPORAL"
    ASSOCIATIVE = "ASSOCIATIVE"


class RelationshipSource(str, Enum):
    """Which agent surfaced or confirmed the relationship (Builder/Gardener split)."""

    BUILDER = "builder"
    GARDENER = "gardener"


class ChunkStatus(str, Enum):
    """Queue status returned by POST /chunks (API contracts §Submit Chunk)."""

    QUEUED = "queued"


class ExportFormat(str, Enum):
    """Export endpoints supported in MVP (DEC-011)."""

    JSON = "json"
    TRANSCRIPT = "transcript"
    VTT = "vtt"
    MARKDOWN = "markdown"

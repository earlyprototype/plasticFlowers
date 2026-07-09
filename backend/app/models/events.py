"""SSE event payload models for `/sessions/{id}/stream`.

Spec references:
- `_docs/_dev/_MVP/_api/01_contracts.md` (Event table)
- `_docs/_dev/_MVP/_PRE_IMPLEMENTATION_REPORT.md` (relationship_removed payload = `{ id }`)
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from .chunk import ChunkProcessedPayload
from .flower import Flower
from .node import Node
from .relationship import Relationship


class NodeRemovedPayload(BaseModel):
    id: str = Field(..., description="Identifier of the node to remove")


class NodeMergedPayload(BaseModel):
    from_id: str = Field(..., description="Duplicate node that will be removed")
    into_id: str = Field(..., description="Canonical node that remains")


class NodeCorrectedPayload(BaseModel):
    """Payload for STT correction events."""
    node_id: str = Field(..., description="ID of the node that was corrected")
    old_label: str = Field(..., description="Original label before correction")
    new_label: str = Field(..., description="Corrected label")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Correction confidence")


class RelationshipRemovedPayload(BaseModel):
    id: str = Field(..., description="Identifier of the relationship to remove")


class FlowerDissolvedPayload(BaseModel):
    id: str = Field(..., description="Identifier of the dissolved Flower")


class GardenerCyclePayload(BaseModel):
    timestamp: datetime = Field(..., description="Completion timestamp of the Gardener run")


class SSEvent(BaseModel):
    type: str


class NodeAddedEvent(SSEvent):
    type: Literal["node_added"] = "node_added"
    payload: Node


class NodeUpdatedEvent(SSEvent):
    type: Literal["node_updated"] = "node_updated"
    payload: Node


class NodeRemovedEvent(SSEvent):
    type: Literal["node_removed"] = "node_removed"
    payload: NodeRemovedPayload


class NodeMergedEvent(SSEvent):
    type: Literal["node_merged"] = "node_merged"
    payload: NodeMergedPayload


class NodeCorrectedEvent(SSEvent):
    """SSE event for STT corrections to node labels."""
    type: Literal["node_corrected"] = "node_corrected"
    payload: NodeCorrectedPayload


class RelationshipAddedEvent(SSEvent):
    type: Literal["relationship_added"] = "relationship_added"
    payload: Relationship


class RelationshipRemovedEvent(SSEvent):
    type: Literal["relationship_removed"] = "relationship_removed"
    payload: RelationshipRemovedPayload


class FlowerCreatedEvent(SSEvent):
    type: Literal["flower_created"] = "flower_created"
    payload: Flower


class FlowerUpdatedEvent(SSEvent):
    type: Literal["flower_updated"] = "flower_updated"
    payload: Flower


class FlowerDissolvedEvent(SSEvent):
    type: Literal["flower_dissolved"] = "flower_dissolved"
    payload: FlowerDissolvedPayload


class ChunkProcessedEvent(SSEvent):
    type: Literal["chunk_processed"] = "chunk_processed"
    payload: ChunkProcessedPayload


class GardenerCycleEvent(SSEvent):
    type: Literal["gardener_cycle"] = "gardener_cycle"
    payload: GardenerCyclePayload


class ReferenceAddedPayload(BaseModel):
    """Payload for reference_added event."""
    node_id: str
    reference_id: str
    summary: str
    provider: str
    url: str | None = None


class ReferenceAddedEvent(SSEvent):
    """Event broadcast when a ReferenceNode is attached to a Node."""
    type: Literal["reference_added"] = "reference_added"
    payload: ReferenceAddedPayload


class ResyncRequiredPayload(BaseModel):
    """Payload for resync_required control events."""
    reason: str = Field(..., description="Why the client must resync (e.g. event_overflow)")


class ResyncRequiredEvent(SSEvent):
    """Control event: the server dropped SSE events for this subscriber, so the
    client must re-fetch the full graph state instead of trusting the stream."""
    type: Literal["resync_required"] = "resync_required"
    payload: ResyncRequiredPayload

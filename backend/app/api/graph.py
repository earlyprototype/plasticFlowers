"""Graph data endpoints.

Spec references:
- `_docs/_dev/_MVP/_api/01_contracts.md` — Graph Data section
- `_docs/_dev/_MVP/_schema/01_data_model.md`
"""

from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Path, Query, status

from ..models import (
    FlowersResponse,
    GraphStateResponse,
    NodesResponse,
    ReferencesResponse,
    RelationshipCategory,
    RelationshipsResponse,
    RelationshipSource,
)
from ..models.enums import NodeStatus
from ..services import (
    fetch_graph_state,
    list_flowers,
    list_nodes,
    list_references,
    list_relationships,
    get_node,
    publish_node_needs_research,
)

router = APIRouter(prefix="/sessions/{session_id}", tags=["graph"])

StatusFilter = Literal["ghost", "solid", "all"]


@router.get("/graph", response_model=GraphStateResponse, summary="Get full graph state")
async def get_full_graph(session_id: str = Path(..., description="Session identifier")) -> GraphStateResponse:
    """GET /sessions/{id}/graph — return nodes, relationships, flowers, bridges."""
    graph_state = await fetch_graph_state(session_id)
    return GraphStateResponse(**graph_state.model_dump(), bridges=[])


@router.get("/nodes", response_model=NodesResponse, summary="Get nodes")
async def get_nodes(
    session_id: str = Path(..., description="Session identifier"),
    status: StatusFilter = Query("all", description="Filter by node status"),
    flower_id: Optional[str] = Query(None, description="Restrict to a given Flower"),
) -> NodesResponse:
    """GET /sessions/{id}/nodes — list nodes (filterable)."""
    node_status: Optional[NodeStatus] = None
    if status != "all":
        try:
            node_status = NodeStatus(status)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status filter")

    nodes = await list_nodes(session_id, status=node_status, flower_id=flower_id)
    return NodesResponse(nodes=nodes)


@router.get(
    "/relationships",
    response_model=RelationshipsResponse,
    summary="Get relationships",
)
async def get_relationships(
    session_id: str = Path(..., description="Session identifier"),
    category: Optional[RelationshipCategory] = Query(None, description="Filter by category"),
    source: Optional[RelationshipSource] = Query(None, description="Filter by agent source"),
) -> RelationshipsResponse:
    """GET /sessions/{id}/relationships — list relationships (filterable)."""
    relationships = await list_relationships(session_id, category=category, source=source)
    return RelationshipsResponse(relationships=relationships)


@router.get("/flowers", response_model=FlowersResponse, summary="Get flowers + bridges")
async def get_flowers(session_id: str = Path(..., description="Session identifier")) -> FlowersResponse:
    """GET /sessions/{id}/flowers — list Flowers and derived bridges."""
    flowers = await list_flowers(session_id)
    return FlowersResponse(flowers=flowers, bridges=[])


@router.get("/references", response_model=ReferencesResponse, summary="Get references")
async def get_references(session_id: str = Path(..., description="Session identifier")) -> ReferencesResponse:
    """GET /sessions/{id}/references — list all references (Librarian UI)."""
    references = await list_references(session_id)
    return ReferencesResponse(references=references)


@router.post("/nodes/{node_id}/research", status_code=status.HTTP_202_ACCEPTED, summary="Trigger manual research")
async def trigger_node_research(
    session_id: str = Path(..., description="Session identifier"),
    node_id: str = Path(..., description="Node identifier"),
) -> dict[str, str]:
    """POST /sessions/{id}/nodes/{node_id}/research — queue research for a node."""
    node = await get_node(session_id, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
        
    await publish_node_needs_research(
        session_id=session_id,
        node_id=node.id,
        label=node.label,
        entity_type=str(node.entity_type),
        research_reason="user_requested",
        priority="high",
    )
    
    return {"status": "queued", "message": f"Research queued for node '{node.label}'"}

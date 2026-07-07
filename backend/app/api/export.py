"""Export endpoints (Gate 6 implementation).

Spec references:
- `_docs/_dev/_MVP/_api/01_contracts.md` — Export section
- DEC-011 — Export formats (JSON, transcript, VTT, Markdown)
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, HTTPException, Path, status
from fastapi.responses import PlainTextResponse
from google import genai
from google.genai import types

from ..models import (
    Flower,
    GraphStateResponse,
    Node,
    Relationship,
    SessionDetail,
    SessionExportBundle,
)
from ..services import (
    fetch_graph_state,
    get_session_record,
    is_fake_llm_enabled,
    list_chunks_for_session,
    list_flowers,
    list_nodes,
    list_relationships,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions/{session_id}/export", tags=["export"])


@router.get(
    "/json",
    response_model=SessionExportBundle,
    summary="Export session as JSON",
)
async def export_json(session_id: str = Path(..., description="Session identifier")) -> SessionExportBundle:
    """GET /sessions/{id}/export/json — full graph + transcript + metadata."""

    session = await get_session_record(session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    # Get chunks and build transcript
    chunks = await list_chunks_for_session(session_id)
    transcript = " ".join(chunk.text for chunk in chunks)

    # Get graph state
    graph_state = await fetch_graph_state(session_id)

    return SessionExportBundle(
        session=SessionDetail(
            id=session.id,
            name=session.name,
            created_at=session.created_at,
            ended_at=session.ended_at,
            transcript=transcript,
        ),
        graph=GraphStateResponse(
            nodes=graph_state.nodes,
            relationships=graph_state.relationships,
            flowers=graph_state.flowers,
            bridges=[],  # Bridges are derived at query time
        ),
        metadata={
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "version": "1.0",
            "chunk_count": len(chunks),
        },
    )


@router.get(
    "/transcript",
    response_class=PlainTextResponse,
    summary="Export transcript (plain text)",
)
async def export_transcript(session_id: str = Path(..., description="Session identifier")) -> PlainTextResponse:
    """GET /sessions/{id}/export/transcript — plain text transcript."""

    session = await get_session_record(session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    chunks = await list_chunks_for_session(session_id)
    transcript = "\n".join(chunk.text for chunk in chunks)

    return PlainTextResponse(
        content=transcript,
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{session_id}_transcript.txt"'},
    )


@router.get(
    "/vtt",
    response_class=PlainTextResponse,
    summary="Export transcript (WebVTT)",
)
async def export_vtt(session_id: str = Path(..., description="Session identifier")) -> PlainTextResponse:
    """GET /sessions/{id}/export/vtt — WebVTT transcript file."""

    session = await get_session_record(session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    chunks = await list_chunks_for_session(session_id)

    vtt_lines = ["WEBVTT", ""]
    for chunk in chunks:
        start = _format_vtt_time(chunk.start_time)
        end = _format_vtt_time(chunk.end_time)
        vtt_lines.append(f"{start} --> {end}")
        vtt_lines.append(chunk.text)
        vtt_lines.append("")

    return PlainTextResponse(
        content="\n".join(vtt_lines),
        media_type="text/vtt",
        headers={"Content-Disposition": f'attachment; filename="{session_id}_transcript.vtt"'},
    )


def _format_vtt_time(seconds: float) -> str:
    """Convert seconds to VTT timestamp format (HH:MM:SS.mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


@router.get(
    "/markdown",
    response_class=PlainTextResponse,
    summary="Export Markdown summary",
)
async def export_markdown(session_id: str = Path(..., description="Session identifier")) -> PlainTextResponse:
    """GET /sessions/{id}/export/markdown — LLM-generated or fake summary."""

    session = await get_session_record(session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    # Generate summary: fake mode for testing, LLM-powered for production
    if is_fake_llm_enabled():
        markdown = await _generate_fake_summary(session_id, session.name)
    else:
        # Fetch full graph state for LLM summarisation
        graph_state = await fetch_graph_state(session_id)
        markdown = await _generate_llm_summary(
            session_id,
            session.name,
            graph_state.nodes,
            graph_state.relationships,
            graph_state.flowers,
        )

    return PlainTextResponse(
        content=markdown,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{session_id}_summary.md"'},
    )


async def _generate_fake_summary(session_id: str, session_name: str) -> str:
    """Generate a simple summary without LLM (fake mode fallback)."""

    nodes = await list_nodes(session_id)
    relationships = await list_relationships(session_id)
    flowers = await list_flowers(session_id)
    chunks = await list_chunks_for_session(session_id)

    # Count relationships by category
    category_counts: dict[str, int] = {}
    for rel in relationships:
        cat = rel.category.value if hasattr(rel.category, "value") else str(rel.category)
        category_counts[cat] = category_counts.get(cat, 0) + 1

    # Build markdown
    lines = [
        f"# Session Summary: {session_name}",
        "",
        f"**Session ID:** {session_id}",
        "",
        "---",
        "",
        "## Flowers (Thematic Clusters)",
        "",
        "## Key Concepts",
        "",
        f"- {len(nodes)} nodes extracted",
        f"- {len([n for n in nodes if getattr(n.status, 'value', n.status) == 'solid'])} confirmed (solid)",
        f"- {len([n for n in nodes if getattr(n.status, 'value', n.status) == 'ghost'])} pending (ghost)",
        "",
        "## Relationships",
        "",
        f"- {len(relationships)} total relationships",
    ]

    if flowers:
        for flower in flowers:
            label = getattr(flower, "label", None) or getattr(flower, "theme", None) or "Untitled Flower"
            stem = getattr(flower, "stem_node_id", None) or getattr(flower, "stem_id", None) or "none"
            lines.insert(8, f"- **{label}** (stem: {stem})") # Insert after "Flowers" header
    else:
         lines.insert(8, "- No flowers formed yet")


    for cat, count in sorted(category_counts.items()):
        lines.append(f"  - {cat}: {count}")

    lines.extend([
        "",
        "## Transcript",
        "",
        f"- {len(chunks)} chunks recorded",
    ])

    return "\n".join(lines)


async def _generate_text(prompt: str, model: str, temperature: float = 0.7) -> str:
    """Generate plain text response from Gemini."""
    from ..config import get_settings
    
    settings = get_settings()
    
    # Call synchronous generation in thread pool
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        _generate_text_sync,
        prompt,
        model,
        temperature,
        settings,
    )
    return result


def _generate_text_sync(prompt: str, model: str, temperature: float, settings) -> str:
    """Synchronous text generation."""
    
    api_key = settings.gemini_api_key.get_secret_value()
    if not api_key:
         raise RuntimeError("GEMINI_API_KEY is not configured")

    if settings.vertex_project_id:
        client = genai.Client(
            vertexai=True,
            project=settings.vertex_project_id,
            location=settings.vertex_location,
            api_key=api_key
        )
    else:
        client = genai.Client(api_key=api_key)
    
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=1024,
        ),
    )
    
    return response.text


async def _generate_llm_summary(
    session_id: str,
    session_name: str,
    nodes: List[Node],
    relationships: List[Relationship],
    flowers: List[Flower],
) -> str:
    """Generate an LLM-powered markdown summary of the session graph."""
    
    # Prepare context
    node_count = len(nodes)
    rel_count = len(relationships)
    flower_count = len(flowers)
    
    # Get node type distribution
    type_dist = {}
    for node in nodes:
        type_dist[node.inferred_type] = type_dist.get(node.inferred_type, 0) + 1
    
    # Get top nodes by connectivity
    node_connections = {}
    for rel in relationships:
        node_connections[rel.source_id] = node_connections.get(rel.source_id, 0) + 1
        node_connections[rel.target_id] = node_connections.get(rel.target_id, 0) + 1
    
    top_nodes = sorted(
        nodes, 
        key=lambda n: node_connections.get(n.id, 0), 
        reverse=True
    )[:10]
    
    # Build prompt
    prompt = f"""Generate a concise markdown summary of this knowledge graph session.

Session: "{session_name}"
Statistics:
- {node_count} concepts/entities
- {rel_count} relationships
- {flower_count} thematic clusters

Node Types Distribution:
{chr(10).join(f"- {type_}: {count}" for type_, count in sorted(type_dist.items(), key=lambda x: x[1], reverse=True)[:10])}

Thematic Clusters (Flowers):
{chr(10).join(f"- {flower.label} ({len([n for n in nodes if n.flower_id == flower.id])} concepts)" for flower in flowers) if flowers else "- No thematic clusters formed yet"}

Top Connected Concepts:
{chr(10).join(f"- {node.label} ({node.inferred_type}): {node_connections.get(node.id, 0)} connections" for node in top_nodes[:5])}

Generate a markdown summary with:
1. Overview paragraph (2-3 sentences about the session topic/focus)
2. Key Themes section (bullet points from Flowers)
3. Core Concepts section (most connected/important nodes)
4. Notable Patterns section (insights about relationship types, clustering)

Keep it concise (200-300 words). Use markdown formatting.
"""
    
    try:
        # Use Gemini 3 Flash Preview for cost-effective summarisation
        response = await _generate_text(
            prompt=prompt,
            model="gemini-2.5-flash",
            temperature=0.7,  # Slightly creative for better summaries
        )
        
        return response
        
    except Exception as e:
        logger.warning(f"LLM summary generation failed, falling back to simple summary: {e}")
        return await _generate_fake_summary(session_id, session_name)

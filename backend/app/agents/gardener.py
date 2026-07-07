"""Gardener agent orchestration (Gate 5).

Wraps the Gardener prompt specification, calls Gemini JSON mode, and returns
typed actions for downstream graph mutation. This agent assumes Builder is
optimistic (per DEC-020); deduplication is handled here.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from time import perf_counter
from typing import Annotated, Iterable, List, Literal, Mapping, MutableSequence, Sequence

from pydantic import BaseModel, BeforeValidator, Field, ValidationError, model_validator

from ..config import get_settings
from ..models import Flower, Node, Relationship, RelationshipCategory, RelationshipSource

logger = logging.getLogger(__name__)


def _uppercase_validator(v: str) -> str:
    if isinstance(v, str):
        return v.upper()
    return v


class GardenerAgentError(RuntimeError):
    """Raised when the Gardener agent cannot produce a usable result."""

    def __init__(self, message: str, *, code: str = "unknown"):
        super().__init__(message)
        self.code = code


class NodeAction(BaseModel):
    """Action for a ghost node: confirm, prune, or merge."""
    action: Literal["confirm", "prune", "merge"] = Field(
        ..., 
        description="confirm=promote to solid, prune=remove, merge=combine with another"
    )
    node_id: str = Field(..., min_length=1, description="The node's id field (e.g., 'node_abc123')")
    merge_into: str = Field("", description="Target node ID if action=merge (e.g., 'node_def456'), else empty")
    reason: str = Field("", max_length=240, description="Explanation for action")


class FlowerAction(BaseModel):
    """Action for a flower: create, update, or dissolve."""
    action: Literal["create", "update", "dissolve"] = Field(
        ...,
        description="create=new flower, update=modify members, dissolve=remove flower"
    )
    flower_id: str = Field("", description="Flower ID if updating/dissolving, else empty")
    label: str = Field("", description="Flower label (2-5 words describing the theme)")
    member_ids: List[str] = Field(default_factory=list, description="List of node IDs (e.g., ['node_abc123', 'node_def456'])")
    stem_node_id: str = Field("", description="ID of the central/stem node (must be in member_ids)")
    reason: str = Field("", max_length=240)


class CorrectionAction(BaseModel):
    original: str = Field(..., min_length=2, description="Original STT error text")
    corrected: str = Field(..., min_length=2, description="Corrected text")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in correction")
    reason: str = Field("", max_length=240, description="Why this correction was made")


class NewRelationship(BaseModel):
    source_id: str = Field(..., min_length=1)
    target_id: str = Field(..., min_length=1)
    category: Annotated[RelationshipCategory, BeforeValidator(_uppercase_validator)]
    description: str = Field(..., min_length=2, max_length=80)
    confidence: float = Field(..., ge=0.0, le=1.0)
    reason: str = Field("", max_length=240)


class ResearchAction(BaseModel):
    """Action to trigger Researcher agent for a node.
    
    Gardener flags nodes that would benefit from external enrichment.
    Criteria: first mention of organisation/funding/unfamiliar term with high confidence.
    """
    action: Literal["research"] = Field(
        "research",
        description="Always 'research' - triggers Researcher agent"
    )
    node_id: str = Field(..., min_length=1, description="Node ID to research")
    entity_type: str = Field(
        ..., 
        description="Classified type: organisation, funding, person, concept, etc."
    )
    reason: str = Field("", max_length=240, description="Why research is needed")
    priority: Literal["high", "normal"] = Field(
        "normal",
        description="high=user-facing entity, normal=background enrichment"
    )


class GardenerLLMResponse(BaseModel):
    corrections: List[CorrectionAction] = Field(default_factory=list)
    node_actions: List[NodeAction] = Field(default_factory=list)
    flower_actions: List[FlowerAction] = Field(default_factory=list)
    new_relationships: List[NewRelationship] = Field(default_factory=list)
    research_actions: List[ResearchAction] = Field(default_factory=list)


@dataclass(slots=True)
class GardenerAgentResult:
    corrections: List[CorrectionAction]
    node_actions: List[NodeAction]
    flower_actions: List[FlowerAction]
    new_relationships: List[NewRelationship]
    research_actions: List[ResearchAction]
    raw_response: GardenerLLMResponse
    llm_duration_ms: float


class GardenerAgent:
    """Coordinates a single Gardener cycle."""

    def __init__(self, *, llm_fn=None) -> None:
        self._llm_fn = llm_fn or _default_llm_fn

    async def run(
        self,
        *,
        ghost_nodes: Sequence[Node],
        solid_nodes: Sequence[Node],
        relationships: Sequence[Relationship],
        flowers: Sequence[Flower],
        recent_transcript: str = "",
        language_variant: str = "en-GB",
        session_context: dict | None = None,
    ) -> GardenerAgentResult:
        prompt = _render_prompt(
            ghost_nodes=ghost_nodes,
            solid_nodes=solid_nodes,
            relationships=relationships,
            flowers=flowers,
            recent_transcript=recent_transcript,
            language_variant=language_variant,
            session_context=session_context,
        )
        
        # Diagnostic: log prompt size and structure
        prompt_chars = len(prompt)
        prompt_tokens_est = prompt_chars // 4  # Rough estimate: 1 token ≈ 4 chars
        logger.info(
            "gardener.prompt_stats chars=%d est_tokens=%d ghosts=%d solids=%d rels=%d flowers=%d",
            prompt_chars,
            prompt_tokens_est,
            len(ghost_nodes),
            len(solid_nodes),
            len(relationships),
            len(flowers),
        )
        
        # Log first 500 chars of prompt to verify format
        logger.debug("gardener.prompt_preview: %s...", prompt[:500])
        
        llm_start = perf_counter()
        try:
            payload = await self._llm_fn(prompt, GardenerLLMResponse)
        except Exception as exc:
            # Check if it's an LLM error (lazy import to avoid circular dependency)
            from ..services.llm import LLMError
            if isinstance(exc, LLMError):
                raise GardenerAgentError("Gemini request failed", code="llm_error") from exc
            raise

        try:
            response = GardenerLLMResponse.model_validate(payload)
        except ValidationError as exc:
            logger.error("Gardener validation failed. Payload: %s. Error: %s", payload, exc)
            raise GardenerAgentError(f"Gemini returned invalid payload: {exc}", code="invalid_payload") from exc

        duration_ms = (perf_counter() - llm_start) * 1000
        return GardenerAgentResult(
            corrections=response.corrections,
            node_actions=response.node_actions,
            flower_actions=response.flower_actions,
            new_relationships=response.new_relationships,
            research_actions=response.research_actions,
            raw_response=response,
            llm_duration_ms=duration_ms,
        )


async def _default_llm_fn(prompt: str, schema: type[GardenerLLMResponse]) -> Mapping[str, object]:
    # Lazy import to avoid circular dependency
    from ..services.llm import generate_structured_json
    
    settings = get_settings()
    return await generate_structured_json(
        prompt, schema=schema, model=settings.gemini_model_gardener
    )


LANGUAGE_INSTRUCTIONS = {
    "en-GB": "Use British English spelling throughout (organisation, analyse, colour, programme, etc.)",
    "en-US": "Use American English spelling throughout (organization, analyze, color, program, etc.)",
}


def _render_prompt(
    *,
    ghost_nodes: Sequence[Node],
    solid_nodes: Sequence[Node],
    relationships: Sequence[Relationship],
    flowers: Sequence[Flower],
    language_variant: str = "en-GB",
    recent_transcript: str,
    session_context: dict | None = None,
) -> str:
    # Language instruction for consistent spelling
    lang_instruction = LANGUAGE_INSTRUCTIONS.get(language_variant, LANGUAGE_INSTRUCTIONS["en-GB"])
    
    sections: MutableSequence[str] = [
        "You are a knowledge graph curator. Your task is to review, refine, and organise a growing knowledge graph extracted from a live talk.",
        f"\n## LANGUAGE\n{lang_instruction}",
    ]
    
    # Include session context if available (helps with incremental proofreading)
    if session_context:
        context_lines = ["## SESSION CONTEXT (for consistent understanding)"]
        if session_context.get("theme_summary"):
            context_lines.append(f"Theme: {session_context['theme_summary']}")
        if session_context.get("key_entities"):
            context_lines.append(f"Key entities: {', '.join(session_context['key_entities'])}")
        if session_context.get("speaker_names"):
            context_lines.append(f"Speakers: {', '.join(session_context['speaker_names'])}")
        if session_context.get("domain_terms"):
            context_lines.append(f"Domain terms: {', '.join(session_context['domain_terms'])}")
        if len(context_lines) > 1:  # More than just the header
            sections.append("\n".join(context_lines))
    
    sections.append("## GHOST NODES (Pending Review)")
    sections.append(_format_nodes(ghost_nodes))
    sections.append("## SOLID NODES (Confirmed)")
    sections.append(_format_nodes(solid_nodes))
    sections.append("## RELATIONSHIPS")
    sections.append(_format_relationships(relationships))
    sections.append("## CURRENT FLOWERS")
    sections.append(_format_flowers(flowers, solid_nodes))
    sections.append("## RECENT TRANSCRIPT")
    sections.append(recent_transcript.strip() or "(none)")
    sections.append("## INSTRUCTIONS")
    sections.append(_INSTRUCTION_BLOCK)
    sections.append("## OUTPUT")
    return "\n".join(sections).strip()


def _format_nodes(nodes: Iterable[Node]) -> str:
    lines: list[str] = []
    for node in nodes:
        lines.append(
            f"- id={node.id} label=\"{node.label}\" type=\"{node.inferred_type}\" "
            f"status={node.status.value} confidence={node.confidence:.2f} mentions={node.mentions} "
            f"flower_id={node.flower_id or 'none'}"
        )
    return "\n".join(lines) if lines else "(none)"


def _format_relationships(relationships: Iterable[Relationship]) -> str:
    lines: list[str] = []
    for rel in relationships:
        lines.append(
            f"- {rel.source_id} -> {rel.target_id} [{rel.category.value}] "
            f"\"{rel.description}\" (conf={rel.confidence:.2f}) id={rel.id}"
        )
    return "\n".join(lines) if lines else "(none)"


def _format_flowers(flowers: Iterable[Flower], nodes: Sequence[Node]) -> str:
    members_by_flower = {}
    for node in nodes:
        if node.flower_id:
            members_by_flower.setdefault(node.flower_id, []).append(node.id)
    lines: list[str] = []
    for flower in flowers:
        member_ids = members_by_flower.get(flower.id, [])
        lines.append(
            f"- id={flower.id} label=\"{flower.label}\" stem={flower.stem_node_id} "
            f"members={member_ids or '[]'} edge_count={flower.edge_count}"
        )
    return "\n".join(lines) if lines else "(none)"


_INSTRUCTION_BLOCK = """Follow the Gardener rules (Phase D includes proofreading):

1) PROOFREAD (STT ERROR CORRECTION)
- Identify speech-to-text errors in node labels and recent transcript
- Focus on: phonetic spellings of proper nouns, technical terms, acronyms, organisation names
- Examples: "enter price ireland" -> "Enterprise Ireland", "see dar" -> "CeADAR"
- Only correct clear errors (confidence > 0.8)
- Use session vocabulary to avoid re-correcting known terms

2) REVIEW GHOST NODES
- For each GHOST node, decide: confirm, prune, or merge
- confirm: node is valid and distinct (promote to solid)
- prune: node is low-value/uncertain (remove it)
- merge: node duplicates an existing solid node (TRUE duplicates only: synonyms, acronyms, spelling)
- DO NOT MERGE hierarchies or related-but-distinct concepts
- IMPORTANT: Use the node's "id" field (e.g., "node_abc123"), NOT the label

3) FORM OR UPDATE FLOWERS
- Flower requires 3+ SOLID nodes AND 2+ relationships between them
- Look at the RELATIONSHIPS section to find connected node clusters
- Provide: label (2-5 words), member_ids (list of node IDs), stem_node_id (most central node ID)
- IMPORTANT: member_ids and stem_node_id must be node IDs (e.g., "node_abc123"), NOT labels
- Dissolve Flowers that lose coherence (<2 members or weak theme)

4) DISCOVER CROSS-CHUNK RELATIONSHIPS
- Only high-confidence relationships between existing nodes
- Use node IDs for source_id and target_id
- Categories: CAUSAL, STRUCTURAL, COMPARATIVE, TEMPORAL, ASSOCIATIVE

5) FLAG FOR RESEARCH (External Enrichment)
- Identify nodes that would benefit from external research
- Criteria: FIRST MENTION of an entity type that users may not know
- Target types: organisation, funding, person, event, tool, dataset, standard, location, podcast, website, repo, paper, concept
- Only flag nodes with HIGH CONFIDENCE (>0.8) - research is based on certainty, not uncertainty
- Provide: node_id, entity_type, reason for research
- Priority: "high" for user-facing concepts, "normal" for background enrichment

6) OUTPUT
- Return strict JSON matching the schema
- All node references must use the node's "id" field, not the label
- If no actions needed, return empty arrays
"""


__all__ = [
    "CorrectionAction",
    "GardenerAgent",
    "GardenerAgentError",
    "GardenerAgentResult",
    "GardenerLLMResponse",
    "NodeAction",
    "FlowerAction",
    "NewRelationship",
    "ResearchAction",
]


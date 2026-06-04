"""Builder agent orchestration (Gate 4).

This module implements Step 1.2 of the Gate 4 plan by wrapping the Builder
prompt (`_docs/_dev/_MVP/_prompts/01_builder.md`), calling the Gemini JSON
client, and translating the output into canonical `Node` and `Relationship`
models ready for persistence and SSE broadcasting.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from time import perf_counter
from typing import Awaitable, Callable, Dict, List, Mapping, MutableSequence, Sequence
from uuid import uuid4

from pydantic import BaseModel, Field, ValidationError

from ..config import get_settings
from ..models import Node, NodeStatus, Relationship, RelationshipCategory, RelationshipSource

logger = logging.getLogger(__name__)

PromptFn = Callable[[str, type["BuilderLLMResponse"]], Awaitable[Mapping[str, object]]]
ClockFn = Callable[[], datetime]
IdFn = Callable[[], str]


class BuilderAgentError(RuntimeError):
    """Raised when the Builder agent cannot produce a usable result."""

    def __init__(self, message: str, *, code: str = "unknown"):
        super().__init__(message)
        self.code = code


class BuilderLLMNode(BaseModel):
    """Schema passed to Gemini for node extraction."""

    label: str = Field(..., min_length=1, max_length=120)
    inferred_type: str = Field(..., min_length=1, max_length=120)
    confidence: float = Field(..., ge=0.0, le=1.0)


class BuilderLLMRelationship(BaseModel):
    """Schema passed to Gemini for relationship extraction."""

    source: str = Field(..., min_length=1, max_length=120)
    target: str = Field(..., min_length=1, max_length=120)
    category: str = Field(..., min_length=3, max_length=32)
    description: str = Field(default="relates to", min_length=2, max_length=80)
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    evidence: str = Field(default="", max_length=512)


class BuilderLLMResponse(BaseModel):
    """Structured JSON envelope requested from Gemini."""

    nodes: List[BuilderLLMNode] = Field(default_factory=list)
    relationships: List[BuilderLLMRelationship] = Field(default_factory=list)


@dataclass(slots=True)
class UnresolvedRelationship:
    """Relationship with label references instead of node IDs.
    
    Used between agent extraction and service-layer ID resolution.
    After similarity checks, the service maps labels to canonical node IDs.
    """
    source_label: str
    target_label: str
    category: RelationshipCategory
    description: str
    confidence: float
    evidence: str
    created_at: datetime


@dataclass(slots=True)
class BuilderAgentResult:
    """Success payload returned by :class:`BuilderAgent`."""

    nodes: List[Node]
    relationships: List[UnresolvedRelationship]
    raw_response: BuilderLLMResponse
    llm_duration_ms: float


class BuilderAgent:
    """High-level coordinator for the Builder agent."""

    def __init__(
        self,
        *,
        llm_fn: PromptFn | None = None,
        clock: ClockFn | None = None,
        id_factory: IdFn | None = None,
    ) -> None:
        self._llm_fn = llm_fn or _default_llm_fn
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._id_factory = id_factory or (lambda: uuid4().hex)

    async def build(
        self,
        *,
        chunk_text: str,
        chunk_timestamp: float,
        existing_nodes: Sequence[Node] = (),
        existing_relationships: Sequence[Relationship] = (),
    ) -> BuilderAgentResult:
        """Run the Builder prompt for the supplied chunk."""

        text = chunk_text.strip()
        if not text:
            raise BuilderAgentError("Chunk text must not be empty")

        prompt = _render_prompt(text, existing_nodes, existing_relationships)
        llm_start = perf_counter()
        try:
            payload = await self._llm_fn(prompt, BuilderLLMResponse)
        except Exception as exc:
            # Check if it's an LLM error (lazy import to avoid circular dependency)
            from ..services.llm import LLMError
            if isinstance(exc, LLMError):
                raise BuilderAgentError("Gemini request failed", code="llm_error") from exc
            raise

        try:
            response = BuilderLLMResponse.model_validate(payload)
        except ValidationError as exc:
            raise BuilderAgentError("Gemini returned invalid payload", code="invalid_payload") from exc

        nodes, relationships = self._translate(response, existing_nodes, chunk_timestamp)
        llm_duration_ms = (perf_counter() - llm_start) * 1000
        return BuilderAgentResult(
            nodes=nodes,
            relationships=relationships,
            raw_response=response,
            llm_duration_ms=llm_duration_ms,
        )

    def _translate(
        self,
        response: BuilderLLMResponse,
        existing_nodes: Sequence[Node],
        chunk_timestamp: float,
    ) -> tuple[List[Node], List[UnresolvedRelationship]]:
        """Translate LLM response to nodes and unresolved relationships.
        
        Nodes are created with temporary IDs. Relationships store labels,
        not IDs, because similarity checks may change which node ID is canonical.
        """
        now = self._clock()
        created_nodes: List[Node] = []
        created_label_keys: set[str] = set()

        for llm_node in response.nodes:
            label_key = _normalise_label(llm_node.label)
            inferred_type = llm_node.inferred_type.strip()
            if not label_key or not inferred_type:
                continue
            if label_key in created_label_keys:
                continue

            node_id = f"node_{self._id_factory()}"
            node = Node(
                id=node_id,
                label=llm_node.label.strip(),
                confidence=_clamp(llm_node.confidence),
                mentions=1,
                timestamps=[float(chunk_timestamp)],
                inferred_type=inferred_type,
                flower_id=None,
                embedding=None,
                created_at=now,
                status=NodeStatus.GHOST,
            )
            created_nodes.append(node)
            created_label_keys.add(label_key)

        # Create unresolved relationships (labels only, no IDs yet)
        relationships: List[UnresolvedRelationship] = []
        seen_relationships: set[tuple[str, str, str]] = set()

        for llm_rel in response.relationships:
            source_label = _normalise_label(llm_rel.source)
            target_label = _normalise_label(llm_rel.target)
            description = llm_rel.description.strip()
            evidence = llm_rel.evidence.strip()

            if (
                not source_label
                or not target_label
                or source_label == target_label
                or not description
                or not evidence
            ):
                continue

            dedup_key = (source_label, target_label, description.lower())
            if dedup_key in seen_relationships:
                continue
            seen_relationships.add(dedup_key)

            relationship = UnresolvedRelationship(
                source_label=source_label,
                target_label=target_label,
                category=_normalise_category(llm_rel.category),
                description=description,
                confidence=_clamp(llm_rel.confidence),
                evidence=evidence,
                created_at=now,
            )
            relationships.append(relationship)

        return created_nodes, relationships


async def _default_llm_fn(
    prompt: str, schema: type[BuilderLLMResponse]
) -> Mapping[str, object]:
    # Lazy import to avoid circular dependency
    from ..services.llm import generate_structured_json
    
    settings = get_settings()
    return await generate_structured_json(
        prompt, schema=schema, model=settings.gemini_model_builder
    )


def _render_prompt(
    chunk_text: str, 
    nodes: Sequence[Node], 
    relationships: Sequence[Relationship] = (),
) -> str:
    sections: MutableSequence[str] = [PROMPT_PREAMBLE]
    existing_nodes = _format_existing_nodes(nodes)
    if existing_nodes:
        sections.append("## EXISTING NODES")
        sections.append(existing_nodes)
    existing_rels = _format_existing_relationships(relationships, limit=20)
    if existing_rels:
        sections.append("## EXISTING RELATIONSHIPS (for context)")
        sections.append(existing_rels)
    sections.append("## TRANSCRIPT CHUNK")
    sections.append(chunk_text.strip())
    sections.append(INSTRUCTION_BLOCK)
    sections.append("## OUTPUT")
    return "\n".join(sections).strip()


def _format_existing_nodes(nodes: Sequence[Node]) -> str:
    grouped: Dict[str, List[str]] = defaultdict(list)
    for node in nodes:
        label = node.label.strip().lower()
        inferred_type = node.inferred_type.strip().lower() if node.inferred_type else "unknown"
        if not label:
            continue
        grouped[inferred_type].append(label)

    if not grouped:
        return ""

    lines: List[str] = []
    for inferred_type in sorted(grouped.keys()):
        unique_labels = list(dict.fromkeys(grouped[inferred_type]))
        lines.append(f"- {inferred_type}: {', '.join(unique_labels)}")
    return "\n".join(lines)


def _format_existing_relationships(
    relationships: Sequence[Relationship],
    limit: int = 20,
) -> str:
    """Format existing relationships for Builder prompt context.
    
    Shows recent relationships to help Builder understand node connections
    and avoid creating redundant relationships.
    """
    if not relationships:
        return ""
    
    # Take most recent relationships (by created_at) up to limit
    sorted_rels = sorted(relationships, key=lambda r: r.created_at, reverse=True)[:limit]
    
    lines: List[str] = []
    for rel in sorted_rels:
        lines.append(
            f"- {rel.source_id} -> {rel.target_id}: \"{rel.description}\" [{rel.category.value}]"
        )
    
    return "\n".join(lines)


def _normalise_label(label: str) -> str:
    return " ".join(label.strip().split()).lower()


def _normalise_category(category: str) -> RelationshipCategory:
    try:
        return RelationshipCategory[category.strip().upper()]
    except KeyError:
        logger.debug("Unknown relationship category '%s'; defaulting to ASSOCIATIVE", category)
        return RelationshipCategory.ASSOCIATIVE


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


PROMPT_PREAMBLE = """You are a knowledge extraction agent. Your task is to identify concepts and relationships from a transcript chunk. The input is a raw speech stream segment. It may start or end mid-sentence."""

INSTRUCTION_BLOCK = """## INSTRUCTIONS

1. EXTRACT NODES
   - Identify noteworthy concepts, people, frameworks, methods, events, organisations, or terms
   - Use lowercase labels (1-4 words)
   - Assign an inferred_type using your best judgment (this is EMERGENT — use whatever category fits, not a predefined list)
   - If a concept matches an existing node, DO NOT create a duplicate
   - Assign a confidence score (0.0-1.0) based on clarity of mention
   - Extract entities even if the context is incomplete (e.g., if a sentence is cut off, capture what is visible)

2. EXTRACT RELATIONSHIPS
   - Only create relationships between nodes mentioned in THIS chunk
   - Assign one of CAUSAL, STRUCTURAL, COMPARATIVE, TEMPORAL, ASSOCIATIVE
   - Use a concise description (1-3 words): verb or verb phrase like "enables", "builds on", "contrasts with", "improves"
   - Store the exact transcript quote separately in the evidence field (not the description)
   - Assign confidence based on how explicit the relationship is

3. OUTPUT FORMAT
   Return valid JSON only. No commentary."""


__all__ = [
    "BuilderAgent",
    "BuilderAgentError",
    "BuilderAgentResult",
    "BuilderLLMResponse",
    "UnresolvedRelationship",
]

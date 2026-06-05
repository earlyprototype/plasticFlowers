"""Researcher Agent for external enrichment of knowledge graph entities.

This agent performs web search to enrich nodes with external information.
Primary: Tavily MCP (remote SSE)
Fallback: Gemini with Google Search grounding

Spec: _docs/ARCHITECTURE_ADVISORY.md Section 3.3
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

from ..config import get_settings
from ..models.reference import (
    EntityType,
    ReferenceNode,
    ReferenceSource,
    ReferenceSourceType,
    SearchProvider,
    ENABLED_ENTITY_TYPES,
)
from google.genai import types as genai_types

# Imported lazily inside methods to avoid an agents<->services circular import
# (matches the pattern in builder.py / gardener.py). Type-only import here:
if TYPE_CHECKING:
    from ..services.tavily_mcp import TavilySearchResponse

logger = logging.getLogger(__name__)


class ResearcherAgentError(RuntimeError):
    """Raised when research fails."""
    
    def __init__(self, message: str, *, code: str = "research_error"):
        super().__init__(message)
        self.code = code


@dataclass(slots=True)
class ResearcherAgentResult:
    """Result of a research operation."""
    reference: ReferenceNode
    provider_used: SearchProvider
    search_duration_ms: float


class ResearcherAgent:
    """Performs external research to enrich knowledge graph nodes.
    
    Two modes:
    - Automatic: Triggered by Gardener via Redis stream
    - On-demand: User clicks node in UI, calls API endpoint
    """
    
    def __init__(self) -> None:
        self._settings = get_settings()
    
    async def research(
        self,
        *,
        session_id: str,
        node_id: str,
        node_label: str,
        entity_type: str,
        context: str = "",
    ) -> ResearcherAgentResult:
        """Research a node and create a ReferenceNode.
        
        Args:
            session_id: Session the node belongs to
            node_id: ID of the node to enrich
            node_label: Label/name of the entity to research
            entity_type: Type classification (organisation, funding, etc.)
            context: Additional context from transcript (optional)
            
        Returns:
            ResearcherAgentResult with the created ReferenceNode
        """
        from time import perf_counter
        from ..services.tavily_mcp import TavilyMCPError

        t0 = perf_counter()
        logger.info(
            "researcher.start session=%s node=%s label=%s type=%s",
            session_id, node_id, node_label, entity_type
        )
        
        # Build search query with context
        search_query = self._build_search_query(node_label, entity_type, context)
        
        # Try Tavily first, then Gemini fallback
        provider_used: SearchProvider
        reference: Optional[ReferenceNode] = None
        
        try:
            reference = await self._research_with_tavily(
                session_id, node_id, node_label, entity_type, search_query
            )
            provider_used = SearchProvider.TAVILY
        except TavilyMCPError as exc:
            logger.warning("Tavily MCP failed, falling back to Gemini: %s", exc)
            reference = await self._research_with_gemini(
                session_id, node_id, node_label, entity_type, search_query
            )
            provider_used = SearchProvider.GEMINI
        
        duration_ms = (perf_counter() - t0) * 1000
        logger.info(
            "researcher.complete session=%s node=%s provider=%s duration_ms=%.0f",
            session_id, node_id, provider_used.value, duration_ms
        )
        
        return ResearcherAgentResult(
            reference=reference,
            provider_used=provider_used,
            search_duration_ms=duration_ms,
        )
    
    def _build_search_query(
        self, label: str, entity_type: str, context: str
    ) -> str:
        """Build an effective search query based on entity type."""
        
        # Type-specific query patterns
        type_hints = {
            "organisation": f"{label} official website about",
            "funding": f"{label} funding scheme grants program",
            "person": f"{label} researcher scientist biography",
            "event": f"{label} conference event",
            "tool": f"{label} software tool documentation",
            "repo": f"{label} github repository",
            "paper": f"{label} research paper abstract",
            "podcast": f"{label} podcast show",
            "website": f"{label} website",
        }
        
        base_query = type_hints.get(entity_type, label)
        
        # Add context if provided (first 100 chars)
        if context:
            context_snippet = context[:100].strip()
            return f"{base_query} {context_snippet}"
        
        return base_query
    
    async def _research_with_tavily(
        self,
        session_id: str,
        node_id: str,
        label: str,
        entity_type: str,
        query: str,
    ) -> ReferenceNode:
        """Perform research using Tavily MCP."""
        from ..services.tavily_mcp import tavily_search

        response = await tavily_search(
            query,
            max_results=5,
            search_depth="basic",
            include_answer=True,
        )
        
        return self._create_reference_from_tavily(
            session_id, node_id, label, entity_type, response
        )
    
    async def _research_with_gemini(
        self,
        session_id: str,
        node_id: str,
        label: str,
        entity_type: str,
        query: str,
    ) -> ReferenceNode:
        """Fallback: Use Gemini with Google Search grounding."""
        from ..services.llm import get_gemini_client

        
        # Use Gardener model for fallback research as it's likely a Pro model capable of search
        model = self._settings.gemini_model_gardener
        client = get_gemini_client()
        
        prompt = (
            f"Research the entity '{label}' (Type: {entity_type}). "
            f"Query: {query}\n\n"
            "Provide a concise summary of the entity based on reliable web sources. "
            "Focus on: definition, key contributions, official status, and relevance."
        )
        
        logger.info("researcher.gemini_fallback query=%s model=%s", query, model)
        
        try:
            # Enable Google Search grounding
            # Note: This requires the model to support tools (Pro/Flash-8b generally do)
            response = await client.aio.models.generate_content(
                model=model,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    tools=[genai_types.Tool(
                        google_search_retrieval=genai_types.GoogleSearchRetrieval(
                            dynamic_retrieval_config=genai_types.DynamicRetrievalConfig(
                                mode=genai_types.DynamicRetrievalConfigMode.DYNAMIC_RETRIEVAL_CONFIG_MODE_UNSPECIFIED,
                                dynamic_threshold=0.7,
                            )
                        )
                    )],
                    temperature=0.2, 
                )
            )
            
            if not response.text:
                raise ResearcherAgentError("Gemini returned empty response")
                
            canonical_summary = response.text.strip()
            
            # Extract sources from grounding metadata
            sources = []
            if response.candidates and response.candidates[0].grounding_metadata:
                metadata = response.candidates[0].grounding_metadata
                if metadata.grounding_chunks:
                    for chunk in metadata.grounding_chunks:
                        if chunk.web:
                            sources.append(ReferenceSource(
                                title=chunk.web.title or "Google Search Result",
                                url=chunk.web.uri,
                                snippet="", # Grounding metadata doesn't always provide snippet text clearly mapped
                                source_type=self._classify_source_type(chunk.web.uri)
                            ))
                            
            # Deduplicate sources by URL
            unique_sources = {}
            for s in sources:
                if s.url not in unique_sources:
                    unique_sources[s.url] = s
            sources = list(unique_sources.values())[:5]
            
            return ReferenceNode(
                id=f"ref_{uuid.uuid4().hex[:12]}",
                node_id=node_id,
                session_id=session_id,
                entity_type=EntityType(entity_type) if entity_type in [e.value for e in EntityType] else EntityType.CONCEPT,
                canonical_summary=canonical_summary,
                sources=sources,
                confidence=0.85 if sources else 0.5, # Slightly lower confidence than raw Tavily
                ambiguity_notes="Generated via Gemini Fallback",
                needs_user_confirmation=False,
                search_provider=SearchProvider.GEMINI,
                fetched_at=datetime.now(timezone.utc),
            )
            
        except Exception as exc:
            logger.error("Gemini fallback failed: %s", exc)
            # Last resort: Return a basic stub
            return ReferenceNode(
                id=f"ref_{uuid.uuid4().hex[:12]}",
                node_id=node_id,
                session_id=session_id,
                entity_type=EntityType(entity_type) if entity_type in [e.value for e in EntityType] else EntityType.CONCEPT,
                canonical_summary=f"Research failed for '{label}'. Provider errors: Tavily (primary), Gemini (fallback).",
                sources=[],
                confidence=0.0,
                ambiguity_notes=f"All providers failed. Last error: {exc}",
                needs_user_confirmation=True,
                search_provider=SearchProvider.GEMINI,
                fetched_at=datetime.now(timezone.utc),
            )
    
    def _create_reference_from_tavily(
        self,
        session_id: str,
        node_id: str,
        label: str,
        entity_type: str,
        response: TavilySearchResponse,
    ) -> ReferenceNode:
        """Convert Tavily search response to ReferenceNode."""
        
        # Use Tavily's answer as canonical summary if available
        if response.answer:
            canonical_summary = response.answer
        elif response.results:
            # Synthesise from top results
            summaries = [r.content[:200] for r in response.results[:3] if r.content]
            canonical_summary = " ".join(summaries)[:500] if summaries else f"Search results for '{label}'"
        else:
            canonical_summary = f"No results found for '{label}'"
        
        # Convert search results to ReferenceSource objects
        sources = []
        for result in response.results[:5]:
            source_type = self._classify_source_type(result.url)
            sources.append(ReferenceSource(
                title=result.title,
                url=result.url,
                snippet=result.content[:500] if result.content else "",
                source_type=source_type,
            ))
        
        # Calculate confidence based on result quality
        confidence = self._calculate_confidence(response, label)
        
        # Detect ambiguity (multiple very different results)
        ambiguity_notes = self._detect_ambiguity(response, label)
        needs_confirmation = bool(ambiguity_notes)
        
        # Check for vocabulary suggestion (official name differs from label)
        vocabulary_suggestion = self._extract_vocabulary_suggestion(response, label)
        
        # Parse entity type safely
        try:
            parsed_entity_type = EntityType(entity_type)
        except ValueError:
            parsed_entity_type = EntityType.CONCEPT
        
        return ReferenceNode(
            id=f"ref_{uuid.uuid4().hex[:12]}",
            node_id=node_id,
            session_id=session_id,
            entity_type=parsed_entity_type,
            canonical_summary=canonical_summary,
            sources=sources,
            confidence=confidence,
            ambiguity_notes=ambiguity_notes,
            needs_user_confirmation=needs_confirmation,
            user_confirmed=False,
            vocabulary_suggestion=vocabulary_suggestion,
            search_provider=SearchProvider.TAVILY,
            fetched_at=datetime.now(timezone.utc),
        )
    
    def _classify_source_type(self, url: str) -> ReferenceSourceType:
        """Classify source authority based on URL."""
        url_lower = url.lower()
        
        if "wikipedia.org" in url_lower:
            return ReferenceSourceType.WIKIPEDIA
        if "github.com" in url_lower:
            return ReferenceSourceType.REPO
        if any(domain in url_lower for domain in [".edu", ".ac.uk", "arxiv.org", "scholar.google"]):
            return ReferenceSourceType.ACADEMIC
        if any(domain in url_lower for domain in [".gov", ".org", ".ie", ".uk"]):
            return ReferenceSourceType.OFFICIAL
        
        return ReferenceSourceType.OTHER
    
    def _calculate_confidence(self, response: TavilySearchResponse, label: str) -> float:
        """Calculate confidence score based on search results."""
        
        if not response.results:
            return 0.2
        
        # Higher confidence if we have an answer
        base_confidence = 0.7 if response.answer else 0.5
        
        # Boost if label appears in top result title
        top_result = response.results[0]
        if label.lower() in top_result.title.lower():
            base_confidence += 0.15
        
        # Boost for multiple relevant results
        if len(response.results) >= 3:
            base_confidence += 0.1
        
        return min(0.95, base_confidence)
    
    def _detect_ambiguity(self, response: TavilySearchResponse, label: str) -> str:
        """Detect if search results suggest multiple distinct entities."""
        
        if len(response.results) < 2:
            return ""
        
        # Check if top results have very different URLs (different organisations)
        domains = set()
        for result in response.results[:3]:
            # Extract domain
            from urllib.parse import urlparse
            try:
                domain = urlparse(result.url).netloc.replace("www.", "")
                domains.add(domain)
            except Exception:
                pass
        
        # If all top results are from different domains, might be ambiguous
        if len(domains) >= 3:
            titles = [r.title for r in response.results[:3]]
            return f"Multiple entities may match '{label}': {', '.join(titles[:2])}"
        
        return ""
    
    def _extract_vocabulary_suggestion(
        self, response: TavilySearchResponse, label: str
    ) -> dict:
        """Extract potential STT correction from official sources."""
        
        if not response.results:
            return {}
        
        # Check if top result has a different casing/spelling
        top_title = response.results[0].title
        
        # Look for the entity name in the title
        label_lower = label.lower()
        title_lower = top_title.lower()
        
        if label_lower in title_lower:
            # Find the actual casing in the title
            start_idx = title_lower.index(label_lower)
            official_name = top_title[start_idx:start_idx + len(label)]
            
            if official_name != label and official_name.lower() == label.lower():
                # Same word, different casing - suggest correction
                return {label.lower(): official_name}
        
        return {}


__all__ = [
    "ResearcherAgent",
    "ResearcherAgentError",
    "ResearcherAgentResult",
]

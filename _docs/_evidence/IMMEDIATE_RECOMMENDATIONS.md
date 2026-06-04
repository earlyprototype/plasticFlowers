# Immediate Implementation Recommendations

**Date:** 30 December 2025  
**Source:** Architecture Review Session  
**Status:** Ready for Implementation  
**Estimated Total Effort:** 7-9 hours

---

## Overview

This document contains the agreed recommendations from the architecture review session, prioritised for immediate implementation. All items are derived from the comprehensive review in `architecture_review_2025-12-30.md`.

---

## Priority 1: Pre-Creation Similarity Check (HIGH)

### Summary
Implement vector similarity checking in Builder BEFORE creating nodes. This reduces GHOST node count, provides accurate mention counts, and improves UI experience.

### Files to Modify
- `backend/app/services/builder_service.py` - Main implementation
- `backend/app/services/similarity.py` - Already exists, minor updates
- `backend/app/config.py` - Add `similarity_check_enabled` flag

### Implementation Steps

1. **Update `builder_service.py`:**
   ```python
   async def _process(self, session_id, chunk, start):
       # ... existing LLM extraction ...
       
       # NEW: For each extracted node, check similarity before create
       label_to_node: Dict[str, Tuple[Node, bool]] = {}  # label -> (node, is_new)
       
       for extracted_node in agent_result.nodes:
           result = await run_similarity(
               session_id, 
               extracted_node.label, 
               chunk.start_time
           )
           
           if isinstance(result, SimilarityMatchResult):
               # Disambiguation check
               if self._types_compatible(extracted_node.inferred_type, result.node.inferred_type):
                   if extracted_node.confidence >= 0.7:
                       # MATCH: Use existing node
                       label_to_node[extracted_node.label] = (result.node, False)
                       continue
           
           # CREATE: New GHOST node
           extracted_node.embedding = result.embedding
           persisted = await create_node(session_id, extracted_node)
           label_to_node[extracted_node.label] = (persisted, True)
       
       # Create relationships using label mapping
       for rel in agent_result.relationships:
           source_node, _ = label_to_node.get(rel.source, (None, False))
           target_node, _ = label_to_node.get(rel.target, (None, False))
           if source_node and target_node:
               # Use actual node IDs
               rel.source_id = source_node.id
               rel.target_id = target_node.id
               await create_relationship(session_id, rel)
   ```

2. **Add disambiguation helper:**
   ```python
   def _types_compatible(self, type1: str, type2: str) -> bool:
       """Check if inferred types are compatible for merging."""
       if not type1 or not type2:
           return True  # Allow if either is missing
       
       # Exact match
       if type1.lower() == type2.lower():
           return True
       
       # Compatible groups (extend as needed)
       compatible_groups = [
           {"concept", "idea", "term", "topic"},
           {"person", "speaker", "author"},
           {"organisation", "company", "institution"},
           {"technology", "framework", "tool", "library"},
       ]
       
       type1_lower, type2_lower = type1.lower(), type2.lower()
       for group in compatible_groups:
           if type1_lower in group and type2_lower in group:
               return True
       
       return False
   ```

3. **Update SSE broadcasting:**
   ```python
   # For matched nodes (is_new=False):
   await sse_manager.broadcast(session_id, NodeUpdatedEvent(payload=node))
   
   # For new nodes (is_new=True):
   await sse_manager.broadcast(session_id, NodeAddedEvent(payload=node))
   ```

4. **Add config flag:**
   ```python
   # In config.py
   similarity_check_enabled: bool = Field(
       True, 
       description="Enable pre-creation similarity check in Builder"
   )
   ```

### Acceptance Criteria
- [ ] Duplicate entities in same chunk don't create duplicate GHOST nodes
- [ ] Mention counts increment in real-time for matched nodes
- [ ] Relationships point to correct (matched or new) node IDs
- [ ] Type compatibility prevents false matches (e.g., Apple company vs fruit)
- [ ] Fallback to creation if embedding fails

### Effort: Medium (2-3 hours)

---

## Priority 2: Expose original_text in TranscriptChunk (HIGH)

### Summary
The `original_text` field IS stored in Neo4j but not exposed in the model or API. Make it visible.

### Files to Modify
- `backend/app/models/chunk.py` - Add field to model
- `backend/app/services/graph_db.py` - Update `_chunk_from_value()`

### Implementation Steps

1. **Update model (`chunk.py`):**
   ```python
   class TranscriptChunk(BaseModel):
       id: str
       text: str
       original_text: Optional[str] = Field(
           None, 
           description="Original STT output before corrections (audit trail)"
       )
       start_time: float
       end_time: float
       session_id: str
   ```

2. **Update retrieval (`graph_db.py`):**
   ```python
   def _chunk_from_value(value: Neo4jNode) -> TranscriptChunk:
       props = dict(value)
       # Include original_text if present
       return TranscriptChunk.model_validate(props)
   ```

### Acceptance Criteria
- [ ] `original_text` visible in chunk retrieval
- [ ] Export endpoints include `original_text`
- [ ] Existing chunks without `original_text` work (field is optional)

### Effort: Small (30 minutes)

---

## Priority 3: Integrate ProofreadCheckpoint (HIGH)

### Summary
The checkpoint infrastructure exists but is not used. Integrate it to enable incremental proofreading.

### Files to Modify
- `backend/app/services/scheduler.py` - Add checkpoint usage
- `backend/app/services/graph_db.py` - Add `get_chunks_after()` helper

### Implementation Steps

1. **Add helper function (`graph_db.py`):**
   ```python
   async def get_chunks_after(
       session_id: str, 
       after_chunk_id: str, 
       limit: int = 10
   ) -> List[TranscriptChunk]:
       """Get chunks created after the given chunk ID."""
       driver = await get_driver()
       query = """
       MATCH (ref:TranscriptChunk {id: $after_chunk_id, session_id: $session_id})
       MATCH (c:TranscriptChunk {session_id: $session_id})
       WHERE c.start_time > ref.start_time
       RETURN c AS chunk
       ORDER BY c.start_time
       LIMIT $limit
       """
       # ... execute and return
   ```

2. **Update Gardener (`scheduler.py`):**
   ```python
   async def _run_gardener(self, session_id: str) -> None:
       # Get checkpoint
       checkpoint = await get_proofread_checkpoint(session_id)
       
       if checkpoint:
           chunks_to_proofread = await get_chunks_after(
               session_id, checkpoint, limit=10
           )
       else:
           # First run - get recent chunks
           chunks_to_proofread = await list_chunks_for_session(session_id)[-10:]
       
       # ... existing Gardener logic ...
       
       # After successful run, update checkpoint
       if chunks_to_proofread:
           await update_proofread_checkpoint(
               session_id, 
               chunks_to_proofread[-1].id
           )
   ```

### Acceptance Criteria
- [ ] Gardener processes only new chunks since last checkpoint
- [ ] Checkpoint persists across server restarts
- [ ] First Gardener cycle processes initial chunks
- [ ] Subsequent cycles skip already-proofread chunks

### Effort: Medium (1-2 hours)

---

## Priority 4: Add Session Context Persistence (HIGH)

### Summary
Store session theme and key entities to maintain context during incremental proofreading.

### Files to Modify
- `backend/app/models/vocabulary.py` - Add SessionContext model
- `backend/app/services/graph_db.py` - Add CRUD functions
- `backend/app/services/scheduler.py` - Use context in Gardener prompt

### Implementation Steps

1. **Add model (`vocabulary.py`):**
   ```python
   class SessionContext(BaseModel):
       session_id: str
       theme_summary: str = Field(
           "", 
           description="Brief description of session topic"
       )
       key_entities: list[str] = Field(
           default_factory=list,
           description="Important recurring entities"
       )
       speaker_names: list[str] = Field(
           default_factory=list,
           description="Identified speaker names"
       )
       domain_terms: list[str] = Field(
           default_factory=list,
           description="Domain-specific vocabulary"
       )
       updated_at: datetime = Field(default_factory=datetime.now)
   ```

2. **Add persistence (`graph_db.py`):**
   ```python
   async def get_session_context(session_id: str) -> Optional[SessionContext]:
       # Query SessionContext node
       
   async def update_session_context(session_id: str, context: SessionContext) -> None:
       # MERGE SessionContext node
   ```

3. **Update Gardener prompt:**
   ```python
   # In scheduler.py
   context = await get_session_context(session_id)
   if context:
       prompt_sections.append(f"""
       ## SESSION CONTEXT
       Theme: {context.theme_summary}
       Key Entities: {', '.join(context.key_entities)}
       Speakers: {', '.join(context.speaker_names)}
       """)
   ```

4. **Gardener extracts/updates context:**
   - During first few cycles, Gardener identifies theme and key entities
   - LLM returns context suggestions in response
   - Context persisted for subsequent cycles

### Acceptance Criteria
- [ ] Session context persisted in Neo4j
- [ ] Gardener prompt includes context when available
- [ ] Context updated as session progresses
- [ ] Incremental proofreading maintains consistent understanding

### Effort: Medium (1.5-2 hours)

---

## Priority 5: Configuration Updates (MEDIUM)

### Summary
Update configuration for production readiness and debugging capability.

### Files to Modify
- `backend/app/config.py`
- `backend/app/services/builder_service.py` - Check builder_enabled
- `backend/app/services/scheduler.py` - Check gardener_enabled

### Implementation Steps

1. **Reduce timeout:**
   ```python
   gemini_request_timeout: float = Field(
       90.0,  # Changed from 180.0
       ge=1.0,
       description="Seconds before a Gemini request is cancelled.",
   )
   ```

2. **Add agent enable flags:**
   ```python
   builder_enabled: bool = Field(
       True, 
       description="Enable Builder agent processing"
   )
   gardener_enabled: bool = Field(
       True, 
       description="Enable Gardener scheduling"
   )
   researcher_enabled: bool = Field(
       True, 
       description="Enable Researcher agent (Phase 3)"
   )
   librarian_enabled: bool = Field(
       True, 
       description="Enable Librarian Q&A (Phase E)"
   )
   similarity_check_enabled: bool = Field(
       True,
       description="Enable pre-creation similarity check in Builder"
   )
   ```

3. **Update agent startup to check flags:**
   ```python
   # In scheduler.py
   async def start(self) -> None:
       settings = get_settings()
       if not settings.gardener_enabled:
           logger.info("Gardener disabled via config")
           return
       # ... existing start logic
   ```

### Acceptance Criteria
- [ ] Timeout reduced to 90s
- [ ] Agent enable flags configurable via environment
- [ ] Agents check their flag before processing

### Effort: Small (30 minutes)

---

## Priority 5b: Gemini Config Helper Function (MEDIUM)

### Summary
Create a shared helper function that enforces Gemini 2.5 configuration patterns (thinking mode disabled, proper schema setup). This prevents future agents from accidentally omitting critical config.

### Files to Modify
- `backend/app/services/llm_utils.py` (new file)
- `backend/app/agents/builder.py` - Use helper
- `backend/app/agents/gardener.py` - Use helper

### Implementation Steps

1. **Create helper (`llm_utils.py`):**
   ```python
   from google.genai import types
   
   def create_gemini_config(
       response_schema: type,
       thinking_budget: int = 0,
   ) -> types.GenerateContentConfig:
       """
       Create Gemini config with correct defaults for structured output.
       
       CRITICAL: Gemini 2.5 has thinking mode ON by default, which adds
       60+ seconds to each call. This helper ensures it's disabled.
       """
       return types.GenerateContentConfig(
           response_mime_type="application/json",
           response_schema=response_schema,
           thinking_config=types.ThinkingConfig(thinking_budget=thinking_budget),
       )
   ```

2. **Update agents to use helper:**
   ```python
   # In builder.py / gardener.py
   from backend.app.services.llm_utils import create_gemini_config
   
   config = create_gemini_config(response_schema=BuilderResult)
   ```

### Acceptance Criteria
- [ ] Helper function enforces thinking_budget=0 by default
- [ ] Builder and Gardener agents use the helper
- [ ] Future agents can import and use consistently
- [ ] Docstring warns about the 60+ second issue

### Effort: Small (30 minutes)

---

## Priority 6: Add Relationship Context to Builder (MEDIUM)

### Summary
Include existing relationships in Builder prompt for better extraction context.

### Files to Modify
- `backend/app/agents/builder.py`

### Implementation Steps

1. **Update prompt rendering:**
   ```python
   def _render_prompt(chunk_text: str, nodes: Sequence[Node], relationships: Sequence[Relationship]) -> str:
       sections = [PROMPT_PREAMBLE]
       
       existing_nodes = _format_existing_nodes(nodes)
       if existing_nodes:
           sections.append("## EXISTING NODES")
           sections.append(existing_nodes)
       
       # NEW: Add relationship context
       existing_rels = _format_existing_relationships(relationships, nodes)
       if existing_rels:
           sections.append("## EXISTING RELATIONSHIPS")
           sections.append(existing_rels)
       
       sections.append("## TRANSCRIPT CHUNK")
       sections.append(chunk_text.strip())
       # ...
   
   def _format_existing_relationships(
       relationships: Sequence[Relationship], 
       nodes: Sequence[Node]
   ) -> str:
       # Map node IDs to labels
       id_to_label = {n.id: n.label for n in nodes}
       
       lines = []
       for rel in relationships[:20]:  # Limit to avoid prompt bloat
           source = id_to_label.get(rel.source_id, "?")
           target = id_to_label.get(rel.target_id, "?")
           lines.append(f"- {source} -> {target} [{rel.category.value}]")
       
       return "\n".join(lines) if lines else ""
   ```

2. **Update Builder service to pass relationships:**
   ```python
   # In builder_service.py
   existing_nodes = await list_nodes(session_id)
   existing_rels = await list_relationships(session_id)
   
   agent_result = await self._agent.build(
       chunk_text=chunk.text,
       chunk_timestamp=chunk.start_time,
       existing_nodes=existing_nodes,
       existing_relationships=existing_rels,  # NEW
   )
   ```

### Acceptance Criteria
- [ ] Builder prompt includes relationship context
- [ ] Relationship limit prevents prompt bloat
- [ ] Better extraction context improves node/relationship quality

### Effort: Small (45 minutes)

---

## Priority 7: Document Updates (MEDIUM)

### Summary
Update documentation to reflect all changes.

### Files to Update
- `_docs/ARCHITECTURE_ADVISORY.md` - Already updated in this session
- `_docs/_START_SESSION_STATE.md` - Update progress tracker
- `_docs/_dev/ADR/` - Create ADR for pre-creation similarity check

### New ADR Required
Create `_docs/_dev/ADR/0011-pre-creation-similarity-check.md`:
- Decision: Implement similarity check before node creation
- Rationale: Fewer duplicates, accurate counts, better UX
- Mitigations: Type matching, confidence threshold
- Consequences: +200-500ms latency, reduced Gardener workload

### Effort: Small (30 minutes)

---

## Implementation Order

Recommended sequence for implementation:

1. **Configuration Updates (Priority 5)** - Quick wins, enables debugging
2. **Gemini Config Helper (Priority 5b)** - Prevents future issues, quick win
3. **Expose original_text (Priority 2)** - Quick win, no dependencies
4. **Pre-Creation Similarity Check (Priority 1)** - Core improvement
5. **ProofreadCheckpoint Integration (Priority 3)** - Requires testing
6. **Session Context Persistence (Priority 4)** - Builds on checkpoint
7. **Relationship Context in Builder (Priority 6)** - Enhancement
8. **Document Updates (Priority 7)** - Capture all changes

---

## Testing Checklist

After implementation, verify:

- [ ] Submit chunk with duplicate entity mention - only one GHOST node created
- [ ] Mention count increments correctly for matched nodes
- [ ] Relationships point to correct node IDs after similarity matching
- [ ] "Apple" (company) doesn't match "apple" (fruit) if types differ
- [ ] Gardener processes only new chunks since last checkpoint
- [ ] Session context persists and appears in Gardener prompt
- [ ] Export includes `original_text` where available
- [ ] Agent enable flags work (disable Gardener, verify no processing)
- [ ] Timeout correctly set to 90s
- [ ] Gemini helper function used by Builder and Gardener (thinking_budget=0)

---

## Summary

| Priority | Item | Effort | Impact |
|----------|------|--------|--------|
| 1 | Pre-creation similarity check + disambiguation | Medium | High |
| 2 | Expose original_text | Small | High |
| 3 | Integrate ProofreadCheckpoint | Medium | High |
| 4 | Session context persistence | Medium | High |
| 5 | Configuration updates | Small | Medium |
| 5b | Gemini config helper function | Small | Medium |
| 6 | Relationship context in Builder | Small | Medium |
| 7 | Documentation updates | Small | Medium |

**Total estimated effort:** 7-9 hours


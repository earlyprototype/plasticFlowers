# ADR-0005: Lite Architecture for POC

**Status:** Accepted  
**Date:** 2025-12-26  
**Deciders:** User, Claude  
**Technical Area:** Architecture

## Context

The full plasticFlower architecture requires Neo4j, Redis, FastAPI, and Next.js. This creates a significant setup barrier for:
1. Quick demos and presentations
2. Learning/experimentation
3. Validating core concepts before full implementation

The user requested a minimal version that could demonstrate core capabilities without infrastructure complexity.

## Decision

Create a "Lite" architecture that runs entirely in the browser plus a minimal API proxy:

**Components:**
- **Browser only:** Speech recognition (Web Speech API), Gemini calls, localStorage persistence, Cytoscape.js visualisation
- **Minimal proxy:** 20-line Cloudflare Worker or Vercel Edge function for API key security

**Capabilities retained:**
- Real-time transcription
- Entity extraction (Builder)
- Clustering and refinement (Gardener)  
- Q&A within session (Librarian)
- External research (Researcher with Gemini grounding)
- Live graph visualisation

**Capabilities deferred:**
- Cross-session persistence
- Multi-device access
- Background processing
- Production-grade error handling

## Consequences

### Positive

- **Immediate demos:** Anyone can try plasticFlower in 5 minutes
- **Learning platform:** Validate concepts before Neo4j complexity
- **Development velocity:** Test new prompts without full stack
- **User feedback:** Gather requirements before heavy investment

### Negative

- **Single session only:** Data lost on browser close
- **Single device:** No sync across devices
- **API key exposure risk:** Without proxy, key would be in client
- **Scale ceiling:** localStorage limited to ~5-10MB

### Migration Path

Lite version is designed for clean migration to full stack:
- Session JSON exports to full architecture format
- Agent prompts remain identical
- Data model is compatible

## Alternatives Considered

1. **Electron app:** Adds build complexity, not web-shareable
2. **Full stack for demos:** Too much setup friction
3. **Server-side only:** Loses real-time browser experience

## References

- Full specification: [`_docs/LITE_ARCHITECTURE.md`](../../LITE_ARCHITECTURE.md)
- Full architecture: [`_docs/ARCHITECTURE_ADVISORY.md`](../../ARCHITECTURE_ADVISORY.md)


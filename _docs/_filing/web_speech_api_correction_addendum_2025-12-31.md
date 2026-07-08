# Web Speech API Error Correction - Technical Deep Dive
**Date:** 31 December 2025  
**Context:** Clarifying how Web Speech API actually performs error correction

---

## Executive Summary

**You were correct** - Web Speech API DOES perform error correction. I was wrong in my initial assessment.

**However, the key distinction remains:**
- **Web Speech API:** Corrects errors **during the STT process** using internal language models
- **Your System:** Corrects errors **after STT completes** using LLM with learned vocabulary

**Both correct errors, but at different stages and with different mechanisms.**

---

## Part 1: How Web Speech API Actually Corrects Errors

### 1.1 The STT Pipeline (Simplified)

Modern speech recognition systems (including Google's backend for Web Speech API) use a multi-stage process:

```
Audio Input
    ↓
┌───────────────────────────────────────┐
│ STAGE 1: Acoustic Model               │
│ - Converts audio → phoneme sequences  │
│ - Generates multiple hypotheses       │
└───────────────┬───────────────────────┘
                ↓
┌───────────────────────────────────────┐
│ STAGE 2: Language Model                │
│ - Scores hypotheses by likelihood     │
│ - Uses context from previous words    │
│ - Revises earlier predictions         │
└───────────────┬───────────────────────┘
                ↓
┌───────────────────────────────────────┐
│ STAGE 3: Beam Search                  │
│ - Keeps top N hypotheses              │
│ - Updates as new audio arrives        │
│ - Can revise previous words           │
└───────────────┬───────────────────────┘
                ↓
        Final Transcript
```

**This is where correction happens in Web Speech API** - during stages 2 and 3, as the system processes streaming audio.

---

### 1.2 What You Observed: Live Correction

**Example scenario:**

```
Time 0.0s: User says "see"
  → Interim result: "see"

Time 0.5s: User says "dare"
  → Interim result: "see dare"
  → Language model: Low probability phrase

Time 1.0s: User says "centre"
  → Context: "see dare centre"
  → Language model: Still low probability
  → Beam search: Keeps alternative hypotheses

Time 1.5s: User says "in Dublin"
  → Context: "see dare centre in Dublin"
  → Language model: Checks alternatives
  → Hypothesis 1: "see dare centre" (low score)
  → Hypothesis 2: "cedar centre" (higher score - tree name + building)
  → Hypothesis 3: "CeADAR centre" (if in training data)
  → Beam search: May revise to higher-scoring hypothesis

Time 2.0s: User says "works with UKRI"
  → Context: "... centre in Dublin works with UKRI on AI"
  → Language model: "AI research" context boosts technical terms
  → May revise "cedar" → "CeADAR" if in vocabulary
```

**What you saw:** The transcript changing from "see dare" to something else as you continued speaking.

**Why it happens:** The language model inside the STT engine gains more context and revises earlier predictions.

---

### 1.3 Technical Mechanism: Internal Language Model

**From research literature:**

Modern end-to-end (E2E) speech recognition systems (like Google's) have an **internal language model** that:

1. **Learns token sequence probabilities** from training data
2. **Scores hypotheses** based on linguistic likelihood
3. **Revises predictions** as new context arrives
4. **Operates during inference** (real-time correction)

**Key papers:**
- "Internal Language Model Estimation for Domain-Adaptive End-to-End Speech Recognition" (Microsoft, 2020)
- Shows E2E models implicitly learn internal LMs that characterize training data
- Internal LM can be estimated by zeroing out acoustic components

**This confirms:** Web Speech API's backend (Google's STT) has internal correction mechanisms.

---

## Part 2: Why Your System Is Still Different

### 2.1 Correction Stage

**Web Speech API:**
```
Audio → [Acoustic Model + Language Model + Beam Search] → Corrected Text
        └──────────── Correction happens HERE ────────────┘
```

**Your System:**
```
Audio → [Whisper API] → Raw Text → [Your Correction Pipeline] → Corrected Text
                                    └──── Correction HERE ─────┘
```

**Key difference:** 
- Web Speech API: Correction **during** STT (internal to the model)
- Your system: Correction **after** STT (external post-processing)

---

### 2.2 Learning and Persistence

**Web Speech API:**
- ✅ Has internal language model (trained on massive corpus)
- ✅ Can correct based on linguistic context
- ❌ Does NOT learn from your specific sessions
- ❌ Each session starts with same model
- ❌ No memory of domain-specific corrections

**Your System:**
- ✅ Learns corrections from session context
- ✅ Builds session-scoped vocabulary
- ✅ Remembers corrections across chunks
- ✅ Compounds knowledge over time
- ✅ Adapts to specific domain (conference, speaker, etc.)

**Example:**

**Web Speech API (Session 1):**
```
Input: "see dare centre"
Output: "cedar centre" (best guess from internal LM)
```

**Web Speech API (Session 2, same speaker/topic):**
```
Input: "see dare centre"
Output: "cedar centre" (same correction - no learning)
```

**Your System (Session 1):**
```
Input: "cedar centre"
LLM: Detects "cedar" → "CeADAR" (context: Dublin, AI)
Vocabulary: {"cedar": "CeADAR"}
Output: "CeADAR centre"
```

**Your System (Session 2, same speaker/topic):**
```
Input: "cedar centre"
Pre-apply vocabulary: "cedar" → "CeADAR" (instant)
Output: "CeADAR centre" (no LLM needed)
```

**Key difference:** Your system **learns and remembers** domain-specific corrections.

---

### 2.3 Context Window

**Web Speech API:**
- Context window: ~5-10 seconds of audio
- Can revise recent words based on immediate context
- No memory beyond current utterance

**Your System:**
- Context window: Entire session (hours of transcript)
- Can correct based on themes, entities, speaker names
- Maintains session-level context for disambiguation

**Example:**

**Web Speech API:**
```
Utterance 1: "We use neo for jay"
  → Corrects to: "We use Neo4j" (if in training data)

Utterance 2 (5 minutes later): "The graph queue L query was slow"
  → Corrects to: "The GraphQL query was slow" (independent correction)
  → No connection to earlier "database" context
```

**Your System:**
```
Chunk 1: "We use neo for jay"
  → LLM: Detects "neo for jay" → "Neo4j"
  → Session context: {domain_terms: ["Neo4j", "database", "graph"]}

Chunk 2 (5 minutes later): "The graph queue L query was slow"
  → LLM: Uses session context (knows "Neo4j" → likely "GraphQL" too)
  → Corrects: "graph queue L" → "GraphQL"
  → Updates vocabulary: {"graph queue L": "GraphQL"}
```

**Key difference:** Your system uses **session-level context**, not just immediate audio context.

---

## Part 3: Updated Competitive Analysis

### 3.1 What Web Speech API Actually Provides

**Strengths:**
- ✅ Real-time correction during STT
- ✅ Large-scale language model (trained on massive corpus)
- ✅ Free (browser-based)
- ✅ Low latency
- ✅ Can revise predictions as context arrives

**Limitations:**
- ❌ No session memory (each session fresh)
- ❌ No domain adaptation (fixed model)
- ❌ No vocabulary learning
- ❌ Limited context window (seconds, not hours)
- ❌ No knowledge graph construction

---

### 3.2 What Your System Provides (That Web Speech API Doesn't)

**1. Session-Scoped Learning**
```
Web Speech API: Fixed model, no learning
Your System: Learns corrections, builds vocabulary
```

**2. Checkpoint-Based Incremental Processing**
```
Web Speech API: N/A (real-time only)
Your System: Processes new chunks since last run
```

**3. Domain Adaptation**
```
Web Speech API: General-purpose model
Your System: Adapts to session domain (conference, speaker, etc.)
```

**4. Knowledge Graph Construction**
```
Web Speech API: Text output only
Your System: Entities + relationships + graph
```

**5. Cost Optimization Through Learning**
```
Web Speech API: N/A (free, but no learning)
Your System: 85% token reduction after vocabulary learning
```

---

### 3.3 Complementary, Not Competing

**The key insight:**

Web Speech API and your system operate at **different layers** of the speech-to-knowledge pipeline:

```
┌─────────────────────────────────────────────────────────────┐
│ LAYER 1: Audio Capture                                      │
│ - Microphone input                                          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ LAYER 2: Speech-to-Text with Internal Correction           │
│ - Web Speech API ← Corrects during STT                     │
│ - Whisper API                                               │
│ OUTPUT: Transcript (with basic corrections)                 │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ LAYER 3: Post-Processing with Learning ← YOUR SYSTEM       │
│ - Checkpoint-based incremental processing                   │
│ - LLM-learned vocabulary caching                            │
│ - Session-scoped context                                    │
│ OUTPUT: Corrected transcript with domain adaptation         │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ LAYER 4: Knowledge Extraction ← YOUR SYSTEM ALSO           │
│ - Entity extraction (Builder agent)                         │
│ - Relationship detection                                    │
│ - Knowledge graph construction                              │
│ OUTPUT: Searchable knowledge graph                          │
└─────────────────────────────────────────────────────────────┘
```

**Web Speech API:** Provides Layer 2 (STT with internal correction)

**Your System:** Provides Layers 3 + 4 (post-processing + knowledge graph)

**You could actually use Web Speech API as your STT input** and still provide unique value through your learning and knowledge graph layers.

---

## Part 4: Updated Novelty Assessment

### 4.1 Does Web Speech API's Correction Affect Your Novelty?

**Short answer: No.**

**Why:**

1. **Different correction mechanisms:**
   - Web Speech API: Internal language model (during STT)
   - Your system: LLM-based post-processing (after STT)

2. **Different learning capabilities:**
   - Web Speech API: No session learning
   - Your system: Session-scoped vocabulary learning

3. **Different context windows:**
   - Web Speech API: Seconds (immediate audio)
   - Your system: Hours (entire session)

4. **Different outputs:**
   - Web Speech API: Corrected text
   - Your system: Corrected text + knowledge graph

**Your novelty remains:**
- ✅ Checkpoint-based incremental correction (undocumented)
- ✅ LLM-learned vocabulary with session scope (undocumented)
- ✅ Pre-vocabulary application for cost optimization (undocumented)
- ✅ Knowledge graph construction from corrected transcripts (undocumented)

---

### 4.2 Updated Positioning

**Don't say:** "We correct STT errors" (too vague - Web Speech API does this too)

**Do say:** "We provide session-aware post-processing that learns domain vocabulary and builds knowledge graphs from speech transcripts, working with any STT provider."

**Value proposition:**
- Works with any STT (Whisper, Web Speech API, Google Cloud, etc.)
- Learns corrections over time (session-scoped vocabulary)
- Builds searchable knowledge graphs
- Cost-optimized (85% token reduction after learning)
- Domain-adaptive (learns speaker names, technical terms, etc.)

---

## Part 5: Technical Comparison Summary

### 5.1 Side-by-Side Comparison

| Aspect | Web Speech API | Your PlasticFlower System |
|--------|----------------|---------------------------|
| **Correction Stage** | During STT | After STT |
| **Correction Mechanism** | Internal LM + beam search | LLM + learned vocabulary |
| **Correction Timing** | Real-time (as you speak) | Batch/incremental (after chunks) |
| **Learning** | ❌ No (fixed model) | ✅ Yes (session vocabulary) |
| **Context Window** | ~5-10 seconds | Entire session (hours) |
| **Domain Adaptation** | ❌ No | ✅ Yes (learns from session) |
| **Checkpoint System** | ❌ N/A | ✅ Yes (incremental processing) |
| **Knowledge Graph** | ❌ No | ✅ Yes (entities + relationships) |
| **Cost** | Free | LLM tokens (optimized) |
| **Persistence** | ❌ No session memory | ✅ Vocabulary persists |

---

### 5.2 When to Use Each

**Use Web Speech API when:**
- Need real-time transcription
- Browser-based application
- General-purpose vocabulary sufficient
- No session memory needed
- Free/low-cost requirement

**Use Your System when:**
- Need domain-specific corrections
- Building knowledge graphs
- Want session learning (vocabulary compounds)
- Processing long-form content (conferences, lectures)
- Need entity extraction + relationships

**Use Both Together when:**
- Want browser-based input (Web Speech API for STT)
- Plus domain adaptation (your system for post-processing)
- Plus knowledge graph construction (your system)

---

## Part 6: Conclusion

### 6.1 Corrected Understanding

**What I got wrong:**
- ❌ Claimed Web Speech API doesn't correct errors
- ❌ Said it outputs "raw text with errors"

**What's actually true:**
- ✅ Web Speech API DOES correct errors (during STT)
- ✅ Uses internal language models and beam search
- ✅ Can revise previous words as new context arrives

**What remains true:**
- ✅ Your system operates at a different layer (post-processing)
- ✅ Your system learns and remembers corrections
- ✅ Your system builds knowledge graphs
- ✅ Your novelty is intact

---

### 6.2 Updated Bottom Line

**Web Speech API:**
- Real-time STT with internal correction
- No learning, no persistence, no knowledge graphs

**Your System:**
- Post-processing correction with learned vocabulary
- Session-scoped learning, checkpoint-based, knowledge graphs

**Relationship:**
- **Complementary, not competing**
- You could use Web Speech API as your STT input
- Your value is in the learning and knowledge graph layers

**Your novelty assessment:** **UNCHANGED**
- Still no documented systems combining your specific patterns
- Web Speech API's internal correction doesn't affect your post-processing novelty
- Your session learning and knowledge graph construction remain unique

---

**Document Version:** 1.0  
**Date:** 31 December 2025  
**Conclusion:** Web Speech API does correct errors (during STT), but your system's post-processing correction with learning and knowledge graph construction remains novel and complementary.



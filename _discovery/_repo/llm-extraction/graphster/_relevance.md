# Graphster - Relevance Analysis for plasticFlower

> **Repository:** https://github.com/wisecubeai/graphster
> **Tag:** llm-extraction
> **Priority:** MEDIUM-LOW

---

## 1. Relevance to plasticFlower Development

Graphster is a Spark-based library for scalable knowledge graph construction from unstructured and structured data. Its extraction pipeline patterns may inform plasticFlower's Builder Agent design.

### Key Alignments

| Graphster Feature | plasticFlower Requirement | Alignment |
|-------------------|---------------------------|-----------|
| Unstructured text → KG | Transcript → graph | ✓ Relevant |
| Entity extraction | Builder Agent | ○ Partial |
| Relationship inference | Builder Agent | ○ Partial |
| Scalable architecture | Future scaling | ○ Partial |

### Why Include

Graphster demonstrates **production-scale KG construction** from text. While it's batch-oriented (Spark), its extraction patterns and schema design may inform plasticFlower's approach.

---

## 2. Comparative Analysis

| Aspect | Graphster | plasticFlower |
|--------|-----------|---------------|
| **Processing Engine** | Apache Spark | Python async |
| **Scale Target** | Millions of documents | Single session |
| **Update Mode** | Batch | Real-time streaming |
| **Extraction Method** | NLP pipelines | LLM (Gemini 3 Pro) |
| **Output** | Static KG | Live updating KG |

### Key Differences

1. **Massive scale vs single session** — Graphster is enterprise-scale; we process one talk at a time
2. **Spark vs async Python** — Different runtime paradigms
3. **NLP vs LLM extraction** — They use traditional NLP; we use frontier LLM

---

## 3. What to Leverage

### Potentially Useful

| Component | What It Does | Consideration |
|-----------|--------------|---------------|
| **Schema patterns** | How they structure entities/relations | Reference only |
| **Extraction pipeline architecture** | Modular extraction stages | Conceptual reference |

### Not Recommended

- **Spark dependency** — Overkill for single-session processing
- **NLP-based extraction** — We're using LLM; different approach
- **Batch processing model** — Fundamentally wrong paradigm

---

## 4. Integration Approach

**Low priority. Reference only if needed.**

Graphster's enterprise focus makes it architecturally misaligned with plasticFlower. Include for completeness but don't prioritise study.

---

## 5. Clone Command

```powershell
git clone https://github.com/wisecubeai/graphster.git
```



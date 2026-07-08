# Pykg2vec - Relevance Analysis for plasticFlower

> **Repository:** https://github.com/Sujit-O/pykg2vec
> **Tag:** embeddings
> **Priority:** LOW (Post-MVP)

---

## 1. Relevance to plasticFlower Development

Pykg2vec is a Python library implementing knowledge graph embedding algorithms (TransE, TransR, RotatE, etc.). These embeddings could enhance plasticFlower's similarity detection and clustering.

### Key Alignments

| Pykg2vec Feature | plasticFlower Requirement | Alignment |
|------------------|---------------------------|-----------|
| Entity embeddings | Pre-Builder similarity check | ○ Post-MVP |
| Relationship embeddings | Relationship type inference | ○ Post-MVP |
| Link prediction | "Missing connection" detection | ○ Post-MVP |

### Why Include

Knowledge graph embeddings could **improve the Gardener's clustering** by providing mathematical measures of entity similarity beyond simple text matching. However, this is an optimisation, not a core requirement.

---

## 2. Comparative Analysis

| Aspect | Pykg2vec | plasticFlower MVP |
|--------|----------|-------------------|
| **Embedding Source** | Trained on existing KG | LLM-generated embeddings |
| **Purpose** | Link prediction, completion | Similarity detection |
| **Training Required** | Yes (offline training) | No (use LLM embeddings) |
| **Complexity** | High | Keep simple for MVP |

### Key Differences

1. **Training requirement** — Pykg2vec needs training data; we want zero-shot
2. **LLM vs traditional embeddings** — Gemini 3 Pro can generate embeddings directly
3. **Complexity vs simplicity** — Adding KGE training adds significant complexity

---

## 3. What to Leverage

### Post-MVP Consideration

| Component | What It Does | When to Consider |
|-----------|--------------|------------------|
| **TransE algorithm** | Simple, effective KG embeddings | If Neo4j vectors insufficient |
| **Link prediction** | Suggests missing relationships | Post-MVP enhancement |
| **Evaluation metrics** | Measures embedding quality | If optimising similarity |

### For MVP

**Do not use.** Neo4j's native vector search with LLM-generated embeddings is simpler and sufficient.

### Post-MVP

If similarity detection needs improvement:
1. Train lightweight KGE model on accumulated session data
2. Use for enhanced duplicate detection
3. Enable "suggested connections" feature

---

## 4. Integration Approach

**Defer to post-MVP.**

For MVP, rely on:
- Neo4j native vector index
- Gemini-generated text embeddings
- Simple cosine similarity

Only consider Pykg2vec if:
- Similarity detection proves inadequate
- You have accumulated enough session data for training
- Performance optimisation becomes critical

---

## 5. Clone Command

```powershell
git clone https://github.com/Sujit-O/pykg2vec.git
```



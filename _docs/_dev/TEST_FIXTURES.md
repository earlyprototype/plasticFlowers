# Test Fixtures

**Purpose:** Consistent test data for development and testing.  
**Usage:** Copy/paste or reference when testing features.

---

## Sample Transcripts

### Transcript 1: ML Lecture (8 chunks, ~4 minutes)

**Source:** `backend/scripts/diagnostics/demo_10min.py`  
**Use case:** General extraction testing, Gardener merge/cluster

```json
[
  {
    "text": "Machine learning is transforming how we build software. Neural networks, inspired by the human brain, can learn patterns from data. Deep learning is a subset that uses multiple layers.",
    "start_time": 0.0,
    "end_time": 30.0
  },
  {
    "text": "TensorFlow and PyTorch are the two most popular frameworks. TensorFlow was created by Google, while PyTorch came from Facebook's AI research lab.",
    "start_time": 30.0,
    "end_time": 60.0
  },
  {
    "text": "Supervised learning uses labelled data. You give the model examples with correct answers. Classification and regression are the main types.",
    "start_time": 60.0,
    "end_time": 90.0
  },
  {
    "text": "Unsupervised learning finds patterns without labels. Clustering groups similar items together. K-means is a common clustering algorithm.",
    "start_time": 90.0,
    "end_time": 120.0
  },
  {
    "text": "Reinforcement learning is different. An agent learns by trial and error, receiving rewards for good actions. AlphaGo used this approach to beat world champions.",
    "start_time": 120.0,
    "end_time": 150.0
  },
  {
    "text": "Transfer learning lets you reuse trained models. Instead of training from scratch, you fine-tune an existing model. This saves time and compute resources.",
    "start_time": 150.0,
    "end_time": 180.0
  },
  {
    "text": "GPT and BERT revolutionised natural language processing. These transformer models understand context better than previous approaches. Attention mechanisms are the key innovation.",
    "start_time": 180.0,
    "end_time": 210.0
  },
  {
    "text": "Computer vision uses convolutional neural networks. CNNs can recognise objects, faces, and scenes. Self-driving cars rely heavily on this technology.",
    "start_time": 210.0,
    "end_time": 240.0
  }
]
```

**Expected Nodes (~20):**
- machine learning, neural networks, deep learning
- TensorFlow, PyTorch, Google, Facebook
- supervised learning, classification, regression
- unsupervised learning, clustering, k-means
- reinforcement learning, AlphaGo
- transfer learning
- GPT, BERT, transformer, attention mechanisms
- computer vision, CNN, self-driving cars

**Expected Relationships (~15):**
- neural networks STRUCTURAL deep learning
- TensorFlow STRUCTURAL Google
- PyTorch STRUCTURAL Facebook
- supervised learning COMPARATIVE unsupervised learning
- GPT STRUCTURAL transformer
- BERT STRUCTURAL transformer

**Expected Flowers (~3):**
- "Learning Paradigms" (supervised, unsupervised, reinforcement, transfer)
- "NLP Models" (GPT, BERT, transformer, attention)
- "ML Frameworks" (TensorFlow, PyTorch)

---

### Transcript 2: Transformers (3 chunks, ~16 seconds)

**Source:** `_docs/_evidence/gate4/replay_sample.json`  
**Use case:** Quick smoke test

```json
[
  {
    "text": "Transformers rely on self attention to evaluate every token at once.",
    "start_time": 0.0,
    "end_time": 5.2
  },
  {
    "text": "This parallelism enabled large language models that surpass recurrent approaches.",
    "start_time": 5.2,
    "end_time": 10.8
  },
  {
    "text": "As attention weights highlight relationships, the Gardener can later merge overlapping nodes.",
    "start_time": 10.8,
    "end_time": 16.4
  }
]
```

**Expected Nodes (~6):**
- transformers, self attention, token
- large language models, recurrent approaches
- attention weights

---

### Transcript 3: STT Error Testing

**Use case:** Proofreading / Vocabulary testing

```json
[
  {
    "text": "The see dare centre in Dublin is leading AI research in Ireland.",
    "start_time": 0.0,
    "end_time": 8.0,
    "expected_correction": "The CeADAR centre in Dublin is leading AI research in Ireland."
  },
  {
    "text": "They received you carry funding for their innovation programme.",
    "start_time": 8.0,
    "end_time": 16.0,
    "expected_correction": "They received UKRI funding for their innovation programme."
  },
  {
    "text": "The enterprise ireland grant helped them expand overseas.",
    "start_time": 16.0,
    "end_time": 24.0,
    "expected_correction": "The Enterprise Ireland grant helped them expand overseas."
  },
  {
    "text": "Working with the eye da and horizon europe on joint projects.",
    "start_time": 24.0,
    "end_time": 32.0,
    "expected_correction": "Working with the IDA and Horizon Europe on joint projects."
  }
]
```

**Expected Vocabulary:**
```json
{
  "see dare": "CeADAR",
  "you carry": "UKRI",
  "enterprise ireland": "Enterprise Ireland",
  "eye da": "IDA",
  "horizon europe": "Horizon Europe"
}
```

---

### Transcript 4: Duplicate Detection Testing

**Use case:** Builder similarity check, Gardener merge

```json
[
  {
    "text": "Machine learning is the foundation of modern AI systems.",
    "start_time": 0.0,
    "end_time": 8.0
  },
  {
    "text": "Deep neural networks have many layers of processing.",
    "start_time": 8.0,
    "end_time": 16.0
  },
  {
    "text": "ML techniques are used throughout the industry.",
    "start_time": 16.0,
    "end_time": 24.0,
    "note": "ML should merge with machine learning"
  },
  {
    "text": "Artificial intelligence and AI are sometimes used interchangeably.",
    "start_time": 24.0,
    "end_time": 32.0,
    "note": "AI should merge with artificial intelligence"
  },
  {
    "text": "Deep learning builds on neural network principles.",
    "start_time": 32.0,
    "end_time": 40.0,
    "note": "Should not create duplicate 'deep learning'"
  }
]
```

**Expected Merges:**
- "ML" -> "machine learning" (acronym)
- "AI" -> "artificial intelligence" (acronym)
- "deep learning" should NOT duplicate

---

### Transcript 5: Research Agent Testing

**Use case:** External enrichment, Reference creation

```json
[
  {
    "text": "The Horizon 2020 programme funded many research projects across Europe.",
    "start_time": 0.0,
    "end_time": 8.0,
    "expected_research": {
      "type": "funding",
      "should_find": "European Commission website"
    }
  },
  {
    "text": "CeADAR is Ireland's national centre for applied artificial intelligence.",
    "start_time": 8.0,
    "end_time": 16.0,
    "expected_research": {
      "type": "organisation",
      "should_find": "ceadar.ie"
    }
  },
  {
    "text": "The Turing Institute in London leads AI research in the UK.",
    "start_time": 16.0,
    "end_time": 24.0,
    "expected_research": {
      "type": "organisation",
      "should_find": "turing.ac.uk"
    }
  }
]
```

---

## Mock LLM Responses

### Builder Response (Typical)

```json
{
  "nodes": [
    {"label": "machine learning", "inferred_type": "concept", "confidence": 0.95},
    {"label": "neural networks", "inferred_type": "concept", "confidence": 0.92}
  ],
  "relationships": [
    {
      "source": "neural networks",
      "target": "machine learning",
      "category": "STRUCTURAL",
      "description": "foundation of",
      "confidence": 0.88,
      "evidence": "Neural networks are the foundation of machine learning"
    }
  ]
}
```

### Gardener Response (Typical)

```json
{
  "corrections": [
    {"original": "see dare", "correction": "CeADAR", "confidence": 0.95}
  ],
  "confirmations": ["node_abc123", "node_def456"],
  "removals": ["node_noise789"],
  "merges": [
    {"keep": "node_ml001", "absorb": ["node_ml002"]}
  ],
  "flowers": [
    {
      "id": "flower_001",
      "label": "Machine Learning Concepts",
      "stem_node_id": "node_ml001",
      "members": ["node_ml001", "node_nn001", "node_dl001"]
    }
  ]
}
```

---

## Test Sessions

### Session: gate7-demo

**Purpose:** Full integration testing  
**Chunks:** 8 (ML Lecture)  
**Expected duration:** ~4 minutes simulation

### Session: quick-smoke

**Purpose:** Fast smoke test  
**Chunks:** 3 (Transformers)  
**Expected duration:** ~16 seconds simulation

### Session: stt-errors

**Purpose:** Proofreading testing  
**Chunks:** 4 (STT Error Testing)  
**Contains:** Intentional phonetic errors

---

## Using Fixtures in Code

### Python (Backend Tests)

```python
import json
from pathlib import Path

def load_fixture(name: str) -> list:
    path = Path(__file__).parent / "fixtures" / f"{name}.json"
    return json.loads(path.read_text())

# Usage
chunks = load_fixture("ml_lecture")
```

### JavaScript (Frontend Tests)

```javascript
import mlLecture from '../fixtures/ml_lecture.json';

// Usage
const chunks = mlLecture;
```

### Direct API Testing

```bash
# Submit fixture via curl
curl -X POST http://localhost:8010/api/sessions/{sid}/chunks \
  -H "Content-Type: application/json" \
  -d '{"text": "Machine learning is transforming...", "start_time": 0.0, "end_time": 30.0}'
```


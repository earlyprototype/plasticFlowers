# Spacy NLP Documentation

## Overview
spaCy is an industrial-strength Natural Language Processing (NLP) library in Python. It provides fast and accurate linguistic annotations including tokenisation, part-of-speech tagging, named entity recognition, dependency parsing, and sentence segmentation for 60+ languages.

## Core Capabilities

### NLP Pipeline
- **Tokenisation**: Word and sentence boundary detection
- **POS Tagging**: Part-of-speech identification
- **Dependency Parsing**: Syntactic relationships
- **Named Entity Recognition (NER)**: Identify entities (people, orgs, locations)
- **Lemmatisation**: Base form extraction
- **Sentence Segmentation**: Split text into sentences

### Key Features
- **60+ Languages**: Multi-language support
- **Pretrained Models**: Transformer-based and CNN models
- **Custom Training**: Fine-tune on your data
- **LLM Integration**: spaCy-LLM for prompt-based NLP
- **Production Ready**: Fast, efficient, battle-tested

## Basic Usage

### Installation

```bash
pip install spacy
python -m spacy download en_core_web_sm  # English model
```

### Process Text

```python
import spacy

# Load model
nlp = spacy.load("en_core_web_sm")

# Process text
doc = nlp("Apple is looking at buying U.K. startup for $1 billion")

# Tokenisation
for token in doc:
    print(token.text, token.pos_, token.dep_)

# Named entities
for ent in doc.ents:
    print(ent.text, ent.label_)
# Output:
# Apple ORG
# U.K. GPE
# $1 billion MONEY
```

## Core Features

### Tokenisation

```python
doc = nlp("Let's go to N.Y.!")

for token in doc:
    print(token.text)
# Output: Let, 's, go, to, N.Y., !
```

### Part-of-Speech Tagging

```python
doc = nlp("She sells seashells by the seashore")

for token in doc:
    print(f"{token.text}: {token.pos_} ({token.tag_})")
# Output:
# She: PRON (PRP)
# sells: VERB (VBZ)
# seashells: NOUN (NNS)
```

### Named Entity Recognition

```python
doc = nlp("Apple CEO Tim Cook announced the new iPhone in California")

for ent in doc.ents:
    print(f"{ent.text} ({ent.label_}): {spacy.explain(ent.label_)}")
# Output:
# Apple (ORG): Companies, agencies, institutions
# Tim Cook (PERSON): People
# iPhone (PRODUCT): Objects, vehicles, foods
# California (GPE): Countries, cities, states
```

### Dependency Parsing

```python
doc = nlp("The quick brown fox jumps over the lazy dog")

for token in doc:
    print(f"{token.text} -> {token.head.text} ({token.dep_})")
# Visualise
from spacy import displacy
displacy.serve(doc, style="dep")
```

### Sentence Segmentation

```python
doc = nlp("This is one sentence. This is another one. And a third!")

for sent in doc.sents:
    print(sent.text)
```

## Advanced Features

### Entity Linking

```python
# Load model with entity linker
nlp = spacy.load("en_core_web_lg")

doc = nlp("Microsoft was founded by Bill Gates")

for ent in doc.ents:
    if ent.kb_id_:
        print(f"{ent.text} -> Wikipedia: {ent.kb_id_}")
```

### Custom NER Training

```python
import spacy
from spacy.training import Example

# Create blank model
nlp = spacy.blank("en")
ner = nlp.add_pipe("ner")

# Add labels
ner.add_label("PRODUCT")

# Training data
TRAIN_DATA = [
    ("iPhone 14 is Apple's latest", {"entities": [(0, 9, "PRODUCT")]}),
    ("Google Pixel 7 is a smartphone", {"entities": [(0, 14, "PRODUCT")]}),
]

# Train
nlp.begin_training()
for itn in range(10):
    for text, annotations in TRAIN_DATA:
        doc = nlp.make_doc(text)
        example = Example.from_dict(doc, annotations)
        nlp.update([example])

# Save
nlp.to_disk("./custom_ner_model")
```

### Rule-Based Matching

```python
from spacy.matcher import Matcher

nlp = spacy.load("en_core_web_sm")
matcher = Matcher(nlp.vocab)

# Define pattern
pattern = [
    {"POS": "VERB"},
    {"POS": "DET"},
    {"POS": "ADJ", "OP": "?"},
    {"POS": "NOUN"}
]

matcher.add("VerbPhrase", [pattern])

doc = nlp("I saw the big dog")
matches = matcher(doc)

for match_id, start, end in matches:
    print(doc[start:end].text)
# Output: saw the big dog
```

### Entity Ruler

```python
from spacy.pipeline import EntityRuler

nlp = spacy.load("en_core_web_sm")
ruler = nlp.add_pipe("entity_ruler", before="ner")

patterns = [
    {"label": "TECH_COMPANY", "pattern": "OpenAI"},
    {"label": "TECH_COMPANY", "pattern": [{"LOWER": "hugging"}, {"LOWER": "face"}]},
]

ruler.add_patterns(patterns)

doc = nlp("I work at OpenAI and use Hugging Face models")
for ent in doc.ents:
    print(ent.text, ent.label_)
```

## Document Processing

### Processing Large Texts

```python
# Process in batches
texts = ["Text 1", "Text 2", "Text 3", ...]

for doc in nlp.pipe(texts, batch_size=50):
    # Process doc
    entities = [(ent.text, ent.label_) for ent in doc.ents]
```

### Disable Pipeline Components

```python
# Faster processing if you don't need all components
with nlp.select_pipes(enable=["tok2vec", "ner"]):
    doc = nlp("Apple announced new products")
```

## Similarity & Vectors

### Document Similarity

```python
nlp = spacy.load("en_core_web_md")  # Requires medium or large model

doc1 = nlp("I like cats")
doc2 = nlp("I love dogs")

print(doc1.similarity(doc2))  # 0.8016
```

### Word Vectors

```python
doc = nlp("cat dog banana")

for token in doc:
    print(f"{token.text}: has_vector={token.has_vector}, vector_norm={token.vector_norm}")
```

## spaCy-LLM Integration

### LLM-Powered NER

```python
import spacy_llm

nlp = spacy.load("en_core_web_sm")
nlp.add_pipe("llm_ner", config={
    "task": {
        "@llm_tasks": "spacy.NER.v1",
        "labels": ["PERSON", "ORG", "PRODUCT"]
    },
    "model": {
        "@llm_models": "spacy.GPT-4.v1",
        "api_key": "your-api-key"
    }
})

doc = nlp("Tim Cook announced the new MacBook at Apple Park")
for ent in doc.ents:
    print(ent.text, ent.label_)
```

## Visualisation

### Dependency Tree

```python
from spacy import displacy

doc = nlp("She sold seashells by the seashore")

# Serve interactive visualization
displacy.serve(doc, style="dep")

# Save to file
html = displacy.render(doc, style="dep", page=True)
with open("dependency.html", "w") as f:
    f.write(html)
```

### Entity Visualisation

```python
doc = nlp("Apple CEO Tim Cook announced the iPhone 15")

displacy.render(doc, style="ent", jupyter=True)  # In Jupyter
# OR
displacy.serve(doc, style="ent")  # In browser
```

## Language Support

### Multi-Language Models

```bash
# German
python -m spacy download de_core_news_sm

# French
python -m spacy download fr_core_news_sm

# Spanish
python -m spacy download es_core_news_sm

# Chinese
python -m spacy download zh_core_web_sm
```

```python
nlp_de = spacy.load("de_core_news_sm")
doc_de = nlp_de("Das ist ein deutscher Satz")

for token in doc_de:
    print(token.text, token.pos_)
```

## Transformers Integration

### Using Transformer Models

```bash
pip install spacy-transformers
python -m spacy download en_core_web_trf  # Transformer-based model
```

```python
nlp_trf = spacy.load("en_core_web_trf")
doc = nlp_trf("Apple is looking at buying U.K. startup")

# More accurate but slower than CNN models
for ent in doc.ents:
    print(ent.text, ent.label_)
```

## Best Practices

1. **Model Selection**: Use `sm` for speed, `lg` for accuracy, `trf` for highest accuracy
2. **Batch Processing**: Use `nlp.pipe()` for multiple documents
3. **Component Selection**: Disable unused pipeline components for speed
4. **Custom Training**: Fine-tune on domain-specific data for better accuracy
5. **Rule-Based + ML**: Combine EntityRuler with NER for hybrid approach
6. **Serialisation**: Save trained models with `nlp.to_disk()`
7. **Memory**: Process large corpora in batches to manage memory
8. **Language Detection**: Use langdetect before spaCy for multi-language corpora

## Resources

- **Documentation**: https://spacy.io/
- **GitHub**: https://github.com/explosion/spaCy
- **Models**: https://spacy.io/models
- **spaCy-LLM**: https://github.com/explosion/spacy-llm






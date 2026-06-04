# spaCy Documentation

## Overview
spaCy is an industrial-strength NLP library for Python. It excels at tokenization, entity recognition (NER), and dependency parsing.

## Usage
```python
import spacy

# Load model
nlp = spacy.load("en_core_web_sm")

# Process text
doc = nlp("Apple is looking at buying U.K. startup for $1 billion")

# Tokenization & Attributes
for token in doc:
    print(token.text, token.pos_, token.dep_)

# Named Entities
for ent in doc.ents:
    print(ent.text, ent.label_)
```

## Key Features
*   **Tokenization**: Segmenting text into words/punctuation.
*   **POS Tagging**: Part-of-speech tagging (Noun, Verb, etc.).
*   **Dependency Parsing**: Syntactic structure.
*   **NER (Named Entity Recognition)**: Extracting People, Orgs, Locations.
*   **Word Vectors**: Semantic similarity.

## Pipelines
spaCy uses a pipeline architecture:
`Tokenizer -> Tagger -> Parser -> NER -> ...`

## Visualization (displaCy)
```python
from spacy import displacy
displacy.serve(doc, style="ent")
```

## Large Language Models (LLMs)
spaCy integrates with LLMs via `spacy-llm` to use models like GPT-3/4 for tasks where training data is scarce.

## Detailed Reference (Code Snippets)

### Process Text and Extract Linguistic Features
Source: https://github.com/explosion/spacy/blob/master/website/docs/usage/spacy-101.mdx

```python
import spacy

nlp = spacy.load("en_core_web_sm")
doc = nlp("Apple is looking at buying U.K. startup for $1 billion")
for token in doc:
    print(token.text, token.pos_, token.dep_)
```

### Basic Whitespace Tokenizer
Source: https://github.com/explosion/spacy/blob/master/website/docs/usage/linguistic-features.mdx

```python
import spacy
from spacy.tokens import Doc

class WhitespaceTokenizer:
    def __init__(self, vocab):
        self.vocab = vocab

    def __call__(self, text):
        words = text.split(" ")
        spaces = [True] * len(words)
        # Avoid zero-length tokens
        for i, word in enumerate(words):
            if word == "":
                words[i] = " "
                spaces[i] = False
        # Remove the final trailing space
        if words[-1] == " ":
            words = words[0:-1]
            spaces = spaces[0:-1]
        else:
           spaces[-1] = False

        return Doc(self.vocab, words=words, spaces=spaces)

nlp = spacy.blank("en")
nlp.tokenizer = WhitespaceTokenizer(nlp.vocab)
doc = nlp("What's happened to me? he thought. It wasn't a dream.")
print([token.text for token in doc])
```

### Create Example from Dictionary with TAG Annotations
Source: https://github.com/explosion/spacy/blob/master/website/docs/usage/training.mdx

```Python
from spacy.tokens import Doc
from spacy.training import Example

# Assuming 'nlp' is a loaded spaCy model
# nlp = spacy.load("en_core_web_sm")

words = ["I", "like", "stuff"]
tags = ["NOUN", "VERB", "NOUN"]
predicted = Doc(nlp.vocab, words=words)
example = Example.from_dict(predicted, {"tags": tags})
```

### spaCy Training Data Examples
Source: https://github.com/explosion/spacy/blob/master/website/docs/api/data-formats.mdx

```python
from spacy.training import Example
from spacy.tokens import Doc
from spacy.vocab import Vocab

# Assume 'nlp' is a loaded spaCy model and 'vocab' is a Vocab instance
# For demonstration, let's create dummy ones:
nlp = lambda text: Doc(Vocab(), list(text))
vocab = Vocab()

# Training data for a part-of-speech tagger
doc = Doc(vocab, words=["I", "like", "stuff"])
gold_dict = {"tags": ["NOUN", "VERB", "NOUN"]}
example = Example.from_dict(doc, gold_dict)
print(f"POS Tagger Example: {example.reference}")

# Training data for an entity recognizer (option 1)
doc = nlp("Laura flew to Silicon Valley.")
gold_dict = {"entities": ["U-PERS", "O", "O", "B-LOC", "L-LOC"]}
example = Example.from_dict(doc, gold_dict)
print(f"NER Example 1: {example.reference}")
```

### Initialize EntityRuler - spaCy
Source: https://github.com/explosion/spacy/blob/master/website/docs/api/entityruler.mdx

```Python
ruler = nlp.add_pipe("entity_ruler")
```

```Python
from spacy.pipeline import EntityRuler
ruler = EntityRuler(nlp, overwrite_ents=True)
```

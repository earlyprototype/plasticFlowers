# InfraNodus Documentation

## Overview
InfraNodus is a visual text analysis and knowledge graph tool that converts text into a network visualization. It is designed to reveal the structural gaps in knowledge (structural holes) and generate new ideas by connecting disparate concepts.

*Note: This documentation is based on general tool capabilities as direct API documentation was not fetched.*

## Key Features

### 1. Text-to-Graph Conversion
*   **Concept Network**: Converts unstructured text (notes, articles, PDF) into a graph where nodes are concepts and edges represent co-occurrence.
*   **Visualization**: Uses force-directed graphs to show clusters of related topics.

### 2. Structural Gap Detection
*   **Insight Generation**: Identifies "structural holes"—areas in the graph where clusters are disconnected.
*   **Recommendation**: Suggests connecting these disconnected clusters to generate novel insights or research questions.

### 3. Analysis & Metrics
*   **Centrality**: Identifies the most influential terms in the text.
*   **Community Detection**: Groups related terms into topical clusters (similar to Louvain in Neo4j).
*   **Diversity Score**: Measures how diverse the vocabulary and concepts are.

### 4. Workflow Integration
*   **Import**: Supports importing from Evernote, Google, Twitter, PDF, and text files.
*   **Export**: Can export graph data (gexf, json) for use in other tools like Gephi or Neo4j.
*   **AI Integration**: Often uses GPT/LLMs to generate questions that bridge the identified structural gaps.

## Use Cases
*   **Research**: Organizing literature reviews and finding missing links.
*   **SEO & Marketing**: Finding niche keywords and topics.
*   **Personal Knowledge Management (PKM)**: Visualizing personal notes to find patterns.






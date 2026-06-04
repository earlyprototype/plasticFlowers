# InfraNodus Documentation

## Overview
InfraNodus is a text network visualisation tool that transforms textual data into interactive network graphs. It specialises in identifying topics, revealing structural gaps in discourse, and detecting emerging patterns in text using network science and AI.

**Note**: InfraNodus does not have comprehensive public API documentation available via Context7. This documentation is based on the tool's publicly known capabilities and interface.

## Core Capabilities

### Text Network Analysis
- **Topic Detection**: Automatically identifies main themes in text
- **Structural Gap Analysis**: Finds missing connections between topics
- **Influence Metrics**: Measures concept importance (betweenness centrality)
- **Cluster Detection**: Groups related concepts into communities

### Visualisation
- **Force-Directed Graph**: Interactive network layout
- **Node Sizing**: Based on word frequency or importance
- **Colour Coding**: Clusters represented by different colours
- **Zoom & Pan**: Navigate large text networks

### AI Integration
- **GPT-Powered Insights**: Generate text to bridge gaps in discourse
- **Sentiment Analysis**: Detect emotional tone in text networks
- **Topic Evolution**: Track how themes change over time

## Use Cases

### 1. Research & Ideation
- **Literature Review**: Visualise connections across academic papers
- **Brainstorming**: Identify unexplored angles in your thinking
- **Concept Mapping**: Create visual knowledge graphs from notes

**Example Workflow:**
1. Import research notes or articles
2. Generate network graph
3. Identify most influential concepts (high betweenness)
4. Explore structural gaps → Generate research questions

### 2. Content Strategy
- **SEO Keyword Research**: Find topic clusters and gaps in your content
- **Competitive Analysis**: Compare your content network to competitors'
- **Content Planning**: Identify underexplored topics to address

### 3. Social Media Analysis
- **Trend Detection**: Identify emerging themes in social conversations
- **Discourse Analysis**: Understand how communities discuss topics
- **Polarisation Detection**: Visualise echo chambers and bridging concepts

### 4. Knowledge Management
- **Personal Knowledge Graph**: Visualise Obsidian notes or Zettelkasten
- **Team Wiki Analysis**: Find information silos and missing connections
- **Documentation Gaps**: Identify undocumented areas in projects

## Key Features

### Structural Gap Detection

InfraNodus uses **betweenness centrality** to identify:
- **Hub Concepts**: Words connecting multiple topics (high betweenness)
- **Isolated Clusters**: Topics with weak connections to main discourse
- **Missing Links**: Potential connections to explore

**Interpreting Gaps:**
- Large gap between clusters → Opportunity for bridging ideas
- Isolated nodes → Underexplored or emerging concepts
- Dense clusters → Well-developed topics

### Topic Evolution (Temporal Analysis)

Track how discourse changes over time:
1. Import timestamped text (e.g., journal entries, tweets)
2. Analyse network evolution
3. Identify emerging vs declining topics
4. Detect shifts in conceptual focus

### AI-Powered Ideation

Use GPT integration to:
- **Generate Bridging Content**: AI suggests text connecting distant clusters
- **Expand Topics**: Get AI recommendations for developing weak areas
- **Summarise Networks**: Generate summaries of main themes

## Obsidian Integration

InfraNodus offers an Obsidian plugin for visualising your notes as networks:

### Setup
1. Install InfraNodus Obsidian plugin
2. Configure API key (requires InfraNodus account)
3. Select vault or folder to analyse

### Usage
- **Visualise Vault**: Transform entire vault into network graph
- **Note Connections**: See how notes relate via shared concepts
- **Discover Gaps**: Identify topics you haven't connected yet
- **Guided Writing**: Use gap analysis to decide what to write next

### Workflow Example
1. Write daily notes in Obsidian
2. Generate InfraNodus graph weekly
3. Identify emerging themes and gaps
4. Create new notes to bridge gaps
5. Repeat → Develop coherent knowledge system

## Visualisation Details

### Graph Elements

**Nodes (Words/Concepts):**
- **Size**: Proportional to frequency or importance
- **Colour**: Cluster membership (topics)
- **Position**: Force-directed layout (related concepts closer)

**Edges (Connections):**
- **Thickness**: Co-occurrence strength
- **Presence**: Words appearing together in text

### Metrics

**Betweenness Centrality:**
- Measures how often a word lies on shortest paths between other words
- High betweenness = hub concept connecting topics

**Clustering Coefficient:**
- Measures how densely connected a concept's neighbours are
- High clustering = concept part of tight-knit topic

**Community Detection:**
- Algorithm groups highly connected words into clusters
- Each cluster represents a topic or theme

## Practical Examples

### Example 1: Literature Review

**Input**: Abstracts from 20 research papers on AI ethics

**Analysis:**
- Identify main themes: "bias", "fairness", "transparency", "accountability"
- Detect gap: Weak connection between "transparency" and "accountability"
- Insight: Research opportunity → How does transparency enable accountability?

**Action**: Generate research question, write paper bridging gap

### Example 2: Content Strategy

**Input**: All blog posts from your website

**Analysis:**
- Topics: "tutorials" (dense), "case studies" (sparse), "best practices" (isolated)
- Gap: No connection between tutorials and best practices
- Insight: Readers learning from tutorials don't see how to apply best practices

**Action**: Write "Best Practices for Tutorial Topics" series

### Example 3: Personal Knowledge Management

**Input**: 6 months of Obsidian daily notes

**Analysis:**
- Clusters: "work projects", "reading", "health", "personal goals"
- Gap: "reading" cluster disconnected from "work projects"
- Insight: You're not applying book insights to work

**Action**: Create "Applied Reading Notes" linking books to work challenges

## Limitations & Considerations

### Data Privacy
- **Cloud-Based**: InfraNodus processes text on their servers
- **Sensitive Data**: Avoid uploading confidential information without reviewing terms
- **Local Alternative**: Consider self-hosted network analysis tools (Gephi, Cytoscape) for sensitive data

### Language Support
- **English-Optimised**: Best results with English text
- **Multilingual**: Supports other languages but with varying quality
- **Technical Text**: Works well with domain-specific terminology

### Graph Size
- **Optimal Range**: 50-5000 words for clear visualisation
- **Too Small**: Limited insights, sparse graph
- **Too Large**: Cluttered visualisation, difficult to interpret

## Alternatives & Complementary Tools

### Similar Tools
- **Gephi**: Open-source network visualisation (requires manual data prep)
- **Obsidian Graph View**: Built-in note connection visualisation (link-based, not text analysis)
- **Roam Research**: Bidirectional linking (manual, not AI-driven)
- **VOSviewer**: Academic bibliometric network analysis

### Integration Stack
- **Obsidian**: Note-taking → InfraNodus for gap analysis
- **Zotero/Mendeley**: Reference management → Export abstracts to InfraNodus
- **Twitter API**: Social listening → InfraNodus for trend detection
- **Google Sheets**: Collect text data → Import to InfraNodus for analysis

## Best Practices

1. **Clean Input Text**: Remove boilerplate, headers, navigation text
2. **Consistent Terminology**: Standardise synonyms before analysis (e.g., "AI" vs "artificial intelligence")
3. **Iterative Refinement**: Generate graph → Remove noise terms → Regenerate
4. **Combine Methods**: Use InfraNodus gap analysis + manual review for insights
5. **Temporal Analysis**: Compare networks over time to track conceptual evolution
6. **Export Data**: Save network metrics for further analysis in R/Python
7. **Share Graphs**: Use InfraNodus sharing features for collaborative analysis

## Resources

- **Website**: https://infranodus.com/
- **Tutorial Videos**: https://www.youtube.com/c/InfraNodus
- **Academic Paper**: Paranyushkin, D. (2019). "InfraNodus: Generating Insight Using Text Network Analysis"
- **Obsidian Plugin**: Search "InfraNodus" in Obsidian Community Plugins
- **Support Forum**: https://infranodus.com/community

---

**Note**: For detailed API documentation, feature updates, or specific implementation guidance, please refer to the official InfraNodus website or contact their support team directly.






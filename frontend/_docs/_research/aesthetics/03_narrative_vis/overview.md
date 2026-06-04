# Narrative Visualization & Storytelling

## Motivating Goal
**To reveal the "Golden Thread" of the conversation—connecting key elements across time to show not just *what* was said, but *how* the narrative evolved.**
Standard graphs flatten time; we want to re-inject the temporal dimension to support storytelling and review.

## Insights & Concepts

### 1. The "Path of Attention"
**Concept:** A conversation is a journey through the graph.
**Application:**
- **Glowing Trail:** Visualize the sequence of activated nodes over the last $N$ minutes as a glowing path.
- **Fading History:** Older parts of the conversation shouldn't disappear, but they should visually recede (dimmer, less contrast), leaving the current topic in the spotlight.

### 2. Timeline Visualization
**Concept:** Linear time is a powerful organizing principle that graphs often ignore.
**Application:**
- **The "Scrubber":** A UI element (like a video player) that lets users replay the growth of the graph. "Show me the state of the mind map at minute 15."
- **Narrative Arcs:** Visualizing the intensity or density of new information over time (e.g., a sparkline showing "Idea Velocity").

### 3. Storytelling Layers
**Concept:** Different users need different levels of detail.
**Application:**
- **The "Sankey" View:** A flow diagram showing how major themes transitioned into one another (e.g., Topic A -> Topic B -> Topic C).
- **Annotated Moments:** Automatically detecting "Aha!" moments or pivots in the conversation and marking them on the timeline.

## References
- **XKCD "Movie Narrative Charts":** Famous visualization of character interactions over time.
- **Sankey Diagrams:** Flow charts showing the movement of quantity (or attention) between states.
- **Storytelling with Data (Cole Nussbaumer Knaflic):** Principles for communicating data effectively.


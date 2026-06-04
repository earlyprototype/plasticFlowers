# Obsidian Documentation

## Overview
Obsidian is a powerful, local-first knowledge base application built on Markdown files. It treats your notes as a "second brain," providing tools for bi-directional linking, graph visualisation, and flexible organisation whilst keeping your data stored locally on your device.

## Core Concepts

### Local-First Philosophy
- **Plain Text Files**: All notes stored as `.md` (Markdown) files
- **No Vendor Lock-In**: Files accessible via any text editor
- **Vault**: A folder on your computer containing your notes
- **Portable**: Sync via Git, Dropbox, iCloud, or Obsidian Sync

### Bi-Directional Linking
- **Internal Links**: `[[Note Title]]` creates/links to notes
- **Backlinks**: See which notes link to current note
- **Graph View**: Visualise connections between notes

## Getting Started

### Installation
1. Download from https://obsidian.md
2. Install on Windows, macOS, Linux, iOS, or Android
3. Create or open a vault (folder)
4. Start writing!

### Creating Notes

```markdown
# My First Note

This is a note in Obsidian. I can link to [[Another Note]].

## Tags
#research #important

## Links
- [[Project Planning]]
- [[Meeting Notes 2025-01-15]]
```

### Linking

```markdown
<!-- Basic link -->
[[Target Note]]

<!-- Link with display text -->
[[Target Note|Custom Text]]

<!-- Link to heading -->
[[Target Note#Heading]]

<!-- Link to block -->
[[Target Note#^block-id]]
```

## Core Features

### Graph View

Visualise your vault as a network:
- **Nodes**: Individual notes
- **Edges**: Links between notes
- **Filters**: Show/hide tags, folders, or specific notes
- **Interactive**: Click to open notes, drag to rearrange

**Settings:**
- **Forces**: Adjust repulsion/attraction strength
- **Groups**: Colour-code by folder, tag, or path
- **Display**: Toggle labels, orphans, attachments

### Tags

```markdown
<!-- Inline tag -->
This is important #urgent

<!-- Nested tags -->
#projects/work/website

<!-- YAML frontmatter -->
---
tags:
  - research
  - literature-review
---
```

### Templates

**Create Template:**
```markdown
---
created: {{date}}
tags: [meeting]
---

# Meeting Notes - {{title}}

## Attendees
-

## Agenda
1.

## Action Items
- [ ]
```

**Use Template:**
1. Install "Templates" core plugin
2. Set templates folder
3. Insert template via command palette (`Ctrl/Cmd + P`)

### Daily Notes

Automatically create dated notes:
```markdown
---
date: 2025-12-21
---

# Daily Note - Saturday, 21 December 2025

## Tasks
- [ ] Review project status
- [ ] Plan next week

## Notes
- [[Meeting with Team]]
```

**Settings:**
- **Date Format**: `YYYY-MM-DD`, `DD-MM-YYYY`, custom
- **Template**: Use template for daily notes
- **Location**: Folder for daily notes

### Search

**Basic Search:**
```
term
```

**Search Operators:**
```
file:filename              # Files containing "filename"
path:folder/               # Files in folder
tag:#research              # Files tagged #research
line:(phrase here)         # Exact phrase
-excluded                  # Exclude term
term1 OR term2             # Either term
term1 AND term2            # Both terms
/regex[0-9]/              # Regular expression
```

## Advanced Features

### Dataview (Plugin)

Query your vault like a database:

```dataview
TABLE file.ctime AS "Created", tags
FROM #research
WHERE file.mtime > date(today) - dur(7 days)
SORT file.mtime DESC
```

**List Example:**
```dataview
LIST
FROM "Projects"
WHERE status = "active"
```

**Task Example:**
```dataview
TASK
WHERE !completed AND due < date(today)
```

### Canvas

Visual workspace for arranging notes, images, and embeds:
- **Create**: New file → Canvas
- **Add**: Drag notes, images, PDFs onto canvas
- **Connect**: Draw arrows between cards
- **Colour**: Organise with colour-coded cards

**Use Cases:**
- Project planning
- Mind mapping
- Presentation storyboards
- Research organisation

### Properties (Frontmatter)

Add metadata to notes:

```yaml
---
title: Project Planning
status: in-progress
priority: high
due: 2025-12-31
tags:
  - work
  - planning
---
```

**Property Types:**
- **Text**: Simple string
- **Number**: Integer or decimal
- **Date**: YYYY-MM-DD
- **Checkbox**: true/false
- **List**: Array of values
- **Link**: `[[Note]]`

**Query Properties:**
```dataview
TABLE status, priority, due
FROM "Projects"
WHERE status = "in-progress"
SORT due ASC
```

### Callouts

Highlight important information:

```markdown
> [!NOTE]
> This is a note callout.

> [!TIP]
> Helpful tip here.

> [!WARNING]
> Caution advised!

> [!DANGER]
> Critical warning!

> [!INFO]
> Additional information.
```

### Embeds

Embed content from other notes:

```markdown
<!-- Embed entire note -->
![[Note Title]]

<!-- Embed specific heading -->
![[Note Title#Heading]]

<!-- Embed block -->
![[Note Title#^block-id]]

<!-- Embed image -->
![[image.png|300]]

<!-- Embed PDF -->
![[document.pdf#page=5]]
```

### Canvas

## Community Plugins

### Popular Plugins

**Obsidian Git:**
- Automatic Git commits
- Push/pull from remote repository
- Version control for your vault

**Templater:**
- Advanced templating with JavaScript
- Dynamic content insertion
- Template variables and functions

**Kanban:**
- Task boards within Obsidian
- Drag-and-drop cards
- Markdown-based kanban boards

**Excalidraw:**
- Hand-drawn diagrams and sketches
- Integrated with Obsidian notes
- Link diagrams to notes

**Smart Connections:**
- AI-powered note recommendations
- Automatic link suggestions
- Semantic search

**Copilot:**
- AI assistant within Obsidian
- Chat with GPT models
- Generate and enhance content

### Installing Plugins

1. Settings → Community Plugins → Browse
2. Search for plugin
3. Install → Enable
4. Configure in plugin settings

## Workflows

### Zettelkasten Method

**Structure:**
- **Fleeting Notes**: Quick captures (Daily Notes)
- **Literature Notes**: Summarise sources
- **Permanent Notes**: Your own insights
- **Index Notes**: Entry points to topics

**Example:**
```
Vault/
├── 00 Inbox/           # Fleeting notes
├── 01 Literature/      # Source summaries
├── 02 Permanent/       # Core knowledge
└── 03 MOCs/            # Maps of Content (indexes)
```

### PARA Method

**Structure:**
- **Projects**: Active, time-bound work
- **Areas**: Ongoing responsibilities
- **Resources**: Reference materials
- **Archives**: Completed/inactive items

```
Vault/
├── Projects/
│   ├── Website Redesign/
│   └── Book Writing/
├── Areas/
│   ├── Health/
│   └── Career/
├── Resources/
│   ├── Articles/
│   └── Tutorials/
└── Archives/
    └── Old Projects/
```

### Personal Knowledge Management (PKM)

**Daily Workflow:**
1. **Capture**: Daily note for quick thoughts
2. **Process**: Review inbox, create permanent notes
3. **Organise**: Link notes, add tags/properties
4. **Review**: Graph view to find gaps and patterns

## Syncing

### Obsidian Sync (Official)
- **Paid Service**: £8/month
- **Features**: End-to-end encryption, version history, sync across devices
- **Setup**: Settings → Sync → Enable

### Alternative Sync Methods

**Git (Free):**
- Use Obsidian Git plugin
- Push to GitHub/GitLab
- Full version control

**Cloud Storage:**
- **Dropbox/OneDrive**: Works, but may cause sync conflicts
- **iCloud**: Good for Apple devices
- **Google Drive**: Use with caution (potential issues)

**Self-Hosted:**
- **Syncthing**: Peer-to-peer sync
- **Nextcloud**: Self-hosted cloud
- **rsync**: Manual sync via scripts

## Customisation

### Themes

1. Settings → Appearance → Themes → Manage
2. Browse community themes
3. Install and activate

**Popular Themes:**
- **Minimal**: Clean, customisable
- **Sanctum**: Elegant, focused
- **Things**: macOS-inspired
- **Atom**: Dark, developer-friendly

### CSS Snippets

Custom styling:

```css
/* .obsidian/snippets/custom.css */

/* Larger text */
.markdown-preview-view {
    font-size: 18px;
}

/* Coloured tags */
.tag[href="#urgent"] {
    background-color: #ff6b6b;
    color: white;
}
```

Enable: Settings → Appearance → CSS Snippets

### Hotkeys

Settings → Hotkeys → Search command → Assign key

**Useful Defaults:**
- `Ctrl/Cmd + P`: Command palette
- `Ctrl/Cmd + O`: Quick switcher (open note)
- `Ctrl/Cmd + N`: New note
- `Ctrl/Cmd + E`: Toggle edit/preview mode
- `Ctrl/Cmd + ,`: Settings
- `Ctrl/Cmd + \`: Toggle sidebar

## Mobile

### iOS/Android Features
- Full feature parity with desktop
- Touch gestures for navigation
- Mobile-specific toolbar
- Sync via Obsidian Sync or cloud storage

### Mobile Workflows
- **Quick Capture**: Use daily notes for quick thoughts
- **Voice Notes**: Dictate using device keyboard
- **Read Mode**: Preview on the go
- **Graph View**: Explore connections on mobile

## Best Practices

1. **Start Simple**: Don't over-organise initially; let structure emerge
2. **Link Liberally**: Create connections—Obsidian's power is in the graph
3. **Use Tags Sparingly**: Prefer links over tags for better connections
4. **Daily Notes**: Capture ideas immediately; process later
5. **Templates**: Standardise recurring note types
6. **Backups**: Sync or backup regularly (Git, cloud, external drive)
7. **Plain Markdown**: Avoid heavy plugin dependence for portability
8. **Review Regularly**: Use graph view to find orphaned notes and gaps

## Integration with Development

### Code Blocks

```python
def hello_world():
    print("Hello from Obsidian!")
```

**Supported:**
- Syntax highlighting for 100+ languages
- Live preview mode
- Copy button on hover

### API Documentation

Store API references as notes:

```markdown
# Neo4j Python Driver

## Installation
\```bash
pip install neo4j
\```

## Connection
\```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
\```

Related: [[Graph Databases]], [[Cypher Queries]]
```

### Project Documentation

**Structure:**
```
ProjectVault/
├── Architecture/
│   ├── System Design.md
│   └── Database Schema.md
├── API Reference/
│   ├── Endpoints.md
│   └── Authentication.md
├── Meetings/
│   └── 2025-12-21 Sprint Planning.md
└── Tasks/
    └── Current Sprint.md
```

## Resources

- **Website**: https://obsidian.md
- **Help Docs**: https://help.obsidian.md
- **Forum**: https://forum.obsidian.md
- **Discord**: https://discord.gg/obsidianmd
- **Plugin Directory**: https://obsidian.md/plugins
- **Theme Directory**: https://obsidian.md/themes






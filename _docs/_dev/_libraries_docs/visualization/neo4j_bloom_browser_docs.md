# Neo4j Bloom & Browser Documentation

## Overview
Neo4j provides powerful built-in tools for exploring and visualising graph data: **Neo4j Browser** (developer-focused query interface) and **Neo4j Bloom** (business user-friendly graph exploration). Both offer intuitive ways to interact with Neo4j databases without writing extensive code.

---

## Neo4j Browser

### What is Neo4j Browser?
Neo4j Browser is a web-based query workbench for developers and data engineers. It allows you to:
- Execute Cypher queries interactively
- Visualise query results as graphs or tables
- Manage database metadata
- View query performance statistics

### Accessing Browser
- **Desktop**: Included with Neo4j Desktop, opens automatically
- **Server**: Access via `http://localhost:7474` (default port)
- **Aura**: Available in Neo4j Aura cloud console

### Basic Usage

#### Connect to Database

```
:server connect
```

Enter credentials:
- **URI**: `bolt://localhost:7687` (or Aura URI)
- **Username**: `neo4j`
- **Password**: Your database password

#### Execute Queries

```cypher
// Find all nodes
MATCH (n) RETURN n LIMIT 25;

// Find specific pattern
MATCH (p:Person)-[:KNOWS]->(friend:Person)
WHERE p.name = 'Alice'
RETURN p, friend;

// Aggregation query
MATCH (p:Product)-[:BELONGS_TO]->(c:Category)
RETURN c.name, count(p) AS productCount
ORDER BY productCount DESC;
```

#### Graph Visualisation

Browser automatically renders nodes and relationships from `RETURN` statements:

```cypher
// Visualise community
MATCH path = (a:Person {name: 'Alice'})-[:KNOWS*1..2]-(friend)
RETURN path;
```

**Visualisation Controls:**
- **Pan**: Click and drag background
- **Zoom**: Mouse wheel or pinch
- **Expand Node**: Click node to see relationships
- **Inspect**: Click to view properties in sidebar

#### Table View

```cypher
// View as table
MATCH (p:Product)
RETURN p.name, p.price, p.category
ORDER BY p.price DESC
LIMIT 10;
```

Toggle between graph/table view using icons at top-right of result pane.

### Browser Commands

#### System Commands

```cypher
// Help
:help

// Clear frame
:clear

// List databases
SHOW DATABASES;

// Use specific database
:use myDatabase

// Schema information
CALL db.schema.visualization();

// Constraints and indexes
SHOW CONSTRAINTS;
SHOW INDEXES;
```

#### Styling

```cypher
// Set node caption
:style {
  "node": {
    "caption": "name"
  }
}

// Customise node colour
// Click node → Settings icon → Change colour
```

Browser remembers style preferences per label.

### Query History & Favourites

- **History**: Access via clock icon (left sidebar)
- **Favourites**: Star icon to save frequently used queries
- **Export/Import**: Share query collections via JSON

### Performance Analysis

```cypher
// Profile query execution
PROFILE MATCH (p:Person)-[:KNOWS*2..3]-(friend)
WHERE p.name = 'Alice'
RETURN friend;

// Explain query plan
EXPLAIN MATCH (p:Person)-[:KNOWS]->(friend)
RETURN p, friend;
```

Results show:
- **DB Hits**: Database operations performed
- **Rows**: Number of results
- **Time**: Execution time
- **Plan**: Visual query execution plan

### Import/Export Data

```cypher
// Import CSV
LOAD CSV WITH HEADERS FROM 'file:///people.csv' AS row
CREATE (p:Person {name: row.name, age: toInteger(row.age)});

// Export query results
// Use Download button in result frame
```

---

## Neo4j Bloom

### What is Neo4j Bloom?
Neo4j Bloom is a code-free graph exploration tool designed for business users, analysts, and non-technical stakeholders. It provides:
- Natural language search
- Point-and-click graph exploration
- Visual pattern discovery
- Shareable perspectives (views)

### Accessing Bloom
- **Desktop**: Install via Graph Apps tab
- **Aura**: Available in Neo4j Aura Professional/Enterprise
- **Server**: Requires Neo4j Bloom license

### Key Features

#### 1. Natural Language Search

Type queries in plain English:

```
Find Person named Alice
Show me all Products under £50
Alice's friends who work at Google
Companies in London with more than 100 employees
```

Bloom translates these into Cypher queries automatically.

#### 2. Point-and-Click Exploration

- **Expand Node**: Double-click node to reveal connected nodes
- **Path Finding**: Right-click → Find paths between nodes
- **Filter Results**: Use search bar filters (sliders, dropdowns)
- **Dismiss/Hide**: Right-click node → Hide to simplify view

#### 3. Search Phrases

Create custom search templates:

**Example:**
- **Phrase**: "Products by {category}"
- **Cypher**: `MATCH (p:Product)-[:BELONGS_TO]->(c:Category {name: $category}) RETURN p`

Users can then type: `Products by Electronics`

#### 4. Perspectives

Perspectives define what users see and search:

**Creating a Perspective:**
1. Open Perspective drawer (left sidebar)
2. Click "Edit Mode"
3. Define:
   - **Node Labels**: Which labels to include
   - **Relationship Types**: Which relationships to display
   - **Search Phrases**: Custom search templates
   - **Styling**: Node colours, sizes, icons

**Example Perspective: "Sales Analysis"**
- Node Labels: `Customer`, `Product`, `Order`
- Relationships: `PURCHASED`, `CONTAINS`
- Search Phrases: "Customer who bought {product}", "Top customers"

#### 5. Scene Actions

Automate complex queries with Scene Actions:

**Example Action: "Find Influencers"**
```cypher
MATCH (p:Person)-[:FOLLOWS]->(influencer:Person)
WITH influencer, count(p) AS followers
WHERE followers > 1000
RETURN influencer
ORDER BY followers DESC
LIMIT 10
```

Users click "Find Influencers" button → Graph updates automatically.

### Styling & Visualisation

#### Node Styling

Configure in Perspective Editor:
- **Caption**: Display property (e.g., `name`)
- **Size**: Based on property value (e.g., `revenue`)
- **Colour**: By property or label
- **Icon**: Choose from library or upload custom

**Example:**
- `Person` nodes: Blue circle, caption = `name`
- `Company` nodes: Red square, caption = `name`, size = `employeeCount`

#### Relationship Styling

- **Caption**: Show relationship property
- **Thickness**: Based on weight/value
- **Colour**: By relationship type

### Rule-Based Styling

Apply conditional styling:

**Example:**
- **Rule**: If `Person.age > 30` → Green node
- **Rule**: If `Product.price > 100` → Large node

### Sharing & Collaboration

#### Share Scene
1. Click "Share" button (top-right)
2. Generate shareable link
3. Recipients view read-only graph snapshot

#### Export Perspective
1. Perspective drawer → Export
2. Share JSON file with team
3. Import via "Import Perspective"

### Advanced Features

#### Pattern Search

Visual query builder:
1. Click "Pattern Search" (left sidebar)
2. Drag labels to canvas
3. Draw relationships
4. Add filters (properties, constraints)
5. Execute → Results appear on graph

**Example Pattern:**
```
(Person)-[:WORKS_AT]->(Company)-[:LOCATED_IN]->(City {name: "London"})
```

#### Path Finding

Find connections between nodes:
1. Right-click node A → "Set as start"
2. Right-click node B → "Find paths to here"
3. Configure:
   - **Max hops**: Relationship depth
   - **Relationship types**: Filter path types
4. View all paths

#### Time-Based Analysis

Animate graph changes over time:
1. Define time property (e.g., `createdDate`)
2. Enable timeline slider
3. Scrub through timeline to see graph evolution

### Use Cases

#### Fraud Detection
- Search: "Accounts with shared phone number"
- Expand suspicious clusters
- Flag anomalous patterns

#### Customer 360
- Search: "Customer {name}"
- Explore purchase history, interactions, support tickets
- Identify churn risk

#### Network Analysis
- Pattern: `(Person)-[:KNOWS*2..3]-(Person)`
- Find communities via visual exploration
- Identify key connectors

---

## Browser vs Bloom Comparison

| Feature | Neo4j Browser | Neo4j Bloom |
|---------|--------------|-------------|
| **Target Users** | Developers, DBAs | Business users, analysts |
| **Query Method** | Cypher queries | Natural language + clicks |
| **Visualisation** | Auto-layout | Manual layout, persistent scenes |
| **Customisation** | Limited styling | Rich styling + perspectives |
| **Learning Curve** | Moderate (requires Cypher) | Low (no code required) |
| **Use Case** | Development, debugging | Exploration, presentations |
| **Performance** | Query-focused | Exploration-focused |

---

## Best Practices

### Neo4j Browser
1. **Use `LIMIT`**: Always limit results to avoid overwhelming visualisation
2. **Profile Queries**: Use `PROFILE` to optimise slow queries
3. **Save Favourites**: Bookmark frequently used queries
4. **Schema First**: Run `CALL db.schema.visualization()` to understand data model
5. **Keyboard Shortcuts**: `Ctrl+Enter` to execute, `Ctrl+↑/↓` for history

### Neo4j Bloom
1. **Design Perspectives**: Create role-specific perspectives (sales, fraud, etc.)
2. **Search Phrases**: Pre-build common queries for non-technical users
3. **Styling Rules**: Use size/colour to encode important properties
4. **Scene Management**: Save scenes for presentations and reports
5. **Limit Scope**: Include only necessary labels/relationships in perspective
6. **Training**: Provide search phrase examples for users

---

## Resources

### Neo4j Browser
- **Documentation**: https://neo4j.com/docs/browser-manual/current/
- **Cypher Manual**: https://neo4j.com/docs/cypher-manual/current/

### Neo4j Bloom
- **Documentation**: https://neo4j.com/docs/bloom-user-guide/current/
- **Tutorial Videos**: https://neo4j.com/videos/
- **Bloom Licensing**: Contact Neo4j sales for enterprise features






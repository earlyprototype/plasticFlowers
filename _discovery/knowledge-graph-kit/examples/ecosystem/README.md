# Louth Manufacturing Digitalization Ecosystem Example

A comprehensive demonstration of **capability-need matching** in a real-world manufacturing ecosystem.

## Overview

This example maps the County Louth (Ireland) manufacturing ecosystem, demonstrating:
- **Realized relationships** (what IS happening)
- **Potential relationships** (what COULD happen)
- **Capability-need matching** for business intelligence
- **Gap identification** for intervention opportunities

Based on the comprehensive research report: `Louth Manufacturing Digitalization Ecosystem Analysis.md`

## What This Example Demonstrates

### 1. Enhanced Entity Fields for Business Intelligence

Organizations include rich business metrics:

```python
'metrics': {
    'employees': 380,
    'revenue': 75000000,
    'growth_rate': '50% YoY'
}

'digital_profile': {
    'maturity_level': 'high-strategic-agility',
    'transformation_stage': 'scaling-hyper-growth',
    'projected_needs': {
        'near_term': [...],
        'medium_term': [...]
    }
}

'strategic_position': {
    'opportunities': [...],
    'threats': [...],
    'competitive_advantages': [...]
}
```

### 2. Capability-Need Matching Pattern

**Capabilities as first-class entities:**
```python
{
    'id': 'industrial-robotics-training',
    'label': 'Industrial Robotics Training',
    'type': 'capability'
}
```

**Organizations declare needs:**
```python
'needs_unmet': [
    'industrial-robotics-training',
    'skilled-welders-80-positions',
    'automation-engineers'
]
```

**Matching via relationships:**
```python
# Provider → Capability
AMTCE --[provides]--> industrial-robotics-training

# Consumer → Capability
Suretank --[needs-from]--> industrial-robotics-training
MSD --[needs-from]--> industrial-robotics-training

# Opportunity identification
AMTCE --[could-provide-to]--> Suretank
```

### 3. Potential vs. Realized Relationships

**Realized (what IS):**
- `provides-to`, `funds`, `supplies`, `partners-with`

**Potential (what COULD BE):**
- `needs-from` - Active demand signal
- `could-provide-to` - Identified match opportunity
- `could-partner-with` - Potential synergy
- `gap` - Missing capability in ecosystem

## Quick Start

### 1. Initialize the Graph

```bash
cd examples/ecosystem
python init.py
```

This creates the directory structure:
```
examples/ecosystem/
├── _data/
│   └── entities.json
├── insights/
├── output/
├── config.yaml
├── viewer.html
└── server.py
```

### 2. Build the Louth Ecosystem

```bash
python build_louth_ecosystem.py
```

This populates the graph with:
- ✅ 20+ organizations (MSD, National Pen, Suretank, etc.)
- ✅ 4 key capabilities (robotics training, regulated AI, etc.)
- ✅ 3 support infrastructure entities (AMTCE, RSRC, FabLab)
- ✅ 2 government agencies
- ✅ 1 policy framework
- ✅ 1 research insight document
- ✅ 50+ relationships (realized and potential)

### 3. Visualize & Explore

```bash
python server.py
```

Then open: http://localhost:8000

## Key Entities in the Graph

### The "Transformation Triangle" (Support Infrastructure)

1. **AMTCE** - Advanced Manufacturing Training Centre
   - Provides: Industrial robotics training, IIoT training, additive manufacturing
   - €62.4M investment, opened 2021

2. **DkIT-RSRC** - Regulated Software Research Centre
   - Provides: Regulated AI research, medical device compliance
   - World-class capability for trustworthy AI

3. **Creative Spark FabLab**
   - Provides: Digital prototyping access for SMEs
   - 3D printing, laser cutting, CNC milling

### Anchor Manufacturers

**Digital-Native:**
- **MSD Dundalk** - €500M vaccine facility, 350 employees
- **National Pen** - Mass customisation platform, €91M revenue
- **Hilton Foods** - Automated food processing with proprietary Greenchain platform

**High-Growth Indigenous:**
- **Suretank** - €75M revenue, 50% YoY growth, modular engineering
- **Bellurgan Precision** - High-precision CNC, Medtronic partner

**Brownfield Opportunity:**
- **Boyne Valley Group** - Iconic Irish FMCG brands, digitalization needed
- **M+L Manufacturing** - Mission-critical switchgear, needs smart product development

### Case Study: The "BD Effect"
- **Becton Dickinson Drogheda** - 60-year legacy facility
- Despite €62M investment in 2021, announced closure in 2024
- Demonstrates: Digital transformation is survival imperative, not optional

## Use Cases for Different Personas

### For Business Analysts 📊

**Query: "What's the market size for industrial robotics training?"**

Filter relationships by type: `needs-from` + target: `industrial-robotics-training`

Results:
- MSD: Needs for 150 employees
- Suretank: Needs for 80 employees
- National Pen: Needs for fulfilment automation

**Total addressable demand:** 230+ workers + ongoing upskilling

### For Development Officers 🎯

**Query: "Where should we invest next?"**

1. Filter by entity type: `capability` + relationship: `gap`
2. Results show:
   - IIoT Product Development Gap (M+L, Suretank need)
   - Brownfield Digitalization Consulting Gap (Boyne Valley needs)

**Intervention opportunity:** Create IIoT R&D programme or attract consulting firm

### For Founders Researching Markets 🚀

**Query: "Who are the potential customers and what do they need?"**

1. Filter organizations by `digital_profile.maturity_level`: `low-medium-brownfield`
2. Results: Boyne Valley Group, traditional SMEs
3. Check `needs_unmet`: ERP, WMS, SCADA, Logistics 4.0
4. Check `strategic_position.threats`: Pilot trap, competition from digital-first firms

**Market entry strategy:** Position as brownfield digitalization specialist, help avoid pilot trap

### For Supply Chain Managers 🔗

**Query: "Who can supply precision components to MSD?"**

1. Find MSD entity
2. Check `needs_unmet`: `precision-cnc-machining`
3. Query for entities offering that capability
4. Result: **Bellurgan Precision** (proven MedTech supplier, Medtronic partner)

**Action:** Facilitate introduction between MSD procurement and Bellurgan

## Exploration Queries

Once the graph is loaded in the viewer:

### View Unmet Needs
Filter: Relationship type = `needs-from`
- See all active demand signals in the ecosystem

### View Matching Opportunities
Filter: Relationship type = `could-provide-to`
- See identified but unrealized partnerships

### View Ecosystem Gaps
Filter: Relationship type = `gap`
- See missing capabilities requiring intervention

### View High-Growth Companies
Filter: Entity field contains `growth_rate`
- Suretank (50% YoY)

### View Digital-Native vs. Brownfield
- Digital-native: MSD, National Pen, Hilton Foods
- Brownfield: Boyne Valley, M+L Manufacturing

## Key Insights from the Graph

1. **Complete Ecosystem:** Louth has rare FDI-Indigenous-Support "closed loop"
   - MSD (FDI) lands → needs components → Bellurgan (Indigenous) ready to supply
   - MSD needs AI validation → RSRC (Support) provides world-class capability
   - MSD needs 150 staff → AMTCE (Support) provides training

2. **Matched Opportunities:**
   - AMTCE ↔ Suretank: Training for 80 new hires
   - RSRC ↔ MSD: AI validation for regulated manufacturing
   - Bellurgan ↔ MSD: Local precision supply chain

3. **Gaps Requiring Intervention:**
   - IIoT product development (M+L, Suretank need to embed sensors)
   - Brownfield consulting (Boyne Valley needs structured transformation)

4. **The BD Effect:**
   - Legacy (60 years) + Recent investment (€62M) ≠ Protection
   - Digital transformation is existential, not optional
   - Every manufacturer faces global consolidation pressure

## Files in This Example

- `config.yaml` - Enhanced ecosystem template configuration
- `build_louth_ecosystem.py` - Script to build the complete graph
- `Louth Manufacturing Digitalization Ecosystem Analysis.md` - Full research report (122 citations)
- `README.md` - This file
- `_data/entities.json` - Graph data (generated by build script)

## Extending This Example

### Add More Manufacturers
```python
gm.add_entity('primary', {
    'id': 'your-company',
    'label': 'Your Company Name',
    'type': 'organization',
    'needs_unmet': [...],
    'capabilities_offered': [...],
    'digital_profile': {...}
})
```

### Add New Capabilities
```python
gm.add_entity('primary', {
    'id': 'your-capability',
    'label': 'Your Capability',
    'type': 'capability',
    'description': 'What this enables'
})
```

### Match Needs to Capabilities
```python
# Declare need
gm.add_relationship('company-id', 'capability-id', 'needs-from')

# Declare provision
gm.add_relationship('provider-id', 'capability-id', 'provides')

# Identify opportunity
gm.add_relationship('provider-id', 'company-id', 'could-provide-to')
```

## Technical Notes

### Entity Types Used
- `organization` - Companies, institutions, agencies
- `capability` - Skills, services, technologies (as matchable entities)
- `platform` - Digital platforms (FabLab)
- `policy` - Regulatory frameworks, government policy

### Relationship Types Used

**Realized:**
- `provides`, `funds`, `enables`, `supplies`, `partners-with`

**Potential:**
- `needs-from` - Active demand
- `could-provide-to` - Identified match
- `could-partner-with` - Synergy opportunity
- `gap` - Missing capability

### Data Quality
- All metrics sourced from the research report with 122 citations
- Organizations verified through public records, company websites, government reports
- Digital maturity assessments based on technology stack, transformation stage, and industry benchmarks

## Credits

**Research Report:** "An Analytical Mapping of the County Louth Manufacturing Ecosystem: Industrial Clusters, Key Entrants, and Digital Transformation Readiness"

**Data Sources:** IDA Ireland, Enterprise Ireland, company financial reports, industry publications (see full report for citations)

**Template Design:** Enhanced ecosystem template with business intelligence fields

---

For questions or issues, refer to the main project README or the template documentation at `templates/ecosystem/README.md`.








# Ecosystem Mapping Template

Knowledge graph optimized for mapping stakeholder ecosystems, organizations, resources, and value flows.

## Entities

### Elements (Primary)
Organizations, platforms, resources, processes, capabilities, and market forces in your ecosystem.

**Types:**
- organization (companies, institutions, agencies)
- platform (digital platforms, marketplaces)
- resource (funding, knowledge, infrastructure)
- process (workflows, methodologies, practices)
- capability (skills, competencies, functions)
- value-stream (value creation/delivery chains)
- market (market segments, sectors)
- technology (key technologies in ecosystem)
- policy (regulations, policies, standards)
- infrastructure (physical/digital infrastructure)

**Fields:**
- `id`: Unique identifier
- `label`: Display name
- `type`: Element type
- `description`: What it is/does
- `sector`: Industry sector or domain
- `maturity`: emerging | developing | mature | declining
- `scale`: local | regional | national | global
- `source_insights`: Insight IDs that mention this
- `related_to`: Related element IDs
- `components`: Sub-element IDs
- `location`: Geographic location (town, business_park, coordinates, logistics_access)
- `metrics`: Business metrics (revenue, employees, investment_received, year_founded)
- `digital_profile`: Digital transformation status (maturity_level, technologies_used, transformation_stage, projected_needs)
- `strategic_position`: Strategic analysis (threats, opportunities, competitive_advantages)
- `capabilities_offered`: Services/products/expertise provided
- `needs_unmet`: Current gaps and unfulfilled requirements
- `target_customers`: Who needs what this entity offers

### Stakeholders (Contributors)
People, organizations, institutions, communities involved in ecosystem.

**Fields:**
- `id`: Unique identifier
- `name`: Stakeholder name
- `type`: individual | organization | institution | community | government
- `role`: Role in ecosystem
- `influence_level`: high | medium | low
- `interests`: Key interests and motivations
- `key_elements`: Element IDs they're involved with
- `mentioned_in`: Insight IDs

### Insights (Sources)
Research findings, interviews, observations, reports about the ecosystem.

**Fields:**
- `id`: Unique identifier
- `title`: Insight title
- `source_type`: interview | report | survey | observation | workshop | secondary-research
- `date`: Date collected/published
- `authors`: Who generated the insight
- `key_elements`: Elements mentioned
- `key_findings`: Main findings (array)
- `references`: Other insight IDs
- `status`: validated | preliminary | needs-verification

## Relationships

### Realized Relationships (What IS)
- `provides-to`: Element A provides value/resource to B
- `receives-from`: Element A receives from B
- `influences`: Element A influences B
- `depends-on`: Element A depends on B
- `competes-with`: Competition relationship
- `partners-with`: Partnership/collaboration
- `funds`: Provides funding
- `regulates`: Regulatory relationship
- `enables`: Element A enables B's operation
- `constrains`: Element A constrains B
- `collaborates-with`: Active collaboration
- `supplies`: Supply chain relationship
- `consumes`: Consumption relationship

### Potential Relationships (What COULD BE)
- `needs-from`: Element A actively needs capability/service from B
- `could-provide-to`: Element A has capability that B might need
- `could-partner-with`: Potential synergy identified but not realized
- `gap`: Missing capability or unfulfilled need in ecosystem
- `capability-overlap`: Potential competition or collaboration area

## Use Cases

### 1. Stakeholder Mapping
Identify all stakeholders and their relationships.

### 2. Power Analysis
Understand influence and power structures.

### 3. Value Flow Mapping
Trace how value flows through ecosystem.

### 4. Gap Analysis
Find missing elements or relationships.

### 5. Opportunity Identification
Spot collaboration or intervention opportunities.

### 6. Risk Assessment
Identify dependencies and vulnerabilities.

### 7. Capability-Need Matching (NEW)
Match unmet needs with available capabilities in the ecosystem.

## Example Usage

### Basic Example: Tech Startup Ecosystem

```python
from core.graph_manager import GraphManager

gm = GraphManager('config.yaml')

# Add organization with enhanced fields
gm.add_entity('primary', {
    'id': 'startup-accelerator',
    'label': 'Tech Accelerator Inc',
    'type': 'organization',
    'description': 'Provides funding and mentorship to early-stage startups',
    'sector': 'Technology',
    'maturity': 'mature',
    'scale': 'national',
    'location': {
        'town': 'Tech City',
        'business_park': 'Innovation Quarter'
    },
    'metrics': {
        'employees': 25,
        'year_founded': 2015,
        'startups_supported': 150
    },
    'capabilities_offered': [
        'seed-funding',
        'mentorship',
        'workspace',
        'network-access'
    ],
    'source_insights': ['interview-001', 'report-tech-ecosystem']
})

# Add funding resource
gm.add_entity('primary', {
    'id': 'seed-funding-pool',
    'label': 'Seed Funding Pool',
    'type': 'resource',
    'description': '£2M annual funding for startups',
    'sector': 'Finance',
    'maturity': 'mature',
    'scale': 'regional'
})

# Add platform
gm.add_entity('primary', {
    'id': 'innovation-hub',
    'label': 'Regional Innovation Hub',
    'type': 'platform',
    'description': 'Physical space and community for entrepreneurs',
    'sector': 'Technology',
    'maturity': 'developing',
    'scale': 'regional',
    'components': ['coworking-space', 'event-space', 'mentorship-program']
})

# Add stakeholder
gm.add_entity('contributors', {
    'id': 'angel-investor-jane',
    'name': 'Jane Smith',
    'type': 'individual',
    'role': 'Angel Investor',
    'influence_level': 'high',
    'interests': ['AI startups', 'SaaS', 'Deep tech'],
    'key_elements': ['startup-accelerator', 'seed-funding-pool']
})

# Add policy
gm.add_entity('primary', {
    'id': 'innovation-grant-policy',
    'label': 'Government Innovation Grant Scheme',
    'type': 'policy',
    'description': 'Tax incentives and grants for R&D',
    'sector': 'Policy',
    'maturity': 'mature',
    'scale': 'national'
})

# Add insight
gm.add_entity('sources', {
    'id': 'interview-001',
    'title': 'Interview: Tech Accelerator Founders',
    'source_type': 'interview',
    'date': '2024-10-15',
    'authors': ['Research Team'],
    'key_elements': ['startup-accelerator', 'innovation-hub'],
    'key_findings': [
        'Funding gap for pre-seed stage',
        'Need for more technical mentors',
        'Strong demand for workspace'
    ],
    'status': 'validated'
})

# Add relationships
gm.add_relationship('startup-accelerator', 'seed-funding-pool', 'provides-to',
                   description='Distributes seed funding to startups')

gm.add_relationship('angel-investor-jane', 'seed-funding-pool', 'funds',
                   description='Contributes to funding pool')

gm.add_relationship('innovation-grant-policy', 'startup-accelerator', 'enables',
                   description='Government policy enables accelerator operations')

gm.add_relationship('startup-accelerator', 'innovation-hub', 'partners-with',
                   description='Collaboration on space and events')

gm.save()
```

### Advanced Example: Manufacturing Ecosystem with Capability Matching

```python
from core.graph_manager import GraphManager

gm = GraphManager('config.yaml')

# Add a capability as a first-class entity
gm.add_entity('primary', {
    'id': 'industrial-robotics-training',
    'label': 'Industrial Robotics Training',
    'type': 'capability',
    'description': 'Hands-on training in 6-axis robots, cobots, vision systems, and robot welding',
    'sector': 'Skills Development',
    'maturity': 'mature',
    'scale': 'regional',
    'location': {'town': 'Dundalk'}
})

# Add training provider
gm.add_entity('primary', {
    'id': 'amtce',
    'label': 'Advanced Manufacturing Training Centre',
    'type': 'organization',
    'description': 'State-of-the-art training facility for Industry 4.0 skills',
    'sector': 'Education & Training',
    'maturity': 'developing',
    'scale': 'national',
    'location': {
        'town': 'Dundalk',
        'business_park': 'DkIT Campus'
    },
    'metrics': {
        'investment_received': 62400000,
        'year_founded': 2021
    },
    'capabilities_offered': [
        'industrial-robotics-training',
        'iiot-training',
        'additive-manufacturing-training',
        'cyber-security-training'
    ],
    'target_customers': ['pharma', 'food-processing', 'engineering']
})

# Add manufacturer with unmet needs
gm.add_entity('primary', {
    'id': 'suretank',
    'label': 'Suretank',
    'type': 'organization',
    'description': 'Modular engineering solutions for energy, marine, and industrial sectors',
    'sector': 'Manufacturing - Heavy Engineering',
    'maturity': 'mature',
    'scale': 'global',
    'location': {
        'town': 'Dunleer',
        'coordinates': '53.8°N, 6.4°W',
        'logistics_access': 'M1 corridor access'
    },
    'metrics': {
        'employees': 380,
        'revenue': 75000000,
        'year_founded': 1984,
        'growth_rate': '50% YoY'
    },
    'needs_unmet': [
        'industrial-robotics-training',
        'skilled-welders',
        'automation-engineers'
    ],
    'digital_profile': {
        'maturity_level': 'high-agile',
        'transformation_stage': 'scaling',
        'technologies_used': ['advanced-cad-cam', 'project-management-software'],
        'projected_needs': {
            'near_term': ['robotic-welding', 'enhanced-cad-cam'],
            'medium_term': ['iiot-integration', 'digital-twin-simulation']
        }
    },
    'strategic_position': {
        'opportunities': [
            'Pivot to offshore wind, data centres, pharma markets',
            'Integrate IIoT sensors into modular solutions'
        ],
        'threats': [
            'Managing hyper-growth (50% in one year)',
            'Skills shortage in tight labour market'
        ]
    }
})

# Add digital-native manufacturer
gm.add_entity('primary', {
    'id': 'msd-dundalk',
    'label': 'MSD (Merck & Co.) Dundalk',
    'type': 'organization',
    'description': 'State-of-the-art vaccine manufacturing facility with drug substance and drug product capabilities',
    'sector': 'Biopharmaceutical',
    'maturity': 'mature',
    'scale': 'global',
    'location': {
        'town': 'Dundalk',
        'business_park': 'IDA Business Park'
    },
    'metrics': {
        'employees': 350,
        'investment_received': 500000000,
        'facility_size_sqm': 15520
    },
    'needs_unmet': [
        'industrial-robotics-training',
        'regulated-ai-expertise',
        'precision-machined-components'
    ],
    'digital_profile': {
        'maturity_level': 'exceptional-digital-native',
        'transformation_stage': 'integration',
        'technologies_used': [
            'single-use-bioreactors',
            'advanced-automation',
            'mes-systems',
            'digital-twins'
        ],
        'projected_needs': {
            'near_term': ['systems-integration', 'data-migration', 'cybersecurity-hardening'],
            'medium_term': ['ai-ml-qc-optimization', 'predictive-analytics']
        }
    }
})

# Add R&D centre
gm.add_entity('primary', {
    'id': 'dkit-rsrc',
    'label': 'DkIT Regulated Software Research Centre',
    'type': 'organization',
    'description': 'Research centre focused on safe, ethical, trustworthy AI in medical devices',
    'sector': 'Research & Development',
    'maturity': 'mature',
    'scale': 'national',
    'location': {'town': 'Dundalk'},
    'capabilities_offered': [
        'regulated-ai-expertise',
        'medical-device-software-compliance',
        'cybersecurity-research',
        'biopharma-graduates'
    ],
    'target_customers': ['medtech', 'biopharma']
})

# REALIZED relationships
gm.add_relationship('amtce', 'industrial-robotics-training', 'provides',
                   description='AMTCE delivers robotics training programmes')

# POTENTIAL relationships (capability-need matching)
gm.add_relationship('suretank', 'industrial-robotics-training', 'needs-from',
                   description='Needs robotics training for 80 new hires and productivity boost')

gm.add_relationship('msd-dundalk', 'industrial-robotics-training', 'needs-from',
                   description='Needs training for 150 new employees')

gm.add_relationship('msd-dundalk', 'regulated-ai-expertise', 'needs-from',
                   description='Needs AI validation for QC labs and process optimization')

gm.add_relationship('dkit-rsrc', 'regulated-ai-expertise', 'provides',
                   description='Provides world-class regulated AI research')

# Identify MATCHED opportunities
gm.add_relationship('amtce', 'suretank', 'could-provide-to',
                   description='AMTCE can train Suretank workforce in robotic welding')

gm.add_relationship('dkit-rsrc', 'msd-dundalk', 'could-provide-to',
                   description='RSRC can help MSD de-risk AI adoption in regulated environment')

# Identify GAPS
gm.add_entity('primary', {
    'id': 'iiot-product-development-gap',
    'label': 'IIoT Product Development Capability Gap',
    'type': 'capability',
    'description': 'No local provider for helping manufacturers embed IIoT into their products',
    'sector': 'Technology Development',
    'maturity': 'emerging',
    'scale': 'regional'
})

gm.save()

# Query capabilities
print("=== Unmet Needs Analysis ===")
for entity_id, entity in gm.graph_data['entities']['primary'].items():
    if entity.get('needs_unmet'):
        print(f"\n{entity['label']}:")
        for need in entity['needs_unmet']:
            print(f"  - {need}")

print("\n=== Available Capabilities ===")
for entity_id, entity in gm.graph_data['entities']['primary'].items():
    if entity.get('capabilities_offered'):
        print(f"\n{entity['label']}:")
        for cap in entity['capabilities_offered']:
            print(f"  - {cap}")
```

## Visualization

Run `python server.py` to visualize:

- **Blue circles** = Organizations
- **Purple circles** = Platforms
- **Green circles** = Resources
- **Orange circles** = Processes
- **Teal circles** = Capabilities
- **Red circles** = Value streams
- **Dark grey circles** = Markets
- **Orange-red circles** = Policies
- **Grey boxes** = Stakeholders
- **Yellow diamonds** = Insights

## Analysis Approaches

### Stakeholder Power Mapping
1. Filter by `influence_level: high`
2. See what they control/influence
3. Identify power concentrations

### Value Flow Analysis
1. Follow `provides-to` and `receives-from` chains
2. Map complete value streams
3. Identify bottlenecks

### Dependency Analysis
1. Find `depends-on` relationships
2. Identify single points of failure
3. Assess ecosystem resilience

### Gap Identification
1. Look for isolated elements (few connections)
2. Find missing relationship types
3. Identify unserved needs

### Collaboration Opportunities
1. Find elements that don't directly connect but share interests
2. Identify complementary capabilities
3. Spot potential partnerships

## Tips for Ecosystem Mapping

- **Start broad**: Map major players first
- **Track provenance**: Always link to insights
- **Verify influence**: Don't assume, validate with stakeholders
- **Update regularly**: Ecosystems evolve quickly
- **Multi-perspective**: Interview diverse stakeholders
- **Value flows matter**: Follow the money/resources/knowledge
- **Scale appropriately**: Match detail to project scope

## Integration with Research Methods

### After Interviews
```python
# Add stakeholder interviewed
gm.add_entity('contributors', {...})

# Add insights from interview
gm.add_entity('sources', {
    'source_type': 'interview',
    'key_findings': [...],
    ...
})

# Add elements they mentioned
# Add relationships they described
```

### After Document Analysis
```python
gm.add_entity('sources', {
    'source_type': 'secondary-research',
    'references': ['other-report-ids'],
    ...
})
```

### After Workshops
```python
gm.add_entity('sources', {
    'source_type': 'workshop',
    'key_findings': ['Collaboratively identified gaps', ...],
    ...
})
```

## Validation Status

Use `status` field on insights:
- `preliminary`: Initial findings, not yet validated
- `validated`: Confirmed by multiple sources
- `needs-verification`: Conflicting information, needs follow-up


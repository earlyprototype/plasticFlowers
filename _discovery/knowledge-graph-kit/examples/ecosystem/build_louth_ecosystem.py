#!/usr/bin/env python3
"""
Build Louth Manufacturing Digitalization Ecosystem Graph
Demonstrates capability-need matching in a real manufacturing ecosystem
"""

import sys
from pathlib import Path
import io

# Fix Windows console encoding issues
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.graph_manager import GraphManager


def build_louth_ecosystem():
    """Build the complete Louth Manufacturing ecosystem graph"""
    
    print("Building Louth Manufacturing Ecosystem")
    print("=" * 60)
    
    # Initialize graph manager
    gm = GraphManager(str(Path(__file__).parent / 'config.yaml'))
    
    # ========================================================================
    # PART 1: KEY CAPABILITIES (as first-class entities)
    # ========================================================================
    
    print("\nAdding key capabilities...")
    
    capabilities = [
        {
            'id': 'industrial-robotics-training',
            'label': 'Industrial Robotics Training',
            'type': 'capability',
            'stakeholder_type': 'capability-provider',
            'cluster': 'support-infrastructure',
            'description': 'Hands-on training in 6-axis robots, cobots, vision systems, robot welding',
            'sector': 'Skills Development',
            'maturity': 'mature',
            'scale': 'regional'
        },
        {
            'id': 'regulated-ai-research',
            'label': 'Regulated AI Research & Compliance',
            'type': 'capability',
            'stakeholder_type': 'capability-provider',
            'cluster': 'support-infrastructure',
            'description': 'Safe, ethical, trustworthy AI for medical devices and regulated industries',
            'sector': 'Research & Development',
            'maturity': 'mature',
            'scale': 'national'
        },
        {
            'id': 'digital-prototyping',
            'label': 'Digital Fabrication & Prototyping',
            'type': 'capability',
            'stakeholder_type': 'capability-provider',
            'cluster': 'support-infrastructure',
            'description': '3D printing (FDM, SLA, SLS), laser cutting, CNC milling for SMEs',
            'sector': 'Manufacturing Technology',
            'maturity': 'developing',
            'scale': 'regional'
        },
        {
            'id': 'precision-cnc-machining',
            'label': 'Precision CNC Machining',
            'type': 'capability',
            'stakeholder_type': 'capability-provider',
            'cluster': 'precision-engineering',
            'description': 'High-precision 4 & 5 axis CNC components for MedTech, aerospace, electronics',
            'sector': 'Manufacturing',
            'maturity': 'mature',
            'scale': 'national'
        }
    ]
    
    for cap in capabilities:
        gm.add_entity('primary', cap)
    
    # ========================================================================
    # PART 2: THE TRANSFORMATION TRIANGLE (Support Infrastructure)
    # ========================================================================
    
    print("Adding support infrastructure...")
    
    gm.add_entity('primary', {
        'id': 'amtce',
        'label': 'Advanced Manufacturing Training Centre of Excellence (AMTCE)',
        'type': 'organization',
        'stakeholder_type': 'support-infrastructure',
        'cluster': 'support-infrastructure',
        'description': 'State-of-the-art national training centre for Industry 4.0 upskilling',
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
            'cyber-security-training',
            'vision-systems-training'
        ],
        'target_customers': ['pharma', 'biopharma', 'food-processing', 'engineering-smes']
    })
    
    gm.add_entity('primary', {
        'id': 'dkit-rsrc',
        'label': 'DkIT Regulated Software Research Centre',
        'type': 'organization',
        'stakeholder_type': 'support-infrastructure',
        'cluster': 'support-infrastructure',
        'description': 'World-class research on safe AI in medical devices, software process compliance',
        'sector': 'Research & Development',
        'maturity': 'mature',
        'scale': 'national',
        'location': {
            'town': 'Dundalk',
            'business_park': 'DkIT Campus'
        },
        'capabilities_offered': [
            'regulated-ai-research',
            'medical-device-software-compliance',
            'cybersecurity-research',
            'biopharma-graduate-pipeline'
        ],
        'target_customers': ['medtech', 'biopharma', 'regulated-industries']
    })
    
    gm.add_entity('primary', {
        'id': 'creative-spark-fablab',
        'label': 'Creative Spark Enterprise FabLab',
        'type': 'platform',
        'stakeholder_type': 'support-infrastructure',
        'cluster': 'support-infrastructure',
        'description': 'Technical prototyping platform with digital fabrication tools for SMEs',
        'sector': 'Innovation Infrastructure',
        'maturity': 'developing',
        'scale': 'regional',
        'location': {'town': 'Dundalk'},
        'capabilities_offered': [
            'digital-prototyping',
            'fdm-3d-printing',
            'sla-3d-printing',
            'sls-3d-printing',
            'laser-cutting',
            'cnc-milling',
            'electronics-prototyping'
        ],
        'target_customers': ['smes', 'startups', 'entrepreneurs']
    })
    
    # ========================================================================
    # PART 3: ANCHOR MANUFACTURERS - DUNDALK
    # ========================================================================
    
    print("Adding anchor manufacturers (Dundalk)...")
    
    gm.add_entity('primary', {
        'id': 'msd-dundalk',
        'label': 'MSD (Merck & Co.) Dundalk',
        'type': 'organization',
        'stakeholder_type': 'anchor-manufacturer',
        'cluster': 'biopharma-medtech',
        'description': 'Digital-native vaccine manufacturing facility - drug substance & product manufacturing',
        'sector': 'Biopharmaceutical',
        'maturity': 'mature',
        'scale': 'global',
        'location': {
            'town': 'Dundalk',
            'business_park': 'IDA Business Park',
            'logistics_access': 'M1 corridor, Dublin-Belfast rail'
        },
        'metrics': {
            'employees': 350,
            'investment_received': 500000000,
            'facility_size_sqm': 15520,
            'year_acquired': 2025
        },
        'needs_unmet': [
            'industrial-robotics-training',
            'regulated-ai-research',
            'precision-cnc-machining',
            'systems-integration-expertise'
        ],
        'digital_profile': {
            'maturity_level': 'exceptional-digital-native',
            'transformation_stage': 'integration',
            'technologies_used': [
                'single-use-bioreactors-48000L',
                'advanced-automation',
                'mes-systems',
                'digital-twins',
                'global-smartfacturing-platform'
            ],
            'projected_needs': {
                'near_term': [
                    'MES/ERP/LIMS integration',
                    'Data migration to MSD platforms',
                    'Cybersecurity hardening',
                    'Process validation & re-qualification'
                ],
                'medium_term': [
                    'AI/ML for predictive QC analytics',
                    'Global digital twin integration',
                    'Advanced process optimization'
                ]
            }
        },
        'strategic_position': {
            'opportunities': [
                'Leapfrogged years of construction with ready-to-run facility',
                'Leverage DkIT-RSRC for AI validation in regulated environment',
                'Tap into local precision engineering supply chain',
                'Access to AMTCE for workforce upskilling'
            ],
            'threats': [
                'Complex systems integration from Chinese-built to MSD global platforms',
                'Competition for skilled workers in tight labour market'
            ],
            'competitive_advantages': [
                'ISPE Facility of the Year 2023 winner',
                'EMA approval for commercial manufacturing',
                'Largest single-use bioreactor facility globally'
            ]
        }
    })
    
    gm.add_entity('primary', {
        'id': 'national-pen',
        'label': 'National Pen (Cimpress)',
        'type': 'organization',
        'stakeholder_type': 'anchor-manufacturer',
        'cluster': 'mass-customisation',
        'description': 'Mass-customisation platform for personalized marketing merchandise - data-driven manufacturing',
        'sector': 'Manufacturing - Mass Customisation',
        'maturity': 'mature',
        'scale': 'global',
        'location': {
            'town': 'Dundalk',
            'logistics_access': 'M1 corridor, serves 24 countries'
        },
        'metrics': {
            'employees': 484,
            'revenue': 91000000,
            'global_parent_revenue': 460900000,
            'years_established': 30
        },
        'needs_unmet': [
            'advanced-workflow-automation',
            'robotic-pick-and-place-systems',
            'ai-driven-pricing-optimization'
        ],
        'digital_profile': {
            'maturity_level': 'high-data-driven',
            'transformation_stage': 'optimization',
            'technologies_used': [
                'digital-printing-full-color',
                'silkscreen-printing',
                'laser-engraving',
                'e-commerce-platform',
                'order-management-system'
            ],
            'projected_needs': {
                'near_term': [
                    'E-commerce backend upgrades for customisation complexity',
                    'Advanced workflow automation software',
                    'Order-to-production pipeline optimization'
                ],
                'medium_term': [
                    'Robotic pick-and-place for fulfilment',
                    'AI dynamic pricing engines',
                    'AI product recommendation systems'
                ]
            }
        },
        'strategic_position': {
            'opportunities': [
                'Leverage Cimpress parent technology capabilities',
                'Further automate print-and-pack fulfilment',
                'AI for demand forecasting and customer segmentation'
            ],
            'threats': [
                'Rising operational costs',
                'Global competition in digital-first space',
                'Continuous margin pressure'
            ]
        }
    })
    
    # ========================================================================
    # PART 4: INDIGENOUS SUPPLY CHAIN - PRECISION ENGINEERING
    # ========================================================================
    
    print("Adding indigenous precision engineering cluster...")
    
    gm.add_entity('primary', {
        'id': 'bellurgan-precision',
        'label': 'Bellurgan Precision Engineering',
        'type': 'organization',
        'stakeholder_type': 'indigenous-sme',
        'cluster': 'precision-engineering',
        'description': 'High-precision components for MedTech, aerospace, electronics - 20+ year Medtronic partner',
        'sector': 'Manufacturing - Precision Engineering',
        'maturity': 'mature',
        'scale': 'national',
        'location': {
            'town': 'Bellurgan (Dundalk)',
            'facility_size_sqft': 42000
        },
        'metrics': {
            'employees': 90,
            'year_founded': 1978
        },
        'capabilities_offered': [
            'precision-cnc-machining',
            'design-for-manufacture-collaboration',
            '4-5-axis-cnc-machining',
            'medtech-quality-systems'
        ],
        'target_customers': ['medtech-mncs', 'aerospace', 'electronics'],
        'needs_unmet': [
            'advanced-cad-cam-software',
            'process-simulation-tools',
            'digital-twin-capability',
            'predictive-maintenance-systems'
        ],
        'digital_profile': {
            'maturity_level': 'medium-high',
            'transformation_stage': 'capability-upgrade',
            'technologies_used': [
                'state-of-art-cnc-4-5-axis',
                'swiss-german-japanese-machine-tools',
                'dfm-collaboration-processes'
            ],
            'projected_needs': {
                'near_term': [
                    'Advanced CAD/CAM for DFM support',
                    'Process simulation tools',
                    '3D printing for jigs/fixtures (via FabLab)'
                ],
                'medium_term': [
                    'Predictive maintenance sensors on CNC fleet',
                    'Full ERP/MES for real-time shop floor tracking',
                    'Digital twin for process optimization'
                ]
            }
        },
        'strategic_position': {
            'opportunities': [
                'Move up value chain from component supplier to co-design solutions partner',
                'Leverage DFM expertise with digital simulation',
                'Potential MSD supplier as they build local supply chain'
            ],
            'threats': [
                'High capital costs to maintain state-of-art CNC fleet',
                'Risk of piecemeal digitalization without comprehensive roadmap'
            ],
            'competitive_advantages': [
                'Medtronic Supplier Excellence Award winner',
                'Louth Business of the Year',
                'Deep apprenticeship programme with national awards'
            ]
        }
    })
    
    # ========================================================================
    # PART 5: DROGHEDA - FOOD PROCESSING CLUSTER
    # ========================================================================
    
    print("Adding food processing cluster (Drogheda)...")
    
    gm.add_entity('primary', {
        'id': 'hilton-foods',
        'label': 'Hilton Foods Ireland',
        'type': 'organization',
        'stakeholder_type': 'anchor-manufacturer',
        'cluster': 'food-processing',
        'description': 'Highly automated multi-protein food processing - developer of Greenchain automation platform',
        'sector': 'Food Processing',
        'maturity': 'mature',
        'scale': 'global',
        'location': {
            'town': 'Drogheda',
            'logistics_access': 'M1 corridor'
        },
        'metrics': {
            'global_employees': 7000,
            'global_revenue': 4000000000
        },
        'capabilities_offered': [
            'greenchain-automation-platform',
            'end-to-end-supply-chain-integration',
            'automated-food-processing',
            'industry-4.0-food-manufacturing'
        ],
        'target_customers': ['major-retail-partners', 'food-processors'],
        'digital_profile': {
            'maturity_level': 'very-high-industry-leader',
            'transformation_stage': 'leading',
            'technologies_used': [
                'advanced-automation-robotics',
                'greenchain-supply-chain-platform',
                'ot-it-integration',
                'data-analytics'
            ],
            'projected_needs': {
                'near_term': [
                    'Further robotics deployment for packing/logistics',
                    'Data analytics for waste reduction',
                    'Energy optimization systems'
                ],
                'medium_term': [
                    'AI demand forecasting linked to retail partners',
                    'Enhanced supply chain transparency and data-sharing'
                ]
            }
        },
        'strategic_position': {
            'opportunities': [
                'Greenchain platform as differentiator for retail partners',
                'Expand automation programme to manage costs'
            ],
            'threats': [
                'Cybersecurity risks from highly connected OT/IT',
                'Rising energy costs for automated facilities'
            ],
            'competitive_advantages': [
                'Proprietary Greenchain technology platform',
                'Net-zero by 2048 commitment',
                'Technology-as-a-service business model'
            ]
        }
    })
    
    gm.add_entity('primary', {
        'id': 'boyne-valley-group',
        'label': 'Boyne Valley Group',
        'type': 'organization',
        'stakeholder_type': 'indigenous-sme',
        'cluster': 'food-processing',
        'description': 'Iconic Irish FMCG brands (Chivers, McDonnells, Boyne Valley Honey) - brownfield opportunity',
        'sector': 'Food Processing & Distribution',
        'maturity': 'mature',
        'scale': 'national',
        'location': {
            'town': 'Drogheda'
        },
        'metrics': {
            'employees': 350,
            'year_founded': 1960
        },
        'needs_unmet': [
            'erp-system-upgrade',
            'warehouse-management-system',
            'scada-dcs-process-control',
            'logistics-4.0-implementation',
            'automated-pick-pack-robotics'
        ],
        'digital_profile': {
            'maturity_level': 'low-medium-brownfield',
            'transformation_stage': 'foundational',
            'technologies_used': [
                'traditional-manufacturing-processes',
                'basic-automation'
            ],
            'projected_needs': {
                'near_term': [
                    'ERP system modernisation',
                    'SCADA/DCS for process control',
                    'Modern warehouse management system (WMS)'
                ],
                'medium_term': [
                    'Full Logistics 4.0 implementation',
                    'Automated pick-and-pack robotics',
                    'IIoT sensors for energy monitoring',
                    'Predictive maintenance systems'
                ]
            }
        },
        'strategic_position': {
            'opportunities': [
                'Significant brownfield digitalization opportunity',
                'Learn from Hilton Foods automation leadership',
                'Leverage M1 logistics advantage for distribution efficiency'
            ],
            'threats': [
                'Lagging behind digital-first competitors',
                'Risk of "pilot trap" - technology trials that fail to scale',
                'Supply chain disruption vulnerability'
            ],
            'competitive_advantages': [
                'Portfolio of iconic national brands',
                'Deep community roots and loyalty',
                '100% renewable energy operations',
                'Member of Guaranteed Irish network'
            ]
        }
    })
    
    # ========================================================================
    # PART 6: SPECIALIZED ENGINEERING
    # ========================================================================
    
    print("Adding specialized engineering firms...")
    
    gm.add_entity('primary', {
        'id': 'ml-manufacturing',
        'label': 'M+L Manufacturing',
        'type': 'organization',
        'stakeholder_type': 'indigenous-sme',
        'cluster': 'specialized-engineering',
        'description': 'Mission-critical switchgear for data centres and pharma - product digitalization opportunity',
        'sector': 'Manufacturing - Electrical Engineering',
        'maturity': 'mature',
        'scale': 'national',
        'location': {
            'town': 'Drogheda',
            'business_park': 'Boyne Business Park',
            'facility_size_sqft': 14000
        },
        'metrics': {
            'employees': 60,
            'year_founded': 1975
        },
        'needs_unmet': [
            'iiot-sensor-integration-rd',
            'smart-switchgear-development',
            'condition-monitoring-platform',
            'predictive-maintenance-service-model'
        ],
        'digital_profile': {
            'maturity_level': 'medium-product-driven',
            'transformation_stage': 'product-evolution-needed',
            'technologies_used': [
                'cad-cam-design',
                'custom-fabrication',
                'traditional-assembly'
            ],
            'projected_needs': {
                'near_term': [
                    'R&D programme for IIoT sensor integration',
                    'Enhanced CAD/CAM for custom design'
                ],
                'medium_term': [
                    'Data analytics platform for condition monitoring-as-a-service',
                    'Transform from capital sales to recurring service revenue model'
                ]
            }
        },
        'strategic_position': {
            'opportunities': [
                'Exploding AI-ready data centre demand creates massive opportunity',
                'Integrate IIoT into switchgear for predictive maintenance',
                'Move from one-off sales to recurring hardware+service model'
            ],
            'threats': [
                'Data centre clients demanding "smart" switchgear with sensors',
                'Risk of displacement by global partners (e.g., Schneider) who can provide digital capabilities'
            ],
            'competitive_advantages': [
                'Established relationships with blue-chip data centre clients',
                'Custom engineering capability',
                'Local presence for pharma and data centre sectors'
            ]
        }
    })
    
    gm.add_entity('primary', {
        'id': 'suretank',
        'label': 'Suretank',
        'type': 'organization',
        'stakeholder_type': 'indigenous-sme',
        'cluster': 'specialized-engineering',
        'description': 'High-growth modular engineering - pivoted from oil/gas to wind, data centres, pharma',
        'sector': 'Manufacturing - Heavy Engineering',
        'maturity': 'mature',
        'scale': 'global',
        'location': {
            'town': 'Dunleer',
            'facilities': '4000m2 fabrication + 2900m2 fit-out',
            'logistics_access': 'M1 corridor'
        },
        'metrics': {
            'employees': 380,
            'revenue': 75000000,
            'growth_rate': '50% YoY',
            'year_founded': 1984
        },
        'needs_unmet': [
            'industrial-robotics-training',
            'skilled-welders-80-positions',
            'automation-engineers',
            'robotic-welding-systems',
            'advanced-cad-cam-modular-design'
        ],
        'digital_profile': {
            'maturity_level': 'high-strategic-agility',
            'transformation_stage': 'scaling-hyper-growth',
            'technologies_used': [
                'advanced-fabrication',
                'modular-design-systems',
                'project-management-software'
            ],
            'projected_needs': {
                'near_term': [
                    'Advanced CAD/CAM for modular design',
                    'Robust ERP and project management suite',
                    'Robotic welding (AMTCE training target)'
                ],
                'medium_term': [
                    'R&D for smart IIoT-enabled modular products',
                    'Digital twin simulations for complex modular designs',
                    'Transition from dumb steel to smart assets'
                ]
            }
        },
        'strategic_position': {
            'opportunities': [
                'Successfully pivoted from 90% oil/gas to diverse growth sectors',
                'Smart container technology market growth',
                'Integrate IIoT for tracking and condition monitoring in modules'
            ],
            'threats': [
                'Managing 50% YoY hyper-growth',
                'Recruiting 80 skilled workers in tight labour market'
            ],
            'competitive_advantages': [
                'Proven strategic agility (oil/gas to renewable pivot)',
                'Dual facility capability (fabrication + fit-out)',
                'Established in high-growth sectors (wind, data centres, pharma)'
            ]
        }
    })
    
    # ========================================================================
    # PART 7: TECH/EDGE COMPUTING
    # ========================================================================
    
    print("Adding technology manufacturers...")
    
    gm.add_entity('primary', {
        'id': 'simply-nuc',
        'label': 'Simply NUC (SNUC)',
        'type': 'organization',
        'stakeholder_type': 'anchor-manufacturer',
        'cluster': 'technology-hardware',
        'description': 'EU HQ & manufacturing for edge AI computing hardware - building Industry 4.0 infrastructure',
        'sector': 'Electronics Manufacturing',
        'maturity': 'developing',
        'scale': 'global',
        'location': {
            'town': 'Dunleer',
            'business_park': 'IDA Business Park',
            'facility_size_sqft': 11000
        },
        'metrics': {
            'employees': 30,
            'global_revenue': 34000000,
            'year_established': 2021
        },
        'capabilities_offered': [
            'edge-ai-hardware-manufacturing',
            'mini-pc-assembly',
            'industrial-edge-servers',
            'ai-at-edge-solutions'
        ],
        'target_customers': ['industrial-manufacturing', 'healthcare', 'edge-computing-users'],
        'digital_profile': {
            'maturity_level': 'exceptional-enabler',
            'transformation_stage': 'market-building',
            'technologies_used': [
                'edge-ai-hardware',
                'industrial-computing-systems',
                'configure-to-order-manufacturing'
            ]
        },
        'strategic_position': {
            'opportunities': [
                'Louth now manufactures the hardware that enables Industry 4.0',
                'Picks-and-shovels for AI transformation in manufacturing',
                'Credible EU manufacturing base for US tech company'
            ],
            'competitive_advantages': [
                'EU HQ and manufacturing for supply chain resilience',
                'Positioned for AI-at-edge market explosion',
                'Serves industrial manufacturing vertical'
            ]
        }
    })
    
    # ========================================================================
    # PART 8: GOVERNMENT AGENCIES & POLICY
    # ========================================================================
    
    print("Adding government agencies and policy frameworks...")
    
    gm.add_entity('primary', {
        'id': 'ida-ireland',
        'label': 'IDA Ireland',
        'type': 'organization',
        'stakeholder_type': 'government-agency',
        'cluster': 'government-policy',
        'description': 'Foreign Direct Investment agency - 55 client companies in Northeast region',
        'sector': 'Government - Economic Development',
        'maturity': 'mature',
        'scale': 'national',
        'capabilities_offered': [
            'fdi-attraction',
            'site-development',
            'investment-support',
            'regional-development'
        ]
    })
    
    gm.add_entity('primary', {
        'id': 'enterprise-ireland',
        'label': 'Enterprise Ireland',
        'type': 'organization',
        'stakeholder_type': 'government-agency',
        'cluster': 'government-policy',
        'description': 'Indigenous enterprise development - builds SME digital capability and resilience',
        'sector': 'Government - Enterprise Development',
        'maturity': 'mature',
        'scale': 'national',
        'capabilities_offered': [
            'sme-digital-transformation-support',
            'innovation-funding',
            'rd-grants',
            'regional-enterprise-development'
        ]
    })
    
    gm.add_entity('primary', {
        'id': 'npf-dundalk-growth-centre',
        'label': 'National Planning Framework - Dundalk Regional Growth Centre',
        'type': 'policy',
        'stakeholder_type': 'policy-framework',
        'cluster': 'government-policy',
        'description': 'National policy designation of Dundalk as strategic growth centre',
        'sector': 'Policy',
        'maturity': 'mature',
        'scale': 'national'
    })
    
    # ========================================================================
    # PART 9: CASE STUDY - BD CLOSURE
    # ========================================================================
    
    print("Adding BD closure case study...")
    
    gm.add_entity('primary', {
        'id': 'becton-dickinson-drogheda',
        'label': 'Becton Dickinson (BD) Drogheda',
        'type': 'organization',
        'stakeholder_type': 'anchor-manufacturer',
        'cluster': 'biopharma-medtech',
        'description': 'CASE STUDY: 60-year legacy MedTech plant - closure despite €62M 2021 investment',
        'sector': 'Medical Devices',
        'maturity': 'declining',
        'scale': 'global',
        'location': {'town': 'Drogheda'},
        'metrics': {
            'employees': 200,
            'year_founded': 1964,
            'year_closure_announced': 2024,
            'year_full_closure': 2026,
            'recent_investment': 62000000,
            'investment_year': 2021
        },
        'digital_profile': {
            'maturity_level': 'low-legacy',
            'transformation_stage': 'failed-to-transform'
        },
        'strategic_position': {
            'threats': [
                'THE BD EFFECT: Proof that legacy and recent investment are no defense',
                'Facility lost in global strategic supply chain optimization review',
                'Competition was global - not local',
                'Demonstrates digital transformation is survival imperative, not opportunity'
            ]
        }
    })
    
    # ========================================================================
    # PART 10: INSIGHTS & ANALYSIS
    # ========================================================================
    
    print("\nAdding research insights...")
    
    gm.add_entity('sources', {
        'id': 'louth-ecosystem-analysis-2025',
        'title': 'Louth Manufacturing Digitalization Ecosystem Analysis',
        'source_type': 'secondary-research',
        'date': '2025-11',
        'authors': ['Research Team'],
        'key_elements': [
            'msd-dundalk', 'national-pen', 'bellurgan-precision',
            'hilton-foods', 'boyne-valley-group', 'suretank',
            'amtce', 'dkit-rsrc', 'creative-spark-fablab'
        ],
        'key_findings': [
            'Louth has a complete "Transformation Triangle" of Skills (AMTCE), R&D (RSRC), and Access (FabLab)',
            'FDI-Indigenous synergy creates closed-loop ecosystem',
            'BD closure demonstrates digital transformation is survival imperative',
            'Cluster specialization opportunity: Regulated Smart Biomanufacturing (Dundalk) and High-Automation Food/Logistics (Drogheda)',
            'Three primary threats: BD Effect (global consolidation), Skills Gap, SME Digital Inertia (Pilot Trap)',
            'Significant brownfield digitalization opportunity (Boyne Valley, M+L, traditional SMEs)',
            'Capability-need matching opportunity: AMTCE training can serve MSD, Suretank, and others',
            'Product digitalization opportunity: M+L switchgear needs IIoT integration'
        ],
        'status': 'validated'
    })
    
    # ========================================================================
    # PART 11: REALIZED RELATIONSHIPS
    # ========================================================================
    
    print("\nAdding realized relationships...")
    
    # Capability provision (REALIZED)
    gm.add_relationship('amtce', 'industrial-robotics-training', 'offers-capability',
                       description='AMTCE delivers comprehensive robotics training programmes')
    
    gm.add_relationship('dkit-rsrc', 'regulated-ai-research', 'offers-capability',
                       description='RSRC provides world-class regulated AI research and compliance expertise')
    
    gm.add_relationship('creative-spark-fablab', 'digital-prototyping', 'offers-capability',
                       description='FabLab provides access to digital fabrication tools for SMEs')
    
    gm.add_relationship('bellurgan-precision', 'precision-cnc-machining', 'offers-capability',
                       description='Bellurgan provides high-precision CNC machining services')
    
    # Funding relationships
    gm.add_relationship('enterprise-ireland', 'amtce', 'funds',
                       description='EI provided €7M of €62.4M total AMTCE investment')
    
    gm.add_relationship('enterprise-ireland', 'creative-spark-fablab', 'funds',
                       description='Funded through Regional Enterprise Development Fund (REDF)')
    
    gm.add_relationship('ida-ireland', 'msd-dundalk', 'enables',
                       description='IDA facilitated site acquisition and development')
    
    # Policy enablement
    gm.add_relationship('npf-dundalk-growth-centre', 'msd-dundalk', 'enables',
                       description='Regional Growth Centre designation attracts strategic FDI')
    
    # Supply chain (REALIZED)
    gm.add_relationship('bellurgan-precision', 'msd-dundalk', 'could-provide-to',
                       description='Proven MedTech supplier capability could serve MSD local supply chain needs')
    
    # Knowledge transfer
    gm.add_relationship('dkit-rsrc', 'msd-dundalk', 'provides-to',
                       description='40% of DkIT biopharma graduates hired by facility (pre-MSD acquisition)')
    
    # ========================================================================
    # PART 12: POTENTIAL RELATIONSHIPS (Capability-Need Matching)
    # ========================================================================
    
    print("Adding potential relationships (capability-need matching)...")
    
    # Training needs matching
    gm.add_relationship('msd-dundalk', 'industrial-robotics-training', 'needs-from',
                       description='Needs training for 150 new employees in advanced automation')
    
    gm.add_relationship('suretank', 'industrial-robotics-training', 'needs-from',
                       description='Needs robotics training for 80 new hires + productivity boost from robotic welding')
    
    gm.add_relationship('national-pen', 'industrial-robotics-training', 'needs-from',
                       description='Needs robotics expertise for pick-and-place automation in fulfilment')
    
    # R&D matching
    gm.add_relationship('msd-dundalk', 'regulated-ai-research', 'needs-from',
                       description='Needs AI validation for QC labs and process optimization in regulated environment')
    
    # Digital transformation support
    gm.add_relationship('boyne-valley-group', 'amtce', 'could-partner-with',
                       description='Brownfield manufacturer could benefit from AMTCE automation training')
    
    gm.add_relationship('bellurgan-precision', 'digital-prototyping', 'needs-from',
                       description='Could use FabLab for jigs/fixtures prototyping via 3D printing')
    
    gm.add_relationship('ml-manufacturing', 'dkit-rsrc', 'could-partner-with',
                       description='Could partner on R&D for IIoT sensor integration in switchgear')
    
    # Knowledge transfer opportunities
    gm.add_relationship('hilton-foods', 'boyne-valley-group', 'could-provide-to',
                       description='Greenchain automation platform expertise could guide Boyne Valley transformation')
    
    # ========================================================================
    # PART 13: GAPS
    # ========================================================================
    
    print("Identifying capability gaps...")
    
    gm.add_entity('primary', {
        'id': 'iiot-product-development-gap',
        'label': 'IIoT Product Development Capability Gap',
        'type': 'capability',
        'stakeholder_type': 'capability-provider',
        'description': 'No local provider to help manufacturers embed IIoT sensors into their products',
        'sector': 'Technology Development',
        'maturity': 'emerging',
        'scale': 'regional'
    })
    
    gm.add_relationship('ml-manufacturing', 'iiot-product-development-gap', 'gap',
                       description='M+L needs IIoT integration expertise to create smart switchgear')
    
    gm.add_relationship('suretank', 'iiot-product-development-gap', 'gap',
                       description='Suretank needs capability to transition from dumb steel to smart modular assets')
    
    gm.add_entity('primary', {
        'id': 'brownfield-digitalization-consulting-gap',
        'label': 'Brownfield Manufacturing Digitalization Consulting Gap',
        'type': 'capability',
        'stakeholder_type': 'capability-provider',
        'description': 'No dedicated consulting support to help traditional manufacturers avoid the "pilot trap"',
        'sector': 'Consulting',
        'maturity': 'emerging',
        'scale': 'regional'
    })
    
    gm.add_relationship('boyne-valley-group', 'brownfield-digitalization-consulting-gap', 'gap',
                       description='Needs structured digitalization roadmap to avoid pilot trap and scale transformation')
    
    # ========================================================================
    # SAVE & REPORT
    # ========================================================================
    
    gm.save()
    
    print("\n" + "=" * 60)
    print("SUCCESS: Louth Manufacturing Ecosystem Graph Built")
    print("=" * 60)
    
    # Generate statistics
    try:
        elements = gm.graph_data.get('elements', {})
        stakeholders = gm.graph_data.get('stakeholders', {})
        insights = gm.graph_data.get('insights', {})
        
        print(f"\nGraph Statistics:")
        print(f"  Organizations: {len([e for e in elements.values() if e.get('type') == 'organization'])}")
        print(f"  Capabilities: {len([e for e in elements.values() if e.get('type') == 'capability'])}")
        print(f"  Policies: {len([e for e in elements.values() if e.get('type') == 'policy'])}")
        print(f"  Platforms: {len([e for e in elements.values() if e.get('type') == 'platform'])}")
        print(f"  Total Elements: {len(elements)}")
        print(f"  Stakeholders: {len(stakeholders)}")
        print(f"  Insights: {len(insights)}")
        print(f"  Total Relationships: {len(gm.graph_data.get('relationships', []))}")
    except Exception as e:
        print(f"\nWARNING: Error generating statistics: {e}")
        print(f"  Graph saved successfully despite statistics error")
    
    # Analyze capability-need matching
    print(f"\nCapability-Need Matching Analysis:")
    needs_from_count = len([r for r in gm.graph_data['relationships'] if r['type'] == 'needs-from'])
    could_provide_count = len([r for r in gm.graph_data['relationships'] if r['type'] == 'could-provide-to'])
    gap_count = len([r for r in gm.graph_data['relationships'] if r['type'] == 'gap'])
    
    print(f"  Active Needs: {needs_from_count}")
    print(f"  Potential Matches: {could_provide_count}")
    print(f"  Identified Gaps: {gap_count}")
    
    print(f"\nFiles created:")
    print(f"  - {gm.entities_path}")
    print(f"\nNext steps:")
    print(f"  1. Run: python server.py")
    print(f"  2. Open: http://localhost:8000")
    print(f"  3. Explore capability-need matching in the graph")
    print(f"  4. Filter by relationship type: 'needs-from', 'could-provide-to', 'gap'")
    print("=" * 60)


if __name__ == "__main__":
    build_louth_ecosystem()


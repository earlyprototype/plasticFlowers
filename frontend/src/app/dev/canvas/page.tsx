'use client';

/**
 * /dev/canvas — visual dev harness for GraphCanvas.
 *
 * Renders the full graph canvas against a hardcoded fixture (a fake design
 * lecture): 16 nodes across 4 flowers, 2 ghosts, intra-flower structure and
 * 2 cross-flower bridges. No backend required — this page is the test
 * harness for cartography and all future visual work.
 */

import { GraphCanvas } from '../../../components/graph';
import type { Flower, Node, Relationship } from '../../../lib/types';

const T0 = '2026-07-10T10:00:00Z';

function makeNode(
  id: string,
  label: string,
  flowerId: string | null,
  overrides: Partial<Node> = {}
): Node {
  return {
    id,
    label,
    confidence: 0.9,
    mentions: 2,
    timestamps: [10],
    inferred_type: 'concept',
    flower_id: flowerId,
    created_at: T0,
    status: 'solid',
    ...overrides,
  };
}

function makeRel(
  id: string,
  sourceId: string,
  targetId: string,
  category: Relationship['category'],
  description: string
): Relationship {
  return {
    id,
    source_id: sourceId,
    target_id: targetId,
    category,
    description,
    confidence: 0.85,
    evidence: 'fixture: design lecture transcript',
    source: 'builder',
    created_at: T0,
  };
}

// --- Fixture: a lecture on visual design fundamentals -----------------------

const FIXTURE_NODES: Node[] = [
  // Flower 1 — Visual hierarchy
  makeNode('n-hierarchy', 'visual hierarchy', 'f-hierarchy', { mentions: 7, timestamps: [12, 40, 95] }),
  makeNode('n-contrast', 'contrast', 'f-hierarchy', { mentions: 4, timestamps: [18, 44] }),
  makeNode('n-scale', 'scale', 'f-hierarchy', { mentions: 3, timestamps: [22] }),
  makeNode('n-focal-point', 'focal point', 'f-hierarchy', { mentions: 2, timestamps: [30] }),

  // Flower 2 — Grid systems
  makeNode('n-grid', 'grid systems', 'f-grid', { mentions: 6, timestamps: [120, 150] }),
  makeNode('n-columns', 'column structure', 'f-grid', { mentions: 3, timestamps: [128] }),
  makeNode('n-baseline', 'baseline rhythm', 'f-grid', { mentions: 2, timestamps: [135] }),
  makeNode('n-swiss', 'swiss modernism', 'f-grid', {
    mentions: 1,
    timestamps: [142],
    status: 'ghost',
    confidence: 0.45,
  }),

  // Flower 3 — Typography
  makeNode('n-typography', 'typography', 'f-type', { mentions: 8, timestamps: [200, 230, 260] }),
  makeNode('n-serifs', 'serif faces', 'f-type', { mentions: 3, timestamps: [208] }),
  makeNode('n-x-height', 'x-height', 'f-type', { mentions: 2, timestamps: [215] }),
  makeNode('n-letterspacing', 'letterspacing', 'f-type', { mentions: 2, timestamps: [224] }),

  // Flower 4 — Color theory
  makeNode('n-color', 'color theory', 'f-color', { mentions: 5, timestamps: [300, 320] }),
  makeNode('n-warm-cool', 'warm vs cool', 'f-color', { mentions: 2, timestamps: [308] }),
  makeNode('n-value', 'tonal value', 'f-color', { mentions: 3, timestamps: [314] }),
  makeNode('n-albers', 'albers exercises', 'f-color', {
    mentions: 1,
    timestamps: [326],
    status: 'ghost',
    confidence: 0.4,
    inferred_type: 'reference',
  }),
];

const FIXTURE_FLOWERS: Flower[] = [
  {
    id: 'f-hierarchy',
    label: 'Visual Hierarchy',
    stem_node_id: 'n-hierarchy',
    edge_count: 3,
    member_ids: ['n-hierarchy', 'n-contrast', 'n-scale', 'n-focal-point'],
    created_at: T0,
  },
  {
    id: 'f-grid',
    label: 'Grid Systems',
    stem_node_id: 'n-grid',
    edge_count: 3,
    member_ids: ['n-grid', 'n-columns', 'n-baseline', 'n-swiss'],
    created_at: T0,
  },
  {
    id: 'f-type',
    label: 'Typography',
    stem_node_id: 'n-typography',
    edge_count: 3,
    member_ids: ['n-typography', 'n-serifs', 'n-x-height', 'n-letterspacing'],
    created_at: T0,
  },
  {
    id: 'f-color',
    label: 'Color Theory',
    stem_node_id: 'n-color',
    edge_count: 3,
    member_ids: ['n-color', 'n-warm-cool', 'n-value', 'n-albers'],
    created_at: T0,
  },
];

const FIXTURE_RELATIONSHIPS: Relationship[] = [
  // Visual hierarchy petals
  makeRel('r-h1', 'n-hierarchy', 'n-contrast', 'STRUCTURAL', 'built from'),
  makeRel('r-h2', 'n-hierarchy', 'n-scale', 'STRUCTURAL', 'uses'),
  makeRel('r-h3', 'n-contrast', 'n-focal-point', 'CAUSAL', 'creates'),
  // Grid petals
  makeRel('r-g1', 'n-grid', 'n-columns', 'STRUCTURAL', 'divided into'),
  makeRel('r-g2', 'n-grid', 'n-baseline', 'STRUCTURAL', 'aligned to'),
  makeRel('r-g3', 'n-grid', 'n-swiss', 'TEMPORAL', 'popularised by'),
  // Typography petals
  makeRel('r-t1', 'n-typography', 'n-serifs', 'STRUCTURAL', 'includes'),
  makeRel('r-t2', 'n-typography', 'n-x-height', 'ASSOCIATIVE', 'measured by'),
  makeRel('r-t3', 'n-typography', 'n-letterspacing', 'ASSOCIATIVE', 'tuned with'),
  // Color petals
  makeRel('r-c1', 'n-color', 'n-warm-cool', 'COMPARATIVE', 'contrasts'),
  makeRel('r-c2', 'n-color', 'n-value', 'STRUCTURAL', 'organised by'),
  makeRel('r-c3', 'n-value', 'n-albers', 'ASSOCIATIVE', 'studied in'),
  // Cross-flower bridges
  makeRel('r-b1', 'n-baseline', 'n-x-height', 'ASSOCIATIVE', 'sets rhythm for'),
  makeRel('r-b2', 'n-value', 'n-contrast', 'CAUSAL', 'drives'),
];

export default function CanvasDevPage() {
  return (
    <main
      style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
        padding: '12px 16px 16px',
        background: '#F5F5F4',
      }}
    >
      <p style={{ margin: 0, fontSize: '13px', color: '#57534E' }}>
        <strong>/dev/canvas</strong> — GraphCanvas visual harness (fixture: design lecture; 16
        nodes, 4 flowers, 2 ghosts, 2 bridges; no backend).
      </p>
      <GraphCanvas
        nodes={FIXTURE_NODES}
        relationships={FIXTURE_RELATIONSHIPS}
        flowers={FIXTURE_FLOWERS}
        connectionState="idle"
      />
    </main>
  );
}

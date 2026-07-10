'use client';

/**
 * /dev/canvas — visual dev harness for GraphCanvas.
 *
 * Renders the full graph canvas against a hardcoded fixture (a fake design
 * lecture): 16 nodes across 4 flowers, 2 ghosts, intra-flower structure and
 * 2 cross-flower bridges. No backend required — this page is the test
 * harness for cartography and all future visual work.
 *
 * Default = instant load of the full fixture. The "Grow" button replays the
 * fixture in timed increments (birth order over ~15s) to exercise the growth
 * grammar live: every arrival SPROUTS, one ghost confirms mid-run (BLOOM on
 * 'swiss modernism') and one extra node is pruned near the end (WILT on
 * 'golden ratio').
 */

import { useCallback, useEffect, useRef, useState } from 'react';

import { GraphCanvas } from '../../../components/graph';
import {
  BIRTH_AMBER,
  BIRTH_DAWN,
  BIRTH_MOSS,
  BIRTH_PAPER,
  CARTOGRAPHY_PALETTE,
  SESSION_HUE_SPAN_MS,
  isCartographyEnabled,
} from '../../../components/graph/config/cartography';
import type { Flower, Node, Relationship } from '../../../lib/types';

const T0 = '2026-07-10T10:00:00Z';

/** Fixture birth time: `minutes` after the session start (time-as-colour). */
function atMinutes(minutes: number): string {
  return new Date(Date.parse(T0) + minutes * 60_000).toISOString();
}

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

// Birth times (created_at) are staggered across the
// 30-minute time-as-colour window, in the same order as the Grow replay:
// the hierarchy island is born at dawn (indigo), grids and typography span
// the middle (moss), and color theory arrives late (amber).
const FIXTURE_NODES: Node[] = [
  // Flower 1 — Visual hierarchy (minutes 0–2.5: dawn indigo)
  makeNode('n-hierarchy', 'visual hierarchy', 'f-hierarchy', { mentions: 7, timestamps: [12, 40, 95], created_at: atMinutes(0) }),
  makeNode('n-contrast', 'contrast', 'f-hierarchy', { mentions: 4, timestamps: [18, 44], created_at: atMinutes(1) }),
  makeNode('n-scale', 'scale', 'f-hierarchy', { mentions: 3, timestamps: [22], created_at: atMinutes(1.5) }),
  makeNode('n-focal-point', 'focal point', 'f-hierarchy', { mentions: 2, timestamps: [30], created_at: atMinutes(2.5) }),

  // Flower 2 — Grid systems (minutes 6–9: dawn → moss)
  makeNode('n-grid', 'grid systems', 'f-grid', { mentions: 6, timestamps: [120, 150], created_at: atMinutes(6) }),
  makeNode('n-columns', 'column structure', 'f-grid', { mentions: 3, timestamps: [128], created_at: atMinutes(7) }),
  makeNode('n-baseline', 'baseline rhythm', 'f-grid', { mentions: 2, timestamps: [135], created_at: atMinutes(8) }),
  makeNode('n-swiss', 'swiss modernism', 'f-grid', {
    mentions: 1,
    timestamps: [142],
    status: 'ghost',
    confidence: 0.45,
    created_at: atMinutes(9),
  }),

  // Flower 3 — Typography (minutes 13–16: moss)
  makeNode('n-typography', 'typography', 'f-type', { mentions: 8, timestamps: [200, 230, 260], created_at: atMinutes(13) }),
  makeNode('n-serifs', 'serif faces', 'f-type', { mentions: 3, timestamps: [208], created_at: atMinutes(14) }),
  makeNode('n-x-height', 'x-height', 'f-type', { mentions: 2, timestamps: [215], created_at: atMinutes(15) }),
  makeNode('n-letterspacing', 'letterspacing', 'f-type', { mentions: 2, timestamps: [224], created_at: atMinutes(16) }),

  // Flower 4 — Color theory (minutes 24–29.5: late amber)
  makeNode('n-color', 'color theory', 'f-color', { mentions: 5, timestamps: [300, 320], created_at: atMinutes(24) }),
  makeNode('n-warm-cool', 'warm vs cool', 'f-color', { mentions: 2, timestamps: [308], created_at: atMinutes(26) }),
  makeNode('n-value', 'tonal value', 'f-color', { mentions: 3, timestamps: [314], created_at: atMinutes(28) }),
  makeNode('n-albers', 'albers exercises', 'f-color', {
    mentions: 1,
    timestamps: [326],
    status: 'ghost',
    confidence: 0.4,
    inferred_type: 'reference',
    created_at: atMinutes(29.5),
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

// --- Grow mode: replay the fixture in birth order --------------------------

type GraphData = {
  nodes: Node[];
  relationships: Relationship[];
  flowers: Flower[];
};

const FULL_FIXTURE: GraphData = {
  nodes: FIXTURE_NODES,
  relationships: FIXTURE_RELATIONSHIPS,
  flowers: FIXTURE_FLOWERS,
};

/** One timed increment of the grow run. Nodes/rels/flowers upsert by id. */
type GrowStep = {
  at: number; // ms from pressing Grow
  nodes?: Node[];
  relationships?: Relationship[];
  flowers?: Flower[];
  removeNodeIds?: string[];
  removeRelIds?: string[];
};

const nodeById = new Map(FIXTURE_NODES.map((n) => [n.id, n]));
const relById = new Map(FIXTURE_RELATIONSHIPS.map((r) => [r.id, r]));
const flowerById = new Map(FIXTURE_FLOWERS.map((f) => [f.id, f]));

const fixtureNode = (id: string): Node => nodeById.get(id)!;
const fixtureRel = (id: string): Relationship => relById.get(id)!;
const fixtureFlower = (id: string): Flower => flowerById.get(id)!;

/** Extra node that only exists during the grow run — pruned near the end. */
const PRUNED_NODE: Node = makeNode('n-golden', 'golden ratio', 'f-hierarchy', {
  mentions: 1,
  timestamps: [52],
  created_at: atMinutes(3),
});
const PRUNED_REL: Relationship = makeRel(
  'r-x1',
  'n-hierarchy',
  'n-golden',
  'ASSOCIATIVE',
  'guided by'
);

const STEP_MS = 700;

/**
 * Birth-order timeline (~15s): each flower appears with its stem, petals
 * arrive one by one with their edge (SPROUT), 'swiss modernism' arrives as
 * a ghost and confirms mid-run (BLOOM), and 'golden ratio' + its edge are
 * pruned in the final step (WILT).
 */
const GROW_TIMELINE: GrowStep[] = [
  // Flower 1 — visual hierarchy
  { at: 0, flowers: [fixtureFlower('f-hierarchy')], nodes: [fixtureNode('n-hierarchy')] },
  { at: STEP_MS, nodes: [fixtureNode('n-contrast')], relationships: [fixtureRel('r-h1')] },
  { at: STEP_MS * 2, nodes: [fixtureNode('n-scale')], relationships: [fixtureRel('r-h2')] },
  { at: STEP_MS * 3, nodes: [fixtureNode('n-focal-point')], relationships: [fixtureRel('r-h3')] },
  // Flower 2 — grid systems
  { at: STEP_MS * 4, flowers: [fixtureFlower('f-grid')], nodes: [fixtureNode('n-grid')] },
  { at: STEP_MS * 5, nodes: [fixtureNode('n-columns')], relationships: [fixtureRel('r-g1')] },
  { at: STEP_MS * 6, nodes: [fixtureNode('n-baseline')], relationships: [fixtureRel('r-g2')] },
  // Ghost arrives (still unconfirmed)
  { at: STEP_MS * 7, nodes: [fixtureNode('n-swiss')], relationships: [fixtureRel('r-g3')] },
  // Flower 3 — typography
  { at: STEP_MS * 8, flowers: [fixtureFlower('f-type')], nodes: [fixtureNode('n-typography')] },
  { at: STEP_MS * 9, nodes: [fixtureNode('n-serifs')], relationships: [fixtureRel('r-t1')] },
  { at: STEP_MS * 10, nodes: [fixtureNode('n-x-height')], relationships: [fixtureRel('r-t2')] },
  {
    at: STEP_MS * 11,
    nodes: [fixtureNode('n-letterspacing')],
    relationships: [fixtureRel('r-t3'), fixtureRel('r-b1')], // + bridge to grid
  },
  // BLOOM: the swiss modernism ghost confirms
  { at: STEP_MS * 12, nodes: [{ ...fixtureNode('n-swiss'), status: 'solid', confidence: 0.9 }] },
  // Flower 4 — color theory (+ the doomed 'golden ratio' aside)
  { at: STEP_MS * 13, flowers: [fixtureFlower('f-color')], nodes: [fixtureNode('n-color')] },
  {
    at: STEP_MS * 14,
    nodes: [fixtureNode('n-warm-cool'), PRUNED_NODE],
    relationships: [fixtureRel('r-c1'), PRUNED_REL],
  },
  {
    at: STEP_MS * 15,
    nodes: [fixtureNode('n-value')],
    relationships: [fixtureRel('r-c2'), fixtureRel('r-b2')], // + bridge to hierarchy
  },
  { at: STEP_MS * 16, nodes: [fixtureNode('n-albers')], relationships: [fixtureRel('r-c3')] },
  // WILT: the aside gets pruned
  { at: STEP_MS * 18, removeNodeIds: ['n-golden'], removeRelIds: ['r-x1'] },
];

const GROW_TOTAL_MS = GROW_TIMELINE[GROW_TIMELINE.length - 1].at + 2500;

function upsertById<T extends { id: string }>(list: T[], additions: T[] | undefined): T[] {
  if (!additions || additions.length === 0) return list;
  const ids = new Set(additions.map((item) => item.id));
  return [...list.filter((item) => !ids.has(item.id)), ...additions];
}

function applyGrowStep(prev: GraphData, step: GrowStep): GraphData {
  let nodes = upsertById(prev.nodes, step.nodes);
  let relationships = upsertById(prev.relationships, step.relationships);
  const flowers = upsertById(prev.flowers, step.flowers);
  if (step.removeNodeIds?.length) {
    const gone = new Set(step.removeNodeIds);
    nodes = nodes.filter((n) => !gone.has(n.id));
  }
  if (step.removeRelIds?.length) {
    const gone = new Set(step.removeRelIds);
    relationships = relationships.filter((r) => !gone.has(r.id));
  }
  return { nodes, relationships, flowers };
}

export default function CanvasDevPage() {
  const [data, setData] = useState<GraphData>(FULL_FIXTURE);
  const [growing, setGrowing] = useState(false);
  // Move 5: portrait mode — the presentation render of the finished map.
  const [portrait, setPortrait] = useState(false);
  // Remount key: a grow run must start from an EMPTY canvas. Feeding empty
  // data into the mounted canvas would instead wilt the whole fixture away
  // (correct verb behavior, wrong demo) and revive nodes re-added within the
  // wilt window rather than sprouting them.
  const [runId, setRunId] = useState(0);
  const timersRef = useRef<number[]>([]);

  const clearTimers = useCallback(() => {
    timersRef.current.forEach((id) => window.clearTimeout(id));
    timersRef.current = [];
  }, []);

  useEffect(() => clearTimers, [clearTimers]);

  const handleGrow = useCallback(() => {
    clearTimers();
    setGrowing(true);
    setRunId((id) => id + 1);
    setData({ nodes: [], relationships: [], flowers: [] });
    GROW_TIMELINE.forEach((step) => {
      timersRef.current.push(
        window.setTimeout(() => setData((prev) => applyGrowStep(prev, step)), step.at)
      );
    });
    timersRef.current.push(window.setTimeout(() => setGrowing(false), GROW_TOTAL_MS));
  }, [clearTimers]);

  const handleReset = useCallback(() => {
    clearTimers();
    setGrowing(false);
    setRunId((id) => id + 1);
    setData(FULL_FIXTURE);
  }, [clearTimers]);

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
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <p style={{ margin: 0, fontSize: '13px', color: '#57534E' }}>
          <strong>/dev/canvas</strong> — GraphCanvas visual harness (fixture: design lecture; 16
          nodes, 4 flowers, 2 ghosts, 2 bridges; no backend).
        </p>
        <button
          onClick={handleGrow}
          disabled={growing}
          style={{
            fontSize: '12px',
            padding: '4px 12px',
            border: '1px solid #A8A29E',
            borderRadius: '4px',
            background: growing ? '#E7E5E4' : '#FFFFFF',
            color: '#44403C',
            cursor: growing ? 'default' : 'pointer',
          }}
        >
          {growing ? 'Growing…' : 'Grow'}
        </button>
        <button
          onClick={handleReset}
          style={{
            fontSize: '12px',
            padding: '4px 12px',
            border: '1px solid #A8A29E',
            borderRadius: '4px',
            background: '#FFFFFF',
            color: '#44403C',
            cursor: 'pointer',
          }}
        >
          Reset
        </button>
        {isCartographyEnabled() ? (
          <button
            id="portrait-toggle"
            onClick={() => setPortrait((value) => !value)}
            style={{
              fontSize: '12px',
              padding: '4px 12px',
              border: `1px solid ${CARTOGRAPHY_PALETTE.coast}`,
              borderRadius: '4px',
              background: portrait ? CARTOGRAPHY_PALETTE.ink : BIRTH_PAPER,
              color: portrait ? BIRTH_PAPER : CARTOGRAPHY_PALETTE.ink,
              cursor: 'pointer',
            }}
          >
            {portrait ? 'Exit portrait' : 'Portrait'}
          </button>
        ) : null}
        {isCartographyEnabled() ? (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              marginLeft: 'auto',
              fontSize: '11px',
              color: '#57534E',
            }}
          >
            <span>0 min</span>
            <div
              aria-hidden="true"
              style={{
                width: '140px',
                height: '10px',
                borderRadius: '5px',
                border: '1px solid #D6D3D1',
                background: `linear-gradient(90deg, ${BIRTH_DAWN} 0%, ${BIRTH_MOSS} 50%, ${BIRTH_AMBER} 100%)`,
              }}
            />
            <span>{SESSION_HUE_SPAN_MS / 60_000}+ min</span>
            <span style={{ fontStyle: 'italic' }}>colour = when the idea appeared</span>
          </div>
        ) : null}
      </div>
      <GraphCanvas
        key={runId}
        nodes={data.nodes}
        relationships={data.relationships}
        flowers={data.flowers}
        connectionState={growing ? 'open' : 'idle'}
        portrait={portrait}
        sessionId="dev-canvas"
      />
    </main>
  );
}

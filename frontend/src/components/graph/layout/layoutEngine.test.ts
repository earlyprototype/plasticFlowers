import { describe, it, expect } from 'vitest';
import {
  identifyIsolatedNodes,
  identifyExistingNodes,
  calculateLayout,
  computeSeedPosition,
  SEED_CLUSTER_RADIUS,
  SEED_JITTER_RADIUS,
} from './layoutEngine';
import type { Node, Relationship, Flower } from '../../../lib/types';

describe('layoutEngine', () => {
  describe('computeSeedPosition', () => {
    it('is deterministic for the same inputs', () => {
      expect(computeSeedPosition('n1', 'f1', 0, 4)).toEqual(computeSeedPosition('n1', 'f1', 0, 4));
    });

    it('clusters members of the same flower near one seed centre', () => {
      const a = computeSeedPosition('n1', 'f1', 0, 4);
      const b = computeSeedPosition('n2', 'f1', 0, 4);
      // Ordinal 0 of 4 → ring angle 0 → centre (R, 0); both within jitter.
      const center = { x: SEED_CLUSTER_RADIUS, y: 0 };
      expect(Math.hypot(a.x - center.x, a.y - center.y)).toBeLessThanOrEqual(SEED_JITTER_RADIUS);
      expect(Math.hypot(b.x - center.x, b.y - center.y)).toBeLessThanOrEqual(SEED_JITTER_RADIUS);
    });

    it('separates different flowers onto distant ring points', () => {
      const a = computeSeedPosition('n1', 'f1', 0, 4);
      const b = computeSeedPosition('n2', 'f2', 1, 4);
      // Adjacent ring points for 4 flowers are R·√2 apart, far beyond 2×jitter.
      expect(Math.hypot(a.x - b.x, a.y - b.y)).toBeGreaterThan(
        SEED_CLUSTER_RADIUS * Math.SQRT2 - 2 * SEED_JITTER_RADIUS
      );
    });

    it('scatters unclustered nodes near the origin', () => {
      const pos = computeSeedPosition('lonely', null, 0, 0);
      expect(Math.hypot(pos.x, pos.y)).toBeLessThanOrEqual(SEED_JITTER_RADIUS * 2.5);
    });
  });

  describe('identifyIsolatedNodes', () => {
    it('should return nodes with no connections', () => {
      const nodes: Node[] = [
        {
          id: 'node1',
          label: 'Isolated',
          confidence: 0.8,
          mentions: 1,
          timestamps: [100],
          inferred_type: 'concept',
          flower_id: null,
          created_at: '2025-01-01T00:00:00Z',
          status: 'solid',
        },
        {
          id: 'node2',
          label: 'Connected',
          confidence: 0.9,
          mentions: 2,
          timestamps: [200],
          inferred_type: 'concept',
          flower_id: null,
          created_at: '2025-01-01T00:00:00Z',
          status: 'solid',
        },
      ];

      const relationships: Relationship[] = [
        {
          id: 'rel1',
          source_id: 'node2',
          target_id: 'node3',
          category: 'STRUCTURAL',
          description: 'related to',
          confidence: 0.8,
          evidence: 'text',
          source: 'builder',
          created_at: '2025-01-01T00:00:00Z',
        },
        {
          id: 'rel2',
          source_id: 'node2',
          target_id: 'node4',
          category: 'STRUCTURAL',
          description: 'connected to',
          confidence: 0.8,
          evidence: 'text',
          source: 'builder',
          created_at: '2025-01-01T00:00:00Z',
        },
      ];

      const isolated = identifyIsolatedNodes(nodes, relationships);

      expect(isolated.has('node1')).toBe(true);
      expect(isolated.has('node2')).toBe(false);
    });

    it('should return nodes with only 1 connection', () => {
      const nodes: Node[] = [
        {
          id: 'node1',
          label: 'One Connection',
          confidence: 0.8,
          mentions: 1,
          timestamps: [100],
          inferred_type: 'concept',
          flower_id: null,
          created_at: '2025-01-01T00:00:00Z',
          status: 'solid',
        },
      ];

      const relationships: Relationship[] = [
        {
          id: 'rel1',
          source_id: 'node1',
          target_id: 'node2',
          category: 'STRUCTURAL',
          description: 'relates to',
          confidence: 0.8,
          evidence: 'text',
          source: 'builder',
          created_at: '2025-01-01T00:00:00Z',
        },
      ];

      const isolated = identifyIsolatedNodes(nodes, relationships);

      expect(isolated.has('node1')).toBe(true);
    });

    it('should exclude nodes in flowers', () => {
      const nodes: Node[] = [
        {
          id: 'node1',
          label: 'In Flower',
          confidence: 0.8,
          mentions: 1,
          timestamps: [100],
          inferred_type: 'concept',
          flower_id: 'flower1',
          created_at: '2025-01-01T00:00:00Z',
          status: 'solid',
        },
      ];

      const relationships: Relationship[] = [];

      const isolated = identifyIsolatedNodes(nodes, relationships);

      expect(isolated.has('node1')).toBe(false);
    });

    it('should exclude nodes with more than 1 connection', () => {
      const nodes: Node[] = [
        {
          id: 'node1',
          label: 'Well Connected',
          confidence: 0.8,
          mentions: 1,
          timestamps: [100],
          inferred_type: 'concept',
          flower_id: null,
          created_at: '2025-01-01T00:00:00Z',
          status: 'solid',
        },
      ];

      const relationships: Relationship[] = [
        {
          id: 'rel1',
          source_id: 'node1',
          target_id: 'node2',
          category: 'STRUCTURAL',
          description: 'relates to',
          confidence: 0.8,
          evidence: 'text',
          source: 'builder',
          created_at: '2025-01-01T00:00:00Z',
        },
        {
          id: 'rel2',
          source_id: 'node1',
          target_id: 'node3',
          category: 'STRUCTURAL',
          description: 'connects to',
          confidence: 0.8,
          evidence: 'text',
          source: 'builder',
          created_at: '2025-01-01T00:00:00Z',
        },
      ];

      const isolated = identifyIsolatedNodes(nodes, relationships);

      expect(isolated.has('node1')).toBe(false);
    });
  });

  describe('identifyExistingNodes', () => {
    it('should identify nodes that exist in current positions', () => {
      const currentPositions = new Map([
        ['node1', { x: 100, y: 100 }],
        ['node2', { x: 200, y: 200 }],
      ]);

      const nodes: Node[] = [
        {
          id: 'node1',
          label: 'Existing',
          confidence: 0.8,
          mentions: 1,
          timestamps: [100],
          inferred_type: 'concept',
          flower_id: null,
          created_at: '2025-01-01T00:00:00Z',
          status: 'solid',
        },
        {
          id: 'node3',
          label: 'New',
          confidence: 0.8,
          mentions: 1,
          timestamps: [100],
          inferred_type: 'concept',
          flower_id: null,
          created_at: '2025-01-01T00:00:00Z',
          status: 'ghost',
        },
      ];

      const existing = identifyExistingNodes(currentPositions, nodes);

      expect(existing.has('node1')).toBe(true);
      expect(existing.has('node3')).toBe(false);
    });
  });

  describe('calculateLayout', () => {
    it('should return locked positions for existing nodes', () => {
      const currentPositions = new Map([
        ['node1', { x: 100, y: 100 }],
        ['node2', { x: 200, y: 200 }],
      ]);

      const nodes: Node[] = [
        {
          id: 'node1',
          label: 'Existing',
          confidence: 0.8,
          mentions: 1,
          timestamps: [100],
          inferred_type: 'concept',
          flower_id: null,
          created_at: '2025-01-01T00:00:00Z',
          status: 'solid',
        },
      ];

      const relationships: Relationship[] = [];
      const flowers: Flower[] = [];

      const result = calculateLayout(
        currentPositions,
        { nodes, relationships, flowers },
        {
          name: 'fcose',
          nodeRepulsion: 45000,
          idealEdgeLength: 350,
          nodeSeparation: 250,
          numIter: 300,
          gravity: 0.08,
          nestingFactor: 0.2,
          gravityCompound: 1.2,
          gravityRangeCompound: 2.0,
        }
      );

      expect(result.nodePositions.has('node1')).toBe(true);
      expect(result.lockedNodeIds.has('node1')).toBe(true);
      expect(result.nodePositions.get('node1')).toEqual({ x: 100, y: 100 });
    });

    it('should identify isolated nodes correctly', () => {
      const currentPositions = new Map();

      const nodes: Node[] = [
        {
          id: 'node1',
          label: 'Isolated',
          confidence: 0.8,
          mentions: 1,
          timestamps: [100],
          inferred_type: 'concept',
          flower_id: null,
          created_at: '2025-01-01T00:00:00Z',
          status: 'solid',
        },
      ];

      const relationships: Relationship[] = [];
      const flowers: Flower[] = [];

      const result = calculateLayout(
        currentPositions,
        { nodes, relationships, flowers },
        {
          name: 'fcose',
          nodeRepulsion: 45000,
          idealEdgeLength: 350,
          nodeSeparation: 250,
          numIter: 300,
          gravity: 0.08,
          nestingFactor: 0.2,
          gravityCompound: 1.2,
          gravityRangeCompound: 2.0,
        }
      );

      expect(result.isolatedNodeIds.has('node1')).toBe(true);
    });
  });
});


import { describe, it, expect } from 'vitest';
import {
  calculateIntelligentPositions,
  CLUSTERING_PRESETS,
  DEFAULT_STRATEGY,
} from './intelligentClustering';
import type { Node } from '../../../lib/types';

describe('intelligentClustering', () => {
  const createTestNode = (overrides: Partial<Node> = {}): Node => ({
    id: `node-${Math.random()}`,
    label: 'Test Node',
    confidence: 0.8,
    mentions: 1,
    timestamps: [Date.now()],
    inferred_type: 'concept',
    flower_id: null,
    created_at: new Date().toISOString(),
    status: 'solid',
    ...overrides,
  });

  describe('calculateIntelligentPositions', () => {
    it('should return empty map for empty nodes array', () => {
      const positions = calculateIntelligentPositions([]);
      expect(positions.size).toBe(0);
    });

    it('should assign positions to all nodes', () => {
      const nodes = [
        createTestNode({ id: 'node1' }),
        createTestNode({ id: 'node2' }),
        createTestNode({ id: 'node3' }),
      ];

      const positions = calculateIntelligentPositions(nodes);
      
      expect(positions.size).toBe(3);
      expect(positions.has('node1')).toBe(true);
      expect(positions.has('node2')).toBe(true);
      expect(positions.has('node3')).toBe(true);
    });

    it('should place nodes with same type in similar regions', () => {
      const concepts = [
        createTestNode({ id: 'concept1', inferred_type: 'concept' }),
        createTestNode({ id: 'concept2', inferred_type: 'concept' }),
      ];

      const positions = calculateIntelligentPositions(concepts, {
        typeWeight: 1.0,
        importanceWeight: 0,
        recencyWeight: 0,
      });

      const pos1 = positions.get('concept1')!;
      const pos2 = positions.get('concept2')!;

      // Both should be in top region (negative Y for concepts)
      expect(pos1.y).toBeLessThan(0);
      expect(pos2.y).toBeLessThan(0);
      
      // Should be relatively close (within region jitter)
      const distance = Math.sqrt(
        Math.pow(pos1.x - pos2.x, 2) + Math.pow(pos1.y - pos2.y, 2)
      );
      expect(distance).toBeLessThan(1500); // Within type region
    });

    it('should place different types in different regions', () => {
      const nodes = [
        createTestNode({ id: 'concept', inferred_type: 'concept' }),  // Top
        createTestNode({ id: 'entity', inferred_type: 'entity' }),   // Left
        createTestNode({ id: 'event', inferred_type: 'event' }),     // Right
        createTestNode({ id: 'process', inferred_type: 'process' }), // Bottom
      ];

      const positions = calculateIntelligentPositions(nodes, {
        typeWeight: 1.0,
        importanceWeight: 0,
        recencyWeight: 0,
      });

      const concept = positions.get('concept')!;
      const entity = positions.get('entity')!;
      const event = positions.get('event')!;
      const process = positions.get('process')!;

      // Concepts: top (negative Y)
      expect(concept.y).toBeLessThan(-500);
      
      // Entities: left (negative X)
      expect(entity.x).toBeLessThan(-500);
      
      // Events: right (positive X)
      expect(event.x).toBeGreaterThan(500);
      
      // Process: bottom (positive Y)
      expect(process.y).toBeGreaterThan(500);
    });

    it('should place high-mention nodes closer to center with importance weight', () => {
      const nodes = [
        createTestNode({ id: 'low', mentions: 1, inferred_type: 'concept' }),
        createTestNode({ id: 'high', mentions: 10, inferred_type: 'concept' }),
      ];

      const positions = calculateIntelligentPositions(nodes, {
        typeWeight: 0,
        importanceWeight: 1.0,
        recencyWeight: 0,
      });

      const lowPos = positions.get('low')!;
      const highPos = positions.get('high')!;

      const lowDistance = Math.sqrt(lowPos.x ** 2 + lowPos.y ** 2);
      const highDistance = Math.sqrt(highPos.x ** 2 + highPos.y ** 2);

      // High mention count should be closer to center
      expect(highDistance).toBeLessThan(lowDistance);
    });

    it('should place recent nodes closer to center with recency weight', () => {
      const now = Date.now();
      const tenMinutesAgo = now - (10 * 60 * 1000);
      const thirtyMinutesAgo = now - (30 * 60 * 1000);

      const nodes = [
        createTestNode({ id: 'recent', timestamps: [now], inferred_type: 'concept' }),
        createTestNode({ id: 'old', timestamps: [thirtyMinutesAgo], inferred_type: 'concept' }),
      ];

      const positions = calculateIntelligentPositions(nodes, {
        typeWeight: 0,
        importanceWeight: 0,
        recencyWeight: 1.0,
      });

      const recentPos = positions.get('recent')!;
      const oldPos = positions.get('old')!;

      const recentDistance = Math.sqrt(recentPos.x ** 2 + recentPos.y ** 2);
      const oldDistance = Math.sqrt(oldPos.x ** 2 + oldPos.y ** 2);

      // Recent should be closer to center
      expect(recentDistance).toBeLessThan(oldDistance);
    });
  });

  describe('CLUSTERING_PRESETS', () => {
    it('should have semantic preset emphasizing type', () => {
      expect(CLUSTERING_PRESETS.SEMANTIC.typeWeight).toBeGreaterThan(0.5);
      expect(CLUSTERING_PRESETS.SEMANTIC.typeWeight).toBeGreaterThan(
        CLUSTERING_PRESETS.SEMANTIC.importanceWeight
      );
    });

    it('should have importance preset emphasizing mentions', () => {
      expect(CLUSTERING_PRESETS.IMPORTANCE.importanceWeight).toBeGreaterThan(0.5);
      expect(CLUSTERING_PRESETS.IMPORTANCE.importanceWeight).toBeGreaterThan(
        CLUSTERING_PRESETS.IMPORTANCE.typeWeight
      );
    });

    it('should have temporal preset emphasizing recency', () => {
      expect(CLUSTERING_PRESETS.TEMPORAL.recencyWeight).toBeGreaterThan(0.5);
      expect(CLUSTERING_PRESETS.TEMPORAL.recencyWeight).toBeGreaterThan(
        CLUSTERING_PRESETS.TEMPORAL.typeWeight
      );
    });

    it('should have balanced preset with mixed weights', () => {
      const balanced = CLUSTERING_PRESETS.BALANCED;
      expect(balanced.typeWeight).toBeGreaterThan(0);
      expect(balanced.importanceWeight).toBeGreaterThan(0);
      expect(balanced.recencyWeight).toBeGreaterThan(0);
    });
  });

  describe('DEFAULT_STRATEGY', () => {
    it('should prioritize type over other factors', () => {
      expect(DEFAULT_STRATEGY.typeWeight).toBeGreaterThan(DEFAULT_STRATEGY.importanceWeight);
      expect(DEFAULT_STRATEGY.typeWeight).toBeGreaterThan(DEFAULT_STRATEGY.recencyWeight);
    });

    it('should have weights that can be normalized', () => {
      const total = 
        DEFAULT_STRATEGY.typeWeight +
        DEFAULT_STRATEGY.importanceWeight +
        DEFAULT_STRATEGY.recencyWeight;
      
      expect(total).toBeGreaterThan(0);
    });
  });

  describe('edge cases', () => {
    it('should handle nodes with unknown types', () => {
      const nodes = [
        createTestNode({ id: 'unknown', inferred_type: 'unknown_type' as any }),
      ];

      const positions = calculateIntelligentPositions(nodes);
      
      expect(positions.has('unknown')).toBe(true);
      // Should default to center-ish (0,0 + jitter)
      const pos = positions.get('unknown')!;
      expect(Math.abs(pos.x)).toBeLessThan(500);
      expect(Math.abs(pos.y)).toBeLessThan(500);
    });

    it('should handle nodes with empty timestamps', () => {
      const nodes = [
        createTestNode({ id: 'no-time', timestamps: [] }),
      ];

      expect(() => {
        calculateIntelligentPositions(nodes);
      }).not.toThrow();
    });

    it('should handle zero weights gracefully', () => {
      const nodes = [createTestNode()];
      
      const positions = calculateIntelligentPositions(nodes, {
        typeWeight: 0,
        importanceWeight: 0,
        recencyWeight: 0,
      });

      // Should handle division by zero (totalWeight = 0)
      expect(positions.size).toBe(1);
      const pos = positions.get(nodes[0].id)!;
      expect(isNaN(pos.x)).toBe(false);
      expect(isNaN(pos.y)).toBe(false);
    });
  });
});


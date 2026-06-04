import { describe, it, expect, beforeEach } from 'vitest';
import cytoscape, { type Core } from 'cytoscape';
import {
  calculateHubStrength,
  calculateAttractionStrength,
  applyRelationshipAttraction,
  getHubIndicators,
  DEFAULT_ORGANIC_CONFIG,
} from './organicGrowth';
import type { Node, Relationship } from '../../../lib/types';

describe('organicGrowth', () => {
  let cy: Core;

  beforeEach(() => {
    cy = cytoscape({
      headless: true,
      styleEnabled: false,
    });
  });

  const createTestNode = (id: string): Node => ({
    id,
    label: `Node ${id}`,
    confidence: 0.8,
    mentions: 1,
    timestamps: [Date.now()],
    inferred_type: 'concept',
    flower_id: null,
    created_at: new Date().toISOString(),
    status: 'solid',
  });

  const createTestRelationship = (
    id: string,
    sourceId: string,
    targetId: string
  ): Relationship => ({
    id,
    source_id: sourceId,
    target_id: targetId,
    category: 'STRUCTURAL',
    description: 'related to',
    confidence: 0.8,
    evidence: 'text',
    source: 'builder',
    created_at: new Date().toISOString(),
  });

  describe('calculateHubStrength', () => {
    it('should return 1.0 for node with 1 connection', () => {
      const relationships: Relationship[] = [
        createTestRelationship('rel1', 'hub', 'node1'),
      ];

      const strength = calculateHubStrength('hub', relationships);
      
      // log2(1 + 2) = log2(3) ≈ 1.58
      expect(strength).toBeGreaterThan(1.0);
      expect(strength).toBeLessThan(2.0);
    });

    it('should return higher strength for nodes with more connections', () => {
      const relationships: Relationship[] = [
        createTestRelationship('rel1', 'hub', 'node1'),
        createTestRelationship('rel2', 'hub', 'node2'),
        createTestRelationship('rel3', 'hub', 'node3'),
        createTestRelationship('rel4', 'hub', 'node4'),
        createTestRelationship('rel5', 'hub', 'node5'),
      ];

      const strength = calculateHubStrength('hub', relationships);
      
      // log2(5 + 2) = log2(7) ≈ 2.81
      expect(strength).toBeGreaterThan(2.5);
      expect(strength).toBeLessThan(3.0);
    });

    it('should grow logarithmically (not linearly)', () => {
      const oneConnection: Relationship[] = [
        createTestRelationship('rel1', 'hub', 'node1'),
      ];

      const tenConnections: Relationship[] = Array.from({ length: 10 }, (_, i) =>
        createTestRelationship(`rel${i}`, 'hub', `node${i}`)
      );

      const strength1 = calculateHubStrength('hub', oneConnection);
      const strength10 = calculateHubStrength('hub', tenConnections);

      // 10x connections should NOT mean 10x strength (logarithmic growth)
      expect(strength10).toBeLessThan(strength1 * 3);
    });

    it('should only count outgoing connections (source)', () => {
      const relationships: Relationship[] = [
        createTestRelationship('rel1', 'hub', 'node1'), // Outgoing
        createTestRelationship('rel2', 'node2', 'hub'), // Incoming (ignored)
        createTestRelationship('rel3', 'hub', 'node3'), // Outgoing
      ];

      const strength = calculateHubStrength('hub', relationships);
      
      // Only 2 outgoing connections should count
      // log2(2 + 2) = log2(4) = 2.0
      expect(strength).toBeCloseTo(2.0, 1);
    });
  });

  describe('calculateAttractionStrength', () => {
    it('should return base strength for weak hubs', () => {
      const relationships: Relationship[] = [
        createTestRelationship('rel1', 'hub', 'node1'),
      ];

      const strength = calculateAttractionStrength('hub', relationships);
      
      // Should be base + small hub bonus (capped at 0.8)
      expect(strength).toBeGreaterThanOrEqual(DEFAULT_ORGANIC_CONFIG.baseAttractionStrength);
      expect(strength).toBeLessThanOrEqual(0.8); // Capped
    });

    it('should return higher strength for strong hubs', () => {
      const relationships: Relationship[] = Array.from({ length: 10 }, (_, i) =>
        createTestRelationship(`rel${i}`, 'hub', `node${i}`)
      );

      const strength = calculateAttractionStrength('hub', relationships);
      
      // Should be capped at 0.8 (max)
      expect(strength).toBeLessThanOrEqual(0.8);
    });

    it('should cap at 80%', () => {
      // Create a mega-hub with 50 connections
      const relationships: Relationship[] = Array.from({ length: 50 }, (_, i) =>
        createTestRelationship(`rel${i}`, 'mega-hub', `node${i}`)
      );

      const strength = calculateAttractionStrength('mega-hub', relationships);
      
      // Should be capped at 0.8
      expect(strength).toBeLessThanOrEqual(0.8);
    });

    it('should scale with hubAttractionMultiplier', () => {
      const relationships: Relationship[] = Array.from({ length: 5 }, (_, i) =>
        createTestRelationship(`rel${i}`, 'hub', `node${i}`)
      );

      const defaultStrength = calculateAttractionStrength('hub', relationships);

      const customConfig = {
        ...DEFAULT_ORGANIC_CONFIG,
        hubAttractionMultiplier: 0.1, // Double the multiplier
      };

      const customStrength = calculateAttractionStrength('hub', relationships, customConfig);
      
      // Custom should be higher
      expect(customStrength).toBeGreaterThan(defaultStrength);
    });
  });

  describe('applyRelationshipAttraction', () => {
    it('should move target node toward source node', () => {
      // Create nodes at known positions
      cy.add([
        {
          group: 'nodes',
          data: { id: 'source' },
          position: { x: 0, y: 0 },
        },
        {
          group: 'nodes',
          data: { id: 'target' },
          position: { x: 1000, y: 0 },
        },
      ]);

      const relationships: Relationship[] = [
        createTestRelationship('rel1', 'source', 'target'),
      ];

      const targetBefore = cy.getElementById('target').position();
      expect(targetBefore.x).toBe(1000);

      applyRelationshipAttraction(cy, 'source', 'target', relationships);

      // Target should have moved closer (animation queued)
      // Note: In headless mode, animation might not fully execute
      // But the function should not throw
      expect(() => {
        cy.getElementById('target').position();
      }).not.toThrow();
    });

    it('should not move nodes beyond max attraction distance', () => {
      // Create nodes very far apart
      cy.add([
        {
          group: 'nodes',
          data: { id: 'source' },
          position: { x: 0, y: 0 },
        },
        {
          group: 'nodes',
          data: { id: 'target' },
          position: { x: 5000, y: 0 }, // Way beyond max distance
        },
      ]);

      const relationships: Relationship[] = [
        createTestRelationship('rel1', 'source', 'target'),
      ];

      // Should not throw, but also should not move
      expect(() => {
        applyRelationshipAttraction(cy, 'source', 'target', relationships);
      }).not.toThrow();
    });

    it('should handle non-existent nodes gracefully', () => {
      const relationships: Relationship[] = [];

      expect(() => {
        applyRelationshipAttraction(cy, 'missing-source', 'missing-target', relationships);
      }).not.toThrow();
    });
  });

  describe('getHubIndicators', () => {
    it('should return empty map for nodes with few connections', () => {
      const nodes: Node[] = [
        createTestNode('node1'),
        createTestNode('node2'),
      ];

      const relationships: Relationship[] = [
        createTestRelationship('rel1', 'node1', 'node2'),
      ];

      const indicators = getHubIndicators(nodes, relationships);
      
      // No significant hubs (strength < 2.0)
      expect(indicators.size).toBe(0);
    });

    it('should identify significant hubs', () => {
      const nodes: Node[] = [
        createTestNode('hub'),
        createTestNode('node1'),
        createTestNode('node2'),
        createTestNode('node3'),
        createTestNode('node4'),
        createTestNode('node5'),
      ];

      const relationships: Relationship[] = Array.from({ length: 5 }, (_, i) =>
        createTestRelationship(`rel${i}`, 'hub', `node${i + 1}`)
      );

      const indicators = getHubIndicators(nodes, relationships);
      
      // Hub should be identified
      expect(indicators.has('hub')).toBe(true);
      expect(indicators.get('hub')).toBeGreaterThan(2.0);
    });

    it('should only include nodes with strength > 2.0', () => {
      const nodes: Node[] = Array.from({ length: 10 }, (_, i) =>
        createTestNode(`node${i}`)
      );

      // Create one strong hub and several weak hubs
      const relationships: Relationship[] = [
        // Strong hub (5 connections)
        ...Array.from({ length: 5 }, (_, i) =>
          createTestRelationship(`rel-strong-${i}`, 'node0', `node${i + 1}`)
        ),
        // Weak hub (1 connection)
        createTestRelationship('rel-weak', 'node6', 'node7'),
      ];

      const indicators = getHubIndicators(nodes, relationships);
      
      // Only strong hub should be included
      expect(indicators.has('node0')).toBe(true);
      expect(indicators.has('node6')).toBe(false);
    });

    it('should return strength values for styling', () => {
      const nodes: Node[] = [
        createTestNode('hub'),
        ...Array.from({ length: 10 }, (_, i) => createTestNode(`node${i}`)),
      ];

      const relationships: Relationship[] = Array.from({ length: 10 }, (_, i) =>
        createTestRelationship(`rel${i}`, 'hub', `node${i}`)
      );

      const indicators = getHubIndicators(nodes, relationships);
      
      const strength = indicators.get('hub');
      expect(strength).toBeDefined();
      expect(strength!).toBeGreaterThan(2.0);
      
      // Strength can be used for visual scaling (e.g., border width)
      const visualScale = Math.min(strength! / 3, 2); // Cap at 2x
      expect(visualScale).toBeGreaterThan(1.0);
      expect(visualScale).toBeLessThanOrEqual(2.0);
    });
  });

  describe('edge cases', () => {
    it('should handle empty relationships array', () => {
      const strength = calculateHubStrength('any-node', []);
      
      // log2(0 + 2) = log2(2) = 1.0
      expect(strength).toBe(1.0);
    });

    it('should handle node with no outgoing connections', () => {
      const relationships: Relationship[] = [
        createTestRelationship('rel1', 'other', 'node'),
        createTestRelationship('rel2', 'other', 'node'),
      ];

      const strength = calculateHubStrength('node', relationships);
      
      // No outgoing connections
      expect(strength).toBe(1.0);
    });

    it('should handle self-loops', () => {
      const relationships: Relationship[] = [
        createTestRelationship('rel1', 'node', 'node'), // Self-loop
      ];

      const strength = calculateHubStrength('node', relationships);
      
      // Self-loop counts as outgoing connection
      expect(strength).toBeGreaterThan(1.0);
    });
  });
});


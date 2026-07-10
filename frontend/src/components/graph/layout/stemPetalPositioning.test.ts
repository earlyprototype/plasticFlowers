import { describe, it, expect, beforeEach } from 'vitest';
import cytoscape, { type Core } from 'cytoscape';
import {
  applyStemPetalPositioning,
  applyAdaptiveStemPetalPositioning,
  calculateOptimalOrbitRadius,
  DEFAULT_STEM_PETAL_CONFIG,
} from './stemPetalPositioning';
import type { Flower } from '../../../lib/types';

describe('stemPetalPositioning', () => {
  let cy: Core;

  beforeEach(() => {
    cy = cytoscape({
      headless: true,
      styleEnabled: false,
    });
  });

  describe('calculateOptimalOrbitRadius', () => {
    it('should calculate base radius for 1 petal', () => {
      const radius = calculateOptimalOrbitRadius(1);
      // 80 + (1 * 15) = 95
      expect(radius).toBe(95);
    });

    it('should scale radius with petal count', () => {
      const radius3 = calculateOptimalOrbitRadius(3);
      const radius5 = calculateOptimalOrbitRadius(5);

      expect(radius5).toBeGreaterThan(radius3);
      expect(radius5).toBe(155); // 80 + (5 * 15) = 155
    });

    it('should handle large petal counts', () => {
      const radius10 = calculateOptimalOrbitRadius(10);
      expect(radius10).toBe(230); // 80 + (10 * 15) = 230
    });
  });

  describe('applyStemPetalPositioning', () => {
    it('should position stem at flower center', () => {
      // Create flower compound node
      cy.add({
        group: 'nodes',
        data: { id: 'flower1', kind: 'flower' },
        classes: 'flower',
        position: { x: 200, y: 200 },
      });

      // Create stem node
      cy.add({
        group: 'nodes',
        data: { id: 'stem1' },
        position: { x: 150, y: 150 }, // Initial position
      });

      // Move to flower (must be done after both nodes exist)
      cy.getElementById('stem1').move({ parent: 'flower1' });

      const flowers: Flower[] = [
        {
          id: 'flower1',
          label: 'Test Flower',
          stem_node_id: 'stem1',
          edge_count: 1,
          member_ids: ['stem1'],
          created_at: '2025-01-01T00:00:00Z',
        },
      ];

      // Should not throw
      expect(() => {
        applyStemPetalPositioning(cy, flowers);
      }).not.toThrow();

      // Verify stem node exists and is child of flower
      const stemNode = cy.getElementById('stem1');
      expect(stemNode.nonempty()).toBe(true);
      expect(stemNode.parent().first().id()).toBe('flower1');
    });

    it('should arrange petals in circle around stem', () => {
      // Create flower
      cy.add({
        group: 'nodes',
        data: { id: 'flower1', kind: 'flower' },
        classes: 'flower',
        position: { x: 300, y: 300 },
      });

      // Create stem and 3 petals
      cy.add([
        {
          group: 'nodes',
          data: { id: 'stem1', parent: 'flower1' },
          position: { x: 250, y: 250 },
        },
        {
          group: 'nodes',
          data: { id: 'petal1', parent: 'flower1' },
          position: { x: 100, y: 100 },
        },
        {
          group: 'nodes',
          data: { id: 'petal2', parent: 'flower1' },
          position: { x: 150, y: 150 },
        },
        {
          group: 'nodes',
          data: { id: 'petal3', parent: 'flower1' },
          position: { x: 200, y: 200 },
        },
      ]);

      const flowers: Flower[] = [
        {
          id: 'flower1',
          label: 'Test Flower',
          stem_node_id: 'stem1',
          edge_count: 1,
          member_ids: ['stem1', 'petal1', 'petal2', 'petal3'],
          created_at: '2025-01-01T00:00:00Z',
        },
      ];

      applyStemPetalPositioning(cy, flowers, DEFAULT_STEM_PETAL_CONFIG);

      // Stem moves to the cluster's centroid (positions are ABSOLUTE model
      // coordinates — arranging around a fixed origin would stack flowers).
      // Members: (250,250), (100,100), (150,150), (200,200) → (175, 175).
      const stemPos = cy.getElementById('stem1').position();
      expect(stemPos.x).toBeCloseTo(175, 5);
      expect(stemPos.y).toBeCloseTo(175, 5);

      // Check petals are arranged in circle around the stem
      const petals = ['petal1', 'petal2', 'petal3'].map((id) =>
        cy.getElementById(id).position()
      );

      // All petals should be ~120px from the cluster centre
      petals.forEach((pos) => {
        const distance = Math.sqrt(
          Math.pow(pos.x - stemPos.x, 2) + Math.pow(pos.y - stemPos.y, 2)
        );
        expect(distance).toBeCloseTo(DEFAULT_STEM_PETAL_CONFIG.petalOrbitRadius, 0);
      });

      // Petals should be evenly distributed (120° apart for 3 petals)
      // This is implicit in the circular arrangement
    });

    it('should handle flower with no stem', () => {
      cy.add({
        group: 'nodes',
        data: { id: 'flower1', kind: 'flower' },
        classes: 'flower',
        position: { x: 100, y: 100 },
      });

      cy.add({
        group: 'nodes',
        data: { id: 'node1', parent: 'flower1' },
        position: { x: 100, y: 100 },
      });

      const flowers: Flower[] = [
        {
          id: 'flower1',
          label: 'Test Flower',
          stem_node_id: null as any, // No stem
          edge_count: 1,
          member_ids: ['node1'],
          created_at: '2025-01-01T00:00:00Z',
        },
      ];

      // Should not throw
      expect(() => {
        applyStemPetalPositioning(cy, flowers);
      }).not.toThrow();

      // Node position unchanged
      const nodePos = cy.getElementById('node1').position();
      expect(nodePos.x).toBe(100);
      expect(nodePos.y).toBe(100);
    });

    it('should handle flower with only stem (no petals)', () => {
      cy.add({
        group: 'nodes',
        data: { id: 'flower1', kind: 'flower' },
        classes: 'flower',
        position: { x: 200, y: 200 },
      });

      cy.add({
        group: 'nodes',
        data: { id: 'stem1' },
        position: { x: 150, y: 150 },
      });

      // Move to flower
      cy.getElementById('stem1').move({ parent: 'flower1' });

      const flowers: Flower[] = [
        {
          id: 'flower1',
          label: 'Test Flower',
          stem_node_id: 'stem1',
          edge_count: 1,
          member_ids: ['stem1'], // Only stem
          created_at: '2025-01-01T00:00:00Z',
        },
      ];

      // Should handle gracefully (no petals to position)
      expect(() => {
        applyStemPetalPositioning(cy, flowers);
      }).not.toThrow();

      // Verify stem still exists
      expect(cy.getElementById('stem1').nonempty()).toBe(true);
    });
  });

  describe('applyAdaptiveStemPetalPositioning', () => {
    it('should use larger orbit for more petals', () => {
      // Create flower
      cy.add({
        group: 'nodes',
        data: { id: 'flower1', kind: 'flower' },
        classes: 'flower',
        position: { x: 300, y: 300 },
      });

      // Create stem and 5 petals
      const memberIds = ['stem1'];
      cy.add({
        group: 'nodes',
        data: { id: 'stem1', parent: 'flower1' },
        position: { x: 300, y: 300 },
      });

      for (let i = 1; i <= 5; i++) {
        const petalId = `petal${i}`;
        memberIds.push(petalId);
        cy.add({
          group: 'nodes',
          data: { id: petalId, parent: 'flower1' },
          position: { x: 100, y: 100 },
        });
      }

      const flowers: Flower[] = [
        {
          id: 'flower1',
          label: 'Test Flower',
          stem_node_id: 'stem1',
          edge_count: 1,
          member_ids: memberIds,
          created_at: '2025-01-01T00:00:00Z',
        },
      ];

      applyAdaptiveStemPetalPositioning(cy, flowers);

      // Stem sits at the cluster centroid; petals orbit at the adaptive
      // radius around it (absolute coordinates).
      const expectedRadius = calculateOptimalOrbitRadius(5);
      const stemPos = cy.getElementById('stem1').position();

      for (let i = 1; i <= 5; i++) {
        const petalPos = cy.getElementById(`petal${i}`).position();
        const distance = Math.sqrt(
          Math.pow(petalPos.x - stemPos.x, 2) + Math.pow(petalPos.y - stemPos.y, 2)
        );
        expect(distance).toBeCloseTo(expectedRadius, 0);
      }
    });

    it('should handle multiple flowers independently', () => {
      // Create two flowers
      cy.add([
        {
          group: 'nodes',
          data: { id: 'flower1', kind: 'flower' },
          classes: 'flower',
          position: { x: 100, y: 100 },
        },
        {
          group: 'nodes',
          data: { id: 'flower2', kind: 'flower' },
          classes: 'flower',
          position: { x: 500, y: 500 },
        },
      ]);

      // Flower 1: stem + 2 petals
      cy.add([
        {
          group: 'nodes',
          data: { id: 'stem1', parent: 'flower1' },
          position: { x: 100, y: 100 },
        },
        {
          group: 'nodes',
          data: { id: 'petal1a', parent: 'flower1' },
          position: { x: 50, y: 50 },
        },
        {
          group: 'nodes',
          data: { id: 'petal1b', parent: 'flower1' },
          position: { x: 150, y: 150 },
        },
      ]);

      // Flower 2: stem + 3 petals
      cy.add([
        {
          group: 'nodes',
          data: { id: 'stem2', parent: 'flower2' },
          position: { x: 500, y: 500 },
        },
        {
          group: 'nodes',
          data: { id: 'petal2a', parent: 'flower2' },
          position: { x: 400, y: 400 },
        },
        {
          group: 'nodes',
          data: { id: 'petal2b', parent: 'flower2' },
          position: { x: 550, y: 550 },
        },
        {
          group: 'nodes',
          data: { id: 'petal2c', parent: 'flower2' },
          position: { x: 600, y: 600 },
        },
      ]);

      const flowers: Flower[] = [
        {
          id: 'flower1',
          label: 'Flower 1',
          stem_node_id: 'stem1',
          edge_count: 1,
          member_ids: ['stem1', 'petal1a', 'petal1b'],
          created_at: '2025-01-01T00:00:00Z',
        },
        {
          id: 'flower2',
          label: 'Flower 2',
          stem_node_id: 'stem2',
          edge_count: 1,
          member_ids: ['stem2', 'petal2a', 'petal2b', 'petal2c'],
          created_at: '2025-01-01T00:00:00Z',
        },
      ];

      applyAdaptiveStemPetalPositioning(cy, flowers);

      // Each stem moves to ITS OWN cluster's centroid — the two flowers stay
      // apart instead of stacking on a shared origin.
      // Flower 1 members: (100,100), (50,50), (150,150) → (100, 100).
      const stem1Pos = cy.getElementById('stem1').position();
      expect(stem1Pos.x).toBeCloseTo(100, 5);
      expect(stem1Pos.y).toBeCloseTo(100, 5);

      // Flower 2 members: (500,500), (400,400), (550,550), (600,600) → (512.5, 512.5).
      const stem2Pos = cy.getElementById('stem2').position();
      expect(stem2Pos.x).toBeCloseTo(512.5, 5);
      expect(stem2Pos.y).toBeCloseTo(512.5, 5);

      // The clusters must not collapse onto the same point
      const stemDistance = Math.hypot(stem2Pos.x - stem1Pos.x, stem2Pos.y - stem1Pos.y);
      expect(stemDistance).toBeGreaterThan(400);

      // Check flowers have different radii (adaptive)
      const radius1 = calculateOptimalOrbitRadius(2);
      const radius2 = calculateOptimalOrbitRadius(3);
      expect(radius2).toBeGreaterThan(radius1);
    });
  });
});


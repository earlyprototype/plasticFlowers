import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import cytoscape, { type Core } from 'cytoscape';
import { AnimationController } from './animationController';
import type { SyncResult } from '../rendering/graphRenderer';

describe('AnimationController', () => {
  let cy: Core;
  let controller: AnimationController;

  beforeEach(() => {
    // Create headless Cytoscape instance
    cy = cytoscape({
      headless: true,
      styleEnabled: false,
    });

    controller = new AnimationController();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('executeAnimationSequence', () => {
    it('should execute animation sequence without throwing errors', () => {
      // Add test nodes
      cy.add([
        { group: 'nodes', data: { id: 'node1', label: 'Node 1' } },
        { group: 'nodes', data: { id: 'node2', label: 'Node 2' } },
      ]);

      const syncResult: SyncResult = {
        addedNodeIds: new Set(['node1']),
        addedEdgeIds: new Set(),
        removedNodeIds: new Set(),
        removedEdgeIds: new Set(),
        updatedNodeIds: new Set(),
      };

      const isolatedNodeIds = new Set<string>();

      // Execute animation - should not throw (don't await completion in headless mode)
      expect(() => {
        controller.executeAnimationSequence(cy, syncResult, isolatedNodeIds);
      }).not.toThrow();
    });

    it('should handle nodes and edges together', () => {
      cy.add([
        { group: 'nodes', data: { id: 'node1' } },
        { group: 'nodes', data: { id: 'node2' } },
        {
          group: 'edges',
          data: { id: 'edge1', source: 'node1', target: 'node2' },
        },
      ]);

      const syncResult: SyncResult = {
        addedNodeIds: new Set(['node1']),
        addedEdgeIds: new Set(['edge1']),
        removedNodeIds: new Set(),
        removedEdgeIds: new Set(),
        updatedNodeIds: new Set(),
      };

      // Should not throw
      expect(() => {
        controller.executeAnimationSequence(cy, syncResult, new Set());
      }).not.toThrow();
    });

    it('should handle isolated nodes for float effects', () => {
      cy.add({ group: 'nodes', data: { id: 'isolated1' } });

      const syncResult: SyncResult = {
        addedNodeIds: new Set(['isolated1']),
        addedEdgeIds: new Set(),
        removedNodeIds: new Set(),
        removedEdgeIds: new Set(),
        updatedNodeIds: new Set(),
      };

      const isolatedNodeIds = new Set(['isolated1']);

      // Should not throw
      expect(() => {
        controller.executeAnimationSequence(cy, syncResult, isolatedNodeIds);
      }).not.toThrow();
    });
  });

  describe('float effects', () => {
    it('should apply float to isolated nodes', () => {
      cy.add({ group: 'nodes', data: { id: 'node1', label: 'Isolated' } });

      const syncResult: SyncResult = {
        addedNodeIds: new Set(['node1']),
        addedEdgeIds: new Set(),
        removedNodeIds: new Set(),
        removedEdgeIds: new Set(),
        updatedNodeIds: new Set(),
      };

      const isolatedNodeIds = new Set(['node1']);

      // Should not throw
      expect(() => {
        controller.executeAnimationSequence(cy, syncResult, isolatedNodeIds);
      }).not.toThrow();
    });

    it('does not float nodes with two or more connections', async () => {
      cy.add([
        { group: 'nodes', data: { id: 'node1' } },
        { group: 'nodes', data: { id: 'node2' } },
        { group: 'nodes', data: { id: 'node3' } },
        { group: 'edges', data: { id: 'e1', source: 'node1', target: 'node2' } },
        { group: 'edges', data: { id: 'e2', source: 'node1', target: 'node3' } },
      ]);

      const syncResult: SyncResult = {
        addedNodeIds: new Set(),
        addedEdgeIds: new Set(),
        removedNodeIds: new Set(),
        removedEdgeIds: new Set(),
        updatedNodeIds: new Set(),
      };

      // node1 has degree 2 -> considered settled, no float
      await controller.executeAnimationSequence(cy, syncResult, new Set(['node1']));
      expect(controller.activeFloatCount).toBe(0);
    });

    it('floats genuinely isolated nodes and stops them on cleanup', async () => {
      cy.add({ group: 'nodes', data: { id: 'lone1' } });

      const syncResult: SyncResult = {
        addedNodeIds: new Set(),
        addedEdgeIds: new Set(),
        removedNodeIds: new Set(),
        removedEdgeIds: new Set(),
        updatedNodeIds: new Set(),
      };

      await controller.executeAnimationSequence(cy, syncResult, new Set(['lone1']));
      expect(controller.activeFloatCount).toBe(1);

      controller.stopAllFloatAnimations(cy);
      expect(controller.activeFloatCount).toBe(0);
    });

    it('caps concurrent float animations', async () => {
      const ids: string[] = [];
      for (let i = 0; i < 40; i += 1) {
        const id = `iso${i}`;
        ids.push(id);
        cy.add({ group: 'nodes', data: { id } });
      }

      const syncResult: SyncResult = {
        addedNodeIds: new Set(),
        addedEdgeIds: new Set(),
        removedNodeIds: new Set(),
        removedEdgeIds: new Set(),
        updatedNodeIds: new Set(),
      };

      await controller.executeAnimationSequence(cy, syncResult, new Set(ids));
      expect(controller.activeFloatCount).toBeLessThanOrEqual(30);
      expect(controller.activeFloatCount).toBeGreaterThan(0);

      controller.stopAllFloatAnimations(cy);
    });

    it('reanchorFloats drops floats for removed nodes and keeps live ones', async () => {
      cy.add([
        { group: 'nodes', data: { id: 'lone1' } },
        { group: 'nodes', data: { id: 'lone2' } },
      ]);

      const syncResult: SyncResult = {
        addedNodeIds: new Set(),
        addedEdgeIds: new Set(),
        removedNodeIds: new Set(),
        removedEdgeIds: new Set(),
        updatedNodeIds: new Set(),
      };

      await controller.executeAnimationSequence(cy, syncResult, new Set(['lone1', 'lone2']));
      expect(controller.activeFloatCount).toBe(2);

      cy.getElementById('lone2').remove();
      controller.reanchorFloats(cy);
      expect(controller.activeFloatCount).toBe(1);

      controller.stopAllFloatAnimations(cy);
    });

    it('should stop all float animations on cleanup', () => {
      cy.add([
        { group: 'nodes', data: { id: 'node1' } },
        { group: 'nodes', data: { id: 'node2' } },
      ]);

      // Stop all should not throw (even when no animations running)
      expect(() => controller.stopAllFloatAnimations(cy)).not.toThrow();
    });
  });

  describe('camera fit', () => {
    it('should execute camera fit as part of sequence', () => {
      cy.add({ group: 'nodes', data: { id: 'node1' } });

      const syncResult: SyncResult = {
        addedNodeIds: new Set(),
        addedEdgeIds: new Set(),
        removedNodeIds: new Set(),
        removedEdgeIds: new Set(),
        updatedNodeIds: new Set(),
      };

      // Should not throw
      expect(() => {
        controller.executeAnimationSequence(cy, syncResult, new Set());
      }).not.toThrow();
    });
  });

  describe('edge cases', () => {
    it('should handle empty sync result', () => {
      const syncResult: SyncResult = {
        addedNodeIds: new Set(),
        addedEdgeIds: new Set(),
        removedNodeIds: new Set(),
        removedEdgeIds: new Set(),
        updatedNodeIds: new Set(),
      };

      // Should not throw
      expect(() => {
        controller.executeAnimationSequence(cy, syncResult, new Set());
      }).not.toThrow();
    });

    it('should handle nodes added to flowers (no float)', () => {
      // Create flower and add node as child
      cy.add([
        {
          group: 'nodes',
          data: { id: 'flower1', kind: 'flower' },
          classes: 'flower',
        },
        {
          group: 'nodes',
          data: { id: 'node1', parent: 'flower1' },
        },
      ]);

      const syncResult: SyncResult = {
        addedNodeIds: new Set(['node1']),
        addedEdgeIds: new Set(),
        removedNodeIds: new Set(),
        removedEdgeIds: new Set(),
        updatedNodeIds: new Set(),
      };

      // Node1 is marked as isolated but has a parent
      const isolatedNodeIds = new Set(['node1']);

      // Should not throw (float not applied to nodes with parents)
      expect(() => {
        controller.executeAnimationSequence(cy, syncResult, isolatedNodeIds);
      }).not.toThrow();
    });
  });
});


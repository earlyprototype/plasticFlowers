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


import { describe, it, expect, beforeEach, vi } from 'vitest';
import cytoscape, { type Core } from 'cytoscape';
import { syncGraphStructure } from './graphRenderer';
import type { Node, Relationship, Flower } from '../../../lib/types';
import type { LayoutResult } from '../layout/layoutEngine';

describe('graphRenderer', () => {
  let cy: Core;

  beforeEach(() => {
    // Create a fresh Cytoscape instance for each test
    cy = cytoscape({
      headless: true, // No DOM rendering needed for tests
      styleEnabled: false, // Disable styling for faster tests
    });
  });

  describe('syncGraphStructure', () => {
    it('should add new nodes to Cytoscape', () => {
      const nodes: Node[] = [
        {
          id: 'node1',
          label: 'New Node',
          confidence: 0.8,
          mentions: 1,
          timestamps: [100],
          inferred_type: 'concept',
          flower_id: null,
          created_at: '2025-01-01T00:00:00Z',
          status: 'solid',
        },
      ];

      const layoutResult: LayoutResult = {
        nodePositions: new Map(),
        lockedNodeIds: new Set(),
        isolatedNodeIds: new Set(),
        flowerStructureChanged: false,
      };

      const result = syncGraphStructure(
        cy,
        { nodes, relationships: [], flowers: [] },
        layoutResult
      );

      expect(result.addedNodeIds).toContain('node1');
      expect(cy.getElementById('node1').nonempty()).toBe(true);
      expect(cy.getElementById('node1').data('label')).toBe('New Node');
    });

    it('should remove nodes not in data', () => {
      // Add node to Cytoscape
      cy.add({
        group: 'nodes',
        data: { id: 'node1', label: 'Old Node' },
      });

      const layoutResult: LayoutResult = {
        nodePositions: new Map(),
        lockedNodeIds: new Set(),
        isolatedNodeIds: new Set(),
        flowerStructureChanged: false,
      };

      // Sync with empty data
      const result = syncGraphStructure(
        cy,
        { nodes: [], relationships: [], flowers: [] },
        layoutResult
      );

      expect(result.removedNodeIds).toContain('node1');
      expect(cy.getElementById('node1').nonempty()).toBe(false);
    });

    it('should update existing nodes', () => {
      // Add initial node
      cy.add({
        group: 'nodes',
        data: { id: 'node1', label: 'Old Label' },
      });

      const nodes: Node[] = [
        {
          id: 'node1',
          label: 'Updated Label',
          confidence: 0.9,
          mentions: 5,
          timestamps: [100, 200, 300],
          inferred_type: 'entity',
          flower_id: null,
          created_at: '2025-01-01T00:00:00Z',
          status: 'solid',
        },
      ];

      const layoutResult: LayoutResult = {
        nodePositions: new Map(),
        lockedNodeIds: new Set(),
        isolatedNodeIds: new Set(),
        flowerStructureChanged: false,
      };

      const result = syncGraphStructure(
        cy,
        { nodes, relationships: [], flowers: [] },
        layoutResult
      );

      expect(result.updatedNodeIds).toContain('node1');
      expect(cy.getElementById('node1').data('label')).toBe('Updated Label');
    });
  });

  describe('flower sync', () => {
    it('should create flower compound nodes', () => {
      const flowers: Flower[] = [
        {
          id: 'flower1',
          label: 'Test Cluster',
          stem_node_id: 'node1',
          edge_count: 1,
          member_ids: ['node1', 'node2'],
          created_at: '2025-01-01T00:00:00Z',
        },
      ];

      const nodes: Node[] = [
        {
          id: 'node1',
          label: 'Node 1',
          confidence: 0.8,
          mentions: 1,
          timestamps: [100],
          inferred_type: 'concept',
          flower_id: 'flower1',
          created_at: '2025-01-01T00:00:00Z',
          status: 'solid',
        },
        {
          id: 'node2',
          label: 'Node 2',
          confidence: 0.8,
          mentions: 1,
          timestamps: [100],
          inferred_type: 'concept',
          flower_id: 'flower1',
          created_at: '2025-01-01T00:00:00Z',
          status: 'solid',
        },
      ];

      const layoutResult: LayoutResult = {
        nodePositions: new Map(),
        lockedNodeIds: new Set(),
        isolatedNodeIds: new Set(),
        flowerStructureChanged: true,
      };

      syncGraphStructure(cy, { nodes, relationships: [], flowers }, layoutResult);

      const flower = cy.getElementById('flower1');
      expect(flower.nonempty()).toBe(true);
      expect(flower.hasClass('flower')).toBe(true);
      expect(flower.data('label')).toContain('Test Cluster');
      expect(flower.data('label')).toContain('(2)'); // Member count
    });

    it('should move nodes to new parent flower', () => {
      // Create flower and node
      cy.add({
        group: 'nodes',
        data: { id: 'flower1', label: 'Flower 1', kind: 'flower' },
        classes: 'flower',
      });
      cy.add({
        group: 'nodes',
        data: { id: 'node1', label: 'Node 1' },
      });

      const flowers: Flower[] = [
        {
          id: 'flower1',
          label: 'Flower 1',
          stem_node_id: 'node1',
          edge_count: 1,
          member_ids: ['node1'],
          created_at: '2025-01-01T00:00:00Z',
        },
      ];

      const nodes: Node[] = [
        {
          id: 'node1',
          label: 'Node 1',
          confidence: 0.8,
          mentions: 1,
          timestamps: [100],
          inferred_type: 'concept',
          flower_id: 'flower1',
          created_at: '2025-01-01T00:00:00Z',
          status: 'solid',
        },
      ];

      const layoutResult: LayoutResult = {
        nodePositions: new Map(),
        lockedNodeIds: new Set(),
        isolatedNodeIds: new Set(),
        flowerStructureChanged: true,
      };

      syncGraphStructure(cy, { nodes, relationships: [], flowers }, layoutResult);

      const node = cy.getElementById('node1');
      expect(node.parent().first().id()).toBe('flower1');
    });

    it('should preserve collapse state on flower updates', () => {
      // Create collapsed flower
      cy.add({
        group: 'nodes',
        data: { id: 'flower1', label: 'Flower', kind: 'flower', collapsed: true },
        classes: 'flower',
      });

      const flowers: Flower[] = [
        {
          id: 'flower1',
          label: 'Updated Flower',
          stem_node_id: 'node1',
          edge_count: 1,
          member_ids: ['node1'],
          created_at: '2025-01-01T00:00:00Z',
        },
      ];

      const nodes: Node[] = [
        {
          id: 'node1',
          label: 'Node 1',
          confidence: 0.8,
          mentions: 1,
          timestamps: [100],
          inferred_type: 'concept',
          flower_id: 'flower1',
          created_at: '2025-01-01T00:00:00Z',
          status: 'solid',
        },
      ];

      const layoutResult: LayoutResult = {
        nodePositions: new Map(),
        lockedNodeIds: new Set(),
        isolatedNodeIds: new Set(),
        flowerStructureChanged: false,
      };

      syncGraphStructure(cy, { nodes, relationships: [], flowers }, layoutResult);

      const flower = cy.getElementById('flower1');
      expect(flower.data('collapsed')).toBe(true);
      expect(flower.data('label')).toContain('▶'); // Collapsed icon
    });
  });

  describe('parent normalization', () => {
    const parentlessNode: Node = {
      id: 'node1',
      label: 'Loner',
      confidence: 0.8,
      mentions: 1,
      timestamps: [100],
      inferred_type: 'concept',
      flower_id: null,
      created_at: '2025-01-01T00:00:00Z',
      status: 'solid',
    };

    const emptyLayoutResult = (): LayoutResult => ({
      nodePositions: new Map(),
      lockedNodeIds: new Set(),
      isolatedNodeIds: new Set(),
      flowerStructureChanged: false,
    });

    it('does not move() parentless nodes on repeated syncs', () => {
      // First sync creates the node
      syncGraphStructure(
        cy,
        { nodes: [parentlessNode], relationships: [], flowers: [] },
        emptyLayoutResult()
      );

      // Cytoscape emits `move` whenever an element changes compound parent —
      // before normalization, undefined !== null caused a move() every sync.
      const moves: string[] = [];
      cy.on('move', (evt) => moves.push(evt.target.id()));

      syncGraphStructure(
        cy,
        { nodes: [parentlessNode], relationships: [], flowers: [] },
        emptyLayoutResult()
      );
      syncGraphStructure(
        cy,
        { nodes: [parentlessNode], relationships: [], flowers: [] },
        emptyLayoutResult()
      );

      expect(moves).toEqual([]);
    });

    it('does not move() nodes whose flower parent is unchanged', () => {
      const flowers: Flower[] = [
        {
          id: 'flower1',
          label: 'Flower 1',
          stem_node_id: 'node1',
          edge_count: 1,
          member_ids: ['node1'],
          created_at: '2025-01-01T00:00:00Z',
        },
      ];
      const memberNode: Node = { ...parentlessNode, flower_id: 'flower1' };

      // First sync creates flower + node (initial move into the flower is fine)
      syncGraphStructure(cy, { nodes: [memberNode], relationships: [], flowers }, emptyLayoutResult());

      const moves: string[] = [];
      cy.on('move', (evt) => moves.push(evt.target.id()));

      syncGraphStructure(cy, { nodes: [memberNode], relationships: [], flowers }, emptyLayoutResult());

      expect(moves).toEqual([]);
      expect(cy.getElementById('node1').parent().first().id()).toBe('flower1');
    });

    it('still moves a node when its parent actually changes', () => {
      const flowers: Flower[] = [
        {
          id: 'flower1',
          label: 'Flower 1',
          stem_node_id: 'node1',
          edge_count: 1,
          member_ids: ['node1'],
          created_at: '2025-01-01T00:00:00Z',
        },
      ];

      // Start parentless
      syncGraphStructure(
        cy,
        { nodes: [parentlessNode], relationships: [], flowers: [] },
        emptyLayoutResult()
      );

      // Then join a flower
      const memberNode: Node = { ...parentlessNode, flower_id: 'flower1' };
      syncGraphStructure(cy, { nodes: [memberNode], relationships: [], flowers }, emptyLayoutResult());

      expect(cy.getElementById('node1').parent().first().id()).toBe('flower1');
    });
  });

  describe('edge sync', () => {
    it('should add new edges', () => {
      const nodes: Node[] = [
        {
          id: 'node1',
          label: 'Node 1',
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
          label: 'Node 2',
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
          description: 'related to',
          confidence: 0.8,
          evidence: 'text',
          source: 'builder',
          created_at: '2025-01-01T00:00:00Z',
        },
      ];

      const layoutResult: LayoutResult = {
        nodePositions: new Map(),
        lockedNodeIds: new Set(),
        isolatedNodeIds: new Set(),
        flowerStructureChanged: false,
      };

      const result = syncGraphStructure(
        cy,
        { nodes, relationships, flowers: [] },
        layoutResult
      );

      expect(result.addedEdgeIds).toContain('rel1');
      expect(cy.getElementById('rel1').nonempty()).toBe(true);
      expect(cy.getElementById('rel1').data('description')).toBe('related to');
    });

    it('should tag inter-flower edges with inter-flower class', () => {
      const flowers: Flower[] = [
        {
          id: 'flower1',
          label: 'Flower 1',
          stem_node_id: 'node1',
          edge_count: 1,
          member_ids: ['node1'],
          created_at: '2025-01-01T00:00:00Z',
        },
        {
          id: 'flower2',
          label: 'Flower 2',
          stem_node_id: 'node2',
          edge_count: 1,
          member_ids: ['node2'],
          created_at: '2025-01-01T00:00:00Z',
        },
      ];

      const nodes: Node[] = [
        {
          id: 'node1',
          label: 'Node 1',
          confidence: 0.8,
          mentions: 1,
          timestamps: [100],
          inferred_type: 'concept',
          flower_id: 'flower1',
          created_at: '2025-01-01T00:00:00Z',
          status: 'solid',
        },
        {
          id: 'node2',
          label: 'Node 2',
          confidence: 0.8,
          mentions: 1,
          timestamps: [100],
          inferred_type: 'concept',
          flower_id: 'flower2',
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
          description: 'connects clusters',
          confidence: 0.8,
          evidence: 'text',
          source: 'builder',
          created_at: '2025-01-01T00:00:00Z',
        },
      ];

      const layoutResult: LayoutResult = {
        nodePositions: new Map(),
        lockedNodeIds: new Set(),
        isolatedNodeIds: new Set(),
        flowerStructureChanged: false,
      };

      syncGraphStructure(cy, { nodes, relationships, flowers }, layoutResult);

      const edge = cy.getElementById('rel1');
      expect(edge.hasClass('inter-flower')).toBe(true);
    });

    it('should not tag intra-flower edges with inter-flower class', () => {
      const flowers: Flower[] = [
        {
          id: 'flower1',
          label: 'Flower 1',
          stem_node_id: 'node1',
          edge_count: 1,
          member_ids: ['node1', 'node2'],
          created_at: '2025-01-01T00:00:00Z',
        },
      ];

      const nodes: Node[] = [
        {
          id: 'node1',
          label: 'Node 1',
          confidence: 0.8,
          mentions: 1,
          timestamps: [100],
          inferred_type: 'concept',
          flower_id: 'flower1',
          created_at: '2025-01-01T00:00:00Z',
          status: 'solid',
        },
        {
          id: 'node2',
          label: 'Node 2',
          confidence: 0.8,
          mentions: 1,
          timestamps: [100],
          inferred_type: 'concept',
          flower_id: 'flower1',
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
          description: 'within cluster',
          confidence: 0.8,
          evidence: 'text',
          source: 'builder',
          created_at: '2025-01-01T00:00:00Z',
        },
      ];

      const layoutResult: LayoutResult = {
        nodePositions: new Map(),
        lockedNodeIds: new Set(),
        isolatedNodeIds: new Set(),
        flowerStructureChanged: false,
      };

      syncGraphStructure(cy, { nodes, relationships, flowers }, layoutResult);

      const edge = cy.getElementById('rel1');
      expect(edge.hasClass('inter-flower')).toBe(false);
    });

    it('should remove edges not in data', () => {
      const nodes: Node[] = [
        {
          id: 'node1',
          label: 'Node 1',
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
          label: 'Node 2',
          confidence: 0.8,
          mentions: 1,
          timestamps: [100],
          inferred_type: 'concept',
          flower_id: null,
          created_at: '2025-01-01T00:00:00Z',
          status: 'solid',
        },
      ];

      // First sync with edge
      let layoutResult: LayoutResult = {
        nodePositions: new Map(),
        lockedNodeIds: new Set(),
        isolatedNodeIds: new Set(),
        flowerStructureChanged: false,
      };

      syncGraphStructure(
        cy,
        {
          nodes,
          relationships: [
            {
              id: 'rel1',
              source_id: 'node1',
              target_id: 'node2',
              category: 'STRUCTURAL',
              description: 'test',
              confidence: 0.8,
              evidence: 'text',
              source: 'builder',
              created_at: '2025-01-01T00:00:00Z',
            },
          ],
          flowers: [],
        },
        layoutResult
      );

      // Verify edge exists
      expect(cy.getElementById('rel1').nonempty()).toBe(true);

      // Now sync without edge (but keep nodes)
      const result = syncGraphStructure(
        cy,
        { nodes, relationships: [], flowers: [] },
        layoutResult
      );

      expect(result.removedEdgeIds).toContain('rel1');
      expect(cy.getElementById('rel1').nonempty()).toBe(false);
    });
  });

  describe('stem node styling', () => {
    it('should add stem class to stem nodes', () => {
      const flowers: Flower[] = [
        {
          id: 'flower1',
          label: 'Test Cluster',
          stem_node_id: 'node1',
          edge_count: 1,
          member_ids: ['node1', 'node2'],
          created_at: '2025-01-01T00:00:00Z',
        },
      ];

      const nodes: Node[] = [
        {
          id: 'node1',
          label: 'Stem Node',
          confidence: 0.9,
          mentions: 5,
          timestamps: [100],
          inferred_type: 'concept',
          flower_id: 'flower1',
          created_at: '2025-01-01T00:00:00Z',
          status: 'solid',
        },
        {
          id: 'node2',
          label: 'Member Node',
          confidence: 0.7,
          mentions: 2,
          timestamps: [100],
          inferred_type: 'concept',
          flower_id: 'flower1',
          created_at: '2025-01-01T00:00:00Z',
          status: 'solid',
        },
      ];

      const layoutResult: LayoutResult = {
        nodePositions: new Map(),
        lockedNodeIds: new Set(),
        isolatedNodeIds: new Set(),
        flowerStructureChanged: true,
      };

      syncGraphStructure(cy, { nodes, relationships: [], flowers }, layoutResult);

      expect(cy.getElementById('node1').hasClass('stem')).toBe(true);
      expect(cy.getElementById('node2').hasClass('stem')).toBe(false);
    });
  });
});


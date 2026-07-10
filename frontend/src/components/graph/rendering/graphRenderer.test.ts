import { describe, it, expect, beforeEach, vi } from 'vitest';
import cytoscape, { type Core } from 'cytoscape';
import {
  syncGraphStructure,
  PENDING_REMOVAL_SCRATCH,
  type PendingRemovalHandle,
} from './graphRenderer';
import { AnimationController, WILT_MS } from '../animation/animationController';
import {
  BIRTH_AMBER,
  BIRTH_DAWN,
  BIRTH_MOSS,
  SESSION_HUE_SPAN_MS,
  birthFill,
  birthGhostTint,
} from '../config/cartography';
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

  describe('deferred removal (wilt hook)', () => {
    const makeNode = (id: string, status: Node['status'] = 'solid'): Node => ({
      id,
      label: id,
      confidence: 0.8,
      mentions: 1,
      timestamps: [100],
      inferred_type: 'concept',
      flower_id: null,
      created_at: '2025-01-01T00:00:00Z',
      status,
    });

    const emptyLayout = (): LayoutResult => ({
      nodePositions: new Map(),
      lockedNodeIds: new Set(),
      flowerStructureChanged: false,
    });

    it('hands departing nodes to the hook instead of removing them, once', () => {
      syncGraphStructure(cy, { nodes: [makeNode('n1')], relationships: [], flowers: [] }, emptyLayout());

      const removeElement = vi.fn();
      const result = syncGraphStructure(
        cy,
        { nodes: [], relationships: [], flowers: [] },
        emptyLayout(),
        { removeElement }
      );

      // Recorded as removed, but the element is still in the graph (mid-wilt)
      expect(result.removedNodeIds).toContain('n1');
      expect(removeElement).toHaveBeenCalledTimes(1);
      expect(cy.getElementById('n1').nonempty()).toBe(true);
      expect(cy.getElementById('n1').scratch(PENDING_REMOVAL_SCRATCH)).toBeTruthy();

      // A second sync while the element departs must not re-report or re-wilt it
      const again = syncGraphStructure(
        cy,
        { nodes: [], relationships: [], flowers: [] },
        emptyLayout(),
        { removeElement }
      );
      expect(again.removedNodeIds.size).toBe(0);
      expect(removeElement).toHaveBeenCalledTimes(1);
    });

    it('cancels a pending removal when the element reappears in the data', () => {
      syncGraphStructure(cy, { nodes: [makeNode('n1')], relationships: [], flowers: [] }, emptyLayout());

      // Defer removal; simulate the animation side attaching its cancel handle
      syncGraphStructure(cy, { nodes: [], relationships: [], flowers: [] }, emptyLayout(), {
        removeElement: () => {},
      });
      const ele = cy.getElementById('n1');
      const cancel = vi.fn(() => ele.removeScratch(PENDING_REMOVAL_SCRATCH));
      ele.scratch(PENDING_REMOVAL_SCRATCH, { cancel } satisfies PendingRemovalHandle);

      // Node comes back — the wilt must be cancelled and the node updated
      const result = syncGraphStructure(
        cy,
        { nodes: [makeNode('n1')], relationships: [], flowers: [] },
        emptyLayout(),
        { removeElement: () => {} }
      );

      expect(cancel).toHaveBeenCalledTimes(1);
      expect(result.updatedNodeIds).toContain('n1');
      expect(cy.getElementById('n1').nonempty()).toBe(true);
    });

    it('integration: element is removed after the wilt completes, or revived by re-add', async () => {
      vi.useFakeTimers();
      try {
        const controller = new AnimationController({ prefersReducedMotion: () => false });
        const options = {
          removeElement: (ele: Parameters<AnimationController['wiltAndRemove']>[0]) =>
            controller.wiltAndRemove(ele),
        };

        syncGraphStructure(
          cy,
          { nodes: [makeNode('n1'), makeNode('n2')], relationships: [], flowers: [] },
          emptyLayout()
        );

        // Both depart…
        syncGraphStructure(cy, { nodes: [], relationships: [], flowers: [] }, emptyLayout(), options);
        expect(cy.getElementById('n1').nonempty()).toBe(true);
        expect(cy.getElementById('n2').nonempty()).toBe(true);

        // …but n2 is re-added mid-wilt
        syncGraphStructure(cy, { nodes: [makeNode('n2')], relationships: [], flowers: [] }, emptyLayout(), options);

        await vi.advanceTimersByTimeAsync(WILT_MS);
        expect(cy.getElementById('n1').nonempty()).toBe(false); // wilted away
        expect(cy.getElementById('n2').nonempty()).toBe(true); // revived
        expect(cy.getElementById('n2').hasClass('wilting')).toBe(false);
      } finally {
        vi.useRealTimers();
      }
    });

    it('reports ghost → solid confirmations exactly once', () => {
      // Arrives as ghost — nothing to confirm
      let result = syncGraphStructure(
        cy,
        { nodes: [makeNode('n1', 'ghost')], relationships: [], flowers: [] },
        emptyLayout()
      );
      expect(result.confirmedNodeIds.size).toBe(0);
      expect(cy.getElementById('n1').hasClass('ghost')).toBe(true);

      // Confirms — reported on the flip
      result = syncGraphStructure(
        cy,
        { nodes: [makeNode('n1', 'solid')], relationships: [], flowers: [] },
        emptyLayout()
      );
      expect(result.confirmedNodeIds).toContain('n1');
      expect(cy.getElementById('n1').hasClass('solid')).toBe(true);

      // Stays solid — never reported again
      result = syncGraphStructure(
        cy,
        { nodes: [makeNode('n1', 'solid')], relationships: [], flowers: [] },
        emptyLayout()
      );
      expect(result.confirmedNodeIds.size).toBe(0);
    });
  });

  describe('time as colour (birth colour data)', () => {
    const SESSION_START = '2026-07-10T10:00:00Z';
    const startMs = Date.parse(SESSION_START);

    const bornAt = (id: string, offsetMs: number): Node => ({
      id,
      label: id,
      confidence: 0.8,
      mentions: 1,
      timestamps: [100],
      inferred_type: 'concept',
      flower_id: null,
      created_at: new Date(startMs + offsetMs).toISOString(),
      status: 'solid',
    });

    const emptyLayout = (): LayoutResult => ({
      nodePositions: new Map(),
      lockedNodeIds: new Set(),
      flowerStructureChanged: false,
    });

    it('stamps birthColor over the fixed window from the earliest birth', () => {
      const nodes = [
        bornAt('n-dawn', 0),
        bornAt('n-moss', SESSION_HUE_SPAN_MS / 2),
        bornAt('n-amber', SESSION_HUE_SPAN_MS + 5 * 60_000), // past the window → clamps
      ];
      syncGraphStructure(cy, { nodes, relationships: [], flowers: [] }, emptyLayout());

      expect(cy.getElementById('n-dawn').data('birthColor')).toBe(BIRTH_DAWN);
      expect(cy.getElementById('n-moss').data('birthColor')).toBe(BIRTH_MOSS);
      expect(cy.getElementById('n-amber').data('birthColor')).toBe(BIRTH_AMBER);
    });

    it('stamps the paper-mixed fill and ghost tint alongside the pure colour', () => {
      syncGraphStructure(
        cy,
        { nodes: [bornAt('n1', 0)], relationships: [], flowers: [] },
        emptyLayout()
      );
      const ele = cy.getElementById('n1');
      expect(ele.data('birthFill')).toBe(birthFill(BIRTH_DAWN));
      expect(ele.data('birthGhost')).toBe(birthGhostTint(BIRTH_DAWN));
    });

    it('never repaints existing nodes as later births extend the session', () => {
      // Early session: only the first node exists.
      syncGraphStructure(
        cy,
        { nodes: [bornAt('n1', 0)], relationships: [], flowers: [] },
        emptyLayout()
      );
      const before = cy.getElementById('n1').data('birthColor');
      expect(before).toBe(BIRTH_DAWN);

      // 25 minutes later a new node arrives — n1's colour must not shift.
      syncGraphStructure(
        cy,
        { nodes: [bornAt('n1', 0), bornAt('n2', 25 * 60_000)], relationships: [], flowers: [] },
        emptyLayout()
      );
      expect(cy.getElementById('n1').data('birthColor')).toBe(before);
      expect(cy.getElementById('n2').data('birthColor')).not.toBe(BIRTH_DAWN);
    });

    it('falls back to dawn when no created_at parses (degenerate window)', () => {
      const broken: Node = { ...bornAt('n1', 0), created_at: 'not-a-date' };
      syncGraphStructure(cy, { nodes: [broken], relationships: [], flowers: [] }, emptyLayout());
      expect(cy.getElementById('n1').data('birthColor')).toBe(BIRTH_DAWN);
    });

    it('anchors the window on options.sessionStartMs (prop beats inference)', () => {
      // Only a mid-session node is synced (the dawn node is filtered out of
      // the view) — inference alone would wrongly make it the session start.
      syncGraphStructure(
        cy,
        { nodes: [bornAt('n-mid', SESSION_HUE_SPAN_MS / 2)], relationships: [], flowers: [] },
        emptyLayout(),
        { sessionStartMs: startMs }
      );
      expect(cy.getElementById('n-mid').data('birthColor')).toBe(BIRTH_MOSS);
    });

    it('ignores a non-finite sessionStartMs and falls back to inference', () => {
      syncGraphStructure(
        cy,
        { nodes: [bornAt('n1', 0)], relationships: [], flowers: [] },
        emptyLayout(),
        { sessionStartMs: Number.NaN }
      );
      expect(cy.getElementById('n1').data('birthColor')).toBe(BIRTH_DAWN);
    });

    it('stamps birth colours only at creation — updates never repaint', () => {
      syncGraphStructure(
        cy,
        { nodes: [bornAt('n1', SESSION_HUE_SPAN_MS / 2)], relationships: [], flowers: [] },
        emptyLayout(),
        { sessionStartMs: startMs }
      );
      expect(cy.getElementById('n1').data('birthColor')).toBe(BIRTH_MOSS);
      expect(cy.getElementById('n1').data('birthFill')).toBe(birthFill(BIRTH_MOSS));

      // Re-sync with a shifted anchor (simulating anchor drift, e.g. the
      // fallback inference changing as the visible set changes): the existing
      // node must keep the colour of its birth moment.
      syncGraphStructure(
        cy,
        { nodes: [bornAt('n1', SESSION_HUE_SPAN_MS / 2)], relationships: [], flowers: [] },
        emptyLayout(),
        { sessionStartMs: startMs + SESSION_HUE_SPAN_MS / 2 }
      );
      expect(cy.getElementById('n1').data('birthColor')).toBe(BIRTH_MOSS);
      expect(cy.getElementById('n1').data('birthFill')).toBe(birthFill(BIRTH_MOSS));
      expect(cy.getElementById('n1').data('birthGhost')).toBe(birthGhostTint(BIRTH_MOSS));
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
        flowerStructureChanged: true,
      };

      syncGraphStructure(cy, { nodes, relationships: [], flowers }, layoutResult);

      expect(cy.getElementById('node1').hasClass('stem')).toBe(true);
      expect(cy.getElementById('node2').hasClass('stem')).toBe(false);
    });
  });
});


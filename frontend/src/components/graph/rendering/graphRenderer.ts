import type { Core, EdgeSingular, NodeSingular } from 'cytoscape';
import type { Node, Relationship, Flower } from '../../../lib/types';
import { computeSeedPosition, type LayoutResult } from '../layout/layoutEngine';
import {
  SESSION_HUE_SPAN_MS,
  birthColor,
  birthFill,
  birthGhostTint,
} from '../config/cartography';

/**
 * Graph Renderer - Syncs data to Cytoscape
 *
 * Applies graph structure changes to Cytoscape without layout calculations or animations.
 * Handles nodes, edges, and compound flower structures.
 */

export interface SyncResult {
  addedNodeIds: Set<string>;
  addedEdgeIds: Set<string>;
  removedNodeIds: Set<string>;
  removedEdgeIds: Set<string>;
  updatedNodeIds: Set<string>;
  /**
   * Nodes whose status flipped ghost → solid in THIS sync. Populated exactly
   * once per confirmation (on the class flip), so the bloom pulse consuming
   * this set can never repeat.
   */
  confirmedNodeIds: Set<string>;
}

/**
 * Scratch namespace marking an element as pending removal (mid-wilt).
 *
 * Protocol: when a `removeElement` hook is supplied, the renderer stamps this
 * scratch before handing the element over, records the id in the removal set
 * once, and skips the element on subsequent syncs while it departs. The
 * animation side stores a `cancel` on the handle; if the element reappears in
 * the data mid-wilt the renderer cancels the removal and updates it in place.
 */
export const PENDING_REMOVAL_SCRATCH = '_pfWilt';

export interface PendingRemovalHandle {
  cancel?: () => void;
}

export interface SyncOptions {
  /**
   * Deferred removal hook (the wilt animation). Called INSTEAD of
   * `ele.remove()` for departing nodes/edges; the implementation must
   * eventually remove the element (or the element stays mid-wilt until the
   * next cancel). Flower compounds always remove immediately — removing a
   * compound removes its children, which must not lag behind the data.
   */
  removeElement?: (ele: NodeSingular | EdgeSingular) => void;
}

/**
 * Sync graph structure to Cytoscape
 */
export function syncGraphStructure(
  cy: Core,
  data: { nodes: Node[]; relationships: Relationship[]; flowers: Flower[] },
  layoutResult: LayoutResult,
  options: SyncOptions = {}
): SyncResult {
  const result: SyncResult = {
    addedNodeIds: new Set(),
    addedEdgeIds: new Set(),
    removedNodeIds: new Set(),
    removedEdgeIds: new Set(),
    updatedNodeIds: new Set(),
    confirmedNodeIds: new Set(),
  };

  // Build lookup sets
  const stemLookup = new Set(data.flowers.map((f) => f.stem_node_id).filter(Boolean));
  const flowerOrdinals = new Map(data.flowers.map((f, index) => [f.id, index]));

  // Time-as-colour (Move 4): session start = earliest node birth currently in
  // the graph. created_at is the truthful birth source — a real ISO datetime
  // stamped by the backend — whereas timestamps[] are seconds relative to the
  // session/page start, not absolute times. Colours are recomputed each sync
  // but are deterministic in (created_at, sessionStart), and sessionStart is
  // stable while the earliest node lives (backends only append later births),
  // so existing nodes are never repainted as the session grows.
  const sessionStartMs = earliestBirthMs(data.nodes);

  // 1. Sync flowers (compound nodes)
  syncFlowers(cy, data.flowers, data.nodes, result);

  // 2. Sync regular nodes
  syncNodes(cy, data.nodes, stemLookup, flowerOrdinals, sessionStartMs, layoutResult, result, options);

  // 3. Sync edges
  syncEdges(cy, data.relationships, result, options);

  return result;
}

/**
 * Remove an element, deferring to the removal hook (wilt) when provided.
 * Returns true when the departure was recorded now; false when the element
 * is already mid-wilt from an earlier sync.
 */
function removeOrDefer(
  ele: NodeSingular | EdgeSingular,
  options: SyncOptions
): boolean {
  if (ele.scratch(PENDING_REMOVAL_SCRATCH)) return false; // already departing
  if (options.removeElement) {
    ele.scratch(PENDING_REMOVAL_SCRATCH, {} satisfies PendingRemovalHandle);
    options.removeElement(ele);
  } else {
    ele.remove();
  }
  return true;
}

/**
 * An element scheduled for removal reappeared in the data — cancel the
 * pending removal (the wilt's cancel handle restores styling) so the update
 * path can proceed on a live element.
 */
function cancelPendingRemoval(ele: NodeSingular | EdgeSingular): void {
  const handle = ele.scratch(PENDING_REMOVAL_SCRATCH) as PendingRemovalHandle | undefined;
  if (!handle) return;
  if (handle.cancel) {
    handle.cancel();
  } else {
    ele.removeScratch(PENDING_REMOVAL_SCRATCH);
  }
}

/**
 * Sync flower compound nodes
 */
function syncFlowers(
  cy: Core,
  flowers: Flower[],
  nodes: Node[],
  result: SyncResult
): void {
  const desiredFlowerIds = new Set(flowers.map((f) => f.id));
  
  // Remove flowers that no longer exist
  cy.nodes('.flower').forEach((ele) => {
    if (!desiredFlowerIds.has(ele.id())) {
      ele.remove();
      result.removedNodeIds.add(ele.id());
    }
  });
  
  // Add/update flowers
  flowers.forEach((flower) => {
    const members = nodes.filter((n) => n.flower_id === flower.id);
    const memberCount = members.length;
    
    const existing = cy.getElementById(flower.id);
    const isCollapsed = existing?.data('collapsed') ?? false;
    const collapseIcon = isCollapsed ? '▶' : '▼';
    const labelWithCount = `${collapseIcon} ${flower.label} (${memberCount})`;
    
    if (existing && existing.nonempty()) {
      // Update existing flower
      existing.data({
        id: flower.id,
        label: labelWithCount,
        kind: 'flower',
        collapsed: isCollapsed,
      });
      existing.classes('flower');
      result.updatedNodeIds.add(flower.id);
    } else {
      // Create new flower
      cy.add({
        group: 'nodes',
        data: {
          id: flower.id,
          label: labelWithCount,
          kind: 'flower',
          collapsed: false,
        },
        classes: 'flower',
        grabbable: true, // Enable dragging!
      });
      result.addedNodeIds.add(flower.id);
    }
  });
}

/**
 * Earliest finite birth time (ms since epoch) among the nodes, or NaN when
 * none parses — birthColor treats a NaN window as degenerate (dawn).
 */
function earliestBirthMs(nodes: Node[]): number {
  let earliest = Number.POSITIVE_INFINITY;
  for (const node of nodes) {
    const ms = Date.parse(node.created_at);
    if (Number.isFinite(ms) && ms < earliest) earliest = ms;
  }
  return Number.isFinite(earliest) ? earliest : Number.NaN;
}

/**
 * Sync regular nodes
 */
function syncNodes(
  cy: Core,
  nodes: Node[],
  stemLookup: Set<string>,
  flowerOrdinals: Map<string, number>,
  sessionStartMs: number,
  layoutResult: LayoutResult,
  result: SyncResult,
  options: SyncOptions
): void {
  const desiredNodeIds = new Set(nodes.map((n) => n.id));

  // Remove nodes that no longer exist (deferred through the wilt hook)
  cy.nodes()
    .filter((ele) => !ele.hasClass('flower'))
    .forEach((ele) => {
      if (!desiredNodeIds.has(ele.id())) {
        if (removeOrDefer(ele, options)) {
          result.removedNodeIds.add(ele.id());
        }
      }
    });
  
  // Add/update nodes
  nodes.forEach((node) => {
    const classes = ['pf-node', node.status];
    if (stemLookup.has(node.id)) {
      classes.push('stem');
    }
    
    const parentId = node.flower_id ?? null;

    // Time as colour: the node's birth hue over the fixed reference window
    // (see the SPAN CONTRACT in config/cartography.ts). Always stamped as
    // data; only the cartography stylesheet/verbs consume it, so with the
    // flag off the legacy palette is untouched.
    const nodeBirthColor = birthColor(
      Date.parse(node.created_at),
      sessionStartMs,
      sessionStartMs + SESSION_HUE_SPAN_MS
    );

    const elementData: Record<string, unknown> = {
      id: node.id,
      label: node.label,
      status: node.status,
      kind: 'node',
      parent: parentId ?? undefined,
      mentions: node.mentions || 0, // CRITICAL: needed for stem-petal positioning
      timestamps: node.timestamps || [], // Also useful for temporal styling
      inferred_type: node.inferred_type || 'concept',
      birthColor: nodeBirthColor, // pure ramp colour (borders, bloom ring)
      birthFill: birthFill(nodeBirthColor), // paper-mixed fill (label legibility)
      birthGhost: birthGhostTint(nodeBirthColor), // reduced-strength ghost border tint
    };
    
    const existing = cy.getElementById(node.id);
    if (existing && existing.nonempty()) {
      // Element re-appeared while departing — cancel the wilt and revive it
      cancelPendingRemoval(existing);

      // BLOOM trigger: detect the ghost → solid flip BEFORE classes are
      // replaced. Only the transition sync reports the id, so the pulse
      // fires exactly once per confirmation.
      if (existing.hasClass('ghost') && node.status === 'solid') {
        result.confirmedNodeIds.add(node.id);
      }

      // Update existing node
      existing.data(elementData);
      existing.classes(classes.join(' '));

      // Move to new parent if needed.
      // Normalize both sides to null: `.parent().first().id()` is undefined for
      // parentless nodes, and `undefined !== null` would move() (remove+re-add)
      // every unclustered node on every sync.
      const currentParentId = existing.parent().first().id() ?? null;
      if (currentParentId !== parentId) {
        existing.move({ parent: parentId });
      }
      
      result.updatedNodeIds.add(node.id);
    } else {
      // Create new node with a deterministic seed position: Cytoscape
      // defaults to (0,0), so a cold load (whole session in one sync) would
      // otherwise stack every node on the same point — a start fCoSe with
      // `randomize: false` cannot untangle. The seed clusters nodes by
      // flower on a wide ring; the layout run then refines from there.
      cy.add({
        group: 'nodes',
        data: elementData,
        classes: classes.join(' '),
        position: computeSeedPosition(
          node.id,
          parentId,
          parentId != null ? flowerOrdinals.get(parentId) ?? 0 : 0,
          flowerOrdinals.size
        ),
      });
      result.addedNodeIds.add(node.id);
    }
  });
}

/**
 * Sync edges
 */
function syncEdges(
  cy: Core,
  relationships: Relationship[],
  result: SyncResult,
  options: SyncOptions
): void {
  const desiredEdgeIds = new Set(relationships.map((r) => r.id));

  // Remove edges that no longer exist (deferred through the wilt hook)
  cy.edges().forEach((edge) => {
    if (!desiredEdgeIds.has(edge.id())) {
      if (removeOrDefer(edge, options)) {
        result.removedEdgeIds.add(edge.id());
      }
    }
  });
  
  // Add/update edges
  relationships.forEach((relationship) => {
    const classes = ['pf-edge'];
    
    // Check if this edge connects nodes in different flowers
    const sourceNode = cy.getElementById(relationship.source_id);
    const targetNode = cy.getElementById(relationship.target_id);
    
    // .parent() returns a NodeCollection; take the first (only) element for singular ops
    const sourceParent = sourceNode.parent().first();
    const targetParent = targetNode.parent().first();

    const isInterFlower =
      sourceParent.nonempty() &&
      targetParent.nonempty() &&
      sourceParent.id() !== targetParent.id() &&
      sourceParent.hasClass('flower') &&
      targetParent.hasClass('flower');
    
    if (isInterFlower) {
      classes.push('inter-flower');
    }
    
    const elementData = {
      id: relationship.id,
      source: relationship.source_id,
      target: relationship.target_id,
      description: relationship.description,
      kind: 'edge',
    };
    
    const existing = cy.getElementById(relationship.id);
    if (existing && existing.nonempty()) {
      // Edge re-appeared while departing — cancel the wilt and revive it
      cancelPendingRemoval(existing);

      // Update existing edge in place. Edge updates are intentionally not
      // recorded in the SyncResult: updatedNodeIds is a node/flower set and
      // no consumer needs updated-edge ids.
      existing.data(elementData);
      existing.classes(classes.join(' '));
    } else {
      // Create new edge
      cy.add({
        group: 'edges',
        data: elementData,
        classes: classes.join(' '),
      });
      result.addedEdgeIds.add(relationship.id);
    }
  });
}


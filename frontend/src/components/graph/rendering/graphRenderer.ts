import type { Core } from 'cytoscape';
import type { Node, Relationship, Flower } from '../../../lib/types';
import type { LayoutResult } from '../layout/layoutEngine';

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
}

/**
 * Sync graph structure to Cytoscape
 */
export function syncGraphStructure(
  cy: Core,
  data: { nodes: Node[]; relationships: Relationship[]; flowers: Flower[] },
  layoutResult: LayoutResult
): SyncResult {
  const result: SyncResult = {
    addedNodeIds: new Set(),
    addedEdgeIds: new Set(),
    removedNodeIds: new Set(),
    removedEdgeIds: new Set(),
    updatedNodeIds: new Set(),
  };
  
  // Build lookup sets
  const flowerMap = new Map(data.flowers.map((f) => [f.id, f]));
  const stemLookup = new Set(data.flowers.map((f) => f.stem_node_id).filter(Boolean));
  
  // 1. Sync flowers (compound nodes)
  syncFlowers(cy, data.flowers, data.nodes, result);
  
  // 2. Sync regular nodes
  syncNodes(cy, data.nodes, stemLookup, layoutResult, result);
  
  // 3. Sync edges
  syncEdges(cy, data.relationships, result);
  
  return result;
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
 * Sync regular nodes
 */
function syncNodes(
  cy: Core,
  nodes: Node[],
  stemLookup: Set<string>,
  layoutResult: LayoutResult,
  result: SyncResult
): void {
  const desiredNodeIds = new Set(nodes.map((n) => n.id));
  
  // Remove nodes that no longer exist
  cy.nodes()
    .filter((ele) => !ele.hasClass('flower'))
    .forEach((ele) => {
      if (!desiredNodeIds.has(ele.id())) {
        ele.remove();
        result.removedNodeIds.add(ele.id());
      }
    });
  
  // Add/update nodes
  nodes.forEach((node) => {
    const classes = ['pf-node', node.status];
    if (stemLookup.has(node.id)) {
      classes.push('stem');
    }
    
    const parentId = node.flower_id ?? null;
    const elementData: Record<string, unknown> = {
      id: node.id,
      label: node.label,
      status: node.status,
      kind: 'node',
      parent: parentId ?? undefined,
      mentions: node.mentions || 0, // CRITICAL: needed for stem-petal positioning
      timestamps: node.timestamps || [], // Also useful for temporal styling
      inferred_type: node.inferred_type || 'concept',
    };
    
    const existing = cy.getElementById(node.id);
    if (existing && existing.nonempty()) {
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
      // Create new node (position will be set by layout)
      cy.add({
        group: 'nodes',
        data: elementData,
        classes: classes.join(' '),
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
  result: SyncResult
): void {
  const desiredEdgeIds = new Set(relationships.map((r) => r.id));
  
  // Remove edges that no longer exist
  cy.edges().forEach((edge) => {
    if (!desiredEdgeIds.has(edge.id())) {
      edge.remove();
      result.removedEdgeIds.add(edge.id());
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
      // Update existing edge
      existing.data(elementData);
      existing.classes(classes.join(' '));
      result.updatedNodeIds.add(relationship.id);
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


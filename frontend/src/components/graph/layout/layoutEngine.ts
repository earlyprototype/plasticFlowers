import type { Node, Relationship, Flower } from '../../../lib/types';

/**
 * Layout Engine - Pure functions for graph layout calculations
 * 
 * Zero Cytoscape coupling - all functions are pure and testable without DOM.
 */

export interface LayoutOptions {
  algorithm: string;
  nodeRepulsion: number;
  idealEdgeLength: number;
  nodeSeparation: number;
  iterations: number;
  gravity: number;
  nestingFactor: number;
  gravityCompound: number;
  gravityRangeCompound: number;
}

export interface LayoutResult {
  nodePositions: Map<string, { x: number; y: number }>;
  lockedNodeIds: Set<string>;
  isolatedNodeIds: Set<string>;
  flowerStructureChanged: boolean;
}

/**
 * Identify nodes that should have float effect
 * Criteria: not in flower AND has ≤1 connection
 */
export function identifyIsolatedNodes(
  nodes: Node[],
  relationships: Relationship[]
): Set<string> {
  const connectionCounts = new Map<string, number>();
  
  // Count connections for each node
  relationships.forEach((r) => {
    connectionCounts.set(r.source_id, (connectionCounts.get(r.source_id) || 0) + 1);
    connectionCounts.set(r.target_id, (connectionCounts.get(r.target_id) || 0) + 1);
  });
  
  // Find standalone nodes with low connections
  return new Set(
    nodes
      .filter((n) => !n.flower_id && (connectionCounts.get(n.id) || 0) <= 1)
      .map((n) => n.id)
  );
}

/**
 * Identify which nodes already exist in the graph
 */
export function identifyExistingNodes(
  currentPositions: Map<string, { x: number; y: number }>,
  nodes: Node[]
): Set<string> {
  const existing = new Set<string>();
  
  nodes.forEach((node) => {
    if (currentPositions.has(node.id)) {
      existing.add(node.id);
    }
  });
  
  return existing;
}

/**
 * Detect if flower structure has changed
 * Returns true if flowers added, removed, or membership changed
 */
export function hasFlowerStructureChanged(
  previousFlowers: Flower[],
  currentFlowers: Flower[]
): boolean {
  const prevIds = new Set(previousFlowers.map(f => f.id));
  const currIds = new Set(currentFlowers.map(f => f.id));
  
  // Flower added or removed
  if (prevIds.size !== currIds.size) return true;
  
  // Check if any flower's membership changed
  return currentFlowers.some(flower => {
    const prev = previousFlowers.find(f => f.id === flower.id);
    if (!prev) return true; // New flower
    
    // Safety check: handle missing member_ids
    const prevMembers = prev.member_ids || [];
    const currentMembers = flower.member_ids || [];
    
    // Check member count and IDs
    if (prevMembers.length !== currentMembers.length) return true;
    
    const prevMemberSet = new Set(prevMembers);
    return currentMembers.some(id => !prevMemberSet.has(id));
  });
}

/**
 * Calculate layout result - which nodes are new, isolated, and should be locked
 */
export function calculateLayout(
  currentPositions: Map<string, { x: number; y: number }>,
  data: { nodes: Node[]; relationships: Relationship[]; flowers: Flower[] },
  options: LayoutOptions,
  previousFlowers: Flower[] = []
): LayoutResult {
  // Identify existing nodes (should be locked during layout)
  const existingNodeIds = identifyExistingNodes(currentPositions, data.nodes);
  
  // Identify isolated nodes (will get float effect)
  const isolatedNodeIds = identifyIsolatedNodes(data.nodes, data.relationships);
  
  // Detect if flower structure changed (major transformative event!)
  const flowerStructureChanged = hasFlowerStructureChanged(previousFlowers, data.flowers);
  
  // Return locked positions for existing nodes
  const lockedPositions = new Map<string, { x: number; y: number }>();
  existingNodeIds.forEach((nodeId) => {
    const pos = currentPositions.get(nodeId);
    if (pos) {
      lockedPositions.set(nodeId, pos);
    }
  });
  
  return {
    nodePositions: lockedPositions,
    lockedNodeIds: existingNodeIds,
    isolatedNodeIds,
    flowerStructureChanged,
  };
}


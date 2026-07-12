import type { FcoseLayoutOptions } from 'cytoscape-fcose';
import type { Node, Relationship, Flower } from '../../../lib/types';
import { hashPhase } from '../config/cartography';

/**
 * Layout Engine - Pure functions for graph layout calculations
 *
 * Zero Cytoscape coupling (type-only import) - all functions are pure and
 * testable without DOM.
 */

/**
 * Layout options are the real fcose layout options from `@types/cytoscape-fcose`
 * (the same shape as `LAYOUT_CONFIG` in `../config/layoutConfig.ts`).
 */
export type LayoutOptions = FcoseLayoutOptions;

export interface LayoutResult {
  nodePositions: Map<string, { x: number; y: number }>;
  lockedNodeIds: Set<string>;
  flowerStructureChanged: boolean;
}

/** Distance of per-flower seed centres from the origin. */
export const SEED_CLUSTER_RADIUS = 900;

/** Max deterministic per-node scatter around its cluster seed centre. */
export const SEED_JITTER_RADIUS = 150;

/**
 * Deterministic initial position for a NEWLY created Cytoscape node.
 *
 * Cytoscape defaults nodes added without a position to (0,0). On a cold
 * load (an entire session arriving in one sync) that stacks every node on
 * the same point, and fCoSe with `randomize: false` cannot untangle fully
 * coincident compounds. Seeding spreads flowers to evenly spaced points on
 * a wide ring (by flower ordinal) with a per-node hash jitter, so the
 * physics starts from distinct, clustered positions. Pure and stable:
 * the same inputs always produce the same seed.
 */
export function computeSeedPosition(
  nodeId: string,
  flowerId: string | null,
  flowerOrdinal: number,
  flowerCount: number
): { x: number; y: number } {
  // Per-node jitter: angle + radius both derived from the node id hash.
  const jitterAngle = hashPhase(nodeId);
  const jitterRadius = (hashPhase(`${nodeId}#r`) / (Math.PI * 2)) * SEED_JITTER_RADIUS;
  const jx = jitterRadius * Math.cos(jitterAngle);
  const jy = jitterRadius * Math.sin(jitterAngle);

  if (!flowerId || flowerCount <= 0) {
    // Unclustered node: looser scatter around the origin.
    return { x: jx * 2.5, y: jy * 2.5 };
  }

  const clusterAngle = (flowerOrdinal / flowerCount) * Math.PI * 2;
  return {
    x: SEED_CLUSTER_RADIUS * Math.cos(clusterAngle) + jx,
    y: SEED_CLUSTER_RADIUS * Math.sin(clusterAngle) + jy,
  };
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
 * Calculate layout result - which nodes are new and should be locked
 */
export function calculateLayout(
  currentPositions: Map<string, { x: number; y: number }>,
  data: { nodes: Node[]; relationships: Relationship[]; flowers: Flower[] },
  options: LayoutOptions,
  previousFlowers: Flower[] = []
): LayoutResult {
  // Identify existing nodes (should be locked during layout)
  const existingNodeIds = identifyExistingNodes(currentPositions, data.nodes);

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
    flowerStructureChanged,
  };
}


import type { Node } from '../../../lib/types';

/**
 * Intelligent Clustering - Pre-position nodes based on semantic attributes
 * 
 * This runs BEFORE fCoSe layout to give it intelligent starting positions.
 * Combines type-based regions, importance scoring, and recency.
 */

export interface ClusteringStrategy {
  typeWeight: number;      // 0-1: How much type influences position
  importanceWeight: number; // 0-1: How much mentions influence position
  recencyWeight: number;    // 0-1: How much recency influences position
}

export const DEFAULT_STRATEGY: ClusteringStrategy = {
  typeWeight: 0.6,       // Type is most important
  importanceWeight: 0.3, // Importance secondary
  recencyWeight: 0.1,    // Recency subtle influence
};

/**
 * Type-based regions - arrange types in semantic space
 * 
 * Layout philosophy:
 * - Abstract concepts (top)
 * - Concrete entities (left)
 * - Actions/events (right)
 * - Processes (bottom)
 */
const TYPE_REGIONS: Record<string, { x: number; y: number }> = {
  // Core types - MUCH WIDER separation
  'concept': { x: 0, y: -2000 },      // Top: Abstract ideas (was -1000)
  'entity': { x: -2000, y: 0 },       // Left: Concrete things (was -1000)
  'event': { x: 2000, y: 0 },         // Right: Actions/happenings (was 1000)
  'process': { x: 0, y: 2000 },       // Bottom: Procedures/methods (was 1000)
  
  // Hybrid types - WIDER spread
  'attribute': { x: -1400, y: -1400 },  // Top-left (was -700)
  'relation': { x: 1400, y: 1400 },     // Bottom-right (was 700)
  'state': { x: 1400, y: -1400 },       // Top-right (was 700, -700)
  'agent': { x: -1400, y: 1400 },       // Bottom-left (was -700, 700)
};

/**
 * Calculate position influenced by node type
 */
function getTypeInfluence(node: Node): { x: number; y: number } {
  const region = TYPE_REGIONS[node.inferred_type] || { x: 0, y: 0 };
  
  // Add MORE jitter so same-type nodes spread out significantly
  const jitter = () => (Math.random() - 0.5) * 800; // Was 300
  
  return {
    x: region.x + jitter(),
    y: region.y + jitter(),
  };
}

/**
 * Calculate position influenced by importance (mention count)
 * Important nodes pull toward center
 */
function getImportanceInfluence(
  node: Node,
  maxMentions: number
): { x: number; y: number } {
  const importance = Math.min(node.mentions / maxMentions, 1);
  
  // Less important = MUCH further from center
  const pushRadius = (1 - importance) * 1500; // Was 800
  const angle = Math.random() * 2 * Math.PI;
  
  return {
    x: pushRadius * Math.cos(angle),
    y: pushRadius * Math.sin(angle),
  };
}

/**
 * Calculate position influenced by recency
 * Recent nodes pull toward center
 */
function getRecencyInfluence(node: Node): { x: number; y: number } {
  const now = Date.now();
  const latestMention = Math.max(...node.timestamps);
  const ageMs = now - latestMention;
  const ageMinutes = ageMs / (1000 * 60);
  
  // Older = MUCH further out (caps at 30 minutes)
  const ageFactor = Math.min(ageMinutes / 30, 1);
  const pushRadius = ageFactor * 1200; // Was 600
  const angle = Math.random() * 2 * Math.PI;
  
  return {
    x: pushRadius * Math.cos(angle),
    y: pushRadius * Math.sin(angle),
  };
}

/**
 * Calculate intelligent pre-positions for nodes
 * Combines type, importance, and recency with configurable weights
 */
export function calculateIntelligentPositions(
  nodes: Node[],
  strategy: ClusteringStrategy = DEFAULT_STRATEGY
): Map<string, { x: number; y: number }> {
  const positions = new Map<string, { x: number; y: number }>();
  
  if (nodes.length === 0) return positions;
  
  // Calculate max mentions for normalization
  const maxMentions = Math.max(...nodes.map(n => n.mentions), 1);
  
  // Normalize weights (ensure they sum to 1)
  const totalWeight = strategy.typeWeight + strategy.importanceWeight + strategy.recencyWeight;
  
  // Handle edge case where all weights are 0
  if (totalWeight === 0) {
    // Default to type-only clustering
    const weights = { type: 1, importance: 0, recency: 0 };
    
    nodes.forEach(node => {
      const typePos = getTypeInfluence(node);
      positions.set(node.id, typePos);
    });
    
    return positions;
  }
  
  const weights = {
    type: strategy.typeWeight / totalWeight,
    importance: strategy.importanceWeight / totalWeight,
    recency: strategy.recencyWeight / totalWeight,
  };
  
  nodes.forEach(node => {
    // Get influences from each factor
    const typePos = getTypeInfluence(node);
    const importancePos = getImportanceInfluence(node, maxMentions);
    const recencyPos = getRecencyInfluence(node);
    
    // Weighted combination
    const x = 
      typePos.x * weights.type +
      importancePos.x * weights.importance +
      recencyPos.x * weights.recency;
      
    const y = 
      typePos.y * weights.type +
      importancePos.y * weights.importance +
      recencyPos.y * weights.recency;
    
    positions.set(node.id, { x, y });
  });
  
  return positions;
}

/**
 * Apply intelligent pre-positions to Cytoscape nodes
 * Call this BEFORE running layout
 */
export function applyIntelligentPositions(
  cy: any,
  positions: Map<string, { x: number; y: number }>
): void {
  positions.forEach((pos, nodeId) => {
    const node = cy.getElementById(nodeId);
    if (node.nonempty()) {
      node.position(pos);
    }
  });
}

/**
 * Preset strategies for different use cases
 */
export const CLUSTERING_PRESETS = {
  // Semantic clustering by type
  SEMANTIC: {
    typeWeight: 0.8,
    importanceWeight: 0.15,
    recencyWeight: 0.05,
  } as ClusteringStrategy,
  
  // Importance-driven (experts/key concepts central)
  IMPORTANCE: {
    typeWeight: 0.2,
    importanceWeight: 0.7,
    recencyWeight: 0.1,
  } as ClusteringStrategy,
  
  // Temporal (conversation flow over time)
  TEMPORAL: {
    typeWeight: 0.2,
    importanceWeight: 0.1,
    recencyWeight: 0.7,
  } as ClusteringStrategy,
  
  // Balanced (default)
  BALANCED: DEFAULT_STRATEGY,
} as const;


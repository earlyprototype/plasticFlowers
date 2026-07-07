import type { Core } from 'cytoscape';
import type { Node, Relationship } from '../../../lib/types';

/**
 * Organic Growth - Dynamic relationship-based clustering
 * 
 * Philosophy:
 * - When A→B relationship created, B moves toward A
 * - High-connection nodes become "gravity wells" (hubs)
 * - Connected nodes naturally cluster around hubs
 * - Flowers emerge organically from relationship structure
 */

export interface OrganicGrowthConfig {
  baseAttractionStrength: number;   // 0-1: How much target moves toward source
  hubAttractionMultiplier: number;  // Multiplier per connection count
  maxAttractionDistance: number;    // Max distance to apply attraction (px)
  animationDuration: number;        // Time for smooth movement (ms)
}

export const DEFAULT_ORGANIC_CONFIG: OrganicGrowthConfig = {
  baseAttractionStrength: 0.7,      // Target moves 70% closer (was 0.3)
  hubAttractionMultiplier: 0.1,     // +10% per connection (was 0.05)
  maxAttractionDistance: 3000,      // Wider range (was 1500)
  animationDuration: 0,             // INSTANT (was 800) - no animation delay
};

/**
 * Calculate node's "hub strength" based on connection count
 * More connections = stronger gravitational pull
 */
export function calculateHubStrength(nodeId: string, relationships: Relationship[]): number {
  // Count outgoing connections (source relationships)
  const outgoingCount = relationships.filter(r => r.source_id === nodeId).length;
  
  // Hub strength grows logarithmically (prevents runaway growth)
  // 1 connection = 1.0x, 5 = 1.8x, 10 = 2.3x, 20 = 3.0x
  return Math.log2(outgoingCount + 2);
}

/**
 * Calculate attraction strength for a specific relationship
 * Stronger hubs pull harder
 */
export function calculateAttractionStrength(
  sourceNodeId: string,
  relationships: Relationship[],
  config: OrganicGrowthConfig = DEFAULT_ORGANIC_CONFIG
): number {
  const hubStrength = calculateHubStrength(sourceNodeId, relationships);
  
  // Base attraction + hub bonus
  const attraction = config.baseAttractionStrength + 
                    (hubStrength * config.hubAttractionMultiplier);
  
  // Cap at 80% (never move more than 80% of the way)
  return Math.min(attraction, 0.8);
}

/**
 * Apply organic attraction for a new relationship
 * Target node moves toward source node
 */
export function applyRelationshipAttraction(
  cy: Core,
  sourceId: string,
  targetId: string,
  relationships: Relationship[],
  config: OrganicGrowthConfig = DEFAULT_ORGANIC_CONFIG
): void {
  const sourceNode = cy.getElementById(sourceId);
  const targetNode = cy.getElementById(targetId);
  
  if (!sourceNode.nonempty() || !targetNode.nonempty()) return;
  
  const sourcePos = sourceNode.position();
  const targetPos = targetNode.position();
  
  // Calculate distance
  const dx = sourcePos.x - targetPos.x;
  const dy = sourcePos.y - targetPos.y;
  const distance = Math.sqrt(dx * dx + dy * dy);
  
  // Only attract if within max distance (ignore very far nodes)
  if (distance > config.maxAttractionDistance) return;
  
  // Calculate attraction strength based on source's hub status
  const attractionStrength = calculateAttractionStrength(sourceId, relationships, config);
  
  // Calculate new position (move X% toward source)
  const newX = targetPos.x + (dx * attractionStrength);
  const newY = targetPos.y + (dy * attractionStrength);
  
  console.log(`  Moving ${targetId} toward ${sourceId}: (${targetPos.x.toFixed(0)},${targetPos.y.toFixed(0)}) → (${newX.toFixed(0)},${newY.toFixed(0)}) [${(attractionStrength*100).toFixed(0)}%]`);
  
  // Apply instantly (no animation) for immediate clustering
  if (config.animationDuration === 0) {
    targetNode.position({ x: newX, y: newY });
  } else {
    // Animate smooth movement
    targetNode.animate(
      {
        position: { x: newX, y: newY },
      },
      {
        duration: config.animationDuration,
        easing: 'ease-out',
      }
    );
  }
}

/**
 * Recalculate all attractions when hub grows
 * When a hub gains a new connection, ALL its neighbors pull closer
 */
export function recalculateHubAttractions(
  cy: Core,
  hubNodeId: string,
  relationships: Relationship[],
  config: OrganicGrowthConfig = DEFAULT_ORGANIC_CONFIG
): void {
  const hubNode = cy.getElementById(hubNodeId);
  if (!hubNode.nonempty()) return;
  
  const hubPos = hubNode.position();
  
  // Find all nodes connected TO this hub (targets of hub's edges)
  const connectedNodeIds = relationships
    .filter(r => r.source_id === hubNodeId)
    .map(r => r.target_id);
  
  // Calculate new hub strength
  const hubStrength = calculateHubStrength(hubNodeId, relationships);
  const attractionStrength = config.baseAttractionStrength + 
                            (hubStrength * config.hubAttractionMultiplier);
  const cappedAttraction = Math.min(attractionStrength, 0.8);
  
  // Pull factor: how much stronger the hub became
  // If hub grew from 3 to 4 connections, pull factor might be 1.1x
  const pullFactor = Math.min(cappedAttraction / config.baseAttractionStrength, 1.5);
  
  // Pull all connected nodes slightly closer
  connectedNodeIds.forEach(targetId => {
    const targetNode = cy.getElementById(targetId);
    if (!targetNode.nonempty()) return;
    
    const targetPos = targetNode.position();
    
    // Calculate distance
    const dx = hubPos.x - targetPos.x;
    const dy = hubPos.y - targetPos.y;
    const distance = Math.sqrt(dx * dx + dy * dy);
    
    if (distance > config.maxAttractionDistance) return;
    
    // Pull closer by a small percentage (10-20%)
    const pullStrength = 0.1 * pullFactor;
    const newX = targetPos.x + (dx * pullStrength);
    const newY = targetPos.y + (dy * pullStrength);
    
    // Apply instantly if duration is 0
    if (config.animationDuration === 0) {
      targetNode.position({ x: newX, y: newY });
    } else {
      // Animate smooth movement
      targetNode.animate(
        {
          position: { x: newX, y: newY },
        },
        {
          duration: config.animationDuration * 1.2, // Slightly slower
          easing: 'ease-in-out',
        }
      );
    }
  });
}

/**
 * Apply organic growth for all new relationships
 * Call this after syncGraphStructure when edges are added
 */
export function applyOrganicGrowth(
  cy: Core,
  addedEdgeIds: Set<string>,
  relationships: Relationship[],
  config: OrganicGrowthConfig = DEFAULT_ORGANIC_CONFIG
): void {
  // Track which hubs gained connections
  const affectedHubs = new Set<string>();
  
  // Apply attraction for each new edge
  addedEdgeIds.forEach(edgeId => {
    const relationship = relationships.find(r => r.id === edgeId);
    if (!relationship) return;
    
    // Move target toward source
    applyRelationshipAttraction(
      cy,
      relationship.source_id,
      relationship.target_id,
      relationships,
      config
    );
    
    // Mark source as affected hub
    affectedHubs.add(relationship.source_id);
  });
  
  // For each hub that grew, recalculate its attractions
  // (This makes all its neighbors pull closer as it becomes more central)
  affectedHubs.forEach(hubId => {
    // No delay needed if instant positioning (duration = 0)
    if (config.animationDuration === 0) {
      recalculateHubAttractions(cy, hubId, relationships, config);
    } else {
      setTimeout(() => {
        recalculateHubAttractions(cy, hubId, relationships, config);
      }, config.animationDuration);
    }
  });
}

/**
 * Get visual hub indicators for prominent nodes
 * Returns map of nodeId -> hub strength for styling
 */
export function getHubIndicators(
  nodes: Node[],
  relationships: Relationship[]
): Map<string, number> {
  const hubStrengths = new Map<string, number>();
  
  nodes.forEach(node => {
    const strength = calculateHubStrength(node.id, relationships);
    if (strength > 2.0) { // Only mark significant hubs
      hubStrengths.set(node.id, strength);
    }
  });
  
  return hubStrengths;
}

/**
 * Calculate optimal positions for a fully-formed cluster
 * Once a hub has stabilized, arrange nodes in optimal orbit
 */
export function optimizeClusterLayout(
  cy: Core,
  hubNodeId: string,
  relationships: Relationship[]
): void {
  const hubNode = cy.getElementById(hubNodeId);
  if (!hubNode.nonempty()) return;
  
  const hubPos = hubNode.position();
  
  // Get all satellites (nodes connected from hub)
  const satelliteIds = relationships
    .filter(r => r.source_id === hubNodeId)
    .map(r => r.target_id);
  
  if (satelliteIds.length === 0) return;
  
  // Calculate ideal orbit radius based on count
  const baseRadius = 200;
  const radiusPerNode = 30;
  const orbitRadius = baseRadius + (satelliteIds.length * radiusPerNode);
  
  // Arrange satellites in circular orbit
  const angleStep = (2 * Math.PI) / satelliteIds.length;
  
  satelliteIds.forEach((satelliteId, index) => {
    const satellite = cy.getElementById(satelliteId);
    if (!satellite.nonempty()) return;
    
    const angle = index * angleStep;
    const targetX = hubPos.x + (orbitRadius * Math.cos(angle));
    const targetY = hubPos.y + (orbitRadius * Math.sin(angle));
    
    // Gently move toward ideal position (don't force)
    const currentPos = satellite.position();
    const dx = targetX - currentPos.x;
    const dy = targetY - currentPos.y;
    
    // Only move 20% of the way (subtle optimization)
    satellite.animate(
      {
        position: {
          x: currentPos.x + (dx * 0.2),
          y: currentPos.y + (dy * 0.2),
        },
      },
      {
        duration: 1200,
        easing: 'ease-in-out',
      }
    );
  });
}


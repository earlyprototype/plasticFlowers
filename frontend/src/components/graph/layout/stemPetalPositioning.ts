import type { Core } from 'cytoscape';
import type { Flower } from '../../../lib/types';

/**
 * Stem-Petal Positioning - Organic arrangement of nodes within flowers
 * 
 * Applies after fCoSe layout to create visually pleasing flower clusters:
 * - Stem node (most mentioned) at center
 * - Petal nodes arranged in circle around stem
 */

export interface StemPetalConfig {
  petalOrbitRadius: number; // Distance of petals from stem
  minPetalSpacing: number;   // Minimum angle between petals (degrees)
}

export const DEFAULT_STEM_PETAL_CONFIG: StemPetalConfig = {
  petalOrbitRadius: 120,     // Petals 120px from stem
  minPetalSpacing: 30,       // At least 30° between petals
};

/**
 * Apply stem-petal positioning to all flowers
 * Call this AFTER fCoSe layout, BEFORE animations
 */
export function applyStemPetalPositioning(
  cy: Core,
  flowers: Flower[],
  config: StemPetalConfig = DEFAULT_STEM_PETAL_CONFIG
): void {
  flowers.forEach((flower) => {
    const flowerNode = cy.getElementById(flower.id);
    if (!flowerNode.nonempty()) return;

    const stemNodeId = flower.stem_node_id;
    if (!stemNodeId) return; // No stem, skip

    const stemNode = cy.getElementById(stemNodeId);
    if (!stemNode.nonempty()) return;

    // Get all petal nodes (members excluding stem)
    const petalNodes = flower.member_ids
      .filter((id) => id !== stemNodeId)
      .map((id) => cy.getElementById(id))
      .filter((node) => node.nonempty());

    if (petalNodes.length === 0) return; // Only stem, no petals

    // Position stem at center of flower (relative to flower)
    // For compound nodes, child positions are relative to parent
    stemNode.position({ x: 0, y: 0 });

    // Arrange petals in circle around stem (relative to flower center at 0,0)
    const petalCount = petalNodes.length;
    const angleStep = 360 / petalCount; // Evenly distribute

    petalNodes.forEach((petalNode, index) => {
      const angle = (index * angleStep) * (Math.PI / 180); // Convert to radians
      
      // Position relative to flower center (0,0)
      const x = config.petalOrbitRadius * Math.cos(angle);
      const y = config.petalOrbitRadius * Math.sin(angle);
      
      petalNode.position({ x, y });
    });
  });
}

/**
 * Calculate optimal petal orbit radius based on petal count
 * More petals = larger orbit to prevent overlap
 */
export function calculateOptimalOrbitRadius(petalCount: number): number {
  const BASE_RADIUS = 80;
  const RADIUS_PER_PETAL = 15;
  
  return BASE_RADIUS + (petalCount * RADIUS_PER_PETAL);
}

/**
 * Apply adaptive stem-petal positioning with dynamic radius
 */
export function applyAdaptiveStemPetalPositioning(
  cy: Core,
  flowers: Flower[]
): void {
  flowers.forEach((flower) => {
    const flowerNode = cy.getElementById(flower.id);
    if (!flowerNode.nonempty()) return;

    const stemNodeId = flower.stem_node_id;
    if (!stemNodeId) return;

    const stemNode = cy.getElementById(stemNodeId);
    if (!stemNode.nonempty()) return;

    const petalNodes = flower.member_ids
      .filter((id) => id !== stemNodeId)
      .map((id) => cy.getElementById(id))
      .filter((node) => node.nonempty());

    if (petalNodes.length === 0) return;

    // Calculate adaptive radius based on petal count
    const orbitRadius = calculateOptimalOrbitRadius(petalNodes.length);

    // Position stem at center (relative to flower at 0,0)
    stemNode.position({ x: 0, y: 0 });

    // Arrange petals with adaptive spacing (relative to flower center)
    const petalCount = petalNodes.length;
    const angleStep = 360 / petalCount;

    petalNodes.forEach((petalNode, index) => {
      const angle = (index * angleStep) * (Math.PI / 180);
      
      // Position relative to flower center (0,0)
      const x = orbitRadius * Math.cos(angle);
      const y = orbitRadius * Math.sin(angle);
      
      petalNode.position({ x, y });
    });
  });
}


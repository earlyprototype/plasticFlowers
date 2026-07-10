import type { Core, Position } from 'cytoscape';
import type { Flower } from '../../../lib/types';

/**
 * Stem-Petal Positioning - Organic arrangement of nodes within flowers
 *
 * Applies after fCoSe layout to create visually pleasing flower clusters:
 * - Stem node (most mentioned) at the cluster's centre
 * - Petal nodes arranged in circle around stem
 *
 * IMPORTANT: Cytoscape `node.position()` is ALWAYS in absolute model
 * coordinates — compound children are NOT positioned relative to their
 * parent. Each flower is therefore arranged around the centroid of its own
 * members (where fCoSe placed the cluster), never around a fixed origin;
 * hardcoding (0,0) would stack every flower on the same point.
 */

/** Centroid of the given nodes' current absolute positions. */
function clusterCenter(members: Array<{ position(): Position }>): Position {
  let x = 0;
  let y = 0;
  members.forEach((node) => {
    const pos = node.position();
    x += pos.x;
    y += pos.y;
  });
  const n = Math.max(members.length, 1);
  return { x: x / n, y: y / n };
}

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

    // Arrange around where fCoSe left this cluster (absolute coordinates).
    const center = clusterCenter([stemNode, ...petalNodes]);

    // Position stem at the cluster centre
    stemNode.position(center);

    // Arrange petals in circle around the stem
    const petalCount = petalNodes.length;
    const angleStep = 360 / petalCount; // Evenly distribute

    petalNodes.forEach((petalNode, index) => {
      const angle = (index * angleStep) * (Math.PI / 180); // Convert to radians

      petalNode.position({
        x: center.x + config.petalOrbitRadius * Math.cos(angle),
        y: center.y + config.petalOrbitRadius * Math.sin(angle),
      });
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

    // Arrange around where fCoSe left this cluster (absolute coordinates).
    const center = clusterCenter([stemNode, ...petalNodes]);

    // Position stem at the cluster centre
    stemNode.position(center);

    // Arrange petals with adaptive spacing around the stem
    const petalCount = petalNodes.length;
    const angleStep = 360 / petalCount;

    petalNodes.forEach((petalNode, index) => {
      const angle = (index * angleStep) * (Math.PI / 180);

      petalNode.position({
        x: center.x + orbitRadius * Math.cos(angle),
        y: center.y + orbitRadius * Math.sin(angle),
      });
    });
  });
}


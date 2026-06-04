import type { Core } from 'cytoscape';

/**
 * Push overlapping nodes apart (for nodes without direct relationships)
 */
export function resolveCollisions(cy: Core, minDistance: number = 150): void {
  const nodes = cy.nodes().filter(n => !n.hasClass('flower'));
  
  // Build adjacency for quick relationship lookups
  const adjacent = new Map<string, Set<string>>();
  cy.edges().forEach(edge => {
    const source = edge.source().id();
    const target = edge.target().id();
    
    if (!adjacent.has(source)) adjacent.set(source, new Set());
    if (!adjacent.has(target)) adjacent.set(target, new Set());
    
    adjacent.get(source)!.add(target);
    adjacent.get(target)!.add(source);
  });
  
  // Check all pairs for overlap
  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      const nodeA = nodes[i];
      const nodeB = nodes[j];
      
      // Skip if connected (relationship exists)
      const aId = nodeA.id();
      const bId = nodeB.id();
      if (adjacent.get(aId)?.has(bId)) continue;
      
      const posA = nodeA.position();
      const posB = nodeB.position();
      
      const dx = posB.x - posA.x;
      const dy = posB.y - posA.y;
      const distance = Math.sqrt(dx * dx + dy * dy);
      
      // Too close? Push apart
      if (distance < minDistance && distance > 0) {
        const overlap = minDistance - distance;
        const pushDistance = overlap / 2;
        
        const angle = Math.atan2(dy, dx);
        
        // Push nodeA away
        nodeA.position({
          x: posA.x - Math.cos(angle) * pushDistance,
          y: posA.y - Math.sin(angle) * pushDistance,
        });
        
        // Push nodeB away
        nodeB.position({
          x: posB.x + Math.cos(angle) * pushDistance,
          y: posB.y + Math.sin(angle) * pushDistance,
        });
      }
    }
  }
}


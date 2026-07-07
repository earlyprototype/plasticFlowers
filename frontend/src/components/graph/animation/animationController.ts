import type { Core } from 'cytoscape';
import type { SyncResult } from '../rendering/graphRenderer';

/**
 * Animation Controller - Handles all graph animations
 * 
 * Camera-first sequencing: camera moves first, then elements fade in, then float effects.
 * Single animation strategy - no competing systems.
 */

export class AnimationController {
  /**
   * Camera animation duration.
   * 1200ms provides smooth pan/zoom without feeling sluggish.
   */
  private readonly CAMERA_DURATION = 1200;
  
  /**
   * Element fade duration for nodes and edges.
   * 800ms is standard UI transition speed - matches camera timing for harmony.
   */
  private readonly FADE_DURATION = 800;
  
  /**
   * Fade start delay.
   * 400ms = halfway through camera movement for choreographed entrance.
   */
  private readonly FADE_DELAY = 400;
  
  /**
   * Float animation cycle duration for isolated nodes.
   * 3000ms = slow, calming motion (not distracting).
   */
  private readonly FLOAT_DURATION = 3000;
  
  /**
   * Float orbit radius in pixels.
   * 15px = subtle movement visible but not jarring.
   */
  private readonly FLOAT_DISTANCE = 15;
  
  private activeFloatAnimations = new Set<string>();
  
  /**
   * Execute complete animation sequence
   * STEP 1: Camera moves first (non-blocking)
   * STEP 2: Elements fade in while camera moving
   * STEP 3: Float effects start after fade completes
   */
  async executeAnimationSequence(
    cy: Core,
    syncResult: SyncResult,
    isolatedNodeIds: Set<string>
  ): Promise<void> {
    // STEP 1: Start camera fit immediately
    this.startCameraFit(cy);
    
    // STEP 2: Fade in new elements (400ms delay)
    await Promise.all([
      this.fadeInNewNodes(cy, syncResult.addedNodeIds),
      this.fadeInNewEdges(cy, syncResult.addedEdgeIds),
    ]);
    
    // STEP 3: Apply float effects to isolated nodes
    this.applyFloatEffects(cy, isolatedNodeIds);
  }
  
  /**
   * Start camera fit animation (non-blocking)
   */
  private startCameraFit(cy: Core): void {
    if (cy.elements().length === 0) return;
    
    cy.animate(
      {
        fit: { eles: cy.elements(), padding: 50 },
        duration: this.CAMERA_DURATION,
        easing: 'ease-in-out',
      },
      {
        duration: this.CAMERA_DURATION,
      }
    );
  }
  
  /**
   * Fade in new nodes
   */
  private async fadeInNewNodes(cy: Core, nodeIds: Set<string>): Promise<void> {
    if (nodeIds.size === 0) return;
    
    // Wait for fade delay
    await this.delay(this.FADE_DELAY);
    
    const promises: Promise<void>[] = [];
    
    nodeIds.forEach((nodeId) => {
      const node = cy.getElementById(nodeId);
      if (!node.nonempty()) return;
      
      // Start invisible
      node.style('opacity', 0);
      
      // Fade in
      const promise = new Promise<void>((resolve) => {
        node.animate(
          {
            style: { opacity: 1 },
          },
          {
            duration: this.FADE_DURATION,
            easing: 'ease-in',
            complete: () => resolve(),
          }
        );
      });
      
      promises.push(promise);
    });
    
    await Promise.all(promises);
  }
  
  /**
   * Fade in new edges
   */
  private async fadeInNewEdges(cy: Core, edgeIds: Set<string>): Promise<void> {
    if (edgeIds.size === 0) return;
    
    // Wait for fade delay
    await this.delay(this.FADE_DELAY);
    
    const promises: Promise<void>[] = [];
    
    edgeIds.forEach((edgeId) => {
      const edge = cy.getElementById(edgeId);
      if (!edge.nonempty()) return;
      
      // Start invisible
      edge.style('opacity', 0);
      
      // Fade in
      const promise = new Promise<void>((resolve) => {
        edge.animate(
          {
            style: { opacity: 1 },
          },
          {
            duration: this.FADE_DURATION,
            easing: 'ease-in',
            complete: () => resolve(),
          }
        );
      });
      
      promises.push(promise);
    });
    
    await Promise.all(promises);
  }
  
  /**
   * Apply float effects to isolated nodes
   */
  private applyFloatEffects(cy: Core, nodeIds: Set<string>): void {
    nodeIds.forEach((nodeId) => {
      // Skip if already floating
      if (this.activeFloatAnimations.has(nodeId)) return;
      
      const node = cy.getElementById(nodeId);
      if (!node.nonempty()) return;
      
      this.activeFloatAnimations.add(nodeId);
      this.startFloatAnimation(cy, nodeId);
    });
  }
  
  /**
   * Start continuous float animation for a node
   */
  private startFloatAnimation(cy: Core, nodeId: string): void {
    const node = cy.getElementById(nodeId);
    if (!node.nonempty()) {
      this.activeFloatAnimations.delete(nodeId);
      return;
    }
    
    const startPos = node.position();
    const seed = nodeId.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0);
    const angle = (seed % 360) * (Math.PI / 180);
    
    const animate = () => {
      const currentNode = cy.getElementById(nodeId);
      
      // Stop if node removed or joined a flower
      if (!currentNode.nonempty() || currentNode.parent().nonempty()) {
        this.activeFloatAnimations.delete(nodeId);
        return;
      }
      
      // Calculate gentle sine-wave offset
      const offset = Math.sin(Date.now() / this.FLOAT_DURATION + seed) * this.FLOAT_DISTANCE;
      
      currentNode.animate(
        {
          position: {
            x: startPos.x + Math.cos(angle) * offset,
            y: startPos.y + Math.sin(angle) * offset,
          },
        },
        {
          duration: this.FLOAT_DURATION,
          easing: 'ease-in-out',
          complete: () => animate(), // Loop forever
        }
      );
    };
    
    animate();
  }
  
  /**
   * Stop all float animations (for cleanup)
   */
  stopAllFloatAnimations(cy: Core): void {
    this.activeFloatAnimations.forEach((nodeId) => {
      const node = cy.getElementById(nodeId);
      if (node.nonempty()) {
        node.stop(true, false);
      }
    });
    this.activeFloatAnimations.clear();
  }
  
  /**
   * Utility: delay helper
   */
  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}


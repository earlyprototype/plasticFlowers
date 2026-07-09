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

  /**
   * Cap on simultaneously floating nodes so large graphs don't accumulate
   * unbounded animation timers.
   */
  private readonly MAX_CONCURRENT_FLOATS = 30;

  /**
   * A node with this many connections is considered "settled" and stops floating.
   */
  private readonly FLOAT_STOP_DEGREE = 2;

  /** Anchor position each float orbits around (re-set after layout runs). */
  private floatAnchors = new Map<string, { x: number; y: number }>();

  /**
   * Generation counter per floating node. Each (re)start bumps the generation;
   * a running loop exits when its captured generation is stale, so re-anchoring
   * never leaves two competing loops on the same node.
   */
  private floatGenerations = new Map<string, number>();

  /** Number of nodes currently floating (exposed for tests/diagnostics). */
  get activeFloatCount(): number {
    return this.floatAnchors.size;
  }

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
    if (cy.destroyed()) return;
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
    if (cy.destroyed()) return;

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
            complete: () => {
              // Drop the inline opacity so stylesheet rules (e.g. the
              // `node.ghost { opacity: 0.15 }` class style) apply again —
              // an inline opacity of 1 would render ghosts fully opaque.
              node.removeStyle('opacity');
              resolve();
            },
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
    if (cy.destroyed()) return;

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
            complete: () => {
              // Let the stylesheet opacity (e.g. base edges at 0.4) win again.
              edge.removeStyle('opacity');
              resolve();
            },
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
      if (this.floatAnchors.has(nodeId)) return;

      // Cap concurrent float animations
      if (this.floatAnchors.size >= this.MAX_CONCURRENT_FLOATS) return;

      const node = cy.getElementById(nodeId);
      if (!node.nonempty()) return;
      // Settled/clustered nodes don't float
      if (node.parent().nonempty() || node.degree(false) >= this.FLOAT_STOP_DEGREE) return;

      this.startFloatAnimation(cy, nodeId);
    });
  }

  /**
   * Start (or restart) the continuous float animation for a node.
   * Anchors to the node's CURRENT position; bumps the generation so any
   * previous loop for this node exits.
   */
  private startFloatAnimation(cy: Core, nodeId: string): void {
    const node = cy.getElementById(nodeId);
    if (!node.nonempty()) {
      this.clearFloat(nodeId);
      return;
    }

    const generation = (this.floatGenerations.get(nodeId) ?? 0) + 1;
    this.floatGenerations.set(nodeId, generation);
    this.floatAnchors.set(nodeId, { ...node.position() });

    const seed = nodeId.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0);
    const angle = (seed % 360) * (Math.PI / 180);

    const animate = () => {
      // A newer loop (re-anchor) or a stop superseded this one
      if (this.floatGenerations.get(nodeId) !== generation) return;
      if (cy.destroyed()) {
        this.clearFloat(nodeId);
        return;
      }

      const currentNode = cy.getElementById(nodeId);

      // Stop if node removed, joined a flower, or gained enough connections
      if (
        !currentNode.nonempty() ||
        currentNode.parent().nonempty() ||
        currentNode.degree(false) >= this.FLOAT_STOP_DEGREE
      ) {
        this.clearFloat(nodeId);
        return;
      }

      const anchor = this.floatAnchors.get(nodeId);
      if (!anchor) return;

      // Calculate gentle sine-wave offset around the current anchor
      const offset = Math.sin(Date.now() / this.FLOAT_DURATION + seed) * this.FLOAT_DISTANCE;

      currentNode.animate(
        {
          position: {
            x: anchor.x + Math.cos(angle) * offset,
            y: anchor.y + Math.sin(angle) * offset,
          },
        },
        {
          duration: this.FLOAT_DURATION,
          easing: 'ease-in-out',
          complete: () => animate(), // Loop until stopped/superseded
        }
      );
    };

    animate();
  }

  /**
   * Re-anchor all float animations to the nodes' current positions.
   * Call after a layout run so floats orbit the new positions instead of
   * fighting the layout with stale captured anchors.
   */
  reanchorFloats(cy: Core): void {
    Array.from(this.floatAnchors.keys()).forEach((nodeId) => {
      const node = cy.getElementById(nodeId);
      if (!node.nonempty()) {
        this.clearFloat(nodeId);
        return;
      }
      // Halt the in-flight animation, then restart anchored at the new position
      node.stop(true, false);
      this.startFloatAnimation(cy, nodeId);
    });
  }

  /**
   * Stop tracking a floating node (its loop exits on the generation check).
   */
  private clearFloat(nodeId: string): void {
    this.floatAnchors.delete(nodeId);
    this.floatGenerations.delete(nodeId);
  }

  /**
   * Stop all float animations (for cleanup)
   */
  stopAllFloatAnimations(cy: Core): void {
    this.floatAnchors.forEach((_anchor, nodeId) => {
      // Invalidate any running loop for this node
      this.floatGenerations.set(nodeId, (this.floatGenerations.get(nodeId) ?? 0) + 1);
      if (cy.destroyed()) return;
      const node = cy.getElementById(nodeId);
      if (node.nonempty()) {
        node.stop(true, false);
      }
    });
    this.floatAnchors.clear();
    this.floatGenerations.clear();
  }

  /**
   * Utility: delay helper
   */
  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}

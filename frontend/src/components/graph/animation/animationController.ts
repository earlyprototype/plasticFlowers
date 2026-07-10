import type { Core, EdgeSingular, NodeSingular } from 'cytoscape';
import type { SyncResult } from '../rendering/graphRenderer';
import { PENDING_REMOVAL_SCRATCH, type PendingRemovalHandle } from '../rendering/graphRenderer';
import { CARTOGRAPHY_PALETTE } from '../config/cartography';

/**
 * Animation Controller — growth is the only animation grammar.
 *
 * Three verbs, nothing else:
 * - SPROUT (new node): the edge from its stem/source extends first (the line
 *   grows over ~350ms), then the node scales in from ~0 with a subtle
 *   overshoot (~300ms). A node arriving with no edge just scales in.
 * - BLOOM (ghost → confirmed): a single expanding ring pulse (~600ms) while
 *   the stylesheet transitions the node to its solid styling. One pulse per
 *   confirmation — graphRenderer only reports ids on the actual class flip.
 * - WILT (node removed/pruned): desaturate toward the terrain tone, shrink
 *   to ~0.35 scale, sink ~6px and fade over ~900ms, THEN remove the element.
 *
 * The grammar runs regardless of the cartography flag: it is motion, not
 * palette. (The wilt desaturation target is the cartography terrain tone,
 * which also reads fine as a muted grey-green on the legacy white canvas.)
 *
 * prefers-reduced-motion: every verb snaps to its final state instantly —
 * nodes/edges appear at stylesheet styling, confirmations restyle without a
 * pulse, removals are immediate.
 *
 * Sequencing is timer-based (setTimeout), not animate-complete based: in
 * headless Cytoscape (tests) the animation loop never ticks, so completion
 * callbacks would never fire. Timers keep the choreography deterministic
 * under fake timers; the visual tween runs alongside in the browser.
 *
 * T9 lesson (keep!): every inline style set for an animation is removed once
 * the verb finishes, so stylesheet rules (e.g. `node.ghost { opacity }`)
 * apply again. An orphaned inline `opacity: 1` renders ghosts fully opaque.
 */

/** Stem-edge line-grow duration (ms). */
export const SPROUT_EDGE_MS = 350;
/** Node scale-in duration (ms). */
export const SPROUT_NODE_MS = 300;
/** Confirmation ring-pulse duration (ms). */
export const BLOOM_MS = 600;
/** Removal wilt duration (ms) — element is removed from the graph after this. */
export const WILT_MS = 900;

/** Wilt geometry: final scale and vertical sink. */
const WILT_SCALE = 0.35;
const WILT_SINK_PX = 6;

/** Ring-pulse ink — the surveyed-sepia stem accent from the cartography set. */
const BLOOM_COLOR = '#A98F5A';

/**
 * System reduced-motion preference. Guarded for non-browser environments
 * (vitest runs in a plain node environment).
 */
function systemPrefersReducedMotion(): boolean {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
    return false;
  }
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

export class AnimationController {
  /** Camera pan/zoom duration — smooth without feeling sluggish. */
  private readonly CAMERA_DURATION = 1200;

  /** Injected for tests; defaults to the media query. Read per verb so a live preference change is respected. */
  private readonly prefersReducedMotion: () => boolean;

  /** Deferred-removal timers for wilting elements, keyed by element id. */
  private readonly wiltTimers = new Map<string, ReturnType<typeof setTimeout>>();

  /** Cleanup timers for bloom pulses (inline overlay style removal). */
  private readonly bloomTimers = new Set<ReturnType<typeof setTimeout>>();

  constructor(options: { prefersReducedMotion?: () => boolean } = {}) {
    this.prefersReducedMotion = options.prefersReducedMotion ?? systemPrefersReducedMotion;
  }

  /** Number of elements currently wilting (exposed for tests/diagnostics). */
  get pendingWiltCount(): number {
    return this.wiltTimers.size;
  }

  /**
   * Execute the growth sequence for one sync:
   * camera moves first (non-blocking), confirmed ghosts bloom, and new
   * elements sprout (stem edge extends, then the node scales in).
   */
  async executeAnimationSequence(cy: Core, syncResult: SyncResult): Promise<void> {
    this.startCameraFit(cy);
    this.bloom(cy, syncResult.confirmedNodeIds);
    await this.sprout(cy, syncResult.addedNodeIds, syncResult.addedEdgeIds);
  }

  /**
   * Start camera fit animation (non-blocking; instant under reduced motion).
   */
  private startCameraFit(cy: Core): void {
    if (cy.elements().length === 0) return;

    if (this.prefersReducedMotion()) {
      cy.fit(cy.elements(), 50);
      return;
    }

    // Viewport animations QUEUE on the core: without clearing, rapid syncs
    // (live growth) build a backlog of stale fits and the camera lags many
    // beats behind the data. Supersede any in-flight/queued fit instead.
    cy.stop(true);
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

  // --- SPROUT ---------------------------------------------------------------

  /**
   * Sprout all newly added elements.
   *
   * Choreography per new node: its "stem edge" (an added edge, preferring one
   * whose other endpoint already existed, preferring the node as target)
   * grows first, then the node scales in. Added edges not serving as anyone's
   * stem grow immediately if both endpoints pre-existed, or after the sprout
   * beat if they connect newly added nodes (so they never point at nothing).
   *
   * Everything new is hidden synchronously before the first await so nothing
   * flashes at full styling before its cue.
   */
  private async sprout(
    cy: Core,
    addedNodeIds: Set<string>,
    addedEdgeIds: Set<string>
  ): Promise<void> {
    if (cy.destroyed()) return;
    if (addedNodeIds.size === 0 && addedEdgeIds.size === 0) return;
    // Reduced motion: elements were added at their stylesheet styling — the
    // instant final state IS the sprout.
    if (this.prefersReducedMotion()) return;

    // Flower compounds don't sprout: their visual is the terrain island (or a
    // near-invisible rectangle) whose size derives from children.
    const newNodes: NodeSingular[] = [];
    addedNodeIds.forEach((id) => {
      const node = cy.getElementById(id);
      if (node.nonempty() && node.isNode() && !node.hasClass('flower')) {
        newNodes.push(node as NodeSingular);
      }
    });

    const newEdges: EdgeSingular[] = [];
    addedEdgeIds.forEach((id) => {
      const edge = cy.getElementById(id);
      if (edge.nonempty() && edge.isEdge()) {
        newEdges.push(edge as EdgeSingular);
      }
    });

    // Hide everything new synchronously (no await yet — no paint happens
    // between the structural sync and this point).
    newNodes.forEach((node) => node.style('opacity', 0));
    newEdges.forEach((edge) => edge.style('opacity', 0));

    // Assign each new node a stem edge.
    const assignedEdgeIds = new Set<string>();
    const stemEdgeByNode = new Map<string, EdgeSingular>();
    newNodes.forEach((node) => {
      const stem = this.pickStemEdge(node, addedNodeIds, addedEdgeIds, assignedEdgeIds);
      if (stem) stemEdgeByNode.set(node.id(), stem);
    });

    const promises: Promise<void>[] = [];

    newNodes.forEach((node) => {
      const stemEdge = stemEdgeByNode.get(node.id()) ?? null;
      promises.push(this.sproutNode(cy, node, stemEdge));
    });

    newEdges.forEach((edge) => {
      if (assignedEdgeIds.has(edge.id())) return; // grows as part of a node's sprout
      const touchesNewNode =
        addedNodeIds.has(edge.source().id()) || addedNodeIds.has(edge.target().id());
      const delay = touchesNewNode ? SPROUT_EDGE_MS + SPROUT_NODE_MS : 0;
      promises.push(this.growEdge(cy, edge, delay));
    });

    await Promise.all(promises);
  }

  /**
   * Choose the edge that "feeds" a new node: prefer added edges whose other
   * endpoint pre-existed (the growth frontier extends from known terrain),
   * then edges where the node is the target. Each edge feeds one node.
   */
  private pickStemEdge(
    node: NodeSingular,
    addedNodeIds: Set<string>,
    addedEdgeIds: Set<string>,
    assignedEdgeIds: Set<string>
  ): EdgeSingular | null {
    const nodeId = node.id();
    const candidates: EdgeSingular[] = [];
    node.connectedEdges().forEach((edge) => {
      if (addedEdgeIds.has(edge.id()) && !assignedEdgeIds.has(edge.id())) {
        candidates.push(edge);
      }
    });
    if (candidates.length === 0) return null;

    const fromExisting = candidates.filter((edge) => {
      const otherId = edge.source().id() === nodeId ? edge.target().id() : edge.source().id();
      return !addedNodeIds.has(otherId);
    });
    const pool = fromExisting.length > 0 ? fromExisting : candidates;
    const asTarget = pool.filter((edge) => edge.target().id() === nodeId);
    const chosen = (asTarget.length > 0 ? asTarget : pool)[0];
    assignedEdgeIds.add(chosen.id());
    return chosen;
  }

  /** Grow the stem edge (if any), then scale the node in. */
  private async sproutNode(
    cy: Core,
    node: NodeSingular,
    stemEdge: EdgeSingular | null
  ): Promise<void> {
    if (stemEdge) {
      await this.growEdge(cy, stemEdge, 0);
      if (cy.destroyed()) return;
    }
    await this.scaleInNode(cy, node);
  }

  /**
   * Line-grow an edge from source to target over SPROUT_EDGE_MS using a
   * dash-offset sweep: with pattern [L, L] and offset animating L → 0 the
   * drawn segment extends from the source endpoint. The target arrow is
   * hidden during the sweep so the line doesn't point at nothing.
   */
  private async growEdge(cy: Core, edge: EdgeSingular, delayMs: number): Promise<void> {
    if (delayMs > 0) {
      await this.delay(delayMs);
      if (cy.destroyed()) return;
    }
    if (edge.removed()) return;

    const src = edge.source().position();
    const tgt = edge.target().position();
    const length = Math.max(Math.hypot(tgt.x - src.x, tgt.y - src.y), 1);

    edge.style({
      'line-style': 'dashed',
      'line-dash-pattern': [length, length],
      'line-dash-offset': length,
      'target-arrow-shape': 'none',
    });
    // Reveal at stylesheet opacity — the dash offset keeps the line at zero
    // drawn length until the sweep starts.
    edge.removeStyle('opacity');

    edge.animate(
      { style: { 'line-dash-offset': 0 } },
      { duration: SPROUT_EDGE_MS, easing: 'ease-out' }
    );

    await this.delay(SPROUT_EDGE_MS);
    if (cy.destroyed() || edge.removed()) return;
    edge.stop(true, true);
    // Drop every inline style so stylesheet rules (e.g. inter-flower dashes,
    // base arrows) win again.
    edge.removeStyle('line-style line-dash-pattern line-dash-offset target-arrow-shape');
  }

  /**
   * Scale a node in from ~0 to its natural (label-derived) size over
   * SPROUT_NODE_MS with a subtle overshoot. The label fades back in with the
   * stylesheet once the scale settles.
   */
  private async scaleInNode(cy: Core, node: NodeSingular): Promise<void> {
    if (cy.destroyed() || node.removed()) return;

    const targetWidth = Math.max(node.width(), 4);
    const targetHeight = Math.max(node.height(), 4);

    node.style({ width: 1, height: 1, 'text-opacity': 0 });
    // Reveal — stylesheet opacity applies (ghosts stay ghostly) while the
    // inline width/height keep the node at a dot.
    node.removeStyle('opacity');

    node.animate(
      { style: { width: targetWidth, height: targetHeight } },
      // easeOutBack — slight overshoot past the natural size, then settle.
      { duration: SPROUT_NODE_MS, easing: 'cubic-bezier(0.175, 0.885, 0.32, 1.275)' as 'ease-out' }
    );

    await this.delay(SPROUT_NODE_MS);
    if (cy.destroyed() || node.removed()) return;
    node.stop(true, true);
    node.removeStyle('width height text-opacity');
  }

  // --- BLOOM ----------------------------------------------------------------

  /**
   * One expanding ring pulse per freshly confirmed node (ghost → solid).
   * The solid restyling itself is handled by the stylesheet class flip (the
   * base style declares 300ms transitions); the pulse marks the moment.
   */
  private bloom(cy: Core, confirmedNodeIds: Set<string>): void {
    if (confirmedNodeIds.size === 0) return;
    if (this.prefersReducedMotion()) return; // class flip restyles instantly

    confirmedNodeIds.forEach((id) => {
      const node = cy.getElementById(id);
      if (!node.nonempty() || !node.isNode()) return;

      node.style({
        'overlay-shape': 'ellipse',
        'overlay-color': BLOOM_COLOR,
        'overlay-opacity': 0.4,
        'overlay-padding': 2,
      });
      node.animate(
        { style: { 'overlay-opacity': 0, 'overlay-padding': 28 } },
        { duration: BLOOM_MS, easing: 'ease-out' }
      );

      // Cleanup slightly after the tween so we never yank a style mid-frame.
      const timer = setTimeout(() => {
        this.bloomTimers.delete(timer);
        if (cy.destroyed() || node.removed()) return;
        node.removeStyle('overlay-shape overlay-color overlay-opacity overlay-padding');
      }, BLOOM_MS + 50);
      this.bloomTimers.add(timer);
    });
  }

  // --- WILT -----------------------------------------------------------------

  /**
   * Wilt an element, then remove it. Passed to graphRenderer as the deferred
   * removal hook: the actual cy.remove() happens WILT_MS later (immediately
   * under reduced motion). If the element is re-added to the data mid-wilt,
   * graphRenderer calls the cancel handle stored in the element's scratch and
   * the element is restored to stylesheet styling in place.
   *
   * Nodes desaturate toward the terrain tone, shrink to WILT_SCALE, sink
   * WILT_SINK_PX and fade; edges and flower compounds simply fade.
   */
  wiltAndRemove(ele: NodeSingular | EdgeSingular): void {
    if (ele.removed()) return;
    const cy = ele.cy();
    if (cy.destroyed()) return;

    const existingHandle = ele.scratch(PENDING_REMOVAL_SCRATCH) as
      | PendingRemovalHandle
      | undefined;
    if (existingHandle?.cancel) return; // already wilting

    if (this.prefersReducedMotion()) {
      ele.removeScratch(PENDING_REMOVAL_SCRATCH);
      ele.remove();
      return;
    }

    const id = ele.id();
    const isPlainNode = ele.isNode() && !ele.hasClass('flower');
    const originalPosition = ele.isNode() ? { ...(ele as NodeSingular).position() } : null;

    const cancel = () => {
      const timer = this.wiltTimers.get(id);
      if (timer !== undefined) clearTimeout(timer);
      this.wiltTimers.delete(id);
      if (ele.removed() || cy.destroyed()) return;
      ele.stop(true, false);
      ele.removeScratch(PENDING_REMOVAL_SCRATCH);
      ele.removeClass('wilting');
      ele.removeStyle('opacity text-opacity width height background-color border-color');
      if (originalPosition) (ele as NodeSingular).position(originalPosition);
    };

    const handle: PendingRemovalHandle = { ...(existingHandle ?? {}), cancel };
    ele.scratch(PENDING_REMOVAL_SCRATCH, handle);
    ele.addClass('wilting');

    if (isPlainNode) {
      const node = ele as NodeSingular;
      node.animate(
        {
          position: {
            x: originalPosition!.x,
            y: originalPosition!.y + WILT_SINK_PX,
          },
          style: {
            width: Math.max(node.width() * WILT_SCALE, 1),
            height: Math.max(node.height() * WILT_SCALE, 1),
            opacity: 0,
            'text-opacity': 0,
            'background-color': CARTOGRAPHY_PALETTE.terrain2,
            'border-color': CARTOGRAPHY_PALETTE.coast,
          },
        },
        { duration: WILT_MS, easing: 'ease-in' }
      );
    } else {
      ele.animate({ style: { opacity: 0 } }, { duration: WILT_MS, easing: 'ease-in' });
    }

    const timer = setTimeout(() => {
      this.wiltTimers.delete(id);
      if (cy.destroyed() || ele.removed()) return;
      ele.remove();
    }, WILT_MS);
    this.wiltTimers.set(id, timer);
  }

  // --- Lifecycle --------------------------------------------------------------

  /**
   * Stop all pending verb timers. Wilting elements are removed IMMEDIATELY
   * (unmount must not leave zombie elements waiting on timers); if the core
   * is already destroyed there is nothing left to remove.
   */
  stopAll(cy: Core): void {
    this.wiltTimers.forEach((timer) => clearTimeout(timer));
    this.wiltTimers.clear();
    this.bloomTimers.forEach((timer) => clearTimeout(timer));
    this.bloomTimers.clear();
    if (!cy.destroyed()) {
      cy.elements('.wilting').remove();
    }
  }

  /**
   * Utility: delay helper
   */
  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}

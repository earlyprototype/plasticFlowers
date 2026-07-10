import type { Core, CollectionReturnValue, EdgeSingular, NodeSingular } from 'cytoscape';
import type { SyncResult } from '../rendering/graphRenderer';
import { PENDING_REMOVAL_SCRATCH, type PendingRemovalHandle } from '../rendering/graphRenderer';
import { CARTOGRAPHY_PALETTE, isCartographyEnabled } from '../config/cartography';

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
 *   to ~0.35 scale and fade over ~900ms, THEN remove the element.
 *
 * The grammar runs regardless of the cartography flag: it is motion, not
 * palette. (The wilt desaturation target is the cartography terrain tone,
 * which also reads fine as a muted grey-green on the legacy white canvas.)
 *
 * prefers-reduced-motion: every verb snaps to its final state instantly —
 * nodes/edges appear at stylesheet styling, confirmations restyle without a
 * pulse, removals are immediate.
 *
 * Portrait mode (Move 5): while `setPortrait(true)` is active the plate must
 * stay calm — the controller runs NO verbs (elements snap to their final
 * states via the same instant path as reduced motion) and the growth-sequence
 * camera fit is suppressed entirely. Portrait entry drives its own camera fit
 * through `startCameraFit` explicitly.
 *
 * Sequencing is timer-based (setTimeout), not animate-complete based: in
 * headless Cytoscape (tests) the animation loop never ticks, so completion
 * callbacks would never fire. Timers keep the choreography deterministic
 * under fake timers; the visual tween runs alongside in the browser.
 * All sprouts in one sync share the same phase instants, so each sync arms
 * ONE timer per beat which fans out to every element awaiting it; every
 * choreography timer is tracked and cleared by stopAll(). An element that
 * starts WILTING mid-sprout makes its remaining sprout phases bail (checked
 * per beat), so a wilt tween is never snapped back to full styling.
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

/** Wilt geometry: final scale. (No position sink — a wilting node stays put,
 * so it neither drags the camera/layout nor storms the terrain redraw with
 * per-frame position events.) */
const WILT_SCALE = 0.35;

/**
 * Ring-pulse ink fallback — the surveyed-sepia stem accent. With cartography
 * on, the pulse uses the node's own birth colour (data('birthColor'), Move 4)
 * so a confirmation flashes in the hue of the idea's birth moment; the sepia
 * covers legacy mode and nodes without a stamped colour.
 */
const BLOOM_COLOR = '#A98F5A';

/** Options for a camera fit (portrait entry passes its own frame). */
export interface CameraFitOptions {
  /** Elements to frame; defaults to all elements. '.wilting' is always excluded. */
  eles?: CollectionReturnValue;
  /** Fit padding in px (default 50). */
  padding?: number;
  /** Tween duration in ms (default 1200). */
  duration?: number;
}

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

  /**
   * Every other choreography timer: shared sprout phase beats and bloom
   * cleanup timers. Batch-level record — stopAll() clears the lot, so an
   * unmount mid-sprout leaves nothing armed.
   */
  private readonly choreographyTimers = new Set<ReturnType<typeof setTimeout>>();

  /** Portrait plate presented — all verbs snap, growth camera fits are suppressed. */
  private portraitActive = false;

  constructor(options: { prefersReducedMotion?: () => boolean } = {}) {
    this.prefersReducedMotion = options.prefersReducedMotion ?? systemPrefersReducedMotion;
  }

  /** Number of elements currently wilting (exposed for tests/diagnostics). */
  get pendingWiltCount(): number {
    return this.wiltTimers.size;
  }

  /** Number of live choreography timers (exposed for tests/diagnostics). */
  get pendingChoreographyCount(): number {
    return this.choreographyTimers.size;
  }

  /**
   * Toggle portrait mode (Move 5). While active, every verb takes its
   * instant final-state path (the reduced-motion behaviour) and
   * executeAnimationSequence never moves the camera — the plate stays calm.
   */
  setPortrait(active: boolean): void {
    this.portraitActive = active;
  }

  /** Verbs snap to final states instantly (reduced motion or portrait). */
  private instantVerbs(): boolean {
    return this.portraitActive || this.prefersReducedMotion();
  }

  /**
   * Execute the growth sequence for one sync:
   * camera moves first (non-blocking), confirmed ghosts bloom, and new
   * elements sprout (stem edge extends, then the node scales in).
   * While portrait is active the camera is NOT touched (the plate keeps the
   * framing chosen on portrait entry) and the verbs snap instantly.
   */
  async executeAnimationSequence(cy: Core, syncResult: SyncResult): Promise<void> {
    if (!this.portraitActive) {
      this.startCameraFit(cy);
    }
    this.bloom(cy, syncResult.confirmedNodeIds);
    await this.sprout(cy, syncResult.addedNodeIds, syncResult.addedEdgeIds);
  }

  /**
   * Start a camera fit animation (non-blocking; instant under reduced
   * motion; supersedes any queued viewport animation). Mid-wilt elements are
   * excluded from the frame — a departing node must not stretch the camera.
   * Also used directly for the portrait-entry fit via `options`.
   */
  startCameraFit(cy: Core, options: CameraFitOptions = {}): void {
    const eles = (options.eles ?? cy.elements()).not('.wilting');
    if (eles.length === 0) return;
    const padding = options.padding ?? 50;

    if (this.prefersReducedMotion()) {
      cy.fit(eles, padding);
      return;
    }

    // Viewport animations QUEUE on the core: without clearing, rapid syncs
    // (live growth) build a backlog of stale fits and the camera lags many
    // beats behind the data. Supersede any in-flight/queued fit instead.
    cy.stop(true);
    cy.animate(
      { fit: { eles, padding } },
      {
        duration: options.duration ?? this.CAMERA_DURATION,
        easing: 'ease-in-out',
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
   * flashes at full styling before its cue. All elements share the batch's
   * phase beats (one timer per instant); each phase re-checks that its
   * element is still alive and not wilting before touching styles.
   */
  private async sprout(
    cy: Core,
    addedNodeIds: Set<string>,
    addedEdgeIds: Set<string>
  ): Promise<void> {
    if (cy.destroyed()) return;
    if (addedNodeIds.size === 0 && addedEdgeIds.size === 0) return;
    // Reduced motion / portrait: elements were added at their stylesheet
    // styling — the instant final state IS the sprout.
    if (this.instantVerbs()) return;

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

    // One shared timer per phase instant for the whole batch (armed NOW, so
    // every element's beats measure from the same t0).
    const at = this.armBatchBeats([
      SPROUT_NODE_MS,
      SPROUT_EDGE_MS,
      SPROUT_EDGE_MS + SPROUT_NODE_MS,
      SPROUT_EDGE_MS + SPROUT_NODE_MS + SPROUT_EDGE_MS,
    ]);

    const promises: Promise<void>[] = [];

    newNodes.forEach((node) => {
      const stemEdge = stemEdgeByNode.get(node.id()) ?? null;
      promises.push(this.sproutNode(cy, node, stemEdge, at));
    });

    newEdges.forEach((edge) => {
      if (assignedEdgeIds.has(edge.id())) return; // grows as part of a node's sprout
      const touchesNewNode =
        addedNodeIds.has(edge.source().id()) || addedNodeIds.has(edge.target().id());
      const startAt = touchesNewNode ? SPROUT_EDGE_MS + SPROUT_NODE_MS : 0;
      promises.push(this.growEdge(cy, edge, startAt, at));
    });

    await Promise.all(promises);
  }

  /**
   * Arm the shared phase beats of one sprout batch. Returns `at(instantMs)`
   * resolving when that instant (measured from now) is reached. All timers
   * are tracked in `choreographyTimers`; stopAll() clears them (the pending
   * awaits then simply never resume — their component is gone).
   */
  private armBatchBeats(instantsMs: number[]): (instantMs: number) => Promise<void> {
    const beats = new Map<number, Promise<void>>();
    for (const instant of instantsMs) {
      if (beats.has(instant)) continue;
      beats.set(
        instant,
        new Promise((resolve) => {
          const timer = setTimeout(() => {
            this.choreographyTimers.delete(timer);
            resolve();
          }, instant);
          this.choreographyTimers.add(timer);
        })
      );
    }
    return (instantMs: number) => beats.get(instantMs) ?? Promise.resolve();
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

  /** True when a sprout phase must not touch the element any more. */
  private sproutBailed(ele: NodeSingular | EdgeSingular): boolean {
    return ele.removed() || ele.hasClass('wilting');
  }

  /** Grow the stem edge (if any), then scale the node in. */
  private async sproutNode(
    cy: Core,
    node: NodeSingular,
    stemEdge: EdgeSingular | null,
    at: (instantMs: number) => Promise<void>
  ): Promise<void> {
    if (stemEdge) {
      await this.growEdge(cy, stemEdge, 0, at);
      if (cy.destroyed()) return;
      await this.scaleInNode(cy, node, SPROUT_EDGE_MS, at);
    } else {
      await this.scaleInNode(cy, node, 0, at);
    }
  }

  /**
   * Line-grow an edge from source to target over SPROUT_EDGE_MS using a
   * dash-offset sweep: with pattern [L, L] and offset animating L → 0 the
   * drawn segment extends from the source endpoint. The target arrow is
   * hidden during the sweep so the line doesn't point at nothing.
   * `startAtMs` is the batch instant at which the sweep begins.
   */
  private async growEdge(
    cy: Core,
    edge: EdgeSingular,
    startAtMs: number,
    at: (instantMs: number) => Promise<void>
  ): Promise<void> {
    if (startAtMs > 0) {
      await at(startAtMs);
      if (cy.destroyed()) return;
    }
    if (this.sproutBailed(edge)) return;

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

    await at(startAtMs + SPROUT_EDGE_MS);
    if (cy.destroyed() || this.sproutBailed(edge)) return;
    edge.stop(true, true);
    // Drop every inline style so stylesheet rules (e.g. inter-flower dashes,
    // base arrows) win again.
    edge.removeStyle('line-style line-dash-pattern line-dash-offset target-arrow-shape');
  }

  /**
   * Scale a node in from ~0 to its natural (label-derived) size over
   * SPROUT_NODE_MS with a subtle overshoot. The label fades back in with the
   * stylesheet once the scale settles. `startAtMs` is the batch instant at
   * which the scale-in begins.
   */
  private async scaleInNode(
    cy: Core,
    node: NodeSingular,
    startAtMs: number,
    at: (instantMs: number) => Promise<void>
  ): Promise<void> {
    if (startAtMs > 0) {
      await at(startAtMs);
      if (cy.destroyed()) return;
    }
    if (this.sproutBailed(node)) return;

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

    await at(startAtMs + SPROUT_NODE_MS);
    if (cy.destroyed() || this.sproutBailed(node)) return;
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
    if (this.instantVerbs()) return; // class flip restyles instantly

    confirmedNodeIds.forEach((id) => {
      const node = cy.getElementById(id);
      if (!node.nonempty() || !node.isNode() || node.hasClass('wilting')) return;

      const ringColor =
        (isCartographyEnabled() ? (node.data('birthColor') as string | undefined) : undefined) ??
        BLOOM_COLOR;
      node.style({
        'overlay-shape': 'ellipse',
        'overlay-color': ringColor,
        'overlay-opacity': 0.4,
        'overlay-padding': 2,
      });
      node.animate(
        { style: { 'overlay-opacity': 0, 'overlay-padding': 28 } },
        { duration: BLOOM_MS, easing: 'ease-out' }
      );

      // Cleanup slightly after the tween so we never yank a style mid-frame.
      const timer = setTimeout(() => {
        this.choreographyTimers.delete(timer);
        if (cy.destroyed() || node.removed()) return;
        node.removeStyle('overlay-shape overlay-color overlay-opacity overlay-padding');
      }, BLOOM_MS + 50);
      this.choreographyTimers.add(timer);
    });
  }

  // --- WILT -----------------------------------------------------------------

  /**
   * Wilt an element, then remove it. Passed to graphRenderer as the deferred
   * removal hook: the actual cy.remove() happens WILT_MS later (immediately
   * under reduced motion or portrait). If the element is re-added to the data
   * mid-wilt, graphRenderer calls the cancel handle stored in the element's
   * scratch and the element is restored to stylesheet styling in place.
   *
   * A wilt starting mid-sprout takes over cleanly: the in-flight sprout tween
   * is halted at its current visual state (stop without jumping) and the
   * element's remaining sprout phases bail on the 'wilting' class.
   *
   * Nodes desaturate toward the terrain tone, shrink to WILT_SCALE and fade
   * in place (no position sink — see WILT_SCALE note); edges and flower
   * compounds simply fade.
   */
  wiltAndRemove(ele: NodeSingular | EdgeSingular): void {
    if (ele.removed()) return;
    const cy = ele.cy();
    if (cy.destroyed()) return;

    const existingHandle = ele.scratch(PENDING_REMOVAL_SCRATCH) as
      | PendingRemovalHandle
      | undefined;
    if (existingHandle?.cancel) return; // already wilting

    if (this.instantVerbs()) {
      ele.removeScratch(PENDING_REMOVAL_SCRATCH);
      ele.remove();
      return;
    }

    // Halt any in-flight verb tween (e.g. a sprout scale-in) WITHOUT jumping
    // to its end state — the wilt animates from wherever the element is now.
    // Pending sprout phase callbacks bail on the 'wilting' class added below.
    ele.stop(true, false);

    const id = ele.id();
    const isPlainNode = ele.isNode() && !ele.hasClass('flower');

    const cancel = () => {
      const timer = this.wiltTimers.get(id);
      if (timer !== undefined) clearTimeout(timer);
      this.wiltTimers.delete(id);
      if (ele.removed() || cy.destroyed()) return;
      ele.stop(true, false);
      ele.removeScratch(PENDING_REMOVAL_SCRATCH);
      ele.removeClass('wilting');
      ele.removeStyle('opacity text-opacity width height background-color border-color');
      // Revive at the element's CURRENT position: layout may have moved
      // everything since the wilt began — snapping back to a stale
      // wilt-start position would teleport the node.
    };

    const handle: PendingRemovalHandle = { ...(existingHandle ?? {}), cancel };
    ele.scratch(PENDING_REMOVAL_SCRATCH, handle);
    ele.addClass('wilting');

    if (isPlainNode) {
      const node = ele as NodeSingular;
      node.animate(
        {
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
   * Stop all pending verb timers (wilt removals, sprout beats, bloom
   * cleanups) — after this call NO controller timer is left alive. Wilting
   * elements are removed IMMEDIATELY (unmount must not leave zombie elements
   * waiting on timers); if the core is already destroyed there is nothing
   * left to remove.
   */
  stopAll(cy: Core): void {
    this.wiltTimers.forEach((timer) => clearTimeout(timer));
    this.wiltTimers.clear();
    this.choreographyTimers.forEach((timer) => clearTimeout(timer));
    this.choreographyTimers.clear();
    if (!cy.destroyed()) {
      cy.elements('.wilting').remove();
    }
  }
}

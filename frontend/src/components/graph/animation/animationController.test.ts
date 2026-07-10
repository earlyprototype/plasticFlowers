import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import cytoscape, {
  type CollectionReturnValue,
  type Core,
  type SingularElementReturnValue,
} from 'cytoscape';
import {
  AnimationController,
  SPROUT_EDGE_MS,
  SPROUT_NODE_MS,
  BLOOM_MS,
  WILT_MS,
} from './animationController';
import { PENDING_REMOVAL_SCRATCH, type SyncResult } from '../rendering/graphRenderer';
import type { PendingRemovalHandle } from '../rendering/graphRenderer';

/**
 * The controller sequences the growth verbs with timers (headless Cytoscape
 * never ticks its animation loop, so animate-complete callbacks are not
 * relied upon). These tests drive the choreography with fake timers and
 * assert the observable style/element state at each beat.
 */

// Fixed dimensions: label-derived sizing needs canvas text measurement,
// which headless Cytoscape doesn't have.
const TEST_STYLE = [
  { selector: 'node', style: { width: 40, height: 20, opacity: 1 } },
  { selector: 'node.ghost', style: { opacity: 0.15 } },
  { selector: 'edge', style: { opacity: 0.4 } },
];

const emptySyncResult = (overrides: Partial<SyncResult> = {}): SyncResult => ({
  addedNodeIds: new Set(),
  addedEdgeIds: new Set(),
  removedNodeIds: new Set(),
  removedEdgeIds: new Set(),
  updatedNodeIds: new Set(),
  confirmedNodeIds: new Set(),
  ...overrides,
});

// parseFloat: dimension styles come back with units (e.g. '40px')
const num = (ele: SingularElementReturnValue, prop: string): number =>
  parseFloat(ele.style(prop));

describe('AnimationController', () => {
  let cy: Core;
  let controller: AnimationController;

  beforeEach(() => {
    vi.useFakeTimers();
    cy = cytoscape({
      headless: true,
      styleEnabled: true,
      style: TEST_STYLE as never,
    });
    controller = new AnimationController({ prefersReducedMotion: () => false });
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  describe('sprout', () => {
    it('grows the stem edge first, then scales the node in', async () => {
      cy.add([
        { group: 'nodes', data: { id: 'existing' }, position: { x: 0, y: 0 } },
        { group: 'nodes', data: { id: 'fresh' }, position: { x: 100, y: 0 } },
        { group: 'edges', data: { id: 'e1', source: 'existing', target: 'fresh' } },
      ]);
      const fresh = cy.getElementById('fresh');
      const edge = cy.getElementById('e1');

      const sequence = controller.executeAnimationSequence(
        cy,
        emptySyncResult({ addedNodeIds: new Set(['fresh']), addedEdgeIds: new Set(['e1']) })
      );

      // Beat 0 (synchronous): the new node is hidden, the stem edge is set up
      // for the line-grow (arrow hidden, dash sweep armed).
      expect(num(fresh, 'opacity')).toBe(0);
      expect(edge.style('target-arrow-shape')).toBe('none');
      expect(edge.style('line-style')).toBe('dashed');

      // Beat 1: edge growth finished — inline dash styles dropped, node
      // scale-in has started from a dot.
      await vi.advanceTimersByTimeAsync(SPROUT_EDGE_MS);
      expect(edge.style('line-style')).toBe('solid'); // stylesheet again
      expect(num(fresh, 'opacity')).toBe(1); // revealed
      expect(num(fresh, 'width')).toBeLessThan(40); // mid-scale

      // Beat 2: scale-in settled — all inline styles removed.
      await vi.advanceTimersByTimeAsync(SPROUT_NODE_MS);
      await sequence;
      expect(num(fresh, 'width')).toBe(40);
      expect(num(fresh, 'opacity')).toBe(1);
    });

    it('scales a node with no edge straight in', async () => {
      cy.add({ group: 'nodes', data: { id: 'lone' } });
      const lone = cy.getElementById('lone');

      const sequence = controller.executeAnimationSequence(
        cy,
        emptySyncResult({ addedNodeIds: new Set(['lone']) })
      );

      // No stem edge — the scale-in starts immediately: revealed, but as a dot.
      expect(num(lone, 'opacity')).toBe(1);
      expect(num(lone, 'width')).toBe(1);

      await vi.advanceTimersByTimeAsync(SPROUT_NODE_MS);
      await sequence;
      expect(num(lone, 'opacity')).toBe(1);
      expect(num(lone, 'width')).toBe(40);
    });

    it('drops inline opacity so ghost stylesheet styling applies after sprout (T9)', async () => {
      cy.add({ group: 'nodes', data: { id: 'g1' }, classes: 'ghost' });
      const ghost = cy.getElementById('g1');

      const sequence = controller.executeAnimationSequence(
        cy,
        emptySyncResult({ addedNodeIds: new Set(['g1']) })
      );

      await vi.advanceTimersByTimeAsync(SPROUT_NODE_MS);
      await sequence;
      // An orphaned inline opacity would render the ghost fully opaque.
      expect(num(ghost, 'opacity')).toBeCloseTo(0.15);
    });

    it('does not sprout flower compounds', async () => {
      cy.add({ group: 'nodes', data: { id: 'flower1' }, classes: 'flower' });
      const flower = cy.getElementById('flower1');

      const sequence = controller.executeAnimationSequence(
        cy,
        emptySyncResult({ addedNodeIds: new Set(['flower1']) })
      );

      expect(num(flower, 'opacity')).toBe(1); // never hidden
      await vi.advanceTimersByTimeAsync(SPROUT_EDGE_MS + SPROUT_NODE_MS);
      await sequence;
    });

    it('reduced motion: resolves immediately with elements at final state', async () => {
      controller = new AnimationController({ prefersReducedMotion: () => true });
      cy.add([
        { group: 'nodes', data: { id: 'a' } },
        { group: 'nodes', data: { id: 'b' } },
        { group: 'edges', data: { id: 'e1', source: 'a', target: 'b' } },
      ]);

      await controller.executeAnimationSequence(
        cy,
        emptySyncResult({ addedNodeIds: new Set(['b']), addedEdgeIds: new Set(['e1']) })
      );

      expect(num(cy.getElementById('b'), 'opacity')).toBe(1);
      expect(cy.getElementById('e1').style('line-style')).toBe('solid');
    });

    it('handles an empty sync result', async () => {
      await expect(
        controller.executeAnimationSequence(cy, emptySyncResult())
      ).resolves.toBeUndefined();
    });
  });

  describe('bloom', () => {
    it('pulses a single expanding ring on a confirmed node, then cleans up', async () => {
      cy.add({ group: 'nodes', data: { id: 'n1' }, classes: 'solid' });
      const node = cy.getElementById('n1');

      const sequence = controller.executeAnimationSequence(
        cy,
        emptySyncResult({ confirmedNodeIds: new Set(['n1']) })
      );

      // Pulse armed synchronously.
      expect(num(node, 'overlay-opacity')).toBeCloseTo(0.4);

      await vi.advanceTimersByTimeAsync(BLOOM_MS + 50);
      await sequence;
      // Inline overlay styles removed — back to the stylesheet default (0).
      expect(num(node, 'overlay-opacity')).toBe(0);
    });

    it('reduced motion: no pulse (class flip restyles instantly)', async () => {
      controller = new AnimationController({ prefersReducedMotion: () => true });
      cy.add({ group: 'nodes', data: { id: 'n1' }, classes: 'solid' });
      const node = cy.getElementById('n1');

      await controller.executeAnimationSequence(
        cy,
        emptySyncResult({ confirmedNodeIds: new Set(['n1']) })
      );

      expect(num(node, 'overlay-opacity')).toBe(0);
    });
  });

  describe('wilt', () => {
    it('defers removal until the wilt completes', async () => {
      cy.add({ group: 'nodes', data: { id: 'doomed' } });
      const node = cy.getElementById('doomed');

      controller.wiltAndRemove(node);

      expect(cy.getElementById('doomed').nonempty()).toBe(true); // still there
      expect(node.hasClass('wilting')).toBe(true);
      expect(controller.pendingWiltCount).toBe(1);

      await vi.advanceTimersByTimeAsync(WILT_MS);
      expect(cy.getElementById('doomed').nonempty()).toBe(false); // now removed
      expect(controller.pendingWiltCount).toBe(0);
    });

    it('wilts edges as well as nodes', async () => {
      cy.add([
        { group: 'nodes', data: { id: 'a' } },
        { group: 'nodes', data: { id: 'b' } },
        { group: 'edges', data: { id: 'e1', source: 'a', target: 'b' } },
      ]);

      controller.wiltAndRemove(cy.getElementById('e1'));
      expect(cy.getElementById('e1').nonempty()).toBe(true);

      await vi.advanceTimersByTimeAsync(WILT_MS);
      expect(cy.getElementById('e1').nonempty()).toBe(false);
    });

    it('is idempotent while an element is already wilting', async () => {
      cy.add({ group: 'nodes', data: { id: 'doomed' } });
      const node = cy.getElementById('doomed');

      controller.wiltAndRemove(node);
      controller.wiltAndRemove(node);
      expect(controller.pendingWiltCount).toBe(1);

      await vi.advanceTimersByTimeAsync(WILT_MS);
      expect(cy.getElementById('doomed').nonempty()).toBe(false);
    });

    it('cancelling a wilt keeps the element and restores its styling in place', async () => {
      cy.add({ group: 'nodes', data: { id: 'phoenix' }, position: { x: 10, y: 20 } });
      const node = cy.getElementById('phoenix');

      controller.wiltAndRemove(node);
      const handle = node.scratch(PENDING_REMOVAL_SCRATCH) as PendingRemovalHandle;
      expect(typeof handle.cancel).toBe('function');

      // Layout moves the (still-present) element while it wilts — the revive
      // must keep the CURRENT position, not teleport back to the wilt-start one.
      node.position({ x: 300, y: 400 });

      handle.cancel!();

      expect(controller.pendingWiltCount).toBe(0);
      expect(node.hasClass('wilting')).toBe(false);
      expect(node.scratch(PENDING_REMOVAL_SCRATCH)).toBeUndefined();
      expect(num(node, 'opacity')).toBe(1); // inline wilt styles dropped
      expect(node.position()).toEqual({ x: 300, y: 400 }); // revived where it is

      // The original removal timer must not fire.
      await vi.advanceTimersByTimeAsync(WILT_MS * 2);
      expect(cy.getElementById('phoenix').nonempty()).toBe(true);
    });

    it('reduced motion: removes immediately', () => {
      controller = new AnimationController({ prefersReducedMotion: () => true });
      cy.add({ group: 'nodes', data: { id: 'doomed' } });

      controller.wiltAndRemove(cy.getElementById('doomed'));

      expect(cy.getElementById('doomed').nonempty()).toBe(false);
      expect(controller.pendingWiltCount).toBe(0);
    });

    it('stopAll removes wilting elements immediately (unmount path)', async () => {
      cy.add({ group: 'nodes', data: { id: 'doomed' } });
      controller.wiltAndRemove(cy.getElementById('doomed'));

      controller.stopAll(cy);

      expect(cy.getElementById('doomed').nonempty()).toBe(false);
      expect(controller.pendingWiltCount).toBe(0);
      // Cleared timers must not throw later.
      await vi.advanceTimersByTimeAsync(WILT_MS * 2);
    });

    it('is safe when the core is destroyed mid-wilt', async () => {
      cy.add({ group: 'nodes', data: { id: 'doomed' } });
      controller.wiltAndRemove(cy.getElementById('doomed'));

      cy.destroy();
      await vi.advanceTimersByTimeAsync(WILT_MS * 2); // must not throw
      controller.stopAll(cy); // must not throw against a destroyed core
    });
  });

  describe('wilt × sprout collision', () => {
    const addStemFixture = () => {
      cy.add([
        { group: 'nodes', data: { id: 'existing' }, position: { x: 0, y: 0 } },
        { group: 'nodes', data: { id: 'fresh' }, position: { x: 100, y: 0 } },
        { group: 'edges', data: { id: 'e1', source: 'existing', target: 'fresh' } },
      ]);
    };

    it('a wilt starting mid-scale-in is never snapped back to full size', async () => {
      addStemFixture();
      const fresh = cy.getElementById('fresh');

      void controller.executeAnimationSequence(
        cy,
        emptySyncResult({ addedNodeIds: new Set(['fresh']), addedEdgeIds: new Set(['e1']) })
      );

      // Scale-in has started at the edge beat: the node is a dot.
      await vi.advanceTimersByTimeAsync(SPROUT_EDGE_MS);
      expect(num(fresh, 'width')).toBe(1);

      // Data removes the node mid-scale-in → the wilt takes over.
      controller.wiltAndRemove(fresh);
      expect(fresh.hasClass('wilting')).toBe(true);

      // The sprout settle beat must bail: finalisation would drop the inline
      // width (snap to the full 40px) under the wilt tween.
      await vi.advanceTimersByTimeAsync(SPROUT_NODE_MS);
      expect(num(fresh, 'width')).toBe(1);
      expect(fresh.hasClass('wilting')).toBe(true);

      // The wilt then completes and removes the element.
      await vi.advanceTimersByTimeAsync(WILT_MS);
      expect(cy.getElementById('fresh').nonempty()).toBe(false);
    });

    it('a node wilted before its reveal cue never flashes visible', async () => {
      addStemFixture();
      const fresh = cy.getElementById('fresh');

      void controller.executeAnimationSequence(
        cy,
        emptySyncResult({ addedNodeIds: new Set(['fresh']), addedEdgeIds: new Set(['e1']) })
      );

      // Still hidden — its stem edge is growing.
      expect(num(fresh, 'opacity')).toBe(0);
      controller.wiltAndRemove(fresh);

      // The scale-in cue must bail: no reveal, ever.
      await vi.advanceTimersByTimeAsync(SPROUT_EDGE_MS + SPROUT_NODE_MS);
      expect(num(fresh, 'opacity')).toBe(0);

      await vi.advanceTimersByTimeAsync(WILT_MS);
      expect(cy.getElementById('fresh').nonempty()).toBe(false);
    });

    it('an edge wilted mid-sweep is not snapped to a full line', async () => {
      cy.add([
        { group: 'nodes', data: { id: 'a' }, position: { x: 0, y: 0 } },
        { group: 'nodes', data: { id: 'b' }, position: { x: 100, y: 0 } },
        { group: 'edges', data: { id: 'e1', source: 'a', target: 'b' } },
      ]);
      const edge = cy.getElementById('e1');

      void controller.executeAnimationSequence(
        cy,
        emptySyncResult({ addedEdgeIds: new Set(['e1']) })
      );

      // Sweep armed (both endpoints pre-existed → grows immediately).
      expect(edge.style('line-style')).toBe('dashed');

      controller.wiltAndRemove(edge);

      // Finalisation must bail: the inline dash sweep styles stay (bailing
      // means no stop(jump-to-end) + removeStyle back to a solid full line).
      await vi.advanceTimersByTimeAsync(SPROUT_EDGE_MS);
      expect(edge.style('line-style')).toBe('dashed');

      await vi.advanceTimersByTimeAsync(WILT_MS);
      expect(cy.getElementById('e1').nonempty()).toBe(false);
    });
  });

  describe('camera', () => {
    it('startCameraFit excludes wilting elements from the frame', () => {
      cy.add([
        { group: 'nodes', data: { id: 'alive' }, position: { x: 0, y: 0 } },
        { group: 'nodes', data: { id: 'dying' }, position: { x: 500, y: 0 } },
      ]);
      controller.wiltAndRemove(cy.getElementById('dying'));

      const animate = vi.spyOn(cy, 'animate');
      controller.startCameraFit(cy);

      expect(animate).toHaveBeenCalledTimes(1);
      const arg = animate.mock.calls[0][0] as {
        fit: { eles: CollectionReturnValue; padding: number };
      };
      const ids = arg.fit.eles.map((ele) => ele.id());
      expect(ids).toContain('alive');
      expect(ids).not.toContain('dying');
    });

    it('honours eles/padding options and reduced motion (instant fit)', () => {
      controller = new AnimationController({ prefersReducedMotion: () => true });
      cy.add([
        { group: 'nodes', data: { id: 'a' }, position: { x: 0, y: 0 } },
        { group: 'nodes', data: { id: 'b' }, position: { x: 100, y: 0 } },
      ]);

      const fit = vi.spyOn(cy, 'fit');
      const animate = vi.spyOn(cy, 'animate');
      controller.startCameraFit(cy, { eles: cy.elements('#a'), padding: 96, duration: 700 });

      expect(animate).not.toHaveBeenCalled(); // no tween under reduced motion
      expect(fit).toHaveBeenCalledTimes(1);
      const [eles, padding] = fit.mock.calls[0] as [CollectionReturnValue, number];
      expect(eles.map((ele) => ele.id())).toEqual(['a']);
      expect(padding).toBe(96);
    });
  });

  describe('portrait mode (setPortrait)', () => {
    it('suppresses the growth camera fit entirely', async () => {
      cy.add({ group: 'nodes', data: { id: 'a' } });
      controller.setPortrait(true);

      const animate = vi.spyOn(cy, 'animate');
      const fit = vi.spyOn(cy, 'fit');
      await controller.executeAnimationSequence(
        cy,
        emptySyncResult({ addedNodeIds: new Set(['a']) })
      );

      expect(animate).not.toHaveBeenCalled();
      expect(fit).not.toHaveBeenCalled();
    });

    it('runs no verbs: instant final states, no pulse, immediate removals', async () => {
      controller.setPortrait(true);
      cy.add({ group: 'nodes', data: { id: 'n1' }, classes: 'solid' });

      await controller.executeAnimationSequence(
        cy,
        emptySyncResult({ addedNodeIds: new Set(['n1']), confirmedNodeIds: new Set(['n1']) })
      );

      const node = cy.getElementById('n1');
      expect(num(node, 'opacity')).toBe(1); // appeared instantly, never hidden
      expect(num(node, 'overlay-opacity')).toBe(0); // no bloom pulse

      controller.wiltAndRemove(node);
      expect(cy.getElementById('n1').nonempty()).toBe(false); // removed instantly
      expect(controller.pendingWiltCount).toBe(0);
    });

    it('verbs animate again after setPortrait(false)', () => {
      controller.setPortrait(true);
      controller.setPortrait(false);
      cy.add({ group: 'nodes', data: { id: 'doomed' } });

      controller.wiltAndRemove(cy.getElementById('doomed'));
      expect(cy.getElementById('doomed').nonempty()).toBe(true); // deferred again
      expect(controller.pendingWiltCount).toBe(1);
    });
  });

  describe('timer hygiene (stopAll)', () => {
    it('leaves no timer alive when stopped mid-choreography (unmount path)', async () => {
      cy.add([
        { group: 'nodes', data: { id: 'existing' }, position: { x: 0, y: 0 } },
        { group: 'nodes', data: { id: 'fresh' }, position: { x: 100, y: 0 } },
        { group: 'edges', data: { id: 'e1', source: 'existing', target: 'fresh' } },
        { group: 'nodes', data: { id: 'confirmed' }, classes: 'solid' },
        { group: 'nodes', data: { id: 'doomed' } },
      ]);

      // A sprout (edge + node beats), a bloom cleanup and a wilt removal all
      // have timers armed at once.
      void controller.executeAnimationSequence(
        cy,
        emptySyncResult({
          addedNodeIds: new Set(['fresh']),
          addedEdgeIds: new Set(['e1']),
          confirmedNodeIds: new Set(['confirmed']),
        })
      );
      controller.wiltAndRemove(cy.getElementById('doomed'));
      expect(controller.pendingChoreographyCount).toBeGreaterThan(0);
      expect(controller.pendingWiltCount).toBe(1);

      controller.stopAll(cy);

      // Every controller timer is gone and mid-wilt elements were removed
      // immediately.
      expect(controller.pendingWiltCount).toBe(0);
      expect(controller.pendingChoreographyCount).toBe(0);
      expect(cy.getElementById('doomed').nonempty()).toBe(false);

      // The only timer that may remain is cytoscape's own animation-step
      // tick (armed by ele.animate); it dies with the core. After destroy,
      // NOTHING is left to fire — the unmount path leaks no timers.
      cy.destroy();
      await vi.advanceTimersByTimeAsync(WILT_MS * 3);
      expect(vi.getTimerCount()).toBe(0);
    });
  });
});

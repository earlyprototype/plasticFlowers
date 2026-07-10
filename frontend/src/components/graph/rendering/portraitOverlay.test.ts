import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import cytoscape, { type Core } from 'cytoscape';

import { createPortraitOverlay, type PortraitInfo, type PortraitOverlay } from './portraitOverlay';

/** Minimal recording stub of a CanvasRenderingContext2D (portrait chrome ops). */
function makeStubCtx() {
  const calls: Array<{ op: string; args: unknown[]; fillStyle?: unknown }> = [];
  const record =
    (op: string) =>
    (...args: unknown[]) => {
      calls.push({ op, args });
    };
  const gradientStops: Array<{ offset: number; color: string }> = [];
  const gradient = {
    addColorStop: (offset: number, color: string) => {
      gradientStops.push({ offset, color });
    },
  };
  const ctx = {
    calls,
    gradientStops,
    gradient,
    fillStyle: '' as unknown,
    strokeStyle: '',
    lineWidth: 0,
    font: '',
    textAlign: '',
    textBaseline: '',
    globalAlpha: 1,
    setTransform: record('setTransform'),
    clearRect: record('clearRect'),
    strokeRect: record('strokeRect'),
    beginPath: record('beginPath'),
    moveTo: record('moveTo'),
    lineTo: record('lineTo'),
    stroke: record('stroke'),
    fillText: record('fillText'),
    measureText: () => ({ width: 120 }),
    createLinearGradient: (...args: unknown[]) => {
      calls.push({ op: 'createLinearGradient', args });
      return gradient;
    },
    fillRect(...args: unknown[]) {
      calls.push({ op: 'fillRect', args, fillStyle: this.fillStyle });
    },
  };
  return ctx;
}

type StubCtx = ReturnType<typeof makeStubCtx>;

function makeStubCanvas(ctx: StubCtx): HTMLCanvasElement {
  return {
    getContext: () => ctx,
    style: {},
    width: 0,
    height: 0,
    clientWidth: 800,
    clientHeight: 600,
  } as unknown as HTMLCanvasElement;
}

const INFO: PortraitInfo = {
  title: 'Design Lecture',
  dateLabel: '10 July 2026',
  durationLabel: '29 min',
  conceptCount: 14,
  islandCount: 4,
};

describe('portraitOverlay', () => {
  let cy: Core;
  let ctx: StubCtx;
  let overlay: PortraitOverlay | null = null;
  let pendingFrames: FrameRequestCallback[] = [];

  /** Run all queued rAF callbacks (one "frame"). */
  const flushFrame = () => {
    const callbacks = pendingFrames;
    pendingFrames = [];
    callbacks.forEach((cb) => cb(0));
  };

  beforeEach(() => {
    pendingFrames = [];
    vi.stubGlobal('requestAnimationFrame', (cb: FrameRequestCallback) => {
      pendingFrames.push(cb);
      return pendingFrames.length;
    });
    vi.stubGlobal('cancelAnimationFrame', () => {});
    vi.stubGlobal('window', { devicePixelRatio: 2 });

    cy = cytoscape({ headless: true, styleEnabled: true });
    ctx = makeStubCtx();
  });

  afterEach(() => {
    overlay?.destroy();
    overlay = null;
    cy.destroy();
    vi.unstubAllGlobals();
  });

  const texts = () => ctx.calls.filter((c) => c.op === 'fillText').map((c) => String(c.args[0]));

  it('draws the double-rule neatline, title block and time legend', () => {
    overlay = createPortraitOverlay(cy, makeStubCanvas(ctx));
    overlay.setInfo(INFO);
    flushFrame();

    // Neatline: two rules (outer heavy + inner hairline), plus the legend
    // bar outline.
    const strokeRects = ctx.calls.filter((c) => c.op === 'strokeRect');
    expect(strokeRects).toHaveLength(3);

    // Title block: title, uppercased meta, stats line.
    expect(texts()).toContain('Design Lecture');
    expect(texts()).toContain('10 JULY 2026 · 29 MIN');
    expect(texts()).toContain('14 concepts across 4 islands · plasticFlowers');

    // Legend: ramp ticks and the caption.
    expect(texts()).toContain('0 min');
    expect(texts()).toContain('30+ min');
    expect(texts()).toContain('colour = when the idea appeared');

    // Gradient bar: dawn → amber stops, filled with the gradient object.
    expect(ctx.gradientStops[0].offset).toBe(0);
    expect(ctx.gradientStops[ctx.gradientStops.length - 1].offset).toBe(1);
    const gradientFills = ctx.calls.filter(
      (c) => c.op === 'fillRect' && c.fillStyle === ctx.gradient
    );
    expect(gradientFills).toHaveLength(1);
  });

  it('draws in screen coordinates at dpr scale (no pan/zoom in the transform)', () => {
    cy.zoom(3);
    cy.pan({ x: 50, y: 60 });
    overlay = createPortraitOverlay(cy, makeStubCanvas(ctx));
    overlay.setInfo(INFO);
    flushFrame();

    const transforms = ctx.calls.filter((c) => c.op === 'setTransform');
    // clearRect pass at identity, chrome at dpr(2) only, then reset —
    // Cytoscape's zoom/pan must never leak into the chrome.
    expect(transforms.map((t) => t.args)).toEqual([
      [1, 0, 0, 1, 0, 0],
      [2, 0, 0, 2, 0, 0],
      [1, 0, 0, 1, 0, 0],
    ]);
  });

  it('renderTo draws at an arbitrary export scale without touching the canvas', () => {
    overlay = createPortraitOverlay(cy, makeStubCanvas(ctx));
    overlay.setInfo(INFO);
    flushFrame();
    ctx.calls.length = 0;

    const exportCtx = makeStubCtx();
    overlay.renderTo(exportCtx as unknown as CanvasRenderingContext2D, 800, 600, 2);

    const transforms = exportCtx.calls.filter((c) => c.op === 'setTransform');
    expect(transforms[0].args).toEqual([2, 0, 0, 2, 0, 0]);
    expect(transforms[transforms.length - 1].args).toEqual([1, 0, 0, 1, 0, 0]);
    expect(exportCtx.calls.filter((c) => c.op === 'fillText').length).toBeGreaterThan(0);
    // The live canvas saw nothing.
    expect(ctx.calls).toHaveLength(0);
  });

  it('redraws on cy resize but NOT on viewport (pan/zoom) changes', () => {
    overlay = createPortraitOverlay(cy, makeStubCanvas(ctx));
    overlay.setInfo(INFO);
    flushFrame();

    cy.zoom(2);
    cy.pan({ x: 9, y: 9 });
    expect(pendingFrames).toHaveLength(0);

    cy.emit('resize');
    expect(pendingFrames).toHaveLength(1);
    flushFrame();
  });

  it('destroy removes the resize listener and stops redraws', () => {
    overlay = createPortraitOverlay(cy, makeStubCanvas(ctx));
    overlay.setInfo(INFO);
    flushFrame();
    overlay.destroy();
    overlay = null;

    cy.emit('resize');
    expect(pendingFrames).toHaveLength(0);
  });
});

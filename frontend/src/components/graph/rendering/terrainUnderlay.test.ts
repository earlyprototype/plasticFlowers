import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import cytoscape, { type Core } from 'cytoscape';

import { createTerrainUnderlay, type TerrainUnderlay } from './terrainUnderlay';
import { CARTOGRAPHY_PALETTE } from '../config/cartography';
import type { Flower } from '../../../lib/types';

/** Minimal recording stub of a CanvasRenderingContext2D. */
function makeStubCtx() {
  const calls: Array<{ op: string; args: unknown[]; fillStyle?: string; strokeStyle?: string }> =
    [];
  const record =
    (op: string) =>
    (...args: unknown[]) => {
      calls.push({ op, args });
    };
  const ctx = {
    calls,
    fillStyle: '',
    strokeStyle: '',
    lineWidth: 0,
    font: '',
    textAlign: '',
    textBaseline: '',
    globalAlpha: 1,
    setTransform: record('setTransform'),
    fillRect: record('fillRect'),
    beginPath: record('beginPath'),
    moveTo: record('moveTo'),
    lineTo: record('lineTo'),
    closePath: record('closePath'),
    fill(...args: unknown[]) {
      calls.push({ op: 'fill', args, fillStyle: this.fillStyle });
    },
    stroke(...args: unknown[]) {
      calls.push({ op: 'stroke', args, strokeStyle: this.strokeStyle });
    },
    save: record('save'),
    restore: record('restore'),
    translate: record('translate'),
    rotate: record('rotate'),
    fillText: record('fillText'),
    measureText: () => ({ width: 8 }),
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

function makeFlower(id: string, label: string, memberIds: string[]): Flower {
  return {
    id,
    label,
    stem_node_id: memberIds[0] ?? '',
    edge_count: 0,
    member_ids: memberIds,
    created_at: '2026-01-01T00:00:00Z',
  };
}

describe('terrainUnderlay', () => {
  let cy: Core;
  let ctx: StubCtx;
  let underlay: TerrainUnderlay | null = null;
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
    underlay?.destroy();
    underlay = null;
    cy.destroy();
    vi.unstubAllGlobals();
  });

  function addMemberNodes() {
    cy.add([
      { group: 'nodes', data: { id: 'a' }, position: { x: 0, y: 0 } },
      { group: 'nodes', data: { id: 'b' }, position: { x: 100, y: 0 } },
      { group: 'nodes', data: { id: 'c' }, position: { x: 50, y: 80 } },
    ]);
  }

  const drawCount = () => ctx.calls.filter((c) => c.op === 'fillRect').length;

  it('draws three contour fills plus one coastline stroke per island', () => {
    addMemberNodes();
    underlay = createTerrainUnderlay(cy, makeStubCanvas(ctx));
    ctx.calls.length = 0;

    underlay.setFlowers([makeFlower('f1', 'Harbor', ['a', 'b', 'c'])]);
    flushFrame();

    const fills = ctx.calls.filter((c) => c.op === 'fill');
    expect(fills.map((f) => f.fillStyle)).toEqual([
      CARTOGRAPHY_PALETTE.terrain1,
      CARTOGRAPHY_PALETTE.terrain2,
      CARTOGRAPHY_PALETTE.terrain3,
    ]);
    const strokes = ctx.calls.filter((c) => c.op === 'stroke');
    expect(strokes).toHaveLength(1);
    expect(strokes[0].strokeStyle).toBe(CARTOGRAPHY_PALETTE.coast);
    // Island name arcs above the island: one fillText per character.
    const glyphs = ctx.calls.filter((c) => c.op === 'fillText');
    expect(glyphs.map((g) => g.args[0]).join('')).toBe('HARBOR');
  });

  it('applies (dpr·zoom, dpr·pan) as the model→screen transform', () => {
    addMemberNodes();
    underlay = createTerrainUnderlay(cy, makeStubCanvas(ctx));
    underlay.setFlowers([makeFlower('f1', 'Harbor', ['a', 'b', 'c'])]);
    flushFrame();

    cy.zoom(2);
    cy.pan({ x: 30, y: 40 });
    flushFrame();

    const transforms = ctx.calls.filter((c) => c.op === 'setTransform');
    // Last draw: identity (background pass) then dpr(2)·zoom(2) with dpr·pan.
    expect(transforms[transforms.length - 1].args).toEqual([4, 0, 0, 4, 60, 80]);
    expect(transforms[transforms.length - 2].args).toEqual([1, 0, 0, 1, 0, 0]);
  });

  it('redraws on viewport and node position changes, coalesced per frame', () => {
    addMemberNodes();
    underlay = createTerrainUnderlay(cy, makeStubCanvas(ctx));
    underlay.setFlowers([makeFlower('f1', 'Harbor', ['a', 'b', 'c'])]);
    flushFrame();

    const before = drawCount();
    // A zoom AND a node move within the same frame coalesce into ONE draw.
    cy.zoom(1.5);
    cy.getElementById('a').position({ x: 10, y: 10 });
    expect(pendingFrames).toHaveLength(1);
    flushFrame();
    expect(drawCount()).toBe(before + 1);

    // The next viewport change schedules a fresh frame.
    cy.pan({ x: 5, y: 5 });
    flushFrame();
    expect(drawCount()).toBe(before + 2);
  });

  it('skips flowers with no positioned members but still paints the paper', () => {
    underlay = createTerrainUnderlay(cy, makeStubCanvas(ctx));
    ctx.calls.length = 0;

    underlay.setFlowers([makeFlower('f-empty', 'Ghost Isle', ['missing-1', 'missing-2'])]);
    flushFrame();

    expect(drawCount()).toBe(1); // background fill only
    expect(ctx.calls.filter((c) => c.op === 'fill')).toHaveLength(0);
    expect(ctx.calls.filter((c) => c.op === 'fillText')).toHaveLength(0);
  });

  it('destroy removes listeners so later viewport changes do not draw', () => {
    addMemberNodes();
    underlay = createTerrainUnderlay(cy, makeStubCanvas(ctx));
    underlay.setFlowers([makeFlower('f1', 'Harbor', ['a', 'b', 'c'])]);
    flushFrame();
    underlay.destroy();
    underlay = null;

    const before = drawCount();
    cy.zoom(3);
    cy.getElementById('a').position({ x: 99, y: 99 });
    expect(pendingFrames).toHaveLength(0);
    flushFrame();
    expect(drawCount()).toBe(before);
  });
});

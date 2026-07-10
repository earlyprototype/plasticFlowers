import { describe, expect, it } from 'vitest';

import {
  BIRTH_AMBER,
  BIRTH_DAWN,
  BIRTH_FILL_PAPER_MIX,
  BIRTH_GHOST_PAPER_MIX,
  BIRTH_MOSS,
  BIRTH_PAPER,
  BLOB_STEPS,
  CARTOGRAPHY_PALETTE,
  ISLAND_PADDING,
  SESSION_HUE_SPAN_MS,
  TERRAIN_LEVELS,
  Y_SQUASH,
  arcLabelPlacements,
  birthColor,
  birthFill,
  birthGhostTint,
  blobPath,
  blobRadius,
  centroidOf,
  hashPhase,
  islandBaseRadius,
  islandLabelRadius,
  isCartographyEnabled,
  mixHex,
} from './cartography';

describe('hashPhase', () => {
  it('is deterministic for the same flower id', () => {
    expect(hashPhase('flower-123')).toBe(hashPhase('flower-123'));
    expect(hashPhase('')).toBe(hashPhase(''));
  });

  it('returns a phase in [0, 2π)', () => {
    for (const id of ['a', 'flower-123', 'f-hierarchy', 'x'.repeat(64), '']) {
      const phase = hashPhase(id);
      expect(phase).toBeGreaterThanOrEqual(0);
      expect(phase).toBeLessThan(Math.PI * 2);
    }
  });

  it('gives different phases for different ids', () => {
    expect(hashPhase('flower-a')).not.toBe(hashPhase('flower-b'));
  });
});

describe('centroidOf / islandBaseRadius', () => {
  const square = [
    { x: 0, y: 0 },
    { x: 100, y: 0 },
    { x: 100, y: 100 },
    { x: 0, y: 100 },
  ];

  it('computes the arithmetic centroid', () => {
    expect(centroidOf(square)).toEqual({ x: 50, y: 50 });
    expect(centroidOf([{ x: 7, y: -3 }])).toEqual({ x: 7, y: -3 });
  });

  it('baseR is the max member distance plus the island padding', () => {
    const centroid = centroidOf(square);
    // Corner distance from (50,50) is 50·√2.
    expect(islandBaseRadius(square, centroid)).toBeCloseTo(50 * Math.SQRT2 + ISLAND_PADDING, 10);
  });

  it('a single member yields just the padding (padding overridable)', () => {
    const p = [{ x: 10, y: 10 }];
    expect(islandBaseRadius(p, centroidOf(p))).toBe(ISLAND_PADDING);
    expect(islandBaseRadius(p, centroidOf(p), 10)).toBe(10);
  });
});

describe('blobRadius / blobPath', () => {
  it('matches the two-lobe formula', () => {
    const baseR = 100;
    const phase = 1.25;
    const a = 0.6;
    const expected =
      baseR * (1 + 0.16 * Math.sin(3 * a + phase) + 0.09 * Math.sin(5 * a + phase * 1.7));
    expect(blobRadius(baseR, a, phase)).toBeCloseTo(expected, 12);
  });

  it('produces a stable path for a fixed phase', () => {
    const centroid = { x: 0, y: 0 };
    const first = blobPath(centroid, 100, 0.5);
    const second = blobPath(centroid, 100, 0.5);
    expect(first).toEqual(second);
    expect(first).toHaveLength(BLOB_STEPS);
  });

  it('places sample points at r(a)·(cos a, sin a·squash) around the centroid', () => {
    const centroid = { x: 200, y: -50 };
    const baseR = 80;
    const phase = 2.0;
    const steps = 8;
    const path = blobPath(centroid, baseR, phase, 1, steps);
    expect(path).toHaveLength(steps);

    // Point 0 (angle 0): purely horizontal offset, unaffected by y-squash.
    expect(path[0].x).toBeCloseTo(centroid.x + blobRadius(baseR, 0, phase), 10);
    expect(path[0].y).toBeCloseTo(centroid.y, 10);

    // Point steps/4 (angle π/2): vertical offset squashed by Y_SQUASH.
    const aTop = Math.PI / 2;
    expect(path[2].x).toBeCloseTo(centroid.x, 10);
    expect(path[2].y).toBeCloseTo(centroid.y + blobRadius(baseR, aTop, phase) * Y_SQUASH, 10);
  });

  it('scales linearly with the contour scale factor', () => {
    const centroid = { x: 0, y: 0 };
    const base = blobPath(centroid, 100, 0.9, 1, 16);
    const outer = blobPath(centroid, 100, 0.9, 1.32, 16);
    for (let i = 0; i < base.length; i += 1) {
      expect(outer[i].x).toBeCloseTo(base[i].x * 1.32, 8);
      expect(outer[i].y).toBeCloseTo(base[i].y * 1.32, 8);
    }
  });

  it('phase changes the silhouette', () => {
    const a = blobPath({ x: 0, y: 0 }, 100, 0.1, 1, 16);
    const b = blobPath({ x: 0, y: 0 }, 100, 2.7, 1, 16);
    expect(a).not.toEqual(b);
  });
});

describe('arcLabelPlacements', () => {
  it('returns one placement per character, in order', () => {
    const widths = [8, 8, 8, 8];
    const placements = arcLabelPlacements('GRID', widths, 200);
    expect(placements.map((p) => p.char)).toEqual(['G', 'R', 'I', 'D']);
  });

  it('places every character exactly on the arc radius', () => {
    const placements = arcLabelPlacements('MAP', [10, 12, 10], 150);
    for (const p of placements) {
      expect(Math.hypot(p.x, p.y)).toBeCloseTo(150, 10);
    }
  });

  it('centres the text on the top of the island (angle -π/2)', () => {
    // Symmetric widths → placements mirror around x = 0, above the centroid.
    const placements = arcLabelPlacements('AA', [10, 10], 100, 4);
    expect(placements[0].x).toBeCloseTo(-placements[1].x, 10);
    expect(placements[0].y).toBeCloseTo(placements[1].y, 10);
    expect(placements[0].y).toBeLessThan(0); // above the centroid (canvas y-down)
  });

  it('a single character sits exactly at the top with no rotation', () => {
    const [p] = arcLabelPlacements('A', [12], 100);
    expect(p.x).toBeCloseTo(0, 10);
    expect(p.y).toBeCloseTo(-100, 10);
    expect(p.rotation).toBeCloseTo(0, 10);
  });

  it('advances by charWidth + spacing along the arc', () => {
    const radius = 100;
    const spacing = 6;
    const widths = [10, 20];
    const [a, b] = arcLabelPlacements('AB', widths, radius, spacing);
    const angleA = Math.atan2(a.y, a.x);
    const angleB = Math.atan2(b.y, b.x);
    // Arc length between char centres = w0/2 + spacing + w1/2.
    expect((angleB - angleA) * radius).toBeCloseTo(10 / 2 + spacing + 20 / 2, 10);
  });

  it('rotation keeps each glyph tangent to the arc (angle + π/2)', () => {
    const placements = arcLabelPlacements('ABC', [10, 10, 10], 80, 2);
    for (const p of placements) {
      expect(p.rotation).toBeCloseTo(Math.atan2(p.y, p.x) + Math.PI / 2, 10);
    }
  });

  it('handles empty labels and non-positive radii', () => {
    expect(arcLabelPlacements('', [], 100)).toEqual([]);
    expect(arcLabelPlacements('AB', [5, 5], 0)).toEqual([]);
  });
});

describe('islandLabelRadius', () => {
  it('is baseR·1.05 + 30', () => {
    expect(islandLabelRadius(100)).toBeCloseTo(135, 10);
    expect(islandLabelRadius(0)).toBeCloseTo(30, 10);
  });
});

describe('isCartographyEnabled', () => {
  it('defaults to on when the variable is unset', () => {
    expect(isCartographyEnabled(undefined)).toBe(true);
  });

  it("only '0' and 'false' disable it", () => {
    expect(isCartographyEnabled('0')).toBe(false);
    expect(isCartographyEnabled('false')).toBe(false);
    expect(isCartographyEnabled('1')).toBe(true);
    expect(isCartographyEnabled('true')).toBe(true);
    expect(isCartographyEnabled('')).toBe(true);
  });
});

describe('mixHex', () => {
  it('returns the endpoints at t = 0 and t = 1', () => {
    expect(mixHex('#000000', '#FFFFFF', 0)).toBe('#000000');
    expect(mixHex('#000000', '#FFFFFF', 1)).toBe('#FFFFFF');
  });

  it('blends channel-wise at the midpoint', () => {
    // 127.5 rounds to 128 = 0x80 per channel.
    expect(mixHex('#000000', '#FFFFFF', 0.5)).toBe('#808080');
    expect(mixHex('#FF0000', '#0000FF', 0.5)).toBe('#800080');
  });

  it('clamps t outside [0, 1]', () => {
    expect(mixHex('#102030', '#405060', -3)).toBe('#102030');
    expect(mixHex('#102030', '#405060', 7)).toBe('#405060');
  });
});

describe('birthColor (time as colour)', () => {
  const start = Date.parse('2026-07-10T10:00:00Z');
  const end = start + SESSION_HUE_SPAN_MS;

  it('hits the ramp stops at 0 / 0.5 / 1', () => {
    expect(birthColor(start, start, end)).toBe(BIRTH_DAWN);
    expect(birthColor(start + SESSION_HUE_SPAN_MS / 2, start, end)).toBe(BIRTH_MOSS);
    expect(birthColor(end, start, end)).toBe(BIRTH_AMBER);
  });

  it('clamps births before the window to dawn and after it to amber', () => {
    expect(birthColor(start - 60_000, start, end)).toBe(BIRTH_DAWN);
    expect(birthColor(end + 60 * 60_000, start, end)).toBe(BIRTH_AMBER);
  });

  it('blends piecewise-linearly between the stops', () => {
    // Quarter of the window = halfway through the dawn→moss segment.
    expect(birthColor(start + SESSION_HUE_SPAN_MS / 4, start, end)).toBe(
      mixHex(BIRTH_DAWN, BIRTH_MOSS, 0.5)
    );
    // Three quarters = halfway through the moss→amber segment.
    expect(birthColor(start + (SESSION_HUE_SPAN_MS * 3) / 4, start, end)).toBe(
      mixHex(BIRTH_MOSS, BIRTH_AMBER, 0.5)
    );
  });

  it('is deterministic for the same inputs', () => {
    const t = start + 7 * 60_000;
    expect(birthColor(t, start, end)).toBe(birthColor(t, start, end));
  });

  it('degenerate windows (zero-length, inverted, NaN) yield dawn', () => {
    expect(birthColor(start, start, start)).toBe(BIRTH_DAWN);
    expect(birthColor(start + 1000, start, start)).toBe(BIRTH_DAWN);
    expect(birthColor(start, end, start)).toBe(BIRTH_DAWN); // inverted span
    expect(birthColor(Number.NaN, Number.NaN, Number.NaN)).toBe(BIRTH_DAWN);
  });
});

describe('birthFill / birthGhostTint', () => {
  it('mix the birth colour toward paper by the documented amounts', () => {
    expect(birthFill(BIRTH_DAWN)).toBe(mixHex(BIRTH_DAWN, BIRTH_PAPER, BIRTH_FILL_PAPER_MIX));
    expect(birthGhostTint(BIRTH_AMBER)).toBe(
      mixHex(BIRTH_AMBER, BIRTH_PAPER, BIRTH_GHOST_PAPER_MIX)
    );
  });

  it('fill sits closer to paper than the ghost tint (labels stay legible)', () => {
    expect(BIRTH_FILL_PAPER_MIX).toBeGreaterThan(BIRTH_GHOST_PAPER_MIX);
  });
});

describe('palette / terrain levels', () => {
  it('exposes the chart-paper token set (light app background)', () => {
    expect(CARTOGRAPHY_PALETTE.terrain1).toBe('#E3E6D3');
    expect(CARTOGRAPHY_PALETTE.terrain2).toBe('#D8DDC4');
    expect(CARTOGRAPHY_PALETTE.terrain3).toBe('#CDD4B6');
    expect(CARTOGRAPHY_PALETTE.coast).toBe('#A8B196');
  });

  it('draws shallows → land (+coastline) → highland, outermost first', () => {
    expect(TERRAIN_LEVELS.map((l) => l.scale)).toEqual([1.32, 1.1, 0.62]);
    expect(TERRAIN_LEVELS.map((l) => l.coastline)).toEqual([false, true, false]);
    expect(TERRAIN_LEVELS.map((l) => l.fill)).toEqual(['terrain1', 'terrain2', 'terrain3']);
  });
});

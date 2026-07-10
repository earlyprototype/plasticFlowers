/**
 * Cartography — palette tokens + pure geometry for the terrain underlay.
 *
 * The graph is rendered as a survey map: each flower (cluster) becomes an
 * organic island drawn on a <canvas> beneath the Cytoscape viewport, with
 * three contour levels (shallows / land / highland), a coastline stroke and
 * a curved serif label arcing above the island.
 *
 * Everything in this module is pure and unit-tested (cartography.test.ts);
 * the impure canvas work lives in ../rendering/terrainUnderlay.ts.
 */

export interface CartographyPalette {
  /** Chart-paper background painted by the underlay canvas. */
  bg: string;
  /** Outer contour — "shallows". */
  terrain1: string;
  /** Mid contour — "land". */
  terrain2: string;
  /** Inner contour — "highland". */
  terrain3: string;
  /** Coastline stroke around the land contour. */
  coast: string;
  /** Label ink for cartographic typography. */
  ink: string;
  /** Alpha applied to island-name ink (faint against the paper). */
  inkAlpha: number;
}

/**
 * The app background is light/neutral (globals.css `--canvas: #FFFFFF`,
 * page shell `#F5F5F4`), so we use the "chart paper" set: warm paper
 * background with muted moss/khaki terrain tones.
 */
export const CARTOGRAPHY_PALETTE: CartographyPalette = {
  bg: '#F4F3E9',
  terrain1: '#E3E6D3',
  terrain2: '#D8DDC4',
  terrain3: '#CDD4B6',
  coast: '#A8B196',
  ink: '#42493E',
  inkAlpha: 0.75,
};

/** Model-coordinate padding added beyond the farthest member node. */
export const ISLAND_PADDING = 46;

/** Vertical squash applied to island blobs (islands read wider than tall). */
export const Y_SQUASH = 0.82;

/** Sample count for a blob outline. */
export const BLOB_STEPS = 64;

/** Coastline stroke width in *screen* pixels (divide by zoom when drawing). */
export const COASTLINE_WIDTH = 1.2;

/** Contour levels drawn outermost-first. */
export const TERRAIN_LEVELS: ReadonlyArray<{
  scale: number;
  fill: keyof Pick<CartographyPalette, 'terrain1' | 'terrain2' | 'terrain3'>;
  coastline: boolean;
}> = [
  { scale: 1.32, fill: 'terrain1', coastline: false }, // shallows
  { scale: 1.1, fill: 'terrain2', coastline: true }, // land + coastline
  { scale: 0.62, fill: 'terrain3', coastline: false }, // highland
];

/** Canvas font string for island (flower) names. */
export const ISLAND_LABEL_FONT =
  "600 15px 'Iowan Old Style', 'Palatino Linotype', Palatino, Georgia, serif";

/** Extra arc-length spacing (px) inserted between island-name characters. */
export const ISLAND_LABEL_LETTER_SPACING = 5;

/** Radius of the arc the island name sits on. */
export function islandLabelRadius(baseR: number): number {
  return baseR * 1.05 + 30;
}

export interface Point {
  x: number;
  y: number;
}

/**
 * Deterministic phase in [0, 2π) derived from a flower id (FNV-1a hash),
 * so island silhouettes are stable across redraws and sessions.
 */
export function hashPhase(id: string): number {
  let h = 0x811c9dc5;
  for (let i = 0; i < id.length; i += 1) {
    h ^= id.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return ((h >>> 0) / 0x100000000) * Math.PI * 2;
}

/** Arithmetic centroid of a non-empty point set. */
export function centroidOf(points: readonly Point[]): Point {
  let x = 0;
  let y = 0;
  for (const p of points) {
    x += p.x;
    y += p.y;
  }
  const n = Math.max(points.length, 1);
  return { x: x / n, y: y / n };
}

/**
 * Base island radius: max distance from the centroid to any member,
 * plus a fixed organic margin (model coordinates).
 */
export function islandBaseRadius(
  points: readonly Point[],
  centroid: Point,
  padding: number = ISLAND_PADDING
): number {
  let max = 0;
  for (const p of points) {
    const d = Math.hypot(p.x - centroid.x, p.y - centroid.y);
    if (d > max) max = d;
  }
  return max + padding;
}

/** Blob radius at a given angle: two low-frequency sine lobes over baseR. */
export function blobRadius(baseR: number, angle: number, phase: number): number {
  return (
    baseR *
    (1 + 0.16 * Math.sin(3 * angle + phase) + 0.09 * Math.sin(5 * angle + phase * 1.7))
  );
}

/**
 * Closed organic blob outline around `centroid`, y-squashed by Y_SQUASH.
 * `scale` multiplies baseR to produce the contour levels.
 */
export function blobPath(
  centroid: Point,
  baseR: number,
  phase: number,
  scale = 1,
  steps: number = BLOB_STEPS
): Point[] {
  const points: Point[] = [];
  for (let i = 0; i < steps; i += 1) {
    const a = (i / steps) * Math.PI * 2;
    const r = blobRadius(baseR * scale, a, phase);
    points.push({
      x: centroid.x + r * Math.cos(a),
      y: centroid.y + r * Math.sin(a) * Y_SQUASH,
    });
  }
  return points;
}

export interface ArcCharPlacement {
  char: string;
  /** Offset from the island centroid (model coordinates). */
  x: number;
  y: number;
  /** Canvas rotation (radians) so the glyph sits tangent to the arc. */
  rotation: number;
}

/**
 * Place label characters along an arc of `radius` centred on the island,
 * arcing over its top (angle -π/2). `charWidths[i]` is the measured width
 * of `label[i]`; `spacing` is the extra arc length between characters.
 * Returned x/y are offsets from the island centroid.
 */
export function arcLabelPlacements(
  label: string,
  charWidths: readonly number[],
  radius: number,
  spacing: number = ISLAND_LABEL_LETTER_SPACING
): ArcCharPlacement[] {
  const chars = Array.from(label);
  const count = Math.min(chars.length, charWidths.length);
  if (count === 0 || radius <= 0) return [];

  let total = spacing * (count - 1);
  for (let i = 0; i < count; i += 1) total += charWidths[i];

  const placements: ArcCharPlacement[] = [];
  let arcPos = -total / 2;
  for (let i = 0; i < count; i += 1) {
    const mid = arcPos + charWidths[i] / 2;
    const angle = -Math.PI / 2 + mid / radius;
    placements.push({
      char: chars[i],
      x: radius * Math.cos(angle),
      y: radius * Math.sin(angle),
      rotation: angle + Math.PI / 2,
    });
    arcPos += charWidths[i] + spacing;
  }
  return placements;
}

/**
 * Feature flag: NEXT_PUBLIC_CARTOGRAPHY, default ON.
 * Only the literal strings '0' and 'false' disable it.
 */
export function isCartographyEnabled(
  value: string | undefined = process.env.NEXT_PUBLIC_CARTOGRAPHY
): boolean {
  return value !== '0' && value !== 'false';
}

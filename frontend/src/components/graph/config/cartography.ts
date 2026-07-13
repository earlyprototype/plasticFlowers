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
  bg: '#FFFFFF',
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

// --- Move 4: time as colour --------------------------------------------------
//
// Every node keeps the hue of its birth moment, so the finished map encodes
// chronology spatially. The ramp runs dawn indigo → moss → late amber with
// piecewise-linear RGB interpolation (first half dawn→moss, second half
// moss→amber).
//
// SPAN CONTRACT: hue is a function of ABSOLUTE birth time mapped over a FIXED
// reference window of SESSION_HUE_SPAN_MS starting at the session start
// (earliest node birth currently in the graph). Minute 0 = dawn, the midpoint
// = moss, anything at/after the end of the window = amber. Because the window
// is fixed, a node's colour never changes as the session extends — history is
// never repainted — and there is no dependency on a session "end". Sessions
// shorter than the window simply never reach amber, which is honest: the map
// only earns its sunset tones by running long.

/** Ramp stop: dawn indigo — the session's opening minutes. */
export const BIRTH_DAWN = '#6272B5';
/** Ramp stop: moss — the middle of the reference window. */
export const BIRTH_MOSS = '#4F8F68';
/** Ramp stop: late amber — at/after the end of the reference window. */
export const BIRTH_AMBER = '#C79A3F';

/** Fixed reference window for the birth-colour ramp (30 minutes). */
export const SESSION_HUE_SPAN_MS = 30 * 60 * 1000;

/**
 * Node "paper" fill (the cartography node background) that birth colours are
 * mixed toward for legible fills — labels sit on near-paper, never on a
 * saturated swatch.
 */
export const BIRTH_PAPER = '#FBFAF2';
/** How far a solid node's fill is mixed toward paper (0 = pure birth colour). */
export const BIRTH_FILL_PAPER_MIX = 0.75;
/** How far a ghost's dashed border tint is mixed toward paper. */
export const BIRTH_GHOST_PAPER_MIX = 0.5;

function hexToRgb(hex: string): [number, number, number] {
  const value = parseInt(hex.slice(1), 16);
  return [(value >> 16) & 0xff, (value >> 8) & 0xff, value & 0xff];
}

function rgbToHex(r: number, g: number, b: number): string {
  const to2 = (c: number) => Math.round(c).toString(16).padStart(2, '0').toUpperCase();
  return `#${to2(r)}${to2(g)}${to2(b)}`;
}

/**
 * Linear RGB mix of two hex colours: t = 0 → `a`, t = 1 → `b` (t clamped).
 * Deterministic (pure arithmetic + rounding), returns uppercase hex.
 */
export function mixHex(a: string, b: string, t: number): string {
  const tt = Math.min(Math.max(t, 0), 1);
  const [ar, ag, ab] = hexToRgb(a);
  const [br, bg, bb] = hexToRgb(b);
  return rgbToHex(ar + (br - ar) * tt, ag + (bg - ag) * tt, ab + (bb - ab) * tt);
}

/**
 * The birth colour of a node born at `birthMs`, mapped over the reference
 * window [sessionStartMs, sessionEndMs]: 0 → dawn, 0.5 → moss, 1 → amber,
 * piecewise-linear in RGB. Times outside the window clamp to the nearest
 * stop; a degenerate (zero/negative-length or non-finite) window yields dawn.
 */
export function birthColor(
  birthMs: number,
  sessionStartMs: number,
  sessionEndMs: number
): string {
  const span = sessionEndMs - sessionStartMs;
  let t = span > 0 ? (birthMs - sessionStartMs) / span : 0;
  if (!Number.isFinite(t)) t = 0;
  t = Math.min(Math.max(t, 0), 1);
  return t <= 0.5 ? mixHex(BIRTH_DAWN, BIRTH_MOSS, t * 2) : mixHex(BIRTH_MOSS, BIRTH_AMBER, (t - 0.5) * 2);
}

/** Legible node fill for a birth colour: mixed well toward paper. */
export function birthFill(color: string): string {
  return mixHex(color, BIRTH_PAPER, BIRTH_FILL_PAPER_MIX);
}

/** Reduced-strength tint for a ghost's dashed border. */
export function birthGhostTint(color: string): string {
  return mixHex(color, BIRTH_PAPER, BIRTH_GHOST_PAPER_MIX);
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

// --- Move 5: the session portrait --------------------------------------------
//
// Portrait mode is the presentation render of the finished map: ghosts hidden,
// camera fitted, and a chrome layer drawn ABOVE the graph in screen
// coordinates — a double-rule neatline (atlas plate style), a title block and
// a time-ramp legend. Everything below is pure geometry/text so it can be
// unit-tested; the impure canvas work lives in ../rendering/portraitOverlay.ts.

/** Outer neatline inset from the canvas edge (CSS px). */
export const NEATLINE_OUTER_INSET = 14;
/** Gap between the outer and inner neatline rules (CSS px). */
export const NEATLINE_GAP = 6;
/** Stroke width of the outer (heavy) neatline rule. */
export const NEATLINE_OUTER_WIDTH = 1.6;
/** Stroke width of the inner (hairline) neatline rule. */
export const NEATLINE_INNER_WIDTH = 0.6;

/** Camera padding (px) when fitting the confirmed graph on portrait entry. */
export const PORTRAIT_FIT_PADDING = 96;

/** Portrait typography — mirrors the established serif/sans tokens. */
export const PORTRAIT_TITLE_FONT =
  "600 26px 'Iowan Old Style', 'Palatino Linotype', Palatino, Georgia, serif";
export const PORTRAIT_META_FONT = '600 11px Nunito, system-ui, sans-serif';
export const PORTRAIT_STATS_FONT = '400 11px Nunito, system-ui, sans-serif';
export const PORTRAIT_TICK_FONT = '600 10px Nunito, system-ui, sans-serif';
export const PORTRAIT_CAPTION_FONT =
  "italic 400 11px 'Iowan Old Style', 'Palatino Linotype', Palatino, Georgia, serif";

export interface Rect {
  x: number;
  y: number;
  width: number;
  height: number;
}

/** The two neatline rectangles (outer heavy rule, inner hairline). */
export function neatlineRects(width: number, height: number): { outer: Rect; inner: Rect } {
  const o = NEATLINE_OUTER_INSET;
  const i = NEATLINE_OUTER_INSET + NEATLINE_GAP;
  return {
    outer: { x: o, y: o, width: width - 2 * o, height: height - 2 * o },
    inner: { x: i, y: i, width: width - 2 * i, height: height - 2 * i },
  };
}

/**
 * Session duration label from a millisecond span. Sub-minute sessions read
 * '<1 min'; an hour boundary switches to 'H h MM min'. Negative or non-finite
 * spans (no dated nodes yet) collapse to an em dash.
 */
export function formatSessionDuration(spanMs: number): string {
  if (!Number.isFinite(spanMs) || spanMs < 0) return '—';
  const totalMin = Math.round(spanMs / 60_000);
  if (totalMin < 1) return '<1 min';
  if (totalMin < 60) return `${totalMin} min`;
  const hours = Math.floor(totalMin / 60);
  const minutes = totalMin % 60;
  return minutes === 0 ? `${hours} h` : `${hours} h ${String(minutes).padStart(2, '0')} min`;
}

/** Atlas-style date label ('10 July 2026'); non-finite times → em dash. */
export function formatPortraitDate(ms: number, locale = 'en-GB'): string {
  if (!Number.isFinite(ms)) return '—';
  return new Date(ms).toLocaleDateString(locale, {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}

/**
 * Default portrait title: sessions only have ids today, so the plate reads
 * 'Session <short-id>' (long ids truncate to 8 chars). Persisting a custom
 * title to the backend is a follow-up — the freetext input is local state.
 */
export function defaultPortraitTitle(sessionId?: string | null): string {
  const id = sessionId?.trim();
  if (!id) return 'Session Portrait';
  return `Session ${id.length > 12 ? id.slice(0, 8) : id}`;
}

/**
 * Filename for the saved portrait PNG: short session id, or today's date
 * when no session id is known. `now` is injectable for tests.
 */
export function portraitExportFilename(
  sessionId?: string | null,
  now: () => Date = () => new Date()
): string {
  const id = sessionId?.trim();
  const stamp = id ? id.slice(0, 8) : now().toISOString().slice(0, 10);
  return `plasticflowers-portrait-${stamp}.png`;
}

/** 'N concepts across M islands · plasticFlowers' (singulars handled). */
export function portraitStatsLine(conceptCount: number, islandCount: number): string {
  const concepts = `${conceptCount} ${conceptCount === 1 ? 'concept' : 'concepts'}`;
  if (islandCount <= 0) return `${concepts} · plasticFlowers`;
  const islands = `${islandCount} ${islandCount === 1 ? 'island' : 'islands'}`;
  return `${concepts} across ${islands} · plasticFlowers`;
}

export interface PortraitTitleBlock {
  /** Serif headline. */
  title: string;
  /** Small-caps meta line: 'DATE · DURATION'. */
  meta: string;
  /** Sans stats line: 'N concepts across M islands · plasticFlowers'. */
  stats: string;
}

/** Assemble the three title-block lines drawn top-left of the plate. */
export function buildPortraitTitleBlock(args: {
  title: string;
  dateLabel: string;
  durationLabel: string;
  conceptCount: number;
  islandCount: number;
}): PortraitTitleBlock {
  const meta = [args.dateLabel, args.durationLabel]
    .filter((part) => part.length > 0)
    .join(' · ')
    .toUpperCase();
  return {
    title: args.title,
    meta,
    stats: portraitStatsLine(args.conceptCount, args.islandCount),
  };
}

/**
 * Evenly spaced gradient stops sampled from the birth-colour ramp, for the
 * legend bar. First stop is dawn, the midpoint is moss, the last is amber.
 */
export function birthRampStops(samples = 9): Array<{ offset: number; color: string }> {
  const count = Math.max(2, Math.floor(samples));
  const stops: Array<{ offset: number; color: string }> = [];
  for (let i = 0; i < count; i += 1) {
    const offset = i / (count - 1);
    stops.push({ offset, color: birthColor(offset, 0, 1) });
  }
  return stops;
}

/** Width/height of the legend gradient bar (CSS px). */
export const PORTRAIT_LEGEND_BAR_WIDTH = 150;
export const PORTRAIT_LEGEND_BAR_HEIGHT = 8;
/** Legend inset from the canvas edge (clears the inner neatline). */
export const PORTRAIT_LEGEND_INSET = NEATLINE_OUTER_INSET + NEATLINE_GAP + 16;

export interface PortraitLegendLayout {
  /** Gradient bar rectangle. */
  bar: Rect;
  /** Baseline for the '0 min' / '30+ min' tick labels (below the bar). */
  tickY: number;
  /** Baseline for the caption ('colour = when the idea appeared'), above the bar. */
  captionY: number;
  minLabel: string;
  maxLabel: string;
  caption: string;
}

/** Bottom-right legend layout: caption above, gradient bar, ticks below. */
export function portraitLegendLayout(width: number, height: number): PortraitLegendLayout {
  const rightEdge = width - PORTRAIT_LEGEND_INSET;
  const tickY = height - PORTRAIT_LEGEND_INSET;
  const barY = tickY - 12 - PORTRAIT_LEGEND_BAR_HEIGHT;
  return {
    bar: {
      x: rightEdge - PORTRAIT_LEGEND_BAR_WIDTH,
      y: barY,
      width: PORTRAIT_LEGEND_BAR_WIDTH,
      height: PORTRAIT_LEGEND_BAR_HEIGHT,
    },
    tickY,
    captionY: barY - 9,
    minLabel: '0 min',
    maxLabel: `${SESSION_HUE_SPAN_MS / 60_000}+ min`,
    caption: 'colour = when the idea appeared',
  };
}

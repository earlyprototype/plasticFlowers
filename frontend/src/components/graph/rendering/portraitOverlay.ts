import type { Core } from 'cytoscape';

import {
  CARTOGRAPHY_PALETTE,
  NEATLINE_INNER_WIDTH,
  NEATLINE_OUTER_WIDTH,
  PORTRAIT_CAPTION_FONT,
  PORTRAIT_META_FONT,
  PORTRAIT_STATS_FONT,
  PORTRAIT_TICK_FONT,
  PORTRAIT_TITLE_FONT,
  birthRampStops,
  buildPortraitTitleBlock,
  neatlineRects,
  portraitLegendLayout,
} from '../config/cartography';

/**
 * Portrait overlay — the presentation chrome of the finished map, drawn on a
 * <canvas> layered ABOVE the Cytoscape viewport (pointer-events: none) in
 * SCREEN coordinates: a double-rule neatline inset from the edges (atlas
 * plate style), a title block top-left (session title, date · duration,
 * 'N concepts across M islands · plasticFlowers') and a time-ramp legend
 * bottom-right built from the birth-colour ramp.
 *
 * The overlay is static — it redraws only on container resize or when the
 * info changes (e.g. the user edits the portrait title). All geometry/text
 * building is pure and lives in ../config/cartography.ts.
 */
export interface PortraitInfo {
  /** Plate headline (custom title or 'Session <short-id>'). */
  title: string;
  /** e.g. '10 July 2026' (session date from the earliest node birth). */
  dateLabel: string;
  /** e.g. '29 min' (earliest birth → latest birth or session end). */
  durationLabel: string;
  /** Confirmed (solid) node count. */
  conceptCount: number;
  /** Flower/island count. */
  islandCount: number;
}

export interface PortraitOverlay {
  /** Update the title-block content (schedules a redraw). */
  setInfo(info: PortraitInfo): void;
  /** Request a redraw on the next animation frame (coalesced). */
  scheduleRedraw(): void;
  /**
   * Draw the chrome into an arbitrary context at `scale` device pixels per
   * CSS pixel. Used by the portrait PNG export so the chrome is re-rendered
   * crisply at export resolution rather than upscaled from the live canvas.
   * Draws no background — the plate underneath shows through.
   */
  renderTo(ctx: CanvasRenderingContext2D, cssWidth: number, cssHeight: number, scale: number): void;
  /** Remove the Cytoscape listener and cancel any pending frame. */
  destroy(): void;
}

/** Title block origin/baselines (CSS px, inside the inner neatline). */
const TITLE_BLOCK_X = 38;
const TITLE_BASELINE_Y = 64;
const TITLE_RULE_Y = 76;
const META_BASELINE_Y = 95;
const STATS_BASELINE_Y = 112;
const TITLE_RULE_MIN_WIDTH = 160;

function drawNeatline(ctx: CanvasRenderingContext2D, width: number, height: number): void {
  const { outer, inner } = neatlineRects(width, height);
  ctx.strokeStyle = CARTOGRAPHY_PALETTE.ink;
  ctx.globalAlpha = 0.85;
  ctx.lineWidth = NEATLINE_OUTER_WIDTH;
  ctx.strokeRect(outer.x, outer.y, outer.width, outer.height);
  ctx.globalAlpha = 0.6;
  ctx.lineWidth = NEATLINE_INNER_WIDTH;
  ctx.strokeRect(inner.x, inner.y, inner.width, inner.height);
  ctx.globalAlpha = 1;
}

function drawTitleBlock(ctx: CanvasRenderingContext2D, info: PortraitInfo): void {
  const block = buildPortraitTitleBlock(info);
  ctx.fillStyle = CARTOGRAPHY_PALETTE.ink;
  ctx.textAlign = 'left';
  ctx.textBaseline = 'alphabetic';

  ctx.font = PORTRAIT_TITLE_FONT;
  ctx.fillText(block.title, TITLE_BLOCK_X, TITLE_BASELINE_Y);
  const titleWidth = ctx.measureText(block.title).width;

  // Hairline rule under the title, like a plate caption divider.
  ctx.strokeStyle = CARTOGRAPHY_PALETTE.coast;
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(TITLE_BLOCK_X, TITLE_RULE_Y);
  ctx.lineTo(TITLE_BLOCK_X + Math.max(TITLE_RULE_MIN_WIDTH, titleWidth), TITLE_RULE_Y);
  ctx.stroke();

  ctx.font = PORTRAIT_META_FONT;
  ctx.globalAlpha = 0.9;
  ctx.fillText(block.meta, TITLE_BLOCK_X, META_BASELINE_Y);

  ctx.font = PORTRAIT_STATS_FONT;
  ctx.globalAlpha = 0.8;
  ctx.fillText(block.stats, TITLE_BLOCK_X, STATS_BASELINE_Y);
  ctx.globalAlpha = 1;
}

function drawLegend(ctx: CanvasRenderingContext2D, width: number, height: number): void {
  const layout = portraitLegendLayout(width, height);
  const { bar } = layout;

  const gradient = ctx.createLinearGradient(bar.x, 0, bar.x + bar.width, 0);
  for (const stop of birthRampStops()) gradient.addColorStop(stop.offset, stop.color);
  ctx.fillStyle = gradient;
  ctx.fillRect(bar.x, bar.y, bar.width, bar.height);
  ctx.strokeStyle = CARTOGRAPHY_PALETTE.ink;
  ctx.globalAlpha = 0.5;
  ctx.lineWidth = 0.75;
  ctx.strokeRect(bar.x, bar.y, bar.width, bar.height);
  ctx.globalAlpha = 1;

  ctx.fillStyle = CARTOGRAPHY_PALETTE.ink;
  ctx.textBaseline = 'alphabetic';
  ctx.font = PORTRAIT_TICK_FONT;
  ctx.globalAlpha = 0.85;
  ctx.textAlign = 'left';
  ctx.fillText(layout.minLabel, bar.x, layout.tickY);
  ctx.textAlign = 'right';
  ctx.fillText(layout.maxLabel, bar.x + bar.width, layout.tickY);

  ctx.font = PORTRAIT_CAPTION_FONT;
  ctx.fillText(layout.caption, bar.x + bar.width, layout.captionY);
  ctx.globalAlpha = 1;
  ctx.textAlign = 'left';
}

export function createPortraitOverlay(cy: Core, canvas: HTMLCanvasElement): PortraitOverlay {
  const ctx = canvas.getContext('2d');
  let info: PortraitInfo = {
    title: '',
    dateLabel: '',
    durationLabel: '',
    conceptCount: 0,
    islandCount: 0,
  };
  let rafId: number | null = null;

  const renderTo = (
    target: CanvasRenderingContext2D,
    cssWidth: number,
    cssHeight: number,
    scale: number
  ) => {
    // All chrome is drawn in SCREEN coordinates (not model): the neatline and
    // typography must not track pan/zoom, only the plate size.
    target.setTransform(scale, 0, 0, scale, 0, 0);
    drawNeatline(target, cssWidth, cssHeight);
    drawTitleBlock(target, info);
    drawLegend(target, cssWidth, cssHeight);
    target.setTransform(1, 0, 0, 1, 0, 0);
  };

  const draw = () => {
    rafId = null;
    if (!ctx || cy.destroyed()) return;

    const container = cy.container();
    const width = container?.clientWidth ?? canvas.clientWidth;
    const height = container?.clientHeight ?? canvas.clientHeight;
    const dpr = window.devicePixelRatio || 1;
    const deviceWidth = Math.max(1, Math.round(width * dpr));
    const deviceHeight = Math.max(1, Math.round(height * dpr));
    if (canvas.width !== deviceWidth || canvas.height !== deviceHeight) {
      canvas.width = deviceWidth;
      canvas.height = deviceHeight;
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
    }

    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, deviceWidth, deviceHeight);
    renderTo(ctx, width, height, dpr);
  };

  const scheduleRedraw = () => {
    if (rafId === null && typeof requestAnimationFrame === 'function') {
      rafId = requestAnimationFrame(draw);
    }
  };

  // Chrome is screen-space and static: only a container resize (or a theme
  // change re-render, which remounts the overlay) invalidates it — pan/zoom
  // must NOT, so 'viewport' is deliberately not listened to.
  cy.on('resize', scheduleRedraw);

  return {
    setInfo(next: PortraitInfo) {
      info = next;
      scheduleRedraw();
    },
    scheduleRedraw,
    renderTo,
    destroy() {
      cy.removeListener('resize', scheduleRedraw);
      if (rafId !== null && typeof cancelAnimationFrame === 'function') {
        cancelAnimationFrame(rafId);
        rafId = null;
      }
    },
  };
}

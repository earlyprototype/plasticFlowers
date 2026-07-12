import type { Core } from 'cytoscape';

import type { Flower } from '../../../lib/types';
import {
  CARTOGRAPHY_PALETTE,
  COASTLINE_WIDTH,
  ISLAND_LABEL_FONT,
  TERRAIN_LEVELS,
  arcLabelPlacements,
  blobPath,
  centroidOf,
  hashPhase,
  islandBaseRadius,
  islandLabelRadius,
  type Point,
} from '../config/cartography';

/**
 * Terrain underlay — a <canvas> layered beneath the Cytoscape viewport that
 * draws each flower as an organic island (three contour levels + coastline)
 * plus a curved serif island name arcing above it.
 *
 * Viewport sync: all island geometry is computed in MODEL coordinates from
 * the members' rendered positions; the canvas context transform is then set
 * to `(dpr·zoom, 0, 0, dpr·zoom, dpr·pan.x, dpr·pan.y)` so the terrain
 * tracks Cytoscape pan/zoom exactly. Redraws are coalesced through
 * requestAnimationFrame: any number of 'viewport'/'position'/'layoutstop'
 * events within a frame produce a single draw.
 */
export interface TerrainUnderlay {
  /** Provide the current flower list (called on element sync). */
  setFlowers(flowers: Flower[]): void;
  /** Request a redraw on the next animation frame (coalesced). */
  scheduleRedraw(): void;
  /**
   * Draw the terrain scene (paper background + islands) into an arbitrary
   * context at `scale` device pixels per CSS pixel. Used by the portrait PNG
   * export so the composite is re-rendered crisply at export resolution
   * rather than upscaled from the live canvas.
   */
  renderTo(ctx: CanvasRenderingContext2D, cssWidth: number, cssHeight: number, scale: number): void;
  /** Remove all Cytoscape listeners and cancel any pending frame. */
  destroy(): void;
}

interface IslandGeometry {
  flower: Flower;
  centroid: Point;
  baseR: number;
  phase: number;
}

function computeIslands(cy: Core, flowers: Flower[]): IslandGeometry[] {
  const islands: IslandGeometry[] = [];
  for (const flower of flowers) {
    const memberIds = new Set(flower.member_ids);
    if (flower.stem_node_id) memberIds.add(flower.stem_node_id);

    const positions: Point[] = [];
    memberIds.forEach((id) => {
      const ele = cy.getElementById(id);
      if (ele.nonempty() && ele.isNode() && ele.style('display') !== 'none') {
        const pos = ele.position();
        positions.push({ x: pos.x, y: pos.y });
      }
    });
    if (positions.length === 0) continue;

    const centroid = centroidOf(positions);
    islands.push({
      flower,
      centroid,
      baseR: islandBaseRadius(positions, centroid),
      phase: hashPhase(flower.id),
    });
  }
  return islands;
}

function traceClosedPath(ctx: CanvasRenderingContext2D, points: Point[]): void {
  if (points.length === 0) return;
  ctx.beginPath();
  ctx.moveTo(points[0].x, points[0].y);
  for (let i = 1; i < points.length; i += 1) {
    ctx.lineTo(points[i].x, points[i].y);
  }
  ctx.closePath();
}

function drawIslandTerrain(
  ctx: CanvasRenderingContext2D,
  island: IslandGeometry,
  zoom: number
): void {
  for (const level of TERRAIN_LEVELS) {
    const outline = blobPath(island.centroid, island.baseR, island.phase, level.scale);
    traceClosedPath(ctx, outline);
    ctx.fillStyle = CARTOGRAPHY_PALETTE[level.fill];
    ctx.fill();
    if (level.coastline) {
      ctx.strokeStyle = CARTOGRAPHY_PALETTE.coast;
      // Keep the coastline a constant screen width like map linework.
      ctx.lineWidth = COASTLINE_WIDTH / zoom;
      ctx.stroke();
    }
  }
}

function drawIslandLabel(ctx: CanvasRenderingContext2D, island: IslandGeometry): void {
  const label = island.flower.label.toUpperCase();
  if (!label.trim()) return;

  ctx.font = ISLAND_LABEL_FONT;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillStyle = CARTOGRAPHY_PALETTE.ink;
  ctx.globalAlpha = CARTOGRAPHY_PALETTE.inkAlpha;

  const chars = Array.from(label);
  const charWidths = chars.map((c) => ctx.measureText(c).width);
  const radius = islandLabelRadius(island.baseR);

  for (const placement of arcLabelPlacements(label, charWidths, radius)) {
    ctx.save();
    ctx.translate(island.centroid.x + placement.x, island.centroid.y + placement.y);
    ctx.rotate(placement.rotation);
    ctx.fillText(placement.char, 0, 0);
    ctx.restore();
  }
  ctx.globalAlpha = 1;
}

export function createTerrainUnderlay(cy: Core, canvas: HTMLCanvasElement): TerrainUnderlay {
  const ctx = canvas.getContext('2d');
  let flowers: Flower[] = [];
  let rafId: number | null = null;

  /**
   * Render the full scene into `target` at `scale` device px per CSS px.
   * Shared by the live draw (scale = devicePixelRatio) and the portrait PNG
   * export (scale = export factor).
   */
  const renderTo = (
    target: CanvasRenderingContext2D,
    cssWidth: number,
    cssHeight: number,
    scale: number
  ) => {
    // Paper background in screen space.
    target.setTransform(1, 0, 0, 1, 0, 0);
    target.fillStyle = CARTOGRAPHY_PALETTE.bg;
    target.fillRect(0, 0, Math.round(cssWidth * scale), Math.round(cssHeight * scale));

    // Model → screen: apply Cytoscape's own zoom/pan (plus the scale) so
    // terrain geometry expressed in model coordinates lands exactly under
    // the nodes.
    const zoom = cy.zoom();
    const pan = cy.pan();
    target.setTransform(scale * zoom, 0, 0, scale * zoom, scale * pan.x, scale * pan.y);

    const islands = computeIslands(cy, flowers);
    // Terrain first, then all labels, so a neighbouring island never covers
    // another island's name.
    for (const island of islands) drawIslandTerrain(target, island, zoom);
    for (const island of islands) drawIslandLabel(target, island);
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

    renderTo(ctx, width, height, dpr);
  };

  const scheduleRedraw = () => {
    if (rafId === null && typeof requestAnimationFrame === 'function') {
      rafId = requestAnimationFrame(draw);
    }
  };

  // 'viewport' covers pan+zoom, 'resize' covers container size changes,
  // 'layoutstop' is layout settle, 'position' keeps islands glued to nodes
  // during drags and growth animations. All coalesce into one draw per frame.
  cy.on('viewport resize layoutstop', scheduleRedraw);
  cy.on('position', 'node', scheduleRedraw);

  return {
    setFlowers(next: Flower[]) {
      flowers = next;
      scheduleRedraw();
    },
    scheduleRedraw,
    renderTo,
    destroy() {
      cy.removeListener('viewport resize layoutstop', scheduleRedraw);
      cy.removeListener('position', 'node', scheduleRedraw);
      if (rafId !== null && typeof cancelAnimationFrame === 'function') {
        cancelAnimationFrame(rafId);
        rafId = null;
      }
    },
  };
}

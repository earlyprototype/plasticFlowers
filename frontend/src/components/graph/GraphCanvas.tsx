'use client';

import cytoscape, { Core } from 'cytoscape';
import fcose from 'cytoscape-fcose';
import { useCallback, useEffect, useMemo, useRef } from 'react';

import type { Flower, Node, Relationship } from '../../lib/types';
import type { ConnectionState } from '../../hooks/useSSE';

import { calculateLayout } from './layout/layoutEngine';
import { syncGraphStructure } from './rendering/graphRenderer';
import { createTerrainUnderlay, type TerrainUnderlay } from './rendering/terrainUnderlay';
import {
  createPortraitOverlay,
  type PortraitInfo,
  type PortraitOverlay,
} from './rendering/portraitOverlay';
import { AnimationController } from './animation/animationController';
import { applyAdaptiveStemPetalPositioning } from './layout/stemPetalPositioning';
import { LAYOUT_CONFIG, ANIMATION_CONFIG, buildStyleConfig } from './config/layoutConfig';
import {
  PORTRAIT_FIT_PADDING,
  defaultPortraitTitle,
  formatPortraitDate,
  formatSessionDuration,
  isCartographyEnabled,
} from './config/cartography';

// Register the fcose layout once at module scope (module evaluation already
// runs exactly once per bundle — a mutable guard flag was a no-op).
cytoscape.use(fcose);

// NEXT_PUBLIC_* vars are inlined at build time, so the flag is a module
// constant: it cannot change within a running bundle.
const CARTOGRAPHY_ENABLED = isCartographyEnabled();

export type GraphCanvasProps = {
  nodes: Node[];
  relationships: Relationship[];
  flowers: Flower[];
  connectionState?: ConnectionState;
  lastChunkError?: string | null;
  className?: string;
  /**
   * Portrait mode (Move 5): present the finished map as a keepable plate —
   * ghosts hidden, camera fitted to the confirmed graph, neatline + title
   * block + time legend drawn on an overlay canvas, and a 'Save portrait'
   * PNG export. Requires cartography mode (ignored when the flag is off).
   */
  portrait?: boolean;
  /** Custom plate title; falls back to 'Session <short-id>'. */
  portraitTitle?: string;
  /** Session id — used for the default title and the export filename. */
  sessionId?: string;
  /** ISO end time (if the session ended) — extends the duration line. */
  sessionEndedAt?: string | null;
};

const connectionMessages: Record<ConnectionState, string> = {
  idle: 'Idle',
  connecting: 'Connecting…',
  open: 'Live',
  reconnecting: 'Reconnecting…',
  error: 'Connection lost',
};

const statusClassMap: Partial<Record<ConnectionState, string>> = {
  open: 'graph-canvas__status--ok',
  connecting: 'graph-canvas__status--warn',
  reconnecting: 'graph-canvas__status--warn',
  error: 'graph-canvas__status--error',
};

/**
 * Capture current positions of all nodes
 */
function captureCurrentPositions(cy: Core): Map<string, { x: number; y: number }> {
  const positions = new Map<string, { x: number; y: number }>();
  cy.nodes().forEach((node) => {
    const pos = node.position();
    positions.set(node.id(), { x: pos.x, y: pos.y });
  });
  return positions;
}

export function GraphCanvas({
  nodes,
  relationships,
  flowers,
  connectionState = 'idle',
  lastChunkError,
  className,
  portrait = false,
  portraitTitle,
  sessionId,
  sessionEndedAt,
}: GraphCanvasProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const underlayCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const terrainRef = useRef<TerrainUnderlay | null>(null);
  const portraitCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const portraitOverlayRef = useRef<PortraitOverlay | null>(null);
  const portraitActiveRef = useRef(false);
  const cyRef = useRef<Core | null>(null);
  // Lazy init: `useRef(new AnimationController())` would construct (and throw
  // away) a fresh instance on every render.
  const animControllerRef = useRef<AnimationController | null>(null);
  const getAnimController = useCallback(() => {
    if (!animControllerRef.current) {
      animControllerRef.current = new AnimationController();
    }
    return animControllerRef.current;
  }, []);
  const syncDebounceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const previousFlowersRef = useRef<Flower[]>([]);
  
  // Ref to access current data in event handlers without re-creating cy instance
  const currentDataRef = useRef({ nodes, flowers });

  const statusClass = useMemo(
    () =>
      `graph-canvas__status ${statusClassMap[connectionState] ?? 'graph-canvas__status--muted'}`,
    [connectionState]
  );

  // Portrait requires cartography — with the flag off the prop is inert.
  const portraitActive = CARTOGRAPHY_ENABLED && portrait;

  // Title-block content, derived from live data: duration runs from the
  // earliest node birth to the latest (or to the session end when known).
  const portraitInfo = useMemo<PortraitInfo>(() => {
    let earliest = Number.POSITIVE_INFINITY;
    let latest = Number.NEGATIVE_INFINITY;
    for (const node of nodes) {
      const ms = Date.parse(node.created_at);
      if (!Number.isFinite(ms)) continue;
      if (ms < earliest) earliest = ms;
      if (ms > latest) latest = ms;
    }
    const endedMs = sessionEndedAt ? Date.parse(sessionEndedAt) : Number.NaN;
    if (Number.isFinite(endedMs) && endedMs > latest) latest = endedMs;
    const hasSpan = Number.isFinite(earliest) && latest >= earliest;
    return {
      title: portraitTitle?.trim() || defaultPortraitTitle(sessionId),
      dateLabel: formatPortraitDate(hasSpan ? earliest : Date.now()),
      durationLabel: hasSpan ? formatSessionDuration(latest - earliest) : '—',
      conceptCount: nodes.filter((n) => n.status === 'solid').length,
      islandCount: flowers.length,
    };
  }, [nodes, flowers, portraitTitle, sessionId, sessionEndedAt]);

  const portraitInfoRef = useRef(portraitInfo);
  useEffect(() => {
    portraitInfoRef.current = portraitInfo;
    portraitOverlayRef.current?.setInfo(portraitInfo);
  }, [portraitInfo]);

  // Keep current data ref updated for event handlers
  useEffect(() => {
    currentDataRef.current = { nodes, flowers };
  }, [nodes, flowers]);

  // Zoom and pan control handlers
  const handleFit = useCallback(() => {
    const cy = cyRef.current;
    if (!cy) return;
    cy.animate(
      {
      fit: { eles: cy.elements(), padding: 50 },
      },
      {
      duration: 1500,
      easing: 'ease-in-out',
      }
    );
  }, []);

  const handleZoomIn = useCallback(() => {
    const cy = cyRef.current;
    if (!cy) return;
    const targetZoom = cy.zoom() * 1.2;
    cy.animate(
      {
      zoom: targetZoom,
      center: { eles: cy.nodes(':selected').length ? cy.nodes(':selected') : cy.nodes() },
      },
      {
      duration: 800,
      easing: 'ease-in-out',
      }
    );
  }, []);

  const handleZoomOut = useCallback(() => {
    const cy = cyRef.current;
    if (!cy) return;
    const targetZoom = cy.zoom() * 0.8;
    cy.animate(
      {
      zoom: targetZoom,
      center: { eles: cy.nodes(':selected').length ? cy.nodes(':selected') : cy.nodes() },
      },
      {
      duration: 800,
      easing: 'ease-in-out',
      }
    );
  }, []);

  const handleReset = useCallback(() => {
    const cy = cyRef.current;
    if (!cy) return;
    cy.animate(
      {
      zoom: 1,
      center: { eles: cy.nodes() },
      },
      {
      duration: 1200,
      easing: 'ease-in-out',
      }
    );
  }, []);

  const handlePanToLatest = useCallback(() => {
    const cy = cyRef.current;
    if (!cy || nodes.length === 0) return;
    
    // Find the node with the most recent timestamp
    let latestNode = nodes[0];
    let latestTime = Math.max(...(latestNode.timestamps || [0]));
    
    for (const node of nodes) {
      const nodeTime = Math.max(...(node.timestamps || [0]));
      if (nodeTime > latestTime) {
        latestTime = nodeTime;
        latestNode = node;
      }
    }
    
    const cyNode = cy.getElementById(latestNode.id);
    if (cyNode.nonempty()) {
      cy.animate(
        {
        center: { eles: cyNode },
        zoom: 1.5,
        },
        {
        duration: 1800,
        easing: 'ease-in-out',
        }
      );
    }
  }, [nodes]);

  // Initialize Cytoscape
  useEffect(() => {
    if (!containerRef.current || cyRef.current) {
      return;
    }
    const cy = cytoscape({
      container: containerRef.current,
      style: buildStyleConfig(CARTOGRAPHY_ENABLED) as any,
      autoungrabify: false,
      boxSelectionEnabled: false,
    });
    cyRef.current = cy;

    // Terrain underlay: cartographic islands drawn beneath the (transparent)
    // Cytoscape viewport, tracking pan/zoom via the canvas transform.
    if (CARTOGRAPHY_ENABLED && underlayCanvasRef.current) {
      terrainRef.current = createTerrainUnderlay(cy, underlayCanvasRef.current);
      terrainRef.current.setFlowers(currentDataRef.current.flowers);
    }

    // Setup event delegation for flower collapse/expand
    cy.on('tap', 'node.flower', (evt) => {
      const node = evt.target;
      const isCollapsed = node.data('collapsed');
      const newState = !isCollapsed;
      node.data('collapsed', newState);
      
      // Update label with new collapse icon
      const { flowers: currentFlowers, nodes: currentNodes } = currentDataRef.current;
      const flowerId = node.id();
      const currentFlower = currentFlowers.find((f) => f.id === flowerId);
      if (currentFlower) {
        const memberCount = currentNodes.filter((n) => n.flower_id === currentFlower.id).length;
        const icon = newState ? '▶' : '▼';
        node.data('label', `${icon} ${currentFlower.label} (${memberCount})`);
      }
      
      // Toggle visibility of child nodes
      const children = node.children();
      if (newState) {
        // Collapse
        children.animate(
          {
          style: { opacity: 0 },
          },
          {
          duration: 600,
          complete: () => {
            children.style('display', 'none');
          },
          }
        );
        node.animate(
          {
          style: { 'border-width': 2, 'border-style': 'dashed' },
          },
          {
          duration: 600,
          easing: 'ease-in-out',
          }
        );
      } else {
        // Expand
        children.style('display', 'element');
        children.style('opacity', 0);
        children.animate(
          {
          style: { opacity: 1 },
          },
          {
          duration: 800,
          complete: () => {
            // Drop inline opacity so stylesheet rules (e.g. ghost 0.15) win again
            children.removeStyle('opacity');
          },
          }
        );
        node.animate(
          {
          style: { 'border-width': 1, 'border-style': 'solid' },
          },
          {
          duration: 800,
          easing: 'ease-in-out',
          }
        );
      }
    });

    // Hover styling: Cytoscape has no :hover pseudo-class, so toggle a
    // `.hovered` class (styled in layoutConfig) from mouse events.
    const handleHoverOn = (evt: cytoscape.EventObject) => {
      evt.target.addClass('hovered');
    };
    const handleHoverOff = (evt: cytoscape.EventObject) => {
      evt.target.removeClass('hovered');
    };
    cy.on('mouseover', 'node.flower', handleHoverOn);
    cy.on('mouseout', 'node.flower', handleHoverOff);
    cy.on('mouseover', 'edge', handleHoverOn);
    cy.on('mouseout', 'edge', handleHoverOff);

    const resizeObserver = new ResizeObserver(() => {
      cy.resize();
    });
    resizeObserver.observe(containerRef.current);

    // Capture the controller in effect scope so the cleanup does not read a
    // ref that may have changed by teardown time (react-hooks/exhaustive-deps).
    const controller = getAnimController();

    return () => {
      resizeObserver.disconnect();
      cy.off('mouseover', 'node.flower', handleHoverOn);
      cy.off('mouseout', 'node.flower', handleHoverOff);
      cy.off('mouseover', 'edge', handleHoverOn);
      cy.off('mouseout', 'edge', handleHoverOff);
      // Unmount: cancel verb timers and remove any mid-wilt elements
      // immediately (no deferred removal against a dying core).
      controller.stopAll(cy);
      terrainRef.current?.destroy();
      terrainRef.current = null;
      cy.destroy();
      cyRef.current = null;
    };
  }, [getAnimController]);

  // Portrait mode entry/exit. Entering hides ghosts (and any mid-wilt
  // leftovers), remembers the camera and fits it to the confirmed graph, and
  // mounts the chrome overlay. Interaction stays ON — a portrait you can
  // still explore is better; we only fit on entry. Exiting restores the
  // hidden elements and the exact previous viewport.
  useEffect(() => {
    portraitActiveRef.current = portraitActive;
    const cy = cyRef.current;
    const canvas = portraitCanvasRef.current;
    if (!portraitActive || !cy || !canvas) return;

    const overlay = createPortraitOverlay(cy, canvas);
    portraitOverlayRef.current = overlay;
    overlay.setInfo(portraitInfoRef.current);

    const previousViewport = { zoom: cy.zoom(), pan: { ...cy.pan() } };
    cy.elements('.ghost, .wilting').addClass('portrait-hidden');
    const kept = cy.elements().not('.portrait-hidden');
    if (kept.length > 0) {
      cy.animate(
        { fit: { eles: kept, padding: PORTRAIT_FIT_PADDING } },
        { duration: 700, easing: 'ease-in-out' }
      );
    }

    return () => {
      portraitActiveRef.current = false;
      overlay.destroy();
      portraitOverlayRef.current = null;
      if (!cy.destroyed()) {
        cy.elements('.portrait-hidden').removeClass('portrait-hidden');
        cy.viewport({ zoom: previousViewport.zoom, pan: previousViewport.pan });
      }
    };
  }, [portraitActive]);

  // 'Save portrait' — composite the three layers at 2x resolution into one
  // PNG: paper + terrain (re-rendered at export scale), the Cytoscape graph
  // (cy.png at the same scale, transparent bg), then the portrait chrome.
  // Each layer re-renders at export resolution, so the file is crisp rather
  // than an upscaled copy of the live canvases.
  const handleSavePortrait = useCallback(async () => {
    const cy = cyRef.current;
    const terrain = terrainRef.current;
    const overlay = portraitOverlayRef.current;
    const container = containerRef.current;
    if (!cy || !terrain || !overlay || !container) return;

    const width = container.clientWidth;
    const height = container.clientHeight;
    const scale = 2;
    const exportCanvas = document.createElement('canvas');
    exportCanvas.width = Math.round(width * scale);
    exportCanvas.height = Math.round(height * scale);
    const ctx = exportCanvas.getContext('2d');
    if (!ctx) return;

    terrain.renderTo(ctx, width, height, scale);

    const graphPng = cy.png({ scale, full: false, bg: 'transparent' });
    await new Promise<void>((resolve, reject) => {
      const img = new Image();
      img.onload = () => {
        ctx.setTransform(1, 0, 0, 1, 0, 0);
        ctx.drawImage(img, 0, 0, exportCanvas.width, exportCanvas.height);
        resolve();
      };
      img.onerror = () => reject(new Error('Portrait export: failed to rasterise the graph'));
      img.src = graphPng;
    });

    overlay.renderTo(ctx, width, height, scale);

    const stamp = sessionId?.trim()
      ? sessionId.trim().slice(0, 8)
      : new Date().toISOString().slice(0, 10);
    const link = document.createElement('a');
    link.href = exportCanvas.toDataURL('image/png');
    link.download = `plasticflowers-portrait-${stamp}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }, [sessionId]);

  // Debounced graph update with clean orchestration
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;

    // Guards against the async callback continuing to use `cy` after the
    // effect re-ran or the component unmounted (cy.destroy()).
    let cancelled = false;
    const controller = getAnimController();

    // Clear existing debounce timer
    if (syncDebounceTimerRef.current) {
      clearTimeout(syncDebounceTimerRef.current);
    }

    // Schedule update after debounce delay
    syncDebounceTimerRef.current = setTimeout(async () => {
      syncDebounceTimerRef.current = null;
      if (cancelled || cy.destroyed()) return;
      // 1. Calculate layout (pure function)
      const currentPositions = captureCurrentPositions(cy);
      const layoutResult = calculateLayout(
        currentPositions,
        { nodes, relationships, flowers },
        LAYOUT_CONFIG,
        previousFlowersRef.current
      );

      // 2. Sync graph structure (applies changes to Cytoscape). Departing
      // nodes/edges are handed to the WILT verb, which removes them from the
      // graph once the wilt completes (~900ms) — or immediately under
      // prefers-reduced-motion.
      const syncResult = syncGraphStructure(cy, { nodes, relationships, flowers }, layoutResult, {
        removeElement: (ele) => controller.wiltAndRemove(ele),
      });

      // 3. Determine if layout should run
      const shouldRunLayout = 
        syncResult.addedNodeIds.size > 0 || 
        syncResult.addedEdgeIds.size > 0 ||
        layoutResult.flowerStructureChanged;

      if (shouldRunLayout) {
        // For flower formation/dissolution, use MASSIVE repulsion to separate clusters
        const layoutConfig = layoutResult.flowerStructureChanged
          ? {
              ...LAYOUT_CONFIG,
              nodeRepulsion: 150000, // MASSIVE repulsion for flower separation (was 65000)
              idealEdgeLength: 600, // Much longer edges during flower events
              nodeSeparation: 500, // Huge separation requirement
              gravity: 0.02, // Almost no gravity = maximum spread
              tilingPaddingVertical: 600, // Enormous padding
              tilingPaddingHorizontal: 600,
              numIter: 500, // More iterations to find stable positions
            }
          : LAYOUT_CONFIG;

        // Lock strategy depends on what changed
        cy.nodes().forEach((node) => {
          const isFlower = node.hasClass('flower');
          
          if (layoutResult.flowerStructureChanged && isFlower) {
            // Flowers are unlocked to self-separate (major transformative event!)
            node.unlock();
          } else if (layoutResult.lockedNodeIds.has(node.id())) {
            // Regular nodes stay locked
            node.lock();
          }
        });

        // Run layout
        const layout = cy.elements().layout(layoutConfig as any);
        layout.run();

        // Unlock all nodes
        cy.nodes().unlock();
      }

      // 3.5. Apply stem-petal positioning within flowers
      // This positions stem nodes at center and arranges petals in circle
      // Done AFTER layout, BEFORE animations to avoid edge conflicts
      if (flowers.length > 0) {
        applyAdaptiveStemPetalPositioning(cy, flowers);
      }

      // 3.6. Element sync complete — hand the fresh flower list to the
      // terrain underlay (schedules a coalesced redraw). Position changes
      // during the upcoming animations are tracked by its own listeners.
      terrainRef.current?.setFlowers(flowers);

      // 3.7. Portrait mode: elements added/updated by this sync may include
      // new ghosts — keep them hidden while the plate is presented.
      if (portraitActiveRef.current) {
        cy.elements('.ghost, .wilting').addClass('portrait-hidden');
      }

      // 4. Execute the growth sequence (camera-first, then bloom + sprout)
      await controller.executeAnimationSequence(cy, syncResult);
      if (cancelled || cy.destroyed()) return;

      // 4.5. Repaint workaround: at low zoom Cytoscape's layered texture
      // cache can retain the mid-fade frame (edges at opacity 0), leaving
      // edges unpainted until a geometry-affecting style change. Verified
      // empirically (cytoscape 3.33): pan, zoom nudges, class toggles and
      // opacity nudges do NOT invalidate the stale layer — a width change
      // does, and the repaint persists after the width is restored.
      if (syncResult.addedEdgeIds.size > 0) {
        const edges = cy.edges();
        edges.style('width', 4);
        setTimeout(() => {
          if (!cy.destroyed()) edges.removeStyle('width');
        }, 60);
      }

      // 5. Update previous flowers for next comparison
      previousFlowersRef.current = [...flowers];
    }, ANIMATION_CONFIG.debounceMs);

    // Cleanup
    return () => {
      cancelled = true;
      if (syncDebounceTimerRef.current) {
        clearTimeout(syncDebounceTimerRef.current);
        syncDebounceTimerRef.current = null;
      }
    };
  }, [nodes, relationships, flowers, getAnimController]);

  return (
    <div className={`graph-canvas ${className ?? ''}`}>
      {portraitActive ? (
        // Portrait chrome replaces the live HUD (status badge, zoom controls,
        // ghost legend) so the plate reads clean; only the export action stays.
        <div className="graph-canvas__portrait-actions">
          <button onClick={handleSavePortrait} id="save-portrait">
            Save portrait
          </button>
        </div>
      ) : (
        <>
          <div className={statusClass}>{connectionMessages[connectionState]}</div>

          <div className="graph-canvas__controls">
            <button onClick={handleFit} title="Fit to view" aria-label="Fit to view">
              ⊡
            </button>
            <button onClick={handleZoomIn} title="Zoom in" aria-label="Zoom in">
              +
            </button>
            <button onClick={handleZoomOut} title="Zoom out" aria-label="Zoom out">
              −
            </button>
            <button onClick={handleReset} title="Reset view" aria-label="Reset view">
              ↺
            </button>
            <button
              onClick={handlePanToLatest}
              title="Pan to latest node"
              aria-label="Pan to latest node"
              disabled={nodes.length === 0}
            >
              ⟶
            </button>
          </div>

          <div className="graph-canvas__legend">
            <div className="graph-canvas__legend-item">
              <div className="graph-canvas__legend-dot graph-canvas__legend-dot--ghost" />
              <span>Ghost: unconfirmed</span>
            </div>
            <div className="graph-canvas__legend-item">
              <div className="graph-canvas__legend-dot graph-canvas__legend-dot--solid" />
              <span>Solid: confirmed</span>
            </div>
          </div>
        </>
      )}

      {lastChunkError ? (
        <div className="graph-canvas__toast" role="status">
          Chunk skipped: {lastChunkError}
        </div>
      ) : null}
      {CARTOGRAPHY_ENABLED ? (
        <canvas ref={underlayCanvasRef} className="graph-canvas__underlay" aria-hidden="true" />
      ) : null}
      <div ref={containerRef} className="graph-canvas__viewport" />
      {CARTOGRAPHY_ENABLED ? (
        <canvas
          ref={portraitCanvasRef}
          className="graph-canvas__portrait"
          aria-hidden="true"
          style={{ display: portraitActive ? 'block' : 'none' }}
        />
      ) : null}
    </div>
  );
}

export default GraphCanvas;

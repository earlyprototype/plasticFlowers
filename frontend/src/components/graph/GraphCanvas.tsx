'use client';

import cytoscape, { Core } from 'cytoscape';
import fcose from 'cytoscape-fcose';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import type { Flower, Node, Relationship } from '../../lib/types';
import type { ConnectionState } from '../../hooks/useSSE';

import { calculateLayout } from './layout/layoutEngine';
import { syncGraphStructure } from './rendering/graphRenderer';
import { createTerrainUnderlay, type TerrainUnderlay } from './rendering/terrainUnderlay';
import {
  computePortraitInfo,
  createPortraitOverlay,
  type PortraitInfo,
  type PortraitOverlay,
} from './rendering/portraitOverlay';
import { AnimationController } from './animation/animationController';
import { applyAdaptiveStemPetalPositioning } from './layout/stemPetalPositioning';
import { LAYOUT_CONFIG, ANIMATION_CONFIG, buildStyleConfig } from './config/layoutConfig';
import {
  PORTRAIT_FIT_PADDING,
  isCartographyEnabled,
  portraitExportFilename,
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
   * UNFILTERED session nodes, when `nodes` is a filtered view. Feeds the
   * portrait title block (concept count, duration) so plate stats document
   * the whole session regardless of active UI filters. Defaults to `nodes`.
   */
  allNodes?: Node[];
  /** UNFILTERED session flowers (see allNodes). Defaults to `flowers`. */
  allFlowers?: Flower[];
  /**
   * Session start (ms since epoch) — the birth-colour anchor (Move 4).
   * Supply it from the session record so node hues are independent of
   * filtering; when absent the renderer infers it from the earliest birth
   * among the nodes it is given.
   */
  sessionStartMs?: number;
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

/** Sentinel title-block content while the plate is not shown. */
const EMPTY_PORTRAIT_INFO: PortraitInfo = {
  title: '',
  dateLabel: '—',
  durationLabel: '—',
  conceptCount: 0,
  islandCount: 0,
};

export function GraphCanvas({
  nodes,
  relationships,
  flowers,
  connectionState = 'idle',
  lastChunkError,
  className,
  allNodes,
  allFlowers,
  sessionStartMs,
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
  // Whether the portrait framing has been applied to a NON-EMPTY collection.
  // Entry on an empty graph has nothing to frame; the first sync that brings
  // content then runs the portrait-framed fit once (see the sync effect).
  const portraitFitDoneRef = useRef(false);
  // Export failures surface as a toast (same pattern as the chunk-error
  // toast); cleared on the next attempt and on portrait exit.
  const [portraitError, setPortraitError] = useState<string | null>(null);
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

  // Title-block content, derived from live data. Uses the UNFILTERED lists
  // (allNodes/allFlowers) — plate stats must document the whole session, not
  // the current filter view. Skipped entirely (cheap sentinel) while the
  // plate is not shown: no reason to scan every node on each live sync.
  const portraitInfo = useMemo<PortraitInfo>(() => {
    if (!portraitActive) return EMPTY_PORTRAIT_INFO;
    return computePortraitInfo({
      nodes: allNodes ?? nodes,
      flowers: allFlowers ?? flowers,
      portraitTitle,
      sessionId,
      sessionEndedAt,
    });
  }, [portraitActive, allNodes, nodes, allFlowers, flowers, portraitTitle, sessionId, sessionEndedAt]);

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
  // leftovers), flips the controller into its calm portrait mode (no verbs,
  // no growth-camera moves — instant final states only), remembers the
  // camera and fits it to the confirmed graph, and mounts the chrome
  // overlay. Interaction stays ON — a portrait you can still explore is
  // better; we only fit on entry. Exiting restores the hidden elements and
  // the exact previous viewport.
  useEffect(() => {
    portraitActiveRef.current = portraitActive;
    const controller = getAnimController();
    // Portrait entry FIRST finalises any in-flight choreography (verbs jump
    // to their end states, verb inline styles dropped, mid-wilt elements
    // removed) — the entry fit below must frame a calm plate of full-size
    // nodes, not a mid-sprout snapshot.
    controller.setPortrait(portraitActive, cyRef.current);
    if (!portraitActive) setPortraitError(null);
    const cy = cyRef.current;
    const canvas = portraitCanvasRef.current;
    if (!portraitActive || !cy || !canvas) return;

    const overlay = createPortraitOverlay(cy, canvas);
    portraitOverlayRef.current = overlay;
    overlay.setInfo(portraitInfoRef.current);

    const previousViewport = { zoom: cy.zoom(), pan: { ...cy.pan() } };
    cy.elements('.ghost, .wilting').addClass('portrait-hidden');
    // Entry fit via the controller: it supersedes any queued growth fit and
    // honours prefers-reduced-motion (instant fit instead of a tween). On an
    // empty graph the fit no-ops; the sync effect retries it once content
    // arrives (portraitFitDoneRef).
    const kept = cy.elements().not('.portrait-hidden');
    portraitFitDoneRef.current = kept.length > 0;
    controller.startCameraFit(cy, {
      eles: kept,
      padding: PORTRAIT_FIT_PADDING,
      duration: 700,
    });

    return () => {
      portraitActiveRef.current = false;
      portraitFitDoneRef.current = false;
      controller.setPortrait(false);
      overlay.destroy();
      portraitOverlayRef.current = null;
      if (!cy.destroyed()) {
        // Halt any in-flight viewport animation (e.g. an exit within the
        // 700ms entry fit) BEFORE restoring — a live tween would otherwise
        // overwrite the restored viewport on its next frame.
        cy.stop(true);
        cy.elements('.portrait-hidden').removeClass('portrait-hidden');
        cy.viewport({ zoom: previousViewport.zoom, pan: previousViewport.pan });
      }
    };
  }, [portraitActive, getAnimController]);

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

    setPortraitError(null);
    try {
      const width = container.clientWidth;
      const height = container.clientHeight;
      const scale = 2;
      const exportCanvas = document.createElement('canvas');
      exportCanvas.width = Math.round(width * scale);
      exportCanvas.height = Math.round(height * scale);
      const ctx = exportCanvas.getContext('2d');
      if (!ctx) {
        throw new Error('could not create an export canvas context');
      }

      terrain.renderTo(ctx, width, height, scale);

      // cy.png is fine for the middle layer: it renders the graph itself
      // at export scale on a transparent background.
      const graphPng = cy.png({ scale, full: false, bg: 'transparent' });
      await new Promise<void>((resolve, reject) => {
        const img = new Image();
        img.onload = () => {
          ctx.setTransform(1, 0, 0, 1, 0, 0);
          ctx.drawImage(img, 0, 0, exportCanvas.width, exportCanvas.height);
          resolve();
        };
        img.onerror = () => reject(new Error('failed to rasterise the graph layer'));
        img.src = graphPng;
      });

      overlay.renderTo(ctx, width, height, scale);

      // toBlob + object URL instead of toDataURL: no multi-megabyte base64
      // string on the main thread, and encoding failures reject visibly.
      const blob = await new Promise<Blob>((resolve, reject) => {
        exportCanvas.toBlob(
          (result) =>
            result ? resolve(result) : reject(new Error('PNG encoding failed')),
          'image/png'
        );
      });

      const url = URL.createObjectURL(blob);
      try {
        const link = document.createElement('a');
        link.href = url;
        link.download = portraitExportFilename(sessionId);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      } finally {
        URL.revokeObjectURL(url);
      }
    } catch (err) {
      setPortraitError(err instanceof Error ? err.message : String(err));
    }
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
        sessionStartMs,
        sessionId,
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

        // Run layout. Mid-wilt elements are excluded: a departing node is
        // already off the map data-wise and must not push live nodes around
        // (or be dragged to a new position while it fades).
        const layout = cy.elements().not('.wilting').layout(layoutConfig as any);
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

        // Portrait fit retry: if the entry fit found nothing to frame (the
        // plate was entered on an empty graph), run the portrait-framed fit
        // once, on the first sync that brings content.
        if (!portraitFitDoneRef.current) {
          const kept = cy.elements().not('.portrait-hidden');
          if (kept.length > 0) {
            portraitFitDoneRef.current = true;
            controller.startCameraFit(cy, {
              eles: kept,
              padding: PORTRAIT_FIT_PADDING,
              duration: 700,
            });
          }
        }
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
  }, [nodes, relationships, flowers, sessionStartMs, sessionId, getAnimController]);

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
      {portraitError ? (
        <div className="graph-canvas__toast" role="alert">
          Save portrait failed: {portraitError}
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

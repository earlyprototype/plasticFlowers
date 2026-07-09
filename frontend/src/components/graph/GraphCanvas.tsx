'use client';

import cytoscape, { Core } from 'cytoscape';
import fcose from 'cytoscape-fcose';
import { useCallback, useEffect, useMemo, useRef } from 'react';

import type { Flower, Node, Relationship } from '../../lib/types';
import type { ConnectionState } from '../../hooks/useSSE';

import { calculateLayout } from './layout/layoutEngine';
import { syncGraphStructure } from './rendering/graphRenderer';
import { AnimationController } from './animation/animationController';
import { applyAdaptiveStemPetalPositioning } from './layout/stemPetalPositioning';
import { LAYOUT_CONFIG, ANIMATION_CONFIG, STYLE_CONFIG } from './config/layoutConfig';

// Register the fcose layout once at module scope (module evaluation already
// runs exactly once per bundle — a mutable guard flag was a no-op).
cytoscape.use(fcose);

export type GraphCanvasProps = {
  nodes: Node[];
  relationships: Relationship[];
  flowers: Flower[];
  connectionState?: ConnectionState;
  lastChunkError?: string | null;
  className?: string;
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
}: GraphCanvasProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
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
      style: STYLE_CONFIG as any,
      autoungrabify: false,
      boxSelectionEnabled: false,
    });
    cyRef.current = cy;

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
      controller.stopAllFloatAnimations(cy);
      cy.destroy();
      cyRef.current = null;
    };
  }, [getAnimController]);

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

      // 2. Sync graph structure (applies changes to Cytoscape)
      const syncResult = syncGraphStructure(cy, { nodes, relationships, flowers }, layoutResult);

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

        // Re-anchor float animations to the freshly laid-out positions so
        // floats don't fight the layout with stale captured anchors.
        controller.reanchorFloats(cy);
      }

      // 3.5. Apply stem-petal positioning within flowers
      // This positions stem nodes at center and arranges petals in circle
      // Done AFTER layout, BEFORE animations to avoid edge conflicts
      if (flowers.length > 0) {
        applyAdaptiveStemPetalPositioning(cy, flowers);
      }

      // 4. Execute animation sequence (camera-first!)
      await controller.executeAnimationSequence(cy, syncResult, layoutResult.isolatedNodeIds);
      if (cancelled || cy.destroyed()) return;

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
      
      {lastChunkError ? (
        <div className="graph-canvas__toast" role="status">
          Chunk skipped: {lastChunkError}
        </div>
      ) : null}
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
      <div ref={containerRef} className="graph-canvas__viewport" />
    </div>
  );
}

export default GraphCanvas;

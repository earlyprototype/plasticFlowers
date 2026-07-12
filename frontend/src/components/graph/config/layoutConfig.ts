/**
 * Graph Configuration - Layout, animation, and style settings
 *
 * Centralized configuration for easy tuning without code changes.
 */

import { CARTOGRAPHY_PALETTE } from './cartography';

export const LAYOUT_CONFIG = {
  name: 'fcose',
  quality: 'proof',
  animate: false, // Disable fCoSe animation - AnimationController handles it
  fit: false, // Manual camera control
  randomize: false, // Predictable layouts
  
  // EXTREME NODE SPACING - Much more aggressive
  nodeRepulsion: 200000, // EXTREME repulsion (was 80000)
  idealEdgeLength: 800, // Very long edges (was 450)
  nodeSeparation: 600, // Massive minimum distance (was 350)
  edgeElasticity: 0.2, // Very stiff edges (was 0.35)
  
  // MINIMAL GRAVITY - Let nodes spread naturally
  gravity: 0.01, // Almost zero gravity (was 0.04)
  gravityRange: 10.0, // Very large range (was 5.0)
  
  // Compound node settings (flowers) - CRITICAL FOR FLOWER SEPARATION
  nestingFactor: 0.05, // Extremely loose nesting (was 0.1)
  gravityCompound: 0.5, // Minimal compound pull (was 0.8)
  gravityRangeCompound: 5.0, // Very wide petal range (was 3.0)
  
  // COMPOUND SEPARATION - Prevent flower overlap!
  nodeRepulsionMultiplier: 3.0, // Compounds repel 3x stronger than regular nodes
  compoundSeparation: 800, // Minimum distance between flower boundaries (critical!)
  
  // MASSIVE PADDING
  tilingPaddingVertical: 800, // Enormous spacing (was 400)
  tilingPaddingHorizontal: 800, // Enormous spacing (was 400)
  
  // More iterations for stable spread
  numIter: 500, // Many iterations (was 400)
  initialEnergyOnIncremental: 0.2, // Very gentle updates (was 0.3)
} as const;

// Growth verb + camera durations live in animation/animationController.ts
// next to their implementations.
export const ANIMATION_CONFIG = {
  debounceMs: 500, // Batch SSE updates
} as const;

export const STYLE_CONFIG = [
  {
    selector: 'core',
    style: {
      'selection-box-color': '#F97316',
    },
  },
  {
    selector: 'node',
    style: {
      shape: 'roundrectangle',
      width: 'label',
      height: 'label',
      padding: '20px', // Even more padding (was 16px)
      'background-color': '#FFFFFF',
      'border-width': 2,
      'border-color': '#1A1A1A',
      'border-style': 'solid',
      label: 'data(label)',
      'text-valign': 'center',
      'text-halign': 'center',
      'font-family': 'Nunito, system-ui, sans-serif',
      'font-size': '14px', // Slightly smaller for less overlap (was 15px)
      'font-weight': 600,
      color: '#1A1A1A',
      'text-max-width': '150px', // Narrower to reduce width (was 180px)
      'text-wrap': 'ellipsis', // Truncate instead of wrap (was 'wrap')
      'text-overflow-wrap': 'anywhere',
      'min-width': '60px', // Smaller minimum (was 80px)
      'min-height': '30px', // Smaller minimum (was 35px)
      'transition-property': 'opacity, background-color, border-color, border-width',
      'transition-duration': '300ms',
      'transition-timing-function': 'ease-in-out',
    },
  },
  {
    selector: 'node.ghost',
    style: {
      opacity: 0.15, // Much more transparent (was 0.5)
      'background-color': '#F9FAFB',
      'border-color': '#E5E7EB',
      'border-style': 'dashed',
      'border-width': 1, // Thinner border
      'font-size': '11px', // Smaller text
      color: '#9CA3AF', // Greyed out text
      'z-index': 1, // Behind everything else
    },
  },
  {
    selector: 'node.solid',
    style: {
      opacity: 1,
      'border-color': '#1A1A1A',
      'border-style': 'solid',
      'border-width': 3, // Thicker border for confirmed nodes
      'background-color': '#FFFFFF',
      'font-weight': 700, // Bolder text
      'z-index': 10, // In front of ghosts
    },
  },
  {
    selector: 'node.stem',
    style: {
      'border-color': '#F97316', // Orange for stem prominence
      'border-width': 5, // Thicker border (was 4)
      'background-color': '#FFEDD5', // Warmer background
      shape: 'roundrectangle',
      padding: '18px', // Larger padding for prominence (was 14px)
      'font-size': '16px', // Larger text than regular nodes
      'font-weight': 700, // Bolder text
      'min-width': '100px', // Minimum size for stem nodes
      'min-height': '40px',
    },
  },
  {
    selector: 'node:selected',
    style: {
      'border-color': '#F97316',
      'border-width': 3,
      'background-color': '#FFF7ED',
    },
  },
  {
    selector: 'node.flower',
    style: {
      shape: 'roundrectangle',
      'background-color': '#EEF2FF', // Subtle blue tint for flowers
      'border-color': '#818CF8', // More prominent border
      'border-width': 3, // Thicker border for visibility
      'border-style': 'solid', // Solid border (not dashed) for prominence
      padding: '120px', // MASSIVE padding to claim space and prevent overlap (was 50px)
      'text-valign': 'top',
      'text-halign': 'center',
      'text-margin-y': -16, // Adjusted for larger padding
      'font-size': '18px', // Larger text (was 16px)
      'font-weight': 700,
      color: '#4338CA', // Stronger color for readability
      'text-transform': 'uppercase',
      'text-max-width': '300px', // Wider labels
      'text-wrap': 'wrap',
      'background-opacity': 0.3, // More transparent (was 0.5)
      'z-compound-depth': 'bottom',
      cursor: 'grab', // Show it's draggable
    },
  },
  {
    // Cytoscape.js has no :hover pseudo-class — GraphCanvas toggles the
    // `.hovered` class via mouseover/mouseout events.
    selector: 'node.flower.hovered',
    style: {
      'border-width': 3,
      'border-color': '#4a90e2',
    },
  },
  {
    selector: 'node.flower:active',
    style: {
      cursor: 'grabbing',
    },
  },
  {
    selector: 'edge',
    style: {
      width: 1, // Thinner lines (was 2)
      'line-color': '#D1D5DB', // Much lighter grey (was #6B7280)
      'target-arrow-color': '#D1D5DB',
      'target-arrow-shape': 'triangle',
      'arrow-scale': 0.6, // Smaller arrows (was 0.8)
      'curve-style': 'bezier',
      label: '', // Hide edge labels by default (they clutter)
      'font-size': '10px',
      'font-family': 'Nunito, system-ui, sans-serif',
      color: '#9CA3AF',
      'text-background-color': '#FFFFFF',
      'text-background-opacity': 0.9,
      'text-background-padding': '3px',
      opacity: 0.4, // Much more transparent (new)
      'transition-property': 'opacity, line-color, width',
      'transition-duration': '300ms',
      'z-index': 0, // Behind nodes
    },
  },
  {
    // See note on node.flower.hovered — hover is driven by event handlers.
    selector: 'edge.hovered',
    style: {
      width: 2,
      opacity: 1,
      'line-color': '#6B7280',
      label: 'data(description)', // Show label on hover
      'z-index': 999,
    },
  },
  {
    selector: 'edge:selected',
    style: {
      width: 3,
      opacity: 1,
      'line-color': '#F97316',
      'target-arrow-color': '#F97316',
      label: 'data(description)',
      'z-index': 999,
    },
  },
  {
    selector: 'edge.inter-flower',
    style: {
      'line-color': '#D1D5DB', // Lighter grey for inter-flower relationships
      'target-arrow-color': '#D1D5DB',
      'line-style': 'dashed', // Dashed line for visual distinction
      width: 1.5, // Slightly thinner
      opacity: 0.7, // More subtle (de-emphasise cluster connections)
    },
  },
  {
    // Portrait mode (Move 5): ghosts and mid-wilt leftovers are hidden while
    // the plate is presented; GraphCanvas toggles this class on entry/exit.
    selector: '.portrait-hidden',
    style: {
      display: 'none',
    },
  },
] as const;

/**
 * Cartography overrides — appended AFTER the base stylesheet so, at equal
 * selector specificity, they win. Typography + colour only: layout physics
 * (padding, sizing, spacing) is untouched.
 *
 * Label hierarchy:
 * - stem nodes: serif stack, 14px, weight 600 (the island's "capital city")
 * - petal/regular nodes: small sans, 11px
 * - ghost nodes: italic, faint label
 * The flower compound rectangle is muted to invisible — the terrain island
 * drawn by the underlay (see rendering/terrainUnderlay.ts) IS the group
 * visual, and its arced name replaces the compound label.
 */
// NOTE: Cytoscape's style parser rejects quoted font names ("style property
// invalid") — list multi-word families unquoted, unlike canvas ctx.font.
const CARTOGRAPHY_SERIF_STACK =
  'Iowan Old Style, Palatino Linotype, Palatino, Georgia, serif';

const CARTOGRAPHY_STYLE_OVERRIDES = [
  {
    selector: 'node',
    style: {
      'background-color': '#FBFAF2', // paper-white over the chart paper
      'border-color': '#57604F',
      'border-width': 1, // lighter linework than the legacy 2px strokes
      'font-family': 'Nunito, system-ui, sans-serif',
      'font-size': '11px',
      'font-weight': 400,
      color: CARTOGRAPHY_PALETTE.ink,
    },
  },
  {
    selector: 'node.ghost',
    style: {
      // Legacy 0.15 disappears entirely against the chart paper; keep
      // ghosts clearly fainter than solid nodes but still readable.
      // Time as colour (Move 4): the dashed border carries the birth hue at
      // reduced strength (paper-mixed by the renderer) — ghosts stay ghosts,
      // but even rumours know when they were first whispered.
      opacity: 0.45,
      'font-style': 'italic',
      'font-size': '10px',
      'text-opacity': 0.75,
      color: '#6B7263',
      'border-color': 'data(birthGhost)',
      'background-color': '#F4F3E9',
    },
  },
  {
    selector: 'node.solid',
    style: {
      // Time as colour (Move 4): fill is the birth hue mixed well toward
      // paper (data(birthFill)) so the ink label stays legible; the border
      // carries the pure birth colour — linework does the talking.
      'font-weight': 600,
      'border-color': 'data(birthColor)',
      'border-width': 1.5, // was 3 — map linework, not marker pen
      'background-color': 'data(birthFill)',
    },
  },
  {
    selector: 'node.stem',
    style: {
      // Stems keep the serif "capital city" typography; the birth colour is
      // the border accent only — label ink stays dark and readable.
      'font-family': CARTOGRAPHY_SERIF_STACK,
      'font-size': '14px',
      'font-weight': 600,
      color: '#38301F',
      'border-color': 'data(birthColor)',
      'border-width': 2, // was 5 — keep prominence without the heavy frame
      'background-color': 'data(birthFill)',
    },
  },
  {
    // The terrain island is the cluster visual now — mute the compound
    // rectangle to near-invisible (its arced island name replaces the label).
    // IMPORTANT: keep background-opacity NONZERO. With a fully transparent
    // compound (background-opacity 0) Cytoscape's initial render leaves
    // edges unpainted until the next viewport invalidation (verified
    // empirically on 3.33 — border-width alone does not help); 0.01 keeps
    // the render path healthy while compositing to <1 RGB unit on screen.
    selector: 'node.flower',
    style: {
      'text-opacity': 0,
      'background-opacity': 0.01,
      'background-color': '#D8DDC4',
      'border-width': 0.5,
      'border-opacity': 0.1,
      'border-color': '#A8B196',
    },
  },
  {
    selector: 'node.flower.hovered',
    style: {
      'border-width': 0.5,
      'border-color': '#A8B196',
    },
  },
  {
    selector: 'edge',
    style: {
      // Legacy 1px/0.4 linework disappears at fit zoom on the paper bg —
      // keep edges quiet but perceptible, like route lines on a survey map.
      'line-color': '#8F997D',
      'target-arrow-color': '#8F997D',
      width: 2,
      opacity: 0.7,
      color: '#6B7263',
      'text-background-color': CARTOGRAPHY_PALETTE.bg,
    },
  },
  {
    // Bridges between islands cross open paper — heavier + darker so the
    // route reads even at fit-all zoom (still dashed from the base style).
    selector: 'edge.inter-flower',
    style: {
      'line-color': '#828C70',
      'target-arrow-color': '#828C70',
      width: 3.5,
      opacity: 0.75,
    },
  },
] as const;

/**
 * Build the Cytoscape stylesheet. With cartography enabled the typography
 * and colour overrides are appended to the base config; otherwise the
 * stylesheet is exactly the legacy STYLE_CONFIG.
 */
export function buildStyleConfig(cartography: boolean) {
  return cartography ? [...STYLE_CONFIG, ...CARTOGRAPHY_STYLE_OVERRIDES] : [...STYLE_CONFIG];
}


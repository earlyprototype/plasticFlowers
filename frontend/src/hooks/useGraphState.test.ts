import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { Node, SSEvent } from "../lib/types";

import { applyEventToMaps, createEmptyMaps, createResyncScheduler } from "./useGraphState";

const makeNode = (overrides: Partial<Node> = {}): Node => ({
  id: "node1",
  label: "Original Label",
  confidence: 0.8,
  mentions: 1,
  timestamps: [1],
  inferred_type: "concept",
  flower_id: null,
  created_at: "2026-01-01T00:00:00Z",
  status: "ghost",
  ...overrides,
});

describe("applyEventToMaps", () => {
  it("adds nodes for node_added events", () => {
    const maps = createEmptyMaps();
    const node = makeNode();
    const next = applyEventToMaps(maps, { type: "node_added", payload: node });
    expect(next.nodes.get("node1")).toEqual(node);
  });

  it("applies node_corrected by relabeling the existing node", () => {
    const maps = createEmptyMaps();
    const node = makeNode();
    maps.nodes.set(node.id, node);

    const next = applyEventToMaps(maps, {
      type: "node_corrected",
      payload: {
        node_id: "node1",
        old_label: "Original Label",
        new_label: "Corrected Label",
        confidence: 0.95,
      },
    });

    expect(next.nodes.get("node1")?.label).toBe("Corrected Label");
    // Other fields are preserved
    expect(next.nodes.get("node1")?.status).toBe("ghost");
    // Original map untouched (immutability)
    expect(maps.nodes.get("node1")?.label).toBe("Original Label");
  });

  it("ignores node_corrected for unknown nodes", () => {
    const maps = createEmptyMaps();
    const next = applyEventToMaps(maps, {
      type: "node_corrected",
      payload: { node_id: "missing", old_label: "a", new_label: "b", confidence: 0.5 },
    });
    expect(next).toBe(maps);
  });

  it("returns the previous maps unchanged for events with a missing payload", () => {
    const maps = createEmptyMaps();
    const malformed = { type: "node_added", payload: undefined } as unknown as SSEvent;
    expect(applyEventToMaps(maps, malformed)).toBe(maps);

    const malformedRemove = { type: "node_removed" } as unknown as SSEvent;
    expect(applyEventToMaps(maps, malformedRemove)).toBe(maps);
  });

  it("removes nodes for node_removed events", () => {
    const maps = createEmptyMaps();
    maps.nodes.set("node1", makeNode());
    const next = applyEventToMaps(maps, { type: "node_removed", payload: { id: "node1" } });
    expect(next.nodes.has("node1")).toBe(false);
  });

  it("leaves the maps untouched for resync_required events (refetch handles them)", () => {
    const maps = createEmptyMaps();
    const next = applyEventToMaps(maps, {
      type: "resync_required",
      payload: { reason: "event_overflow" },
    });
    expect(next).toBe(maps);
  });
});

describe("createResyncScheduler", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("coalesces a burst of resync requests into a single refetch", () => {
    const refetch = vi.fn();
    const scheduler = createResyncScheduler(refetch, 500);

    scheduler.request();
    scheduler.request();
    scheduler.request();

    vi.advanceTimersByTime(499);
    expect(refetch).not.toHaveBeenCalled();

    vi.advanceTimersByTime(1);
    expect(refetch).toHaveBeenCalledTimes(1);

    // No trailing extra refetch from the burst
    vi.advanceTimersByTime(5000);
    expect(refetch).toHaveBeenCalledTimes(1);
  });

  it("re-arms for a fresh request after the previous refetch fired", () => {
    const refetch = vi.fn();
    const scheduler = createResyncScheduler(refetch, 500);

    scheduler.request();
    vi.advanceTimersByTime(500);
    expect(refetch).toHaveBeenCalledTimes(1);

    scheduler.request();
    vi.advanceTimersByTime(500);
    expect(refetch).toHaveBeenCalledTimes(2);
  });

  it("cancel() drops a pending refetch (unmount cleanup)", () => {
    const refetch = vi.fn();
    const scheduler = createResyncScheduler(refetch, 500);

    scheduler.request();
    scheduler.cancel();

    vi.advanceTimersByTime(5000);
    expect(refetch).not.toHaveBeenCalled();
  });
});

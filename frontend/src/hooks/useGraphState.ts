import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { getGraphState, getReferences } from "../lib/api";
import type {
  Flower,
  GraphStateResponse,
  Node,
  ReferenceNode,
  Relationship,
  SSEvent,
} from "../lib/types";

import { useSSE } from "./useSSE";

export type GraphMaps = {
  nodes: Map<string, Node>;
  relationships: Map<string, Relationship>;
  flowers: Map<string, Flower>;
  references: Map<string, ReferenceNode>;
};

export const createEmptyMaps = (): GraphMaps => ({
  nodes: new Map(),
  relationships: new Map(),
  flowers: new Map(),
  references: new Map(),
});

/**
 * Pure reducer applying a single SSE event to the graph maps.
 * Returns `prev` unchanged when the event does not affect the maps
 * (including events with a missing payload — defensive against empty SSE data).
 */
export function applyEventToMaps(prev: GraphMaps, event: SSEvent): GraphMaps {
  if ((event as { payload?: unknown }).payload == null) {
    return prev;
  }
  switch (event.type) {
    case "node_added":
    case "node_updated": {
      const nodes = new Map(prev.nodes);
      nodes.set(event.payload.id, event.payload);
      return { ...prev, nodes };
    }
    case "node_removed": {
      const nodes = new Map(prev.nodes);
      nodes.delete(event.payload.id);
      return { ...prev, nodes };
    }
    case "node_merged": {
      const nodes = new Map(prev.nodes);
      nodes.delete(event.payload.from_id);
      return { ...prev, nodes };
    }
    case "node_corrected": {
      const existing = prev.nodes.get(event.payload.node_id);
      if (!existing) return prev;
      const nodes = new Map(prev.nodes);
      nodes.set(event.payload.node_id, { ...existing, label: event.payload.new_label });
      return { ...prev, nodes };
    }
    case "relationship_added": {
      const relationships = new Map(prev.relationships);
      relationships.set(event.payload.id, event.payload);
      return { ...prev, relationships };
    }
    case "relationship_removed": {
      const relationships = new Map(prev.relationships);
      relationships.delete(event.payload.id);
      return { ...prev, relationships };
    }
    case "flower_created":
    case "flower_updated": {
      const flowers = new Map(prev.flowers);
      flowers.set(event.payload.id, event.payload);
      return { ...prev, flowers };
    }
    case "flower_dissolved": {
      const flowers = new Map(prev.flowers);
      flowers.delete(event.payload.id);
      return { ...prev, flowers };
    }
    case "reference_added": {
      const references = new Map(prev.references);
      // Key by node_id for easy lookup
      references.set(event.payload.node_id, event.payload);
      return { ...prev, references };
    }
    default:
      return prev;
  }
}

export function useGraphState(sessionId: string | null | undefined) {
  const [maps, setMaps] = useState<GraphMaps>(() => createEmptyMaps());
  const [graphError, setGraphError] = useState<string | null>(null);
  const [lastChunkError, setLastChunkError] = useState<string | null>(null);
  const warnedEmptyPayloadRef = useRef(false);

  // Activity counters
  const [builderCount, setBuilderCount] = useState(0);
  const [gardenerCount, setGardenerCount] = useState(0);
  const [researcherCount, setResearcherCount] = useState(0);

  const refreshGraph = useCallback(async () => {
    if (!sessionId) {
      setMaps(createEmptyMaps());
      setBuilderCount(0);
      setGardenerCount(0);
      setResearcherCount(0);
      return;
    }
    try {
      // Lazy load references separately (Senior Dev recommendation)
      const [fullGraph, referencesData] = await Promise.all([
        getGraphState(sessionId),
        getReferences(sessionId),
      ]);

      setMaps({
        nodes: new Map(fullGraph.nodes.map((node) => [node.id, node])),
        relationships: new Map(fullGraph.relationships.map((ratio) => [ratio.id, ratio])),
        flowers: new Map(fullGraph.flowers.map((flower) => [flower.id, flower])),
        references: new Map(referencesData.references.map((ref) => [ref.node_id, ref])),
      });

      setGraphError(null);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      setGraphError(message);
      console.warn("Failed to refresh graph state", error);
    }
  }, [sessionId]);

  useEffect(() => {
    if (!sessionId) {
      setMaps(createEmptyMaps());
      setBuilderCount(0);
      setGardenerCount(0);
      setResearcherCount(0);
      return;
    }
    void refreshGraph();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  const handleEvent = useCallback((event: SSEvent) => {
    console.log("[SSE] Received:", event.type, event.payload);
    // Defensive guard: skip malformed events with no payload rather than
    // crashing on e.g. `event.payload.id` (useSSE also filters these).
    if ((event as { payload?: unknown }).payload == null) {
      if (!warnedEmptyPayloadRef.current) {
        warnedEmptyPayloadRef.current = true;
        console.warn(`Ignoring SSE event "${event.type}" with missing payload`);
      }
      return;
    }

    // Handle counters outside the map update to keep logic clean
    if (event.type === "chunk_processed") {
      setBuilderCount((c) => c + 1);
      setLastChunkError(event.payload.error ?? null);
    } else if (event.type === "gardener_cycle") {
      setGardenerCount((c) => c + 1);
    } else if (event.type === "reference_added") {
      setResearcherCount((c) => c + 1);
    }

    setMaps((prev) => applyEventToMaps(prev, event));
  }, []);

  const { connectionState, lastError: sseError } = useSSE({
    sessionId,
    onEvent: handleEvent,
    onReconnect: refreshGraph,
  });

  const nodes = useMemo(() => Array.from(maps.nodes.values()), [maps.nodes]);
  const relationships = useMemo(
    () => Array.from(maps.relationships.values()),
    [maps.relationships],
  );
  const flowers = useMemo(() => Array.from(maps.flowers.values()), [maps.flowers]);
  const references = useMemo(() => Array.from(maps.references.values()), [maps.references]);

  return {
    nodes,
    relationships,
    flowers,
    references,
    connectionState,
    sseError,
    graphError,
    lastChunkError,
    refreshGraph,
    builderCount,
    gardenerCount,
    researcherCount,
  };
}

export type UseGraphStateReturn = ReturnType<typeof useGraphState>;

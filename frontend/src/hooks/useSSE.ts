import { useCallback, useEffect, useRef, useState } from "react";

import { getStreamUrl } from "../lib/api";
import type { SSEvent } from "../lib/types";

export type ConnectionState = "idle" | "connecting" | "open" | "reconnecting" | "error";

type UseSSEOptions = {
  sessionId: string | null | undefined;
  onEvent?: (event: SSEvent) => void;
  onReconnect?: () => Promise<void> | void;
};

const DEFAULT_RETRY_BASE_MS = 1000;
const MAX_RETRY_DELAY_MS = 30000;

const EVENT_TYPES: Array<SSEvent["type"]> = [
  "node_added",
  "node_updated",
  "node_removed",
  "node_merged",
  "relationship_added",
  "relationship_removed",
  "flower_created",
  "flower_updated",
  "flower_dissolved",
  "chunk_processed",
  "gardener_cycle",
  "gardener_cycle",
  "heartbeat",
  "reference_added",
];

const WATCHDOG_TIMEOUT_MS = 45000;

export const computeBackoffDelay = (attempt: number): number => {
  const safeAttempt = Math.max(0, attempt);
  const delay = DEFAULT_RETRY_BASE_MS * 2 ** safeAttempt;
  return Math.min(MAX_RETRY_DELAY_MS, delay);
};

export function useSSE({ sessionId, onEvent, onReconnect }: UseSSEOptions) {
  const [connectionState, setConnectionState] = useState<ConnectionState>("idle");
  const [lastError, setLastError] = useState<string | null>(null);
  const isFirstConnectionRef = useRef(true);
  const onEventRef = useRef(onEvent);
  const onReconnectRef = useRef(onReconnect);

  // Keep refs up to date
  useEffect(() => {
    onEventRef.current = onEvent;
    onReconnectRef.current = onReconnect;
  }, [onEvent, onReconnect]);

  const handleEvent = useCallback(
    (type: SSEvent["type"], data: string) => {
      if (!onEventRef.current) return;
      try {
        const payload = data ? (JSON.parse(data) as SSEvent["payload"]) : undefined;
        onEventRef.current({ type, payload } as SSEvent);
      } catch (error) {
        console.warn("Failed to parse SSE payload", error);
      }
    },
    [],
  );

  useEffect(() => {
    if (!sessionId || typeof window === "undefined") {
      setConnectionState("idle");
      return;
    }

    let eventSource: EventSource | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let watchdogTimer: ReturnType<typeof setTimeout> | null = null;
    let reconnectAttempts = 0;
    let isMounted = true;

    const clearReconnectTimer = () => {
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
      }
    };

    const clearWatchdog = () => {
      if (watchdogTimer) {
        clearTimeout(watchdogTimer);
        watchdogTimer = null;
      }
    };

    const cleanup = () => {
      clearReconnectTimer();
      clearWatchdog();
      if (eventSource) {
        eventSource.close();
        eventSource = null;
      }
    };

    const scheduleReconnect = () => {
      if (!isMounted) return;
      cleanup(); // Force close existing connection
      clearReconnectTimer();
      const delay = computeBackoffDelay(reconnectAttempts);
      reconnectAttempts += 1;
      reconnectTimer = setTimeout(() => {
        reconnectTimer = null;
        connect();
      }, delay);
    };

    const resetWatchdog = () => {
      clearWatchdog();
      watchdogTimer = setTimeout(() => {
        if (!isMounted) return;
        console.warn("SSE Watchdog timeout: no events received");
        scheduleReconnect();
      }, WATCHDOG_TIMEOUT_MS);
    };

    const connect = () => {
      try {
        cleanup();
        setConnectionState("connecting"); // Always connecting for a new/changed session URL
        setLastError(null);
        eventSource = new EventSource(getStreamUrl(sessionId));
        console.log("[useSSE] EventSource created:", eventSource, "URL:", getStreamUrl(sessionId));

        if (!eventSource) {
          console.error("[useSSE] EventSource is null after creation!");
          return;
        }

        EVENT_TYPES.forEach((eventType) => {
          console.log("[useSSE] Registering listener for:", eventType);
          eventSource!.addEventListener(eventType, (event) => {
            console.log("[useSSE] Event listener fired:", eventType, event);
            resetWatchdog(); // Reset timer on any valid event
            if (eventType !== "heartbeat") {
              handleEvent(eventType, (event as MessageEvent).data ?? "");
            }
          });
        });
        console.log("[useSSE] All", EVENT_TYPES.length, "event listeners registered");

        eventSource.onopen = async () => {
          if (!isMounted) return;
          setConnectionState("open");
          reconnectAttempts = 0;
          resetWatchdog(); // Start the timer once connected
          const wasReconnecting = !isFirstConnectionRef.current;
          isFirstConnectionRef.current = false;
          if (wasReconnecting && onReconnectRef.current) {
            try {
              await onReconnectRef.current();
            } catch (error) {
              console.warn("Graph refresh after reconnect failed", error);
              setLastError(error instanceof Error ? error.message : String(error));
            }
          }
        };

        eventSource.onerror = () => {
          if (!isMounted) return;
          setConnectionState("error");
          setLastError("SSE connection error");
          scheduleReconnect();
        };
      } catch (error) {
        setLastError(error instanceof Error ? error.message : String(error));
        scheduleReconnect();
      }
    };

    connect();

    return () => {
      isMounted = false;
      cleanup();
    };
  }, [sessionId]);

  return { connectionState, lastError };
}

export type UseSSEReturn = ReturnType<typeof useSSE>;


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

// One entry per SSE event name — duplicates would register duplicate listeners
// and double-deliver every occurrence of that event (see useSSE.test.ts).
export const EVENT_TYPES: ReadonlyArray<SSEvent["type"]> = [
  "node_added",
  "node_updated",
  "node_removed",
  "node_merged",
  "node_corrected",
  "relationship_added",
  "relationship_removed",
  "flower_created",
  "flower_updated",
  "flower_dissolved",
  "chunk_processed",
  "gardener_cycle",
  "heartbeat",
  "reference_added",
  "resync_required",
];

const WATCHDOG_TIMEOUT_MS = 45000;

export const computeBackoffDelay = (attempt: number): number => {
  const safeAttempt = Math.max(0, attempt);
  const delay = DEFAULT_RETRY_BASE_MS * 2 ** safeAttempt;
  return Math.min(MAX_RETRY_DELAY_MS, delay);
};

/**
 * Minimal structural type for EventSource so the connection manager can be
 * driven by a fake implementation in tests (vitest runs without jsdom).
 */
export type EventSourceLike = {
  addEventListener: (type: string, listener: (event: MessageEvent) => void) => void;
  close: () => void;
  onopen: ((event: Event) => void) | null;
  onerror: ((event: Event) => void) | null;
};

export type SSEConnectionOptions = {
  url: string;
  eventTypes?: ReadonlyArray<string>;
  onEvent: (type: string, data: string) => void;
  onStateChange?: (state: ConnectionState) => void;
  onError?: (message: string) => void;
  /** Invoked when the stream re-opens after having been open before (i.e. a successful reconnect). */
  onReconnected?: () => void;
  createEventSource?: (url: string) => EventSourceLike;
  watchdogTimeoutMs?: number;
};

/**
 * Framework-free SSE connection manager with exponential-backoff reconnects.
 *
 * State transitions: connecting -> open, and on error/watchdog timeout:
 * -> reconnecting (while the backoff timer runs) -> connecting -> open.
 */
export function createSSEConnection(options: SSEConnectionOptions): {
  start: () => void;
  stop: () => void;
} {
  const {
    url,
    eventTypes = EVENT_TYPES,
    onEvent,
    onStateChange,
    onError,
    onReconnected,
    createEventSource = (target: string) => new EventSource(target) as EventSourceLike,
    watchdogTimeoutMs = WATCHDOG_TIMEOUT_MS,
  } = options;

  let eventSource: EventSourceLike | null = null;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  let watchdogTimer: ReturnType<typeof setTimeout> | null = null;
  let reconnectAttempts = 0;
  let hasOpenedOnce = false;
  let stopped = false;

  const setState = (state: ConnectionState) => {
    if (!stopped) onStateChange?.(state);
  };

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

  const closeSource = () => {
    if (eventSource) {
      eventSource.close();
      eventSource = null;
    }
  };

  const scheduleReconnect = () => {
    if (stopped) return;
    closeSource();
    clearWatchdog();
    clearReconnectTimer();
    setState("reconnecting");
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
      if (stopped) return;
      console.warn("SSE Watchdog timeout: no events received");
      scheduleReconnect();
    }, watchdogTimeoutMs);
  };

  const connect = () => {
    if (stopped) return;
    try {
      closeSource();
      setState("connecting");
      const source = createEventSource(url);
      eventSource = source;

      eventTypes.forEach((eventType) => {
        source.addEventListener(eventType, (event) => {
          resetWatchdog(); // Reset timer on any valid event
          if (eventType !== "heartbeat") {
            onEvent(eventType, (event as MessageEvent).data ?? "");
          }
        });
      });

      source.onopen = () => {
        if (stopped) return;
        setState("open");
        reconnectAttempts = 0;
        resetWatchdog(); // Start the timer once connected
        const wasReconnect = hasOpenedOnce;
        hasOpenedOnce = true;
        if (wasReconnect) {
          onReconnected?.();
        }
      };

      source.onerror = () => {
        if (stopped) return;
        onError?.("SSE connection error");
        scheduleReconnect();
      };
    } catch (error) {
      onError?.(error instanceof Error ? error.message : String(error));
      scheduleReconnect();
    }
  };

  return {
    start: () => {
      connect();
    },
    stop: () => {
      stopped = true;
      clearReconnectTimer();
      clearWatchdog();
      closeSource();
    },
  };
}

export function useSSE({ sessionId, onEvent, onReconnect }: UseSSEOptions) {
  const [connectionState, setConnectionState] = useState<ConnectionState>("idle");
  const [lastError, setLastError] = useState<string | null>(null);
  const onEventRef = useRef(onEvent);
  const onReconnectRef = useRef(onReconnect);
  const warnedEmptyPayloadRef = useRef(false);

  // Keep refs up to date
  useEffect(() => {
    onEventRef.current = onEvent;
    onReconnectRef.current = onReconnect;
  }, [onEvent, onReconnect]);

  const handleEvent = useCallback((type: SSEvent["type"], data: string) => {
    if (!onEventRef.current) return;
    try {
      const payload = data ? (JSON.parse(data) as SSEvent["payload"]) : undefined;
      if (payload == null) {
        // Single runtime guard at the SSE boundary: events with empty/undefined
        // payloads never reach consumers, so downstream handlers can rely on
        // `event.payload` being present (no per-consumer re-checks).
        if (!warnedEmptyPayloadRef.current) {
          warnedEmptyPayloadRef.current = true;
          console.warn(`SSE event "${type}" arrived with an empty payload; skipping`);
        }
        return;
      }
      onEventRef.current({ type, payload } as SSEvent);
    } catch (error) {
      console.warn("Failed to parse SSE payload", error);
    }
  }, []);

  useEffect(() => {
    if (!sessionId || typeof window === "undefined") {
      setConnectionState("idle");
      return;
    }

    const connection = createSSEConnection({
      url: getStreamUrl(sessionId),
      onEvent: (type, data) => handleEvent(type as SSEvent["type"], data),
      onStateChange: (state) => {
        setConnectionState(state);
        if (state === "connecting" || state === "open") {
          setLastError(null);
        }
      },
      onError: (message) => setLastError(message),
      onReconnected: () => {
        void (async () => {
          if (!onReconnectRef.current) return;
          try {
            await onReconnectRef.current();
          } catch (error) {
            console.warn("Graph refresh after reconnect failed", error);
            setLastError(error instanceof Error ? error.message : String(error));
          }
        })();
      },
    });

    connection.start();
    return () => connection.stop();
  }, [sessionId, handleEvent]);

  return { connectionState, lastError };
}

export type UseSSEReturn = ReturnType<typeof useSSE>;

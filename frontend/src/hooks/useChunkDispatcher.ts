import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { submitChunk } from "../lib/api";
import type { ChunkSubmissionRequest } from "../lib/types";

const SENTENCE_REGEX = /[.!?]+/g;

export type UseChunkDispatcherOptions = {
  sessionId?: string | null;
  minSentences?: number;
  maxDelayMs?: number;
  /** How often the stale-buffer timer checks whether buffered text should flush. */
  staleCheckIntervalMs?: number;
  /** Injectable clock returning seconds (used for chunk start/end timestamps and staleness). */
  clock?: () => number;
};

const DEFAULT_MIN_SENTENCES = 3;
const DEFAULT_MAX_DELAY_MS = 15000;
const DEFAULT_STALE_CHECK_INTERVAL_MS = 1000;
const MAX_BUFFER_CHARS = 1000;

export type ChunkBufferOptions = {
  minSentences?: number;
  maxDelayMs?: number;
  maxBufferChars?: number;
  /** Seconds clock for chunk start/end timestamps (test injection point). */
  clock?: () => number;
  /** Milliseconds clock for staleness checks; derived from `clock` when provided. */
  nowMs?: () => number;
};

/**
 * Framework-free chunk buffer.
 *
 * Accumulates transcript fragments and decides when they should be dispatched:
 * - `shouldDispatch()` — sentence/char thresholds reached, or
 * - `isStale()` — buffered text has waited longer than `maxDelayMs`
 *   (covers unpunctuated Web Speech transcripts that never trip the sentence gate).
 */
export function createChunkBuffer(options: ChunkBufferOptions = {}) {
  const {
    minSentences = DEFAULT_MIN_SENTENCES,
    maxDelayMs = DEFAULT_MAX_DELAY_MS,
    maxBufferChars = MAX_BUFFER_CHARS,
    clock,
    nowMs = clock ? () => clock() * 1000 : () => performance.now(),
  } = options;

  let parts: string[] = [];
  let sentences = 0;
  let startTimestamp = getTimestamp(clock);
  let bufferStartedAtMs: number | null = null;

  const reset = () => {
    parts = [];
    sentences = 0;
    startTimestamp = getTimestamp(clock);
    bufferStartedAtMs = null;
  };

  return {
    append(text: string): void {
      const trimmed = text.trim();
      if (!trimmed) return;
      if (parts.length === 0) {
        startTimestamp = getTimestamp(clock);
        bufferStartedAtMs = nowMs();
      }
      parts.push(trimmed);
      sentences += countSentences(trimmed);
    },
    shouldDispatch(): boolean {
      if (parts.length === 0) return false;
      const totalChars = parts.reduce((sum, str) => sum + str.length, 0);
      return sentences >= minSentences || totalChars >= maxBufferChars;
    },
    isStale(): boolean {
      return (
        parts.length > 0 &&
        bufferStartedAtMs !== null &&
        nowMs() - bufferStartedAtMs >= maxDelayMs
      );
    },
    /** Drain the buffer into a submission payload; null when empty. */
    takeChunk(): ChunkSubmissionRequest | null {
      if (parts.length === 0) return null;
      const payload: ChunkSubmissionRequest = {
        text: parts.join(" ").trim(),
        start_time: startTimestamp,
        end_time: getTimestamp(clock),
      };
      // Reset IMMEDIATELY so new input can accumulate while the network call runs
      reset();
      return payload;
    },
    reset,
    get pendingText(): string {
      return parts.join(" ");
    },
    get pendingSentences(): number {
      return sentences;
    },
  };
}

export type ChunkBuffer = ReturnType<typeof createChunkBuffer>;

/**
 * Interval timer that flushes a stale non-empty buffer.
 * Returns a stop function that clears the interval (call on unmount).
 */
export function startStaleFlushTimer(
  buffer: Pick<ChunkBuffer, "isStale">,
  flush: () => void,
  intervalMs: number,
): () => void {
  const intervalId = setInterval(() => {
    if (buffer.isStale()) {
      flush();
    }
  }, intervalMs);
  return () => clearInterval(intervalId);
}

export function useChunkDispatcher(options: UseChunkDispatcherOptions = {}) {
  const {
    sessionId,
    minSentences = DEFAULT_MIN_SENTENCES,
    maxDelayMs = DEFAULT_MAX_DELAY_MS,
    staleCheckIntervalMs = DEFAULT_STALE_CHECK_INTERVAL_MS,
    clock,
  } = options;
  const [isDispatching, setIsDispatching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Lazily create the buffer once; thresholds/clock are fixed for the hook's lifetime.
  const bufferRef = useRef<ChunkBuffer | null>(null);
  if (bufferRef.current === null) {
    bufferRef.current = createChunkBuffer({ minSentences, maxDelayMs, clock });
  }
  const buffer = bufferRef.current;

  const sessionIdRef = useRef(sessionId);
  useEffect(() => {
    sessionIdRef.current = sessionId;
  }, [sessionId]);

  const dispatchChunk = useCallback(async () => {
    const targetSessionId = sessionIdRef.current;
    if (!targetSessionId) return;
    const payload = buffer.takeChunk();
    if (!payload) return;

    setIsDispatching(true);
    setError(null);
    try {
      await submitChunk(targetSessionId, payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      // Note: We do not restore the buffer on error to avoid ordering/duplication issues
      // with new live input that may have arrived.
    } finally {
      setIsDispatching(false);
    }
  }, [buffer]);

  const append = useCallback(
    async (text: string, isFinal: boolean) => {
      if (!text.trim()) return;
      buffer.append(text);
      if (isFinal && (buffer.shouldDispatch() || buffer.isStale())) {
        await dispatchChunk();
      }
    },
    [buffer, dispatchChunk],
  );

  // Real timer flushing stale buffers — without it, the session's final
  // utterance could sit in the buffer forever (staleness was previously only
  // evaluated on the next append).
  useEffect(() => {
    if (!sessionId) return;
    return startStaleFlushTimer(buffer, () => void dispatchChunk(), staleCheckIntervalMs);
  }, [sessionId, buffer, dispatchChunk, staleCheckIntervalMs]);

  const resetBuffer = useCallback(() => {
    buffer.reset();
  }, [buffer]);

  return useMemo(
    () => ({
      append,
      dispatchNow: dispatchChunk,
      reset: resetBuffer,
      isDispatching,
      error,
      pendingText: buffer.pendingText,
      pendingSentences: buffer.pendingSentences,
    }),
    [append, dispatchChunk, resetBuffer, isDispatching, error, buffer],
  );
}

function countSentences(text: string): number {
  const matches = text.match(SENTENCE_REGEX);
  return matches ? matches.length : 0;
}

function getTimestamp(clock?: () => number): number {
  return clock ? clock() : performance.now() / 1000;
}

export type UseChunkDispatcherReturn = ReturnType<typeof useChunkDispatcher>;

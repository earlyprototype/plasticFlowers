import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { submitChunk } from "../lib/api";
import type { ChunkSubmissionRequest } from "../lib/types";

const SENTENCE_REGEX = /[.!?]+/g;

export type UseChunkDispatcherOptions = {
  sessionId?: string | null;
  minSentences?: number;
  maxDelayMs?: number;
  /** Injectable clock returning seconds (used for chunk start/end timestamps and staleness). */
  clock?: () => number;
};

const DEFAULT_MIN_SENTENCES = 3;
const DEFAULT_MAX_DELAY_MS = 15000;
const MAX_BUFFER_CHARS = 1000;

export type ChunkBufferOptions = {
  minSentences?: number;
  maxDelayMs?: number;
  maxBufferChars?: number;
  /**
   * Injectable clock returning seconds — the single time source for chunk
   * start/end timestamps and staleness (milliseconds derived internally).
   */
  clock?: () => number;
  /**
   * Stale-flush deadline: invoked once, `maxDelayMs` after the buffer
   * transitions empty -> non-empty. Cleared by `takeChunk()`/`reset()`/
   * `dispose()`; re-armed on the next append into an empty buffer. Without it,
   * a session's final unpunctuated utterance could sit in the buffer forever.
   */
  onDeadline?: () => void;
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
    onDeadline,
  } = options;

  const nowMs = clock ? () => clock() * 1000 : () => performance.now();

  let parts: string[] = [];
  let sentences = 0;
  let startTimestamp = getTimestamp(clock);
  let bufferStartedAtMs: number | null = null;
  let deadlineTimer: ReturnType<typeof setTimeout> | null = null;

  const clearDeadline = () => {
    if (deadlineTimer !== null) {
      clearTimeout(deadlineTimer);
      deadlineTimer = null;
    }
  };

  const armDeadline = () => {
    if (!onDeadline) return;
    clearDeadline();
    deadlineTimer = setTimeout(() => {
      deadlineTimer = null;
      onDeadline();
    }, maxDelayMs);
  };

  const reset = () => {
    parts = [];
    sentences = 0;
    startTimestamp = getTimestamp(clock);
    bufferStartedAtMs = null;
    clearDeadline();
  };

  return {
    append(text: string): void {
      const trimmed = text.trim();
      if (!trimmed) return;
      if (parts.length === 0) {
        startTimestamp = getTimestamp(clock);
        bufferStartedAtMs = nowMs();
        armDeadline();
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
    /** Clear a pending stale-flush deadline without touching the buffer (unmount cleanup). */
    dispose(): void {
      clearDeadline();
    },
    get pendingText(): string {
      return parts.join(" ");
    },
    get pendingSentences(): number {
      return sentences;
    },
  };
}

export type ChunkBuffer = ReturnType<typeof createChunkBuffer>;

export function useChunkDispatcher(options: UseChunkDispatcherOptions = {}) {
  const {
    sessionId,
    minSentences = DEFAULT_MIN_SENTENCES,
    maxDelayMs = DEFAULT_MAX_DELAY_MS,
    clock,
  } = options;
  const [isDispatching, setIsDispatching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // The buffer's stale-flush deadline calls the latest dispatch function via a ref
  // (the buffer is created once, before dispatchChunk exists).
  const deadlineFlushRef = useRef<() => void>(() => {});

  // Lazily create the buffer once; thresholds/clock are fixed for the hook's lifetime.
  const bufferRef = useRef<ChunkBuffer | null>(null);
  if (bufferRef.current === null) {
    bufferRef.current = createChunkBuffer({
      minSentences,
      maxDelayMs,
      clock,
      onDeadline: () => deadlineFlushRef.current(),
    });
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

  useEffect(() => {
    deadlineFlushRef.current = () => void dispatchChunk();
  }, [dispatchChunk]);

  // Clear any pending stale-flush deadline when the component unmounts.
  useEffect(() => () => buffer.dispose(), [buffer]);

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

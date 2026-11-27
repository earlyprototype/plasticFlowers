import { useEffect, useMemo, useReducer, useState } from "react";

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

type DispatcherOptions = Omit<UseChunkDispatcherOptions, "sessionId"> & {
  submit?: (sessionId: string, payload: ChunkSubmissionRequest) => Promise<unknown>;
  onChange?: () => void;
};

type SessionQueue = {
  pending: ChunkSubmissionRequest[];
  inFlight: Promise<void> | null;
  error: string | null;
};

export function createChunkDispatcher({ submit = submitChunk, onChange, ...options }: DispatcherOptions = {}) {
  const queues = new Map<string, SessionQueue>();

  function deliver(sessionId: string, queue: SessionQueue): Promise<void> {
    if (queue.inFlight) return queue.inFlight;
    if (queue.error !== null) return Promise.resolve();
    queue.inFlight = Promise.resolve().then(async () => {
      try {
        while (queue.pending.length > 0) {
          await submit(sessionId, queue.pending[0]);
          queue.pending.shift();
        }
      } catch (err) {
        queue.error = err instanceof Error ? err.message : String(err);
      } finally {
        queue.inFlight = null;
        if (queue.pending.length === 0) queues.delete(sessionId);
        onChange?.();
      }
    });
    onChange?.();
    return queue.inFlight;
  }

  return {
    forSession(sessionId: string | null | undefined) {
      const buffer = createChunkBuffer({ ...options, onDeadline: () => void dispatchNow() });

      function dispatchNow(): Promise<void> {
        if (!sessionId) return Promise.resolve();
        const chunk = buffer.takeChunk();
        if (!chunk) return Promise.resolve();
        const queue: SessionQueue = queues.get(sessionId) ?? { pending: [], inFlight: null, error: null };
        queues.set(sessionId, queue);
        queue.pending.push({ ...chunk, client_request_id: crypto.randomUUID() });
        onChange?.();
        return deliver(sessionId, queue);
      }

      return {
        buffer,
        append(text: string, isFinal: boolean): Promise<void> {
          if (!sessionId || !text.trim()) return Promise.resolve();
          buffer.append(text);
          if (isFinal && (buffer.shouldDispatch() || buffer.isStale())) return dispatchNow();
          onChange?.();
          return Promise.resolve();
        },
        dispatchNow,
        reset() {
          buffer.reset();
          onChange?.();
        },
      };
    },
    retry(sessionId: string) {
      const queue = queues.get(sessionId);
      if (!queue) return Promise.resolve();
      queue.error = null;
      return deliver(sessionId, queue);
    },
    get isDispatching() {
      return Array.from(queues.values()).some((queue) => queue.inFlight !== null);
    },
    get failures() {
      return Array.from(queues).flatMap(([sessionId, { error }]) =>
        error === null ? [] : [{ sessionId, error }],
      );
    },
  };
}

export function useChunkDispatcher({ sessionId, minSentences, maxDelayMs, clock }: UseChunkDispatcherOptions = {}) {
  const [, onChange] = useReducer((revision: number) => revision + 1, 0);
  const [dispatcher] = useState(() => createChunkDispatcher({ minSentences, maxDelayMs, clock, onChange }));
  const session = useMemo(() => dispatcher.forSession(sessionId), [dispatcher, sessionId]);

  useEffect(() => () => { void session.dispatchNow(); }, [session]);

  const failures = dispatcher.failures;
  return {
    append: session.append,
    dispatchNow: session.dispatchNow,
    reset: session.reset,
    retry: dispatcher.retry,
    isDispatching: dispatcher.isDispatching,
    error: failures[0]?.error ?? null,
    failures,
    pendingText: session.buffer.pendingText,
    pendingSentences: session.buffer.pendingSentences,
  };
}

function countSentences(text: string): number {
  const matches = text.match(SENTENCE_REGEX);
  return matches ? matches.length : 0;
}

function getTimestamp(clock?: () => number): number {
  return clock ? clock() : performance.now() / 1000;
}

export type UseChunkDispatcherReturn = ReturnType<typeof useChunkDispatcher>;

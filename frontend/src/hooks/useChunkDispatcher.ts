import { useCallback, useMemo, useRef, useState } from "react";

import { submitChunk } from "../lib/api";
import type { ChunkSubmissionRequest } from "../lib/types";

const SENTENCE_REGEX = /[.!?]+/g;

export type UseChunkDispatcherOptions = {
  sessionId?: string | null;
  minSentences?: number;
  maxDelayMs?: number;
  clock?: () => number;
};

const DEFAULT_MIN_SENTENCES = 3;
const DEFAULT_MAX_DELAY_MS = 15000;
const MAX_BUFFER_CHARS = 1000;

export function useChunkDispatcher(options: UseChunkDispatcherOptions = {}) {
  const { sessionId, minSentences = DEFAULT_MIN_SENTENCES, maxDelayMs = DEFAULT_MAX_DELAY_MS, clock } =
    options;
  const [isDispatching, setIsDispatching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bufferRef = useRef<string[]>([]);
  const sentencesRef = useRef(0);
  const startTimestampRef = useRef<number>(getTimestamp(clock));
  const lastDispatchRef = useRef<number>(getTimestamp(clock) * 1000);

  const resetBuffer = useCallback(() => {
    bufferRef.current = [];
    sentencesRef.current = 0;
    startTimestampRef.current = getTimestamp(clock);
  }, [clock]);

  const flushIfStale = useCallback(async () => {
    if (!sessionId || bufferRef.current.length === 0) return;
    const nowMs = performance.now();
    if (nowMs - lastDispatchRef.current > maxDelayMs) {
      await dispatchChunk();
    }
  }, [sessionId, maxDelayMs]);

  const dispatchChunk = useCallback(async () => {
    if (!sessionId || bufferRef.current.length === 0) return;
    setIsDispatching(true);
    setError(null);
    
    // Capture snapshot of current buffer
    const text = bufferRef.current.join(" ").trim();
    const endTime = getTimestamp(clock);
    const payload: ChunkSubmissionRequest = {
      text,
      start_time: startTimestampRef.current,
      end_time: endTime,
    };

    // Reset buffer IMMEDIATELY so new input can accumulate while we wait for network
    resetBuffer();

    try {
      await submitChunk(sessionId, payload);
      lastDispatchRef.current = performance.now();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      // Note: We do not restore the buffer on error to avoid ordering/duplication issues
      // with new live input that may have arrived.
    } finally {
      setIsDispatching(false);
    }
  }, [sessionId, clock, resetBuffer]);

  const append = useCallback(
    async (text: string, isFinal: boolean) => {
      if (!text.trim()) return;
      bufferRef.current.push(text.trim());
      sentencesRef.current += countSentences(text);
      
      const totalChars = bufferRef.current.reduce((sum, str) => sum + str.length, 0);

      if (isFinal && (sentencesRef.current >= minSentences || totalChars >= MAX_BUFFER_CHARS)) {
        await dispatchChunk();
      } else if (isFinal) {
        await flushIfStale();
      }
    },
    [minSentences, dispatchChunk, flushIfStale],
  );

  return useMemo(
    () => ({
      append,
      dispatchNow: dispatchChunk,
      reset: resetBuffer,
      isDispatching,
      error,
      pendingText: bufferRef.current.join(" "),
      pendingSentences: sentencesRef.current,
    }),
    [append, dispatchChunk, resetBuffer, isDispatching, error],
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


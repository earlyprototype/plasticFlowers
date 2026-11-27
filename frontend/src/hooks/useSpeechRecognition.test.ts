import { afterEach, expect, it, vi } from "vitest";

import type { ChunkSubmissionRequest } from "../lib/types";
import { createChunkDispatcher } from "./useChunkDispatcher";
import { createSpeechRecorder } from "./useSpeechRecognition";

afterEach(() => vi.useRealTimers());

it("finishes the old recognizer in its own session before continuing a live microphone", async () => {
  vi.useFakeTimers();
  const recognizers: SpeechRecognition[] = [];
  const recorder = createSpeechRecorder({
    createRecognition() {
      const recognition = { start: vi.fn(), stop: vi.fn() } as unknown as SpeechRecognition;
      recognizers.push(recognition);
      return recognition;
    },
    onState: vi.fn(), onError: vi.fn(), onInterim: vi.fn(),
  });
  const submit = vi.fn(async (_session: string, _payload: ChunkSubmissionRequest) => {});
  const dispatcher = createChunkDispatcher({ submit });
  function target(sessionId: string) {
    const session = dispatcher.forSession(sessionId);
    return { sessionId, onTranscript: session.append, onEnd: session.dispatchNow };
  }
  const result = (text: string) => ({
    results: [[{ transcript: text }]],
  } as unknown as SpeechRecognitionEvent);
  recorder.setTarget(target("A"));
  recorder.start();
  const old = recognizers[0];
  old.onresult!(result("alpha"));
  recorder.setTarget(target("B"));
  expect(old.stop).toHaveBeenCalledTimes(1);
  // Browser stop completes asynchronously and may first send a revised result.
  vi.advanceTimersByTime(8000);
  old.onresult!(result("alpha revised"));
  old.onend!(new Event("end"));

  const current = recognizers[1];
  expect(current.start).toHaveBeenCalledTimes(1);
  current.onresult!(result("bravo"));
  vi.advanceTimersByTime(8000);
  recorder.stop();
  current.onend!(new Event("end"));
  await vi.advanceTimersByTimeAsync(30000);
  expect(submit.mock.calls.map(([id, chunk]) => [id, chunk.text])).toEqual([
    ["A", "alpha revised"], ["B", "bravo"],
  ]);
  expect(recognizers).toHaveLength(2);
});

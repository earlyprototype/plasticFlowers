import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { createChunkBuffer, createChunkDispatcher } from "./useChunkDispatcher";
import type { ChunkSubmissionRequest } from "../lib/types";

describe("createChunkBuffer", () => {
  it("does not reach the dispatch gate on short unpunctuated text", () => {
    const buffer = createChunkBuffer({ clock: () => 1 });
    buffer.append("web speech text with no punctuation at all");
    expect(buffer.shouldDispatch()).toBe(false);
    expect(buffer.pendingSentences).toBe(0);
  });

  it("dispatches once the sentence threshold is met", () => {
    const buffer = createChunkBuffer({ clock: () => 1, minSentences: 3 });
    buffer.append("One. Two. Three.");
    expect(buffer.shouldDispatch()).toBe(true);
  });

  it("dispatches once the char threshold is met even without punctuation", () => {
    const buffer = createChunkBuffer({ clock: () => 1 });
    buffer.append("a".repeat(1000));
    expect(buffer.shouldDispatch()).toBe(true);
  });

  it("becomes stale once buffered text has waited past maxDelayMs", () => {
    let seconds = 100;
    const buffer = createChunkBuffer({ clock: () => seconds, maxDelayMs: 15000 });

    buffer.append("final utterance without punctuation");
    expect(buffer.isStale()).toBe(false);

    seconds = 114; // 14s later — not yet stale
    expect(buffer.isStale()).toBe(false);

    seconds = 115.5; // 15.5s later — stale
    expect(buffer.isStale()).toBe(true);
  });

  it("is never stale when empty", () => {
    let seconds = 0;
    const buffer = createChunkBuffer({ clock: () => seconds, maxDelayMs: 15000 });
    seconds = 1000;
    expect(buffer.isStale()).toBe(false);
  });

  it("takeChunk drains the buffer and stamps start/end times", () => {
    let seconds = 10;
    const buffer = createChunkBuffer({ clock: () => seconds });
    buffer.append("hello");
    seconds = 12;
    buffer.append("world");
    seconds = 14;

    const chunk = buffer.takeChunk();
    expect(chunk).toEqual({ text: "hello world", start_time: 10, end_time: 14 });
    expect(buffer.pendingText).toBe("");
    expect(buffer.takeChunk()).toBeNull();
    expect(buffer.isStale()).toBe(false);
  });
});

describe("stale-flush deadline (onDeadline)", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("flushes buffered text exactly maxDelayMs after the first append", () => {
    const buffer = createChunkBuffer({
      clock: () => 0,
      maxDelayMs: 15000,
      onDeadline: () => {
        buffer.takeChunk();
      },
    });
    const spy = vi.spyOn(buffer, "takeChunk");

    buffer.append("tail text that never gets punctuation");

    vi.advanceTimersByTime(14999);
    expect(spy).not.toHaveBeenCalled();

    vi.advanceTimersByTime(1);
    expect(spy).toHaveBeenCalledTimes(1);
    expect(buffer.pendingText).toBe("");
  });

  it("does not arm while the buffer stays empty (no timer churn at idle)", () => {
    const onDeadline = vi.fn();
    const buffer = createChunkBuffer({ clock: () => 0, maxDelayMs: 15000, onDeadline });

    buffer.append("   "); // whitespace-only appends never enter the buffer
    vi.advanceTimersByTime(60000);
    expect(onDeadline).not.toHaveBeenCalled();
  });

  it("keeps the deadline anchored to the empty -> non-empty transition across appends", () => {
    const onDeadline = vi.fn();
    const buffer = createChunkBuffer({ clock: () => 0, maxDelayMs: 15000, onDeadline });

    buffer.append("first fragment");
    vi.advanceTimersByTime(10000);
    buffer.append("second fragment"); // must not push the deadline back
    vi.advanceTimersByTime(5000);
    expect(onDeadline).toHaveBeenCalledTimes(1);
  });

  it("is cleared when takeChunk drains the buffer before the deadline", () => {
    const onDeadline = vi.fn();
    const buffer = createChunkBuffer({ clock: () => 0, maxDelayMs: 15000, onDeadline });

    buffer.append("dispatched before going stale");
    buffer.takeChunk();

    vi.advanceTimersByTime(60000);
    expect(onDeadline).not.toHaveBeenCalled();
  });

  it("is cleared by reset", () => {
    const onDeadline = vi.fn();
    const buffer = createChunkBuffer({ clock: () => 0, maxDelayMs: 15000, onDeadline });

    buffer.append("text");
    buffer.reset();

    vi.advanceTimersByTime(60000);
    expect(onDeadline).not.toHaveBeenCalled();
  });

  it("is cleared by dispose (unmount cleanup)", () => {
    const onDeadline = vi.fn();
    const buffer = createChunkBuffer({ clock: () => 0, maxDelayMs: 15000, onDeadline });

    buffer.append("text");
    buffer.dispose();

    vi.advanceTimersByTime(60000);
    expect(onDeadline).not.toHaveBeenCalled();
  });

  it("re-arms on the next append after the buffer empties", () => {
    const onDeadline = vi.fn();
    const buffer = createChunkBuffer({ clock: () => 0, maxDelayMs: 15000, onDeadline });

    buffer.append("first chunk");
    buffer.takeChunk();

    buffer.append("second chunk");
    vi.advanceTimersByTime(15000);
    expect(onDeadline).toHaveBeenCalledTimes(1);
  });
});

describe("session-bound delivery", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it("sends each short utterance to the session that captured it when its deadline fires", async () => {
    const submit = vi.fn(async (_session: string, _payload: ChunkSubmissionRequest) => {});
    const dispatcher = createChunkDispatcher({ submit, clock: () => Date.now() / 1000 });
    const a = dispatcher.forSession("A");
    a.append("alpha", true);
    await vi.advanceTimersByTimeAsync(5000);
    const b = dispatcher.forSession("B");
    b.append("bravo", true);

    await vi.advanceTimersByTimeAsync(10000);
    expect(submit.mock.calls.map(([id, chunk]) => [id, chunk.text])).toEqual([["A", "alpha"]]);
    await vi.advanceTimersByTimeAsync(5000);
    expect(submit.mock.calls.map(([id, chunk]) => [id, chunk.text])).toEqual([
      ["A", "alpha"], ["B", "bravo"],
    ]);
  });

  it("holds later speech during a failed request and retries the original payload once", async () => {
    let rejectFirst!: (error: Error) => void;
    const submit = vi.fn(async (_session: string, _payload: ChunkSubmissionRequest) => {});
    submit.mockImplementationOnce(() => new Promise<void>((_, reject) => { rejectFirst = reject; }));
    let seconds = 10;
    const dispatcher = createChunkDispatcher({ submit, clock: () => seconds });
    const a = dispatcher.forSession("A");
    a.append("first", true);
    seconds = 11;
    const firstAttempt = a.dispatchNow();
    await Promise.resolve();

    seconds = 12;
    a.append("second", true);
    seconds = 13;
    void a.dispatchNow();
    expect(submit).toHaveBeenCalledTimes(1);
    rejectFirst(new Error("connection lost"));
    await firstAttempt;
    expect(dispatcher.failures).toEqual([{ sessionId: "A", error: "connection lost" }]);
    await vi.advanceTimersByTimeAsync(30000);
    expect(submit).toHaveBeenCalledTimes(1);

    seconds = 99;
    await Promise.all([dispatcher.retry("A"), dispatcher.retry("A")]);
    await a.dispatchNow();
    await dispatcher.retry("A");
    const [[firstSession, first], retry, [secondSession, second]] = submit.mock.calls;
    expect(firstSession).toBe("A");
    expect(first).toEqual({
      text: "first", start_time: 10, end_time: 11, client_request_id: expect.stringMatching(/^[0-9a-f-]{36}$/i),
    });
    expect(retry).toEqual(["A", first]);
    expect(secondSession).toBe("A");
    expect(second).toEqual({
      text: "second", start_time: 12, end_time: 13, client_request_id: expect.stringMatching(/^[0-9a-f-]{36}$/i),
    });
    expect(second.client_request_id).not.toBe(first.client_request_id);
    expect(submit).toHaveBeenCalledTimes(3);
    expect(dispatcher.failures).toEqual([]);
  });

  it("continues sending B while A is in flight or waiting for retry after a permanent rejection", async () => {
    let rejectA!: (error: Error) => void;
    const submit = vi.fn(async (session: string, _payload: ChunkSubmissionRequest) => {
      if (session === "A") throw new Error("session ended");
    });
    submit.mockImplementationOnce(() => new Promise<void>((_, reject) => { rejectA = reject; }));
    const dispatcher = createChunkDispatcher({ submit });
    const a = dispatcher.forSession("A");
    a.append("ending", true);
    const firstAttempt = a.dispatchNow();
    await Promise.resolve();
    const b = dispatcher.forSession("B");
    b.append("new session", true);
    void b.dispatchNow();
    await Promise.resolve();
    expect(submit.mock.calls.map(([id]) => id)).toEqual(["A", "B"]);

    rejectA(new Error("session ended"));
    await firstAttempt;
    b.append("more speech", true);
    await b.dispatchNow();
    expect(submit.mock.calls.map(([id]) => id)).toEqual(["A", "B", "B"]);
    await dispatcher.retry("A");
    expect(dispatcher.failures).toEqual([{ sessionId: "A", error: "session ended" }]);
    expect(submit.mock.calls[3]).toEqual(submit.mock.calls[0]);
  });
});

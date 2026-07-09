import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { createChunkBuffer, startStaleFlushTimer } from "./useChunkDispatcher";

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

describe("startStaleFlushTimer", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("flushes a stale non-empty buffer without requiring another append", () => {
    let seconds = 0;
    const buffer = createChunkBuffer({ clock: () => seconds, maxDelayMs: 15000 });
    const flush = vi.fn(() => {
      buffer.takeChunk();
    });
    const stop = startStaleFlushTimer(buffer, flush, 1000);

    buffer.append("tail text that never gets punctuation");

    // Not yet stale: ticks occur but nothing flushes
    seconds = 10;
    vi.advanceTimersByTime(10000);
    expect(flush).not.toHaveBeenCalled();

    // Past maxDelayMs: the next tick flushes exactly once (buffer drained)
    seconds = 16;
    vi.advanceTimersByTime(2000);
    expect(flush).toHaveBeenCalledTimes(1);
    expect(buffer.pendingText).toBe("");

    stop();
  });

  it("stops checking after the returned stop function runs (unmount cleanup)", () => {
    let seconds = 0;
    const buffer = createChunkBuffer({ clock: () => seconds, maxDelayMs: 15000 });
    const flush = vi.fn();
    const stop = startStaleFlushTimer(buffer, flush, 1000);

    buffer.append("text");
    stop();

    seconds = 1000;
    vi.advanceTimersByTime(60000);
    expect(flush).not.toHaveBeenCalled();
  });
});

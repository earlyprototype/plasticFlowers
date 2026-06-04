import { describe, expect, it } from "vitest";

import { computeBackoffDelay } from "./useSSE";

describe("computeBackoffDelay", () => {
  it("starts at one second for the first attempt", () => {
    expect(computeBackoffDelay(0)).toBe(1000);
  });

  it("doubles the delay exponentially", () => {
    expect(computeBackoffDelay(1)).toBe(2000);
    expect(computeBackoffDelay(2)).toBe(4000);
    expect(computeBackoffDelay(3)).toBe(8000);
  });

  it("caps the backoff at thirty seconds", () => {
    expect(computeBackoffDelay(5)).toBe(30000);
    expect(computeBackoffDelay(10)).toBe(30000);
  });

  it("handles negative attempts defensively", () => {
    expect(computeBackoffDelay(-1)).toBe(1000);
  });
});


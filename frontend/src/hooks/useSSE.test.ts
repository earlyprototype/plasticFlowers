import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  computeBackoffDelay,
  createSSEConnection,
  EVENT_TYPES,
  type ConnectionState,
} from "./useSSE";

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

describe("EVENT_TYPES", () => {
  it("contains no duplicate registrations (a duplicate double-delivers every event)", () => {
    expect(new Set(EVENT_TYPES).size).toBe(EVENT_TYPES.length);
  });

  it("registers gardener_cycle exactly once so cycles increment counters once", () => {
    expect(EVENT_TYPES.filter((type) => type === "gardener_cycle")).toHaveLength(1);
  });

  it("subscribes to node_corrected", () => {
    expect(EVENT_TYPES).toContain("node_corrected");
  });

  it("subscribes to resync_required so queue-overflow notices reach the graph handler", () => {
    expect(EVENT_TYPES).toContain("resync_required");
  });
});

class FakeEventSource {
  static instances: FakeEventSource[] = [];

  listeners = new Map<string, Array<(event: MessageEvent) => void>>();
  onopen: ((event: Event) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  closed = false;

  constructor(public url: string) {
    FakeEventSource.instances.push(this);
  }

  addEventListener(type: string, listener: (event: MessageEvent) => void): void {
    const existing = this.listeners.get(type) ?? [];
    existing.push(listener);
    this.listeners.set(type, existing);
  }

  close(): void {
    this.closed = true;
  }

  emitOpen(): void {
    this.onopen?.({} as Event);
  }

  emitError(): void {
    this.onerror?.({} as Event);
  }

  emit(type: string, data: string): void {
    (this.listeners.get(type) ?? []).forEach((listener) =>
      listener({ data } as MessageEvent),
    );
  }
}

describe("createSSEConnection", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    FakeEventSource.instances = [];
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  const buildConnection = (overrides: { onEvent?: (type: string, data: string) => void } = {}) => {
    const states: ConnectionState[] = [];
    const reconnected = vi.fn();
    const connection = createSSEConnection({
      url: "http://test/stream",
      onEvent: overrides.onEvent ?? (() => {}),
      onStateChange: (state) => states.push(state),
      onReconnected: reconnected,
      createEventSource: (url) => new FakeEventSource(url),
    });
    return { connection, states, reconnected };
  };

  it("transitions connecting -> open on first connect", () => {
    const { connection, states } = buildConnection();
    connection.start();
    expect(states).toEqual(["connecting"]);

    FakeEventSource.instances[0].emitOpen();
    expect(states).toEqual(["connecting", "open"]);
    connection.stop();
  });

  it("enters reconnecting when a reconnect is scheduled, then connecting -> open", () => {
    const { connection, states, reconnected } = buildConnection();
    connection.start();
    FakeEventSource.instances[0].emitOpen();

    FakeEventSource.instances[0].emitError();
    expect(states).toEqual(["connecting", "open", "reconnecting"]);
    expect(FakeEventSource.instances[0].closed).toBe(true);
    expect(reconnected).not.toHaveBeenCalled();

    // First backoff delay is 1s; afterwards a fresh EventSource is created.
    vi.advanceTimersByTime(1000);
    expect(states).toEqual(["connecting", "open", "reconnecting", "connecting"]);
    expect(FakeEventSource.instances).toHaveLength(2);

    FakeEventSource.instances[1].emitOpen();
    expect(states).toEqual(["connecting", "open", "reconnecting", "connecting", "open"]);
    expect(reconnected).toHaveBeenCalledTimes(1);
    connection.stop();
  });

  it("stops reconnecting after stop() is called", () => {
    const { connection, states } = buildConnection();
    connection.start();
    FakeEventSource.instances[0].emitError();
    expect(states.at(-1)).toBe("reconnecting");

    connection.stop();
    vi.advanceTimersByTime(60000);
    expect(FakeEventSource.instances).toHaveLength(1);
    expect(states.at(-1)).toBe("reconnecting");
  });

  it("delivers event data to onEvent but never forwards heartbeats", () => {
    const received: Array<[string, string]> = [];
    const { connection } = buildConnection({
      onEvent: (type, data) => received.push([type, data]),
    });
    connection.start();
    const source = FakeEventSource.instances[0];
    source.emitOpen();

    source.emit("gardener_cycle", '{"timestamp":"t"}');
    source.emit("heartbeat", "ping");
    expect(received).toEqual([["gardener_cycle", '{"timestamp":"t"}']]);
    connection.stop();
  });
});

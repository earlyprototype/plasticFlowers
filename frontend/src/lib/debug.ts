/**
 * Tiny debug logger gated behind NEXT_PUBLIC_DEBUG.
 *
 * Per-event logging (SSE traffic, speech chunking) is far too noisy for
 * normal use but valuable when diagnosing a live session. Set
 * `NEXT_PUBLIC_DEBUG=1` (or `true`) in the environment / .env.local to
 * enable it. `console.warn` / `console.error` for real anomalies should be
 * used directly, never gated.
 */
const DEBUG_ENABLED =
  process.env.NEXT_PUBLIC_DEBUG === "1" || process.env.NEXT_PUBLIC_DEBUG === "true";

export function debugLog(...args: unknown[]): void {
  if (DEBUG_ENABLED) {
    // eslint-disable-next-line no-console
    console.log(...args);
  }
}

/**
 * Test-only helpers for accessing internal session store state.
 * @internal - Test utilities only. Not part of public API.
 */

import { sessionStore } from "./session-store-instance.js";
import type { SessionState } from "./session-store.js";

/**
 * Opt a test into rules injection.
 *
 * Rules injection is off by default (`pluginConfig["wopal-plugin"].rules.enabled`
 * is `false`), so tests that assert injection must deliver the opt-in switch
 * through the engine's `pluginConfig` slice — the plugin no longer reads
 * settings files. Spread the result into the plugin input:
 *
 * ```ts
 * const hooks = await plugin({ ...mockInput, ...enableRulesInjection() });
 * ```
 */
export function enableRulesInjection(): {
  pluginConfig: Record<string, Record<string, unknown>>;
} {
  return { pluginConfig: { "wopal-plugin": { rules: { enabled: true } } } };
}

export function setSessionStateLimit(limit: number): void {
  sessionStore.setMax(limit);
}

export function getSessionStateIDs(): string[] {
  return sessionStore.ids();
}

export function getSessionStateSnapshot(
  sessionID: string,
): SessionState | undefined {
  return sessionStore.snapshot(sessionID);
}

export function upsertSessionState(
  sessionID: string,
  mutator: (state: SessionState) => void,
): void {
  sessionStore.upsert(sessionID, mutator);
}

export function resetSessionState(): void {
  sessionStore.reset();
}

export function getSeedCount(sessionID: string): number {
  return sessionStore.get(sessionID)?.seedCount ?? 0;
}

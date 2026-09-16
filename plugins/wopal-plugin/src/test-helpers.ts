/**
 * Test-only helpers for accessing internal session store state.
 * @internal - Test utilities only. Not part of public API.
 */

import { mkdirSync, writeFileSync } from "fs";
import { join } from "path";
import { sessionStore } from "./session-store-instance.js";
import type { SessionState } from "./session-store.js";

/**
 * Opt a test into rules injection.
 *
 * Rules injection is off by default (`wopal.rules.enabled: false`), so tests
 * that assert injection must write the opt-in switch into the global settings
 * layer that the plugin reads (`$WOPAL_HOME/config/settings.jsonc`).
 */
export function enableRulesInjection(wopalHome: string): void {
  const configDir = join(wopalHome, "config");
  mkdirSync(configDir, { recursive: true });
  writeFileSync(
    join(configDir, "settings.jsonc"),
    JSON.stringify({ wopal: { rules: { enabled: true } } }),
  );
}

export function setSessionStateLimit(limit: number): void {
  sessionStore.setMax(limit);
}

export function getSessionStateIDs(): string[] {
  return sessionStore.ids();
}

export function getSessionStateSnapshot(sessionID: string): SessionState | undefined {
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

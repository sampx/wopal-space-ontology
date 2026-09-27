import type { WopalPluginConfig } from "./schema.js";
import { defaultWopalPluginConfig } from "./schema.js";

export type ConfigFragment = Record<string, unknown>;

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value) &&
    !(value instanceof Date)
  );
}

function deepMergeInto(
  target: Record<string, unknown>,
  fragment: Record<string, unknown>,
): void {
  for (const [key, value] of Object.entries(fragment)) {
    const existing = target[key];
    if (isPlainObject(value)) {
      const next = isPlainObject(existing) ? existing : {};
      deepMergeInto(next, value);
      target[key] = next;
      continue;
    }
    target[key] = Array.isArray(value) ? [...value] : value;
  }
}

/**
 * Layers the engine-delivered config slice over the plugin's built-in
 * defaults: objects merge deeply, slice leaves win, arrays replace whole.
 *
 * The engine owns the three settings layers (global → space-public →
 * space-local) and delivers `wopal.pluginConfig["wopal-plugin"]` already
 * merged; the plugin only layers that slice onto its defaults (D-01
 * precedence). Layer provenance is engine-side, so no per-leaf `sources`
 * attribution is recorded (D-02).
 */
export function mergeConfigs(fragment: ConfigFragment = {}): WopalPluginConfig {
  const config: Record<string, unknown> = structuredClone(
    defaultWopalPluginConfig,
  );
  deepMergeInto(config, fragment);
  return config as WopalPluginConfig;
}

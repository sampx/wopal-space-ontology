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
 * Layers the plugin's config fragments over its built-in defaults in
 * consumption order (D-01): defaults < inline mount options < engine-delivered
 * slice. Objects merge deeply, later leaves win, arrays replace whole.
 *
 * The engine owns the three settings layers (global → space-public →
 * space-local) and delivers `wopal.pluginConfig["wopal-plugin"]` already
 * merged; the plugin layers the delivered slice over the defaults and the
 * inline mount options. Layer provenance is engine-side, so no per-leaf
 * `sources` attribution is recorded (D-02).
 */
export function mergeConfigs(
  inlineOptions: ConfigFragment = {},
  engineSlice: ConfigFragment = {},
): WopalPluginConfig {
  const config: Record<string, unknown> = structuredClone(
    defaultWopalPluginConfig,
  );
  deepMergeInto(config, inlineOptions);
  deepMergeInto(config, engineSlice);
  return config as WopalPluginConfig;
}

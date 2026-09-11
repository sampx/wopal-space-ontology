import type { WopalPluginConfig } from "./schema.js";
import { defaultWopalPluginConfig } from "./schema.js";

export type ConfigLayer =
  | "global"
  | "space-public"
  | "space-local";

export type ConfigSource = ConfigLayer | "default";

export type ConfigFragment = Record<string, unknown>;

export type ConfigSourceFile = Record<string, ConfigSource>;

export interface MergedConfig {
  config: WopalPluginConfig;
  sources: ConfigSourceFile;
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value) &&
    !(value instanceof Date)
  );
}

function recordLeaves(
  value: unknown,
  prefix: string,
  sources: ConfigSourceFile,
  layer: ConfigSource,
): void {
  if (!isPlainObject(value)) {
    sources[prefix] = layer;
    return;
  }
  const entries = Object.entries(value);
  if (entries.length === 0) {
    sources[prefix] = layer;
  }
  for (const [key, child] of entries) {
    recordLeaves(child, prefix === "" ? key : `${prefix}.${key}`, sources, layer);
  }
}

function deepMergeInto(
  target: Record<string, unknown>,
  fragment: Record<string, unknown>,
  sources: ConfigSourceFile,
  layer: ConfigLayer,
  prefix: string,
): void {
  for (const [key, value] of Object.entries(fragment)) {
    const path = prefix === "" ? key : `${prefix}.${key}`;
    const existing = target[key];
    if (isPlainObject(value)) {
      const next = isPlainObject(existing) ? existing : {};
      deepMergeInto(next, value, sources, layer, path);
      target[key] = next;
      continue;
    }
    target[key] = Array.isArray(value) ? [...value] : value;
    recordLeaves(value, path, sources, layer);
  }
}

export function mergeConfigs(layers: {
  layer: ConfigLayer;
  fragment: ConfigFragment;
}[]): MergedConfig {
  const config: Record<string, unknown> = structuredClone(
    defaultWopalPluginConfig,
  );
  const sources: ConfigSourceFile = {};
  recordLeaves(defaultWopalPluginConfig, "", sources, "default");

  for (const { layer, fragment } of layers) {
    deepMergeInto(config, fragment, sources, layer, "");
  }
  return { config: config as WopalPluginConfig, sources };
}

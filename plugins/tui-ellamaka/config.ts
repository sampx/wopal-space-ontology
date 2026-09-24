/**
 * ONT-G4 unified config channel for the TUI plugin.
 *
 * The engine hands TUI plugins their options only through the inline mount
 * entry (`[spec, options]`), and `TuiPluginApi` exposes no `wopalSpaceRoot`
 * and no config reader. Until the engine contract grows those surfaces, the
 * plugin resolves its own behavior config: locate the Wopal space root from
 * the process cwd, deep-merge the three-layer settings (global →
 * space-public → space-local, later wins), and read
 * `wopal.pluginConfig["tui-ellamaka"]`. The inline mount options
 * (`rawOptions`) stay as a fallback for un-migrated deployments.
 */

import { existsSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { parse as parseJsonc, type ParseError } from "jsonc-parser";

export interface TuiEllamakaConfig {
  enabled?: boolean;
  label?: string;
  [key: string]: unknown;
}

type JsonObject = Record<string, unknown>;

const PLUGIN_KEY = "tui-ellamaka";

function isPlainObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function parseJsoncObject(text: string): JsonObject | undefined {
  const errors: ParseError[] = [];
  const parsed: unknown = parseJsonc(text, errors, {
    allowTrailingComma: true,
    disallowComments: false,
  });
  if (errors.length > 0 || !isPlainObject(parsed)) return undefined;
  return parsed;
}

/**
 * Locate the Wopal space root by walking up from the process cwd looking for
 * a `.wopal` directory. Returns undefined when cwd lies outside any space.
 */
export function findSpaceRoot(wopalHome: string): string | undefined {
  let dir = resolve(process.cwd());
  const homeRoot = resolve(wopalHome, "..");
  for (;;) {
    if (existsSync(join(dir, ".wopal"))) return dir;
    // Stop before climbing above the filesystem root or into WOPAL_HOME's
    // parent chain beyond itself (a space never lives above the user home).
    if (dir === dirname(dir)) return undefined;
    dir = dirname(dir);
  }
}

function deepMergeInto(target: JsonObject, fragment: JsonObject): void {
  for (const [key, value] of Object.entries(fragment)) {
    const existing = target[key];
    if (isPlainObject(value) && isPlainObject(existing)) {
      deepMergeInto(existing, value);
      continue;
    }
    target[key] = value;
  }
}

/**
 * Deep-merge raw settings fragments (already-extracted `wopal` nodes or
 * partial objects). Malformed fragments are skipped rather than fatal — a
 * broken optional layer must not break TUI startup.
 */
export function mergeSettingLayers(fragments: unknown[]): JsonObject {
  const merged: JsonObject = {};
  for (const fragment of fragments) {
    if (!isPlainObject(fragment)) continue;
    deepMergeInto(merged, fragment);
  }
  return merged;
}

/** Extract `wopal.pluginConfig["tui-ellamaka"]` from one parsed settings object. */
export function extractPluginConfig(settings: unknown): JsonObject | undefined {
  if (!isPlainObject(settings)) return undefined;
  const wopal = settings["wopal"];
  if (!isPlainObject(wopal)) return undefined;
  const pluginConfig = wopal["pluginConfig"];
  if (!isPlainObject(pluginConfig)) return undefined;
  const entry = pluginConfig[PLUGIN_KEY];
  if (entry === undefined) return undefined;
  if (!isPlainObject(entry)) {
    throw new Error(
      `wopal.pluginConfig["${PLUGIN_KEY}"] must be an object, got ${typeof entry}`,
    );
  }
  return entry;
}

function readWopalNode(path: string): JsonObject | undefined {
  if (!existsSync(path)) return undefined;
  try {
    const text = readFileSync(path, "utf8");
    const parsed = parseJsoncObject(text);
    const wopal = parsed?.["wopal"];
    return isPlainObject(wopal) ? wopal : undefined;
  } catch {
    // Unreadable file: skip the layer, same as a missing one.
    return undefined;
  }
}

/**
 * Resolve the plugin's effective config.
 *
 * Priority: `wopal.pluginConfig["tui-ellamaka"]` (three-layer deep merge,
 * later layer wins) → inline mount options (`rawOptions`) → built-in
 * defaults. A non-object pluginConfig entry fails loud.
 */
export function resolveTuiConfig(
  wopalHome: string,
  rawOptions?: unknown,
): TuiEllamakaConfig {
  const spaceRoot = findSpaceRoot(wopalHome);
  const fragments: JsonObject[] = [];
  if (spaceRoot !== undefined) {
    fragments.push(
      readWopalNode(join(wopalHome, "config", "settings.jsonc")) ?? {},
      readWopalNode(join(spaceRoot, ".wopal", "config", "settings.jsonc")) ?? {},
      readWopalNode(
        join(spaceRoot, ".wopal", "config", "settings.local.jsonc"),
      ) ?? {},
    );
  }
  const mergedWopal = mergeSettingLayers(fragments);
  const fromSettings = extractPluginConfig({ wopal: mergedWopal });

  const base = isPlainObject(rawOptions) ? rawOptions : {};
  if (fromSettings === undefined) {
    return { enabled: true, ...base } as TuiEllamakaConfig;
  }
  return { enabled: true, ...base, ...fromSettings } as TuiEllamakaConfig;
}

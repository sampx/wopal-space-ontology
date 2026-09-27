/**
 * Behaviour config consumption for the tui-ellamaka plugin.
 *
 * The engine merges the three settings layers (`wopal.pluginConfig`, global →
 * space-public → space-local) and delivers the whole table through
 * `TuiPluginApi.pluginConfig`; the plugin takes its own entry from that table
 * and validates its shape. The inline mount options stay as a compatibility
 * fallback.
 */

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

function shapeOf(value: unknown): string {
  if (value === null) return "null";
  if (Array.isArray(value)) return "array";
  return typeof value;
}

/**
 * Resolve the plugin's effective config.
 *
 * Precedence: built-in defaults < inline mount options (`rawOptions`) <
 * engine-delivered `pluginConfig["tui-ellamaka"]`, later wins per key. The
 * table entry fails loud when it is not an object or when a known field
 * (`enabled`, `label`) carries the wrong type, so a malformed settings value
 * surfaces instead of silently reverting to defaults.
 */
export function resolveTuiConfig(
  pluginConfig: Record<string, unknown> | undefined,
  rawOptions?: unknown,
): TuiEllamakaConfig {
  const config: TuiEllamakaConfig = { enabled: true };
  if (isPlainObject(rawOptions)) Object.assign(config, rawOptions);

  const entry = pluginConfig?.[PLUGIN_KEY];
  if (entry === undefined) return config;
  if (!isPlainObject(entry)) {
    throw new Error(
      `pluginConfig["${PLUGIN_KEY}"] must be an object, got ${shapeOf(entry)}`,
    );
  }
  if (entry.enabled !== undefined && typeof entry.enabled !== "boolean") {
    throw new Error(
      `pluginConfig["${PLUGIN_KEY}"].enabled must be a boolean, got ${shapeOf(entry.enabled)}`,
    );
  }
  if (entry.label !== undefined && typeof entry.label !== "string") {
    throw new Error(
      `pluginConfig["${PLUGIN_KEY}"].label must be a string, got ${shapeOf(entry.label)}`,
    );
  }
  Object.assign(config, entry);
  return config;
}

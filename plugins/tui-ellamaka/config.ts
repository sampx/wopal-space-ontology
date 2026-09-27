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
 * Keys whose assignment would walk the prototype chain: assigning the own
 * key `__proto__` invokes the inherited setter and swaps the object's
 * prototype. Entry/inline payloads carrying them are ignored per-key.
 */
const UNSAFE_KEYS = new Set(["__proto__", "constructor", "prototype"]);

function assignFields(target: JsonObject, source: JsonObject): void {
  for (const [key, value] of Object.entries(source)) {
    if (UNSAFE_KEYS.has(key)) continue;
    target[key] = value;
  }
}

/** Known behavioural fields fail loud when their type is wrong. */
function validateKnownFields(location: string, source: JsonObject): void {
  if (source.enabled !== undefined && typeof source.enabled !== "boolean") {
    throw new Error(
      `${location}.enabled must be a boolean, got ${shapeOf(source.enabled)}`,
    );
  }
  if (source.label !== undefined && typeof source.label !== "string") {
    throw new Error(
      `${location}.label must be a string, got ${shapeOf(source.label)}`,
    );
  }
}

/**
 * Resolve the plugin's effective config.
 *
 * Precedence: built-in defaults < inline mount options (`rawOptions`) <
 * engine-delivered `pluginConfig["tui-ellamaka"]`, later wins per key. A
 * known field (`enabled`, `label`) carrying the wrong type fails loud on
 * both channels; the table entry also fails loud when it is not an object.
 * Malformed values surface instead of silently reverting to defaults.
 */
export function resolveTuiConfig(
  pluginConfig: Record<string, unknown> | undefined,
  rawOptions?: unknown,
): TuiEllamakaConfig {
  const config: TuiEllamakaConfig = { enabled: true };
  if (isPlainObject(rawOptions)) {
    validateKnownFields("inline options for tui-ellamaka", rawOptions);
    assignFields(config, rawOptions);
  }

  const entry = pluginConfig?.[PLUGIN_KEY];
  if (entry === undefined) return config;
  if (!isPlainObject(entry)) {
    throw new Error(
      `pluginConfig["${PLUGIN_KEY}"] must be an object, got ${shapeOf(entry)}`,
    );
  }
  validateKnownFields(`pluginConfig["${PLUGIN_KEY}"]`, entry);
  assignFields(config, entry);
  return config;
}

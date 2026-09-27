import { wopalPluginConfigSchema, type WopalPluginConfig } from "./schema.js";
import { mergeConfigs } from "./merge.js";

const PLUGIN_NAME = "wopal-plugin";

export interface LoadWopalConfigOptions {
  /**
   * Engine-delivered slice `PluginInput.pluginConfig["wopal-plugin"]`, already
   * deep-merged across the three settings layers (global → space-public →
   * space-local) by the engine. `undefined` means the space declares no entry
   * for this plugin — the built-in defaults apply.
   */
  pluginConfig?: Record<string, unknown>;
  /**
   * Environment loaded from `.env` files by the runtime. Used as a fallback
   * source when resolving `$VAR` references, so secrets kept in `.env` stay
   * referenced from the config slice while `process.env` keeps precedence.
   */
  fallbackEnvironment?: NodeJS.ProcessEnv;
}

class ConfigError extends Error {
  constructor(location: string, detail: string) {
    super(`${PLUGIN_NAME} config error at ${location}: ${detail}`);
    this.name = "ConfigError";
  }
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value) &&
    !(value instanceof Date)
  );
}

function resolveVarReferences(
  value: unknown,
  path: string,
  environment: NodeJS.ProcessEnv,
  fallbackEnvironment: NodeJS.ProcessEnv,
): unknown {
  if (typeof value === "string") {
    if (!value.startsWith("$")) return value;
    const varName = value.slice(1);
    const resolved = environment[varName] ?? fallbackEnvironment[varName];
    if (resolved === undefined || resolved === "") {
      throw new ConfigError(
        path || "(root)",
        `environment variable "${varName}" referenced by "${value}" is not set in process.env or the .env files`,
      );
    }
    return resolved;
  }
  if (Array.isArray(value)) {
    return value.map((item, index) =>
      resolveVarReferences(
        item,
        `${path}[${index}]`,
        environment,
        fallbackEnvironment,
      ),
    );
  }
  if (isPlainObject(value)) {
    const resolved: Record<string, unknown> = {};
    for (const [key, child] of Object.entries(value)) {
      resolved[key] = resolveVarReferences(
        child,
        path === "" ? key : `${path}.${key}`,
        environment,
        fallbackEnvironment,
      );
    }
    return resolved;
  }
  return value;
}

function formatZodIssues(error: {
  issues: { path: PropertyKey[]; message: string }[];
}): string {
  return error.issues
    .map((issue) => `${issue.path.join(".") || "(root)"}: ${issue.message}`)
    .join("; ");
}

function validate(candidate: Record<string, unknown>): WopalPluginConfig {
  const result = wopalPluginConfigSchema.safeParse(candidate);
  if (!result.success) {
    throw new ConfigError(
      "plugin config",
      `validation failed: ${formatZodIssues(result.error)}`,
    );
  }
  return result.data;
}

/**
 * Resolves the effective wopal-plugin configuration.
 *
 * There are no settings-file inputs: the engine merges the three settings
 * layers and delivers `wopal.pluginConfig["wopal-plugin"]` through
 * `PluginInput.pluginConfig`. The delivered slice is layered over the
 * built-in defaults, `$VAR` references are resolved (`process.env` first,
 * the runtime-provided `.env` environment as fallback), and the result is
 * validated strictly — invalid config fails loud instead of degrading.
 */
export function loadWopalConfig(
  options: LoadWopalConfigOptions = {},
  environment: NodeJS.ProcessEnv = process.env,
): WopalPluginConfig {
  const slice = options.pluginConfig;
  if (slice !== undefined && !isPlainObject(slice)) {
    throw new ConfigError(
      `pluginConfig["${PLUGIN_NAME}"]`,
      "the plugin config entry must be an object",
    );
  }

  const merged = mergeConfigs(slice ?? {});
  const resolved = resolveVarReferences(
    merged,
    "",
    environment,
    options.fallbackEnvironment ?? {},
  );
  return validate(resolved as Record<string, unknown>);
}

export { ConfigError };

import { existsSync, readFileSync } from "fs";
import { join } from "path";
import { parse, type ParseError } from "jsonc-parser";
import { wopalPluginConfigSchema, type WopalPluginConfig } from "./schema.js";
import {
  mergeConfigs,
  type ConfigFragment,
  type ConfigLayer,
  type ConfigSourceFile,
} from "./merge.js";

export interface LoadedConfig {
  config: WopalPluginConfig;
  sources: ConfigSourceFile;
}

export interface LoadWopalConfigOptions {
  wopalHome: string;
  wopalSpaceRoot?: string;
  /**
   * Environment loaded from `.env` files. Used as a fallback source when
   * resolving `$VAR` references, so secrets kept in `.env` stay referenced
   * from settings while `process.env` keeps precedence.
   */
  fallbackEnvironment?: NodeJS.ProcessEnv;
}

class ConfigError extends Error {
  constructor(path: string, detail: string) {
    super(`wopal config error in ${path}: ${detail}`);
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

interface LayerDefinition {
  layer: ConfigLayer;
  path: string;
}

function layerPaths(options: LoadWopalConfigOptions): LayerDefinition[] {
  const paths: LayerDefinition[] = [
    {
      layer: "global",
      path: join(options.wopalHome, "config", "settings.jsonc"),
    },
  ];
  if (options.wopalSpaceRoot !== undefined) {
    const configDir = join(options.wopalSpaceRoot, ".wopal", "config");
    paths.push(
      { layer: "space-public", path: join(configDir, "settings.jsonc") },
      { layer: "space-local", path: join(configDir, "settings.local.jsonc") },
    );
  }
  return paths;
}

function extractWopalNode(content: string, path: string): ConfigFragment {
  const errors: ParseError[] = [];
  const parsed: unknown = parse(content, errors, {
    allowTrailingComma: true,
    disallowComments: false,
  });
  if (errors.length > 0 || !isPlainObject(parsed)) {
    throw new ConfigError(path, "invalid JSONC content");
  }
  const wopalNode = parsed["wopal"];
  if (wopalNode === undefined) return {};
  if (!isPlainObject(wopalNode)) {
    throw new ConfigError(path, `"wopal" node must be an object`);
  }
  return wopalNode;
}

function readLayer(definition: LayerDefinition): ConfigFragment | undefined {
  if (!existsSync(definition.path)) return undefined;
  let content: string;
  try {
    content = readFileSync(definition.path, "utf-8");
  } catch (err) {
    throw new ConfigError(
      definition.path,
      `cannot read file: ${err instanceof Error ? err.message : String(err)}`,
    );
  }
  return extractWopalNode(content, definition.path);
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
        path,
        `environment variable "${varName}" referenced by "${value}" is not set in process.env or the .env files`,
      );
    }
    return resolved;
  }
  if (Array.isArray(value)) {
    return value.map((item, index) =>
      resolveVarReferences(item, `${path}[${index}]`, environment, fallbackEnvironment),
    );
  }
  if (isPlainObject(value)) {
    const resolved: Record<string, unknown> = {};
    for (const [key, child] of Object.entries(value)) {
      resolved[key] = resolveVarReferences(
        child,
        `${path}.${key}`,
        environment,
        fallbackEnvironment,
      );
    }
    return resolved;
  }
  return value;
}

function formatZodIssues(error: { issues: { path: (string | number)[]; message: string }[] }): string {
  return error.issues
    .map((issue) => `${issue.path.join(".") || "(root)"}: ${issue.message}`)
    .join("; ");
}

function validate(
  merged: Record<string, unknown>,
  originPaths: string,
): WopalPluginConfig {
  const result = wopalPluginConfigSchema.safeParse(merged);
  if (!result.success) {
    throw new Error(
      `wopal config validation failed (${originPaths}): ${formatZodIssues(result.error)}`,
    );
  }
  return result.data;
}

export function loadWopalConfig(
  options: LoadWopalConfigOptions,
  environment: NodeJS.ProcessEnv = process.env,
): LoadedConfig {
  const definitions = layerPaths(options);
  const layers: { layer: ConfigLayer; fragment: ConfigFragment }[] = [];
  for (const definition of definitions) {
    const fragment = readLayer(definition);
    if (fragment === undefined) continue;
    layers.push({ layer: definition.layer, fragment });
  }

  const merged = mergeConfigs(layers);

  const validated = validate(
    resolveVarReferences(
      merged.config,
      "config",
      environment,
      options.fallbackEnvironment ?? {},
    ) as Record<string, unknown>,
    definitions.map(({ path }) => path).join(", "),
  );

  return { config: validated, sources: merged.sources };
}

export { ConfigError };

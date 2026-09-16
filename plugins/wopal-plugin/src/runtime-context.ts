import { dirname, join } from "path";
import { fileURLToPath } from "url";
import { resolveWopalHome } from "./paths.js";

export interface RuntimeContext {
  readonly wopalHome: string;
  readonly directory: string;
  readonly pluginRoot: string;
  readonly isWopalSpace: boolean;
  readonly wopalSpaceRoot?: string;
  readonly logDir: string;
}

/**
 * Plugin package root. The module lives at `<root>/src` in development and
 * `<root>/dist` once built, so the parent of this file's directory is the
 * plugin root in both layouts.
 */
const PLUGIN_ROOT = dirname(dirname(fileURLToPath(import.meta.url)));

export interface RuntimeContextInput {
  directory: string;
  wopalHome?: string;
  wopalSpaceRoot?: string;
}

export function createRuntimeContext(input: RuntimeContextInput): RuntimeContext {
  const wopalHome = resolveWopalHome(input.wopalHome);
  const context: RuntimeContext = {
    wopalHome,
    directory: input.directory,
    pluginRoot: PLUGIN_ROOT,
    isWopalSpace: input.wopalSpaceRoot !== undefined,
    logDir: input.wopalSpaceRoot
      ? join(input.wopalSpaceRoot, ".wopal-space", "logs")
      : join(wopalHome, "logs"),
    ...(input.wopalSpaceRoot !== undefined
      ? { wopalSpaceRoot: input.wopalSpaceRoot }
      : {}),
  };
  return Object.freeze(context);
}

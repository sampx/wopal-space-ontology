/**
 * Runtime Context
 *
 * Detects the execution environment: WOPAL_HOME, wopal-space status
 * (via WOPAL_SPACE_ROOT set by ellamaka), and log directory routing.
 * Initialized once at plugin startup.
 */

import { homedir } from "os";
import { join } from "path";

export interface RuntimeContext {
  wopalHome: string;       // process.env.WOPAL_HOME ?? ~/.wopal
  directory: string;        // ellamaka working directory (from pluginInput.directory)
  isWopalSpace: boolean;   // WOPAL_SPACE_ROOT is set
  spaceRoot?: string;       // WOPAL_SPACE_ROOT, the wopal-space root directory
  logDir: string;           // space: <spaceRoot>/.wopal-space/logs/ ; else: WOPAL_HOME/logs/
}

let _context: RuntimeContext | null = null;

/**
 * Initialize the runtime context singleton.
 * Must be called once at plugin startup before any other module
 * accesses the context via getRuntimeContext().
 */
export function initRuntimeContext(directory: string): RuntimeContext {
  const wopalHome = process.env.WOPAL_HOME || join(homedir(), ".wopal");
  const spaceRoot = process.env.WOPAL_SPACE_ROOT;
  const isWopalSpace = spaceRoot !== undefined;
  const logDir = isWopalSpace
    ? join(spaceRoot, ".wopal-space", "logs")
    : join(wopalHome, "logs");

  _context = {
    wopalHome,
    directory,
    isWopalSpace,
    logDir,
    ...(spaceRoot !== undefined ? { spaceRoot } : {}),
  };
  return _context;
}

/**
 * Get the runtime context singleton.
 * Throws if initRuntimeContext() has not been called.
 */
export function getRuntimeContext(): RuntimeContext {
  if (!_context) {
    throw new Error("RuntimeContext not initialized");
  }
  return _context;
}

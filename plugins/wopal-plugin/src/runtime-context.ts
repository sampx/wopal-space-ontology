/**
 * Runtime Context
 *
 * Detects the execution environment: WOPAL_HOME, wopal-space status,
 * and log directory routing. Initialized once at plugin startup.
 */

import { homedir } from "os";
import { join } from "path";
import { existsSync } from "fs";

export interface RuntimeContext {
  wopalHome: string;       // process.env.WOPAL_HOME ?? ~/.wopal
  workspaceRoot: string;   // from pluginInput.directory
  isWopalSpace: boolean;   // workspaceRoot/.wopal/ exists
  logDir: string;          // space: .wopal-space/logs/ ; else: WOPAL_HOME/logs/
}

let _context: RuntimeContext | null = null;

/**
 * Initialize the runtime context singleton.
 * Must be called once at plugin startup before any other module
 * accesses the context via getRuntimeContext().
 */
export function initRuntimeContext(workspaceRoot: string): RuntimeContext {
  const wopalHome = process.env.WOPAL_HOME || join(homedir(), ".wopal");
  const isWopalSpace = existsSync(join(workspaceRoot, ".wopal"));
  const logDir = isWopalSpace
    ? join(workspaceRoot, ".wopal-space", "logs")
    : join(wopalHome, "logs");

  _context = { wopalHome, workspaceRoot, isWopalSpace, logDir };
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

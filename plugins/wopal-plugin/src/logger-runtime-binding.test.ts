/**
 * Regression guard for module-level logger routing.
 *
 * The module-level loggers (`contextLogger` and friends) are process-wide
 * singletons, but a single process hosts more than one runtime instance. When
 * their destination was frozen to the process environment, a wopal-space
 * instance logged `compact scheduled` into `<WOPAL_HOME>/logs/wopal-plugin.log`
 * instead of the space's own `<space>/.wopal-space/logs/wopal-plugin.log`.
 *
 * These assertions fail if the singletons stop following the runtime installed
 * by the composition root, or start falling back to the WOPAL_HOME log again.
 */

import { afterEach, describe, expect, it } from "vitest";
import { existsSync, mkdirSync, readFileSync, rmSync } from "fs";
import { dirname, join } from "path";
import { tmpdir } from "os";
import {
  bindLoggerRuntime,
  contextLogger,
  coreLogger,
  getLogFile,
  resetLoggerRuntime,
} from "./logger.js";
import { createRuntimeContext } from "./runtime-context.js";
import { createPluginRuntime } from "./index.js";

const roots = new Set<string>();
const savedWopalHome = process.env.WOPAL_HOME;
const savedLogFile = process.env.WOPAL_PLUGIN_LOG_FILE;

function makeRoot(name: string): string {
  const root = join(tmpdir(), `logger-binding-${name}-${crypto.randomUUID()}`);
  mkdirSync(root, { recursive: true });
  roots.add(root);
  return root;
}

function spaceLogFile(spaceRoot: string): string {
  return join(spaceRoot, ".wopal-space", "logs", "wopal-plugin.log");
}

afterEach(() => {
  resetLoggerRuntime();
  if (savedWopalHome !== undefined) process.env.WOPAL_HOME = savedWopalHome;
  else delete process.env.WOPAL_HOME;
  if (savedLogFile !== undefined)
    process.env.WOPAL_PLUGIN_LOG_FILE = savedLogFile;
  else delete process.env.WOPAL_PLUGIN_LOG_FILE;
  for (const root of roots) rmSync(root, { recursive: true, force: true });
  roots.clear();
});

describe("module-level logger runtime binding", () => {
  it("routes singletons to the bound runtime log dir", () => {
    const spaceRoot = makeRoot("space");
    const context = createRuntimeContext({
      directory: spaceRoot,
      wopalSpaceRoot: spaceRoot,
    });
    bindLoggerRuntime(context, { WOPAL_PLUGIN_LOG_LEVEL: "info" });

    contextLogger.info("routed-to-space");

    const logFile = spaceLogFile(spaceRoot);
    expect(existsSync(logFile)).toBe(true);
    expect(readFileSync(logFile, "utf-8")).toContain("routed-to-space");
  });

  it("never falls back to <WOPAL_HOME>/logs while a runtime is bound", () => {
    const home = makeRoot("home");
    const spaceRoot = makeRoot("space-home");
    mkdirSync(join(home, "logs"), { recursive: true });
    process.env.WOPAL_HOME = home;

    const context = createRuntimeContext({
      directory: spaceRoot,
      wopalSpaceRoot: spaceRoot,
    });
    bindLoggerRuntime(context, { WOPAL_PLUGIN_LOG_LEVEL: "info" });

    coreLogger.info("must-not-reach-home");

    expect(existsSync(join(home, "logs", "wopal-plugin.log"))).toBe(false);
    expect(readFileSync(spaceLogFile(spaceRoot), "utf-8")).toContain(
      "must-not-reach-home",
    );
  });

  it("routes to the most recently bound runtime (last writer wins)", () => {
    const spaceA = makeRoot("a");
    const spaceB = makeRoot("b");
    const contextA = createRuntimeContext({
      directory: spaceA,
      wopalSpaceRoot: spaceA,
    });
    const contextB = createRuntimeContext({
      directory: spaceB,
      wopalSpaceRoot: spaceB,
    });

    bindLoggerRuntime(contextA, { WOPAL_PLUGIN_LOG_LEVEL: "info" });
    contextLogger.info("from-a");
    bindLoggerRuntime(contextB, { WOPAL_PLUGIN_LOG_LEVEL: "info" });
    contextLogger.info("from-b");

    expect(readFileSync(spaceLogFile(spaceA), "utf-8")).toContain("from-a");
    expect(readFileSync(spaceLogFile(spaceA), "utf-8")).not.toContain("from-b");
    expect(readFileSync(spaceLogFile(spaceB), "utf-8")).toContain("from-b");
  });

  it("keeps the env-derived destination when no runtime is bound", () => {
    const logFile = join(makeRoot("fallback"), "explicit.log");
    mkdirSync(dirname(logFile), { recursive: true });
    process.env.WOPAL_PLUGIN_LOG_FILE = logFile;

    coreLogger.info("fallback-path");

    expect(readFileSync(logFile, "utf-8")).toContain("fallback-path");
  });

  it("prefers the runtime log dir over WOPAL_HOME for a non-VITEST environment", () => {
    const spaceRoot = makeRoot("resolve");
    const context = createRuntimeContext({
      directory: spaceRoot,
      wopalSpaceRoot: spaceRoot,
    });

    expect(getLogFile(context, { WOPAL_HOME: "/nonexistent/wopal-home" })).toBe(
      spaceLogFile(spaceRoot),
    );
  });

  it("is bound by createPluginRuntime (composition root wiring)", () => {
    const home = makeRoot("compose-home");
    const spaceRoot = makeRoot("compose-space");
    mkdirSync(join(spaceRoot, ".wopal"), { recursive: true });
    process.env.WOPAL_HOME = home;

    createPluginRuntime({ directory: spaceRoot, wopalSpaceRoot: spaceRoot });

    contextLogger.info("bound-by-bootstrap");

    expect(readFileSync(spaceLogFile(spaceRoot), "utf-8")).toContain(
      "bound-by-bootstrap",
    );
    expect(existsSync(join(home, "logs", "wopal-plugin.log"))).toBe(false);
  });
});

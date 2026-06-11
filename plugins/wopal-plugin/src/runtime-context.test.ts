import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { mkdirSync, rmSync } from "fs";
import path from "path";
import os from "os";
import { initRuntimeContext } from "./runtime-context.js";

describe("RuntimeContext", () => {
  let testDir: string;
  let savedWopalHome: string | undefined;
  let savedWopalSpaceRoot: string | undefined;

  beforeEach(() => {
    testDir = path.join(os.tmpdir(), `runtime-ctx-test-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`);
    mkdirSync(testDir, { recursive: true });

    savedWopalHome = process.env.WOPAL_HOME;
    delete process.env.WOPAL_HOME;

    savedWopalSpaceRoot = process.env.WOPAL_SPACE_ROOT;
    delete process.env.WOPAL_SPACE_ROOT;
  });

  afterEach(() => {
    if (savedWopalHome !== undefined) {
      process.env.WOPAL_HOME = savedWopalHome;
    } else {
      delete process.env.WOPAL_HOME;
    }
    if (savedWopalSpaceRoot !== undefined) {
      process.env.WOPAL_SPACE_ROOT = savedWopalSpaceRoot;
    } else {
      delete process.env.WOPAL_SPACE_ROOT;
    }
    if (testDir) {
      rmSync(testDir, { recursive: true, force: true });
    }
  });

  it("throws when getRuntimeContext() is called before initRuntimeContext", async () => {
    vi.resetModules();
    const { getRuntimeContext } = await import("./runtime-context.js");
    expect(() => getRuntimeContext()).toThrow("RuntimeContext not initialized");
  });

  it("uses process.env.WOPAL_HOME when set", () => {
    process.env.WOPAL_HOME = "/custom/wopal-home";
    process.env.WOPAL_SPACE_ROOT = testDir;

    const ctx = initRuntimeContext(testDir);
    expect(ctx.wopalHome).toBe("/custom/wopal-home");
  });

  it("falls back to ~/.wopal when WOPAL_HOME is not set", () => {
    process.env.WOPAL_SPACE_ROOT = testDir;

    const ctx = initRuntimeContext(testDir);
    expect(ctx.wopalHome).toBe(path.join(os.homedir(), ".wopal"));
  });

  it("returns true and sets spaceRoot when WOPAL_SPACE_ROOT is set", () => {
    process.env.WOPAL_SPACE_ROOT = testDir;

    const ctx = initRuntimeContext(testDir);
    expect(ctx.isWopalSpace).toBe(true);
    expect(ctx.spaceRoot).toBe(testDir);
  });

  it("returns false when WOPAL_SPACE_ROOT is not set", () => {
    const ctx = initRuntimeContext(testDir);
    expect(ctx.isWopalSpace).toBe(false);
    expect(ctx.spaceRoot).toBeUndefined();
  });

  it("routes to .wopal-space/logs/ inside wopal-space", () => {
    process.env.WOPAL_SPACE_ROOT = testDir;

    const ctx = initRuntimeContext(testDir);
    expect(ctx.logDir).toBe(path.join(testDir, ".wopal-space", "logs"));
  });

  it("routes to WOPAL_HOME/logs/ outside wopal-space", () => {
    const customHome = path.join(testDir, "custom-home");
    process.env.WOPAL_HOME = customHome;

    const ctx = initRuntimeContext(testDir);
    expect(ctx.logDir).toBe(path.join(customHome, "logs"));
  });

  it("stores the provided directory value", () => {
    process.env.WOPAL_SPACE_ROOT = testDir;

    const ctx = initRuntimeContext(testDir);
    expect(ctx.directory).toBe(testDir);
  });

  it("detects wopal-space even when directory differs from spaceRoot", () => {
    process.env.WOPAL_SPACE_ROOT = testDir;
    const subDir = path.join(testDir, "projects", "ellamaka");
    mkdirSync(subDir, { recursive: true });

    const ctx = initRuntimeContext(subDir);
    expect(ctx.isWopalSpace).toBe(true);
    expect(ctx.spaceRoot).toBe(testDir);
    expect(ctx.directory).toBe(subDir);
  });
});

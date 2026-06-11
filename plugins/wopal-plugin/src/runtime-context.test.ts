import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { mkdirSync, rmSync } from "fs";
import path from "path";
import os from "os";
import { initRuntimeContext } from "./runtime-context.js";

describe("RuntimeContext", () => {
  let testDir: string;
  let savedWopalHome: string | undefined;

  beforeEach(() => {
    testDir = path.join(os.tmpdir(), `runtime-ctx-test-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`);
    mkdirSync(testDir, { recursive: true });

    savedWopalHome = process.env.WOPAL_HOME;
    delete process.env.WOPAL_HOME;
  });

  afterEach(() => {
    if (savedWopalHome !== undefined) {
      process.env.WOPAL_HOME = savedWopalHome;
    } else {
      delete process.env.WOPAL_HOME;
    }
    if (testDir) {
      rmSync(testDir, { recursive: true, force: true });
    }
  });

  it("throws when getRuntimeContext() is called before initRuntimeContext", async () => {
    // Must use fresh module import to get null _context
    vi.resetModules();
    const { getRuntimeContext } = await import("./runtime-context.js");
    expect(() => getRuntimeContext()).toThrow("RuntimeContext not initialized");
  });

  it("uses process.env.WOPAL_HOME when set", () => {
    process.env.WOPAL_HOME = "/custom/wopal-home";
    mkdirSync(path.join(testDir, ".wopal"), { recursive: true });

    const ctx = initRuntimeContext(testDir);
    expect(ctx.wopalHome).toBe("/custom/wopal-home");
  });

  it("falls back to ~/.wopal when WOPAL_HOME is not set", () => {
    mkdirSync(path.join(testDir, ".wopal"), { recursive: true });

    const ctx = initRuntimeContext(testDir);
    expect(ctx.wopalHome).toBe(path.join(os.homedir(), ".wopal"));
  });

  it("returns true when .wopal/ directory exists in workspaceRoot", () => {
    mkdirSync(path.join(testDir, ".wopal"), { recursive: true });

    const ctx = initRuntimeContext(testDir);
    expect(ctx.isWopalSpace).toBe(true);
  });

  it("returns false when .wopal/ directory does not exist", () => {
    const ctx = initRuntimeContext(testDir);
    expect(ctx.isWopalSpace).toBe(false);
  });

  it("routes to .wopal-space/logs/ inside wopal-space", () => {
    mkdirSync(path.join(testDir, ".wopal"), { recursive: true });

    const ctx = initRuntimeContext(testDir);
    expect(ctx.logDir).toBe(path.join(testDir, ".wopal-space", "logs"));
  });

  it("routes to WOPAL_HOME/logs/ outside wopal-space", () => {
    const customHome = path.join(testDir, "custom-home");
    process.env.WOPAL_HOME = customHome;

    const ctx = initRuntimeContext(testDir);
    expect(ctx.logDir).toBe(path.join(customHome, "logs"));
  });

  it("stores the provided workspaceRoot value", () => {
    mkdirSync(path.join(testDir, ".wopal"), { recursive: true });

    const ctx = initRuntimeContext(testDir);
    expect(ctx.workspaceRoot).toBe(testDir);
  });
});

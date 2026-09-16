/**
 * Regression guard for the `WOPAL_HOME` path-resolution bug.
 *
 * When the ambient value was the literal, unexpanded `~/.wopal`, raw
 * `path.join` produced a *relative* path that resolved against the process cwd
 * and created a junk `~/.wopal/...` tree inside the plugin package. When the
 * value was absent, tests fell back to the developer's real `~/.wopal` and
 * polluted it.
 *
 * These assertions fail if either class of leak returns.
 */

import { describe, it, expect } from "vitest";
import { tmpdir } from "os";
import { homedir } from "os";
import { join, isAbsolute } from "path";
import { getSessionContextDir } from "./context/session-context.js";
import { getDefaultMemoryDbPath } from "./memory/store.js";
import { resolveWopalHome } from "./paths.js";

describe("WOPAL_HOME test isolation", () => {
  it("pins the ambient WOPAL_HOME to an absolute path under tmpdir", () => {
    const value = process.env.WOPAL_HOME;
    expect(value).toBeDefined();
    expect(isAbsolute(value!)).toBe(true);
    expect(value!.startsWith(tmpdir())).toBe(true);
    expect(value!.split(/[/\\]/)).not.toContain("~");
  });

  it("never routes session context into the plugin cwd", () => {
    const dir = getSessionContextDir();
    expect(isAbsolute(dir)).toBe(true);
    expect(dir.startsWith(process.cwd())).toBe(false);
  });

  it("never routes memory storage into the plugin cwd", () => {
    const dir = getDefaultMemoryDbPath();
    expect(isAbsolute(dir)).toBe(true);
    expect(dir.startsWith(process.cwd())).toBe(false);
  });

  it("never routes storage into the developer's real home", () => {
    const realHome = join(homedir(), ".wopal");
    const dir = getSessionContextDir();
    expect(dir.startsWith(realHome)).toBe(false);
    expect(getDefaultMemoryDbPath().startsWith(realHome)).toBe(false);
  });

  it("absolutises a literal tilde value instead of treating it as relative", () => {
    const wopalHome = resolveWopalHome("~/.wopal");
    expect(isAbsolute(wopalHome)).toBe(true);
    expect(join(wopalHome, "storage").startsWith(process.cwd())).toBe(false);
  });
});

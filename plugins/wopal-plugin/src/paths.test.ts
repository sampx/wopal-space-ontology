import { describe, it, expect } from "vitest";
import { join, resolve } from "path";
import { homedir } from "os";
import { resolveWopalHome } from "./paths.js";

describe("resolveWopalHome", () => {
  it("expands a leading ~ into the user home", () => {
    expect(resolveWopalHome("~/.wopal")).toBe(join(homedir(), ".wopal"));
  });

  it("expands a bare ~ into the user home", () => {
    expect(resolveWopalHome("~")).toBe(homedir());
  });

  it("expands ~/sub/dir without leaving a literal tilde segment", () => {
    const resolved = resolveWopalHome("~/sub/dir");
    expect(resolved).toBe(join(homedir(), "sub", "dir"));
    expect(resolved.includes("~")).toBe(false);
  });

  it("does not expand a tilde that is not a leading segment", () => {
    expect(resolveWopalHome("/opt/~weird/.wopal")).toBe("/opt/~weird/.wopal");
  });

  it("keeps an absolute path as-is", () => {
    expect(resolveWopalHome("/custom/wopal-home")).toBe("/custom/wopal-home");
  });

  it("absolutises a relative path against the current working directory", () => {
    expect(resolveWopalHome("relative/wopal-home")).toBe(
      resolve(process.cwd(), "relative/wopal-home"),
    );
  });

  it("falls back to <home>/.wopal when the value is undefined", () => {
    expect(resolveWopalHome(undefined)).toBe(join(homedir(), ".wopal"));
  });

  it("falls back to <home>/.wopal when the value is empty", () => {
    expect(resolveWopalHome("")).toBe(join(homedir(), ".wopal"));
  });

  it("falls back to <home>/.wopal when the value is whitespace only", () => {
    expect(resolveWopalHome("   ")).toBe(join(homedir(), ".wopal"));
  });

  it("trims surrounding whitespace before resolving", () => {
    expect(resolveWopalHome("  /custom/wopal-home  ")).toBe(
      "/custom/wopal-home",
    );
  });

  it("never returns a value containing a leading literal tilde segment", () => {
    for (const input of ["~/.wopal", "~", "~/a/b", "~/wopal/"]) {
      expect(resolveWopalHome(input).startsWith("~")).toBe(false);
    }
  });
});

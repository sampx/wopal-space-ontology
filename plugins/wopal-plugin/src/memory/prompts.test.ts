import { afterEach, describe, expect, it } from "vitest";
import { mkdirSync, rmSync, writeFileSync } from "fs";
import { join } from "path";
import { tmpdir } from "os";
import { createRuntimeContext } from "../runtime-context.js";
import { createMemoryPrompts } from "./prompts.js";

describe("createMemoryPrompts", () => {
  const roots: string[] = [];

  afterEach(() => {
    for (const root of roots.splice(0))
      rmSync(root, { recursive: true, force: true });
  });

  it("uses the user-level prompt file when the plugin ships no override", () => {
    const root = join(tmpdir(), `wopal-prompts-${crypto.randomUUID()}`);
    const home = join(root, "home");
    const space = join(root, "space");
    roots.push(root);
    mkdirSync(join(space, ".wopal"), { recursive: true });
    mkdirSync(join(home, "prompts"), { recursive: true });
    // The plugin ships `dedup.md`, so use a filename it does not provide.
    writeFileSync(join(home, "prompts", "dedup-custom.md"), "home-dedup");

    const context = createRuntimeContext({
      directory: space,
      wopalHome: home,
      wopalSpaceRoot: space,
    });

    expect(context.pluginRoot).toBeTruthy();
    expect(createMemoryPrompts(context).resolvePromptFile("dedup-custom.md")).toBe(
      join(home, "prompts", "dedup-custom.md"),
    );
  });

  it("prefers the plugin-shipped prompt over the user-level file", () => {
    const root = join(tmpdir(), `wopal-prompts-${crypto.randomUUID()}`);
    const home = join(root, "home");
    const space = join(root, "space");
    roots.push(root);
    mkdirSync(join(space, ".wopal"), { recursive: true });
    mkdirSync(join(home, "prompts"), { recursive: true });
    writeFileSync(join(home, "prompts", "dedup.md"), "home-dedup");

    const context = createRuntimeContext({
      directory: space,
      wopalHome: home,
      wopalSpaceRoot: space,
    });

    expect(createMemoryPrompts(context).resolvePromptFile("dedup.md")).toBe(
      join(context.pluginRoot, "prompts", "dedup.md"),
    );
  });
});

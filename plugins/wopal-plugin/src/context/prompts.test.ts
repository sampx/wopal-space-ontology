import { afterEach, describe, expect, it } from "vitest";
import { mkdirSync, rmSync, writeFileSync } from "fs";
import { join } from "path";
import { tmpdir } from "os";
import { createRuntimeContext } from "../runtime-context.js";
import { createContextPrompts, loadTitlePrompt } from "./prompts.js";

describe("createContextPrompts", () => {
  const roots: string[] = [];

  afterEach(() => {
    for (const root of roots.splice(0))
      rmSync(root, { recursive: true, force: true });
  });

  it("resolves the user-level prompt for every invocation context", () => {
    const root = join(tmpdir(), `wopal-prompts-${crypto.randomUUID()}`);
    const home = join(root, "home");
    const spaceA = join(root, "a");
    const spaceB = join(root, "b");
    roots.push(root);
    for (const directory of [join(home, "prompts"), spaceA, spaceB]) {
      mkdirSync(directory, { recursive: true });
    }
    writeFileSync(join(home, "prompts", "title.md"), "home");

    const promptsA = createContextPrompts(
      createRuntimeContext({
        directory: spaceA,
        wopalHome: home,
        wopalSpaceRoot: spaceA,
      }),
    );
    const promptsB = createContextPrompts(
      createRuntimeContext({
        directory: spaceB,
        wopalHome: home,
        wopalSpaceRoot: spaceB,
      }),
    );
    const promptsGlobal = createContextPrompts(
      createRuntimeContext({ directory: root, wopalHome: home }),
    );

    expect(promptsA.loadTitlePrompt()).toBe("home");
    expect(promptsB.loadTitlePrompt()).toBe("home");
    expect(promptsGlobal.loadTitlePrompt()).toBe("home");
  });

  it("ignores a space-level prompt file", () => {
    const root = join(tmpdir(), `wopal-prompts-${crypto.randomUUID()}`);
    const home = join(root, "home");
    const space = join(root, "space");
    roots.push(root);
    mkdirSync(join(space, ".wopal", "prompts"), { recursive: true });
    mkdirSync(join(home, "prompts"), { recursive: true });
    writeFileSync(
      join(space, ".wopal", "prompts", "distill.md"),
      "space-distill",
    );

    const context = createRuntimeContext({
      directory: space,
      wopalHome: home,
      wopalSpaceRoot: space,
    });

    // A space-level file must never be picked up: the plugin ships its own
    // `distill.md`, and the space layer is not part of the resolution chain.
    expect(createContextPrompts(context).resolvePromptFile("distill.md")).toBe(
      join(context.pluginRoot, "prompts", "distill.md"),
    );
  });

  it("resolves the plugin-level prompt ahead of the user-level prompt", () => {
    const root = join(tmpdir(), `wopal-prompts-${crypto.randomUUID()}`);
    const home = join(root, "home");
    roots.push(root);
    mkdirSync(join(home, "prompts"), { recursive: true });
    writeFileSync(join(home, "prompts", "title.md"), "home-title");

    // The plugin root is fixed by the module location, so write the
    // plugin-level override where the resolver actually looks for it.
    const context = createRuntimeContext({ directory: root, wopalHome: home });
    const pluginPrompts = join(context.pluginRoot, "prompts");
    mkdirSync(pluginPrompts, { recursive: true });
    const pluginTitle = join(pluginPrompts, "title.md");
    writeFileSync(pluginTitle, "plugin-title");

    try {
      expect(createContextPrompts(context).loadTitlePrompt()).toBe(
        "plugin-title",
      );
    } finally {
      rmSync(pluginTitle, { force: true });
    }
  });

  it("uses the inline default when neither level provides the file", () => {
    const root = join(tmpdir(), `wopal-prompts-${crypto.randomUUID()}`);
    const home = join(root, "home");
    const space = join(root, "space");
    roots.push(root);
    mkdirSync(join(space, ".wopal"), { recursive: true });
    mkdirSync(home, { recursive: true });

    const prompts = createContextPrompts(
      createRuntimeContext({
        directory: space,
        wopalHome: home,
        wopalSpaceRoot: space,
      }),
    );

    expect(prompts.loadTitlePrompt()).toContain("{{summary}}");
    expect(prompts.buildExtractionPrompt("hello")).toContain("hello");
  });

  it("loads prompt files lazily on first consumer call", () => {
    const root = join(tmpdir(), `wopal-prompts-${crypto.randomUUID()}`);
    const home = join(root, "home");
    const space = join(root, "space");
    roots.push(root);
    mkdirSync(join(space, ".wopal"), { recursive: true });
    mkdirSync(join(home, "prompts"), { recursive: true });

    const prompts = createContextPrompts(
      createRuntimeContext({
        directory: space,
        wopalHome: home,
        wopalSpaceRoot: space,
      }),
    );

    const titlePath = join(home, "prompts", "title.md");
    const distillPath = join(home, "prompts", "distill.md");
    expect(prompts.loadTitlePrompt()).toContain("{{summary}}");
    expect(prompts.buildExtractionPrompt("hello")).toContain("hello");

    writeFileSync(titlePath, "lazy-title");
    writeFileSync(distillPath, "lazy-distill");
    expect(prompts.loadTitlePrompt()).toContain("{{summary}}");
    expect(prompts.buildExtractionPrompt("hello")).toContain("hello");
  });

  it("caches prompt content after the first load", () => {
    const root = join(tmpdir(), `wopal-prompts-${crypto.randomUUID()}`);
    const home = join(root, "home");
    const space = join(root, "space");
    roots.push(root);
    mkdirSync(join(space, ".wopal"), { recursive: true });
    mkdirSync(join(home, "prompts"), { recursive: true });
    writeFileSync(join(home, "prompts", "title.md"), "cached-title");

    const prompts = createContextPrompts(
      createRuntimeContext({
        directory: space,
        wopalHome: home,
        wopalSpaceRoot: space,
      }),
    );

    expect(prompts.loadTitlePrompt()).toBe("cached-title");
    rmSync(join(home, "prompts", "title.md"));
    expect(prompts.loadTitlePrompt()).toBe("cached-title");

    const freshPrompts = createContextPrompts(
      createRuntimeContext({
        directory: space,
        wopalHome: home,
        wopalSpaceRoot: space,
      }),
    );
    expect(freshPrompts.loadTitlePrompt()).toContain("{{summary}}");
  });

  it("builds the shared default prompts lazily on first call", () => {
    const root = join(tmpdir(), `wopal-prompts-${crypto.randomUUID()}`);
    const home = join(root, "home");
    roots.push(root);
    mkdirSync(join(home, "prompts"), { recursive: true });

    const savedHome = process.env.WOPAL_HOME;
    process.env.WOPAL_HOME = home;
    try {
      expect(loadTitlePrompt()).toContain("{{summary}}");

      writeFileSync(join(home, "prompts", "title.md"), "lazy-shared");
      expect(loadTitlePrompt()).toContain("{{summary}}");
    } finally {
      if (savedHome === undefined) delete process.env.WOPAL_HOME;
      else process.env.WOPAL_HOME = savedHome;
    }
  });
});

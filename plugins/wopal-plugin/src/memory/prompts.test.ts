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

  it("falls back to the user-level prompt file when the space level is missing", () => {
    const root = join(tmpdir(), `wopal-prompts-${crypto.randomUUID()}`);
    const home = join(root, "home");
    const space = join(root, "space");
    roots.push(root);
    mkdirSync(join(space, ".wopal"), { recursive: true });
    mkdirSync(join(home, "prompts"), { recursive: true });
    writeFileSync(join(home, "prompts", "dedup.md"), "home-dedup");

    const prompts = createMemoryPrompts(
      createRuntimeContext({
        directory: space,
        wopalHome: home,
        wopalSpaceRoot: space,
      }),
    );
    const dedupPrompt = prompts.buildBatchDedupPrompt(
      [{ index: 1, category: "knowledge", body: "candidate" }],
      new Map([[1, [{ index: 1, body: "existing", id: "m1" }]]]),
    );

    expect(dedupPrompt).toContain("home-dedup");
  });
});

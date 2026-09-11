import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { mkdirSync, rmSync, writeFileSync } from "fs";
import { join } from "path";
import { tmpdir } from "os";
import { createPluginRuntime } from "./index.js";
import { LLMClient } from "./llm-client.js";
import { EmbeddingClient } from "./memory/embedder.js";
import { getDefaultMemoryDbPath } from "./memory/store.js";
import { getSessionContextDir } from "./context/session-context.js";

describe("plugin runtime isolation", () => {
  const keys = [
    "WOPAL_HOME",
    "WOPAL_LLM_BASE_URL",
    "WOPAL_LLM_MODEL",
    "WOPAL_LLM_API_KEY",
    "WOPAL_EMBEDDING_BASE_URL",
    "WOPAL_EMBEDDING_MODEL",
    "WOPAL_EMBEDDING_API_KEY",
  ] as const;
  const saved = new Map<string, string | undefined>();
  let root: string;

  beforeEach(() => {
    root = join(tmpdir(), `wopal-runtime-isolation-${crypto.randomUUID()}`);
    mkdirSync(root, { recursive: true });
    for (const key of keys) {
      saved.set(key, process.env[key]);
      delete process.env[key];
    }
    process.env.WOPAL_HOME = join(root, "home");
    mkdirSync(process.env.WOPAL_HOME, { recursive: true });
  });

  afterEach(() => {
    for (const key of keys) {
      const value = saved.get(key);
      if (value === undefined) delete process.env[key];
      else process.env[key] = value;
    }
    saved.clear();
    rmSync(root, { recursive: true, force: true });
  });

  function createSpace(name: string, key: string) {
    const spaceRoot = join(root, name);
    mkdirSync(join(spaceRoot, ".wopal"), { recursive: true });
    writeFileSync(
      join(spaceRoot, ".wopal", ".env"),
      [
        "WOPAL_LLM_BASE_URL=http://llm.invalid",
        `WOPAL_LLM_API_KEY=${key}`,
        "WOPAL_EMBEDDING_BASE_URL=http://embedding.invalid",
        "WOPAL_EMBEDDING_API_KEY=test",
      ].join("\n"),
    );
    return { directory: join(spaceRoot, "project"), wopalSpaceRoot: spaceRoot };
  }

  it("keeps roots, env, prompts, and clients isolated in any order", () => {
    const inputA = createSpace("a", "key-a");
    const inputB = createSpace("b", "key-b");

    const runtimeB = createPluginRuntime(inputB);
    const runtimeA = createPluginRuntime(inputA);
    const llmA = new LLMClient(
      { ...runtimeA.env, WOPAL_LLM_BASE_URL: "http://llm.invalid" },
      runtimeA.loggers.core,
    );
    const llmB = new LLMClient(
      { ...runtimeB.env, WOPAL_LLM_BASE_URL: "http://llm.invalid" },
      runtimeB.loggers.core,
    );
    const embeddingA = new EmbeddingClient(
      {
        ...runtimeA.env,
        WOPAL_EMBEDDING_BASE_URL: "http://embedding.invalid",
        WOPAL_EMBEDDING_MODEL: "embedding-model",
      },
      runtimeA.loggers.memory,
    );
    const embeddingB = new EmbeddingClient(
      {
        ...runtimeB.env,
        WOPAL_EMBEDDING_BASE_URL: "http://embedding.invalid",
        WOPAL_EMBEDDING_MODEL: "embedding-model",
      },
      runtimeB.loggers.memory,
    );

    expect(runtimeA.context.wopalSpaceRoot).toBe(inputA.wopalSpaceRoot);
    expect(runtimeB.context.wopalSpaceRoot).toBe(inputB.wopalSpaceRoot);
    expect(llmA.getModel()).toBe("gpt-4o-mini");
    expect(llmB.getModel()).toBe("gpt-4o-mini");
    expect(embeddingA.getModel()).toBe("embedding-model");
    expect(embeddingB.getModel()).toBe("embedding-model");
    expect(runtimeA.env.WOPAL_LLM_API_KEY).toBe("key-a");
    expect(runtimeB.env.WOPAL_LLM_API_KEY).toBe("key-b");
    expect(process.env.WOPAL_LLM_API_KEY).toBeUndefined();
  });

  it("creates independent runtimes concurrently", async () => {
    const inputA = createSpace("a", "key-a");
    const inputB = createSpace("b", "key-b");

    const [runtimeA, runtimeB, runtimeGlobal] = await Promise.all([
      Promise.resolve().then(() => createPluginRuntime(inputA)),
      Promise.resolve().then(() => createPluginRuntime(inputB)),
      Promise.resolve().then(() => createPluginRuntime({ directory: root })),
    ]);

    expect(runtimeA.env.WOPAL_LLM_API_KEY).toBe("key-a");
    expect(runtimeB.env.WOPAL_LLM_API_KEY).toBe("key-b");
    expect(runtimeGlobal.env.WOPAL_LLM_API_KEY).toBeUndefined();
    expect(runtimeGlobal.context.wopalSpaceRoot).toBeUndefined();
  });

  it("keeps memory storage under WOPAL_HOME", () => {
    const wopalHome = join(root, "home");
    expect(getDefaultMemoryDbPath(wopalHome)).toBe(
      join(wopalHome, "storage", "memory"),
    );
    expect(getSessionContextDir(wopalHome)).toBe(
      join(wopalHome, "storage", "session_context"),
    );
  });
});

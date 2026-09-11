import { describe, expect, it } from "vitest";
import {
  resolveResources,
  type ResourceFactories,
  type ResourceRuntime,
  type StoreResourceDeps,
} from "./index.js";
import { createLLMResource, type LLMResourceDeps } from "./llm-resource.js";
import {
  createEmbeddingResource,
  type EmbeddingResourceDeps,
} from "./embedding-resource.js";
import type { WopalPluginConfig } from "../config/index.js";
import type { MemoryStore } from "../memory/store.js";
import type { EmbeddingClient } from "../memory/embedder.js";
import type { LLMClient } from "../llm-client.js";
import { createRuntimeContext } from "../runtime-context.js";
import type { LoggerInstance } from "../logger.js";

function noopLogger(): LoggerInstance {
  const noop = (): void => {};
  return {
    trace: noop,
    debug: noop,
    info: noop,
    warn: noop,
    error: noop,
    fatal: noop,
  };
}

function recordingLogger(): {
  logger: LoggerInstance;
  warns: Record<string, unknown>[];
} {
  const warns: Record<string, unknown>[] = [];
  const noop = (): void => {};
  const warn = (data: string | Record<string, unknown>): void => {
    if (typeof data === "object") warns.push(data);
  };
  return {
    logger: {
      trace: noop,
      debug: noop,
      info: noop,
      warn,
      error: noop,
      fatal: noop,
    },
    warns,
  };
}

function createRuntime(env?: Record<string, string>): {
  runtime: ResourceRuntime;
  coreWarns: Record<string, unknown>[];
  memoryWarns: Record<string, unknown>[];
} {
  const core = recordingLogger();
  const memory = recordingLogger();
  return {
    runtime: {
      context: createRuntimeContext({
        directory: "/wopal-test/space/project",
        wopalHome: "/wopal-test/home",
      }),
      env: env ?? {},
      loggers: { core: core.logger, memory: memory.logger },
    },
    coreWarns: core.warns,
    memoryWarns: memory.warns,
  };
}

interface FactoryCalls {
  store: number;
  embedder: number;
  llm: number;
}

function spyFactories(
  failures: { store?: Error; embedder?: Error; llm?: Error } = {},
): {
  factories: ResourceFactories;
  calls: FactoryCalls;
  deps: {
    store: StoreResourceDeps[];
    embedder: EmbeddingResourceDeps[];
    llm: LLMResourceDeps[];
  };
} {
  const calls: FactoryCalls = { store: 0, embedder: 0, llm: 0 };
  const deps = {
    store: [] as StoreResourceDeps[],
    embedder: [] as EmbeddingResourceDeps[],
    llm: [] as LLMResourceDeps[],
  };
  const factories: ResourceFactories = {
    createStore: (input) => {
      calls.store += 1;
      deps.store.push(input);
      if (failures.store) throw failures.store;
      return Promise.resolve({} as MemoryStore);
    },
    createEmbedder: (input) => {
      calls.embedder += 1;
      deps.embedder.push(input);
      if (failures.embedder) throw failures.embedder;
      return Promise.resolve({} as EmbeddingClient);
    },
    createLLM: (input) => {
      calls.llm += 1;
      deps.llm.push(input);
      if (failures.llm) throw failures.llm;
      return Promise.resolve({} as LLMClient);
    },
  };
  return { factories, calls, deps };
}

function buildConfig(
  switches: {
    memory?: boolean;
    context?: boolean;
    withEmbedding?: boolean;
    withLlm?: boolean;
  } = {},
): WopalPluginConfig {
  return {
    memory: { enabled: switches.memory ?? false, injection: true },
    context: { enabled: switches.context ?? false },
    ...(switches.withLlm === false
      ? {}
      : {
          llm: {
            baseUrl: "http://llm.invalid",
            model: "llm-model",
            apiKey: "cfg-llm-key",
          },
        }),
    ...(switches.withEmbedding === false
      ? {}
      : {
          embedding: {
            baseUrl: "http://embedding.invalid",
            model: "embedding-model",
          },
        }),
  };
}

describe("resolveResources", () => {
  it("constructs no resources when memory and context are disabled", async () => {
    const { runtime } = createRuntime();
    const { factories, calls } = spyFactories();

    const resources = await resolveResources(buildConfig(), runtime, factories);

    expect(calls).toEqual({ store: 0, embedder: 0, llm: 0 });
    expect(resources.store).toBeUndefined();
    expect(resources.embedder).toBeUndefined();
    expect(resources.llm).toBeUndefined();
  });

  it("constructs store and embedder only when memory is enabled", async () => {
    const { runtime } = createRuntime();
    const { factories, calls } = spyFactories();

    const resources = await resolveResources(
      buildConfig({ memory: true }),
      runtime,
      factories,
    );

    expect(calls).toEqual({ store: 1, embedder: 1, llm: 0 });
    expect(resources.store).toBeDefined();
    expect(resources.embedder).toBeDefined();
    expect(resources.llm).toBeUndefined();
  });

  it("constructs llm only when context is enabled", async () => {
    const { runtime } = createRuntime();
    const { factories, calls } = spyFactories();

    const resources = await resolveResources(
      buildConfig({ context: true }),
      runtime,
      factories,
    );

    expect(calls).toEqual({ store: 0, embedder: 0, llm: 1 });
    expect(resources.llm).toBeDefined();
    expect(resources.store).toBeUndefined();
    expect(resources.embedder).toBeUndefined();
  });

  it("constructs all resources when memory and context are enabled", async () => {
    const { runtime } = createRuntime();
    const { factories, calls, deps } = spyFactories();
    const config = buildConfig({ memory: true, context: true });

    const resources = await resolveResources(config, runtime, factories);

    expect(calls).toEqual({ store: 1, embedder: 1, llm: 1 });
    expect(resources.store).toBeDefined();
    expect(resources.embedder).toBeDefined();
    expect(resources.llm).toBeDefined();
    expect(deps.store[0]?.wopalHome).toBe(runtime.context.wopalHome);
    expect(deps.embedder[0]?.baseUrl).toBe("http://embedding.invalid");
    expect(deps.embedder[0]?.model).toBe("embedding-model");
    expect(deps.embedder[0]?.apiKey).toBeUndefined();
    expect(deps.llm[0]?.baseUrl).toBe("http://llm.invalid");
    expect(deps.llm[0]?.model).toBe("llm-model");
    expect(deps.llm[0]?.apiKey).toBe("cfg-llm-key");
  });

  it("constructs store and embedder from environment when embedding config is missing", async () => {
    const { runtime } = createRuntime({
      WOPAL_EMBEDDING_BASE_URL: "http://env.invalid",
      WOPAL_EMBEDDING_MODEL: "env-model",
      WOPAL_EMBEDDING_API_KEY: "env-key",
    });
    const { factories, calls, deps } = spyFactories();
    const config = buildConfig({
      memory: true,
      context: true,
      withEmbedding: false,
    });

    const resources = await resolveResources(config, runtime, factories);

    expect(calls).toEqual({ store: 1, embedder: 1, llm: 1 });
    expect(resources.store).toBeDefined();
    expect(resources.embedder).toBeDefined();
    expect(resources.llm).toBeDefined();
    expect(deps.embedder[0]?.baseUrl).toBeUndefined();
    expect(deps.embedder[0]?.model).toBeUndefined();
    expect(deps.embedder[0]?.environment.WOPAL_EMBEDDING_BASE_URL).toBe(
      "http://env.invalid",
    );
    expect(deps.embedder[0]?.environment.WOPAL_EMBEDDING_MODEL).toBe(
      "env-model",
    );
  });

  it("constructs llm from environment when llm config is missing", async () => {
    const { runtime } = createRuntime({
      WOPAL_LLM_BASE_URL: "http://env.invalid",
      WOPAL_LLM_API_KEY: "env-key",
    });
    const { factories, calls, deps } = spyFactories();
    const config = buildConfig({ memory: true, context: true, withLlm: false });

    const resources = await resolveResources(config, runtime, factories);

    expect(calls).toEqual({ store: 1, embedder: 1, llm: 1 });
    expect(resources.llm).toBeDefined();
    expect(resources.store).toBeDefined();
    expect(resources.embedder).toBeDefined();
    expect(deps.llm[0]?.baseUrl).toBeUndefined();
    expect(deps.llm[0]?.model).toBeUndefined();
    expect(deps.llm[0]?.environment.WOPAL_LLM_BASE_URL).toBe(
      "http://env.invalid",
    );
  });

  it("prefers config over environment for embedding overrides", async () => {
    const { runtime } = createRuntime({
      WOPAL_EMBEDDING_BASE_URL: "http://env.invalid",
      WOPAL_EMBEDDING_MODEL: "env-model",
      WOPAL_EMBEDDING_API_KEY: "env-key",
    });
    const { factories, calls, deps } = spyFactories();
    const config: WopalPluginConfig = {
      memory: { enabled: true, injection: true },
      context: { enabled: false },
      embedding: {
        baseUrl: "http://config.invalid",
        model: "config-model",
        apiKey: "config-key",
      },
    };

    await resolveResources(config, runtime, factories);

    expect(calls.embedder).toBe(1);
    expect(deps.embedder[0]?.baseUrl).toBe("http://config.invalid");
    expect(deps.embedder[0]?.model).toBe("config-model");
    expect(deps.embedder[0]?.apiKey).toBe("config-key");
    expect(deps.embedder[0]?.environment.WOPAL_EMBEDDING_BASE_URL).toBe(
      "http://env.invalid",
    );
  });

  it("prefers config over environment for llm overrides", async () => {
    const { runtime } = createRuntime({
      WOPAL_LLM_BASE_URL: "http://env.invalid",
      WOPAL_LLM_MODEL: "env-model",
      WOPAL_LLM_API_KEY: "env-key",
    });
    const { factories, calls, deps } = spyFactories();
    const config: WopalPluginConfig = {
      memory: { enabled: false, injection: true },
      context: { enabled: true },
      llm: {
        baseUrl: "http://config.invalid",
        model: "config-model",
        apiKey: "config-key",
      },
    };

    await resolveResources(config, runtime, factories);

    expect(calls.llm).toBe(1);
    expect(deps.llm[0]?.baseUrl).toBe("http://config.invalid");
    expect(deps.llm[0]?.model).toBe("config-model");
    expect(deps.llm[0]?.apiKey).toBe("config-key");
    expect(deps.llm[0]?.environment.WOPAL_LLM_BASE_URL).toBe(
      "http://env.invalid",
    );
  });

  it("degrades embedder and llm when neither config nor environment provides required settings", async () => {
    const { runtime, coreWarns, memoryWarns } = createRuntime();
    const { factories, calls } = spyFactories({
      embedder: new Error(
        "EmbeddingClient requires WOPAL_EMBEDDING_BASE_URL environment variable",
      ),
      llm: new Error(
        "LLMClient requires WOPAL_LLM_BASE_URL and WOPAL_LLM_API_KEY environment variables",
      ),
    });
    const config = buildConfig({
      memory: true,
      context: true,
      withEmbedding: false,
      withLlm: false,
    });

    const resources = await resolveResources(config, runtime, factories);

    expect(calls).toEqual({ store: 1, embedder: 1, llm: 1 });
    expect(resources.store).toBeDefined();
    expect(resources.embedder).toBeUndefined();
    expect(resources.llm).toBeUndefined();
    expect(memoryWarns.some((warn) => "err" in warn)).toBe(true);
    expect(coreWarns.some((warn) => "err" in warn)).toBe(true);
  });

  it("keeps other resources when the store factory fails", async () => {
    const { runtime, memoryWarns } = createRuntime();
    const { factories, calls } = spyFactories({
      store: new Error("store boom"),
    });

    const resources = await resolveResources(
      buildConfig({ memory: true, context: true }),
      runtime,
      factories,
    );

    expect(calls).toEqual({ store: 1, embedder: 1, llm: 1 });
    expect(resources.store).toBeUndefined();
    expect(resources.embedder).toBeDefined();
    expect(resources.llm).toBeDefined();
    expect(memoryWarns.some((warn) => "err" in warn)).toBe(true);
  });

  it("keeps store when the embedder factory fails", async () => {
    const { runtime } = createRuntime();
    const { factories, calls } = spyFactories({
      embedder: new Error("embedder boom"),
    });

    const resources = await resolveResources(
      buildConfig({ memory: true, context: true }),
      runtime,
      factories,
    );

    expect(calls).toEqual({ store: 1, embedder: 1, llm: 1 });
    expect(resources.embedder).toBeUndefined();
    expect(resources.store).toBeDefined();
    expect(resources.llm).toBeDefined();
  });

  it("keeps store and embedder when the llm factory fails", async () => {
    const { runtime, coreWarns } = createRuntime();
    const { factories, calls } = spyFactories({ llm: new Error("llm boom") });

    const resources = await resolveResources(
      buildConfig({ memory: true, context: true }),
      runtime,
      factories,
    );

    expect(calls).toEqual({ store: 1, embedder: 1, llm: 1 });
    expect(resources.llm).toBeUndefined();
    expect(resources.store).toBeDefined();
    expect(resources.embedder).toBeDefined();
    expect(coreWarns.some((warn) => "err" in warn)).toBe(true);
  });
});

describe("resource client mapping", () => {
  it("maps llm config onto the client with config precedence over environment", () => {
    const client = createLLMResource({
      baseUrl: "http://config.invalid",
      model: "config-model",
      environment: {
        WOPAL_LLM_BASE_URL: "http://env.invalid",
        WOPAL_LLM_MODEL: "env-model",
        WOPAL_LLM_API_KEY: "env-key",
      },
      logger: noopLogger(),
    });

    expect(client.getModel()).toBe("config-model");
  });

  it("keeps the environment endpoint when no llm config overrides are provided", () => {
    const client = createLLMResource({
      environment: {
        WOPAL_LLM_BASE_URL: "http://env.invalid",
        WOPAL_LLM_API_KEY: "env-key",
      },
      logger: noopLogger(),
    });

    expect(client.getModel()).toBe("gpt-4o-mini");
  });

  it("maps embedding config onto the client and keeps environment api key fallback", () => {
    const client = createEmbeddingResource({
      baseUrl: "http://config.invalid",
      model: "config-model",
      environment: { WOPAL_EMBEDDING_API_KEY: "env-key" },
      logger: noopLogger(),
    });

    expect(client.getModel()).toBe("config-model");
  });

  it("keeps the environment endpoint when no embedding config overrides are provided", () => {
    const client = createEmbeddingResource({
      environment: {
        WOPAL_EMBEDDING_BASE_URL: "http://env.invalid",
        WOPAL_EMBEDDING_MODEL: "env-model",
      },
      logger: noopLogger(),
    });

    expect(client.getModel()).toBe("env-model");
  });
});

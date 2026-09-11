import type { WopalPluginConfig } from "../config/index.js";
import type { MemoryStore } from "../memory/store.js";
import type { EmbeddingClient } from "../memory/embedder.js";
import type { LLMClient } from "../llm-client.js";
import type { RuntimeContext } from "../runtime-context.js";
import type { RuntimeEnvironment } from "../runtime-environment.js";
import type { LoggerInstance } from "../logger.js";
import {
  createEmbeddingResource,
  type EmbeddingResourceDeps,
} from "./embedding-resource.js";
import { createLLMResource, type LLMResourceDeps } from "./llm-resource.js";

export interface PluginResources {
  store?: MemoryStore;
  embedder?: EmbeddingClient;
  llm?: LLMClient;
}

export interface ResourceRuntime {
  context: RuntimeContext;
  env: RuntimeEnvironment;
  loggers: {
    core: LoggerInstance;
    memory: LoggerInstance;
  };
}

export interface StoreResourceDeps {
  wopalHome: string;
  logger: LoggerInstance;
}

export type StoreFactory = (
  deps: StoreResourceDeps,
) => MemoryStore | Promise<MemoryStore>;

export type EmbedderFactory = (
  deps: EmbeddingResourceDeps,
) => EmbeddingClient | Promise<EmbeddingClient>;

export type LLMFactory = (
  deps: LLMResourceDeps,
) => LLMClient | Promise<LLMClient>;

export interface ResourceFactories {
  createStore: StoreFactory;
  createEmbedder: EmbedderFactory;
  createLLM: LLMFactory;
}

export const defaultResourceFactories: ResourceFactories = {
  createStore: async ({ wopalHome, logger }) => {
    const { MemoryStore } = await import("../memory/store.js");
    const store = new MemoryStore(undefined, wopalHome, logger);
    await store.init();
    return store;
  },
  createEmbedder: (deps) => createEmbeddingResource(deps),
  createLLM: (deps) => createLLMResource(deps),
};

function toError(error: unknown): Error {
  return error instanceof Error ? error : new Error(String(error));
}

async function attempt<T>(
  task: () => T | Promise<T>,
  onError: (err: Error) => void,
): Promise<{ value?: T }> {
  try {
    return { value: await task() };
  } catch (error) {
    onError(toError(error));
    return {};
  }
}

async function createMemoryResources(
  config: WopalPluginConfig,
  runtime: ResourceRuntime,
  factories: ResourceFactories,
): Promise<{ store?: MemoryStore; embedder?: EmbeddingClient }> {
  const { memory } = runtime.loggers;
  if (!config.memory.enabled) {
    return {};
  }
  const embeddingConfig = config.embedding;

  const [store, embedder] = await Promise.all([
    attempt(
      () =>
        factories.createStore({
          wopalHome: runtime.context.wopalHome,
          logger: memory,
        }),
      (err) =>
        memory.warn({ err }, "Memory store initialization failed (non-fatal)"),
    ),
    attempt(
      () =>
        factories.createEmbedder({
          ...(embeddingConfig !== undefined
            ? {
                baseUrl: embeddingConfig.baseUrl,
                model: embeddingConfig.model,
                ...(embeddingConfig.apiKey !== undefined
                  ? { apiKey: embeddingConfig.apiKey }
                  : {}),
              }
            : {}),
          environment: runtime.env,
          logger: memory,
        }),
      (err) =>
        memory.warn(
          { err },
          "Embedding client initialization failed (non-fatal)",
        ),
    ),
  ]);
  return {
    ...(store.value !== undefined ? { store: store.value } : {}),
    ...(embedder.value !== undefined ? { embedder: embedder.value } : {}),
  };
}

async function createContextResources(
  config: WopalPluginConfig,
  runtime: ResourceRuntime,
  factories: ResourceFactories,
): Promise<{ llm?: LLMClient }> {
  const { core } = runtime.loggers;
  if (!config.context.enabled) {
    return {};
  }
  const llmConfig = config.llm;

  const { value } = await attempt(
    () =>
      factories.createLLM({
        ...(llmConfig !== undefined
          ? {
              baseUrl: llmConfig.baseUrl,
              model: llmConfig.model,
              ...(llmConfig.apiKey !== undefined
                ? { apiKey: llmConfig.apiKey }
                : {}),
            }
          : {}),
        environment: runtime.env,
        logger: core,
      }),
    (err) =>
      core.warn({ err }, "LLM resource initialization failed (non-fatal)"),
  );
  return { ...(value !== undefined ? { llm: value } : {}) };
}

export async function resolveResources(
  config: WopalPluginConfig,
  runtime: ResourceRuntime,
  factories: ResourceFactories = defaultResourceFactories,
): Promise<PluginResources> {
  const [memoryResources, contextResources] = await Promise.all([
    createMemoryResources(config, runtime, factories),
    createContextResources(config, runtime, factories),
  ]);
  return { ...memoryResources, ...contextResources };
}

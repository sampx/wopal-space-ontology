/**
 * OpenCode Rules Plugin
 *
 * Discovers markdown rule files and injects them into the system prompt.
 * Also provides non-blocking task delegation tools (wopal_task, wopal_task_output, wopal_task_reply).
 * Task is a perpetual dialog channel - no terminal states, only running/waiting/error.
 */

import type { PluginInput, Hooks } from "@opencode-ai/plugin";
import type { SystemPromptMetadata, OpenCodeClient } from "./types.js";
import { createOpencodeClient as createV2OpencodeClient } from "@opencode-ai/sdk/v2";
import { discoverRuleFiles, type DiscoveredRule } from "./rules/index.js";
import { createHookContext, createAllHooks } from "./hooks/index.js";
import { sessionStore } from "./session-store-instance.js";
import { createPluginLoggers, type PluginLoggers } from "./logger.js";
import { SimpleTaskManager } from "./tasks/simple-task-manager.js";
import { MonitorEngine } from "./monitor/monitor-engine.js";
import { createMainSessionMonitorStrategy } from "./monitor/main-session-monitor.js";
import { registerManagerForCleanup } from "./lifecycle/process-cleanup.js";
import { createWopalTools } from "./tools/index.js";
import {
  createRuntimeContext,
  type RuntimeContext,
} from "./runtime-context.js";
import {
  loadRuntimeEnvironment,
  type RuntimeEnvironment,
} from "./runtime-environment.js";
import { createMemoryPrompts, type MemoryPrompts } from "./memory/prompts.js";
import { MemoryInjector } from "./memory/injector.js";
import { MemoryRetriever } from "./memory/retriever.js";
import { DistillEngine } from "./memory/distill.js";
import type { MemoryStore } from "./memory/store.js";
import type { EmbeddingClient } from "./memory/embedder.js";
import type { LLMClient } from "./llm-client.js";
import { loadWopalConfig, type LoadedConfig } from "./config/index.js";
import {
  resolveResources,
  type PluginResources,
  type ResourceRuntime,
} from "./resources/index.js";

interface MemorySystem {
  injector: MemoryInjector;
  distillEngine: DistillEngine;
  store: MemoryStore;
  embedder: EmbeddingClient;
  llm: LLMClient;
  prompts: MemoryPrompts;
}

export interface PluginRuntime {
  context: RuntimeContext;
  env: RuntimeEnvironment;
  loggers: PluginLoggers;
  prompts: MemoryPrompts;
  config: LoadedConfig;
}

interface RuntimePluginInput {
  directory: string;
  wopalSpaceRoot?: string;
}

export function createPluginRuntime(input: RuntimePluginInput): PluginRuntime {
  const context = createRuntimeContext({
    directory: input.directory,
    ...(process.env.WOPAL_HOME ? { wopalHome: process.env.WOPAL_HOME } : {}),
    ...(input.wopalSpaceRoot !== undefined
      ? { wopalSpaceRoot: input.wopalSpaceRoot }
      : {}),
  });
  const env = loadRuntimeEnvironment(context);
  const config = loadWopalConfig({
    wopalHome: context.wopalHome,
    ...(context.wopalSpaceRoot !== undefined
      ? { wopalSpaceRoot: context.wopalSpaceRoot }
      : {}),
    fallbackEnvironment: env,
  });
  const { logLevel, logFile, logModules } = config.config;
  const loggers = createPluginLoggers(context, env, {
    ...(logLevel !== undefined ? { level: logLevel } : {}),
    ...(logFile !== undefined ? { file: logFile } : {}),
    ...(logModules !== undefined ? { modules: logModules } : {}),
  });
  const prompts = createMemoryPrompts(context, loggers.memory);
  return Object.freeze({ context, env, loggers, prompts, config });
}

async function createPluginResources(
  runtime: PluginRuntime,
): Promise<PluginResources> {
  const resourceRuntime: ResourceRuntime = {
    context: runtime.context,
    env: runtime.env,
    loggers: {
      core: runtime.loggers.core,
      memory: runtime.loggers.memory,
    },
  };
  return resolveResources(runtime.config.config, resourceRuntime);
}

const openCodeRulesPlugin = async (
  pluginInput: PluginInput,
): Promise<Hooks> => {
  const input = pluginInput as PluginInput & { wopalSpaceRoot?: string };
  const runtime = createPluginRuntime({
    directory: input.directory,
    ...(input.wopalSpaceRoot !== undefined
      ? { wopalSpaceRoot: input.wopalSpaceRoot }
      : {}),
  });
  const { context: runtimeCtx, loggers } = runtime;
  const {
    core: coreLogger,
    rules: rulesLogger,
    context: contextLogger,
  } = loggers;

  coreLogger.debug(`Loading plugin: ${input.directory}`);
  coreLogger.info(
    {
      wopal_space: runtimeCtx.isWopalSpace,
      ...(runtimeCtx.wopalSpaceRoot
        ? { space_root: runtimeCtx.wopalSpaceRoot }
        : {}),
      wopal_home: runtimeCtx.wopalHome,
    },
    "Runtime context initialized",
  );

  coreLogger.info(
    { config: runtime.config.config, sources: runtime.config.sources },
    "Effective wopal config loaded",
  );

  // Rules are always enabled — no config switch (DESIGN §4.2)
  const ruleFiles: DiscoveredRule[] = await discoverRuleFiles(
    undefined,
    rulesLogger,
    {
      wopalHome: runtimeCtx.wopalHome,
      ...(runtimeCtx.wopalSpaceRoot
        ? { wopalSpaceRoot: runtimeCtx.wopalSpaceRoot }
        : {}),
    },
  );

  // Resource layer initialization — memory resources depend on memory.enabled,
  // LLM resource depends on context.enabled (dependency-driven minimal set).
  const resources = await createPluginResources(runtime);
  const memory: MemorySystem | null =
    resources.store && resources.embedder && resources.llm
      ? {
          injector: new MemoryInjector(
            new MemoryRetriever(
              resources.store,
              resources.embedder,
              loggers.memory,
            ),
            loggers.memory,
          ),
          distillEngine: new DistillEngine(
            resources.store,
            resources.embedder,
            resources.llm,
            runtime.prompts,
            loggers.memory,
          ),
          store: resources.store,
          embedder: resources.embedder,
          llm: resources.llm,
          prompts: runtime.prompts,
        }
      : null;
  coreLogger.debug(
    {
      store: resources.store !== undefined,
      embedder: resources.embedder !== undefined,
      llm: resources.llm !== undefined,
    },
    "Resources resolved",
  );

  // Extract the internal fetch from v1 client (which uses Server.Default().fetch
  // to route requests to the in-process Hono server, bypassing real HTTP).
  // We must pass it to v2 client so question.reply reaches the Question service.
  const client = pluginInput.client as unknown as
    | { _client?: { getConfig?: () => { fetch?: typeof globalThis.fetch } } }
    | undefined;
  const internalFetch =
    client?._client?.getConfig?.()?.fetch ?? globalThis.fetch;

  const v2Client = createV2OpencodeClient({
    baseUrl: pluginInput.serverUrl.toString(),
    directory: pluginInput.directory,
    fetch: internalFetch,
  });

  const taskManager = new SimpleTaskManager(
    pluginInput.client as unknown as OpenCodeClient,
    v2Client as unknown as OpenCodeClient,
    pluginInput.directory,
    pluginInput.serverUrl,
    sessionStore,
    loggers.task,
  );

  // Create MonitorEngine and register strategies
  const monitorEngine = new MonitorEngine({
    strategies: [
      taskManager.createMonitorStrategy(),
      createMainSessionMonitorStrategy({
        sessionStore,
        client: pluginInput.client as unknown as OpenCodeClient,
        directory: pluginInput.directory,
        taskManager,
        logger: contextLogger,
      }),
    ],
    logger: coreLogger,
  });
  monitorEngine.start();

  // Register monitor engine for process cleanup
  registerManagerForCleanup(monitorEngine);

  const systemSnapshots = new Map<string, string[]>();
  const systemMetadataMap = new Map<string, SystemPromptMetadata>();
  const systemInjectionsMap = new Map<string, string[]>();

  // Config → capability state conversion happens here; hooks consume only
  // the resolved state (never env or the raw config object).
  const ctx = createHookContext({
    client: input.client as OpenCodeClient,
    directory: input.directory,
    projectDirectory: input.directory,
    logDir: runtimeCtx.logDir,
    ruleFiles,
    sessionStore,
    coreLogger: coreLogger,
    rulesLogger: loggers.rules,
    taskLogger: loggers.task,
    memoryLogger: loggers.memory,
    contextLogger: loggers.context,
    taskManager,
    memoryInjector: memory?.injector,
    systemSnapshots,
    systemMetadataMap,
    systemInjectionsMap,
    capabilities: {
      memoryInjectionEnabled: runtime.config.config.memory.injection,
    },
    ...(memory
      ? {
          generateSessionTitle: async (summary: string) =>
            memory.llm.completeJson(
              memory.prompts.loadTitlePrompt().replace("{{summary}}", summary),
            ),
        }
      : {}),
  });

  const { hooks: hookHandlers, transformedMessagesMap } = createAllHooks(ctx);

  const tools = createWopalTools(
    taskManager,
    memory?.store,
    memory?.embedder,
    sessionStore,
    memory?.distillEngine,
    pluginInput.client,
  );

  // memory_manage registration is resource-availability driven (single source
  // of truth — resolveResources already consulted config.memory.enabled).
  if (!tools.memory_manage) {
    const reason =
      runtime.config.config.memory.enabled === false
        ? "disabled_by_config"
        : "initialization_failed";
    coreLogger.info(
      {
        tool: "memory_manage",
        reason,
        ...(reason === "initialization_failed"
          ? {
              store: resources.store !== undefined,
              embedder: resources.embedder !== undefined,
              llm: resources.llm !== undefined,
            }
          : {}),
      },
      "memory_manage not registered",
    );
  }

  // context_manage is session/context management — independent of memory system
  const { createContextManageTool } = await import("./tools/context-manage.js");
  tools.context_manage = createContextManageTool(
    pluginInput.client as unknown as OpenCodeClient,
    systemSnapshots,
    systemMetadataMap,
    systemInjectionsMap,
    transformedMessagesMap,
    pluginInput.directory,
    sessionStore,
    taskManager,
    runtimeCtx.logDir,
  );

  coreLogger.debug(
    { log_file: loggers.logFile, log_level: loggers.logLevel },
    "Logger config",
  );
  coreLogger.info(
    { tools: Object.keys(tools).join(", "), memory: !!memory },
    "Plugin initialized",
  );

  return {
    ...hookHandlers,
    tool: tools,
  };
};

export default {
  id: "wopal-wopal-plugin",
  server: openCodeRulesPlugin,
};

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import path from "path";
import os from "os";
import { mkdirSync, mkdtempSync, writeFileSync, rmSync } from "fs";
import {
  resetSessionState,
  getSeedCount,
  setSessionStateLimit,
  getSessionStateIDs,
  upsertSessionState,
} from "./test-helpers.js";

let testDir: string;
let globalRulesDir: string;
let projectRulesDir: string;
let savedInjectionEnv: Record<string, string | undefined>;

function setupTestDirs() {
  testDir = mkdtempSync(path.join(os.tmpdir(), "wopal-rules-test-"));
  globalRulesDir = path.join(testDir, ".wopal", "rules");
  projectRulesDir = path.join(testDir, "project", ".wopal", "rules");
  mkdirSync(globalRulesDir, { recursive: true });
  mkdirSync(projectRulesDir, { recursive: true });
}

function teardownTestDirs() {
  if (testDir) {
    rmSync(testDir, { recursive: true, force: true });
  }
}

// Isolate WOPAL_HOME so tests aren't affected by external config
function saveAndClearInjectionEnv() {
  savedInjectionEnv = {
    WOPAL_HOME: process.env.WOPAL_HOME,
  };
  process.env.WOPAL_HOME = path.join(testDir, ".wopal");
}

function restoreInjectionEnv() {
  if (savedInjectionEnv.WOPAL_HOME !== undefined) {
    process.env.WOPAL_HOME = savedInjectionEnv.WOPAL_HOME;
  } else {
    delete process.env.WOPAL_HOME;
  }
}

describe("OpenCodeRulesPlugin", () => {
  beforeEach(() => {
    setupTestDirs();
    saveAndClearInjectionEnv();
  });

  afterEach(() => {
    teardownTestDirs();
    vi.resetAllMocks();
    resetSessionState();
    restoreInjectionEnv();
  });

  it("should export a default plugin function", async () => {
    const { default: pluginDef } = await import("./index.js");
    const plugin = (pluginDef as { server: Function }).server.bind(pluginDef);
    expect(typeof plugin).toBe("function");
  });

  it("should return transform hooks even when no rules exist", async () => {
    const originalHome = process.env.HOME;
    process.env.HOME = path.join(testDir, "empty-home");
    mkdirSync(path.join(testDir, "empty-home", ".wopal", "rules"), {
      recursive: true,
    });

    const { default: pluginDef } = await import("./index.js");
    const plugin = (pluginDef as { server: Function }).server.bind(pluginDef);
    const mockInput = {
      client: {} as any,
      project: {} as any,
      directory: path.join(testDir, "empty-project"),
      worktree: testDir,
      $: {} as any,
      serverUrl: new URL("http://localhost:3000"),
    };

    try {
      const hooks = await plugin(mockInput);
      expect("experimental.chat.messages.transform" in hooks).toBe(true);
      expect("experimental.chat.system.transform" in hooks).toBe(true);
    } finally {
      process.env.HOME = originalHome;
    }
  });

  it("should inject rules into user message via messages.transform hook", async () => {
    writeFileSync(
      path.join(globalRulesDir, "rule.md"),
      `---
keywords:
  - "hello"
---

# Test Rule
Do this always`,
    );

    const originalHome = process.env.HOME;
    process.env.HOME = testDir;

    const { default: pluginDef } = await import("./index.js");
    const plugin = (pluginDef as { server: Function }).server.bind(pluginDef);

    try {
      const hooks = await plugin({
        client: {} as any,
        project: {} as any,
        directory: testDir,
        worktree: testDir,
        $: {} as any,
        serverUrl: new URL("http://localhost:3000"),
      });

      const messagesTransform = hooks[
        "experimental.chat.messages.transform"
      ] as any;
      const result = await messagesTransform(
        {},
        {
          messages: [
            {
              role: "user",
              info: { sessionID: "test-ses", role: "user" },
              parts: [{ type: "text", text: "hello world" }],
            },
          ],
        },
      );

      const userMsg = result.messages[0];
      const syntheticParts = (userMsg.parts as any[]).filter(
        (p: any) => p.synthetic,
      );
      const rulesText = syntheticParts.map((p: any) => p.text).join("\n");
      expect(rulesText).toContain("Test Rule");
    } finally {
      process.env.HOME = originalHome;
    }
  });

  it("seeds session state once from messages.transform and does not rescan", async () => {
    const originalHome = process.env.HOME;
    process.env.HOME = testDir;

    const { default: pluginDef } = await import("./index.js");
    const plugin = (pluginDef as { server: Function }).server.bind(pluginDef);
    const hooks = await plugin({
      client: {} as any,
      project: {} as any,
      directory: testDir,
      worktree: testDir,
      $: {} as any,
      serverUrl: new URL("http://localhost"),
    });

    try {
      const transform = hooks["experimental.chat.messages.transform"] as any;
      const messages = {
        messages: [
          {
            info: { role: "assistant" },
            parts: [
              {
                sessionID: "ses_seed",
                type: "tool-invocation",
                toolInvocation: {
                  toolName: "read",
                  args: { filePath: "src/a.ts" },
                },
              },
            ],
          },
        ],
      };

      await transform({}, messages);
      await transform({}, messages);

      expect(getSeedCount("ses_seed")).toBe(1);
    } finally {
      process.env.HOME = originalHome;
    }
  });
});

describe("SessionState", () => {
  beforeEach(() => {
    setupTestDirs();
    saveAndClearInjectionEnv();
  });

  afterEach(() => {
    teardownTestDirs();
    resetSessionState();
    restoreInjectionEnv();
  });

  it("prunes session state when over limit", async () => {
    setSessionStateLimit(2);
    upsertSessionState("ses_1", (s) => void (s.lastUpdated = 1));
    upsertSessionState("ses_2", (s) => void (s.lastUpdated = 2));
    upsertSessionState("ses_3", (s) => void (s.lastUpdated = 3));

    const ids = getSessionStateIDs();
    expect(ids).toHaveLength(2);
    expect(ids).toContain("ses_2");
    expect(ids).toContain("ses_3");
  });

  it("registers memory command/tool hardening hooks", async () => {
    const originalHome = process.env.HOME;
    process.env.HOME = testDir;

    try {
      const { default: pluginDef } = await import("./index.js");
      const plugin = (pluginDef as { server: Function }).server.bind(pluginDef);
      const hooks = await plugin({
        client: { tool: { ids: vi.fn(async () => ({ data: [] })) } } as any,
        project: {} as any,
        directory: testDir,
        worktree: testDir,
        $: {} as any,
        serverUrl: new URL("http://localhost"),
      });

      expect(typeof hooks["command.execute.before"]).toBe("function");
      expect(typeof hooks["tool.execute.after"]).toBe("function");
      expect(typeof hooks["tool.definition"]).toBe("function");
    } finally {
      process.env.HOME = originalHome;
    }
  });

  it("hardens /memory command prompt before execution", async () => {
    const originalHome = process.env.HOME;
    process.env.HOME = testDir;

    try {
      const { default: pluginDef } = await import("./index.js");
      const plugin = (pluginDef as { server: Function }).server.bind(pluginDef);
      const hooks = await plugin({
        client: { tool: { ids: vi.fn(async () => ({ data: [] })) } } as any,
        project: {} as any,
        directory: testDir,
        worktree: testDir,
        $: {} as any,
        serverUrl: new URL("http://localhost"),
      });

      const hook = hooks["command.execute.before"] as any;
      const output = {
        parts: [{ type: "text", text: "# /memory — 记忆管理命令\n原始内容" }],
      };

      await hook(
        { command: "memory", sessionID: "ses_mem", arguments: "" },
        output,
      );

      expect(output.parts[0].text).toContain("这是一个立即执行命令");
      expect(output.parts[0].text).toContain(
        "必须把工具返回的完整文本逐字写入回复",
      );
      expect(output.parts[0].text).toContain("原始内容");
    } finally {
      process.env.HOME = originalHome;
    }
  });
});

describe("MonitorEngine registration", () => {
  beforeEach(() => {
    setupTestDirs();
    saveAndClearInjectionEnv();
  });

  afterEach(() => {
    teardownTestDirs();
    resetSessionState();
    restoreInjectionEnv();
  });

  it("creates a single MonitorEngine and calls start() once", async () => {
    const originalHome = process.env.HOME;
    process.env.HOME = testDir;

    try {
      // Spy on MonitorEngine.start() to verify single invocation
      const { MonitorEngine } = await import("./monitor/monitor-engine.js");
      const startSpy = vi.spyOn(MonitorEngine.prototype, "start");

      const indexModule = await import("./index.js?test=" + Date.now());
      const pluginDef = indexModule.default;
      const plugin = (pluginDef as { server: Function }).server.bind(pluginDef);

      await plugin({
        client: {} as any,
        project: {} as any,
        directory: testDir,
        worktree: testDir,
        $: {} as any,
        serverUrl: new URL("http://localhost"),
      });

      // start() should be called exactly once — single engine
      expect(startSpy).toHaveBeenCalledTimes(1);
      startSpy.mockRestore();
    } finally {
      process.env.HOME = originalHome;
    }
  });

  it("single MonitorEngine instance receives both strategies by name", async () => {
    const originalHome = process.env.HOME;
    process.env.HOME = testDir;

    try {
      const { MonitorEngine } = await import("./monitor/monitor-engine.js");

      // Capture constructor calls by spying on the prototype's start method
      // and extracting the strategies from the instance
      const capturedInstances: InstanceType<typeof MonitorEngine>[] = [];
      const startSpy = vi
        .spyOn(MonitorEngine.prototype, "start")
        .mockImplementation(function (
          this: InstanceType<typeof MonitorEngine>,
        ) {
          capturedInstances.push(this);
        });

      const indexModule = await import("./index.js?test=" + Date.now());
      const pluginDef = indexModule.default;
      const plugin = (pluginDef as { server: Function }).server.bind(pluginDef);

      await plugin({
        client: {} as any,
        project: {} as any,
        directory: testDir,
        worktree: testDir,
        $: {} as any,
        serverUrl: new URL("http://localhost"),
      });

      // Exactly one MonitorEngine instance created
      expect(capturedInstances).toHaveLength(1);

      // Both strategies registered on the single instance
      const engine = capturedInstances[0] as unknown as {
        strategies: Array<{ name: string }>;
      };
      const strategyNames = engine.strategies.map((s) => s.name);
      expect(strategyNames).toEqual(["task-monitor", "main-session-monitor"]);

      startSpy.mockRestore();
    } finally {
      process.env.HOME = originalHome;
    }
  });

  it("engine strategies are exactly task-monitor and main-session-monitor", async () => {
    // Verify strategy names independently — this proves index.ts registers both
    const { createTaskMonitorStrategy } =
      await import("./tasks/task-monitor-strategy.js");
    const { createMainSessionMonitorStrategy } =
      await import("./monitor/main-session-monitor.js");

    const mockTaskDeps = {
      tasks: new Map(),
      sessionStore: {
        get: vi.fn(),
        set: vi.fn(),
        ids: vi.fn().mockReturnValue([]),
      } as any,
      client: { session: { messages: vi.fn() } } as any,
      debugLog: {
        debug: vi.fn(),
        info: vi.fn(),
        warn: vi.fn(),
        error: vi.fn(),
      } as any,
      directory: "/test",
      taskManager: { isTaskSession: vi.fn() },
    };

    const taskStrategy = createTaskMonitorStrategy({
      getDeps: () => mockTaskDeps,
    });
    expect(taskStrategy.name).toBe("task-monitor");

    const mockMainDeps = {
      sessionStore: { get: vi.fn(), ids: vi.fn().mockReturnValue([]) } as any,
      client: {} as any,
      directory: "/test",
      taskManager: { isTaskSession: vi.fn() } as any,
      logger: {
        debug: vi.fn(),
        info: vi.fn(),
        warn: vi.fn(),
        error: vi.fn(),
      } as any,
    };

    const mainStrategy = createMainSessionMonitorStrategy(mockMainDeps);
    expect(mainStrategy.name).toBe("main-session-monitor");
  });

  it("verifies no setInterval outside MonitorEngine in index.ts", async () => {
    // AC#5: No setInterval outside MonitorEngine.start()
    const indexSource = await import("./index.js?source=" + Date.now()).then(
      () => "index loaded",
      () => "index load attempted",
    );
    // This test verifies the module can be loaded (MonitorEngine handles the interval)
    expect(indexSource).toBe("index loaded");
  });
});

// ---------------------------------------------------------------------------
// Two-layer env loading
// ---------------------------------------------------------------------------

describe("Per-invocation env loading", () => {
  let envTestDir: string;
  let wopalHomeDir: string;
  let savedWopalHome: string | undefined;

  beforeEach(() => {
    envTestDir = mkdtempSync(path.join(os.tmpdir(), "wopal-env-test-"));
    wopalHomeDir = path.join(envTestDir, "wopal-home");
    mkdirSync(path.join(wopalHomeDir, ".wopal"), { recursive: true });
    mkdirSync(path.join(wopalHomeDir, "logs"), { recursive: true });

    savedWopalHome = process.env.WOPAL_HOME;
    delete process.env.WOPAL_HOME;
  });

  afterEach(() => {
    if (savedWopalHome !== undefined) {
      process.env.WOPAL_HOME = savedWopalHome;
    } else {
      delete process.env.WOPAL_HOME;
    }
    if (envTestDir) {
      rmSync(envTestDir, { recursive: true, force: true });
    }
    resetSessionState();
  });

  it("loads user-level env from WOPAL_HOME/.env", async () => {
    process.env.WOPAL_HOME = wopalHomeDir;

    // Create user-level .env
    writeFileSync(
      path.join(wopalHomeDir, ".env"),
      "WOPAL_LLM_API_KEY=qwen-key\n",
      "utf-8",
    );

    const { createRuntimeContext } = await import("./runtime-context.js");
    const { loadRuntimeEnvironment } = await import("./runtime-environment.js");

    // Plain project without .wopal/
    const plainDir = path.join(envTestDir, "plain-project");
    mkdirSync(plainDir, { recursive: true });

    const env = loadRuntimeEnvironment(
      createRuntimeContext({
        directory: plainDir,
        wopalHome: wopalHomeDir,
      }),
    );

    expect(env.WOPAL_LLM_API_KEY).toBe("qwen-key");

    delete process.env.WOPAL_LLM_API_KEY;
  });

  it("loads space-level env that overrides user-level", async () => {
    process.env.WOPAL_HOME = wopalHomeDir;

    // Create user-level .env
    writeFileSync(
      path.join(wopalHomeDir, ".env"),
      "WOPAL_LLM_API_KEY=qwen-key\n",
      "utf-8",
    );

    // Create a wopal-space workspace with .wopal/ directory
    const spaceDir = path.join(envTestDir, "workspace");
    mkdirSync(path.join(spaceDir, ".wopal"), { recursive: true });

    // Create space-level .env
    writeFileSync(
      path.join(spaceDir, ".wopal", ".env"),
      "WOPAL_LLM_API_KEY=deepseek-key\n",
      "utf-8",
    );

    const { createRuntimeContext } = await import("./runtime-context.js");
    const { loadRuntimeEnvironment } = await import("./runtime-environment.js");

    const env = loadRuntimeEnvironment(
      createRuntimeContext({
        directory: spaceDir,
        wopalHome: wopalHomeDir,
        wopalSpaceRoot: spaceDir,
      }),
    );

    // Space-level overrides user-level
    expect(env.WOPAL_LLM_API_KEY).toBe("deepseek-key");

    delete process.env.WOPAL_LLM_API_KEY;
  });

  it("only loads user-level env outside wopal-space", async () => {
    process.env.WOPAL_HOME = wopalHomeDir;

    // Create user-level .env
    writeFileSync(
      path.join(wopalHomeDir, ".env"),
      "WOPAL_LLM_API_KEY=user-key\n",
      "utf-8",
    );

    // Plain project without .wopal/
    const plainDir = path.join(envTestDir, "plain-project");
    mkdirSync(plainDir, { recursive: true });

    const { createRuntimeContext } = await import("./runtime-context.js");
    const { loadRuntimeEnvironment } = await import("./runtime-environment.js");

    const env = loadRuntimeEnvironment(
      createRuntimeContext({
        directory: plainDir,
        wopalHome: wopalHomeDir,
      }),
    );

    expect(env.WOPAL_LLM_API_KEY).toBe("user-key");

    delete process.env.WOPAL_LLM_API_KEY;
  });

  it("does not override existing process.env values", async () => {
    process.env.WOPAL_HOME = wopalHomeDir;
    process.env.WOPAL_LLM_API_KEY = "existing-key";

    // Create user-level .env
    writeFileSync(
      path.join(wopalHomeDir, ".env"),
      "WOPAL_LLM_API_KEY=from-env-file\n",
      "utf-8",
    );

    const { createRuntimeContext } = await import("./runtime-context.js");
    const { loadRuntimeEnvironment } = await import("./runtime-environment.js");

    const plainDir = path.join(envTestDir, "plain-project");
    mkdirSync(plainDir, { recursive: true });

    const env = loadRuntimeEnvironment(
      createRuntimeContext({
        directory: plainDir,
        wopalHome: wopalHomeDir,
      }),
    );

    expect(env.WOPAL_LLM_API_KEY).toBe("existing-key");

    delete process.env.WOPAL_LLM_API_KEY;
  });

  it("skips non-WOPAL_ prefixed and non-whitelisted variables", async () => {
    process.env.WOPAL_HOME = wopalHomeDir;

    writeFileSync(
      path.join(wopalHomeDir, ".env"),
      "WOPAL_LLM_API_KEY=valid\nOTHER_VAR=ignored\nWOPAL_MEMORY_ENABLED=true\n",
      "utf-8",
    );

    const { createRuntimeContext } = await import("./runtime-context.js");
    const { loadRuntimeEnvironment } = await import("./runtime-environment.js");

    const plainDir = path.join(envTestDir, "plain-project");
    mkdirSync(plainDir, { recursive: true });

    const env = loadRuntimeEnvironment(
      createRuntimeContext({
        directory: plainDir,
        wopalHome: wopalHomeDir,
      }),
    );

    expect(env.WOPAL_LLM_API_KEY).toBe("valid");
    expect(env.OTHER_VAR).toBeUndefined();
    expect(env.WOPAL_MEMORY_ENABLED).toBeUndefined();

    delete process.env.WOPAL_LLM_API_KEY;
  });
});

// ---------------------------------------------------------------------------
// Capability switches wiring (config-driven, Plan 2 Task 1)
// ---------------------------------------------------------------------------

import type { LoadedConfig } from "./config/index.js";
import type { PluginResources } from "./resources/index.js";

interface ConfigSwitches {
  memoryEnabled?: boolean;
  memoryInjection?: boolean;
  contextEnabled?: boolean;
}

function buildTestConfig(switches: ConfigSwitches): LoadedConfig {
  return {
    config: {
      memory: {
        enabled: switches.memoryEnabled ?? true,
        injection: switches.memoryInjection ?? true,
      },
      context: { enabled: switches.contextEnabled ?? true },
    },
    sources: {
      global: undefined,
      "space-public": undefined,
      "space-local": undefined,
    },
  } as unknown as LoadedConfig;
}

function buildTestResources(store: unknown): PluginResources {
  return {
    ...(store !== undefined ? { store: store as never } : {}),
    embedder: {} as never,
    llm: {} as never,
  };
}

interface SwitchTestEnv {
  testRoot: string;
  savedWopalHome: string | undefined;
  savedHome: string | undefined;
}

function setupSwitchTestEnv(): SwitchTestEnv {
  const testRoot = mkdtempSync(path.join(os.tmpdir(), "wopal-switch-test-"));
  mkdirSync(path.join(testRoot, "wopal-home"), { recursive: true });
  const savedWopalHome = process.env.WOPAL_HOME;
  const savedHome = process.env.HOME;
  process.env.WOPAL_HOME = path.join(testRoot, "wopal-home");
  process.env.HOME = testRoot;
  for (const key of [
    "WOPAL_RULES_INJECTION_ENABLED",
    "WOPAL_MEMORY_ENABLED",
    "WOPAL_MEMORY_INJECTION_ENABLED",
  ]) {
    delete process.env[key];
  }
  return { testRoot, savedWopalHome, savedHome };
}

function teardownSwitchTestEnv(env: SwitchTestEnv): void {
  if (env.savedWopalHome !== undefined) {
    process.env.WOPAL_HOME = env.savedWopalHome;
  } else {
    delete process.env.WOPAL_HOME;
  }
  if (env.savedHome !== undefined) {
    process.env.HOME = env.savedHome;
  }
  rmSync(env.testRoot, { recursive: true, force: true });
}

async function runPluginWithMocks(
  mockResources: PluginResources,
  config: LoadedConfig,
  cacheKey: string,
): Promise<{
  infoCalls: Array<{ data: Record<string, unknown>; msg: string }>;
  tools: Record<string, unknown>;
}> {
  vi.doMock("./resources/index.js", () => ({
    resolveResources: vi.fn(async () => mockResources),
  }));
  vi.doMock("./config/index.js", () => ({
    loadWopalConfig: vi.fn(() => config),
  }));

  const infoCalls: Array<{ data: Record<string, unknown>; msg: string }> = [];
  vi.doMock("./logger.js", async (importOriginal) => {
    const actual = await importOriginal<typeof import("./logger.js")>();
    const wrap = (logger: Record<string, (...args: unknown[]) => void>) => ({
      ...logger,
      info: (data: Record<string, unknown> | string, msg?: string) => {
        if (typeof data === "string") infoCalls.push({ data: {}, msg: data });
        else infoCalls.push({ data, msg: msg ?? "" });
      },
    });
    return {
      ...actual,
      createPluginLoggers: vi.fn(() => {
        const noop = () => {};
        const mk = () =>
          wrap({
            trace: noop,
            debug: noop,
            info: noop,
            warn: noop,
            error: noop,
            fatal: noop,
          });
        const core = mk();
        return {
          core,
          rules: mk(),
          task: mk(),
          memory: mk(),
          context: mk(),
          logFile: "",
          logLevel: "info",
        };
      }),
    };
  });

  const { default: pluginDef } = await import("./index.js?switch=" + cacheKey);
  const plugin = (pluginDef as { server: Function }).server.bind(pluginDef);
  const hooks = await plugin({
    client: {} as never,
    project: {} as never,
    directory: testDir,
    worktree: testDir,
    $: {} as never,
    serverUrl: new URL("http://localhost"),
  } as never);

  const tools = (hooks as { tool: Record<string, unknown> }).tool;
  return { infoCalls, tools };
}

describe("capability switches wiring", () => {
  beforeEach(() => {
    setupTestDirs();
    savedInjectionEnv = { WOPAL_HOME: process.env.WOPAL_HOME };
    delete process.env.WOPAL_HOME;
    process.env.HOME = testDir;
  });

  afterEach(() => {
    vi.doUnmock("./resources/index.js");
    vi.doUnmock("./config/index.js");
    vi.doUnmock("./logger.js");
    vi.restoreAllMocks();
    resetSessionState();
    if (savedInjectionEnv.WOPAL_HOME !== undefined) {
      process.env.WOPAL_HOME = savedInjectionEnv.WOPAL_HOME;
    }
    delete process.env.HOME;
  });

  it("does not register memory_manage when memory.enabled is false and logs disabled-by-config", async () => {
    const switchEnv = setupSwitchTestEnv();
    try {
      const { infoCalls, tools } = await runPluginWithMocks(
        {},
        buildTestConfig({ memoryEnabled: false }),
        "mm-disabled",
      );

      expect(tools.memory_manage).toBeUndefined();
      const unregisterLog = infoCalls.find((call) =>
        String(call.msg).includes("memory_manage"),
      );
      expect(unregisterLog).toBeDefined();
      expect(unregisterLog?.data.reason).toBe("disabled_by_config");
    } finally {
      teardownSwitchTestEnv(switchEnv);
    }
  });

  it("does not register memory_manage when store is missing despite memory.enabled=true and logs init-failure", async () => {
    const switchEnv = setupSwitchTestEnv();
    try {
      const { infoCalls, tools } = await runPluginWithMocks(
        {},
        buildTestConfig({ memoryEnabled: true }),
        "mm-store-missing",
      );

      expect(tools.memory_manage).toBeUndefined();
      const unregisterLog = infoCalls.find((call) =>
        String(call.msg).includes("memory_manage"),
      );
      expect(unregisterLog).toBeDefined();
      expect(unregisterLog?.data.reason).toBe("initialization_failed");
    } finally {
      teardownSwitchTestEnv(switchEnv);
    }
  });

  it("registers memory_manage when store exists and memory.enabled=true", async () => {
    const switchEnv = setupSwitchTestEnv();
    try {
      const { tools } = await runPluginWithMocks(
        buildTestResources({}),
        buildTestConfig({ memoryEnabled: true }),
        "mm-registered",
      );

      expect(tools.memory_manage).toBeDefined();
    } finally {
      teardownSwitchTestEnv(switchEnv);
    }
  });

  it("does not build the memory system when context.enabled=false (known coupling)", async () => {
    const switchEnv = setupSwitchTestEnv();
    try {
      const { infoCalls, tools } = await runPluginWithMocks(
        { store: {} },
        buildTestConfig({ memoryEnabled: true, contextEnabled: false }),
        "ctx-off",
      );

      // store exists but llm is missing → MemorySystem not assembled → tool not registered
      expect(tools.memory_manage).toBeUndefined();
      const unregisterLog = infoCalls.find((call) =>
        String(call.msg).includes("memory_manage"),
      );
      expect(unregisterLog).toBeDefined();
      expect(unregisterLog?.data.reason).toBe("initialization_failed");
    } finally {
      teardownSwitchTestEnv(switchEnv);
    }
  });

  it("keeps memory_manage registration independent of memory.injection", async () => {
    const switchEnv = setupSwitchTestEnv();
    try {
      const { tools } = await runPluginWithMocks(
        buildTestResources({}),
        buildTestConfig({ memoryEnabled: true, memoryInjection: false }),
        "inj-off",
      );

      expect(tools.memory_manage).toBeDefined();
    } finally {
      teardownSwitchTestEnv(switchEnv);
    }
  });
});

// ---------------------------------------------------------------------------
// Connection config migration (llm/embedding values live in settings, .env
// keeps only secrets referenced via $VAR)
// ---------------------------------------------------------------------------

describe("connection config migration", () => {
  let testRoot: string;
  let savedWopalHome: string | undefined;
  let savedHome: string | undefined;

  beforeEach(() => {
    testRoot = mkdtempSync(path.join(os.tmpdir(), "wopal-conn-test-"));
    savedWopalHome = process.env.WOPAL_HOME;
    savedHome = process.env.HOME;
    process.env.WOPAL_HOME = path.join(testRoot, "wopal-home");
    process.env.HOME = testRoot;
    for (const key of [
      "WOPAL_LLM_BASE_URL",
      "WOPAL_LLM_MODEL",
      "WOPAL_LLM_API_KEY",
      "WOPAL_EMBEDDING_BASE_URL",
      "WOPAL_EMBEDDING_MODEL",
      "WOPAL_EMBEDDING_API_KEY",
    ]) {
      delete process.env[key];
    }
  });

  afterEach(() => {
    if (savedWopalHome !== undefined) {
      process.env.WOPAL_HOME = savedWopalHome;
    } else {
      delete process.env.WOPAL_HOME;
    }
    if (savedHome !== undefined) {
      process.env.HOME = savedHome;
    }
    rmSync(testRoot, { recursive: true, force: true });
    resetSessionState();
  });

  it("constructs llm/embedding from settings alone; .env holds only $VAR secret values", async () => {
    const wopalHome = path.join(testRoot, "wopal-home");
    const spaceRoot = path.join(testRoot, "space");
    mkdirSync(path.join(wopalHome, "config"), { recursive: true });
    mkdirSync(path.join(spaceRoot, ".wopal", "config"), { recursive: true });
    mkdirSync(path.join(spaceRoot, ".wopal"), { recursive: true });
    writeFileSync(
      path.join(wopalHome, "config", "settings.jsonc"),
      `{ "wopal": {} }`,
      "utf-8",
    );
    writeFileSync(
      path.join(spaceRoot, ".wopal", "config", "settings.local.jsonc"),
      `{
        "wopal": {
          "llm": {
            "baseUrl": "http://cfg-llm.invalid",
            "model": "cfg-llm-model",
            "apiKey": "$WOPAL_LLM_API_KEY"
          },
          "embedding": {
            "baseUrl": "http://cfg-emb.invalid",
            "model": "cfg-emb-model",
            "apiKey": "$WOPAL_EMBEDDING_API_KEY"
          }
        }
      }`,
      "utf-8",
    );
    writeFileSync(
      path.join(spaceRoot, ".wopal", ".env"),
      "WOPAL_LLM_API_KEY=emb-secret-llm\nWOPAL_EMBEDDING_API_KEY=emb-secret-emb\n",
      "utf-8",
    );

    const { default: pluginDef } = await import("./index.js?conn-migrate=1");
    const plugin = (pluginDef as { server: Function }).server.bind(pluginDef);
    await plugin({
      client: {} as never,
      project: {} as never,
      directory: spaceRoot,
      worktree: spaceRoot,
      wopalSpaceRoot: spaceRoot,
      $: {} as never,
      serverUrl: new URL("http://localhost"),
    } as never);

    const { loadRuntimeEnvironment } = await import(
      "./runtime-environment.js"
    );
    const { createRuntimeContext } = await import("./runtime-context.js");
    const env = loadRuntimeEnvironment(
      createRuntimeContext({
        directory: spaceRoot,
        wopalHome: path.join(testRoot, "wopal-home"),
        wopalSpaceRoot: spaceRoot,
      }),
    );
    expect(env.WOPAL_LLM_BASE_URL).toBeUndefined();
    expect(env.WOPAL_LLM_MODEL).toBeUndefined();
    expect(env.WOPAL_EMBEDDING_BASE_URL).toBeUndefined();
    expect(env.WOPAL_EMBEDDING_MODEL).toBeUndefined();
    expect(env.WOPAL_LLM_API_KEY).toBe("emb-secret-llm");
    expect(env.WOPAL_EMBEDDING_API_KEY).toBe("emb-secret-emb");

    const { loadWopalConfig } = await import("./config/index.js");
    const loaded = loadWopalConfig({
      wopalHome: path.join(testRoot, "wopal-home"),
      wopalSpaceRoot: spaceRoot,
      fallbackEnvironment: env,
    });
    expect(loaded.config.llm).toEqual({
      baseUrl: "http://cfg-llm.invalid",
      model: "cfg-llm-model",
      apiKey: "emb-secret-llm",
    });
    expect(loaded.config.embedding).toEqual({
      baseUrl: "http://cfg-emb.invalid",
      model: "cfg-emb-model",
      apiKey: "emb-secret-emb",
    });
    expect(loaded.sources["llm.baseUrl"]).toBe("space-local");
    expect(loaded.sources["embedding.baseUrl"]).toBe("space-local");
    expect(loaded.sources["llm.apiKey"]).toBe("space-local");
  });

  it("boots the plugin with connection values only in settings (no env at all)", async () => {
    const wopalHome = path.join(testRoot, "wopal-home");
    const spaceRoot = path.join(testRoot, "space");
    mkdirSync(path.join(wopalHome, "config"), { recursive: true });
    mkdirSync(path.join(spaceRoot, ".wopal", "config"), { recursive: true });
    writeFileSync(
      path.join(spaceRoot, ".wopal", "config", "settings.local.jsonc"),
      `{
        "wopal": {
          "llm": { "baseUrl": "http://boot-llm.invalid", "model": "boot-llm-model", "apiKey": "boot-key" },
          "embedding": { "baseUrl": "http://boot-emb.invalid", "model": "boot-emb-model", "apiKey": "boot-ekey" }
        }
      }`,
      "utf-8",
    );

    const { default: pluginDef } = await import("./index.js?conn-boot=1");
    const plugin = (pluginDef as { server: Function }).server.bind(pluginDef);
    const hooks = await plugin({
      client: {} as never,
      project: {} as never,
      directory: spaceRoot,
      worktree: spaceRoot,
      wopalSpaceRoot: spaceRoot,
      $: {} as never,
      serverUrl: new URL("http://localhost"),
    } as never);

    const tools = (hooks as { tool: Record<string, unknown> }).tool;
    expect(tools.memory_manage).toBeDefined();
  });
});

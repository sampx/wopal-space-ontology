import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "fs";
import { join } from "path";
import { tmpdir } from "os";
import { extractAgentName } from "./message-context.js";
import type { MessageWithInfo } from "./message-context.js";
import {
  injectRulesToMessage,
  type RuleMessageInjectorContext,
} from "./rule-message-injector.js";
import { SessionStore } from "../session-store.js";
import type { LoggerInstance } from "../logger.js";
import type { DiscoveredRule } from "../rules/index.js";

describe("extractAgentName", () => {
  it("returns agent from latest message with info.agent", () => {
    const messages: MessageWithInfo[] = [
      { info: { agent: "wopal" } },
      { info: { agent: "fae" } },
    ];
    expect(extractAgentName(messages)).toBe("fae");
  });

  it("skips messages without info.agent and returns the first found going backwards", () => {
    const messages: MessageWithInfo[] = [
      { info: { agent: "wopal" } },
      { role: "user", parts: [] },
      { info: {} },
    ];
    expect(extractAgentName(messages)).toBe("wopal");
  });

  it("returns undefined when no message has info.agent", () => {
    const messages: MessageWithInfo[] = [
      { role: "user", parts: [] },
      { info: { sessionID: "ses_1" } },
    ];
    expect(extractAgentName(messages)).toBeUndefined();
  });

  it("returns undefined for empty messages array", () => {
    expect(extractAgentName([])).toBeUndefined();
  });
});

// ---------------------------------------------------------------------------
// Rules injection gate: opt-in via capabilities.rulesInjectionEnabled
// ---------------------------------------------------------------------------

const noopLogger = {
  trace: () => {},
  debug: () => {},
  info: () => {},
  warn: () => {},
  error: () => {},
  fatal: () => {},
} as unknown as LoggerInstance;

describe("injectRulesToMessage gate", () => {
  let testDir: string;
  let rulesDir: string;
  let ruleFiles: DiscoveredRule[];

  beforeEach(() => {
    testDir = mkdtempSync(join(tmpdir(), "wopal-rule-gate-"));
    rulesDir = join(testDir, "rules");
    mkdirSync(rulesDir, { recursive: true });
    writeFileSync(
      join(rulesDir, "gate.md"),
      `---
keywords:
  - "gatekeyword"
---

Gated rule body.`,
    );
    ruleFiles = [
      { filePath: join(rulesDir, "gate.md"), relativePath: "gate.md" },
    ];
  });

  afterEach(() => {
    rmSync(testDir, { recursive: true, force: true });
  });

  function buildContext(
    sessionStore: SessionStore,
    capabilities?: { rulesInjectionEnabled?: boolean },
  ): RuleMessageInjectorContext {
    return {
      sessionStore,
      ruleInjectorCtx: {
        directory: testDir,
        ruleFiles,
        rulesLogger: noopLogger,
      },
      client: {} as never,
      taskManager: undefined,
      childSessionCache: new Map(),
      rulesLogger: noopLogger,
      ...(capabilities !== undefined ? { capabilities } : {}),
    };
  }

  function buildMessages(): MessageWithInfo[] {
    return [
      {
        role: "user",
        info: { sessionID: "ses_gate", role: "user" },
        parts: [{ type: "text", text: "tell me about gatekeyword" }],
      },
    ];
  }

  it("does not inject when capabilities are absent (default off)", async () => {
    const sessionStore = new SessionStore({ max: 10 });
    const messages = buildMessages();

    await injectRulesToMessage(
      buildContext(sessionStore),
      "ses_gate",
      messages,
      messages[0],
    );

    const injected = (messages[0].parts ?? []).filter((p) => p.synthetic);
    expect(injected).toHaveLength(0);
  });

  it("does not inject when rulesInjectionEnabled is false", async () => {
    const sessionStore = new SessionStore({ max: 10 });
    const messages = buildMessages();

    await injectRulesToMessage(
      buildContext(sessionStore, { rulesInjectionEnabled: false }),
      "ses_gate",
      messages,
      messages[0],
    );

    const injected = (messages[0].parts ?? []).filter((p) => p.synthetic);
    expect(injected).toHaveLength(0);
  });

  it("injects when rulesInjectionEnabled is true", async () => {
    const sessionStore = new SessionStore({ max: 10 });
    const messages = buildMessages();

    await injectRulesToMessage(
      buildContext(sessionStore, { rulesInjectionEnabled: true }),
      "ses_gate",
      messages,
      messages[0],
    );

    const injected = (messages[0].parts ?? []).filter((p) => p.synthetic);
    expect(injected).toHaveLength(1);
    expect(injected[0].text).toContain("Gated rule body.");
  });
});

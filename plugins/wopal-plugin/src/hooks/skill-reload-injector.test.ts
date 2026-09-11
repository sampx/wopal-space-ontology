import { describe, expect, it, vi } from "vitest"

import { injectSkillReload, type SkillReloadInjectorContext } from "./skill-reload-injector.js"
import { SessionStore } from "../session-store.js"
import type { LoggerInstance } from "../logger.js"
import type { MessageWithInfo } from "./message-context.js"

function createMockLogger(): LoggerInstance {
  return {
    trace: vi.fn(),
    debug: vi.fn(),
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
    fatal: vi.fn(),
  }
}

function makeUserMessage(): MessageWithInfo {
  return { info: { role: "user" }, parts: [{ type: "text", text: "continue" }] }
}

describe("injectSkillReload — context capability gating (D-04)", () => {
  it("injects recovery protocol when context is enabled", async () => {
    const sessionStore = new SessionStore({ max: 10 })
    sessionStore.upsert("ses-recovery", (s) => {
      s.needsRecoveryInjection = true
    })
    const ctx: SkillReloadInjectorContext = {
      sessionStore,
      contextLogger: createMockLogger(),
      capabilities: { contextEnabled: true },
    }
    const message = makeUserMessage()

    await injectSkillReload(ctx, "ses-recovery", message)

    const text = message.parts?.map((p) => (p as { text?: string }).text).join("\n") ?? ""
    expect(text).toContain("Execute recovery protocol")
  })

  it("does not inject recovery protocol when context is disabled", async () => {
    const sessionStore = new SessionStore({ max: 10 })
    sessionStore.upsert("ses-recovery", (s) => {
      s.needsRecoveryInjection = true
    })
    const ctx: SkillReloadInjectorContext = {
      sessionStore,
      contextLogger: createMockLogger(),
      capabilities: { contextEnabled: false },
    }
    const message = makeUserMessage()

    await injectSkillReload(ctx, "ses-recovery", message)

    const text = message.parts?.map((p) => (p as { text?: string }).text).join("\n") ?? ""
    expect(text).not.toContain("Execute recovery protocol")
  })

  it("does not inject legacy skill-reload reminder when context is disabled", async () => {
    const sessionStore = new SessionStore({ max: 10 })
    sessionStore.upsert("ses-skill", (s) => {
      s.needsSkillReload = true
      s.loadedSkills.add("space-master")
    })
    const ctx: SkillReloadInjectorContext = {
      sessionStore,
      contextLogger: createMockLogger(),
      capabilities: { contextEnabled: false },
    }
    const message = makeUserMessage()

    await injectSkillReload(ctx, "ses-skill", message)

    expect(message.parts).toHaveLength(1)
    expect(sessionStore.get("ses-skill")?.needsSkillReload).toBeUndefined()
  })

  it("injects legacy skill-reload reminder when context is enabled", async () => {
    const sessionStore = new SessionStore({ max: 10 })
    sessionStore.upsert("ses-skill", (s) => {
      s.needsSkillReload = true
      s.loadedSkills.add("space-master")
    })
    const ctx: SkillReloadInjectorContext = {
      sessionStore,
      contextLogger: createMockLogger(),
      capabilities: { contextEnabled: true },
    }
    const message = makeUserMessage()

    await injectSkillReload(ctx, "ses-skill", message)

    const text = message.parts?.map((p) => (p as { text?: string }).text).join("\n") ?? ""
    expect(text).toContain("请重新加载这些技能")
    expect(sessionStore.get("ses-skill")?.needsSkillReload).toBeUndefined()
  })
})

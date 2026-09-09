import { describe, it, expect, vi, beforeEach } from "vitest"
import type { WopalTask, OpenCodeClient, SessionMessage } from "../types.js"
import type { LoggerInstance } from "../logger.js"
import type { SessionStore } from "../session-store.js"
import {
  sendProgressNotification,
  notifyParent,
  sendNotification,
  resolveChildModelString,
  formatChildContextLine,
} from "./task-notifier.js"
import { createSessionStore } from "../session-store.js"

const mockLogger: LoggerInstance = {
  trace: vi.fn(),
  debug: vi.fn(),
  info: vi.fn(),
  warn: vi.fn(),
  error: vi.fn(),
  fatal: vi.fn(),
}

function storeWithChildModel(overrides?: {
  providerID?: string
  modelID?: string
  contextLimit?: number
  tokens?: { input: number; output: number; cache?: { read?: number; write?: number }; updatedAt: number }
}): SessionStore {
  const store = createSessionStore()
  store.upsert("session-123", (state) => {
    state.providerID = overrides?.providerID ?? "deepseek"
    state.modelID = overrides?.modelID ?? "deepseek-chat"
    if (overrides?.contextLimit !== undefined) state.contextLimit = overrides.contextLimit
    if (overrides?.tokens) state.lastTokens = overrides.tokens
  })
  return store
};

describe("task-notifier", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe("sendProgressNotification", () => {
    it("contains all required fields in notification text", async () => {
      const mockPromptAsync = vi.fn().mockResolvedValue(undefined)
      const mockMessages = vi.fn().mockResolvedValue({
        data: [
          {
            info: { role: "assistant" },
            parts: [
              { type: "text", text: "Task output text" },
              { type: "tool", tool: "bash" },
              { type: "tool", tool: "bash" },
              { type: "tool", tool: "read" },
              { type: "tool", tool: "todowrite", state: { input: { todos: [{ status: "completed" }] } } },
            ],
          },
        ],
      })

      const client: OpenCodeClient = {
        session: {
          promptAsync: mockPromptAsync,
          messages: mockMessages,
        },
      } as OpenCodeClient

      const task: WopalTask = {
        id: "wopal-task-123",
        sessionID: "session-123",
        parentSessionID: "parent-456",
        description: "Test task",
        status: "running",
        createdAt: new Date(),
        startedAt: new Date(Date.now() - 3 * 60 * 1000),
        agent: "test-agent",
        prompt: "test",
      }

      await sendProgressNotification(
        { client, debugLog: mockLogger },
        task,
        42,
        65,
        "time_quota",
      )

      expect(mockPromptAsync).toHaveBeenCalledOnce()
      const callArg = mockPromptAsync.mock.calls[0][0]
      const notificationText = callArg.body.parts[0].text

      // Verify required fields
      expect(notificationText).toContain("wopal-task-123")
      expect(notificationText).toContain("**Agent:** test-agent")
      expect(notificationText).toContain("Test task")
      expect(notificationText).toContain("42 messages")
      expect(notificationText).toContain("65% used ⚠️") // Context warning
      expect(notificationText).toContain("3m") // Runtime
      expect(notificationText).toContain("time quota elapsed") // Trigger
      expect(notificationText).toContain("4 calls") // Tool count (bash:2, read:1, todowrite:1)
      expect(notificationText).toContain("bash:2") // Top tool
      expect(notificationText).toContain("✓1 (1/1, 100%)") // Todo summary with percentage
      expect(notificationText).toContain("Task output text") // Last output
    })

    it("PROGRESS notification contains child model line from sessionStore", async () => {
      const mockPromptAsync = vi.fn().mockResolvedValue(undefined)
      const mockMessages = vi.fn().mockResolvedValue({ data: [] })
      const client: OpenCodeClient = {
        session: {
          promptAsync: mockPromptAsync,
          messages: mockMessages,
        },
      } as OpenCodeClient

      const task: WopalTask = {
        id: "wopal-task-123",
        sessionID: "session-123",
        parentSessionID: "parent-456",
        description: "Test task",
        status: "running",
        createdAt: new Date(),
        startedAt: new Date(),
        agent: "test",
        prompt: "test",
      }

      await sendProgressNotification(
        { client, debugLog: mockLogger, sessionStore: storeWithChildModel() },
        task,
        10,
        null,
      )

      const notificationText = mockPromptAsync.mock.calls[0][0].body.parts[0].text
      expect(notificationText).toContain("**Model:** deepseek/deepseek-chat")
    })

    it("PROGRESS notification omits model line when store has no model info", async () => {
      const mockPromptAsync = vi.fn().mockResolvedValue(undefined)
      const client: OpenCodeClient = {
        session: { promptAsync: mockPromptAsync },
      } as OpenCodeClient

      const task: WopalTask = {
        id: "wopal-task-123",
        sessionID: "session-123",
        parentSessionID: "parent-456",
        description: "Test task",
        status: "running",
        createdAt: new Date(),
        startedAt: new Date(),
        agent: "test",
        prompt: "test",
      }

      await sendProgressNotification(
        { client, debugLog: mockLogger },
        task,
        10,
        null,
      )

      const notificationText = mockPromptAsync.mock.calls[0][0].body.parts[0].text
      expect(notificationText).not.toContain("**Model:**")
    })

    it("does not crash when messages API fails", async () => {
      const mockPromptAsync = vi.fn().mockResolvedValue(undefined)
      const mockMessages = vi.fn().mockRejectedValue(new Error("API failure"))
      const client: OpenCodeClient = {
        session: {
          promptAsync: mockPromptAsync,
          messages: mockMessages,
        },
      } as OpenCodeClient

      const task: WopalTask = {
        id: "wopal-task-123",
        sessionID: "session-123",
        parentSessionID: "parent-456",
        description: "Test task",
        status: "running",
        startedAt: new Date(),
        createdAt: new Date(),
        agent: "test",
        prompt: "test",
      }

      await sendProgressNotification(
        { client, debugLog: mockLogger },
        task,
        42,
        null,
      )

      expect(mockPromptAsync).toHaveBeenCalledOnce()
    })
  })

  describe("notifyParent", () => {
    it("IDLE notification contains tools/todos/last output", async () => {
      const mockPromptAsync = vi.fn().mockResolvedValue(undefined)
      const mockMessages = vi.fn().mockResolvedValue({
        data: [
          {
            info: { role: "assistant" },
            parts: [
              { type: "text", text: "Task completed successfully" },
              { type: "tool", tool: "bash" },
              { type: "tool", tool: "todowrite", state: { input: { todos: [{ status: "completed" }, { status: "completed" }] } } },
            ],
          },
        ],
      })

      const client: OpenCodeClient = {
        session: {
          promptAsync: mockPromptAsync,
          messages: mockMessages,
        },
      } as OpenCodeClient

      const task: WopalTask = {
        id: "wopal-task-123",
        sessionID: "session-123",
        parentSessionID: "parent-456",
        description: "Test task",
        status: "idle",
        createdAt: new Date(),
        agent: "test",
        prompt: "test",
      }

      await notifyParent({ client, debugLog: mockLogger }, task)

      expect(mockPromptAsync).toHaveBeenCalledOnce()
      const notificationText = mockPromptAsync.mock.calls[0][0].body.parts[0].text

      expect(notificationText).toContain("[WOPAL TASK IDLE]")
      expect(notificationText).toContain("**Agent:** test")
      expect(notificationText).toContain("✓2 (2/2, 100%)") // Todo summary with percentage
      expect(notificationText).toContain("Task completed successfully") // Last output
    })

    it("STUCK notification stays concise (no enrichment)", async () => {
      const mockPromptAsync = vi.fn().mockResolvedValue(undefined)
      const mockMessages = vi.fn().mockResolvedValue({
        data: [{ info: { role: "assistant" }, parts: [{ type: "text", text: "Output" }] }],
      })

      const client: OpenCodeClient = {
        session: {
          promptAsync: mockPromptAsync,
          messages: mockMessages,
        },
      } as OpenCodeClient

      const task: WopalTask = {
        id: "wopal-task-123",
        sessionID: "session-123",
        parentSessionID: "parent-456",
        description: "Test task",
        status: "stuck",
        error: "Task crashed with timeout",
        createdAt: new Date(),
        agent: "test",
        prompt: "test",
      }

      await notifyParent({ client, debugLog: mockLogger }, task)

      expect(mockPromptAsync).toHaveBeenCalledOnce()
      expect(mockMessages).not.toHaveBeenCalled() // No message fetch for error
      const notificationText = mockPromptAsync.mock.calls[0][0].body.parts[0].text

      expect(notificationText).toContain("[WOPAL TASK STUCK]")
      expect(notificationText).toContain("**Agent:** test")
      expect(notificationText).toContain("Task crashed with timeout")
      expect(notificationText).toContain("wopal_task_reply")
      expect(notificationText).not.toContain("Tools:")
      expect(notificationText).not.toContain("Todos:")
      expect(notificationText).not.toContain("Last output:")
    })

    it("ERR notification is finish-only and not resumable", async () => {
      const mockPromptAsync = vi.fn().mockResolvedValue(undefined)
      const client: OpenCodeClient = {
        session: { promptAsync: mockPromptAsync },
      } as OpenCodeClient

      const task: WopalTask = {
        id: "wopal-task-123",
        sessionID: "session-123",
        parentSessionID: "parent-456",
        description: "Invalid agent",
        status: "error",
        error: "Agent not found",
        createdAt: new Date(),
        agent: "nonexistent-agent",
        prompt: "test",
      }

      await notifyParent({ client, debugLog: mockLogger }, task)

      const notificationText = mockPromptAsync.mock.calls[0][0].body.parts[0].text
      expect(notificationText).toContain("[WOPAL TASK ERR]")
      expect(notificationText).toContain("Agent not found")
      expect(notificationText).toContain("cannot be resumed")
      expect(notificationText).toContain("wopal_task_finish")
      expect(notificationText).not.toContain("wopal_task_reply")
    })

    it("does not fetch messages when task.error is set", async () => {
      const mockPromptAsync = vi.fn().mockResolvedValue(undefined)
      const mockMessages = vi.fn().mockResolvedValue({ data: [] })
      const client: OpenCodeClient = {
        session: {
          promptAsync: mockPromptAsync,
          messages: mockMessages,
        },
      } as OpenCodeClient

      const task: WopalTask = {
        id: "wopal-task-123",
        sessionID: "session-123",
        parentSessionID: "parent-456",
        description: "Test task",
        status: "stuck",
        error: "Error occurred",
        createdAt: new Date(),
        agent: "test",
        prompt: "test",
      }

      await notifyParent({ client, debugLog: mockLogger }, task)

      expect(mockMessages).not.toHaveBeenCalled()
    })

    it("fetches messages only for idle non-error", async () => {
      const mockPromptAsync = vi.fn().mockResolvedValue(undefined)
      const mockMessages = vi.fn().mockResolvedValue({ data: [] })
      const client: OpenCodeClient = {
        session: {
          promptAsync: mockPromptAsync,
          messages: mockMessages,
        },
      } as OpenCodeClient

      const task: WopalTask = {
        id: "wopal-task-123",
        sessionID: "session-123",
        parentSessionID: "parent-456",
        description: "Test task",
        status: "idle",
        createdAt: new Date(),
        agent: "test",
        prompt: "test",
      }

      await notifyParent({ client, debugLog: mockLogger }, task)

      expect(mockMessages).toHaveBeenCalledOnce()
    })

    it("IDLE notification contains child model and context lines from sessionStore", async () => {
      const mockPromptAsync = vi.fn().mockResolvedValue(undefined)
      const mockMessages = vi.fn().mockResolvedValue({ data: [] })
      const client: OpenCodeClient = {
        session: {
          promptAsync: mockPromptAsync,
          messages: mockMessages,
        },
      } as OpenCodeClient

      const task: WopalTask = {
        id: "wopal-task-123",
        sessionID: "session-123",
        parentSessionID: "parent-456",
        description: "Test task",
        status: "idle",
        createdAt: new Date(),
        agent: "test",
        prompt: "test",
      }

      await notifyParent(
        {
          client,
          debugLog: mockLogger,
          sessionStore: storeWithChildModel({
            contextLimit: 200000,
            tokens: { input: 120000, output: 0, cache: { read: 40000 }, updatedAt: Date.now() },
          }),
        },
        task,
      )

      const notificationText = mockPromptAsync.mock.calls[0][0].body.parts[0].text
      expect(notificationText).toContain("**Model:** deepseek/deepseek-chat")
      expect(notificationText).toContain("**Context:** 80% used")
    })

    it("STUCK notification contains child model line without context line", async () => {
      const mockPromptAsync = vi.fn().mockResolvedValue(undefined)
      const client: OpenCodeClient = {
        session: { promptAsync: mockPromptAsync },
      } as OpenCodeClient

      const task: WopalTask = {
        id: "wopal-task-123",
        sessionID: "session-123",
        parentSessionID: "parent-456",
        description: "Test task",
        status: "stuck",
        createdAt: new Date(),
        agent: "test",
        prompt: "test",
      }

      await notifyParent(
        { client, debugLog: mockLogger, sessionStore: storeWithChildModel() },
        task,
      )

      const notificationText = mockPromptAsync.mock.calls[0][0].body.parts[0].text
      expect(notificationText).toContain("**Model:** deepseek/deepseek-chat")
      expect(notificationText).not.toContain("**Context:**")
    })

    it("notifications degrade silently when child model is unavailable", async () => {
      const mockPromptAsync = vi.fn().mockResolvedValue(undefined)
      const client: OpenCodeClient = {
        session: { promptAsync: mockPromptAsync },
      } as OpenCodeClient

      const task: WopalTask = {
        id: "wopal-task-123",
        sessionID: "session-123",
        parentSessionID: "parent-456",
        description: "Test task",
        status: "idle",
        createdAt: new Date(),
        agent: "test",
        prompt: "test",
      }

      await notifyParent({ client, debugLog: mockLogger }, task)

      const notificationText = mockPromptAsync.mock.calls[0][0].body.parts[0].text
      expect(notificationText).not.toContain("**Model:**")
      expect(notificationText).not.toContain("**Context:**")
    })
  })

  describe("resolveChildModelString", () => {
    const client: OpenCodeClient = {
      session: { promptAsync: vi.fn() },
    } as OpenCodeClient

    it("returns provider/model from sessionStore", async () => {
      const model = await resolveChildModelString(
        { client, debugLog: mockLogger, sessionStore: storeWithChildModel() },
        "session-123",
      )
      expect(model).toBe("deepseek/deepseek-chat")
    })

    it("falls back to messages API when store lacks model", async () => {
      const messagesClient: OpenCodeClient = {
        session: {
          messages: vi.fn().mockResolvedValue({
            data: [
              {
                info: {
                  role: "assistant",
                  providerID: "anthropic",
                  modelID: "claude-sonnet",
                },
                parts: [],
              },
            ],
          }),
        },
      } as unknown as OpenCodeClient

      const model = await resolveChildModelString(
        { client: messagesClient, debugLog: mockLogger },
        "session-999",
      )
      expect(model).toBe("anthropic/claude-sonnet")
    })

    it("returns null when neither store nor messages API yield a model", async () => {
      const emptyClient: OpenCodeClient = {
        session: { messages: vi.fn().mockResolvedValue({ data: [] }) },
      } as OpenCodeClient

      const model = await resolveChildModelString(
        { client: emptyClient, debugLog: mockLogger },
        "session-999",
      )
      expect(model).toBeNull()
    })
  })

  describe("formatChildContextLine", () => {
    it("returns context line when store has tokens and contextLimit", () => {
      const line = formatChildContextLine(
        storeWithChildModel({
          contextLimit: 100000,
          tokens: { input: 30000, output: 0, updatedAt: Date.now() },
        }),
        "session-123",
      )
      expect(line).toBe("\n**Context:** 30% used")
    })

    it("returns empty string when store has no token data", () => {
      expect(formatChildContextLine(undefined, "session-123")).toBe("")
      expect(formatChildContextLine(createSessionStore(), "session-123")).toBe("")
    })
  })

  describe("sendNotification", () => {
    it("returns true on success", async () => {
      const mockPromptAsync = vi.fn().mockResolvedValue(undefined)
      const client: OpenCodeClient = {
        session: { promptAsync: mockPromptAsync },
      } as OpenCodeClient

      const result = await sendNotification(
        { client, debugLog: mockLogger },
        "parent-123",
        "Test notification",
      )

      expect(result).toBe(true)
      expect(mockPromptAsync).toHaveBeenCalledWith({
        path: { id: "parent-123" },
        body: {
          noReply: false,
          parts: [{ type: "text", text: "Test notification" }],
        },
      })
    })

    it("returns false on failure", async () => {
      const mockPromptAsync = vi.fn().mockRejectedValue(new Error("Network error"))
      const client: OpenCodeClient = {
        session: { promptAsync: mockPromptAsync },
      } as OpenCodeClient

      const result = await sendNotification(
        { client, debugLog: mockLogger },
        "parent-123",
        "Test notification",
      )

      expect(result).toBe(false)
    })

    it("returns false when promptAsync unavailable", async () => {
      const client: OpenCodeClient = {
        session: {},
      } as OpenCodeClient

      const result = await sendNotification(
        { client, debugLog: mockLogger },
        "parent-123",
        "Test notification",
      )

      expect(result).toBe(false)
    })

    it("noReply defaults to false for task notifications", async () => {
      const mockPromptAsync = vi.fn().mockResolvedValue(undefined)
      const client: OpenCodeClient = {
        session: { promptAsync: mockPromptAsync },
      } as OpenCodeClient

      await sendNotification(
        { client, debugLog: mockLogger },
        "parent-123",
        "Task notification",
      )

      expect(mockPromptAsync.mock.calls[0][0].body.noReply).toBe(false)
    })

    it("noReply is true for permission notifications", async () => {
      const mockPromptAsync = vi.fn().mockResolvedValue(undefined)
      const client: OpenCodeClient = {
        session: { promptAsync: mockPromptAsync },
      } as OpenCodeClient

      await sendNotification(
        { client, debugLog: mockLogger },
        "parent-123",
        "Permission notification",
        true,
      )

      expect(mockPromptAsync.mock.calls[0][0].body.noReply).toBe(true)
    })
  })
})

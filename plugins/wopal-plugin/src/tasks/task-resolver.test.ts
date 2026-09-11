import { describe, expect, it } from "vitest"
import {
  resolveTask,
  formatAmbiguousErrorMessage,
  formatNotFoundErrorMessage,
  MIN_FUZZY_QUERY_LENGTH,
} from "./task-resolver.js"
import type { WopalTask } from "../types.js"

function createTask(overrides?: Partial<WopalTask>): WopalTask {
  return {
    id: "wopal-task-1bcbb6eacffeD6Mr5eedcZH1hZ",
    sessionID: "ses_1bcbb6eacffeD6Mr5eedcZH1hZ",
    status: "running",
    description: "Test task",
    agent: "fae",
    prompt: "Do something",
    parentSessionID: "parent-1",
    createdAt: new Date(),
    ...overrides,
  }
}

describe("resolveTask", () => {
  describe("exact matching", () => {
    it("returns exact match for a full task ID", () => {
      const task = createTask()
      const result = resolveTask([task], task.id)

      expect(result).toEqual({ type: "exact", task })
    })

    it("prefers exact match over fuzzy match when the ID is also a prefix of another task", () => {
      const shortTask = createTask({ id: "wopal-task-1" })
      const longTask = createTask({ id: "wopal-task-12" })
      const result = resolveTask([shortTask, longTask], "wopal-task-1")

      expect(result).toEqual({ type: "exact", task: shortTask })
    })

    it("matches exact ID regardless of other tasks in the set", () => {
      const a = createTask({ id: "wopal-task-aaa" })
      const b = createTask({ id: "wopal-task-bbb" })
      const result = resolveTask([a, b], "wopal-task-bbb")

      expect(result).toEqual({ type: "exact", task: b })
    })
  })

  describe("prefix matching", () => {
    it("resolves a unique truncated prefix (compaction summary scenario)", () => {
      const task = createTask()
      const result = resolveTask([task], "wopal-task-1bcbb6eacffe")

      expect(result).toEqual({ type: "unique", task, matchedBy: "prefix" })
    })

    it("resolves a bare truncated prefix without the wopal-task- decoration via normalized", () => {
      const task = createTask()
      const result = resolveTask([task], "1bcbb6eacffe")

      expect(result).toEqual({ type: "unique", task, matchedBy: "normalized" })
    })
  })

  describe("suffix matching", () => {
    it("resolves a unique trailing hash fragment (debug log scenario)", () => {
      const task = createTask()
      const result = resolveTask([task], "D6Mr5eedcZH1hZ")

      expect(result).toEqual({ type: "unique", task, matchedBy: "suffix" })
    })

    it("resolves a formatSessionID-style suffix with (task) decoration", () => {
      const task = createTask()
      const result = resolveTask([task], "D6Mr5eedcZH1hZ(task)")

      expect(result).toEqual({ type: "unique", task, matchedBy: "suffix" })
    })
  })

  describe("normalized (hash body) matching", () => {
    it("resolves a bare full hash without prefix", () => {
      const task = createTask()
      const result = resolveTask([task], "1bcbb6eacffeD6Mr5eedcZH1hZ")

      expect(result).toEqual({ type: "unique", task, matchedBy: "normalized" })
    })

    it("resolves a full session ID (ses_ form)", () => {
      const task = createTask()
      const result = resolveTask([task], "ses_1bcbb6eacffeD6Mr5eedcZH1hZ")

      expect(result).toEqual({ type: "unique", task, matchedBy: "normalized" })
    })

    it("resolves a bare hash fragment via body prefix", () => {
      const task = createTask()
      const result = resolveTask([task], "1bcbb6eac")

      expect(result).toEqual({ type: "unique", task, matchedBy: "normalized" })
    })
  })

  describe("ambiguity hard-blocking", () => {
    it("rejects when multiple tasks share the queried prefix", () => {
      const a = createTask({ id: "wopal-task-1bcbb6eacffeAAA", description: "Task A" })
      const b = createTask({ id: "wopal-task-1bcbb6eacffeBBB", description: "Task B" })
      const result = resolveTask([a, b], "wopal-task-1bcbb6eacffe")

      expect(result.type).toBe("ambiguous")
      if (result.type !== "ambiguous") throw new Error("expected ambiguous")
      expect(result.query).toBe("wopal-task-1bcbb6eacffe")
      expect(result.candidates).toHaveLength(2)
      expect(result.candidates.map((t) => t.id)).toEqual([a.id, b.id])
    })

    it("rejects when multiple tasks share the queried suffix", () => {
      const a = createTask({ id: "wopal-task-AAA123456", description: "Task A" })
      const b = createTask({ id: "wopal-task-BBB123456", description: "Task B" })
      const result = resolveTask([a, b], "123456")

      expect(result.type).toBe("ambiguous")
      if (result.type !== "ambiguous") throw new Error("expected ambiguous")
      expect(result.candidates).toHaveLength(2)
    })

    it("rejects when multiple tasks share the queried hash body", () => {
      const a = createTask({ id: "wopal-task-abc123XXX" })
      const b = createTask({ id: "wopal-task-abc123YYY" })
      const result = resolveTask([a, b], "abc123")

      expect(result.type).toBe("ambiguous")
      if (result.type !== "ambiguous") throw new Error("expected ambiguous")
      expect(result.candidates).toHaveLength(2)
    })

    it("rejects the shared wopal-task- prefix that hits every task", () => {
      const a = createTask({ id: "wopal-task-aaa" })
      const b = createTask({ id: "wopal-task-bbb" })
      const result = resolveTask([a, b], "wopal-task-")

      expect(result.type).toBe("ambiguous")
      if (result.type !== "ambiguous") throw new Error("expected ambiguous")
      expect(result.candidates).toHaveLength(2)
    })

    it("deduplicates a candidate matching multiple modes and reports it as unique", () => {
      const task = createTask()
      // "wopal-task-1bcbb6" is both a prefix and (after normalization) a body prefix
      const result = resolveTask([task], "wopal-task-1bcbb6")

      expect(result).toEqual({ type: "unique", task, matchedBy: "prefix" })
    })

    it("reports ambiguity even when the query is a prefix of one task and a suffix of another", () => {
      const a = createTask({ id: "wopal-task-abcdef" })
      const b = createTask({ id: "wopal-task-xyzabc" })
      const result = resolveTask([a, b], "abc")

      expect(result.type).toBe("ambiguous")
      if (result.type !== "ambiguous") throw new Error("expected ambiguous")
      expect(result.candidates).toHaveLength(2)
    })
  })

  describe("not found", () => {
    it("returns not_found with available tasks when nothing matches", () => {
      const a = createTask({ id: "wopal-task-aaa" })
      const b = createTask({ id: "wopal-task-bbb" })
      const result = resolveTask([a, b], "wopal-task-zzz")

      expect(result.type).toBe("not_found")
      if (result.type !== "not_found") throw new Error("expected not_found")
      expect(result.query).toBe("wopal-task-zzz")
      expect(result.availableTasks).toEqual([a, b])
    })

    it("returns not_found with empty availableTasks when task set is empty", () => {
      const result = resolveTask([], "wopal-task-abc")

      expect(result.type).toBe("not_found")
      if (result.type !== "not_found") throw new Error("expected not_found")
      expect(result.availableTasks).toEqual([])
    })

    it("returns not_found for empty query", () => {
      const task = createTask()
      const result = resolveTask([task], "")

      expect(result.type).toBe("not_found")
      if (result.type !== "not_found") throw new Error("expected not_found")
      expect(result.availableTasks).toEqual([task])
    })

    it("returns not_found for whitespace-only query", () => {
      const task = createTask()
      const result = resolveTask([task], "   ")

      expect(result.type).toBe("not_found")
    })
  })

  describe("minimum query length guard", () => {
    it(`rejects fuzzy matching for queries shorter than ${MIN_FUZZY_QUERY_LENGTH} chars`, () => {
      const task = createTask()
      // "1b" would uniquely prefix-match, but is too short — fuzzy refused
      const result = resolveTask([task], "1b")

      expect(result.type).toBe("not_found")
      if (result.type !== "not_found") throw new Error("expected not_found")
      expect(result.availableTasks).toEqual([task])
    })

    it("still allows exact match for short queries", () => {
      const task = createTask({ id: "wopal-task-ab" })
      const result = resolveTask([task], "wopal-task-ab")

      expect(result).toEqual({ type: "exact", task })
    })

    it("allows fuzzy matching at exactly the minimum length", () => {
      const task = createTask()
      const result = resolveTask([task], "1bc")

      expect(result).toEqual({ type: "unique", task, matchedBy: "normalized" })
    })
  })

  describe("input hygiene", () => {
    it("trims surrounding whitespace from the query", () => {
      const task = createTask()
      const result = resolveTask([task], "  wopal-task-1bcbb6eacffe  ")

      expect(result).toEqual({ type: "unique", task, matchedBy: "prefix" })
    })

    it("works with any Iterable input", () => {
      const task = createTask()
      const set = new Set([task])
      const result = resolveTask(set, task.id)

      expect(result).toEqual({ type: "exact", task })
    })
  })
})

describe("formatAmbiguousErrorMessage", () => {
  it("lists all candidates with IDs, status and description", () => {
    const a = createTask({ id: "wopal-task-aaa", description: "Task A" })
    const b = createTask({ id: "wopal-task-bbb", description: "Task B" })
    const message = formatAmbiguousErrorMessage("wopal-task-a", [a, b])

    expect(message).toContain("wopal-task-a")
    expect(message).toContain("Ambiguous task reference")
    expect(message).not.toContain("(ambiguous)")
    expect(message).not.toContain("Task IDs are ambiguous; use one of the full task IDs")
    expect(message).toContain("wopal-task-aaa")
    expect(message).toContain("wopal-task-bbb")
    expect(message).toContain("Task A")
    expect(message).toContain("Task B")
    expect(message).toContain("running")
  })
})

describe("formatNotFoundErrorMessage", () => {
  it("lists available tasks when they exist", () => {
    const a = createTask({ id: "wopal-task-aaa", description: "Task A" })
    const message = formatNotFoundErrorMessage("wopal-task-zzz", [a])

    expect(message).toContain("wopal-task-zzz")
    expect(message).toContain("wopal-task-aaa")
    expect(message).toContain("Task A")
  })

  it("explains there are no active tasks when the list is empty", () => {
    const message = formatNotFoundErrorMessage("wopal-task-zzz", [])

    expect(message).toContain("wopal-task-zzz")
    expect(message).toContain("No active tasks")
  })
})

import { tool, type ToolDefinition, type ToolContext } from "@opencode-ai/plugin";
import type { MemoryStore, MemoryCategory } from "../../memory/store.js";
import type { EmbeddingClient } from "../../memory/embedder.js";
import type { SessionStore } from "../../session-store.js";
import { ECHO_REMINDER } from "./formatters.js";
import { formatList, formatStats, formatSearch, deleteMemories, addMemory, updateMemory, formatInjected } from "./crud.js";

export function createMemoryManageTool(
  store: MemoryStore,
  embedder?: EmbeddingClient,
  sessionStore?: SessionStore,
): ToolDefinition {
  return tool({
    description: `Manage long-term memory in LanceDB.

## Read:
- search: Internal keyword scoring search with compact ranked output. USE PROACTIVELY before complex tasks, when facing ambiguity, or after criticism. No display needed unless user asked.
- stats: Memory system statistics. No display needed unless user asked.
- injected: View memories currently injected into your context. No display needed unless user asked.
- list: User-facing inventory. If user asked to list memories, display the full result.

## Mutation (MUST show full content to user + wait for explicit approval before executing):
- add: Create a memory. Required flow: search for duplicates → show full text to user → wait for approval → execute. Category required.
- update: Modify a memory. Show before/after content to user → wait for approval → execute.
- delete: Remove memories. Show full content of each memory to user → wait for approval → execute.

Categories: requirement, profile, preference, knowledge, fact, gotcha, experience (English only).

⚠️ Tags quality determines retrieval quality. When adding memories, choose 3-5 specific tags that capture the core topic — avoid generic tags like "wopal" or "task". Good: "wopal-plugin,tool-description,prompt-engineering". Bad: "plugin,tool,fix". When searching, combine query + tags for best results.

## Search scoring hints:
- Tag exact match scores +35 (highest priority), text phrase +25, text term +8.
- Combining query + tags can boost relevant memories from score ~20 to ~60+ (tier-breaking boost).
- Use known tags from memory results (e.g., "dev-flow", "wopal-plugin"), don't invent new ones.

⚠️ Showing content then immediately calling the tool WITHOUT waiting for user response = violation. Valid approval signals: "ok", "同意", "写入", "可以". Your own display is NOT confirmation.

ID format: from list/search results in brackets (e.g., [53cc9388] → id="53cc9388"). Never pass body text as id.`,
    args: {
      command: tool.schema
        .enum(["list", "stats", "search", "delete", "add", "update", "injected"])
        .describe("Subcommand"),
      query: tool.schema
        .string()
        .optional()
        .describe("Search keywords or phrase. Search uses deterministic keyword scoring, not vector similarity."),
      category: tool.schema
        .string()
        .optional()
        .describe("Category: requirement/profile/preference/knowledge/fact/gotcha/experience. Required for add, optional for update."),
      limit: tool.schema
        .number()
        .optional()
        .describe("Max items for list/search. Search default: 6, capped at 12."),
      text: tool.schema
        .string()
        .optional()
        .describe("Memory text for add/update (minimum 20 chars for add)"),
      importance: tool.schema
        .number()
        .min(0)
        .max(1)
        .optional()
        .describe("Importance 0-1 (default 0.5 for add)"),
      project: tool.schema
        .string()
        .optional()
        .describe("Project scope (default wopal-space for add)"),
      tags: tool.schema
        .string()
        .optional()
        .describe("Comma-separated keywords for precise retrieval. Add: choose 3-5 specific tags (avoid generic ones). Search: tag exact match = +35 score (highest), combine with query to boost relevant memories. Use existing tags from memory results, not invented ones."),
      id: tool.schema
        .string()
        .optional()
        .describe("Memory ID from list/search brackets (e.g., 53cc9388). Delete accepts comma-separated IDs."),
    },
    execute: async (args, context: ToolContext) => {
      const { command, query, category, limit, text, importance, project, tags, id } = args;

      switch (command) {
        case "list":
          return (await formatList(store, category, limit)) + ECHO_REMINDER;
        case "stats":
          return await formatStats(store);
        case "search":
          return await formatSearch(store, query ?? "", tags, limit);
        case "delete":
          return (await deleteMemories(store, id ?? "")) + ECHO_REMINDER;
        case "add":
          return (await addMemory(store, embedder, text ?? "", category as MemoryCategory | undefined, {
            sessionId: context.sessionID ?? "unknown",
            importance: importance ?? 0.5,
            project: project ?? "wopal-space",
            tags: tags ? tags.split(",").map(s => s.trim()).filter(Boolean) : [],
          })) + ECHO_REMINDER;
        case "update": {
          const updateOpts: { text?: string; category?: MemoryCategory; importance?: number; project?: string; tags?: string[] } = {};
          if (text !== undefined) updateOpts.text = text;
          if (category !== undefined) updateOpts.category = category as MemoryCategory;
          if (importance !== undefined) updateOpts.importance = importance;
          if (project !== undefined) updateOpts.project = project;
          if (tags !== undefined) updateOpts.tags = tags.split(",").map(s => s.trim()).filter(Boolean);
          return (await updateMemory(store, embedder, id ?? "", updateOpts)) + ECHO_REMINDER;
        }
        case "injected":
          return await formatInjected(sessionStore, context.sessionID);
        default:
          return `未知命令: ${command}`;
      }
    },
  });
}

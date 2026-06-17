/**
 * Prompt Loading
 *
 * Loads prompt templates via 4-layer cascading:
 * 1. Env var override (absolute/~/relative path)
 * 2. Space-level: <workspace>/.wopal/prompts/<filename>
 * 3. User-level: WOPAL_HOME/prompts/<filename>
 * 4. Inline fallback (caller provides)
 *
 * Env vars WOPAL_DISTILL_PROMPT_FILE / WOPAL_DEDUP_PROMPT_FILE / WOPAL_TITLE_PROMPT_FILE
 * override file paths with higher priority.
 */

import { homedir } from "os";
import { join } from "path";
import { existsSync, readFileSync } from "fs";
import type { MemoryCategory } from "./types.js";
import { memoryLogger } from "../logger.js";
import { getRuntimeContext } from "../runtime-context.js";

/**
 * Resolve prompt file path from environment variable.
 *
 * Supports:
 * - Absolute path: /path/to/file.md
 * - Home directory: ~/path/to/file.md
 * - Relative path: path/to/file.md (relative to cwd)
 */
function resolveEnvFilePath(envVar: string): string | null {
  const envPath = process.env[envVar];
  if (!envPath) return null;

  if (envPath.startsWith("/")) {
    return envPath;
  }

  if (envPath.startsWith("~/")) {
    return join(homedir(), envPath.slice(2));
  }

  return join(process.cwd(), envPath);
}

/**
 * Resolve a prompt template file via 4-layer cascading.
 * Returns the file path if found, null otherwise (caller falls back to inline default).
 *
 * Layers:
 * 1. Env var override — resolved via resolveEnvFilePath
 * 2. Space-level — .wopal/prompts/<filename> (if running inside a wopal-space)
 * 3. User-level — WOPAL_HOME/prompts/<filename>
 * 4. null — caller uses inline default
 */
export function resolvePromptFile(envVar: string, filename: string): string | null {
  // Layer 1: env var override
  const envPath = resolveEnvFilePath(envVar);
  if (envPath && existsSync(envPath)) {
    return envPath;
  }

  // Layers 2-3 require RuntimeContext (may not be initialized in test contexts)
  let ctx: import("../runtime-context.js").RuntimeContext;
  try {
    ctx = getRuntimeContext();
  } catch {
    return null;
  }

  // Layer 2: space-level template
  if (ctx.isWopalSpace) {
    const spacePath = join(ctx.spaceRoot!, ".wopal", "prompts", filename);
    if (existsSync(spacePath)) {
      return spacePath;
    }
  }

  // Layer 3: user-level template
  const userPath = join(ctx.wopalHome, "prompts", filename);
  if (existsSync(userPath)) {
    return userPath;
  }

  // Layer 4: no file found — caller falls back to inline default
  return null;
}

/**
 * Load a prompt file: env var override → space-level → user-level → null.
 * Returns null if no source is available (caller uses inline default).
 */
function loadPromptFile(envVar: string, filename: string): string | null {
  const filePath = resolvePromptFile(envVar, filename);
  if (!filePath) return null;

  try {
    memoryLogger.debug(`Loaded prompt from: ${filePath}`);
    return readFileSync(filePath, "utf-8");
  } catch (error) {
    memoryLogger.warn(`Failed to load prompt from ${filePath}: ${error}`);
    return null;
  }
}

/** Title generation prompt for session title after compaction */
export function loadTitlePrompt(): string {
  return loadPromptFile("WOPAL_TITLE_PROMPT_FILE", "title.md")
    ?? "You are a title generator. Output ONLY valid JSON: {\"title\":\"Brief natural thread title\"}. The title must be a single line, ≤50 characters, and use the same language as the summary. Never output labels like Thread Title or Title as the title value.\n\n---\nConversation summary:\n{{summary}}";
}

/** Extracted memory from LLM (single-layer body) */
export interface ExtractResult {
  memories: Array<{
    category: MemoryCategory;
    body: string;
    tags: string[];
  }>;
  title?: string;
}

/**
 * Load extraction prompt template.
 */
function loadPromptTemplate(): string {
  return loadPromptFile("WOPAL_DISTILL_PROMPT_FILE", "distill.md")
    ?? "# Memory Extraction\n\nAnalyze the conversation below and extract memories worth preserving for future sessions.\n\n## Recent Conversation\n{{conversation}}\n\n## Output Format\n\nReturn a JSON object:\n{\"memories\": [{\"category\": \"knowledge\", \"body\": \"Title\\n\\nCore content...\", \"tags\": [\"tag\"]}]}\n\nIf nothing to extract, return {\"memories\": []}";
}

/**
 * Build extraction prompt for LLM (always reads from file for hot-reload).
 */
export function buildExtractionPrompt(conversation: string): string {
  return loadPromptTemplate().replace("{{conversation}}", conversation);
}

/**
 * Build deduplication prompt — single LLM call for decision + merge content.
 */
export function buildBatchDedupPrompt(
  candidates: Array<{ index: number; category: string; body: string }>,
  existingByCandidate: Map<number, Array<{ index: number; body: string; id: string }>>
): string {
  const candidatesWithExisting = candidates.filter(
    (c) => existingByCandidate.has(c.index) && existingByCandidate.get(c.index)!.length > 0
  );

  const input = candidatesWithExisting.map((c) => {
    const existing = existingByCandidate.get(c.index)!;
    return {
      candidate: { index: c.index, category: c.category, body: c.body },
      similar_existing: existing.map((e) => ({ index: e.index, body: e.body })),
    };
  });

  const template = loadPromptFile("WOPAL_DEDUP_PROMPT_FILE", "dedup.md")
    ?? "You are a memory deduplicator. For each candidate, compare with similar existing memories and decide: create (unrelated, coexist), skip (discard), merge (supplement), or replace (outdated).\n\nInput:\n{{input}}\n\nOutput JSON:\n{\"decisions\": [{\"index\": 1, \"action\": \"create\"}, {\"index\": 2, \"action\": \"skip\"}, {\"index\": 3, \"action\": \"merge\", \"merge_into\": 1, \"merged_body\": \"...\", \"tags\": [\"tag\"]}]}";

  return template.replace("{{input}}", JSON.stringify(input, null, 2));
}

/**
 * Prompt Loading
 *
 * Loads prompt templates via cascading convention paths:
 * 1. Space-level: <space>/.wopal/prompts/<filename>
 * 2. User-level: WOPAL_HOME/prompts/<filename>
 * 3. Inline fallback (caller provides)
 */

import { join } from "path";
import { existsSync, readFileSync } from "fs";
import type { MemoryCategory } from "./types.js";
import { memoryLogger, type LoggerInstance } from "../logger.js";
import { createRuntimeContext, type RuntimeContext } from "../runtime-context.js";

/**
 * Resolve a prompt template file via convention paths.
 * Returns the file path if found, null otherwise (caller falls back to inline default).
 *
 * Layers:
 * 1. Space-level — .wopal/prompts/<filename> (if running inside a wopal-space)
 * 2. User-level — WOPAL_HOME/prompts/<filename>
 * 3. null — caller uses inline default
 */
function resolveRuntimePromptFile(
  context: RuntimeContext,
  filename: string,
): string | null {
  if (context.wopalSpaceRoot) {
    const spacePath = join(context.wopalSpaceRoot, ".wopal", "prompts", filename);
    if (existsSync(spacePath)) {
      return spacePath;
    }
  }

  const userPath = join(context.wopalHome, "prompts", filename);
  if (existsSync(userPath)) {
    return userPath;
  }

  return null;
}

/**
 * Load a prompt file: space-level → user-level → null.
 * Returns null if no source is available (caller uses inline default).
 */
function loadPromptFile(
  context: RuntimeContext,
  logger: LoggerInstance,
  filename: string,
): string | null {
  const filePath = resolveRuntimePromptFile(context, filename);
  if (!filePath) return null;

  try {
    logger.debug(`Loaded prompt from: ${filePath}`);
    return readFileSync(filePath, "utf-8");
  } catch (error) {
    logger.warn({ err: error }, `Failed to load prompt from ${filePath}`);
    return null;
  }
}

export interface MemoryPrompts {
  resolvePromptFile(filename: string): string | null;
  loadTitlePrompt(): string;
  buildExtractionPrompt(conversation: string): string;
  buildBatchDedupPrompt(
    candidates: Array<{ index: number; category: string; body: string }>,
    existingByCandidate: Map<number, Array<{ index: number; body: string; id: string }>>,
  ): string;
}

const TITLE_FALLBACK = "You are a title generator. Output ONLY valid JSON: {\"title\":\"Brief natural thread title\"}. The title must be a single line, ≤50 characters, and use the same language as the summary. Never output labels like Thread Title or Title as the title value.\n\n---\nConversation summary:\n{{summary}}";
const EXTRACTION_FALLBACK = "# Memory Extraction\n\nAnalyze the conversation below and extract memories worth preserving for future sessions.\n\n## Recent Conversation\n{{conversation}}\n\n## Output Format\n\nReturn a JSON object:\n{\"memories\": [{\"category\": \"knowledge\", \"body\": \"Title\\n\\nCore content...\", \"tags\": [\"tag\"]}]}\n\nIf nothing to extract, return {\"memories\": []}";
const DEDUP_FALLBACK = "You are a memory deduplicator. For each candidate, compare with similar existing memories and decide: create (unrelated, coexist), skip (discard), merge (supplement), or replace (outdated).\n\nInput:\n{{input}}\n\nOutput JSON:\n{\"decisions\": [{\"index\": 1, \"action\": \"create\"}, {\"index\": 2, \"action\": \"skip\"}, {\"index\": 3, \"action\": \"merge\", \"merge_into\": 1, \"merged_body\": \"...\", \"tags\": [\"tag\"]}]}";

export function createMemoryPrompts(
  context: RuntimeContext,
  logger: LoggerInstance = memoryLogger,
): MemoryPrompts {
  const cache = new Map<string, string | null>();
  const load = (filename: string) => {
    if (!cache.has(filename)) {
      cache.set(filename, loadPromptFile(context, logger, filename));
    }
    return cache.get(filename) ?? null;
  };
  return {
    resolvePromptFile: (filename) => resolveRuntimePromptFile(context, filename),
    loadTitlePrompt: () => load("title.md") ?? TITLE_FALLBACK,
    buildExtractionPrompt: (conversation) =>
      (load("distill.md") ?? EXTRACTION_FALLBACK)
        .replace("{{conversation}}", conversation),
    buildBatchDedupPrompt: (candidates, existingByCandidate) => {
      const candidatesWithExisting = candidates.filter(
        (candidate) => (existingByCandidate.get(candidate.index)?.length ?? 0) > 0,
      );
      const input = candidatesWithExisting.map((candidate) => ({
        candidate: {
          index: candidate.index,
          category: candidate.category,
          body: candidate.body,
        },
        similar_existing: existingByCandidate.get(candidate.index)!.map((existing) => ({
          index: existing.index,
          body: existing.body,
        })),
      }));
      return (load("dedup.md") ?? DEDUP_FALLBACK)
        .replace("{{input}}", JSON.stringify(input, null, 2));
    },
  };
}

let sharedPrompts: MemoryPrompts | undefined;

/**
 * Module-level default prompts, built lazily on first call and cached for
 * subsequent invocations. Avoids filesystem access at import time.
 */
function sharedDefaultPrompts(): MemoryPrompts {
  sharedPrompts ??= (() => {
    const context = createRuntimeContext({
      directory: process.cwd(),
      ...(process.env.WOPAL_HOME ? { wopalHome: process.env.WOPAL_HOME } : {}),
    });
    return createMemoryPrompts(context);
  })();
  return sharedPrompts;
}

export function resolvePromptFile(filename: string): string | null {
  return sharedDefaultPrompts().resolvePromptFile(filename);
}

export function loadTitlePrompt(): string {
  return sharedDefaultPrompts().loadTitlePrompt();
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
export function buildExtractionPrompt(conversation: string): string {
  return sharedDefaultPrompts().buildExtractionPrompt(conversation);
}

/**
 * Build deduplication prompt — single LLM call for decision + merge content.
 */
export function buildBatchDedupPrompt(
  candidates: Array<{ index: number; category: string; body: string }>,
  existingByCandidate: Map<number, Array<{ index: number; body: string; id: string }>>
): string {
  return sharedDefaultPrompts().buildBatchDedupPrompt(candidates, existingByCandidate);
}

/**
 * Context Prompt Loading
 *
 * Loads context-side prompt templates (session title generation and session
 * distillation extraction) via the shared convention-path resolver, and
 * composes the memory-owned deduplication prompt into a single facade.
 *
 * Resolution order (see memory/prompts.ts):
 * 1. Space-level: <space>/.wopal/prompts/<filename>
 * 2. User-level: WOPAL_HOME/prompts/<filename>
 * 3. Inline fallback (caller provides)
 */

import type { MemoryCategory } from "../memory/types.js";
import { contextLogger, type LoggerInstance } from "../logger.js";
import { createRuntimeContext, type RuntimeContext } from "../runtime-context.js";
import {
  createMemoryPrompts,
  loadPromptFile,
  type MemoryPrompts,
} from "../memory/prompts.js";

export interface ContextPrompts extends MemoryPrompts {
  loadTitlePrompt(): string;
  buildExtractionPrompt(conversation: string): string;
}

const TITLE_FALLBACK = "You are a title generator. Output ONLY valid JSON: {\"title\":\"Brief natural thread title\"}. The title must be a single line, ≤50 characters, and use the same language as the summary. Never output labels like Thread Title or Title as the title value.\n\n---\nConversation summary:\n{{summary}}";
const EXTRACTION_FALLBACK = "# Memory Extraction\n\nAnalyze the conversation below and extract memories worth preserving for future sessions.\n\n## Recent Conversation\n{{conversation}}\n\n## Output Format\n\nReturn a JSON object:\n{\"memories\": [{\"category\": \"knowledge\", \"body\": \"Title\\n\\nCore content...\", \"tags\": [\"tag\"]}]}\n\nIf nothing to extract, return {\"memories\": []}";

export function createContextPrompts(
  context: RuntimeContext,
  logger: LoggerInstance = contextLogger,
): ContextPrompts {
  const cache = new Map<string, string | null>();
  const load = (filename: string) => {
    if (!cache.has(filename)) {
      cache.set(filename, loadPromptFile(context, logger, filename));
    }
    return cache.get(filename) ?? null;
  };
  return {
    ...createMemoryPrompts(context, logger),
    loadTitlePrompt: () => load("title.md") ?? TITLE_FALLBACK,
    buildExtractionPrompt: (conversation) =>
      (load("distill.md") ?? EXTRACTION_FALLBACK)
        .replace("{{conversation}}", conversation),
  };
}

let sharedPrompts: ContextPrompts | undefined;

/**
 * Module-level default prompts, built lazily on first call and cached for
 * subsequent invocations. Avoids filesystem access at import time.
 */
function sharedDefaultPrompts(): ContextPrompts {
  sharedPrompts ??= (() => {
    const context = createRuntimeContext({
      directory: process.cwd(),
      ...(process.env.WOPAL_HOME ? { wopalHome: process.env.WOPAL_HOME } : {}),
    });
    return createContextPrompts(context);
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

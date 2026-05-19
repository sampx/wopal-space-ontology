/**
 * Memory Injector - Memory injection into system prompt
 *
 * Handles memory retrieval, child session detection (via session-utils),
 * and delegates context building to conversation-context module.
 */

import type { SessionStore } from "../session-store.js";
import type { MemoryInjector } from "../memory/index.js";
import type { DebugLog } from "../debug.js";
import type { MessageWithInfo } from "./message-context.js";
import type { OpenCodeClient } from "../types.js";
import { isChildSession } from "./session-utils.js";
import { buildEnrichedQuery } from "./conversation-context.js";

export interface MemoryInjectorContext {
  client: OpenCodeClient;
  sessionStore: SessionStore;
  memoryDebugLog: DebugLog;
  memoryInjector: MemoryInjector | undefined;
  childSessionCache: Map<string, boolean>;
  taskManager: { findBySession: (sessionID: string) => unknown } | undefined;
}

export interface SystemTransformOutput {
  system: string[];
}

/**
 * Inject relevant memories into system prompt.
 * All skip decisions (already injected, short/command, child session) are made here
 * so that repeated system.transform calls (e.g. after tool use) exit immediately.
 */
export async function injectMemoriesIntoSystem(
  ctx: MemoryInjectorContext,
  sessionID: string,
  output: SystemTransformOutput,
): Promise<void> {
  if (!ctx.memoryInjector) return;

  const state = ctx.sessionStore.get(sessionID);

  // Gate: only proceed when flagged by chat.message or history seed
  if (!state?.needsMemoryInjection) {
    return;
  }

  // Consume the flag immediately — tool-use re-enters will skip entirely
  ctx.sessionStore.upsert(sessionID, (s) => {
    s.needsMemoryInjection = false;
  });

  // Skip child sessions — check early to avoid wasted retrieval work
  const isChild = await isChildSession(sessionID, {
    client: ctx.client,
    taskManager: ctx.taskManager,
    cache: ctx.childSessionCache,
  });
  if (isChild) {
    clearInjectedMemory(ctx.sessionStore, sessionID);
    ctx.memoryDebugLog("Skipped memory injection for child session");
    return;
  }

  // Skip entirely if memory store is empty
  try {
    if (await ctx.memoryInjector.isEmpty()) {
      clearInjectedMemory(ctx.sessionStore, sessionID);
      return;
    }
  } catch {
    // Store not initialized yet, skip silently
    clearInjectedMemory(ctx.sessionStore, sessionID);
    return;
  }

  const userQuery = state.lastUserPrompt;
  if (!userQuery) {
    clearInjectedMemory(ctx.sessionStore, sessionID);
    ctx.memoryDebugLog("Skipped memory injection (no user query)");
    return;
  }

  // Build enriched query — fetch full session messages for context
  let allMessages: MessageWithInfo[] = [];
  try {
    const messages = await ctx.client.session?.messages?.({
      path: { id: sessionID },
    });
    const data = (messages as { data?: MessageWithInfo[] } | undefined)?.data;
    if (Array.isArray(data)) {
      allMessages = data;
    }
    ctx.memoryDebugLog(
      `API returned ${allMessages.length} messages for context extraction`,
    );
  } catch {
    // Fallback: no messages available
  }

  const enrichedQuery = buildEnrichedQuery(
    ctx.memoryDebugLog,
    sessionID,
    userQuery,
    allMessages,
  );
  if (!enrichedQuery) {
    clearInjectedMemory(ctx.sessionStore, sessionID);
    ctx.memoryDebugLog(
      `Skipped memory injection for short/command input: "${userQuery}"`,
    );
    return;
  }

  // Execute retrieval + injection with timeout guard
  try {
    let timedOut = false;
    const injectPromise = doInjectMemories(
      ctx,
      sessionID,
      output,
      enrichedQuery,
      () => timedOut,
    );
    const timeoutPromise = new Promise<"timeout">((resolve) =>
      setTimeout(() => resolve("timeout"), 8_000),
    );
    const result = await Promise.race([injectPromise, timeoutPromise]);
    if (result === "timeout") {
      timedOut = true;
      clearInjectedMemory(ctx.sessionStore, sessionID);
      ctx.memoryDebugLog("Memory injection timed out (8s), skipping");
    }
    // Suppress unhandled rejection from the loser of Promise.race
    injectPromise.catch(() => {});
  } catch (error) {
    clearInjectedMemory(ctx.sessionStore, sessionID);
    ctx.memoryDebugLog(`Memory injection failed: ${error}`);
  }
}

/**
 * Pure retrieval + injection. All skip decisions are made by the caller.
 */
async function doInjectMemories(
  ctx: MemoryInjectorContext,
  sessionID: string,
  output: SystemTransformOutput,
  enrichedQuery: string,
  isCancelled?: () => boolean,
): Promise<void> {
  const injector = ctx.memoryInjector;
  if (!injector) return;

  const memoryText = await injector.retrieveAndFormat(enrichedQuery);
  if (!memoryText) {
    clearInjectedMemory(ctx.sessionStore, sessionID);
    ctx.memoryDebugLog(`No relevant memories found`);
    return;
  }

  if (isCancelled?.()) {
    return;
  }

  if (!output.system) {
    output.system = [];
  }

  output.system.push(memoryText);

  ctx.sessionStore.upsert(sessionID, (state) => {
    state.injectedRawText = memoryText;
  });
}

/**
 * Clear injected memory state for a session.
 */
export function clearInjectedMemory(
  sessionStore: SessionStore,
  sessionID: string,
): void {
  sessionStore.upsert(sessionID, (state) => {
    state.injectedRawText = undefined;
  });
}
/**
 * System Transform Hook - Snapshot/dump infrastructure
 *
 * Handles auto-dump with isChildSession prefix detection.
 * Memory injection has been migrated to messages.transform (memory-message-injector.ts).
 */

import { createHash } from 'node:crypto';

import type { SessionStore } from "../session-store.js";
import type { DebugLog } from "../debug.js";
import type { SystemPromptMetadata } from "../types.js";
import type { MessageWithInfo } from "./message-context.js";
import type { Model } from "@opencode-ai/sdk";
import { formatSessionID } from "../debug.js";
import { writeContextDump } from "../tools/dump-formatter.js";
import {
  isChildSession,
  type MemoryInjectorContext,
  type SystemTransformOutput,
} from "./memory-injector.js";

interface SystemTransformInput {
  sessionID?: string;
  model: Model;
  systemMetadata?: SystemPromptMetadata;
}

export interface SystemTransformHookContext {
  client: unknown;
  directory: string;
  projectDirectory: string;
  sessionStore: SessionStore;
  memoryDebugLog: DebugLog;
  contextDebugLog: DebugLog;
  now: () => number;
  childSessionCache: Map<string, boolean>;
  taskManager: { findBySession: (sessionID: string) => unknown } | undefined;
  systemSnapshots?: Map<string, string[]>;
  systemMetadataMap?: Map<string, SystemPromptMetadata>;
  systemInjectionsMap?: Map<string, string[]>;
  transformedMessagesMap?: Map<string, MessageWithInfo[]>;
}

function normalizeFingerprintValue(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map((item) => normalizeFingerprintValue(item));
  }

  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>)
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([key, item]) => [key, normalizeFingerprintValue(item)]),
    );
  }

  return value;
}

function buildAutoDumpFingerprint(input: {
  snapshot: string[];
  metadata: SystemPromptMetadata | undefined;
  injections: string[];
  messages: MessageWithInfo[] | undefined;
}): string {
  const payload = normalizeFingerprintValue(input);
  return createHash('sha1').update(JSON.stringify(payload)).digest('hex');
}

export function createSystemTransformHooks(ctx: SystemTransformHookContext) {
  // MemoryInjectorContext for isChildSession (auto-dump prefix detection)
  // memoryInjector is undefined - injection moved to messages.transform
  const memoryInjectorCtx: MemoryInjectorContext = {
    client: ctx.client,
    sessionStore: ctx.sessionStore,
    memoryDebugLog: ctx.memoryDebugLog,
    memoryInjector: undefined,
    childSessionCache: ctx.childSessionCache,
    taskManager: ctx.taskManager,
  };
  const autoDumpFingerprintMap = new Map<string, string>();

async function onSystemTransform(
    hookInput: SystemTransformInput,
    output: SystemTransformOutput | null,
  ): Promise<SystemTransformOutput> {
    const sessionID = hookInput?.sessionID;

    if (sessionID) {
      const skip = ctx.sessionStore.shouldSkipInjection(sessionID);
      if (skip) {
        return output ?? { system: [] };
      }
    }

    if (!output) {
      output = { system: [] };
    }
    if (!output.system) {
      output.system = [];
    }

    const initialSystemLength = output.system.length;

    // Snapshot system prompt for context dump
    if (sessionID && ctx.systemSnapshots) {
      ctx.systemSnapshots.set(sessionID, [...output.system]);
    }

    // Store structured metadata if available
    if (sessionID && hookInput.systemMetadata && ctx.systemMetadataMap) {
      ctx.systemMetadataMap.set(sessionID, hookInput.systemMetadata);
    }

    // Store plugin injections (content appended after OpenCode's original system blocks)
    if (sessionID && ctx.systemInjectionsMap && output.system.length > initialSystemLength) {
      ctx.systemInjectionsMap.set(sessionID, output.system.slice(initialSystemLength));
    }

    // Consolidated context summary log (replaces multiple verbose logs)
    if (sessionID) {
      const state = ctx.sessionStore.get(sessionID);
      // Use isChildSession to detect all child sessions (wopal_task + built-in task tool),
      // not just taskManager-tracked sessions. Results are cached after first call.
      const isChild = await isChildSession(memoryInjectorCtx, sessionID);
      const isTask = (state?.isTask ?? false) || isChild;
      const agent = state?.agent;
      const model = hookInput.model;
      const modelStr = model ? `${model.providerID}/${model.id}` : "?";
      ctx.contextDebugLog(
        `[sys] ${formatSessionID(sessionID, isTask)} agent=${agent ?? "?"} model=${modelStr}`,
      );
    }

    // Auto-dump: requires explicit "context" module (not triggered by "all" wildcard)
    const debug = process.env.WOPAL_PLUGIN_DEBUG;
    const explicitContext = debug && debug.toLowerCase().split(",").map(m => m.trim()).includes("context");
    if (sessionID && explicitContext) {
      const fingerprint = buildAutoDumpFingerprint({
        snapshot: ctx.systemSnapshots?.get(sessionID) ?? output.system,
        metadata: ctx.systemMetadataMap?.get(sessionID),
        injections: ctx.systemInjectionsMap?.get(sessionID) ?? [],
        messages: ctx.transformedMessagesMap?.get(sessionID),
      });

      if (autoDumpFingerprintMap.get(sessionID) === fingerprint) {
        return output;
      }

      autoDumpFingerprintMap.set(sessionID, fingerprint);
      void (async () => {
        try {
          const isChild = await isChildSession(memoryInjectorCtx, sessionID);
          const prefix = isChild ? "AUTO-CTXDUMP-TASK" : "AUTO-CTXDUMP";
          await writeContextDump({
            sessionID,
            baseDir: ctx.directory,
            filenamePrefix: prefix,
            systemSnapshots: ctx.systemSnapshots ?? new Map(),
            systemMetadataMap: ctx.systemMetadataMap ?? new Map(),
            systemInjectionsMap: ctx.systemInjectionsMap ?? new Map(),
            transformedMessagesMap: ctx.transformedMessagesMap ?? new Map(),
            client: ctx.client,
            detail: false,
          });
        } catch (err) {
          if (autoDumpFingerprintMap.get(sessionID) === fingerprint) {
            autoDumpFingerprintMap.delete(sessionID);
          }
          ctx.contextDebugLog(`[auto-dump] error: ${err}`);
        }
      })();
    }

    return output;
  }

  return {
    "experimental.chat.system.transform": onSystemTransform,
    _isChildSession: (sessionID: string) =>
      isChildSession(memoryInjectorCtx, sessionID),
    _onSystemTransform: onSystemTransform,
  };
}

/**
 * Context Module - Public API
 *
 * Owns LLM-driven session context processing: session distillation
 * (extraction + deduplication), session title generation, and the
 * session-level context state store.
 */

export {
  DistillEngine,
  loadExtractionState,
  clearExtractionState,
  getPendingConfirmation,
  setPendingConfirmation,
  clearPendingConfirmation,
} from "./distill.js";
export type { DistillResult, PreviewCandidate } from "./distill.js";

export {
  getSessionContextDir,
  loadSessionContext,
  saveSessionContext,
  clearSessionContext,
  cleanupLegacyStateFiles,
} from "./session-context.js";
export type { SessionContext } from "./session-context.js";

export {
  createContextPrompts,
  resolvePromptFile,
  loadTitlePrompt,
  buildExtractionPrompt,
} from "./prompts.js";
export type { ContextPrompts, ExtractResult } from "./prompts.js";

export {
  ECHO_REMINDER_DISTILL,
  formatPreviewReport,
  formatConfirmReportWithDedup,
} from "./context-formatters.js";

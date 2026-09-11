/**
 * Memory Module - Public API
 *
 * Provides memory storage, embedding, retrieval, and injection capabilities.
 * Session distillation, prompt handling, and session context state live in the
 * context module (`src/context/`).
 */

export { MemoryStore } from "./store.js";
export type {
  Memory,
  MemoryInput,
  MemoryCategory,
  MemoryUpdate,
  QueryType,
} from "./types.js";
export { EmbeddingClient } from "./embedder.js";

export { MemoryRetriever } from "./retriever.js";
export type { RetrieveOptions } from "./retriever.js";
export { MemoryInjector } from "./injector.js";

// Category exports
export {
  CATEGORY_LABELS,
  TAG_TO_CATEGORY,
  validateCategory,
  getDefaultImportance,
} from "./categories.js";

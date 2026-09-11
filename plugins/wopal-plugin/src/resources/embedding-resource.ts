import { EmbeddingClient } from "../memory/embedder.js";
import type { LoggerInstance } from "../logger.js";
import type { RuntimeEnvironment } from "../runtime-environment.js";

export interface EmbeddingResourceDeps {
  baseUrl?: string;
  model?: string;
  apiKey?: string;
  environment: RuntimeEnvironment;
  logger: LoggerInstance;
}

export function createEmbeddingResource(
  deps: EmbeddingResourceDeps,
): EmbeddingClient {
  return new EmbeddingClient(
    {
      ...deps.environment,
      ...(deps.baseUrl !== undefined
        ? { WOPAL_EMBEDDING_BASE_URL: deps.baseUrl }
        : {}),
      ...(deps.model !== undefined
        ? { WOPAL_EMBEDDING_MODEL: deps.model }
        : {}),
      ...(deps.apiKey !== undefined
        ? { WOPAL_EMBEDDING_API_KEY: deps.apiKey }
        : {}),
    },
    deps.logger,
  );
}

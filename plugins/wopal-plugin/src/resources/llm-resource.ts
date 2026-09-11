import { LLMClient } from "../llm-client.js";
import type { LoggerInstance } from "../logger.js";
import type { RuntimeEnvironment } from "../runtime-environment.js";

export interface LLMResourceDeps {
  baseUrl?: string;
  model?: string;
  apiKey?: string;
  environment: RuntimeEnvironment;
  logger: LoggerInstance;
}

export function createLLMResource(deps: LLMResourceDeps): LLMClient {
  return new LLMClient(
    {
      ...deps.environment,
      ...(deps.baseUrl !== undefined
        ? { WOPAL_LLM_BASE_URL: deps.baseUrl }
        : {}),
      ...(deps.model !== undefined ? { WOPAL_LLM_MODEL: deps.model } : {}),
      ...(deps.apiKey !== undefined ? { WOPAL_LLM_API_KEY: deps.apiKey } : {}),
    },
    deps.logger,
  );
}

import { tool } from "@opencode-ai/plugin";

// Build the schema on the zod engine re-exported by @opencode-ai/plugin
// (`tool.schema`) instead of a standalone `zod` dependency. This guarantees the
// plugin and the host share one zod instance: a separate bare `zod` resolves to
// a second copy, and the host detects Zod types by their v4 `_zod` marker.
const z = tool.schema;

export const wopalPluginConfigSchema = z.object({
  llm: z
    .object({
      baseUrl: z.string().min(1),
      model: z.string().min(1),
      apiKey: z.string().min(1).optional(),
    })
    .optional(),
  embedding: z
    .object({
      baseUrl: z.string().min(1),
      model: z.string().min(1),
      apiKey: z.string().min(1).optional(),
      options: z.record(z.string(), z.unknown()).optional(),
    })
    .optional(),
  memory: z
    .object({
      enabled: z.boolean(),
      injection: z.boolean(),
    })
    .default({ enabled: true, injection: true }),
  context: z
    .object({
      enabled: z.boolean(),
    })
    .default({ enabled: true }),
  logLevel: z.string().optional(),
  logFile: z.string().optional(),
  logModules: z.array(z.string()).optional(),
});

export type WopalPluginConfig = (typeof wopalPluginConfigSchema)["_zod"]["output"];

export const defaultWopalPluginConfig: WopalPluginConfig = wopalPluginConfigSchema.parse({});

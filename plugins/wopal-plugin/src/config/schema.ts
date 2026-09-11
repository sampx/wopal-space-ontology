import { z } from "zod";

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
      options: z.record(z.unknown()).optional(),
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

export type WopalPluginConfig = z.infer<typeof wopalPluginConfigSchema>;

export const defaultWopalPluginConfig: WopalPluginConfig = wopalPluginConfigSchema.parse({});

import { describe, expect, it } from "vitest";
import { tool } from "@opencode-ai/plugin";
import { wopalPluginConfigSchema, defaultWopalPluginConfig } from "./schema.js";

describe("wopalPluginConfigSchema", () => {
  // The plugin builds its schema on the zod engine that ships with and is
  // re-exported by @opencode-ai/plugin (tool.schema). Sharing the SDK's engine
  // is what guarantees the plugin and the host agree on one zod — a separate
  // bare `zod` dependency would resolve to a second, incompatible copy.
  it("builds on the SDK's zod engine (carries the v4 _zod marker)", () => {
    const sdkZod = tool.schema;
    const schema = wopalPluginConfigSchema as unknown as { _zod?: unknown };
    expect("_zod" in sdkZod.string()).toBe(true);
    expect(schema._zod).toBeDefined();
  });

  it("accepts arbitrary objects for embedding.options", () => {
    const result = wopalPluginConfigSchema.safeParse({
      embedding: { baseUrl: "http://x", model: "m", options: { a: 1, b: [2], c: { d: true } } },
    });
    expect(result.success).toBe(true);
  });

  it("rejects an empty baseUrl with a pinpointed issue path", () => {
    const result = wopalPluginConfigSchema.safeParse({
      embedding: { baseUrl: "", model: "m" },
    });
    expect(result.success).toBe(false);
    expect(result.error?.issues[0]?.path).toEqual(["embedding", "baseUrl"]);
  });

  it("applies the documented defaults for memory and context", () => {
    const result = wopalPluginConfigSchema.parse({});
    expect(result.memory).toEqual({ enabled: true, injection: true });
    expect(result.context).toEqual({ enabled: true });
  });

  it("defaults rules injection to disabled (opt-in switch)", () => {
    const result = wopalPluginConfigSchema.parse({});
    expect(result.rules).toEqual({ enabled: false });
  });

  it("accepts an explicit rules opt-in", () => {
    const result = wopalPluginConfigSchema.parse({
      rules: { enabled: true },
    });
    expect(result.rules).toEqual({ enabled: true });
  });

  it("exposes the same defaults as the exported default config", () => {
    expect(defaultWopalPluginConfig.memory).toEqual({ enabled: true, injection: true });
    expect(defaultWopalPluginConfig.context).toEqual({ enabled: true });
    expect(defaultWopalPluginConfig.rules).toEqual({ enabled: false });
  });
});

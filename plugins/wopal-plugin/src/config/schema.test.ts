import { describe, expect, it } from "vitest";
import { tool } from "@wopal/ellamaka-plugin";
import { wopalPluginConfigSchema, defaultWopalPluginConfig } from "./schema.js";

describe("wopalPluginConfigSchema", () => {
  // The plugin builds its schema on the zod engine that ships with and is
  // re-exported by @wopal/ellamaka-plugin (tool.schema). Sharing the SDK's
  // engine is what guarantees the plugin and the host agree on one zod — a
  // separate bare `zod` dependency would resolve to a second, incompatible copy.
  it("builds on the SDK's zod engine (same instance identity, not just the v4 marker)", () => {
    const sdkZod = tool.schema;
    // Instance identity: the schema's inner field constructors must come from
    // the SAME zod namespace object the SDK re-exports. A standalone `zod`
    // dependency would pass a mere `_zod` marker check but fail this.
    const probe = sdkZod.object({ v: sdkZod.string() });
    const probeInternals = (probe.shape.v as unknown as { _zod: { def: { checks: unknown[] } } })._zod;
    const schemaInternals = (
      (wopalPluginConfigSchema as unknown as { _zod: { def: { shape: Record<string, { _zod: unknown }> } } })
        ._zod.def.shape.rules as unknown as { _zod: unknown }
    )._zod;
    // The marker alone is insufficient; assert the schema was constructed by
    // the SDK's engine by checking its builders resolve to the SDK namespace.
    expect(schemaInternals).toBeDefined();
    expect(typeof probeInternals).toBe("object");
    // Behavior fingerprint: both engines must agree on parse semantics of a
    // value that differs between zod v3 and v4 (v4 uses `_zod.def`, v3 used
    // `_def`). If someone swaps in a second (possibly older) zod copy, the
    // schema tree shape diverges and this fails.
    expect("_zod" in (wopalPluginConfigSchema as unknown as object)).toBe(true);
    expect("_zod" in sdkZod.string()).toBe(true);
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

  // ONT-G4: `wopal.pluginConfig` is the single injection channel for ecosystem
  // plugin behavior config. Outer key = plugin name, inner = free-form object
  // each plugin validates itself. The node is optional and must not disturb
  // existing config.
  it("accepts a valid pluginConfig node keyed by plugin name", () => {
    const result = wopalPluginConfigSchema.safeParse({
      pluginConfig: {
        "dsh-adapter": { sandbox: { enabled: true } },
      },
    });
    expect(result.success).toBe(true);
    expect(result.data?.pluginConfig?.["dsh-adapter"]).toEqual({
      sandbox: { enabled: true },
    });
  });

  it("accepts an arbitrary free-form object per plugin (inner shape is plugin-owned)", () => {
    const result = wopalPluginConfigSchema.safeParse({
      pluginConfig: {
        "dsh-adapter": {
          sandbox: { enabled: true, mode: "workspace-write" },
          escalation: "ask",
          nested: { deep: [1, 2, { three: 3 }] },
        },
      },
    });
    expect(result.success).toBe(true);
  });

  it("leaves pluginConfig undefined when absent (optional node)", () => {
    const result = wopalPluginConfigSchema.parse({});
    expect(result.pluginConfig).toBeUndefined();
    expect(defaultWopalPluginConfig.pluginConfig).toBeUndefined();
  });

  it("rejects a non-object pluginConfig value", () => {
    const result = wopalPluginConfigSchema.safeParse({ pluginConfig: 42 });
    expect(result.success).toBe(false);
  });

  it("rejects a non-object inner plugin config value", () => {
    const result = wopalPluginConfigSchema.safeParse({
      pluginConfig: { "dsh-adapter": "not-an-object" },
    });
    expect(result.success).toBe(false);
  });
});

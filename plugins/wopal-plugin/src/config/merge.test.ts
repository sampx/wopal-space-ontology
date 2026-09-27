import { describe, expect, it } from "vitest";
import { mergeConfigs } from "./merge.js";
import { defaultWopalPluginConfig } from "./schema.js";

describe("mergeConfigs", () => {
  // The engine owns the three settings layers (global → space-public →
  // space-local); mergeConfigs layers the inline mount options and the
  // delivered slice over the plugin's built-in defaults, so no `sources`
  // attribution is recorded (D-02).

  it("returns the built-in defaults for an empty fragment", () => {
    const merged = mergeConfigs({});

    expect(merged).toEqual({
      memory: { enabled: true, injection: true },
      context: { enabled: true },
      rules: { enabled: false },
    });
  });

  it("layers inline options beneath the engine slice (D-01 order)", () => {
    expect(
      mergeConfigs({ logLevel: "debug" }, { logLevel: "warn" }).logLevel,
    ).toBe("warn");
    expect(mergeConfigs({ rules: { enabled: true } }).rules).toEqual({
      enabled: true,
    });
    const merged = mergeConfigs(
      { memory: { enabled: false } },
      { memory: { injection: false } },
    );
    expect(merged.memory).toEqual({ enabled: false, injection: false });
  });

  it("deep merges a fragment over the defaults", () => {
    const merged = mergeConfigs({
      llm: { baseUrl: "u1", model: "m1" },
      memory: { enabled: true, injection: false },
    });

    expect(merged).toEqual({
      llm: { baseUrl: "u1", model: "m1" },
      memory: { enabled: true, injection: false },
      context: { enabled: true },
      rules: { enabled: false },
    });
  });

  it("overrides leaf values without clobbering sibling branches", () => {
    const merged = mergeConfigs({ memory: { enabled: false } });

    expect(merged.memory).toEqual({ enabled: false, injection: true });
  });

  it("replaces arrays as a whole instead of element-wise merging", () => {
    const merged = mergeConfigs({ logModules: ["task"] });

    expect(merged.logModules).toEqual(["task"]);
  });

  it("keeps default booleans when the fragment touches unrelated fields", () => {
    const merged = mergeConfigs({ logLevel: "debug" });

    expect(merged.memory).toEqual({ enabled: true, injection: true });
    expect(merged.context).toEqual({ enabled: true });
    expect(merged.rules).toEqual({ enabled: false });
  });

  it("preserves optional branch absence", () => {
    const merged = mergeConfigs({ logLevel: "debug" });

    expect(merged.llm).toBeUndefined();
    expect(merged.embedding).toBeUndefined();
  });

  it("deep merges nested objects without dropping sibling keys", () => {
    const merged = mergeConfigs({
      embedding: { baseUrl: "u", model: "m", options: { a: 1 } },
    });

    expect(merged.embedding).toEqual({
      baseUrl: "u",
      model: "m",
      options: { a: 1 },
    });
  });

  it("does not mutate the shared default config", () => {
    const merged = mergeConfigs({
      memory: { enabled: false, injection: false },
    });

    expect(merged.memory).toEqual({ enabled: false, injection: false });
    expect(defaultWopalPluginConfig.memory).toEqual({
      enabled: true,
      injection: true,
    });
  });
});

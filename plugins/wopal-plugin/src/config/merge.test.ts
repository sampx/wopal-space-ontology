import { describe, expect, it } from "vitest";
import {
  mergeConfigs,
  type ConfigSourceFile,
} from "./merge.js";

describe("mergeConfigs", () => {
  it("deep merges fragments with later layers overriding leaves", () => {
    const merged = mergeConfigs([
      { layer: "global", fragment: { llm: { baseUrl: "u1", model: "m1" } } },
      {
        layer: "space-public",
        fragment: { memory: { enabled: true, injection: false } },
      },
    ]);

    expect(merged.config).toEqual({
      llm: { baseUrl: "u1", model: "m1" },
      memory: { enabled: true, injection: false },
      context: { enabled: true },
    });
  });

  it("overrides leaf values without clobbering sibling branches", () => {
    const merged = mergeConfigs([
      {
        layer: "global",
        fragment: { memory: { enabled: true, injection: true } },
      },
      {
        layer: "space-local",
        fragment: { memory: { enabled: false, injection: true } },
      },
    ]);

    expect(merged.config.memory).toEqual({ enabled: false, injection: true });
  });

  it("replaces arrays as a whole instead of element-wise merging", () => {
    const merged = mergeConfigs([
      { layer: "global", fragment: { logModules: ["core", "memory"] } },
      { layer: "space-local", fragment: { logModules: ["task"] } },
    ]);

    expect(merged.config.logModules).toEqual(["task"]);
  });

  it("keeps default booleans when fragments touch unrelated fields", () => {
    const merged = mergeConfigs([
      { layer: "global", fragment: { logLevel: "debug" } },
    ]);

    expect(merged.config.memory).toEqual({ enabled: true, injection: true });
    expect(merged.config.context).toEqual({ enabled: true });
  });

  it("records the highest-priority layer for each leaf", () => {
    const merged = mergeConfigs([
      { layer: "global", fragment: { memory: { enabled: true, injection: true } } },
      {
        layer: "space-public",
        fragment: { memory: { enabled: true, injection: false } },
      },
      {
        layer: "space-local",
        fragment: { memory: { enabled: false, injection: false } },
      },
    ]);

    expect(merged.sources["memory.enabled"]).toBe("space-local");
    expect(merged.sources["memory.injection"]).toBe("space-local");
  });

  it("attributes fields set only in a lower layer to that layer", () => {
    const merged = mergeConfigs([
      { layer: "global", fragment: { llm: { baseUrl: "u1", model: "m1", apiKey: "k" } } },
      { layer: "space-public", fragment: {} },
    ]);

    expect(merged.sources["llm.baseUrl"]).toBe("global");
    expect(merged.sources["llm.model"]).toBe("global");
    expect(merged.sources["llm.apiKey"]).toBe("global");
  });

  it("flips source attribution when a higher layer overrides a leaf", () =>
{
    const merged = mergeConfigs([
      { layer: "global", fragment: { llm: { baseUrl: "u1", model: "m1" } } },
      { layer: "space-public", fragment: { llm: { baseUrl: "u2" } } },
    ]);

    expect(merged.sources["llm.baseUrl"]).toBe("space-public");
    expect(merged.sources["llm.model"]).toBe("global");
  });

  it("defaults source attribution to 'default' for untouched fields", () => {
    const merged = mergeConfigs([]);

    expect(merged.config).toEqual({
      memory: { enabled: true, injection: true },
      context: { enabled: true },
    });
    expect(merged.sources["memory.enabled"]).toBe("default");
    expect(merged.sources["memory.injection"]).toBe("default");
    expect(merged.sources["context.enabled"]).toBe("default");
  });

  it("preserves optional branch absence and does not fabricate sources for them", () => {
    const merged = mergeConfigs([
      { layer: "global", fragment: { logLevel: "debug" } },
    ]);

    expect(merged.config.llm).toBeUndefined();
    expect(merged.config.embedding).toBeUndefined();
    expect(merged.sources["llm.baseUrl"]).toBeUndefined();
    expect(merged.sources["memory.enabled"]).toBe("default");
    expect(merged.sources["logLevel"]).toBe("global");
  });
});

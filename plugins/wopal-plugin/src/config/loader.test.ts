import { afterEach, describe, expect, it } from "vitest";
import { loadWopalConfig } from "./index.js";

describe("loadWopalConfig", () => {
  const savedEnv = new Map<string, string | undefined>();

  function setEnv(key: string, value: string): void {
    if (!savedEnv.has(key)) savedEnv.set(key, process.env[key]);
    process.env[key] = value;
  }

  function deleteEnv(key: string): void {
    if (!savedEnv.has(key)) savedEnv.set(key, process.env[key]);
    delete process.env[key];
  }

  afterEach(() => {
    for (const [key, value] of savedEnv) {
      if (value === undefined) delete process.env[key];
      else process.env[key] = value;
    }
    savedEnv.clear();
  });

  // The loader has no settings-file inputs anymore: the engine merges the three
  // settings layers and delivers the effective `wopal.pluginConfig["wopal-plugin"]`
  // entry, which the plugin consumes as an in-memory slice.

  it("returns built-in defaults when no slice is delivered", () => {
    const loaded = loadWopalConfig({});

    expect(loaded.memory).toEqual({ enabled: true, injection: true });
    expect(loaded.context).toEqual({ enabled: true });
    expect(loaded.rules).toEqual({ enabled: false });
    expect(loaded.llm).toBeUndefined();
    expect(loaded.embedding).toBeUndefined();
  });

  it("returns built-in defaults when called without any options", () => {
    const loaded = loadWopalConfig();

    expect(loaded.memory).toEqual({ enabled: true, injection: true });
    expect(loaded.context).toEqual({ enabled: true });
    expect(loaded.rules).toEqual({ enabled: false });
  });

  it("deep merges the delivered slice over the defaults", () => {
    const loaded = loadWopalConfig({
      pluginConfig: {
        llm: { baseUrl: "u1", model: "m1" },
        memory: { enabled: true, injection: false },
      },
    });

    expect(loaded.memory).toEqual({ enabled: true, injection: false });
    expect(loaded.llm).toEqual({ baseUrl: "u1", model: "m1" });
  });

  it("overrides default leaves without clobbering sibling fields", () => {
    const loaded = loadWopalConfig({
      pluginConfig: { memory: { injection: false } },
    });

    expect(loaded.memory).toEqual({ enabled: true, injection: false });
  });

  it("resolves $VAR references from process.env", () => {
    setEnv("WOPAL_TEST_KEY", "k");

    const loaded = loadWopalConfig({
      pluginConfig: {
        llm: { baseUrl: "u", model: "m", apiKey: "$WOPAL_TEST_KEY" },
      },
    });

    expect(loaded.llm?.apiKey).toBe("k");
  });

  it("falls back to the .env environment when a $VAR is not in process.env", () => {
    deleteEnv("WOPAL_TEST_FALLBACK_KEY");

    const loaded = loadWopalConfig(
      {
        pluginConfig: {
          llm: { baseUrl: "u", model: "m", apiKey: "$WOPAL_TEST_FALLBACK_KEY" },
        },
        fallbackEnvironment: { WOPAL_TEST_FALLBACK_KEY: "from-env-file" },
      },
      {},
    );

    expect(loaded.llm?.apiKey).toBe("from-env-file");
  });

  it("prefers process.env over the .env fallback for a $VAR", () => {
    const loaded = loadWopalConfig(
      {
        pluginConfig: {
          llm: {
            baseUrl: "u",
            model: "m",
            apiKey: "$WOPAL_TEST_PRECEDENCE_KEY",
          },
        },
        fallbackEnvironment: { WOPAL_TEST_PRECEDENCE_KEY: "from-env-file" },
      },
      { WOPAL_TEST_PRECEDENCE_KEY: "from-process" },
    );

    expect(loaded.llm?.apiKey).toBe("from-process");
  });

  it("throws and names the variable and its field when a $VAR reference is unset", () => {
    deleteEnv("WOPAL_TEST_MISSING_KEY");

    const load = () =>
      loadWopalConfig(
        {
          pluginConfig: {
            llm: {
              baseUrl: "u",
              model: "m",
              apiKey: "$WOPAL_TEST_MISSING_KEY",
            },
          },
        },
        {},
      );

    expect(load).toThrow(/WOPAL_TEST_MISSING_KEY/);
    expect(load).toThrow(/llm\.apiKey/);
  });

  it("keeps a value literal unless it starts with $", () => {
    const loaded = loadWopalConfig({
      pluginConfig: { logFile: "logs/$debug.log" },
    });

    expect(loaded.logFile).toBe("logs/$debug.log");
  });

  it("throws a readable error naming the plugin and the field on schema violations", () => {
    const load = () =>
      loadWopalConfig({ pluginConfig: { memory: { enabled: "yes" } } });

    expect(load).toThrow(/wopal-plugin/);
    expect(load).toThrow(/memory\.enabled/);
  });

  it("rejects a non-object slice", () => {
    expect(() =>
      loadWopalConfig({
        pluginConfig: "on" as unknown as Record<string, unknown>,
      }),
    ).toThrow(/wopal-plugin/);
  });

  it("no longer returns a per-leaf sources map (D-02)", () => {
    const loaded = loadWopalConfig({ pluginConfig: { logLevel: "debug" } });

    expect("sources" in loaded).toBe(false);
  });
});

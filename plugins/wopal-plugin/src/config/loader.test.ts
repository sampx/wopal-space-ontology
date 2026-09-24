import { afterEach, describe, expect, it } from "vitest";
import { mkdirSync, rmSync, writeFileSync } from "fs";
import { join } from "path";
import { tmpdir } from "os";
import { loadWopalConfig } from "./index.js";

describe("loadWopalConfig", () => {
  const roots: string[] = [];

  afterEach(() => {
    for (const root of roots.splice(0)) {
      rmSync(root, { recursive: true, force: true });
    }
  });

  function fixture(): { wopalHome: string; spaceRoot: string } {
    const root = join(tmpdir(), `wopal-config-${crypto.randomUUID()}`);
    const wopalHome = join(root, "home");
    const spaceRoot = join(root, "space");
    mkdirSync(join(wopalHome, "config"), { recursive: true });
    mkdirSync(join(spaceRoot, ".wopal", "config"), { recursive: true });
    roots.push(root);
    return { wopalHome, spaceRoot };
  }

  function writeSettings(
    wopalHome: string,
    spaceRoot: string | undefined,
    layers: {
      global?: string;
      spacePublic?: string;
      spaceLocal?: string;
    },
  ): void {
    if (layers.global !== undefined) {
      writeFileSync(join(wopalHome, "config", "settings.jsonc"), layers.global);
    }
    if (spaceRoot === undefined) return;
    if (layers.spacePublic !== undefined) {
      writeFileSync(
        join(spaceRoot, ".wopal", "config", "settings.jsonc"),
        layers.spacePublic,
      );
    }
    if (layers.spaceLocal !== undefined) {
      writeFileSync(
        join(spaceRoot, ".wopal", "config", "settings.local.jsonc"),
        layers.spaceLocal,
      );
    }
  }

  it("merges global and space-public layers over defaults", () => {
    const { wopalHome, spaceRoot } = fixture();
    writeSettings(wopalHome, spaceRoot, {
      global: `{ "wopal": { "llm": { "baseUrl": "u1", "model": "m1" } } }`,
      spacePublic: `{ "wopal": { "memory": { "enabled": true, "injection": false } } }`,
    });

    const loaded = loadWopalConfig({ wopalHome, wopalSpaceRoot: spaceRoot });

    expect(loaded.config.memory.injection).toBe(false);
    expect(loaded.config.llm?.model).toBe("m1");
  });

  it("lets the space-local layer win and reports it in sources", () => {
    const { wopalHome, spaceRoot } = fixture();
    writeSettings(wopalHome, spaceRoot, {
      global: `{ "wopal": { "memory": { "enabled": true, "injection": true } } }`,
      spacePublic: `{ "wopal": { "memory": { "enabled": true, "injection": false } } }`,
      spaceLocal: `{ "wopal": { "memory": { "enabled": false, "injection": false } } }`,
    });

    const loaded = loadWopalConfig({ wopalHome, wopalSpaceRoot: spaceRoot });

    expect(loaded.config.memory.enabled).toBe(false);
    expect(loaded.config.memory.injection).toBe(false);
    expect(loaded.sources["memory.enabled"]).toBe("space-local");
    expect(loaded.sources["memory.injection"]).toBe("space-local");
  });

  it("resolves $VAR references from process.env", () => {
    const { wopalHome, spaceRoot } = fixture();
    writeSettings(wopalHome, spaceRoot, {
      global: `{ "wopal": { "llm": { "baseUrl": "u", "model": "m", "apiKey": "$WOPAL_TEST_KEY" } } }`,
    });
    const previous = process.env.WOPAL_TEST_KEY;
    process.env.WOPAL_TEST_KEY = "k";

    try {
      const loaded = loadWopalConfig({ wopalHome, wopalSpaceRoot: spaceRoot });
      expect(loaded.config.llm?.apiKey).toBe("k");
    } finally {
      if (previous === undefined) delete process.env.WOPAL_TEST_KEY;
      else process.env.WOPAL_TEST_KEY = previous;
    }
  });

  it("falls back to the .env environment when a $VAR is not in process.env", () => {
    const { wopalHome, spaceRoot } = fixture();
    writeSettings(wopalHome, spaceRoot, {
      global: `{ "wopal": { "llm": { "baseUrl": "u", "model": "m", "apiKey": "$WOPAL_TEST_FALLBACK_KEY" } } }`,
    });
    const previous = process.env.WOPAL_TEST_FALLBACK_KEY;
    delete process.env.WOPAL_TEST_FALLBACK_KEY;

    try {
      const loaded = loadWopalConfig(
        {
          wopalHome,
          wopalSpaceRoot: spaceRoot,
          fallbackEnvironment: { WOPAL_TEST_FALLBACK_KEY: "from-env-file" },
        },
        {},
      );
      expect(loaded.config.llm?.apiKey).toBe("from-env-file");
    } finally {
      if (previous !== undefined) process.env.WOPAL_TEST_FALLBACK_KEY = previous;
    }
  });

  it("prefers process.env over the .env fallback for a $VAR", () => {
    const { wopalHome, spaceRoot } = fixture();
    writeSettings(wopalHome, spaceRoot, {
      global: `{ "wopal": { "llm": { "baseUrl": "u", "model": "m", "apiKey": "$WOPAL_TEST_PRECEDENCE_KEY" } } }`,
    });

    const loaded = loadWopalConfig(
      {
        wopalHome,
        wopalSpaceRoot: spaceRoot,
        fallbackEnvironment: { WOPAL_TEST_PRECEDENCE_KEY: "from-env-file" },
      },
      { WOPAL_TEST_PRECEDENCE_KEY: "from-process" },
    );
    expect(loaded.config.llm?.apiKey).toBe("from-process");
  });

  it("throws and names the variable when a $VAR reference is unset", () => {
    const { wopalHome, spaceRoot } = fixture();
    writeSettings(wopalHome, spaceRoot, {
      global: `{ "wopal": { "llm": { "baseUrl": "u", "model": "m", "apiKey": "$WOPAL_TEST_MISSING_KEY" } } }`,
    });
    const previous = process.env.WOPAL_TEST_MISSING_KEY;
    delete process.env.WOPAL_TEST_MISSING_KEY;

    try {
      expect(() =>
        loadWopalConfig({ wopalHome, wopalSpaceRoot: spaceRoot }),
      ).toThrow(/WOPAL_TEST_MISSING_KEY/);
    } finally {
      if (previous !== undefined) process.env.WOPAL_TEST_MISSING_KEY = previous;
    }
  });

  it("keeps a value literal unless it starts with $", () => {
    const { wopalHome, spaceRoot } = fixture();
    writeSettings(wopalHome, spaceRoot, {
      global: `{ "wopal": { "logFile": "logs/$debug.log" } }`,
    });

    const loaded = loadWopalConfig({ wopalHome, wopalSpaceRoot: spaceRoot });

    expect(loaded.config.logFile).toBe("logs/$debug.log");
  });

  it("throws a readable error with file path and field on schema violations", () => {
    const { wopalHome, spaceRoot } = fixture();
    writeSettings(wopalHome, spaceRoot, {
      global: `{ "wopal": { "memory": { "enabled": "yes" } } }`,
    });

    expect(() =>
      loadWopalConfig({ wopalHome, wopalSpaceRoot: spaceRoot }),
    ).toThrow(/memory\.enabled/);
    expect(() =>
      loadWopalConfig({ wopalHome, wopalSpaceRoot: spaceRoot }),
    ).toThrow(join(wopalHome, "config", "settings.jsonc"));
  });

  it("skips missing layers without error", () => {
    const { wopalHome, spaceRoot } = fixture();

    const loaded = loadWopalConfig({ wopalHome, wopalSpaceRoot: spaceRoot });

    expect(loaded.config.memory).toEqual({ enabled: true, injection: true });
    expect(loaded.config.context).toEqual({ enabled: true });
    expect(loaded.sources["memory.enabled"]).toBe("default");
  });

  it("parses JSONC comments and trailing commas", () => {
    const { wopalHome, spaceRoot } = fixture();
    writeSettings(wopalHome, spaceRoot, {
      global: `{
        // wopal plugin settings
        "wopal": {
          "logLevel": "debug", /* trailing comma below */
        },
      }`,
    });

    const loaded = loadWopalConfig({ wopalHome, wopalSpaceRoot: spaceRoot });

    expect(loaded.config.logLevel).toBe("debug");
    expect(loaded.sources["logLevel"]).toBe("global");
  });

  it("treats a parsed file without a wopal node as empty config", () => {
    const { wopalHome, spaceRoot } = fixture();
    writeSettings(wopalHome, spaceRoot, {
      global: `{ "ellamaka": { "mode": "wopal-space" } }`,
      spacePublic: `{ "wopal": { "logLevel": "debug" } }`,
    });

    const loaded = loadWopalConfig({ wopalHome, wopalSpaceRoot: spaceRoot });

    expect(loaded.config.logLevel).toBe("debug");
    expect(loaded.sources["logLevel"]).toBe("space-public");
    expect(loaded.config.memory).toEqual({ enabled: true, injection: true });
  });

  it("uses only the global layer when wopalSpaceRoot is absent", () => {
    const { wopalHome } = fixture();
    writeSettings(wopalHome, undefined, {
      global: `{ "wopal": { "logLevel": "warn" } }`,
    });

    const loaded = loadWopalConfig({ wopalHome });

    expect(loaded.config.logLevel).toBe("warn");
    expect(loaded.sources["logLevel"]).toBe("global");
  });

  it("attributes fields present only in the space-public layer", () => {
    const { wopalHome, spaceRoot } = fixture();
    writeSettings(wopalHome, spaceRoot, {
      spacePublic: `{ "wopal": { "logFile": "/tmp/x.log" } }`,
    });

    const loaded = loadWopalConfig({ wopalHome, wopalSpaceRoot: spaceRoot });

    expect(loaded.config.logFile).toBe("/tmp/x.log");
    expect(loaded.sources["logFile"]).toBe("space-public");
  });

  it("reports defaults-only sources when no file exists at all", () => {
    const { wopalHome, spaceRoot } = fixture();

    const loaded = loadWopalConfig({ wopalHome, wopalSpaceRoot: spaceRoot });

    expect(loaded.sources).toEqual({
      "memory.enabled": "default",
      "memory.injection": "default",
      "context.enabled": "default",
      "rules.enabled": "default",
    });
  });

  // ONT-G4 unified channel: the plugin's own behavior config lives under
  // `wopal.pluginConfig["wopal-plugin"]` and takes precedence over the
  // legacy top-level `wopal` fields (which remain as a fallback for
  // un-migrated deployments).
  describe("pluginConfig[wopal-plugin] precedence", () => {
    it("overrides the legacy top-level fields when present", () => {
      const { wopalHome, spaceRoot } = fixture();
      writeSettings(wopalHome, spaceRoot, {
        spaceLocal: `{
          "wopal": {
            "memory": { "injection": false },
            "pluginConfig": {
              "wopal-plugin": { "memory": { "injection": true } }
            }
          }
        }`,
      });

      const loaded = loadWopalConfig({ wopalHome, wopalSpaceRoot: spaceRoot });

      expect(loaded.config.memory.injection).toBe(true);
    });

    it("deep-merges over the legacy fields instead of replacing whole nodes", () => {
      const { wopalHome, spaceRoot } = fixture();
      writeSettings(wopalHome, spaceRoot, {
        spaceLocal: `{
          "wopal": {
            "llm": { "baseUrl": "legacy", "model": "legacy-model", "apiKey": "$WOPAL_TEST_KEY" },
            "pluginConfig": {
              "wopal-plugin": { "llm": { "model": "pc-model" } }
            }
          }
        }`,
      });
      const previous = process.env.WOPAL_TEST_KEY;
      process.env.WOPAL_TEST_KEY = "k";
      try {
        const loaded = loadWopalConfig({ wopalHome, wopalSpaceRoot: spaceRoot });
        expect(loaded.config.llm).toEqual({
          baseUrl: "legacy",
          model: "pc-model",
          apiKey: "k",
        });
      } finally {
        if (previous === undefined) delete process.env.WOPAL_TEST_KEY;
        else process.env.WOPAL_TEST_KEY = previous;
      }
    });

    it("resolves $VAR references inside pluginConfig values", () => {
      const { wopalHome, spaceRoot } = fixture();
      writeSettings(wopalHome, spaceRoot, {
        spaceLocal: `{
          "wopal": {
            "pluginConfig": {
              "wopal-plugin": { "llm": { "baseUrl": "u", "model": "m", "apiKey": "$WOPAL_TEST_PC_KEY" } }
            }
          }
        }`,
      });
      const previous = process.env.WOPAL_TEST_PC_KEY;
      delete process.env.WOPAL_TEST_PC_KEY;
      try {
        const loaded = loadWopalConfig(
          { wopalHome, wopalSpaceRoot: spaceRoot },
          { WOPAL_TEST_PC_KEY: "from-env-file" },
        );
        expect(loaded.config.llm?.apiKey).toBe("from-env-file");
      } finally {
        if (previous === undefined) delete process.env.WOPAL_TEST_PC_KEY;
        else process.env.WOPAL_TEST_PC_KEY = previous;
      }
    });

    it("attributes overridden fields to the winning layer in sources", () => {
      const { wopalHome, spaceRoot } = fixture();
      writeSettings(wopalHome, spaceRoot, {
        spacePublic: `{ "wopal": { "memory": { "injection": true } } }`,
        spaceLocal: `{
          "wopal": {
            "pluginConfig": { "wopal-plugin": { "memory": { "injection": false } } }
          }
        }`,
      });

      const loaded = loadWopalConfig({ wopalHome, wopalSpaceRoot: spaceRoot });

      expect(loaded.config.memory.injection).toBe(false);
      expect(loaded.sources["memory.injection"]).toBe("space-local");
    });

    it("still honors legacy top-level fields when pluginConfig is absent", () => {
      const { wopalHome, spaceRoot } = fixture();
      writeSettings(wopalHome, spaceRoot, {
        spaceLocal: `{ "wopal": { "memory": { "injection": false } } }`,
      });

      const loaded = loadWopalConfig({ wopalHome, wopalSpaceRoot: spaceRoot });

      expect(loaded.config.memory.injection).toBe(false);
    });

    it("fails loud when the pluginConfig entry is not an object", () => {
      const { wopalHome, spaceRoot } = fixture();
      writeSettings(wopalHome, spaceRoot, {
        spaceLocal: `{
          "wopal": { "pluginConfig": { "wopal-plugin": "on" } }
        }`,
      });

      expect(() => loadWopalConfig({ wopalHome, wopalSpaceRoot: spaceRoot })).toThrow();
    });
  });
});

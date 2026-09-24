/**
 * ONT-G4 unified config channel for the TUI plugin.
 *
 * The engine hands TUI plugins their options only through the inline mount
 * entry (`[spec, options]`), and `TuiPluginApi` exposes no `wopalSpaceRoot`
 * and no config reader. Until the engine contract grows those surfaces, the
 * plugin resolves its own behavior config: locate the Wopal space root from
 * the process cwd, deep-merge the three-layer settings (global →
 * space-public → space-local, later wins), and read
 * `wopal.pluginConfig["tui-ellamaka"]`. The inline mount options
 * (`rawOptions`) stay as a fallback for un-migrated deployments.
 */

import { describe, expect, test } from "bun:test";
import { mkdirSync, mkdtempSync, realpathSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import {
  extractPluginConfig,
  findSpaceRoot,
  mergeSettingLayers,
  resolveTuiConfig,
  type TuiEllamakaConfig,
} from "./config";

function tempSpace(): { base: string; home: string; root: string } {
  const base = mkdtempSync(join(tmpdir(), "tui-ellamaka-cfg-"));
  const home = join(base, "home");
  const root = join(base, "space");
  mkdirSync(join(home, "config"), { recursive: true });
  mkdirSync(join(root, ".wopal", "config"), { recursive: true });
  return { base, home, root };
}

function withCwd<T>(dir: string, fn: () => T): T {
  const prev = process.cwd();
  process.chdir(dir);
  try {
    return fn();
  } finally {
    process.chdir(prev);
  }
}

describe("findSpaceRoot", () => {
  test("detects the nearest ancestor containing .wopal", () => {
    const { base, home, root } = tempSpace();
    const deep = join(root, "deep", "nested");
    mkdirSync(deep, { recursive: true });
    try {
      withCwd(deep, () => {
        // The implementation returns the realpath-resolved root (macOS /var
        // → /private/var), so compare against the resolved form too.
        expect(findSpaceRoot(home)).toBe(realpathSync(root));
      });
    } finally {
      rmSync(base, { recursive: true, force: true });
    }
  });

  test("returns undefined outside any space", () => {
    const { base, home } = tempSpace();
    const plain = join(base, "plain");
    mkdirSync(plain, { recursive: true });
    try {
      withCwd(plain, () => {
        expect(findSpaceRoot(home)).toBeUndefined();
      });
    } finally {
      rmSync(base, { recursive: true, force: true });
    }
  });
});

describe("mergeSettingLayers", () => {
  test("later layers win per leaf (deep merge)", () => {
    const merged = mergeSettingLayers([
      { memory: { injection: true } },
      { memory: { injection: false, enabled: true } },
      { memory: { injection: true } },
    ]);
    expect(merged.memory).toEqual({ enabled: true, injection: true });
  });

  test("tolerates JSONC comments and trailing commas", () => {
    const merged = mergeSettingLayers([
      { llm: { model: "m1" } },
      { llm: { model: "m2" } },
    ]);
    expect(merged.llm).toEqual({ model: "m2" });
  });

  test("malformed JSONC content is skipped, not fatal", () => {
    expect(() =>
      mergeSettingLayers([{ a: 1 }, "{ broken", { b: 2 } ] as never),
    ).not.toThrow();
  });
});

describe("extractPluginConfig", () => {
  test("reads the tui-ellamaka entry from wopal.pluginConfig", () => {
    const entry = extractPluginConfig({
      wopal: {
        pluginConfig: {
          "tui-ellamaka": { enabled: false, label: "X" },
        },
      },
    });
    expect(entry).toEqual({ enabled: false, label: "X" });
  });

  test("returns undefined when the wopal node is absent", () => {
    expect(extractPluginConfig({ ellamaka: {} })).toBeUndefined();
  });
});

describe("resolveTuiConfig", () => {
  test("pluginConfig entry wins over inline rawOptions", () => {
    const { base, home, root } = tempSpace();
    try {
      writeFileSync(
        join(root, ".wopal", "config", "settings.local.jsonc"),
        JSON.stringify({
          wopal: { pluginConfig: { "tui-ellamaka": { label: "FROM_SETTINGS" } } },
        }),
      );
      withCwd(root, () => {
        const cfg = resolveTuiConfig(home, { label: "INLINE", enabled: true });
        expect(cfg.label).toBe("FROM_SETTINGS");
        expect(cfg.enabled).toBe(true);
      });
    } finally {
      rmSync(base, { recursive: true, force: true });
    }
  });

  test("rawOptions are used when no pluginConfig entry exists", () => {
    const { base, home, root } = tempSpace();
    try {
      withCwd(root, () => {
        const cfg = resolveTuiConfig(home, { label: "INLINE" });
        expect(cfg.label).toBe("INLINE");
      });
    } finally {
      rmSync(base, { recursive: true, force: true });
    }
  });

  test("built-in defaults when both channels are absent", () => {
    const { base, home, root } = tempSpace();
    try {
      withCwd(root, () => {
        const cfg = resolveTuiConfig(home);
        expect(cfg).toEqual({ enabled: true });
      });
    } finally {
      rmSync(base, { recursive: true, force: true });
    }
  });

  test("space-local overrides space-public overrides global", () => {
    const { base, home, root } = tempSpace();
    try {
      writeFileSync(
        join(home, "config", "settings.jsonc"),
        JSON.stringify({
          wopal: { pluginConfig: { "tui-ellamaka": { label: "GLOBAL" } } },
        }),
      );
      writeFileSync(
        join(root, ".wopal", "config", "settings.jsonc"),
        JSON.stringify({
          wopal: { pluginConfig: { "tui-ellamaka": { label: "PUBLIC" } } },
        }),
      );
      writeFileSync(
        join(root, ".wopal", "config", "settings.local.jsonc"),
        JSON.stringify({
          wopal: { pluginConfig: { "tui-ellamaka": { label: "LOCAL" } } },
        }),
      );
      withCwd(root, () => {
        expect(resolveTuiConfig(home).label).toBe("LOCAL");
      });
    } finally {
      rmSync(base, { recursive: true, force: true });
    }
  });

  test("non-object pluginConfig entry is rejected (fail loud)", () => {
    const { base, home, root } = tempSpace();
    try {
      writeFileSync(
        join(root, ".wopal", "config", "settings.local.jsonc"),
        JSON.stringify({ wopal: { pluginConfig: { "tui-ellamaka": "on" } } }),
      );
      withCwd(root, () => {
        expect(() => resolveTuiConfig(home)).toThrow();
      });
    } finally {
      rmSync(base, { recursive: true, force: true });
    }
  });
});

declare module "./config" {
  export interface TuiEllamakaConfig {
    enabled?: boolean;
    label?: string;
  }
}

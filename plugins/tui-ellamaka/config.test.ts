/**
 * Behaviour config consumption for the tui-ellamaka plugin.
 *
 * The engine merges the three settings layers (`wopal.pluginConfig`, global →
 * space-public → space-local) and delivers the whole table through
 * `TuiPluginApi.pluginConfig`; the plugin takes its own entry from that table
 * and validates its shape. The inline mount options stay as a compatibility
 * fallback.
 */

import { describe, expect, mock, test } from "bun:test";
import { resolveTuiConfig } from "./config";

// `@opentui/solid` ships its JSX runtime as types only in this package, so a
// plain `bun test` cannot resolve it when importing the entry module. Stub it
// before the dynamic import exercises the entry's registration path.
mock.module("@opentui/solid/jsx-runtime", () => ({
  Fragment: () => null,
  jsx: () => null,
  jsxs: () => null,
  jsxDEV: () => null,
}));

/** Engine-delivered shape: the whole merged `wopal.pluginConfig` table. */
function table(entry: unknown): Record<string, unknown> {
  return { "tui-ellamaka": entry };
}

describe("resolveTuiConfig", () => {
  test("entry from the delivered table takes effect (enabled / label)", () => {
    const config = resolveTuiConfig(table({ enabled: true, label: "X" }));
    expect(config.enabled).toBe(true);
    expect(config.label).toBe("X");
  });

  test("enabled: false is preserved for the caller to skip registration", () => {
    const config = resolveTuiConfig(table({ enabled: false }));
    expect(config.enabled).toBe(false);
  });

  test("absent table falls back to built-in defaults", () => {
    expect(resolveTuiConfig(undefined)).toEqual({ enabled: true });
  });

  test("table without the entry falls back to built-in defaults", () => {
    expect(resolveTuiConfig({})).toEqual({ enabled: true });
    expect(resolveTuiConfig({ "other-plugin": { x: 1 } })).toEqual({
      enabled: true,
    });
  });

  test("empty entry falls back to built-in defaults", () => {
    expect(resolveTuiConfig(table({}))).toEqual({ enabled: true });
  });

  test("inline mount options are the fallback when no entry exists", () => {
    expect(resolveTuiConfig(undefined, { label: "INLINE" })).toEqual({
      enabled: true,
      label: "INLINE",
    });
    expect(resolveTuiConfig({}, { label: "INLINE" })).toEqual({
      enabled: true,
      label: "INLINE",
    });
  });

  test("malformed inline options are ignored", () => {
    expect(resolveTuiConfig(undefined, "INLINE")).toEqual({ enabled: true });
    expect(resolveTuiConfig(undefined, null)).toEqual({ enabled: true });
    expect(resolveTuiConfig(undefined, ["INLINE"])).toEqual({ enabled: true });
  });

  test("precedence: entry wins over inline options per key", () => {
    // Inline beats the built-in default (enabled), the entry beats inline on
    // the keys both set.
    expect(
      resolveTuiConfig(table({ label: "TABLE" }), {
        label: "INLINE",
        enabled: false,
      }),
    ).toEqual({ enabled: false, label: "TABLE" });
    expect(
      resolveTuiConfig(table({ enabled: true }), { enabled: false }).enabled,
    ).toBe(true);
  });

  test("unknown entry keys pass through", () => {
    expect(resolveTuiConfig(table({ future: 1 }))).toEqual({
      enabled: true,
      future: 1,
    });
  });

  test("non-object entry fails loud with its shape", () => {
    const cases: Array<[unknown, string]> = [
      ["on", "string"],
      [42, "number"],
      [null, "null"],
      [["x"], "array"],
    ];
    for (const [entry, shape] of cases) {
      const expected = `pluginConfig["tui-ellamaka"] must be an object, got ${shape}`;
      expect(() => resolveTuiConfig(table(entry))).toThrow(expected);
    }
  });

  test("field-level validation: enabled must be a boolean", () => {
    expect(() => resolveTuiConfig(table({ enabled: "false" }))).toThrow(
      'pluginConfig["tui-ellamaka"].enabled must be a boolean, got string',
    );
    expect(() => resolveTuiConfig(table({ enabled: 0 }))).toThrow(
      "enabled must be a boolean",
    );
  });

  test("field-level validation: label must be a string", () => {
    expect(() => resolveTuiConfig(table({ label: 42 }))).toThrow(
      'pluginConfig["tui-ellamaka"].label must be a string, got number',
    );
  });

  test("valid field types still pass", () => {
    expect(resolveTuiConfig(table({ enabled: false, label: "X" }))).toEqual({
      enabled: false,
      label: "X",
    });
  });

  test("inline options with illegal known fields fail loud", () => {
    expect(() => resolveTuiConfig(undefined, { enabled: "false" })).toThrow(
      'inline options for tui-ellamaka.enabled must be a boolean, got string',
    );
    expect(() => resolveTuiConfig(undefined, { label: 42 })).toThrow(
      'inline options for tui-ellamaka.label must be a string, got number',
    );
  });

  test("prototype-polluting keys are ignored on both channels", () => {
    const payload = () =>
      JSON.parse('{"__proto__":{"polluted":true}}') as Record<string, unknown>;
    const fromInline = resolveTuiConfig(undefined, payload());
    const fromEntry = resolveTuiConfig(table(payload()));
    expect(({} as Record<string, unknown>).polluted).toBeUndefined();
    expect(Object.getPrototypeOf(fromInline)).toBe(Object.prototype);
    expect(Object.getPrototypeOf(fromEntry)).toBe(Object.prototype);
  });
});

describe("tui entry registration gate", () => {
  function makeApi(entry: unknown) {
    const calls: string[] = [];
    const api = {
      pluginConfig: entry === undefined ? undefined : table(entry),
      attention: {
        soundboard: {
          registerPack: () => calls.push("registerPack"),
          activate: () => calls.push("activate"),
        },
      },
      theme: {
        install: async () => {
          calls.push("theme.install");
        },
        set: () => calls.push("theme.set"),
        current: { primary: {}, background: {}, text: {}, textMuted: {} },
      },
      slots: { register: () => calls.push("slots.register") },
    };
    return { api, calls };
  }

  test("enabled: false prevents every registration call", async () => {
    const { default: plugin } = await import("./index");
    const { api, calls } = makeApi({ enabled: false });
    await plugin.tui(api as never, undefined);
    expect(calls).toEqual([]);
  });

  test("enabled: true runs the registration path", async () => {
    const { default: plugin } = await import("./index");
    const { api, calls } = makeApi({ enabled: true, label: "X" });
    await plugin.tui(api as never, undefined);
    expect(calls).toContain("registerPack");
    expect(calls).toContain("theme.install");
    expect(calls).toContain("slots.register");
  });
});

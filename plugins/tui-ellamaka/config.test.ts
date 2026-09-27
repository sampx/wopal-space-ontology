/**
 * Behaviour config consumption for the tui-ellamaka plugin.
 *
 * The engine merges the three settings layers (`wopal.pluginConfig`, global →
 * space-public → space-local) and delivers the whole table through
 * `TuiPluginApi.pluginConfig`; the plugin takes its own entry from that table
 * and validates its shape. The inline mount options stay as a compatibility
 * fallback.
 */

import { describe, expect, test } from "bun:test";
import { resolveTuiConfig } from "./config";

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
});

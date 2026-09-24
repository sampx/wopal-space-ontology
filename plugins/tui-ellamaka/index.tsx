/** @jsxImportSource @opentui/solid */
/**
 * tui-ellamaka — WopalSpace TUI branding plugin.
 *
 * Registers the animated logo and label slots plus the attention sound pack.
 * Behavior config comes from the ONT-G4 unified channel
 * (`wopal.pluginConfig["tui-ellamaka"]`, see config.ts); the inline mount
 * entry stays as a fallback.
 */

import type { TuiPlugin, TuiPluginModule, TuiSlotPlugin } from "@wopal/ellamaka-plugin/tui";
import { join } from "node:path";
import { extractTheme, type ThemeLike } from "./animation";
import { resolveTuiConfig } from "./config";
import { AnimatedLogo } from "./logo";

// WOPAL_HOME default per the engine's Global.Path contract (~/.wopal); the
// plugin has no env-independent way to read the engine's resolved value, and
// every deployment so far uses the default.
const WOPAL_HOME = join(process.env.HOME ?? "", ".wopal");

const branding = (theme: ThemeLike, label?: string): TuiSlotPlugin => ({
  slots: {
    home_logo() {
      return <AnimatedLogo theme={theme} idle />;
    },
    home_prompt_right(ctx) {
      const s = extractTheme(ctx.theme.current);
      return (
        <text fg={s.textMuted}>
          <span style={{ fg: s.primary }}>{label ?? "ELLAMAKA"}</span>
        </text>
      );
    },
    session_prompt_right(ctx, _value) {
      const s = extractTheme(ctx.theme.current);
      return (
        <text fg={s.primary}>{label ?? "ELLAMAKA"}</text>
      );
    },
  },
});

const tui: TuiPlugin = async (api, options) => {
  // ONT-G4 unified channel: behavior config lives in
  // `wopal.pluginConfig["tui-ellamaka"]` (three-layer settings resolved from
  // the process cwd's space root); the inline mount entry (`rawOptions`)
  // stays as a fallback. The engine only passes TUI options inline, so the
  // plugin resolves its own config until the TuiPluginApi grows a config
  // surface.
  const config = resolveTuiConfig(WOPAL_HOME, options);
  if (config.enabled === false) return;
  api.attention.soundboard.registerPack({
    id: "wopal-space",
    name: "WopalSpace",
    sounds: {
      permission: "./asset/silent.wav",
      default: "./asset/pulse-a.wav",
    },
  })
  api.attention.soundboard.activate("wopal-space")
  await api.theme.install("./ellamaka-theme.json");
  api.theme.set("ellamaka-theme");
  const theme = extractTheme(api.theme.current);
  api.slots.register(branding(theme, config.label));
};

const plugin: TuiPluginModule & { id: string } = {
  id: "tui-ellamaka",
  tui,
};

export default plugin;

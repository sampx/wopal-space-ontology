/** @jsxImportSource @opentui/solid */
/**
 * tui-ellamaka — WopalSpace TUI branding plugin.
 *
 * Registers the animated logo and label slots plus the attention sound pack.
 * Behavior config is delivered by the engine through `TuiPluginApi.pluginConfig`
 * (the whole merged `wopal.pluginConfig` table, see config.ts); the inline
 * mount entry stays as a fallback.
 */

import type { TuiPlugin, TuiPluginModule, TuiSlotPlugin } from "@wopal/ellamaka-plugin/tui";
import { extractTheme, type ThemeLike } from "./animation";
import { resolveTuiConfig } from "./config";
import { AnimatedLogo } from "./logo";

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
  // Engine-delivered config: `api.pluginConfig["tui-ellamaka"]` (the merged
  // wopal.pluginConfig table); the inline mount entry stays as a fallback.
  const config = resolveTuiConfig(api.pluginConfig, options);
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

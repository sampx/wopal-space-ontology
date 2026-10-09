/** @jsxImportSource @opentui/solid */
/**
 * Animated logo component: solid-js signal loop driving the pure animation
 * core (animation.ts) inside an @opentui canvas box, with sound cues from
 * sound.ts.
 */

import { BoxRenderable, MouseButton, MouseEvent, TextAttributes } from "@opentui/core";
import { useRenderer } from "@opentui/solid";
import { For, createMemo, createSignal, onCleanup, onMount, type JSX } from "solid-js";
import {
  CHARGE,
  CTX,
  GAP,
  GLOW_OUT,
  HOLD,
  KICK,
  LAG,
  LIFE,
  PEAK,
  bloom,
  buildIdleState,
  clamp,
  extractTheme,
  field,
  glow,
  ghost,
  idle,
  lerp,
  lit,
  noise,
  pick,
  push,
  select,
  ramp,
  shade,
  shimmerConfig,
  shimmer,
  tint,
  trace,
  wave,
  type Color,
  type Frame,
  type Glow,
  type Hold,
  type IdleState,
  shimmerConfig as SHIMMER_CFG,
  type Release,
  type Ring,
  type ThemeLike,
  type Trace,
} from "./animation";
import { soundDispose, soundPulse, soundStart } from "./sound";

// ─── Animated Logo Component ─────────────────────────────────────────

export function AnimatedLogo(props: {
  theme: ThemeLike;
  ink?: Color;
  idle?: boolean;
}) {
  const ctx = CTX;
  const theme = props.theme;
  const renderer = useRenderer();
  const [rings, setRings] = createSignal<Ring[]>([]);
  const [hold, setHold] = createSignal<Hold>();
  const [release, setRelease] = createSignal<Release>();
  const [glowSig, setGlow] = createSignal<Glow>();
  const [now, setNow] = createSignal(0);
  let box: BoxRenderable | undefined;
  let timer: ReturnType<typeof setInterval> | undefined;
  let hum = false;

  const stop = () => {
    if (!timer) return;
    clearInterval(timer);
    timer = undefined;
  };

  const tick = () => {
    const t = performance.now();
    setNow(t);
    const item = hold();
    if (item && !hum && t - item.at >= HOLD) {
      hum = true;
      soundStart();
    }
    if (item && t - item.at >= CHARGE) {
      burst(item.x, item.y);
    }
    let live = false;
    setRings((list) => {
      const next = list.filter((item) => t - item.at < LIFE);
      live = next.length > 0;
      return next;
    });
    const flash = glowSig();
    if (flash && t - flash.at >= GLOW_OUT) {
      setGlow(undefined);
    }
    if (!live) setRelease(undefined);
    if (live || hold() || release() || glowSig()) return;
    stop();
  };

  const start = () => {
    if (timer) return;
    timer = setInterval(tick, 16);
  };

  onCleanup(() => {
    stop();
    hum = false;
    soundDispose();
  });

  onMount(() => {
    if (!props.idle) return;
    setNow(performance.now());
  });

  const hit = (x: number, y: number) => {
    const char = ctx.FULL[y]?.[x];
    return char !== undefined && char !== " ";
  };

  const press = (x: number, y: number, t: number) => {
    const last = hold();
    if (last) burst(last.x, last.y);
    setNow(t);
    if (!last) setRelease(undefined);
    setHold({ x, y, at: t, glyph: select(x, y, ctx) });
    hum = false;
    start();
  };

  const burst = (x: number, y: number) => {
    const item = hold();
    if (!item) return;
    hum = false;
    const t = performance.now();
    const age = t - item.at;
    const rise = ramp(age, HOLD, CHARGE);
    const level = push(rise);
    setHold(undefined);
    setRelease({ x, y, at: t, glyph: item.glyph, level, rise });
    if (item.glyph !== undefined) {
      setGlow({
        glyph: item.glyph,
        at: t,
        force: lerp(0.18, 1.5, rise * level),
      });
    }
    setRings((list) => [
      ...list,
      {
        x: x + 0.5,
        y: y * 2 + 1,
        at: t,
        force: lerp(0.82, 2.55, level),
        kick: lerp(0.32, 0.32 + KICK, level),
      },
    ]);
    setNow(t);
    start();
    soundPulse(lerp(0.8, 1, level));
  };

  const frame = createMemo(() => {
    const t = now();
    const item = hold();
    return {
      t,
      list: rings(),
      hold: item,
      release: release(),
      glow: glowSig(),
      spark: item ? noise(item.x, item.y, t) : 0,
    };
  });

  const dusk = createMemo(() => {
    const base = frame();
    const t = base.t - LAG;
    const item = base.hold;
    return {
      t,
      list: base.list,
      hold: item,
      release: base.release,
      glow: base.glow,
      spark: item ? noise(item.x, item.y, t) : 0,
    };
  });

  const idleState = createMemo(() =>
    props.idle ? buildIdleState(frame().t, ctx) : undefined,
  );
  const useSubpixelBlocks = () => renderer.capabilities?.rgb === true;

  const renderLine = (
    line: string,
    y: number,
    inkColor: Color,
    bold: boolean,
    off: number,
    f: Frame,
    d: Frame,
    state: IdleState | undefined,
  ): JSX.Element[] => {
    const shadow = tint(theme.background, inkColor, 0.25);
    const attrs = bold ? TextAttributes.BOLD : undefined;

    return Array.from(line).map((char, i) => {
      if (char === " ") {
        return (
          <text fg={inkColor} attributes={attrs} selectable={false}>
            {char}
          </text>
        );
      }

      const h = field(off + i, y, f, ctx);
      const charLit = lit(char);
      const pulseTop = state
        ? idle(off + i, y * 2, f, ctx, state)
        : { glow: 0, peak: 0, primary: 0 };
      const pulseBot = state
        ? idle(off + i, y * 2 + 1, f, ctx, state)
        : { glow: 0, peak: 0, primary: 0 };
      const peakMixTop = charLit ? Math.min(1, pulseTop.peak) : 0;
      const peakMixBot = charLit ? Math.min(1, pulseBot.peak) : 0;
      const primaryMixTop = charLit ? Math.min(1, pulseTop.primary) : 0;
      const primaryMixBot = charLit ? Math.min(1, pulseBot.primary) : 0;
      const inkTopTint =
        primaryMixTop > 0
          ? tint(inkColor, theme.primary, primaryMixTop)
          : inkColor;
      const inkBotTint =
        primaryMixBot > 0
          ? tint(inkColor, theme.primary, primaryMixBot)
          : inkColor;
      const inkTop =
        peakMixTop > 0 ? tint(inkTopTint, PEAK, peakMixTop) : inkTopTint;
      const inkBot =
        peakMixBot > 0 ? tint(inkBotTint, PEAK, peakMixBot) : inkBotTint;
      const pulse = {
        glow: (pulseTop.glow + pulseBot.glow) / 2,
        peak: (pulseTop.peak + pulseBot.peak) / 2,
        primary: (pulseTop.primary + pulseBot.primary) / 2,
      };
      const peakMix = charLit ? Math.min(1, pulse.peak) : 0;
      const primaryMix = charLit ? Math.min(1, pulse.primary) : 0;
      const inkPrimary =
        primaryMix > 0 ? tint(inkColor, theme.primary, primaryMix) : inkColor;
      const inkTinted =
        peakMix > 0 ? tint(inkPrimary, PEAK, peakMix) : inkPrimary;
      const shadowMixCfg = state?.cfg.shadowMix ?? shimmerConfig.shadowMix;
      const shadowMixTop = Math.min(1, pulseTop.peak * shadowMixCfg);
      const shadowMixBot = Math.min(1, pulseBot.peak * shadowMixCfg);
      const shadowTop =
        shadowMixTop > 0 ? tint(shadow, PEAK, shadowMixTop) : shadow;
      const shadowBot =
        shadowMixBot > 0 ? tint(shadow, PEAK, shadowMixBot) : shadow;
      const shadowMix = Math.min(1, pulse.peak * shadowMixCfg);
      const shadowTinted =
        shadowMix > 0 ? tint(shadow, PEAK, shadowMix) : shadow;
      const n = wave(off + i, y, f, charLit, ctx) + h;
      const s = wave(off + i, y, d, false, ctx) + h;
      const p = charLit ? pick(off + i, y, f, ctx) : 0;
      const e = charLit ? trace(off + i, y, f, ctx) : 0;
      const b = charLit ? bloom(off + i, y, f, ctx) : 0;
      const q = shimmer(off + i, y, f, ctx);

      if (char === "_") {
        return (
          <text
            fg={shade(inkTinted, theme, s * 0.08)}
            bg={shade(shadowTinted, theme, ghost(s, 0.24) + ghost(q, 0.06))}
            attributes={attrs}
            selectable={false}
          >
            {" "}
          </text>
        );
      }

      if (char === "^") {
        return (
          <text
            fg={shade(inkTop, theme, n + p + e + b)}
            bg={shade(
              shadowBot,
              theme,
              ghost(s, 0.18) + ghost(q, 0.05) + ghost(b, 0.08),
            )}
            attributes={attrs}
            selectable={false}
          >
            ▀
          </text>
        );
      }

      if (char === "~") {
        return (
          <text
            fg={shade(shadowTop, theme, ghost(s, 0.22) + ghost(q, 0.05))}
            attributes={attrs}
            selectable={false}
          >
            ▀
          </text>
        );
      }

      if (char === ",") {
        return (
          <text
            fg={shade(shadowBot, theme, ghost(s, 0.22) + ghost(q, 0.05))}
            attributes={attrs}
            selectable={false}
          >
            ▄
          </text>
        );
      }

      if (char === "█" && useSubpixelBlocks()) {
        return (
          <text
            fg={shade(inkTop, theme, n + p + e + b)}
            bg={shade(inkBot, theme, n + p + e + b)}
            attributes={attrs}
            selectable={false}
          >
            ▀
          </text>
        );
      }

      if (char === "▀") {
        return (
          <text
            fg={shade(inkTop, theme, n + p + e + b)}
            attributes={attrs}
            selectable={false}
          >
            ▀
          </text>
        );
      }

      if (char === "▄") {
        return (
          <text
            fg={shade(inkBot, theme, n + p + e + b)}
            attributes={attrs}
            selectable={false}
          >
            ▄
          </text>
        );
      }

      return (
        <text
          fg={shade(inkTinted, theme, n + p + e + b)}
          attributes={attrs}
          selectable={false}
        >
          {char}
        </text>
      );
    });
  };

  const mouse = (evt: MouseEvent) => {
    if (!box) return;
    if (
      (evt.type === "down" || evt.type === "drag") &&
      evt.button === MouseButton.LEFT
    ) {
      const x = evt.x - box.x;
      const y = evt.y - box.y;
      if (!hit(x, y)) return;
      if (evt.type === "drag" && hold()) return;
      evt.preventDefault();
      evt.stopPropagation();
      const t = performance.now();
      press(x, y, t);
      return;
    }

    if (!hold()) return;
    if (evt.type === "up") {
      const item = hold();
      if (!item) return;
      burst(item.x, item.y);
    }
  };

  return (
    <box ref={(item: BoxRenderable) => (box = item)}>
      <box
        position="absolute"
        top={0}
        left={0}
        width={ctx.FULL[0]?.length ?? 0}
        height={ctx.FULL.length}
        zIndex={1}
        onMouse={mouse}
      />
      <For each={ctx.shape.left}>
        {(line, index) => (
          <box flexDirection="row" gap={1}>
            <box flexDirection="row">
              {renderLine(
                line,
                index(),
                props.ink ?? theme.textMuted,
                !!props.ink,
                0,
                frame(),
                dusk(),
                idleState(),
              )}
            </box>
            <box flexDirection="row">
              {renderLine(
                ctx.shape.right[index()],
                index(),
                props.ink ?? theme.text,
                true,
                ctx.LEFT + GAP,
                frame(),
                dusk(),
                idleState(),
              )}
            </box>
          </box>
        )}
      </For>
    </box>
  );
}

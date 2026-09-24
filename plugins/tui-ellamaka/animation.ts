/**
 * Animation core for the WopalSpace animated logo: shimmer/ring/burst
 * math over the glyph-mapped logo shape.
 *
 * Pure computation — no renderer or solid-js imports here. The component
 * (logo.tsx) consumes these functions per animation frame.
 */

import { RGBA } from "@opentui/core";

// ─── Animation Constants ─────────────────────────────────────────────

export type ShimmerConfig = {
  period: number;
  rings: number;
  sweepFraction: number;
  coreWidth: number;
  coreAmp: number;
  softWidth: number;
  softAmp: number;
  tail: number;
  tailAmp: number;
  haloWidth: number;
  haloOffset: number;
  haloAmp: number;
  breathBase: number;
  noise: number;
  ambientAmp: number;
  ambientCenter: number;
  ambientWidth: number;
  shadowMix: number;
  primaryMix: number;
  originX: number;
  originY: number;
};

export const shimmerConfig: ShimmerConfig = {
  period: 4600,
  rings: 2,
  sweepFraction: 1,
  coreWidth: 1.2,
  coreAmp: 1.9,
  softWidth: 10,
  softAmp: 1.6,
  tail: 5,
  tailAmp: 0.64,
  haloWidth: 4.3,
  haloOffset: 0.6,
  haloAmp: 0.16,
  breathBase: 0.04,
  noise: 0.1,
  ambientAmp: 0.36,
  ambientCenter: 0.5,
  ambientWidth: 0.34,
  shadowMix: 0.1,
  primaryMix: 0.3,
  originX: 4.5,
  originY: 13.5,
};

export const GAP = 1;
const WIDTH = 0.76;
const GAIN = 2.3;
const FLASH = 2.15;
const TRAIL = 0.28;
const SWELL = 0.24;
const WIDE = 1.85;
const DRIFT = 1.45;
const EXPAND = 1.62;
export const LIFE = 1020;
export const CHARGE = 3000;
export const HOLD = 90;
const SINK = 40;
const ARC = 2.2;
const FORK = 1.2;
const DIM = 1.04;
export const KICK = 0.86;
export const LAG = 60;
const SUCK = 0.34;
const SHIMMER_IN = 60;
const SHIMMER_OUT = 2.8;
const TRACE = 0.033;
const TAIL = 1.8;
const TRACE_IN = 200;
export const GLOW_OUT = 1600;
export const PEAK = RGBA.fromInts(255, 255, 255);

// ─── Types ───────────────────────────────────────────────────────────

export type Ring = { x: number; y: number; at: number; force: number; kick: number };
export type Hold = { x: number; y: number; at: number; glyph: number | undefined };
export type Release = {
  x: number;
  y: number;
  at: number;
  glyph: number | undefined;
  level: number;
  rise: number;
};
export type Glow = { glyph: number; at: number; force: number };
export type Frame = {
  t: number;
  list: Ring[];
  hold: Hold | undefined;
  release: Release | undefined;
  glow: Glow | undefined;
  spark: number;
};
export type Trace = { glyph: number; i: number; l: number };

export type IdleState = {
  cfg: ShimmerConfig;
  reach: number;
  rings: number;
  active: Array<{ head: number; eased: number; ambient: number }>;
};

export type LogoShape = { left: string[]; right: string[] };

export type LogoContext = {
  LEFT: number;
  FULL: string[];
  SPAN: number;
  MAP: ReturnType<typeof mapGlyphs>;
  shape: LogoShape;
};

// ─── Math Utilities ──────────────────────────────────────────────────

const NEAR = [
  [1, 0],
  [1, 1],
  [0, 1],
  [-1, 1],
  [-1, 0],
  [-1, -1],
  [0, -1],
  [1, -1],
] as const;

export function clamp(n: number) {
  return Math.max(0, Math.min(1, n));
}

export function lerp(a: number, b: number, t: number) {
  return a + (b - a) * clamp(t);
}

export function ease(t: number) {
  const p = clamp(t);
  return p * p * (3 - 2 * p);
}

export function push(t: number) {
  const p = clamp(t);
  return ease(p * p);
}

export function ramp(t: number, start: number, end: number) {
  if (end <= start) return ease(t >= end ? 1 : 0);
  return ease((t - start) / (end - start));
}

export function noise(x: number, y: number, t: number) {
  const n = Math.sin(x * 12.9898 + y * 78.233 + t * 0.043) * 43758.5453;
  return n - Math.floor(n);
}

export function lit(char: string) {
  return char !== " " && char !== "_" && char !== "~" && char !== ",";
}

export function key(x: number, y: number) {
  return `${x},${y}`;
}

// ─── Color Utilities ─────────────────────────────────────────────────

export type Color = RGBA

export type ThemeLike = {
  primary: Color
  background: Color
  text: Color
  textMuted: Color
}

export function extractTheme(theme: { primary: RGBA; background: RGBA; text: RGBA; textMuted: RGBA }): ThemeLike {
  return {
    primary: theme.primary,
    background: theme.background,
    text: theme.text,
    textMuted: theme.textMuted,
  }
}

export function tint(base: Color, overlay: Color, alpha: number): Color {
  const r = base.r + (overlay.r - base.r) * alpha;
  const g = base.g + (overlay.g - base.g) * alpha;
  const b = base.b + (overlay.b - base.b) * alpha;
  return RGBA.fromInts(
    Math.round(r * 255),
    Math.round(g * 255),
    Math.round(b * 255),
  );
}

export function glow(base: Color, theme: ThemeLike, n: number) {
  const mid = tint(base, theme.primary, 0.84);
  const top = tint(theme.primary, PEAK, 0.96);
  if (n <= 1)
    return tint(base, mid, Math.min(1, Math.sqrt(Math.max(0, n)) * 1.14));
  return tint(mid, top, Math.min(1, 1 - Math.exp(-2.4 * (n - 1))));
}

export function shade(base: Color, theme: ThemeLike, n: number) {
  if (n >= 0) return glow(base, theme, n);
  return tint(base, theme.background, Math.min(0.82, -n * 0.64));
}

export function ghost(n: number, scale: number) {
  if (n < 0) return n;
  return n * scale;
}

// ─── Glyph Mapping ───────────────────────────────────────────────────

export function route(list: Array<{ x: number; y: number }>) {
  const left = new Map(list.map((item) => [key(item.x, item.y), item]));
  const path: Array<{ x: number; y: number }> = [];
  let cur = [...left.values()].sort((a, b) => a.y - b.y || a.x - b.x)[0];
  let dir = { x: 1, y: 0 };

  while (cur) {
    path.push(cur);
    left.delete(key(cur.x, cur.y));
    if (!left.size) return path;

    const next = NEAR.map(([dx, dy]) => left.get(key(cur.x + dx, cur.y + dy)))
      .filter((item): item is { x: number; y: number } => !!item)
      .sort((a, b) => {
        const ax = a.x - cur.x;
        const ay = a.y - cur.y;
        const bx = b.x - cur.x;
        const by = b.y - cur.y;
        const adot = ax * dir.x + ay * dir.y;
        const bdot = bx * dir.x + by * dir.y;
        if (adot !== bdot) return bdot - adot;
        return Math.abs(ax) + Math.abs(ay) - (Math.abs(bx) + Math.abs(by));
      })[0];

    if (!next) {
      cur = [...left.values()].sort((a, b) => {
        const da = (a.x - cur.x) ** 2 + (a.y - cur.y) ** 2;
        const db = (b.x - cur.x) ** 2 + (b.y - cur.y) ** 2;
        return da - db;
      })[0];
      dir = { x: 1, y: 0 };
      continue;
    }

    dir = { x: next.x - cur.x, y: next.y - cur.y };
    cur = next;
  }

  return path;
}

export function mapGlyphs(full: string[]) {
  const cells = [] as Array<{ x: number; y: number }>;

  for (let y = 0; y < full.length; y++) {
    for (let x = 0; x < (full[y]?.length ?? 0); x++) {
      if (lit(full[y]?.[x] ?? " ")) cells.push({ x, y });
    }
  }

  const all = new Map(cells.map((item) => [key(item.x, item.y), item]));
  const seen = new Set<string>();
  const glyph = new Map<string, number>();
  const trace = new Map<string, Trace>();
  const center = new Map<number, { x: number; y: number }>();
  let id = 0;

  for (const item of cells) {
    const start = key(item.x, item.y);
    if (seen.has(start)) continue;
    const stack = [item];
    const part = [] as Array<{ x: number; y: number }>;
    seen.add(start);

    while (stack.length) {
      const cur = stack.pop()!;
      part.push(cur);
      glyph.set(key(cur.x, cur.y), id);
      for (const [dx, dy] of NEAR) {
        const next = all.get(key(cur.x + dx, cur.y + dy));
        if (!next) continue;
        const mark = key(next.x, next.y);
        if (seen.has(mark)) continue;
        seen.add(mark);
        stack.push(next);
      }
    }

    const path = route(part);
    path.forEach((cell, i) =>
      trace.set(key(cell.x, cell.y), { glyph: id, i, l: path.length }),
    );
    center.set(id, {
      x: part.reduce((sum, item) => sum + item.x, 0) / part.length + 0.5,
      y: (part.reduce((sum, item) => sum + item.y, 0) / part.length) * 2 + 1,
    });
    id++;
  }

  return { glyph, trace, center };
}

export function build(shape: LogoShape): LogoContext {
  const LEFT = shape.left[0]?.length ?? 0;
  const FULL = shape.left.map(
    (line, i) => line + " ".repeat(GAP) + shape.right[i],
  );
  const SPAN = Math.hypot(FULL[0]?.length ?? 0, FULL.length * 2) * 0.94;
  return { LEFT, FULL, SPAN, MAP: mapGlyphs(FULL), shape };
}

export const LOGO_LEFT = [
  "                 ",
  "█▀▀▀ █   █   █▀▀█",
  "█▀▀▀ █   █   █▀▀█",
  "▀▀▀▀ ▀▀▀ ▀▀▀ ▀  ▀",
];

export const LOGO_RIGHT = [
  "                    ",
  "█▀▀▀█ █▀▀█ █  ▀ █▀▀█",
  "█ ▀ █ █▀▀█ █▀▀  █▀▀█",
  "▀ ▀ ▀ ▀  ▀ ▀  ▀ ▀  ▀",
];

export const CTX = build({ left: LOGO_LEFT, right: LOGO_RIGHT });

// ─── Animation Functions ─────────────────────────────────────────────

export function shimmer(x: number, y: number, frame: Frame, ctx: LogoContext) {
  return frame.list.reduce((best, item) => {
    const age = frame.t - item.at;
    if (age < SHIMMER_IN || age > LIFE) return best;
    const dx = x + 0.5 - item.x;
    const dy = y * 2 + 1 - item.y;
    const dist = Math.hypot(dx, dy);
    const p = age / LIFE;
    const r = ctx.SPAN * (1 - (1 - p) ** EXPAND);
    const lag = r - dist;
    if (lag < 0.18 || lag > SHIMMER_OUT) return best;
    const band = Math.exp(-(((lag - 1.05) / 0.68) ** 2));
    const wobble = 0.5 + 0.5 * Math.sin(frame.t * 0.035 + x * 0.9 + y * 1.7);
    const n = band * wobble * (1 - p) ** 1.45;
    if (n > best) return n;
    return best;
  }, 0);
}

export function remain(
  x: number,
  y: number,
  item: Release,
  t: number,
  ctx: LogoContext,
) {
  const age = t - item.at;
  if (age < 0 || age > LIFE) return 0;
  const p = age / LIFE;
  const dx = x + 0.5 - item.x - 0.5;
  const dy = y * 2 + 1 - item.y * 2 - 1;
  const dist = Math.hypot(dx, dy);
  const r = ctx.SPAN * (1 - (1 - p) ** EXPAND);
  if (dist > r) return 1;
  return clamp((r - dist) / 1.35 < 1 ? 1 - (r - dist) / 1.35 : 0);
}

export function wave(
  x: number,
  y: number,
  frame: Frame,
  live: boolean,
  ctx: LogoContext,
) {
  return frame.list.reduce((sum, item) => {
    const age = frame.t - item.at;
    if (age < 0 || age > LIFE) return sum;
    const p = age / LIFE;
    const dx = x + 0.5 - item.x;
    const dy = y * 2 + 1 - item.y;
    const dist = Math.hypot(dx, dy);
    const r = ctx.SPAN * (1 - (1 - p) ** EXPAND);
    const fade = (1 - p) ** 1.32;
    const j =
      1.02 +
      noise(x + item.x * 0.7, y + item.y * 0.7, item.at * 0.002 + age * 0.06) *
        0.52;
    const edge =
      Math.exp(-(((dist - r) / WIDTH) ** 2)) * GAIN * fade * item.force * j;
    const swell =
      Math.exp(-(((dist - Math.max(0, r - DRIFT)) / WIDE) ** 2)) *
      SWELL *
      fade *
      item.force;
    const trail =
      dist < r
        ? Math.exp(-(r - dist) / 2.4) *
          TRAIL *
          fade *
          item.force *
          lerp(0.92, 1.22, j)
        : 0;
    const flash =
      Math.exp(-(dist * dist) / 3.2) *
      FLASH *
      item.force *
      Math.max(0, 1 - age / 140) *
      lerp(0.95, 1.18, j);
    const kick =
      Math.exp(-(dist * dist) / 2) * item.kick * Math.max(0, 1 - age / 100);
    const suck =
      Math.exp(-(((dist - 1.25) / 0.75) ** 2)) *
      item.kick *
      SUCK *
      Math.max(0, 1 - age / 110);
    const wake =
      live && dist < r ? Math.exp(-(r - dist) / 1.25) * 0.32 * fade : 0;
    return sum + edge + swell + trail + flash + wake - kick - suck;
  }, 0);
}

export function field(x: number, y: number, frame: Frame, ctx: LogoContext) {
  const held = frame.hold;
  const rest = frame.release;
  const item = held ?? rest;
  if (!item) return 0;
  const rise = held ? ramp(frame.t - held.at, HOLD, CHARGE) : rest!.rise;
  const level = held ? push(rise) : rest!.level;
  const body = rise;
  const storm = level * level;
  const sink = held ? ramp(frame.t - held.at, SINK, CHARGE) : rest!.rise;
  const dx = x + 0.5 - item.x - 0.5;
  const dy = y * 2 + 1 - item.y * 2 - 1;
  const dist = Math.hypot(dx, dy);
  const angle = Math.atan2(dy, dx);
  const spin = frame.t * lerp(0.008, 0.018, storm);
  const dim =
    lerp(0, DIM, sink) *
    lerp(0.99, 1.01, 0.5 + 0.5 * Math.sin(frame.t * 0.014));
  const core =
    Math.exp(-(dist * dist) / Math.max(0.22, lerp(0.22, 3.2, body))) *
    lerp(0.42, 2.45, body);
  const shell =
    Math.exp(
      -(
        ((dist - lerp(0.16, 2.05, body)) /
          Math.max(0.18, lerp(0.18, 0.82, body))) **
        2
      ),
    ) * lerp(0.1, 0.95, body);
  const ember =
    Math.exp(
      -(
        ((dist - lerp(0.45, 2.65, body)) /
          Math.max(0.14, lerp(0.14, 0.62, body))) **
        2
      ),
    ) * lerp(0.02, 0.78, body);
  const arc = Math.max(0, Math.cos(angle * 3 - spin + frame.spark * 2.2)) ** 8;
  const seam = Math.max(0, Math.cos(angle * 5 + spin * 1.55)) ** 12;
  const ring =
    Math.exp(-(((dist - lerp(1.05, 3, level)) / 0.48) ** 2)) *
    arc *
    lerp(0.03, 0.5 + ARC, storm);
  const fork =
    Math.exp(-(((dist - (1.55 + storm * 2.1)) / 0.36) ** 2)) *
    seam *
    storm *
    FORK;
  const spark =
    Math.max(0, noise(x, y, frame.t) - lerp(0.94, 0.66, storm)) *
    lerp(0, 5.4, storm);
  const glitch = spark * Math.exp(-dist / Math.max(1.2, 3.1 - storm));
  const crack = Math.max(0, Math.cos((dx - dy) * 1.6 + spin * 2.1)) ** 18;
  const lash =
    crack *
    Math.exp(-(((dist - (1.95 + storm * 2)) / 0.28) ** 2)) *
    storm *
    1.1;
  const flicker =
    Math.max(0, noise(item.x * 3.1, item.y * 2.7, frame.t * 1.7) - 0.72) *
    Math.exp(-(dist * dist) / 0.15) *
    lerp(0.08, 0.42, body);
  const fade =
    frame.release && !frame.hold
      ? remain(x, y, frame.release, frame.t, ctx)
      : 1;
  return (
    (core + shell + ember + ring + fork + glitch + lash + flicker - dim) * fade
  );
}

export function pick(x: number, y: number, frame: Frame, ctx: LogoContext) {
  const held = frame.hold;
  const rest = frame.release;
  const item = held ?? rest;
  if (!item) return 0;
  const rise = held ? ramp(frame.t - held.at, HOLD, CHARGE) : rest!.rise;
  const dx = x + 0.5 - item.x - 0.5;
  const dy = y * 2 + 1 - item.y * 2 - 1;
  const dist = Math.hypot(dx, dy);
  const fade =
    frame.release && !frame.hold
      ? remain(x, y, frame.release, frame.t, ctx)
      : 1;
  return Math.exp(-(dist * dist) / 1.7) * lerp(0.2, 0.96, rise) * fade;
}

export function select(x: number, y: number, ctx: LogoContext) {
  const direct = ctx.MAP.glyph.get(key(x, y));
  if (direct !== undefined) return direct;
  const near = NEAR.map(([dx, dy]) =>
    ctx.MAP.glyph.get(key(x + dx, y + dy)),
  ).find((item): item is number => item !== undefined);
  return near;
}

export function trace(x: number, y: number, frame: Frame, ctx: LogoContext) {
  const held = frame.hold;
  const rest = frame.release;
  const item = held ?? rest;
  if (!item || item.glyph === undefined) return 0;
  const step = ctx.MAP.trace.get(key(x, y));
  if (!step || step.glyph !== item.glyph || step.l < 2) return 0;
  const age = frame.t - item.at;
  const rise = held ? ramp(age, HOLD, CHARGE) : rest!.rise;
  const appear = held ? ramp(age, 0, TRACE_IN) : 1;
  const speed = lerp(TRACE * 0.48, TRACE * 0.88, rise);
  const head = (age * speed) % step.l;
  const dist = Math.min(
    Math.abs(step.i - head),
    step.l - Math.abs(step.i - head),
  );
  const tail = (head - TAIL + step.l) % step.l;
  const lag = Math.min(
    Math.abs(step.i - tail),
    step.l - Math.abs(step.i - tail),
  );
  const fade =
    frame.release && !frame.hold
      ? remain(x, y, frame.release, frame.t, ctx)
      : 1;
  const core = Math.exp(-((dist / 1.05) ** 2)) * lerp(0.8, 2.35, rise);
  const glowVal = Math.exp(-((dist / 1.85) ** 2)) * lerp(0.08, 0.34, rise);
  const trail = Math.exp(-((lag / 1.45) ** 2)) * lerp(0.04, 0.42, rise);
  return (core + glowVal + trail) * appear * fade;
}

export function idle(
  x: number,
  pixelY: number,
  frame: Frame,
  ctx: LogoContext,
  state: IdleState,
): { glow: number; peak: number; primary: number } {
  const cfg = state.cfg;
  const dx = x + 0.5 - cfg.originX;
  const dy = pixelY - cfg.originY;
  const dist = Math.hypot(dx, dy);
  const angle = Math.atan2(dy, dx);
  const wob1 = noise(x * 0.32, pixelY * 0.25, frame.t * 0.0005) - 0.5;
  const wob2 = noise(x * 0.12, pixelY * 0.08, frame.t * 0.00022) - 0.5;
  const ripple = Math.sin(angle * 3 + frame.t * 0.0012) * 0.3;
  const jitter = (wob1 * 0.55 + wob2 * 0.32 + ripple * 0.18) * cfg.noise;
  const traveled = dist + jitter;
  let glowSum = 0;
  let peakSum = 0;
  let haloSum = 0;
  let primarySum = 0;
  let ambientSum = 0;
  for (const active of state.active) {
    const head = active.head;
    const eased = active.eased;
    const delta = traveled - head;
    const core = Math.exp(-(Math.abs(delta / cfg.coreWidth) ** 1.8));
    const soft = Math.exp(-(Math.abs(delta / cfg.softWidth) ** 1.6));
    const tailRange = cfg.tail * 2.6;
    const tail =
      delta < 0 && delta > -tailRange ? (1 + delta / tailRange) ** 2.6 : 0;
    const haloDelta = delta + cfg.haloOffset;
    const haloBand = Math.exp(-(Math.abs(haloDelta / cfg.haloWidth) ** 1.6));
    glowSum += (soft * cfg.softAmp + tail * cfg.tailAmp) * eased;
    peakSum += core * cfg.coreAmp * eased;
    haloSum += haloBand * cfg.haloAmp * eased;
    primarySum += (haloBand + tail * 0.6) * eased;
    ambientSum += active.ambient;
  }
  ambientSum /= state.rings;
  return {
    glow: glowSum / state.rings,
    peak: cfg.breathBase + ambientSum + (peakSum + haloSum) / state.rings,
    primary: (primarySum / state.rings) * cfg.primaryMix,
  };
}

export function bloom(x: number, y: number, frame: Frame, ctx: LogoContext) {
  const item = frame.glow;
  if (!item) return 0;
  const glyph = ctx.MAP.glyph.get(key(x, y));
  if (glyph !== item.glyph) return 0;
  const age = frame.t - item.at;
  if (age < 0 || age > GLOW_OUT) return 0;
  const p = age / GLOW_OUT;
  const flash = (1 - p) ** 2;
  const dx = x + 0.5 - ctx.MAP.center.get(item.glyph)!.x;
  const dy = y * 2 + 1 - ctx.MAP.center.get(item.glyph)!.y;
  const bias = Math.exp(-((Math.hypot(dx, dy) / 2.8) ** 2));
  return lerp(item.force, item.force * 0.18, p) * lerp(0.72, 1.1, bias) * flash;
}

export function buildIdleState(t: number, ctx: LogoContext): IdleState {
  const cfg = shimmerConfig;
  const w = ctx.FULL[0]?.length ?? 1;
  const h = ctx.FULL.length * 2;
  const corners: [number, number][] = [
    [0, 0],
    [w, 0],
    [0, h],
    [w, h],
  ];
  let maxCorner = 0;
  for (const [cx, cy] of corners) {
    const d = Math.hypot(cx - cfg.originX, cy - cfg.originY);
    if (d > maxCorner) maxCorner = d;
  }
  const reach = maxCorner + cfg.tail * 2;
  const rings = Math.max(1, Math.floor(cfg.rings));
  const active = [] as IdleState["active"];
  for (let i = 0; i < rings; i++) {
    const offset = i / rings;
    const cyclePhase = (t / cfg.period + offset) % 1;
    if (cyclePhase >= cfg.sweepFraction) continue;
    const phase = cyclePhase / cfg.sweepFraction;
    const envelope = Math.sin(phase * Math.PI);
    const eased = envelope * envelope * (3 - 2 * envelope);
    const d = (phase - cfg.ambientCenter) / cfg.ambientWidth;
    active.push({
      head: phase * reach,
      eased,
      ambient: Math.abs(d) < 1 ? (1 - d * d) ** 2 * cfg.ambientAmp : 0,
    });
  }
  return { cfg, reach, rings, active };
}

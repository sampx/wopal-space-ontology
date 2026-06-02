/** @jsxImportSource @opentui/solid */
import { RGBA } from "@opentui/core"
import type {
  TuiPlugin,
  TuiPluginApi,
  TuiPluginModule,
  TuiSlotPlugin,
} from "@opencode-ai/plugin/tui"

const art = {
  left: [
    "                   ",
    "█▀▀▀ █    █    █▀▀█",
    "█___ █    █    █__█",
    "▀▀▀▀ ▀▀▀▀ ▀▀▀▀ ▀~~▀",
  ],
  right: [
    "                   ",
    "█▄▀█ █▀▀█ █  █ █▀▀█",
    "█__█ █__█ █▀▄  █__█",
    "▀  ▀ ▀~~▀ ▀  ▀ ▀~~▀",
  ],
}

type Color = RGBA

const ink = (map: Record<string, unknown>, name: string, fallback: string): Color => {
  const value = map[name]
  if (value instanceof RGBA) return value
  if (typeof value === "string") return RGBA.fromHex(value)
  return RGBA.fromHex(fallback)
}

const skin = (map: Record<string, unknown>) => ({
  text: ink(map, "text", "#f0f0f0"),
  muted: ink(map, "textMuted", "#a5a5a5"),
  accent: ink(map, "primary", "#5f87ff"),
  bg: ink(map, "backgroundPanel", "#1d1d1d"),
  border: ink(map, "border", "#4a4a4a"),
})

// Map marker characters to styled segments:
// _ → space with shadow bg, ^ → ▀ with fg + shadow bg,
// ~ → ▀ with shadow fg, space → space, other → char with fg
const draw = (line: string, fg: Color, shadow: Color, bg: Color) => {
  type Seg = { text: string; fg?: Color; bg?: Color }
  const segs: Seg[] = []
  let buf = ""
  let curFg: Color | undefined
  let curBg: Color | undefined

  const flush = () => {
    if (!buf) return
    segs.push({ text: buf, fg: curFg, bg: curBg })
    buf = ""
  }

  for (const ch of line) {
    let sFg: Color | undefined
    let sBg: Color | undefined
    let out: string

    if (ch === "_") {
      sBg = bg
      out = " "
    } else if (ch === "^") {
      sFg = fg
      sBg = bg
      out = "▀"
    } else if (ch === "~") {
      sFg = shadow
      out = "▀"
    } else if (ch === " ") {
      out = " "
    } else {
      sFg = fg
      out = ch
    }

    if (curFg !== sFg || curBg !== sBg) {
      flush()
      curFg = sFg
      curBg = sBg
    }
    buf += out
  }
  flush()
  return segs
}

const branding = (): TuiSlotPlugin => ({
  slots: {
    home_logo(ctx) {
      const s = skin(ctx.theme.current)
      return (
        <box flexDirection="column">
          {art.left.map((row, i) => (
            <box flexDirection="row">
              {draw(row, s.muted, s.border, s.bg).map((seg) => (
                <text fg={seg.fg} backgroundColor={seg.bg}>{seg.text}</text>
              ))}
              <text> </text>
              {draw(art.right[i], s.accent, s.border, s.bg).map((seg) => (
                <text fg={seg.fg} backgroundColor={seg.bg}>{seg.text}</text>
              ))}
            </box>
          ))}
        </box>
      )
    },
    home_prompt_right(ctx) {
      const s = skin(ctx.theme.current)
      return (
        <text fg={s.muted}>
          <span style={{ fg: s.accent }}>ELLAMAKA</span>
        </text>
      )
    },
    session_prompt_right(ctx, value) {
      const s = skin(ctx.theme.current)
      return (
        <text fg={s.muted}>
          <span style={{ fg: s.accent }}>ELLAMAKA</span>:{value.session_id.slice(0, 8)}
        </text>
      )
    },
  },
})

const tui: TuiPlugin = async (api, options) => {
  if (options?.enabled === false) return
  await api.theme.install("./ellamaka-theme.json")
  api.theme.set("ellamaka-theme")
  api.slots.register(branding())
}

const plugin: TuiPluginModule & { id: string } = {
  id: "tui-ellamaka",
  tui,
}

export default plugin

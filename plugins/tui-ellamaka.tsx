/** @jsxImportSource @opentui/solid */
import { RGBA } from "@opentui/core"
import type {
  TuiPlugin,
  TuiPluginModule,
  TuiSlotPlugin,
} from "@opencode-ai/plugin/tui"

type Color = RGBA

const logo = [
  "                                      ",
  "█▀▀▀ █   █   ▄▀▀▄ █   █ ▄▀▀▄ █  █ ▄▀▀▄",
  "█▀▀▀ █   █   █▄▄█ ██ ██ █▄▄█ █▄▀  █▄▄█",
  "█▄▄▄ █▄▄ █▄▄ █  █ █ █ █ █  █ █ ▀▄ █  █",
]

const ink = (map: Record<string, unknown>, name: string, fallback: string): Color => {
  const value = map[name]
  if (value instanceof RGBA) return value
  if (typeof value === "string") return RGBA.fromHex(value)
  return RGBA.fromHex(fallback)
}

const skin = (map: Record<string, unknown>) => ({
  muted: ink(map, "textMuted", "#a5a5a5"),
  accent: ink(map, "primary", "#5f87ff"),
})

const branding = (): TuiSlotPlugin => ({
  slots: {
    home_logo(ctx) {
      const s = skin(ctx.theme.current)
      const r = (c: string, fg: Color) => {
        if (c === " ") return <text selectable={false}>{" "}</text>
        if (c === "█") return <text fg={fg} selectable={false}>█</text>
        if (c === "▀") return <text fg={fg} selectable={false}>▀</text>
        if (c === "▄") return <text fg={fg} selectable={false}>▄</text>
        return <text fg={fg} selectable={false}>{c}</text>
      }
      return (
        <box flexDirection="column">
          {logo.map((line) => (
            <box flexDirection="row">
              {Array.from(line).map((c) => r(c, s.accent))}
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

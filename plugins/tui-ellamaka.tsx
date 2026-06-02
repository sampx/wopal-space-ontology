/** @jsxImportSource @opentui/solid */
import { RGBA } from "@opentui/core"
import type {
  TuiPlugin,
  TuiPluginModule,
  TuiSlotPlugin,
} from "@opencode-ai/plugin/tui"

type Color = RGBA

const LOGO_LEFT = [
  "                 ",
  "█▀▀▀ █   █   █▀▀█",
  "█▀▀▀ █   █   █▀▀█",
  "▀▀▀▀ ▀▀▀ ▀▀▀ ▀  ▀",
]

const LOGO_RIGHT = [
  "                    ",
  "█▀▀▀█ █▀▀█ █  █ █▀▀█",
  "█ ▀ █ █▀▀█ █▀▀  █▀▀█",
  "▀   ▀ ▀  ▀ ▀  ▀ ▀  ▀",
]

const SHADOW_MARKER = /[_^~]/

const tint = (a: Color, b: Color, t: number): Color =>
  RGBA.fromInts(
    Math.round((a.r * (1 - t) + b.r * t) * 255),
    Math.round((a.g * (1 - t) + b.g * t) * 255),
    Math.round((a.b * (1 - t) + b.b * t) * 255),
  )

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
})

const branding = (): TuiSlotPlugin => ({
  slots: {
    home_logo(ctx) {
      const s = skin(ctx.theme.current)

      const renderLine = (line: string, fg: Color, bold: boolean) => {
        const shadow = tint(s.bg, fg, 0.25)
        const elements: any[] = []
        let i = 0

        while (i < line.length) {
          const rest = line.slice(i)
          const markerIndex = rest.search(SHADOW_MARKER)

          if (markerIndex === -1) {
            elements.push(
              <text fg={fg} fontWeight={bold ? "bold" : undefined} selectable={false}>
                {rest}
              </text>,
            )
            break
          }

          if (markerIndex > 0) {
            elements.push(
              <text fg={fg} fontWeight={bold ? "bold" : undefined} selectable={false}>
                {rest.slice(0, markerIndex)}
              </text>,
            )
          }

          const marker = rest[markerIndex]
          switch (marker) {
            case "_":
              elements.push(
                <text fg={fg} bg={shadow} fontWeight={bold ? "bold" : undefined} selectable={false}>
                  {" "}
                </text>,
              )
              break
            case "^":
              elements.push(
                <text fg={fg} bg={shadow} fontWeight={bold ? "bold" : undefined} selectable={false}>
                  ▀
                </text>,
              )
              break
            case "~":
              elements.push(
                <text fg={shadow} fontWeight={bold ? "bold" : undefined} selectable={false}>
                  ▀
                </text>,
              )
              break
          }

          i += markerIndex + 1
        }

        return elements
      }

      return (
        <box>
          {LOGO_LEFT.map((line, index) => (
            <box flexDirection="row" gap={1}>
              <box flexDirection="row">{renderLine(line, s.muted, false)}</box>
              <box flexDirection="row">{renderLine(LOGO_RIGHT[index], s.text, true)}</box>
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

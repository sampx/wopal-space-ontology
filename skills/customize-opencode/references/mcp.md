# MCP servers

`mcp:` is an object keyed by server name. Each server has a `type`:

```json
"mcp": {
  "playwright": {
    "type": "local",
    "command": ["npx", "-y", "@playwright/mcp"],
    "enabled": true,
    "env": {}
  },
  "remote-thing": {
    "type": "remote",
    "url": "https://...",
    "headers": { "Authorization": "Bearer ..." }
  }
}
```

- `"local"` — opencode spawns the server itself via `command` (an array of strings; never a single string). Optional `env` sets environment variables, optional `enabled` defaults to true.
- `"remote"` — opencode connects to an already-running server over `url`; optional `headers` adds request headers.

Use `enabled: false` to disable a server inherited from a parent config.

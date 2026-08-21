# Permissions

`permission:` is a map of action → flat string or per-tool object:

```json
"permission": {
  "edit": "deny",
  "bash": { "git *": "allow", "*": "ask" }
}
```

Actions are grouped by tool (e.g. `edit`, `bash`, `webfetch`, `websearch`). A flat string applies to the whole tool. An object maps rule patterns to actions:

- `"allow"` — always allow, no prompt.
- `"ask"` — always ask before running.
- `"deny"` — always deny.

The **last matching rule wins**; put broad rules first and narrow rules last. Example above: `git *` allowed, everything else under `bash` asks.

`"*"` in an object is a catch-all that matches any command for that tool. `permission` at the top level uses the same keys as tool names.

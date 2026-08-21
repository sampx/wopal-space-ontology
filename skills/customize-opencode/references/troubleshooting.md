# Escape hatches

When a user's config is broken and opencode won't start, these env vars help:

- `OPENCODE_DISABLE_PROJECT_CONFIG=1` — skips the project's local config and starts from globals only. Run from the project directory, opencode loads, the user edits the broken file, then they restart without the flag.
- `OPENCODE_CONFIG=/path/to/file.json` — loads an additional explicit config.
- `OPENCODE_CONFIG_CONTENT='{"$schema":"https://opencode.ai/config.json"}'` — injects inline JSON as a final local-scope merge.
- `OPENCODE_DISABLE_DEFAULT_PLUGINS=1` — skips default plugins.
- `OPENCODE_PURE=1` — skips external plugins entirely.
- `OPENCODE_DISABLE_EXTERNAL_SKILLS=1` — skips the external skill scans under `~/.claude/` and `~/.agents/`.

# When proposing edits

- Prefer the smallest edit that preserves the user's existing config.
- Preserve `$schema` and any fields the user didn't ask to change.
- For agents, skills, and plugins, prefer creating new files in the correct location over inlining everything in `opencode.json`.
- If the user's existing config is malformed, point them at the escape hatches above rather than breaking their session.
- After saving any config change, remind the user to quit and restart opencode — running sessions keep using the already-loaded config.

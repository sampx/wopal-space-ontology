---
name: ellamaka-config
description: |-
  Configure ellamaka (WopalSpace OpenCode fork) — edit config files, agent permissions, model/provider settings, and rules. Use proactively for permission changes, model config, provider setup, formatter rules, environment variables, or debugging config loading issues. Covers both upstream OpenCode paths and ellamaka-specific wopal-space mode config priority order.
  
  Examples:
  - user: "Add Anthropic as a provider" → edit global or wopal-space config
  - user: "Restrict agent permissions" → edit agent frontmatter permission or settings.jsonc
  - user: "Config not loading" → check wopal-space mode config priority
  - user: "Disable gofmt formatter" → edit formatters section, set languages.gofmt.enabled = false
---

# ellamaka Configuration

Help users configure ellamaka (WopalSpace OpenCode fork) through guided setup of config files and rules.

<reference>

## File Locations

### ellamaka (WopalSpace Fork)

| Type | Global | Space |
|------|-------------------|-------------|
| **Config** | `~/.wopal/ellamaka/config/opencode.jsonc` | `.wopal/config/settings.jsonc` |
| **Agent** | `~/.wopal/agents/{name}.md` | `.wopal/agents/{name}.md` |

**Wopal-space mode config loading order** (priority low→high):
1. defaults (built-in)
2. `~/.wopal/ellamaka/config/opencode.jsonc` global
3. `.wopal/config/settings.jsonc` → `ellamaka` 
4. `.wopal/agents/{name}.md`

> ⚠️ Wopal-space mode bypasses standard config returns directly, **skipping** project `opencode.jsonc`, `~/.config/opencode/`, `OPENCODE_CONFIG`.

> **Precedence:** Project > Global. Configs are merged, not replaced.

</reference>

<config_file>

## Config File (opencode.jsonc or config/settings.jsonc#ellamaka)

### Basic Setup

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "model": "anthropic/claude-sonnet-4-20250514",
  "theme": "opencode",
}
```

### Key Options

| Option | Purpose | Example |
|--------|---------|---------|
| `model` | Default model | `"anthropic/claude-sonnet-4-20250514"` |
| `small_model` | Lightweight tasks | `"anthropic/claude-3-5-haiku-20241022"` |
| `theme` | UI theme | `"opencode"`, `"catppuccin"`, `"dracula"` |
| `autoupdate` | Auto-update OpenCode | `true` / `false` |
| `share` | Session sharing | `"manual"` / `"auto"` / `"disabled"` |

### Permissions

Control what requires approval using the `permission` field.

```jsonc
{
  "permission": {
    "edit": "allow",           // "allow" | "ask" | "deny"
    "bash": {
      "npm *": "allow",        // pattern matching
      "git *": "allow",
      "rm *": "ask",
      "*": "ask"               // default for this tool
    },
    "webfetch": "allow",
    "skill": {
      "*": "allow",
      "dangerous-*": "deny"
    }
  }
}
```

### Legacy Configuration

Agents may occasionally work on legacy projects using outdated configuration fields (e.g., `tools`, `maxSteps`). You MUST correct these to the modern `permission` and `steps` fields when encountered.

### Custom Instructions

Include additional instruction files:

```jsonc
{
  "instructions": [
    "CONTRIBUTING.md",
    "docs/guidelines.md",
    ".cursor/rules/*.md"
  ]
}
```

**Full schema reference:** See `references/config-schema.md`

</config_file>

<rules_file>

## Rules (AGENTS.md)

Project instructions for all agents. Similar to CLAUDE.md or Cursor rules.

### Tips

- SHOULD be specific about your project's patterns
- SHOULD include common commands
- SHOULD document any non-obvious conventions
- SHOULD keep it concise (agents have limited context)

</rules_file>

<config_tips>

## Comment Out, Don't Delete

OpenCode supports JSONC (JSON with comments). SHOULD comment out unused configs instead of deleting:

```jsonc
{
  "plugin": [
    "opencode-openai-codex-auth@latest",
    //"@tarquinen/opencode-dcp@latest",     // disabled for now
    //"@howaboua/pickle-thinker@0.4.0",     // only for GLM-4.6
    "@ramtinj95/opencode-tokenscope@latest"
  ]
}
```

**Why:** You might want to re-enable later. Keeps a record of what you've tried.

## Validate After Major Changes

After editing opencode.jsonc, you MUST run this validation (not just suggest it):

```bash
opencode run "test"
```

**Execute it yourself** using the Bash tool before telling the user the change is complete.

If broken, you'll see a clear error with line number:
```
Error: Config file at ~/.config/opencode/opencode.jsonc is not valid JSON(C):
--- Errors ---
CommaExpected at line 464, column 5
   Line 464:     "explore": {
              ^
--- End ---
```

Common JSONC mistakes:
- Missing comma after object (especially after adding new sections)
- Trailing comma before `}`
- Unclosed brackets

</config_tips>

<common_configurations>

## Minimal Safe Config

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "model": "anthropic/claude-sonnet-4-20250514",
  "permission": {
    "edit": "ask",
    "bash": "ask"
  }
}
```

## Power User Config

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "model": "anthropic/claude-sonnet-4-20250514",
  "autoupdate": true,
  "permission": {
    "edit": "allow",
    "bash": {
      "*": "allow",
      "rm -rf *": "deny",
      "sudo *": "ask"
    }
  },
  "instructions": ["CONTRIBUTING.md"]
}
```

## Team Project Config

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "model": "anthropic/claude-sonnet-4-20250514",
  "share": "auto",
  "instructions": [
    "docs/development.md",
    "docs/api-guidelines.md"
  ]
}
```

</common_configurations>

<troubleshooting>

| Issue | Solution |
|-------|----------|
| Config not loading | Check JSON syntax, ensure valid path |
| Skill not found | Verify `SKILL.md` (uppercase), check frontmatter |
| Permission denied unexpectedly | Check global vs project config precedence |
| Permission change not taking effect (wopal-space mode) | Wopal-space skips project `opencode.jsonc`. Check agent frontmatter > `settings.jsonc` > global config > defaults |

</troubleshooting>

## References

- `references/config-schema.md` - Full config options

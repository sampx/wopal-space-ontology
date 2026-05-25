# Ellamaka (opencode) Configuration Schema Reference (Q4 2025)

<instructions>
This document defines the schema and valid values for `opencode.json`. You MUST adhere strictly to these definitions. 
</instructions>

<top_level_options>

```jsonc
{
  "$schema": "https://opencode.ai/config.json",

  // Model Configuration
  "model": "provider/model-id",
  "small_model": "provider/model-id",
  "provider": {},
  "disabled_providers": ["openai", "gemini"],

  // UI & Updates
  "theme": "opencode",
  "autoupdate": true,
  "tui": { "scroll_speed": 3 },
  "keybinds": {},

  // Sharing
  "share": "manual", // "manual" | "auto" | "disabled"

  // Tools & Permissions
  "tools": {},
  "permission": {},

  // Agents & Commands
  "agent": {},
  "command": {},

  // Instructions & MCP
  "instructions": [],
  "mcp": {},

  // Formatters
  "formatter": {},
}
```

</top_level_options>

<model_configuration>

## model / small_model

```jsonc
{
  "model": "anthropic/claude-4-5-sonnet-20250929",
  "small_model": "anthropic/claude-4-5-haiku-20251015",
}
```

Format: `provider/model-id`. Run `opencode models` to list available models.

## provider

Configure custom providers or override settings:

```jsonc
{
  "provider": {
    "anthropic": {
      "models": {},
      "options": {
        "apiKey": "{env:ANTHROPIC_API_KEY}",
      },
    },
  },
}
```

## disabled_providers

Prevent providers from loading even if credentials exist:

```jsonc
{
  "disabled_providers": ["openai", "gemini"],
}
```

</model_configuration>

<tools_configuration>

Enable/disable tools globally:

```jsonc
{
  "tools": {
    "bash": true,
    "edit": true,
    "write": true,
    "read": true,
    "glob": true,
    "grep": true,
    "list": true,
    "patch": true,
    "webfetch": true,
    "todowrite": true,
    "todoread": true,
    "skill": true,
  },
}
```

Wildcards supported for MCP tools:

```jsonc
{
  "tools": {
    "mymcp_*": false,
  },
}
```

</tools_configuration>

<permissions>

## Simple Permissions

```jsonc
{
  "permission": {
    "edit": "allow", // "allow" | "ask" | "deny"
    "webfetch": "ask",
  },
}
```

## Pattern-Based Bash Permissions

```jsonc
{
  "permission": {
    "bash": {
      "*": "allow", // Default for all
      "rm *": "ask", // Ask before delete
      "rm -rf *": "deny", // Block recursive delete
      "sudo *": "deny", // Block sudo
      "git push": "ask", // Ask before push
      "npm run *": "allow", // Allow npm scripts
    },
  },
}
```

## Skill Permissions

```jsonc
{
  "permission": {
    "skill": {
      "*": "allow",
      "dangerous-*": "deny",
      "experimental-*": "ask",
    },
  },
}
```

</permissions>

<agent_configuration>

Define agents in config:

```jsonc
{
  "agent": {
    "my-agent": {
      "description": "What triggers this agent",
      "mode": "subagent",
      "model": "anthropic/claude-4-5-sonnet-20250929",
      "prompt": "System prompt or {file:./prompt.txt}",
      "temperature": 0.3,
      "maxSteps": 25,
      "disable": false,
      "tools": {
        "bash": false,
      },
      "permission": {
        "edit": "ask",
      },
    },
  },
}
```

</agent_configuration>

<commands>

Custom slash commands:

```jsonc
{
  "command": {
    "test": {
      "template": "Run tests and show failures. $ARGUMENTS",
      "description": "Run test suite",
      "agent": "build",
      "model": "anthropic/claude-4-5-sonnet-20250929",
    },
  },
}
```

### Command Template Placeholders

Templates support dynamic input via placeholders:

```jsonc
{
  "command": {
    "review": {
      "template": "Review commit $1. Focus on: $2",
      "description": "Review a specific commit",
    },
  },
}
```

| Placeholder | Behavior |
|-------------|----------|
| `$ARGUMENTS` | Raw string after command name, no splitting, quotes preserved |
| `$1`, `$2`...`$N` | Positional token (space-split, quoted strings treated as one token, quotes stripped) |
| `$N` (highest) | "Rest" semantics — all remaining tokens from position N onward, joined by space |
| No placeholder used | Arguments auto-appended to template end with two newlines |

Example with `/review abc123 security performance`:

- `$ARGUMENTS` → `abc123 security performance` (raw)
- `$1` → `abc123`
- `$2` → `security performance` (rest semantics: highest placeholder gets everything after)

Example with quoted input `/test "hello world" --verbose`:

- `$ARGUMENTS` → `"hello world" --verbose` (raw, quotes preserved)
- `$1` → `hello world` (quotes stripped)
- `$2` → `--verbose`

Replacement order: positional (`$1`..`$N`) first, then `$ARGUMENTS`, then auto-append fallback.

Note: `$@` is NOT supported.

</commands>

<instructions>

Include additional instruction files:

```jsonc
{
  "instructions": [
    "CONTRIBUTING.md",
    "docs/guidelines.md",
    ".cursor/rules/*.md",
    "packages/*/AGENTS.md",
  ],
}
```

Supports glob patterns.

</instructions>

<formatters>

Configure code formatters:

```jsonc
{
  "formatter": {
    "prettier": {
      "disabled": true,
    },
    "custom": {
      "command": ["npx", "prettier", "--write", "$FILE"],
      "environment": { "NODE_ENV": "development" },
      "extensions": [".js", ".ts", ".jsx", ".tsx"],
    },
  },
}
```

</formatters>

<mcp_servers>

Configure Model Context Protocol servers:

```jsonc
{
  "mcp": {
    "my-server": {
      "type": "local",
      "command": ["npx", "-y", "@org/package"],
      "environment": { "KEY": "VALUE" },
    },
    "remote-name": {
      "type": "remote",
      "url": "https://api.example.com/mcp",
      "headers": { "Authorization": "Bearer ..." },
    },
  },
}
```

</mcp_servers>

<model_variants>

## Model Variants (ctrl+t)

Variants allow you to define multiple parameter sets for a single model, cycleable via `ctrl+t`.

```jsonc
{
  "provider": {
    "openai": {
      "models": {
        "gpt-5.2": {
          "variants": {
            "high": {
              "reasoningEffort": "high",
              "reasoningSummary": "detailed",
            },
            "low": {
              "reasoningEffort": "low",
              "textVerbosity": "low",
            },
          },
        },
      },
    },
  },
}
```

### Functional Variant Properties

| Property           | Provider          | Values                                      |
| ------------------ | ----------------- | ------------------------------------------- | ------- |
| `reasoningEffort`  | OpenAI/Azure      | `minimal`, `low`, `medium`, `high`, `xhigh` |
| `reasoningSummary` | OpenAI/Azure      | `auto`, `detailed`                          |
| `textVerbosity`    | OpenAI Compatible | `low`, `medium`, `high`                     |
| `thinking`         | Anthropic         | `{ type: "enabled", budgetTokens: number }` |
| `thinkingLevel`    | Google            | `"low"                                      | "high"` |
| `include`          | OpenAI/Azure      | `["reasoning.encrypted_content"]`           |

</model_variants>

<variable_substitution>

## Environment Variables

```jsonc
{
  "model": "{env:OPENCODE_MODEL}",
  "provider": {
    "openai": {
      "options": {
        "apiKey": "{env:OPENAI_API_KEY}",
      },
    },
  },
}
```

## File Contents

```jsonc
{
  "agent": {
    "custom": {
      "prompt": "{file:./prompts/custom.txt}",
    },
  },
  "provider": {
    "anthropic": {
      "options": {
        "apiKey": "{file:~/.secrets/anthropic-key}",
      },
    },
  },
}
```

</variable_substitution>

<misc_options>

## TUI Options

```jsonc
{
  "tui": {
    "scroll_speed": 3,
  },
}
```

## Sharing Options

```jsonc
{
  "share": "manual", // "manual" | "auto" | "disabled"
}
```

- `manual` - Share via `/share` command (default)
- `auto` - Auto-share new conversations
- `disabled` - No sharing

</misc_options>

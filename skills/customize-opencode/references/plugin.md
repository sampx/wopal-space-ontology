# Plugins

`plugin:` is a list of plugins to load at startup. Each entry is either a
string or a `[name, options]` tuple:

```json
"plugin": [
  "opencode-gemini-auth",
  "opencode-foo@1.2.3",
  "./local-plugin.ts",
  ["opencode-bar", { "option": "value" }]
]
```

- `"opencode-gemini-auth"` — a bare npm package name; opencode resolves and loads the latest version.
- `"opencode-foo@1.2.3"` — an npm package with a pinned version.
- `"./local-plugin.ts"` — a local TypeScript file path, relative to the declaring config.
- `["opencode-bar", { "option": "value" }]` — a package plus a JSON options object; opencode passes the options to the plugin's factory.

A plugin module exports `default` (or any named export) of type `Plugin = (input: PluginInput, options?) => Promise<Hooks>`. The export is a function, not a plain object literal, and the function returns an object (return `{}` if there is nothing to register).

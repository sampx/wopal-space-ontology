---
name: cordis-plugin-development
description: Use when designing, reviewing, adding, enabling, disabling, installing, configuring, or debugging a plugin, bundle, feature, page, panel, tool, or MCP connection in the current Harness profile, including a shipped plugin that is disabled by default, and for any visual object, decoration, or widget request that names no other destination, which means an installed UI plugin rendered in the Harness Web UI.
---

# Persistent Harness plugins

For implementation, use ordinary workspace files to author a bundle, then `plugin_manager` with `action: install_bundle` and `file:<absolute package directory>` as `target` (or `ellamaka dsh plugin --profile web add <absolute package directory>` in Ellamaka) to install it in the current profile. Changes affect every session in that profile and survive restart. Load `editing-cordis-compositions` for agent preset changes.

Do not write the profile's `package.json` or `cordis.patch.yml`, create packages under `$DSH_HOME`, or run pnpm in the profile directory: `install_bundle` performs those steps, and each hand-made write outside the workspace needs its own approval. Every `plugin_manager` action, including `list_plugins` and `list_bundles`, also needs approval without Full access, so call it only when its result decides the next step.

## Ellamaka 与 DSH 集成部署及升级排错

- **部署与安装（强制 `file:` 复制，禁止 `link:` 软链）**：
  - **Ellamaka 内置版**：`$DSH_HOME` 为 `$WOPAL_HOME/dsh/home`，用户配置在 `profiles/web/cordis.patch.yml`，官方依赖在 `closures/<fingerprint>/`（只读）。安装执行 `DSH_HOME=~/.wopal/dsh/home ellamaka dsh plugin --profile web add <bundle 绝对目录>`，它会自动把本地目录转为 `file:<绝对路径>` 交给官方 pnpm 安装器打包复制。
  - **官方桌面版**：使用 `plugin_manager` 的 `install_bundle` 时，`target` 必须传 **`file:<bundle 绝对目录>`**（切勿传裸绝对路径，否则 pnpm 会建 `link:` 软链导致源文件改动直接穿透或依赖解析异常；已安装旧版时先 `remove_bundle` 再 `install_bundle`）。
  - 插件的 `@deepseek-ai/*` 依赖必须写在 `peerDependencies`（同时与 `engines.dsh` 保持一致的版本范围），由 dsh loader 从安装作用域解析；写进 `dependencies` 会在 profile 里装出第二份模块实例。
- **升级后插件/Preset 断裂排查路径**：
  1. **看精确错误**：UI「设置 → Agent Preset」悬停 `加载失败` 徽章读取 `<entry id> (<plugin name>): <原因>`（如 `never started` 代表模块/子路径导出在当前版本不存在、import 失败；`is no longer supported` 代表 `Config` 字段废弃），或通过 `plugin_manager` `list_plugins` 检查。
  2. **查官方破坏性变更声明（Upgrade Guides）**：在 DSH 源码参考仓 `labs/ref-repos/deepseek-harness/docs/upgrade-guide/v<版本>/<主题>/guide.{md,zh.md}` 检索涉及的包名或字段，按其中的 `## Change` 与 `## Migration` 修复；同时对照同版本 `packages/bundle/web-app/presets/cordis.patch.yml` 与 `packages/bundle/base/cordis.patch.yml` 的官方写法。
  3. **核对运行时真实导出与 Schema**：用 `cordis_inspect_query` 的 `Config.listConfigs` 查插件的 `packageDir` 与 JSON Schema，读 `<packageDir>/package.json` 的 `exports` 与 `<packageDir>/README.md` 确认当前版本入口。修复后用 `file:<绝对路径>` 重装并重启验证。

## Design or review

Read the applicable references below and inspect the proposed or existing plugin against current APIs. Report design choices or findings instead of following the installation workflow. Do not write files, install bundles, or change profile state unless the user requests implementation.

## Enable a shipped plugin

A shipped bundle can resolve a plugin row and leave it `disabled`. The row id and its reason are in the shipped patch, `packages/bundle/*/cordis.patch.yml` in a source checkout. Write a workspace bundle whose patch overrides that row with `disabled: false` and inserts the Host rows it depends on; a source checkout's `apps/cli/config/examples/<feature>/cordis.yml` lists them for opt-in features. Packages shipped with dsh resolve from the dsh installation, so the bundle declares no dependencies on them. Install it with `install_bundle`.

## Deliver a working plugin first

1. Resolve the requested result and destination. An unspecified visual destination is the current Harness Web UI; a standalone image or HTML file does not complete such a request. Choose reasonable visual details and implement a small first version; install it before visual refinement.
2. Discover only the APIs needed for that version: `cordis_inspect_list`, then targeted `cordis_inspect_query` calls. For UI, query Client `Slots.listSubTree` and the selected slot's registration options and props. For anything beyond a static decoration, such as tool policy, agent context, session-derived state, or Chat rows, read `references/practices.md` before choosing the extension point; for a user action in plugin UI, also read `references/user-actions.md`. Once the chosen slot and registration API are known, write the plugin.
3. Read and copy the matching template files into one workspace directory, or author the package, patch, and required Host/Client files there. Before installing, complete the display checklist in `references/host-plugin.md`: meaningful localized titles/descriptions, an original or licensed icon, and exported resources with distribution checks where applicable. This applies to Host-only and configuration-only bundles too; adapt template text and artwork to the request. Check JavaScript syntax and the manifest, then install. Use the installed plugin as the first preview; do not create preview HTML, mock shells, design variants, screenshot scripts, or rasterizer tooling first.
4. Read the installation result: `application` and `warnings` decide whether the change is live, not logs, process lists, or the page's boot payload. Confirm new rows with approval-free `cordis_inspect_query`, not `list_plugins`. After `application: applied`, exercise the capability or inspect the live Client registration. Verify installed display metadata and the icon using `references/host-plugin.md`. Use the connected page when available; follow `references/verification.md` for page/panel design checks and unavailable browser control, and `references/user-actions.md` for user actions. Restore user state changed during testing. Report verification limits; installation and slot registration alone do not establish what the user sees.
5. Fix observed defects in the same plugin. When the requested result works, finish with its location, verification status, and the reason for any display-resource exception; never silently accept default artwork. Do not continue speculative variants, optional features, or mock previews. Close any task list.

## Knowledge sources, in order

1. Inspection: `cordis_inspect_query` answers exact Service methods and Event modes (`Service`, `Event`), a mounted plugin's Config JSON Schema (`Config.listConfigs`: filter the paged directory by `name`, then query the `entry` id), the Tools this Agent can call (`Tool`), and live Client Slots and theme tokens (`Slots`, `Theme`).
2. Package documentation: `Config.listConfigs` with `name` set to the package finds its entries; querying one `entry` returns its `packageDir`, the resolved package directory. Read `<packageDir>/README.md`. Bundled packages resolve from the dsh installation and profile-installed bundles from the profile, so never guess the path from `$DSH_PROFILE_DIR`.
3. Source: installed packages ship built `lib/index.js` and `lib/types/**/*.d.ts` with JSDoc under that same `packageDir`, not `src/`; a source checkout of DSH has `packages/<group>/<name>/src` and `docs/upgrade-guide/` for breaking changes across releases. Read them when inspection and the README leave a question open, and start source-level diagnosis from a concrete installation or runtime failure.

`DSH_PROFILE` (profile name) and `DSH_PROFILE_DIR` (its directory, whose `node_modules` holds only profile-installed bundles) are set in every shell call of a profile-launched Harness and absent when the Harness was booted without a profile. Bash reads them as `$DSH_PROFILE`; PowerShell, which the Windows preset uses, reads them as `$env:DSH_PROFILE`. With `dsh` on the PATH, `dsh --profile "$DSH_PROFILE" --dump-config` prints the composed profile.

## Read next

The files below live in this skill's base directory, which the `skill` tool reported, and the table is the complete list: do not enumerate that directory. In every deployment, including a source checkout, read these files with the file-read tool, write copies into the workspace with the file-write tool, and verify a copy by reading it back. In Desktop the directory sits inside `app.asar`, which only the Host process's own file reads can open; shell commands (`ls`, `cat`, `cp`, `cmp`), the glob and search tools (they run a native ripgrep process), `node`, and pnpm all fail on it. Never install or syntax-check a template in place; copy its contents into the workspace first.

| Task | File |
|---|---|
| Bundle manifest, locale resources, icons, installation, Host exports and Config | `references/host-plugin.md` |
| Web UI: Client manifest, module loader, slot registration | `references/ui-plugin.md` |
| Connecting an MCP server through a configuration-only bundle | `references/mcp-bundle.md` |
| Page/panel design checks and verification without browser control | `references/verification.md` |
| UI plugin template, including display resources | `templates/decoration/package.json`, `templates/decoration/cordis.patch.yml`, `templates/decoration/index.js`, `templates/decoration/client.js`, `templates/decoration/locale`, `templates/decoration/icon.svg` |
| MCP bundle template, including display resources | `templates/mcp/package.json`, `templates/mcp/cordis.patch.yml`, `templates/mcp/locale`, `templates/mcp/icon.svg` |
| Loader patch dialect and the list of installable plugin packages | the `cordis-composition-reference` skill |
| Choosing extension points, contexts, and state mechanisms for upgrade stability and performance | `references/practices.md` |
| Sharing application operations between UI actions and agent tools | `references/user-actions.md` |

---
name: editing-cordis-compositions
description: Use when creating, changing, or validating an agent preset or other Cordis composition for this harness, including deciding host versus preset placement and checking that an authored preset mounts.
---

# Editing Cordis compositions

Agent presets are ordinary `@deepseek-ai/dsh-agent-preset` declarations carried by bundle patches. Nothing edits a declaration in place: a preset is created or changed by installing a bundle whose patch declares or overrides it. This file states the declaration format; when it leaves a question open, read the `@deepseek-ai/dsh-agent-preset` README and `lib/types` declarations under the `packageDir` that `cordis_inspect_query` `Config.listConfigs` returns when queried with a `preset-<id>` row's `entry` id, or `packages/preset/agent-preset/src` in a source checkout.

## Ellamaka 与 DSH 集成部署

- **单一真相源**：WopalSpace 的三个 preset（`wopal`、`fae`、`rook`）由 `<ontology>/dsh/agents-presets`（`@wopal/dsh-presets`）中的 `<role>/preset.patch.yml` 手工直接维护；`package.json` 的 `dsh.bundle.patch` 按顺序声明 `["fae/preset.patch.yml", "rook/preset.patch.yml", "wopal/preset.patch.yml"]`（被引用的 `fae`/`rook` 必须排在 `wopal` 之前，否则 `agentPreset` 声明期校验会报 `Unknown agent preset`）。
- **版本兼容声明**：`package.json` 同时维护相同范围的 `engines.dsh` 与 `peerDependencies["@deepseek-ai/dsh"]`（当前要求 `>=0.2.2-rc.1`）。插件的 `@deepseek-ai/*` 依赖一律写在 `peerDependencies`，切勿写进 `dependencies`。
- **安装一律用 `file:`（打包复制），禁止 `link:` 软链**：
  - **Ellamaka 内置版**（`$DSH_HOME` 为 `$WOPAL_HOME/dsh/home`，用户配置在 `profiles/web/cordis.patch.yml`，官方依赖在 `closures/<fingerprint>/`）：执行 `DSH_HOME=~/.wopal/dsh/home ellamaka dsh plugin --profile web add <bundle 绝对目录>`（命令会自动把本地路径规范化为 `file:<绝对路径>` 交给官方 pnpm 安装器复制落盘）。
  - **官方桌面版**（`~/.dsh/profiles/desktop`，由 Electron 独占）：使用 `plugin_manager` 工具时必须传 `target: "file:<bundle 绝对目录>"`（若已安装需先 `remove_bundle` 再 `install_bundle`）；或在应用「设置 → 插件」中输入 `file:<bundle 绝对目录>`。**严禁传不带 `file:` 前缀的裸目录路径**，否则 pnpm 会建成 `link:` 软链。
- **生效机制**：`file:` 安装是独立打包快照（受 `package.json` 的 `files` 字段控制）；修改源目录后**必须重新安装并重启应用**，在新会话中验证（既有会话保留启动时绑定的 preset revision）。项目技能由宿主自动扫描 `<projectRoot>/.dsh/skills`（rank 100），包内 4 个 Cordis 创作技能仅在 `wopal` 中通过锚定 `baseUrl` 的 `customSkillDirs` 挂载，切勿写死机器绝对路径。

## 升级后 Preset / 插件损坏排查与修复（破坏性变更定位）

DSH 在 0.x 阶段升级频繁且包含破坏性变更（插件合拆、子路径导出移除、`Config` 字段改名或废弃）。只要 preset 内任意一行插件挂载失败，整张 preset 卡片就会标为 `加载失败`。按以下固定顺序定位并修复：

1. **先拿精确报错行（`row.broken`）**：
   - 在应用 UI「设置 → Agent Preset」悬停 `加载失败` 徽章，读取 `<entry id> (<plugin name>): <原因>` 原文；或用 `plugin_manager`（`list_plugins` / `list_bundles`）及 `cordis_inspect_query` `Config.listConfigs` 查看异常条目。
   - 典型报错含义：
     - `<id> (<name>): never started`：Loader 在 `import(<name>)` 阶段失败（包名改名、或子路径导出如 `/list-agents` 已从该包 `package.json` 的 `exports` 移除），导致未创建 fiber。
     - `<id> (<name>): ... is no longer supported` 或 Schema 校验报错：插件 `Config` 契约发生破坏性变更（如 `dsh-tool-subagent` 废除内联 `persona`/`toolFilter` 改用 `agentPreset`，或 `modelSelectionSettings` 改名为 `modelSelection`）。
     - `Unknown agent preset <id>`：`agentPreset` 引用的角色尚未注册（检查 `dsh.bundle.patch` 数组顺序或被引用 preset 本身是否损坏）。
     - `Duplicate agent preset`：同一 profile 内 bundle 与 `cordis.patch.yml` 重复声明了同 `id` 的 preset。
2. **去哪里查官方破坏性声明与升级指南（Upgrade Guides）**：
   - **官方升级指南目录**：在 DSH 源码参考仓（如空间内的 `labs/ref-repos/deepseek-harness/docs/upgrade-guide/`，按 `v<semver>/<kebab-case-topic>/guide.md` 与 `guide.zh.md` 归档）检索报错涉及的包名、子路径或配置字段。每篇指南均包含 `## Change`（破坏性变更内容）和 `## Migration`（迁移步骤）。
   - **对照官方内置 Preset 最新写法**：直接读取同版本官方内置 preset 作为权威对照模板——源码仓看 `packages/bundle/web-app/presets/cordis.patch.yml`（及 `standard.patch.yml`）和 `packages/bundle/base/cordis.patch.yml`；已安装运行时则通过 `cordis_inspect_query` `Config.listConfigs` 查询 `preset-cordis` / `preset-standard` 拿到 `packageDir`，或读取目标插件 `<packageDir>/package.json`（核对 `exports`）与 `<packageDir>/README.md`、`lib/index.js`。
   - **查询运行时实时 Schema**：用 `cordis_inspect_query` 的 `Config.listConfigs`（按 `name` 过滤再查 `entry`）获取当前运行版本的精确 JSON Schema，确认合法字段名。
3. **修复与重装验证**：
   - 按官方迁移指南与内置 `cordis.patch.yml` 同步修改 `<role>/preset.patch.yml`（删除已合并/废弃的子路径插件行、更新 `config` 键名），并同步提升 `package.json` 的 `version` 与 `engines.dsh` / `peerDependencies`。
   - 通过 `file:<bundle 绝对目录>` 重新安装（先 `remove_bundle` 再 `install_bundle`，或跑 `ellamaka dsh plugin --profile web add`），重启后在「设置 → Agent Preset」及新会话中确认徽章恢复正常。

## Where declarations live

The shipped Web presets are `presets/<id>.patch.yml` files of the `@deepseek-ai/dsh-web-app` bundle, ids `standard`, `ptc`, `minimal` and `cordis`. Installed, the bundle resolves from the dsh installation, not the profile; querying `Config.listConfigs` with the `entry` id of any `preset-<id>` row it declares returns that `packageDir`. In a source checkout of DSH it is `packages/bundle/web-app/`. Read one file with the file-read tool when you need a template; `minimal.patch.yml` is the shortest. In Desktop the bundle sits inside `app.asar`, which shell commands cannot open. Load `cordis-composition-reference` for the patch dialect and the list of plugin packages a preset can mount.

A declaration row has these `config` fields: `id` (required, lowercase letters, digits and hyphens), `plugins` (required Cordis entry list), and optional `name`, `description` and `order` (roster position). The Loader row `id` is `preset-<id>` by convention.

## Create a preset

Write a bundle directory in the workspace with exactly two files, then install it.

`review-preset/package.json`:

```json
{
  "name": "@local/dsh-review-preset",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "dsh": { "bundle": { "patch": "./cordis.patch.yml" } }
}
```

`review-preset/cordis.patch.yml`:

```yaml
- insert:
    - id: preset-review
      name: '@deepseek-ai/dsh-agent-preset'
      config:
        id: review
        name: Review
        description: Reviews changes with the shell only.
        order: 10
        plugins:
          - id: persona
            name: '@deepseek-ai/dsh-persona'
            config:
              prefix: You review software changes.
          - id: tool-bash
            name: '@deepseek-ai/dsh-tool-bash'
```

Install with `ellamaka dsh plugin --profile web add <absolute bundle directory>` in the Ellamaka deployment (which normalizes the path to `file:<abs>`), or with `plugin_manager` (`action: install_bundle`, `target: "file:<absolute bundle directory>"`) when `plugin_manager` is available. It runs package installation and bundle selection itself; do not reproduce those steps with shell commands, and never hand-edit the profile's `package.json`.

## Change a shipped preset

Override the declaration by its Loader row id instead of inserting. The override replaces the complete `config`, so restate `id`, `plugins` and every other field the shipped file carries:

```yaml
- id: preset-standard
  name: '@deepseek-ai/dsh-agent-preset'
  config:
    id: standard
    order: 1
    plugins:
      # the shipped list with your changes
```

## Migrate a legacy preset

Before declaration rows, a user preset was a directory `$DSH_HOME/.agent-presets/<id>/` holding `preset.yml` (display `name`, `description`, `order`) and `agent.cordis.yml` (the plugin entry list). Nothing reads that directory any more. To migrate one, create a bundle as above whose declaration takes `id` from the directory name, `name`, `description`, and `order` from `preset.yml`, and `plugins` from `agent.cordis.yml` verbatim; check each plugin name against `cordis-composition-reference` because packages renamed since the preset was written fail at activation. Install it and verify the row in a new session.

## Verify

`plugin_manager` `list_bundles` lists the installed bundle; `list_plugins` shows the `preset-<id>` row with its activation state. A declaration whose activation fails stays on the roster with its diagnostic and cannot compose a session until the bundle is fixed and reinstalled. Existing sessions and their children keep the plugin revision they started with; validate changed behavior in a new session. Installing a bundle executes plugin code in the Host process, so it requires Full access or approval.

## Choose plugin placement

Host plugins supply shared services: tools and prompt registries, the Agent loop, sessions, persistence, settings, sandbox policy, model routes, and subagent backends. Preset plugins contribute scoped tools, persona, prompt sections, and policies to those registries. Preset revisions are eagerly activated once and shared by their selecting Agents.

A preset plugin that supplies a service must isolate the provider and all its consumers in the same realm. A service consumed by Host plugins belongs in the Host configuration. Scope controls contributions and event visibility; `isolate` controls service instances. Use ordinary Cordis groups for nested plugin lists. Keep `!!js` expressions only in plugin configuration or `disabled`; the Loader evaluates them when activating the child plugin. Resolve assets from installed packages rather than a preset directory.

## Extend the Host

For new plugin code or profile-wide capabilities, load `cordis-plugin-development`, author a workspace bundle, and install it with `plugin_manager`. Inspect available APIs through `cordis_inspect_list` and `cordis_inspect_query`, including a mounted plugin's Config schema through the Host `Config` provider; those tools do not invoke Remote methods. Verify the installed capability before reporting completion.

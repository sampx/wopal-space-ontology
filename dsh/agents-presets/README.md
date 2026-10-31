# WopalSpace DSH preset bundle

声明 `wopal`、`fae`、`rook` 三个 agent preset。每个角色的 `<role>/preset.patch.yml` **就是唯一真相源，手工直接编辑**。

## 目录

| 路径 | 作用 |
|---|---|
| `package.json` | bundle 清单，`dsh.bundle.patch` 列出三个 patch（官方实现接受字符串或数组） |
| `wopal/preset.patch.yml` | 编排者声明 |
| `wopal/skills/` | 随包分发的 4 个 Cordis 创作技能，**只给 wopal** |
| `fae/preset.patch.yml`、`rook/preset.patch.yml` | 执行者 / 审查者声明 |

新增角色目录时同步 `package.json` 的 `files`：`file:` 安装是打包复制，漏登记会静默缺文件。

## 版本兼容

**本包面向 DSH ≥ 0.2.1-rc.5**，两个版本字段都写同一范围（缺一不可）：

```json
"engines": { "dsh": ">=0.2.1-rc.5" },
"peerDependencies": { "@deepseek-ai/dsh": ">=0.2.1-rc.5" }
```

依据官方 `plugin-compatibility` 实现：

- 存在 `engines.dsh` 时它**单独决定**兼容性，`peerDependencies` 被整体忽略；
- 不存在 `engines.dsh` 时，每个 `@deepseek-ai/dsh*` peer 都必须匹配；
- **DSH 0.2.0-rc.2 不认识 `engines.dsh`**，实测直接忽略它 —— 只写 `engines.dsh` 会让老运行时失去全部校验。

**为什么不能声称兼容 rc.2**：rc.2 的 `dsh-tool-subagent` schema 里没有 `agentPreset` / `allowedAgentPresets`（实测 0 处），且 `Config` 未 `.strict()` —— 未知键被**静默忽略**。把本包装到 rc.2 上不会报错，但 `subagent_fae` / `subagent_rook` 会既没有 `persona` 也没有 `agentPreset`，退化成两个普通 `subagent`：灵魂与工具白名单全丢，且没有任何提示。门槛抬到 rc.5+ 之后，rc.2 会明确 `skipping profile bundle ... incompatible`，rc.5 正常加载 7 个 preset（都实测过）。

两个方向都要记住：

- 内置版仍跑 rc.2 → 继续用它已安装的旧快照（那份是 rc.2 契约，正确），**不要**装本包；
- 内置版闭包升到 rc.5+ → **必须重装本包**：已装的 1.0.0 精确钉 `@deepseek-ai/dsh: 0.2.0-rc.2`，在新运行时会被拒绝，三个 preset 静默消失。

profile 的 `pnpm-workspace.yaml` 需要 `autoInstallPeers: false`，否则 pnpm 会把 `@deepseek-ai/dsh` 当依赖去 registry 拉取（官方 profile 默认已如此）。

## 委派子代理（rc.5 契约，实测踩过）

`@deepseek-ai/dsh-tool-subagent` 在 0.2.1-rc.5 **硬性禁止**内联 `persona` 与 `toolFilter`，入口直接抛错：

> `tool-subagent: <field> is no longer supported; configure persona and tool plugins in an Agent Preset and select it with agentPreset (spawn only)`

子代理的灵魂与工具面只能由一个 Agent Preset 承担，用 `agentPreset` 引用它的 `config.id`：

```yaml
- id: tool-subagent-fae
  name: '@deepseek-ai/dsh-tool-subagent'
  config:
    provider: spawn        # agentPreset 只有 spawn 支持；fork 继承父上下文，配置了会抛 does not support independent agent preset selection
    toolName: subagent_fae
    agentPreset: fae
    allowedAgentPresets:   # 锁死该工具只能起 fae，模型不能换
      - fae
```

rc.5 的 `Config` 只有这些键：`provider`（必填）、`toolName`、`modelSelectionSettings`、`agentOptions`、`agentPreset`、`allowedAgentPresets`、`maxDepth`。**不要再写 rc.2 时代的 `backgroundMode`** —— 已从 schema 移除，留着不报错但完全无效。

声明期校验（`SubagentPresetSelection.validate`）会对 `agentPreset` 与 `allowedAgentPresets` 里每个 id 调 `agentPresets.readDocument(id)`，**未注册即抛 `Unknown agent preset`**。所以被引用的 preset 必须先完成注册：`dsh.bundle.patch` 数组即应用顺序，**fae、rook 必须排在 wopal 之前**。引用官方内置 preset（standard/ptc/minimal/cordis）无此风险，它们属于更早的 bundle 层。

## 校验（替代旧的 `--check`）

手工维护没有生成期检查，改用真实 loader 组一遍：

```sh
TMP=<临时目录>
mkdir -p $TMP/profiles/verify/node_modules/@wopal
ln -s <本目录绝对路径> $TMP/profiles/verify/node_modules/@wopal/dsh-presets
printf '# root\n[]\n' > $TMP/profiles/verify/cordis.yml
# $TMP/profiles/verify/package.json 的 dsh.profile.bundles:
#   ["@deepseek-ai/dsh-base","@deepseek-ai/dsh-web-app","@wopal/dsh-presets"]
DSH_HOME=$TMP dsh --profile verify --dump-config
```

YAML 与结构错误当场报出；`skipping profile bundle` 说明版本门槛没过；`Duplicate agent preset` 说明与别处的同 id 声明撞车。两个运行时各跑一次。

**`--dump-config` 不挂载插件，因此看不见插件 config 层的拒绝**（上面那条 `persona is no longer supported` 就是例子）。权威信号在运行中的应用里：设置 → Agent Preset，`加载失败` 徽章悬停出的 `row.broken` 会逐行点名挂载失败的条目（`<entry id> (<plugin name>): <原因>`）。排错先取这行原文，别靠静态组成推断。

## 安装

**官方桌面版**（`~/.dsh/profiles/desktop`，由 Electron 应用独占）：CLI 走不通 —— `dsh --profile desktop --dump-config` 报 `managed exclusively by the Electron application`，`dsh plugin --profile desktop list` 报锁文件 `EPERM`。用应用内 **设置 → 插件 → 从本地目录安装**，目标填本目录绝对路径；装完 ⌘Q 完全退出再开。

**ellamaka 内置版**（`$WOPAL_HOME/dsh/home`）：

```sh
DSH_HOME=~/.wopal/dsh/home ellamaka dsh plugin --profile web add <本目录绝对路径>
```

该 profile 带 `patchReload: "live"`，只热载 patch 文件；**包版本替换必须重启产品**。

两种安装落盘形态不同，改动生效方式也不同（都实测过）：

| 目标 profile | 安装方式 | 落盘形态 | 改完源后 |
|---|---|---|---|
| 官方桌面版 | 应用内插件管理 / `install_bundle` | **软链** `link:<本目录>` | 重启即生效，无需重装 |
| ellamaka 内置版 | `ellamaka dsh plugin ... add` | **打包复制** | 必须重装 + 重启 |

所以内置版那份是独立快照：源目录改了，它不会跟着变，直到有人重装。两边版本可能长期不一致，排查时先看各自 `node_modules/@wopal/dsh-presets/package.json` 的 `version`。

## 技能与角色边界

技能根由官方 `skill-filesystem` 自行发现，**preset 不写路径**。宿主层已挂一份（`includeDefaultRoots` 默认 true），按固定等级扫描：

| 根 | 来源 | rank |
|---|---|---|
| `<projectRoot>/.dsh/skills` | 空间装配输出；projectRoot = 最近的含 `.git` 目录 | 100 |
| `<projectRoot>/.agents/skills` | 同上 | 200 |
| `customSkillDirs` | 仅当 preset 显式声明 | 300 |
| `$DSH_HOME/skills`、`$AGENTS_HOME/skills` | 用户级 | 400 / 500 |

| preset | 空间技能（project-dsh 根，自动） | 包内 4 个创作技能（customSkillDirs） |
|---|---|---|
| wopal | ✅ | ✅ 声明，锚在 `baseUrl` |
| fae / rook | ✅ | ❌ 整行不声明 |

硬规矩：

- **patch 里不允许出现机器相关绝对路径** —— 写死工作区挂载点，包换机即废。指向包内文件一律用 `baseUrl`（见 wopal 的 `customSkillDirs`，与官方 `cordis` preset 同法）。
- **哪些空间技能可见由装配决定**：`assembly/archetypes/*.yaml` 的 `skills:` 清单 → 装出 `<projectRoot>/.dsh/skills`。preset 不得用绝对路径去补装配的缺漏，那是越权且不可分发。
- 4 个创作技能（`editing-cordis-compositions`、`cordis-plugin-development`、`cordis-composition-reference`、`agent-experience`）是编排者专属，fae/rook 靠"不声明 skill-filesystem 行"来排除。
- `$WOPAL_HOME/skills` 是空目录，不能当锚点（实测）。

曾踩过的坑（留此备忘）：为了让 fae/rook 看到 `.wopal/skills`，早期版本在此写死了工作区绝对路径，导致包不可分发。正确解法是删掉声明、由装配补齐 `.dsh/skills`。

角色边界：fae 禁止提问、规划、委派；rook 的只读边界由 fs 沙箱执行策略承担，不因技能可见而放宽。

`order` 用 11/12/13，避开内置 standard/ptc/minimal/cordis 的 1..4。

## 生效与恢复

新声明在**新会话**生效；已有会话保留绑定的 preset revision，程序不自动重试。同一 profile 内不要同时存在本 bundle 与手抄进 `cordis.patch.yml` 的同 id 声明 —— 注册表会抛 `Duplicate agent preset`，对应卡片被标为加载失败。

升级前保留源目录快照；恢复时匹配旧引擎、旧闭包与旧 home。本 bundle 不清理用户的会话、凭证或附件。

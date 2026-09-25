# enhance-plugin-config-delivery

## Metadata

- **Type**: enhance
- **Project Path**: .wopal
- **Created**: 2026-09-25
- **Stage**: draft
- **Mode**: (accept 时记录：isolated | quick)
- **Worktree**: (accept 时记录)
- **Branch**: (accept 时记录)
- **Base Commit**: (accept 时记录)
- **Final Commit**: (integrate 时记录：集成到空间分支后的提交)

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

本体三插件（dsh-adapter / wopal-plugin / tui-ellamaka）从"各自读 settings 文件"切换为"消费引擎交付的 pluginConfig 表"；装配单 `coding.yaml` 切换为分段映射格式；wopal-plugin 运行时 id 修正为 `wopal-plugin`。

## Technical Context

### Architecture Context

- **现状（自读）**：三个插件都自己读三层 settings 的 `wopal.pluginConfig.<插件名>`：
  - dsh-adapter：`plugins/dsh-adapter/index.ts` 的 `settingsLayerPaths`（`:205`）/ `readPluginConfigLayer`（`:230`）/ `loadPluginConfig`（`:265`），三层 deep merge + zod 校验（`:173`），内联 options 作为 fallback。唯一 fork 扩展是 `PluginInput.wopalSpaceRoot`。
  - wopal-plugin：`plugins/wopal-plugin/src/config/loader.ts` 的 `loadWopalConfig`（`:154`），三层读取 + `$VAR` 解析 + zod 校验，并把 `pluginConfig["wopal-plugin"]` 作为最高优先片段叠加（`:177-179`）。
  - tui-ellamaka：`plugins/tui-ellamaka/config.ts` 的 `resolveTuiConfig`（`:120`），自行定位空间根、三层 merge、内联 mount options fallback。
- **变更动机**：设计定案（`projects/ellamaka/docs/DESIGN-config-engine.md` Plugin Configuration Assembly）——插件不读配置文件，读取收口到引擎；引擎无条件装配 `wopal.pluginConfig` 表并经 `PluginInput.pluginConfig`（server 插件）与 `TuiPluginApi.pluginConfig`（TUI 插件）整表交付，插件按硬编码键自取并校验。引擎侧交付实现由 `ellamaka/enhance-config-delivery` 承担；本提案只做插件侧消费改造 + 装配单格式切换。
- **装配单现状**：`assembly/archetypes/coding.yaml` 的 `plugins` 为纯名字数组（`tui-ellamaka` / `wopal-plugin` / `dsh-adapter` 混列）。分段格式（`ellamaka` / `tui` 段键）由 `wopal-cli/enhance-assembly-sectioned-plugins` 提供解析与两段物化；本提案负责把 `coding.yaml` 切换为新格式并验证物化落段。
- **id 现状**：`plugins/wopal-plugin/src/index.ts:359` 导出 `id: "wopal-wopal-plugin"`——与装配/配置键名 `wopal-plugin` 不一致（file 源插件强制导出 id，`resolvePluginId` 以导出值为运行时 id）。该 id 参与 TUI 插件启用状态键与去重身份，错误名会让身份链与配置键脱节。
- **设计真相源**：`projects/ellamaka/docs/DESIGN-config-engine.md`（Plugin Configuration Assembly）、`.wopal/docs/DESIGN-assembly.md`（装配单分段声明与物化）、`.wopal/docs/DESIGN-dsh-adapter.md`（Configuration 节）、`.wopal/docs/DESIGN-wopal-plugin.md`（Plugin Config Node 节）、`.wopal/docs/DESIGN-capabilities.md`（TUI Brand Plugin 节）。

### Key Decisions

- D-01: 三插件统一消费「引擎交付表」为唯一主通道：`PluginInput.pluginConfig`（dsh-adapter / wopal-plugin）与 `TuiPluginApi.pluginConfig`（tui-ellamaka）。插件删除文件读取链与空间根定位逻辑，只按硬编码键自取条目。
- D-02: 消费优先级 = `内置默认 < 装配条目内联 options < pluginConfig[插件名]`；内联 fallback 保留（兼容未迁移部署），但其来源只是装配条目第二参数，不再触发文件读取。
- D-03: `$VAR` 解析留在插件侧（设计：wopal 段为文件镜像、不代换）；插件对自取切片内的 `$VAR` 做解析（wopal-plugin 现有解析逻辑迁移；dsh-adapter 的 sandbox 配置不含 `$VAR` 场景，按最小实现处理）。
- D-04: 校验（zod fail-loud）留在插件侧不变；交付表缺失该插件条目时按"未配置"语义走默认/内联，不视为错误。
- D-05: `coding.yaml` 直接切换为分段映射（`version: 1` 不变，无兼容层）；切换以 `wopal-cli/enhance-assembly-sectioned-plugins` 已交付为前提。
- D-06: wopal-plugin 导出 id 修正为 `wopal-plugin`（运行时身份与配置键、装配名对齐）。
- D-07: 发布顺序：先引擎交付（`ellamaka/enhance-config-delivery`）与 CLI 分段物化（`wopal-cli/enhance-assembly-sectioned-plugins`）落地，再本提案一次性切换三插件消费与装配单格式（同批发布，避免中间态读不到配置）。

### Key Interfaces

消费面（插件侧，测试锁定）：

```ts
// dsh-adapter / wopal-plugin（server 插件）— PluginInput 既有 fork 字段扩展
input.pluginConfig["dsh-adapter"]      // 未配置 → undefined → 走内联/默认
input.pluginConfig["wopal-plugin"]

// tui-ellamaka（TUI 插件）— TuiPluginApi 新增字段
api.pluginConfig["tui-ellamaka"]       // { enabled?: boolean; label?: string }
```

装配单（`assembly/archetypes/coding.yaml`）：

```yaml
version: 1
plugins:
  ellamaka:
    - wopal-plugin
    - dsh-adapter
  tui:
    - tui-ellamaka
```

## In Scope

- dsh-adapter：删三层自读链，改取 `input.pluginConfig["dsh-adapter"]` + zod 校验 + 内联 fallback；`wopalSpaceRoot` 消费点如仅用于文件定位则同步清理（保留引擎仍注入的契约字段）
- wopal-plugin：loader 改取 `input.pluginConfig["wopal-plugin"]` 切片 + `$VAR` 解析 + zod 校验；旧顶层字段 fallback 语义维持与内联一致的兼容层级
- tui-ellamaka：删 `config.ts` 文件读取链，改取 `api.pluginConfig["tui-ellamaka"]` + 校验 + 内联 fallback
- `assembly/archetypes/coding.yaml` 切换分段格式
- wopal-plugin 导出 id 修正 `wopal-plugin`
- 三插件测试更新；wopal-plugin lint / typecheck 纳入验证

## Out of Scope

- 引擎侧交付实现与 `/config-v2`（`ellamaka/enhance-config-delivery`）
- CLI 装配单解析与两段物化（`wopal-cli/enhance-assembly-sectioned-plugins`）
- 插件读取 `ELLAMAKA_LOG_LEVEL`（另一提案 `enhance-logging-unified-level-consumption`，待交付）
- 设置面板的插件配置编辑 UI（产品侧后续）
- `settings.local.jsonc` 临时内联冗余的删除（引擎 Plan 的 User Validation 前置）

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| dsh-adapter | `plugins/dsh-adapter/index.ts`, `plugins/dsh-adapter/index.test.ts` | 修改 | 消费交付表、删自读链 |
| wopal-plugin | `plugins/wopal-plugin/src/config/loader.ts`, `src/config/schema.ts`, `src/index.ts`, `src/config/*.test.ts`, `src/index.test.ts` | 修改 | 消费交付表、id 修正 |
| tui-ellamaka | `plugins/tui-ellamaka/index.tsx`, `plugins/tui-ellamaka/config.ts`, `plugins/tui-ellamaka/config.test.ts` | 修改/删除 | 消费交付表、删 config.ts |
| 装配单 | `assembly/archetypes/coding.yaml` | 修改 | 分段格式切换 |

## Acceptance Criteria

### Agent Verification

1. [ ] dsh-adapter 消费：注入 `pluginConfig["dsh-adapter"]` 片段 → 生效配置正确（含无 entry 走内联、非法 entry fail loud 报错信息含插件名与字段路径）；源码不再有任何 settings 文件读取调用。
2. [ ] wopal-plugin 消费：注入切片 → 生效配置正确（deep merge、`$VAR` 解析、zod 校验、缺失走默认）；源码不再读 settings 文件；旧顶层字段兼容语义与设计一致。
3. [ ] tui-ellamaka 消费：`api.pluginConfig["tui-ellamaka"]` 的 `enabled`/`label` 生效；非法形状报错；`config.ts` 及其文件读取链删除；内联 fallback 仍生效。
4. [ ] 装配单切换：`coding.yaml` 为新分段格式；在空间上经 CLI 物化后 `settings.local.jsonc` 的 `ellamaka.plugin` 与 `tui.plugin` 分段正确（与 CLI 侧联合验证，物化命令可重跑幂等）。
5. [ ] wopal-plugin id：导出 id 为 `wopal-plugin`；TUI 插件启用状态键与去重身份随之对齐（无 `wopal-wopal-plugin` 残留）。
6. [ ] 回归与质量（cross-Task）：三插件既有测试适配后全绿（dsh-adapter `bun test`、wopal-plugin `bun run test:run`、tui-ellamaka 等效测试入口）；wopal-plugin `bun run lint` / `typecheck` 通过；改动文件格式检查通过。

### User Validation

#### Scenario 1: 插件功能实机回归（重启后）
- Goal: 确认三插件切换消费通道后，实机行为与改造前一致（沙箱、记忆/规则、TUI 品牌）。
- 验证环境: 本空间 + 桌面 workbench + TUI；`settings.local.jsonc` 中临时内联冗余已由引擎 Plan 前置删除。
- Precondition: 引擎 Plan 与 CLI Plan 已交付；本提案已实施并集成；Agent 已完成 AC#1-6 验证。
- 启动命令: 用户自行重启桌面 ellamaka 与 TUI（无 CLI 命令）。
- User Actions:
  1. workbench 中确认沙箱三态选择器显示且默认态正确（dsh-adapter 配置来自 pluginConfig）；
  2. 发起一条普通会话消息，确认规则/记忆插件无报错、TUI 日志无插件配置错误；
  3. 启动 TUI 确认品牌 logo 与 label（tui-ellamaka 配置生效）。
- 通过判据: 选择器默认态 = `workspace-write`；会话正常；TUI 品牌元素正常；`.wopal-space/logs/wopal-logs/` 无配置类 error。
- 失败反馈: 提供最新 `serve-*.log` / `tui-*.log`、`settings.local.jsonc` 全文、插件启动日志片段。

- [ ] 用户已完成上述功能验证并确认结果符合预期

## Implementation

### Task 1: dsh-adapter 消费引擎交付表

**Verification Intent**: AC#1

**Behavior**:
- 注入 `{ "dsh-adapter": { sandbox: { enabled: true, mode: "read-only" } } }` → 生效配置同上
- 无 entry（`{}`）→ 回落内联 options（带内联时）或默认（无内联）
- entry 非法（`sandbox.enabled` 非布尔）→ 抛错，信息含 `dsh-adapter` 与字段路径
- 深层对象 merge 语义（多来源叠加场景）与设计一致
- 源码中 `settingsLayerPaths` / `readPluginConfigLayer` / `loadPluginConfig` 文件读取链删除

**Pre-read**: `plugins/dsh-adapter/index.ts:143-285`（配置链）、`plugins/dsh-adapter/index.test.ts`、`projects/ellamaka/docs/DESIGN-config-engine.md`（Plugin Configuration Assembly）

**Design**:
插件入口从 `input.pluginConfig["dsh-adapter"]` 取切片替代三层自读；校验复用现有 `dshAdapterConfigSchema`；内联 options 继续作为低优先级 fallback（`input.pluginConfig` 条目存在时优先）。三层 deep merge 与来源解析归引擎，插件侧删除对应代码与测试；`$VAR` 场景该插件不含，遇字符串值按设计不做代换（保持镜像语义）。`wopalSpaceRoot` 若仅服务文件定位则不再消费（引擎字段保留）。

**TDD**: true

**Changes**:
1. RED：交付表消费矩阵（有/无 entry、非法、merge）落成失败测试，确认失败
2. GREEN：实现切片消费与自读链删除，至测试全绿
3. REFACTOR：清理不再使用的路径/JSONC 依赖（如 `jsonc-parser` 不再需要）

**Verify**: `cd .wopal/plugins/dsh-adapter && bun test` 全绿

**Done**:
任务产出：dsh-adapter 消费引擎交付表
实际触碰文件：
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

### Task 2: wopal-plugin 消费引擎交付表

**Verification Intent**: AC#2

**Behavior**:
- 注入 `{ "wopal-plugin": { memory: {...}, rules: {...} } }` → 生效配置正确、zod 校验、`$VAR` 解析正常
- 无 entry → 复用默认 + 旧顶层字段兼容层级
- 非法值 → fail loud（保留现有错误格式）
- loader 不再读任何 settings 文件；`$VAR` 解析与 env allowlist 语义不变
- 来源标注（sources）改为交付表自身携带或按表来源语义降级——以设计为准（引擎不做切片来源，插件侧 sources 语义按设计裁剪）

**Pre-read**: `plugins/wopal-plugin/src/config/loader.ts`、`src/config/merge.ts`、`src/config/schema.ts`、`src/config/loader.test.ts`、`.wopal/docs/DESIGN-wopal-plugin.md`（Plugin Config Node）

**Design**:
`loadWopalConfig` 的三层文件读取替换为对注入切片的处理：切片作为最高优先片段（与现状 `pluginConfig["wopal-plugin"]` 叠加语义一致），`$VAR` 解析与 zod 校验逻辑原样复用；`ConfigError` 的错误定位信息（原文件路径）改为插件名与来源标记。`pluginConfig` 全表仍由入口 `index.ts` 从 `pluginInput.pluginConfig["wopal-plugin"]` 传入。旧顶层字段（`rules.enabled` 等）兼容层级保持既有顺序。日志输出的 `sources` 字段如依赖文件层标注，按引擎交付语义调整（无文件层时标注为 `engine` 或按设计省略——以 `DESIGN-wopal-plugin.md` 更新为准）。

**TDD**: true

**Changes**:
1. RED：切片消费矩阵（有/无、非法、$VAR、旧字段兼容）落成失败测试，确认失败
2. GREEN：实现切片消费与文件读取链删除，至测试全绿
3. REFACTOR：收敛 loader 入口签名（去掉路径层定义）

**Verify**: `cd .wopal/plugins/wopal-plugin && bun run test:run && bun run lint && bun run typecheck` 全绿

**Done**:
任务产出：wopal-plugin 消费引擎交付表
实际触碰文件：
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

### Task 3: tui-ellamaka 消费 TuiPluginApi 交付表

**Verification Intent**: AC#3

**Behavior**:
- `api.pluginConfig["tui-ellamaka"]` = `{ enabled: true, label: "X" }` → 品牌 label 为 X、插件启用
- `enabled: false` → 不注册（等同现状）
- 无 entry → 默认（enabled 缺省 true）+ 内联 options fallback
- entry 非对象 → fail loud（保留现状错误语义）
- `config.ts` 文件读取链删除（`findSpaceRoot` / `readWopalNode` / 三层 merge 不再存在）

**Pre-read**: `plugins/tui-ellamaka/index.tsx`、`plugins/tui-ellamaka/config.ts`、`plugins/tui-ellamaka/config.test.ts`、`projects/ellamaka/docs/DESIGN-config-engine.md`（TUI 交付段）

**Design**:
`index.tsx` 的 `tui(api, options)` 改用 `api.pluginConfig?.["tui-ellamaka"]` 取条目（类型来自 `@wopal/ellamaka-plugin/tui` 的 `TuiPluginApi`）；校验保留最小 zod/形状检查；内联 `options` 继续 fallback（`pluginConfig` 优先）。`config.ts` 整体删除（含其测试），`WOPAL_HOME` 定位逻辑不再需要。插件仍只依赖引擎交付，不做任何文件读取。

**TDD**: true

**Changes**:
1. RED：api 交付消费矩阵（有/无 entry、enabled、非法、fallback）落成失败测试，确认失败
2. GREEN：实现 api 消费、删除 config.ts 与相关引用，至测试全绿
3. REFACTOR：清理 import 与注释（ONT-G4 注释更新为新通道）

**Verify**: `cd .wopal/plugins/tui-ellamaka && bun test` 全绿（若项目无测试入口，退化为类型检查 + 引擎侧集成测试命令，以实际为准）

**Done**:
任务产出：tui-ellamaka 消费 TuiPluginApi 交付表
实际触碰文件：
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

### Task 4: 装配单切换与 id 修正

**Verification Intent**: AC#4, AC#5

**Behavior**:
- `coding.yaml` 为新分段格式，其余四类能力声明不变
- 经 CLI 物化后 `settings.local.jsonc` 双段正确、可幂等重跑
- wopal-plugin 导出 id = `wopal-plugin`；无 `wopal-wopal-plugin` 源码残留

**Pre-read**: `assembly/archetypes/coding.yaml`、`plugins/wopal-plugin/src/index.ts:350-361`、`.wopal/docs/DESIGN-assembly.md`（装配单格式）

**Design**:
`coding.yaml` 的 `plugins` 改为分段映射（`ellamaka` / `tui` 段键）；wopal-plugin 导出 id 字符串修正。物化验证依赖 CLI Plan 已交付的解析与物化实现（联合验收在 Delivery Notes 说明）。本 Task 属本体侧切换动作，落地即改变装配行为——与 Task 1-3 同批集成，确保中间态不破坏启动。

**TDD**: false（装配单为声明式数据、id 为字面量修正；验证以物化幂等命令与源码扫描为主）

**Changes**:
1. 装配单 `plugins` 切换为分段映射
2. wopal-plugin 导出 id 修正
3. 验证物化命令幂等（依赖 CLI 侧实现）

**Verify**: `git -C .wopal diff --stat` 显示仅预期文件；`grep -rn "wopal-wopal-plugin" .wopal/plugins/` 无命中；物化命令 `wopal space capability add plugin wopal-plugin --section ellamaka`（或等效）重跑输出 up to date

**Done**:
任务产出：装配单分段格式 + id 修正
实际触碰文件：
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

## Delegation Strategy

| Wave | Task | 执行者 | 依赖 | 委派理由 |
|------|------|--------|------|---------|
| 1 | Task 1, Task 2, Task 3 | fae | 引擎交付 Plan 已交付 | 三插件消费改造相互独立，可分派并行（同 worktree 串行） |
| 2 | Task 4 | fae | Task 1-3 + CLI Plan 已交付 | 装配单切换需消费改造就位，避免中间态 |

## Delivery

`space sync` 与 `ontology contribute` 由用户拍板，技能不自动上行。

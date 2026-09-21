# enhance-plugins-consumer-migration

## Metadata

- **Issue**: #
- **Type**: enhance
- **Target Project**: wopal-space-ontology

- **Project Path**: .wopal

- **Created**: 2026-09-19
- **Status**: reviewing
- **Base Commit**: (approve 时自动记录实施基线,集成分支 HEAD)
- **Final Commit**: (verify 时自动记录合入提交,集成分支 HEAD)

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

将 `wopal-plugin` 与 `dsh-adapter` 两个插件从「手抄 fork 扩展类型 + 寄生依赖」迁移为「显式声明 `@wopal/ellamaka-plugin` 依赖」，消除运行时契约与依赖声明的分离异味。

## Technical Context

### Architecture Context

两个插件深度消费 ellamaka fork 插件契约层的扩展（`wopalSpaceRoot`、`chat.params.systemMetadata`、`tool.provider`、`ToolContext.extra`），但依赖声明与真实使用分离：

- `wopal-plugin` 在 `src/types.ts` 手抄了 `SystemPromptMetadata` / `SystemPromptSection` / `SystemPromptSectionKind` 三个类型（与 fork 契约层同构），依赖声明写的是上游 `@opencode-ai/plugin@~1.15.13`，运行时靠 fork 引擎注入扩展字段。
- `dsh-adapter` 连 `package.json` 都没有，直接放 `.wopal/plugins/dsh-adapter/`，import 的 `@opencode-ai/plugin` 裸路径靠寄生 `wopal-plugin` 的依赖安装产物解析。

设计决策已确认：品牌化发布 `@wopal/ellamaka-plugin` / `@wopal/ellamaka-sdk`（见 `projects/ellamaka/docs/DESIGN-distribution.md` 的 npm 包发布机制），插件消费 fork 扩展时显式声明该依赖、删除手抄类型。本 Plan 是消费者侧迁移，依赖品牌化包已发布（ellamaka 侧 Plan `feature-npm-plugin-sdk-publish` 先行或并行）。

**参考资料**：
- `projects/ellamaka/docs/DESIGN-distribution.md` — npm 包发布机制（包身份、版本策略、兜底 pin）
- `.wopal/docs/DESIGN-wopal-plugin.md` — wopal-plugin 的 Plugin SDK Contract 章节
- `.wopal/docs/DESIGN-dsh-adapter.md` — dsh-adapter 的 Plugin SDK Contract 章节

### Key Decisions

- D-01: 两个插件改声明 `@wopal/ellamaka-plugin` 为直接依赖，版本跟随产品主版本（纯 `x.y.z`）
- D-02: `wopal-plugin` 删除 `src/types.ts` 中手抄的 `SystemPromptMetadata` 等三个类型，改从 `@wopal/ellamaka-plugin` 导入
- D-03: `dsh-adapter` 补齐 `package.json`（声明 `@wopal/ellamaka-plugin` 依赖与插件元数据），不再依赖同目录其他插件的依赖安装结果
- D-04: 插件依赖仍由引擎的插件依赖收集机制安装到 `.wopal/` 运行时 node_modules，不改变安装路径
- D-05: `@wopal/ellamaka-plugin` 尚未发布到 npm（发布账号待解锁）期间，验证用 symlink 接线到 ellamaka worktree 的包目录（`.wopal/node_modules/@wopal/ellamaka-plugin` → `<ellamaka-worktree>/packages/plugin`），模拟 npm 安装结果；发布后删除 symlink，由引擎的依赖安装机制按 package.json 声明正常接管
- D-06: 两个插件声明的 `@wopal/ellamaka-plugin` 版本必须一致——引擎的 `collectPluginDeps` 用 Map 聚合所有插件依赖，同名依赖后者覆盖前者；版本不一致会导致安装结果不确定

### Key Interfaces

N/A（插件内部依赖声明调整，不新增对外契约）

## In Scope

- `wopal-plugin` 依赖迁移：package.json 声明 `@wopal/ellamaka-plugin`，删除手抄类型，改 import fork 包
- `dsh-adapter` 补齐 package.json 并声明 `@wopal/ellamaka-plugin` 依赖
- 两个插件的类型引用与 import 语句同步更新
- 相关测试调整（类型导入来源变化）

## Out of Scope

- `@wopal/ellamaka-plugin` / `@wopal/ellamaka-sdk` 的品牌化与发布（归 ellamaka 侧 Plan `feature-npm-plugin-sdk-publish`）
- 引擎侧 `config.ts` 的 pin 逻辑调整（归 ellamaka 侧 Plan）
- 插件行为逻辑变更（仅依赖声明与类型导入调整）
- 运行时依赖安装机制的变更

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| wopal-plugin 依赖 | `.wopal/plugins/wopal-plugin/package.json` | 修改 | 声明 `@wopal/ellamaka-plugin` 依赖 |
| wopal-plugin 类型 | `.wopal/plugins/wopal-plugin/src/types.ts` | 修改 | 删除手抄 SystemPrompt 类型，改 import |
| wopal-plugin 消费点 | `.wopal/plugins/wopal-plugin/src/index.ts`、`src/hooks/system-transform.ts`、`src/tools/*.ts` 等 | 修改 | 类型导入来源切换 |
| dsh-adapter 依赖 | `.wopal/plugins/dsh-adapter/package.json` | 创建 | 补齐包声明与依赖 |
| dsh-adapter 消费点 | `.wopal/plugins/dsh-adapter/index.ts` | 修改 | import 来源切换 |
| 测试 | 两个插件的测试文件 | 修改 | 类型导入来源变化后的断言 |

## Acceptance Criteria

### Agent Verification

1. [ ] `wopal-plugin` 的 package.json 声明 `@wopal/ellamaka-plugin` 依赖（版本随产品主版本），且 `src/types.ts` 不再包含手抄的 `SystemPromptMetadata` / `SystemPromptSection` / `SystemPromptSectionKind` 定义，消费点改从 `@wopal/ellamaka-plugin` 导入
   - 验证命令（实施时回填）
2. [ ] `dsh-adapter` 目录含 package.json，声明 `@wopal/ellamaka-plugin` 依赖与插件元数据（name/id），`index.ts` 的 `@opencode-ai/plugin` import 全部切换为 `@wopal/ellamaka-plugin`
   - 验证命令（实施时回填）
3. [ ] 两个插件在 `@wopal/ellamaka-plugin` 已发布（或本地 link）的前提下编译通过、测试全绿，无手抄类型残留
   - 验证命令（实施时回填）
4. [ ] 依赖安装记录（plugin-deps 机制）将 `dsh-adapter` 纳入管理，不再依赖 wopal-plugin 的依赖安装产物
   - 验证命令（实施时回填）

### User Validation

#### Scenario 1: 插件在真实引擎加载且依赖自洽
- Goal: 用户确认迁移后两个插件在 ellamaka 引擎中正常加载，依赖声明与运行时一致
- 验证环境: 本空间 `.wopal`（wopal-plugin 与 dsh-adapter 的实际运行位置）
- Precondition: `@wopal/ellamaka-plugin` 已发布到 npm（或本地 workspace link）；`.wopal/node_modules` 已安装新依赖
- 启动命令: `cd /Volumes/U500G/coding/wopal-workspace && ellamaka serve`（或重启引擎）
- User Actions:
  1. 重启 ellamaka serve，观察 `serve-*.log` 无 `background dependency install failed`
  2. 打开 workbench，确认两个插件的工具（wopal_task、memory_manage、context_manage 等）可用
- 通过判据: serve 日志无依赖安装失败警告；插件工具正常注册（`Plugin initialized` 日志可见）
- 失败反馈: `$WOPAL_HOME/logs/serve-*.log` 与 `.wopal-space/logs/wopal-plugin.log` 的完整输出

- [ ] 用户已完成上述功能验证并确认结果符合预期

## Implementation

### Task 1: wopal-plugin 依赖迁移与类型去重

**Verification Intent**: AC#1, AC#3

**Behavior**:
- `wopal-plugin` 的 `package.json` dependencies 含 `@wopal/ellamaka-plugin`（版本跟随产品主版本）
- `src/types.ts` 不再定义 `SystemPromptSectionKind` / `SystemPromptSection` / `SystemPromptMetadata`，消费点从 `@wopal/ellamaka-plugin` 导入
- 插件在依赖可解析的前提下测试全绿、无手抄类型残留

**Pre-read**: `.wopal/plugins/wopal-plugin/package.json`、`src/types.ts`、`src/index.ts`、`src/hooks/system-transform.ts`、`src/tools/context-manage.ts`、`src/tools/dump-formatter.ts`

**Design**:
将 `wopal-plugin` 的插件契约类型来源从「本地手抄」切换到「`@wopal/ellamaka-plugin` 包导入」。具体：在 `package.json` dependencies 声明 `@wopal/ellamaka-plugin`；删除 `src/types.ts` 中三个手抄类型定义；所有 `SystemPromptMetadata` 等类型的消费点（index.ts、system-transform.ts、context-manage.ts、dump-formatter.ts、system-prompt-formatter.ts、context-manage-actions.ts）改为从包导入。`PluginInput & { wopalSpaceRoot?: string }` 的断言在包类型已含该字段后简化为直接类型。运行时契约不变（引擎仍注入扩展字段）。依赖未发布期间用 symlink 接线保证测试可跑：`.wopal/node_modules/@wopal/ellamaka-plugin` → ellamaka worktree 的 `packages/plugin`，`.wopal/node_modules/@wopal/ellamaka-sdk` → 同 worktree 的 `packages/sdk/js`（D-05）。接线后依赖解析走 node_modules 向上查找链，与发布后的 npm 安装形态一致。

**TDD**: true

**Changes**:
1. RED：将「types.ts 无手抄类型、消费点从包导入」落成失败测试（如 grep 断言手抄类型定义已移除、import 来源为 `@wopal/ellamaka-plugin`），确认失败
2. GREEN：更新 package.json 依赖、删除手抄类型、切换消费点 import 至测试全绿
3. REFACTOR：清理类型断言的冗余（`as PluginInput & {...}` 简化）

**Verify**:
`cd .wopal/plugins/wopal-plugin && bun run test:run` 全绿（该目录无 workspace 配置，pnpm 不可用，bun 是既有测试运行方式）；`grep -rn "SystemPromptSectionKind" src/types.ts` 无命中

**Done**:
任务产出：wopal-plugin 依赖迁移完成，手抄类型删除，消费点改从 `@wopal/ellamaka-plugin` 导入。
实际触碰文件：<实施后回填>
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤.

### Task 2: dsh-adapter 补齐 package.json 与依赖声明

**Verification Intent**: AC#2, AC#3, AC#4

**Behavior**:
- `.wopal/plugins/dsh-adapter/` 含 `package.json`，声明 `name`（或插件 id）、`@wopal/ellamaka-plugin` 依赖
- `index.ts` 的 `@opencode-ai/plugin` import 全部切换为 `@wopal/ellamaka-plugin`
- 插件的依赖可被引擎的插件依赖收集机制识别（`{plugin,plugins}/*/package.json` glob 命中）
- 测试全绿（index.test.ts）

**Pre-read**: `.wopal/plugins/dsh-adapter/index.ts`、`index.test.ts`、`projects/ellamaka/packages/opencode/src/config/wopal-space.ts`（collectPluginDeps 的 glob 与读取逻辑）

**Design**:
补齐 `dsh-adapter` 的 `package.json`，使引擎的 `collectPluginDeps`（glob `{plugin,plugins}/*/package.json`）能识别其依赖并纳入安装管理。包声明含 `name`、`dependencies`（`@wopal/ellamaka-plugin`，版本与 wopal-plugin 声明一致，见 D-06）、`type: module` 等最小字段。`index.ts` 的 import 从 `@opencode-ai/plugin` 切换为 `@wopal/ellamaka-plugin`。`tool.schema` 的 zod 引擎共享依赖随包导入解析。补 package.json 不改变插件的加载方式（仍由 settings.local.jsonc 的 `../plugins/dsh-adapter` 引用、按 file 插件 import），仅使其依赖进入引擎的依赖收集范围。

**TDD**: true

**Changes**:
1. RED：将「dsh-adapter 有 package.json、import 来源为 `@wopal/ellamaka-plugin`」落成失败测试，确认失败
2. GREEN：创建 package.json、切换 import 至测试全绿
3. REFACTOR：如测试结构需调整

**Verify**:
`cd .wopal/plugins/dsh-adapter && bun test index.test.ts` 全绿（该目录无 package.json 与 workspace 配置，`bun test <file>` 是既有运行方式，基线 49 pass）；`grep -rn "@opencode-ai/plugin" .wopal/plugins/dsh-adapter/index.ts` 无命中

**Done**:
任务产出：dsh-adapter 补齐 package.json，依赖声明独立，import 切换为 `@wopal/ellamaka-plugin`。
实际触碰文件：<实施后回填>
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

## Delegation Strategy

| Wave | Task | 执行者 | 依赖 | 委派理由 |
|------|------|--------|------|---------|
| 1 | Task 1 | fae | 无 | wopal-plugin 依赖迁移，独立行为组 |
| 1 | Task 2 | fae | 无 | dsh-adapter 补齐依赖，与 Task 1 无文件争用 |

Wave 1 两 Task 独立可并行；若实施 Agent 上下文不足以并行，可串行执行。

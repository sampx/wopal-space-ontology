# refactor-plugin-config-consumption

## Metadata

- **Type**: refactor
- **Project Path**: .wopal
- **Created**: 2026-09-27
- **Stage**: draft
- **Mode**: (accept 时记录：isolated | quick)
- **Worktree**: (accept 时记录)
- **Branch**: (accept 时记录)
- **Base Commit**: (accept 时记录)
- **Final Commit**: (integrate 时记录：集成到空间分支后的提交)

## Scope Assessment

- **Complexity**: High
- **Confidence**: Medium

## Goal

三个本体插件全部改由引擎交付的 `pluginConfig` 整表消费配置，不再自己读三层 settings；`wopal-plugin` 运行时 id 修正为 `wopal-plugin`。闭  ONT-G5，装配单格式不参与改动。启动前提为 ellamaka `feature-plugin-config` 已一次性交付，全过程只验证一次。

## Technical Context

### Architecture Context

- 契约：`PluginInput.pluginConfig`（server 插件）与 `TuiPluginApi.pluginConfig`（TUI 插件）由引擎三层合并后整表交付；缺层/缺 `wopal` 段按空对象（`projects/ellamaka/docs/DESIGN-config-engine.md` Plugin Configuration Assembly）。
- 当前各自读文件：`plugins/dsh-adapter/index.ts`、`plugins/wopal-plugin/src/config/loader.ts`、`plugins/tui-ellamaka/config.ts`；`plugins/wopal-plugin/src/index.ts:359` 导出 id 为 `wopal-wopal-plugin`。`assembly/archetypes/coding.yaml` 已是 `ellamaka` / `tui` 分段映射，不在本提案变更。
- 前置与前身：旧提案 `enhance-plugin-config-delivery` 前提（coding.yaml 仍未分段）已过时并被淘汰；其插件侧消费部分由本提案承接，改为仅 ONT-G5。

### Key Decisions

- D-01: 插件消费面统一为引擎整表切片，优先级不变：内置默认 < 装配条目内联 options < `pluginConfig[插件名]`；`$VAR` 解析与 zod/形状校验保留。
- D-02: 仅完成三个插件与 id 对齐；不重印 `coding.yaml` 分段格式（已存在）。
- D-03: 一次交付、验收、归档：全部 AC 通过的本窗口完成；不依赖未来引擎 CD 或任何其他未交付 Plan。

### Key Interfaces

- dsh-adapter / wopal-plugin：`input.pluginConfig["dsh-adapter" | "wopal-plugin"]`；无条目走内联/默认。
- tui-ellamaka：`api.pluginConfig["tui-ellamaka"]`。
- wopal-plugin 导出 id 固定为 `wopal-plugin`。
- 无新增 CLI/HTTP；引擎契约不在此改变。

## In Scope

- 三插件去除 settings 文件读取链与空间根配置定位（保留非配置用途的空间根使用）。
- 切片消费、缺省/非法值处理与既有回归测试。
- `wopal-plugin` 运行时 id 对齐。

## Out of Scope

- ELL-G13 引擎交付实现：ellamaka `feature-plugin-config` 完成传输。
- 武器库、派发与规则装配：`enhance-session-assembly`。
- `coding.yaml` 内容与实体二选装配路径：CLI `refactor-space-assembly-state`。

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| wopal-plugin | `plugins/wopal-plugin/src/config/`, `src/index.ts`, `src/index.test.ts` | 修改 | 消费切片、id 修正 |
| dsh-adapter | `plugins/dsh-adapter/index.ts`, `index.test.ts` | 修改 | 消费切片 |
| tui-ellamaka | `plugins/tui-ellamaka/index.tsx`, `config.ts`, `config.test.ts` | 修改/删除 | 消费切片 |

## Acceptance Criteria

### Agent Verification

1. [ ] 引擎模拟注入 `pluginConfig` 时上表三插件生效配置正确；缺条目走内联/默认；非法值与 `$VAR` 行为与现有规则一致（插件侧仅与应用契约相关）。
2. [ ] 三插件源码不再调用 settings 文件读取；`wopal-plugin` 导出 id 为 `wopal-plugin`，去重键在现有路径可识别。
3. [ ] 本地 `bun run test:run`、适配插件测试与 lint/typecheck 全部通过；引擎尚未交付时的模拟路径稳定。

### User Validation

本提案为机器可断言 + 引擎契约已验证，暂不设用户验证；如引擎 Plan 交付契约变更导致本提案过时，须先修订提案再实施。

## Implementation

### Task 1: 三插件消费统一与 id 对齐

**Verification Intent**: AC#1, AC#2, AC#3

**Behavior**: 三插件注入引擎整表即各自取键；id 修正；旧读取链删除；回归全绿。

**Pre-read**: `plugins/wopal-plugin/src/config/loader.ts`、`plugins/dsh-adapter/index.ts`、`plugins/tui-ellamaka/config.ts`、`projects/ellamaka/docs/DESIGN-config-engine.md`

**Design**: 一次走到位：删除三处读取链、统一入口签名，测试按注入表驱动；无对应引擎代码时不写引擎。

**TDD**: true

**Changes**:
1. RED：三插件的注入表/缺失/非法矩阵测试确认失败。
2. GREEN：消费统一与 id 修正至测试全绿。
3. REFACTOR：删除遗留读取依赖并跑文档/格式门禁。

**Verify**: `cd .wopal/plugins/dsh-adapter && bun test`；`cd .wopal/plugins/wopal-plugin && bun run test:run`；tui 等价入口；`bun run lint` / `bun run typecheck` 全绿。

**Done**:
任务产出：待实施后回填。
实际触碰文件：待实施后回填。
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤

## Delegation Strategy

| Wave | Task | 执行者 | 依赖 | 委派理由 |
|------|------|--------|------|---------|
| 1 | Task 1 | fae | `feature-plugin-config` 已交付 | 单窗口三插件消费一致收口 |

## Delivery

实施留在空间分支；`space sync` / `ontology contribute` 由用户拍板。
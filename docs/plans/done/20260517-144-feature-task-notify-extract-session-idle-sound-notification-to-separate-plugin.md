# 144-feature-task-notify-extract-session-idle-sound-notification-to-separate-plugin

## Metadata

- **Issue**: #144
- **Type**: feature
- **Target Project**: wopal-space-ontology
- **Project Path**: .wopal
- **Project Type**: ontology-worktree
- **Created**: 2026-05-17
- **Status**: done

## Scope Assessment

- **Complexity**: Low
- **Confidence**: High

## Goal

将 session idle 声音通知从 wopal-plugin 中提取为独立插件 `session-notify`，实现解耦。

## Technical Context

### Architecture Context

当前 `task-completion-notify.ts`（19 行）导出 `notifyTaskCompletion`，通过 `afplay Glass.aiff` 播放声音。该函数**当前无任何调用者**（dead code）——`event-router.ts` 的 `session.idle` 处理中仅保留 `notifyParent` 逻辑，声音播放已移除。

### Key Decisions

- D-01: 新插件命名 `session-notify`，单文件 `.wopal/plugins/session-notify.ts`，无独立 package.json / tsconfig，无 symlink
- D-02: 无条件播放——所有 `session.idle` 事件触发声音，不区分主会话 / 子会话（无 TaskManager 可用）
- D-03: 删除 wopal-plugin 中的 `task-completion-notify.ts` 死代码，更新 `AGENTS.md`

## In Scope

- 创建单文件插件 `.wopal/plugins/session-notify.ts`，监听 `session.idle` 播放 Glass 声音
- 删除 wopal-plugin 中的 `task-completion-notify.ts`
- 更新 wopal-plugin `AGENTS.md` 通知行描述

## Out of Scope

- wopal-plugin 内部的 idle 诊断逻辑（保留）
- 其他通知机制（progress、stuck 等）
- 非 macOS 平台的声音方案

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| **新插件** | `.wopal/plugins/session-notify.ts` | 创建 | 单文件插件：event hook + 声音播放 |
| **死代码清理** | `.wopal/wopal-plugin/src/tasks/task-completion-notify.ts` | 删除 | 声音通知已迁移到独立插件 |
| **文档更新** | `.wopal/wopal-plugin/AGENTS.md` | 修改 | 更新通知模块描述 |

## Acceptance Criteria

<!-- agent-verify-guard -->

### Agent Verification

1. [x] `test -f .wopal/plugins/session-notify.ts` → exit 0 — 新插件文件存在
2. [x] `rg 'session\.idle' .wopal/plugins/session-notify.ts` ≥ 1 — 监听 session.idle 事件
3. [x] `rg 'afplay' .wopal/wopal-plugin/src/` 返回 0 — wopal-plugin 不再包含声音播放代码
4. [x] `test ! -f .wopal/wopal-plugin/src/tasks/task-completion-notify.ts` → exit 0 — 死代码已删除
5. [x] `cd .wopal/wopal-plugin && bun run test:run` 全部 pass — 删除死代码后无回归

### User Validation

#### Scenario 1: session idle 声音通知
- Goal: 确认新插件加载后，session idle 时能听到 Glass 声音
- Precondition: 重启 ellamaka
- User Actions:
  1. 等待任意会话进入 idle 状态（如委派 wopal_task 完成后）
  2. 听是否有 Glass 声音
- Expected Result: 听到 Glass 提示音

- [x] 用户已完成上述功能验证并确认结果符合预期

## Implementation

### Task 1: 创建 session-notify 插件

**Verification Intent**: AC#1, AC#2

**Behavior**: `.wopal/plugins/session-notify.ts` 作为独立 EllaMaka 插件加载，监听 `session.idle` 事件，无条件播放 Glass 声音

**Files**: `.wopal/plugins/session-notify.ts`

**Pre-read**: `.wopal/wopal-plugin/src/tasks/task-completion-notify.ts`（待提取的声音逻辑）, `.wopal/wopal-plugin/src/index.ts`（插件入口模式参考）

**Design**:
单文件 EllaMaka 插件，遵循 `export default { id, server }` 结构。`server` 函数返回 `{ event }` hook，在 event hook 中过滤 `session.idle` 事件后调用 `Bun.spawn(["afplay", ...])`。

不 import 任何 wopal-plugin 模块，仅依赖 `@opencode-ai/plugin` 类型。不需要独立 package.json 或 tsconfig——EllaMaka 用 Bun 直接执行 `.ts` 文件。

**TDD**: false

**Changes**:
1. 创建 `.wopal/plugins/session-notify.ts`（约 20 行）

**Verify**:
1. `rg -c 'session\.idle' .wopal/plugins/session-notify.ts` ≥ 1
2. `rg -c 'afplay' .wopal/plugins/session-notify.ts` ≥ 1

**Done**:
任务产出：单文件插件 session-notify.ts 创建完成
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

### Task 2: 清理 wopal-plugin 死代码并更新文档

**Verification Intent**: AC#3, AC#4, AC#5

**Behavior**: `task-completion-notify.ts` 文件不存在，wopal-plugin 所有测试 pass，AGENTS.md 通知行描述已更新

**Files**: `.wopal/wopal-plugin/src/tasks/task-completion-notify.ts`, `.wopal/wopal-plugin/AGENTS.md`

**Pre-read**: `.wopal/wopal-plugin/AGENTS.md` 通知模块描述部分

**Design**:
`task-completion-notify.ts` 当前无任何导入者（dead code）。直接删除。AGENTS.md 中通知行从"完成 marker + 声音"改为仅"完成 marker"。

**TDD**: false

**Changes**:
1. 删除 `.wopal/wopal-plugin/src/tasks/task-completion-notify.ts`
2. 更新 `.wopal/wopal-plugin/AGENTS.md` 第 74 行：`task-notifier.ts`（进度） + `task-completion-notify.ts`（完成 marker + 声音）→ `task-notifier.ts`（进度通知）

**Verify**:
1. `test ! -f .wopal/wopal-plugin/src/tasks/task-completion-notify.ts` → exit 0
2. `cd .wopal/wopal-plugin && bun run test:run` 全部 pass
3. `rg 'task-completion-notify' .wopal/wopal-plugin/AGENTS.md` = 0

**Done**:
任务产出：wopal-plugin 死代码已清理，AGENTS.md 已更新
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

## Delegation Strategy

N/A — 两个 Task 均为 Low complexity，Wopal 直接执行。

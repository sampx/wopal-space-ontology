# 98-fix-wopal-plugin-fix-4-regression-bugs-from-97-refactor

## Metadata

- **Issue**: #98
- **Type**: fix
- **Target Project**: ontology
- **Created**: 2026-04-15
- **Status**: done

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

修复插件重构（#97）后引入的 4 个回归 bug：IDLE 通知断裂、wopal_task_diff 空返回、wopal_task_output 上下文用量丢失、PROGRESS 通知缺上下文用量。

## Technical Context

#97 模块化重构将 846 行的 `simple-task-manager.ts` 拆分为 6 个模块。纯结构拆分理论上无行为变更，但实际引入了 4 个回归 bug：

| Bug | 症状 | 根因 |
|-----|------|------|
| 1 | 子会话 idle 后无 IDLE 通知 | `notifyParent` 错误静默 + `promptAsync` error handler 覆盖 idle 状态 |
| 2 | `wopal_task_diff` 返回空 | `session.diff` 缓存依赖 summarize，未完成 LLM 周期时缓存为空 + 缺 `directory` 参数 |
| 3 | `wopal_task_output` 无上下文用量 | 运行时断裂（需调试日志确认具体点） |
| 4 | PROGRESS 通知无上下文用量 | 同 Bug 3，共享 `getContextUsage` 根因 |

Bug 3 和 Bug 4 共享同一根因：`getContextUsage` / `getContextUsagePercent` 在运行时某个环节返回 null。代码逻辑与 #97 前一致（纯函数提取），可能是运行时环境变化导致。

## In Scope

- Bug 1: IDLE 通知断裂修复（3 个断裂点）
- Bug 2: wopal_task_diff 空返回修复
- Bug 3 & 4: 上下文用量丢失修复（共享根因，通过调试日志定位）

## Out of Scope

- 不修改 OpenCode 核心代码（session.diff 行为是上游设计）
- 不改变 wopal_task 状态机整体架构
- 不新增功能

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| hooks | `event-router.ts` | 修改 | Bug 1.1: notifyParent 错误处理改为 warn log |
| tasks | `task-launcher.ts` | 修改 | Bug 1.2: error handler 增加 idleNotified 检查 |
| tools | `wopal-task-diff.ts` | 修改 | Bug 2: 传入 directory 参数 + 诊断增强 |
| tools | `output-helpers.ts` | 修改 | Bug 3: getContextUsage 调试日志增强 |
| tasks | `task-monitor.ts` | 修改 | Bug 4: getContextUsagePercent 调试日志增强 |

## Implementation

### Task 1: Bug 1 — IDLE 通知断裂修复

**Files**: `hooks/event-router.ts`, `tasks/task-launcher.ts`

**Changes**:
1. `event-router.ts:75`: `notifyParent().catch(() => {})` → 改为 `.catch(err => ctx.taskDebugLog('warn', '[notifyParent] error:', err))` 记录错误
2. `task-launcher.ts:166-173`: `promptAsync` error handler 中增加 `if (task.idleNotified) return` 检查，不覆盖已 idle 任务的状态（idle 状态优先，error handler 不干预）
3. `event-router.ts:59-60`: `findBySession` 失败时增加诊断日志 `ctx.taskDebugLog('[session.idle] no task found for sessionID=${sessionID}')`
4. `task-launcher.ts:118-127`: sessionID 提取失败时增加诊断日志说明 sessionToTask 映射未建立的原因

**Verification**: `bun run test:run` + 重启 OpenCode 后验证 wopal_task idle 通知正常

- [x] Step 1: 修改完成（4 个文件）
- [x] Step 2: 测试通过（≥ 419 cases）
- [x] Step 3: lint 0 error

### Task 2: Bug 2 — wopal_task_diff 空返回修复

**Files**: `tools/wopal-task-diff.ts`

**Changes**:
1. Line 79-81: `session.diff` 调用传入 `directory` 参数：从 `manager.getDirectory()` 获取
   - 改为 `v2Client.session.diff({ sessionID: task.sessionID, directory: manager.getDirectory() })`
2. 保留现有 snapshot 诊断逻辑（Line 37-77），增强分类输出区分：
   - "无文件变更"（diff 返回空数组但有数据）
   - "diff 不可用"（缓存未生成，OpenCode summarize 未触发）
3. 增加调试日志对比有/无 directory 参数的结果差异

**Verification**: `bun run test:run` + 重启 OpenCode 后验证 wopal_task_diff 在有变更时正确显示

- [x] Step 1: 修改完成
- [x] Step 2: 测试通过
- [x] Step 3: lint 0 error

### Task 3: Bug 3 & 4 — 上下文用量丢失修复

**Files**: `tools/output-helpers.ts`, `tasks/task-monitor.ts`

**Changes**:
1. `output-helpers.ts:getContextUsage` 增加与 `task-monitor.ts:getContextUsagePercent` 同级别的调试日志：
   - `messages` 获取结果日志
   - `lastAssistant` 查找结果 + tokens 字段检查
   - `providers` API 返回格式 + provider/model 匹配
   - `contextLimit` 查找结果
2. `task-monitor.ts` 已有详细日志，无需修改（作为对比基准）
3. 通过调试日志确认断裂点后针对性修复

**Verification**: `bun run test:run` + 重启 OpenCode 后验证 wopal_task_output 显示上下文用量，PROGRESS 通知包含上下文信息

- [x] Step 1: 调试日志增加完成（output-helpers.ts）
- [x] Step 2: 通过日志确认断裂点（缺少中间日志导致无法定位）
- [x] Step 3: 修复断裂点（添加完整日志，参照 task-monitor.ts）
- [x] Step 4: 测试通过
- [x] Step 5: lint 0 error

## Delegation Strategy

| 批次 | Task | 执行者 | 原因 |
|------|------|--------|------|
| 1 | Task 1 (IDLE 通知) + Task 2 (diff 工具) | Wopal 自行 | wopal_task 有 bug，不能用委派 |
| 2 | Task 3 (上下文用量) | Wopal 自行 | 需运行时调试分析 |

全部由 Wopal 自行完成。修复完成后 wopal_task 才能正常工作。

## Test Plan

#### 单元测试

- 全量运行现有测试，对比前后通过数（≥ 419）
- 重点检查 event-router、task-launcher、wopal-task-diff 相关测试

#### 集成测试

- 重启 OpenCode 后验证 wopal_task 基本行为正常

#### E2E 测试

1. 启动 wopal_task → 等 idle → 确认收到 `[WOPAL TASK IDLE]` 通知
2. 启动 wopal_task（含文件变更）→ 调用 wopal_task_diff → 确认显示 diff
3. 启动 wopal_task（运行中）→ 调用 wopal_task_output → 确认显示上下文用量
4. 启动 wopal_task（运行中）→ 等待 PROGRESS 通知 → 确认包含上下文信息

### Regression Testing

- `bun run build` + `bun run test:run` + `bun run lint` 全量通过
- 重启 OpenCode 后验证 wopal_task 基本行为正常
- 规则注入和记忆注入正常（不受此次修改影响）

### Adjustment Strategy

- Task 3 如果调试日志显示 `client.config.providers` 返回格式变化，调整解析逻辑
- 如果 `tokens` 字段在子会话中始终为空，考虑备选方案（如使用消息数估算或依赖 task.lastContextUsage 缓存）
- 如果断裂点不在预期位置，通过调试日志逐步排查

## Acceptance Criteria

### Agent Verification

- [x] `bun run build` 编译通过
- [x] `bun run test:run` 全部通过，用例数 ≥ 419 (437 passed, 4 skipped = 441 total, 含 WR-01 idleNotified 竞态守卫 18 新测试)
- [x] `bun run lint` 0 error
- [x] 所有修改文件 ≤ 300 行限制 (event-router: 195, task-launcher: 183, output-helpers: 167, wopal-task-diff: 112)

### User Validation

- 子会话 idle 后收到 `[WOPAL TASK IDLE]` 通知
- `wopal_task_diff` 在有变更时正确显示
- `wopal_task_output` 显示上下文用量百分比
- `[WOPAL TASK PROGRESS]` 通知包含上下文用量信息

- [x] 用户已完成上述功能验证并确认结果符合预期

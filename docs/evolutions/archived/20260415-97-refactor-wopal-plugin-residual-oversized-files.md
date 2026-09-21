# 97-refactor-wopal-plugin-residual-oversized-files

## Metadata

- **Issue**: #97
- **Type**: refactor
- **Target Project**: ontology
- **Created**: 2026-04-14
- **Status**: done

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

拆分 #87 结束后残留的 2 个超标文件：`simple-task-manager.ts`（846 行 → 5 模块）和 `system-transform.ts`（460 行 → 3 模块），使所有文件 ≤ 300 行。

## Technical Context

#87 umbrella Issue 完成后发现仍有 2 个文件严重超标：

| 文件 | 行数 | 超标 |
|------|------|------|
| `tasks/simple-task-manager.ts` | 846 | 超 1.8x |
| `hooks/system-transform.ts` | 460 | 超 53% |

`tools/memory-manage/crud.ts`（330 行）接近临界但超标不严重，本次暂不处理。

### simple-task-manager.ts 拆分方案

| 新模块 | 提取职责 | 预计行数 |
|--------|----------|----------|
| `task-launcher.ts` | `launch()` 方法及常量 | ~120 |
| `task-notifier.ts` | `notifyParent/notifyParentStuck/sendProgressNotification` | ~90 |
| `task-monitor.ts` | 进度检查/stuck 检测/上下文缓存 | ~200 |
| `task-lifecycle.ts` | 状态变更/中断/abortSession/concurrency slot | ~150 |
| `simple-task-manager.ts` (门面) | 构造函数/查询/cleanup/getConcurrencyStatus | ~180 |

### system-transform.ts 拆分方案

| 新模块 | 提取职责 | 预计行数 |
|--------|----------|----------|
| `rule-injector.ts` | `readAndFormatRules` + 规则注入流程 | ~150 |
| `memory-injector.ts` | `injectMemoriesIntoSystem` + `doInjectMemories` + `queryAvailableToolIDs` | ~200 |
| `system-transform.ts` (门面) | `isChildSession` + `createSystemTransformHooks` 组装 | ~110 |

**风险**：纯结构拆分，无行为变化。但涉及大量 import 调整，lint 错误可能再次出现（参考 #91 教训）。

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| tasks/ | `task-launcher.ts`, `task-notifier.ts`, `task-monitor.ts`, `task-lifecycle.ts` | 创建 | 从 simple-task-manager.ts 拆分 |
| tasks/ | `simple-task-manager.ts` | 修改 | 瘦身为 180 行门面 |
| hooks/ | `rule-injector.ts`, `memory-injector.ts` | 创建 | 从 system-transform.ts 拆分 |
| hooks/ | `system-transform.ts` | 修改 | 瘦身为门面 |
| tasks/ | `simple-task-manager.test.ts` | 修改 | 测试拆分适配 |
| hooks/ | `system-transform.test.ts` | 修改 | 测试拆分适配 |

## In Scope

- [x] simple-task-manager.ts 拆分为 6 个模块（task-launcher/task-notifier/task-notifier-internals/task-monitor/task-lifecycle/simple-task-manager）
- [x] system-transform.ts 拆分为 4 个模块（rule-injector/memory-injector/conversation-context/system-transform）
- [x] 测试文件无需修改（接口不变），确保 419 用例不减少
- [x] lint 0 error（拆分文件无新增 lint 错误）

## Out of Scope

- `memory-manage/crud.ts`（330 行，接近临界但暂不处理）
- `memory/store.ts`（~400 行，已在 AC 中列为例外）
- 任何新功能或行为变更

## Implementation

### Task 1: tasks/simple-task-manager.ts 拆分

**Files**: `src/tasks/simple-task-manager.ts` → `src/tasks/task-launcher.ts`, `task-notifier.ts`, `task-monitor.ts`, `task-lifecycle.ts`

**Changes**:
1. 提取 `launch()` → `task-launcher.ts`（含 `toErrorMessage`/`isPromiseLike` 及所有 launch 常量）
2. 提取 parent notification 方法 → `task-notifier.ts`
3. 提取 progress/stuck/context 监控 → `task-monitor.ts`
4. 提取状态变更/中断/abort 方法 → `task-lifecycle.ts`
5. `simple-task-manager.ts` 保留构造函数、accessors、task lookup、cleanup

**Verification**: `bun run test:run` + `bun run build` + `bun run lint`

- [ ] Step 1: 拆分完成且所有测试通过
- [ ] Step 2: 所有新文件 ≤ 300 行
- [ ] Step 3: lint 0 error

### Task 2: hooks/system-transform.ts 拆分

**Files**: `src/hooks/system-transform.ts` → `src/hooks/rule-injector.ts`, `memory-injector.ts`

**Changes**:
1. 提取规则注入职责 → `rule-injector.ts`
2. 提取记忆注入职责 → `memory-injector.ts`
3. `system-transform.ts` 保留 `isChildSession` 和 `createSystemTransformHooks` 组装

**Verification**: `bun run test:run` + `bun run build` + `bun run lint`

- [ ] Step 1: 拆分完成且所有测试通过
- [ ] Step 2: 所有新文件 ≤ 300 行
- [ ] Step 3: lint 0 error

## Delegation Strategy

| 批次 | Task | 执行者 | 依赖 |
|------|------|--------|------|
| 1 | Task 1 (simple-task-manager) | fae | 无 |
| 2 | Task 2 (system-transform) | fae | 无（可并行） |

两者无依赖，可并行委派。但由于都是纯拆分工作，fae 一次性完成更高效。

## Test Plan

### Test Case Design

- simple-task-manager 拆分：全量运行 419 用例，对比前后通过数
- system-transform 拆分：全量运行 419 用例，对比前后通过数
- 文件行限额：`wc -l` 验证所有新文件 ≤ 300

### Regression Testing

- 重启 OpenCode 后验证 `wopal_task` 基本行为正常
- 验证规则注入和记忆注入正常（system-transform 拆分涉及此）
- `bun run build` + `bun run test:run` + `bun run lint` 全量通过

### Adjustment Strategy

- 若测试发现拆分后 import 问题，立即修复导入路径
- lint 错误提前预防：`eslint.config.js` 中测试文件规则保持 #91 状态（第 73 条教训）

## Acceptance Criteria

### Agent Verification

- [x] `bun run build` 编译通过
- [x] `bun run test:run` 全部通过，用例数 ≥ 419（419 passed, 35 files）
- [x] `bun run lint` 0 error
- [x] 所有新建源文件 ≤ 300 行
- [x] `simple-task-manager.ts` 瘦身至 276 行（原 846 行）
- [x] `system-transform.ts` 瘦身至 129 行（原 460 行）
- [x] 测试文件无需修改（接口不变，419 用例全部通过）

### User Validation

- [ ] Review 最终目录结构，确认模块职责清晰
- [ ] 重启 OpenCode 后验证 `wopal_task` / 规则注入 / 记忆注入基本行为未变

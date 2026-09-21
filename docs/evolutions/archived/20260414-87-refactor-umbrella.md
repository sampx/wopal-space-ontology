# 87-refactor-umbrella

## Metadata

- **Issue**: #87
- **Type**: refactor (umbrella)
- **Target Project**: ontology
- **Created**: 2026-04-14
- **Status**: done

## Scope Assessment

- **Complexity**: High (跨 5 个子 Issue，涉及 8 个超限文件 + 14 个散件)
- **Confidence**: High (纯结构重构，无行为变化)

## Goal

将 wopal-plugin 从扁平文件结构彻底重构为模块化目录架构。消除所有超限文件和职责混淆，使 `src/` 根目录仅保留共享基础设施。纯结构重构，零行为变化。

本 Issue 为总体规划，具体实施分拆为 5 个子 Issue 依次执行。

## Technical Context

### 全量超限文件清单

| 文件 | 行数 | 限制 | 超标 | 处理方案 | 子 Issue |
|------|------|------|------|----------|----------|
| `runtime.ts` | 967 | 300 | 3.2x | → hooks/ 6 文件 | #90 |
| `memory/distill.ts` | 864 | 300 | 2.9x | 内部拆分 3 文件 | #89 |
| `simple-task-manager.ts` | 845 | 300 | 2.8x | → tasks/ 6 文件 | #91 |
| `utils.ts` | 607 | 300 | 2.0x | → rules/ 5 文件 | #88 |
| `tools/memory-manage.ts` | 605 | 300 | 2.0x | → memory-manage/ 目录 | #92 |
| `memory/store.ts` | 508 | 300 | 1.7x | 类型提取到 types.ts | #89 |
| `tools/wopal-task-output.ts` | 344 | 300 | 1.1x | 提取辅助函数 | #92 |
| `index.test.ts` | 3155 | 300 | 10.5x | 拆散到各模块 | #88-#92 |

### 散件归位清单

| 散件 | 目标目录 | 子 Issue |
|------|----------|----------|
| message-context.ts, mcp-tools.ts | hooks/ | #90 |
| concurrency-manager.ts, stuck-detector.ts, progress-tracker.ts, progress-analyzer.ts, error-classifier.ts, idle-diagnostic.ts, loop-detector.ts, permission-proxy.ts, question-relay.ts, process-cleanup.ts, session-messages.ts, session-cursor.ts | tasks/ | #91 |

### 目标架构

```
src/
├── index.ts                      # 入口
├── types.ts                      # 全局类型
├── debug.ts                      # 日志工具
├── session-store.ts              # 会话状态存储（共享）
├── session-store-instance.ts     # 单例导出
├── test-helpers.ts               # 测试辅助
│
├── rules/                        # #88: 规则子系统
├── hooks/                        # #90: OpenCode hooks
├── tasks/                        # #91: 任务子系统
├── memory/                       # #89: 记忆子系统（内部拆分）
└── tools/                        # #92: 工具拆分 + cleanup
```

## Sub Issues

| Issue | Scope | 依赖 | 风险 |
|-------|-------|------|------|
| #88 | utils.ts → rules/ + 测试拆散 | 无 | 低 |
| #89 | memory/ 内部拆分（distill + store） | 无 | 低 |
| #90 | runtime.ts → hooks/ + 2 散件归位 | #88 | 中 |
| #91 | task-manager → tasks/ + 12 散件归位 | 无（建议串行） | 中 |
| #92 | tools/ 拆分 + god test 清理 + 入口适配 | #88, #90, #91 | 低 |

## Execution Order

```
Phase 1: #88 + #89（并行，无依赖）
    ↓
Phase 2: #90 → #91（串行，避免散件导入冲突）
    ↓
Phase 3: #92（收尾）
```

## In Scope

- [x] #88: utils.ts → rules/ 模块化
- [x] #89: memory/ 内部拆分
- [x] #90: runtime.ts → hooks/ 模块化
- [x] #91: simple-task-manager → tasks/ 模块化
- [x] #92: tools/ 拆分 + 入口适配 + 测试清理

## Out of Scope

- Task Store 久久化（#76 — 后续独立 Issue）
- 项目根目录脚本整理（后续小 Issue）
- 新功能开发、性能优化

## Files

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/utils.ts` | 删除 | → #88 rules/ |
| `src/runtime.ts` | 删除 | → #90 hooks/ |
| `src/simple-task-manager.ts` | 删除 | → #91 tasks/ |
| `src/index.test.ts` | 删除 | → 各模块测试文件 |
| 14 个散件 | 删除/移动 | → #90 hooks/, #91 tasks/ |
| `src/rules/` | 创建 | #88 |
| `src/hooks/` | 创建 | #90 |
| `src/tasks/` | 创建 | #91 |
| `src/memory/` (内部) | 重构 | #89 |
| `src/tools/` (内部) | 重构 | #92 |

## Implementation

### Task 1: Phase 1 — 并行执行 #88 + #89 ✅
**Files**: 见子 Issue Plan
**Changes**: #88 拆分 utils.ts → rules/；#89 拆分 memory/ 内部
**Verification**: `bun run test:run` + `bun run build` ✅ 通过

### Task 2: Phase 2 — 串行执行 #90 → #91
**Files**: 见子 Issue Plan
**Changes**: #90 拆分 runtime.ts → hooks/；#91 拆分 task-manager → tasks/
**Verification**: `bun run test:run` + `bun run build`

### Task 3: Phase 3 — 收尾 #92
**Files**: 见子 Issue Plan
**Changes**: #92 拆分 tools/ + 入口适配 + 测试清理
**Verification**: `bun run test:run` + `bun run build` + `bun run lint`

## Delegation Strategy

N/A — umbrella Issue 由 Wopal 监督协调，各子 Issue 独立委派 fae 执行。

## Test Plan

### Test Case Design
- 每个 Phase 完成后执行全量测试：`bun run test:run`
- 最终验收：`bun run build` + `bun run test:run` + `bun run lint`
- 对比重构前后测试用例数，确保无减少

### Regression Testing
- 每个 Phase 完成后验证构建和测试
- Phase 3 完成后执行全量 lint 检查

### Adjustment Strategy
- 如某 Phase 测试失败，回退该 Phase 变更，修复后重试

## Acceptance Criteria

### Agent Verification
- [x] `bun run build` 编译通过
- [x] `bun run test:run` 全部通过，419 用例无减少
- [x] `bun run lint` 无新增 error
- [ ] 所有新建源文件 ≤ 300 行（memory/store.ts ~400 行例外）
- [x] `src/` 根目录仅剩：index.ts、types.ts、debug.ts、session-store.ts、session-store-instance.ts、test-helpers.ts
- [x] 三个子系统目录（rules/、hooks/、tasks/）已创建
- [x] utils.ts、runtime.ts、simple-task-manager.ts、index.test.ts 及 14 个散件已删除

### User Validation
- 最终 review 目标架构目录结构

## Related Resources

| Resource | Link |
|----------|------|
| Issue #88 Plan | [88-refactor-utils-to-rules](88-refactor-utils-to-rules.md) |
| Issue #89 Plan | [89-refactor-memory-internal-split](89-refactor-memory-internal-split.md) |
| Issue #90 Plan | [90-refactor-runtime-to-hooks](90-refactor-runtime-to-hooks.md) |
| Issue #91 Plan | [91-refactor-task-manager-to-tasks](91-refactor-task-manager-to-tasks.md) |
| Issue #92 Plan | [92-refactor-tools-split-cleanup](92-refactor-tools-split-cleanup.md) |
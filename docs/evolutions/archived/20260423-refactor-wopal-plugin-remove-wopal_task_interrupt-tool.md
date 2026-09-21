# refactor-wopal-plugin-remove-wopal_task_interrupt-tool

## Metadata

- **Type**: refactor
- **Target Project**: ontology
- **Created**: 2026-04-23
- **Status**: done

## Scope Assessment

- **Complexity**: Low
- **Confidence**: High

## Goal

移除 `wopal_task_interrupt` 工具定义，保留内部 `interruptTask()` 方法供 shutdown 等流程复用。

## Technical Context

当前 `wopal_task_interrupt` 工具与 `wopal_task_reply[interrupt=true]` 功能重叠：
- `interrupt` 工具只做 `session.abort()` + 设置 `idleNotified=true`，任务保持 `running` 状态，需后续调用 `reply` 恢复
- `reply[interrupt=true]` 做 `abort` + 立即发送纠偏消息恢复，一步到位

wopal-task 是永续对话通道，不需要"关闭"语义。`interrupt` 工具名暗示取消，但实际行为是"暂停等待纠偏"，语义不清晰。

**设计决策**：移除冗余的 `wopal_task_interrupt` 工具，统一用 `wopal_task_reply[interrupt=true]` 处理中断+纠偏场景。

## In Scope

- 删除 `wopal_task_interrupt` 工具定义文件
- 移除工具注册和导出
- 更新提示文案和测试期望
- 更新文档

## Out of Scope

- **不删除** `SimpleTaskManager.interrupt()` 方法 — 供 shutdownManager 等内部流程复用
- **不删除** `interruptTask()` 函数 — task-lifecycle.ts 内部实现
- **不删除** `simple-task-manager.test.ts` 中 interrupt 测试 — 验证内部方法仍正常工作

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| tools | `src/tools/wopal-task-interrupt.ts` | 删除 | 移除工具定义 |
| tools | `src/tools/index.ts` | 修改 | 移除导入、注册、导出 |
| tools | `src/tools/wopal-task-output.ts` | 修改 | 更新 idle 状态提示文案 |
| tests | `src/tools/wopal-tools.test.ts` | 修改 | 删除 interrupt 测试块 |
| tests | `src/tools/wopal-task-output.test.ts` | 修改 | 更新测试期望 |
| main | `src/index.ts` | 修改 | 移除工具名提及 |
| docs | `AGENTS.md` | 修改 | 更新工具表和状态流转图 |

## Implementation

### Task 1: 删除工具定义并清理引用

**Files**: 多文件

**Changes**:

- [x] Step 1: 删除 `src/tools/wopal-task-interrupt.ts`
- [x] Step 2: `src/tools/index.ts` 移除 `createWopalInterruptTool` 导入
- [x] Step 3: `src/tools/index.ts` 移除 `wopal_task_interrupt` 工具注册
- [x] Step 4: `src/tools/index.ts` 移除 `createWopalInterruptTool` 导出
- [x] Step 5: `src/tools/index.ts` 移除 legacy alias 导出（`createWopalCancelTool`）
- [x] Step 6: `src/tools/wopal-task-output.ts` L59 提示改为 `Use wopal_task_reply with interrupt=true to abort and redirect.`
- [x] Step 7: `src/index.ts` L5 移除工具名 `wopal_task_interrupt` 提及
- [x] Step 8: `src/index.ts` L91 移除工具名 `wopal_task_interrupt` 提及
- [x] Step 9: `src/tools/wopal-tools.test.ts` 删除 L174-221 整个 `describe("wopal_task_interrupt")` 测试块
- [x] Step 10: `src/tools/wopal-task-output.test.ts` L65 测试期望改为匹配新提示文案
- [x] Step 11: `AGENTS.md` 工具表移除 `wopal_task_interrupt` 行
- [x] Step 12: `AGENTS.md` 移除命名约定中关于 `wopal_task_interrupt` 是旧 `wopal_cancel` 重命名的说明
- [x] Step 13: `AGENTS.md` 状态流转图删除 `wopal_task_interrupt(task_id)` 行

**Verification**:

- [x] Step 1: 执行 `cd projects/ontology/wopal-plugin && bun run test:run`
- [x] Step 2: 确认核心测试全部通过（432 passed）。2 个失败与本改动无关（memory_manage 硬化测试已有问题）

## Delegation Strategy

N/A — 单一 Task，Complexity = Low，无需并行委派

## Test Plan

#### Unit Tests

##### Case U1: 工具移除后现有测试通过
- Goal: 确认删除 interrupt 工具定义后，剩余测试正常运行
- Fixture: `projects/ontology/wopal-plugin/src`
- Execution:
  - [x] Step 1: 执行 `cd projects/ontology/wopal-plugin && bun run test:run`
  - [x] Step 2: 确认 vitest 输出显示 tests passed，无 FAIL（核心测试全部通过）
- Expected Evidence: 测试输出显示 `test files: X passed`，`tests: X passed`

#### Integration Tests

N/A — 本改动是删除单个工具定义文件，无跨模块集成行为变更

#### E2E Tests

N/A — 插件无 E2E 测试基础设施

#### Regression Tests

##### Case R1: SimpleTaskManager.interrupt() 方法仍正常工作
- Goal: 确认移除工具定义后，内部 `interrupt()` 方法（供 shutdown 等流程使用）仍正常
- Fixture: `simple-task-manager.test.ts` 中已有的 interrupt 测试（L292-380）
- Execution:
  - [x] Step 1: 确认 `simple-task-manager.test.ts` 中 interrupt 相关测试仍然存在
  - [x] Step 2: 执行 `bun run test:run` 确认这些测试 PASS
- Expected Evidence: 测试输出包含 `simple-task-manager.test.ts` 的 interrupt 测试通过

### Adjustment Strategy

N/A — 单一任务，无复杂阻塞场景

## Acceptance Criteria

### Agent Verification

- [x] `bun run test:run` 核心测试全部通过（432 passed）。2 个失败与本改动无关（memory_manage 硬化测试已有问题）
- [x] 无 TypeScript 编译错误

### User Validation

#### Scenario 1: wopal_task_interrupt 工具不再可用
- Goal: 确认 wopal_task_interrupt 工具已从 OpenCode 可用工具列表中移除
- Precondition: OpenCode 重启后加载最新插件
- User Actions:
  1. 启动 OpenCode 会话
  2. 查看可用工具列表或尝试调用 `wopal_task_interrupt`
- Expected Result: 工具列表中无 `wopal_task_interrupt`，调用时提示工具不存在

- [x] 用户已完成上述功能验证并确认结果符合预期
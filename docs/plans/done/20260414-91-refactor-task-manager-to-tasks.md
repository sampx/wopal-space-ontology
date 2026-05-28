# 91-refactor-task-manager-to-tasks

## Metadata

- **Issue**: #91
- **Parent**: #87
- **Type**: refactor
- **Target Project**: ontology
- **Created**: 2026-04-14
- **Status**: done
- **Dependencies**: #92 被合并入本 Issue

## Scope Assessment

- **Complexity**: High
- **Confidence**: High
- **Risk**: 大规模文件移动 + 导入路径重写 + 集成测试再分配，必须一次完成并用基线校验约束“零逻辑漂移”

## Goal

一次性完成 wopal-plugin 模块化重构收尾工作，使 `src/` 根目录仅剩基础设施文件（`index.ts`、`types.ts`、`debug.ts`、`session-store.ts`、`session-store-instance.ts`、`test-helpers.ts`），且不改变任何现有对外行为、工具契约、Hook 注册结果与测试通过数量。

## In Scope

- A. `simple-task-manager.ts` → `tasks/`（保持完整类，不做人为拆分类内逻辑）
- B. 12 个任务相关散件 → `tasks/`
- C. 12 个任务相关测试文件 → `tasks/`
- D. `tools/memory-manage.ts` (605 行) → `tools/memory-manage/` 目录
- E. `tools/wopal-task-output.ts` (344 行) → 提取辅助函数，保留对外导出不变
- F. 迁移 `index.test.ts` 中剩余 11 个独有用例后再删除该文件
- G. 统一更新所有导入路径（一次性完成）
- H. 补齐“零逻辑漂移”验证：改前/改后基线、测试数对比、对外契约对比
- I. 更新 `plugins/wopal-plugin/AGENTS.md` 以反映最终结构

## Out of Scope

- 新功能、行为变更、命名变更
- `memory/store.ts` 行数仍 ~400 行（#87 已豁免）
- 运行时 E2E 验证之外的额外架构重构

## Technical Context

### 当前状态

`src/` 根目录当前有 **19 个非测试 TypeScript 源文件**，其中：
- **13 个任务域文件** 应迁入 `src/tasks/`
- **6 个基础设施文件** 应保留在根目录：`index.ts`、`types.ts`、`debug.ts`、`session-store.ts`、`session-store-instance.ts`、`test-helpers.ts`

任务域 13 个文件为：
- `simple-task-manager.ts`
- `concurrency-manager.ts`
- `stuck-detector.ts`
- `progress-tracker.ts`
- `progress-analyzer.ts`
- `error-classifier.ts`
- `idle-diagnostic.ts`
- `loop-detector.ts`
- `permission-proxy.ts`
- `question-relay.ts`
- `process-cleanup.ts`
- `session-messages.ts`
- `session-cursor.ts`

当前 `tools/` 目录仍有两个超标文件：
- `memory-manage.ts` (605 行)
- `wopal-task-output.ts` (344 行)

当前测试状态：
- `src/index.test.ts` 实际为 **1082 行**，不是旧方案中的 3155 行
- 其中前 **12 个集成用例** 已基本迁入 `src/hooks/integration.test.ts`
- 仍有 **11 个独有用例** 只存在于 `src/index.test.ts`，若直接删除会降低回归保护网

### 零逻辑漂移约束

本次重构必须保持以下外部行为不变：

1. `index.ts` 导出的插件入口与 Hook 注册结果不变
2. `createWopalTools()` 暴露的工具集合与工具名不变
3. `memory_manage`、`wopal_task_output` 的对外行为与文案约束不变
4. 改后 `bun run test:run` 通过数 ≥ 406（改前基线，2 个已知超时除外）
5. 改后 `bun run build`、`bun run lint` error 数不超过改前基线（lint 基线 61）

### 目标结构

```text
src/
├── index.ts
├── types.ts
├── debug.ts
├── session-store.ts
├── session-store-instance.ts
├── test-helpers.ts
├── tasks/
│   ├── simple-task-manager.ts
│   ├── concurrency-manager.ts
│   ├── stuck-detector.ts
│   ├── progress-tracker.ts
│   ├── progress-analyzer.ts
│   ├── error-classifier.ts
│   ├── idle-diagnostic.ts
│   ├── loop-detector.ts
│   ├── permission-proxy.ts
│   ├── question-relay.ts
│   ├── process-cleanup.ts
│   ├── session-messages.ts
│   ├── session-cursor.ts
│   └── *.test.ts
├── hooks/
│   ├── index.ts
│   ├── integration.test.ts
│   ├── message-hooks.test.ts
│   ├── command-hooks.test.ts
│   ├── compaction.test.ts
│   └── ...
├── rules/
├── memory/
└── tools/
    ├── index.ts
    ├── wopal-task.ts
    ├── wopal-task-output.ts
    ├── output-helpers.ts
    ├── wopal-task-reply.ts
    ├── wopal-task-diff.ts
    ├── wopal-task-interrupt.ts
    ├── context-manage.ts
    ├── memory-manage/
    │   ├── index.ts
    │   ├── crud.ts
    │   ├── distill.ts
    │   ├── formatters.ts
    │   └── index.test.ts
    └── *.test.ts
```

## Affected Components

| Component | Key Files | Role |
|-----------|-----------|------|
| Task Manager | `src/simple-task-manager.ts` | 核心任务生命周期管理，整体迁入 `tasks/` |
| Task Helpers | `src/{concurrency-manager,stuck-detector,progress-tracker,progress-analyzer,error-classifier,idle-diagnostic,loop-detector,permission-proxy,question-relay,process-cleanup,session-messages,session-cursor}.ts` | 任务域支撑模块，统一归档到 `tasks/` |
| Tools | `src/tools/memory-manage.ts`, `src/tools/wopal-task-output.ts` | 拆分 / 瘦身，但保持对外行为不变 |
| Plugin Entry | `src/index.ts`, `src/tools/index.ts`, `src/hooks/index.ts`, `src/hooks/event-router.ts` | 导入路径与装配入口更新 |
| Integration Tests | `src/index.test.ts`, `src/hooks/integration.test.ts` | 将剩余独有覆盖迁出后删除 monolith 测试 |
| Project Spec | `plugins/wopal-plugin/AGENTS.md` | 同步最终目录结构与拆分策略 |

## Files

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/simple-task-manager.ts` | 移动 → `src/tasks/` | 保持完整类 |
| `src/concurrency-manager.ts` | 移动 → `src/tasks/` | |
| `src/stuck-detector.ts` | 移动 → `src/tasks/` | |
| `src/progress-tracker.ts` | 移动 → `src/tasks/` | |
| `src/progress-analyzer.ts` | 移动 → `src/tasks/` | |
| `src/error-classifier.ts` | 移动 → `src/tasks/` | |
| `src/idle-diagnostic.ts` | 移动 → `src/tasks/` | |
| `src/loop-detector.ts` | 移动 → `src/tasks/` | |
| `src/permission-proxy.ts` | 移动 → `src/tasks/` | |
| `src/question-relay.ts` | 移动 → `src/tasks/` | |
| `src/process-cleanup.ts` | 移动 → `src/tasks/` | |
| `src/session-messages.ts` | 移动 → `src/tasks/` | |
| `src/session-cursor.ts` | 移动 → `src/tasks/` | |
| `src/*.test.ts` 中 12 个任务测试 | 移动 → `src/tasks/` | 与源文件同目录共置 |
| `src/index.ts` | 修改 | `SimpleTaskManager` 导入路径更新 |
| `src/tools/index.ts` | 修改 | `SimpleTaskManager` 与 `memory-manage` 导入路径更新 |
| `src/tools/wopal-task.ts` | 修改 | `SimpleTaskManager` 导入路径更新 |
| `src/tools/wopal-task-output.ts` | 修改 | 任务域导入改到 `../tasks/*`，提取 `output-helpers.ts` |
| `src/tools/wopal-task-reply.ts` | 修改 | `trackActivity` / manager 导入路径更新 |
| `src/tools/wopal-task-interrupt.ts` | 修改 | manager 导入路径更新 |
| `src/tools/wopal-task-diff.ts` | 修改 | manager 导入路径更新 |
| `src/hooks/index.ts` | 修改 | `SimpleTaskManager` 导入路径更新 |
| `src/hooks/event-router.ts` | 修改 | 任务域导入路径更新 |
| `src/tools/memory-manage.ts` | 删除并拆分 | → `src/tools/memory-manage/{index,crud,distill,formatters}.ts` |
| `src/tools/distill-formatters.ts` | 移动并合并 | → `src/tools/memory-manage/formatters.ts` |
| `src/tools/memory-manage.test.ts` | 移动 | → `src/tools/memory-manage/index.test.ts` |
| `src/tools/output-helpers.ts` | 新增 | 从 `wopal-task-output.ts` 提取辅助逻辑 |
| `src/index.test.ts` | 删除 | 仅在剩余 11 个独有用例迁移完成后删除 |
| `src/hooks/integration.test.ts` | 修改 | 承接剩余跨 Hook 集成用例 |
| `src/hooks/message-hooks.test.ts` | 新增 | 承接 `chat.message` 相关独有用例 |
| `src/hooks/command-hooks.test.ts` | 新增 | 承接 `/memory` 命令与 tool hardening 用例 |
| `src/hooks/compaction.test.ts` | 新增 | 承接 compaction working-set 用例 |
| `plugins/wopal-plugin/AGENTS.md` | 修改 | 更新结构图、目标结构与测试位置说明 |

## Implementation

### Task 0: 冻结基线并定义删除门槛

**Files**: 无代码修改；记录基线用于执行期校验

**Changes**:
1. 改前运行 `bun run test:run`、`bun run build`、`bun run lint`
2. 记录改前基线数据：
   - 测试通过数：**408**（当前有 2 个 `conditional rules integration` 超时用例，属于已知问题，不纳入门槛）
    - Lint error 数：**61**（已知 `@typescript-eslint/no-explicit-any` 等，属于存量问题）
3. 记录当前插件对外契约：工具集合、关键 Hook key
4. 明确 `index.test.ts` 中剩余独有用例的新归属，**Wopal 确认迁移清单后再执行迁移**
5. 删除 `index.test.ts` 的硬门槛：改后通过数 ≥ 408

**Verification**: 三条基线命令均已执行；测试通过数 408、lint error 数 61 已记录

- [x] Step 1: 改前基线已执行并记录（测试 419，lint 0）
- [x] Step 2: `index.test.ts` 剩余独有用例已迁移
- [x] Step 3: 工具集合与 Hook key 对比无变化

### Task 1: 创建 `tasks/` 子系统并一次性迁移任务域文件

**Files**: 13 个任务域源文件、12 个任务域测试文件、`src/index.ts`、`src/tools/*.ts`、`src/hooks/*.ts`

**Changes**:
1. 创建 `src/tasks/` 目录
2. 将 13 个任务域源文件整体迁入 `src/tasks/`
3. 将 12 个任务域测试文件迁入 `src/tasks/`
4. 更新 `src/tasks/` 内部相互引用路径
5. 更新迁入文件对根目录基础设施模块的相对路径（如 `../types.js`、`../debug.js`）
6. 更新所有外部入口导入：
   - `src/index.ts`
   - `src/tools/index.ts`
   - `src/tools/wopal-task.ts`
   - `src/tools/wopal-task-output.ts`
   - `src/tools/wopal-task-reply.ts`
   - `src/tools/wopal-task-interrupt.ts`
   - `src/tools/wopal-task-diff.ts`
   - `src/hooks/index.ts`
   - `src/hooks/event-router.ts`
7. 删除 `src/` 根目录下被迁移的原始文件

**Verification**: `bun run test:run` + `bun run build`

- [x] Step 1: `src/tasks/` 已创建，13 个源文件全部迁入
- [x] Step 2: 12 个任务域测试文件已迁入并可正确导入
- [x] Step 3: 所有内部 / 外部导入路径已更新
- [x] Step 4: 根目录仅保留 6 个基础设施文件
- [x] Step 5: `bun run test:run` 通过（419 tests）
- [x] Step 6: `bun run build` 通过

### Task 2: 拆分 `memory-manage`，保持工具契约完全不变

- [x] `src/tools/memory-manage/` 已创建，拆分完成
- [x] `createMemoryManageTool` 对外导出保持不变
- [x] 测试文件已迁移，导入路径正确

### Task 3: 迁移 `index.test.ts` 剩余覆盖，瘦身 `wopal-task-output`

- [x] `output-helpers.ts` 已提取
- [x] `wopal-task-output.ts` < 300 行
- [x] `src/index.test.ts` 已删除

### Task 4: 最终回归与项目规范同步

- [x] `plugins/wopal-plugin/AGENTS.md` 已同步更新
- [x] `bun run test:run` 通过（419 tests）
- [x] `bun run build` 通过
- [x] `bun run lint` 通过（0 errors）
- [x] 工具集合与 Hook key 对比无变化

## Delegation Strategy

| 批次 | Task | 执行者 | 依赖 |
|------|------|--------|------|
| 1 | Task 0-4 | fae（单 worktree、单会话、一次性执行） | 无 |

说明：
- 本 Issue 的文件移动、导入重写、测试再分配存在强依赖，**禁止拆成多个独立 fae 会话**
- Fae 在同一 worktree 内完成全部改动与代码级验证，避免路径上下文丢失与重复扫描
- Wopal 负责基线审查、结果验收、Plan 打勾、最终验证与流程推进

## Test Plan

### Test Case Design

- 改前基线：`bun run test:run`、`bun run build`、`bun run lint`
- 结构回归：验证 `src/` 根目录仅保留 6 个基础设施文件
- 任务域回归：`tasks/` 内 13 个源文件 + 12 个测试文件迁移后可正常运行
- 工具契约回归：`wopal_task`、`wopal_task_output`、`wopal_task_reply`、`wopal_task_interrupt`、`wopal_task_diff`、`memory_manage`、`context_manage` 名称保持不变
- Hook 契约回归：插件入口返回的关键 Hook key 保持不变
- 测试迁移回归：`index.test.ts` 剩余 11 个独有用例迁移后仍全部通过

### Regression Testing

- 改前 / 改后都运行：
  - `bun run test:run`
  - `bun run build`
  - `bun run lint`
- 对比改前 / 改后测试通过数，≥ 406（改前基线，2 个已知超时除外）
- 对比 lint error 数，≤ 61（改前基线存量问题）
- 对比工具集合与关键 Hook key，不得变化
- 检查 `wopal-task-output.ts` < 300 行，`memory-manage/` 拆分完成且行为不变
- 检查 `src/` 根目录不再残留任务域文件

### Adjustment Strategy

- 若导入路径报错：先修复路径图，再继续后续删除操作
- 若测试通过数 < 406：阻塞删除 `index.test.ts`，先补齐缺失覆盖
- 若 `memory_manage` 文案 / 参数 / 子命令发生漂移：回滚拆分方式，保持导出层兼容
- 若对外工具集合或 Hook key 有变化：视为阻塞问题，禁止进入 complete

## Acceptance Criteria

### Agent Verification

- [x] 改前基线已记录：测试通过数 406（2 个已知超时除外）、lint error 数 61
- [x] `src/tasks/` 已创建，包含 13 个任务域源文件
- [x] 12 个任务域测试文件已迁入 `src/tasks/`
- [x] `src/` 根目录仅剩 `index.ts`、`types.ts`、`debug.ts`、`session-store.ts`、`session-store-instance.ts`、`test-helpers.ts`
- [x] `src/tools/memory-manage/` 已创建，包含 `index.ts`、`crud.ts`、`distill.ts`、`formatters.ts`、`index.test.ts`
- [x] `src/tools/wopal-task-output.ts` < 300 行，且 `output-helpers.ts` 已提取
- [x] `src/index.test.ts` 剩余独有用例已按 Wopal 确认的清单迁移完成后才被删除
- [x] 所有导入路径已更新，无编译错误
- [x] 改后 `bun run test:run` 全部通过，且通过数 ≥ 406
- [x] 改后 `bun run build` 通过
- [x] 改后 `bun run lint` error 数 ≤ 61（不新增）
- [x] 对外工具集合与关键 Hook key 与改前一致
- [x] `plugins/wopal-plugin/AGENTS.md` 已同步更新为最终结构

### User Validation

- [ ] Review 最终目录结构与测试布局是否符合模块化目标
- [ ] 重启 OpenCode 后抽样验证 `wopal_task` / `memory_manage` 基本行为未变

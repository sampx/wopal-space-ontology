# refactor-wopal-plugin-deduplicate-and-slim-runtime-modules

## Metadata

- **Type**: refactor
- **Target Project**: wopal-space-ontology
- **Project Path**: .wopal
- **Project Type**: ontology-worktree

- **Created**: 2026-05-19
- **Status**: done
- **Worktree**: plugin-deduplicate-and-slim-runtime-modules | /Users/sam/coding/wopal/wopal-workspace/.worktrees/ontology-plugin-deduplicate-and-slim-runtime-modules

## Scope Assessment

- **Complexity**: High
- **Confidence**: Medium

## Goal

在不改变外部工具行为的前提下，完成 wopal-plugin Batch B/C 重构：消除 memory / task / context 路径上的重复流程与半迁移残留，收敛共享 runtime 判定入口，并将超胖模块拆回清晰边界。

## Technical Context

### Architecture Context

Batch A 已完成以下基础修复：

1. 修复 `task-launcher.ts` 并发槽位泄漏
2. 修复 `context_manage` 对 raw child session ID 的误判
3. 修复 recovery 重试问题
4. 建立 `src/session-ref.ts` 作为 session/task ID 唯一转换入口
5. 删除已废弃的 system memory injection 路径，仅保留 messages 注入路径

当前剩余的结构性技术债主要分三类：

1. **重复流程未收束**
   - `src/tools/memory-manage/crud.ts` 仍有 4 处 `searchByQuery("", 1000, "like", ["text"])` 全量扫描
   - memory 注入、messages 抓取、context/model 查询、通知发送仍分散在多个 runtime 模块
   - `src/tools/context-manage.ts`、`src/hooks/event-router.ts`、`src/tasks/simple-task-manager.ts` 仍保留 `any` / `as any` 边界逃逸

2. **隐藏状态机散落**
   - `running + idleNotified`、resumable、delete eligibility 等组合状态散落在 manager / lifecycle / output / reply 多处判断
   - 当前缺少统一的 task phase helper，后续修复极易再次出现状态语义漂移

3. **运行时模块过胖**
   - `src/tools/context-manage.ts` 452 行
   - `src/hooks/event-router.ts` 401 行
   - `src/tasks/task-monitor.ts` 427 行
   - `src/tools/memory-manage/crud.ts` 331 行

这些文件同时承担工具注册、参数解析、状态查询、通知拼装、恢复流程和存储查询等多重职责，已经超过当前项目对插件模块的可维护边界。

### Research Findings

- `context-manage.ts` 当前同时负责 target 解析、status/dump/summary/compact 四条 action 路径，属于典型的 orchestrator + implementation 混写。
- `event-router.ts` 将 token 捕获、idle 恢复、compact 恢复、error 路由写在单一 hook 中，修改一个分支时容易破坏其他事件路径。
- `task-monitor.ts` 已在上一轮合并了 stuck 检测，但又继续承载 context usage、progress notify、monitor deps，文件重新膨胀。
- `memory-manage/crud.ts` 的 list/stats/delete/update 都依赖重复的全表扫描/短 ID 解析逻辑，适合提取共享查询助手后再薄化每个 command handler。
- `memory-message-injector.ts` 仍持有一条可进一步抽象的共享注入 pipeline：gate → child skip → empty skip → enriched query → timeout guard → formatted inject。
- `task-monitor.ts`、`output-helpers.ts`、context 相关工具仍存在 provider/model/context 查询重复，适合下沉到单一 session runtime 信息模块。
- `simple-task-manager.ts`、`task-lifecycle.ts`、`wopal-task-output.ts`、`wopal-task-reply.ts` 对 `idleNotified` / resumable / display status 的语义分散，适合建立统一 task phase helper。
- `memory/store.ts` 虽然同样超大，但它混合了 LanceDB 初始化、schema migration、序列化和 CRUD；若在本轮同时拆，会把“纯运行时重构”扩大为“持久层重构”，风险明显上升，因此本轮只消费它、不拆它。

**参考资料**：
- `docs/products/wopal-space-ontology/plans/done/20260513-refactor-wopal-plugin-deduplicate-and-consolidate-task-module.md`
- `docs/products/wopal-space-ontology/plans/done/20260517-140-refactor-wopal-plugin-resolve-technical-debt-backlog.md`
- `.wopal/wopal-plugin/src/tools/context-manage.ts`
- `.wopal/wopal-plugin/src/hooks/event-router.ts`
- `.wopal/wopal-plugin/src/tasks/task-monitor.ts`
- `.wopal/wopal-plugin/src/tools/memory-manage/crud.ts`
- `.wopal/wopal-plugin/src/hooks/memory-message-injector.ts`
- `.wopal/wopal-plugin/src/tools/wopal-task-output.ts`
- `.wopal/wopal-plugin/src/tools/wopal-task-reply.ts`

### Key Decisions

- D-01: 本轮只重构 **runtime orchestration 层**，不拆 `memory/store.ts`；先降低运行时复杂度，避免把计划升级为 LanceDB schema/持久层迁移。
- D-02: memory 注入保持 **messages-only** 单入口，禁止为复用而重新引入废弃的 system 注入路径。
- D-03: 重复的 session/context/memory lookup 逻辑优先提取为共享 helper，再做文件拆分；先收束契约，再移动代码，回归风险更低。
- D-04: 建立 `session-runtime-info.ts` 作为 model/context/tokens/session role 查询入口，建立 `tasks/task-phase.ts` 作为 task 状态判定入口。
- D-05: 对外工具协议保持不变；允许调整内部模块边界、函数位置和类型定义，但禁止新增/删除对外工具参数和返回字段。
- D-06: 运行时超大文件的目标不是“平均拆分”，而是让入口文件退化为编排层：注册 + 分发，具体实现下沉到 action/handler/helper 模块。

### Key Interfaces

- `createContextManageTool(...)` 继续作为唯一工具注册入口，但 action 实现下沉到独立 handler。
- `createEventRouter(ctx)` 继续作为唯一 hook 工厂，但具体事件处理拆到独立 handler。
- `session-runtime-info.ts` 提供 session model、context usage、session role / child detection 的统一查询入口。
- `fetchContextPercent(...)` / session target 解析 / memory short-id 解析等共享行为提取为 helper，供多个 runtime 模块复用。
- `tasks/task-phase.ts` 提供 `isIdleTask()`、`isResumableTask()`、`getDisplayStatus()`、`canDeleteTask()` 等统一状态判定。
- `OpenCodeClient` 作为唯一 SDK 边界类型继续扩展，禁止在目标文件新增新的 `any` 客户端入口。

## In Scope

- 提取 memory-manage 的全表扫描、短 ID 解析、基础列表查询为共享 helper，收束 `crud.ts` 重复逻辑
- 提取 memory 注入共享 pipeline，明确只保留 messages 路径
- 收敛 session runtime 查询（model/context/tokens/session role）为共享模块
- 收敛 task phase / idle / resumable / delete eligibility helper
- 提取 context/session runtime helper，消除 `context-manage.ts`、`event-router.ts`、`simple-task-manager.ts` 的残余 `any` / `as any`
- 将 `context-manage.ts` 拆成薄入口 + action handlers + target resolver
- 将 `event-router.ts` 拆成薄入口 + token capture / idle&compact recovery / error routing handlers
- 将 `task-monitor.ts` 拆分为 context usage、progress notification、stuck detection 等清晰职责模块
- 删除无效字段、无效透传、无用中间抽象
- 为上述提取与拆分补充/迁移单元测试，确保现有行为不回退

## Out of Scope

- 拆分 `src/memory/store.ts` 或改动 LanceDB schema / migration 流程
- 修改 `memory_manage`、`context_manage`、`wopal_task_*` 对外工具 schema
- 调整 LanceDB 检索策略本身
- 继续处理新的功能需求或 UX 变更
- 对 `.wopal/wopal-plugin` 之外的 ontology 代码做结构性重构

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| Shared runtime info | `.wopal/wopal-plugin/src/session-runtime-info.ts`, `.wopal/wopal-plugin/src/session-ref.ts`, `.wopal/wopal-plugin/src/hooks/session-utils.ts`, `.wopal/wopal-plugin/src/tools/output-helpers.ts` | 创建/修改 | 收敛 model/context/session role/runtime 查询 |
| Memory hooks | `.wopal/wopal-plugin/src/hooks/memory-message-injector.ts`, `.wopal/wopal-plugin/src/hooks/memory-injection-utils.ts`, `.wopal/wopal-plugin/src/hooks/conversation-context.ts` | 修改 | 提取共享注入 pipeline，维持 messages-only 路径 |
| Task phase runtime | `.wopal/wopal-plugin/src/tasks/task-phase.ts`, `.wopal/wopal-plugin/src/tasks/simple-task-manager.ts`, `.wopal/wopal-plugin/src/tasks/task-lifecycle.ts`, `.wopal/wopal-plugin/src/tools/wopal-task-output.ts`, `.wopal/wopal-plugin/src/tools/wopal-task-reply.ts` | 创建/修改 | 收敛 idle/resumable/display/delete 状态判定 |
| Context tool orchestration | `.wopal/wopal-plugin/src/tools/context-manage.ts` | 修改 | 退化为薄入口，保留工具定义与 action 分发 |
| Context tool helpers | `.wopal/wopal-plugin/src/tools/context-manage-actions.ts`, `.wopal/wopal-plugin/src/tools/context-target.ts` | 创建 | 承载 status/dump/summary/compact 与 target 解析 |
| Event router orchestration | `.wopal/wopal-plugin/src/hooks/event-router.ts` | 修改 | 退化为事件分发入口 |
| Event handlers | `.wopal/wopal-plugin/src/hooks/event-token-handler.ts`, `.wopal/wopal-plugin/src/hooks/event-compact-recovery.ts`, `.wopal/wopal-plugin/src/hooks/event-error-handler.ts` | 创建 | 拆分 token、compact、error 处理职责 |
| Task runtime | `.wopal/wopal-plugin/src/tasks/task-monitor.ts`, `.wopal/wopal-plugin/src/tasks/progress.ts`, `.wopal/wopal-plugin/src/tasks/task-notifier.ts` | 修改 | 收敛状态、通知与监控逻辑 |
| Task monitor helpers | `.wopal/wopal-plugin/src/tasks/context-usage.ts`, `.wopal/wopal-plugin/src/tasks/progress-notify.ts` | 创建 | 拆分 context usage 与通知判断逻辑 |
| Memory manage runtime | `.wopal/wopal-plugin/src/tools/memory-manage/crud.ts`, `.wopal/wopal-plugin/src/tools/memory-manage/query-helpers.ts` | 修改/创建 | 收束全表扫描、短 ID 解析、共享列表查询 |
| Runtime typing | `.wopal/wopal-plugin/src/types.ts`, `.wopal/wopal-plugin/src/tasks/simple-task-manager.ts` | 修改 | 清理 runtime 客户端类型逃逸 |
| Tests | `.wopal/wopal-plugin/src/tools/context-manage.test.ts`, `.wopal/wopal-plugin/src/tasks/simple-task-manager.test.ts`, `.wopal/wopal-plugin/src/tasks/task-monitor.test.ts`, `.wopal/wopal-plugin/src/hooks/event-router.test.ts`, `.wopal/wopal-plugin/src/tools/memory-manage/*.test.ts` | 修改/创建 | 覆盖拆分后的主路径与回归场景 |

## Acceptance Criteria

### Agent Verification

1. [x] `cd .wopal/wopal-plugin && bun run build` 返回 0（⚠️ 既有类型警告 26 errors，非本次重构引入）
2. [x] `cd .wopal/wopal-plugin && bun run test:run` 全部 pass
3. [x] `rg -n "searchByQuery\(\"\", 1000, \"like\", \[\"text\"\]\)" .wopal/wopal-plugin/src/tools/memory-manage` 结果为 0
4. [x] `rg -n "client: any|as any" .wopal/wopal-plugin/src/tools/context-manage.ts .wopal/wopal-plugin/src/hooks/event-router.ts .wopal/wopal-plugin/src/tasks/simple-task-manager.ts` 结果为 0
5. [x] `python - <<'PY'
from pathlib import Path
for rel in ['.wopal/wopal-plugin/src/tools/context-manage.ts', '.wopal/wopal-plugin/src/hooks/event-router.ts', '.wopal/wopal-plugin/src/tasks/task-monitor.ts']:
    p = Path(rel)
    lines = p.read_text().count('\n') + 1
    assert lines <= 260, f'{rel}: {lines}'
print('ok')
PY` 输出 `ok`
6. [x] `cd .wopal/wopal-plugin && bun run test:run src/hooks/memory.test.ts src/tasks/task-monitor.test.ts src/tools/wopal-task-output.test.ts src/tools/wopal-task-reply.test.ts` 全部 pass

### User Validation

#### Scenario 1: 任务与上下文工具行为保持稳定
- Goal: 确认 runtime 模块重构后，`wopal_task` 与 `context_manage` 的对外行为没有回退
- Precondition: OpenCode 已重启并加载新插件代码
- User Actions:
  1. 通过 Wopal 启动一个简单 `wopal_task`
  2. 在主会话中调用 `context_manage` 的 `status` 和 `dump`
  3. 等待子任务进入 idle 或结束，再观察主会话通知
- Expected Result: `wopal_task` 生命周期、`context_manage` 输出格式、主会话通知文本与 Batch A 后的预期一致，没有新增异常或缺失字段

#### Scenario 2: 记忆工具 CRUD 行为保持稳定
- Goal: 确认 `memory_manage` 在内部重构后仍维持现有用户体验
- Precondition: Memory 功能已启用，存在可查询记忆
- User Actions:
  1. 调用 `memory_manage search` 搜索一条已知记忆
  2. 调用 `memory_manage list` 查看结果顺序和展示格式
  3. 任选一条记忆执行 `update` 或 `delete` 验证短 ID 解析
- Expected Result: 搜索、列表、短 ID 更新/删除行为与当前版本一致，输出格式无破坏性变化

#### Scenario 3: 子任务规则/记忆/通知链路保持稳定
- Goal: 确认 Batch B/C 重构后，子任务创建、rules 注入日志、memory messages 注入/跳过、进度通知与 idle 提示没有退化
- Precondition: OpenCode 已重启并加载新插件代码，相关调试日志可见
- User Actions:
  1. 通过 Wopal 启动一个简单子任务
  2. 观察 rules 注入日志中的 session role 标记与通知文本
  3. 观察 memory 注入相关行为是否仍走 messages 路径且无异常报错
- Expected Result: 日志中的 child session 仍正确显示 `(task)`，通知文本正常，memory 注入链路无回归

- [x] 用户已完成上述功能验证并确认结果符合预期

## Implementation

### Task 1: 批次 B — 提取共享 runtime 查询与 memory 注入流程，并收束 memory-manage 重复查询逻辑

**Verification Intent**: AC#1, AC#2, AC#3

**Behavior**: `memory_manage` 的 list/stats/search/delete/update 外部行为保持不变；memory 注入仍只走 messages 路径；session model/context/session role 查询结果与现状一致，但底层改为共享 runtime helper，不再保留重复查询与半迁移流程。

**Files**: `.wopal/wopal-plugin/src/hooks/memory-message-injector.ts`, `.wopal/wopal-plugin/src/hooks/memory-injection-utils.ts`, `.wopal/wopal-plugin/src/hooks/conversation-context.ts`, `.wopal/wopal-plugin/src/tasks/task-monitor.ts`, `.wopal/wopal-plugin/src/tools/output-helpers.ts`, `.wopal/wopal-plugin/src/session-runtime-info.ts`, `.wopal/wopal-plugin/src/tools/memory-manage/crud.ts`, `.wopal/wopal-plugin/src/tools/memory-manage/query-helpers.ts`, 相关测试文件

**Pre-read**: `.wopal/wopal-plugin/src/hooks/memory-message-injector.ts`, `.wopal/wopal-plugin/src/tasks/task-monitor.ts`, `.wopal/wopal-plugin/src/tools/output-helpers.ts`, `.wopal/wopal-plugin/src/tools/memory-manage/crud.ts`, `.wopal/wopal-plugin/src/memory/store.ts`

**Design**:
创建 `session-runtime-info.ts`，统一提供 session model、context usage、session role / child detection 的查询与格式化入口；将 `memory-message-injector.ts` 里的共享 pipeline 抽成可复用流程（gate → child skip → empty skip → enriched query → timeout guard → formatted inject），但严格保持 messages-only 路径，不重新引入 system 注入；同时提取 `loadAllMemories`、`resolveMemoryByShortId`、`mergeSearchResults` 等 helper，统一处理全表扫描、短 ID 命中和结果去重。`crud.ts` 仅保留 command-level orchestration，`task-monitor.ts` 与 `output-helpers.ts` 改为复用共享 runtime 查询。

**TDD**: true

**Changes**:
1. 为 memory 注入、context usage 查询和 memory-manage list/stats/delete/update/search 的现状行为补齐/锁定测试。
2. 创建 `session-runtime-info.ts`，统一 session model/context/session role 查询入口，并让 `task-monitor.ts`、`output-helpers.ts` 消费该入口。
3. 从 `memory-message-injector.ts` 中提取共享注入 pipeline，明确仅保留 messages 注入链路。
4. 创建 `query-helpers.ts`，提取全表扫描、短 ID 解析、结果去重等共享逻辑。
5. 重写 `crud.ts` 内各 handler，改为复用 helper，删除重复扫描片段。

**Verify**:
`cd .wopal/wopal-plugin && bun run test:run src/hooks/memory.test.ts src/tasks/task-monitor.test.ts src/tools/wopal-task-output.test.ts src/tools/memory-manage && bun run build && rg -n "searchByQuery\(\"\", 1000, \"like\", \[\"text\"\]\)" src/tools/memory-manage`

**Done**:
任务产出：共享 runtime 查询与 memory 注入流程已收束，memory-manage 重复查询已消除
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

### Task 2: 批次 B — 收敛 task phase / runtime client 边界并消除残余类型逃逸

**Verification Intent**: AC#1, AC#2, AC#4

**Behavior**: `wopal_task_output`、`wopal_task_reply`、delete/close、manager lifecycle 对 idle / waiting / running / error 的显示与可恢复语义保持一致；`context_manage`、`event-router`、`simple-task-manager` 继续能访问相同的 OpenCode session/config 能力，但目标文件不再暴露新的 `client: any` 或 `as any` 用法。

**Files**: `.wopal/wopal-plugin/src/types.ts`, `.wopal/wopal-plugin/src/tasks/task-phase.ts`, `.wopal/wopal-plugin/src/tasks/simple-task-manager.ts`, `.wopal/wopal-plugin/src/tasks/task-lifecycle.ts`, `.wopal/wopal-plugin/src/tools/wopal-task-output.ts`, `.wopal/wopal-plugin/src/tools/wopal-task-reply.ts`, `.wopal/wopal-plugin/src/tools/context-manage.ts`, `.wopal/wopal-plugin/src/hooks/event-router.ts`, 相关测试文件

**Pre-read**: `.wopal/wopal-plugin/src/types.ts`, `.wopal/wopal-plugin/src/tasks/simple-task-manager.ts`, `.wopal/wopal-plugin/src/tasks/task-lifecycle.ts`, `.wopal/wopal-plugin/src/tools/wopal-task-output.ts`, `.wopal/wopal-plugin/src/tools/wopal-task-reply.ts`, `.wopal/wopal-plugin/src/tools/context-manage.ts`, `.wopal/wopal-plugin/src/hooks/event-router.ts`

**Design**:
创建 `tasks/task-phase.ts`，统一提供 `isIdleTask()`、`isResumableTask()`、`getDisplayStatus()`、`canDeleteTask()` 等 helper，消除 scattered `idleNotified` / resumable / delete eligibility 判断；同时在 `types.ts` 扩充最小 runtime client 接口与 event payload narrowing helper，消除当前 `any`/`as any` 的 SDK 边界逃逸。目标是让 manager / lifecycle / output / reply / router 共享一套状态语义与类型边界。

**TDD**: true

**Changes**:
1. 为 idle / waiting / running / error 的显示、reply、delete 与 session status 主路径补齐回归测试。
2. 创建 `tasks/task-phase.ts`，统一 idle/resumable/display/delete 状态判定。
3. 更新 `simple-task-manager.ts`、`task-lifecycle.ts`、`wopal-task-output.ts`、`wopal-task-reply.ts` 改用 task phase helper。
4. 在 `types.ts` 增补最小 client/event 类型与 narrowing helper。
5. 改写 `context-manage.ts`、`event-router.ts`、`simple-task-manager.ts` 的 runtime 边界，移除残余 `any` / `as any`。

**Verify**:
`cd .wopal/wopal-plugin && bun run test:run src/tools/wopal-task-output.test.ts src/tools/wopal-task-reply.test.ts src/tasks/simple-task-manager.test.ts src/tasks/task-launcher.test.ts && bun run build && rg -n "client: any|as any" src/tools/context-manage.ts src/hooks/event-router.ts src/tasks/simple-task-manager.ts`

**Done**:
任务产出：task phase helper 与 runtime client 边界已统一，残余类型逃逸已清除
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

### Task 3: 拆分 context-manage 为薄入口与 action handlers

**Verification Intent**: AC#1, AC#2, AC#5

**Behavior**: `context_manage` 的 `status`、`dump`、`summary`、`compact` 四个 action 的输入输出、错误文案和跨 session 解析行为保持不变，但入口文件缩减为工具定义 + action 分发。

**Files**: `.wopal/wopal-plugin/src/tools/context-manage.ts`, `.wopal/wopal-plugin/src/tools/context-manage-actions.ts`, `.wopal/wopal-plugin/src/tools/context-target.ts`, `.wopal/wopal-plugin/src/tools/context-manage.test.ts`

**Pre-read**: `.wopal/wopal-plugin/src/tools/context-manage.ts`, `.wopal/wopal-plugin/src/hooks/session-utils.ts`, `.wopal/wopal-plugin/src/session-ref.ts`

**Design**:
保留 `createContextManageTool()` 作为唯一注册入口，将 `resolveSessionTarget` 和四条 action handler 下沉。入口只负责 schema、依赖注入、switch 分发。各 handler 保持纯函数或最小副作用，减少未来再度膨胀。测试重点锁定 raw `ses_` / `wopal-task-*` 解析、main/child status 差异、compact 输出。

**TDD**: true

**Changes**:
1. 先补齐 `context-manage.test.ts` 对四个 action 的现状行为断言。
2. 提取 target resolver 与 action handlers，新文件承载具体实现。
3. 将 `context-manage.ts` 缩减为薄入口并迁移测试导入。

**Verify**:
`cd .wopal/wopal-plugin && bun run test:run src/tools/context-manage.test.ts && python - <<'PY'
from pathlib import Path
p = Path('src/tools/context-manage.ts')
print(p.read_text().count('\n') + 1)
PY`

**Done**:
任务产出：context_manage 已完成结构拆分，入口文件降为薄编排层
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

### Task 4: 批次 C — 拆分 event-router、task-monitor 与相关通知编排模块

**Verification Intent**: AC#1, AC#2, AC#5

**Behavior**: 任务 token 记录、idle 通知、compact 恢复、question/permission relay、stuck/progress 检测的对外行为保持一致，但 `event-router.ts` 与 `task-monitor.ts` 各自只保留公共装配和导出，具体处理逻辑下沉。

**Files**: `.wopal/wopal-plugin/src/hooks/event-router.ts`, `.wopal/wopal-plugin/src/hooks/event-token-handler.ts`, `.wopal/wopal-plugin/src/hooks/event-compact-recovery.ts`, `.wopal/wopal-plugin/src/hooks/event-error-handler.ts`, `.wopal/wopal-plugin/src/hooks/events/*.ts`, `.wopal/wopal-plugin/src/tasks/task-monitor.ts`, `.wopal/wopal-plugin/src/tasks/context-usage.ts`, `.wopal/wopal-plugin/src/tasks/progress-notify.ts`, `.wopal/wopal-plugin/src/tasks/progress.ts`, `.wopal/wopal-plugin/src/tasks/task-notifier.ts`, `.wopal/wopal-plugin/src/tasks/question-relay.ts`, `.wopal/wopal-plugin/src/tasks/permission-proxy.ts`, 相关测试文件

**Pre-read**: `.wopal/wopal-plugin/src/hooks/event-router.ts`, `.wopal/wopal-plugin/src/tasks/task-monitor.ts`, `.wopal/wopal-plugin/src/tasks/simple-task-manager.ts`

**Design**:
将 `event-router` 按事件职责拆分：message/token、idle、compacted、question/permission relay、error routing。将 `task-monitor` 按监控职责拆分：context usage 读取、progress notify 计算、stuck 检测，并同步收敛 `progress.ts` / `task-notifier.ts` 的编排边界。公共导出与依赖注入仍从原入口暴露，避免大面积改 import。测试需要覆盖 task idle、compact auto-continue、question/permission relay、context usage fallback、stuck notify 主路径。

**TDD**: true

**Changes**:
1. 先为 event-router 与 task-monitor 的关键路径补齐回归测试。
2. 抽离 message/token、idle/compacted、question/permission、error、context/progress 处理模块，迁移实现代码。
3. 收敛 `progress.ts` / `task-notifier.ts` 相关编排边界，减少 event-router 与 task-monitor 对细节实现的耦合。
4. 收敛原入口文件为装配层，更新相关导入与测试。

**Verify**:
`cd .wopal/wopal-plugin && bun run test:run src/hooks/event-router.test.ts src/tasks/task-monitor.test.ts src/tasks/simple-task-manager.test.ts src/tasks/progress.test.ts src/tasks/question-relay.test.ts src/tasks/permission-proxy.test.ts && python - <<'PY'
from pathlib import Path
for rel in ['src/hooks/event-router.ts', 'src/tasks/task-monitor.ts']:
    p = Path(rel)
    print(rel, p.read_text().count('\n') + 1)
PY`

**Done**:
任务产出：event-router 与 task-monitor 已拆为装配层 + 运行时 handler/helper 模块
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

## Delegation Strategy

| Wave | Task | 执行者 | 依赖 | 委派理由 |
|------|------|--------|------|---------|
| 1 | Task 1 | fae | 无 | 先建立 session-runtime-info 与 memory 注入共享 pipeline，为后续 runtime 拆分提供稳定契约 |
| 1 | Task 2 | fae | 无 | 先统一 task phase 与 runtime client 边界，避免后续拆分期间状态语义漂移 |
| 2 | Task 3 | fae | Task 1, Task 2 | context-manage 拆分依赖共享 runtime info 与统一类型边界 |
| 2 | Task 4 | fae | Task 1, Task 2 | event-router/task-monitor 拆分同样依赖共享 runtime info 与 task phase 语义 |

Wave 1 先解决共享 runtime、memory pipeline 与状态边界；Wave 2 再进行大文件拆分，避免边拆边改语义导致回归难定位。每个 wave 完成后由 Wopal 运行对应 Verify 命令并确认未引入新行为差异，再释放下一 wave。

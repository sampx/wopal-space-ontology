# refactor-wopal-plugin-simplify-wopal_task-status-model

## Metadata

- **Type**: refactor
- **Target Project**: wopal-space-ontology
- **Project Path**: .wopal
- **Project Type**: ontology-worktree
- **Created**: 2026-05-23
- **Status**: done
- **MainBranch**: space/main
- **Worktree**: plugin-simplify-wopal_task-status-model | /Users/sam/coding/wopal/wopal-workspace/.worktrees/ontology-plugin-simplify-wopal_task-status-model

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

简化 `wopal_task` 任务状态语义与状态机，删除无价值的 `pending`，将当前复杂且误导性的 stuck/error 判断收敛为可解释、可恢复、低复杂度的停止分类逻辑，同时保留已验证可用的 `question.asked` relay 机制。`error` 仅保留给“未进入可恢复 assistant 执行链”的不可恢复失败。

## Technical Context

### Architecture Context

`wopal-plugin` 的任务状态目前由多个模块共同维护：

- `types.ts` 定义 `pending | running | waiting | error`。
- `task-phase.ts` 通过 `idleNotified` 把 `running` 二次解释为隐藏的 `idle` phase。
- `task-monitor.ts` 用 no-activity/stuck timeout 推测 stuck。
- `error-handler.ts` 将部分 `session.error` 映射为 task error。
- `question-relay.ts` 将子会话 native question relay 到主会话。

该模型的问题：

1. `pending` 只是 launch 中的瞬时实现细节，不表达主控可执行动作。
2. `running + idleNotified` 把真实的 `idle` 藏成组合状态，导致工具、通知、tick、删除/恢复规则分散判断。
3. 原 `error` 语义过宽：可恢复的“异常停止但仍可 reply/finish”应叫 `stuck`；未进入 assistant 执行链、无法 reply 恢复的失败才应叫 `error`。
4. 当前 stuck 判断混合了运行中 no-activity、session error、idle 后等待判断等多个概念，容易误报。
5. `question.asked` relay 已验证能触发 `[WOPAL TASK QUESTION]`，并能通过 question reply 路径恢复；该机制应保留，而不是纳入本次清理范围删除。

目标状态模型：

- `running`: 子会话当前正在推进一轮 prompt，占用执行槽。
- `idle`: 子会话停止推进，且本轮产生了新的非 synthetic assistant text；主控可 output/reply/finish。
- `waiting`: 子会话触发 native `question.asked`，正在等待 question reply；保留给开启 question 权限的子代理使用。
- `stuck`: 子会话已出现 assistant 执行证据（任意 assistant part、工具调用、text delta 等），停止时本轮没有新的非 synthetic assistant text；主控可 output/reply/finish。
- `error`: 子会话未出现 assistant 执行证据即失败（例如 agent 不存在）；主控可 output/finish，不可 reply。

### Research Findings

会话内验证结论：

1. native question path：fae 使用 question 工具时，插件能收到 `question.asked` 并发送 `[WOPAL TASK QUESTION]`；当前机制可用，应保留。
2. plain text question path：禁用 fae question 工具后，fae 输出普通 `[QUESTION]` 文本并自然触发 `[WOPAL TASK IDLE]`，没有 TUI select box；这是 fae 当前配置下的推荐交互方式，但不属于本 Plan 的实现范围。
3. 状态机优化应聚焦：显式 idle、移除 pending、用 stuck 取代 error、降低 stuck 判断复杂度、保留 waiting/question relay 的兼容能力。

**参考资料**：
- `.wopal/plugins/wopal-plugin/src/types.ts`
- `.wopal/plugins/wopal-plugin/src/tasks/task-phase.ts`
- `.wopal/plugins/wopal-plugin/src/tasks/task-launcher.ts`
- `.wopal/plugins/wopal-plugin/src/tasks/task-lifecycle.ts`
- `.wopal/plugins/wopal-plugin/src/tasks/task-monitor.ts`
- `.wopal/plugins/wopal-plugin/src/tasks/task-notifier.ts`
- `.wopal/plugins/wopal-plugin/src/tasks/question-relay.ts`
- `.wopal/plugins/wopal-plugin/src/hooks/events/idle-compact-handler.ts`
- `.wopal/plugins/wopal-plugin/src/hooks/events/error-handler.ts`
- `.wopal/plugins/wopal-plugin/src/tools/wopal-task-reply.ts`
- `.wopal/plugins/wopal-plugin/src/tasks/session-messages.ts`

### Key Decisions

- D-01: 目标状态为 `running | idle | waiting | stuck | error`；保留 `waiting` 仅用于 native question relay。
- D-02: 删除 `pending`；launch 未成功不入 task 表，launch 成功即 `running`。
- D-03: 删除 `idleNotified`；`idle` 作为显式状态存储，避免组合字段判断。
- D-04: `error` 只表示未进入可恢复 assistant 执行链的不可恢复失败；异常停止但可恢复的状态统一命名为 `stuck`。
- D-05: `stuck` 不再由运行中 no-activity 定时器推测，而由停止事件分类产生：停止时本轮无新 assistant text，且已有 assistant 执行证据。
- D-06: 保留 `question.asked` relay、`pendingQuestionID` 与 `waiting`，因为它们服务已验证可用的 native question 权限场景。
- D-07: 不把“禁用 question 工具”纳入本 Plan；该工作已由用户完成，不应在计划中重复实现。

### Key Interfaces

目标类型：

```ts
export type WopalTaskStatus = "running" | "idle" | "waiting" | "stuck" | "error"
```

关键字段保留/删除：

```ts
interface WopalTask {
  status: WopalTaskStatus
  lastAssistantMessage?: string
  pendingQuestionID?: string // retained for native question relay
  // removed: idleNotified, waitingReason, error/completedAt-as-state-driver
}
```

停止分类规则：

```text
on stop event for running/waiting task:
  latest = latest non-synthetic assistant text
  evidence = any assistant execution evidence (assistant part/tool/text delta/previous assistant text)
  if latest exists and latest !== task.lastAssistantMessage:
    task.lastAssistantMessage = latest
    status = idle
  else if evidence exists:
    status = stuck
  else:
    status = error
```

question relay 规则：

```text
question.asked from child session:
  status = waiting
  pendingQuestionID = requestID
  send [WOPAL TASK QUESTION]

wopal_task_reply on waiting with pendingQuestionID:
  question.reply(requestID, message)
  status = running
```

## In Scope

- 将 `WopalTaskStatus` 从 `pending | running | waiting | error` 收敛为 `running | idle | waiting | stuck | error`，其中 `error` 语义收窄为不可恢复失败。
- 删除 `pending` 状态及其生产代码分支、工具文案、测试边界。
- 删除 `idleNotified` 隐藏 phase，改用显式 `idle` 状态。
- 收窄 `error` 状态，改用 `stuck` 表达“已有 assistant 执行证据但异常停止且仍可恢复/删除”。
- 重构 `session.idle`、`session.error`、`promptAsync` reject 的停止处理，统一分类为 `idle`、`stuck` 或 `error`。
- 清理/移除当前基于 no-activity timeout 的 stuck 误判逻辑，避免运行中任务被推测成 stuck。
- 保留并整理 `question.asked` relay 机制：`waiting` 只表示 native question 等待回复，不参与 stuck/error 判断。
- 更新 `wopal_task_reply`、`finish`、`abort`、`output`、`context_manage status`、tick 日志、通知文案和测试。
- 更新 `agents-collab` skill 中过时的任务状态说明。

## Out of Scope

- 不禁用 question 工具；该配置工作已由用户完成。
- 不删除 `question-relay.ts` 或 native question reply 机制。
- 不恢复旧的泛化 `error` 状态；`error` 仅用于未进入 assistant 执行链、不可 reply 恢复的任务级失败。
- 不改变 task 并发上限、TTL、非阻塞启动机制。
- 不改变 fae/rook agent 权限文件。

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| Task types | `.wopal/plugins/wopal-plugin/src/types.ts` | 修改 | 收敛 status union，删除 idle/error 旧字段依赖 |
| Phase helpers | `.wopal/plugins/wopal-plugin/src/tasks/task-phase.ts`, `.test.ts` | 修改 | 定义 active/resumable/deletable/display 规则 |
| Launcher | `.wopal/plugins/wopal-plugin/src/tasks/task-launcher.ts`, `.test.ts` | 修改 | 删除 pending，launch 成功即 running |
| Lifecycle | `.wopal/plugins/wopal-plugin/src/tasks/task-lifecycle.ts`, `.test.ts` | 修改 | abort/finish/recover 改为 idle/stuck/waiting 语义 |
| Stop classifier | `.wopal/plugins/wopal-plugin/src/tasks/task-stop-classifier.ts`, `.test.ts` | 创建 | 统一停止分类 idle/stuck |
| Event handlers | `.wopal/plugins/wopal-plugin/src/hooks/events/idle-compact-handler.ts`, `error-handler.ts`, `event-router.ts`, `.test.ts` | 修改 | idle/error/reject 事件统一走停止分类；question relay 保留 |
| Question relay | `.wopal/plugins/wopal-plugin/src/tasks/question-relay.ts`, tests | 修改 | 保留 waiting/pendingQuestionID；删除 waitingReason 依赖 |
| Tools | `.wopal/plugins/wopal-plugin/src/tools/wopal-task-reply.ts`, `wopal-task-finish.ts`, `wopal-task-abort.ts`, `wopal-task-output.ts`, tests | 修改 | 操作对象改为 running/idle/waiting/stuck |
| Monitor/notify | `.wopal/plugins/wopal-plugin/src/tasks/task-monitor.ts`, `task-monitor-strategy.ts`, `task-notifier.ts`, tests | 修改 | 清理旧 stuck timeout，更新 tick 与通知 |
| Manager/status | `.wopal/plugins/wopal-plugin/src/tasks/simple-task-manager.ts`, `.wopal/plugins/wopal-plugin/src/tools/context-manage.ts`, tests | 修改 | status listing 与恢复/删除规则统一 |
| Skill docs | `.wopal/skills/agents-collab/SKILL.md` | 修改 | 更新子任务状态机说明 |
| Plugin project docs | `.wopal/plugins/wopal-plugin/AGENTS.md` | 修改 | 更新任务模块说明、错误处理章节中的旧状态语义 |

## Acceptance Criteria

### Agent Verification

1. [x] `cd .wopal/plugins/wopal-plugin && bun run typecheck` → exit 0
2. [x] `cd .wopal/plugins/wopal-plugin && bun run test:run` → all tests pass
3. [x] `cd .wopal/plugins/wopal-plugin && rg "export type WopalTaskStatus" src/types.ts` → exactly one definition containing `running`, `idle`, `waiting`, `stuck`, `error` and not containing `pending`
4. [x] `cd .wopal/plugins/wopal-plugin && rg "idleNotified|waitingReason" src` → no production-code matches
5. [x] `cd .wopal/plugins/wopal-plugin && rg "status:\s*['\"]pending['\"]|status\s*=\s*['\"]pending['\"]" src` → no production-code matches
6. [x] `cd .wopal/plugins/wopal-plugin && rg "question-relay|pendingQuestionID" src` → production references still exist for native question relay
7. [x] `cd .wopal/plugins/wopal-plugin && rg "\[WOPAL TASK STUCK\]" src/tasks/task-notifier.ts` → ≥ 1 match (动态生成 task.status.toUpperCase())
8. [x] `cd .wopal/plugins/wopal-plugin && rg "DEFAULT_STUCK_TIMEOUT_MS|checkStuckTasks" src` → no production-code matches, or remaining matches are renamed away from stuck semantics
9. [x] `.wopal/skills/dev-flow/scripts/flow.sh plan refactor-wopal-plugin-simplify-wopal_task-status-model --check` → plan validation pass

### User Validation

#### Scenario 1: 普通子任务完成后显示 idle
- Goal: 确认正常完成的子任务不再显示 `running + idleNotified` 或 error，而是显式 `idle`。
- Precondition: 本计划实现已部署到当前 Ellamaka runtime。
- User Actions:
  1. Wopal 启动一个 fae 验证任务，要求 fae 输出一段普通文本后停止。
  2. 观察主会话通知与 `context_manage status`。
- Expected Result: 主会话收到 `[WOPAL TASK IDLE]`，task status 显示 `idle`，Result 中包含 fae 输出文本。

#### Scenario 2: 未进入 assistant 执行链的失败显示 error
- Goal: 确认启动/配置级失败（如 agent 不存在）被标记为 `error`，不会误报为可恢复 `stuck`。
- Precondition: 本计划实现已部署到当前 Ellamaka runtime。
- User Actions:
  1. Wopal 使用不存在的 agent 发起子任务。
  2. 观察主会话通知与 `context_manage status`。
  3. 让 Wopal 执行 `wopal_task_reply` 与 `wopal_task_finish`。
- Expected Result: task 显示 `error`，通知为 `[WOPAL TASK ERR]`；reply 被拒绝，finish 可删除任务。

#### Scenario 2b: 已有 assistant 执行证据但无新 text 显示 stuck
- Goal: 确认已有 assistant part / 工具调用 / text delta 的任务在停止时无新 assistant text 才标记为 `stuck`。
- Precondition: 存在可模拟已有 assistant 执行证据后停止且无新 text 的路径。
- Expected Result: task 显示 `stuck`，通知为 `[WOPAL TASK STUCK]`；reply 可恢复为 `running`，finish 可删除任务。

#### Scenario 3: native question relay 仍然可用
- Goal: 确认开启 question 工具权限的子代理仍可触发 question relay，不被本次状态机重构破坏。
- Precondition: 临时使用一个允许 question 工具的子代理或测试夹具。
- User Actions:
  1. 子代理触发 question。
  2. 观察主会话收到 `[WOPAL TASK QUESTION]` 或 TUI question UI。
  3. 通过 question reply 路径回复。
- Expected Result: task 进入 `waiting`；回复后恢复 `running`；子任务继续完成后进入 `idle` 或 `stuck`。

- [x] 用户已完成上述功能验证并确认结果符合预期

## Implementation

### Task 1: Redefine task status and helper semantics

**Verification Intent**: AC#1, AC#2, AC#3, AC#4

**Behavior**: 生产代码中任务状态只有 `running | idle | waiting | stuck | error`；`running` 是唯一 active 状态，`idle/waiting/stuck` 可恢复，`error` 不可恢复但可删除。

**Files**: `.wopal/plugins/wopal-plugin/src/types.ts`, `.wopal/plugins/wopal-plugin/src/tasks/task-phase.ts`, `.wopal/plugins/wopal-plugin/src/tasks/task-phase.test.ts`, `.wopal/plugins/wopal-plugin/src/tools/pending-boundary.test.ts`

**Pre-read**: `.wopal/plugins/wopal-plugin/src/types.ts`, `.wopal/plugins/wopal-plugin/src/tasks/task-phase.ts`

**Design**:

1. 将 `WopalTaskStatus` 改为 `"running" | "idle" | "waiting" | "stuck" | "error"`。
2. 删除 `idleNotified`、`waitingReason` 字段；保留 `pendingQuestionID` 用于 native question relay。
3. 重写 helper：
   - `isTaskActive`: 仅 `running`。
   - `isResumableTask`: `idle | waiting | stuck`。
   - `canDeleteTask`: `idle | waiting | stuck | error`。
   - `getDisplayStatus`: 直接返回 `task.status`。
4. 将 pending-boundary 测试重构为四态边界测试；如保留文件名，测试内容必须脱离 pending 语义。

**TDD**: true

**Changes**:
1. RED: 先更新 helper 测试为四态矩阵，确认旧实现失败。
2. GREEN: 修改类型与 helper 使测试通过。
3. REFACTOR: 删除旧注释和旧字段夹具。

**Verify**:
`cd .wopal/plugins/wopal-plugin && bun run test:run -- src/tasks/task-phase.test.ts src/tools/pending-boundary.test.ts`

**Done**:
任务产出：任务状态类型与 helper 已收敛为 `running | idle | waiting | stuck | error`。
勾选验收：AC#3, AC#4 | Checklist#1, Checklist#2
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

### Task 2: Remove pending/error lifecycle branches

**Verification Intent**: AC#1, AC#2, AC#3, AC#5

**Behavior**: launch 成功即 `running`，失败不留下 `pending` task；异常停止交由 Task 3 分类为 `idle/stuck/error`。

**Files**: `.wopal/plugins/wopal-plugin/src/tasks/task-launcher.ts`, `.wopal/plugins/wopal-plugin/src/tasks/task-lifecycle.ts`, `.wopal/plugins/wopal-plugin/src/tasks/simple-task-manager.ts`, `.wopal/plugins/wopal-plugin/src/tools/wopal-task-finish.ts`, `.wopal/plugins/wopal-plugin/src/tools/wopal-task-abort.ts`, related tests

**Pre-read**: `.wopal/plugins/wopal-plugin/src/tasks/task-launcher.ts`, `.wopal/plugins/wopal-plugin/src/tasks/task-lifecycle.ts`, `.wopal/plugins/wopal-plugin/src/tasks/simple-task-manager.ts`

**Design**:

1. `launchTask` 删除 `pending` 写入：创建 session 后直接构造 `running` task；如果 `promptAsync` 不能启动，清理 session 并返回 launch failure，不保留 task。
2. 删除 `failTask` 将 task 标记为 `error` 的路径；保留必要的 abort/session cleanup 辅助函数。
3. `wopal_task_abort` 对 active `running` 执行 abort 后将任务置为 `idle`，释放并发槽。
4. `finishTask` 允许删除 `idle/waiting/stuck/error`，拒绝 active `running`。
5. `recoverFromSession` 恢复历史子会话时默认 `idle`，因为恢复出的会话不是当前 active run。

**TDD**: true

**Changes**:
1. RED: 更新 launcher/lifecycle/finish/abort/simple-task-manager 测试到新状态语义。
2. GREEN: 修改生命周期代码，删除 pending/error 分支。
3. REFACTOR: 清理旧错误文案、旧测试 fixture 和 completedAt-as-state-driver。

**Verify**:
`cd .wopal/plugins/wopal-plugin && bun run test:run -- src/tasks/task-launcher.test.ts src/tasks/simple-task-manager.test.ts src/tools/wopal-task-finish.test.ts src/tools/wopal-task-abort.test.ts`

**Done**:
任务产出：launch、finish、abort 生命周期已删除 pending/error 状态分支。
勾选验收：AC#5 | Checklist#2
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

### Task 3: Replace stuck/error heuristics with stop classification

**Verification Intent**: AC#1, AC#2, AC#5, AC#7, AC#8

**Behavior**: 任何停止事件都通过同一分类器判断：本轮有新 assistant text → `idle`；无新 text 但已有 assistant 执行证据 → `stuck`；未进入 assistant 执行链即失败 → `error`。运行中 no-activity 不再直接产生 stuck 状态或 STUCK 通知。

**Files**: `.wopal/plugins/wopal-plugin/src/tasks/task-stop-classifier.ts`, `.wopal/plugins/wopal-plugin/src/tasks/task-monitor.ts`, `.wopal/plugins/wopal-plugin/src/tasks/task-notifier.ts`, `.wopal/plugins/wopal-plugin/src/hooks/events/idle-compact-handler.ts`, `.wopal/plugins/wopal-plugin/src/hooks/events/error-handler.ts`, `.wopal/plugins/wopal-plugin/src/tasks/task-launcher.ts`, related tests

**Pre-read**: `.wopal/plugins/wopal-plugin/src/tasks/session-messages.ts`, `.wopal/plugins/wopal-plugin/src/tasks/notification-summary.ts`, `.wopal/plugins/wopal-plugin/src/tasks/task-monitor.ts`, `.wopal/plugins/wopal-plugin/src/hooks/events/error-handler.ts`

**Design**:

1. 新增 `task-stop-classifier.ts`，集中实现 assistant text 分类。
2. `session.idle` 对 `running` 或 `waiting` task 调 classifier，设置 `idle/stuck/error`，释放并发槽并通知父会话。
3. `session.error` 过滤 `MessageAbortedError` 后调用 classifier；若无 assistant text 但有执行证据，进入 `stuck`；若无执行证据，进入 `error`。
4. `promptAsync.catch` 对仍 active 的 task 调 classifier，避免旧 async reject 覆盖已停止/已恢复任务。
5. 删除或重命名 `checkStuckTasks` / `DEFAULT_STUCK_TIMEOUT_MS` 等 no-activity stuck 逻辑；如仍保留运行中进度提醒，必须改成 progress/no-activity 文案，不得使用 stuck 语义。
6. `[WOPAL TASK STUCK]` 文案改为“任务已有 assistant 执行证据但本轮没有新的 assistant text”，并提示可 `output/reply/finish`；`[WOPAL TASK ERR]` 只提示 `output/finish`。

**TDD**: true

**Changes**:
1. RED: 增加 classifier 测试，覆盖新 assistant text、无 assistant text、assistant text 未变化、messages 拉取失败、waiting 后 idle。
2. GREEN: 接入 idle/error/reject 停止事件。
3. REFACTOR: 删除旧 stuck timeout 与 error 状态路径。

**Verify**:
```bash
cd .wopal/plugins/wopal-plugin && bun run test:run -- src/tasks/task-stop-classifier.test.ts src/tasks/task-monitor.test.ts src/tasks/task-notifier.test.ts src/hooks/event-router.test.ts src/tasks/task-launcher.test.ts
# Explicit stop-classification coverage (>= 1 match each)
rg "classifyTaskStop|task-stop-classifier" src/tasks src/hooks --type ts -c
# Ensure all three stop entry points are integrated (>= 1 match each file)
rg "classifyTaskStop" src/hooks/events/idle-compact-handler.ts src/hooks/events/error-handler.ts src/tasks/task-launcher.ts --type ts -c
# No legacy pending/failTask path remains in production code (strict exit 1 on match)
! rg "status:\s*['\"]pending['\"]|status\s*=\s*['\"]pending['\"]|failTask" src --type ts -g '!**/*.test.ts'
```

**Done**:
任务产出：stuck/error 旧判断已被统一停止分类替代。
勾选验收：AC#7, AC#8 | Checklist#4, Checklist#5
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

### Task 4: Preserve and simplify question relay handling

**Verification Intent**: AC#1, AC#2, AC#4, AC#6

**Behavior**: `question.asked` relay 机制保留；触发 question 时 task 进入 `waiting`，可通过 `wopal_task_reply` 的 `question.reply` 分支恢复；若用户通过 TUI/native path 回复，后续停止事件也能正确转入 `idle/stuck/error`。

**Files**: `.wopal/plugins/wopal-plugin/src/tasks/question-relay.ts`, `.wopal/plugins/wopal-plugin/src/hooks/event-router.ts`, `.wopal/plugins/wopal-plugin/src/tools/wopal-task-reply.ts`, related tests

**Pre-read**: `.wopal/plugins/wopal-plugin/src/tasks/question-relay.ts`, `.wopal/plugins/wopal-plugin/src/tools/wopal-task-reply.ts`, `.wopal/plugins/wopal-plugin/src/hooks/event-router.ts`

**Design**:

1. `handleQuestionAsked` 保留 child session relay：设置 `status = "waiting"`、保存 `pendingQuestionID`、发送 `[WOPAL TASK QUESTION]`。
2. 删除 `waitingReason`，因为 `waiting` 只表达一种语义：native question 等待回复。
3. `wopal_task_reply` 对 `waiting + pendingQuestionID` 保留 `question.reply` 路径；成功后设为 `running`。
4. 停止分类器必须接受 `waiting` task 的后续 `session.idle/session.error`，避免 TUI/native reply 后状态卡在 waiting。
5. 保留 event-router 的 `question.asked` 分支；只清理旧文案与旧字段。

**TDD**: true

**Changes**:
1. RED: 更新 question-relay 与 wopal-task-reply 测试，要求 waiting 保留但 waitingReason 删除。
2. GREEN: 修改 question relay 与 reply 分支。
3. REFACTOR: 确保 question relay 没有引入 pending/error/idleNotified 旧语义。

**Verify**:
```bash
cd .wopal/plugins/wopal-plugin && bun run test:run -- src/hooks/event-router.test.ts src/tasks/question-relay.test.ts src/tools/wopal-task-reply.test.ts
# pendingQuestionID preserved (>= 1 match each file)
rg "pendingQuestionID" src/tasks/question-relay.ts src/tools/wopal-task-reply.ts --type ts -c
# waitingReason removed from production code (strict exit 1 on match)
! rg "waitingReason" src --type ts -g '!**/*.test.ts'
# question.reply path exists (>= 1 match)
rg "question\.reply" src/tools/wopal-task-reply.ts --type ts -c
```

**Done**:
任务产出：native question relay 保留并对齐新状态模型。
勾选验收：AC#6 | Checklist#3
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

### Task 5: Update user-visible outputs and collaboration docs

**Verification Intent**: AC#1, AC#2, AC#3, AC#4, AC#5, AC#6, AC#7, AC#8, AC#9

**Behavior**: 所有用户可见输出、tick 日志、通知和协作文档统一使用 `running | idle | waiting | stuck | error`，不再传播 pending/idleNotified 旧模型；`error` 仅表达不可恢复失败。

**Files**: `.wopal/plugins/wopal-plugin/src/tasks/task-monitor.ts`, `.wopal/plugins/wopal-plugin/src/tasks/task-monitor-strategy.ts`, `.wopal/plugins/wopal-plugin/src/tools/wopal-task-output.ts`, `.wopal/plugins/wopal-plugin/src/tools/context-manage.ts`, `.wopal/skills/agents-collab/SKILL.md`, `.wopal/plugins/wopal-plugin/AGENTS.md`, related tests

**Pre-read**: `.wopal/plugins/wopal-plugin/src/tasks/task-monitor.ts`, `.wopal/plugins/wopal-plugin/src/tools/wopal-task-output.ts`, `.wopal/plugins/wopal-plugin/src/tools/context-manage.ts`, `.wopal/skills/agents-collab/SKILL.md`, `.wopal/plugins/wopal-plugin/AGENTS.md`

**Design**:

1. `formatTaskTickLines` 直接显示 `task.status`，覆盖所有 task。
2. `context_manage status` 和 `wopal_task_output` 显示五态，并针对 `waiting/stuck/error` 给出正确操作建议。
3. `notifyParent` 发送 `[WOPAL TASK IDLE]`、`[WOPAL TASK WAITING]`、`[WOPAL TASK STUCK]`、`[WOPAL TASK ERR]` 的文案与 Result/diagnostic 信息。
4. 更新 `agents-collab`：状态模型、通知处理、reply/finish/abort 决策树都改为新模型。
5. 更新 `wopal-plugin/AGENTS.md`：模块边界中的 `task-lifecycle.ts` 说明（删除 failTask）、诊断模块列表（更新/删除 error-classifier）、错误处理章节中的 `failTask() 标记 error 状态` 改为新 stuck 语义。
6. 执行全量 typecheck/test 与 Plan check。

**TDD**: true

**Changes**:
1. RED: 更新 output/status/tick/notifier/skill 文案测试。
2. GREEN: 修改输出与文档。
3. REFACTOR: 全仓搜索旧状态词，删除过时注释、测试名和误导性提示。

**Verify**:
```bash
cd .wopal/plugins/wopal-plugin && bun run typecheck && bun run test:run && cd /Users/sam/coding/wopal/wopal-workspace && .wopal/skills/dev-flow/scripts/flow.sh plan refactor-wopal-plugin-simplify-wopal_task-status-model --check
# agents-collab status vocabulary (>= 1 match)
rg "running\s*\|\s*idle\s*\|\s*waiting\s*\|\s*stuck\s*\|\s*error" .wopal/skills/agents-collab/SKILL.md -c
# agents-collab decision tree updated (>= 1 match)
rg "(reply|finish|abort).*\(idle|stuck|waiting\)" .wopal/skills/agents-collab/SKILL.md -c
# No legacy pending/idleNotified residue in user-visible production outputs (strict exit 1 on match)
! rg "(pending|idleNotified)" src/tools/context-manage.ts src/tools/wopal-task-output.ts src/tasks/task-notifier.ts src/tasks/task-monitor.ts --type ts -g '!**/*.test.ts'
# Plugin AGENTS.md no longer references old status semantics (strict exit 1 on match)
! rg "failTask|标记.*error.*状态|errorCategory" AGENTS.md
```

**Done**:
任务产出：用户可见输出与协作文档已统一到新状态模型。
勾选验收：AC#9 | Checklist#2, Checklist#5
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

## Delegation Strategy

| Wave | Task | 执行者 | 依赖 | 委派理由 |
|------|------|--------|------|---------|
| 1 | Task 1 | fae | 无 | 状态类型与 helper 是所有后续改动的基础，autonomous: true |
| 2 | Task 2 | fae | Task 1 | 生命周期分支依赖新 helper，autonomous: true |
| 3 | Task 4 | fae | Task 1, Task 2 | question relay 简化需新 status union 且不能与生命周期清理并行，autonomous: true |
| 4 | Task 3 | fae | Task 1, Task 2, Task 4 | 停止分类需要新生命周期和 waiting 兼容语义，autonomous: true |
| 5 | Task 5 | fae | Task 1-4 | 用户可见输出和文档必须最后统一，autonomous: true |

Wave 间门控：每个 wave 完成后，Wopal 必须执行以下检查：

1. 运行对应 Task 的 Verify 命令，确认 grep 断言全部满足
2. `git diff .wopal/plugins/wopal-plugin/src` 检查是否误改用户已完成的 agent question 权限配置
3. 执行 cross-task regression checklist（见下方）

## Implementation Notes

- 不要修改 `.wopal/agents/fae*.md`、`.wopal/agents/rook*.md` 中用户已完成的工具权限配置。
- `waiting` 是兼容 native question relay 的保留状态，不应扩展为泛化"等待用户输入"状态。
- `stuck` 是停止态，不是运行中推测态；运行中长时间无输出最多是 progress/no-activity 提醒，不应改变 task status。
- `error` 是未进入 assistant 执行链的不可恢复停止态；不可 reply，只能 output/finish 后重新创建 task。
- 所有停止态（`idle/waiting/stuck/error`）都应可 `finish`；`idle/stuck` 可普通 `promptAsync` reply；`waiting + pendingQuestionID` 优先走 `question.reply`。

## Cross-Task Regression Checklist

每个 Task 完成后必须验证以下跨任务一致性：

1. `WopalTaskStatus` union 稳定为 `running | idle | waiting | stuck | error`
   - `rg "export type WopalTaskStatus" src/types.ts`
2. `idleNotified`、`waitingReason`、`pending` 在生产代码中不存在（strict exit 1 on match）
   - `! rg "idleNotified|waitingReason|status:\s*['\"]pending['\"]" src --type ts -g '!**/*.test.ts'`
3. `pendingQuestionID` 在 `question-relay.ts` 与 `wopal-task-reply.ts` 中保留
   - `rg "pendingQuestionID" src/tasks/question-relay.ts src/tools/wopal-task-reply.ts -c`
4. 所有停止事件入口统一调用 `classifyTaskStop`
   - `rg "classifyTaskStop" src/hooks/events src/tasks/task-launcher.ts -c`
5. `[WOPAL TASK STUCK]` 文案改为新语义，`[WOPAL TASK ERR]` 用于不可恢复失败，且不存在 `[WOPAL TASK ERROR]` 文案（strict exit 1 on match for ERROR）
    - `rg "\[WOPAL TASK STUCK\]" src/tasks/task-notifier.ts -A 2`
    - `rg "\[WOPAL TASK ERR\]|status === 'error'" src/tasks/task-notifier.ts -c`
   - `! rg "\[WOPAL TASK ERROR\]" src/tasks/task-notifier.ts`

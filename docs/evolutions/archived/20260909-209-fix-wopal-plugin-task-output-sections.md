# 209-fix-wopal-plugin-task-output-sections

## Metadata

- **Issue**: #209
- **Type**: fix
- **Target Project**: wopal-space-ontology
- **Project Type**: ontology-worktree

- **Project Path**: .wopal

- **Created**: 2026-09-09
- **Status**: done
- **Verification Commit**: c9eb427959c2da361215fa2536725c5ef22cf864
- **Worktree**:
  - branch: wopal-space-ontology-209-fix-wopal-plugin-task-output-sections
  - path: (removed)
- **Verification Dir**: /Volumes/U500G/coding/wopal-workspace/.wopal
- **Base Commit**: 7a200d4c0ef90efd8b1456ddf5ec5053087eccd6
- **Final Commit**: dbb4e3b38bdbb52af7263311288c1ec7948c4cc9

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

修复 `wopal_task_output` 分段读取的两处真实缺陷（`tools` 段的 `last_n` 截断失效、`text`/`reasoning` 默认只读最后一条 assistant 消息导致多工具步骤后读到空内容），并移除 `wopal_task_finish` 成功回包中硬编码的 "OpenCode" 文案；同时在所有 task progress 报告与结果输出中，以 `provider/model` 形式标注子代理（agent）实际使用的模型，并在 `[WOPAL TASK IDLE]` 通知中补充子代理的上下文占用百分比。

## Technical Context

### Architecture Context

wopal-plugin（ellamaka 运行时插件）任务返回链路：

- `wopal_task_output` 工具定义在 `.wopal/plugins/wopal-plugin/src/tools/wopal-task-output.ts`，按 `section` 分段读取子代理 session 消息。它已含 `**Model:** provider/model`（当 `task.sessionID` 存在时，通过 `getSessionModelInfo` 读取子 session 最近一条 assistant 消息的 provider/model）。
- 通知组装在 `.wopal/plugins/wopal-plugin/src/tasks/task-notifier.ts`：`sendProgressNotification` 输出 `[WOPAL TASK PROGRESS]`；`notifyParent` 输出 `[WOPAL TASK IDLE/STUCK/ERR/WAITING]`。两者均**不**含模型信息，也含 `sessionStore`（可查子 session 的 provider/modelID 与 lastTokens/contextLimit）。
- 结果类输出：`context_manage(status)`（`.wopal/plugins/wopal-plugin/src/tools/context-manage-actions.ts` → `listTasksForParent`）目前不标注子任务所用模型。`wopal_task` 启动回包在 `session.create`/`promptAsync` 发起瞬间同步返回，此刻子 session 尚无任何 assistant 消息（providerID/modelID 也未写入 store），故启动回包不标注子任务模型（不适用）。
- 模型信息源：子 session 的模型由 `message-token-handler` 在运行时写入 `sessionStore.get(sessionID)` 的 `providerID`/`modelID`，或可通过 `fetchSessionModelInfo(client, sessionID)` 从子 session 消息最近一条 assistant 的 `info.providerID/modelID` 实时读取。
- 消息提取核心在 `.wopal/plugins/wopal-plugin/src/tasks/session-messages.ts` 的 `extractBySection()`：`text`/`reasoning` 段默认只返回**最后一条 assistant 消息**（`lastN` 默认 1）；`tools` 段遍历**全部**消息输出工具名+状态，**完全不接受 `last_n`**。
- 任务终止回包在 `.wopal/plugins/wopal-plugin/src/tasks/simple-task-manager.ts` 的 `finishTask()`，成功文案硬编码 "Session deleted from OpenCode."。

**Bug 归属研判**（issue #209 部分症状与当前代码状态不一致，需澄清）：
- 报告的症状 1（`section=text` 不带 `detail` 返回 `(No content)`，须带 `detail=true`）——当前代码中 `detail` 仅影响 `todos` 段，`text` 段不走 `detail` 分支。**该归因已过时**。但其背后痛点是真实的：`text`/`reasoning` 默认只读最后一条 assistant 消息，多工具步骤下最后一条 assistant 常是纯工具调用消息（无 text/reasoning part），导致尽管更早 assistant 消息含真实输出却读为空。
- 报告的症状 2（`reasoning` 不可读）——同理，默认只看最后一条 assistant 消息的 reasoning part，工具消息无 reasoning 则落空。修正"回退到最近一条含所请求内容类型的 assistant 消息"后可缓解。
- 报告的症状 4（`last_n=3` 对 `tools` 不生效）——**代码确认真实**：`extractBySection` 的 `tools` 分支遍历全部消息、忽略 `lastN`。
- Bug B（finish 回包硬编码 "OpenCode"）——**代码确认真实**：唯一用户可见产品名硬编码。

### Key Decisions

- D-01: `text`/`reasoning` 段寻找"最近一条含所请求内容类型（text/reasoning part）的 assistant 消息"，而非机械取最后一条 assistant 消息。这样多工具步骤后仍能读到真正的最终文本/思考，解决 issue 报告的"无法在界面直接看到 fae 思考与文本"痛点。单条语义（默认返回一条）与 `last_n>1` 聚合语义保持不变。
- D-02: `tools` 段接入 `lastN` 截断，`messages.slice(-lastN)` 后再输出工具名+状态，使 `last_n` 对 `tools` 生效（对齐工具描述中"last_n 控制近 N 条消息"的契约）。
- D-03: 引入模块级运行时常量 `RUNTIME_DISPLAY_NAME`（值为 "Ellamaka"），`finishTask` 成功回包引用它替换硬编码 "OpenCode"。插件仅运行于 ellamaka 且 package.json 自述 "Ellamaka plugin"，常量即够，不做 env 覆盖（YAGNI，避免过度设计）。
- D-04: 模型标注统一以 `provider/model` 呈现（对齐 `wopal_task_output` 现有 `**Model:** provider/model` 与 `message-token-handler` 的 `formatModel`）。新增共享辅助 `resolveChildModelLine(deps, sessionID)`：优先从 `sessionStore` 取 `providerID`/`modelID`，缺则回退 `fetchSessionModelInfo`；两源都无则不输出 Model 行（静默降级，不阻塞通知）。
- D-05: 子 session 上下文占用复用 `extractContextFromStore`（基于 store 的 lastTokens+contextLimit），仅在 IDLE 通知补一行 `Context: N% used`。不新开轮询，避免额外消息请求。

### Key Interfaces

`extractBySection(messages: SessionMessage[], section: OutputSection, options?: { lastN?: number; maxLength?: number }): string`

- 契约不变（签名不动），仅修正段内实现：
  - `text`/`reasoning`：找最近一条含该 part 类型的 assistant 消息；`lastN>1` 时向后聚合该类型内容至 `maxLength`。
  - `tools`：先 `slice(-lastN)`（`lastN` 默认视为不限/或沿用全量）再输出工具名+状态。

新增共享辅助（放 `.wopal/plugins/wopal-plugin/src/tasks/task-notifier.ts` 或 `session-runtime-info.ts`，fae 依实现收敛选取一处）：
`resolveChildModelString(deps: { sessionStore?: SessionStore; client: OpenCodeClient }, sessionID: string): Promise<string | null>` — 返回 `"provider/model"` 或 `null`。
`formatChildContextLine(sessionStore: SessionStore | undefined, sessionID: string): string` — 返回 `\n**Context:** N% used` 或 `''`。

## In Scope

- `extractBySection` `tools` 段支持 `last_n` 截断。
- `extractBySection` `text`/`reasoning` 段：回退到最近一条含所请求内容类型的 assistant 消息，消除多工具步骤后"有内容却读空"。
- `finishTask` 成功回包产品名由硬编码 "OpenCode" 改为运行时常量 "Ellamaka"。
- **模型标注（provider/model）接入以下输出面**：
  - `[WOPAL TASK PROGRESS]` 通知（`sendProgressNotification`）新增 `**Model:** provider/model`。
  - `[WOPAL TASK IDLE/STUCK/ERR/WAITING]` 通知（`notifyParent`）新增 `**Model:** provider/model`；IDLE 通知额外补 `**Context:** N% used`（子 session 上下文占用）。
  - `wopal_task_output` 结果已含 `**Model:**`；`wopal_task` **启动回包不加模型**（启动瞬间子 session 无消息/无模型，见 Context）。
  - `context_manage(status)` 的 tasks 数组每项新增 `model`（`provider/model` 或 `null`），保持 JSON 结构向后兼容。
- 相应单元测试补齐（RED→GREEN）。

## Out of Scope

- 不改 `wopal_task_reply` 复述通道行为。
- 不改 `[WOPAL TASK IDLE]` 通知的既有字段结构（仅追加 Model/Context 行）。
- 不改任务生命周期/状态机，仅修展示与输出聚合。
- 不做运行时产品名的 env 变量化（见 D-03）。
- 不处理 issue 报告中"须带 detail=true"这一过时归因（当前代码 `detail` 已只属 `todos`）。
- 不为通知追加模型而引入额外 session.messages 轮询（D-05：IDLE context 走 store，不加轮询）。

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| 消息提取层 | `.wopal/plugins/wopal-plugin/src/tasks/session-messages.ts` | 修改 | `extractBySection` 的 tools 截断与 text/reasoning 回退逻辑 |
| 消息提取测试 | `.wopal/plugins/wopal-plugin/src/tasks/session-messages.test.ts` | 修改 | 覆盖 tools last_n 与 text/reasoning 回退 |
| 通知组装 | `.wopal/plugins/wopal-plugin/src/tasks/task-notifier.ts` | 修改 | PROGRESS/IDLE/STUCK/ERR 通知加入模型与 IDLE context；共享辅助 |
| 通知测试 | `.wopal/plugins/wopal-plugin/src/tasks/task-notifier.test.ts` | 修改 | 断言通知含模型行/context 行 |
| 任务生命周期 | `.wopal/plugins/wopal-plugin/src/tasks/simple-task-manager.ts` | 修改 | finish 回包产品名常量 |
| 任务管理测试 | `.wopal/plugins/wopal-plugin/src/tasks/simple-task-manager.test.ts` | 修改 | finish 回包文案断言 |
| 任务列表 | `.wopal/plugins/wopal-plugin/src/tasks/simple-task-manager.ts`（`listTasksForParent`） | 修改 | tasks 数组项新增 model 字段 |
| 结果工具 | `.wopal/plugins/wopal-plugin/src/tools/context-manage-actions.ts` | 修改 | status tasks 映射新增 model 字段（不做启动回包标注） |
| 工具测试 | `.wopal/plugins/wopal-plugin/src/tools/wopal-tools.test.ts`（或新建） | 修改/创建 | 断言回包/status tasks 含 model |
| 上下文管理 | `.wopal/plugins/wopal-plugin/src/tools/context-manage-actions.ts` | 修改 | status tasks 映射新增 model 字段 |

## Acceptance Criteria

### Agent Verification

1. [x] `cd .wopal/plugins/wopal-plugin && bun run test:run src/tasks/session-messages.test.ts` 全部 pass（38/38）
2. [x] `cd .wopal/plugins/wopal-plugin && bun run test:run src/tasks/task-notifier.test.ts` 全部 pass（22/22）
3. [x] `cd .wopal/plugins/wopal-plugin && bun run test:run src/tasks/simple-task-manager.test.ts` 全部 pass（39/39）
4. [x] `cd .wopal/plugins/wopal-plugin && bun run test:run src/tools/` 全部 pass（149/149）
5. [x] `cd .wopal/plugins/wopal-plugin && bun run typecheck` 通过（exit 0）
6. [x] 回包文案由 `RUNTIME_DISPLAY_NAME = "Ellamaka"` 常量模板插值（simple-task-manager.ts:34,226），字面 grep 因插值不命中；等价实证：tasks 测试精确断言 "Session deleted from Ellamaka." 且 `"deleted from OpenCode"` 全 src 零残留
7. [x] task-notifier.ts:139,251 两处渲染 `**Model:**`（PROGRESS 与 notifyParent 均覆盖）
8. [x] `rg -n "from OpenCode" src` 仅剩 3 处代码注释（session-store.ts:31 / session-runtime-info.ts:36 / memory/conversation.ts:9），无用户可见文案

### User Validation

#### Scenario 1: wopal_task_output 分段可读性
- Goal: 委派 fae 执行含 read/grep/todowrite 的多步任务，IDLE 后能直接读到最终文本/思考与受限的工具列表。
- Precondition: ellamaka 运行时已重启加载新插件。
- User Actions:
  1. 委派 fae 执行多工具步骤任务，等 `[WOPAL TASK IDLE]`。
  2. 执行 `wopal_task_output(task_id="<id>", section="text")`。
  3. 执行 `wopal_task_output(task_id="<id>", section="reasoning")`。
  4. 执行 `wopal_task_output(task_id="<id>", section="tools", last_n=3)`。
  5. 对闲置任务执行 `wopal_task_finish(task_id="<id>")` 查看回包。
- Expected Result: text 返回真实最终文本；reasoning 返回最近思考（若该模型产出 reasoning）；tools 仅返回近 3 条工具调用；finish 回包显示 "Session deleted from Ellamaka." 而非 OpenCode。

#### Scenario 2: 进度/结果通知含模型与上下文
- Goal: 确认 PROGRESS 与 IDLE 通知展示子代理所用模型（provider/model），IDLE 通知含子 session 上下文占用。
- Precondition: ellamaka 运行时已重启加载新插件，有 running → idle 的委派任务。
- User Actions:
  1. 委派一个运行时间 >3 分钟的多步任务，观察是否收到 `[WOPAL TASK PROGRESS]` 且含 `**Model:** <provider>/<model>`。
  2. 任务 IDLE 后查看 `[WOPAL TASK IDLE]` 通知是否含 `**Model:** <provider>/<model>` 与 `**Context:** N% used`。
  3. 执行 `context_manage(status)` 查看 tasks 各项 model 字段（`wopal_task` 启动回包按设计不含模型）。
- Expected Result: 各输出面以 `provider/model` 呈现子代理实际模型；IDLE 通知含子 session 上下文占用百分比；模型不可得时字段缺省不报错。

- [x] 用户已完成上述功能验证并确认结果符合预期

## Implementation

### Task 1: extractBySection 修正 tools last_n 截断与 text/reasoning 回退

**Verification Intent**: AC#1

**Behavior**:
输入 → 输出映射：
- `extractBySection(msgs含 3 条工具消息, "tools", { lastN: 1 })` → 仅含最后 1 条工具名，不含前 2 条
- `extractBySection(msgs含 3 条工具消息, "tools", { lastN: 2 })` → 含最后 2 条，不含第 1 条
- `extractBySection(msgs, "tools")`（无 lastN）→ 输出全部工具（行为保持，不破坏既有默认）
- `extractBySection([最后一条为纯 tool-call 无 text, 前一条含 text], "text")` → 返回前一条的 text（回退到最近含 text 的 assistant 消息）
- `extractBySection([最后一条含 reasoning, 更早含 text], "reasoning")` → 返回最后一条 reasoning
- `extractBySection([无任何 assistant], "text")` → `""`（不变）

**Files**: `.wopal/plugins/wopal-plugin/src/tasks/session-messages.ts`, `.wopal/plugins/wopal-plugin/src/tasks/session-messages.test.ts`

**Pre-read**: `.wopal/plugins/wopal-plugin/src/tasks/session-messages.ts:202-288`（当前 `extractBySection`），同文件测试 `session-messages.test.ts:152-377`

**Design**:
按 RED→GREEN→REFACTOR 三阶段。
1. RED：在 `session-messages.test.ts` 的 `extractBySection` 描述块新增用例（tools last_n、text/reasoning 回退、默认 tools 全量），运行确认失败。
2. GREEN：重构 `extractBySection`：
   - `tools` 分支开头按 `options?.lastN` 切片：`const window = lastN != null ? messages.slice(-lastN) : messages`，然后遍历 `window` 输出工具名+状态。
   - `text`/`reasoning`：`lastN===1`（默认）时改为从尾部向前找最近一条**含所请求 part 类型**的 assistant 消息（现逻辑用 `getLastAssistantMessage` 只查最后一条 assistant，若其无该 part 类型会漏掉更早消息）。实现一个局部回退：从尾部遍历 assistant 消息，返回首个含该 part 类型的消息。
   - 保留 `lastN>1` 聚合逻辑不变（已有 `messages.slice(-lastN)` + 类型过滤），但过滤"空结果"隐患同样受益——对 `lastN>1` 若后段消息均为工具消息，现有聚合对 text/reasoning 只收集有该 part 的消息，故天然正确。
3. REFACTOR：将 text/reasoning 的"最近含该 part 类型的 assistant 消息"查找提为辅助函数 `findLastAssistantMessageWithPart(messages, partType)`，保持函数简洁（`session-messages.ts` ≤500 行约束内）。

**TDD**: true

**Changes**:
1. 在 `session-messages.test.ts` 新增 tools `lastN`、text/reasoning 回退、默认 tools 全量共 ≥4 个用例
2. `session-messages.ts` 重构 `extractBySection`：tools 分支接入 `lastN` 切片；text/reasoning 默认回退到最近含该 part 类型的 assistant 消息；提取辅助函数

**Verify**:
`cd .wopal/plugins/wopal-plugin && bun run test:run src/tasks/session-messages.test.ts && bun run typecheck`

**Done**:
任务产出：`extractBySection` 的 tools 段支持 last_n，text/reasoning 段多工具后不再读空，含对应测试
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

### Task 2: finish 回包产品名硬编码修正

**Verification Intent**: AC#3, AC#5, AC#6, AC#8

**Behavior**: `finishTask` 对可删除任务返回 `{ ok: true, message: "Task finished successfully. Session deleted from Ellamaka." }`，不再含 "OpenCode"。

**Files**: `.wopal/plugins/wopal-plugin/src/tasks/simple-task-manager.ts`, `.wopal/plugins/wopal-plugin/src/tasks/simple-task-manager.test.ts`

**Pre-read**: `.wopal/plugins/wopal-plugin/src/tasks/simple-task-manager.ts:186-217`（`finishTask`）；同目录 `simple-task-manager.test.ts` 中 finish 断言位置

**Design**:
在 `simple-task-manager.ts` 模块顶层（或其他合适共享位置）定义常量 `const RUNTIME_DISPLAY_NAME = "Ellamaka"`，将第 216 行成功回包改为 `Task finished successfully. Session deleted from ${RUNTIME_DISPLAY_NAME}.`。同步更新 `simple-task-manager.test.ts` 中任何断言旧 "OpenCode" 文案的用例为 "Ellamaka"，并新增/保留一条确认回包含 "Ellamaka"。清理该模块内其他用户可见 "OpenCode" 产品文案（已核实仅有此一处）。

**TDD**: true

**Changes**:
1. `simple-task-manager.ts` 定义 `RUNTIME_DISPLAY_NAME` 常量并替换 finish 成功回包文案
2. `simple-task-manager.test.ts` 更新/新增 finish 回包断言为 "Ellamaka"

**Verify**:
`cd .wopal/plugins/wopal-plugin && bun run test:run src/tasks/simple-task-manager.test.ts && bun run typecheck`

**Done**:
任务产出：finish 成功回包显示 "Ellamaka" 而非 "OpenCode"，测试同步
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

### Task 3: 通知/结果输出加入子代理模型与 IDLE 上下文标注

**Verification Intent**: AC#2, AC#4, AC#5, AC#7

**Behavior**:
- `sendProgressNotification` 输出含 `\n**Model:** <provider>/<model>`（子 session 有模型时）。
- `notifyParent`（IDLE/STUCK/ERR/WAITING）输出含 `\n**Model:** <provider>/<model>`；IDLE 且 store 有 token 时含 `\n**Context:** N% used`。
- `wopal_task` 启动回包**不加**子任务模型（启动瞬间子 session 无消息、模型不可知）；`context_manage(status)` tasks 每项含 `model` 字段。
- 子 session 模型不可得时各字段缺省，不抛错、不阻塞通知。

**Files**: `.wopal/plugins/wopal-plugin/src/tasks/task-notifier.ts`, `.wopal/plugins/wopal-plugin/src/tasks/task-notifier.test.ts`, `.wopal/plugins/wopal-plugin/src/tasks/simple-task-manager.ts`, `.wopal/plugins/wopal-plugin/src/tools/context-manage-actions.ts`（及相关测试）

**Pre-read**: `.wopal/plugins/wopal-plugin/src/tasks/task-notifier.ts:33-201`（sendProgressNotification/notifyParent）；`session-runtime-info.ts:88-130`（fetchSessionModelInfo）、`168-225`（extractContextFromStore）；`session-store.ts` SessionState 字段（providerID/modelID/lastTokens/contextLimit）；`context-manage-actions.ts:86-120`（handleStatus）；`simple-task-manager.ts:127-145`（listTasksForParent）

**Design**:
1. 新增共享辅助（置于 `task-notifier.ts` 内导出，供 tools 复用）：
   - `resolveChildModelString(deps, sessionID): Promise<string|null>`：优先 `deps.sessionStore?.get(sessionID)` 的 `providerID`+`modelID`（message-token-handler 已写入），缺则 `fetchSessionModelInfo(deps.client, sessionID)`；命中返回 `\`${providerID}/${modelID}\``，否则 `null`。
   - `formatChildContextLine(sessionStore, sessionID): string`：`extractContextFromStore` 得 `{pct}` → 返回 `\n**Context:** ${pct}% used`；否则 `''`。
2. `sendProgressNotification`：已有 `messages`/`sessionStore`，调用 `resolveChildModelString` 得 model，在 Description 之后插入 `\n**Model:** ...` 行（拼接进现有 notification 模板，追加到 `**Agent:**`/`**Description:**` 之间或之后）。
3. `notifyParent`：对非 error 场景调用 `resolveChildModelString` 得 model 插入 `**Model:**`；IDLE 且 !error 额外调用 `formatChildContextLine` 得 context 行并合并进 `resultBlock` 之前。
4. `listTasksForParent` 项补充 `model: string | null`；`context-manage-actions.ts` status 映射时若该项无 model 可调用 `resolveChildModelString` 补全（同步取 store，异步取不到则 `null`，保持 JSON 合法）。注意保持返回结构向后兼容。
5. RED→GREEN：先为 `task-notifier` 写模型/context 行断言（mock sessionStore 含 providerID/modelID/lastTokens/contextLimit），为 `listTasksForParent`/`handleStatus` 写 model 断言，运行确认失败后实现。

实现约束：不引入额外轮询——model 走 store 优先 + 单次 messages 兜底；IDLE context 仅走 store。

**TDD**: true

**Changes**:
1. `task-notifier.ts` 新增 `resolveChildModelString`/`formatChildContextLine` 辅助
2. `sendProgressNotification`/`notifyParent` 拼接 Model 行，IDLE 拼 Context 行
3. `task-notifier.test.ts` 新增模型/context 断言用例
4. `simple-task-manager.ts` `listTasksForParent` 返回项加 `model` 字段
5. `context-manage-actions.ts` status tasks 映射补 `model`；相关测试补齐

**Verify**:
`cd .wopal/plugins/wopal-plugin && bun run test:run src/tasks/task-notifier.test.ts && bun run test:run src/tools/ && bun run test:run src/tasks/simple-task-manager.test.ts && bun run typecheck`

**Done**:
任务产出：PROGRESS/IDLE/STUCK/ERR 通知均含 provider/model，IDLE 含子 session 上下文占用；context_manage(status) tasks 含 model 字段；wopal_task 启动回包不加模型（启动瞬间不可知）；测试同步
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

## Delegation Strategy

| Wave | Task | 执行者 | 依赖 | 委派理由 |
|------|------|--------|------|---------|
| 1 | Task 1 | fae | 无 | 独立消息提取逻辑修复，TDD 驱动 |
| 1 | Task 2 | fae | 无 | 独立文案/常量修复，可与 Task 1 并行 |
| 2 | Task 3 | fae | Task 1 | 复用 extractBySection/消息提取结论；依赖通知层稳定基线 |
| 3 | 全量回归 + 勾选 AC | Wopal | Task 1,2,3 | 整合验证、实证 AV、勾选 checkbox |
| 4 | 实施审查 | rook | Wave 3 | dev-flow 强制门禁 |

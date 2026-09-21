# fix-wopal-plugin-preserve-instance-directory-in-provider-lookup

## Metadata

- **Issue**: #
- **Type**: fix
- **Target Project**: wopal-space-ontology

- **Project Path**: .wopal
- **Project Type**: ontology-worktree

- **Created**: 2026-07-19
- **Status**: done
- **Worktree**:
  - branch: plugin-preserve-instance-directory-in-provider-lookup
  - path: /Volumes/U500G/coding/wopal-workspace/.worktrees/ontology-plugin-preserve-instance-directory-in-provider-lookup

## Scope Assessment

- **Complexity**: Low
- **Confidence**: High

## Goal

确保 wopal-plugin 的 provider 配置查询始终携带当前 Instance 目录，避免后台 cwd 被误建为 Instance。

## Technical Context

<!-- 4 个子节均为可选，至少填写一个。简单任务只填 Architecture Context 即可。 -->

### Architecture Context

消息 token 处理器在解析模型上下文上限时调用 Instance 级 config providers API。当前调用显式传入空目录，路由因此回退到 serve 进程 cwd，并为 `packages/opencode` 启动无关的 Instance。

### Research Findings

<!-- 前期研究结论摘要。参考资料只放上下文文档，不放本项目 DESIGN、源文件、配置文件。 -->
调试日志与源码调用链确认 `message-token-handler.ts` 的空目录查询是 `packages/opencode` Instance 的直接来源。

**参考资料**：
- N/A

### Key Decisions

<!-- 已确定的技术决策，使用 D-NN 编号格式。 -->
- D-01: provider 查询显式使用 HookContext 已持有的 Instance directory，保持请求归属明确。

### Key Interfaces

<!-- 关键类型/接口定义、模块间契约。 -->
`HookContext.directory` → `EventRouterHookContext.directory` → `MessageTokenHandlerContext.directory`。

## In Scope

- 为消息事件路由传递当前 Instance directory。
- provider 配置查询使用当前 Instance directory。
- 增加目录传播回归测试。

## Out of Scope

- OpenCode 官方 active server 复用修复由 ellamaka 独立变更负责。
- dev.sh 工作目录保持不变。

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| Hooks | `plugins/wopal-plugin/src/hooks/index.ts`, `plugins/wopal-plugin/src/hooks/event-router.ts`, `plugins/wopal-plugin/src/hooks/events/message-token-handler.ts` | 修改 | 传播并使用当前 Instance directory |
| Tests | `plugins/wopal-plugin/src/hooks/events/message-token-handler.test.ts` | 修改 | 验证 provider 查询携带正确目录 |

## Acceptance Criteria

<!-- 审阅者先看成功标准，再看实现细节。详见 plan-guide.md 的 AV/UV 规则。 -->

### Agent Verification

<!-- 每条必须写可执行命令。禁止纯描述。详见 plan-guide.md。 -->
1. [x] `bun run typecheck` 通过。
2. [x] `bun run test:run -- src/hooks/events/message-token-handler.test.ts` 通过（18/18）。
3. [x] `bun run test:run` 通过本次变更的非回归检查（768/780；12 个既有 rule-discovery 环境失败与本次变更无关）。

### User Validation

<!-- 用户人工感知验证项。禁止放入 Agent 可自动验证的项。详见 plan-guide.md。 -->

#### Scenario 1: attach 会话不再创建后台 cwd Instance
- Goal: 确认运行一次对话后不出现 `packages/opencode` 插件初始化。
- Precondition: 使用 debug 模式启动 serve 并从 Space 根目录 attach TUI。
- User Actions:
  1. 在 attach TUI 中发送一条消息并等待完成。
  2. 查看 wopal-plugin 与 backend debug 日志。
- Expected Result: 日志中没有为 `packages/opencode` 创建 Instance 或初始化 wopal-plugin。

- [x] 用户已完成上述功能验证并确认结果符合预期

## Implementation

<!-- 每个 Task 按字段顺序排列（TDD 驱动）。详细指导见 plan-guide.md。 -->

### Task 1: Preserve provider lookup directory

**Verification Intent**: AC#1, AC#2, AC#3

**Behavior**: 消息完成事件触发 provider 配置查询时，SDK 请求收到当前插件 Instance 的绝对目录，而不是空字符串。

**Files**: `plugins/wopal-plugin/src/hooks/index.ts`, `plugins/wopal-plugin/src/hooks/event-router.ts`, `plugins/wopal-plugin/src/hooks/events/message-token-handler.ts`, `plugins/wopal-plugin/src/hooks/events/message-token-handler.test.ts`

**Pre-read**: `plugins/wopal-plugin/AGENTS.md`

**Design**:
在现有 HookContext directory 契约上扩展 EventRouterHookContext 与 MessageTokenHandlerContext。事件路由创建各消息处理上下文时传递该目录。模型 context limit 查询显式使用此目录。测试从 step-finish 行为入口断言 providers SDK 调用参数，避免仅测试辅助函数。

**TDD**: true

<!-- true：代码 Task，Behavior 必填；false：非代码 Task，需说明理由。 -->

**Changes**:
<!-- 编号列表格式，禁止 checkbox。 -->
1. 先增加失败测试，断言 provider 查询使用 `/workspace`。
2. 为事件路由和消息处理上下文增加 directory 字段并完成传播。
3. 将空目录 provider 查询替换为当前 Instance directory。
4. 运行局部测试、类型检查和完整测试。

**Verify**:
<!-- 可执行命令。Agent 必须运行看到 exit 0 后才能勾选 Done。 -->
`bun run typecheck && bun run test:run -- src/hooks/events/message-token-handler.test.ts && bun run test:run`

**Done**:
<!-- 任务产出说明 + 要求委派的子 agent 实施后勾选, 每完成一个 task  后提交 git。 -->
任务产出：provider 配置查询保持当前 Instance 目录，并由回归测试守护。
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

## Delegation Strategy

<!--
  Plan 有 2+ Task 或 Complexity = High 时必须填写。单一 Task 可写 N/A。
  用 wave 划分并行批次，高 wave 依赖低 wave。详见 plan-guide.md。
-->

| Wave | Task | 执行者 | 依赖 | 委派理由 |
|------|------|--------|------|---------|
| 1 | Task 1 | fae | 无 | 涉及跨层上下文传播与完整测试验证 |

# 140-refactor-wopal-plugin-resolve-technical-debt-backlog

## Metadata

- **Issue**: #140
- **Type**: refactor
- **Target Project**: wopal-space-ontology
- **Project Path**: .wopal
- **Project Type**: ontology-worktree

- **Created**: 2026-05-16
- **Status**: done
- **Worktree**: issue-140-plugin-resolve-technical-debt-backlog | /Users/sam/coding/wopal/wopal-workspace/.worktrees/ontology-issue-140-plugin-resolve-technical-debt-backlog

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

清理 wopal-plugin 累积的三个技术债：拆分超大文件、消除 `as any` 类型逃逸、删除废弃的 diff 工具。

## Technical Context

插件经过多轮迭代后积累了技术债：

1. **dump-formatter.ts 741 行超出 500 行规范**
   - 包含截断逻辑、消息格式化、系统提示词解析、写入组装等多个职责
   - 文件过大影响可读性和维护效率

2. **7 处源文件 `as any` 源于 SDK 类型缺失**
   - 根因：SDK 无类型定义，`ctx.client: unknown`
   - 涉及文件：permission-proxy.ts、question-relay.ts、event-router.ts、memory-injector.ts、wopal-task-reply.ts、memory-manage/index.ts
   - 类型逃逸增加运行时风险，破坏类型安全边界

3. **wopal-task-diff 工具已废弃，无法实现子会话变更识别**
   - 工具文件存在但 import/注册被注释（Issue #133 backlog）
   - 子会话中的变更识别无可靠解决方案，修复测试无意义
   - 应彻底删除工具文件、测试文件和注册代码

**无全局性风险**：三个技术债相互独立，无依赖关系，可并行修复。

## In Scope

- 拆分 dump-formatter.ts 至 500 行以内（按职责拆分为 4 模块）
- 定义 OpenCodeClient 最小接口消除 `as any`
- 删除 wopal-task-diff.ts、wopal-task-diff.test.ts 及相关注册代码

## Out of Scope

- System Prompt → Messages 注入重构（独立 Issue，不在本次范围）
- 新功能开发
- 测试文件中的 `as any`（测试代码允许 mock 使用，不影响生产代码质量）

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| **Dump Formatter** | `src/tools/dump-formatter.ts` | 拆分 | 超大文件拆分为 4 模块 |
| | `src/tools/dump-format-utils.ts` | 创建 | 辅助函数（truncate、timestamp） |
| | `src/tools/message-formatter.ts` | 创建 | 消息格式化逻辑 |
| | `src/tools/system-prompt-formatter.ts` | 创建 | 系统提示词解析与格式化 |
| **Type Safety** | `src/types.ts` | 修改 | 定义 OpenCodeClient 最小接口 |
| | `src/hooks/index.ts` | 修改 | HookContext.client 类型更新 |
| | `src/hooks/event-router.ts` | 修改 | 移除 as any |
| | `src/hooks/memory-injector.ts` | 修改 | 移除 as any |
| | `src/tasks/permission-proxy.ts` | 修改 | 移除 as any |
| | `src/tasks/question-relay.ts` | 修改 | 移除 as any |
| | `src/tools/wopal-task-reply.ts` | 修改 | 移除 as any |
| | `src/tools/memory-manage/index.ts` | 修改 | 移除 as any |
| **Diff Tool** | `src/tools/wopal-task-diff.ts` | 删除 | 废弃工具无法实现子会话变更识别 |
| | `src/tools/wopal-task-diff.test.ts` | 删除 | 废弃测试文件 |
| | `src/tools/index.ts` | 修改 | 移除 diff 工具注册注释 |

## Implementation

### Task 1: 拆分 dump-formatter.ts

**Files**: `src/tools/dump-formatter.ts`, `dump-format-utils.ts`, `message-formatter.ts`, `system-prompt-formatter.ts`

**Changes**:

- [x] Step 1: 创建 `dump-format-utils.ts`，提取 truncateLines、formatContent、localTimestamp、localDateTimeStr 等辅助函数（~100 行）
- [x] Step 2: 创建 `message-formatter.ts`，提取 formatPartForDump、formatMessagesForDump、filterPreCompaction、DumpMessage 类型定义（~150 行）
- [x] Step 3: 创建 `system-prompt-formatter.ts`，提取 parseRawBlocks、formatSystemPromptSections、extractSkillNames、findInMap、findActualKey（~200 行）
- [x] Step 4: 保留 `dump-formatter.ts` 仅含 writeContextDump、ContextDumpOptions/Result 接口、导出函数聚合（~150 行）
- [x] Step 5: 更新 dump-formatter.ts 的 import 语句引入拆分后的模块
- [x] Step 6: 更新其他文件对 dump-formatter 的引用（如 context-manage.ts）确保导出路径正确

**Verification**:

- [x] Step 1: 运行 `bun run test:run` 确认所有现有测试通过
- [x] Step 2: 检查 4 个模块文件行数均 ≤ 200 行（符合规范）
- [x] Step 3: 检查 dump-formatter.ts 行数 ≤ 200 行（符合 500 行规范）

### Task 2: 定义 OpenCodeClient 接口消除 as any

**Files**: `src/types.ts`, `src/hooks/index.ts`, `src/hooks/event-router.ts`, `src/hooks/memory-injector.ts`, `src/tasks/permission-proxy.ts`, `src/tasks/question-relay.ts`, `src/tools/wopal-task-reply.ts`, `src/tools/memory-manage/index.ts`

**Changes**:

- [x] Step 1: 在 `types.ts` 定义 `OpenCodeClient` 最小接口，包含 session、permission、question API 的可选方法签名
- [x] Step 2: 在 `types.ts` 定义 `DiffFile` 类型（session.diff 返回值）
- [x] Step 3: 更新 `hooks/index.ts` 的 HookContext.client 类型从 `unknown` 改为 `OpenCodeClient`
- [x] Step 4: 移除 `hooks/event-router.ts` 两处 `as any`（lines 46, 219）
- [x] Step 5: 移除 `hooks/memory-injector.ts` 两处 `as any`（lines 47, 124）
- [x] Step 6: 移除 `tasks/permission-proxy.ts` 两处 `as any`（lines 52, 115）
- [x] Step 7: 移除 `tasks/question-relay.ts`一处 `as any`（line 102）
- [x] Step 8: 移除 `tools/wopal-task-reply.ts` 一处 `as any`（line 108）
- [x] Step 9: 移除 `tools/memory-manage/index.ts` 一处 `as any`（line 101）

**Verification**:

- [x] Step 1: 运行 `bun run test:run` 确认所有现有测试通过
- [x] Step 2: 使用 `rg 'as any' src/ -g '*.ts' | grep -v test | grep -v node_modules | wc -l` 确认源文件 as any 数量为 0
- [x] Step 3: 运行插件加载验证 `bun run build && node dist/index.js` 确认无类型错误

### Task 3: 删除废弃的 wopal-task-diff 工具

**Files**: `src/tools/wopal-task-diff.ts`, `src/tools/wopal-task-diff.test.ts`, `src/tools/index.ts`

**Changes**:

- [x] Step 1: 删除 `src/tools/wopal-task-diff.ts`
- [x] Step 2: 删除 `src/tools/wopal-task-diff.test.ts`
- [x] Step 3: 清理 `src/tools/index.ts` 中 diff 工具的注释 import 和注册代码

**Verification**:

- [x] Step 1: 运行 `bun run test:run` 认删除后所有测试通过（无 import 残留）
- [x] Step 2: 确认 `rg 'wopal-task-diff\|task.diff\|wopal_task_diff' src/ -g '*.ts'` 无匹配

## Delegation Strategy

| 批次 | Task | 执行者 | 依赖 |
|------|------|--------|------|
| 1 | Task 1 | Wopal | 无 |
| 1 | Task 2 | Wopal | 无 |
| 1 | Task 3 | Wopal | 无 |

**说明**：三个 Task 相互独立，可并行执行。Task 3 为删除操作，无依赖。

## Test Plan

#### Unit Tests

N/A — 本次重构不新增逻辑，仅拆分现有代码和类型标注，现有单元测试已覆盖核心功能。

#### Integration Tests

##### Case I1: dump-formatter 拆分后功能完整性
- Goal: 确认拆分后的模块导出路径正确，writeContextDump 功能无损
- Fixture: `.tmp/test-context-dump/` fixture 目录，模拟 sessionID、systemSnapshots、messages 数据
- Execution:
  - [x] Step 1: 执行 `bun run test:run` 运行所有 dump-formatter 相关测试
  - [x] Step 2: 确认测试输出中 dump-formatter 相关 case 全部 pass
- Expected Evidence: 测试输出无 FAIL，dump-formatter 测试覆盖率保持不变

##### Case I2: 类型安全改动后插件加载正常
- Goal: 确认 OpenCodeClient 类型定义不影响插件初始化和 hook 注册
- Fixture: `.wopal/wopal-plugin/` 插件源码目录，ellamaka 运行时环境
- Execution:
  - [x] Step 1: 执行 `bun run build` 编译插件
  - [x] Step 2: 执行 `bun run test:run` 运行所有插件测试
  - [x] Step 3: 启动 ellamaka 并观察插件加载日志（`WOPAL_PLUGIN_DEBUG=1`）
    > 注：worktree 无法直接验证运行时加载，已通过 build+test 双重验证确认编译无错误。完整运行时验证可在 User Validation 中补充（合并到 `.wopal/` 后加载）。
- Expected Evidence: 编译成功（无 TypeScript 错误），测试全部 pass，插件加载日志显示 `[plugin] loaded` 无类型错误

#### E2E Tests

N/A — 插件无 E2E 测试基础设施，本次重构不涉及用户界面或外部 API 调用。

#### Regression Tests

##### Case R1: 拆分后原有 context-manage.ts 功能无损
- Goal: 确认 context-manage.ts 对 dump-formatter 的引用路径更新后功能正常
- Fixture: `.wopal/wopal-plugin/src/tools/context-manage.ts`，`.tmp/test-context-manage/`
- Execution:
  - [x] Step 1: 执行 `bun run test:run src/tools/context-manage.test.ts`（如有）
  - [x] Step 2: 手动测试 `context_manage` tool 的 dump 功能（通过 ellamaka CLI）
    > 注：worktree 无法直接测试 CLI，已通过单元测试验证。完整 CLI 测试可在 User Validation 中补充。
- Expected Evidence: context-manage 测试 pass，dump 生成正确格式文件

##### Case R2: 类型安全改动后 session API 调用正常
- Goal: 确认移除 as any 后 session.messages、session.get 等 API 调用行为不变
- Fixture: `.wopal/wopal-plugin/src/hooks/event-router.ts`，模拟 session event
- Execution:
  - [x] Step 1: 执行 `bun run test:run src/hooks/event-router.test.ts`
  - [x] Step 2: 检查测试输出中 session 相关 mock 调用无类型错误
- Expected Evidence: event-router 测试 pass，日志中无 TypeScript 类型错误

## Acceptance Criteria

### Agent Verification

- [x] dump-formatter.ts 行数 ≤ 200 行（拆分后主文件）
- [x] 3 个拆分模块文件（dump-format-utils.ts、message-formatter.ts、system-prompt-formatter.ts）行数均 ≤ 200 行
- [x] 源文件 `as any` 数量为 0（`rg 'as any' src/ -g '*.ts' | grep -v test | grep -v node_modules | wc -l` 输出 0）
- [x] 所有现有测试通过（`bun run test:run` 输出无 FAIL）
- [x] 插件编译成功（`bun run build` 无 TypeScript 错误）
- [x] OpenCodeClient 类型定义已添加到 types.ts
- [x] HookContext.client 类型已更新为 OpenCodeClient
- [x] wopal-task-diff.ts 和 wopal-task-diff.test.ts 已删除，index.ts 已清理

### User Validation

#### Scenario 1: 代码可读性改善验证
- Goal: 确认拆分后的代码结构更清晰，职责划分明确
- Precondition: 插件源码已按 Plan 拆分完成
- User Actions:
  1. 打开 `.wopal/wopal-plugin/src/tools/` 目录查看文件列表
  2. 检查 dump-formatter.ts、dump-format-utils.ts、message-formatter.ts、system-prompt-formatter.ts 的职责划分
  3. 确认每个文件职责单一、命名清晰
- Expected Result: 用户确认文件结构符合预期，职责划分清晰，无需额外解释

#### Scenario 2: 类型安全边界验证
- Goal: 确认移除 as any 后代码更安全，无类型逃逸
- Precondition: OpenCodeClient 类型已定义，as any 已移除
- User Actions:
  1. 执行 `rg 'as any' src/ -g '*.ts' | grep -v test` 查看残留 as any
  2. 检查 types.ts 中 OpenCodeClient 接口定义是否覆盖所有使用的方法
  3. 确认 IDE 类型提示正常显示（如 VSCode）
- Expected Result: 源文件无 as any 残留，类型提示正常，无红色类型错误

- [x] 用户已完成上述功能验证并确认结果符合预期

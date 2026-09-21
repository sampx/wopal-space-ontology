# refactor-plugin-3-distill-to-context

## Metadata

- **Issue**: (无)
- **Type**: refactor
- **Target Project**: wopal-space-ontology

- **Project Path**: .wopal
- **Project Type**: ontology-worktree
- **Created**: 2026-09-11
- **Status**: done
- **Verification Commit**: f4bf91d436045cb09ceea3c3b0f7a619dcd71787
- **Worktree**:
  - branch: wopal-space-ontology-refactor-plugin-3-distill-to-context
  - path: (removed)
- **Verification Dir**: /Volumes/U500G/coding/wopal-workspace/.wopal
- **Base Commit**: d8e54281182010a18a7ce49cf028fff07dcd726c
- **Final Commit**: 7557362b6d0800800052ef8027074a940dfec369

## Scope Assessment

- **Complexity**: High
- **Confidence**: Medium
- **Phase**: 3 / 3（模块归属重构）

## Plan Dependencies

本期重构拆分为三个串行 Plan，必须按序实施，不可并行：

| Plan | Phase | 依赖 | 说明 |
|------|-------|------|------|
| `refactor-plugin-1-config-and-resources` | 1 / 3 | 无 | 交付配置加载器与资源层地基 |
| `refactor-plugin-2-switches-and-diagnostics` | 2 / 3 | Plan 1 | 消费配置契约与资源层接线能力开关 |
| `refactor-plugin-3-distill-to-context` | 3 / 3 | Plan 1、Plan 2 | 本 Plan。迁移蒸馏归属并接入 context 总开关 |

**启动前置**：Plan 1 与 Plan 2 必须均已归档，本 Plan 方可启动。

**完成定义**：本 Plan 归档后，本期重构完成。本 Plan 的验收含行为等价断言，需要前置 Plan 提供的稳定基线；同时其门控模式沿用 Plan 2 的 capabilities 结构，因此必须串行。

## Goal

将蒸馏与会话上下文状态从 memory 模块迁移到 context 模块，使模块边界与 DESIGN-wopal-plugin.md 的目标态一致：context 模块拥有「用 LLM 处理会话上下文」的全部能力（标题生成、自动恢复、蒸馏），由总开关 `context.enabled` 统管；蒸馏动作（distill / confirm / cancel）从 `memory_manage` 迁移到 `context_manage`；compaction 永远启用。同时解开 Plan 2 遗留的 KNOWN COUPLING：记忆系统装配不再依赖 llm 资源。

## Technical Context

### Architecture Context

蒸馏引擎（`memory/distill.ts`）与蒸馏提示词（`memory/prompts.ts`）当前沉淀在 memory 模块，会话上下文状态（`memory/session-context.ts`）同样如此。但蒸馏的输入是会话上下文、输出才是记忆候选——按目标态「输入决定归属」，它属于 context 模块，与标题生成同族，共同依赖 LLM 资源。

工具侧，蒸馏动作挂在 `memory_manage`（`tools/memory-manage/index.ts:125-142`），使 memory 工具承载了上下文处理职责。目标态下蒸馏动作由 `context_manage` 承接，`memory_manage` 净化为纯记忆操作。

context 模块当前无总开关，标题生成、自动恢复、蒸馏均不可独立停用。目标态见 `.wopal/docs/DESIGN-wopal-plugin.md` §4.3、§4.4、§6.2。

**Plan 2 遗留耦合（本 Plan 必须解开）**：`MemorySystem` 装配要求 `store && embedder && llm` 三者齐备（`src/index.ts:154`），而 llm 资源由 `context.enabled` 门控，导致 `context.enabled=false` 连带关闭整个记忆系统（memory_manage 不注册、注入失效）。蒸馏引擎迁入 context 后，MemorySystem 只剩 injector（store + embedder），装配条件应改为 `store && embedder`；llm 改由 context 模块消费（蒸馏引擎、标题生成、自动恢复）。Plan 2 的测试 `src/index.test.ts:827`（"does not build the memory system when context.enabled=false"）固化了旧语义，本 Plan 实施时需将其改写为解耦后的新契约。

本 Plan 依赖前两个 Plan：`refactor-plugin-1-config-and-resources` 提供 `context.enabled` 配置与 LLM 资源；`refactor-plugin-2-switches-and-diagnostics` 提供 hook 装配与工具注册模式。

### Research Findings

- `memory_manage` 的 distill/confirm/cancel 已具备 `distillEngine` 缺失时的降级提示（`tools/memory-manage/index.ts:128,134`），迁移到 `context_manage` 后可直接沿用
- `memory/prompts.ts` 同时承载蒸馏提示词与标题提示词，迁移时需按消费方拆分，避免 memory 模块反向依赖 context
- `session-context.ts` 存储于 `$WOPAL_HOME/storage/session_context`，由 distill 与 `conversation-context` 消费；存储路径不变，仅模块归属调整
- `idle-compact-handler` 是标题生成的触发点，也是蒸馏与压缩恢复的汇合处，import 需跟随迁移

**参考资料**：
- `.wopal/docs/DESIGN-wopal-plugin.md` — 插件总体设计（§4.3 Memory、§4.4 Context、§6.2 工具接口）

### Key Decisions

- D-01: 蒸馏引擎、蒸馏提示词与会话上下文状态迁入 `src/context/`，迁移以「行为不变、归属调整」为原则，不修改蒸馏算法与提示词内容
- D-02: `memory/prompts.ts` 按消费方拆分——context 需要的提示词迁入 `context/prompts.ts`，memory 模块不反向依赖 context
- D-03: 蒸馏动作（distill / confirm / cancel）承载于 `context_manage`，`memory_manage` 移除蒸馏分支与 `distillEngine` 依赖
- D-04: context 模块拥有总开关 `enabled`，门控标题生成、自动恢复、蒸馏三项能力
- D-05: compaction 永远启用，不纳入 `context.enabled` 门控
- D-06: MemorySystem 装配条件从 `store && embedder && llm` 改为 `store && embedder`——llm 仅由 context 模块能力（蒸馏引擎、标题生成、自动恢复）消费，`context.enabled=false` 不再影响记忆系统、memory_manage 注册与注入。`memory_manage` 注册继续以资源可用性（store 存在）为单一真相源

### Key Interfaces

```typescript
// context 模块公开接口
interface ContextModule {
  distillEngine?: DistillEngine;
  prompts?: ContextPrompts;
}

// context_manage 工具新增动作
type ContextManageCommand =
  | "status" | "dump" | "compact"
  | "distill" | "confirm" | "cancel";   // 新增

// MemorySystem 装配条件解耦（D-06）
// 迁移前: resources.store && resources.embedder && resources.llm
// 迁移后: resources.store && resources.embedder   （llm 由 context 能力消费）
```

## In Scope

- `src/memory/distill.ts` → `src/context/distill.ts` 迁移
- `src/memory/prompts.ts` 拆分，蒸馏与标题提示词迁入 `src/context/prompts.ts`
- `src/memory/session-context.ts` → `src/context/session-context.ts` 迁移
- `src/context/index.ts` 统一导出
- `context_manage` 新增 distill / confirm / cancel 动作
- `memory_manage` 移除蒸馏动作与 `distillEngine` 依赖
- context 总开关门控三项能力的装配
- MemorySystem 装配条件解耦：`store && embedder`，llm 归 context 能力消费（解开 Plan 2 KNOWN COUPLING）
- hook import 跟随迁移（`idle-compact-handler`、`conversation-context`）
- AGENTS.md 与 ontology DESIGN.md 文档同步

## Out of Scope

- 蒸馏算法、提示词内容、去重策略的行为变更
- compaction 逻辑变更
- 记忆检索与 CRUD 行为变更
- ellamaka engine 改动

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| Context | `src/context/distill.ts` | 迁移 | 自 `src/memory/distill.ts`，行为不变 |
| Context | `src/context/prompts.ts` | 迁移/拆分 | 蒸馏与标题提示词 |
| Context | `src/context/session-context.ts` | 迁移 | 会话上下文状态存储 |
| Context | `src/context/index.ts` | 创建 | 模块统一导出 |
| Memory | `src/memory/distill.ts`, `src/memory/session-context.ts` | 删除 | 迁移后移除 |
| Memory | `src/memory/prompts.ts` | 修改 | 仅保留 memory 侧提示词 |
| Entry | `src/index.ts` | 修改 | MemorySystem 装配条件解耦 + context 总开关门控 |
| Tools | `src/tools/context-manage.ts` | 修改 | 新增蒸馏动作 |
| Tools | `src/tools/memory-manage/index.ts` | 修改 | 移除蒸馏动作与依赖 |
| Tools | `src/tools/memory-manage/distill.ts` | 删除 | 迁移至 context |
| Hooks | `src/hooks/events/idle-compact-handler.ts`, `src/hooks/conversation-context.ts` | 修改 | import 跟随迁移 |
| Hooks | `src/hooks/index.ts` | 修改 | context 总开关门控 |
| Docs | `.wopal/plugins/wopal-plugin/AGENTS.md`, `.wopal/docs/DESIGN.md` | 修改 | 模块归属与开关表同步 |

## Acceptance Criteria

### Agent Verification

1. [x] `cd .wopal/plugins/wopal-plugin && bun run typecheck` exit 0
2. [x] `cd .wopal/plugins/wopal-plugin && bun run test:run` 全部 pass
3. [x] `rg -n "distill|Distill" .wopal/plugins/wopal-plugin/src/tools/memory-manage/index.ts` 无命中（蒸馏动作已迁出）
4. [x] `rg -n "distillEngine" .wopal/plugins/wopal-plugin/src/tools/memory-manage` 无命中（依赖已移除）
5. [x] `ls .wopal/plugins/wopal-plugin/src/memory/distill.ts .wopal/plugins/wopal-plugin/src/memory/session-context.ts` 均不存在（已迁移）
6. [x] `ls .wopal/plugins/wopal-plugin/src/context/distill.ts .wopal/plugins/wopal-plugin/src/context/session-context.ts .wopal/plugins/wopal-plugin/src/context/prompts.ts` 均存在
7. [x] `rg -n "distill|confirm|cancel" .wopal/plugins/wopal-plugin/src/tools/context-manage.ts` 命中三个动作
8. [x] `rg -n "context.enabled|contextEnabled" .wopal/plugins/wopal-plugin/src/index.ts` 命中门控逻辑，且 MemorySystem 装配条件为 `store && embedder`（无 `resources.llm` 参与 memory 判定）
9. [x] `rg -n "distill" .wopal/plugins/wopal-plugin/AGENTS.md` 中 memory_manage 相关行不含蒸馏描述，且 context_manage 相关行命中三个蒸馏动作（文档同步，与迁移前状态可区分）
10. [x] `bun run test:run -- src/context src/tools` 全 pass，且测试含以下断言：
    - 「context.enabled=false 时蒸馏动作返回降级提示」
    - 「context.enabled=false 时 compaction 仍生效」
    - 「memory.enabled=true + context.enabled=false 时记忆系统构建、memory_manage 注册」（D-06 解耦反转断言，改写 Plan 2 的 index.test.ts:827 known-coupling 测试）

### User Validation

蒸馏动作往返（distill/confirm/cancel）、开关组合降级提示、工具注册与检索可用性均为可断言行为，已由 Agent Verification 自动化覆盖（AC#3, AC#4, AC#7, AC#10）。

UA 仅保留一项无法自动化、需人工感知的验证：**真实会话中蒸馏候选的质量**（LLM 从对话中提取的记忆候选是否切题、摘要是否准确），这是代码断言无法替代的主观质量判断。

#### Scenario 1: 真实会话中的蒸馏候选质量

- Goal: 确认蒸馏引擎迁移到 context 模块后，候选提取质量与迁移前一致
- 验证环境: 项目 AGENTS.md「Verification Mechanisms」章节（headless 启动 + 插件日志）；对话需先积累若干轮含可记忆事实的真实交互
- Precondition: 本 Plan 已合入，`.wopal/` 在集成分支，`context.enabled=true`（默认）
- 启动命令: `ellamaka run "执行 context_manage distill，汇报候选列表" --print-logs --log-level DEBUG`
- User Actions:
  1. 与 ellamaka 进行 2-3 轮含明确事实的对话（如项目决策、个人偏好）
  2. 执行 `context_manage` 的 distill 动作，观察返回的候选列表内容
  3. 主观评估候选是否切题（提取的是对话中的真实事实而非噪声）、摘要是否准确
- 通过判据: 候选内容与对话事实对应、无系统性噪声候选；迁移前后对比无质量劣化
- 失败反馈: 附 `<space>/.wopal-space/logs/wopal-plugin.log` 相关时段、候选列表原文与对话上下文

- [x] 用户已完成上述功能验证并确认结果符合预期

## Implementation

### Task 1: 蒸馏与会话上下文迁移到 context 模块

**Verification Intent**: AC#1, AC#2, AC#5, AC#6, AC#10

**Behavior**:
输入 → 输出映射：
- 迁移后 `context/distill.ts` 导出与原 `memory/distill.ts` 一致的公开 API（`DistillEngine`、`loadExtractionState`、`clearExtractionState`、`getPendingConfirmation`、`setPendingConfirmation`、`clearPendingConfirmation`）
- 迁移后 `context/session-context.ts` 的存储路径与读写行为不变
- `context/prompts.ts` 提供蒸馏与标题提示词，`memory/prompts.ts` 不再包含它们
- 原 memory 模块文件删除后，全仓无 `from "../memory/distill` 或 `from "./distill` 的悬空引用

**Files**: `src/context/distill.ts`, `src/context/prompts.ts`, `src/context/session-context.ts`, `src/context/index.ts`, `src/memory/distill.ts`（删除）, `src/memory/session-context.ts`（删除）, `src/memory/prompts.ts`, `src/hooks/events/idle-compact-handler.ts`, `src/hooks/conversation-context.ts`, `src/memory/index.ts`, 对应 `*.test.ts`

**Pre-read**: `src/memory/distill.ts`、`src/memory/prompts.ts`、`src/memory/session-context.ts`、`src/hooks/events/idle-compact-handler.ts`、`src/hooks/conversation-context.ts`

**Design**:
分三阶段 TDD：
1. RED：为迁移后的公开 API 契约与提示词归属编写测试（可从原测试平移，断言不变）
2. GREEN：以 `git mv` 保持历史迁移 `distill.ts` 与 `session-context.ts` 到 `src/context/`；拆分 `prompts.ts`；创建 `context/index.ts`；更新全部 import（`memory/index.ts`、`idle-compact-handler`、`conversation-context`、`memory-manage/distill.ts` 的引用）
3. REFACTOR：收敛 context 模块的导出面，清理迁移残留

约束：迁移以行为不变为原则，不改蒸馏算法与提示词内容；`session-context` 的存储路径（`$WOPAL_HOME/storage/session_context`）不变；logger 归属随模块调整（`memoryLogger` → `contextLogger`），但日志语义保持一致；测试文件随源文件迁移并保持断言不变。

**TDD**: true

**Changes**:
1. 迁移 `src/memory/distill.ts` → `src/context/distill.ts`，调整 import 与 logger
2. 拆分 `src/memory/prompts.ts`，蒸馏与标题提示词迁入 `src/context/prompts.ts`
3. 迁移 `src/memory/session-context.ts` → `src/context/session-context.ts`
4. 创建 `src/context/index.ts` 统一导出
5. 更新全部消费方 import（`memory/index.ts`、`hooks/events/idle-compact-handler.ts`、`hooks/conversation-context.ts`）
6. 迁移对应测试文件并保持断言

**Verify**:
`cd .wopal/plugins/wopal-plugin && bun run test:run -- src/context` 全部 pass 且 `bun run typecheck` exit 0

**Done**:
任务产出：蒸馏与会话上下文状态归属 context 模块，原 memory 文件移除，全仓引用一致
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

### Task 2: 蒸馏动作迁移、context 总开关与 memory 装配解耦

**Verification Intent**: AC#1, AC#2, AC#3, AC#4, AC#7, AC#8, AC#10

**Behavior**:
输入 → 输出映射：
- `context_manage` 调用 distill → 返回候选列表；confirm → 写入记忆；cancel → 清空待确认
- `memory_manage` 调用 distill/confirm/cancel → 不再是合法动作（枚举中不存在）
- `context.enabled=false` → 标题生成、自动恢复、蒸馏不生效，`context_manage` 的蒸馏动作返回降级提示
- `context.enabled=false` → compaction 仍生效
- `context.enabled=false` + `memory.enabled=true` → 记忆系统照常构建，`memory_manage` 注册，注入可用（D-06 解耦）
- `context.enabled=true` → 三项能力行为与迁移前一致

**Files**: `src/tools/context-manage.ts`, `src/tools/memory-manage/index.ts`, `src/tools/memory-manage/distill.ts`（删除）, `src/index.ts`, `src/index.test.ts`, 对应 `*.test.ts`

**Pre-read**: `src/tools/context-manage.ts`、`src/tools/memory-manage/index.ts`、`src/hooks/index.ts`、`src/index.ts`（MemorySystem 装配段）、`src/index.test.ts`（known-coupling 测试）

**Design**:
分三阶段 TDD：
1. RED：为 `context_manage` 的蒸馏三动作、`memory_manage` 动作集收窄、`context.enabled=false` 的降级与 compaction 独立性、D-06 解耦组合编写测试；改写 Plan 2 的 `src/index.test.ts:827` known-coupling 测试为解耦后契约（context.enabled=false → memory_manage 仍注册）
2. GREEN：`context-manage.ts` 新增 distill / confirm / cancel 动作并接入 distill 引擎与客户端；`memory-manage/index.ts` 移除蒸馏分支与 `distillEngine` 参数，删除 `memory-manage/distill.ts`；`src/index.ts` 将 MemorySystem 装配条件从 `store && embedder && llm` 改为 `store && embedder`，llm 改由 context 能力消费（蒸馏引擎、generateSessionTitle、自动恢复按 `context.enabled` 门控）；compaction 不受门控
3. REFACTOR：收敛工具动作分发表，清理已无消费者的参数

约束：蒸馏降级提示沿用已有的「requires the memory system to be initialized」同义表述，明确指向 context 能力；`context.enabled=false` 时不得影响 compaction hook 与记忆检索；`memory_manage` 动作枚举收窄后需同步更新工具描述文案；`memory_manage` 注册保持资源可用性驱动（store 存在），不引入配置读取。

**TDD**: true

**Changes**:
1. 修改 `src/tools/context-manage.ts`：新增 distill / confirm / cancel 动作
2. 修改 `src/tools/memory-manage/index.ts`：移除蒸馏动作与 `distillEngine` 参数，更新描述文案
3. 删除 `src/tools/memory-manage/distill.ts`
4. 修改 `src/index.ts`：MemorySystem 装配条件解耦（`store && embedder`）+ context 总开关门控三项能力
5. 修改 `src/hooks/index.ts`：context 总开关门控装配，compaction 不受影响
6. 改写 `src/index.test.ts` known-coupling 测试为 D-06 解耦契约
7. 修改/创建对应测试

**Verify**:
`cd .wopal/plugins/wopal-plugin && bun run test:run -- src/tools` 全部 pass 且 `bun run typecheck` exit 0

**Done**:
任务产出：context_manage 承接蒸馏动作，memory_manage 净化为纯记忆操作，context 总开关门控三项能力，memory/context 装配解耦（context.enabled=false 不再影响记忆系统）
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

### Task 3: 文档同步

**Verification Intent**: AC#9

**Behavior**:
- 插件 AGENTS.md 的工具说明反映蒸馏归属：`memory_manage` 描述不含蒸馏动作、`context_manage` 描述含 distill / confirm / cancel
- ontology DESIGN.md §4.5 插件模块表与插件总体设计对齐

**Files**: `.wopal/plugins/wopal-plugin/AGENTS.md`, `.wopal/docs/DESIGN.md`

**Pre-read**: `.wopal/docs/DESIGN-wopal-plugin.md`

**Design**:
按 DESIGN-wopal-plugin.md 的目标态改写两处文档。Plan 2 已完成 AGENTS.md 模块表 context 可配置状态与 §8 Config Nodes（AC#9 前置已部分达成），本任务仅同步蒸馏归属：AGENTS.md 工具说明更新 `memory_manage`（移除蒸馏动作描述）/ `context_manage`（新增三动作）的动作集；DESIGN.md §4.5 模块表删除「Disable Switch」列，改为「可配置」列并与插件总体设计对齐。

**TDD**: false

<!-- false: 纯文档变更，无业务逻辑。 -->

**Changes**:
1. 修改 `.wopal/plugins/wopal-plugin/AGENTS.md`：工具说明同步蒸馏归属
2. 修改 `.wopal/docs/DESIGN.md` §4.5：模块表对齐插件总体设计

**Verify**:
`rg -n "memory_manage" .wopal/plugins/wopal-plugin/AGENTS.md` 相关行不含蒸馏描述，且 `rg -n "distill" .wopal/plugins/wopal-plugin/AGENTS.md` 命中 context_manage 三动作说明

**Done**:
任务产出：插件开发规范与 ontology 设计文档与实现一致
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

## Delegation Strategy

| Wave | Task | 执行者 | 依赖 | 委派理由 |
|------|------|--------|------|---------|
| 1 | Task 1 | fae | Plan 1、Plan 2 归档 | 跨模块文件迁移，需完整上下文，单独委派 |
| 2 | Task 2 | fae | Task 1 | 工具动作迁移与装配解耦依赖模块归属就位 |
| 3 | Task 3 | Wopal | Task 2 | 纯文档小变更，按委派边界规则直接执行 |

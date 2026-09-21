# refactor-plugin-2-switches-and-diagnostics

## Metadata

- **Issue**: (无)
- **Type**: refactor
- **Target Project**: wopal-space-ontology

- **Project Path**: .wopal
- **Project Type**: ontology-worktree
- **Created**: 2026-09-11
- **Status**: done
- **Verification Commit**: 4d1f9ac427a1fb6595715cd95d76256acd5f3b83
- **Worktree**:
  - branch: wopal-space-ontology-refactor-plugin-2-switches-and-diagnostics
  - path: (removed)
- **Verification Dir**: /Volumes/U500G/coding/wopal-workspace/.wopal
- **Base Commit**: 188722063cc3f2f8b5b22fb3d466d5250ca9fd6d
- **Final Commit**: d8e54281182010a18a7ce49cf028fff07dcd726c

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High
- **Phase**: 2 / 3（能力开关与诊断）

## Plan Dependencies

本期重构拆分为三个串行 Plan，必须按序实施，不可并行：

| Plan | Phase | 依赖 | 说明 |
|------|-------|------|------|
| `refactor-plugin-1-config-and-resources` | 1 / 3 | 无 | 交付配置加载器与资源层地基 |
| `refactor-plugin-2-switches-and-diagnostics` | 2 / 3 | Plan 1 | 本 Plan。消费配置契约与资源层接线能力开关 |
| `refactor-plugin-3-distill-to-context` | 3 / 3 | Plan 1、Plan 2 | 迁移蒸馏归属并接入 context 总开关 |

**启动前置**：Plan 1 必须已归档（状态 `done` 并完成 archive），本 Plan 方可启动。

**完成定义**：本 Plan 归档后，Plan 3 方可启动。三者改动同一批文件与装配链，且本 Plan 的 capabilities 结构是 Plan 3 门控模式的直接前提，因此必须串行。

## Goal

将配置驱动的能力开关接入插件运行时：`memory.enabled` 经资源层控制记忆系统本体（`memory_manage` 注册随之），`memory.injection` 控制自动注入置位；Rules 移除残留旗标后恒启用。日志配置迁入配置文件并保留诊断 env 覆盖；顺带完成三项低风险修复（prompts 惰性构建、注入标志门控前移、任务解析器诊断文案）。

## Technical Context

### Architecture Context

前置 Plan（`refactor-plugin-1-config-and-resources`）已交付三层配置加载器与资源层，但功能开关尚未接线到运行时：配置能读、资源能按需建，但 hook 装配与工具注册仍走旧的布尔 `RuntimeEnvironment` 判断（`src/index.ts:134-136`）。

`HookContext` 当前以 `rulesInjectionEnabled` / `memoryInjectionEnabled` 两个布尔旗标传递能力状态（`src/hooks/index.ts:35-36`、`:59-60`）。其中 `rulesInjectionEnabled` 在 DESIGN §4.2 中不存在配置开关（Rules 默认启用），移除后应恒为启用；`memoryInjectionEnabled` 需要保留并改为 capabilities 结构。`message-hooks.ts` 在未检查开关的情况下无条件置位 `needsMemoryInjection`（`:49`、`:125`），功能关闭时每条消息仍产生一次无效 store 写。`memory_manage` 以 `store` 是否存在决定注册（`src/tools/index.ts:31`），禁用时工具直接消失且无日志说明原因。

日志配置读自 `WOPAL_PLUGIN_LOG_LEVEL` / `_FILE` / `_MODULES`（`src/logger.ts:24-46`），与功能开关混在同一命名空间。目标态见 `.wopal/docs/DESIGN-wopal-plugin.md` §4.2、§4.3、§5.4。

### Research Findings

- 目标态配置契约与资源层契约已在前置 Plan 定义（`WopalPluginConfig`、`PluginResources`）
- 注入门控前移的现实收益：`needsMemoryInjection` 在 `message-hooks` 置位（`src/hooks/message-hooks.ts`），injector 内部虽有 early return 兜底，但置位动作本身会触发会话状态写入
- 日志诊断保留 env 通道的理由：启动脚本按进程场景动态传入日志级别与位置，静态配置无法表达该变化

**参考资料**：
- `.wopal/docs/DESIGN-wopal-plugin.md` — 插件总体设计（§4.3 Memory 模块、§4.6 Monitor、§5.3 环境变量角色）

### Key Decisions

- D-01: `HookContext` 以 capabilities 结构替换布尔旗标，新字段可选且默认 true（遵循插件 AGENTS.md「New HookContext field: Must be optional, default true」）
- D-02: 功能开关唯一来源为配置文件，hook 与工具层只消费已解析配置，不读 env；Rules 不设配置开关，注入恒启用
- D-03: `memory_manage` 注册条件为 **资源可用性**（`store` 是否存在），而非独立的 `memory.enabled` 布尔。理由：`resolveResources` 已按 `config.memory.enabled` 决定是否构造 store，注册再读一次配置会形成双重真相源；工具可用当且仅当其依赖存在。禁用时由 `index.ts` 输出 info 日志，区分「配置关闭」（`config.memory.enabled=false`）与「初始化失败」（配置启用但 store 缺失）
- D-04: 日志配置以「配置文件为默认值 + 诊断 env 为覆盖」组合，env 覆盖优先级更高
- D-05: prompts 改为惰性构建，消费方调用时才加载

### Key Interfaces

```typescript
// HookContext 的能力结构（替换 rulesInjectionEnabled / memoryInjectionEnabled）
// 注意：不含 rules 旗标 —— Rules 恒启用（DESIGN §4.2）
interface HookCapabilities {
  memoryInjectionEnabled?: boolean; // 默认 true；控制 needsMemoryInjection 置位与注入
}

// memory_manage 注册输入（资源可用性驱动，非独立布尔）
interface MemoryToolInput {
  store?: MemoryStore;        // 有则注册
  embedder?: EmbeddingClient;
  distillEngine?: DistillEngine;
}

// 日志配置解析契约
interface ResolvedLogConfig {
  level: string;
  file?: string;
  modules?: string[];
}
```

## In Scope

- 移除 `src/index.ts` 中三处功能 env 开关兼容读取（`WOPAL_RULES_INJECTION_ENABLED`、`WOPAL_MEMORY_ENABLED`、`WOPAL_MEMORY_INJECTION_ENABLED`），完成运行时切换
- `memory.enabled` 接线：经资源层控制记忆系统构建，`memory_manage` 注册随资源可用性；`memory.injection` 接线：注入能力门控与 `needsMemoryInjection` 前置判断
- Rules 注入开关归位：移除读取后按 DESIGN §4.2 恒启用（Rules 不暴露配置开关），不再保留布尔旗标
- `HookContext` 布尔旗标 → capabilities 结构
- 日志配置迁入配置文件，保留 `WOPAL_PLUGIN_LOG_*` env 覆盖
- prompts 惰性构建
- 任务解析器（`task-resolver.ts`）歧义诊断文案修复

## Out of Scope

- context 模块总开关与蒸馏迁移 — 由后续 Plan 承接
- 资源层本身（已在前置 Plan 完成）
- 记忆检索算法、注入内容构造逻辑的行为变更
- 日志格式与 logger 分级策略变更

## Known Coupling

`MemorySystem` 的构建当前要求 `store && embedder && llm` 三者齐备（`src/index.ts`），而 llm 资源由 `context.enabled` 门控（Plan 1 已接线）。因此关闭 `context.enabled` 会连带使记忆系统整体不构建。本 Plan 保持该行为不变（context 归属 Plan 3），但需在 Task 1 的测试中显式覆盖该组合，避免被当作回归。

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| Hooks | `src/hooks/index.ts` | 修改 | `HookContext` 改用 capabilities 结构 |
| Hooks | `src/hooks/message-hooks.ts` | 修改 | `needsMemoryInjection` 置位前检查注入能力 |
| Hooks | `src/hooks/memory-message-injector.ts` | 修改 | 保留内部 early return 作为纵深防御 |
| Tools | `src/tools/index.ts` | 修改 | `memory_manage` 按 `memory.enabled` 条件注册 |
| Entry | `src/index.ts` | 修改 | hook 装配与工具注册接入配置 |
| Logger | `src/logger.ts` | 修改 | 日志配置改为「配置默认 + env 覆盖」 |
| Memory | `src/memory/prompts.ts` | 修改 | 惰性构建 |
| Tasks | `src/tasks/task-resolver.ts` | 修改 | 歧义诊断文案修复 |
| Tests | 对应 `*.test.ts` | 修改/创建 | 开关组合、日志优先级、文案断言 |

## Acceptance Criteria

### Agent Verification

1. [x] `cd .wopal/plugins/wopal-plugin && bun run typecheck` exit 0
2. [x] `cd .wopal/plugins/wopal-plugin && bun run test:run` 全部 pass (919/919)
3. [x] `rg -n "rulesInjectionEnabled|memoryInjectionEnabled" .wopal/plugins/wopal-plugin/src --glob '!*.test.ts'` `rulesInjectionEnabled` 零命中；`memoryInjectionEnabled` 仅存在于 capabilities 结构内部（符合 Key Interfaces 命名，布尔旗标已替换为结构）
4. [x] `rg -n "WOPAL_RULES_INJECTION_ENABLED|WOPAL_MEMORY_ENABLED|WOPAL_MEMORY_INJECTION_ENABLED" .wopal/plugins/wopal-plugin/src --glob '!*.test.ts'` 零命中（三处 env 兼容读取已彻底移除）
5. [x] `bun run test:run -- src/logger.test.ts` 37/37 pass，且测试断言日志优先级「配置 logLevel 生效」「env 覆盖配置」「两者皆无时默认 info」三种组合
6. [x] `rg -n "store" .wopal/plugins/wopal-plugin/src/tools/index.ts` 命中 `memory_manage` 的条件注册分支（`if (store)`），且 `rg -n "config" .wopal/plugins/wopal-plugin/src/tools/index.ts` 零命中（工具层不直接读配置）
7. [x] `bun run test:run -- src/hooks src/index.test.ts` 129/129 pass，含「injection=false 时 needsMemoryInjection 不被置位」与「store 缺失时 memory_manage 不注册」断言（message-hooks.test.ts 4 用例、tools/wopal-tools.test.ts）
8. [x] `bun run test:run -- src/index.test.ts` 21/21 pass，且含「context.enabled=false 时记忆系统不构建」（KNOWN COUPLING 显式断言，index.test.ts:827）与「memory.enabled=false 不注册+disabled_by_config 日志」（:772）
9. [x] `rg -n "Ambiguous task reference" .wopal/plugins/wopal-plugin/src/tasks/task-resolver.ts` 命中单一语言文案「Ambiguous task reference: ... Use one of the full task IDs:」，且 `rg -n "\(ambiguous\)"` 零命中（重复类型标签已去除）

### User Validation

本 Plan 的可断言行为（开关组合、工具注册、日志优先级、注入标志）均由 Agent Verification 自动化覆盖。

UA 仅保留一项无法自动化、需人工感知的验证：记忆注入在真实对话中的**自然度与连贯性**（回答是否恰当引用记忆、关闭注入后对话是否流畅无异常），这是代码断言无法替代的主观质量判断。

#### Scenario 1: 真实会话中的记忆注入体验

- Goal: 确认开启注入时记忆内容自然融入对话，关闭注入后检索能力保留且对话无异常
- 验证环境: 项目 AGENTS.md「Verification Mechanisms」章节（headless 启动 + 插件日志）；需先用 `memory_manage add` 写入一条带独特关键词的记忆作为检索目标
- Precondition: 本 Plan 已合入，`.wopal/` 在 feature 分支，`memory.enabled=true`
- 启动命令: `ellamaka run "我之前关于 <关键词> 是怎么决定的？" --print-logs --log-level DEBUG`
- User Actions:
  1. 以上命令提问一个能命中既有记忆的问题，观察回答是否自然引用记忆内容（而非生硬罗列）
  2. 在空间配置写入 `"wopal": { "memory": { "injection": false } }`，重启后以同一问题再问，观察回答不再携带记忆上下文
  3. 在同一会话执行 `memory_manage search <关键词>`，确认检索仍返回结果
- 通过判据: 开启时回答有上下文连续性且引用恰当；关闭后无记忆注入痕迹、检索仍可用、对话无报错
- 失败反馈: 附 `<space>/.wopal-space/logs/wopal-plugin.log` 相关时段与 `git diff -w` 输出

- [x] 用户已完成上述功能验证并确认结果符合预期

## Implementation

### Task 1: memory 注入开关接线与 capabilities 结构

**Verification Intent**: AC#1, AC#2, AC#3, AC#4, AC#6, AC#7, AC#8

**Behavior**:
输入 → 输出映射：
- `memory.enabled=false` → 资源层不构造 store（Plan 1 已实现），`memory_manage` 不注册，`index.ts` info 日志说明「配置关闭」
- `memory.enabled=true` 但 store 构造失败 → `memory_manage` 不注册，info 日志说明「初始化失败」
- `memory.enabled=true, injection=false` → `memory_manage` 注册可用；`needsMemoryInjection` 不被置位
- `memory.enabled=true, injection=true` → 注入行为与迁移前一致
- `context.enabled=false` → 记忆系统整体不构建（KNOWN COUPLING，行为与现状一致）
- `HookContext` 未传 capabilities 字段 → 默认按 true 处理（向后兼容）
- Rules 注入 → 恒启用（移除旗标后不再有开关路径）

**Files**: `src/hooks/index.ts`, `src/hooks/message-hooks.ts`, `src/hooks/memory-message-injector.ts`, `src/tools/index.ts`, `src/index.ts`, 对应 `*.test.ts`

**Pre-read**: `src/hooks/index.ts`（`HookContext` 与 `createAllHooks`）、`src/hooks/message-hooks.ts`、`src/hooks/memory-message-injector.ts`、`src/tools/index.ts`、`src/index.ts`（资源装配段）

**Design**:
分三阶段 TDD：
1. RED：为开关组合下的工具注册与注入标志行为编写测试（含 store 缺失、injection 关闭、context 关闭三种）
2. GREEN：`hooks/index.ts` 移除 `rulesInjectionEnabled`、将 `memoryInjectionEnabled` 收入 capabilities 结构（字段可选、默认 true）；`message-hooks.ts` 在置位 `needsMemoryInjection` 前检查注入能力；`memory-message-injector.ts` 保留内部 early return 作为纵深防御；`tools/index.ts` 保持以 `store` 存在为注册条件（不引入配置读取）；`index.ts` 移除三处 env 读取，从已解析配置注入能力状态并在工具未注册时按原因输出 info 日志
3. REFACTOR：清理 `HookContext` 中已无消费者的字段

约束：hook 与工具层只消费已解析状态，不直接读 env 也不直接读配置对象（配置→能力状态的转换在 `index.ts` 完成）；`memory_manage` 注册条件保持单一真相源（资源可用性）；新字段遵循 AGENTS.md「New HookContext field: Must be optional, default true」；Rules 移除旗标后恒启用，不新增配置项。

**TDD**: true

**Changes**:
1. 修改 `src/hooks/index.ts`：移除 `rulesInjectionEnabled`，`memoryInjectionEnabled` 收入 capabilities 结构
2. 修改 `src/hooks/message-hooks.ts`：`needsMemoryInjection` 置位前检查注入能力
3. 修改 `src/hooks/memory-message-injector.ts`：对齐 capabilities 字段命名
4. 修改 `src/tools/index.ts`：`memory_manage` 注册保持资源可用性驱动（如有必要，仅调整注释与日志接入点）
5. 修改 `src/index.ts`：移除三处 env 读取，配置→能力状态转换在此完成，工具未注册时按原因输出 info 日志

**Verify**:
`cd .wopal/plugins/wopal-plugin && bun run test:run -- src/hooks src/tools src/index.test.ts` 全部 pass 且 `bun run typecheck` exit 0

**Done**:
任务产出：memory 注入开关生效，注入独立可关且不影响检索，工具按资源可用性注册并说明原因，Rules 恒启用
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

### Task 2: 日志配置接入与 P7 修复

**Verification Intent**: AC#1, AC#2, AC#5, AC#9

**Behavior**:
输入 → 输出映射：
- 配置 `logLevel="debug"` 且无 env 覆盖 → logger 阈值为 debug
- 配置 `logLevel="debug"` 且 `WOPAL_PLUGIN_LOG_LEVEL=warn` → logger 阈值为 warn
- 配置未提供 logLevel 且无 env → 默认 info
- `memory.enabled=false` 或无 memory 消费方 → 不构建 memory prompts
- 消费方调用 prompts → 按需加载且内容与迁移前一致
- resolver 歧义错误消息 → 单一语言，无重复类型标签

**Files**: `src/logger.ts`, `src/index.ts`, `src/memory/prompts.ts`, `src/tasks/task-resolver.ts`, 对应 `*.test.ts`

**Pre-read**: `src/logger.ts`、`src/memory/prompts.ts`、`src/tasks/task-resolver.ts`

**Design**:
分三阶段 TDD：
1. RED：为日志优先级（配置默认 < env 覆盖）、prompts 惰性构建、resolver 文案编写测试
2. GREEN：`logger.ts` 接受已解析日志配置，env 仅作覆盖；`prompts.ts` 改为按需构建（首次调用时加载并缓存）；`task-resolver.ts` 清理歧义消息中的双语与重复类型标签；`index.ts` 传递日志配置
3. REFACTOR：清理 prompts 全局构建残留

约束：env 覆盖只作用于诊断项，不影响功能开关；prompts 惰性化不改变内容与缓存语义；resolver 文案修改不改变错误分类逻辑。

**TDD**: true

**Changes**:
1. 修改 `src/logger.ts`：日志配置改为「配置默认 + env 覆盖」
2. 修改 `src/index.ts`：传递已解析日志配置
3. 修改 `src/memory/prompts.ts`：惰性构建
4. 修改 `src/tasks/task-resolver.ts`：修复歧义诊断文案
5. 修改/创建对应测试

**Verify**:
`cd .wopal/plugins/wopal-plugin && bun run test:run -- src/logger.test.ts src/tasks/task-resolver.test.ts` 全部 pass

**Done**:
任务产出：日志配置进配置文件且保留 env 覆盖；prompts 惰性构建；resolver 文案修正
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

## Delegation Strategy

| Wave | Task | 执行者 | 依赖 | 委派理由 |
|------|------|--------|------|---------|
| 1 | Task 1 | fae | Plan 1 归档 | 开关接线是本节核心，改动跨 hook 与 tool |
| 1 | Task 2 | fae | Plan 1 归档 | 日志与 P7 修复相对独立，可与 Task 1 并行 |

# refactor-wopal-plugin-modular-loading-and-log-prefix

## Metadata

- **Type**: refactor
- **Project**: wopal-space-ontology
- **Created**: 2026-05-13
- **Status**: done

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

实现插件模块化加载：禁用时模块代码完全不执行；日志归属正确化（prefix 去掉 `wopal-` 前缀，模块细节由模块自己打印）。

## Technical Context

当前插件架构存在以下问题：

1. **禁用开关作用域混乱**：`WOPAL_RULES_INJECTION_ENABLED=false` 时，规则发现仍执行并打印日志；`WOPAL_MEMORY_INJECTION_ENABLED=false` 时，Memory 系统仍初始化
2. **日志归属错误**：`discoverRuleFiles()` 内部创建默认 `debugLog()` 导致规则发现日志标记为 `[wopal-plugin]`；Memory 初始化日志也用顶层 `debugLog`
3. **Prefix 冗余**：`[wopal-plugin]`、`[wopal-rules]` 等包含多余的 `wopal-` 前缀

### Architecture Design

#### 模块划分

插件由 1 个 Global 层 + 4 个功能模块组成：

| 模块 | 禁用开关 | 启动时行为 | 运行时行为 |
|------|---------|-----------|-----------|
| **Global (Plugin)** | 无 | 加载 .env、检查所有开关、报告禁用状态、注册 Hooks/Tools | Plugin 生命周期日志 |
| **Rules** | `WOPAL_RULES_INJECTION_ENABLED` | 禁用时跳过 `discoverRuleFiles()`，`ruleFiles = []` | 禁用时跳过 `injectRules()` |
| **Memory** | `WOPAL_MEMORY_ENABLED` | 禁用时跳过 `ensureMemorySystem()`，`memory = null` | 禁用时工具不注册、注入不执行 |
| **Task** | 无（始终启用） | `SimpleTaskManager` 初始化 + cleanup handlers | 任务委派、idle 监控、双向通信 |
| **Context** | 无（始终启用） | 无启动逻辑 | 会话摘要、user prompt 更新、snapshot、compaction |

#### Memory 双开关逻辑

```
WOPAL_MEMORY_ENABLED=true   + WOPAL_MEMORY_INJECTION_ENABLED=true   → 完整功能（初始化 + 注入 + 工具）
WOPAL_MEMORY_ENABLED=true   + WOPAL_MEMORY_INJECTION_ENABLED=false  → 初始化正常，注入跳过，工具可用
WOPAL_MEMORY_ENABLED=false  + (忽略 INJECTION)                      → 模块不初始化，工具不注册
```

默认均为 `true`。`WOPAL_MEMORY_ENABLED=false` 时 `WOPAL_MEMORY_INJECTION_ENABLED` 被忽略。

#### 环境变量清单

| 变量 | 默认值 | 控制范围 |
|------|--------|---------|
| `WOPAL_RULES_INJECTION_ENABLED` | `true` | Rules 模块整体（发现 + 注入） |
| `WOPAL_MEMORY_ENABLED` | `true` | Memory 模块整体（初始化 + 注入 + 工具） |
| `WOPAL_MEMORY_INJECTION_ENABLED` | `true` | 仅 Memory 注入（不影响工具和 distill） |
| `WOPAL_PLUGIN_DEBUG` | (空) | 调试日志过滤：`1`/`*`/`all` 全部，或逗号分隔模块名 |
| `WOPAL_PLUGIN_LOG_FILE` | (tmpdir) | 日志文件路径 |

#### 启动流程（index.ts）

```
1. pluginDebugLog("Plugin loaded! directory: ...")

2. loadWopalEnv()                                           // 静默加载 .env

3. 读开关（loadWopalEnv 之后，确保 .env 已生效）:
   rulesEnabled          = WOPAL_RULES_INJECTION_ENABLED  !== "false"
   memoryEnabled         = WOPAL_MEMORY_ENABLED            !== "false"
   memoryInjectionEnabled = WOPAL_MEMORY_INJECTION_ENABLED !== "false"

4. Rules 模块初始化:
   if (rulesEnabled) {
     rulesDebugLog("Discovering rule files...")
     ruleFiles = discoverRuleFiles(dir, rulesDebugLog)      // 传入模块级 log
     rulesDebugLog(`Discovered ${N} rule files`)
   } else {
     pluginDebugLog("Rules module disabled")                // Global 层报告一次
     ruleFiles = []
   }

5. Memory 模块初始化:
   if (memoryEnabled) {
     memory = ensureMemorySystem()                          // 内部用 [memory] 日志
   } else {
     pluginDebugLog("Memory module disabled")               // Global 层报告一次
     memory = null
   }

6. Task 模块初始化（始终）:
   taskManager = new SimpleTaskManager(...)

7. 创建 HookContext:
   传入 ruleFiles, memory?.injector,
   rulesInjectionEnabled, memoryInjectionEnabled

8. 注册 Hooks + Tools:
   - memory_manage:   仅 memory != null 时注册
   - context_manage:  仅 memory != null 时注册
   - wopal_task_*:    始终注册

9. pluginDebugLog("Plugin initialized: tools=[...], memory=...")
```

#### 运行时注入流程（system-transform.ts）

```
onSystemTransform(hookInput, output):

  // 1. Session state 检查（Global 层）
  skip = sessionStore.shouldSkipInjection(sessionID)
  if (skip) return output

  // 2. Rules 注入（受 rulesInjectionEnabled 控制）
  if (ctx.rulesInjectionEnabled) {
    formattedRules = await injectRules(ruleInjectorCtx, ...)
    if (formattedRules) output.system.push(formattedRules)
  }
  // 禁用时无日志，代码不执行

  // 3. Memory 注入（受 memoryInjectionEnabled 控制）
  if (ctx.memoryInjectionEnabled && ctx.memoryInjector && sessionID) {
    await injectMemoriesIntoSystem(memoryInjectorCtx, sessionID, output)
  }
  // 禁用时无日志，代码不执行

  // 4. Context 模块（始终运行，不受任何开关影响）
  // snapshot, metadata, auto-dump...

  return output
```

#### 日志归属规范

| 日志内容 | 归属模块 | Prefix | Module |
|---------|---------|--------|--------|
| Plugin loaded/initialized | Global | `[plugin]` | `plugin` |
| Rules disabled（一次性） | Global | `[plugin]` | `plugin` |
| Memory disabled（一次性） | Global | `[plugin]` | `plugin` |
| 规则发现/匹配/注入细节 | Rules | `[rules]` | `rules` |
| LanceDB/Embedding/LLM 初始化 | Memory | `[memory]` | `memory` |
| 记忆检索/注入细节 | Memory | `[memory]` | `memory` |
| 任务委派/监控/通信 | Task | `[task]` | `task` |
| 会话状态/snapshot/compaction | Context | `[context]` | `context` |

**原则**：
- 禁用状态在 Global 层（`[plugin]`）报告**一次**
- 模块细节由模块自己的 log 打印
- 禁用时模块代码**完全不执行**（包括 discovery/initialization）
- Module name（`plugin`/`rules`/`task`/`memory`/`context`）用于 `WOPAL_PLUGIN_DEBUG` 过滤，不变

#### HookContext 数据结构

```typescript
interface HookContext {
  client: unknown;
  directory: string;
  projectDirectory: string;
  ruleFiles: DiscoveredRule[];
  sessionStore: SessionStore;
  pluginDebugLog: DebugLog;          // [plugin] / plugin
  rulesDebugLog: DebugLog;           // [rules]  / rules
  taskDebugLog: DebugLog;            // [task]   / task
  memoryDebugLog: DebugLog;          // [memory] / memory
  contextDebugLog: DebugLog;         // [context]/ context
  now: () => number;
  taskManager: SimpleTaskManager | undefined;
  memoryInjector: MemoryInjector | undefined;
  childSessionCache: Map<string, boolean>;
  systemSnapshots: Map<string, string[]>;
  systemMetadataMap: Map<string, SystemPromptMetadata>;
  systemInjectionsMap: Map<string, string[]>;
  rulesInjectionEnabled: boolean;    // 新增
  memoryInjectionEnabled: boolean;   // 新增
}
```

#### 各模块 createDebugLog 调用规范

模块内部文件应使用对应模块的 prefix + module 创建 log：

| 文件类别 | 当前 prefix | 目标 prefix | module |
|---------|------------|------------|--------|
| `src/index.ts` (Global) | `[wopal-plugin]` | `[plugin]` | `plugin` |
| `src/hooks/index.ts` | `[wopal-plugin]`, `[wopal-rules]` 等 | `[plugin]`, `[rules]` 等 | 对应 module |
| `src/rules/*` | `[wopal-plugin]`（默认） | `[rules]` | `rules` |
| `src/memory/*` | `[wopal-memory]` | `[memory]` | `memory` |
| `src/tasks/*` | `[wopal-task]` | `[task]` | `task` |
| `src/tools/context-manage.ts` | `[wopal-context]` | `[context]` | `context` |
| `src/tools/wopal-task-*.ts` | `[wopal-task]` | `[task]` | `task` |
| `src/tools/dump-formatter.ts` | `[wopal-context]` | `[context]` | `context` |

#### discoverRuleFiles 签名变更

已完成（本上下文内）。当前签名：

```typescript
export async function discoverRuleFiles(
  projectDir?: string,
  rulesDebugLog?: DebugLog,      // 可选，传入时用模块级 log 打印发现日志
): Promise<DiscoveredRule[]>
```

调用方负责传入 `rulesDebugLog`，不再内部创建。

## In Scope

- Prefix 全量替换：`[wopal-xxx]` → `[xxx]`
- `debug.ts` 默认 prefix 改 `[plugin]`
- `index.ts` 启动流程重写：模块化加载 + 开关控制
- Memory 双开关逻辑：`WOPAL_MEMORY_ENABLED`（全局禁用） + `WOPAL_MEMORY_INJECTION_ENABLED`（仅禁用注入）
- `HookContext` 扩展：传递 `rulesInjectionEnabled` + `memoryInjectionEnabled`
- `system-transform.ts` 移除 "disabled by environment variable" 日志
- `rules/formatter.ts` 修正 log 归属

## Out of Scope

- 拆分不同模块的注入 system prompt 功能（后续重构 user message 注入时再做）
- Task/Context 模块的禁用开关（无需）

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| Core | `src/debug.ts` | 修改 | 默认 prefix `[plugin]` |
| Entry | `src/index.ts` | 修改 | 启动流程重写 + 开关控制 |
| Hooks | `src/hooks/index.ts` | 修改 | HookContext 扩展 + prefix 更新 |
| Hooks | `src/hooks/system-transform.ts` | 修改 | 移除 disabled 日志 + 从 ctx 读开关 |
| Rules | `src/rules/discoverer.ts` | 已改 | 接受外部 rulesDebugLog（本上下文已完成） |
| Rules | `src/rules/formatter.ts` | 修改 | `createDebugLog()` → `createDebugLog("[rules]", "rules")` |
| Memory | `src/memory/store.ts` | 修改 | prefix `[memory]` |
| Memory | `src/memory/injector.ts` | 修改 | prefix `[memory]` |
| Memory | `src/memory/retriever.ts` | 修改 | prefix `[memory]` |
| Memory | `src/memory/embedder.ts` | 修改 | prefix `[memory]` |
| Memory | `src/memory/llm-client.ts` | 修改 | prefix `[memory]` |
| Memory | `src/memory/distill.ts` | 修改 | prefix `[memory]` |
| Memory | `src/memory/dedup.ts` | 修改 | prefix `[memory]` |
| Memory | `src/memory/prompts.ts` | 修改 | prefix `[memory]` |
| Memory | `src/memory/session-context.ts` | 修改 | prefix `[memory]` |
| Task | `src/tasks/simple-task-manager.ts` | 修改 | prefix `[task]` |
| Task | `src/tasks/progress.ts` | 修改 | prefix `[task]` |
| Task | `src/tasks/idle-diagnostic.ts` | 修改 | prefix `[task]` |
| Task | `src/tasks/loop-detector.ts` | 修改 | prefix `[task]` |
| Task | `src/tasks/permission-proxy.ts` | 修改 | prefix `[task]` |
| Task | `src/tasks/question-relay.ts` | 修改 | prefix `[task]` |
| Task | `src/tasks/process-cleanup.ts` | 修改 | prefix `[task]` |
| Task | `src/tasks/task-completion-notify.ts` | 修改 | prefix `[task]` |
| Tools | `src/tools/wopal-task-output.ts` | 修改 | prefix `[task]` |
| Tools | `src/tools/wopal-task-reply.ts` | 修改 | prefix `[task]` |
| Tools | `src/tools/wopal-task-diff.ts` | 修改 | prefix `[task]` |
| Tools | `src/tools/output-helpers.ts` | 修改 | prefix `[task]` |
| Tools | `src/tools/context-manage.ts` | 修改 | prefix `[context]` |
| Tools | `src/tools/dump-formatter.ts` | 修改 | prefix `[context]` |
| Tests | `src/debug.test.ts` | 修改 | prefix 同步更新 |

## Implementation

### Task 1: Prefix 批量替换

**Files**: 20+ files（memory/*, tasks/*, tools/*, hooks/*）

**Changes**:

- [x] Step 1: 替换 `[wopal-plugin]` → `[plugin]`（3 文件）
- [x] Step 2: 替换 `[wopal-rules]` → `[rules]`（5 文件）
- [x] Step 3: 替换 `[wopal-task]` → `[task]`（14 文件）
- [x] Step 4: 替换 `[wopal-memory]` → `[memory]`（10 文件）
- [x] Step 5: 替换 `[wopal-context]` → `[context]`（4 文件）

**Verification**:

- [x] Step 1: grep 确认无 `[wopal-` 残留
- [x] Step 2: 单元测试通过

### Task 2: debug.ts 默认 prefix

**Files**: `src/debug.ts`

**Changes**:

- [x] Step 1: `createDebugLog()` 默认 prefix 从 `[wopal-plugin]` 改为 `[plugin]`

**Verification**:

- [x] Step 1: 单元测试通过（debug.test.ts 需同步更新）

### Task 3: index.ts 启动流程重写

**Files**: `src/index.ts`

**Changes**:

- [x] Step 1: 读三开关（在 `loadWopalEnv` 之后）：`WOPAL_RULES_INJECTION_ENABLED`、`WOPAL_MEMORY_ENABLED`（新增）、`WOPAL_MEMORY_INJECTION_ENABLED`
- [x] Step 2: Rules 模块：`rulesEnabled` 为 true 时调用 `discoverRuleFiles(dir, rulesDebugLog)` 打印发现日志；false 时跳过调用，`ruleFiles = []`，Global 层用 `pluginDebugLog` 报告 "Rules module disabled"
- [x] Step 3: Memory 模块：`memoryEnabled` 为 true 时调用 `ensureMemorySystem()`（内部日志用 `memoryDebugLog`）；false 时跳过调用，`memory = null`，Global 层用 `pluginDebugLog` 报告 "Memory module disabled"
- [x] Step 4: 移除模块级 `memoryDebugLog` 声明（改为在 `ensureMemorySystem()` 函数内部创建局部 `memoryDebugLog`）
- [x] Step 5: `ensureMemorySystem()` 内部用 `createDebugLog("[memory]", "memory")` 替代顶层 `debugLog`，初始化日志归属正确
- [x] Step 6: 工具注册逻辑：`memory_manage` 和 `context_manage` 仅在 `memory != null` 时注册
- [x] Step 7: `createHookContext()` 调用新增 `rulesInjectionEnabled` 和 `memoryInjectionEnabled` 参数

**Verification**:

- [x] Step 1: 禁用 Rules：`WOPAL_RULES_INJECTION_ENABLED=false` → `WOPAL_PLUGIN_DEBUG=1` 日志中只有 `[plugin] Rules module disabled`，无 `[rules]` 发现日志
- [x] Step 2: 禁用 Memory：`WOPAL_MEMORY_ENABLED=false` → `WOPAL_PLUGIN_DEBUG=1` 日志中只有 `[plugin] Memory module disabled`，无 `[memory]` LanceDB/Embedding 日志
- [x] Step 3: 禁用 Memory Injection：`WOPAL_MEMORY_ENABLED=true` + `WOPAL_MEMORY_INJECTION_ENABLED=false` → `[memory]` 初始化日志出现，但 system transform 不注入
- [x] Step 4: 单元测试通过

### Task 4: HookContext 扩展 + system-transform 适配

**Files**: `src/hooks/index.ts`, `src/hooks/system-transform.ts`

**Changes**:

- [x] Step 1: `HookContextOptions` 接口新增可选字段：`rulesInjectionEnabled?: boolean`, `memoryInjectionEnabled?: boolean`（默认 true）
- [x] Step 2: `HookContext` 接口新增字段：`rulesInjectionEnabled: boolean`, `memoryInjectionEnabled: boolean`
- [x] Step 3: `createHookContext()` 将 opts 中的开关值存入 ctx（默认 true）
- [x] Step 4: `createAllHooks()` 调用 `createHookContext` 时传入 `rulesInjectionEnabled` 和 `memoryInjectionEnabled`（从 index.ts 传入）
- [x] Step 5: `system-transform.ts` 从 `ctx.rulesInjectionEnabled` 读取开关，不再读环境变量 `process.env.WOPAL_RULES_INJECTION_ENABLED`
- [x] Step 6: `system-transform.ts` 从 `ctx.memoryInjectionEnabled` 读取开关，不再读环境变量 `process.env.WOPAL_MEMORY_INJECTION_ENABLED`
- [x] Step 7: 移除 `system-transform.ts` 中的 "disabled by environment variable" 日志（禁用时代码不执行到该分支）
- [x] Step 8: 5 个 `createDebugLog` 调用 prefix 更新：`[wopal-plugin]` → `[plugin]`，`[wopal-rules]` → `[rules]` 等

**Verification**:

- [x] Step 1: `hooks/index.test.ts` 单元测试通过
- [x] Step 2: `hooks/integration.test.ts` 单元测试通过
- [x] Step 3: 禁用 Rules Injection 后 system transform 无 "disabled" 日志

### Task 5: rules/formatter.ts log 归属修正

**Files**: `src/rules/formatter.ts`

**Changes**:

- [x] Step 1: `createDebugLog()` → `createDebugLog("[rules]", "rules")`

**Verification**:

- [x] Step 1: 单元测试通过

## Delegation Strategy

| 批次 | Task | 执行者 | 依赖 |
|------|------|--------|------|
| 1 | Task 1 (Prefix 批量替换) | fae | 无 |
| 1 | Task 2 (debug.ts) | Wopal | 无 |
| 1 | Task 5 (formatter.ts) | Wopal | 无 |
| 2 | Task 3 (index.ts 启动流程) | Wopal | Task 1, 2 |
| 2 | Task 4 (HookContext + system-transform) | Wopal | Task 1 |
| 3 | 全量测试验证 | Wopal | Task 2-5 |

说明：
- Task 1 纯字符串替换，量大低风险，委派 fae
- Task 2/5 单文件修改，Wopal 直接执行
- Task 3/4 核心逻辑，Wopal 执行
- 批次 1 可并行，批次 2 依赖 prefix 改完，批次 3 最后验证

## Test Plan

#### Unit Tests

N/A — 本次重构不新增功能，现有 421 个单元测试覆盖所有改动文件。

#### Integration Tests

##### Case I1: 禁用 Rules 模块后无规则发现日志
- Goal: 确认 `WOPAL_RULES_INJECTION_ENABLED=false` 时规则发现完全不执行
- Fixture: 设置环境变量，启动插件
- Execution:
  - [x] Step 1: 设置 `WOPAL_RULES_INJECTION_ENABLED=false` + `WOPAL_PLUGIN_DEBUG=rules`
  - [x] Step 2: 启动插件，检查日志文件
  - [x] Step 3: 确认无 `[rules]` 日志（规则发现不执行）
- Expected Evidence: 日志文件中无 "Discovered rule" 相关输出

##### Case I2: 禁用 Memory 模块后无初始化日志
- Goal: 确认 `WOPAL_MEMORY_ENABLED=false` 时 Memory 系统不初始化
- Fixture: 设置环境变量，启动插件
- Execution:
  - [x] Step 1: 设置 `WOPAL_MEMORY_ENABLED=false` + `WOPAL_PLUGIN_DEBUG=memory`
  - [x] Step 2: 启动插件，检查日志文件
  - [x] Step 3: 确认无 `[memory]` 日志（LanceDB/Embedding 不初始化）
- Expected Evidence: 日志文件中无 "Memory system initialized" 输出

##### Case I3: 禁用 Memory Injection 后注入跳过
- Goal: 确认 `WOPAL_MEMORY_INJECTION_ENABLED=false` 时 Memory 初始化正常但注入跳过
- Fixture: 设置环境变量，启动插件，触发 system transform
- Execution:
  - [x] Step 1: 设置 `WOPAL_MEMORY_ENABLED=true` + `WOPAL_MEMORY_INJECTION_ENABLED=false`
  - [x] Step 2: 启动插件，检查日志有 Memory 初始化
  - [x] Step 3: 触发 system transform，确认无 `[memory] inject` 日志
- Expected Evidence: 初始化日志存在，注入日志不存在

#### Regression Tests

##### Case R1: 单元测试全量通过
- Goal: 确认重构不破坏现有功能
- Fixture: 修改后的代码
- Execution:
  - [x] Step 1: `bun run test:run`
  - [x] Step 2: 确认 421 tests passed
- Expected Evidence: 所有测试通过，无新增失败

## Acceptance Criteria

### Agent Verification

- [x] 421 单元测试通过
- [x] grep 确认无 `[wopal-` prefix 残留
- [x] 三个 Integration Case 通过（禁用 Rules/Memory/Injection）

### User Validation

#### Scenario 1: 禁用开关生效验证
- Goal: 确认用户能通过环境变量控制模块加载
- Precondition: 插件已部署
- User Actions:
  1. 设置 `WOPAL_RULES_INJECTION_ENABLED=false`，重启 OpenCode
  2. 观察 `logs/wopal-plugins-debug.log`，确认无 `[rules]` 发现日志
  3. 设置 `WOPAL_MEMORY_ENABLED=false`，重启
  4. 确认无 `[memory]` LanceDB/Embedding 日志
- Expected Result: 禁用时模块完全不加载，日志干净

#### Scenario 2: Prefix 简洁化验证
- Goal: 确认日志 prefix 去掉冗余 `wopal-` 前缀
- Precondition: 插件已部署，`WOPAL_PLUGIN_DEBUG=1`
- User Actions:
  1. 启动 OpenCode，触发各种操作
  2. 检查 `logs/wopal-plugins-debug.log`
  3. 确认日志 prefix 格式：`[plugin]`, `[rules]`, `[task]`, `[memory]`, `[context]`
- Expected Result: 所有日志 prefix 无 `wopal-` 前缀，简洁清晰

- [x] 用户已完成上述功能验证并确认结果符合预期
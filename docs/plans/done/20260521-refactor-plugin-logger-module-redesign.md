# refactor-plugin-logger-module-redesign

## Metadata

- **Type**: refactor
- **Target Project**: wopal-space-ontology
- **Project Path**: .wopal/
- **Project Type**: ontology-worktree
- **Created**: 2026-05-21
- **Status**: done
- **MainBranch**: space/main
- **Worktree**: logger-module-redesign | /Users/sam/coding/wopal/wopal-workspace/.worktrees/ontology-logger-module-redesign

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

将 wopal-plugin 的日志模块从无级别开关式 `createXxxLog()` 工厂 API 重构为标准阈值级别体系 + 模块 logger 单例，统一日志语义、输出格式和调用约定。

## Technical Context

### Architecture Context

当前日志模块 `src/debug.ts` 存在以下问题：

1. **无级别体系**：`createDebugLog` / `createTraceLog` 是独立开关（受 `WOPAL_PLUGIN_DEBUG` / `WOPAL_PLUGIN_TRACE` 控制），不是阈值；`createInfoLog` / `createWarnLog` 无过滤，始终输出。无法通过单一环境变量控制日志粒度。
2. **API 设计混乱**：工厂函数每次调用返回新闭包，浪费对象；`createInfoLog` 与 `createWarnLog` 签名不一致（后者硬编码 `[WARN]`）；消费方可能用错级别（如 `createInfoLog` 打调试信息）。
3. **输出无级别标记**：日志格式 `时间 prefix msg`，无 `[LEVEL]` 标记，排查时无法区分 info/warn/error。
4. **性能隐患**：`formatCSTTimestamp()` 每次调用 `toLocaleString` + 正则 split；`appendFileSync` 每次阻塞写盘。
5. **可测性差**：`writeLog` 硬编码 `process.env.VITEST` 跳过日志；无依赖注入。

影响范围：28 个文件使用旧 API（含 1 个测试文件）。

### Research Findings

对比了两个内部项目的日志实现：

| 维度 | GESP Backend (`logger.ts`) | Wopal-CLI (`logger.ts`) |
|------|---------------------------|------------------------|
| 级别体系 | 6 级标准阈值（trace→fatal） | 4 级 + isDebug 开关 |
| 阈值控制 | `LOG_LEVEL` 数值比较 | debug boolean |
| 敏感信息 | 无处理 | 自动脱敏（正则过滤） |
| 日志轮转 | 无 | 按天轮转 + 自动清理 |
| 代码量 | 97 行 | 235 行 |

结论：采用 GESP backend 设计为骨架（零依赖、简洁、阈值语义清晰），叠加 wopal-cli 的敏感信息脱敏能力，加上插件特有的模块过滤功能。

**参考资料**：
- `projects/gesp/packages/backend/src/utils/logger.ts` — GESP logger 实现
- `projects/wopal-cli/src/lib/logger.ts` — wopal-cli logger 实现（脱敏逻辑）
- `.wopal/wopal-plugin/AGENTS.md` — 已更新的日志规范

### Key Decisions

- D-01: 采用 GESP backend 的 6 级阈值体系（trace 10 → fatal 60），不引入第三方库（pino 等），理由：插件日志量低，零依赖优先
- D-02: 模块 logger 命名从 `plugin` 改为 `core`，因为 `plugin` 描述"它是什么"（所有模块都是 plugin 的一部分），`core` 描述"它做什么"（引导、生命周期编排），日志信息量更大
- D-03: 保留敏感信息脱敏（从 wopal-cli 移植），过滤 token/password/api_key/secret/credential/authorization/private_key 字段，与 AGENTS.md 日志编写规则第 5 条一致
- D-04: 保留模块过滤功能（`WOPAL_PLUGIN_LOG_MODULES`），这是插件特有的需求，GESP backend 不需要但插件需要
- D-05: 旧环境变量 `WOPAL_PLUGIN_DEBUG` / `WOPAL_PLUGIN_TRACE` 在源码中废弃，统一为 `WOPAL_PLUGIN_LOG_LEVEL` + `WOPAL_PLUGIN_LOG_MODULES`；`emt`/`oct` 启动脚本**保持 `--debug [module]` / `--trace [module]` 接口不变**，内部映射为新环境变量（如 `--debug task` → `WOPAL_PLUGIN_LOG_LEVEL=debug WOPAL_PLUGIN_LOG_MODULES=task`）
- D-06: 保留 `formatSessionID()` 工具函数，从 `debug.ts` 迁移到 `logger.ts`，因为它是日志相关的辅助函数

### Key Interfaces

```typescript
// src/logger.ts 公开 API

// 级别定义（内部）
const LEVELS: Record<string, number> = {
  trace: 10, debug: 20, info: 30, warn: 40, error: 50, fatal: 60
}

// 模块 logger 类型 — 替代旧 DebugLog 函数类型
export interface LoggerInstance {
  trace(msg: string): void
  trace(data: Record<string, unknown>, msg: string): void
  debug(msg: string): void
  debug(data: Record<string, unknown>, msg: string): void
  info(msg: string): void
  info(data: Record<string, unknown>, msg: string): void
  warn(msg: string): void
  warn(data: Record<string, unknown>, msg: string): void
  error(msg: string): void
  error(data: Record<string, unknown>, msg: string): void
  fatal(msg: string): void
  fatal(data: Record<string, unknown>, msg: string): void
}

// 模块 logger 单例导出
export const coreLogger: LoggerInstance
export const rulesLogger: LoggerInstance
export const taskLogger: LoggerInstance
export const memoryLogger: LoggerInstance
export const contextLogger: LoggerInstance

// 辅助函数（保留）
export function formatSessionID(sessionID: string | undefined, isTask: boolean): string
```

**旧 `DebugLog` 函数类型迁移方案**（方案 B：对象注入）：

旧代码中 `DebugLog` 作为 `(message: string) => void` 函数类型注入到 HookContext 和模块依赖中。新方案改为注入 `LoggerInstance` 对象：

```typescript
// 旧 HookContext 接口
interface HookContext {
  pluginDebugLog: DebugLog;    // 函数
  rulesDebugLog: DebugLog;     // 函数
  taskDebugLog: DebugLog;      // 函数
  memoryDebugLog: DebugLog;    // 函数
  contextDebugLog: DebugLog;   // 函数
}

// 新 HookContext 接口
interface HookContext {
  coreLogger: LoggerInstance;    // 对象
  rulesLogger: LoggerInstance;   // 对象
  taskLogger: LoggerInstance;    // 对象
  memoryLogger: LoggerInstance;  // 对象
  contextLogger: LoggerInstance; // 对象
}

// 调用变更
// 旧：ctx.contextDebugLog("msg")
// 新：ctx.contextLogger.debug("msg")

// 依赖注入变更（如 task-launcher.ts）
// 旧：constructor(..., debugLog: DebugLog) { this.debugLog = debugLog; }
// 新：constructor(..., logger: LoggerInstance) { this.logger = logger; }
// 旧：this.debugLog("Task started")
// 新：this.logger.debug("Task started")
```

此方案影响范围：
- `hooks/index.ts`：HookContext 接口重写 + createHookContext 工厂重写
- 所有消费 HookContext 的 hook 文件：字段名从 `xxxDebugLog` → `xxxLogger`，调用加级别方法
- tasks 模块注入点：`debugLog: DebugLog` → `logger: LoggerInstance`
- 测试文件 mock：从 `vi.fn()` → `{ debug: vi.fn(), info: vi.fn(), ... }`

## In Scope

- 新建 `src/logger.ts`：基于 GESP logger 的 6 级阈值体系 + 模块过滤 + 敏感信息脱敏
- 新建 `src/logger.test.ts`：覆盖级别过滤、模块过滤、脱敏、输出格式、formatSessionID
- 迁移 44 个消费文件（由 `rg 'from.*debug\.js' --type ts -l` 确定的完整列表）从旧 API 到新 logger
- 清除所有源码中的旧环境变量引用（`WOPAL_PLUGIN_DEBUG` / `WOPAL_PLUGIN_TRACE`）
- 删除旧 `src/debug.ts` 和 `src/debug.test.ts`
- 更新 `AGENTS.md` 中遗留的旧 API 引用（如有）
- 更新 `.wopal/scripts/emt` 和 `.wopal/scripts/oct`：`--debug`/`--trace` 接口不变，内部环境变量映射为 `WOPAL_PLUGIN_LOG_LEVEL` + `WOPAL_PLUGIN_LOG_MODULES`

## Out of Scope

- 日志异步队列（插件日志量低，appendFileSync 可接受）
- 日志轮转（同上）
- JSON 输出格式（插件调试场景用纯文本即可）
- 控制台双写（插件运行在 EllaMaka 进程内，不应向 stdout 输出）

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| Logger Core | `src/logger.ts` | 创建 | 新日志模块：级别体系、模块过滤、脱敏、文件输出 |
| Logger Tests | `src/logger.test.ts` | 创建 | 覆盖级别过滤、模块过滤、脱敏、输出格式、formatSessionID |
| Old Logger | `src/debug.ts`, `src/debug.test.ts` | 删除 | 旧日志模块，迁移完成后移除 |
| Core | `src/index.ts`, `src/session-runtime-info.ts` | 修改 | 导入迁移：coreLogger |
| Rules | `src/rules/discoverer.ts` | 修改 | 导入迁移：rulesLogger |
| Memory (9 files) | `src/memory/store.ts`, `injector.ts`, `embedder.ts`, `session-context.ts`, `prompts.ts`, `dedup.ts`, `llm-client.ts`, `retriever.ts`, `distill.ts` | 修改 | 导入迁移：memoryLogger |
| Tasks (10 files) | `src/tasks/simple-task-manager.ts`, `task-launcher.ts`, `task-lifecycle.ts`, `task-monitor.ts`, `task-notifier.ts`, `progress-notify.ts`, `question-relay.ts`, `permission-proxy.ts`, `process-cleanup.ts`, `loop-detector.ts` | 修改 | 导入迁移：taskLogger + formatSessionID + LoggerInstance 注入 |
| Hooks (15 files) | `src/hooks/index.ts`, `event-router.ts`, `system-transform.ts`, `conversation-context.ts`, `compaction.ts`, `command-hooks.ts`, `message-hooks.ts`, `skill-reload-injector.ts`, `memory-injection-utils.ts`, `memory-message-injector.ts`, `rule-message-injector.ts`, `rule-injector.ts`, `events/message-token-handler.ts`, `events/error-handler.ts`, `events/idle-compact-handler.ts` | 修改 | 导入迁移：对应模块 logger + HookContext 接口重写 + 环境变量清理（system-transform.ts） |
| Tools (6 files) | `src/tools/output-helpers.ts`, `context-manage-actions.ts`, `context-manage.ts`, `wopal-task-reply.ts`, `wopal-task-abort.ts`, `dump-format-utils.ts` | 修改 | 导入迁移：对应模块 logger |
| Tests (2 files) | `src/tasks/task-notifier.test.ts`, `src/hooks/system-transform.test.ts` | 修改 | mock 迁移、旧环境变量清理 |
| Scripts | `.wopal/scripts/emt`, `.wopal/scripts/oct` | 修改 | `--debug`/`--trace` 接口不变，内部映射为新环境变量 |

> 总计 44 个消费文件 + 2 个旧文件删除 + 2 个新文件创建。消费文件完整列表由 `rg 'from.*debug\.js' --type ts -l` 确定。

## Acceptance Criteria

### Agent Verification

1. [x] `rg -c 'createDebugLog|createTraceLog|createInfoLog|createWarnLog|isDebugEnabled|isTraceEnabled' .wopal/wopal-plugin/src/ --type ts` 返回 0（无旧 API 残留，排除 debug.ts 本身）
2. [x] `rg -c 'from.*["\'].*debug\.js["\']' .wopal/wopal-plugin/src/ --type ts` 返回 0（无旧模块导入）
3. [x] `rg -c 'coreLogger|rulesLogger|taskLogger|memoryLogger|contextLogger' .wopal/wopal-plugin/src/logger.ts` ≥ 5（5 个模块 logger 全部导出）
4. [x] `rg -n 'process\.env\.WOPAL_PLUGIN_(DEBUG|TRACE)' .wopal/wopal-plugin/src/ --type ts` 返回空（运行时代码中无旧环境变量读取）
5. [x] `rg -c 'formatSessionID' .wopal/wopal-plugin/src/logger.ts` ≥ 1（formatSessionID 已迁移到新模块）
6. [x] `test -f .wopal/wopal-plugin/src/logger.test.ts && bun run test:run --reporter=verbose .wopal/wopal-plugin/src/logger.test.ts` 全部 pass（日志测试覆盖：级别过滤、模块过滤、脱敏、输出格式、formatSessionID）
7. [x] `bun run typecheck` 在 `.wopal/wopal-plugin/` 通过（exit 0）
8. [x] `bun run test:run` 在 `.wopal/wopal-plugin/` 通过（exit 0）
9. [x] `test ! -f .wopal/wopal-plugin/src/debug.ts && test ! -f .wopal/wopal-plugin/src/debug.test.ts`（旧文件已删除）
10. [x] `rg 'WOPAL_PLUGIN_LOG_LEVEL' .wopal/scripts/emt .wopal/scripts/oct` 命中（启动脚本已更新）
11. [x] `rg 'WOPAL_PLUGIN_LOG_MODULES' .wopal/scripts/emt .wopal/scripts/oct` 命中（启动脚本支持模块过滤）
12. [x] `rg -n 'WOPAL_PLUGIN_(DEBUG|TRACE)' .wopal/scripts/emt .wopal/scripts/oct .wopal/.env.example` 返回空（脚本和环境模板中旧变量已清零）

### User Validation

#### Scenario 1: 日志级别控制行为验证
- Goal: 确认新日志系统按级别阈值正确过滤输出
- Precondition: 插件正常运行，日志文件路径 `<cwd>/.wopal-space/logs/wopal-plugin.log`
- User Actions:
  1. 默认配置启动 EllaMaka，执行一次对话触发插件
  2. 检查日志文件：只有 `[WARN]` 和 `[ERROR]` 级别条目
  3. 设置 `WOPAL_PLUGIN_LOG_LEVEL=debug` 重启，再次执行对话
  4. 检查日志文件：看到 `[DEBUG]`、`[INFO]`、`[WARN]`、`[ERROR]` 级别条目
- Expected Result: 日志级别阈值过滤行为正确，输出格式包含 `[LEVEL]` 标记和模块名

- [x] 用户已完成上述功能验证并确认结果符合预期

## Implementation

### Task 1: 创建新日志模块 logger.ts + 测试

**Verification Intent**: AC#1, AC#3, AC#5, AC#6

**Behavior**: 
- `WOPAL_PLUGIN_LOG_LEVEL` 控制阈值，低于该级别的日志不输出
- `WOPAL_PLUGIN_LOG_MODULES` 控制模块过滤，未列出的模块不输出
- 敏感字段（token/password/secret 等）自动替换为 `[REDACTED]`
- 输出格式：`时间 [LEVEL] [module] key=val ... 消息`
- 5 个模块 logger 单例正确导出
- `formatSessionID` 函数保留并正确工作

**Files**: `src/logger.ts`, `src/logger.test.ts`

**Pre-read**: `projects/gesp/packages/backend/src/utils/logger.ts`, `projects/wopal-cli/src/lib/logger.ts`, `src/debug.ts`

**Design**:

基于 GESP backend logger 的核心结构，叠加三个扩展：

1. **级别过滤**：`LEVELS` 数值映射 + `shouldLog(levelNum)` 阈值比较。`WOPAL_PLUGIN_LOG_LEVEL` 默认 `warn`。

2. **模块过滤**：`parseModules(envVar)` 解析逗号分隔的模块名。`WOPAL_PLUGIN_LOG_MODULES` 为空时不过滤。每个模块 logger 在 `shouldLog` 中额外检查模块过滤。

3. **敏感信息脱敏**：从 wopal-cli 移植 `SENSITIVE_KEYS` 正则数组 + `sanitizeData()` 递归函数。在 `formatMeta()` 中调用。

4. **模块 logger 工厂**：`createModuleLogger(moduleName)` 返回包含 trace/debug/info/warn/error/fatal 方法的对象。内部调用统一的 `log(level, levelNum, data, msg)` 函数。

5. **文件输出**：保留 `getLogFile()` + `ensureLogFile()` + `appendFileSync` 模式。移除 `process.env.VITEST` 硬编码检查，改为通过环境变量控制（测试时设置 `WOPAL_PLUGIN_LOG_FILE=/dev/null` 或测试专用路径）。

6. **时间戳**：改用 `new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai', ... })` 直接输出（同 GESP），避免手写 `getFullYear()/getMonth()` 拼接。

7. **保留 `formatSessionID()`**：从 `debug.ts` 原样迁移。

测试覆盖：
- 级别过滤：设置不同 LOG_LEVEL，验证只有 >= 阈值的日志写入
- 模块过滤：设置 LOG_MODULES=task，验证只有 taskLogger 输出
- 脱敏：验证 token/session_id/password 字段替换为 [REDACTED]
- 输出格式：验证时间戳、[LEVEL]、[module]、key=val 格式正确
- formatSessionID：验证 main/task 后缀、截断行为

**TDD**: true

**Changes**:
1. 创建 `src/logger.ts`，实现 LEVELS、parseModules、sanitizeData、formatMeta、writeLine、shouldLog、log、createModuleLogger、5 个模块 logger 导出、formatSessionID
2. 创建 `src/logger.test.ts`，覆盖上述测试用例
3. 运行测试确认通过

**Verify**: `cd .wopal/wopal-plugin && bun run test:run --reporter=verbose src/logger.test.ts` 全部 pass

**Done**:
任务产出：新日志模块 `src/logger.ts` 及其测试 `src/logger.test.ts`，5 个模块 logger 单例可用
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

### Task 2: 迁移所有消费文件到新 logger API

**Verification Intent**: AC#1, AC#2, AC#4, AC#7

**Behavior**:
- 所有 `createDebugLog` / `createTraceLog` / `createInfoLog` / `createWarnLog` 调用替换为对应模块 logger 的级别方法
- 所有 `from ".../debug.js"` 导入替换为 `from ".../logger.js"`
- 所有 `DebugLog` 类型引用改为 `LoggerInstance` 类型（注入点参数 + HookContext 接口）
- 所有 `formatSessionID` 导入从 `debug.js` 迁移到 `logger.js`
- 级别映射正确：`debugLog(msg)` → `logger.debug(msg)`、`traceLog(msg)` → `logger.trace(msg)`、`infoLog(msg)` → `logger.info(msg)`、`warnLog(msg)` → `logger.warn(msg)`
- 模块映射正确：`[plugin]` → `coreLogger`、`[rules]` → `rulesLogger`、`[task]` → `taskLogger`、`[memory]` → `memoryLogger`、`[context]` → `contextLogger`
- 旧的 `isDebugEnabled()` / `isTraceEnabled()` 条件守卫全部移除（新 logger 内部处理过滤）
- 旧环境变量引用 `WOPAL_PLUGIN_DEBUG` / `WOPAL_PLUGIN_TRACE` 全部清除：`system-transform.ts` 中 auto-dump 判断改为读取 `WOPAL_PLUGIN_LOG_MODULES`
- typecheck 通过

**Files**: 44 个消费文件（完整列表由 `rg 'from.*debug\.js' --type ts -l` 确定，排除 debug.ts 和 debug.test.ts）

**Pre-read**: `src/logger.ts`（Task 1 产出），所有待迁移文件

**Design**:

迁移规则（每个文件执行相同模式）：

1. **导入替换**：
   - 旧：`import { createDebugLog, createWarnLog } from "../debug.js";`
   - 新：`import { taskLogger } from "../logger.js";`（选择对应模块）
   - 旧：`import { formatSessionID } from "../debug.js";`
   - 新：`import { formatSessionID } from "../logger.js";`
   - 旧：`import type { DebugLog } from "../debug.js";`
   - 新：`import type { LoggerInstance } from "../logger.js";`（注入点参数类型）

2. **变量声明删除**：
   - 旧：`const debugLog = createDebugLog("[task]", "task");`、`const traceLog = createTraceLog("[task]", "task");`、`const warnLog = createWarnLog("[task]");`、`const infoLog = createInfoLog("[task]");`
   - 新：删除所有变量声明，直接使用模块 logger

3. **调用替换**：
   - `debugLog("msg")` → `taskLogger.debug("msg")`
   - `traceLog("msg")` → `taskLogger.trace("msg")`
   - `infoLog("msg")` → `taskLogger.info("msg")`
   - `warnLog("msg")` → `taskLogger.warn("msg")`

4. **条件守卫移除**：
   - 旧：`if (isDebugEnabled("task")) { debugLog(...); }`
   - 新：`taskLogger.debug(...);`（logger 内部处理过滤）

5. **混合日志文件**：部分文件同时使用多个模块的日志（如 `index.ts` 用 `[plugin]` 和 `[context]`），需导入多个模块 logger。

6. **注入点迁移（HookContext + deps）**：按 Key Interfaces 中方案 B 执行：
   - `hooks/index.ts`：HookContext 接口字段重命名（`xxxDebugLog` → `xxxLogger`）
   - createHookContext 工厂：从 `createDebugLog()` → 模块 logger 单例（`coreLogger`、`taskLogger` 等）
   - 所有 hook 文件：字段引用改名 + 调用加级别方法
   - tasks 模块注入点（`task-launcher.ts`、`task-monitor.ts`、`task-lifecycle.ts`、`task-notifier.ts`）：参数类型从 `DebugLog` → `LoggerInstance`，字段改名，调用加级别
   - 测试文件 mock：从 `vi.fn()` → `{ debug: vi.fn(), info: vi.fn(), warn: vi.fn(), error: vi.fn() }`

7. **环境变量引用清理**：
   - `system-transform.ts` 中 `process.env.WOPAL_PLUGIN_DEBUG` 的功能开关逻辑（auto-dump 判断）改为读取 `WOPAL_PLUGIN_LOG_MODULES`，检查是否包含 `"context"` 模块，保持"仅显式启用 context 时 auto-dump 生效"的语义

8. **测试文件 mock**：`task-notifier.test.ts` 和 `system-transform.test.ts` 中对 `DebugLog` 的 mock 改为 `LoggerInstance` mock，旧环境变量 `WOPAL_PLUGIN_DEBUG` 引用替换为 `WOPAL_PLUGIN_LOG_LEVEL` / `WOPAL_PLUGIN_LOG_MODULES`。

**TDD**: false — 纯机械迁移，行为不变，无需 TDD

**Changes**:
1. 按模块分批迁移：core (index.ts, session-runtime-info.ts) → rules (discoverer.ts) → memory (9 files) → tasks (10 files) → hooks (15 files) → tools (6 files) → test mocks (2 files)
2. 每批迁移后运行 typecheck 确认无错误
3. 全部迁移完成后运行 `bun run typecheck` + `bun run test:run`

**Verify**: `cd .wopal/wopal-plugin && bun run typecheck && bun run test:run` 全部通过

**Done**:
任务产出：44 个消费文件完成日志 API 迁移 + 旧环境变量清零，typecheck + 测试通过
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

### Task 3: 清理旧模块 + 更新启动脚本 + 环境变量清零

**Verification Intent**: AC#4, AC#5, AC#6, AC#9, AC#10, AC#11

**Behavior**:
- `src/debug.ts` 和 `src/debug.test.ts` 已删除
- `emt`/`oct` 脚本**保持 `--debug [module]` / `--trace [module]` 接口不变**，内部映射为新环境变量（`WOPAL_PLUGIN_LOG_LEVEL` + `WOPAL_PLUGIN_LOG_MODULES`）
- 旧环境变量 `WOPAL_PLUGIN_DEBUG` 和 `WOPAL_PLUGIN_TRACE` 在源码和脚本中无残留引用
- `.env.example` 中旧环境变量已移除，新环境变量已添加

**Files**: `.wopal/scripts/emt`, `.wopal/scripts/oct`, `.wopal/.env`, `.wopal/.env.example`

**Pre-read**: `.wopal/scripts/emt`, `.wopal/scripts/oct`, `.wopal/.env`, `.wopal/.env.example`

**Design**:

1. 删除旧文件：`src/debug.ts` 和 `src/debug.test.ts`

2. 脚本内部映射（`emt` 和 `oct` 同样处理，**用户接口不变**）：
   - `--debug` 无参数 → `WOPAL_PLUGIN_LOG_LEVEL=debug`
   - `--debug task` → `WOPAL_PLUGIN_LOG_LEVEL=debug WOPAL_PLUGIN_LOG_MODULES=task`
   - `--debug task,context` → `WOPAL_PLUGIN_LOG_LEVEL=debug WOPAL_PLUGIN_LOG_MODULES=task,context`
   - `--trace [module]` → `WOPAL_PLUGIN_LOG_LEVEL=trace` + 对应 `WOPAL_PLUGIN_LOG_MODULES`
   - 同时传 `--debug` 和 `--trace` 时，`--trace` 优先（级别更高）

4. 更新 `.env.example`：移除 `WOPAL_PLUGIN_DEBUG` / `WOPAL_PLUGIN_TRACE`，添加 `WOPAL_PLUGIN_LOG_LEVEL` / `WOPAL_PLUGIN_LOG_MODULES`

5. 全局搜索确认无残留旧环境变量引用（排除 docs/ 和 plan 文件）

**TDD**: false — 非代码逻辑变更：文件删除 + 脚本参数更新 + 环境变量清理

**Changes**:
1. 删除 `src/debug.ts` 和 `src/debug.test.ts`
2. 更新 `.wopal/scripts/emt`：保持 `--debug`/`--trace` 接口不变，内部映射为 `WOPAL_PLUGIN_LOG_LEVEL` + `WOPAL_PLUGIN_LOG_MODULES`
3. 更新 `.wopal/scripts/oct`：同上
4. 更新 `.wopal/.env.example`：替换旧环境变量为新环境变量
5. 检查 `.wopal/.env` 中的旧环境变量，如存在则替换
6. 运行 `bun run typecheck && bun run test:run` 确认无破坏

**Verify**: `test ! -f .wopal/wopal-plugin/src/debug.ts && cd .wopal/wopal-plugin && bun run typecheck && bun run test:run` 全部通过 && `rg -n 'process\.env\.WOPAL_PLUGIN_(DEBUG|TRACE)' .wopal/wopal-plugin/src/ --type ts` 返回空 && `rg -n 'WOPAL_PLUGIN_(DEBUG|TRACE)' .wopal/scripts/emt .wopal/scripts/oct .wopal/.env.example` 返回空

**Done**:
任务产出：旧模块清理完成，启动脚本 `--debug`/`--trace` 内部映射为新环境变量，旧环境变量清零
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

## Delegation Strategy

| Wave | Task | 执行者 | 依赖 | 委派理由 |
|------|------|--------|------|---------|
| 1 | Task 1 | fae | 无 | 新模块创建 + 测试，标准代码实现任务 |
| 2 | Task 2 | fae | Task 1 | 44 文件迁移（含 HookContext 接口重写 + LoggerInstance 注入迁移 + 环境变量清零），需新模块先就绪 |
| 3 | Task 3 | fae | Task 2 | 清理旧模块 + 脚本更新，依赖迁移完成 |

Wave 间门控：每 wave 完成后 Wopal 运行 Verify 命令验证产出，通过后释放下一 wave。

# fix-wopal-plugin-isolate-runtime-context-per-instance

## Metadata

- **Issue**: #
- **Type**: fix
- **Target Project**: wopal-space-ontology
- **Project Path**: .wopal
- **Project Type**: ontology-worktree
- **Related Plan**: `../ellamaka/fix-sidecar-isolate-wopalspace-context-per-instance.md`
- **Dependency**: Ellamaka 提供 `PluginInput.wopalSpaceRoot?: string`
- **Review Exception**: 用户明确要求 Wopal 亲自实施和审阅，不委派 fae 或 rook。
- **Created**: 2026-07-30
- **Status**: done
- **Worktree**:
  - branch: plugin-isolate-runtime-context-per-instance
  - path: /Volumes/U500G/coding/wopal-workspace/.worktrees/ontology-plugin-isolate-runtime-context-per-instance
- **Verification Commit**: 0326f54

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

让 wopal-plugin 在每次 plugin `server(input)` 调用中独立使用 `PluginInput.wopalSpaceRoot` 定位空间资源。非 WopalSpace instance 只使用 WOPAL_HOME。插件不再通过 `process.env.WOPAL_SPACE_ROOT` 或模块级“当前空间”决定 `.env`、规则、日志和 prompt 路径。

## Technical Context

### Architecture Context

Ellamaka sidecar 会在同一进程中为不同 directory 创建独立 Plugin state。当前 wopal-plugin 仍假设“一进程一空间”：`runtime-context.ts` 从 `process.env.WOPAL_SPACE_ROOT` 构造模块级 `_context`，`loadWopalEnv()` 将空间 `.env` 写回 `process.env`，规则发现又动态读取该 env。

这会让后初始化的空间覆盖先初始化空间的路径，让非空间 instance 继承空间配置。Ellamaka 已收敛为可选字符串契约 `PluginInput.wopalSpaceRoot`，plugin 只需围绕这个字段隔离自身的路径和配置消费者。

SessionStore、TaskManager、MonitorEngine 和 Memory 数据库位置不由空间根决定。它们继续使用现有生命周期和 WOPAL_HOME 全局存储，不进入本次重构。

### Key Decisions

- D-01: `PluginInput.wopalSpaceRoot` 是唯一空间根来源。缺失表示非 WopalSpace。
- D-02: RuntimeContext 是 `server(input)` 内创建的不可变值，只包含 `wopalHome`、`directory` 和可选 `wopalSpaceRoot`。
- D-03: `.env` loader 返回只读 effective env，不修改 `process.env`。优先级为进程启动 env > 空间 `.wopal/.env` > WOPAL_HOME `.env`。
- D-04: 路径消费者显式接收 RuntimeContext、effective env 或窄化后的路径参数。模块级代码不保存“当前空间”。
- D-05: Memory 数据库与 session context 继续位于 `$WOPAL_HOME/storage/`。LLM、embedding、feature switches 和 prompt 读取当前 plugin invocation 的 effective env。
- D-06: `_memorySystem` 改为 plugin invocation 内局部实例，避免首个 instance 的 LLM/embedding 配置被后续 instance 复用。
- D-07: SessionStore、TaskManager、MonitorEngine、hook maps 和任务协议保持现状。它们不是空间根串台的来源。
- D-08: 当前工作 directory 只用于 session、tool 和文件操作，不形成第三层 `.env`、规则、日志或 prompt 配置。

### Key Interfaces

```ts
type RuntimeContext = {
  wopalHome: string
  directory: string
  wopalSpaceRoot?: string
}

type RuntimeEnvironment = Readonly<Record<string, string | undefined>>

type PluginRuntime = {
  context: RuntimeContext
  env: RuntimeEnvironment
  loggers: PluginLoggers
}
```

### Path Resolution Matrix

| Resource | 非 WopalSpace | WopalSpace（空间根或任意子目录） |
|----------|---------------|----------------------------------|
| Mode | `wopalSpaceRoot === undefined` | `wopalSpaceRoot` 为绝对路径 |
| Global root | `$WOPAL_HOME` | `$WOPAL_HOME` |
| Space root | 无 | `PluginInput.wopalSpaceRoot` |
| Environment | process baseline + `$WOPAL_HOME/.env` | process baseline + `$WOPAL_HOME/.env` + `<wopalSpaceRoot>/.wopal/.env` |
| Rules | `$WOPAL_HOME/rules` | `$WOPAL_HOME/rules` + `<wopalSpaceRoot>/.wopal/rules` |
| Plugin log | `$WOPAL_HOME/logs/wopal-plugin.log` | `<wopalSpaceRoot>/.wopal-space/logs/wopal-plugin.log` |
| Memory prompts | env override → `$WOPAL_HOME/prompts` → inline | env override → `<wopalSpaceRoot>/.wopal/prompts` → `$WOPAL_HOME/prompts` → inline |
| Memory database | `$WOPAL_HOME/storage/memory` | `$WOPAL_HOME/storage/memory` |
| Session context | `$WOPAL_HOME/storage/session_context` | `$WOPAL_HOME/storage/session_context` |

## In Scope

- 将 RuntimeContext 改为消费 `PluginInput.wopalSpaceRoot` 的纯工厂，删除 `_context` singleton。
- 将 `.env` 合并改为无进程副作用的 per-invocation effective env。
- 让规则、日志和 memory prompt 显式消费当前 plugin runtime。
- 让 feature switches、LLM 和 embedding 配置读取 effective env。
- 将 `_memorySystem` 绑定到当前 plugin invocation，同时保持 Memory 数据库为 WOPAL_HOME 全局存储。
- 增加非空间、Space A 根目录、Space A 子目录、Space B、反向顺序和并发初始化测试。
- 更新 plugin DESIGN 与 README 的路径所有权说明。

## Out of Scope

- Ellamaka 的空间检测与 PluginInput 类型由关联 Plan 负责。
- SessionStore、TaskManager、MonitorEngine、hook maps 和任务协议重构不属于本 Plan。
- Shell、PTY、MCP、LSP 子进程环境不属于本 Plan。
- Memory 数据库按空间拆分不属于本 Plan。
- Workbench localStorage 历史 tab 清理不属于本 Plan。

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| Runtime | `plugins/wopal-plugin/src/runtime-context.ts`, `plugins/wopal-plugin/src/runtime-environment.ts`, `plugins/wopal-plugin/src/index.ts` | 修改/创建 | 创建 per-invocation context 与 effective env |
| Paths | `plugins/wopal-plugin/src/rules/discoverer.ts`, `plugins/wopal-plugin/src/logger.ts`, `plugins/wopal-plugin/src/memory/prompts.ts` | 修改 | 消费当前 runtime 的规则、日志与 prompt 路径 |
| Memory config | `plugins/wopal-plugin/src/memory/embedder.ts`, `plugins/wopal-plugin/src/llm-client.ts`, `plugins/wopal-plugin/src/memory/distill.ts`, `plugins/wopal-plugin/src/hooks/events/idle-compact-handler.ts` | 修改 | 使用当前 invocation env 与 prompt loader |
| Global storage | `plugins/wopal-plugin/src/memory/store.ts`, `plugins/wopal-plugin/src/memory/session-context.ts` | 修改 | 直接使用 WOPAL_HOME，不依赖空间 RuntimeContext |
| Tests | `plugins/wopal-plugin/src/runtime-context.test.ts`, `plugins/wopal-plugin/src/runtime-environment.test.ts`, `plugins/wopal-plugin/src/rules/discoverer.test.ts`, `plugins/wopal-plugin/src/logger.test.ts`, `plugins/wopal-plugin/src/memory/prompts.test.ts`, `plugins/wopal-plugin/src/index.test.ts`, `plugins/wopal-plugin/src/runtime-isolation.test.ts` | 修改/创建 | 覆盖路径矩阵、顺序、并发和无 env 副作用 |
| Docs | `docs/DESIGN.md`, `plugins/wopal-plugin/README.md` | 修改 | 记录单字段契约和路径所有权 |

## Acceptance Criteria

### Agent Verification

1. [x] `cd plugins/wopal-plugin && bun run test:run -- src/runtime-context.test.ts src/runtime-environment.test.ts` 通过；源码不再从 `process.env.WOPAL_SPACE_ROOT` 推断空间。
2. [x] `cd plugins/wopal-plugin && bun run test:run -- src/rules/discoverer.test.ts src/logger.test.ts src/memory/prompts.test.ts` 通过；非空间、A 根目录、A 子目录和 B 分别使用 Path Resolution Matrix 中的路径。
3. [x] `cd plugins/wopal-plugin && bun run test:run -- src/index.test.ts src/runtime-isolation.test.ts` 通过；A/B/非空间按正序、反序和并发初始化时，root、effective env、logger 与 memory client 配置互不串台。
4. [x] `cd plugins/wopal-plugin && bun run typecheck:fix && bun run typecheck && bun run test:run && bun run build` 通过。
5. [x] `! rg 'process\.env\.WOPAL_SPACE_ROOT|process\.env\["WOPAL_SPACE_ROOT"\]' plugins/wopal-plugin/src --glob '!*.test.ts'` 成功，生产源码不存在全局 root 旁路。
6. [x] Memory 数据库与 session context 的路径测试确认两种模式均使用 `$WOPAL_HOME/storage/`。

### User Validation

#### Scenario 1: 非空间与两个空间同时运行
- Goal: 确认 `.env`、规则、日志和 prompt 路径属于当前 plugin instance。
- Precondition: Ellamaka 已包含 `PluginInput.wopalSpaceRoot` 契约；WOPAL_HOME、Space A、Space B 使用不同的非敏感测试标记。
- User Actions:
  1. 重启当前 Ellamaka。
  2. 同时打开 Workbench General、Space A 和 Space B。
  3. 分别触发规则、日志与 memory prompt。
  4. 交换打开顺序后重复检查。
- Expected Result: Workbench General 只使用 WOPAL_HOME；A/B 只使用各自空间路径；顺序和并发不改变结果。

- [x] 用户已完成上述功能验证并确认结果符合预期

## Implementation

### Task 1: 建立 per-invocation runtime 与 effective env

**Verification Intent**: AC#1, AC#3

**Behavior**:
- 非空间 PluginInput → `wopalSpaceRoot=undefined`，只合并 WOPAL_HOME `.env`。
- Space A 根目录或子目录 → `wopalSpaceRoot=A`，合并 A 的 `.wopal/.env`。
- A/B 正序、反序或并发创建 → effective env 相互独立，`process.env` 不变。

**Files**: `plugins/wopal-plugin/src/runtime-context.ts`, `plugins/wopal-plugin/src/runtime-environment.ts`, `plugins/wopal-plugin/src/index.ts`, `plugins/wopal-plugin/src/runtime-context.test.ts`, `plugins/wopal-plugin/src/runtime-environment.test.ts`

**Pre-read**: `plugins/wopal-plugin/src/index.ts`, `plugins/wopal-plugin/src/runtime-context.ts`

**Design**:
RuntimeContext 工厂接收 `directory`、`wopalSpaceRoot` 和进程级 WOPAL_HOME。RuntimeEnvironment loader 解析两层 `.env` 并返回冻结对象。plugin `server(input)` 在局部创建 PluginRuntime，不保存模块级当前空间。

**TDD**: true

**Changes**:
1. 用纯工厂替换 `_context` 与 `init/getRuntimeContext`。
2. 新增无副作用 `.env` 合并器。
3. 让 feature switches 从 runtime env 读取。
4. 增加双空间顺序、反序和并发测试。

**Verify**: `cd plugins/wopal-plugin && bun run test:run -- src/runtime-context.test.ts src/runtime-environment.test.ts && bun run typecheck`

**Done**: 每次 plugin invocation 拥有独立且不可变的 root 与 env。
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

### Task 2: 隔离空间路径消费者

**Verification Intent**: AC#2, AC#5

**Behavior**:
- 非空间 → WOPAL_HOME rules/logs/prompts。
- Space A 根目录与子目录 → 相同的 A rules/logs/prompts。
- Space B → B 路径；交错调用不读取 A。

**Files**: `plugins/wopal-plugin/src/rules/discoverer.ts`, `plugins/wopal-plugin/src/logger.ts`, `plugins/wopal-plugin/src/memory/prompts.ts`, `plugins/wopal-plugin/src/rules/discoverer.test.ts`, `plugins/wopal-plugin/src/logger.test.ts`, `plugins/wopal-plugin/src/memory/prompts.test.ts`

**Pre-read**: `plugins/wopal-plugin/src/hooks/context.ts`, `plugins/wopal-plugin/src/hooks/index.ts`

**Design**:
规则发现接收可选 `wopalSpaceRoot`。Logger factory 绑定当前 invocation 的 log file 与 env，并通过既有 HookContext/logger 参数传递。Prompt resolver 接收 RuntimeContext、effective env 或已绑定的 loader callback，不再查询模块 singleton。

**TDD**: true

**Changes**:
1. 删除规则发现对 `process.env.WOPAL_SPACE_ROOT` 的读取和当前 directory `.wopal/rules` 附加层。
2. 创建绑定 instance 路径和配置的 logger set。
3. 将 prompt 路径解析绑定到当前 runtime。
4. 添加交错路径调用测试。

**Verify**: `cd plugins/wopal-plugin && bun run test:run -- src/rules/discoverer.test.ts src/logger.test.ts src/memory/prompts.test.ts`

**Done**: 所有空间路径都从当前 invocation 的 `wopalSpaceRoot` 推导。
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

### Task 3: 隔离 Memory 配置并保留全局存储

**Verification Intent**: AC#3, AC#6

**Behavior**:
- A/B 的 LLM、embedding、feature switches 与 prompt 使用各自 effective env。
- Memory 数据库与 session context 在两种模式下都使用 WOPAL_HOME。
- 初始化或释放 A 不改变 B 的 memory client 配置。

**Files**: `plugins/wopal-plugin/src/index.ts`, `plugins/wopal-plugin/src/memory/store.ts`, `plugins/wopal-plugin/src/memory/session-context.ts`, `plugins/wopal-plugin/src/memory/embedder.ts`, `plugins/wopal-plugin/src/llm-client.ts`, `plugins/wopal-plugin/src/memory/distill.ts`, `plugins/wopal-plugin/src/hooks/events/idle-compact-handler.ts`, `plugins/wopal-plugin/src/index.test.ts`, `plugins/wopal-plugin/src/runtime-isolation.test.ts`

**Pre-read**: `plugins/wopal-plugin/src/hooks/context.ts`, `plugins/wopal-plugin/src/memory/injector.ts`

**Design**:
MemoryStore 与 session context 直接接收或解析 WOPAL_HOME 路径。LLMClient、EmbeddingClient 和 prompt loader 接收 invocation env。`_memorySystem` 变为 `server(input)` 内局部对象。既有 SessionStore、TaskManager 和 MonitorEngine 保持原结构。

**TDD**: true

**Changes**:
1. 将全局存储路径与空间 RuntimeContext 解耦。
2. 让 LLM/embedding 构造器消费 effective env。
3. 移除 `_memorySystem` singleton。
4. 将 title prompt loader 通过现有 HookContext 或窄 callback 注入。
5. 增加双 invocation memory 配置隔离测试。

**Verify**: `cd plugins/wopal-plugin && bun run test:run -- src/index.test.ts src/runtime-isolation.test.ts src/memory/store.test.ts`

**Done**: Memory 配置按 invocation 隔离，持久化位置继续全局共享。
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

### Task 4: 完成集成回归与文档

**Verification Intent**: AC#3–AC#6

**Behavior**: 同一模块中的 A/B/非空间按任意顺序初始化和交错执行时，root、env、paths 与 clients 保持隔离；生产源码不存在 root env 旁路。

**Files**: `plugins/wopal-plugin/src/runtime-isolation.test.ts`, `docs/DESIGN.md`, `plugins/wopal-plugin/README.md`

**Pre-read**: `plugins/wopal-plugin/AGENTS.md`, `docs/DESIGN.md`, `plugins/wopal-plugin/README.md`

**Design**:
集成 fixture 使用临时 WOPAL_HOME、Space A、Space B 和非空间目录，直接构造三个 PluginInput。测试不修改真实 HOME，不通过 `process.env.WOPAL_SPACE_ROOT` 模拟空间。文档记录单字段契约、路径矩阵和全局存储边界。

**TDD**: true

**Changes**:
1. 覆盖顺序、反序、并发和交错执行。
2. 扫描生产源码确认无 root env 旁路。
3. 更新 DESIGN 与 README。
4. 运行完整类型检查、测试和构建。

**Verify**: `cd plugins/wopal-plugin && bun run typecheck:fix && bun run typecheck && bun run test:run && bun run build`

**Done**: plugin 多 instance 空间路径与配置隔离具备完整回归保护。
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤.

## Delegation Strategy

Wopal 亲自按 Task 1 → Task 2 → Task 3 → Task 4 串行实施和审阅。所有测试使用临时目录与临时 WOPAL_HOME。用户完成运行时验证前不提交代码。

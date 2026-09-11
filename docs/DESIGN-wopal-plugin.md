# DESIGN — wopal-plugin 总体设计

> **Status**: Draft
> **Updated**: 2026-09-11
> **Parent**: `.wopal/docs/DESIGN.md`（ontology 总体设计，§4.5 插件体系、§4.8 配置体系）

---

## 1. Project Role

wopal-plugin 是 WopalSpace 在 ellamaka 运行时上的专用插件，以 TypeScript 编写、Bun 执行。插件在 Agent 会话生命周期内提供四项核心能力：规则注入、任务委派、记忆系统、上下文管理。

插件以声明式配置驱动自身行为。配置承载于空间配置体系，随空间分发与覆盖。插件不修改 ellamaka 核心行为，所有能力以 Hook 与 Tool 的形式注入运行时。

每个 ellamaka instance 加载独立插件实例。`PluginInput.wopalSpaceRoot` 是唯一空间根来源，字段缺失表示非 WopalSpace instance。插件为每次 `server(input)` 调用构造独立的运行时上下文、配置、日志器与资源客户端。

## 2. Capability Scope

| 能力域 | 拥有的目标能力 | 边界 |
|--------|----------------|------|
| 规则注入 | 规则文件发现、条件匹配、系统提示词注入 | 不定义规则内容 |
| 任务委派 | 非阻塞子会话启动、状态监控、双向通信、并发控制、进程清理 | 不管理任务业务逻辑 |
| 记忆系统 | LanceDB 持久化、语义检索、自动注入、CRUD、蒸馏确认流 | 不持有记忆数据 |
| 上下文管理 | 会话摘要、上下文压缩与恢复、标题生成、会话转储 | 不改变模型行为 |

插件向 Agent 暴露 7 个工具：`wopal_task`、`wopal_task_output`、`wopal_task_reply`、`wopal_task_abort`、`wopal_task_finish`、`memory_manage`、`context_manage`。

## 3. Key Decisions

| Decision | Rationale |
|----------|-----------|
| 声明式配置优于环境变量开关 | 配置面需要类型、分组、默认值声明与注释；环境变量仅承载密钥与运行时诊断覆盖 |
| 配置承载于 settings 体系顶层 `wopal` 节点 | 复用既有三层配置与 git 传播模型；settings.jsonc 顶层是自由容器（`tui` 先例） |
| 资源层与模块分离 | `LLMClient`、`EmbeddingClient` 是共享资源，各模块按自身需求声明依赖 |
| 蒸馏归属 context 模块 | 蒸馏的输入是会话上下文，与标题生成同族，统一 LLM 资源依赖 |
| compaction 不纳入开关 | 会话安全阀，永远启用 |
| Prompt 模板按约定路径解析，不设配置项 | 空间级与用户级路径已覆盖自定义需求，配置项会为边缘场景增加心智负担 |
| 插件能实现尽量不改造 engine | 所有能力以 Hook/Tool 注入，不改 ellamaka 核心 |
| Plugin instance 隔离 | 每个 instance 独立运行时上下文、配置、日志与资源 |

## 4. Module Architecture

| 模块 | 职责 | 可配置 |
|------|------|--------|
| Runtime（`runtime-*`） | 空间根解析、配置加载、日志器构建、环境合并 | — |
| Resources | LLM / Embedding 客户端共享资源，按模块依赖初始化 | — |
| Rules（`rules/`） | 规则发现 → 条件匹配 → 格式化注入 | 默认启用 |
| Memory（`memory/`） | LanceDB 存储、语义检索、自动注入、CRUD | `enabled`、`injection` |
| Context（`hooks/`） | 会话摘要、压缩恢复、标题生成、蒸馏 | `enabled` |
| Task（`tasks/`） | 子会话启动、状态监控、双向通信、并发控制 | 始终启用 |
| Monitor（`monitor/`） | 周期性调度引擎，统一管理监控策略 | 始终启用 |
| Lifecycle（`lifecycle/`） | 进程退出清理注册表 | — |
| Tools（`tools/`） | 插件工具定义与注册 | 按模块开关 |

| 目录 | 职责 |
|------|------|
| `src/hooks/` | Hook 注册与注入逻辑；`system-transform.ts` 是系统提示词修改的唯一入口 |
| `src/tasks/` | 任务管理；`SimpleTaskManager` 是唯一公开入口 |
| `src/memory/` | 记忆持久化；`MemoryStore` 是唯一持久化访问入口 |
| `src/monitor/` | `MonitorEngine` 是唯一周期调度引擎 |
| `src/tools/` | 工具定义；任务工具统一 `wopal_task_*` 前缀 |

部署：`.wopal/plugins/wopal-plugin.ts` → symlink → `src/index.ts`。

### 4.1 Resources 资源层

`LLMClient` 与 `EmbeddingClient` 是插件级共享资源，不属于任何功能模块。功能模块按自身需求声明对资源的依赖，资源按依赖关系初始化：

- Embedding：memory 模块（注入 / 检索 / CRUD 去重）
- LLM：context 模块（标题生成 / 蒸馏）

资源初始化按启用能力的最小集推导。能力全关时零资源初始化。资源缺失时该模块降级并记录 warn 日志，降级以模块为粒度，不连锁拖垮无关模块。

### 4.2 Rules 模块

Rules 模块发现全局（`~/.wopal/rules`）与空间（`<space>/.wopal/rules`）两级规则文件，按 Agent 作用域与关键词条件匹配，通过 `messages.transform` 注入系统提示词。规则发现发生在插件初始化时，注入发生在每条消息周期。Rules 默认启用，不暴露独立配置开关。

### 4.3 Memory 模块

Memory 模块管理 LanceDB 记忆存储与检索。`MemoryStore` 是唯一持久化访问入口，记录使用 `tags` 字段。模块拥有两个配置开关：

- `enabled`：记忆系统本体——store、embedder、`memory_manage` 工具。关闭时以上全部不初始化
- `injection`：自动注入——将检索到的记忆注入用户消息。独立于 `enabled`，关闭不影响记忆检索

注入是上下文成本敏感能力。`injection` 独立可关让用户在不放弃检索的前提下消除注入开销。注入门控前置：`needsMemoryInjection` 标志仅在注入能力启用时置位，避免功能关闭时每条消息产生无效 store 写。

记忆蒸馏的 `preview → confirm` 两步流程由 context 模块拥有（见 4.4），memory 模块不承担蒸馏引擎。

### 4.4 Context 模块

Context 模块管理会话生命周期中的上下文质量。模块拥有总开关 `enabled`，统管三项增强能力：

- 标题生成：压缩完成后为会话生成标题
- 自动恢复：压缩后自动发送恢复指令，保持会话连续性
- 蒸馏：从会话上下文提炼记忆候选，经 preview → confirm 两步确认后写入记忆库

`compaction`（上下文压缩）不纳入开关，永远启用——它是会话安全阀，关闭会导致上下文管理失效。

蒸馏归属 context 模块的依据：蒸馏的输入是会话上下文，输出是记忆候选，其本质是用 LLM 处理会话上下文，与标题生成、压缩同族。输出落点不决定归属，输入决定归属。蒸馏关闭时相关操作返回清晰的降级提示，不影响记忆检索与 CRUD。

### 4.5 Task 模块

Task 模块提供非阻塞子会话委派。`SimpleTaskManager` 是唯一公开入口，负责：

- 任务启动：`wopal_task` 启动子会话，受并发限制约束
- 状态监控：通过 Monitor 策略周期检查任务状态，分类 `idle` / `stuck` / `error`
- 双向通信：`wopal_task_reply` 注入消息续会话，`wopal_task_output` 查询输出
- 生命周期：任务可中止、可完成清理，子会话异常分类处理
- 通知：进度通知、会话 ID 解析、任务引用解析

任务工具永远注册，不依赖任何开关。`SimpleTaskManager` 的周期监控通过 `MonitorStrategy` 注册进 `MonitorEngine`。

### 4.6 Monitor 模块

`MonitorEngine` 是插件内唯一的周期调度引擎。以固定间隔执行已注册的 `MonitorStrategy`，统一管理会话状态视图。现有策略：任务监控策略（Task 模块注册）、主会话监控策略（会话状态与压缩触发）。其他模块不得创建独立调度链，新策略实现 `MonitorStrategy` 接口并注册进引擎。

### 4.7 Lifecycle 模块

进程退出清理注册表。监控引擎与任务管理器在进程退出时统一清理，避免孤儿定时器与未关闭资源。

## 5. Configuration

### 5.1 配置承载

插件配置承载于既有三层 settings 体系，顶层 `wopal` 节点：

| 层级 | 文件 | Git | 职责 |
|------|------|-----|------|
| 全局 | `~/.wopal/config/settings.jsonc` | 否 | 所有空间共享的默认值 |
| 空间公共 | `<space>/.wopal/config/settings.jsonc` | 是 | 空间能力基线，随分支分发 |
| 空间私有 | `<space>/.wopal/config/settings.local.jsonc` | 否 | 本地调参，覆盖公共默认 |

合并规则：deep merge，后者覆盖前者的叶子值。文件缺失则跳过该层。优先级：代码默认 < 全局 < 空间公共 < 空间私有。

插件启动时读取三层配置，输出 effective config 日志，标明每项配置的来源层级。

### 5.2 配置 Schema

```jsonc
"wopal": {
  "llm":       { "baseUrl": "...", "model": "...", "apiKey": "$WOPAL_LLM_API_KEY" },
  "embedding": { "baseUrl": "...", "model": "...", "apiKey": "$WOPAL_EMBEDDING_API_KEY" },
  "memory":    { "enabled": true, "injection": true },
  "context":   { "enabled": true },
  "logLevel":  "info"
}
```

Schema 由 zod 定义，每个字段声明类型与默认值。非法配置在启动时报错，不静默降级。未配置的字段使用默认值。

`apiKey` 支持 `$VAR` 环境变量引用：以 `$` 开头从 `process.env` 解析，未设置时启动报错；不以 `$` 开头按字面值处理。配置文件即使进 git 也不承载明文密钥。

### 5.3 Prompt 模板解析

提示词模板按约定路径解析，不设配置项。解析顺序：

| 层级 | 路径 | 说明 |
|------|------|------|
| 空间级 | `<space>/.wopal/prompts/<filename>` | 空间自定义，随空间分发 |
| 用户级 | `$WOPAL_HOME/prompts/<filename>` | 跨空间共享 |
| 内联默认 | 插件内置 | 前两层均未命中时使用 |

三个模板文件的约定名：

| 文件 | 消费方 | 用途 |
|------|--------|------|
| `distill.md` | context | 会话蒸馏的提取提示词 |
| `dedup.md` | context | 蒸馏候选与既有记忆的去重决策提示词 |
| `title.md` | context | 会话标题生成提示词 |

模板加载发生在消费方首次调用时（惰性），加载结果按文件路径缓存。模板内容使用 `{{placeholder}}` 占位符，由消费方填充。

设计取舍：不提供「任意路径覆盖」配置项。约定路径已覆盖空间与用户两级自定义需求，而新增 `prompts: { distill: "/abs/path" }` 之类的配置面为边缘场景增加了用户心智负担与 schema 复杂度。需要跨空间复用的模板放用户级，需要随空间分发的模板放空间级。

### 5.4 环境变量角色

环境变量收敛为两个角色，功能开关不使用环境变量：

| 角色 | 变量 | 说明 |
|------|------|------|
| 密钥 | `WOPAL_LLM_API_KEY`、`WOPAL_EMBEDDING_API_KEY` | 由配置 `apiKey` 字段以 `$` 引用 |
| 日志诊断覆盖 | `WOPAL_PLUGIN_LOG_LEVEL` / `_FILE` / `_MODULES` | 运行时覆盖，供启动脚本动态传入，优先级高于配置文件 |

日志诊断保留 env 通道：启动脚本按进程场景动态传入日志级别与位置，静态配置文件无法表达这种运行时变化。配置文件 `logLevel` 是声明式默认值，诊断 env 是运行时覆盖，二者定位不同，不重叠。

### 5.5 配置来源优先级

一般配置：代码默认 < 全局 < 空间公共 < 空间私有。日志诊断：上述链条之上叠加 `WOPAL_PLUGIN_LOG_*` env 覆盖。

## 6. Interfaces and Contracts

### 6.1 Hook 接口

| Hook | 用途 |
|------|------|
| `messages.transform` | 规则注入、记忆注入、技能重载注入；`system-transform.ts` 是系统提示词修改的唯一入口 |
| `event` | 事件路由：消息增量、会话 idle/compacted/error 分发到专用处理器 |
| `tool` | 工具注册表，见 6.2 |
| `system.transform` | 会话系统提示词快照与上下文转储基础设施 |

事件路由将事件分发到专用处理器：`message-token-handler`（消息增量）、`idle-compact-handler`（idle/compacted 恢复与标题生成）、`error-handler`（会话错误）。

### 6.2 工具接口

| 工具 | 注册条件 | 职责 |
|------|----------|------|
| `wopal_task` | 始终 | 非阻塞子会话启动 |
| `wopal_task_output` | 始终 | 任务状态与输出查询 |
| `wopal_task_reply` | 始终 | 双向通信与恢复 |
| `wopal_task_abort` | 始终 | 任务终止 |
| `wopal_task_finish` | 始终 | 任务完成清理 |
| `memory_manage` | `memory.enabled` | 记忆 list/stats/search/add/update/delete/injected |
| `context_manage` | 始终 | 会话 status/dump/compact + 蒸馏（distill/confirm/cancel） |

`memory_manage` 条件注册，禁用时输出 info 日志说明原因。蒸馏动作属于 context 模块，承载于 `context_manage` 工具。

### 6.3 日志体系

| Logger | Scope |
|--------|-------|
| `coreLogger` | Bootstrap、生命周期 |
| `rulesLogger` | 规则发现/匹配/注入 |
| `taskLogger` | 任务委派/监控/通信 |
| `memoryLogger` | LanceDB/检索/注入/蒸馏 |
| `contextLogger` | 会话状态/压缩/恢复 |

日志级别 trace/debug/info/warn/error/fatal，默认 info。核心事件完成记录一条 info；关键数据点用 debug；详细流程用 trace。结构化字段通过 data 对象携带，字段名 snake_case。错误日志必须携带 `{ err: error }`。

## 7. Data and State Model

| State | Location | Owner | Rules |
|-------|----------|-------|-------|
| 会话状态 | `sessionStore` 内存 Map | hooks | 会话级瞬态，含注入标志、压缩状态、技能加载集 |
| 会话上下文 | `$WOPAL_HOME/storage/session_context` | context | 蒸馏提取状态、会话摘要、标题 |
| 记忆数据 | `$WOPAL_HOME/storage/memory` LanceDB | memory | 检索式记忆，tags 字段，蒸馏经 preview→confirm 写入 |
| 系统提示词快照 | 插件进程内 Map | hooks | 规则/记忆注入的会话级快照 |
| 任务状态 | `SimpleTaskManager` 内存 | tasks | 任务生命周期与并发控制 |
| 插件运行时状态 | 插件进程内 | runtime | 每个 instance 独立 |

会话上下文（`session-context.ts`）采用模块化块结构：`distill` 块（提取状态）、`summary` 块（会话摘要），未来扩展不修改现有结构。

## 8. Related Documents

- `.wopal/docs/DESIGN.md` — ontology 总体设计（§4.5 插件体系、§4.8 配置体系、§6.2 工具接口）
- `.wopal/plugins/wopal-plugin/AGENTS.md` — 插件开发规范
- `.wopal/plugins/wopal-plugin/docs/rules.md` — 规则体系使用说明
- Issue #225 — 配置体系重构的问题清单与来源
# refactor-plugin-1-config-and-resources

## Metadata

- **Issue**: (无)
- **Type**: refactor
- **Target Project**: wopal-space-ontology

- **Project Path**: .wopal
- **Project Type**: ontology-worktree
- **Created**: 2026-09-11
- **Status**: done
- **Verification Commit**: 3f957c6455eb326f50134f826b4305ec7409311b
- **Worktree**:
  - branch: wopal-space-ontology-refactor-plugin-1-config-and-resources
  - path: (removed)
- **Verification Dir**: /Volumes/U500G/coding/wopal-workspace/.wopal
- **Base Commit**: 22ffc29dab7d749bbd2f3c1698f5d7327e24db26
- **Final Commit**: c08c6a2c98257060bce2b4b780d95ba0e3a85547

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High
- **Phase**: 1 / 3（配置与资源地基）

## Plan Dependencies

本期重构拆分为三个串行 Plan，必须按序实施，不可并行：

| Plan | Phase | 依赖 | 说明 |
|------|-------|------|------|
| `refactor-plugin-1-config-and-resources` | 1 / 3 | 无 | 本 Plan。交付配置加载器与资源层地基 |
| `refactor-plugin-2-switches-and-diagnostics` | 2 / 3 | Plan 1 | 消费本 Plan 的配置契约与资源层接线能力开关 |
| `refactor-plugin-3-distill-to-context` | 3 / 3 | Plan 1、Plan 2 | 迁移蒸馏归属并接入 context 总开关 |

**启动前置**：本 Plan 无前置，可立即启动。

**完成定义**：本 Plan 归档后，Plan 2 方可启动。三者改动同一批文件与装配链（`src/index.ts`、`src/hooks/index.ts`、`src/tools/index.ts`），且后续 Plan 在编译期依赖本 Plan 的产物（`WopalPluginConfig`、`resolveResources`），因此必须串行。

## Goal

以结构化三层配置体系取代 wopal-plugin 的扁平环境变量开关，并将 LLM / Embedding 客户端解耦为按能力依赖初始化的共享资源层。本 Plan 完成后，配置可读、可校验、可按空间覆盖，资源按启用能力的最小集初始化；插件现有功能行为保持不变。

## Technical Context

### Architecture Context

wopal-plugin 当前以扁平 `RuntimeEnvironment`（`$WOPAL_HOME/.env` + `<space>/.wopal/.env` + `process.env` 合并的字符串记录）驱动三个布尔开关。配置面无类型、无分组、无默认值声明；布尔语义靠字符串比较，拼写错误静默失效。

资源侧，`createMemorySystem`（`src/index.ts:71-115`）全量构造 store / embedder / llm / distillEngine，关闭任何功能都不减少初始化成本；`LLMClient` 被 memory 模块独占，其他模块借用时被绑上 memory 生命周期。

目标态见 `.wopal/docs/DESIGN-wopal-plugin.md` §4.1 与 §5。本 Plan 只交付配置加载器与资源层两块地基，功能开关的行为变更由后续 Plan 承接；配置默认值与现状等价，因此本 Plan 合入后行为不变。

wopal-space 模式下 ellamaka 只对 `settings.jsonc` 的 `ellamaka` 子节点做严格 schema 校验（`wopal-space.ts:299-303`），顶层是自由容器，`tui` 是现成先例。插件在顶层新增 `wopal` 节点无需改动 ellamaka。

### Research Findings

- 插件按 ellamaka instance 加载，`RuntimeContext` 已提供 `wopalHome` 与 `wopalSpaceRoot`，三层配置路径可确定性推导
- `MemoryStore` 只依赖 `wopalHome` 与 logger，不依赖 LLM；检索路径（store + embedder）与 LLM 路径可分离初始化
- ellamaka 使用 `jsonc-parser` 解析 settings（兼容注释与尾逗号），插件侧采用同一解析器可保持行为一致
- 插件已有 `zod` 依赖，可直接用于 schema 定义与校验

**参考资料**：
- `.wopal/docs/DESIGN-wopal-plugin.md` — 插件总体设计（§4.1 资源层、§5 配置体系）

### Key Decisions

- D-01: 配置承载于 settings 体系顶层 `wopal` 节点，三层 deep merge（全局 < 空间公共 < 空间私有）。理由：复用既有配置分层与 git 传播模型，不新增配置文件；顶层自由容器无需改 engine
- D-02: schema 由 zod 定义，字段声明类型与默认值，非法配置启动报错。理由：消除拼写错误静默失效
- D-03: `apiKey` 支持 `$VAR` 环境变量引用。理由：配置文件进 git 时不承载明文密钥
- D-04: 三个功能 env 开关（`WOPAL_RULES_INJECTION_ENABLED`、`WOPAL_MEMORY_ENABLED`、`WOPAL_MEMORY_INJECTION_ENABLED`）直接移除，不做兼容映射。理由：功能开关唯一真相源为配置文件，保留 env 通道等于在新体系旁留下 P6 批评的旧暗门（拼写静默失效、双路径语义歧义）；当前无任何 .env 使用这些开关，硬切换零迁移成本
- D-05: 日志诊断 env（`WOPAL_PLUGIN_LOG_LEVEL` / `_FILE` / `_MODULES`）保留为运行时覆盖，优先级高于配置文件。理由：启动脚本需按进程场景动态传参，静态配置无法表达；日志是观测手段，不改变功能行为
- D-06: LLM / Embedding 提升为插件级共享资源，按已启用能力的依赖最小集初始化，单资源失败只降级该资源
- D-07: 三个 prompt 路径 env 变量移除且不新增配置项，模板按约定路径解析（空间级 `<space>/.wopal/prompts/` → 用户级 `$WOPAL_HOME/prompts/` → 内联默认）。理由：约定路径已覆盖空间与用户两级自定义需求；当前 `.env` 未使用这些变量；新增配置项会为边缘场景增加 schema 与心智复杂度

### Key Interfaces

```typescript
// 配置结构（zod schema 推导类型）
interface WopalPluginConfig {
  llm?: { baseUrl: string; model: string; apiKey?: string };
  embedding?: { baseUrl: string; model: string; apiKey?: string };
  memory: { enabled: boolean; injection: boolean };   // 默认 { true, true }
  context: { enabled: boolean };                      // 默认 { true }
  logLevel?: string;
  logFile?: string;
  logModules?: string[];
}

// 配置加载契约
interface LoadedConfig {
  config: WopalPluginConfig;
  sources: Record<string, string>;   // 字段路径 → 来源层级，用于 effective 日志
}

// 资源层契约
interface PluginResources {
  store?: MemoryStore;
  embedder?: EmbeddingClient;
  llm?: LLMClient;
}
```

## In Scope

- 三层 `wopal` 配置加载器：JSONC 解析、deep merge、zod 校验、`$VAR` 引用解析、来源标注
- 将三个功能 env 开关（`WOPAL_RULES_INJECTION_ENABLED`、`WOPAL_MEMORY_ENABLED`、`WOPAL_MEMORY_INJECTION_ENABLED`）从 `RuntimeEnvironment` 白名单中移除（本 Plan 内 `src/index.ts` 的兼容读取保持行为等价，运行时切换归属 Plan 2）
- effective config 启动日志（含各项来源层级）
- LLM / Embedding 资源层解耦：`resolveResources` 按能力依赖推导最小资源集
- 移除 `createMemorySystem` 全量构造入口
- 修正 `memory/index.ts` 对 `LLMClient` 的归属导出
- `src/runtime-environment.ts` 职责收窄：仅加载密钥与日志诊断变量
- 移除三个 prompt 路径 env 变量（`WOPAL_DISTILL_PROMPT_FILE`、`WOPAL_DEDUP_PROMPT_FILE`、`WOPAL_TITLE_PROMPT_FILE`），保留空间级与用户级约定路径解析
- 改写 `.wopal/.env.example`：只列密钥与诊断变量，指向配置文件

## Out of Scope

- 功能开关的行为变更（memory 双开关接线、context 总开关、工具注册调整）— 由后续 Plan 承接
- 蒸馏模块归属迁移 — 由后续 Plan 承接
- 日志配置接入与 P7 修复 — 由后续 Plan 承接
- ellamaka engine 改动：完全在插件内实现
- 空间初始化模板（wopal-cli）对 `wopal` 节点的渲染
- 为 prompt 模板提供任意路径覆盖的配置项（按设计取舍只保留约定路径）

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| Config | `src/config/schema.ts`, `src/config/merge.ts`, `src/config/loader.ts`, `src/config/index.ts` | 创建 | 三层配置加载、校验、合并、来源标注 |
| Config tests | `src/config/loader.test.ts`, `src/config/merge.test.ts` | 创建 | 配置加载与校验测试 |
| Resources | `src/resources/index.ts`, `src/resources/llm-resource.ts`, `src/resources/embedding-resource.ts` | 创建 | 共享资源层与按依赖初始化 |
| Resources tests | `src/resources/index.test.ts` | 创建 | 资源最小集推导测试 |
| Runtime | `src/runtime-environment.ts` | 修改 | 职责收窄：仅加载密钥与日志诊断变量 |
| Prompts | `src/memory/prompts.ts` | 修改 | 移除 `WOPAL_*_PROMPT_FILE` 覆盖分支，只保留约定路径解析 |
| Entry | `src/index.ts` | 修改 | 接入配置加载与资源层，移除 `createMemorySystem` |
| Memory | `src/memory/index.ts` | 修改 | 调整 LLMClient 导出归属 |
| Docs | `.wopal/.env.example` | 修改 | 删除功能开关与 prompt 变量段，重写加载顺序说明 |

## Acceptance Criteria

### Agent Verification

1. [x] `cd .wopal/plugins/wopal-plugin && bun run typecheck` exit 0
2. [x] `cd .wopal/plugins/wopal-plugin && bun run test:run` 全部 pass
3. [x] `rg -n "createMemorySystem" .wopal/plugins/wopal-plugin/src --glob '!*.test.ts'` 无命中（全量构造入口已移除）
4. [x] `rg -n "topLevelExtraKeys|ConfigParse" .wopal/plugins/wopal-plugin/src` 无命中（插件不依赖 ellamaka 内部解析）
5. [x] `bun run test:run -- src/config` 全 pass，且测试文件包含跨层覆盖断言（全局 < 公共 < 私有）
6. [x] `bun run test:run -- src/resources` 全 pass，且测试断言「memory 关闭且 context 关闭时不构造 store/embedder/llm」
7. [x] `rg -n "WOPAL_MEMORY_ENABLED|WOPAL_RULES_INJECTION_ENABLED|WOPAL_MEMORY_INJECTION_ENABLED" .wopal/plugins/wopal-plugin/src/runtime-environment.ts` 无命中（白名单不含功能开关）；`src/index.ts` 允许保留三处兼容读取，其运行时移除归属 Plan 2
8. [x] `rg -n "WOPAL_DISTILL_PROMPT_FILE|WOPAL_DEDUP_PROMPT_FILE|WOPAL_TITLE_PROMPT_FILE" .wopal/plugins/wopal-plugin/src --glob '!*.test.ts'` 无命中（prompt 路径 env 覆盖已从生产代码移除）
9. [x] `rg -n "PROMPT_FILE|MEMORY_ENABLED|RULES_INJECTION_ENABLED" .wopal/.env.example` 无命中（env 模板已只保留密钥与诊断变量）
10. [x] `rg -n "WOPAL_LLM_API_KEY|WOPAL_EMBEDDING_API_KEY|WOPAL_PLUGIN_LOG_LEVEL" .wopal/.env.example` 命中（密钥与诊断变量保留）
11. [x] `bun run test:run -- src/memory` 全 pass，且 prompts 测试断言「空间级路径命中」「用户级路径回退」「均未命中时使用内联默认」

### User Validation

#### Scenario 1: 三层配置生效
- Goal: 确认配置文件能实际驱动插件，且层级覆盖与非法值拦截符合预期
- Precondition: ontology 已应用本 Plan 变更，ellamaka 已重启
- User Actions:
  1. 在 `.wopal/config/settings.local.jsonc` 写入 `"wopal": { "memory": { "injection": false } }`，重启 ellamaka，观察启动日志
  2. 在 `~/.wopal/config/settings.jsonc` 写入不同值，观察空间层是否仍覆盖全局层
  3. 写入非法值如 `"wopal": { "memory": { "enabled": "yes" } }`，重启观察报错
- Expected Result: 启动日志输出 effective config 并标明各项来源层级；空间层覆盖全局层；非法配置启动即报错，不静默降级

- [x] 用户已完成上述功能验证并确认结果符合预期

## Implementation

### Task 1: 三层配置加载器（schema + merge + loader）

**Verification Intent**: AC#1, AC#2, AC#5, AC#7

**Behavior**:
输入 → 输出映射：
- `loadWopalConfig({ global: A, spacePublic: B })`，A.llm.model="m1" 且 B.memory.injection=false → `config.memory.injection === false` 且 `config.llm.model === "m1"`
- 同一字段在全局/公共/私有三层分别取值 → 私有值生效，`sources["memory.injection"]` 指向私有层级
- `apiKey: "$FOO"` 且 `process.env.FOO="k"` → 解析为 `"k"`；`process.env.FOO` 未设置 → 抛错并指明变量名
- `{ memory: { enabled: "yes" } }` → zod 校验失败并抛错（不静默降级）
- 某层文件不存在 → 跳过该层且不报错
- 某层 JSONC 含注释与尾逗号 → 正常解析
- 解析到的层级结构缺失 `wopal` 节点 → 视为空配置，不影响其余层

**Files**: `src/config/schema.ts`, `src/config/merge.ts`, `src/config/loader.ts`, `src/config/index.ts`, `src/config/loader.test.ts`, `src/config/merge.test.ts`

**Pre-read**: `.wopal/docs/DESIGN-wopal-plugin.md`（§5 Configuration）、`src/runtime-context.ts`

**Design**:
分三阶段 TDD：
1. RED：编写测试覆盖上述 Behavior 的全部映射
2. GREEN：`schema.ts` 定义 zod schema、默认值与推导类型；`merge.ts` 实现 deep merge（叶子覆盖、数组整体替换）并累计来源标注；`loader.ts` 读取三层文件、用 `jsonc-parser` 解析、提取顶层 `wopal` 节点、按序 merge、解析 `$VAR`、包装可读错误；`index.ts` 导出统一入口
3. REFACTOR：清理重复的路径推导与错误包装

约束：schema 校验失败必须抛出含文件路径与字段的可读错误，不得回退默认值；`$VAR` 未命中必须抛错，不得降级为空值；三层路径由 `RuntimeContext` 的 `wopalHome` 与 `wopalSpaceRoot` 推导，非 WopalSpace instance 时跳过空间两层；功能开关只从配置文件读取，不读取任何功能类 env。

**TDD**: true

**Changes**:
1. 创建 `src/config/schema.ts`：zod schema + 默认值 + 类型 `WopalPluginConfig`
2. 创建 `src/config/merge.ts`：deep merge 与来源标注
3. 创建 `src/config/loader.ts`：三层读取、JSONC 解析、`wopal` 节点提取、`$VAR` 解析、错误包装
4. 创建 `src/config/index.ts`：导出加载入口与类型
5. 创建 `src/config/loader.test.ts`、`src/config/merge.test.ts` 覆盖 Behavior

**Verify**:
`cd .wopal/plugins/wopal-plugin && bun run test:run -- src/config` 全部 pass

**Done**:
任务产出：可独立测试的三层配置加载器，支持深合并、来源标注与 `$VAR` 引用
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

### Task 2: 资源层解耦与按依赖初始化

**Verification Intent**: AC#1, AC#2, AC#3, AC#6

**Behavior**:
输入 → 输出映射：
- `memory.enabled=false, context.enabled=false` → 不构造 store / embedder / llm
- `memory.enabled=true, context.enabled=false` → 构造 store + embedder，不构造 llm
- `memory.enabled=false, context.enabled=true` → 构造 llm，不构造 store / embedder
- 两者皆 true → 三者均构造
- memory 启用但缺 embedding 配置 → store/embedder 初始化降级并 warn，llm 不受影响
- 某资源构造抛错 → 仅该资源缺失，其余资源正常

**Files**: `src/resources/index.ts`, `src/resources/llm-resource.ts`, `src/resources/embedding-resource.ts`, `src/resources/index.test.ts`, `src/index.ts`, `src/memory/index.ts`

**Pre-read**: `src/index.ts`（`createMemorySystem` 与装配流程）、`src/llm-client.ts`、`src/memory/embedder.ts`、`src/memory/store.ts`

**Design**:
分三阶段 TDD：
1. RED：为四种能力组合的资源构造最小集与单资源降级编写测试（注入可观测构造依赖，断言哪些资源被创建）
2. GREEN：`embedding-resource.ts` / `llm-resource.ts` 各自封装构造、初始化与错误边界；`resources/index.ts` 实现 `resolveResources(config, runtime)`，按 `memory.enabled` 推导 store + embedder、按 `context.enabled` 推导 llm；`index.ts` 删除 `createMemorySystem`，改用资源层装配
3. REFACTOR：收敛重复的初始化样板

约束：各资源独立 try/catch，失败仅降级该资源并记录 `{ err: error }`；`LLMClient` 的归属导出不留在 memory 模块，避免 memory 反向声明 LLM 所有权；本 Plan 不接线功能开关到 hook/tool（由后续 Plan 承接），仅完成资源装配与配置读取。

**TDD**: true

**Changes**:
1. 创建 `src/resources/embedding-resource.ts`、`src/resources/llm-resource.ts`：构造、初始化与错误边界
2. 创建 `src/resources/index.ts`：`resolveResources(config, runtime)` 按能力依赖推导最小资源集
3. 创建 `src/resources/index.test.ts` 覆盖四种组合与单资源降级
4. 修改 `src/index.ts`：接入配置加载与资源层，移除 `createMemorySystem`
5. 修改 `src/memory/index.ts`：调整 `LLMClient` 导出归属

**Verify**:
`cd .wopal/plugins/wopal-plugin && bun run test:run -- src/resources` 全部 pass 且 `bun run typecheck` exit 0

**Done**:
任务产出：共享资源层，资源按启用能力的最小集初始化，单资源失败不连锁拖垮
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤.

### Task 3: env 职责收窄、prompt 路径移除与 .env.example 改写

**Verification Intent**: AC#1, AC#2, AC#8, AC#9, AC#10, AC#11

**Behavior**:
输入 → 输出映射：
- `.env` 中的 `WOPAL_LLM_API_KEY` / `WOPAL_EMBEDDING_API_KEY` / `WOPAL_PLUGIN_LOG_*` → 仍被读取并生效
- `.env` 中的 `WOPAL_MEMORY_ENABLED` / `WOPAL_RULES_INJECTION_ENABLED` / `WOPAL_MEMORY_INJECTION_ENABLED` → 不被读取，对行为无影响
- `.env` 中的 `WOPAL_DISTILL_PROMPT_FILE` / `WOPAL_DEDUP_PROMPT_FILE` / `WOPAL_TITLE_PROMPT_FILE` → 不被读取，对行为无影响
- `<space>/.wopal/prompts/distill.md` 存在 → 解析到该文件
- 空间级不存在但 `$WOPAL_HOME/prompts/distill.md` 存在 → 回退到用户级
- 两级均不存在 → 使用内联默认模板
- `.env.example` 内容 → 只包含密钥与日志诊断变量，无功能开关与 prompt 变量

**Files**: `src/runtime-environment.ts`, `src/memory/prompts.ts`, 对应 `*.test.ts`, `.wopal/.env.example`

**Pre-read**: `.wopal/docs/DESIGN-wopal-plugin.md`（§5.3 Prompt 模板解析、§5.4 环境变量角色）、`src/runtime-environment.ts`、`src/memory/prompts.ts`

**Design**:
分三阶段 TDD：
1. RED：为 env 白名单过滤（密钥与诊断变量保留、功能与 prompt 变量忽略）、prompt 约定路径三级解析编写测试
2. GREEN：`runtime-environment.ts` 改为只加载密钥与诊断变量（白名单过滤，其余变量不进入 RuntimeEnvironment）；`prompts.ts` 删除 `resolveEnvFilePath` 与 `WOPAL_*_PROMPT_FILE` 分支，保留空间级 → 用户级 → 内联默认的三级解析；改写 `.wopal/.env.example`，删除功能开关段与 prompt 变量段，保留密钥与日志变量，重写加载顺序说明并移除已失效的 `WOPAL_MEMORY_ENABLED` 引用
3. REFACTOR：清理 prompts 中已无消费者的 env 参数与 `RuntimeEnvironment` 传递

约束：`.env` 中保留的密钥与诊断变量行为不变；prompt 解析的文件名（`distill.md` / `dedup.md` / `title.md`）与路径约定不变；本 Plan 不移动 prompt 文件位置（归属迁移由后续 Plan 承接）；`.env.example` 的说明需与设计文档 §5.3 / §5.4 一致，明确「功能配置在 settings.jsonc，env 只承载密钥与日志覆盖」。

**TDD**: true

**Changes**:
1. 修改 `src/runtime-environment.ts`：白名单过滤，仅加载密钥与日志诊断变量
2. 修改 `src/memory/prompts.ts`：删除 env 路径覆盖分支，保留约定路径三级解析
3. 修改/创建对应测试
4. 改写 `.wopal/.env.example`：删除功能开关段与 prompt 变量段，重写加载顺序说明

**Verify**:
`cd .wopal/plugins/wopal-plugin && bun run test:run -- src/memory src/runtime-environment.test.ts` 全部 pass

**Done**:
任务产出：env 职责收窄为密钥与诊断覆盖，prompt 只走约定路径，`.env.example` 与新体系一致
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

## Delegation Strategy

| Wave | Task | 执行者 | 依赖 | 委派理由 |
|------|------|--------|------|---------|
| 1 | Task 1 | fae | 无 | 配置加载器为地基，自包含可独立验证 |
| 1 | Task 3 | fae | 无 | env 收窄与 prompt 路径移除，改动文件与 Task 1/2 不重叠，可并行 |
| 2 | Task 2 | fae | Task 1 | 资源层消费配置，需加载器就位 |

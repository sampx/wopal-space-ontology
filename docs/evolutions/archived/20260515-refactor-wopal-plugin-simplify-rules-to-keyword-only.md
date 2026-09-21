# 简化规则注入：只保留关键词匹配 + Agent 作用域

## Metadata

- **Type**: refactor
- **Target Project**: wopal-space-ontology（`.wopal/wopal-plugin/`）
- **Project Path**: .wopal
- **Project Type**: ontology-worktree
- **Created**: 2026-05-15
- **Status**: done
- **Prerequisite**: Plan #139（Rules 注入迁移到 messages.transform）已完成并归档
- **Worktree**: plugin-simplify-rules-to-keyword-only | /Users/sam/coding/wopal/wopal-workspace/.worktrees/ontology-plugin-simplify-rules-to-keyword-only

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

删除 rules 模块中 globs/tools 匹配和 contextPaths 全链路，规则注入简化为 keywords-only + Agent 作用域。

## Technical Context

当前 `formatter.ts` 支持 3 种 OR 匹配条件：

- **globs** → 匹配 `contextPaths`（只在首次 seed 时采集，后续不再更新，实际匹配效果差）
- **tools** → 调用 `client.tool?.ids` + `client.mcp?.status` 查询可用工具（几乎永远为 true，语义不对且成本高）
- **keywords** → 直接匹配用户意图（最有效）

`contextPaths` 整个数据链路（`path-extractor.ts` seed → `sessionStore.contextPaths` → `command-hooks.ts` 工具追踪 → `compaction.ts` 注入）的唯一用途就是供 globs 匹配，globs 删除后全链路无消费者。

**风险**：现有 `.wopal/rules/` 下规则文件的 keywords 字段使用了 glob pattern（如 `**/*.ts`），删除 globs 匹配后这些规则无法触发，需前置修正为语义关键词。

## In Scope

- 删除 globs 和 tools 触发逻辑
- 无 keywords 的规则不注入（静默跳过，原"无条件规则"行为删除）
- 规则发现路径改为 `~/.wopal/rules/`（全局）和 `.wopal/rules/`（项目级）
- 支持 Agent 作用域：`rules/<agent-name>/*.md` 仅该 agent，`rules/*.md` 通用
- 从 messages 提取当前 agent name（`info.agent`）
- 删除 contextPaths 全链路：path-extractor、sessionStore.contextPaths、message-hooks seed、command-hooks 工具追踪、compaction 上下文注入
- 清理死代码：`RuleMetadata` 的 globs/tools 字段、`parseRuleMetadata` 中 globs/tools 解析、`minimatch` 依赖、`mcp-tools.ts`
- 更新 wopal-plugin 文档：删除 `docs/compaction-handling.md`，修改 `docs/rules.md`

## Out of Scope

- 不改动 Memory 注入
- 不改动 Skill Reload
- 不改动 `message-context.ts` 中 `extractSessionID`、`extractLatestUserPrompt`、`normalizeContextPath`、`sanitizePathForContext` 函数（仍被其他模块使用）

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| Matcher | `rules/matcher.ts`, `rules/matcher.test.ts` | 修改 | 删除 globs/tools 函数和 minimatch import |
| Formatter | `rules/formatter.ts`, `rules/formatter.test.ts` | 修改 | 删除 globs/tools 匹配；无 keywords 规则 skip；新增 agentName 参数和过滤 |
| Discoverer | `rules/discoverer.ts`, `rules/discoverer.test.ts` | 修改 | 路径改为 `.wopal/rules`；RuleMetadata 删除 globs/tools；新增 agentScope |
| Rules index | `rules/index.ts` | 修改 | 移除 globs/tools/path-extractor 导出 |
| Path extractor | `rules/path-extractor.ts`, `rules/path-extractor.test.ts` | 删除 | 唯一消费者 contextPaths seed 已删除 |
| Mcp tools | `hooks/mcp-tools.ts`, `hooks/mcp-tools.test.ts` | 删除 | tools 匹配已删除 |
| Message context | `hooks/message-context.ts`, `hooks/message-context.test.ts` | 修改 | 新增 agent 字段；删除 toExtractableMessages |
| Rule injector | `hooks/rule-injector.ts`, `hooks/rule-injector.test.ts` | 修改 | 删除 queryAvailableToolIDs；简化 injectRules 签名 |
| Rule message injector | `hooks/rule-message-injector.ts` | 修改 | 新增 extractAgentName；删除 contextPaths |
| Message hooks | `hooks/message-hooks.ts`, `hooks/message-hooks.test.ts` | 修改 | 删除 contextPaths seed 逻辑 |
| Command hooks | `hooks/command-hooks.ts`, `hooks/command-hooks.test.ts` | 修改 | 删除工具路径追踪 |
| Compaction | `hooks/compaction.ts`, `hooks/compaction.test.ts` | 修改 | 删除 contextPaths 注入 |
| Session store | `session-store.ts`, `session-store.test.ts` | 修改 | 删除 contextPaths 字段 |
| Hooks index | `hooks/index.ts` | 修改 | 简化 RuleInjectorContext |
| Plugin entry | `index.ts` | 修改 | 简化 context 构造 |
| Dependencies | `package.json` | 修改 | 移除 minimatch 和 @types/minimatch |
| Rule files | `.wopal/rules/*.md` | 修改 | keywords 从 glob pattern 修正为语义关键词 |
| Docs | `docs/compaction-handling.md` | 删除 | 内容依赖 contextPaths |
| Docs | `docs/rules.md` | 修改 | 反映新规则系统 |

## Implementation

### Task 1: 简化 matcher + formatter（T1）

**Files**: `rules/matcher.ts`, `rules/matcher.test.ts`, `rules/formatter.ts`, `rules/formatter.test.ts`

**Changes**:
- [x] Step 1: 删除 `fileMatchesGlobs` 函数和测试
- [x] Step 2: 删除 `toolsMatchAvailable` 函数和测试
- [x] Step 3: 删除 `import { minimatch } from "minimatch"`
- [x] Step 4: 只保留 `promptMatchesKeywords`
- [x] Step 5: formatter 删除 globs 和 tools 匹配逻辑
- [x] Step 6: formatter 无 keywords 的规则直接 skip（原"无条件规则"不再注入）
- [x] Step 7: formatter 新增 `agentName` 参数，agent 过滤：`relativePath` 在 `<agentName>/` 子目录下才参与匹配
- [x] Step 8: 通用规则（根目录）所有 agent 都可匹配

**Verification**:
- [x] Step 1: `bun run test:run` matcher + formatter 测试通过
- [x] Step 2: 确认 `grep -rn "fileMatchesGlobs\|toolsMatchAvailable" src/rules/` → 无结果

### Task 2: 规则文件 + discoverer 更新（T2）

**Files**: `.wopal/rules/*.md`, `rules/discoverer.ts`, `rules/discoverer.test.ts`

**Changes**:
- [x] Step 1: `typescript.md` keywords 从 `['**/*.ts', '**/*.tsx']` 修正为 `['typescript', 'ts', '.ts']`
- [x] Step 2: `python.md` keywords 从 `['**/*.py']` 修正为 `['python', 'py', '.py']`
- [x] Step 3: `astro.md` keywords 从 `['**/*.astro', '**/astro.config.*']` 修正为 `['astro']`
- [x] Step 4: 确认 `mem-rule.md` keywords 正确
- [x] Step 5: discoverer 全局路径改为 `~/.wopal/rules/`（优先）和 `$XDG_CONFIG_HOME/wopal/rules/`（备选）
- [x] Step 6: discoverer 项目级路径改为 `.wopal/rules/`
- [x] Step 7: `DiscoveredRule` 新增 `agentScope?: string` 字段（从子目录名推断）
- [x] Step 8: `RuleMetadata` 删除 `globs` 和 `tools` 字段
- [x] Step 9: `parseRuleMetadata` 删除 globs/tools 解析逻辑

**Verification**:
- [x] Step 1: `bun run test:run` discoverer 测试通过
- [x] Step 2: 确认 `RuleMetadata` 无 globs/tools（类型检查）
- [x] Step 3: 确认 `grep -rn "\.opencode/rules\|config/opencode" src/rules/discoverer.ts` → 无结果

### Task 3: contextPaths 全链路删除（T3）

**Files**: `rules/path-extractor.ts`, `rules/path-extractor.test.ts`, `session-store.ts`, `session-store.test.ts`, `hooks/message-hooks.ts`, `hooks/message-hooks.test.ts`, `hooks/message-context.ts`, `hooks/message-context.test.ts`, `hooks/command-hooks.ts`, `hooks/command-hooks.test.ts`, `hooks/compaction.ts`, `hooks/compaction.test.ts`

**Changes**:
- [x] Step 1: 删除 `rules/path-extractor.ts` 和 `rules/path-extractor.test.ts`
- [x] Step 2: `session-store.ts` 删除 `contextPaths` 字段定义、初始化、拷贝逻辑
- [x] Step 3: `message-hooks.ts` 删除 seed 逻辑（`extractFilePathsFromMessages` + `normalizeContextPath` + contextPaths.add）
- [x] Step 4: `message-context.ts` 删除 `toExtractableMessages` 函数和 `Message`/`MessagePart` import
- [x] Step 5: `command-hooks.ts` 删除 `onToolExecuteBefore` 中 contextPaths.add 逻辑（保留 skill 追踪）
- [x] Step 6: `compaction.ts` 删除 `onSessionCompacting` 中 contextPaths 读取和注入逻辑，保留 `markCompacting` 调用
- [x] Step 7: 更新所有对应的 test 文件

**Verification**:
- [x] Step 1: `bun run test:run` 全部通过
- [x] Step 2: `grep -rn "contextPaths" src/` → 无结果
- [x] Step 3: `grep -rn "extractFilePathsFromMessages\|toExtractableMessages" src/` → 无结果

### Task 4: 简化 rule-injector + agent 提取（T4）

**Files**: `hooks/rule-injector.ts`, `hooks/rule-injector.test.ts`, `hooks/rule-message-injector.ts`, `hooks/message-context.ts`

**Changes**:
- [x] Step 1: `message-context.ts` 的 `MessageWithInfo.info` 新增 `agent?: string` 字段
- [x] Step 2: `rule-injector.ts` 删除 `queryAvailableToolIDs` 函数
- [x] Step 3: `rule-injector.ts` 的 `RuleInjectorContext` 删除 `client` 字段
- [x] Step 4: `rule-injector.ts` 的 `injectRules` 参数简化为 `(ruleFiles, agentName, userPrompt)`
- [x] Step 5: `rule-message-injector.ts` 新增 `extractAgentName`（从 messages 末尾向前遍历，返回第一个含 `info.agent` 的消息的 agent 值）
- [x] Step 6: `rule-message-injector.ts` 调用 `injectRules` 时传入 `agentName`，删除 contextPaths 相关

**Verification**:
- [x] Step 1: `bun run test:run` rule-injector 测试通过
- [x] Step 2: Agent name 提取测试：user message `info.agent = "fae"` → 返回 "fae"
- [x] Step 3: Agent name 降级测试：无 agent 字段 → 返回 undefined

### Task 5: 清理依赖 + 文档（T5）

**Files**: `hooks/mcp-tools.ts`, `hooks/mcp-tools.test.ts`, `package.json`, `rules/index.ts`, `hooks/index.ts`, `index.ts`, `docs/compaction-handling.md`, `docs/rules.md`

**Changes**:
- [x] Step 1: 删除 `hooks/mcp-tools.ts` 和 `hooks/mcp-tools.test.ts`
- [x] Step 2: `package.json` 移除 `minimatch` 和 `@types/minimatch`，运行 `bun install`
- [x] Step 3: `rules/index.ts` 移除 `fileMatchesGlobs`、`toolsMatchAvailable`、`extractFilePathsFromMessages`、`Message`、`MessagePart` 导出
- [x] Step 4: `hooks/index.ts` 简化 `RuleInjectorContext` 构造，移除 `client` 依赖
- [x] Step 5: `index.ts` 简化 context 构造
- [x] Step 6: 删除 `docs/compaction-handling.md`
- [x] Step 7: 更新 `docs/rules.md`

**Verification**:
- [x] Step 1: `bun run build` 编译通过
- [x] Step 2: `bun run test:run` 全部通过
- [x] Step 3: `grep "minimatch" package.json` → 无结果
- [x] Step 4: `grep -rn "queryAvailableToolIDs\|extractConnectedMcpCapabilityIDs" src/` → 无结果

## Worktree Setup (只能由 wopal 执行)

1. 加载 `dev-flow` 技能
2. 执行 `flow.sh approve <issue-or-plan> --confirm --worktree`
3. 进入 worktree 后检查依赖：`cd .wopal/wopal-plugin && bun install`
4. 所有 Task 委派给 fae 在 worktree 中并行执行
5. **合并回 space/main**：全部 Task 完成并通过验证后，将 worktree feature 分支合并到 `space/main`
7. **清理**：合并完成后删除 worktree（`git worktree remove`）

## Delegation Strategy

| 批次 | Task | 执行者 | 依赖 |
|------|------|--------|------|
| 1 | Task 1（matcher + formatter） | fae | 无 |
| 1 | Task 2（规则文件 + discoverer） | fae | 无 |
| 1 | Task 3（contextPaths 全链路） | fae | 无 |
| 2 | Task 4（rule-injector + agent 提取） | fae | Task 1 |
| 2 | Task 5（清理依赖 + 文档） | fae | Task 1 |
| 3 | 集成收尾（rules/index + hooks/index + index.ts）+ build + test | Wopal | Task 1-5 |

## Test Plan

#### Unit Tests

##### Case U1: Keyword 匹配
- Goal: 有 keywords 的规则正确匹配
- Fixture: mock 规则文件，keywords: ["typescript"]
- Execution:
  - [x] Step 1: userPrompt = "帮我写 typescript 代码"
  - [x] Step 2: 调用 `readAndFormatRules`
  - [x] Step 3: 确认返回匹配的规则内容
- Expected Evidence: 规则内容包含

##### Case U2: 无 keywords 的规则被跳过
- Goal: 无 keywords 的规则不注入
- Fixture: mock 规则文件，无 frontmatter
- Execution:
  - [x] Step 1: 调用 `readAndFormatRules`
  - [x] Step 2: 确认返回空
- Expected Evidence: content 为空

##### Case U3: Agent 专属规则过滤
- Goal: wopal/ 子目录规则只匹配 wopal agent
- Fixture: 规则文件在 `wopal/workflow.md`，keywords: ["dev-flow"]
- Execution:
  - [x] Step 1: agentName = "wopal"，匹配成功
  - [x] Step 2: agentName = "fae"，不参与匹配
  - [x] Step 3: agentName = undefined，不参与匹配
- Expected Evidence: 只有 wopal agent 时返回内容

##### Case U4: 通用规则所有 agent 都可匹配
- Goal: 根目录规则所有 agent 都可触发
- Fixture: 规则文件 `typescript.md`，keywords: ["typescript"]
- Execution:
  - [x] Step 1: agentName = "wopal"，匹配成功
  - [x] Step 2: agentName = "fae"，匹配成功
- Expected Evidence: 两种 agent 都返回内容

##### Case U5: Agent name 提取
- Goal: 从 messages 正确提取 agent name
- Fixture: messages 包含 user message（`info.agent = "fae"`）和 previous assistant message（`info.agent = "wopal"`），最新的是 user message
- Execution:
  - [x] Step 1: 调用 `extractAgentName`
  - [x] Step 2: 确认返回 "fae"
- Expected Evidence: 返回最新含 agent 字段的消息的 agent 值

##### Case U5b: Agent name 提取 - 降级
- Goal: messages 中无 agent 字段时返回 undefined
- Fixture: messages 中 info.agent 均为 undefined
- Execution:
  - [x] Step 1: 调用 `extractAgentName`
  - [x] Step 2: 确认返回 undefined
- Expected Evidence: 返回 undefined，降级为通用规则匹配

##### Case U6: Agent 作用域发现
- Goal: discoverer 从子目录推断 agentScope
- Fixture: 规则文件在 `fae/execution-rules.md`
- Execution:
  - [x] Step 1: 调用 `discoverRuleFiles`
  - [x] Step 2: 确认返回的 DiscoveredRule.agentScope = "fae"
- Expected Evidence: agentScope 正确推断

#### Integration Tests

N/A — 本次为内部重构，不涉及外部集成点变化。

#### E2E Tests

N/A — 用户手动验证覆盖真实场景。

#### Regression Tests

##### Case R1: 原"无条件规则"不再注入
- Goal: 无 frontmatter 的规则文件不再被注入
- Fixture: 规则文件无 frontmatter（旧行为会当作"unconditional"注入）
- Execution:
  - [x] Step 1: 调用 `readAndFormatRules`，规则文件无 keywords
  - [x] Step 2: 确认返回空 content
- Expected Evidence: content 为空，matchedRules 为空

##### Case R2: contextPaths 全链路已清除
- Goal: 确认 contextPaths 相关代码全部删除
- Fixture: 代码库
- Execution:
  - [x] Step 1: `grep -rn "contextPaths" src/` → 无结果
  - [x] Step 2: `grep -rn "extractFilePathsFromMessages" src/` → 无结果
  - [x] Step 3: `grep -rn "toExtractableMessages" src/` → 无结果
- Expected Evidence: 所有 grep 无结果

##### Case R3: compaction 不受影响
- Goal: compaction hook 正常触发，但不注入 contextPaths
- Fixture: sessionStore 无 contextPaths 字段
- Execution:
  - [x] Step 1: 触发 onSessionCompacting
  - [x] Step 2: 确认 hook 正常返回，output.context 不含 "OpenCode Rules"
- Expected Evidence: compaction hook 无报错

##### Case R4: Skill Reload 不受影响
- Goal: Skill Reload 注入独立于规则
- Fixture: sessionStore 标记 needsSkillReload
- Execution:
  - [x] Step 1: 调用 injectSkillReload
  - [x] Step 2: 确认正常注入
- Expected Evidence: 不受影响

## Acceptance Criteria

### Agent Verification

- [x] `bun run build` 编译通过
- [x] `bun run test:run` 通过
- [x] `grep -rn "fileMatchesGlobs" src/` → 无结果
- [x] `grep -rn "toolsMatchAvailable" src/` → 无结果
- [x] `grep -rn "queryAvailableToolIDs" src/` → 无结果
- [x] `grep -rn "extractConnectedMcpCapabilityIDs" src/` → 无结果
- [x] `grep -rn "minimatch" src/` → 无结果
- [x] `grep "minimatch" package.json` → 无结果
- [x] `grep -rn "contextPaths" src/` → 无结果
- [x] `grep -rn "extractFilePathsFromMessages" src/` → 无结果
- [x] `grep -rn "toExtractableMessages" src/` → 无结果
- [x] `grep -rn "\.opencode/rules\|config/opencode" src/` → 无结果
- [x] `RuleMetadata` 接口中无 `globs` 和 `tools` 字段
- [x] `parseRuleMetadata` 中无 globs/tools 解析逻辑
- [x] `docs/compaction-handling.md` 已删除
- [x] `docs/rules.md` 已更新

### User Validation

#### Scenario 1: 关键词规则正常注入
- Goal: 有 keywords 的规则正确注入到 user message
- Precondition: `.wopal/rules/` 下放置含语义 keywords 的规则文件
- User Actions:
  1. 发送匹配关键词的消息
  2. 观察 debug 日志或 agent 行为
- Expected Result: 规则被遵守

#### Scenario 2: Agent 专属规则隔离
- Goal: fae 子目录规则不影响 wopal agent
- Precondition: `.wopal/rules/fae/` 下放置规则，`.wopal/rules/` 根目录无同名规则
- User Actions:
  1. wopal agent 发送消息
  2. 确认 fae 规则未被注入
- Expected Result: wopal 不受 fae 规则影响

#### Scenario 3: 路径迁移
- Goal: 规则从 `.opencode/rules/` 迁移到 `.wopal/rules/` 后正常加载
- Precondition: 规则文件已移到 `.wopal/rules/`
- User Actions:
  1. 重启 ellamaka
  2. 触发规则关键词
- Expected Result: 规则正常生效

- [x] 用户已完成上述功能验证并确认结果符合预期

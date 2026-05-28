# OpenCode Task Tool 与 wopal_task 子会话机制深度对比研究

> 基于 OpenCode 源码（`labs/ref-repos/opencode/`）逐行追踪，对比内置 task tool 与 wopal-plugin 插件中 wopal_task 在子会话创建、上下文加载、工具/Skill/Agent 可见性方面的差异，并提出增强方案。

---

## 1. 两条 API 路径：源码级追踪

### 1.1 架构总览

```
┌─ Internal Path ──────────────────────────────────────┐
│  TaskTool.execute()                                  │
│    → sessions.create({ parentID, permission })       │
│    → Effect → Session.Service.create() → createNext()│
│                                                      │
│    → ops.prompt({ sessionID, model, agent, tools })  │
│    → SessionPrompt.prompt() → createUserMessage()    │
│    → loop() → runLoop()                              │
└──────────────────────────────────────────────────────┘
                       ║
              服务器端完全相同
                       ║
┌─ SDK Path ───────────────────────────────────────────┐
│  client.session.create()                             │
│    → POST /session                                   │
│    → SessionShare.create() → Session.Service.create()│
│      → createNext() (完全相同的 Effect 函数)          │
│                                                      │
│  client.session.promptAsync()                        │
│    → POST /session/:id/prompt_async                  │
│    → SessionPrompt.prompt() (完全相同的 Effect 函数)  │
│    → createUserMessage() → loop() → runLoop()        │
└──────────────────────────────────────────────────────┘
```

**核心结论**：两条路径在服务器端完全汇合，使用相同的 `SessionPrompt.prompt()` → `runLoop()` 管线。差异仅在于调用方传入了什么参数。

### 1.2 `sessions.create()` vs `client.session.create()` — 完全等价

| 参数 | 内部 Effect 路径 | SDK HTTP 路径 | 代码依据 |
|------|----------------|--------------|---------|
| `parentID` | ✅ | ✅ body.parentID | `session/index.ts:686` / `openapi.json:2249` |
| `permission` | ✅ `Permission.Ruleset` | ✅ `PermissionRuleset` | `index.ts:690` / `openapi.json:2268` |
| `workspaceID` | ✅ | ✅ | `index.ts:691` / `openapi.json:2271` |
| `title` | ✅ | ✅ | `index.ts:688` / `openapi.json:2252` |
| `directory` | 从 `InstanceState.directory` | 从 `InstanceState.directory` | `index.ts:500` |

**存储逻辑**（`index.ts:375-413` `createNext`）：

```typescript
const createNext = Effect.fn("Session.createNext")(function* (input) {
  const result: Info = {
    id: SessionID.descending(input.id),
    parentID: input.parentID,        // 父会话链接
    directory: yield* InstanceState.directory,  // 共享实例目录
    permission: input.permission,    // 权限规则集
    title: input.title ?? createDefaultTitle(!!input.parentID),
    // ...
  }
})
```

**`parentID` 的作用**：仅存储在 DB `parent_id` 列中。用于查询子会话、TUI 层级展示、HTTP 头 `x-parent-session-id`。**不会导致子会话继承父会话的上下文、指令或系统提示词。**

**唯一差异**：SDK 路径经过 `SessionShare.create()` 包装（`share/session.ts:43-50`），如果启用 auto-share 会自动分享，不影响上下文加载。

### 1.3 `ops.prompt()` vs `client.session.promptAsync()` — 完全等价

**`PromptInput` schema**（`prompt.ts:1697-1761`）：

| 参数 | SDK 支持 | 内部路径支持 | 处理方式 |
|------|---------|------------|---------|
| `parts` | ✅ | ✅ | 创建用户消息 |
| `agent` | ✅ | ✅ | `agents.get(name)` 解析 |
| `model` | ✅ | ✅ | `input.model ?? ag.model ?? lastModel()` |
| `tools` | ✅ (废弃) | ✅ | 转换为 `session.permission` |
| `system` | ✅ | ✅ | 追加到系统提示词 |
| `format` | ✅ | ✅ | 结构化输出控制 |
| `noReply` | ✅ | ✅ | 跳过 runLoop |
| `variant` | ✅ | ✅ | 模型变体选择 |

**汇合点**（`prompt.ts:1268-1287`）：

```typescript
const prompt: (input: PromptInput) => Effect.Effect<MessageV2.WithParts> = 
  Effect.fn("SessionPrompt.prompt")(function* (input: PromptInput) {
    const session = yield* sessions.get(input.sessionID)
    const message = yield* createUserMessage(input)
    yield* sessions.touch(input.sessionID)

    // tools 权限转换 — 两条路径都走这里
    const permissions: Permission.Ruleset = []
    for (const [t, enabled] of Object.entries(input.tools ?? {})) {
      permissions.push({ permission: t, action: enabled ? "allow" : "deny", pattern: "*" })
    }
    if (permissions.length > 0) {
      session.permission = permissions
      yield* sessions.setPermission({ sessionID: session.id, permission: permissions })
    }

    return yield* loop({ sessionID: input.sessionID })
  })
```

---

## 2. 权限合并机制

### 2.1 `Permission.merge` 与 `evaluate`

**`merge`**（`permission/index.ts:293-295`）：
```typescript
export function merge(...rulesets: Ruleset[]): Ruleset {
  return rulesets.flat()  // 简单拼接数组
}
```

**`evaluate`**（`permission/evaluate.ts:9-14`）：
```typescript
export function evaluate(permission, pattern, ...rulesets) {
  const rules = rulesets.flat()
  const match = rules.findLast(  // 最后一条匹配的规则胜出
    (rule) => Wildcard.match(permission, rule.permission) && Wildcard.match(pattern, rule.pattern),
  )
  return match ?? { action: "ask", permission, pattern: "*" }
}
```

**规则优先级**：数组中靠后的规则覆盖靠前的。

### 2.2 权限合并顺序

工具调用时（`llm.ts:400`）：
```typescript
Permission.merge(input.agent.permission, input.permission ?? [])
//                    ↑ 先放 agent 规则           ↑ 后放 session 规则
// findLast → 后者覆盖前者
```

**结论**：session 级 deny 规则排在数组后面，`findLast` 优先命中 → **session 配置覆盖 agent 默认**。

### 2.3 `tools` 参数与 `permission` 的关系

`promptAsync` 中传入 `tools` 会转换为 session permission。

**⚠️ 重要**：`prompt()` 中的 `session.permission = permissions` 是**赋值**不是追加（`prompt.ts:1280`）。如果你同时在 `create()` 和 `promptAsync()` 中传权限，**后者覆盖前者**。

**正确做法**：所有权限控制放在同一个地方——要么都在 `create` 的 `permission` 中，要么都在 `promptAsync` 的 `tools` 中。

---

## 3. 子会话上下文加载全流程

### 3.1 `runLoop()` 中的系统提示词组装

每次 LLM 调用（`prompt.ts:1464-1480`）：

```typescript
const [skills, env, instructions, modelMsgs] = yield* Effect.all([
  Effect.promise(() => SystemPrompt.skills(agent)),       // 按 agent 过滤的技能列表
  Effect.promise(() => SystemPrompt.environment(model)),  // 环境信息（工作目录、平台、日期）
  instruction.system().pipe(Effect.orDie),               // AGENTS.md, CLAUDE.md 等
  MessageV2.toModelMessagesEffect(msgs, model),          // 对话历史
])
const system = [...env, ...(skills ? [skills] : []), ...instructions]
```

### 3.2 指令加载路径（`instruction.ts:122-178`）

```typescript
const systemPaths = function* () {
  // 1. 项目级：findUp("AGENTS.md"/"CLAUDE.md", Instance.directory, Instance.worktree)
  //    从工作目录向上查找，直到 worktree 根
  // 2. 全局级：~/.claude/CLAUDE.md, config dir AGENTS.md
  // 3. 配置级：opencode.jsonc 中 instructions 数组中的 URL
}
```

**关键点**：子会话共享 `Instance.directory`，所以 `findUp` 找到完全相同的 AGENTS.md。

### 3.3 系统提示词最终组装（`llm.ts:107-114`）

```typescript
system.push([
  ...(input.agent.prompt ? [input.agent.prompt] : SystemPrompt.provider(input.model)),
  ...input.system,                              // instruction.system() 的结果
  ...(input.user.system ? [input.user.system] : []),  // promptAsync 的 system 参数
].filter(Boolean).join("\n"))
```

**三者是追加关系，不是替换。** `system` 参数只能加，不能减。

---

## 4. 内置 task vs wopal_task 逐项对比

### 4.1 创建时参数传递

| 参数 | 内置 task（`tool/task.ts:70-97`） | wopal_task（`task-launcher.ts:111-114`） |
|------|----------------------------------|----------------------------------------|
| `parentID` | ✅ `ctx.sessionID` | ✅ `input.parentSessionID` |
| `permission` | ✅ 三层 deny 规则 | ❌ **未传** |
| `title` | ✅ `description + @agent subagent` | ✅ `input.description` |

### 4.2 prompt 时参数传递

| 参数 | 内置 task（`tool/task.ts:132-146`） | wopal_task（`task-launcher.ts:143-152`） |
|------|------------------------------------|----------------------------------------|
| `model` | ✅ 父会话 model | ❌ **未传** |
| `agent` | ✅ `next.name`（已校验存在） | ✅ `input.agent`（字符串，未校验） |
| `tools` | ✅ task + todowrite + primary_tools | ⚠️ 仅 `wopal_task: false` |
| `parts` | ✅ `resolvePromptParts()` 解析 | ❌ 纯文本 `[{type:"text"}]` |
| `system` | ❌ 未传 | ❌ 未传 |

### 4.3 功能对比矩阵

| 能力 | 内置 task | wopal_task | 谁更强 |
|------|---------|-----------|-------|
| **工具裁剪** | ✅ primary_tools 可配 + task/todowrite 条件禁用 | ❌ 仅禁用 wopal_task | 内置 |
| **权限层** | ✅ create 时设 permission + prompt 时设 tools | ❌ 无 | 内置 |
| **Model 继承** | ✅ 显式传父会话 model | ❌ 用 agent 默认 | 内置 |
| **Prompt 模板** | ✅ resolvePromptParts 解析 @file/@agent | ❌ 纯文本 | 内置 |
| **双向通信** | ❌ 同步等待，一次性返回 | ✅ waiting/error/interrupt/reply/diff | wopal |
| **并发控制** | ❌ 无 | ✅ 并发槽管理 + stuck 检测 | wopal |
| **进度监控** | ❌ 无 | ✅ 消息数/时间/上下文用量通知 | wopal |
| **权限自动代理** | ❌ 子会话无 TUI 会阻塞 | ✅ 自动 once 授权 | wopal |

---

## 5. `parts` 结构化消息机制

### 5.1 Part 类型定义（`message-v2.ts`）

| 类型 | 作用 | 服务器端行为 |
|------|------|------------|
| `text` | 纯文本 | 直接使用 |
| `file` | 文件附件（`url` 为 `file://`） | 自动调用 `read` tool 读取内容，注入 synthetic text |
| `agent` | 声明使用哪个 agent | 检查权限，注入 synthetic text 提示调用 task tool |
| `subtask` | 内嵌子任务声明 | 触发内置 task tool 执行子任务 |

### 5.2 `resolvePromptParts` 模板解析（`prompt.ts:117-149`）

内置 task 不直接传纯文本，而是：

```typescript
// 输入： "请分析 @src/index.ts 的结构"
// 解析：
//   1. 正则提取 "@src/index.ts"
//   2. 检查文件是否存在 → { type: "file", url: "...", filename: "src/index.ts" }
//   3. 如果文件不存在，检查是否是 agent 名 → { type: "agent", name: "xxx" }
//   4. parts = [{ type: "text" }, { type: "file" }]
```

**效果**：子代理在启动时就"看到了"文件内容，不需要自己再 `read` 一次。

### 5.3 `file` part 的自动读取（`prompt.ts:1032-1196`）

```typescript
// 检测到 file part 后：
// 1. 调用 read tool 读取文件
// 2. 注入: "Called the Read tool with the following input: {...}"
// 3. 注入: 文件实际内容
// 4. 如果是 text/plain，还支持行范围引用 (?start=N&end=N)
```

---

## 6. 增强方案

### 6.1 方向：利用 SDK 等价参数

既然两条路径等价，`wopal_task` 可以传入与内置 task 相同的参数：

```typescript
// task-launcher.ts promptAsync body
body: {
  agent: input.agent,
  model: input.model,                        // 指定模型
  system: input.system,                      // 注入额外上下文/规则
  parts: [
    { type: "text", text: input.prompt },
    ...fileParts,                            // 自动解析 @file 引用
  ],
  tools: {
    "wopal_task": false,
    ...input.denyTools?.reduce((acc, t) => ({ ...acc, [t]: false }), {}),
  },
}
```

### 6.2 自动解析 `@file` 引用

```typescript
// wopal-task.ts 参数中增加
files: z.array(z.string()).optional().describe("Files to attach to context")

// 或在 execute 中解析 prompt 中的 @xxx 模式
const fileRefs = input.prompt.matchAll(/@(\S+)/g)
const fileParts = [...fileRefs].map(([, ref]) => {
  const filepath = path.resolve(directory, ref)
  return {
    type: "file" as const,
    url: pathToFileURL(filepath).href,
    filename: ref,
    mime: "text/plain",
  }
})
```

### 6.3 权限裁剪

```typescript
// wopal-task.ts 参数
denyTools: z.array(z.string()).optional().describe("Tools to deny in child session")

// task-launcher.ts
body: {
  tools: {
    "wopal_task": false,
    ...(input.denyTools ?? []).reduce((acc, t) => ({ ...acc, [t]: false }), {}),
  },
}
```

---

## 7. Instruction 加载的不可绕过性

### 7.1 为什么不能跳过

`runLoop()` 中硬编码（`prompt.ts:1464-1467`）：

```typescript
const instructions = yield* instruction.system().pipe(Effect.orDie)
```

**没有参数可以跳过。** `system` 参数是追加，不是替换。`PromptInput` schema 中没有 `skipInstructions` 字段。

### 7.2 三条出路

| 方案 | 可行性 | 代价 |
|------|--------|------|
| **修改 OpenCode 源码** | ✅ 可行 | 维护 fork（Ellamaka），升级时需 rebase |
| **不同 directory 启动子会话** | ⚠️ 半可行 | 子会话脱离项目目录，文件路径断裂 |
| **接受现状，优化 instruction 体积** | ✅ 可行 | 不改机制，只减少内容 |

### 7.3 方案 1 的具体修改（推荐）

在 Ellamaka fork 的 `prompt.ts` `runLoop` 中：

```typescript
// 如果是子会话，跳过 instruction 加载或加载精简版
const instructions = session.parentID 
  ? []  // 子会话不加载项目级 instruction
  : yield* instruction.system().pipe(Effect.orDie)
```

或者在 `instruction.ts` 的 `systemPaths` 中加条件，子会话只加载全局级 instruction，跳过项目级 AGENTS.md。

---

## 8. 关键源码索引

| 发现 | 文件 | 行号 |
|------|------|------|
| Session.create 参数 schema | `session/index.ts` | 685-695 |
| Session.createNext 实现 | `session/index.ts` | 375-413 |
| PromptInput schema | `session/prompt.ts` | 1697-1761 |
| prompt() 实现 | `session/prompt.ts` | 1268-1287 |
| tools → permission 转换 | `session/prompt.ts` | 1275-1282 |
| createUserMessage | `session/prompt.ts` | 910-943 |
| resolvePromptParts | `session/prompt.ts` | 117-149 |
| runLoop 系统提示词组装 | `session/prompt.ts` | 1464-1480 |
| instruction.systemPaths | `session/instruction.ts` | 122-161 |
| instruction.system | `session/instruction.ts` | 164-178 |
| LLM system prompt 组装 | `session/llm.ts` | 107-114 |
| Permission.merge | `permission/index.ts` | 293-295 |
| Permission.evaluate | `permission/evaluate.ts` | 9-14 |
| Permission.disabled | `permission/index.ts` | 299-308 |
| resolveTools | `session/llm.ts` | 397-403 |
| resolveTools (prompt) | `session/prompt.ts` | 346-514 |
| file part 自动读取 | `session/prompt.ts` | 956-1196 |
| agent part 处理 | `session/prompt.ts` | 1201-1217 |
| TaskTool 创建子会话 | `tool/task.ts` | 68-98 |
| TaskTool prompt 调用 | `tool/task.ts` | 130-146 |
| SDK session.create | `sdk/js/src/v2/gen/sdk.gen.ts` | 1585-1621 |
| SDK session.promptAsync | `sdk/js/src/v2/gen/sdk.gen.ts` | 2252-2305 |
| 服务端 create 路由 | `server/routes/session.ts` | 193-217 |
| 服务端 prompt_async 路由 | `server/routes/session.ts` | 841-875 |
| wopal_task 创建 | `wopal-plugin/src/tasks/task-launcher.ts` | 64-184 |
| wopal_task prompt | `wopal-plugin/src/tasks/task-launcher.ts` | 143-152 |

---

## 9. 斜线命令机制：三层拦截架构

### 9.1 关键发现：`/compact` 不是真正的后端命令

深入追踪后发现，OpenCode 中的"斜线命令"并非统一机制，而是**三类完全不同的路由**：

```
用户输入 "/xxx" → TUI 前端判断
  ├── TUI 前端动作（如 /compact, /editor, /unshare）
  │     → 直接调用 SDK API，不经过 LLM
  ├── 后端命令（如 /init, /review, /skill-name）
  │     → session.command() → 模板展开 → 作为文本发给 LLM
  └── 未知文本
        → session.prompt() → 作为普通文本发给 LLM
```

### 9.2 TUI 前端动作

**注册机制**（`dialog-command.tsx`）：

```typescript
export type CommandOption = {
  slash?: { name: string; aliases?: string[] }  // 斜线名
  onSelect: (dialog) => { /* 前端逻辑 */ }
}
```

`/compact` 注册（`routes/session/index.tsx:468-493`）：
```tsx
{
  title: "Compact session",
  slash: { name: "compact", aliases: ["summarize"] },
  onSelect: (dialog) => {
    // 直接调用 summarize API！不经过 session.command()
    sdk.client.session.summarize({
      sessionID: route.sessionID,
      modelID: selectedModel.modelID,
      providerID: selectedModel.providerID,
    })
    dialog.clear()
  },
}
```

**自动补全拦截**（`autocomplete.tsx:359-376, 453-458`）：
```typescript
const commands = createMemo((): AutocompleteOption[] => {
  const results: AutocompleteOption[] = [...command.slashes()]  // 收集 TUI 前端动作
  for (const serverCommand of sync.data.command) { ... }       // 收集后端命令
})

function select() {
  selected.onSelect?.()  // 直接执行前端逻辑！不发给 LLM！
}
```

### 9.3 ACP 代理的硬编码处理

**ACP 层**（`acp/agent.ts:1448-1533`）也做了类似的客户端拦截：

```typescript
const cmd = (() => {
  const text = parts.filter(p => p.type === "text").map(p => p.text).join("").trim()
  if (!text.startsWith("/")) return
  const [name, ...rest] = text.slice(1).split(/\s+/)
  return { name, args: rest.join(" ").trim() }
})()

if (!cmd) {
  // 普通文本 → session.prompt()
  return this.sdk.session.prompt({ sessionID, ...parts })
}

const command = await this.config.sdk.command.list(...)
if (command) {
  // 后端命令 → session.command()
  return this.sdk.session.command({ sessionID, command: command.name, ... })
}

switch (cmd.name) {
  case "compact":
    // 硬编码的 /compact → session.summarize()！
    await this.config.sdk.session.summarize({ sessionID, providerID, modelID })
    break
}
```

### 9.4 后端命令（模板展开型）

**流程**（`prompt.ts:1538-1652`）：
```
session.command() → Command.Service.get() → 模板展开 → prompt() → LLM
```

**命令来源**（`command/index.ts:76-190`）：

| 来源 | 示例 | 特性 |
|------|------|------|
| 内置 | `/init`, `/review` | 模板硬编码 |
| opencode.jsonc | 用户自定义 | 模板配置 |
| MCP prompts | MCP server 提供的 prompts | 动态获取 |
| Skills | 每个技能名自动注册为同名命令 | 技能内容即模板 |

**子会话可见性**：`Command.Service` 是 `InstanceState`，按 `Instance.directory` 缓存。子会话共享同一目录，**命令列表与主会话完全一致**。

### 9.5 LLM 上下文中的命令可见性

OpenCode 的上下文注入机制：

| 注入内容 | 来源 | 位置 |
|---------|------|------|
| 工具列表 | `ToolRegistry.tools()` | LLM function calling schema |
| 技能列表 | `SystemPrompt.skills()` | 系统提示词 |
| Agent 列表 | `describeTask()` 注入到 Task tool description | Task tool 描述文本 |
| 环境信息 | `SystemPrompt.environment()` | 系统提示词 |
| Instruction | `instruction.system()` | AGENTS.md 等 |

**⚠️ 不注入的内容**：
- 用户自定义命令列表
- MCP prompts 列表
- 内置命令（`/init`、`/review`）
- 技能命令（技能名注册的命令）

**本质区别**：
```
工具（Tool）     → LLM 主动调用 → 必须注入 schema（function calling）
命令（Command） → 用户触发 → 模板展开为纯文本 → 作为用户消息发送
TUI 动作        → 客户端拦截 → 直接调 SDK API → 不经过 LLM
```

---

## 10. 会话压缩机制：`session.summarize()` 源码追踪

### 10.1 真正的压缩路径

`/compact` 的实际后端路径是 `POST /session/{sessionID}/summarize`：

**服务端路由**（`server/routes/session.ts:506-564`）：
```typescript
.post("/:sessionID/summarize", async (c) => {
  const sessionID = c.req.valid("param").sessionID
  const body = c.req.valid("json")  // { providerID, modelID, auto?: false }
  const session = await Session.get(sessionID)
  await SessionRevert.cleanup(session)
  const msgs = await Session.messages({ sessionID })
  
  // 找最后一条 user 消息确定 agent
  let currentAgent = await Agent.defaultAgent()
  for (let i = msgs.length - 1; i >= 0; i--) {
    if (msgs[i].info.role === "user") {
      currentAgent = msgs[i].info.agent || await Agent.defaultAgent()
      break
    }
  }
  
  await SessionCompaction.create({
    sessionID,
    agent: currentAgent,
    model: { providerID: body.providerID, modelID: body.modelID },
    auto: body.auto,
  })
  await SessionPrompt.loop({ sessionID })
  return c.json(true)
})
```

**SDK v2**（`sdk/js/src/v2/gen/sdk.gen.ts:2041-2077`）：
```typescript
v2Client.session.summarize({
  sessionID: childSessionID,
  providerID: "openai",
  modelID: "gpt-4o",
})
```

**SDK types**（`types.gen.ts:3558`）：
```typescript
export type SessionSummarizeData = {
  body?: { providerID?: string; modelID?: string; auto?: boolean }
  path: { sessionID: string }
  url: "/session/{sessionID}/summarize"
}
```

### 10.2 Compaction 完整流程

**Phase 1: `create()`**（`compaction.ts:346-369`）
```typescript
// 创建含 compaction 类型的用户消息
const msg = await session.updateMessage({
  id: MessageID.ascending(),
  role: "user",
  model: input.model,
  sessionID: input.sessionID,
  agent: input.agent,
})
await session.updatePart({
  id: PartID.ascending(),
  messageID: msg.id,
  sessionID: msg.sessionID,
  type: "compaction",   // ← 关键标记
  auto: input.auto,
  overflow: input.overflow,
})
```

**Phase 2: `loop()` 检测**（`prompt.ts:1321-1373`）
```typescript
// runLoop 中检测 compaction part
const task = msg.parts.filter(part => part.type === "compaction" || part.type === "subtask")

if (task?.type === "compaction") {
  const result = await compaction.process({
    messages: msgs,
    parentID: lastUser.id,
    sessionID,
    auto: task.auto,
    overflow: task.overflow,
  })
  if (result === "stop") break
  continue  // 处理完后继续 loop
}
```

**Phase 3: `process()`**（`compaction.ts:141-343`）
```
1. 用 "compaction" agent（或用户消息的 model）
2. 将完整对话历史发给 LLM，prompt: "Provide a detailed prompt for continuing our conversation..."
3. LLM 生成结构化摘要（Goal/Instructions/Discoveries/Accomplished/Relevant files）
4. 将旧消息标记为 compacted（`part.state.time.compacted = Date.now()`）
5. 自动继续：注入 "Continue if you have next steps..." 触发后续对话
```

**Phase 4: 上下文清理**（`message-v2.ts:725-726`）
```typescript
if (part.state.time.compacted) {
  const outputText = "[Old tool result content cleared]"  // 压缩后不再显示
  const attachments = []                                   // 媒体也被清除
}
```

### 10.3 Compaction 的特殊 prompt

OpenCode 使用的压缩提示词（`compaction.ts:189-217`）：
```
Provide a detailed prompt for continuing our conversation above.
Focus on information that would be helpful for continuing the conversation,
including what we did, what we're doing, which files we're working on,
and what we're going to do next.
The summary that you construct will be used so that another agent can
read it and continue the work.
Do not call any tools. Respond only with the summary text.
Respond in the same language as the user's messages in the conversation.
```

### 10.4 关键设计：压缩后自动继续

`process()` 中（`compaction.ts:283-338`）：
- 压缩成功后，自动创建新的用户消息
- 注入提示：`"Continue if you have next steps, or stop and ask for clarification if you are unsure how to proceed."`
- 子会话继续运行，无需主 agent 额外发送消息

---

## 11. 主 agent 向子会话发送压缩的可行方案

### 11.1 为什么不能用 `/compact` 文本

| 场景 | 实际结果 |
|------|---------|
| 用户在 TUI 输入 `/compact` 并选中回车 | TUI 拦截 → 调用 `summarize()` → 不发给 LLM |
| 主 agent 输出文本 `/compact` | 只是普通文本，子会话收到后**不会触发压缩** |
| `wopal_task_reply` 发送 `/compact` 文本 | 子会话收到文本，**不会触发压缩** |
| `wopal_task_reply` 调用 `session.command("compact")` | 如果后端没注册此命令 → 报错 `Command not found` |

**结论**：唯一可靠的路径是直接调用 `session.summarize()` API。

### 11.2 方案：在 `wopal_task_reply` 中增加 `compact` 参数

**依赖验证**：

| 依赖 | 状态 | 位置 |
|------|------|------|
| `v2Client.session.summarize()` | ✅ SDK v2 已生成 | `sdk/js/src/v2/gen/sdk.gen.ts:2041` |
| `getTaskModelInfo()` | ✅ 已存在 | `tools/output-helpers.ts:27-56` |
| `v2Client` 使用 internal fetch | ✅ 正确路由到 Hono 服务器 | `index.ts:96-103` |
| 子会话有 model 信息 | ✅ 从第一条 assistant 消息获取 | `message.info.providerID/modelID` |

**实现代码**（`wopal-task-reply.ts`）：

```typescript
// 新增参数
compact: tool.schema.boolean().optional().default(false)
  .describe("Compact child session context before sending message"),

// execute 中逻辑（在现有 reply 逻辑之前）
if (args.compact) {
  const modelInfo = await getTaskModelInfo(manager.getClient(), task.sessionID!)
  if (!modelInfo) return "Error: Cannot compact — no model info for child session"

  const v2Client = manager.getV2Client()
  if (typeof v2Client?.session?.summarize !== "function") {
    return "Error: session.summarize is unavailable"
  }

  await v2Client.session.summarize({
    sessionID: task.sessionID,
    providerID: modelInfo.providerID,
    modelID: modelInfo.modelID,
  })

  // compact 后可选发送消息
  if (message.trim()) {
    if (typeof clientAny?.session?.promptAsync !== "function") {
      return "Session compacted but cannot send follow-up message: promptAsync unavailable"
    }
    await clientAny.session.promptAsync({
      path: { id: task.sessionID },
      body: { parts: [{ type: "text", text: message }] },
    })
    return `Session compacted. Follow-up message sent.`
  }

  return `Session compacted. Context cleared. The child session will auto-continue with a summary.`
}
```

**用户调用**：
```
wopal_task_reply(task_id="xxx", compact=true)
wopal_task_reply(task_id="xxx", compact=true, message="继续推进")
```

### 11.3 不需要修改 OpenCode 源码

整个方案完全通过 SDK API 实现，不需要修改 Ellamaka fork。

---

## 12. 关键源码索引（新增）

| 发现 | 文件 | 行号 |
|------|------|------|
| `/compact` TUI 注册 | `cli/cmd/tui/routes/session/index.tsx` | 468-493 |
| `/compact` ACP 拦截 | `acp/agent.ts` | 1521-1533 |
| TUI 命令补全 | `cli/cmd/tui/component/prompt/autocomplete.tsx` | 359-386 |
| TUI 命令发送 | `cli/cmd/tui/component/prompt/index.tsx` | 663-692 |
| `dialog-command.tsx` 注册机制 | `cli/cmd/tui/component/dialog-command.tsx` | 全文件 |
| `session.summarize` 路由 | `server/routes/session.ts` | 506-564 |
| `SessionCompaction.create()` | `session/compaction.ts` | 346-369 |
| `SessionCompaction.process()` | `session/compaction.ts` | 141-343 |
| loop 检测 compaction part | `session/prompt.ts` | 1356-1373 |
| compacted 消息清理 | `session/message-v2.ts` | 725-726 |
| SDK `session.summarize()` | `sdk/js/src/v2/gen/sdk.gen.ts` | 2041-2077 |
| `getTaskModelInfo()` | `wopal-plugin/src/tools/output-helpers.ts` | 27-56 |

---

## 13. 结论

1. **SDK 与内部路径等价**：`client.session.create()` + `client.session.promptAsync()` 与内置 `sessions.create()` + `ops.prompt()` 在服务器端走完全相同的代码路径。所有 `PromptInput` 参数都可以使用。

2. **wopal_task 当前利用不足**：只传了 `agent`、纯文本 `parts`、单一 `tools` 限制。未利用 `model`、`system`、`file parts`、`permission` 等能力。

3. **权限是合并覆盖**：session 级规则排在数组后面，`findLast` 优先匹配 → session 配置覆盖 agent 默认。但 `create` 和 `prompt` 中的权限是覆盖关系而非追加，需统一放在一处。

4. **instruction 无法通过参数跳过**：`runLoop` 中硬编码加载，`system` 参数只追加不替换。要跳过需要修改 OpenCode 源码（Ellamaka fork）。

5. **parts 是结构化消息**：支持 `text`/`file`/`agent`/`subtask` 四种类型。`file` part 会在服务器端自动读取文件内容注入上下文，避免子代理额外 `read` 调用。

6. **斜线命令不是统一机制**：存在三层路由——TUI 前端动作（如 `/compact` 直接调 SDK API）、后端命令（如 `/init` 模板展开）、普通文本。LLM 无法直接触发 TUI 前端动作。

7. **`/compact` 是 TUI/ACP 前端拦截**：不经过 `session.command()` 的命令模板展开流程，而是直接调用 `session.summarize()` API。主 agent 向子会话发 `/compact` 文本不会触发压缩。

8. **子会话压缩的唯一路径**：直接调用 `v2Client.session.summarize({ sessionID, providerID, modelID })`。Plugin 已持有 v2Client 和 `getTaskModelInfo()`，完全可行，不需要修改 OpenCode 源码。

9. **增强方案**：在 `wopal_task_reply` 中增加 `compact` 参数，触发 `session.summarize()` 压缩子会话上下文。压缩成功后 OpenCode 会自动注入继续提示词，子会话无需手动唤醒。

# 后台自动审查进化系统设计研究

> 基于 Hermes Agent (`labs/ref-repos/hermes-agent/`) 与 OpenCode (`labs/ref-repos/opencode/`)
> 源码级分析，提出在 Ellamaka fork 中实现后台自动记忆蒸馏与 Skill 进化系统的设计方案。

---

## 1. 问题定义

### 1.1 当前痛点

记忆系统的蒸馏流程依赖人工触发（`/memo distill`），对话结束后经验随上下文流失。同时，
记忆到 Skill 的链路完全断裂——没有自动化的 "经验发现 → 技能创建" 通路。

### 1.2 目标

借鉴 Hermes Agent 的后台审查机制，在对话结束后自动启动独立审查流程，实现：

1. **自动记忆蒸馏**：从对话中提取偏好、教训、经验，写入 LanceDB
2. **自动 Skill 进化**：识别可复用方法论，创建/更新 Skill
3. **零用户干扰**：审查过程完全后台，不阻塞主对话

---

## 2. Hermes Agent 后台审查机制分析

### 2.1 核心源码路径

| 文件 | 行号 | 功能 |
|------|------|------|
| `run_agent.py` | 2448-2547 | `_spawn_background_review()` — 孵化后台审查 |
| `run_agent.py` | 8590-8605 | 记忆审查触发（turn-based counter ≥ 10） |
| `run_agent.py` | 11586-11614 | 技能审查触发 + dispatch |
| `tools/memory_tool.py` | 105-299 | `MemoryStore` — 共享存储 + 文件锁 |

### 2.2 工作机制

```
User sends message → Main agent processes → Response delivered
                                                          │
                                    ┌─────────────────────┴─────────────────────┐
                                    │ (turn counter ≥ interval?)                │
                                    ▼                                           ▼
                         Memory review fires?                        Skill review fires?
                         (_turns_since_memory ≥ 10)                 (_iters_since_skill ≥ 10)
                                    │                                           │
                                    └─────────────────┬─────────────────────────┘
                                                      │
                                    ┌─────────────────▼─────────────────────────┐
                                    │   _spawn_background_review() (daemon)     │
                                    │                                           │
                                    │   1. AIAgent(quiet, max_iterations=8)     │
                                    │   2. Share _memory_store (same object)     │
                                    │   3. Set nudge intervals to 0 (no loops)  │
                                    │   4. Redirect stdout/stderr to /dev/null   │
                                    │   5. run_conversation(prompt, messages)    │
                                    │   6. Scan for save actions                 │
                                    │   7. Summarize + notify user               │
                                    │   8. Close review agent                    │
                                    └───────────────────────────────────────────┘
```

### 2.3 三个关键审查 Prompt

**MEMORY_REVIEW_PROMPT:**
> "Review the conversation above. Has the user revealed persona, desires, preferences?
> Has the user expressed expectations about behavior or work style? If something stands
> out, save using the memory tool."

**SKILL_REVIEW_PROMPT:**
> "Review the conversation above. Was a non-trivial approach used requiring trial and
> error, or changing course due to experiential findings? If a relevant skill exists,
> update it. Otherwise create a new one if reusable."

**COMBINED_REVIEW_PROMPT:**
> "Review the conversation above for both memory and skills. Only act if there's
> something genuinely worth saving. If nothing stands out, say 'Nothing to save.' and stop."

### 2.4 核心设计特征

| 特征 | 做法 | 意图 |
|------|------|------|
| **内聚隔离** | Daemon thread in same process | 共享内存存储，不阻塞主 loop |
| **完整 Agent Loop** | 完整 `AIAgent` 实例 | 能自主调用工具、多轮交互 |
| **共享存储** | `review_agent._memory_store = self._memory_store` | 零序列化，直接引用同一对象 |
| **预算控制** | `max_iterations=8`（主 agent 约 90） | 强制简洁，防止无限循环 |
| **静默模式** | `quiet_mode=True` + stdout redirect to `/dev/null` | 用户完全无感知 |
| **防递归** | `_memory_nudge_interval = 0` | 审查 agent 不再 spawn 子审查 |
| **结果追溯** | 扫描 `review_agent._session_messages` 中的 tool return | 自动构建摘要 |
| **最佳努力** | try/except 包裹，失败静默忽略 | 不因为审查失败影响主对话 |

### 2.5 关键约束

- **同一进程内**：审查 agent 与主 agent 在同一 Python 进程
- **不是单独 LLM 调用**：是完整的 AIAgent 实例，有自己的 conversation loop
- **不是轻量摘要**：能自主判断、试错、创建/更新 skill、写入记忆、修复文件
- **共享上下文**：通过 `messages_snapshot` 传入完整对话历史
- **文件锁保护**：MemoryStore 使用 `fcntl.flock` 处理并发写入

---

## 3. 为什么 OpenCode 子会话方案不够

### 3.1 不可行的方案逐一排除

| 方案 | 问题 |
|------|------|
| **SSE 订阅 `session.idle`** | TUI 模式下默认不启 HTTP 端点，SSE 不可达 |
| **HTTP `prompt_async` 创建子会话** | `prompt_async` 路由存在但主流程阻塞等待，不满足 fire-and-forget |
| **Plugin 内 `void async` fire-and-forget** | 只能串行 LLM 调用，没有独立 agent loop，无法完成 Skill 进化 |
| **Plugin spawn 子进程** | 跨进程通信笨重，API keys/路径参数传递，违背内聚原则 |

### 3.2 根本原因

Hermes 的审查 agent 是**完整的、有多轮 tool-call 能力的独立 agent**，
而插件层只能做到单次 LLM 调用（蒸馏 prompt → LLM → json → write）。
但 Skill 进化需要多步骤 agent loop 迭代：

```
审查 prompt
  ↓
Round 1: "值得创建 skill，先查现有 skill..." → skill_manage query
  ↓
Round 2: "没有现成的，创建新 skill" → skill_manage create
  ↓
Round 3: "SKILL.md 需要描述优化" → write file
  ↓
Round 4: "记录相关经验到记忆" → memory_manage add
  ↓
完成
```

单一 LLM 调用无法完成这个过程。需要**完整的 agent loop**（LLM → tool call → response → next loop）。

---

## 4. 核心方案：修改 Ellamaka 实现后台审查服务

既然 fork 了 OpenCode（`projects/ellamaka/`），可以在源码层实现与 Hermes 等价的后台审查机制。

### 4.1 架构总览

```
┌─ Ellamaka 主进程 ─────────────────────────────────────────────┐
│                                                               │
│  Agent Loop                    Background Reviewer Service    │
│  ┌─────────┐                   ┌────────────────────────┐     │
│  │prompt() │  LLM loop         │ spawn(sessionID)       │     │
│  │         │────┐               │                        │     │
│  └─────────┘    │               │ 1. createSession()     │     │
│                 ▼               │ 2. pre-populate msgs   │     │
│  正常响应用户   │               │ 3. processor.create()   │     │
│                 │               │ 4. processor.process()  │     │
│  ─ ─ ─ ─ ─ ─ ─│─ ─ ─ ─ ─ ─ ─  │ 5. loop ≤ N rounds      │     │
│                 │               │ 6. scan tool messages   │     │
│  Effect runtime │               │ 7. publish result event │     │
│                 │               │ 8. cleanup session       │     │
│  ─ ─ ─ ─ ─ ─ ─│─ ─ ─ ─ ─ ─ ─  └────────────────────────┘     │
│                 │                      │                      │
│  forkIn ←───────┴── Effect fiber ──▶ 完全并发的 fiber           │
│  (同一个 Effect scope，完全独立的 fiber，不阻塞主流程)             │
│                                                               │
│  共享基础设施:                                                 │
│  - SessionProcessor (同一个实例)                                │
│  - ToolRegistry (自动包含 plugin 注册的工具)                     │
│  - LLM Provider (可独立指定 model)                              │
│  - Event Bus (发布 review.complete 事件)                        │
└───────────────────────────────────────────────────────────────┘
```

### 4.2 Hermes 与 Ellamaka 的精确对应

| Hermes Agent | Ellamaka (OpenCode fork) | 对应意图 |
|---|---|---|
| `AIAgent(max_iterations=8)` | `SessionProcessor.create()` + `maxSteps` | 完整 agent loop + 预算 |
| `Thread(target=review, daemon=True)` | `Effect.forkIn(scope)` | 并发纤维，不阻塞主流程 |
| `review._memory_store = self._memory_store` | 同一 ToolRegistry → memory_manage/skill_manage 共享存储 | 零成本共享存储 |
| `conversation_history=messages_snapshot` | 克隆消息到 review session + 追加审查 prompt | 共享对话上下文 |
| `quiet_mode=True` + `/dev/null` | 静默 session，不 publish busy status / 不推 TUI | 用户无感知 |
| 扫描 `_session_messages` → 摘要 | 读取 review session 最后消息 | 可追溯的审查结果 |
| try/except → 静默忽略 | Effect.catchAll(Effect.succeed) | 最佳努力，不影响主流程 |
| `_nudge_interval = 0` 防递归 | 审查 session 禁用 session.idle → 不触发审查 | 防止无限递归 |

### 4.3 核心服务设计

**新增文件：`packages/opencode/src/session/background-reviewer.ts`**

```
BackgroundReviewer.Service
  ├── spawn(sessionID, prompt, options)  ← 触发后台审查
  ├── abort(reviewID)                     ← 取消审查
  ├── state(reviewID)                     ← 状态查询
  └── list(active)                        ← 活跃审查列表
```

**Spawn 流程:**

```
1. 创建 review session
   - Session.Service.create({ parentID: sessionID })
   - silent 标记 → 跳过 global status event

2. 预加载对话消息
   - 读取主 session 的消息 → 按顺序写入 review session
   - 最后追加审查 prompt 作为 user message

3. 启动 processor
   - SessionProcessor.create(session, model, options)
   - maxSteps = 8（同 Hermes max_iterations）
   - 传入 custom system prompt（审查指令）

4. Effect.forkIn(scope)
   - 在同一 Effect runtime 中并发执行
   - 不阻塞主 fiber
   - 审查 session 有独立 runLoop

5. 完成后发布 BusEvent
   - review.complete → plugin 可监听
   - payload 包含 sessionID + 简要结果

6. 自动清理 review session
```

### 4.4 触发时机

**修改位置：`packages/opencode/src/session/status.ts`**

当 session status 变为 `idle` 时：
- 当前行为：publish `session.idle` event → plugin 收到
- 新增行为 → 同时触发 BackgroundReviewer.spawn()（如果满足条件）

具体条件（同 Hermes 逻辑）：
1. 对话轮数 ≥ 阈值（可配置，默认 3）
2. 距上次审查 ≥ 冷却时间（可配置，默认 30 分钟）
3. 非子会话（跳过后台审查触发的子 session）

### 4.5 预算控制

```typescript
interface ReviewOptions {
  maxSteps?: number          // agent loop 最大轮数，默认 8
  model?: { providerID, modelID }  // 可选指定不同模型
  systemPrompt?: string      // 审查指令
  cooldownMs?: number        // 冷却时间，默认 30 分钟
}
```

### 4.6 审查 Prompt 设计

复用 Hermes 的 prompt 策略，分为 memory review 和 skill review。

```markdown
你是独立的后台审查 Agent。你的任务是分析以下对话并执行操作：

**Memory**: 用户是否透露了偏好、工作要求、行为期望？如果有值得记住的，
调用 memory_manage 工具保存。

**Skills**: 是否使用了非平凡的方法完成任务，包含试错过程或经验发现？
如果有，调用 skill_manage 工具创建或更新 skill。

规则：
- 没有值得保存的直接回复 "Nothing to save."
- 不要询问用户
- 不要修改已有记忆

以下是待审查的对话：
{{clipped_messages}}
```

### 4.7 结果追溯

审查完成后，插件通过 BusEvent `review.complete` 接收通知，可：
1. 读取 review session 最后消息，获取审查结果
2. 在父 session 推送摘要通知（"💾 2条记忆写入，1个skill草稿创建"）
3. 日志记录用于调试

---

## 5. 需要修改的源码文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/session/background-reviewer.ts` | **新增** | 核心服务实现 |
| `src/session/status.ts` | **修改** | idle 时触发 review spawn |
| `src/session/prompt.ts` | **修改** | 支持 maxSteps + 静默模式 |
| `src/session/session.ts` | **修改** | Event 定义增加 `review.complete` |
| `src/bus/bus-event.ts` | **修改** | 定义 review 相关事件 |
| `src/session/schema.ts` | **修改** | Session 字段扩展（is_review / silent 标记） |

---

## 6. 关键设计决策

### 6.1 为什么用 Effect.forkIn(scope) 而不是 spawn 子进程

- **同一进程内**，共享 ToolRegistry — plugin 注册的 tool 自动可见
- **零序列化成本** — 不需要跨进程传递 API keys、数据库路径
- **统一生命周期管理** — Scope 释放 → fiber 中断，自动清理
- **与 Hermes 的 daemon thread 模型等价** — 内聚隔离，而非跨进程隔离

### 6.2 为什么不在插件层做

| | 插件层 | 核心层 (Ellamaka) |
|---|---|---|
| 进程独立性 | 插件已是独立进程 ✓ | 主进程内 ✓ |
| Agent loop | 只能单次 LLM 调用 ✗ | 完整 loop ✓ |
| Skill 进化 | 无法多轮工具执行 ✗ | 能自主 tool call ✓ |
| 存储共享 | 同一 LanceDB ✓ | 同一数据库 ✓ |
| 架构耦合 | 依赖 plugin hook 机制 | 纯核心实现 |
| 触发可靠性 | 依赖 event router | 直接在 idle 内触发 |

### 6.3 与手动蒸馏的关系

| | 手动蒸馏 (`/memo distill`) | 后台审查 (auto-review) |
|---|---|---|
| 触发 | 用户主动 | session.idle 自动 |
| 流程 | preview → 确认 → confirm | 自动确认写入 |
| 去重 | 向量 + LLM 四路判定 | 复用同一 dedup |
| Skill 链路 | 无 | 审查 agent 自主调用 skill_manage |
| 冲突 | 不会（LanceDB 去重） | 同上 |

后台审查是**自动化的补充**，不替代手动蒸馏。

---

## 7. 风险评估

| 风险 | 影响 | 缓解 |
|------|------|------|
| 审查 agent 无限循环 | 消耗 API 调用 | maxSteps=8 硬性限制 |
| 多个 idle 连续触发 | 并发审查 | 冷却机制 + 会话去重 |
| review session 未清理 | 数据库膨胀 | 自动清理已完成 session |
| 审查 prompt 误判 | 写入无价值记忆 | 去重 + 低 importance |
| forkIn fiber 与主 fiber 竞争 LLM 调用 | API 速率限制 | Effect.forkIn 并发控制 |

---

## 8. 后续工作

1. **实现 BackgroundReviewer 服务**: 在 `projects/ellamaka/packages/opencode/src/session/background-reviewer.ts` 中实现
2. **审查 Prompt 优化**: 基于 distill.md 和 Hermes prompt 调优
3. **Memory → Skill 判断逻辑**: 审查 agent 如何判断 "值得转 skill" 的详细标准
4. **效果验证**: 在真实对话中观察自动蒸馏质量，调整 prompt 和阈值
5. **Skill 草稿审查流程**: 后台自动创建的 skill 如何进入 INBOX 等待人工审批

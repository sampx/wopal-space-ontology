---
name: agents-collab
description: |
  Wopal 与子 Agent（fae、rook 等）交互的基础规范。⚠️ MUST load before ANY delegation — 涵盖委派工具 API、任务生命周期、通知处理、状态检查与恢复。

  🔴 Trigger: "委派"、"delegate"、"让 fae 执行"、"fae 任务"、"rook 审查"、"检查状态"、"取消任务"、"abort 任务"、"agent 协作"、或任何意图将任务交给子 Agent 执行的场景。

  🔴 严禁不加载本技能就直接委派，这是严重失职。

  注意：本技能不包含与特定工作流（如 dev-flow）绑定的 prompt 模板 — 那些由对应工作流技能提供。
---

# agents-collab — 子 Agent 交互基础

本技能定义**如何**与子 Agent 进行工具级交互。至于**何时**委派、prompt 中应包含哪些工作流特定指令（如 Plan 路径、Done checkbox），由上层工作流技能（如 dev-flow）决定。

---

## 工具优先级

必须优先用 `wopal_task` 委派任务，只有当 `wopal_task` 不可用时才用内置 `task` 工具。
`wopal_task` 提供：双向通信、进度监控、非阻塞执行。用 `task` = 放弃以上能力 = 降级执行。

---

## Prompt 格式

委派 prompt 必须精准完整，确保子 Agent 一次就能准确完成任务。标准格式：

```
你好 <agent>, 我是 wopal, 现在由于 <原因>, 请你执行以下任务:

Task: <任务描述>
Goal: <目标描述>

<精准上下文：绝对路径、文件:行号、当前代码、改动位置、不改动的边界>
```

**必须包含的位置信息**：
- 有 Plan 时：给出 Plan 文件绝对路径
- 涉及 worktree（如 `.wopal/`）时：明确指出 worktree 根路径，提醒不要改错位置

**核心原则**：上下文精准完整，一次给全，减少返工。

---

## 委派工具

### wopal_task — 启动任务

```typescript
wopal_task({
  description: "3-5词",
  prompt: "<按上方 Prompt 格式编写>",
  agent: "fae"       // 或 "rook"、"general" 等，默认 "general"
})
// 返回 task_id，用于后续监控和交互
```

- 异步非阻塞，主 session 不等待，可同时启动多个任务
- 并发上限：最多 3 个任务并行，超出自动排队
- TTL：30min 无交互自动清理

### wopal_task_output — 检查状态与输出

```typescript
wopal_task_output({ task_id })                              // 概要状态
wopal_task_output({ task_id, section: "text" })             // 文本输出
wopal_task_output({ task_id, section: "tools" })            // 工具调用记录
wopal_task_output({ task_id, section: "reasoning" })        // 思考过程
wopal_task_output({ task_id, section: "text", last_n: 3 })  // 只看最近 3 条
```

### wopal_task_reply — 通信/恢复/重定向

向 idle/waiting/error 任务发送消息，恢复执行或纠正方向。子 Agent **会被唤醒**。

```typescript
wopal_task_reply({ task_id, message: "继续完善测试覆盖" })
wopal_task_reply({ task_id, message: "改为...", interrupt: true })  // abort 当前执行 + 注入消息
```

| 适用状态 | 行为 |
|---------|------|
| `waiting` | 发送消息，恢复执行 |
| `idle`（running + idleNotified）| 清除 idle 标记，发送消息，恢复执行 |
| `error` | 发送消息，重新执行 |
| `running`（活跃）| 必须用 `interrupt=true`，否则消息排队 |

**禁止**：`wopal_task_reply({ message: "任务完成" })` — 子 Agent 被唤醒继续运行，形成无意义循环。IDLE 本身就是"完成信号"，验收通过后用 `wopal_task_finish` 终结。

### wopal_task_abort — 停止活跃运行任务

纯停止，不发送消息，不唤醒子 Agent。后续可用 `finish` 终结或 `reply` 恢复。

```typescript
wopal_task_abort({ task_id })
```

### wopal_task_finish — 终结任务

终结 pending/idle/error/waiting 任务并删除子会话。子 Agent **不会被唤醒**。运行中任务需先 `abort` 或 `reply(interrupt=true)`。

```typescript
wopal_task_finish({ task_id })
```

---

## 任务生命周期

### 状态模型

```
pending → running → error
              ↓
           waiting
              ↓
           running (after reply)
```

显示状态：`status=running` + `idleNotified=false` 为"活跃"，`idleNotified=true` 为"idle 等待判断"。

- `idle` 不是独立存储状态，是 running + idleNotified 的 phase
- `finish` 是终结动作（删除任务），不是状态

### 状态与行动

| 存储状态 | 含义 | Wopal 行动 |
|---------|------|-----------|
| `pending` | 排队中（并发槽位满）| `finish` 清理（如不再需要）|
| `running`（活跃）| 执行中 | 等待通知或 `output` 检查进度 |
| `idle`（running + idleNotified）| Session idle，等待判断 | 验收 → `finish` 或 `reply` 返工 |
| `waiting` | 子 Agent 在提问 | `reply` 回答 |
| `error` | 会话级异常 | `output` 查日志 → `reply` 引导修复 或 `finish` 清理 |

---

## 通知驱动机制

任务状态变更通过系统通知 `[WOPAL TASK *]` 告知 Wopal。**不要轮询，等待通知。**

| 通知 | 触发条件 | 处理流程 |
|------|---------|---------|
| `[WOPAL TASK PROGRESS]` | 定期心跳 | 了解进度即可，无需行动 |
| `[WOPAL TASK IDLE]` | 子 Agent session idle | 见下方 IDLE 决策树 |
| `[WOPAL TASK WAITING]` | 子 Agent 使用 question tool | `reply` 回答 |
| `[WOPAL TASK ERROR]` | 会话级错误 | `output` 查日志 → `reply` 引导修复 或 `finish` 清理 |
| `[WOPAL TASK STUCK]` | no_activity 或 loop_detected | `output(section="reasoning")` 检查 → 死循环则 `abort`；正常推理则继续等待 |

`ERROR` 仅由会话级异常触发（session.crash、启动失败、promptAsync 失败）。bash 命令报错不会触发。`reply` 无法更换 agent 类型——需要换 agent 只能创建新 task。

---

## IDLE 任务处理决策树

```
IDLE 通知到达
    ↓
① wopal_task_output(section="text") 查看输出
    ↓
② 验收判定
    ├─ 通过、无后续需要 → wopal_task_finish 释放资源
    │                       ❌ 禁止什么都不做等 TTL（僵尸 task 占并发槽位）
    ├─ 通过、后续可能复用 → 保留（如 rook PASS 后可能需再审）
    ├─ 不通过 → wopal_task_reply 返工（⚠️ 上下文 >50% 时见下方规则）
    └─ 子 Agent 提问 → wopal_task_reply 回答
```

---

## 返工与复用策略

### 主控职责

委派规范、复盘结论、何时复用/换 task 的判断由 Wopal 负责。fae/rook 不负责总结委派经验。收到审查结论后 Wopal 必须主动推进下一步，不要停等用户重复授权。

### 复用优先级

只要 task **还活着**、scope **未实质变化**、上下文 **仍健康**，优先 `reply` 复用：

| 场景 | 首选 | 不推荐 |
|------|------|--------|
| fae 需小幅返工 | `reply` 续做 | 新开 fae task |
| rook REVISE/BLOCK，修完复审 | `reply` 续审原 rook | 新开 rook task |
| 补充信息/继续执行 | `reply` | 终结后重建 |

### 何时停止复用

满足任一条件时，应新开 task 或由 Wopal 收尾：

1. 上下文 >50%（硬阈值）
2. 已发生一轮返工循环，且上下文 45%+
3. 任务 scope 实质变化（如从代码修复变成规范编写）
4. 子 Agent 明显跑偏、循环、质量持续下降

经验法则：运行中且健康 → 不打断；idle 后质量不达标但上下文偏高 → 不硬 reply 做第二轮。

---

## 子会话上下文压缩

收到 `[WOPAL TASK PROGRESS]` 时检查上下文占用：

| 占用 | 建议 |
|------|------|
| < 45% | 无需关注 |
| 45-55% | 评估剩余工作量 |
| ≥ 55% | 建议压缩 |
| ≥ 75% | 紧急压缩 |

压缩前确认：无未提交变更、无阻塞依赖、非 stuck 状态。

**主会话**：`context_manage(action="compact")`，压缩后 Plugin 自动发送恢复指令。

**子会话**：`context_manage(action="compact", session_id="wopal-task-xxx")`，压缩后 Plugin 发送 `[WOPAL TASK COMPACTED]` 通知，Wopal 用 `reply` 发送精准恢复指令。

---

## 并行委派中的产物交叉

多 Agent 并行时，`output` 返回的文件列表可能含其他 Agent 的工作成果。只关注当前任务的预期产出，通过 `git status` 在对应项目目录检查。不要误判为异常或删除其他 Agent 的文件。

---

## 禁止与限制

| 禁止 | 原因 |
|------|------|
| 不加载本技能就委派 | 缺乏机制指引，必然出错 |
| 频繁轮询 `output` | 浪费上下文，等待通知即可 |
| 嵌套 wopal_task | 子 Agent 已禁用 |
| 同一 task 反复 reply 返工（上下文 >50%） | 高上下文下返工质量下降 |
| `reply("任务完成")` | 子 Agent 被唤醒继续运行，无意义循环 |

| 限制 | 应对 |
|------|------|
| 并发最大 3 | 超出自动排队 |
| TTL 30min | 通知后未处理则自动清理 |

---

## 故障排查

详见 `references/troubleshooting.md`

# Codex with ChatGPT — Session-based Expert Collaboration Adapter

> **Status**: Active
> **Updated**: 2026-10-23

## 1. Positioning

`codex-with-chatgpt`（C2C）不是开发流程、Plan 状态机或 review 状态机。

它是 **Codex 与 ChatGPT 远程专家 Agent 之间的 Session / 交互适配层**。

Codex 在用户电脑上运行，拥有当前工作的 controller 职责；ChatGPT 通过
WopalSpace-Bot 接入同一个 workspace，可以在请求权限与空间技能允许的范围内直接读取、
分析、设计、写文档、修改代码、运行命令/测试、调试和评审。

ChatGPT 不再被固定为 planner / reviewer。它可以承担：

- 技术咨询和问题分析；
- 架构与设计；
- 编写或修改 DESIGN / Plan；
- 被委派的实施任务；
- 实施过程中疑难问题的协助；
- proposal / Plan review；
- implementation / code review；
- debugging / root-cause analysis；
- 其他由空间规则和技能允许的专家工作。

Codex 始终拥有：

- 工作目标与 owning workflow 的控制权；
- 决定什么时候向 ChatGPT 委派什么；
- 为每个请求声明技能、上下文、约束和 authority；
- 收到 response 后继续业务流程；
- owning workflow 明确保留给 controller 的 commit、进度、用户门禁等职责。

## 2. Core abstraction

C2C 的第一层抽象是 **Session**，不是 Plan，也不是 review round。

```text
Session = 围绕一个稳定工作目标的持续协作上下文

Session
  ├─ Request 1 -> Response 1
  ├─ Request 2 -> Response 2
  ├─ Request 3 -> Response 3
  └─ ...
```

例如：

```text
SESSION_ID: c2c_dsh_upgrade
SESSION_GOAL: 完成 DSH upgrade guardrails 工作

req_01 -> 架构咨询
req_02 -> 修改 DESIGN
req_03 -> 实施 Task 2
req_04 -> 分析测试失败
req_05 -> implementation review
```

这些 request 属于同一个工作目标，因此共享一个 Session 和一段 ChatGPT conversation。

工作目标实质变化时，应创建新的 Session，而不是把无关工作继续塞进旧 Session。

## 3. What C2C owns — and does not own

C2C 拥有：

- Session identity 与 Session directory；
- Session goal 与 ChatGPT conversation binding；
- 一组按时间顺序保存的 request / response 历史；
- 同一 Session 同时只允许一个 pending request；
- Browser interaction 与后台 completion channel；
- C2C 自己产生的中间文档/评审报告/证据的 Session-local 存储；
- ChatGPT reviewer role binding（替代 Rook）。

C2C 不拥有：

- `dev-flow` / `ontology-evolution` 等业务生命周期；
- Plan approval / implementation / verification / archive 状态；
- review budget 与 re-review 轮次；
- PASS / REVISE / BLOCK 的业务定义；
- commit / merge / user validation 权限；
- 某个任务应该如何设计、实施或评审。

因此以下旧 C2C 业务状态不再存在：

```text
INIT / PLAN / EXECUTING / EXECUTED / REVIEW / DONE / BLOCKED
```

`BLOCKED` 只保留为 **单次 response status**：表示 ChatGPT 没能完成本次专家请求；它不是
review verdict，也不是整个 workflow 的状态。

## 4. Skill precedence and request authority

一次 C2C 请求受三层规则共同约束：

1. **Space rules**：根及目录 `AGENTS.md`、启动协议；
2. **Owning workflow / task skills**：例如 `dev-flow`、`df-implement`、
   `df-proposal-review`、`df-implement-review`；
3. **C2C**：Session、浏览器、后台 response、ChatGPT remote-agent binding。

C2C 不覆盖前两层的业务方法和权限。

每个 request 必须显式带 `AUTHORITY`，告诉 ChatGPT 本次允许做到什么程度。例如：

```text
Analyze only; do not edit files.
```

```text
May revise docs/design/DESIGN.md; do not edit source code.
```

```text
May implement Plan Task 3, edit code/tests and run verification; do not commit or edit Plan progress.
```

```text
Review only; do not modify the reviewed change.
```

ChatGPT 不得从“自己有写权限”推断“本次允许写”。请求 authority、owning skill 与用户授权
共同决定可写面。

## 5. Reviewer override

启用 C2C 时，**ChatGPT 完全替代 Rook 的评审职责**。

- proposal / Plan review：ChatGPT 读取 `df-proposal-review`；
- implementation / code review：ChatGPT 读取 `df-implement-review`；
- C2C 模式不再调用 Rook；
- review skill 中出现的 `Rook` 名字只表示普通非 C2C 场景的默认 reviewer；
- 方法、budget、severity、verdict、报告格式、re-review 规则全部继续由 review skill 定义。

因此 C2C 不保存“评审第几轮”，也不增加额外轮次；每个 review request 都消耗 owning
review skill 自己的预算。例如 `df-implement-review` 的首次评审 + 一次复审上限仍然有效。
如果 review skill 允许再复审，Codex 只是再创建一个新的
`REQUEST_ID`。

## 6. Identity model

### 6.1 SESSION_ID

`SESSION_ID` 是一个稳定工作目标的协作标识。

它绑定：

- Session goal；
- Session directory；
- ChatGPT conversation URL；
- 所有 request / response 历史；
- C2C-owned artifacts。

正常情况下：

```text
1 SESSION_ID = 1 work goal = 1 ChatGPT conversation = N request/response pairs
```

conversation 发生 404 或其他不可恢复故障时，可以换 chat，但保持同一个 `SESSION_ID`。

### 6.2 REQUEST_ID

`REQUEST_ID` 只标识 Session 中的一次专家请求。

它用于：

- 把后台 waiter 与正确 response 对上；
- 防止旧 response 串到新 request；
- 在 Session 历史里定位这一轮工作。

它不是 iteration，也不表达 review round 或业务阶段。

## 7. Request contract

Codex 在发送 request 前先读取当前 workflow 与相关技能，并只传指针和任务说明。

```text
[C2C]
SESSION_ID: <stable session id>
REQUEST_ID: <unique request id>

SESSION_GOAL:
<stable work goal>

GOAL:
<exact job for this request>

CONTEXT:
- <Plan / DESIGN / checkout / commit / file / evidence pointer>

AVAILABLE_SKILLS:
- <path> — <why useful>

REQUIRED_SKILLS:
- <path> — <must govern this request>

AUTHORITY:
<what ChatGPT may read/edit/run/decide for this request>

CONSTRAINTS:
<settled user decisions and hard boundaries; or none>

EXPECTED_RESULT:
<analysis / implementation / artifact / verdict etc.>

SESSION_DIR:
.wopal-space/c2c/sessions/<SESSION_ID>/
```

`AVAILABLE_SKILLS` 只列与本次工作相关的技能，不机械列出整个 `.codex/skills`。

`REQUIRED_SKILLS` 由 owning workflow / task nature 决定。例如：

- 直接实施 -> `df-implement`；
- proposal/Plan review -> `df-proposal-review`；
- implementation review -> `df-implement-review`。

ChatGPT 收到后：

1. `space_status`；
2. 按根 `AGENTS.md` 的启动链加载空间规则；
3. 读取 `REQUIRED_SKILLS`；
4. 需要时读取 `AVAILABLE_SKILLS`；
5. 自己读取真实文件、代码、diff、图片与证据；
6. 在 authority 与技能允许的范围完成工作；
7. 把 C2C-owned 中间产物写入 Session directory；
8. 正式 workflow artifact 写到 owning skill 的 canonical 路径；
9. 最后执行 `session.py respond`；
10. 在浏览器聊天里给人类可读结论。

## 8. Response contract

response status 只有两个：

```text
COMPLETED — ChatGPT 完成了本次请求
BLOCKED   — 因缺输入、权限、用户决策或基础设施，ChatGPT 没能完成本次请求
```

任务特定结果放 `data`。例如 review：

```json
{
  "requestId": "req_05",
  "status": "COMPLETED",
  "summary": "实施评审发现一个 Blocker。",
  "artifacts": [
    ".wopal-space/c2c/sessions/c2c_demo/implementation-review.md"
  ],
  "data": {
    "verdict": "BLOCK",
    "counts": "1B 0W 0I"
  },
  "completedAt": "..."
}
```

`BLOCK` 是 review skill 的 verdict，不是 C2C status。

## 9. Session lifecycle

Session 自己只有一个极小生命周期：

```text
OPEN -> CLOSED
```

解释：

- `OPEN`：可以继续创建新的 request；
- `CLOSED`：这个工作目标的协作已经结束，不再接收 request。

C2C 不从 response 自动关闭 Session。是否结束整个工作目标由 Codex 根据 owning workflow
决定。

`close` 在存在 pending request 时必须拒绝。

## 10. Storage model

### 10.1 Workspace binding

```text
.wopal-space/c2c/space.json
```

保存：

```json
{
  "spaceId": "wopal-workspace",
  "connectorName": "WopalSpace-Bot",
  "projectUrl": "..."
}
```

### 10.2 One directory per Session

```text
.wopal-space/c2c/
  space.json
  sessions/
    c2c_demo/
      session.json
      architecture-analysis.md
      implementation-review.md
      debug-notes.md
```

`session.json` 示例：

```json
{
  "sessionId": "c2c_demo",
  "goal": "完成某个工作目标",
  "status": "OPEN",
  "chatUrl": "https://chatgpt.com/...",
  "requests": [
    {
      "requestId": "req_01",
      "goal": "分析架构方案",
      "preparedAt": "...",
      "response": {
        "requestId": "req_01",
        "status": "COMPLETED",
        "summary": "...",
        "artifacts": [".wopal-space/c2c/sessions/c2c_demo/architecture-analysis.md"],
        "completedAt": "..."
      }
    },
    {
      "requestId": "req_02",
      "goal": "实施 Task 2",
      "preparedAt": "..."
    }
  ],
  "pendingRequestId": "req_02",
  "createdAt": "...",
  "updatedAt": "..."
}
```

下一次 request 不覆盖上一条 response；Session 是整个协作历史的索引。

### 10.3 Artifact ownership

C2C-owned 中间成果统一放 Session directory，例如：

- review report；
- architecture analysis；
- debug notes；
- Session-specific sanitized evidence；
- 临时比较/调研结果。

因此 C2C 不再使用专用 `.wopal-space/reviews/` 目录。

但正式 artifact 仍由 owning skill 决定 canonical 位置：

- dev-flow Plan 仍在 Plan 目录；
- DESIGN 仍在产品/项目设计目录；
- ontology proposal 仍在 proposal 目录；
- 代码/测试仍在项目 checkout。

Session 只在 `response.artifacts` 中引用这些路径。

`drop` 只删除自己的 Session directory，不跟随外部 artifact 指针删除文件。
`drop` 只接受已经 `CLOSED` 的 Session，避免把仍准备继续协作的 Session 当成垃圾清理。

## 11. Background channel

后台 checkpoint 是 Codex 判断“这一轮专家工作完成”的权威机器信号。

推荐顺序：

```text
Codex: session.py open --session <S> --goal '<session goal>'       # first time only
Codex: session.py prepare --session <S> --request <R> --goal '<request goal>'
Codex: start session.py wait --session <S> --request <R>
Codex: browser sends C2C request
ChatGPT: read skills/workspace; do the work
ChatGPT: write Session/canonical artifacts
ChatGPT: session.py respond --session <S> --request <R> ...        # last machine action
Codex: wait returns READY
Codex: consume response, continue owning workflow
```

`respond` 必须匹配当前 `pendingRequestId`，否则拒绝。

response 写入后：

- request 历史保留；
- `pendingRequestId` 变为 `null`；
- Session 仍保持 `OPEN`；
- Codex 可以创建下一条 request。

`wait` 可以读取已经完成的历史 request，因此 Codex 重启后仍可以恢复旧 response。

只要 `pendingRequestId` 还存在，Codex 本轮就没有结束；`wait` timeout 只触发恢复，不触发
最终用户回复。

## 12. Browser channel

浏览器负责：

- 打开/恢复 ChatGPT conversation；
- 发送 request；
- 用户可见全过程；
- 观察生成/错误；
- 后台 response 缺失时恢复；
- conversation 丢失时 HANDOFF。

边界：浏览器自动化始终由 Codex 直接执行。`session.py` 只维护 Session/request/response
checkpoint，不生成 browser payload，不输入 composer，不点击 Send，也不负责页面导航。

规则：

1. 一个 Session 正常复用一个 conversation；
2. 使用保存的 `chatUrl`；
3. 使用 Codex in-app browser（iab）；
4. 新会话用 Chat mode；
5. `tab.markHandoff()` + `tab.markDeliverable()` 保持交付标签页；
6. Browser transport 必须把一个 C2C request 当成一个原子消息：先构造完整多行文本，再一次性
   写入 composer；正文换行不得转换成 Enter 提交事件；提交动作与正文输入分离，只点击一次
   Send；
7. Request 以 `[C2C]` 开始、以 `[C2C END]` 结束。发送前后都用这两个边界和
   `REQUEST_ID` 校验完整性；发送后必须只新增一条 user message；
8. 如果部分 request 已被错误提交，不继续发送剩余片段；该 conversation 已被污染，改用新的
   Chat conversation HANDOFF 同一个 Session 和 pending request，再完整重发；
9. 正常等待以后台 `wait` 为主，浏览器低频观察；
10. 浏览器已经有答案但后台没有 response 时，让 ChatGPT 补跑同一个 request 的 `respond`；
11. 不从聊天文字推导业务 workflow state。

Codex 重启恢复 pending request 时，先检查保存的 conversation。若已经存在同一个
`REQUEST_ID` 且同一条 user message 同时包含 `[C2C]` 与 `[C2C END]`，只恢复 `wait`，
不重发；只有完整消息不存在时才发送，发现残片则按 transport-corrupted 规则换 chat HANDOFF。

## 13. Generic work examples

### 13.1 Consultation

Codex 请求 ChatGPT 分析问题，`AUTHORITY` 可设为只读。ChatGPT 返回 recommendation。

### 13.2 Design / Plan authoring

如果 owning skill 允许 ChatGPT 修改正式文档，`AUTHORITY` 指定可写路径。ChatGPT 直接更新
canonical artifact，response 引用该路径。

### 13.3 Delegated implementation

Codex 可以直接委派一个实施任务给 ChatGPT：

- REQUIRED skill 通常包含 `df-implement`；
- `AUTHORITY` 说明可修改哪些项目文件、可运行哪些验证、是否禁止 commit/Plan progress；
- ChatGPT 通过 WopalSpace-Bot 直接修改空间内项目并运行验证；
- response 返回 touched files / verification / relevant artifacts；
- Codex 按 owning workflow 做 controller-owned acceptance/commit/progress。

### 13.4 Review

C2C 模式下全部 review 由 ChatGPT 完成，Rook 不再参与。review report 默认写 Session directory。

### 13.5 Debug / implementation assistance

Codex 实施中遇到困难时，在同一个 Session 新建 request，请 ChatGPT分析、修改或直接协助修复，
取决于 `AUTHORITY`。

## 14. Recovery

| Situation | Recovery |
|---|---|
| Codex restart | `session.py get --session <S>`；读取 history、`pendingRequestId`、chatUrl |
| waiter interrupted | 对同一 request 重跑 `wait` |
| wait timeout | 看一次浏览器；恢复同一 request 后继续等待，不结束本轮 |
| stale/wrong response | 拒绝，不猜；读取同一 Session 当前 pending request |
| conversation 404 | 新建 conversation，保持同一 `SESSION_ID`，更新 chatUrl，HANDOFF 当前 Session |
| connector unavailable | 停止并告知用户；不伪造结果 |

HANDOFF 传 Session goal、当前 request、相关 skills/context，不恢复 C2C 之外的 workflow 状态机。

## 15. Cleanup

当整个工作目标完成且没有 pending request：

```bash
session.py close --session <SESSION_ID>
```

当 owning workflow / 用户不再需要 C2C 历史和中间成果：

```bash
session.py drop --session <SESSION_ID>
```

这样可以一次清理：

- Session checkpoint；
- review report；
- architecture/debug 中间文档；
- Session-specific evidence。

而正式 Plan/DESIGN/source 等 external artifacts 不受影响。

## 16. Evidence and media

继续坚持 **pointers, not payloads**：

- workspace 可见 checkout：ChatGPT 用 `exec_command` / `git -C` 自读；
- Session-specific sanitized evidence 可以直接写入 Session directory；
- 外部 workflow 的 evidence 仍按 owning skill 放置；
- 不把大 diff / log 粘进控制消息。

媒体：

- 有 OpenAI/用户 file reference -> `save_artifact`；
- 只有 browser download -> `scripts/media_import.py`；
- 图片 -> `read_image`；
- Session-owned media 可以放 Session directory；
- 正式产品媒体仍放 canonical path。

## 17. Packaging

```text
codex-with-chatgpt/
  SKILL.md
  SKILL.zh.md
  docs/DESIGN.md
  references/protocol.md
  references/zh/protocol.zh.md
  references/project-instructions.md
  references/zh/project-instructions.zh.md
  scripts/session.py
  scripts/media_import.py
  tests/test_session.py
```

`SKILL.md` 是操作权威；`DESIGN.md` 定义架构与边界；`protocol.md` 定义请求/HANDOFF 模板；
`session.py` 只管理 Session + request/response checkpoint，不管理业务 workflow。

## 18. Design invariants

1. **C2C owns expert collaboration sessions, not business workflow.**
2. **A Session represents one stable work goal.**
3. **One Session contains many request/response exchanges.**
4. **ChatGPT is a remote expert agent, not a fixed planner/reviewer.**
5. **ChatGPT may implement when request authority and skills permit it.**
6. **Codex remains the controller.**
7. **C2C mode replaces Rook for all review duties.**
8. **Review rules come from review skills, never from C2C.**
9. **No C2C iteration semantics.**
10. **One Session normally binds one ChatGPT conversation.**
11. **C2C-owned artifacts live under the Session directory.**
12. **Canonical workflow artifacts stay in their owning locations.**
13. **Browser is visible interaction; background response is reliable completion.**
14. **Pointers, not payloads.**
15. **Pending request means Codex keeps the current turn alive.**
16. **WopalSpace-Bot belongs to ChatGPT only; Codex never calls it directly.**

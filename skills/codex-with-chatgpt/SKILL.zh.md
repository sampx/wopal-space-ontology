---
name: codex-with-chatgpt
description: >
  当 Codex 在一个工作任务中需要与 ChatGPT 持续协作时使用，例如咨询、设计、实施协助、
  调试或评审，并可能围绕同一工作目标进行一轮或多轮交互。
---

# Codex with ChatGPT

C2C 通过 WopalSpace-Bot 把本地 Codex 与 ChatGPT 远程专家 Agent 连接起来。

核心模型：

```text
Session = 一个工作目标 / 一段持续协作
  Request 1 -> Response 1
  Request 2 -> Response 2
  Request 3 -> Response 3
```

Session 不是 Plan，也不是 review round。同一个 Session 可以连续包含咨询、设计、实施、
调试和评审请求。

## 硬规则

1. **C2C 只管交互，不管业务流程。** `dev-flow`、`ontology-evolution` 等 owning skill
   继续管理生命周期、门禁、返工、commit 和用户授权。
2. **ChatGPT 是远程专家 Agent，不是固定 planner/reviewer。** 只要请求权限和相关技能允许，
   它可以读取、分析、设计、写文档、改代码、跑命令/测试、调试和评审。
3. **Codex 是 controller。** 它拥有本地工作目标，决定委派什么，提供相关技能、上下文和
   权限，并在每个 response 后继续 owning workflow。
4. **C2C 中 ChatGPT 完全替代 Rook。** 不调用 Rook；review skill 里的 Rook 名称只是普通
   非 C2C 场景的默认 reviewer 绑定。
5. **评审规则仍由 review skill 定义。** C2C 不复制 review budget、PASS/REVISE/BLOCK、
   报告格式或复审规则。
6. **Session 是一等公民；Request 不是业务轮次。** 一个 `SESSION_ID` 内有多组
   `REQUEST_ID -> response`，没有 C2C iteration。
7. **一个 Session 正常绑定一个 ChatGPT conversation。** 故障恢复换聊天时仍保持同一个
   `SESSION_ID`。
8. **传指针，不传大载荷。** 发路径、commit、revision、skill 路径和简短目标；ChatGPT
   自己读取真实空间。
9. **后台 response 是机器完成信号。** 浏览器文字是用户可见解释与恢复通道。
10. **C2C 自己的中间成果放 Session 目录。** 其他 workflow 的正式产物留在 canonical
    位置，Session 只记录指针。
11. **有 pending request 就继续本轮。** `prepare` 之后，在对应 response 被收到并消费前，
    Codex 不能发送最终回复。`wait` 超时不是完成，恢复同一个 request 后继续等待。
12. **WopalSpace-Bot 只给 ChatGPT 用。** Codex 永远不直接调用它。本地工具失败就本地
    修复；如果要交给 ChatGPT 处理，显式新建一个 C2C request。
13. **实施、测试和验证默认由 Codex 负责。** ChatGPT 运行在远程 Docker 环境，可能与
    宿主 workspace 的运行环境不一致；因此代码实施默认由 Codex 完成，只有 Codex 确实
    遇到困难或委派明显更合适时才交给 ChatGPT。ChatGPT 改过代码后，最终测试与验证仍由
    Codex 在本地环境执行后再接受结果。
14. **浏览器自动化由 Codex 自己负责。** `session.py` 只管理 Session/request checkpoint，
    不生成浏览器 payload、不往 ChatGPT composer 输入文字、不点击 Send、也不决定页面导航。
    浏览器交互继续由 Codex 直接执行，Skill 负责把操作规则写清楚。

## 规则优先级与权限

每次请求依次受三层规则约束：

1. 空间 `AGENTS.md` / 启动协议；
2. owning workflow 与 task skill；
3. C2C 的传输、Session 与 ChatGPT 角色绑定。

C2C 不削弱前两层。

每个 request 还必须写 `AUTHORITY`，说明 ChatGPT 本次允许做什么，例如：

- 只分析，不改文件；
- 可以修改指定 DESIGN，不改代码；
- 可以实施指定 Task，修改代码/测试并运行验证，但不 commit；
- 只做评审，不修改被评审内容。

不要自行扩大权限。owning skill 对委派工作的限制仍然适用于 ChatGPT。

## 评审替代

启用 C2C 时，ChatGPT 完全替代 Rook：

- proposal/Plan review -> ChatGPT + `df-proposal-review`；
- implementation/code review -> ChatGPT + `df-implement-review`；
- 不再额外调用 Rook；
- 评审预算和复审规则原样来自 review skill。

C2C 不增加评审轮次；每次 C2C review request 都占用 owning review skill 自己的预算。
例如 `df-implement-review` 仍然最多是首次评审 + 一次复审。

## 连接

连接器：**WopalSpace-Bot**。

WopalSpace-Bot 只存在于 ChatGPT 侧。Codex 只使用自己的本地工具、in-app browser 和
`session.py`，绝不直接调用 WopalSpace-Bot。

ChatGPT 每次 C2C 请求先 `space_status`，再按根 `AGENTS.md` 的启动链加载规则。开始任务前
必须读取 Codex 指定的 `REQUIRED_SKILLS`，必要时读取 `AVAILABLE_SKILLS`。

连接不可用时停止并说明，不伪造空间证据或 response。

## Session 模型

Session 表示一个稳定工作目标。工作目标发生实质变化时，新建 Session。

```text
SESSION_ID: c2c_dsh_upgrade
GOAL: 完成 DSH upgrade guardrails 工作
CHAT: 一个 ChatGPT conversation

requests:
  req_01 -> 架构咨询
  req_02 -> 修改 DESIGN
  req_03 -> 实施一个 Task
  req_04 -> 实施评审
```

Session 自己只有非常轻的生命周期：

```text
OPEN -> CLOSED
```

这里只表示还能不能继续收 request，不表示 dev-flow 或产品流程状态。

## Session 存储

```text
.wopal-space/c2c/
  space.json
  sessions/
    <SESSION_ID>/
      session.json
      <C2C 自己的中间成果...>
```

例如：

```text
architecture-analysis.md
plan-review.md
implementation-review.md
debug-notes.md
evidence.patch
```

不再创建 C2C 专用 `reviews/` 目录；评审报告归产生它的 Session。

正式产物仍留在 owning skill 的 canonical 位置：

- dev-flow Plan -> 原 Plan 路径；
- DESIGN -> 原设计路径；
- ontology proposal -> 原 proposal 路径；
- 源码和测试 -> 项目 checkout。

Session 只保存这些外部产物的指针。删除 Session 只删除自己的目录，不删除外部正式产物。

## Codex 发请求前

1. 加载 owning workflow skill。
2. 找出当前工作目标和本次请求相关的技能。
3. 为这个稳定目标打开一个 Session。
4. 后续同目标请求复用该 Session。
5. 每次请求提供：
   - `AVAILABLE_SKILLS`：可能有帮助的相关技能；
   - `REQUIRED_SKILLS`：本次必须遵守的方法技能。
6. 明确写 `AUTHORITY`。
7. 给出真实 Plan/DESIGN/checkout/commit/evidence 指针，不粘大段内容。

不要机械发送整个技能目录。

## Request 协议

使用 `references/zh/protocol.zh.md` 中的完整模板，它是唯一协议定义。新 ChatGPT
conversation 的第一条 request 带 `ROLE`；每一条 request 都带固定 `INSTRUCTION`。
GOAL、CONTEXT、skills、AUTHORITY、EXPECTED_RESULT 等动态字段按本次请求填写。

## 浏览器通道

浏览器是可见交互通道。

- 一个 `SESSION_ID` 正常复用一个 ChatGPT conversation；
- 优先使用 Session 保存的 `chatUrl`；
- 使用 Codex in-app browser（iab），除非用户明确要求，否则不接管桌面浏览器；
- 新 C2C conversation 使用 Chat mode；
- 标签页用 `tab.markHandoff()` + `tab.markDeliverable()` 保留并交付。

发送与等待：

1. 打开/恢复 Session 的 conversation；
2. 先在内存中构造完整 request，再一次性写入 composer。request 内的换行只是文本，
   不能用会把 `\n` 解释成键盘 Enter 的逐字/逐键输入方式；优先用一次性的 fill、粘贴式
   DOM 写入或等价原子输入；
3. 写入完成后先检查 composer：必须同时包含开头 `[C2C]` 与结尾 `[C2C END]`，并且
   `REQUEST_ID` 正确；然后只点击一次 Send。不要用 Enter 作为提交动作；
4. 发送后确认页面只新增一条 user message，而且这条消息同时包含 `[C2C]` 与
   `[C2C END]`。如果任何片段已经被错误发出，不要继续补发剩余片段；把当前 conversation
   视为 transport-corrupted，新建 Chat conversation，并对同一个 Session / pending request
   做 HANDOFF 后重新原子发送完整 request；
5. 以后台 waiter 为正常完成通道；
6. 必要时低频看浏览器：仍生成就继续等；已回答但没有后台 response，就要求 ChatGPT
   补跑 `respond`；404 时新建 conversation 并 HANDOFF 同一个 Session。

Codex 重启后如果存在 pending request，不要直接重发。先打开 Session 保存的 conversation，
检查可见 user message：如果已经有一条消息同时包含同一个 `REQUEST_ID`、`[C2C]` 和
`[C2C END]`，说明 request 已经发出，只恢复 `wait`；只有完整消息不存在时才重新发送。
如果只看到残片，走上面的 transport-corrupted 恢复流程。

不要从浏览器里的 DONE/PASS/BLOCK 推导 workflow 状态。

request pending 时，对用户只能发进度更新，不能作为最终回复结束本轮。`READY` 后读取
response，并在同一轮继续 owning workflow，除非真的到了需要用户输入/确认的 gate。

## 后台通道

```bash
S=.codex/skills/codex-with-chatgpt/scripts/session.py
```

### 1. 空间绑定

```bash
python3 $S set --space-id <space-id> \
  --connector-name WopalSpace-Bot --project-url '<project-url>'
```

### 2. 为工作目标打开 Session

```bash
python3 $S open \
  --session <SESSION_ID> \
  --goal '<稳定工作目标>' \
  [--chat-url '<chat-url>']
```

这会创建：

```text
.wopal-space/c2c/sessions/<SESSION_ID>/session.json
```

同一个 id + 同一个 goal 重复 open 是幂等的；拿同一个 Session id 换工作目标会被拒绝。

后续更新 conversation URL：

```bash
python3 $S set --session <SESSION_ID> --chat-url '<chat-url>'
```

### 3. 准备本次 request

```bash
python3 $S prepare \
  --session <SESSION_ID> \
  --request <REQUEST_ID> \
  --goal '<本次 request 目标>'
```

一个 Session 同时只允许一个 pending request；已经完成的 request/response 永久保留在本
Session 历史里，不会被下一次覆盖。

### 4. 后台等待

```bash
python3 $S wait \
  --session <SESSION_ID> \
  --request <REQUEST_ID> \
  --timeout 1800
```

wait 进程由当前 harness 保持，不用 `nohup`、`&` 或 `setsid` 脱离。

`wait` 超时不代表可以回复用户并停止，只代表机器完成信号还没到。检查/恢复同一个 request，
然后在本轮继续等待。

### 5. ChatGPT 写回 response

ChatGPT 最后一个机器动作：

```bash
python3 $S respond \
  --session <SESSION_ID> \
  --request <REQUEST_ID> \
  --status COMPLETED \
  --summary '<一句核心结论>' \
  [--artifact '<path>'] \
  [--data-json '<任务特定 JSON>']
```

评审报告优先放 Session：

```bash
python3 $S respond \
  --session c2c_auth \
  --request req_04 \
  --status COMPLETED \
  --summary '实施评审发现 1 个 blocker。' \
  --artifact '.wopal-space/c2c/sessions/c2c_auth/implementation-review.md' \
  --data-json '{"verdict":"BLOCK","counts":"1B 0W 0I"}'
```

评审成功发现 Blocker 仍然是 `COMPLETED`；`BLOCK` 是 review skill 的 verdict。

本次专家工作本身无法完成时：

```bash
python3 $S respond \
  --session <SESSION_ID> --request <REQUEST_ID> \
  --status BLOCKED --summary '<缺什么、需要什么>'
```

### 6. 同 Session 继续下一次请求

收到 response 后，Codex 可以在同一个 Session 继续 `prepare` 新 `REQUEST_ID`。

### 7. 关闭与清理

整个工作目标完成且没有 pending request 后：

```bash
python3 $S close --session <SESSION_ID>
```

owning workflow 不再需要这些协作历史/中间成果后：

```bash
python3 $S drop --session <SESSION_ID>
```

`drop` 只删除 `.wopal-space/c2c/sessions/<SESSION_ID>/`。
`OPEN` Session 不能直接 drop，必须先 close。

退出码和恢复动作统一定义在 `references/zh/protocol.zh.md`。

## ChatGPT 可以承担什么工作

C2C 不把请求固化成某个 workflow。同一个 Session 中可以依次让 ChatGPT：

- 分析问题或架构；
- 在 Codex 实施途中做技术咨询；
- 在 owning skill 允许时创建/修改 DESIGN 或 Plan；
- Codex 需要帮助时实施被委派的 Task，但最终测试与验证回到 Codex 本地环境完成；
- 分析失败和调试；
- 评审 Plan/proposal；
- 评审实现、commit、diff 或任意代码；
- 生成其他本次请求允许的空间产物。

允许动作由 `REQUIRED_SKILLS`、`AUTHORITY`、空间规则和 owning workflow 共同决定。

## 证据与 diff

ChatGPT 通过 WopalSpace-Bot 自己读取证据。

- 空间可见 repo/worktree -> `exec_command` + `git -C <path>`；
- worker 看不到的 Git 元数据 -> Codex 写 sanitized evidence；Session 专属证据优先放 Session
  目录；
- 外部 CI/GitHub 证据也用指针文件；
- 不把大 diff / log 塞进控制消息。

## 恢复

```bash
python3 $S ls
python3 $S get --session <SESSION_ID>
```

Codex 重启后：

1. 读取 `session.json` 与 `chatUrl`；
2. 看 `pendingRequestId`；
3. 必要时对同一 request 重新 `wait`；
4. owning workflow 自己从自己的文件恢复业务状态。

ChatGPT conversation 丢失时不新建 Session：保持同一 `SESSION_ID`，更新 `chatUrl`，然后
HANDOFF Session goal + 当前 request。

## 媒体

- 有 OpenAI/用户文件引用 -> `save_artifact`；
- 只有浏览器下载 -> `scripts/media_import.py`；
- 图片 -> `read_image`；
- Session 自己的媒体/证据可以放 Session 目录；
- 产品/workflow 正式媒体仍放 canonical 路径。

## 参考

- `docs/DESIGN.md` — 架构与边界
- `references/protocol.md` — Session/request/response 与 HANDOFF 模板
- `references/project-instructions.md` — 最小 ChatGPT Project 绑定文本

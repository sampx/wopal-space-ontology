# C2C Session / Request 协议

C2C 把本地 Codex 与 ChatGPT 远程专家 Agent 连接起来。一个 Session 代表一个稳定工作目标，
里面可以有多组 request / response。

WopalSpace-Bot 只给 ChatGPT 用。Codex 使用自己的本地工具；本地工具失败时，要么本地修复，
要么显式发一个 C2C request 委派给 ChatGPT，不能直接改用 WopalSpace-Bot。

## Session 标识

```text
SESSION_ID: c2c_<稳定目标>
SESSION_GOAL: <一个工作目标>
```

正常情况下，一个 Session 复用一个 ChatGPT conversation。故障换 chat 时仍使用同一个
`SESSION_ID`。

## Request

```text
[C2C]
SESSION_ID: <稳定 session id>
REQUEST_ID: <本 Session 内唯一 request id>

ROLE:
你是这个 Session 的远程专家 Agent。Codex 是 controller。

SESSION_GOAL:
<稳定工作目标>

GOAL:
<本次具体专家工作>

CONTEXT:
- <path / checkout / commit / evidence pointer>

AVAILABLE_SKILLS:
- .codex/skills/<skill>/SKILL.md — <为什么相关>

REQUIRED_SKILLS:
- .codex/skills/<skill>/SKILL.md — <本次必须遵守>

AUTHORITY:
<本次允许 ChatGPT 读取、修改、执行、决定什么>

CONSTRAINTS:
<已确定边界；没有则 none>

EXPECTED_RESULT:
<分析 / 建议 / 实施 / artifact / review 结果>

SESSION_DIR:
.wopal-space/c2c/sessions/<SESSION_ID>/

INSTRUCTION:
先 `space_status`。读取根 AGENTS.md 与启动链；开始工作前读取 REQUIRED_SKILLS，必要时读取
AVAILABLE_SKILLS。通过 WopalSpace-Bot 自己检查真实空间，不依赖转述。按照 AUTHORITY 与
owning skill 决定可修改/执行范围。C2C 自己的中间产物写 SESSION_DIR；其他 workflow 的
正式产物写回其 canonical 路径。

LAST_ACTION:
用以下命令写回 response：
python3 .codex/skills/codex-with-chatgpt/scripts/session.py respond \
  --session <SESSION_ID> --request <REQUEST_ID> --status COMPLETED \
  --summary '<一句结论>' [--artifact <path>] [--data-json '<json>']

[C2C END]
```

新 conversation 第一条 request 带 `ROLE`；后续同一 conversation 可以省略。固定
`INSTRUCTION` 段每一条 request 都必须携带。

`REQUEST_ID` 只用于关联，不是 iteration 或 review round。

## Response 语义

| Status | 含义 |
|---|---|
| `COMPLETED` | ChatGPT 完成了本次专家请求 |
| `BLOCKED` | 因输入、权限、用户决策或基础设施缺失而无法完成本次请求 |

任务特定结果放 `data` 和 artifacts，C2C 不解释其业务语义。

### 评审示例

成功发现 blocker 的 review 仍是 `COMPLETED`：

```bash
python3 .codex/skills/codex-with-chatgpt/scripts/session.py respond \
  --session c2c_auth --request req_42 --status COMPLETED \
  --summary '实施评审发现 1 个 blocker。' \
  --artifact '.wopal-space/c2c/sessions/c2c_auth/implementation-review.md' \
  --data-json '{"verdict":"BLOCK","counts":"1B 0W 0I"}'
```

`BLOCK` 是 review skill 的 verdict，不是 C2C status。

### 专家请求本身无法完成

```bash
python3 .codex/skills/codex-with-chatgpt/scripts/session.py respond \
  --session c2c_auth --request req_43 --status BLOCKED \
  --summary '缺少要求的设计文件，请提供或指出替代文件。'
```

## Reviewer 替代

启用 C2C 时，ChatGPT 完全替代 Rook：

- proposal/Plan review -> REQUIRED `df-proposal-review`；
- implementation/code review -> REQUIRED `df-implement-review`；
- C2C 模式不调用 Rook；
- review skill 里的 Rook 名称只是普通非 C2C 的默认绑定；
- 方法、budget、verdict、报告格式仍由 review skill 定义；
- C2C 不增加 review round。每次 C2C review request 都占用 owning review skill
  自己的预算；例如 `df-implement-review` 仍然最多首次评审 + 一次复审。

## 后台握手

工作目标第一次使用：

```bash
S=.codex/skills/codex-with-chatgpt/scripts/session.py
python3 $S open --session <SESSION_ID> --goal '<SESSION_GOAL>'
```

每次请求：

```bash
python3 $S prepare \
  --session <SESSION_ID> \
  --request <REQUEST_ID> \
  --goal '<本次 request 目标>'

python3 $S wait \
  --session <SESSION_ID> \
  --request <REQUEST_ID> \
  --timeout 1800
```

wait 退出码：

| Exit | 含义 | Codex 处理 |
|---|---|---|
| `0` | 收到匹配的合法 response | 消费结果，继续 owning workflow |
| `2` | 超时 | 检查/恢复同一个 request，然后继续等待 |
| `3` | Session/request/response 非法或不匹配 | 读取同一 Session 修复，不猜 |
| `130` | SIGINT/KeyboardInterrupt 中断 | 对同一 request 重新执行 `wait` |

request pending 时，Codex 必须保持本轮继续运行。`wait` 超时不是完成：检查/恢复同一个
request 后继续等待。

ChatGPT 最后一个机器动作是给相同 Session + request 写 `respond`。非当前 pending request 的
response 会被拒绝。

完成的 request/response 会保留在 Session 历史里；下一次 `prepare` 只是追加，不覆盖。

## Session 文件

```json
{
  "sessionId": "c2c_auth",
  "goal": "完成 auth refactor 工作",
  "status": "OPEN",
  "chatUrl": "https://chatgpt.com/...",
  "requests": [
    {
      "requestId": "req_01",
      "goal": "分析设计",
      "preparedAt": "2026-10-23T08:00:00Z",
      "response": {
        "requestId": "req_01",
        "status": "COMPLETED",
        "summary": "...",
        "artifacts": [
          ".wopal-space/c2c/sessions/c2c_auth/architecture-analysis.md"
        ],
        "completedAt": "2026-10-23T08:05:00Z"
      }
    },
    {
      "requestId": "req_02",
      "goal": "实施 Task 2",
      "preparedAt": "2026-10-23T08:10:00Z"
    }
  ],
  "pendingRequestId": "req_02"
}
```

Session 自己只有 `OPEN / CLOSED`。dev-flow state、review round、iteration 都不属于这里。

## Session 产物

C2C 自己的中间产物放在 `session.json` 旁边：

```text
.wopal-space/c2c/sessions/c2c_auth/
  session.json
  architecture-analysis.md
  implementation-review.md
  debug-notes.md
```

不再单独建立 C2C `reviews/` 目录。

其他 workflow 拥有的正式 artifact 仍放 canonical 位置，Session 只记路径。

## 关闭与清理

```bash
python3 $S close --session <SESSION_ID>
python3 $S drop --session <SESSION_ID>
```

有 pending request 时 `close` 会拒绝。`drop` 只接受已经 `CLOSED` 的 Session，并且只删除
Session directory，不删除 Session 引用的外部正式 artifact。

## 浏览器行为

1. 复用 Session 保存的 `chatUrl`；
2. 只用一个 in-app browser tab；
3. `tab.markHandoff()` + `tab.markDeliverable()`；
4. 先完整构造 request，再用一次性的 composer-set 操作写入全文。换行属于消息内容；
   禁止用会把 `\n` 变成 Enter 键事件的逐字/逐键输入来发送多行 request；
5. 提交前检查 composer 同时含有 `[C2C]`、正确 `REQUEST_ID`、`[C2C END]`；提交时
   只点击一次 Send，禁止用 Enter 提交；
6. 提交后确认页面只新增一条 user message，且该消息同时含 `[C2C]` 和 `[C2C END]`；
   如果已经出现部分消息，停止发送剩余片段，把该 conversation 视为 transport-corrupted，
   新建 Chat conversation，对同一个 Session / pending request HANDOFF 后重新发送完整 request；
7. 正常等待后台 waiter；
8. 必要时或 waiter timeout 再看浏览器；
9. 已有可见答复但无后台 response -> 要求 ChatGPT 对同一 request 跑 `respond`；
10. conversation 404 -> 新建 conversation，HANDOFF 同一个 Session。

浏览器自动化属于 Codex。`session.py` 不负责往 ChatGPT 输入、点击、提交或导航。Codex
重启后如果 `pendingRequestId` 仍存在，重新发送前先检查保存的 conversation：若可见的一条
user message 已同时包含同一个 `REQUEST_ID`、`[C2C]`、`[C2C END]`，说明已经发送，只恢复
`wait`；完整消息不存在才发送；只有残片时走 transport-corrupted 恢复。

等待期间可以给用户进度更新，但不能发送最终回复结束本轮。`READY` 后消费 response，
并在同一轮继续 owning workflow，除非真的到了需要用户输入/确认的 gate。

不要把浏览器里的 DONE/PASS/BLOCK 当 workflow state。

## HANDOFF

```text
[C2C]
SESSION_ID: <同一个 session id>
REQUEST_ID: <当前 pending request id>

ROLE:
你是这个 Session 的远程专家 Agent。Codex 是 controller。

HANDOFF:
原 ChatGPT conversation 不可用，继续同一个 Session。

SESSION_GOAL:
<稳定工作目标>

GOAL:
<当前专家工作>

CONTEXT:
- <当前指针>

AVAILABLE_SKILLS:
- <相关技能>

REQUIRED_SKILLS:
- <必须技能>

AUTHORITY:
<当前 request 权限>

KNOWN_RESULT:
<只写已经确认的事实>

EXPECTED_RESULT:
<剩余要交付的内容>

SESSION_DIR:
.wopal-space/c2c/sessions/<SESSION_ID>/

LAST_ACTION:
用 session.py respond 为本 SESSION_ID + REQUEST_ID 写回 response。

[C2C END]
```

HANDOFF 只恢复协作上下文，不编码业务 workflow state。

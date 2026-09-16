# 实施审查细则 — 详细流程

六项正确性检查的完整流程。当某项检查需要完整方法、模式目录或严重度校准时加载本文件。

**目的提醒**：本审查回答的是"这个变更是否真的交付了，代码是否健全"。它不审形式——形式由测试、lint、typecheck 与 CI 负责，且已经通过。

目录：
1. [通读变更](#1-通读变更)
2. [C1 目标与真值验证](#2-c1--目标与真值验证)
3. [C2 范围完备](#3-c2--范围完备)
4. [C3 实质与接线](#4-c3--实质与接线)
5. [C4 缺陷与安全扫描](#5-c4--缺陷与安全扫描)
6. [C5 测试完整性](#6-c5--测试完整性)
7. [C6 规范与技术债](#7-c6--规范与技术债)
8. [严重度校准](#8-严重度校准)
9. [完整示例](#9-完整示例)
10. [报告骨架](#10-报告骨架)

---

## 1. 通读变更

先构造审查集：diff（`git diff`、`git diff --cached`、`git show <hash>` 或 `git diff <A>..<B>`）、变更文件清单，以及 Plan 支撑时 Plan 的声明。读一遍；然后开始探针。

阅读时建立三份清单：

1. **声明** —— 变更应当满足的每一条显式交付物或验收标准。
2. **产物** —— 每个新增或修改的文件、符号、路由、组件或 schema 元素，连同它被消费的位置。
3. **疑点** —— 一切像存根、接线缺口或缺测试的地方，留待扫描时核验。

不要在阅读与探针之间来回切换——每次回读文件的代价都高于省下的探针成本。

从一开始就留意审查模式。无 Plan 模式下，变更自身的声明意图（描述、commit message）是唯一的规格——其余全部归 C2-C6。

---

## 2. C1 — 目标与真值验证

### 检查为何存在

测试证明的是它断言的东西，不是被承诺的东西。变更可以是绿的，却仍是存根、孤立文件或目标的缩水版。本检查把承诺与产物逐级对照。

### 流程

1. **提取声明。**
   - Plan 支撑：Plan 中的每一条真值、每一条验收标准，以及声明的 Goal。
   - 无 Plan：变更自身的声明意图——描述、commit message，或审查 prompt 中的显式说明。若都没有，说明这一点并跳到 C2。
2. **定位产物**：声明所依赖的文件、函数、路由、组件或 schema 元素。
3. **对每个产物走四级**：

| 级别 | 问题 | 如何定案 |
|---|---|---|
| 1. 存在 | 预期路径下有产物吗？ | `ls`、`rg --files`、`git show --stat` |
| 2. 实质性 | 是真实实现，不是存根吗？ | 读代码；模式目录见 C3 |
| 3. 已接线 | 被 import、注册或调用——从入口可达吗？ | 追踪调用点：跨项目 `rg <symbol>` |
| 4. 功能性 | 调用时行为正确吗？ | 能静态推理的静态推理；否则 `Needs Human` |

4. **裁定缩水。** 当产物交付得比声明少（缩减的范围、延后的分支、所述目标的 `v1`），检查是否有 Plan 决策授权它。已授权 → 记录，不是发现。静默 → BLOCKER。

### 严重度

| 情形 | 严重度 |
|---|---|
| 声明的产物不在变更中 | BLOCKER |
| 产物是存根 | BLOCKER |
| 产物真实但永不可达 | WARNING；当"可达"本身即声明时 → BLOCKER |
| 静默缩减声明的交付物 | BLOCKER |
| 缩水得到 Plan 决策授权 | 不是发现 |
| 第 4 级无法静态证明 | `Needs Human` —— 不是发现 |
| 无 Plan 模式且无声明意图 | 说明意图未被声明；继续 C2-C6 |

### 第 4 级纪律

第 4 级是"调用时确实工作"。不要凭静态阅读声称它。静态阅读能定案的：对声明点名的输入而言逻辑显然正确。不能定案的：运行时行为、时序、渲染、外部集成、真实数据。这些进 `Needs Human`，并写明人类应当做的具体观察。

通常需要人工观察的第 4 级事项：

- 视觉外观与布局
- 端到端用户流程可用性
- 实时行为（WebSocket / SSE / 流式）
- 外部服务集成（支付、邮件、第三方 API）
- 错误消息是否清晰有用
- 响应式 / 移动端行为
- 无障碍性

---

## 3. C2 — 范围完备

### 检查为何存在

声明范围与交付范围在不同时刻写成，会漂移。欠交付藏在"其余部分后续跟上"的背后。过度交付则藏着无关工作与未声明的耦合。

### 流程

1. **构造交付集**：从载体取 `git diff --name-status`、`git show --stat`。
2. **构造声明集**：从 Plan 文件清单或变更描述取。
3. **双向求差：**
   - `声明 − 交付` → 承诺却缺失的工作
   - `交付 − 声明` → 声明之外完成的工作
4. **核对操作类型。** 删除与重命名必须与声明一致；未声明的删除就是整个功能无声消失的方式。
5. **逐项裁定。** 声明项缺失仅在有声明依赖它时才是 BLOCKER。多出的文件是 WARNING，除非耦合是必要的——必要的话，发现是"声明已过期"，而非"代码有错"。

### 严重度

| 情形 | 严重度 |
|---|---|
| 声明的交付物缺失，且有声明依赖它 | BLOCKER |
| 声明项缺失，不承重 | WARNING |
| 变更文件超出声明范围 | WARNING |
| 未声明的删除或重命名 | WARNING |

---

## 4. C3 — 实质与接线

### 检查为何存在

变更"看起来完成了"却其实没有，最常见的形态是能满足类型与预期的占位代码。第二常见的是没有任何东西调用它的真实代码。

### A 部分 — 存根扫描

对变更文件扫描以下模式。出现是信号，不是判决：结合上下文归类。

**注释存根**

```javascript
// TODO: implement later
// FIXME: this is broken
// HACK: temporary
// PLACEHOLDER
// ...（本应有逻辑的位置只有省略）
```

探针：`rg -n 'TODO|FIXME|XXX|HACK|PLACEHOLDER' <changed files>`

**占位文本**

```
"placeholder"   "lorem ipsum"   "coming soon"   "under construction"
"TBD"           "Not implemented"
```

探针：`rg -ni 'placeholder|lorem ipsum|coming soon|under construction|TBD|not implemented' <changed files>`

**空实现**

```javascript
return null   return undefined   return {}   return []
```

```python
pass   return None   return {}   return []
```

探针：`rg -n 'return null|return undefined|return \{\}|return \[\]' <changed files>`

注意：诚实的空返回是存在的。按调用方或声明是否依赖真实内容来归类。

**仅日志处理器**

```javascript
function handler(data) {
  console.log(data)          // 只打日志，不做任何事
}
```

探针：读每个处理器函数体；只打日志或只转发的函数体没有行为。

**假动态值**

```jsx
// 应来自 state/props，实为硬编码
<div>Message 1</div>
const id = "fixed-id"        // 应为动态生成
const count = 3              // 应为计算结果
const price = "$9.99"        // 应为格式化结果
```

按声明归类：若行为必须是动态的而值是固定的 → BLOCKER；若该值本就应当固定 → 不是发现。

**前端空壳**

```jsx
return <div>Component</div>
return <p>Coming soon</p>
return <div>{/* TODO */}</div>
return null
return <></>

onClick={() => {}}                       // 空处理器
onChange={() => console.log('clicked')}  // 仅日志处理器
onSubmit={(e) => e.preventDefault()}     // 仅阻止默认行为
```

检查组件是否渲染了实质元素——动态表达式、state 或 props 的使用、已接线的处理器。

**API 路由空壳**

```typescript
export async function GET() {
  return Response.json([])              // 静态空数组，无数据源
}
export async function POST() {
  return new Response()                 // 空响应体
}
export async function POST(req) {
  console.log(await req.json())
  return Response.json({ ok: true })    // 打日志并应答，但从不处理
}
```

**数据库 schema 空壳**

```prisma
model Message {
  id      String @id
  content String
  // 缺少: createdAt, userId, chatId 以及使用它们的关系
}
```

对照声明检查每个模型：行为所需的字段与关系必须存在。

**Hooks / 工具空壳**

```typescript
export function useAuth() {
  return { user: null, login: () => {}, logout: () => {} }
}
export function useUser() {
  return { name: "Test User", email: "test@example.com" }   // 硬编码
}
```

检查返回的函数与值是否做真实工作——调 API、操作 state、产生副作用。

### B 部分 — 接线检查

对每个新产物，核验其链条的三段：

1. **声明 → import**：`rg <symbol>` —— 使用处 import 了吗？
2. **import → 使用**：import 真的被引用了吗，还是只是存在？
3. **使用 → 可达**：有某个入口（路由、渲染树、CLI、任务运行器）能通向它吗？

按模式检查：

**组件 → 数据源。** 取数调用必须被 await、消费并渲染（或以其他方式使用）：

```jsx
// 已消费
useEffect(() => { fetch('/api/messages').then(r => r.json()).then(setMessages) }, [])

// 未消费：无 await，无 .then，无赋值
fetch('/api/messages')

// 被注释掉
// fetch('/api/messages').then(r => r.json()).then(setMessages)
```

**state → 渲染。** 应当驱动输出的 state 变量必须真的出现在输出里：

```jsx
const [messages, setMessages] = useState([])
return <div>No messages</div>            // 渲染常量，不是 state
return <div>{otherData.map(...)}</div>   // 渲染了错误的变量
```

**API → 存储。** 查询必须被 await，结果必须被返回，而不是被丢弃：

```typescript
const messages = await prisma.message.findMany()
return Response.json(messages)           // 正确

await prisma.message.findMany()
return Response.json({ ok: true })       // 查询了，然后丢弃结果

const messages = prisma.message.findMany()
return Response.json(messages)           // 返回的是 Promise，不是数据
```

**路由 → 注册。** 新路由、命令或任务必须在框架或运行器能发现它的地方注册。

### 严重度

| 情形 | 严重度 |
|---|---|
| 存根占据了某条声明行为 | BLOCKER |
| 新模块、组件或路由从未被 import、注册或使用 | WARNING |
| 真实产物仅能通过死代码到达 | WARNING |
| 声明依赖的空返回 | BLOCKER |
| 诚实的空返回（无依赖） | 不是发现 |
| 非关键路径上的 TODO / FIXME | INFO |

---

## 5. C4 — 缺陷与安全扫描

### 检查为何存在

测试覆盖的是有人想到要断言的部分。缺陷藏身于没人断言的支路、输入与时序里。安全漏洞则活在测试永远不会越过的信任边界上。

### A 部分 — 缺陷扫描

逐个 hunk 自问失败问题：**什么输入、状态或时序会让这里出错？**

高产区域：

- **错误路径** —— 失败被吞掉，错误只打日志不传播，错误分支跳过清理
- **异步处理** —— 缺少 `await`、浮动 Promise、竞态、未处理的 rejection、顺序假设
- **边界值** —— 空集合、零、负数、超大值、区间与切片的 off-by-one
- **类型/运行时接缝** —— 解析后的输入被当作已定型使用、`as` 断言覆盖未校验数据、可空性假设
- **状态迁移** —— 重入、重复提交、部分应用的更新、失败时未回滚
- **比较逻辑** —— `==` 与 `===` 语义、对合法可为 falsy 的值做 falsy 检查

只报有具体场景的发现。"可能有错"不是发现。

### B 部分 — 安全扫描

找出信任边界并逐项检查：

- **注入** —— 用户输入未参数化地流入查询、shell 命令或模板
- **XSS** —— 未转义地插值进渲染输出、`dangerouslySetInnerHTML` 的等价物
- **不安全反序列化** —— 不可信载荷传入带代码执行面的解析器
- **缺失校验** —— 请求体未经校验即使用；schema 校验存在但被绕过
- **授权缺口** —— 新路由或处理器缺少同类已有的鉴权检查
- **密钥暴露** —— 凭证出现在代码、提交文件、日志或错误消息中

探针：`rg -n 'eval\(|dangerouslySetInnerHTML|innerHTML|exec\(|spawn\(' <changed files>`；检查每个新 POST/PUT 处理器是否在使用前校验。

### 严重度

| 情形 | 严重度 |
|---|---|
| 有具体失败场景的缺陷 | BLOCKER |
| 可利用的安全漏洞（注入、XSS、缺失鉴权、密钥泄露） | BLOCKER |
| 有具体场景的潜在风险（"在 Z 场景下会导致 Y"） | WARNING |
| 公开面上缺失输入校验 | WARNING |
| 没有具体场景的担忧 | 不要报 |

---

## 6. C5 — 测试完整性

### 检查为何存在

测试是变更能提供的最强证据——也最容易造假。如果真正重要的测试被跳过、循环或空洞，绿色的套件什么都证明不了。

### 流程

1. **把行为映射到测试。** 对变更声明的每个行为，找到覆盖它的测试。声明了行为却无覆盖测试 → WARNING（Plan 要求测试时 → BLOCKER）。
2. **检查断言。** 读每个测试实际断言的内容，而不是它名字说的内容。
3. **扫描坏模式**（见下）。

### 坏模式

**跳过 / 禁用的测试**

```typescript
it.skip('sends a message', () => { ... })
xit('loads data')
xdescribe('Messages')
describe.skip('Chat', () => { ... })
```

```python
@pytest.mark.skip
def test_send(): ...
```

```go
t.Skip("not implemented")
```

探针：`rg -n 'skip\(|xit|xdescribe|\.skip|@pytest\.mark\.skip|t\.Skip' <changed test files>`
判定：某条声明行为的唯一测试被跳过 → BLOCKER。

**循环证明**

系统生成期望值，同一个系统再验证它：

```typescript
const expected = generateOutput(input)   // 被测函数
const actual = generateOutput(input)     // 同一函数
expect(actual).toEqual(expected)         // 什么都没证明
```

判定：BLOCKER。

**占位断言**

```typescript
expect(true).toBe(true)
expect(false).toBe(false)
expect(1).toBe(1)
```

探针：`rg -n 'expect\(true\)|expect\(false\)|expect\(1\)|expect\("test"\)' <changed test files>`
判定：BLOCKER。

**弱断言**

```typescript
expect(result).toBeDefined()
expect(component).toBeTruthy()
expect(data).not.toBeNull()
```

它们检查存在性，不检查值：

```typescript
// 弱
expect(result).toBeDefined()
// 强 —— 断言真实行为
expect(result).toEqual({ id: 1, name: 'test' })
expect(result.items).toHaveLength(3)
```

探针：`rg -n 'toBeDefined|toBeTruthy|toBeFalsy|not\.toBeNull' <changed test files>`
判定：单个弱断言 → INFO；文件内全部断言都弱 → WARNING。

**缺失断言**

测试文件或测试用例里完全没有 `expect` / `assert` ——空壳照跑，照报绿。

探针：`rg -c 'expect|assert' <test file>` ——为零 → WARNING。

**冗余测试**

大量测试重复同一个 happy path，而不同分支仍无覆盖。读变更的测试，检查每个测试是否保护了不同的行为。

判定：关键分支无覆盖 → WARNING；否则不报。

### 判断注记

标准是"行为损坏时这个测试会不会失败"。功能移除后仍然通过的测试就是装饰，无论看起来多完备。当覆盖存在但你看不出某测试能否抓住回归时，去读断言与它执行的代码路径——不要数测试名字。

---

## 7. C6 — 规范与技术债

### 检查为何存在

项目有常驻契约——`AGENTS.md`、既有模式、安全规则——以及债务预算。无视第一项或透支第二项的变更，成本由下一位贡献者承担。

### 流程

1. **读项目规则。** 项目根目录的 `AGENTS.md`（若有目录级规则一并读）。对照每一条适用规则检查变更文件。
2. **检查模式一致性。** 变更是否遵循同类工作的既有模式——错误处理、日志、配置、类型、模块结构？
3. **扫描债务增长。**

### 重复 / 抽取

仅当重复造成真实维护成本或漂移风险时才报：

- 同一段校验 / 解析 / 重试 / 分支逻辑在本次范围内多处出现
- 重复逻辑已在漂移，或很可能漂移
- 抽公共工具能明显降低 bug 风险或未来编辑成本

**不要**报：无实际成本的小重复，或抽象后会变得更难读的直线序列。

### 死代码 / 脆弱接线

- 任何入口都到不了的代码 → 当它掩盖声明行为时 WARNING，否则 INFO
- 遗留的注释代码块 → INFO
- 配置或接线与代码实际读取的内容无声不一致 → WARNING

### 严重度

| 情形 | 严重度 |
|---|---|
| 违反已声明的安全约束 | BLOCKER |
| 违反规范或破坏既有模式 | WARNING |
| 重复已在漂移，或很可能漂移 | WARNING |
| 死代码掩盖了声明行为 | WARNING |
| 注释代码块、过期 TODO | INFO |
| 品味层面的偏好 | 不是发现 |

---

## 8. 严重度校准

四类，按读者应当采取的行动定义：

| 类别 | 含义 | 自问 |
|---|---|---|
| **BLOCKER** | 变更不能照此上线 | "若这样上线，是坏掉了还是不诚实？" |
| **WARNING** | 能上线，但带着风险、缺口或未证明的声明 | "这会带来返工还是掩盖缺陷？" |
| **INFO** | 值得知道的改进，无需行动 | "合理的作者会耸肩吗？" |
| **Needs Human** | 只有运行时或人工观察能定案 | "我无法静态验证它吗？" |

刻意缺席：**警告计数阈值**。判定由严重度推出，不靠计数：有 Blocker → BLOCK，否则有 Warning → REVISE，否则 PASS。

### 校准演练

| 情形 | 正确判定 |
|---|---|
| 处理器只打日志，而声明是"处理消息" | BLOCKER（存根占据声明） |
| 函数存在、写得正确，但全项目没有调用点 | WARNING（未接线） |
| 某条声明行为的唯一测试被跳过 | BLOCKER |
| 测试断言 `expect(true).toBe(true)` | BLOCKER |
| 一个测试含 `toBeDefined` 加两条强值断言 | 不是发现（强测试里的单个弱断言最多 INFO） |
| 四行输入归一化重复，规则预期保持一致 | 不是发现 |
| 重复的校验已在两个调用点之间出现分歧 | WARNING |
| 查询执行了、结果被丢弃、返回静态 `{ ok: true }` | BLOCKER（声明依赖该数据） |
| 删除的辅助函数其实仍被 import（构建会抓到） | 不是发现——构建失败归 CI |
| 对变更组件视觉外观的担忧 | `Needs Human`，不是发现 |
| "我会把这个模块组织得不一样" | 不是发现 |

---

## 9. 完整示例

### 示例 A — 逐级行走抓住存根

**Plan 声明**："消息从数据库获取"。路由存在：

```typescript
// api/messages/route.ts:8
export async function GET() {
  return Response.json([])
}
```

**探针**：第 2 级——读函数体；没有查询。第 3 级会通过（路由已注册），对空系统第 4 级也可能通过。

**发现**：
```yaml
check: C1_goal_verification
severity: blocker
location: "api/messages/route.ts:8-10"
reality: "处理器返回常量；不接触任何数据源"
impact: "『从数据库获取』这一声明在第 2 级即为假；该端点无法服务真实数据"
fix: "按声明查询存储并返回其结果"
```

### 示例 B — 第 3 级抓住接线缺口

**变更**：新增 `MarkdownRenderer` 组件，实现完整，带测试。

**探针**：`rg MarkdownRenderer src/` ——它只出现在自身文件与其测试中。消息列表仍渲染纯文本。

**发现**：
```yaml
check: C3_wiring
severity: warning
location: "components/MarkdownRenderer.tsx:1"
reality: "除自身模块与测试外，没有任何 import 或使用"
impact: "该组件从应用不可达；渲染改进实际并未交付给用户"
fix: "在消息列表中用新组件渲染消息，或若时机未到则移除该组件"
```

### 示例 C — 测试中的循环证明

**变更**：一个解析器加测试。

**探针**：读断言。

```typescript
const expected = parse(input)
const actual = parse(input)
expect(actual).toEqual(expected)
```

**发现**：
```yaml
check: C5_test_integrity
severity: blocker
location: "tests/parser.test.ts:14-16"
reality: "expected 与 actual 都来自被测解析器；任何输出，无论对错，都相等"
impact: "该测试无法对它所声称保护的行为失败"
fix: "改为断言手写的独立期望值"
```

### 示例 D — 正确不报的重复

**变更**：两个新处理器各自在校验前对 email 做 trim 与归一化。规则四行且稳定。

**正确处理**：不报。抽取并不能可测量地降低 bug 风险。若审查者想报，细则说：仅当重复造成真实维护成本或漂移风险时才报。

### 示例 E — 有具体场景的缺陷

**变更**：一个更新端点。

**探针**：检查边界值。

```typescript
// api/profile/route.ts:22
const { name } = await req.json()
await db.updateUser(userId, name)     // name 可能为 undefined；无校验
```

**发现**：
```yaml
check: C4_defect_scan
severity: warning
location: "api/profile/route.ts:22-23"
reality: "name 从请求体读出后未经校验直接写入；缺少 name 的请求会把 undefined 写覆盖存储值"
impact: "在『客户端省略该字段』这一场景下，用户已存的 name 被破坏"
fix: "写入前校验请求体，并拒绝缺少必填字段的请求"
```

### 示例 F — 严重逻辑风险，仅讨论

**变更**：一个清理任务。

```typescript
// src/jobs/purge.ts:18
await deleteAllUserContent(userId)
```

**发现**：严重且不可逆，但是否正确取决于 prompt 未陈述的产品策略——放进 `Serious Logic Risks (Discuss with User)`；它不改变判定。

---

## 10. 报告骨架

```markdown
# 实施审查 — {范围标签}

## 概要
- 审查类型: Implementation (Plan-backed | Planless diff)
- 判定: PASS | REVISE | BLOCK
- 统计: Blocker N / Warning N / Info N / Needs-human N
- 审查对象: {Plan 路径 / commit / commit range / working tree}

## Blocker
### B-01: {标题}
- 位置: `{file}:{line}`
- 证据: `{片段}` / {输出}
- 影响: {失败模式}
- 修复方向: {改什么}

## Warning
{同上}

## Info
{每条一行}

## Serious Logic Risks (Discuss with User)
{可能源于需求驱动的严重风险}

## Requirement Questions
{仅需求歧义}

## Needs Human
- {条目} — 需要的观察: {看什么}

## Positive Findings
- {已核验项 —— 写明核验方式}

## UNCOVERED STEPS
{仅当有步骤未完成时出现}
```

### 判定决策

- 出现任何 Blocker → `BLOCK`
- 无 Blocker，至少一条 Warning → `REVISE`
- 只有 Info（或没有）→ `PASS`
- `Needs Human`、`Serious Logic Risks`、`Requirement Questions` 默认永不影响判定

### PASS 必须带 Positive Findings

`PASS` 必须写明检查了什么、怎么检查的——例如："双向求差了交付与声明范围；把每条声明行为走完存在/实质/接线；对变更文件做了存根扫描；对变更测试做了跳过/循环/占位断言审计"。只给一个裸 `PASS`，等于要读者凭空相信你，这违背审查的意义。

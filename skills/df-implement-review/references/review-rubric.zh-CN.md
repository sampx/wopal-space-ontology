# Implementation Review Rubric — Pattern Catalogues & Procedures

四个核心问题背后的具体排查方法。当某项检查需要详细步骤、常见问题清单或具体案例时，加载本文件。

以下模式是取证线索，不是必须穷举的检查清单或独立的定级规则。按 `SKILL.md` 和 `df-implement` 的最小化原则，结合产品实际用途、用户、部署、信任边界、获批设计及实际后果选择适用检查；按实际价值和风险定级。无法说明影响或修复收益的边界问题不进入修复清单，明确的强制契约和重大真实风险仍须核查。

目录：
1. [通读一遍建立三张清单](#1-通读一遍建立三张清单)
2. [Q1 半成品与未接通代码排查](#2-q1--半成品与未接通代码排查)
3. [Q2 对外接口与共用逻辑排查（防误伤）](#3-q2--对外接口与共用逻辑排查防误伤)
4. [Q3 常见 Bug 与边界漏洞清单](#4-q3--常见-bug-与边界漏洞清单)
5. [Q4 测试有效性与文档同步](#5-q4--测试有效性与文档同步)
6. [Q4 孤儿代码标签（仅本次 diff 范围）](#6-q4--孤儿代码标签仅在本次-diff-范围内)
7. [批量排查命令（Probes）](#7-批量排查命令probes)
8. [能力资产规范检查（进化提案）](#8-能力资产规范检查进化提案)
9. [严重度判定参考](#9-严重度判定参考)
10. [评审实例](#10-评审实例)
11. [完整交付基线范围与对抗式 DESIGN/Proposal 核查](#11-完整交付基线范围与对抗式-designproposal-核查)

---

## 1. Building the three lists

先把改动（`git diff`、`git diff --cached`、`git show <hash>` 或 `git diff <A>..<B>`）和被修改的文件完整读一遍。不要边读边跑搜索命令来回切换——反复重读文件最浪费上下文。在通读过程中顺手建好三张清单：

1. **承诺清单（Claims）**——每条要交付的功能或验收标准，来源是 Plan 任务、设计文档条款、`AGENTS.md` 里写明"必须"的规则，或对话里明确记录过的决定。评审前先把这些找齐。
2. **对外接口（Contract surface）**——diff 改动的每个导出函数/类、参数与返回值、数据结构（schema）、共享类型、配置项，外加**参数没变但内部逻辑变了**的函数。
3. **疑点标记（Flags）**——读代码时顺手记下的疑似半成品、没接通的入口、假测试、本次改动留下的孤儿代码，留到后面集中核实。

建好清单后，四个问题围绕三张清单做定点核实，不重复无目的扫描。发现同源缺陷时，本轮内追查共同实现、同类操作和受影响调用方，合并关键反例和验收条件；优先用实际行为证据确认影响。

缺少授权或设计证据时，如实说明 Q1 哪些完整性结论无法判断；继续检查 Q2–Q4 的真实缺陷、交付物质量及适用技术债。仓库审计可提出有依据的维护精简，不凭空发明产品目标。

## 2. Q1 — Stub patterns & probes

搜到特征词只是线索，不是最终结论——要按**"承诺的功能或调用方是不是真的依赖这段逻辑"**来定性。

**注释占位（未完成的 TODO）**
```javascript
// TODO: implement later
// FIXME: this is broken
// HACK: temporary
// PLACEHOLDER
// ... (该写业务逻辑的地方是空的)
```
排查命令：`rg -n 'TODO|FIXME|XXX|HACK|PLACEHOLDER' <被改文件>`

**占位文案**
```
"placeholder"   "lorem ipsum"   "coming soon"   "under construction"
"TBD"           "Not implemented"
```
排查命令：`rg -ni 'placeholder|lorem ipsum|coming soon|under construction|TBD|not implemented' <被改文件>`

**空实现**
```javascript
return null   return undefined   return {}   return []
```
```python
pass   return None   return {}   return []
```
排查命令：`rg -n 'return null|return undefined|return \{\}|return \[\]|pass\s*$' <被改文件>`——有些场景确实该返回空值；要看调用方或承诺的功能是不是指望它返回真实数据。

**只打日志不干活的函数**——函数体里只有日志打印或原样转发，没有实际业务处理。逐个检查新增或修改的 handler。

**写死的假动态值**
```jsx
<div>Message 1</div>        // 本应从 state/props 读取
const id = "fixed-id"       // 本应动态生成
const count = 3             // 本应计算得出
```
对照承诺清单定性：如果功能要求是动态数据，代码里却写死常量，直接标 **BLOCKER**。

**前端空壳组件**
```jsx
return <div>Component</div>
return <p>Coming soon</p>
return null
onClick={() => {}}
onSubmit={(e) => e.preventDefault()}
```

**API 路由空壳**
```typescript
export async function GET() { return Response.json([]) }   // 写死空数组，根本没查数据源
export async function POST() { return new Response() }     // 空响应体
```

**数据库表结构缺失**——数据模型缺少完成该功能必需的字段或关联关系。

**Hook / 工具函数空壳**
```typescript
export function useAuth() { return { user: null, login: () => {}, logout: () => {} } }
```

**新写代码的接通检查（防"写了但没接上"）：**
- 声明了 → 有地方 import（`rg <symbol>`）
- import 了 → 真正调用了（不只是写在文件头）
- 调用了 → 从真实入口可达（路由、页面渲染树、CLI 命令、定时任务入口）
- 组件 → 数据源：请求确实 `await` 了、拿到数据了、渲染出来了
- 状态 → 界面：state 变量真正出现在渲染输出里
- 接口 → 存储：数据库查询真正执行并把结果返回，而不是查完直接丢弃
- 路由 → 注册：新写的路由/子命令/任务已经在总入口注册，能被框架加载到

## 3. Q2 — Contract-surface procedure

这是编译和测试最容易漏掉的地方。最常溜过去的坑是：**函数签名没变但行为悄悄变了**，或者**把以前没写测试的老调用方搞坏了**。

### Step 1 — extract the contract surface

从 diff 中列出其他代码可能依赖的每一项改动：

- 导出的函数/类——参数、返回类型、抛出的异常
- 数据结构——schema 字段、JSON 返回格式、枚举值、数据库列
- 共享类型 / 常量 / 配置项名称
- **参数和返回类型没变，但内部逻辑变了的函数**——最危险、最隐蔽的一类
- 测试公共设施——fixture、mock、辅助函数（改了它们可能导致原本能抓 bug 的老测试失效）

### Step 2 — find all consumers

在全项目搜索 `rg <symbol>`，特别注意 **diff 之外**的文件。如果调用方太多，先用 `rg -l <symbol>` 列出文件，挑选几类有代表性的调用点核对，并在报告里如实说明哪些没查完。

### Step 3 — classify the break type

| 破坏类型 | 重点查什么 |
|---|---|
| 参数/返回值变化 | 增删参数、收窄或放宽类型、修改返回类型。强类型能抓大部分，但遇到 `any`、`as` 强转或动态语言就会漏掉 |
| 空值变化 | 以前保证不返回 `null`/空数组，现在可能返回 `null`（或反过来）。老调用方直接 `.map()` 或链式调用就会崩溃 |
| 同步变异步 | 以前直接返回值，现在返回 Promise；动态语言或没加 `await` 的调用方会静默出错 |
| 顺序变化 | 调用方依赖的数组排序、事件触发顺序、遍历顺序变了 |
| 重复调用副作用变化 | 以前重试是安全的（幂等），现在重试会重复扣款/重复写入（或反过来） |
| 副作用变化 | 以前是纯函数，现在悄悄改了全局状态；或者把调用方依赖的副作用删掉了 |
| 报错方式变化 | 错误码、HTTP 状态码、报错文案格式变了——很多调用方会按报错信息做分支处理 |
| 默认行为变化 | 同样的正常输入，现在走到了别的分支或返回了不一样的结果 |
| 性能骤降 | 高频路径从 O(n) 变成 O(n²)，数据量一大直接卡死 |
| 数据结构未同步迁移 | 字段改名或删除了，但还有老代码在读旧字段名；或者删掉了枚举值 |

对每个调用方问一句：它依赖上面表格里的哪条假设？改完之后这条假设还成立吗？

### Severity

- diff 之外的调用点在实际使用场景下发生实质回归或违反重要契约 → **BLOCKER**；轻微且值得修正的问题按 SKILL.md 定级，低收益问题不要求修复
- 行为确实变了，但可能是设计有意为之 → 先回去查设计条款；设计已经批准的改动不算问题。授权依据不明时披露限制；独立证实的缺陷按实际严重度报告
- 调用方太多没查全 → Other notes，绝不假装全查过了

## 4. Q3 — Defect catalogue

从真实使用路径、变更契约及实际风险选择以下排查模式。**只报告有证据、可达触发条件及实际影响的真实问题。** 性能与安全防护以当前设计、信任边界和合理负载为依据，不要求把所有理论边界防到极致；可造成重大后果的真实风险不因低概率而忽略。一个模式的存在不自动决定严重度。

**并发与状态冲突**
- 多个异步操作同时读写同一个共享状态，存在竞态条件（race condition）
- 共享计数器或标志位"先检查再修改"（非原子操作），并发下会覆盖彼此结果
- 重复触发：按钮连点或请求重入时，上一次还没跑完又进了下一次
- 半截失败：多步修改里第 1 步已落盘、第 2 步报错退出，没有回滚导致数据残缺
- 闭包拿到了过期的循环变量或旧的 React props/state

**资源未释放**
- 打开的文件句柄、数据库连接、流（stream）没有在所有分支上关闭
- 报错分支漏掉清理（正常走完会关闭，进 `catch` 或提前 `return` 就漏关了）
- 连接池借出的连接没归还（高并发下会把连接池耗尽）
- 每次渲染或每次调用都新建文件监听、定时器、事件订阅，却没有销毁

**边界值与数值计算**
- 范围、数组切片、分页计算的差一错误（off-by-one）
- 空数组、空对象、缺字段时没判空就直接访问属性
- `0`、负数、超大数进入除法、内存分配或数组下标
- 累加器、计数器、缓冲区溢出或未设上限

**异步处理**
- 漏写 `await`（需要等结果或等落盘的地方变成了后台裸跑）
- 未捕获的 Promise 报错（floating promise）
- 乱序覆盖：先发出的慢请求比后发出的快请求晚回来，把新数据覆盖成了旧数据
- 调用外部接口/外部命令没设超时（timeout），网络卡住时永远挂起

**错误处理**
- `catch` 吞掉异常后什么都不做，带着损坏的状态继续往下跑
- 本该立刻中止的操作只打了一行日志就继续执行
- 实际执行失败却返回成功状态（例如 HTTP 200 里包着错误文本，调用方以为成功了）
- 发生部分失败后状态不一致，既没清理也没回滚

**类型与运行时脱节**
- 对未经校验的外部数据直接用 `as` 强制转换类型
- 外部传入的参数还没过校验就直接拿去用
- 某个字段在合法情况下也可能缺失，代码却直接当非空字段用
- `JSON.parse`、环境变量、URL 查询参数没做校验就直接当成强类型结构使用

**安全漏洞**
- 用户输入未做参数化或转义，直接拼进 SQL、Shell 命令或模板
- `innerHTML` / `dangerouslySetInnerHTML` 混入了用户可控内容
- 不安全的反序列化（`eval`、直接反序列化不可信数据）
- 请求体还没做权限和格式校验就被业务代码消费；或者校验逻辑可被绕过
- 新增的接口/命令漏掉了同类接口都有的登录鉴权检查
- 代码、配置文件、日志或报错信息里硬编码或泄露了密钥/Token

排查命令：`rg -n 'eval\(|dangerouslySetInnerHTML|innerHTML|exec\(|spawn\(' <被改文件>`；逐个检查新增的 POST/PUT 接口是否先校验后使用，新增路由是否挂载了鉴权中间件。

## 5. Q4 — Test integrity & documentation drift

### Test integrity — broken patterns

| 假测试模式 | 排查命令 | 判定 |
|---|---|---|
| 被跳过/禁用的测试 | `rg -n 'it\.skip|xdescribe|xit|@pytest\.mark\.skip|t\.Skip' <测试文件>` | 必需验证被跳过且无等效证据时按门禁定级；合法环境限制如实披露 |
| 自己证自己（循环证明） | 期望值（expected）是用被测函数自己算出来的 | 被当作有效验证证据时 **BLOCKER** |
| 假断言（占位断言） | `rg -n 'expect\(true\)|expect\(false\)|expect\(1\)'` | 被当作有效验证证据时 **BLOCKER** |
| 弱断言（只查存不存在） | `rg -n 'toBeDefined|toBeTruthy|not\.toBeNull'` | 根据实际行为和其他验证证据判断是否存在有价值的覆盖缺口 |
| 根本没写断言 | `rg -c 'expect\|assert' <file>` 结果为 0 | 仅是线索；检查 runner、退出状态和实际结果，按验证缺口定级 |
| 设计明确承诺的行为没有测试 | 对照承诺清单逐条找测试或其他有效验证 | 必需验证不足按 SKILL.md 定级；不重复要求等效测试 |

衡量标准只有一条：**如果把对应的业务功能改坏，这个测试会报错变红吗？** 把功能代码删了还能绿的测试就是摆设。

判定范围严格限定在**设计明确承诺的行为**上。设计没提的内部实现分支、你没预料到的写法，都不算测试缺口——那是实现自由，不是漏测。把"所有改动的分支都该有测试"当标准，等于用评审员的想象给实现方加需求。

实际验证优先复用已有入口和隔离测试环境，选择 `rules/testing.md` 规定的最低成本有效层级。记录运行命令或操作、观察结果及未验证事项；代码反例足以证明缺陷时不强制构造额外复杂测试，关键行为缺乏证据时才补做定向验证。不修改交付代码或测试来获取通过结果。

### Documentation drift

改了对外接口或命令用法，却不更新对应的文档，等于误导用户。直接复用 Q2 整理出的对外接口清单，对每一项变更（API、数据结构、CLI 参数、配置项、设计明确规定的行为）：

1. 找出文档里写它的地方——`rg '<symbol>' docs/ README* AGENTS.md` 以及公开的注释文档。
2. 检查本次 diff 有没有同步更新这些文档。
3. 现状 DESIGN 与代码、规约与 DESIGN 或各级规约之间不一致，或受影响的 DESIGN、规约违反各自技能质量要求 → **BLOCKER**。业务 Proposal 驱动交付未经授权实质偏离设计或违反未变更的上层架构约束 → **BLOCKER**；非关键目标偏差或已授权但提案未同步 → **WARNING**。受影响术语表一致性按 dev-doc-master 强制文档要求检查。未要求记载的内部实现细节不算缺漏。
4. 如果项目守则（如 `AGENTS.md`）明确规定"改代码必须同步改对应文档" → 违反直接标 **BLOCKER**。

纯粹的内部重构、对外行为毫无变化的，不需要改文档。如果文档在当前仓库之外看不到 → 列入 Other notes。

## 6. Q4 — Orphan tags (change review: diff-created orphans only)

**变更评审只查本次改动制造的孤儿与重复**，不做全仓瘦身；全仓瘦身是 Repo audit 模式的事。

每条问题写一行：位置、删什么、用什么替。**给不出具体替换方案的只是抱怨，不能算问题。**

| 标签 | 抓什么问题 | 替换方案 |
|---|---|---|
| `delete:` | 本次改动切换调用方后留下的孤儿函数/文件/依赖；本次改动新写进来的死代码 | 直接删掉 |
| `shrink:` | 本次改动新增的重复逻辑，本可复用既有函数，或用更短写法 | 写明复用位置或更短写法 |

`stdlib:`、`native:`、`yagni:` 只在 Repo audit 模式下使用。变更评审里提这三类，等于替实现方重新选技术方案——除非设计条款本来就这么要求，否则不报。

### What to hunt (change review)

- **本次改动留下的孤儿代码与孤儿测试**：对 diff 里删掉的每一个 `import` 或函数调用，在全项目搜一下（`rg <符号或模块名>`）还有没有生产代码在用。如果生产代码已经是 0 引用（或者只剩它自己的测试文件在测它），必须把**旧模块和它的测试文件**一起标 `delete:`。
- 本次改动新写进来的死代码、注释掉的旧代码块、没人用的导出

不要在变更评审里做这些事（它们属于 Repo audit）：盘点历史遗留死代码、扫全仓 0 引用依赖、评估既有实现该不该用标准库、审查已有接口是否过度抽象。这些都不是本次改动引入的，提了只会把一次小修变成重构。

### Runtime & platform check for `stdlib:` and `native:` (Repo audit only)

在建议用标准库或系统命令替换前，必须核实两件事：
1. **运行时最低版本**：查看 `package.json` 的 `engines`、`pyproject.toml` 的 `requires-python`、`go.mod` 等，确认该内置 API 在项目支持的最低版本中已经存在（例如 `path.matchesGlob` 需要 Node >=20.17 / >=22.5）。
2. **跨平台兼容性**：如果 `native:` 建议调用系统外部命令（如 `zip`、`tar`、`sed`），确认该项目支持的所有目标操作系统（macOS / Linux / Windows）默认都自带该命令和对应参数。

### Never flag

- 能护住核心逻辑的最精简测试——一个冒烟测试、一条 `assert` 自检、一个小巧的单元测试文件。那是质量底线，不是赘肉。
- 带有合规 `simplified:` 标记、且明确写清了上限与升级触发条件的临时简化方案（仅在缺少升级触发条件时才标为无锚点腐烂风险）。
- 外部输入边界上的安全校验、防止数据丢失的错误处理、权限与安全防护——绝不能为了省行数而删减。
- 设计明确接受的技术取舍：轮询代替事件、固定节流窗口、顺序执行代替并发、一次重试代替指数退避。这些是设计决策，不是赘肉。
- 纯个人偏好（"换我写会换一种目录结构"）、变量起名风格、代码格式偏好。

### Severity

| 情形 | 严重度 |
|---|---|
| 本次 diff 切换了调用方，导致被替换的旧代码/旧测试在生产代码中变成 0 引用（本次制造的孤儿） | 按 `df-implement` 清理义务报告 **WARNING** |
| 本次改动新增的重复逻辑，项目里已有适用实现（报告需点名具体的 `file:line`） | 有实际维护收益时 **WARNING**；简单且稳定的少量重复不报 |
| 历史遗留的死代码 / 没人用的依赖（仅 Repo audit 模式） | INFO（如果掩盖了功能缺失则升为 WARNING） |
| 标准库/原生替换、单实现接口等选型建议（仅 Repo audit 模式） | INFO |
| 无已证实缺陷或新增重复的可选简化建议 | INFO |

**先满足实际设计和必要安全约束，再求精简**——不为了省行数削弱必要防护，也不以未经证明的风险要求额外防护。发现本次新增的过度设计时，指出不必要的结构、实际维护成本和更直接的替代方案；不把普通实现选择当成缺陷。

### The metric (Repo audit only)

报告末尾附上：`net: -N lines, -M dependencies possible`（合计可精简的真实代码行数与依赖数）。如果代码已经很干净，写 `Lean already. Ship.`。

变更评审不算这笔账：那里没有"必须找出可删代码"的义务，硬算总账只会催生凑数的重构建议。

## 7. Probe bundle

### Diff review probes (Modes 1 & 2)

通读完 diff 后，按适用语言、变更契约及风险，从以下命令中选择有价值的探查，在被修改的文件上集中执行（把 `<被改文件>` 替换为实际路径）：

```bash
FILES='<被改文件>'
rg -n 'TODO|FIXME|XXX|HACK|PLACEHOLDER' $FILES
rg -ni 'placeholder|lorem ipsum|coming soon|under construction|TBD|not implemented' $FILES
rg -n 'return null|return undefined|return \{\}|return \[\]|pass\s*$' $FILES
rg -n 'console\.log|print\(' $FILES
rg -n 'eval\(|dangerouslySetInnerHTML|innerHTML|exec\(|spawn\(' $FILES
rg -n 'it\.skip|xdescribe|xit|describe\.skip|@pytest\.mark\.skip|t\.Skip' $FILES
rg -n 'expect\(true\)|expect\(false\)|expect\(1\)' $FILES
rg -n 'toBeDefined|toBeTruthy|toBeFalsy|not\.toBeNull' $FILES
```

- **调用方排查（Q2）**：对 diff 修改的每个导出函数/类/类型，运行 `rg -l '<符号名>' <项目路径>` 找出所有调用方（重点看 diff 之外的文件）。
- **孤儿代码排查（Q4）**：对 diff 中**删掉**的每个 `import` 或旧函数调用，运行 `rg -l '<旧模块或旧函数名>' <项目路径>`，检查它是否已经变成 0 生产引用（以及它的测试文件是否成了孤儿测试）。
- **本次新增重复排查（Q4）**：用新代码里的一段特征片段跑 `rg -n '<特征片段>' <项目路径>`，看项目里是不是已经有同样的实现。只报本次改动写出来的重复；过度抽象和工厂类的扫描属于 Repo audit。
- **项目守则检查**：仅当 diff 触及带本地化同名的 `AGENTS.md`（`AGENTS.<locale>.md`）时执行。标题与行内代码必须跨版本一致：

```bash
diff <(grep '^#' AGENTS.md) <(grep '^#' AGENTS.<locale>.md)
diff <(grep -o '`[^`]*`' AGENTS.md | sort -u) <(grep -o '`[^`]*`' AGENTS.<locale>.md | sort -u)
```

diff 非空即漂移，是否算缺陷按 `SKILL.md`（`## 项目守则评审`）的级别规则判定。过了这层检查仍存在的语义差异需要人工阅读。

### Repo audit probes (Mode 3 — whole-repo or directory lean audit)

当不看 diff、直接对现有项目或目录做**全仓瘦身审查（Repo audit）**时，先跑以下静态扫描命令把底数摸清，避免纯靠肉眼漏掉孤儿文件或误判动态导入：

1. **核对依赖清单与实际引用次数**：
   - 读取 `package.json` / `pyproject.toml` / `Cargo.toml` / `go.mod`。
   - 对每个生产依赖，在源码目录（如 `src/`）统计引用次数（`rg '<包名>' src/`），注意同时排查静态 `import`、动态 `await import('<包名>')` 以及副作用导入 `import '<包名>'`。
   - 0 引用的依赖标 `delete:`；只在 1 个地方用到且能被标准库几行代码替代的标 `stdlib:` 或 `native:`。
2. **扫描 0 引用的孤儿文件**：
   - 列出 `src/` 下所有非入口文件，检查每个文件名（去掉后缀）在 `src/` 下是否有被其他文件引用。
   - 如果某个源文件在 `src/` 下是 0 引用，只有 `tests/` 里的测试文件在引用它，说明它是**死代码配孤儿测试**——把源文件和对应测试文件一起标 `delete:`。
3. **扫描 0 外部引用的导出符号（死导出）**：
   - 提取 `src/` 下所有的 `export function|const|class|type|interface` 名称，统计每个符号在 `src/` 下的被引用文件数。
   - 只有定义文件自己用到（或只有测试文件用到）的导出，标 `delete:`（若文件内部自用则去掉 `export`，若内部也不用则整段删掉）。
4. **排查单实现抽象与冗余大文件**：
   - 运行 `rg -n 'interface |abstract class |Factory|Manager|Adapter' src/`，并按行数排序查看最大的源文件（`wc -l`）。
5. **排查遗留欠账标记、跳过测试与过期文档（分析技术债时必跑）**：
   - 运行 `rg -n 'TODO|FIXME|XXX|HACK|PLACEHOLDER|simplified:' src/` 和 `rg -n 'it\.skip|xdescribe|xit|describe\.skip|@pytest\.mark\.skip|t\.Skip' tests/`，把代码里留下的半成品欠账、临时简化记号与失效测试一并揪出来。对 `simplified:` 检查是否注明了升级触发条件（未注明升级条件的标为无触发条件的腐烂风险）。
   - 报告按收益从高到低分组输出：**可删减的依赖** → **死文件与死导出（`delete:`）** → **标准库/原生替换（`stdlib:` / `native:`）** → **过度抽象与重复逻辑（`yagni:` / `shrink:`）**（如有遗留 `TODO`/`simplified:`/失效测试/过期文档则单列一组**遗留欠账与测试/文档缺口**），末尾汇总 `net: -N lines, -M dependencies possible`。

## 8. Capability standards gate (evolution proposals)

当传入的参数包含进化提案（evolution proposal）路径时，说明本次落地的是空间的能力资产（技能、规则、Agent）。对照平台规范逐项检查落地文件：

| 规范要求 | 检查方法 |
|---|---|
| 文件头包含 `name` + `description` | 直接读文件开头的 YAML frontmatter |
| 触发条件写在 `description` 里 | `description` 明确写了什么场景下触发；不能把触发时机藏在正文后半截 |
| 正文只留工作流 + 输出格式 + 核心红线 | 没有长篇大论的说教或背景铺垫；详细目录和长篇案例下沉到 `references/` |
| `scripts/` 只放确定性、可复用的脚本 | 一次性命令片段不要塞进 `scripts/` |
| 目录结构守规矩 | 目录和文件命名与其他技能保持一致，不自创奇怪的子目录或文件格式 |
| 说人话、指令明确 | 无论是人还是 Agent，读一遍就能明白具体步骤；满篇技术黑话、翻译腔或模棱两可的表述直接作为问题报出 |

严重度按 SKILL.md 统一判定；受影响的规约违反权威 SOP 或质量要求 → **BLOCKER**。其他能力资产违反强制标准或无法正常工作 → **BLOCKER**。

这项检查与 `df-proposal-review` 前后呼应：提案评审查的是**计划写得对不对**，这里查的是**实际写出来的文件合不合格**。

## 9. Severity calibration

| 具体场景 | 正确判定 |
|---|---|
| 函数只打了一行日志，但承诺的功能是"处理并保存消息" | BLOCKER（Q1 半成品空壳） |
| 函数逻辑写对了，但全项目没有任何地方调用它 | WARNING（Q1 写了没接通） |
| Diff 把工具函数的空输入返回值从 `[]` 改成了 `null`，而 diff 外有调用方直接对返回值调 `.map()` | BLOCKER（Q2 破坏现有调用方） |
| 接口原本报错返回 4xx，现在改成返回 HTTP 200 带错误对象，导致按状态码判断的调用方失效 | 按影响定 WARNING 或 BLOCKER（Q2） |
| 必需的核心行为验证被跳过，却声称已验证通过 | BLOCKER（Q4 虚假验证）；如实记录合法环境限制，不冒充产品故障 |
| 测试里写 `expect(true).toBe(true)` | BLOCKER（Q4 假断言） |
| 测试里先写了 `toBeDefined`，后面紧跟着两条具体的值断言 | 正常，不报错 |
| 4 行简单的输入清洗逻辑在两处出现，且规则稳定 | 正常，不报错 |
| 两处复制粘贴的校验逻辑已经出现不一致（改了一处漏了另一处） | WARNING（Q4 逻辑分叉） |
| 数据库查询执行了，但返回结果被丢弃，直接返回写死的 `{ ok: true }` | BLOCKER（Q1 假实现） |
| 删掉了一个还在被别处 import 的函数（编译或打包会直接报错） | 不报——编译报错归 CI 管 |
| 实际可并发的两个写操作存在明确的交错覆盖场景，导致用户数据丢失 | BLOCKER（Q3 并发竞态） |
| 代码正常，但未经授权改变已批准的重要设计决定或未变更的上层架构 | BLOCKER（Q1 设计偏离）；非关键偏差或已授权但提案未同步 → WARNING |
| 代码实现了一种设计文档明确接受的取舍（如固定的短缓存窗口、顺序执行、轮询），且没有违背任何设计条款 | 不报——设计已拍板 |
| 代码用了一种评审员不喜欢的写法，但设计既没规定也没禁止 | 不报（最多 Info，且通常只在报告外记下） |
| 修改已记录的接口，所属现状 DESIGN 未同步 | BLOCKER（Q4 DESIGN 同步） |
| 多提交交付中早期提交改了公开契约，所属 DESIGN 整个交付窗口未动，最后一次提交干净 | BLOCKER（只有对着完整交付基线 diff 才能发现的漏同步） |
| 同一现状 DESIGN 或规约的两处描述互相矛盾 | BLOCKER（Q4 成果一致性） |
| 本次改动新增的 `retry.ts` 与项目已有的 `src/lib/http.ts:88` 退避重试逻辑重复 | WARNING（Q4 重复造轮子） |
| Diff 把命令从调 `lib/doctor.ts` 改成调 `lib/inspect.ts`，导致 `lib/doctor.ts` 和 `tests/lib/doctor.test.ts` 在生产代码中变成 0 引用 | WARNING（Q4 `delete:` 本次改动留下的孤儿代码与测试） |
| `package.json` 里装着 `eventsource`，但 `rg 'eventsource' src/` 显示 0 引用（历史遗留，本次没动） | Repo audit 模式才报 INFO；变更评审不报 |
| 定义了 `AbstractStore` 接口，但全项目只有一个 `FileStore` 实现（历史遗留，本次没动） | Repo audit 模式才报 INFO；变更评审不报 |
| 落地技能将必需触发条件藏在正文里 | BLOCKER（强制能力规范） |
| 新落地的技能文件头缺少 `description` 字段 | BLOCKER（能力资产规范） |
| 担心改完后的界面样式好不好看 | 列入 Other notes（请人眼确认） |
| "要是让我写，我会换一种模块划分方式" | 个人偏好，不报错 |
| 设计文档写了"未确认配额耗尽按限流处理"，实现照做，但评审员认为应该立刻禁用账号 | Other notes 中的设计疑虑，不影响结论 |
| 设计文档没提某个内部实现分支，实现按自己的判断写了，测试也没覆盖 | 不报——设计没承诺这个行为 |
| 管理员配置的规则在真实可达输入下可造成服务中断、影响其他用户 | BLOCKER（Q3 重大稳定性风险）；验证共同根因及关键边界，要求最小可靠修复 |
| 仅在接近资源上限且罕见的操作组合下略早拒绝请求，符合当前允许的保守限制 | 不报；若确有非关键契约偏差且值得修正，按实际影响定级或交用户决定，不为精确到每个字节追加复杂机制 |
| 只在假设未来向公众开放、负载增长或改变信任边界时才需要的防御措施 | 不报；若有实际设计价值，另作非阻断设计反馈 |

裁决规则：有 Blocker → **BLOCK**；没有 Blocker 但有值得修订的 Warning → **REVISE**；其余 → **PASS**。主控可按所属流程记录接受的 Warning 并有条件通过。按实际影响和强制契约裁决，不搞凑数计分，不因低收益问题延长复审。

## 10. Worked examples

### Example A — Stub caught by Q1

**承诺功能**："从数据库读取消息列表"。代码里有路由文件：

```typescript
// api/messages/route.ts:8
export async function GET() {
  return Response.json([])
}
```

```yaml
finding:
  check: Q1_stub
  severity: blocker
  location: "api/messages/route.ts:8-10"
  evidence: "GET 处理函数直接返回写死的空数组，根本没查数据库"
  impact: "接口永远返回空列表，承诺的功能实际上没做"
  fix: "连接数据库查询消息列表并返回真实查询结果"
```

### Example B — Silent behavior change caught by Q2

**Diff 改动**：为了迎合一个新调用方，把某工具函数在空输入时的返回值从 `[]` 改成了 `null`。原本的老测试没有覆盖空输入场景。

```typescript
// utils/filter.ts:12  (改动行)
if (!list.length) return null          // 原来是: return list
```

```yaml
finding:
  check: Q2_regression
  severity: blocker
  location: "utils/filter.ts:12"
  evidence: "rg 'filter\(' src/ 找到 14 处调用，其中 9 处在 diff 之外；有 3 处拿到返回值后直接调用 .map() 或 .length"
  impact: "那 3 处老调用方一旦遇到空列表，运行时会直接抛出 TypeError 崩溃，而现有测试全部显示通过"
  fix: "恢复空输入返回空数组 [] 的行为，只在需要 null 的那一个新调用方做转换；或者把全部 14 处调用点都改好并补齐空输入测试"
```

### Example C — Contract surface too large: honest scoping

某次 diff 重写了被 60 个文件引用的公共函数 `formatDate`。把 60 个文件挨个读完不现实，也会撑爆上下文。

**正确做法**：先提炼出函数的**对外约定**——参数类型、支持的输入格式、返回的字符串格式、时区处理方式，对比新旧版本有哪些差异。用 `rg -l` 列出所有调用方，按使用场景（页面展示、接口序列化、缓存 key 拼接等）挑 3–5 个代表性调用点深读。剩下的如实写进 Other notes 并说明原因。

### Example D — Circular proof caught by Q4

```typescript
// tests/parser.test.ts:14-16
const expected = parse(input)
const actual = parse(input)
expect(actual).toEqual(expected)
```

```yaml
finding:
  check: Q4_test_integrity
  severity: blocker
  location: "tests/parser.test.ts:14-16"
  evidence: "expected 和 actual 都是调同一个被测函数 parse(input) 算出来的"
  impact: "哪怕 parse 函数写错了、返回乱码，两边结果也一样，测试永远不会报错"
  fix: "把 expected 改成手写的、确定的期望结果"
```

### Example E — Duplication this diff introduced (reportable in a change review)

**Diff 改动**：本次改动新建了 `src/lib/slug.ts`（18 行）手写字符串转 URL slug 的逻辑。搜了一下项目发现 `package.json` 已经安装了 `lodash`，里面的 `kebabCase` 就能直接搞定，而且 `rg "kebabCase" src/` 显示项目里已有两个文件在用它。

```
src/lib/slug.ts:L1-18: delete/shrink: 本次新增的 18 行 slug 转换与项目已用的 lodash.kebabCase 重复。替换方案：删掉此文件，直接 import kebabCase。
```

判定为 **WARNING**（本次改动引入了与既有实现重复的逻辑）。

注意范围和时机：只有**这次改动新写出来的重复**才归变更评审管。如果项目里本来就装着 `lodash` 而两个老文件手写了 slug 转换，那属于历史遗留，留给 Repo audit，不在本次报告里出现。

### Example F — Serious logic risk only when it contradicts the design

```typescript
// src/jobs/purge.ts:18
await deleteAllUserContent(userId)
```

已证实违反必须遵守的安全或设计契约应判 Blocker，不以操作是否可逆为前提（例如设计要求软删除，代码却永久删除）。

如果设计要求就是硬删除，这不是风险，是照做。此时若评审员认为设计错了，写一条 Other notes 中的设计疑虑 说明"硬删不可逆，建议改为软删除 + 保留期"，让用户先改设计，而不是在实施评审里拦下这次交付。

## 11. Delivery-baseline scope & adversarial DESIGN/Proposal verification

### Establish the full delivery diff

```bash
# with a delivery base (preferred for multi-commit or branch deliveries):
git diff --name-status <delivery_base>...HEAD
# single uncommitted change only:
git diff --name-status
```

要专门搜的"早期漏同步"形态：用 `git log --oneline <delivery_base>..HEAD` 列出每个碰了非测试代码的提交，核对所属 `DESIGN-<module>.md` 是否在**同一交付窗口内**被改过。某模块的代码在早期提交变了、但它的 DESIGN 文档在 `<delivery_base>` 之后没有任何提交碰过——这正是 `--check-sync --base` 会拦的漏同步，即使最后一个提交是干净的也要报。

### Adversarial checklist — authorization → code (Chain 1)

| 核查点 | 方法 |
|---|---|
| 批准范围内每一项都交付 | 把 `Authorized scope` / Issue 条目 / Plan 任务逐条映射到 diff 代码块；映射不到的就是 Q1 缺交付 |
| 没有超出批准范围的夹带 | `git diff --name-status <base>...HEAD` 对照声明的文件与行为范围；未声明的文件改动或行为变化都是问题 |
| 设计忠实度 | 将重要变更契约及未改变的上层架构约束追到真实代码、调用方和测试，指出获批目标/权威依据与实际偏离；保持这些契约的内部实现自由不报问题。 |
| 明确排除项未被越过 | 提案的排除清单（如"不含布局改动"）被任何一个代码块越过 → Q1 范围违约 |

### Adversarial checklist — code → DESIGN (Chain 2)

| 核查点 | 方法 |
|---|---|
| 每处契约变化都有所属 DESIGN 同步 | 对每个变化的导出/默认值/失败边界，`rg '<符号或行为>' docs/`，确认所属 `DESIGN-<module>.md` 的 diff 里有对应更新 |
| 术语定义及同步 | 对新增或变化的领域含义，核对获批目标、已核实行为与术语表及其消费者；漏掉必需同步或生效定义冲突 → BLOCKER。遵循术语表指南，不强制简单项目建立术语表。 |
| DESIGN 语句与真实行为一致 | 把更新后的 DESIGN 文本对着代码块读；虚构行为或写了未来功能 → BLOCKER（事实失真） |
| `DESIGN Sync` 块里的声明要实测 | 复跑或抽查声称的门禁（`verify-docset.py --check-sync --base`）；对照基线、环境及输入；确认必需门禁失败则阻断交付，无法确定则披露，伪造须有证据 |
| `--pure-refactor` 理由诚实 | 对声称纯重构的文件 diff 检查有无对外可见变化（导出面、默认值、错误契约）；藏着行为变化的 → BLOCKER |
| 并行写集未越界 | 确认 diff 只碰授权写集内的 `DESIGN-<module>.md`；模块实施者改了共享主 `DESIGN.md` → BLOCKER（违反成文写集规则） |

### 现状 DESIGN → 各层级规约（第三链）

读取 `space-master` 和 `dev-doc-master` 的实际质量标准。检查受影响的项目、模块、目录、文档等规约，包括未修改但已因交付失效的规则；核查与代码、现状 DESIGN、父子级规约的一致性、全部适用的强制 SOP、语言、引用和门禁。任何不符合均为 BLOCKER。纯内部改动不强制制造文档变更。

### Proposal lifecycle verification checklist

| 核查点 | 方法 |
|---|---|
| 全交付且有用户验收才迁移 | `proposals/implemented/` 里出现该提案的前提是 diff 覆盖全部 `Authorized scope` 且迁移前已取得用户验收（提交历史、交付报告或记录本身任一可查即可）；部分交付躺在 `implemented/` → BLOCKER |
| 部分替代双向互链 | 全交付时新提案写明替代了老决策的哪些部分、老记录链回新提案；全交付时缺任一方向 → WARNING |
| 完全替代当场处置 | 老记录被吸收删除或迁入 `archived/<class>/`（带 `Archived: YYYY-MM-DD`）且发生在同一交付；都没做 → WARNING |
| 未验收的当前提案维护 | 用户明确授权的调整融入原提案；单纯漏同步 → WARNING。被替代的历史 `implemented/` 提案提前改动仍为 BLOCKER |
| 不回退、不解冻 | 任何 `implemented/` → `proposed/` 的回退，或 `archived/` 下任何内容改动 → BLOCKER |

### Severity calibration for sync failures

| 情形 | 判定 |
|---|---|
| 早期提交改了公开行为，所属 DESIGN 在整个交付窗口内未更新 | BLOCKER（事实失真，只有对着完整交付基线 diff 才看得见） |
| 真实的纯内部重构，带 `--pure-refactor` 理由，无可见契约变化 | 不报——核实理由诚实即可 |
| 声称 `--pure-refactor`，但 diff 改了导出、默认值或错误契约 | BLOCKER（纯重构声明不成立） |
| 并行实施者改了共享主 `DESIGN.md` | BLOCKER（越界） |
| 范围只交付了一部分就迁入 `implemented/` | BLOCKER（冒充全交付） |
| 全交付时部分替代的双向互链缺一边 | WARNING（提案维护缺口；若导致现状 DESIGN/规约违反质量要求则 BLOCKER） |
| 同步后的 DESIGN 措辞略欠精确但事实正确且符合质量要求 | INFO |

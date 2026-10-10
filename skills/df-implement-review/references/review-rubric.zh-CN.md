# 实施评审手册 — 模式目录与流程

四个问题背后的详细方法。某项检查需要完整流程、模式目录或实例时加载本文件。

目录：
1. [三张清单怎么建](#1-三张清单怎么建)
2. [Q1 空壳模式与探查](#2-q1-空壳模式与探查)
3. [Q2 契约面流程](#3-q2-契约面流程)
4. [Q3 缺陷目录](#4-q3-缺陷目录)
5. [Q4 测试诚信与文档漂移](#5-q4-测试诚信与文档漂移)
6. [Q4 Lean 标签](#6-q4-lean-标签)
7. [探查捆绑包](#7-探查捆绑包)
8. [能力标准门（进化提案）](#8-能力标准门进化提案)
9. [严重度校准](#9-严重度校准)
10. [实例](#10-实例)

---

## 1. 三张清单怎么建

把 diff（`git diff`、`git diff --cached`、`git show <hash>` 或 `git diff <A>..<B>`）和被改文件读一遍。不要在读和探之间来回切换——每回读一次，亏的比省的多。读的过程中填三张清单：

1. **主张**——每条交付物或验收标准（Plan 或提案的真相，或改动自己声明的意图）。
2. **契约面**——diff 改动的每个导出符号、签名、schema、共享类型、配置，外加逻辑变了但签名没变的函数。
3. **标记**——疑似空壳、接线缺口、可疑测试、虚肥候选，扫查时解决。

之后四个问题全部用定点探查消费清单。绝不重扫读过的内容。

## 2. Q1 — 空壳模式与探查

模式出现只是信号，不是判决——按"有没有主张或调用方依赖真实行为"来定性。

**注释空壳**
```javascript
// TODO: implement later
// FIXME: this is broken
// HACK: temporary
// PLACEHOLDER
// ... (逻辑该在的地方是空壳)
```
探查：`rg -n 'TODO|FIXME|XXX|HACK|PLACEHOLDER' <被改文件>`

**占位文本**
```
"placeholder"   "lorem ipsum"   "coming soon"   "under construction"
"TBD"           "Not implemented"
```
探查：`rg -ni 'placeholder|lorem ipsum|coming soon|under construction|TBD|not implemented' <被改文件>`

**空实现**
```javascript
return null   return undefined   return {}   return []
```
```python
pass   return None   return {}   return []
```
探查：`rg -n 'return null|return undefined|return \{\}|return \[\]|pass\s*$' <被改文件>`——诚实的空返回是存在的；按"有没有调用方或主张依赖真实内容"定性。

**只打日志的 handler**——只打日志或转发的函数体没有行为。逐个读 handler 体。

**假动态值**
```jsx
<div>Message 1</div>        // 应该来自 state/props
const id = "fixed-id"       // 应该是生成的
const count = 3             // 应该是算出来的
```
对照主张定性：行为必须是动态的而值是写死的，BLOCKER。

**前端空壳**
```jsx
return <div>Component</div>
return <p>Coming soon</p>
return null
onClick={() => {}}
onSubmit={(e) => e.preventDefault()}
```

**API 路由空壳**
```typescript
export async function GET() { return Response.json([]) }   // 静态，无数据源
export async function POST() { return new Response() }     // 空响应体
```

**数据库 schema 空壳**——模型缺声称行为所需的字段/关联。

**Hook / 工具空壳**
```typescript
export function useAuth() { return { user: null, login: () => {}, logout: () => {} } }
```

**每个新产物的接线检查：**
- 声明 → import 了（`rg <symbol>`）
- import → 用了（被引用，不只是存在）
- 用了 → 从入口可达（路由、渲染树、CLI、job runner）
- 组件 → 数据源：fetch 被 await、被消费、被渲染
- 状态 → 渲染：状态变量真的出现在渲染输出里
- API → 存储：查询被 await 且结果被返回，不是被丢弃
- 路由 → 注册：新路由/命令/job 在框架发现它的地方注册了

## 3. Q2 — 契约面流程

机械门禁最容易漏的。溜过去的是：无声行为变化和没测过的行为被破坏。

### 第一步——提取契约面

从 diff 列出其他代码可以依赖的每个产物：

- 导出的函数/类——签名、返回类型、抛出的错误
- 数据形状——schema 字段、JSON 响应结构、枚举值、数据库列
- 共享类型 / 常量 / 配置键
- **逻辑变了但签名没变的函数**——最危险的类别
- 测试基础设施——fixture、mock、helper（它们的改动会改变既有测试证明的东西）

### 第二步——找全部消费者

全项目 `rg <symbol>`，包括 diff 之外的文件。消费者多：`rg -l <symbol>`，抽代表性样本读，说明没覆盖什么。

### 第三步——定性破坏类型

| 破坏类型 | 找什么 |
|---|---|
| 签名变化 | 加/删参数、类型收窄/放宽、返回类型变化。类型系统抓得住大部分——但 `any`、`as` 强转、动态语言抓不住 |
| 可空性变化 | 原来永不 null（或空），现在 null；或反过来。依赖旧保证做索引/链式调用的调用方会断 |
| 同步 → 异步 | 现在返回 Promise；动态语言里没 await 的调用方无声地断 |
| 顺序变化 | 调用方依赖的数组顺序、事件顺序、迭代顺序 |
| 幂等性变化 | 重试的调用现在重复生效（或不再生效） |
| 副作用变化 | 纯函数现在写全局状态；或调用方依赖的副作用被移除 |
| 错误契约变化 | 错误码、HTTP 状态、错误消息格式变了——调用方经常解析消息 |
| 默认/行为分支变化 | 真实输入走的路径现在返回不一样的数据 |
| 性能悬崖 | 热路径 O(n) → O(n²) 就是破坏 |
| Schema 漂移 | 字段改名/删除但没迁移所有读取方；枚举值被删 |

每个消费者问一句：它依赖的是这张表里的哪条假设，还成立吗？

### 严重度

- 有具体场景的 diff 外调用点被打破 → **BLOCKER**
- 可能是故意的语义变化（Plan 决策）→ **WARNING** 或 `Serious Logic Risks`
- 消费者没查全 → `UNCOVERED STEPS`，绝不假装覆盖

## 4. Q3 — 缺陷目录

拿改动 hunks 对这些模式走一遍。只报有具体场景的 finding。

**并发与状态**
- 共享状态上的异步操作竞态
- 共享计数器/标志上的非原子读-改-写（先查后动）
- 重入：handler 没跑完又被进入（重复提交）
- 部分更新：多步变更第 2 步在第 1 步提交后失败，没有回滚
- 闭包过期的循环变量或 props

**资源生命周期**
- 打开的 handle/连接/流没有在所有路径上关闭
- 错误分支跳过清理（正常路径关了，catch 没关）
- 池化连接没还（负载下泄漏）
- 每次渲染/调用创建文件/定时器/订阅，没有 teardown

**边界与数值**
- 范围、切片、分页的差一错误
- 空集合 / 缺 key / 访问前 undefined
- 零、负数、超大值流进除法、分配、索引
- 溢出/尺寸限制：求和、计数、缓冲区

**异步**
- 缺 `await`（结果重要的地方fire-and-forget）
- 悬空 promise：rejection 无人处理
- 顺序假设：响应乱序到达覆盖新状态
- 外部调用缺超时；调用方永远挂起

**错误处理**
- 吞掉异常后带着非法状态继续跑
- 该中止的操作 log-and-continue
- 失败被报成成功（HTTP 200 带着客户端看不见的错误 payload）
- 部分失败后状态不一致；没有补偿或回滚

**类型/运行时接缝**
- 对代码没有验证过的数据做 `as`/不安全强转
- 解析后的输入没验证就当类型化的用
- 从可以合法缺失的 key 假设非空
- JSON.parse / 环境变量 / 查询参数被当成类型化的

**安全**
- 用户输入未参数化直达 SQL、shell、模板
- `innerHTML` / `dangerouslySetInnerHTML` 带任何用户可影响的内容
- 不安全反序列化（`eval`、反序列化不可信 payload）
- 请求体没验证就用；有验证但可绕过
- 新路由/handler 缺兄弟们都有的鉴权检查
- 密钥出现在代码、提交的文件、日志、错误消息里

探查：`rg -n 'eval\(|dangerouslySetInnerHTML|innerHTML|exec\(|spawn\(' <被改文件>`；每个新 POST/PUT handler 查使用前有没有验证；新路由查鉴权中间件。

## 5. Q4 — 测试诚信与文档漂移

### 测试诚信——坏模式

| 模式 | 探查 | 判决 |
|---|---|---|
| 跳过/禁用的测试 | `rg -n 'it\.skip|xdescribe|xit|@pytest\.mark\.skip|t\.Skip' <测试文件>` | 声称行为 BLOCKER |
| 循环证明 | 期望值由被测代码生成 | BLOCKER |
| 占位断言 | `rg -n 'expect\(true\)|expect\(false\)|expect\(1\)'` | BLOCKER |
| 弱断言（只验存在） | `rg -n 'toBeDefined|toBeTruthy|not\.toBeNull'` | 全弱文件 WARNING；单条弱 INFO |
| 没有断言 | `rg -c 'expect\|assert' <file>` → 零 | WARNING |
| 冗余 happy-path 测试而真分支没测 | 读测试 | 关键分支没测 WARNING |

标准：**行为坏了这个测试会红吗？** 功能删掉还能过的测试是装饰品。

### 文档漂移

改了外部契约却不同步描述它的文档，等于带着谎言发布。复用 Q2 契约面；每个变更的契约（API、schema、CLI 标志、配置键、行为语义）：

1. 找到文档位置——`rg '<symbol>' docs/ README* AGENTS.md` 和公开 docstring。
2. 查 diff 更新了这些位置没有。行为变了文档没动 → WARNING（REVISE：更新文档）。
3. 项目规则（写在 `AGENTS.md`）要求文档随代码走 → 违反即 BLOCKER，与一切成文约束同罪。

纯内部重构、无契约变化，不触发。文档在你看不到的仓库里 → `Needs Human`。

## 6. Q4 — Lean 标签

用五个标签猎虚胖。每条 finding 一行：位置、砍什么、拿什么替。**没有替换方案的 finding 是抱怨，不是 finding。**

| 标签 | 抓什么 | 替换方案 |
|---|---|---|
| `delete:` | 死代码、没人用的灵活性、投机功能 | 什么都不用 |
| `stdlib:` | 标准库本来就有的东西手写了一遍 | 点名那个函数 |
| `native:` | 依赖或代码在干平台白送的事 | 点名那个特性 |
| `yagni:` | 单实现接口、单产品工厂、没人设置的配置、只有一个调用者的层 | 出现第二个需求前先内联 |
| `shrink:` | 同样的逻辑，更短更清晰的写法 | 给出更短的写法 |

### 猎什么

- 死代码、注释掉的代码块、没用的导出和标志
- 代码里零引用的依赖（全项目 `rg <包导入名>`）——`delete:` 掉这个依赖
- 手写的重试/校验/格式化/深拷贝 helper，而标准库或已装包本来就有——`stdlib:`
- 只做转发的包装、单产品工厂、单实现接口——`yagni:`
- 同一逻辑两处各一份、砍掉一份不影响——`delete:` 或 `shrink:` 并给出存活位置
- 一行内置函数就能替代的手写循环——`shrink:` 给出更短写法

### 绝不标

- 逻辑坏了会红的那个最小检查——一个冒烟测试、一条 `assert` 自检、一个小测试文件。那是极简底线，不是赘肉。
- 信任边界上的输入校验、防数据丢失的错误处理、安全措施——永不简化掉，永不标删除。
- 口味（"换我会换个结构"）、命名、风格偏好。

### 严重度

| 情形 | 严重度 |
|---|---|
| 重复实现仓库已有基础设施——仓库已有、finding 点名 `file:line` | **WARNING**（REVISE） |
| 梯子满足不了的需求一个没有却新增重量级依赖 | **WARNING**（REVISE） |
| 死代码 / 没人用的依赖 | INFO（掩盖声称行为时 WARNING） |
| 单实现接口、投机扩展点 | INFO |
| `shrink:` 建议 | INFO |

先正确，后精简——永不拿一个换另一个。lean finding 绝不与 Q1–Q3 冲突；冲突时正确性赢，lean 想法作废。

### 那个数

报告结尾：`net: -N lines, -M dependencies possible`——把所有 finding 的现实可砍量加总。没得砍 → `Lean already. Ship.`

## 7. 探查捆绑包

读完 diff 后，对被改文件跑一遍（填上路径）：

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

diff 触碰的每个导出符号：`rg -l '<symbol>' <project>` 找消费者，包括 diff 之外的。

lean 扫查追加：`rg -n 'class |interface |factory' <被改文件>` 找抽象候选，每个新增依赖对一下它的 import 次数。

## 8. 能力标准门（进化提案）

prompt 带进化提案路径时，改动落地的是能力资产。对落地文件查平台自身的标准：

| 标准 | 查法 |
|---|---|
| frontmatter `name` + `description` | 读文件头 |
| 触发条件在 description 里 | description 说了什么时候用；正文没把触发信息埋在后段 |
| 正文 = 工作流 + 输出 + 注意事项 | 没有长篇大论、没有功能巡礼；长内容下沉到 `references/` |
| `scripts/` 只放确定性、可复用的逻辑 | 一次性片段不进 scripts/ |
| 不发明结构 | 资产结构对齐平台其他资产（没有来路不明的子目录、没有新发明的文件类型） |
| 大白话、精准 | agent 读一遍就知道该干什么；黑话和机器腔是 finding |

严重度：违反成文标准 → **WARNING**（REVISE）；资产落地后根本没法用（缺 frontmatter、引用不存在的文件）→ **BLOCKER**。

这道门是 df-proposal-review 的补充：那边查**声称的**交付物，这边查**落地的**文件。

## 9. 严重度校准

| 情形 | 正确裁决 |
|---|---|
| Handler 只打日志，声称是"处理消息" | BLOCKER（Q1 空壳） |
| 函数写得对但全项目没有调用点 | WARNING（Q1 未接线） |
| Diff 把 helper 的空输入返回从 `[]` 改成 `null`；diff 外调用方直接 `.map()` | BLOCKER（Q2） |
| 端点对原来按 4xx 分支的调用方现在返回 200 带错误体 | WARNING/BLOCKER 按严重度（Q2） |
| 声称行为的唯一测试被跳过 | BLOCKER（Q4 测试诚信） |
| `expect(true).toBe(true)` | BLOCKER（Q4） |
| 测试有一条 `toBeDefined` 加两条强值断言 | 不是 finding |
| 四行输入规范化重复、规则稳定 | 不是 finding |
| 重复校验在两个调用点已经各自漂移 | WARNING（Q4） |
| 查询执行了、结果被丢弃、返回静态 `{ ok: true }` | BLOCKER（Q1） |
| 删掉的 helper 其实还有 import（构建会抓） | 不是 finding——构建破坏归 CI |
| 两个异步写入有具体交错场景的竞态 | BLOCKER（Q3） |
| 实现能跑但违反成文设计约束（模块边界、写成"必须"的 API 契约） | BLOCKER（Q1 设计合规） |
| 改动改了文档描述的 API，diff 没动文档 | WARNING（Q4 文档漂移） |
| 新建 `retry.ts` 重复 `src/lib/http.ts:88` 已在用的退避 | WARNING（Q4 lean——重复实现） |
| `package.json` 列着 `eventsource`；`rg 'eventsource' src/` 零 import | INFO（Q4 lean——`delete:` 掉依赖） |
| `AbstractStore` 只有一个 `FileStore` 实现 | INFO（Q4 lean——`yagni:`） |
| 落地技能把触发条件埋在正文第 4 节 | WARNING（能力门） |
| 落地技能 frontmatter 缺 `description` | BLOCKER（能力门） |
| 对改动组件外观的担忧 | `Needs Human` |
| "换我会换个模块结构" | 不是 finding |

裁决备注：有 Blocker → BLOCK，否则有 Warning → REVISE，否则 PASS。数 warning 条数不是机制。

## 10. 实例

### 实例 A — Q1 抓住的空壳

**主张**："消息从数据库获取"。路由存在：

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
  evidence: "handler 返回常量；没有 consult 任何数据源"
  impact: "端点无法服务真实数据；主张在实质层面为假"
  fix: "查询存储并返回其结果，如主张所要求"
```

### 实例 B — Q2 抓住的无声行为变化

**Diff**：某工具函数空输入的返回从 `[]` 改成 `null`，为了满足一个新调用方。没有既有测试断言空输入场景。

```typescript
// utils/filter.ts:12  (改动行)
if (!list.length) return null          // 原来是: return list
```

```yaml
finding:
  check: Q2_regression
  severity: blocker
  location: "utils/filter.ts:12"
  evidence: "rg 'filter\(' src/ 找到 14 个调用点，9 个在 diff 外；3 个直接对结果 .map()/.length"
  impact: "那 3 个调用点任何一个收到空输入就在运行时抛 TypeError，而测试套件全绿"
  fix: "空输入返回空数组，在想要 null 的那一个调用方加 null 适配；或更新全部 14 个调用点并审计各自空输入场景"
```

### 实例 C — 契约面过大：诚实划界

diff 重写了 60 个文件共用的 `formatDate`。读全 60 个不是评审——是巡查。

**正确处理**：提取*契约*——签名、接受的输入、输出格式、时区行为。契约与旧版做差。`rg -l` 消费者，跨类别读 3–5 个代表性调用点（props 渲染、API 序列化、缓存键——任何可能藏着格式假设的）。其余报进 `UNCOVERED STEPS` 或 `Needs Human` 并给理由。

### 实例 D — Q4 抓住的循环证明

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
  evidence: "expected 和 actual 都来自被测的解析器"
  impact: "测试对它声称保护的行为不可能失败；任何输出、对或错，都判等"
  fix: "对手写的独立期望值断言"
```

### 实例 E — 带替换方案的 lean finding（Q4）

**Diff**：新建 `src/lib/slug.ts`（18 行）手写 slug 化。`rg 'slugif' src/ node_modules/.package-lock.json` 显示没装专门的包；但 `package.json` 列着 `lodash`，它的 `kebabCase` 就能干——而且 `rg "kebabCase" src/` 显示已有两个文件在 import 它。

```
src/lib/slug.ts:L1-18: stdlib(已装)：18 行 slug 化。lodash kebabCase 覆盖，已有 2 个文件在 import。替换：删文件，import kebabCase。
```

报 WARNING（重复实现已可用的能力）；量化贡献：`net: -18 lines`。

### 实例 F — 严重逻辑风险，仅讨论

```typescript
// src/jobs/purge.ts:18
await deleteAllUserContent(userId)
```

严重、不可逆，但可能是需求驱动的。报进 `Serious Logic Risks (Discuss with User)`；不改裁决。

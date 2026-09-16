# 实施审查参考手册 — 模式目录与流程

四个问题背后的详细方法。某项检查需要完整流程、模式目录或示例时加载本文件。

目录：
1. [三张清单怎么建](#1-三张清单怎么建)
2. [Q1 存根模式与探测](#2-q1-存根模式与探测)
3. [Q2 契约面追踪流程](#3-q2-契约面追踪流程)
4. [Q3 缺陷目录](#4-q3-缺陷目录)
5. [Q4 测试证据与技术债信号](#5-q4-测试证据与技术债信号)
6. [探针命令块](#6-探针命令块)
7. [严重度校准](#7-严重度校准)
8. [示例](#8-示例)

---

## 1. 三张清单怎么建

把 diff（`git diff`、`git diff --cached`、`git show <hash>` 或 `git diff <A>..<B>`）和变更文件读完一遍。不要在读和探测之间来回切换——每回读一次文件的成本高于它省下的探针。边读边填三张清单：

1. **声明清单** — 变更必须满足的每条交付项或验收标准（Plan 真值，或变更自身的声明意图）。
2. **契约面清单** — diff 改到的每个导出符号、签名、schema、共享类型、配置项，加上"签名没变但逻辑变了"的函数。
3. **疑点清单** — 可能的存根、接线缺口、可疑测试，留待扫描时核实。

之后四个问题只从清单取材、定向探测。已读过的内容禁止重扫。

## 2. Q1 — 存根模式与探测

模式出现是信号，不是判决——要结合上下文判断是否有声明或调用方依赖真实行为。

**注释存根**
```javascript
// TODO: implement later
// FIXME: this is broken
// HACK: temporary
// PLACEHOLDER
// ...（该有逻辑的地方是空的）
```
探测：`rg -n 'TODO|FIXME|XXX|HACK|PLACEHOLDER' <变更文件>`

**占位文本**
```
"placeholder"   "lorem ipsum"   "coming soon"   "under construction"
"TBD"           "Not implemented"
```
探测：`rg -ni 'placeholder|lorem ipsum|coming soon|under construction|TBD|not implemented' <变更文件>`

**空实现**
```javascript
return null   return undefined   return {}   return []
```
```python
pass   return None   return {}   return []
```
探测：`rg -n 'return null|return undefined|return \{\}|return \[\]|pass\s*$' <变更文件>` —— 存在诚实的空返回；判断标准是是否有调用方或声明依赖真实内容。

**只打日志的处理器** —— 函数体只 log 或只转发，等于没有行为。逐个读处理器函数体。

**写死的假值**
```jsx
<div>Message 1</div>        // 应该来自 state/props
const id = "fixed-id"       // 应该动态生成
const count = 3             // 应该计算得出
```
对照声明判断：行为必须动态而值是固定 → BLOCKER。

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
export async function GET() { return Response.json([]) }   // 静态、无数据源
export async function POST() { return new Response() }     // 空响应体
```

**数据库 schema 存根** —— 模型缺少声明行为所需的字段或关联。

**Hook / 工具函数存根**
```typescript
export function useAuth() { return { user: null, login: () => {}, logout: () => {} } }
```

**每个新产物的接线检查：**
- 声明 → import（`rg <符号>`）
- import → 使用（真的被引用，不只是出现）
- 使用 → 可达（从入口可达：路由、渲染树、CLI、任务）
- 组件 → 数据源：fetch 被 await、被消费、被渲染
- state → 渲染：state 变量真的出现在输出里
- API → 存储：查询被 await 且结果被返回，没有丢弃
- 路由 → 注册：新路由/命令/任务在框架发现机制里注册了

## 3. Q2 — 契约面追踪流程

机械门禁漏得最多的一关。类型检查抓得住编译失败，已有测试抓得住它们覆盖的东西。漏掉的是：静默行为变更，和没有任何测试覆盖的行为被破坏。

### 第一步 — 提取契约面

从 diff 列出其他代码可能依赖的每个东西：

- 导出的函数/类 — 签名、返回类型、抛出的错误
- 数据形状 — schema 字段、JSON 响应结构、枚举值、数据库列
- 共享类型 / 常量 / 配置键
- **签名没变但逻辑变了的函数** —— 最危险的一类
- 测试基础设施 — fixture、mock、helper（改了它们等于改了既有测试证明的东西）

### 第二步 — 找全消费方

`rg <符号>` 全项目搜，包括 diff 之外的文件。消费方多时：`rg -l <符号>` 列清单，抽代表性样本读，未覆盖部分明确声明。

### 第三步 — 按破坏类型分类

| 破坏类型 | 查什么 |
|---|---|
| 签名变更 | 参数增删、类型收窄/放宽、返回类型变化。类型系统能抓大部分——但 `any`、`as` 断言和动态语言抓不到 |
| 可空性变更 | 原来保证非空（或空），现在可能 null（或相反）。按旧保证索引或链式调用的调用方会炸 |
| 同步变异步 | 现在返回 Promise；动态语言里没做 await 的调用方静默坏掉 |
| 顺序变更 | 数组顺序、事件顺序、迭代顺序，被调用方依赖 |
| 幂等性变更 | 重试的调用现在重复生效（或不再生效） |
| 副作用变更 | 原来是纯函数现在写全局状态；或原来有副作用、调用方依赖它，现在没了 |
| 错误契约变更 | 错误码、HTTP 状态码、错误消息格式变了——调用方经常解析错误消息 |
| 默认值/行为分支变更 | 某真实输入的路径现在返回与以前不同的数据 |
| 性能悬崖 | 热路径从 O(n) 变 O(n²)，这也是破坏 |
| schema 漂移 | 字段改名/删除没迁移所有读者；枚举值被移除 |

对每个消费方问：它持有哪些依赖假设，现在仍成立吗？

### 严重度

- diff 之外的调用方被破坏且有具体场景 → **BLOCKER**
- 语义变了但可能是有意（Plan 拍板）→ **WARNING** 或 `Serious Logic Risks`
- 消费方没查全 → `UNCOVERED STEPS`，禁止假装覆盖

## 4. Q3 — 缺陷目录

对照这些模式过每个 hunk。只报有具体场景的发现。

**并发与状态**
- 共享状态上的异步竞态
- 非原子读改写（check 后再 act）作用于共享计数器/标志
- 重入：处理器没执行完就被再次进入（重复提交）
- 部分更新：多步变更中第二步可能失败而第一步已提交，且无回滚
- 循环变量/props 的陈旧闭包

**资源生命周期**
- 打开的句柄/连接/流不是在所有路径都关闭
- 错误路径跳过清理（正常路径关了，catch 没关）
- 池化连接未归还（负载下泄漏）
- 每次渲染或每次调用创建 file/timer/subscription 且无销毁

**边界与数值**
- 区间、切片、分页的 off-by-one
- 空集合 / 键缺失 / undefined 在访问前
- 零、负、超大值流入除法、分配、索引
- 溢出/上限：求和、计数器、缓冲区

**异步**
- 缺 `await`（结果要紧时 fire-and-forget）
- 悬空 promise：rejection 从未被处理
- 顺序假设：响应乱序到达时覆盖了更新的状态
- 外部调用无超时；调用方永久挂起

**错误处理**
- 吞掉异常后用无效状态继续前进
- 记日志后继续，但该操作必须中止
- 失败报成成功（HTTP 200 带客户端看不见的错误载荷）
- 部分失败后的不一致状态；无补偿或回滚

**类型/运行时缝**
- 对未校验数据做 `as`/不安全断言
- 未经验证的解析输入被当作已类型化
- 对可能合法缺失的键做可空性假设
- JSON.parse / 环境变量 / 查询参数被当作类型化数据

**安全**
- 用户输入未经参数化进入 SQL、shell 或模板
- `innerHTML` / `dangerouslySetInnerHTML` 承接任何用户影响的内容
- 不安全反序列化（`eval`、反序列化不受信载荷）
- 请求体在验证前使用；验证存在但可绕过
- 新路由/处理器缺了兄弟路由都有的鉴权检查
- 密钥出现在代码、提交文件、日志或错误消息里

探测：`rg -n 'eval\(|dangerouslySetInnerHTML|innerHTML|exec\(|spawn\(' <变更文件>`；检查每个新的 POST/PUT 处理器是否先验证后使用；检查新路由是否有鉴权中间件。

## 5. Q4 — 测试证据与技术债信号

### 测试完整性 — 坏模式

| 模式 | 探测 | 判定 |
|---|---|---|
| 跳过/禁用的测试 | `rg -n 'it\.skip|xdescribe|xit|@pytest\.mark\.skip|t\.Skip' <测试文件>` | 覆盖声明行为 → BLOCKER |
| 循环证明 | 期望值由被测代码自己生成 | BLOCKER |
| 占位断言 | `rg -n 'expect\(true\)|expect\(false\)|expect\(1\)'` | BLOCKER |
| 弱断言（只查存在性） | `rg -n 'toBeDefined|toBeTruthy|not\.toBeNull'` | 全文件弱 → WARNING；单个弱 → INFO |
| 无断言 | `rg -c 'expect\|assert' <文件>` 为零 | WARNING |
| 快乐路径冗余、真实分支未测 | 读测试 | 关键分支未测 → WARNING |

判据：**行为坏了，这个测试会失败吗？** 删掉功能照样通过的测试，是装饰品。

### 文档同步

变更改动了对外契约却不同步更新描述它的文档，等于交付一份谎言。复用 Q2 的契约面清单；对每个被改动的契约（API、schema、CLI 参数、配置键、行为语义）：

1. 找到描述它的文档 — `rg '<符号>' docs/ README* AGENTS.md` 以及公开 docstring。
2. 检查本次 diff 是否更新了这些位置。行为变了而文档没动 → WARNING（REVISE：更新文档）。
3. 项目在 `AGENTS.md` 里成文要求"文档随代码走" → 违反即 BLOCKER，与任何成文约束同级。

纯内部重构、无契约变化的变更不触发本检查。可见仓库之外的文档 → `Needs Human`。

### 技术债信号

只在造成真实维护成本或风险时报。

- **错误抽象层** — 什么都抽象不出来的 helper/模块，或抽象错了轴（加一行代码穿四层）
- **循环模块依赖** — A 引 B，B 引 A
- **上帝模块** — 一个文件持续承接无关职责，每次变更都在喂它
- **不对称 API** — 有 `open` 没 `close`、有 `get` 没 `set`、有 `start` 没 `stop`；调用方无法清理
- **复制粘贴已分叉** — 同一逻辑在两处，一处已经漂移；或 sort/normalize/validate 逻辑复制后每份略有不同
- **魔法数字 / 写死的环境假设** — 路径、端口、时间戳、限额内联，会无声腐烂
- **过度设计** — 为不存在的需求建的抽象、插件体系、配置面
- **死代码 / 注释掉的块** — INFO，掩盖声明行为时升 WARNING
- 项目 `AGENTS.md` 的规则与既有模式始终适用。

## 6. 探针命令块

读完 diff 后一次跑完（替换文件路径）：

```bash
FILES='<变更文件>'
rg -n 'TODO|FIXME|XXX|HACK|PLACEHOLDER' $FILES
rg -ni 'placeholder|lorem ipsum|coming soon|under construction|TBD|not implemented' $FILES
rg -n 'return null|return undefined|return \{\}|return \[\]|pass\s*$' $FILES
rg -n 'console\.log|print\(' $FILES
rg -n 'eval\(|dangerouslySetInnerHTML|innerHTML|exec\(|spawn\(' $FILES
rg -n 'it\.skip|xdescribe|xit|describe\.skip|@pytest\.mark\.skip|t\.Skip' $FILES
rg -n 'expect\(true\)|expect\(false\)|expect\(1\)' $FILES
rg -n 'toBeDefined|toBeTruthy|toBeFalsy|not\.toBeNull' $FILES
```

diff 碰过的每个导出符号，用 `rg -l '<符号>' <项目目录>` 找消费方（含 diff 之外）。

## 7. 严重度校准

| 情形 | 正确判定 |
|---|---|
| 处理器只打日志，而声明是"处理消息" | BLOCKER（Q1 存根） |
| 函数写对了但全项目没有调用点 | WARNING（Q1 未接线） |
| diff 把 helper 空输入返回从 `[]` 改为 `null`；diff 外的调用方直接 `.map()` | BLOCKER（Q2） |
| 接口现在用 200 + 错误载荷，而调用方依赖 4xx | 按严重度 WARNING/BLOCKER（Q2） |
| 声明行为的唯一测试被跳过 | BLOCKER（Q4） |
| `expect(true).toBe(true)` | BLOCKER（Q4） |
| 测试有一个 `toBeDefined` 加两个强值断言 | 不是发现 |
| 四行输入归一化重复，规则稳定 | 不是发现 |
| 重复的校验已经在两个调用点间分叉 | WARNING（Q4 技术债） |
| 查询执行了、结果丢了、返回静态 `{ ok: true }` | BLOCKER（Q1） |
| 删了仍被引用的 helper（编译能抓） | 不是发现——CI 管编译 |
| 两次异步写有具体交错导致竞态 | BLOCKER（Q3） |
| 实现能跑但违反了成文设计约束（模块边界、写明"必须"的 API 契约） | BLOCKER（Q1 设计一致性） |
| 变更改了文档描述的 API，文档在 diff 中未动 | WARNING（Q4 文档同步） |
| 变更组件的视觉效果 | `Needs Human` |
| "我会把这个模块组织得不一样" | 不是发现 |

判定规则：有 Blocker → BLOCK；否则有 Warning → REVISE；否则 PASS。数 Warning 个数不构成机制。

## 8. 示例

### 示例 A — Q1 抓住存根

**声明**："消息从数据库获取"。路由存在：

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
  evidence: "handler 返回常量；没有查询任何数据源"
  impact: "该接口无法提供真实数据；声明在『实质性』一层即失败"
  fix: "按声明要求查询存储并返回其结果"
```

### 示例 B — Q2 抓住静默行为变更

**diff**：为了满足一个新调用方，工具函数对空输入的返回从 `[]` 改成 `null`。没有既有测试断言空输入场景。

```typescript
// utils/filter.ts:12  （变更行）
if (!list.length) return null          // 原来是: return list
```

```yaml
finding:
  check: Q2_regression
  severity: blocker
  location: "utils/filter.ts:12"
  evidence: "rg 'filter(' src/ 找到 14 个调用点，其中 9 个在 diff 之外；有 3 个直接在结果上 .map()/.length"
  impact: "这 3 个调用点收到空输入时运行期抛 TypeError，而测试套件全绿"
  fix: "空输入仍返回空数组；在需要 null 的那一个调用点加适配，或同时更新全部 14 个调用点并审计其空输入场景"
```

### 示例 C — 契约面过大时的诚实裁剪

diff 重写了被 60 个文件使用的共享 `formatDate`。把 60 个文件都读一遍不是审查，是普查。

**正确处理**：提取*契约*——签名、接受输入、输出格式、时区行为，与旧版逐项比对。`rg -l` 列出消费方，按类别（props 渲染、API 序列化、缓存键——任何可能依赖格式假设的）各读 2-3 个代表性调用点。其余写进 `UNCOVERED STEPS` 或 `Needs Human` 并说明原因。

### 示例 D — Q4 抓住循环证明

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
  evidence: "期望值与实际值都来自被测 parser 本身"
  impact: "该测试不可能因声称保护的行为而失败；任何输出——无论对错——都恒等于自己"
  fix: "改用手写的独立期望值做断言"
```

### 示例 E — 严重逻辑风险，仅讨论

```typescript
// src/jobs/purge.ts:18
await deleteAllUserContent(userId)
```

严重、不可逆，但可能是需求驱动。放进 `Serious Logic Risks (Discuss with User)`；不影响判定。
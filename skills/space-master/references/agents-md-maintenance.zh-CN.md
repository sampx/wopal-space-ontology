# AGENTS.md Maintenance

创建或更新项目级、目录级 `AGENTS.md` 的权威规范。

> English: [agents-md-maintenance.md](./agents-md-maintenance.md)

## 1. When to Update

只有一次改动完成后留下的长期 Agent 行为边界，代码、测试、配置、既有文档都承载不了时，才更新。**不更新是正常结果**；不要为了走完流程而加规则。

### Document ownership

| 文档 | 负责 | 不负责 |
|---|---|---|
| DESIGN | 架构、行为契约、状态模型、业务流程 | 编码风格、CLI 输出格式、日志字段、测试入口细节 |
| AGENTS.md | Agent 实现、测试、验证时遵守的规则 | 历史、一次性决策、从 DESIGN 抄来的架构描述 |
| README.md | 人类安装、使用、能力入口 | Agent 规则、内部验证流程、实现约束 |

AGENTS.md 是 Agent 进入项目后最先读的操作文档。它必须让 Agent 不用翻源码重新找命令、风格、错误模型、输出契约、日志位置和测试 fixture，就能开始干活。

### Project standards discovery

新项目，或者 AGENTS.md 缺少操作标准的项目，先查工具链：

1. 包管理、构建、类型检查、格式化、lint 配置：实际命令和强制规则。
2. 统一错误类型、稳定字段、副作用不确定模型。
3. 输出契约：CLI 的 stdout/stderr 和退出码；服务的配置与生命周期错误；库的导出和导入副作用。
4. 日志实现、位置、轮转、记录字段、禁止内容。
5. 单元和集成测试命令、分层、fixture、契约 helper、清理；确认新增测试会被现有入口收进去。
6. 具体命令、路径、符号、格式。不要写“先搜索”“复用现有 helper”这种不点名对象的泛泛建议。

项目还没有形成惯例时，才以业界做法为基线；实际技术栈、配置和公开契约优先。

### Quality gates come before the rulebook

门禁是 Agent 不用猜、直接能跑的检查。写质量检查前，先把技术栈支持的检查做成可执行脚手架：

1. 按语言和框架选定通行的格式化工具、lint 或静态分析、类型检查、单元运行器、集成运行器。
2. 接进现有命令面（`package.json`、`Makefile`、构建脚本）。门禁必须可执行。
3. 每条准确命令写进 Quality Gates 表，带上阻断条件和失败时要看的日志或产物。
4. 能机械判定的一律自动化；人工验证只留给人、外部系统或运行时观察。

AGENTS.md 只写已安装的工具和命令。缺脚手架就先建，再写依赖它的规则。

### Standards by project type

| 项目类型 | 必须写明 |
|---|---|
| CLI | 成功与失败流、JSON/文本格式、缩进与结尾换行、退出码、help/version 例外、敏感信息脱敏 |
| 服务 / 常驻进程 | 配置归属、启动和关闭错误、健康/就绪上报、日志位置与轮转、优雅失败 |
| 库 | 公开导出、错误契约、导入纯净性、依赖边界、兼容策略 |
| UI / 应用 | 加载、空、错误、禁用状态；用户可见错误措辞；可访问性与输出一致性 |

只写适用的行，记录项目自己的选择。

## 2. Language Version and Naming Rules

- 偏好语言非英文：先写 `AGENTS.<locale>.md` 供审核；确认后才翻译进 `AGENTS.md`。
- `<locale>` 用 IETF BCP 47 / RFC 5646 标签。
- 正式英文文件不带后缀，绝不创建 `AGENTS.en-US.md`。
- 偏好语言是英文：直接更新 `AGENTS.md`。
- 偏好语言版本照抄英文模板的每个标题；只翻译正文、表格单元格、示例和解释性文字。标题绝不翻译、不改名。
- 只用 Markdown 标题层级，不加 `## 1.` 这类章节编号。
- 结构以 `templates/agent-rules.md` 为唯一真相源。

## 3. Content Boundary Rules

`AGENTS.md` 是实现、测试、验证时的操作规则。

一条规则必须同时满足：

- 跨后续任务和重构长期有效。
- 限制 Agent 的权限、职责、行为或决策边界。
- 工作时需要——日志、输出与路由、部署与发布限制、测试与验证、编码纪律——即使 DESIGN 已写细节。
- 是精简的操作规则，不是复述 DESIGN 原文；细节链接 DESIGN。
- 写明具体命令、路径、符号、格式或边界。
- 机械检查有现成工具、脚本或命令支撑。

**“DESIGN 也写了”不是省略理由。** Agent 不会每个任务都翻遍 DESIGN，日常约束必须能从规则手册直接拿到：这里写精简版，链接 DESIGN。只有当规则不增加任何 Agent 必须执行的动作时才删。

绝不写入：

- 本次改动的一次性设计决策、结构、数据模型，以及涉及的文件、函数、配置值、UI 结构或测试断言。
- 单个 Bug 记录，或唯一目的是防止该 Bug 复发的规则——做成测试。
- 全量目录、API、命令、字段或架构清单。
- 不指明已安装命令或工具的“检查”“确认”“审查”。
- 代码、配置、脚本、Plan 或文档里已有、又没附带操作指令的事实。
- 不约束决策的经验记录；那属于长期记忆。

**两种失误。** 塞太多：把一次性决策、Bug 经过或 DESIGN 原文搬进来，后来的 Agent 分不清长期规则和历史。砍太狠：因为“DESIGN 也写了”删掉工作约束，Agent 干活时没了规则可依。拿不准就保留精简版。

新增前先合并重复和过期规则。一句能说清就只写一句。链接全用相对路径：这些文件要提交并跨机器共享。Canonical References 只列强制文档（PRD、DESIGN、业务规则）；调研、教程、辅助说明属于参考资料。

### The Code Review Rules Section

- 代码项目必须包含 `## Code Review Rules`；纯文档目录可省略。
- 新项目按模板生成；更新时永久保留——绝不删除、改名或翻译标题。
- 内容只是方向性骨架：项目实际使用的审查流程、缺陷报告边界，以及写在各自项目文件里的特有检查点。

## 3.5 Document-Set Consistency

- 对照代码和权威文档审计规则（见 Rule Audit）；代码已消失或约束已由结构保证的规则，删除或修正。
- DESIGN 或 PRD 变更时，对齐 `AGENTS.md` 中与之矛盾的过期约束。
- 架构/目录章节只列现存路径；目标结构属于 Implementation Rules。

## 4. Rule Audit (Before Any Update)

先审计，不要先翻译或润色。把每条规则分类为保留、删除、修正，附上证据，并写进确认方案。

### Delete (any one suffices)

1. 引用的模块、文件或命令已不存在。用 `rg "<name>" <project>/src/` 和 `git log --all --oneline --diff-filter=D -- <path>` 验证。
2. 结构已经保证：共享常量、生成类型或 CI 检查。结构保证的规则是噪音。
3. 只是设计细节，不是工作约束：复述 DESIGN 的结构、流程或模型，不改变 Agent 行为。比“DESIGN 提过”窄得多——日志、输出与路由、部署与发布限制、测试与验证、编码纪律仍要精简保留。
4. 只是实现事实：描述代码做了什么，不约束选择。需要就去读代码。

### Keep

- 安全边界：删除范围、凭证单写入口、受保护内容。
- 行为约束：薄 handler、输出统一走单一服务、错误码约定。
- DESIGN 已覆盖也必须保留的操作约束（见 Delete 第 3 条）。
- `Code Review Rules`：标题原样，内容照常审计。
- `User-Supplied Rules`：永远不动。

### Fix

- 目录或命令清单与实际不符。
- 与更新的权威文档或设计机制冲突。
- 中英漂移：双向合并到正确内容。

### Evidence

用 `rg` 或 `ls` 查存在性，`git log --oneline` 查模块搬移或删除，对照 DESIGN 和协议文档查重复，读被引用模块判断决策边界。

## 5. Workflow

### Step 1: Resolve Target

1. 给了路径：直接用。
2. 给了项目名：定位仓库并确认推断路径。
3. 只有一个匹配：请用户确认。多个：列出候选让用户选。
4. 项目级：`<project>/AGENTS.md`；目录级：`<target-directory>/AGENTS.md`。

**产出**：目标目录、目标路径、需要确认的假设。

### Step 2: Collect Context

读目标 `AGENTS.md` 和最近的父级；相关 DESIGN（PRD 仅当存在且未并入 DESIGN；`BUSINESS_RULES.md` 仅当存在）；包管理/构建/测试/类型检查/lint 配置，含门禁命令；负责风格、错误、CLI 输出、日志、fixture 的代码——只取命令和硬约束，不搬源码百科；提供了 `rules-context` 时一并读。然后对每条现有规则执行 Rule Audit。

常见位置：

```text
<project>/docs/PRD*.md
<project>/docs/DESIGN*.md
<project>/AGENTS.md
```

**产出**：强制文档清单、审计分类、实现事实、缺失或待确认信息。

### Step 3: Draft Confirmation Plan

动笔前拿到明确确认。方案包含：

1. 目标路径。
2. 要引用的强制文档。
3. 要写入或保留的 frontmatter `name` 与 `description`。
4. 保留、新增、删除、压缩的规则及审计分类。
5. 移到 `User-Supplied Rules` 的原规则，以及建议删除的规则与理由。
6. 架构/目录方案。
7. Quality Gates 与开发/测试标准：命令、失败条件、fixture 和 helper、错误处理、CLI 输出、日志。
8. `rules-context` 合并到哪里。
9. 可能超过 300 行时的压缩或拆分策略。
10. 确认 `User-Supplied Rules` 不变。
11. 要丢弃的低信息内容：`N/A` 占位、与 DESIGN/frontmatter/全局规章重复的文字、冗长清单。
12. 每个结构条目：当前事实、长期目标约束，还是临时方案。
13. 每条被删规则：为什么不约束 Agent 工作——绝不只写“DESIGN 也写了”。
14. `Code Review Rules` 的处理（保留、生成、补检查点），或确认有意省略。

已有规则在初次创建后不可变：任何增删改都写进方案，等明确确认。

小改动（不动 frontmatter、路径、范围；1–2 个章节）可压缩为：目标、受影响章节、保留规则、增删合并、`User-Supplied Rules` 不变、结构分类。

**产出**：待确认的方案。

### Step 4: Write After Confirmation

1. 偏好语言非英文：先更新 `AGENTS.<locale>.md`。
2. 审核版确认后，翻译进 `AGENTS.md`，语义保持一致。
3. 偏好语言是英文：直接写 `AGENTS.md`；不建 `AGENTS.en-US.md`。
4. 确认前绝不写入、覆盖或重排 `AGENTS.md`。

**产出**：更新后的审核版和/或正式版路径。

## 6. Quality Checklist

- [ ] 目标路径明确或已安全推断
- [ ] 每条现有规则都已对照代码和权威文档审计；结果在方案中展示
- [ ] frontmatter `name` 与 `description` 存在；正文不重复
- [ ] `description` 单行、稳定，适合自动发现
- [ ] 存在时，已考虑目标与父级 `AGENTS.md`
- [ ] 存在时，已引用 PRD、DESIGN、`BUSINESS_RULES.md`
- [ ] 不存在的文档没有写成 `N/A` 占位
- [ ] 正文概括长期操作约束；细节链接 DESIGN
- [ ] 长期操作约束齐全：日志、输出/路由、部署与发布限制、测试与验证、编码纪律
- [ ] 风格、错误契约、CLI/输出、日志位置、禁止内容都用具体命令、路径、类型或格式写明
- [ ] Quality Gates 每行都有现存命令和阻断条件；没有任何机械检查留给文字
- [ ] 测试命令、分层、fixture、helper、运行器注册都明确
- [ ] Agent 不用翻源码重新找惯例就能实现；没有不点名的泛泛提醒
- [ ] README 没有 Agent 规则；DESIGN 没有重复的编码或测试政策
- [ ] 没有一次性设计决策或单个 Bug 记录
- [ ] 没有架构图、API 清单、命令清单或目录百科
- [ ] 架构只列现存路径；目标结构没有当成事实
- [ ] 项目级文档引用子目录 `AGENTS.md`，不复制细节
- [ ] 目标 80–150 行，硬上限 300 行
- [ ] 基本开发和测试命令保留
- [ ] 规则聚焦实现、测试、验证
- [ ] 适用时已先生成偏好语言版本
- [ ] 强制文档是引用而非复制
- [ ] 没有从 `BUSINESS_RULES.md` 抽取规则写进正文
- [ ] Testing 章节显式继承空间的 canonical testing/TDD rule；可以写明项目特有的 TDD 行为边界，但不重复通用 RED/GREEN 判定理论；项目特有命令、分层、fixture/helper、runner 注册和宿主/人工验证边界继续写清楚
- [ ] 偏好语言版本的标题与英文模板一致
- [ ] `User-Supplied Rules` 未变：无增、无改、无删、无重排，原始规范迁移除外
- [ ] 未过时的原规则都保留；删除的在方案中有理由
- [ ] 动笔前已展示完整方案并获确认
- [ ] 代码项目包含 `Code Review Rules`；标题未动
- [ ] `Code Review Rules` 引用的审查流程在本项目中确实存在
- [ ] 适用时，正式英文版已确认后更新

## 7. Response After Completion

用用户语言汇报：

1. 更新的文件与范围。
2. 关键的新增或修改规则。
3. 核对或对齐了哪些文档（DESIGN、PRD、README）。
4. 忽略的 `rules-context` 内容及原因。
5. 缺失的强制引用或假设。

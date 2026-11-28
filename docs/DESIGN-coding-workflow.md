# DESIGN — Coding Workflow

> **Status**: Active
> **Updated**: 2026-11-28
> **Parent**: `./DESIGN.md`（ontology overall design: Module Architecture section）
> **Parent Architecture**: `../../docs/products/wopal-space/DESIGN.md`
> **Parent Product**: `../../docs/products/wopal-space/PRD.md`

---

## Overview and Scope

本模块描述 coding 空间里"一项业务变更从决定到落地"的工作流能力现状：谁写决定、谁审决定、谁实施、谁验收，以及各环节的产物放在哪里、由哪个脚本把关。

已落地的能力分三层：

- **文档底座** `dev-doc-master`：产品 PRD、产品 DESIGN、项目/模块现状 DESIGN 的写作与确定性校验，是正文表达标准的**唯一**来源。
- **决定记录** `dev-proposal`：业务/项目 Proposal 的设计分析、分轮讨论、确定目标规格、批准记录、验收前授权调整维护、生命周期迁移、已实施决策的再变更分流，配套确定性校验器 `verify-proposals.py` 与薄命令 `/cupdate-proposal`。
- **实施前评审** `df-proposal-review`：对 Plan、本体进化提案、业务 Proposal、设计文档的独立只读评审，三种模式分流。

实施与实施后评审两个流程技能的**现状契约**（授权输入、隔离工作树入口、交付门禁、对抗式评审范围）也由本模块描述：

- **实施** `df-implement`：三种授权来源统一输入，`direct` 默认 `git-worktrees` 隔离实施，交付出口跑覆盖整次交付基线的机械门禁，交付报告携带必填 `DESIGN Sync` 证据块。
- **实施后评审** `df-implement-review`：对覆盖整次交付基线的完整 diff 做对抗式双向核验，文档质量标准直接引用 `dev-doc-master` 清单。

`Owned Here`：以上五个技能的状态机、目录契约、校验规则与相互路由边界；`df-implement` / `df-implement-review` 不含自有状态机，本模块只约束其输入输出契约与路由位置。

不在此模块（各自在别处拥有）：

- **Plan 编排状态机**（`dev-flow`）与本体能力进化状态机（`ontology-evolution`）——本模块只定义它们在流程里的位置与交接口，不复制其内部规则。
- `AGENTS.md` / `README.md` 治理（`space-master`）。

`Source Carrier`：`skills/dev-doc-master/`、`skills/dev-proposal/`、`skills/df-proposal-review/`、`skills/df-implement/`、`skills/df-implement-review/`、`commands/cupdate-proposal.md`、`rules/coding-workflow.md`、`assembly/archetypes/coding.yaml`。

## Usage and Interface Contracts

### 技能入口

| 技能 | 何时加载 | 命令入口 | 配套脚本 |
|---|---|---|---|
| `dev-doc-master` | 编写、更新、按模块拆分或校验 PRD、产品 DESIGN、项目/模块现状 DESIGN 及领域术语表 GLOSSARY | `/cupdate-prd`、`/cupdate-design` | `skills/dev-doc-master/scripts/verify-docset.py` |
| `dev-proposal` | 分析讨论设计、编写确定的目标规格、判断是否需要 Proposal、记录批准与 `Delivery`、迁移或归档已交付决策 | `/cupdate-proposal` | `skills/dev-proposal/scripts/verify-proposals.py` |
| `df-proposal-review` | 实施前独立只读评审 Plan、本体进化提案、业务 Proposal、设计文档 | 无独立命令，由请求方直接加载 | 复用上述两个脚本，自身不带脚本 |
| `df-implement` | 实施已批准 Proposal（`Delivery: direct`）、明确 Issue 或 Plan Task：实施代码、测试，维护 Proposal 并依次同步现状 DESIGN 与各层级规约 | 无独立命令，由请求方直接加载 | 复用上述两个校验器，自身不带脚本 |
| `df-implement-review` | 实施后独立只读评审：对照授权来源与完整交付基线 diff 核查提案目标、代码与测试、现状 DESIGN 和各级规约 | 无独立命令，由请求方直接加载 | 复用上述两个校验器，自身不带脚本 |

五个技能都随 `coding` 类型装配单分发（`assembly/archetypes/coding.yaml` 的 `skills` 与 `commands` 段）。装配单引用任一不存在的能力会让空间装配 fail closed，因此挂载与资产必须同批落地。

### `df-proposal-review` 评审契约

业务 Proposal 评审架构继承、设计确定性、契约完整性、决策、可行性与可证伪验收；Plan 评审当前授权目标的实施覆盖和任务衔接，不重复审批已认可决定；文档评审区分产品前瞻规划与项目/模块现状。提案驱动 Plan 以当前 Proposal 为目标依据，未明确变更的上层设计约束继续有效，现状 DESIGN 用于核实现有事实。既定设计内的工作按授权及适用 Active DESIGN 实施。

评审先核查实质，再复用适用机械门禁。错误方案、关键目标或验收缺失、未授权的 Plan 范围、虚假证据，以及受评审现状 DESIGN 或各级规约违反权威技能 SOP、质量要求或相互不一致，判为 Blocker；非关键验证缺口、已授权调整尚未同步提案或有证据的冗余成本判为 Warning；合理技术建议为 Info。未验证事项不冒充缺陷或已通过。

报告与实施评审采用相同的简明结构：用户偏好语言、范围与结论、问题位置、依据和影响、修正要求、验收方式；Info、积极发现和建议合计最多一两句话。评审只读，不授权实施或审批。

### `df-implement` 实施契约

实施技能不绑定 Plan 状态机，也没有自有状态机。它的现状契约：

- **授权输入**：已批准 Proposal（`Delivery: direct`，按其 `Authorized scope`）、明确 Issue、可选 Plan Task 三选一；按实际持有的授权路由，不按文件名猜来源。
- **隔离入口**：`direct` 交付默认先加载 `git-worktrees` 创建隔离工作树与功能分支再编码，严禁默认直改主分支；仅用户显式要求或主控已指派工作树时免建。隔离分支起点即 `<delivery-base>`。
- **同交付同步**：Proposal 是获批变更的唯一目标依据，未变更的既有架构及契约继续有效，Plan 组织实施。用户在测试或验证中明确授权的调整按 `dev-proposal` 优先融入当前提案。代码和测试实施验证后，调用 `dev-doc-master` 同步实际变化的项目/模块现状 DESIGN 与受影响术语表，再按 `space-master` 审查、同步和加固受影响的项目、模块、目录、文档等各级规约。纯内部改动无需制造文档变更。并行任务只改授权写集，主控协调共享成果。
- **交付出口门禁**：文档目录受 `dev-doc-master` 治理时运行 `verify-docset.py --check-sync --base <delivery-base>`（从项目工作树根目录执行，脚本路径按技能实际安装位置解析；跨多提交或独立分支必须传覆盖整次交付的基线；`--check-sync` 对所有受治理交付必开，纯内部重构以附加在 `--check-sync` 上的 `--pure-refactor "<reason>"` 免除 DESIGN 同步要求留痕待审，不能单独替代门禁）；涉及 Proposal 内容或生命周期时运行 `verify-proposals.py <proposals-root> [--link-scope <docs-dir>]...`，各级规约执行 `space-master` 的适用检查。校验失败修正成果，不修改校验器。
- **交付报告**：沿用 `Done` / `Touched` / `Verified` / `AC Commands` / `Skipped` / `Notes/deviations` 字段，必填 `DESIGN Sync` 块（Worktree / Delivery base / Gates / Docs synced / Drift report 五个子字段）；缺块或空块的报告按未完成退回。
- **边界**：实施者不 commit、不审批、不写 Plan Done、不自签验收；进行中旧 Plan 保持原有合同不被追溯改写。

### `df-implement-review` 评审契约

评审技能同样无自有状态机，只读。它的现状契约：

- **评审范围**：覆盖整次交付基线的完整 `git diff <delivery_base>...HEAD`，与交付出口 `--check-sync --base` 检查同一范围；只有单次未提交改动可直接用 `git diff`。多提交交付只审最后一个提交是评审失效的头号形态。
- **三段核验**：当前授权 Proposal → 代码及测试，代码 → 项目/模块现状 DESIGN 与术语表，DESIGN → 各级规约；检查受影响但未更新的文档/规约，核实 `DESIGN Sync` 的真实证据和 `--pure-refactor` 理由。
- **Proposal 生命周期核查**：全交付且有用户验收才迁入 `implemented/`；部分替代全交付时双向互链；完全替代当场吸收删除或归档冻结；未验收的当前提案融入用户明确授权的调整；提前改被替代的历史提案、回退 `implemented/`、改动 `archived/` 均为 Blocker。
- **质量标准**：现状 DESIGN 按 `dev-doc-master` 审核；各级规约按 `space-master` 审核，不复制两套底座的细则。
- **严重度**：单纯提案目标偏差为 Warning；真实 Bug、回归、安全缺陷、虚假证据、代码与现状 DESIGN 不一致、DESIGN 与规约或规约之间不一致，以及任一受影响 DESIGN/规约违反适用技能 SOP 和质量要求，均为 Blocker。历史保护和写集违规仍阻断。技术取舍与选型建议为 Info，不冒充缺陷。
- **报告**：Q1–Q4 检查、PASS/REVISE/BLOCK、只读与两轮收敛目标保持；默认简报使用用户偏好语言，按位置、问题、修复要求、验收组织发现，Info、积极发现和技术建议合计最多一两句话，披露未覆盖范围。

### 路由契约

`rules/coding-workflow.md` 拥有跨技能的路由边界，是技能之间的**唯一**分流权威：

- 按场景给出首选入口与明确排除项，不做能力细节的二次定义；
- 实施与评审技能（`df-implement`、`df-implement-review`）在交付出口与评审时调用两个能力底座，不复制其细则；
- 本体能力资产变更一律走 `ontology-evolution`，不走业务 Proposal。

规则的中文审核版位于 `docs/LANG/zh-CN/rules/coding-workflow.md`，两份语义保持一致，`keywords` 集合逐项相同。

## Proposal Lifecycle

业务 Proposal 的完整状态机。这是本模块的核心契约。

### 目录布局

Proposal 根目录按归属确定：

- 产品级 `docs/products/{product}/proposals/`
- 项目级 `projects/{project}/docs/proposals/`

根目录下的相对路径为 `{lifecycle}/{class}/yyyy-mm-dd-<slug>.md`：

- `lifecycle` 是闭集 `proposed | implemented | rejected | archived`，`archived/` 下没有 `implemented` 层；
- `class` 是六类闭集 `feature | bug-fix | simplification | architecture | process | testing`；
- 文件名日期取**首次提出日**，迁移与归档都不改名。

目录本身是索引：单数 `proposal/` 目录、未知分类目录、集中式 `INDEX.md` 都被校验器拒绝。

### 状态迁移

```text
proposed ──用户批准──▶ approved ──批准范围全交付且用户验收──▶ implemented ──使命完成──▶ archived
    │                       │
    └────用户否决───────────┴──▶ rejected
```

| 状态 | 位置 | 迁移条件 |
|---|---|---|
| `proposed` | `proposed/<class>/` | 文件写完即停在此态，等待用户阅读 |
| `approved` | `proposed/<class>/` | 用户明确批准；文件**留在原目录**，避免实施期内 Plan 与外部链接断链 |
| `implemented` | `implemented/<class>/` | 批准范围**全部**交付且用户验收放行；同交付把骨架改写为现在时 |
| `rejected` | `rejected/<class>/` | 用户否决；理由写进状态行 `Status: rejected — <一行理由>`，页面是否留存取决于能否防止重犯 |
| （冻结） | `archived/<class>/` | 已实施记录完成使命；`Status` 仍为 `implemented`，另加 `Archived: YYYY-MM-DD` |

不变量：

1. **不存在过程状态**。`implementing`、`verifying`、`done` 都不是 Proposal 状态；进度归 Plan 与 Issue。
2. **部分交付不迁移**。批准范围未全部交付时，文件留在 `proposed/`，`Status: approved` 不变。
3. **单个 Plan 完成不触发迁移**。Plan 的 `done`/`archive` 与 Proposal 状态无关；只有全范围交付加用户验收才迁移。
4. **格式有效不等于授权**。校验器能确认授权字段的存在与写法，不能证明有人批准过；审批是人的动作。

### 文件头字段

| 字段 | 何时必填 | 约束 |
|---|---|---|
| `Status` | 恒填 | `proposed` / `approved` / `implemented` / `rejected — <理由>`；须与所在 `lifecycle` 目录匹配 |
| `Class` | 恒填 | 六类闭集；须与所在 `class` 目录匹配 |
| `Created` | 恒填 | 首次提出日期 |
| `Approved` | `Status: approved` | 日期 + 批准人 |
| `Authorized scope` | `Status: approved` | 一句话写清批准范围与明确排除项；"全部"或多个无边界主题不算范围 |
| `Delivery` | `Status: approved` | 只允许 `direct` 或 `plan` |
| `Archived` | `archived/` 必填 | `YYYY-MM-DD`，紧贴 `Status: implemented` 下一行 |

### 正文骨架

| 生命周期 | 必填章节 | 禁用章节 |
|---|---|---|
| `proposed/`（含 `approved`） | `## Problem`、`## Design Basis`、`## Proposal`、`## Acceptance criteria` | — |
| `implemented/` | `## Problem`、`## Design Basis`、`## Decision`、`## Consequences` | `## Proposal`、`## Plan`、`## Migration plan`、`## Acceptance criteria` |
| `rejected/` | `## Problem`、`## Design Basis`、`## Proposal` | — |
| `archived/` | 不校验骨架（正文冻结） | — |

`## Design Decisions` 按需记录有长期价值的最终选择及理由。风险控制写进目标契约及验收；迁入 `implemented/` 时 `## Proposal` 改为 `## Decision`，实际验收结果及剩余代价写入 `## Consequences`，保留设计依据与重要决策。

### 交付方式

`Delivery` 由**用户**决定，Agent 不代选：

- `direct` — 跳过 `dev-flow` 拆 Plan，由 `df-implement` 默认调用 `git-worktrees` 创建隔离工作树实施。
- `plan` — 启用可选 `dev-flow` 拆解 Plan/Task，隔离工作树与共享 Delivery 由 `dev-flow` 管理。

Agent 可以陈述客观事实（涉及几个仓库、是否需要并行、是否需分批验收）帮助选择，不能以主观判断替代用户决策。

### 验收前的授权调整

已批准但未验收的 Proposal 是当前交付目标、设计决定、范围和验收要求的唯一来源。自动化实施不自行改目标；用户参与测试、验证时明确授权的新增、扩围或方向调整，优先在代码变更前融入原提案，已经实施的在交付前补齐。提案以用户偏好语言、正向肯定的目标态写作，原地替换失效内容并同步授权范围、验收、重要决策理由及剩余风险，保持状态、路径、基线不变，不重复审批。共享成果由主控协调。

### 已实施决策的再变更

已 `implemented/` 的记录是历史决定：**改事实可以，改决定不行**。

| 变更性质 | 处置 |
|---|---|
| 纯事实漂移（路径、名称、局部实现细节变化，决定未变） | 同交付原地更新 `implemented/` 的事实描述；不新建提案、不加变更日志 |
| 设计调整 / 优化 / 局部推翻 | 新建 `proposed/` 提案走独立评审与用户批准 |
| 彻底推翻 / 功能下线 | 新建提案；全范围交付时吸收删除或迁入 `archived/` 冻结 |

局部推翻的硬约束：

- 严禁把 `implemented/` 记录退回 `proposed/` 重新审批；
- 严禁原地改写成另一项决定；
- 新提案全范围交付前不得修改老记录；
- 全交付时同交付**双向互链**：新提案声明替代了哪些决策、哪些继续有效；老提案把被替代段落改成现状并链向新提案。

`archived/` 永久只读冻结：不解冻、不改写、不翻译、不重排、不删除，也不校验其出链。

## Implementation Gates

每个环节都有确定性脚本把关，语义质量另由评审负责。

### `verify-proposals.py`

纯 Python 标准库，单快照静态检查，只读。用法：

```bash
python3 skills/dev-proposal/scripts/verify-proposals.py <proposals-root> [--json] [--link-scope <docs-dir>]...
```

`<proposals-root>` 可以是 `proposals/` 本身，也可以是包含它的目录（自动下探一级）。

报告 28 个分类校验码，分五组；另有一个用法错误码 `ROOT_MISSING`（退出码 2，不进入问题列表）：

| 组 | 问题码 | 检查内容 |
|---|---|---|
| 布局 | `LAYOUT_SINGULAR_DIR`、`LAYOUT_SINGULAR_SIBLING`、`LAYOUT_INDEX_FILE`、`LAYOUT_UNKNOWN_CLASS`、`LAYOUT_UNKNOWN_LIFECYCLE`、`LAYOUT_ARCHIVED_NESTED`、`LAYOUT_BAD_FILENAME`、`LAYOUT_UNEXPECTED_PATH` | 目录树形状与命名 |
| 状态 | `STATUS_MISSING`、`STATUS_DUPLICATE`、`STATUS_UNKNOWN_VALUE`、`STATUS_REJECTED_NO_REASON`、`STATUS_PATH_MISMATCH` | 状态行唯一性与取值是否匹配所在目录 |
| 字段 | `CLASS_MISSING`、`CLASS_UNKNOWN_VALUE`、`CLASS_FIELD_MISMATCH`、`CREATED_MISSING`、`CREATED_BAD_DATE`、`APPROVAL_MISSING`、`APPROVAL_BAD_DATE`、`APPROVAL_BAD_DELIVERY`、`ARCHIVE_MISSING_DATE`、`ARCHIVE_DATE_MISPLACED` | 身份字段完整性、授权三字段与归档日期位置 |
| 骨架 | `SKELETON_MISSING_SECTION`、`SKELETON_FORBIDDEN_SECTION` | 各生命周期必填与禁用章节 |
| 链接 | `LINK_BROKEN_OUTBOUND`、`LINK_ABSOLUTE_PATH`、`LINK_SCOPE_MISSING` | 相对出链可达、无本地绝对路径（HTTP(S) URL 不参与判定）、`--link-scope` 目录存在 |

三条边界：

- **只做单快照**。不建历史数据库、不做冻结内容哈希清单、不做 Git 历史回退比对、不做跨仓库全量扫描。跨提交状态回退与归档正文篡改靠 Agent 规则与正常评审。
- **归档不查出链**。`archived/` 只校验位置、`Status: implemented` 与 `Archived: YYYY-MM-DD`；历史快照允许指向已不存在的路径。
- **统一当前格式**。所有非归档提案按当前骨架校验，`Design Basis` 必填；位置错误、根目录游离 Markdown、缺少头部元数据均失败，不跳过。归档正文保持冻结，不要求重写骨架。

`--link-scope <docs-dir>`（可重复）把引用 Proposal 的外部文档一并纳入扫描，使移动或删除造成的断链在调用方被发现。退出码 0 通过、1 有问题、2 用法错误。

回归套件 `scripts/test_verify_proposals.py` 含 91 条隔离用例，每条在临时目录自建树，不触碰真实仓库；每个可输出的问题码都有能独立失败的用例。

### `verify-docset.py`

文档集的确定性门禁；`--check-sync` 在显式开启时执行代码同步检查。可选 GLOSSARY 纳入通用结构与链接检查，存在时须在所属主 DESIGN 或 PRD 的 Companion Documents 头部登记真实目标。覆盖子文档 `Parent` 链接、孤立子文档、绝对路径、相对链接可达、末尾节重复、模板占位符、非空章节、过程态词汇、`Updated` 日期、头部字段闭集、`Status` 取值，以及可选的代码到 DESIGN 同步映射。

主 DESIGN **不要求**头部枚举 `Sub-DESIGNs`：子文档靠 `DESIGN-*.md` 文件名与 `Parent` 链接自我标识，主文档在正文（通常是 `## Module Architecture`）链接下来。脚本把"只被头部提到"的子文档报为孤立子文档。

## Data and State Model

本模块不持有运行态数据。它约束的持久状态是**文档与代码里的元信息**：

| 状态 | 位置 | 所有者 | 规则 |
|---|---|---|---|
| Proposal 生命周期 | 文件头 `Status` 行 | `dev-proposal` 契约 | 只能取四个生命周期值，须与所在目录匹配 |
| 批准与交付方式 | 文件头 `Approved` / `Authorized scope` / `Delivery` | 用户 | 只有用户批准后由 Agent 录入；格式通过不等于授权 |
| 决定归属 | `proposals/{lifecycle}/{class}/` 路径 | 目录布局 | 一项决定只有一个归属，主文档不另建索引 |
| 设计现状 | `docs/**/DESIGN*.md` | `dev-doc-master` 契约 | 只写已交付、经核实的现实；未落地方案不预写 |
| 归档冻结 | `archived/<class>/` 路径 + `Archived` 行 | 归档流程 | 冻结后字节稳定，不再接受任何内容改动 |
| 能力装配 | `assembly/archetypes/*.yaml` | 装配单 | 引用的每个技能、命令、规则、插件都必须在同一棵树里存在 |

## Business Rules and Failure Boundaries

生效规则：

1. **未落地不预写**：未交付的方案不进现状 DESIGN；提案阶段只动 `proposals/proposed/`。
2. **已实施决定不可原地改写**：任何改变默认值、边界或决策的调整都必须新建提案；事实漂移才允许原地同步。
3. **`archived/` 永久冻结**：任何内容改动（含"顺手修正路径"）都是违规。
4. **批准不可伪造**：Agent 不得代填 `Approved`、`Authorized scope`、`Delivery`；没有用户明确同意就只能停在 `proposed`。
5. **部分不冒充全部**：批准范围未全部交付时不得迁入 `implemented/`，也不得在正文声称已完成。
6. **装配引用必须解析**：装配单引用的能力缺失会让空间装配 fail closed。
7. **评审不做二次审批**：审阅已批准 Proposal 派生的 Plan 只核查实施方案与范围忠实度，不重开设计决策。

失败与恢复：

| 失败 | 表现 | 恢复 |
|---|---|---|
| 路径与 `Status` 不匹配 | 校验器报 `STATUS_PATH_MISMATCH`，退出码 1 | 按所在目录改 `Status`，或把文件移回对应目录 |
| 已实施记录被原地改写决策 | 校验器不报（单快照看不到"曾经是什么"）；由评审报 Blocker | 回退改动，改为新建 `proposed/` 提案并在全交付时双向互链 |
| 部分交付被迁入 `implemented/` | 骨架可能合法，校验器通过 | 移回 `proposed/` 并恢复 `Status: approved`，或经用户确认收窄范围 |
| 更名或删除留下断链 | 校验器报 `LINK_BROKEN_OUTBOUND` | 修好入链；外部引用靠 `--link-scope` 覆盖 |
| 归档记录缺日期 | 校验器报 `ARCHIVE_MISSING_DATE` | 补 `Archived: YYYY-MM-DD`；若已冻结则不得为补字段而解冻，需先确认归档是否真的已完成 |
| 装配引用悬空 | 空间装配 fail closed，进入不了 coding 空间 | 补齐资产或修正装配单；两者必须同批落地 |

已知边界：

- 校验器不做历史比对，因此跨提交的状态回退与归档篡改在脚本层面不可见。
- 是否值得写 Proposal 属语义判断，脚本不参与。
- `dev-proposal` 目前不调用 `dev-flow` 派生 Plan：`Delivery: plan` 是记录在案的用户决定，具体拆解由用户安排。

## Reference Documents

| Document | Purpose |
|---|---|
| `./DESIGN-capabilities.md` | 技能、命令、规则体系总览 |
| `./DESIGN-evolution.md` | 本体能力进化状态机（与本模块分流） |
| `skills/dev-doc-master/SKILL.md` | 文档底座入口与路由 |
| `skills/dev-doc-master/references/design-project-guide.md` | 现状 DESIGN 写作与审查指南 |
| `skills/dev-proposal/SKILL.md` | Proposal 生命周期入口 |
| `skills/dev-proposal/references/lifecycle.md` | 字段、迁移清单与校验器边界的完整细则 |
| `skills/dev-proposal/references/supersession.md` | 再变更分流的判断细则 |
| `skills/df-proposal-review/SKILL.md` | 三种评审模式与问题清单 |
| `skills/df-proposal-review/references/review-rubric.md` | 分模式流程、严重度校准与实例 |
| `skills/df-implement/SKILL.md` | 实施契约入口：授权来源、隔离工作树、交付门禁与 `DESIGN Sync` 报告 |
| `skills/df-implement-review/SKILL.md` | 实施后评审契约入口：完整基线范围、对抗式核验与严重度校准 |
| `skills/df-implement-review/references/review-rubric.md` | 评审排查细则：基线范围程序、DESIGN/Proposal 核查清单与严重度标尺 |
| `commands/cupdate-proposal.md` | Proposal 薄命令入口 |
| `rules/coding-workflow.md` | 跨技能路由与禁止越界 |
| `assembly/archetypes/coding.yaml` | coding 类型装配单 |

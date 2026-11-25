---
name: dev-proposal
description: |
  编写与维护业务/项目 Proposal：判断某项改动是否需要提案、起草正文、记录用户批准与 `Delivery: direct | plan`、在 proposed/implemented/rejected/archived 之间迁移，以及处理已实施决定的后续变更。

  使用场景：用户要求新建、修订、批准、迁移、归档或演进一份 Proposal。

  不适用：既定设计内的普通缺陷与任务（用 df-implement）、对 Proposal/Plan/DESIGN 的独立只读评审（用 df-proposal-review）、PRD/DESIGN 写作（用 dev-doc-master）、本体能力进化提案（用 ontology-evolution）、编排开发 Plan（用 dev-flow）。
---

# dev-proposal — 业务 Proposal 生命周期

**你只做一件事：让一项重要设计决定有据可查、有主可问、有期可守。**

Proposal 记录的是**决定**：为什么做、选了哪条路、放弃了什么、什么算完成、代价是什么。它不记录执行进度，也不是现状文档。执行进度归 Plan 与 Issue，已交付的系统行为归项目/模块现状 DESIGN。

## 什么时候必须有 Proposal

出现下面任一种情况时，写 Proposal：

- 需要在多条可行路径之间做选择，而且选择理由无法从代码读出来；
- 改变已生效的默认值、边界、权限、失败语义或对外契约；
- 推翻或部分推翻一份已 `implemented/` 的决定；
- 影响多个项目、多个模块的共同约定，或需要用户重新拍板范围。

只有下面全部成立时，才**不**写 Proposal：

- 属于既有决定范围内明确的任务或缺陷；
- 一条 Issue 或一次直接实施就能说清范围与验收；
- 不需要用户在设计层面重新选择。

普通 Bug、样式微调、机械改名、纯内部重构一律走 Issue 或直接实施。**Proposal 不是开发动作的仪式**：为了"看起来规范"而给每个改动套一份 Proposal，只会制造没人读的档案。

同一主题已有 Proposal 时，先审计再动笔：能原地同步事实就不新建，需要改决定就新建并互链，详见下文「已实施提案的再变更」。

## 目录与状态机

### 布局

Proposal 根目录按归属确定：

- 产品级：`docs/products/{product}/proposals/`
- 项目级：`projects/{project}/docs/proposals/`

根目录下是两轴路径 `{lifecycle}/{class}/yyyy-mm-dd-<slug>.md`：

```
proposals/
├── proposed/<class>/
├── implemented/<class>/
├── rejected/<class>/
└── archived/<class>/
```

- `lifecycle` 闭集：`proposed | implemented | rejected | archived`。`archived/` 下**没有** `implemented` 这一层。
- `class` 闭集（六类，不得自创）：`feature | bug-fix | simplification | architecture | process | testing`。
  - `feature`：新增面向用户或模型的能力。
  - `bug-fix`：修正缺陷，或补上复盘暴露的缺口。
  - `simplification`：删除代码、行为或表面，不新增能力。
  - `architecture`：关于已交付源码的结构性决定——模块如何关联、运行时词汇是什么。
  - `process`：围绕代码的工具、策略与工作流，不是运行时行为。
  - `testing`：测试基础设施与策略。
- 文件名 `yyyy-mm-dd-<slug>.md`：日期取**首次提出**该主题的日期（以 Git 历史为准），slug 用小写 kebab-case，2–4 个词。
- **禁止**单数 `proposal/` 目录、未知分类目录、集中式 `INDEX.md`。目录本身就是索引；`INDEX.md` 会与所有无关改动争抢同一个文件。
- 存量前格式文件（旧路径、旧命名）保持历史只读兼容：可以读、可以引用，不强制迁移，也不要按新规则去改它。

### 状态机

```text
proposed ──用户批准──▶ approved ──全范围交付且用户验收──▶ implemented ──使命完成──▶ archived
    │                       │
    └────用户否决───────────┴──▶ rejected
```

| 状态 | 位置 | 含义 |
|---|---|---|
| `proposed` | `proposed/<class>/` | 已写好在等用户读，未获授权 |
| `approved` | `proposed/<class>/` | 用户已批准并授权范围；**文件留在 `proposed/`**，避免实施期内 Plan 与链接断掉 |
| `implemented` | `implemented/<class>/` | 批准范围全部交付并经用户验收放行 |
| `rejected` | `rejected/<class>/` | 用户否决，状态行写明一行理由 |
| （冻结） | `archived/<class>/` | 已完成使命、不再指导日常工作的 `implemented/` 记录，`Status` 仍为 `implemented`，另加 `Archived: YYYY-MM-DD` |

硬性约束：

- **绝不引入 `implementing` / `verifying` / `done` 这类过程状态**。Proposal 没有执行进度；进度归 Plan 与 Issue。
- 部分交付**不迁入** `implemented/`：文件留在 `proposed/`，`Status: approved` 不变。是否部分交付由交付证据说明，不靠状态猜。
- 单个 Plan 完成或归档**不会**自动把 Proposal 变成 `implemented`。只有批准范围全部交付并经用户验收，才由 Agent 在同一交付内迁移。
- 未获用户明确批准，不得写 `approved`；未获验收放行，不得写 `implemented`。**格式校验不能伪造审批**——脚本通过只说明写法合规，不代表有人批准过。

### 文件头契约

```markdown
# <标题>

Status: proposed

- **Class**: architecture
- **Created**: 2026-11-22
```

`Status` 是第三行，取值 `proposed`、`approved`、`implemented`，或 `rejected — <一行理由>`。状态行不带日期、不带括号补充；日期在文件名与 `Created` 字段，其余事实在 Git 里。

批准后追加三条，缺一不可：

```markdown
- **Approved**: 2026-11-22 — <批准人>
- **Authorized scope**: <一句话说清批准了什么，包含明确排除项>
- **Delivery**: direct | plan
```

归档时在 `Status: implemented` 正下方插入 `Archived: YYYY-MM-DD`，这是归档唯一允许的内容改动。

### 正文骨架

`proposed/`（含 `approved`）用未来时骨架：

```markdown
## Problem
## Proposal
…（按需的专属章节：接口、迁移、取舍分析等）…
## Alternatives considered
## Acceptance criteria
## Risks
```

`implemented/` 用现在时骨架：

```markdown
## Problem
## Decision
…（按需的专属章节）…
## Alternatives considered
## Consequences
```

迁移到 `implemented/` 时**同一交付内机械改写**：`## Proposal` → `## Decision`，`## Acceptance criteria` 与 `## Risks` 合并进 `## Consequences`（代价与收益都写）。`implemented/` 中**禁用**计划期标题：`## Proposal`、`## Plan`、`## Migration plan`、`## Acceptance criteria`。

`rejected/` 保留提议期正文与原本章节（可以有 `## Acceptance criteria`），结论只写在状态行。

`## Alternatives considered` 在四种生命周期里都必填。每条写清"是什么方案、为什么输"。**备选方案只记录真实考虑过的**，不凭空补写；早于本格式的存量文件不追溯。

正文表达规范——清晰度、术语一致、去 AI 味、`Source Carrier`、实测取证——直接引用 `dev-doc-master`（含 `references/design-project-guide.md`），本技能不重复抄写。Proposal 阶段**不动现状 DESIGN**：未落地的设计不许预写进 `DESIGN.md` 或 `DESIGN-<module>.md`。

## 交付方式：由用户显式决定

`Delivery` 只有两个值，且**必须由用户决定**，Agent 不得代选：

- **`direct`** — 跳过 `dev-flow` 拆 Plan。由 `df-implement` 默认调用 `git-worktrees` 创建隔离工作树实施，**不默认直接在主/集成分支上开发**。适合范围清楚、单点收口、无需多任务并行的交付。
- **`plan`** — 启用可选 `dev-flow` 拆解 Plan/Task，隔离工作树与共享 Delivery 由 `dev-flow` 管理。适合跨项目、多交付物或需要并行写集的交付。

Agent 可以把**客观事实**摆到用户面前帮助选择：涉及几个仓库、是否需要并行、是否要中途分批验收。**严禁**用"这个模型够强/不够强""这个任务复杂/简单"之类的主观判断替用户选路。

新增决策或实质改变授权范围，必须重新获得用户确认；旧批准不覆盖新范围。

## 工作流

1. **判定必要性**：按上文三条门槛确认这次改动需要 Proposal。不需要就转 Issue 或直接实施，并说明理由。
2. **起草前审计**：在对应 `proposals/` 根目录下搜索同主题的活跃与已实施记录。命中的处理见「已实施提案的再变更」。
3. **写文件**：从 `templates/proposal-proposed.md` 复制骨架到 `proposed/<class>/yyyy-mm-dd-<slug>.md`，填满 `## Problem`、`## Proposal`、`## Alternatives considered`、`## Acceptance criteria`、`## Risks`。验收标准要能被第三方判断"达成/未达成"。
4. **等用户读**。文件写完即 `Status: proposed`，不自行推进。
5. **记录批准**：用户明确同意后，补齐 `Approved`、`Authorized scope`、`Delivery` 三条，状态改为 `approved`，文件位置不变。
6. **创建交付分支或工作树前，先提交已批准的 Proposal**：在集成分支上单独提交这次 Proposal 变更，再从该提交开始交付，让已批准的记录进入交付基线。这个提交只包含 Proposal 变更。
7. **交付**：按 `Delivery` 分流。交付过程中把 Source、关联 Plan、实际提交与评审验收证据链在 Proposal 里（链接即可，不复制进度表）。
8. **全范围交付且用户验收后迁移**：移动到 `implemented/<class>/`，改 `Status: implemented`，同交付机械改写骨架为现在时（`Decision` / `Consequences`），并同步受影响的现状 DESIGN。
9. **否决时**：判断这份否决理由是否能防止**将来有人再犯同样有诱惑力的错误**。能——移入 `rejected/<class>/` 并把理由写进状态行；不能——整份删除，并修好所有入链。
10. **归档清理**：`implemented/` 中已完成使命、不再指导日常工作的记录移入 `archived/<class>/`，插入 `Archived: YYYY-MM-DD` 后永久冻结。微小的 UI 调整或纯机械变更不归档，直接删除并修好入链。

每一步都要跑一次校验（路径相对本技能目录）：

```bash
python3 scripts/verify-proposals.py <proposals-root>
```

退出码 0 才算写法合规；脚本只查单快照的静态事实，设计质量仍由评审与用户判断。

## 已实施提案的再变更

这是本技能最容易出错、也最值得记住的部分。**已 `implemented/` 的提案记录的是历史决定；改事实可以，改决定不行。**

先判断这次改动属于哪一类：

| 类别 | 判据 | 处置 |
|---|---|---|
| **纯事实漂移** | 原决定、边界、默认值都没变，只是路径挪了、名字改了、局部实现细节变了 | 在同一交付内**原地更新** `implemented/<class>/` 的事实描述。直接改成现状，不新建提案，不加变更日志。 |
| **设计调整 / 优化 / 局部推翻** | 需要改变原决定、核心默认值或边界；需要用户重新拍板（哪怕嘴上叫"优化"或"局部增强"） | **新建** `proposed/<class>/yyyy-mm-dd-<slug>.md`，走独立评审与用户批准。 |
| **彻底推翻 / 功能下线** | 原决定整体失效，新的替代它 | **新建**提案；全范围交付时当场处置老提案（见下）。 |

第二条的硬约束：

- **严禁**把已 `implemented/` 的提案退回 `proposed/`，也严禁把它原地改写成另一项决定。历史决定被改写，读者就再也看不到"当初为什么这么选"。
- 新提案在**全范围交付前不得修改**老的 `implemented/` 提案。
- 新提案迁入 `implemented/` 时，**同交付双向互链**：新提案写明部分替代了老提案的哪些决策、老提案哪些决策继续有效；老提案把被替代的段落改成现状并链向新提案。

第三条的硬约束：全范围交付时**当场**处置老提案，不等日后大扫除。二选一：

- **吸收后删除**——把老提案里仍然独特的理由、备选方案、代价、验证方式与遗留缺口全部保留进新提案，修好所有入链，然后删除老文件；
- **迁入 `archived/<class>/` 永久冻结**——老提案仍有独立历史价值时选这条。

**`archived/` 永久只读冻结**：不解冻、不改写、不翻译、不重排、不移动、不删除，也不核查它的出链。后续演进只能新建活跃提案，必要时把它当历史背景引用。

## 诚实边界

- 本技能只负责 Proposal 的写作、批准记录、迁移与冻结。它**不执行实施**，也不替用户批准。
- 当前工作流引擎还不能从 Proposal 直接派生 Plan/Task。在 `dev-flow` 支持之前，**不要假装或自动调用不存在的 Proposal→Plan 命令**；`Delivery: plan` 目前是记录在案的用户决定，具体拆解由用户安排。
- 独立评审由 `df-proposal-review` 承担。本技能写，它审；不要自己给自己发通行证。

## 参考

- 状态机、字段与迁移细则：`references/lifecycle.md`
- 再变更分流与替代合并的判断细则：`references/evolution-triage.md`
- 骨架模板：`templates/proposal-proposed.md`、`templates/proposal-implemented.md`
- 静态校验器：`scripts/verify-proposals.py`
- 正文表达规范：`dev-doc-master`（`references/consistency.md`、`references/design-project-guide.md`）

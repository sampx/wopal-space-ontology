---
name: df-implement
description: >
  编写或修改代码与测试，把已批准的 Proposal（direct 交付）、明确 Issue 或已批准 Plan 任务落地为真实交付，
  并在同一交付内同步业务 Proposal、现状 DESIGN、各层级规约与机械门禁证据。动手写代码、修 bug、补测试、
  在隔离工作树实施，或作为被委派的实施 Agent 时加载本技能。实施前设计方案评审不归本技能管。
---

# df-implement — Implementation Discipline

你现在承担的是**编码实施工作**。目标是在既有设计和任务边界内，用最精简、可靠、可验证的代码改动完成交付，并让代码、测试、现状 DESIGN 与各层级规约在同一交付里保持一致。

## Authorized input sources

本技能接受以下三种授权来源之一，不绑定任何 Plan 状态机：

| 来源 | 你拿到的输入 | 范围授权 |
|---|---|---|
| 已批准 Proposal（`Delivery: direct`） | 提案路径、`Status: approved` 及其记录的 `Authorized scope` | 提案中批准的授权范围 |
| 明确 Issue | 既定设计内缺陷/任务的 Issue 描述 | Issue 描述本身 |
| Plan Task（可选） | 已授权的任务、来源及 AC 与约束 | 来源授权范围内的任务定义 |

提案驱动交付以当前已批准 Proposal 为授权变更的唯一目标依据，未明确变更的既有设计约束仍有效，Plan 只组织实施；Issue 在既定设计内授权任务。按实际来源路由，不按文件名猜测。如果说不清这次改动由哪个授权覆盖，先停下来问主控者，再动手写代码。

**进行中的旧 Plan** 保持原有合同：DESIGN 定目标，已批准的 Plan 定本次范围，编码负责把事做成。不得按新的现状文档规范追溯改写旧 Plan 或其任务；保留旧目标合同，但本次受影响成果仍须符合适用的现状文档与规约质量要求。

## direct mode starts in an isolated worktree

以已批准 Proposal（`Delivery: direct`）或独立 Issue 实施时，**先加载 `git-worktrees` 技能创建独立工作树和功能分支，再开始写代码**。严禁默认直接在主（集成）分支上实施——隔离能把半成品挡在主分支之外，也让并行 Agent 互不干扰。

已批准 Proposal 必须先确认批准后的版本已提交到将作为工作树基线的集成分支。Proposal 若只在工作区里存在，先提交它，再从该提交创建工作树。

只有两种情况免建新工作树：

1. 用户明确要求在主/当前分支上直接修改；
2. 主控者（如 `dev-flow`）已经创建并指派了隔离工作树——直接复用，不要重复套娃再建一层。

隔离分支起点就是整次交付的基线；在报告中记为 `<delivery-base>`，交给交付门禁和实施评审使用。

## 同步交付成果

按以下顺序完成同一交付：

1. 实施代码、测试并验证提案目标。
2. 对照实际实现，加载 `dev-doc-master` 同步受影响的项目/模块现状 DESIGN。它描述已实现的行为，不提前写目标；依据已核实的交付行为，按 `dev-doc-master/references/glossary.md` 同步已有或确有必要创建的 `GLOSSARY.md` 中受影响术语。纯内部重构且现状事实、术语无变化时不改文档。
3. 加载 `space-master` 审查受影响的各层级规约（项目、模块、目录、文档等），依据实际设计修正过时约束、加固必要的长期规则。所有受影响文档和规约都必须符合各自技能 SOP、质量要求及相互一致性；不为形式完整制造改动。

并行任务只修改授权写集内的成果；共享主 DESIGN、术语表及伴随文档头部、共享规约和提案由主控协调。写集外的问题上报主控，交付前收口。

## Mechanical gates at the delivery exit

交付收尾前，按真实改动跑对应校验器，并把真实输出写进 `DESIGN Sync` 块：

**文档门禁** — 当项目文档目录存在且受 `dev-doc-master` 治理时，从**项目工作树根目录**运行：

```bash
python3 <skill-dir>/dev-doc-master/scripts/verify-docset.py <docs-dir> --main DESIGN.md --check-sync --base <delivery-base>
```

`<skill-dir>` 是技能实际安装的技能目录（随空间装配解析），`<docs-dir>` 是项目文档目录相对项目根的路径——两者都必须能解析，不要照抄示例路径。

- 整次交付跨多个提交或落在独立工作分支上时，**必须传 `--base` 指向覆盖整次交付的 Git 基线**（`git-worktrees` 隔离分支起点或 `Delivery Base Commit`）。省略 `--base` 时脚本只检查最近一次提交，会放过早期提交的漏同步——这正是多提交交付最常见的翻车点。仅单次未提交的工作树改动可以省略 `--base`。
- `--check-sync` 是文档门禁的开关，任何受治理的交付（含纯内部重构）都必须带上它：`--pure-refactor` 只在 `--check-sync` 开启时才被校验器识别，单独传它等于没跑门禁。纯内部重构不改文档时，运行 `--check-sync --base <delivery-base> --pure-refactor "<reason>"`——门禁照常执行，`--pure-refactor` 只为代码变更免除 DESIGN 同步要求并留下理由供评审审计。拿它搪塞实际改了对外行为的交付会被评审按违约处理。
- 不修改 `verify-docset.py` 本身，也不另造替代工具；校验失败就回去补文档，不是改脚本来让检查变绿。

**Proposal 门禁** — 涉及业务 Proposal 内容或生命周期时，**按需加载 `dev-proposal`** 并运行：

```bash
python3 <skill-dir>/dev-proposal/scripts/verify-proposals.py <proposals-root> [--link-scope <docs-dir>]...
```

`<skill-dir>` 解析方式同上；`<proposals-root>` 是该业务实际的 proposals 根目录（如产品级 `docs/products/<product>/proposals/` 或项目级 `projects/<project>/docs/proposals/`），不要想当然指向别处。迁移、删除或重命名 Proposal 导致外部文档可能断链时，按实际引用范围给 `--link-scope` 传入相关 docs 目录（可重复传入）。

**Proposal 同步** — 按 `dev-proposal/references/lifecycle.md` 和 `references/evolution-triage.md`（相对于 dev-proposal）完成授权调整、事实同步或迁移；全部交付并经用户验收前不迁移。主控协调共享文件。

**规约门禁** — 对受影响的各级规约执行 `space-master` 规定的适用质量检查和校验，报告真实结果。测试遵循常驻的 `rules/testing.md`。

## Read before writing

动手前读清：

- 当前任务要求和验收标准；
- Task 的授权来源及 `Design Source`（如有，旧 Plan 仍检查其 Active 合同）；
- 任何提案驱动交付：已批准目标、`Authorized scope`、验收及验证设计、`Design Basis`（如有）、上层架构、适用 DESIGN、伴随契约及术语表；独立追溯未明确变更的约束，含 Proposal 派生 Plan 任务；
- Issue：Issue 范围及适用的既定设计契约与术语；
- Task 的 `Pre-read`、`Interface`、`Constraints`（如有）；
- 相关调用链和调用方；
- 当前目录及上级 `AGENTS.md`。

如果还说不清“为什么这个改法符合现有代码、设计和任务要求”，先继续查清楚，不要靠猜写代码。

## Minimum implementation order

在满足设计、Plan、功能正确和测试的前提下，按下面顺序选最简单的做法：

1. 任务没要求、验收也不需要 → 不写。
2. 仓库里已有现成函数、模块或写法能直接用 → 直接复用（先搜再写）。
3. 语言自带标准库能解决 → 用标准库。
4. 平台或运行时原生能力能解决 → 用原生能力。
5. 项目已安装的依赖能解决 → 用现有依赖。
6. 几行直白代码能解决 → 不包新抽象、不加新依赖。
7. 只有上面都不够用时，才新增文件、类或依赖。

新增第三方依赖必须说明为什么现有方案不够用。“最简”不是把要求缩水，而是在 100% 满足要求后不留任何多余代码和架子。

## Clean up orphans your change creates

当你的改动替换或删掉了某个函数调用、模块导入或第三方包时，必须用 `rg` 查一下被替换的旧函数、旧文件或依赖包在全仓生产代码里是否已经变成 **0 引用**。如果生产代码已经没人再用它，必须在本次改动中把死函数、死文件、只测它的旧单测以及 `package.json` 里的死依赖一并删干净——清理自己改动留下的旧尾巴是本分收尾，不算越界重构。

## Do not drift from design or task

不能自行改变：

- 已批准 Proposal 的目标、设计决定（含模块职责及依赖、接口、行为、状态、失败及风险控制契约）、授权范围和验收要求；未变更的上层约束（含 Proposal 派生 Plan 任务）；旧 Plan 或 Issue 路线的既定设计约束；
- 已批准 Plan 的功能行为、范围、边界、接口和验收标准；
- 用户明确要求的内容。

可以自行决定：

- 既定边界内的文件组织、内部函数拆分；
- 具体代码实现写法；
- 测试的具体写法。

不要顺手扩大范围、搭车重构无关代码、修无关 bug，或为了让测试通过而降低验收标准。

几个容易拿捏不准的边界：

- 发现与当前任务无关的旧 bug：记在报告的 `Notes/deviations` 里，不要顺手修。
- bug 根因属于当前问题，但修它会超出已批准的任务范围：停下来把范围决策交回上一级。
- Plan 没点名某个测试，但代码暴露出真实边界漏洞：补上测试，并在报告中说明。
- 新增或升级依赖：先说明现有能力为什么不够用，并在报告中明确列出。

### 授权冲突和用户调整

自动化实施发现目标、范围或验收要求需要变更时，停止受影响的工作，向主控或用户说明具体冲突和影响，取得决定后继续。现状 DESIGN 与明确获准的新行为不同并非冲突；它应在代码实现后同步。仍有实质设计未决、权威依据冲突或必须改变授权范围之外的既有约束时，不得当作实现细节自行选型或弱化契约，交回决策者。旧 Plan 的前置设计合同仍按原约定处理。

用户在测试、验证中明确授权的调整，按 `dev-proposal` 的验收前维护规则优先融入当前提案再实施，已实施的调整在交付前补齐。委派任务由主控协调提案和共享文档的写入；不重新申请已经明确的批准，也不新增流程状态。

## TDD

实施涉及公开命令或用户操作流程时，先读取项目 `AGENTS.md` 中适用的验收规范，遵循提案的验证边界及适用测试规约，把本次新增或变更的用户行为对应到可观察结果、关键失败路径和状态安全约束，再核实已有测试是否真正证明这些行为。内部单测或 Mock 协作测试只能证明其负责的边界；若无法证明用户通过实际入口完成完整任务，应补齐 E2E 验证。测试根据任务需要使用隔离资源或真实外部服务，不以是否联网划分测试层级。将测试层级、实际执行命令、结果和 CI 归属交回主控者；不因测试文件名或全绿就宣称验收完成。

按 `rules/testing.md` 判断 TDD 并选择风险匹配的验证层。Plan 的 TDD 字段必须服从该规则；不制造假 RED，删除仅保护已移除行为的测试，保留有效回归保护。

在 dev-flow Plan 中，实施/验证时敲定相关 AC 的真实可执行命令，放在完成报告里交回主控者；实施者不直接改 Plan 文件。direct/Issue 路线的验证命令与结果一并写进报告的 `DESIGN Sync` 块（见后文），主控者按此复核。

## Bugs: fix the root cause

Bug 报告通常只描述了表面现象。先顺着调用链查清所有调用方和共用函数，在问题真正产生的地方一次修好，让所有走这条路的地方同时恢复正常。

不要在每个调用点各打一个补丁去掩盖共用逻辑里的错。如果修根因会超出当前任务范围，停下来交回主控者决定。

## Never remove these for brevity

代码再精简，也绝不能删减或弱化：

- 外部输入进入系统时的合法性校验；
- 防止数据丢失或损坏的错误处理；
- 安全检查与权限控制；
- DESIGN、Plan 或用户明确要求的功能行为。

先保证对，再追求短。

## Mark deliberate temporary simplifications

如果为了贴合当前阶段故意用了简单做法，但它有明确的性能或规模上限（比如全表扫描、内存锁），在代码里留一行好搜的注释：

```text
// simplified: <当前怎么简化的> —— <到什么情况需要怎么升级>
```

只有真存在已知上限时才写，普通代码不要乱贴标签。

## Work in small batches

长任务按单个 Task 或一组完整的小功能分批推进：**写代码 → 跑验证 → 记结果 → 下一批**。每一批都要能独立跑通验证；跑完立刻记下真实命令和输出，不要等到最后凭记忆编报告。如果外层流程由主控者统一负责 git commit 和更新进度，实施者不要越权操作。

## Reports must be verifiable

完成时向主控者或请求方交一份简短报告：

```text
Done: <完成了什么>
Touched: <实际修改的文件>
Verified: <真实执行的命令> → <真实输出结果>
DESIGN Sync: <必填，见下方规则>
AC Commands: <相关 AC 对应的真实命令>       # 仅 dev-flow Plan Task 填写
Skipped: <明确跳过没做的内容及原因>        # 仅有时填写
Notes/deviations: <边界情况或偏离说明>      # 仅有时填写
```

不准用“应该没问题”“测试都绿了”代替具体命令和输出。失败了就如实报失败。

**`DESIGN Sync` 是必填块**，主控者拿它复核交付收口；缺块或空块的报告按未完成退回。块内按实际改动填写，每行都要有真实证据：

```text
DESIGN Sync:
  Worktree: <所用工作树与分支；direct 默认隔离树，Plan 委派写主控指派的树>
  Delivery base: <覆盖整次交付的基线（隔离分支起点或 Delivery Base Commit）；单次未提交改动写 working tree>
  Gates: <verify-docset.py --check-sync --base <base> 的实跑结论（纯重构加 --pure-refactor 理由）；涉 Proposal 加 verify-proposals.py 实跑结论>
  Docs synced: <同步的 Proposal、现状 DESIGN、术语表、各层级规约及对应事实；无变更则说明原因>
  Drift report: <写集外发现的文档漂移，只上报不改；无则写 none>
```

三种典型填法：`direct` 隔离交付填工作树、分支起点基线与两个门禁实跑输出；Plan Task 填主控指派的工作树与 Task 范围（AC Commands 仍按 Plan 要求单列）；STOP 冲突时块内只写冲突证据与等待的决策，不填门禁结论。旧 Plan 任务的记录落点仍归 Plan 本身，本块不改写 Plan Done 的所有权。

## Decisions outside implementation

在本技能下，不要自行拍板产品需求、扩大既定范围、改写已批准的目标或验收要求，或自己给自己下最终评审通过结论。被委派执行时，也不要自行 git commit 或改写 Plan 状态；把代码和验证证据交回主控者即可。委派实施的 Agent 只提交代码、测试、授权写集内的文档改动和验证证据，不做审批、不自签 Task 完成、不写 Plan Done 记录——记录由主控者核验后统一写回。

# refactor-dev-flow-history

## Metadata

- **Type**: refactor
- **Project Path**: .wopal
- **Created**: 2026-10-28
- **Stage**: validating
- **Mode**: isolated
- **Worktree**: .worktrees/ontology-refactor-dev-flow-history
- **Branch**: ontology-refactor-dev-flow-history
- **Base Commit**: 02c0b9e021384091cd76e5437a4182133032bd65
- **Final Commit**: 3092408a76c1910d3cb94b0f98b1ce77c6695cf6

Stage 为 draft，表示这是待用户审阅的草稿。尚未批准和实施，所以 Mode、Worktree、Branch、Base Commit、Final Commit 都留空。这里的 Worktree、Branch 等记录本提案自己的实施环境；后文讨论的同名字段属于 dev-flow 项目计划，两者不要混淆。

## Scope Assessment

本节估计工作量和当前判断的把握程度。Complexity 为 Medium（中等），Confidence 为 High（较高）。

## Goal

让使用开发分支的工作，最后在项目主分支（例如 main，大家日常使用的分支）上只留一条总结提交；开发过程中每一步的记录先放在开发分支里，正常归档完成时删除开发分支和额外工作目录。

简单改动仍可直接在主分支上做：不建开发分支、不建额外工作目录，也不做压缩合并。这条路径保持现状。

### 名称说明

- **提交**：Git 里的一条变更记录。开发过程可以有很多条，正式分支默认只留最后整理好的一条。
- **开发分支**：暂存开发中各条提交的分支。它只在集成和归档之前保留这些过程记录；正常归档会删除它。
- **正式分支**：最终接收改动的分支，例如 main。
- **额外工作目录**：Git 为同一项目另开的一份目录，让开发分支与原目录分开工作。文中的 --no-worktree 表示不新建这份额外目录，直接在主分支上实施。
- **压缩合并（squash）**：只在有开发分支时使用，把开发分支上的多条提交合并成主分支上的一条。
- **Plan**：一份开发计划。多个 Plan 可以记录同一次交付中的不同工作。
- **slug**：Plan 名称最后一段的短英文名称，例如 enhance-plan-naming 中的 plan-naming。
- **Delivery**：一次正式交付；多个 Plan 可以属于同一次交付。
- **PR**：Pull Request，托管平台上的代码合并请求。

## Technical Context

本节说明为什么要改，以及当前程序和文档的差异。

### Architecture Context

在有开发分支的路径上，规则和实际指引不一致：文档说默认把多条开发提交合成一条，但 verify-switch 给出的命令会直接合并开发分支。正式分支没有其他新提交时，Git 可能把全部开发提交一起带过去；正式分支已经有新提交时，Git 会再加一条“合并提交”，并继续保留全部中间提交。

Plan 命名指南还规定开发分支名最多 55 个字符，太长时截短名称并加四位校验码；但当前 approve 代码直接把项目名和 Plan 名称拼在一起，没有执行这条限制。因此，本提案会把指南中的长度规则落实到程序中。

证据：
- .wopal/skills/dev-flow/references/commands.md:288-298 写明默认使用 squash（把多条提交合成一条）。
- .wopal/skills/dev-flow/scripts/commands/verify_switch.py:293-300 实际给出普通 git merge 命令。
- .wopal/skills/dev-flow/tests/python/unit/test_verify_switch.py:412-416 的测试也要求输出普通合并命令。
- .wopal/skills/dev-flow/references/plan-guide.md:342-345 规定分支名上限为 55 个字符并加四位校验码；.wopal/skills/dev-flow/scripts/commands/approve.py:72-86 当前只拼接项目名和 Plan 名称，没有截短或校验码。

此外，Final Commit（最终提交）目前有两种意思：有些流程记录正式分支上的提交，有些流程记录开发分支的最新提交。后续流程无法只靠这个字段判断本次工作最终落在哪条分支上。

### Research Findings

- 问题不只是一条合并命令写错；开发中的逐条记录和最终交付记录没有分开。
- Issue（任务跟踪单）只用来关联任务，不应改变最终交付方式。
- 在开发分支上工作（默认模式和 --existing-worktree），中间提交不能进入主分支；--no-worktree 本来就在主分支上实施，没有开发分支，也就没有压缩合并这一步。
- --existing-worktree 表示把 Plan 接到已有的额外工作目录上。多个这样的 Plan 可以共用一次交付，但必须明确哪些 Plan 属于一组，且整组只合入一次。
- “保留开发历史”只指集成完成到正常归档之间：这段时间可以从开发分支查看每条提交。正常归档仍会删除分支和额外工作目录，归档后不保证还能从 Git 找回这些逐条记录。

**References**:
- .wopal/skills/dev-flow/SKILL.md
- .wopal/skills/dev-flow/references/commands.md
- .wopal/skills/dev-flow/references/plan-guide.md

### Key Decisions

- D-01：有开发分支的交付统一按“一次正式交付”处理。开发分支上可以有多条开发、评审修复和验证修复记录；默认主分支只增加一条总结结果的提交。--no-worktree 不在其中，它在主分支上直接提交。
- D-02：有开发分支时，由 flow.sh integrate（把已验证改动写入正式分支的命令）负责正式合入；verify-switch（让项目目录切到开发分支供用户检查）、complete（标记开发和评审已完成）以及给执行者的说明都不再要求手动合并。--no-worktree 没有开发分支，不需要 integrate，实施完成即已在主分支上。
- D-03：有开发分支时，交付提交的标题在开发前定稿，权责链固定为四步。第一，由写 Plan 的人（控制器或受委派的规划者）起草，按 type(scope): result 格式说明做成了什么，例如 feat(scope): describe outcome，不能只写“合并”。第二，由用户在 approve 时连同 Plan 一起确认，确认即冻结。第三，冻结后只有用户要求改 Plan 才能改，改完要重新确认。第四，integrate 只从 Plan 字段读出标题原样使用，脚本不生成、不改写、不追加自动文本。Issue 标题只能作为起草参考。
- D-04：Issue（任务跟踪单）可有可无；两种情况走相同的交付流程。跨仓库 Issue 不把容易指错仓库的 #数字 直接当作提交标题来源。
- D-05：--no-worktree 表示不建开发分支、不建额外工作目录，直接在集成分支（main）上实施，适用于用户明确选择的简单改动。approve 前要求项目目录没有未提交改动；实施完成后用户直接在主分支上检查结果。这条路径没有压缩合并、没有开发分支可删，也不走 integrate。
- D-06：多个 --existing-worktree Plan（复用已有额外工作目录的开发计划）可以共用一次交付。第一个获批的 Plan 是负责人，记录正式分支、开发分支、共同起点、合入方式和提交标题。后续 Plan 必须填负责人的 Plan 名称作为 Delivery，并复用相同开发分支和这些记录；approve 会逐项核对，不一致就拒绝。成员范围就是所有尚未归档、且 Delivery 字段填了同一负责人名称的 Plan，不另建成员清单。integrate 可以从任一成员 Plan 启动，但会查齐所有成员，并把共同起点之后的全部改动合入正式分支一次。
- D-07：Final Commit（最终提交）现在含义不一，因此拆成两个字段。有开发分支时，Verification Commit 记录用户检查过的开发分支提交，Integration Commit 记录主分支上的那条交付提交；共享交付的 Integration Commit 只记在负责人 Plan 中，其他 Plan 都查同一记录。--no-worktree 只记录主分支上用户检查到的那个提交作为 Verification Commit，没有 Integration Commit。
- D-08：有开发分支时，默认把开发中的多条提交合成主分支上的一条（squash）。只有用户在合入前明确选择 preserve-history（在主分支保留多条开发提交）时，才保留全部提交。--no-worktree 不涉及这一步。
- D-09：Plan 名称继续遵守现有规则，最后一段的短英文名称最多 20 个字符。本提案只把命名指南已有的分支长度规则落实到程序：新建开发分支最多 55 个字符；超长时只截短 Plan 名称末尾，并加上由完整名称算出的固定四位校验码。现有 Plan 名称和分支都不改。

### Key Interfaces

本节固定脚本和多个 Plan 共用的字段与命令，避免不同步骤各自猜意思。

开发计划（Plan）增加或统一使用以下字段。字段名是脚本要识别的固定英文名称，后面说明它在人话里代表什么。

下表适用于有开发分支的交付（默认模式和 --existing-worktree）。--no-worktree 只使用 Verification Commit 一项，记录主分支上用户检查到的提交；其余字段留空。

| 固定字段名 | 人话解释 |
|------------|----------|
| Delivery | 一次正式交付的编号。用负责人 Plan 的名称作编号；同组其他 Plan 填同一个名称。 |
| Commit Subject | 正式分支上那条提交的标题。组内所有 Plan 标题必须一致。 |
| Integration Strategy | 把改动放进正式分支的方式。默认 squash（把多条开发提交合成一条）；用户明确选择时才保留多条提交。 |
| Integration Branch | 接收最终改动的正式分支，例如 main。组内所有 Plan 必须相同。 |
| Work Branch | 存放开发中各条提交的开发分支。组内所有 Plan 必须相同；新建分支最长 55 个字符，太长时截短名称并附加四位校验码。 |
| Delivery Base Commit | 这次交付开始前，正式分支上的最后一条提交。负责人 Plan 在获批时记录，其他 Plan 使用相同编号。 |
| Verification Commit | 用户实际检查过的提交编号。有开发分支时指开发分支上的提交；--no-worktree 时指主分支上的提交。 |
| Integration Commit | 主分支上生成的交付提交编号；负责人 Plan 记录一次，所有成员 Plan 共用。--no-worktree 没有这一项。 |

Commit Subject 的产生与使用规则：

1. 起草：写 Plan 的人在开发开始前写入该字段，作为 Plan 的一部分提交审阅。
2. 定稿：用户在 approve 时确认 Plan，标题随之一并冻结。
3. 变更：冻结后只能通过修改 Plan 并重新获得用户确认来改变。
4. 使用：integrate 直接读取字段值传给提交命令；脚本不调用任何生成、拼接或自动补全逻辑。PR 路径的合并标题与它逐字相同。
5. 共享交付：负责人 Plan 的标题就是整组唯一定稿，成员 Plan 填不同标题时 approve 拒绝。

正式集成命令：

    flow.sh integrate ISSUE_OR_PLAN --confirm

integrate 只用于有开发分支的交付（默认模式和 --existing-worktree）。--no-worktree 的 Plan 不走 integrate。

命令参数 issue-or-plan 可以是 Issue 编号，也可以是任一成员 Plan 名称。命令从这个 Plan 找到负责人；成员就是所有尚未归档、且 Delivery 字段相同的 Plan。然后按以下步骤操作：

1. 检查同组所有 Plan 都在 verifying（等待用户验证）状态，并要求开发目录没有未提交改动。用户刚完成整组改动的检查后执行 --confirm，表示同意集成；命令同时把当时开发分支的最新提交编号记作每个成员的 Verification Commit。
2. 检查正式分支、开发分支、共同起点、合入方式和提交标题是否一致；任何一项不同就停止并说明原因。
3. 从共同起点到开发分支当前版本收集全部改动，不能只收最后一个 Plan 写的部分。
4. 默认把全部改动合成一条提交。PR（Pull Request，托管平台上的代码合并请求）也必须用平台的“合成一条提交”方式，且使用相同标题。
5. 确认正式分支只增加符合所选方式的交付记录，并把这条提交的编号写入负责人 Plan。
6. 每个成员 Plan 再运行 verify --confirm（记录该 Plan 已验证完成）时，都查负责人 Plan 中同一条正式交付提交，不能把正式分支后来出现的其他提交误当成本次交付。

共享交付的全部 Plan 都完成集成和验证后才能归档。归档时，先对非负责人 Plan 使用 --keep-worktree（移动 Plan 归档但暂时保留共用开发目录），最后归档负责人 Plan；默认流程会在这一步删除共用开发分支和工作目录。

## In Scope

本次要完成的范围：

- 有开发分支的路径（默认模式和 --existing-worktree）：无论有无 Issue（任务跟踪单）、有无 PR（托管平台上的代码合并请求），都遵守同一默认交付规则。
- --no-worktree 保持现有的主分支直实施：不建开发分支，不做压缩合并，也不改变这条路径的现有行为。
- 新增 flow.sh integrate 命令，检查并把开发改动写入正式分支；普通流程不再让执行者手动合并。
- 定义 Delivery、提交标题、合入方式、开发验证提交和正式交付提交的含义。
- 让多个 --existing-worktree Plan 能明确共用一次交付，并验证成员、共同起点和提交信息。
- 明确 --no-worktree 仍是主分支直实施，并把这条路径与有开发分支的交付规则分开说明，避免误加压缩合并要求。
- 调整 verify-switch、complete、verify、archive（归档并清理工作目录）等命令、Plan 模板和相关 Git 辅助程序的职责。
- 增加真实临时 Git 仓库测试，覆盖自动前移、正式分支已有其他提交、有无 PR、有无 Issue、共享交付和共用分支的归档清理；并验证 --no-worktree 仍在主分支直实施、不产生开发分支。
- 把命名指南已有的“开发分支最多 55 个字符，超长时截短名称并加四位校验码”落实到分支生成程序；Plan 名称仍保持最多 20 个字符。

## Out of Scope

本次明确不改的内容：

- 不修改本体演进流程（ontology-evolution）自身的步骤或 Git 历史机制；这需要另一个提案。
- 不修改 projects/wopal-cli（Wopal CLI 项目）；如需改它的代码，另建 dev-flow 开发计划。
- 不重写已有项目的 Git 历史。
- Plan 名称最后一段仍最多 20 个字符；不在本提案中放宽命名限制。
- 不取消用户明确选择 preserve-history 的场景。
- 不修改 dev-flow 的状态名称：planning（计划中）、reviewing（待审）、executing（实施中）、verifying（待用户验证）、done（已完成）。
- 不修改全局 rules/git.md；当前工作目录没有这份文件的可见副本，本次规则只写在 dev-flow 自己的说明中。
- 不修改本体提案的命名规则；那属于 ontology-evolution 自身能力改进。

## Affected Files

以下是预计会修改的文件及其用途；实施后以实际改动为准。Operation 表示如何改，Role 表示文件的用途。

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| dev-flow 中文审阅版 | .wopal/skills/dev-flow/SKILL.zh-CN.md | modify | 先供用户阅读并确认新规则 |
| dev-flow 正式文档 | .wopal/skills/dev-flow/SKILL.md、references/commands.md、templates/plan.md | modify | 用户确认中文版本后，同步正式规则、命令说明和 Plan 模板 |
| dev-flow commands | .wopal/skills/dev-flow/scripts/flow.py、scripts/commands/{plan,approve,complete,verify,verify_switch,integrate,archive}.py | modify/create | 增加统一合入、55 字符分支限制和归档清理 |
| Git helper | .wopal/skills/dev-flow/scripts/lib/git.py | modify | 分开检查“改动是否已包含”和“提交历史是否符合规则” |
| tests | .wopal/skills/dev-flow/tests/python/ | modify/create | 用真实 Git 提交图验证交付、分支和归档结果 |

## Assembly Intent

本次是否要调整空间默认启用哪些规则或工具：

| Ref | Scope | 理由 |
|-----|-------|------|

## Acceptance Criteria

本节列出完成后必须达到的结果，以下称为验收标准（AC）。

### Agent Verification

可由执行者用命令检查的结果：

1. [x] **有开发分支时主分支只留一条交付记录**：用真实临时 Git 仓库建立至少 3 条工作、评审修复或验证修复提交。无论正式分支没有前进还是期间有其他提交进入，默认集成后正式分支只增加一条新提交（不是把两条分支接在一起的合并提交），标题与 Commit Subject 完全一致，也没有把中间开发提交带进正式分支。归档前，开发分支仍指向包含全部开发提交的版本；正常归档后，开发分支和额外工作目录均已删除。
2. [x] **两条路径各自成立**：有开发分支的默认模式和 --existing-worktree 使用同一压缩合并规则，Issue 只影响关联信息。--no-worktree 仍在主分支直实施：不创建开发分支和额外工作目录，不执行压缩合并，归档时也不删除任何开发分支。
3. [x] **提交记录指向准确**：有开发分支时，Verification Commit 只指用户检查过的开发分支提交，Integration Commit 只指主分支实际生成的交付提交；--no-worktree 只记录主分支上用户检查到的提交，不写 Integration Commit。verify --confirm 必须检查本次交付记录的提交编号。
4. [x] **共用一次交付**：多个 --existing-worktree Plan 加入同一 Delivery 时，approve 拒绝不同开发分支、正式分支、起点或提交标题；integrate 从任一成员 Plan 都会包含共同起点之后的全部成员改动，只生成一条正式交付记录，并把同一个 Integration Commit 提供给所有成员 Plan 的 verify。
5. [x] **保留多条提交是明确例外**：只有 Integration Strategy 写明 preserve-history，且用户在合入前明确选择时，正式分支才保留所有开发提交。默认方式不能改成普通合并（可能把多条中间提交一起带进正式分支）。
6. [x] **现有安全门继续有效**：用户确认、实现审查、防止覆盖其他人未提交改动的检查、供用户检查时切换到开发分支的方式和 PR 检查都通过回归验证。有开发分支的单 Plan 正常归档仍删除开发分支和额外工作目录；--no-worktree 的归档不涉及开发分支清理。
7. [x] **分支长度准确**：Plan 名称继续执行现有的 20 字符限制。新建开发分支最多 55 个字符；超过时只截短 Plan 名称部分并附加稳定的四位校验码。旧 Plan 和已存在的分支保持原样。
8. [x] **共用分支只清理一次**：共用 Delivery 的非负责人 Plan 归档时保留开发分支，让其他成员还能完成归档；负责人 Plan 最后归档时删除共用开发分支和工作目录。全部归档结束后，不得留下这次交付的分支或工作目录。
9. [x] **提交标题的权责链可核查**：技能说明里写明起草人、冻结时点、变更权限和“脚本只读取不改写”四条规则；integrate 与 PR 合并命令所使用的提交标题必须与 Plan 字段逐字相同，其正式交付标题路径上不得有生成、拼接或改写逻辑；成员 Plan 标题不一致时 approve 拒绝。

### User Validation

需要用户确认的结果；本次用户明确说明该行为主要面向 Agent、缺少可直接观察的用户界面，并授权由 Agent 使用真实临时 Git 场景代做验证，以该结果作为本次 User Validation：

#### Scenario 1: 正式分支的提交容易看懂

- Goal（目的）: 确认一次交付在项目正式分支上只留下一个能说明改了什么的提交。
- Environment（环境）: 使用改进后的 dev-flow 完成一次有多条开发记录的测试交付。
- Precondition（开始条件）: 所有自动检查通过，测试交付已完成集成。
- Launch command（查看命令）: git log --first-parent --oneline -8（查看正式分支最近的提交）
- User Actions（操作步骤）:
  1. 查看测试项目正式分支最近的提交。
  2. 判断本次交付是否只有一条正式提交，标题是否能直接说明交付内容。
- Pass criteria（通过标准）: 默认方式没有额外的合并提交，也没有把工作、评审或验证的中间提交带到正式分支；本次交付只有一条含义明确的正式提交。
- Failure feedback（失败时提供的内容）: 提供 git log --graph --first-parent --oneline -12 的输出，并说明哪条提交或标题不清楚。

- [x] 用户已明确授权 Agent 代做本场景验证，并接受该验证结果作为本次 User Validation。

**Validation record (2026-10-29)**: Agent 在独立临时 Git 仓库中建立 `main` + `work-delivery`，开发分支依次产生 implementation / review correction / validation correction 三条提交，同时让 `main` 先进入一条无关提交，再调用正式 `integrate_local_delivery(..., strategy="squash")`。结果：`main_before..main` 只有 1 条正式提交；正式标题逐字为 `feat(dev-flow): simulated formal delivery`；三条开发提交均不是 `main` ancestor；`work-delivery` tip 保持不变；Integration Commit 等于新的 `main` HEAD。随后执行关键真实 Git 场景回归（Shared Delivery、成员 PR、冲突 PR、dirty worktree、metadata durability/retry、preserve-history、no-worktree、55 字符分支、共享归档、固定 Integration Commit）→ `26 passed`；全量 `python -m pytest tests/python/ -q` → `560 passed, 42 subtests passed`；`bash scripts/flow.sh integrate --help` 正常；`wopal space evo check refactor-dev-flow-history` → `Result: OK`。验证结论：通过。

## Implementation

Task 是实施任务。Verification Intent 列出它对应的验收标准；Pre-read 是开始前要读的资料；Behavior 是要实现的可观察结果；Design 是实现边界；TDD 说明是否先写一个会失败的测试；Verify 是要执行的检查；Done 是验收通过后回填的完成记录。

### Task 1: 更新供用户审阅的中文版规则

**Verification Intent**: AC#2, AC#3, AC#4, AC#5, AC#9（本 Task 对应的验收标准编号）

**Behavior**:
- 中文版用普通中文说明主分支、开发分支、一次交付、合并方式和两个提交编号分别指什么。
- 写清 --no-worktree 的主分支直实施路径，以及多个 Plan 共用一次交付、归档时删除分支的步骤。
- 写清交付提交标题由谁起草、何时冻结、冻结后怎么改，以及脚本只照搬 Plan 字段。
- 命令和字段名必须保留英文时，紧接着用中文解释。

**Pre-read**: .wopal/skills/dev-flow/SKILL.zh-CN.md、.wopal/skills/dev-flow/AGENTS.zh-CN.md、本提案的 D-01 至 D-09。

**Design**: 只改中文审阅版，不改英文正式版、Plan 模板或脚本。Wopal 检查文字是否覆盖本提案的交付规则，完成后提交这一部分并请用户阅读。

**TDD**: false（本 Task 只更新文字，不改变程序行为，因此无需先写测试）— 本 Task 只更新文字说明，不改变程序行为。

**Changes**:
1. 更新中文技能说明，解释开发分支与正式分支的差别，以及归档时删除开发分支的边界。
2. 用具体步骤解释 --no-worktree 的主分支直实施，以及多个 Plan 共用一次交付的处理方式。
3. 用普通中文解释必要的 Git 术语；命令和字段名保留原样，紧接着说明意思。
4. 补上提交标题的权责链：起草人、approve 时冻结、变更需重新确认、脚本只读取。

**Verify**: 实施期回填文档一致性检查命令；逐项对照 D-01 至 D-09，确认每个字段和流程都有清楚解释，且没有与本提案相矛盾的句子。

**Done**:
Task output（结果摘要）: 已更新 dev-flow 中文审阅版，明确有开发分支与正式分支的历史边界、默认 squash 单提交、--no-worktree 主分支直实施、共享 Delivery、Verification/Integration Commit、Commit Subject 四步权责链、55 字符开发分支规则和共享归档清理。验证执行 `git diff --check` 与 D-01 至 D-09 文档一致性扫描，结果均 PASS。
Files touched（实际修改的文件）: skills/dev-flow/SKILL.zh-CN.md
- [x] 执行者已完成本 Task 的工作，验收者已检查 Verify 结果并回填记录。

**User direction after Task 1**: 用户明确纠正本检查点：进入实施后不中途停机确认，中英文 Skill 说明连续完成，随后继续脚本与测试实现；全部实现和自动验证完成后再进行一次最终评审/验证。

### Task 2: 同步英文正式说明和 Plan 模板

**Verification Intent**: AC#2, AC#3, AC#4, AC#5, AC#9（本 Task 对应的验收标准编号）

**Behavior**:
- 英文正式说明、命令指南和 Plan 模板都与用户确认过的中文版规则一致。
- 不再叫实施者手动运行普通 git merge。
- 每个新增字段、状态和命令在中英文版本里意思相同。
- 英文版同样写明提交标题的权责链，且与中文版逐条对应。

**Pre-read**: .wopal/skills/dev-flow/SKILL.md、references/commands.md、templates/plan.md、.wopal/skills/dev-flow/AGENTS.md。

**Design**: 按用户对原检查点的明确修订，Task 1 完成后直接开始。具体实现之前按本提案冻结的字段和行为同步英文内容，不再自行补充产品决策。

**TDD**: false（本 Task 只同步文档，不改变程序行为，因此无需先写测试）— 本 Task 只同步文档和模板，不改变程序行为；程序测试放在 Task 3。

**Changes**:
1. 同步英文技能说明、命令指南和 Plan 模板。
2. 移除与默认规则冲突的普通合并指引，以及把开发提交和正式提交混在一起的说明；新增字段和命令都保留精确名称并解释含义。
3. 补齐提交标题的权责链：谁起草、approve 时冻结、变更需重新确认、脚本只读取；PR 合并标题与字段逐字相同。

**Verify**: 实施期回填文档一致性检查命令，并逐项确认：中英文语义一致；Plan 模板含 Commit Subject 字段；默认指引不再要求普通合并；技能说明中能直接找到“谁起草、何时冻结、如何变更、脚本只读取”四条规则。

**Done**:
Task output（结果摘要）: 已将用户确认的交付历史规则同步到英文正式 Skill、命令参考和 Plan 模板；中英文均明确 Delivery 字段、提交标题四步权责链、默认 squash、共享 Delivery、--no-worktree 直实施，以及 integrate 取 Commit Subject 原值；旧的手工普通 merge 指引已移除。
Files touched（实际修改的文件）: skills/dev-flow/SKILL.md；skills/dev-flow/references/commands.md；skills/dev-flow/templates/plan.md；docs/evolutions/refactor-dev-flow-history.md
- [x] 执行者已完成本 Task 的工作，验收者已检查 Verify 结果并回填记录。

### Task 3: 实现统一合入命令并检查提交记录

**Verification Intent**: AC#1, AC#2, AC#3, AC#4, AC#5, AC#6, AC#7, AC#8, AC#9（本 Task 对应的验收标准编号）

**Behavior**:
- 有开发分支的 Plan 都通过 integrate 命令把改动写进正式分支，执行者不手动合并。
- 有开发分支时，默认把开发时的多条提交合成主分支上的一条提交。
- --no-worktree 继续在主分支直实施，不建开发分支，也不走 integrate 和压缩合并。
- 多个 Plan 共用一次交付时，先核对共同起点、分支、标题、合并方式和每个成员是否都完成用户验证，再合入一次。
- 有开发分支且用户明确选择保留多条提交时，主分支才保留它们。
- 集成时提交标题直接取自 Plan 字段，脚本不生成、不拼接、不改写；成员标题不一致时拒绝。
- 共用开发分支的 Plan 先分别归档，最后归档负责人 Plan 并删除共用分支和工作目录。
- Plan 名称保持现有 20 个字符上限；开发分支最多 55 个字符，超长时截短名称并加四位校验码。

**Pre-read**: .wopal/skills/dev-flow/scripts/commands/{plan,approve,complete,verify,verify_switch,integrate,archive}.py、scripts/lib/git.py、scripts/flow.py、tests/python/。

**Design**: integrate 命令负责写正式分支；同一次交付的负责人 Plan 保存共同起点和正式提交编号。复用现有 Plan 和 Git 辅助代码。先写真实 Git 仓库测试，再实现新规则；最后删除只要求旧合并方式的测试和重复说明。

**TDD**: true（先写会失败的测试，再实现功能）— 改变了用户能看到的提交记录和分支清理结果，因此先写能复现旧问题的测试，再完成实现。

**Changes**:
1. 先写真实 Git 测试，覆盖目标分支直接前移、目标分支已有新提交、单个 Plan、共用交付、有无 PR、有无 Issue、55 字符分支边界、超长名称稳定截短、归档清理，以及 --no-worktree 不建开发分支的直实施路径。
2. 让测试通过：有开发分支的交付记录 Delivery 负责人和成员、共同起点、提交标题、合入方式、开发分支、验证提交和正式提交；--no-worktree 只记录主分支上的验证提交。实现统一 integrate、开发分支长度限制和正确的分组归档清理。
3. 增加断言：集成与 PR 合并所使用的交付标题与 Plan 字段逐字相同；正式交付标题处理路径上不存在自动生成、拼接或改写逻辑；共享交付标题不一致时 approve 拒绝。
4. 删除只要求旧合并方式的测试和重复说明，保留并调整安全检查。

**Verify**: 实施期回填 dev-flow 单元测试与集成测试命令。必须包含真实 Git 提交关系检查：有开发分支时多条开发提交最终只在主分支形成一条交付提交，提交标题与 Plan 字段逐字相同；长项目和 Plan 名称生成的开发分支不超过 55 个字符；归档后开发分支和额外工作目录都不存在；--no-worktree 全程没有创建开发分支。

**Done**:
Task output（结果摘要）: 已实现 `flow.sh integrate` 与完整 Delivery 元数据流；默认 squash、明确 preserve-history、PR 合入均逐字使用 Plan `Commit Subject`。approve 会冻结/校验共享 Delivery 并生成 ≤55 字符稳定开发分支；complete 不再提前写 Verification Commit；verify 以固定 Integration Commit 核验本次交付，--no-worktree 只记录用户实际检查的正式分支 Verification Commit；共享 Delivery 按“成员保留、负责人最后清理”归档。integrate 的 Plan 记录提交失败可安全重试，不会重复正式合入。TDD 红灯确认后完成实现。验证：`python -m pytest tests/python/unit/test_integrate.py tests/python/unit/test_complete_verification_commit.py -q` → 16 passed；`python -m pytest tests/python/ -q` → 547 passed, 42 subtests passed；`bash scripts/flow.sh integrate --help` 正常；生产路径旧 Final Commit / 手工 merge 残留扫描为空；`git diff --check` 通过。
Files touched（实际修改的文件）: skills/dev-flow/references/{commands.md,plan-guide.md,plan-guide.zh-CN.md,troubleshooting.md}；skills/dev-flow/scripts/commands/{approve.py,archive.py,complete.py,integrate.py,verify.py,verify_switch.py}；skills/dev-flow/scripts/{flow.py,flow.sh}；skills/dev-flow/tests/python/unit/{test_approve.py,test_archive_delivery.py,test_complete_verification_commit.py,test_integrate.py,test_verify.py,test_verify_switch.py}；docs/evolutions/refactor-dev-flow-history.md
- [x] 执行者已完成本 Task 的工作，验收者已检查 Verify 结果并回填记录。

### Task 4: 实施评审返工（第 1 轮 BLOCK findings）

**Origin**: mandatory implementation review 对 `c72c19f..5421b40` 判 `BLOCK`（3 Blocker + 2 Warning）。本 Task 只修复 B-01～B-03、W-01～W-02 及其直接影响面，不重新打开已通过的设计项。

**Behavior**:
- integrate 在任何正式 Git mutation 前同时检查 canonical checkout 和仍存在的 Delivery worktree；任一处 dirty 都拒绝，且不写 Verification / Integration Commit。
- Shared Delivery 从所有成员统一解析 PR identity；任一合法成员创建的唯一 PR 都成为该 Delivery 的正式 PR 路径，不同 PR URL 则拒绝。
- Delivery 一旦已有 Integration Commit 即关闭新成员加入；已正式集成后的 Work Branch 若继续前进，重跑 integrate 明确拒绝而不是再次集成或静默成功。
- 本次新增 Git / GitHub mutation 与查询统一通过 `scripts/lib/git.py` / `scripts/lib/github.py`，command 层只负责编排 Delivery 状态。
- Shared Delivery approve 的五个共同字段逐项都有回归测试，并保留实际 existing-worktree branch 与 Work Branch 不一致的行为测试。

**TDD**: true — 先用真实 Git worktree / bare origin 复现 B-01～B-03，并用参数化测试补齐 W-02，再实现修复。

**Changes**:
1. B-01：integrate 解析所有成员 Plan 的 Worktree metadata；仍存在的 worktree 若有 staged / unstaged / untracked 变更，正式合入前直接失败。canonical checkout 的 dirty gate 保持不变。
2. B-02：PR URL 改为 Delivery 级统一解析；唯一 PR 可记录在任一成员，integrate 走该 PR 并在成功后把同一 PR identity 写回所有成员；多个不同 URL 在 Git mutation 前拒绝。
3. B-03：approve 在 owner 已有 Integration Commit 时拒绝新成员；integrate retry 要求所有成员 Verification Commit 一致且等于当前 Work Branch tip，否则判定 Delivery 已关闭且分支发生漂移并拒绝。
4. W-01：新增正式交付 Git helper（commit existence / subject / ancestry / merge-base / path-scoped status / branch integration / remote fast-forward）集中到 `lib/git.py`；PR merge 集中到 `lib/github.py`；approve / integrate / verify 不再新增直接 Git subprocess 调用。
5. W-02：Shared Delivery mismatch 测试参数化覆盖 Commit Subject、Integration Strategy、Integration Branch、Work Branch、Delivery Base Commit 五字段，并单独覆盖真实 existing-worktree branch mismatch。

**Verify**: `python -m pytest tests/python/unit/test_integrate.py tests/python/unit/test_approve.py tests/python/unit/test_verify.py tests/python/unit/test_git_semantics.py::TestFormalDeliveryGitHelpers -q`；`python -m pytest tests/python/ -q`；`git diff --check`；扫描本轮 command-layer diff 中新增 direct Git subprocess。

**Done**:
Task output（结果摘要）: 第 1 轮评审的 3 Blocker + 2 Warning 已全部按直接影响面修复。真实 Git 回归证明：dirty registered worktree 会在 main 前进和 VC/IC 写入前阻断；成员 Plan 持有的唯一 PR 会成为 Shared Delivery 的正式 PR 路径并同步给全组，冲突 PR identity 会拒绝；正式集成后的 Work Branch 漂移会拒绝重跑，owner 已有 Integration Commit 后 approve 不再允许 late member。Git/GitHub 正式交付操作已收口到 `lib/git.py` / `lib/github.py`。W-02 五字段参数化与实际 worktree branch mismatch 均已锁定。验证：聚焦 `60 passed`；全量 `559 passed, 42 subtests passed`；本轮 command-layer diff 新增 direct Git 调用扫描为 0；`git diff --check` PASS。
Files touched（实际修改的文件）: skills/dev-flow/scripts/commands/{approve.py,integrate.py,verify.py}；skills/dev-flow/scripts/lib/{git.py,github.py}；skills/dev-flow/tests/python/unit/{test_approve.py,test_git_semantics.py,test_integrate.py}；docs/evolutions/refactor-dev-flow-history.md
- [x] 执行者已完成本 Task 的工作，验收者已检查 Verify 结果并回填记录。

**Implementation Review 记录**: 第 1 轮对 `c72c19f..5421b40` 判 `BLOCK`（3 Blocker + 2 Warning），Task 4 完成全部返工；第 2 轮对 `5421b40..e65dc11` 确认原 5 项均已修复，但发现 W-01 helper 化直接引入的 durability Blocker B-N01（Plan path status query 失败被误判为 clean）。主控按 TDD 自修：`paths_have_changes()` 将 clean / changed / Git query failure 分为 `False` / `True` / `GitMutationFailure`，`_commit_plan_records()` 对 query failure fail-loud；真实损坏 Plan repo index 的完整 integrate→失败→修复 index→retry 回归证明正式分支始终只有一条交付 commit，Plan VC/IC 最终 durable。修复提交 `809e9f0`，相关模块 `62 passed`，全量 `560 passed, 42 subtests passed`。用户明确要求“有 BLOCK 必须再次评审”，因此追加第 3 轮 fix verification；对 `e65dc11..809e9f0` 的最终评审结论为 `PASS`（Blocker 0 / Warning 0，B-N01 FIXED，direct blast radius clean）。Implementation Review gate 至此通过。

**第 2 轮终局复审后的主控自修**：复审确认第 1 轮 B-01～B-03 / W-01～W-02 已全部修复，但发现 W-01 helper 化直接引入 B-N01：`paths_have_changes()` 把 path-scoped `git status` 查询失败与 clean 同样返回 False，使正式代码已经集成后可能跳过 Plan metadata commit 并错误返回成功。评审预算已用尽，因此主控仅修复该直接 blast-radius 缺陷，不开启第三轮设计/实现评审。修复后 `paths_have_changes()` 在 status 非零时返回 `GitMutationFailure`，`_commit_plan_records()` 明确记录诊断并非零失败；真实损坏 Plan repo index 的回归证明：formal main 可已前进，但命令返回失败且不会声称 VC/IC 已持久化；恢复 index 后重试只提交既有 Delivery records，正式分支仍只有第一次生成的单条 formal commit。验证：B-N01 RED 两测均失败；修复后聚焦 `3 passed`，相关 `test_integrate.py + test_git_semantics.py` 共 `62 passed`，全量 `560 passed, 42 subtests passed`，`git diff --check` PASS。
Files touched（本次终局自修）: skills/dev-flow/scripts/lib/git.py；skills/dev-flow/scripts/commands/integrate.py；skills/dev-flow/tests/python/unit/{test_git_semantics.py,test_integrate.py}；docs/evolutions/refactor-dev-flow-history.md

## Delegation Strategy

本节说明每项工作由谁做、按什么顺序做，以及开始前要满足什么条件。

| Wave | Task | Executor | Depends on | Why delegated |
|------|------|----------|------------|---------------|
| 1 | Task 1 | fae | none | 整理中文说明 |
| 2 | Task 2 | fae | Task 1 | 连续同步英文正式说明和模板，不设中间用户门 |
| 3 | Task 3 | fae | Task 2 | 文字说明确认一致后，再改命令和检查程序 |
| 4 | Task 4 | Wopal/controller | Task 3 + implementation review round 1 | 按评审 findings 做一轮完整返工并准备复审 |

实施阶段连续完成 Task 1 → Task 2 → Task 3；第 1 轮 implementation review 若有 finding，则在 `implementing` 内完成 Task 4 返工和第 2 轮复审；只有复审通过后才进入用户最终验证。

## Delivery

本提案的最终交付范围：

本提案不修改其他项目仓库。功能完成后，是否把改动同步到空间的上游仓库、是否提交 PR（托管平台上的代码合并请求）都由用户决定。有开发分支的交付在正常归档时删除开发分支和额外工作目录，共享交付按本提案规定的顺序只清理一次；--no-worktree 本来就没有开发分支可删。

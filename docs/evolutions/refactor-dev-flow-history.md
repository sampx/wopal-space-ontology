# refactor-dev-flow-history

## Metadata

- **Type**: refactor
- **Project Path**: .wopal
- **Created**: 2026-10-28
- **Stage**: accepted
- **Mode**: isolated
- **Worktree**: .worktrees/ontology-refactor-dev-flow-history
- **Branch**: ontology-refactor-dev-flow-history
- **Base Commit**: 02c0b9e021384091cd76e5437a4182133032bd65
- **Final Commit**: (none)

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

1. [ ] **有开发分支时主分支只留一条交付记录**：用真实临时 Git 仓库建立至少 3 条工作、评审修复或验证修复提交。无论正式分支没有前进还是期间有其他提交进入，默认集成后正式分支只增加一条新提交（不是把两条分支接在一起的合并提交），标题与 Commit Subject 完全一致，也没有把中间开发提交带进正式分支。归档前，开发分支仍指向包含全部开发提交的版本；正常归档后，开发分支和额外工作目录均已删除。
2. [ ] **两条路径各自成立**：有开发分支的默认模式和 --existing-worktree 使用同一压缩合并规则，Issue 只影响关联信息。--no-worktree 仍在主分支直实施：不创建开发分支和额外工作目录，不执行压缩合并，归档时也不删除任何开发分支。
3. [ ] **提交记录指向准确**：有开发分支时，Verification Commit 只指用户检查过的开发分支提交，Integration Commit 只指主分支实际生成的交付提交；--no-worktree 只记录主分支上用户检查到的提交，不写 Integration Commit。verify --confirm 必须检查本次交付记录的提交编号。
4. [ ] **共用一次交付**：多个 --existing-worktree Plan 加入同一 Delivery 时，approve 拒绝不同开发分支、正式分支、起点或提交标题；integrate 从任一成员 Plan 都会包含共同起点之后的全部成员改动，只生成一条正式交付记录，并把同一个 Integration Commit 提供给所有成员 Plan 的 verify。
5. [ ] **保留多条提交是明确例外**：只有 Integration Strategy 写明 preserve-history，且用户在合入前明确选择时，正式分支才保留所有开发提交。默认方式不能改成普通合并（可能把多条中间提交一起带进正式分支）。
6. [ ] **现有安全门继续有效**：用户确认、实现审查、防止覆盖其他人未提交改动的检查、供用户检查时切换到开发分支的方式和 PR 检查都通过回归验证。有开发分支的单 Plan 正常归档仍删除开发分支和额外工作目录；--no-worktree 的归档不涉及开发分支清理。
7. [ ] **分支长度准确**：Plan 名称继续执行现有的 20 字符限制。新建开发分支最多 55 个字符；超过时只截短 Plan 名称部分并附加稳定的四位校验码。旧 Plan 和已存在的分支保持原样。
8. [ ] **共用分支只清理一次**：共用 Delivery 的非负责人 Plan 归档时保留开发分支，让其他成员还能完成归档；负责人 Plan 最后归档时删除共用开发分支和工作目录。全部归档结束后，不得留下这次交付的分支或工作目录。
9. [ ] **提交标题的权责链可核查**：技能说明里写明起草人、冻结时点、变更权限和“脚本只读取不改写”四条规则；integrate 与 PR 合并命令所使用的提交标题必须与 Plan 字段逐字相同，其正式交付标题路径上不得有生成、拼接或改写逻辑；成员 Plan 标题不一致时 approve 拒绝。

### User Validation

需要用户亲自观察确认的结果：

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

- [ ] 用户已亲自验证上述结果并确认通过。

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
Task output（结果摘要）: (backfilled after verification)
Files touched（实际修改的文件）: (backfilled after implementation)
- [ ] 执行者已完成本 Task 的工作，验收者已检查 Verify 结果并回填记录。

**User checkpoint after Task 1**: Task 1 完成并提交后，Wopal 将中文审阅版交给用户确认。用户明确同意后才开始 Task 2。未获得确认前，不改英文正式版、Plan 模板和运行脚本。

### Task 2: 同步英文正式说明和 Plan 模板

**Verification Intent**: AC#2, AC#3, AC#4, AC#5, AC#9（本 Task 对应的验收标准编号）

**Behavior**:
- 英文正式说明、命令指南和 Plan 模板都与用户确认过的中文版规则一致。
- 不再叫实施者手动运行普通 git merge。
- 每个新增字段、状态和命令在中英文版本里意思相同。
- 英文版同样写明提交标题的权责链，且与中文版逐条对应。

**Pre-read**: .wopal/skills/dev-flow/SKILL.md、references/commands.md、templates/plan.md、.wopal/skills/dev-flow/AGENTS.md。

**Design**: 仅在用户确认 Task 1 的中文审阅版后开始。具体实现之前先按本提案冻结的字段和行为同步英文内容，不再自行补充产品决策。

**TDD**: false（本 Task 只同步文档，不改变程序行为，因此无需先写测试）— 本 Task 只同步文档和模板，不改变程序行为；程序测试放在 Task 3。

**Changes**:
1. 同步英文技能说明、命令指南和 Plan 模板。
2. 移除与默认规则冲突的普通合并指引，以及把开发提交和正式提交混在一起的说明；新增字段和命令都保留精确名称并解释含义。
3. 补齐提交标题的权责链：谁起草、approve 时冻结、变更需重新确认、脚本只读取；PR 合并标题与字段逐字相同。

**Verify**: 实施期回填文档一致性检查命令，并逐项确认：中英文语义一致；Plan 模板含 Commit Subject 字段；默认指引不再要求普通合并；技能说明中能直接找到“谁起草、何时冻结、如何变更、脚本只读取”四条规则。

**Done**:
Task output（结果摘要）: (backfilled after verification)
Files touched（实际修改的文件）: (backfilled after implementation)
- [ ] 执行者已完成本 Task 的工作，验收者已检查 Verify 结果并回填记录。

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
Task output（结果摘要）: (backfilled after verification)
Files touched（实际修改的文件）: (backfilled after implementation)
- [ ] 执行者已完成本 Task 的工作，验收者已检查 Verify 结果并回填记录。

## Delegation Strategy

本节说明每项工作由谁做、按什么顺序做，以及开始前要满足什么条件。

| Wave | Task | Executor | Depends on | Why delegated |
|------|------|----------|------------|---------------|
| 1 | Task 1 | fae | none | 先整理中文说明，供用户阅读确认 |
| 2 | Task 2 | fae | Task 1 + 用户确认 | 用户同意中文版后，再同步英文正式说明和模板 |
| 3 | Task 3 | fae | Task 2 | 文字说明确认一致后，再改命令和检查程序 |

Task 1 完成并由 Wopal 验收、提交后，暂停并请用户确认中文审阅版。确认之前不能开始 Task 2。

## Delivery

本提案的最终交付范围：

本提案不修改其他项目仓库。功能完成后，是否把改动同步到空间的上游仓库、是否提交 PR（托管平台上的代码合并请求）都由用户决定。有开发分支的交付在正常归档时删除开发分支和额外工作目录，共享交付按本提案规定的顺序只清理一次；--no-worktree 本来就没有开发分支可删。

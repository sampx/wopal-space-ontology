---
name: df-plan-review
description: >
  审查一份执行前的 Plan——照它字面执行，行不行得通、能不能达成目标？在用户要求
  审查、检查、验证一份 Plan 或实施计划时使用——特别是迁移、重构、跨模块改动、
  破坏性操作等高风险工作，例如「审查这个方案」、「这个 plan 能跑通吗」、「验证
  执行计划」。不适用：已由自动检查把关的常规 Plan、审查代码（用
  `df-implement-review`）、写方案。
---

# df-plan-review — Plan 正确性审查

**你只判断一件事：照这份 Plan 字面执行，工作能不能做成、能不能达成目标？**

## 你管什么，脚本管什么

`flow.sh plan check` 已经把关了格式：字段齐全、占位符、TDD↔Behavior 配对、checkbox 形状、AC 命令存在、User Validation 结构、状态有效。重查这些是浪费，只会制造噪音。

你管的是正则算不出来的东西——这份 Plan 的各部分是否互相咬合、是否符合现实、是否凑得成目标。

Plan 没问题就快速说没问题，收工。这个审查是特意发起的，不是走仪式。

## 三个问题

所有能逃过 `plan check` 的失败，都属于这三个之一：

| | 问题 | 抓住什么 |
|---|---|---|
| Q1 | 计划的各部分对得上吗？ | 没人生产的文件、没人创建的符号、没人认领的 AC、和依赖矛盾的顺序 |
| Q2 | 计划里关于代码库的说法属实吗？ | 过期的路径、错的行号、错的计数、和设计文档的静默冲突、跑不起来的命令 |
| Q3 | 照这样执行，能达成目标吗？ | 没有任务覆盖的目标、被悄悄缩水的决策、什么都证明不了的 AC |

出结论前三个问题都要走一遍。某个问题查出一个 Blocker，不代表可以跳过其余两个。

## 输入

你需要 Plan 路径和工作区根目录，其余都可以自己发现。

- prompt 带 `review_type: plan`、Plan 路径、Base Commit、关注点清单——就用它们。
- prompt 没给上下文，也照常做：读 Plan，从 `Project Path` 元数据定位目标项目，在报告里写明你做了什么假设。
- **Plan 声明了 Worktree 时**，活动副本在 worktree 里，不在集成分支上——状态和 checkbox 去那里读，代码核查用 worktree 的 HEAD。

## 怎么干：读一遍、记三张清单、再查证

效率是审查质量的一部分——烧时间的审查只会产噪音。分两段：

**第一段——Plan 从头到尾读一遍，带行号。** 边读边记三张清单，后面全靠它们：

1. **事实**——每一条关于代码库的具体说法：计数、路径、行号范围、文档章节、ID、命令、flag、"这个文件是新建的"、"这个文件要删除"。
2. **符号**——每个反引号里的代码名：哪个任务用它、哪个任务该创建它。
3. **文件**——所有出现过的路径，以及出现在哪：`## Affected Files` 表、`Changes`、`Pre-read`、测试路径。

**第二段——照着清单回答问题。** Q1 和 Q3 只需要 Plan 本身。只有 Q2 需要碰代码库，把它的命令攒成一批一起跑。检查之间不许回头重读 Plan——每回头一次，成本都超过省的。

查证不要巡山：路径用 `test -e`，行号用 `sed -n 'Np'`，章节和符号用 `rg -n`，版本用 `git cat-file`。确认一个章节的存在，永远不要整篇读设计文档。一份正常 Plan，大约 15–25 条命令就该查完；多模块大 Plan 可以多些，小 Plan 更少。

查不实的条目放进 `Unverified`——永远不许升格成 findings。

## Q1 — 计划的各部分对得上吗？

四项检查，全部只靠 Plan 本身。

1. **行为有人认领、规格可测。** Agent Verification 里的每个 AC，都必须被某个任务的 `Verification Intent` 引用——或者明确标记 cross-task。没人认领的验收标准永远没人证明。还要查位置：agent 能机械验证的（测试、lint、typecheck、可脚本化的检查）必须放 Agent Verification；如果躺在 User Validation 里，就是 Plan 把本可自动化的工作推给用户。每个 TDD 任务的 Behavior 必须照字面可测——实施 agent 不靠猜就能写成失败测试；「正确工作」这类含糊描述等于没规格，RED 阶段没有可失败的东西。
2. **符号有出处。** 任务*用到*的每个代码名，必须由更早的任务创建，拼写一字不差。跨任务 Plan 最容易断在接缝上：任务 2「注册 A–E 五个错误码」，任务 4「失败就抛 `TEMPLATE_MISSING`」——一个从没人声明过的名字。这是整个审查里性价比最高的检查：纯机械、读完一遍当场做完、格式校验器永远看不见。
3. **顺序服从依赖。** 每个消费者都排在它的生产者之后。任务之间文件重叠，只有在 Plan 声称并行执行时才是冲突；Plan 明说 wave 是串行的依赖层级，那重叠就是 Plan 自己的设计，不是缺陷。

**文件清单是预计范围，不是契约。** Task 不再携带 Files 字段；`## Affected Files` 表只是预计范围——实施 agent 会在真实代码上调整文件选择，Done 时回填实际触碰的文件。不要审计任务与表的双向一致（那套对账已经废弃）。只查两件事：表里某行声明的操作在仓库里已经不成立（「新建」的文件其实已存在、「删除」的文件其实不存在——过时前提，值得 WARNING）；声明并行执行时各 wave 的文件有重叠（BLOCKER）。

严重度：用了没人创建的符号 → **BLOCKER**；生产者拼写不一致 → **BLOCKER**；生产者在更后面的 wave → **BLOCKER**；声称并行执行下文件重叠 → **BLOCKER**。没人认领的 AC → **WARNING**；Behavior 不可测 → **WARNING**；可自动化验证躺在 User Validation → **WARNING**；人工观察条目冒充 agent 可验证 → **WARNING**；Affected Files 表的过时操作前提 → **WARNING**。

## Q2 — 计划里关于代码库的说法属实吗？

Plan 是对着代码的脑内模型写的。模型过时，建在其上的每个任务继承同样的错——而且错误在中期执行时才爆出来，预算已经烧完。代码库是唯一权威。

每条事实说法都要机械核掉。不许因为「看着没错」就放行：

| 说法 | 怎么查 |
|---|---|
| 「36 个 capability」 | 到事实源头去数 |
| 「`src/x.ts` 存在」 | `test -e` / `ls` |
| 「`file.ts:619-669`」 | 在目标版本上 `sed -n '619p'`——偏差几行没事，落在错误的代码上不算 |
| 「DESIGN.md §3 说 X」 | `rg -n '^#{2,3} ' doc` |
| 「D-12」/「issue #45」 | 到它的源头里找这个 ID |
| 「跑 `flow.sh verify`」 | 命令存在吗，接受这个 flag 吗 |
| 「新建文件 F」 | F 是否已经存在 |
| 「删除文件 F」 | F 是否存在 |

**写明你对着哪个版本查的**——Base Commit、worktree HEAD 或集成分支 HEAD。不带版本的 finding，别人一提交就腐烂。Plan 声明了 worktree 时，事实核查用 worktree 的 HEAD，不是集成分支。

再查一致性：Plan 引设计文档、`AGENTS.md`、既有接口作为依据。Plan 做的每个决定，找出权威文档怎么说的，然后对比。分歧分三类：

- **明说了**——Plan 声明它改了这个文档、或有理由地推迟、或说明了偏离理由 → 这是决定，不是缺陷。
- **静默**——偏离了却只字不提 → 一份未经协商就撕毁的契约。

判定冲突前，先确定哪份文档对所实施的模型说了算——旧文档有时描述的已经是过去时。

严重度：Plan 倚仗的错误前提 → **BLOCKER**；会让任务做错事的错误说法 → **BLOCKER**；触犯明确安全/安保约束的分歧 → **BLOCKER**；在声明环境里跑不起来的 AC 命令 → **BLOCKER**。不影响工作的偏差 → **WARNING**；对文档或规则的静默偏离 → **WARNING**；无关痛痒的偏差（计数不精确、顺序差异）→ **INFO**；查不实 → `Unverified`，不算 finding。

## Q3 — 照这样执行，能达成目标吗？

最贵的失败：一份 Plan 过了一切检查，仍然交付缩水。四个角度。

1. **目标全覆盖。** 把 Goal 拆成一个个独立的部分。每个部分都要有任务。没有任务的部分只是愿望，不是计划。
2. **决策全落地。** 每个 `D-xx`，任务交付的必须和决策说的一致——不是影子版本。盯紧缩水措辞：「v1」「simplified」「static for now」「hardcoded」「placeholder」「stub」「not wired to」「for now」。按顺序问两个问题：缩水是否违背 Goal 或某个决策？缩水是否被某个 `D-xx` 或范围声明明确授权（比如「本 Plan 交付静态层，动态后做」）？只有*没人批准的*缩水才算 finding。Plan 自己说清楚了分阶段交付，就是合法的。
3. **AC 能查出问题。** 两拍制下，第一拍是判据式写法——这合法（真实命令在 RED 阶段回填）。你管的是：如果功能坏了，这条判据能抓出来吗？怎么都通过的 AC——行为声明配个「文件存在」、或者把改动复述一遍——是装饰品，不是验证。判据式 AC 没写行为通过标准（没说可观察结果）就什么都抓不到。
4. **能交接。** 执行者只拿这份 Plan + 声明的 `Pre-read`，能开工吗？前面任务的接口和输出必须点名，不能暗示（「调用 `parseConfig()`，返回 `ParsedConfig`」才算就绪；「沿用任务 2 的返回结构」不算）。及格线是「胜任的执行者能推进」，只有缺了会走错路的信息才报——要被猜的接口、歧义的输出结构、执行者无从发现的依赖。

严重度：没有任务覆盖的目标部分 → **BLOCKER**；被悄悄缩水的决策 → **BLOCKER**（要么照做，要么明说分阶段）；查不出问题的 AC → **WARNING**；只凭 Plan 开不了工的任务 → **WARNING**。Plan 自己白纸黑字授权的缩水 → 不算 finding。

## 这些不要报

- **格式**——字段形状、排版、占位符样式、checkbox 布局。`plan check` 管的，而且已经过了。
- **已授权的决定**——任何 `D-xx` 或范围声明批准的内容。不同意它不构成 finding。
- **产品意图**——业务取舍归 Plan 主人。看着不对的需求放进 `Requirement Questions`，不是 Blocker/Warning。
- **口味**——「换我会换个结构」、命名观感、替代设计。
- **查不实的担忧**——毫无根据的「万一处理不了 X」。要么查实，要么闭嘴。
- **Plan 规模**——任务数、文件数、wave 数永远不是缺陷。上下文预算是按任务管理的，一份大而内聚的 Plan 很正常。只有交付组之间无依赖、且能独立验收时，才建议拆分——而且永远不是 Blocker。

finding 必须两边都有出处——Plan 说了什么，现实怎么反驳的。缺一边，最多算 Info。

## 评审预算——最多 2 轮

每次评审会话有硬预算：**首次评审加最多一次复审（共 2 次裁定），之后评审关闭。**评审在双方都烧真实订阅 token——一轮挤一点、每次挤一两个 finding 的牙膏式循环，是到达同一结论最贵的方式，禁止。

让 2 轮够用的做法：

1. **首次评审必须穷尽。**三个问题（Q1/Q2/Q3）全部跑完，把**所有** finding 一次性报完，包括你本想「留到下轮再说」的边缘发现。单个 finding 要深挖，但扣着不报不是严谨，是服务缺陷。
2. **复审时既查回归也扫全量，然后关闭。**复审验证修复的同时要再整体过一遍 Plan——本轮找到的一切都是最终结论，没有第 3 轮让你补漏。
3. **Owner 侧义务（Wopal）**：委派评审或复审时，prompt 里必须写明这个预算（例如「评审预算：最多 2 轮——本轮列全所有 finding，不会有下一轮」）。不带预算声明的复审 prompt 等于纵容挤牙膏。

如果第 2 轮仍是 BLOCK，评审按报告的 finding 关闭——不得继续循环。Plan 主人自行决定：修复后**新开会话**重新委派评审，或接受已记录的风险。关闭后新开一次评审是合法的；在原会话里悄悄续到第 3 轮不是。

## 结论与报告

```
PASS   — 没有 Blocker，没有 Warning
REVISE — 没有 Blocker，至少一个 Warning
BLOCK  — 至少一个 Blocker
```

`Unverified` 永远不改结论。

审查开始时，给每个问题（Q1/Q2/Q3）建一条 todo，边做边划掉。三个问题全部走完才能出结论。预算耗尽也不许装完成：照常出报告，加一个明确的 `UNCOVERED CHECKS` 段落说明没做到什么、为什么。

```markdown
# Plan Review — {plan-name}

## Summary
- Review type: Plan
- Verdict: PASS | REVISE | BLOCK
- Counts: Blocker N / Warning N / Info N / Unverified N
- Verified against: {Base Commit | worktree HEAD | integration HEAD}

## Blocker
### B-01: {issue title}
- Plan location: `{plan}.md:{line}`
- Reality: `{file}:{line}` 或 `{命令输出}` — {它为什么反驳了 Plan}
- Impact: {执行会怎么失败}
- Fix direction: {该补什么、改什么}

## Warning
{同 Blocker 格式；Impact 可省}

## Info
{一行一条}

## Unverified
- {条目} — 原因：{为什么查不了}

## Requirement Questions
{仅当需求本身有歧义，且靠 Plan 和代码解决不了}

## Positive Findings
- {已核实的条目：写明怎么核实的，读者才能信}

## UNCOVERED CHECKS
{仅当有检查没能完成}
```

`PASS` 必须配一小段 `Positive Findings`——查了什么、怎么查的。一句裸 PASS 等于让读者凭信仰接受结论，审查的意义就没了。

## 结论之后

- **`REVISE` / `BLOCK`**：修订后的 Plan 必须再审一遍才算干净——改了不复查等于没修。复用同一个审查会话（reply），之前的发现和处置还留在上下文里。
- **`PASS`**：只是给发起审查一方的输入，不是自动闸门。它不授权 `approve`，不替代 `plan check`，也不改变执行中 Plan 的状态。
- 审查不授权改动。发现的问题归还原主。

## References

某个问题需要完整步骤、严重度表或范例时，加载 rubric：

- `references/review-rubric.md` — 三张清单怎么建、每个问题的步骤、命令查证手册、严重度校准、范例（要认识的真实缺陷形状）

## Examples

### 例 1 — 没人创建的符号（Blocker）

Plan 的任务 4 写着失败分支「fails fast with `TEMPLATE_MISSING`」。任务 2 列了它注册的五个错误码，里面没有这个名字。整份 Plan 从没声明过这个码。

```yaml
finding:
  check: Q1_symbols
  severity: blocker
  plan_location: "{plan}.md:{line}"
  reality: "错误码注册清单在 {plan}.md:{line}；TEMPLATE_MISSING 不在其中"
  fix: "把这个码加进注册任务，或改用已有错误码"
```

### 例 2 — 错误前提（Blocker）

Plan 的前提是「schema 路径在 ontology 里已不存在，所以初始化必然失败」。在目标版本上查证被引文件，发现还有一处调用点仍读旧路径，而 Plan 没提——前提不完整，建在其上的任务会让这条路继续活着。

```yaml
finding:
  check: Q2_facts
  severity: blocker
  plan_location: "{plan}.md:{line}"
  reality: "{file}:{line} 仍在读旧路径"
  revision: "{commit}"
  fix: "把遗漏的调用点写进任务范围，或加一个任务删掉它"
```

### 例 3 — 不算 finding（校准）

一份 Plan 声明了六个任务，并在决策里写明不拆分，因为任务互相依赖、上下文按任务管理。任务数偏多。

**正确处理**：不算 finding。这个决定是明确且站得住脚的——规模不是缺陷，单 Plan 与否归 Plan 作者。值得的话记进 Positive Findings。
# enhance-multi-issue-close

## Metadata

- **Type**: enhance
- **Project Path**: .wopal
- **Created**: 2026-10-29
- **Stage**: draft
- **Mode**: (none)
- **Worktree**: (none)
- **Branch**: (none)
- **Base Commit**: (none)
- **Final Commit**: (none)

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High — 每个主张都有 file:line 或真实 Issue 状态为证；已实测 `gh issue close` 对已关闭 Issue 返回 0，因此重复关闭天然幂等。

## Goal

修复 dev-flow 两类会静默漏过的写侧完整性问题：让 Plan 关联的每一个 Issue 都按同一生命周期被同步、标注和关闭，同时让生成与提交的 Plan 不再携带模板 HTML 注释或作者占位残留。

## Technical Context

### Architecture Context

dev-flow 已经承认 Plan 可以关联多个 Issue，但只在**查找**一侧实现了复数语义，在**写入**一侧全部退化为单值，两者之间没有对齐。

查找侧（正确）：`scripts/lib/project.py:125` 的 `_plan_issues()` 用正则 `findall` 返回 `set[int]`，`scripts/lib/project.py:161` 用它匹配任意编号；`references/plan-guide.md:281` 已明确写出 `#249, #250` 中任一号都能找回 Plan。

写入侧（单值）：

- `scripts/plan.py:67` 的 `get_plan_issue()` 用 `re.search(r'#?(\d+)')`（`scripts/plan.py:74`）只返回第一个数字。这是全部写侧命令的唯一 Issue 来源：`approve.py:444`、`submit.py:90`、`complete.py:296`、`verify.py:360`、`archive.py:751`。
- `scripts/commands/reset.py:43` 与 `scripts/commands/sync.py:43` 各自又实现了一份「取第一个编号」，同一语义共三处重复。
- `archive.py:987` 只用 `close_issue(plan_issue, ...)` 关一个 Issue；`verify.py:526` 同样只关 `effective_issue`；`complete.py:101` 的 PR 正文只写 `Closes #N`。
- 同步面（正文、status/type/project 标签、`| Plan |` 链接行）也只作用于主 Issue：`archive.py:928` 起的 sync 块、`complete.py:423`。

**实测后果**：`refactor-space-evo-git-hist` 的 `Issue: #244, #246, #248` 归档后，#244 被 `archive` 关闭并变 `status/done`；#246/#248 仍停在 `OPEN` + `status/planning`，正文也没同步归档链接，需要人工补关。这不是报错，而是静默漏做。

**为什么之前没暴露**：提交 `c2385f1`（`fix(dev-flow): resolve every Issue in the Plan Issue list`）只修了查找侧，目的是防止「第二个编号找不到 Plan 而重复建 Plan」。写侧没有被同一轮修到，也没有 AC 覆盖多 Issue 的收尾。

**规范侧的空缺**：`references/plan-guide.md` 只在「Finding a Plan by Issue」里提到多 Issue 列表，从未定义多 Issue Plan 完成时每个 Issue 该如何处理。`references/commands.md:103` 把 close 记为终态 best-effort，但没有区分「关掉一个」与「关掉应关的全部」。

**Plan 清洁质量门同样缺失**：`scripts/validation.py:47` 的 `check_doc_plan()` 目前只聚合 `Status`、Product/Phase 配对、Plan 名和 Project Path 检查，没有任何 HTML 注释或模板残留检查。`templates/plan.md` 则包含大量 `<!-- ... -->` 作者提示，以及 `<Describe ...>`、`Low|Medium|High`、`Task Title` 等待填写占位。`scripts/commands/plan.py:236-299` 读取模板后只替换 `{plan_name}` / `{issue}` 等结构化 metadata，再原样写出其余正文，因此这些作者提示会进入新建 Plan。实际的 #266 Plan 已在 `submit` 自动 `plan check` 通过后仍保留 64 行模板 HTML 注释，证明当前质量门无法发现这类成品污染。

这不是语义审查缺失，而是机械文档卫生缺失。`references/plan-guide.md` 当前明确说 `plan check` 不判断 Design/TDD/Behavior 等内容质量；本提案保持这条边界，只增加可确定性判定的模板残留检查。

### Research Findings

- `gh issue close` 对已经 CLOSED 的 Issue 返回 0，并输出 `! Issue ... is already closed`（本次实测 #246）。批量关闭不需要先查状态即可安全重跑。
- 归档顺序已经是「先 durable 再外部可见」：`archive.py` 在 `commit_archived_plan` 成功后才做 Issue sync 与 close（D-06/D-07）。批量关闭沿用同一位置，不引入新的持久化风险。
- `sync_plan_to_issue_body`（`scripts/issue.py:491`）、`ensure_issue_labels`（`scripts/issue.py:576`）、`update_issue_plan_link`（`scripts/plan.py:360`）的签名都是单 Issue，批量化只需在调用层循环，单 Issue 实现不必改语义。
- 现有测试用 `@patch("commands.archive.get_plan_issue")` 注入单值（`tests/python/unit/test_archive.py:580` 等），改成复数返回必然触及这些 mock 点，属于预期的测试改写面。
- `create_plan_from_template()` 的生成路径天然知道哪些内容来自模板，因此可以在写文件前剥离 HTML 作者注释；不需要删除模板源里的维护提示，也不需要让使用者手工逐段删除。
- `submit.py:82` 与 `approve.py:436` 都在生命周期写入之前调用同一个 `check_doc_plan()`。把 Plan 清洁度加入这个机械 gate 后，`plan check`、`submit`、`approve` 会获得同一行为，不需要再维护三套检查。
- 合法技术文本也可能包含尖括号，例如命令契约中的 `<name>`。因此不能用“Plan 出现 `<...>` 就失败”的宽泛正则；兜底检查只识别 HTML 注释和明确的模板作者占位形态，并报告具体行号。

**References**:

- `skills/dev-flow/scripts/plan.py`
- `skills/dev-flow/scripts/lib/project.py`
- `skills/dev-flow/scripts/commands/archive.py`、`verify.py`、`complete.py`、`approve.py`、`submit.py`、`sync.py`、`reset.py`
- `skills/dev-flow/references/plan-guide.md`、`references/commands.md`

### Key Decisions

- D-01：**新增唯一的复数解析入口 `get_plan_issues()`，返回有序去重的 `list[int]`；`get_plan_issue()` 保留为取主 Issue 的薄封装。** 主 Issue 定义为字段里的第一个编号。理由：PR 标题、commit subject、日志里的 `plan #N` 都需要一个稳定代表，「全部 Issue」是另一个概念，分开命名可以避免调用点默默改变含义；同时收敛 `reset`/`sync` 的两份重复解析。
- D-02：**每个关联 Issue 都做完整收尾：正文同步、status 标签、type/project 标签、`| Plan |` 链接、关闭。** 理由：只关不标会留下 `status/planning` 的 CLOSED Issue，后续 `issue list` 仍会读错状态；漏掉链接时 Issue 指不到归档 Plan，变成孤岛。附带一条规则：`Issue` 字段的语义是「本 Plan 覆盖的 Issue」，因此列进来就意味着随交付关闭；若某个 Issue 只是关联参考、不随本次交付完成，就不该列进这个字段。
- D-03：**批量操作对每个 Issue 独立尽力完成，再汇总报告，单个失败不中断其余。** 理由：sync 与 close 都在 archive 的持久化点之后，属于终态外部副作用，无法回滚；中断会让剩下的 Issue 更可能保持脏状态。汇总逐条列出每个编号的结果，失败项带原因，不再静默。
- D-04：**主 Issue 失败仍不改变 archive 的持久化结论，但必须可见。** 沿用 `commands.md:103` 的终态定位，并补一条：「应关的都没关」不等于成功。实现上让 close 结果进入汇总输出，`archive` 结尾不再只写一个 Issue 行。
- D-05：**PR 路径为每个 Issue 写一行 `Closes #N`。** `complete.py:101` 目前只写主 Issue；GitHub 支持一个 PR 关联多个 `Closes` 引用，这样多个 Issue 才能靠 PR 合并自动关闭，而不是依赖本地补关——PR 路径里外部合并可能先于本地收尾发生。
- D-06：**`--no-worktree`、isolated、共享 Delivery 三种形态共用同一套收尾逻辑，不新增模式分支。** 理由：这是 Issue 侧收尾，与交付形态无关；分散实现正是这次漏关的成因。
- D-07：**重复编号去重并保持声明顺序。** 理由：`#244, #244` 这类手误不应导致重复关闭或重复评论。
- D-08：**Plan 模板保留作者提示，但 `plan new` 的渲染结果不携带 HTML 注释。** `create_plan_from_template()` 在写出 Plan 前剥离 `<!-- ... -->` 块，再做现有空行归一化。理由：模板提示属于模板维护/作者指导，不属于成品 Plan；在生成边界移除比要求每个 Agent 手工清理更可靠。
- D-09：**`check_doc_plan()` 增加机械 Plan hygiene gate。** 任意残留 HTML 注释，以及模板中明确要求作者替换的占位内容，都导致 `plan check` 失败并报告行号；该 gate 同时由 `submit` / `approve` 自动继承。它不检查 Design、TDD、Behavior 等语义质量，也不把命令/API 示例中的 `<name>`、`<id>` 等合法技术记号当占位残留。
- D-10：**模板占位识别采用窄规则，不做泛化尖括号扫描。** 识别对象是模板已知的作者占位形态（例如独占行的说明占位、`Commit Subject` 初始提示、Complexity/Confidence 枚举提示、默认 Task/Delegation 占位），新增模板作者占位时必须同步这份机械 gate 的测试。理由：宁可漏掉未知的新模板提示并由测试暴露，也不能误伤真实接口契约。

### Key Interfaces

| 面 | 契约 |
|---|---|
| `get_plan_issues(plan_path)` | 解析 `Issue` 字段的全部编号；无编号返回 `[]`；去重且保持声明顺序 |
| `get_plan_issue(plan_path)` | 返回 `get_plan_issues()` 的首项，否则 `None`；语义与今天完全一致 |
| Issue 收尾顺序 | 正文同步 → status 标签 → type/project 标签 → Plan 链接 → 关闭；单个失败不影响其余 |
| 汇总输出 | 逐条 `#N: closed` 或 `#N: FAILED (<reason>)`；存在失败时明确写出失败个数 |
| PR 正文 | 每个关联 Issue 一行 `Closes #N`，按声明顺序，不重复 |
| 幂等 | 重复 archive/verify 不报错、不产生重复关闭评论；已 CLOSED 视为成功 |
| Plan 生成清洁度 | `plan new` 生成文件不包含模板 HTML 注释；模板源可继续保留作者提示 |
| Plan hygiene gate | `plan check` / `submit` / `approve` 拒绝 HTML 注释与已知模板作者占位残留，并给出行号；合法 `<name>` 技术记号不受影响 |

## In Scope

- 新增 `get_plan_issues()` 作为唯一复数解析入口，`get_plan_issue()` 改为薄封装。
- 删除 `reset.py`、`sync.py` 内各自的 `extract_primary_plan_issue()`，改调统一实现。
- `archive` 的 Issue 收尾块批量化：逐 Issue 完整收尾并汇总报告。
- `verify` 的 Issue 收尾块批量化：逐 Issue 标签、正文、关闭，并去掉现在的 `except ... pass` 静默。
- `complete` 的 PR 正文改为每个关联 Issue 一行 `Closes #N`；状态标签同步改为逐 Issue。
- `approve`、`submit` 的 Issue 同步改为逐 Issue。
- `plan new` 渲染时剥离模板 HTML 作者注释，使新建 Plan 默认就是干净骨架。
- `check_doc_plan()` 增加 Plan hygiene 机械检查：拒绝残留 HTML 注释与已知作者占位，并输出可定位的行号；`submit` / `approve` 自动复用同一 gate。
- 更新 `references/plan-guide.md`（多 Issue 收尾契约）与 `references/commands.md`（`archive`/`verify`/`complete` 的 Issue 面描述，以及 close 定位补上「应关尽关」）。
- 更新 `references/plan-guide.md` 的 `plan check` 描述，明确“语义质量不机械审查”不等于允许模板残留，HTML 注释/作者占位属于确定性的文档卫生门。
- 补齐多 Issue 场景的单元测试与既有 mock 改写。
- 补齐 Plan 生成与 `check_doc_plan()` 的清洁度测试，含合法 `<name>` 不误报的负向保护。

## Out of Scope

- 不改 `_plan_issues()` 的查找行为，也不改「多个 Plan 匹配同一编号时 fail closed」的既有语义。理由：查找侧已经正确，本轮只补写侧。
- 不新增 Issue 之间的父子或依赖建模。理由：同一交付覆盖多个 Issue 是并列关系，引入层级会扩大契约面，当前没有需求证据。
- 不改变「创建错误的 Issue 必须 delete 而非 close」的既有规则。理由：那条针对写错的 Issue，与正常交付收尾无关。
- 不引入批量失败的重试队列。理由：close 与标签编辑本身幂等，重跑 `archive`/`verify` 已足够。
- 不把 close 提升为持久化门。理由：沿用 `commands.md:103` 的终态定位，本轮只要求失败可见。
- 不把 `plan check` 扩展成 Plan 内容评审器。理由：Design Source、Behavior、TDD 选择、AC 质量仍由 authoring/review 负责，本轮只增加确定性的模板残留与 HTML 注释卫生检查。
- 不禁止 Plan 正文里的合法尖括号技术记号。理由：`<name>`、`<id>` 等属于 CLI/API 契约表达，不是模板污染。

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| Plan 解析 | `scripts/plan.py` | modify | 新增 `get_plan_issues()`，`get_plan_issue()` 薄封装 |
| 命令重复解析 | `scripts/commands/reset.py`、`scripts/commands/sync.py` | modify | 删除本地解析，改用统一入口 |
| 归档收尾 | `scripts/commands/archive.py` | modify | Issue sync/close 批量化与汇总报告 |
| 验证收尾 | `scripts/commands/verify.py` | modify | Issue sync/close 批量化，去掉静默吞错 |
| 完成交付 | `scripts/commands/complete.py` | modify | 多个 `Closes #N`、逐 Issue 标签同步 |
| 审批与提交 | `scripts/commands/approve.py`、`scripts/commands/submit.py` | modify | 逐 Issue 同步 |
| Plan 生成 | `scripts/commands/plan.py` | modify | 渲染 Plan 时剥离模板 HTML 作者注释 |
| Plan 机械校验 | `scripts/validation.py` | modify | `check_doc_plan()` 增加 HTML 注释与已知模板占位残留 gate |
| 规范 | `references/plan-guide.md`、`references/commands.md` | modify | 多 Issue 收尾契约、close 定位、Plan hygiene gate 描述 |
| 测试 | `tests/python/unit/test_archive.py`、`test_verify.py`、`test_approve.py`、`test_submit.py` | modify | mock 改写与多 Issue 断言 |
| 测试 | `tests/python/unit/test_multi_issue_close.py` | create | 多 Issue 收尾行为集中覆盖 |
| 测试 | `tests/python/unit/test_check_doc.py`、`test_plan_metadata_contract.py` | modify | Plan 注释/模板残留拒绝、生成清洁度与合法 `<name>` 保护 |

## Assembly Intent

| Ref | Scope | 理由 |
|-----|-------|------|

## Acceptance Criteria

### Agent Verification

1. [ ] **复数解析唯一且有序**：`get_plan_issues()` 对 `#244, #246, #248` 返回 `[244, 246, 248]`，对 `#244` 返回 `[244]`，对 `#244, #244` 返回 `[244]`，对空字段与缺失字段返回 `[]`；`get_plan_issue()` 在同样输入下分别返回 `244`、`244`、`244`、`None`；`reset.py` 与 `sync.py` 不再各自定义解析函数。
2. [ ] **归档关闭全部关联 Issue**：以 `Issue: #A, #B, #C` 的 done Plan 执行 `archive`，三个 Issue 都收到正文同步、`status/done`、type/project 标签与归档后的 Plan 链接，且都被关闭；输出逐条列出三个编号的结果。
3. [ ] **验证收尾覆盖全部 Issue**：`verify --confirm` 对多 Issue Plan 执行后，每个 Issue 的 status 标签为 `status/done` 且状态为 CLOSED；不再存在静默吞错的 close 路径。
4. [ ] **PR 正文覆盖每个 Issue**：多 Issue Plan 走 PR 路径时，PR 正文包含每个编号各一行 `Closes #N`，顺序与 Plan 声明一致且无重复；单 Issue Plan 的 PR 正文与今天一致。
5. [ ] **幂等与部分失败可见**：对已全部关闭的 Plan 重跑 `archive`（或 `verify`）不报错、不产生重复关闭评论、退出码为 0；构造其中一个 Issue 关闭失败时，其余 Issue 仍被处理，汇总里该编号标 FAILED 并给出原因，整体明确写出失败个数，不宣称全部成功。
6. [ ] **单 Issue 与无 Issue 回归**：单 Issue Plan 的收尾输出、commit subject（`plan #N`）、PR 正文与改动前逐字一致；无 Issue Plan（`Issue: N/A` 或缺失字段）在所有命令下都不产生 gh 调用，行为与今天一致。
7. [ ] **三种交付形态一致**：`--no-worktree`、isolated、共享 Delivery 三种形态下，多 Issue 收尾结果相同，每个 Issue 都被同步与关闭。
8. [ ] **新建 Plan 默认无模板注释**：执行 `plan new` 后，生成的 Plan 中 `<!--` / `-->` 命中数为 0；模板源 `templates/plan.md` 可以继续保留作者提示；现有 metadata 替换、空 Product/Phase 与空行归一化行为不回归。
9. [ ] **Plan hygiene 是机械硬门**：构造包含 HTML 注释、`<Describe the Plan goal in one sentence.>`、初始 `Commit Subject` 提示、`Low|Medium|High` 或默认 `Task Title` 等已知模板残留的 Plan，`plan check` 均非零并报告对应行；同一 Plan 中出现 `wopal space evo accept <name>`、`GET /items/<id>` 等合法技术记号时不误报。`submit` / `approve` 对同类脏 Plan 在任何状态 commit、Issue sync 或 worktree 创建前拒绝。
10. [ ] **技能质量门**：`python -m pytest tests/python/ -v` 全绿；references 与实现描述一致（`get_plan_issues` 契约、多行 `Closes`、close 定位、Plan hygiene gate）。

### User Validation

N/A — 全部目标都是 Issue 状态、标签、正文与命令输出的可断言结果，可用 mock 的 `gh` 调用序列与真实 fixture 复核，不需要人工视觉或交互判断。

## Implementation

### Task 1: 统一复数 Issue 解析入口

**Verification Intent**: 1

**Behavior**:
- Given `Issue: #244, #246, #248`，When 调用 `get_plan_issues()`，Then 返回 `[244, 246, 248]`，去重且保序。
- Given 任意输入，When 调用 `get_plan_issue()`，Then 与今天返回的首个编号完全一致（含 `None` 情形）。
- Given `reset.py` 与 `sync.py`，When 检查源码，Then 两者不再各自定义 `extract_primary_plan_issue()`。

**Pre-read**: `scripts/plan.py`、`scripts/lib/project.py:125`、`scripts/commands/reset.py`、`scripts/commands/sync.py`

**Design**: 新增 `get_plan_issues()`，复用 `lib/project.py` 中已验证的数字提取正则；`get_plan_issue()` 变为 `issues[0] if issues else None`。`reset`/`sync` 的本地实现删除，改为导入统一函数并保留各自的取主语义。

**TDD**: true

**Changes**:
1. RED: 为上述输入写失败测试。
2. GREEN: 实现统一入口并替换两处重复定义。

**Verify**: `python -m pytest tests/python/unit/test_project_resolver.py tests/python/unit/test_plan_metadata_contract.py -v`

**Done**:
Task output: <one line>
Files touched: <fill in after implementation>
- [ ] The implementation agent has completed all development and verification steps above.

---

### Task 2: 归档与验证的批量收尾

**Verification Intent**: 2, 3, 5

**Behavior**:
- Given done 状态的多 Issue Plan，When `archive`，Then 每个 Issue 完成正文、标签、链接与关闭，输出逐条结果。
- Given 任一 Issue 关闭失败，When `archive`，Then 其余 Issue 继续处理，汇总标出 FAILED 与失败个数。
- Given 已全部关闭的 Plan，When 重跑 `archive`，Then 退出码为 0 且无重复评论。

**Pre-read**: `scripts/commands/archive.py`（sync 块与 close 块）、`scripts/commands/verify.py:515-535`、`scripts/issue.py`

**Design**: 抽出承担「单个 Issue 完整收尾」的函数，`archive` 与 `verify` 循环调用并收集结果；收尾顺序为正文同步 → status 标签 → type/project 标签 → 链接 → 关闭。`verify` 去掉静默吞错，改为记录失败原因。

**TDD**: true

**Changes**:
1. RED: 为多 Issue 归档与验证写失败测试，含部分失败与幂等重跑。
2. GREEN: 实现循环收尾与汇总输出。

**Verify**: `python -m pytest tests/python/unit/test_archive.py tests/python/unit/test_verify.py tests/python/unit/test_multi_issue_close.py -v`

**Done**:
Task output: <one line>
Files touched: <fill in after implementation>
- [ ] The implementation agent has completed all development and verification steps above.

---

### Task 3: PR 与审批、提交路径的复数覆盖

**Verification Intent**: 4, 6, 7

**Behavior**:
- Given 多 Issue Plan 走 PR 路径，When `complete` 创建 PR，Then 正文包含每个编号一行 `Closes #N`。
- Given 单 Issue 或无 Issue Plan，When 走任意命令，Then 输出与今天一致。
- Given `approve` / `submit` / `complete`，When 执行，Then 每个关联 Issue 都同步到当前状态。

**Pre-read**: `scripts/commands/complete.py:95-110,420-460`、`scripts/commands/approve.py:689-706`、`scripts/commands/submit.py:90-135`

**Design**: PR 正文由编号列表生成；三处状态标签同步改为循环。单 Issue 时输出保持原样，不改变 commit subject 与单行 `Closes`。

**TDD**: true

**Changes**:
1. RED: 为多 Issue PR 正文与三种形态一致性写失败测试。
2. GREEN: 实现复数覆盖并保持单 Issue 输出不变。

**Verify**: `python -m pytest tests/python/unit/test_approve.py tests/python/unit/test_submit.py tests/python/integration/test_issue_contract.py -v`

**Done**:
Task output: <one line>
Files touched: <fill in after implementation>
- [ ] The implementation agent has completed all development and verification steps above.

---

### Task 4: Plan 模板渲染与机械卫生门

**Verification Intent**: 8, 9

**Behavior**:
- Given `templates/plan.md` 含 HTML 作者注释，When `plan new` 渲染 Plan，Then 生成文件不含任何 HTML 注释，模板源本身不被改写。
- Given Plan 仍含 HTML 注释或已知模板作者占位，When `plan check` / `submit` / `approve`，Then 在任何生命周期副作用前失败并报告具体行号。
- Given Plan 的命令/API 示例含 `<name>` / `<id>` 等技术记号，When `plan check`，Then 不因这些合法记号失败。

**Pre-read**: `scripts/commands/plan.py:195-299`、`scripts/validation.py:47-64`、`templates/plan.md`、`tests/python/unit/test_check_doc.py`、`tests/python/unit/test_plan_metadata_contract.py`

**Design**: `create_plan_from_template()` 在 metadata 替换后、写文件前剥离 HTML comment block；`check_doc_plan()` 新增独立 hygiene checker，返回带行号的机械问题。占位识别只匹配模板作者约定的明确形态，不扫描所有尖括号文本。`submit` / `approve` 不新增专用分支，继续复用 `check_doc_plan()`。

**TDD**: true

**Changes**:
1. RED: 增加“生成结果无 HTML 注释”“check 拒绝残留”“合法 `<name>` 不误报”“submit/approve refuse-before-write”测试。
2. GREEN: 实现渲染清理与 hygiene checker，并复用现有 lifecycle gate。

**Verify**: `python -m pytest tests/python/unit/test_check_doc.py tests/python/unit/test_plan_metadata_contract.py tests/python/unit/test_submit.py tests/python/unit/test_approve.py -v`

**Done**:
Task output: <one line>
Files touched: <fill in after implementation>
- [ ] The implementation agent has completed all development and verification steps above.

---

### Task 5: 规范与文档对齐

**Verification Intent**: 10

**Behavior**:
- Given `references/plan-guide.md`，When 阅读多 Issue 相关章节，Then 明确写出「每个关联 Issue 都被同步与关闭」的收尾契约。
- Given `references/commands.md`，When 阅读 `archive`/`verify`/`complete` 与 close 记录，Then 描述与实现一致。
- Given `references/plan-guide.md` 的 Plan validation 章节，When 阅读 `plan check` 边界，Then 明确区分机械 hygiene（HTML 注释/模板残留，必须拒绝）与语义质量（Design/TDD/Behavior，不由 regex gate 判断）。

**Pre-read**: `references/plan-guide.md:276-290`、`references/commands.md:87,103`

**Design**: 在 plan-guide 的「Finding a Plan by Issue」之后补一节收尾契约，并同步其 `plan check` 边界；commands.md 的 close 记录补上应关尽关与失败可见。

**TDD**: false

**Changes**:
1. 更新两份 reference 的相关段落。

**Verify**: `python -m pytest tests/python/ -v` 全绿，且 `rg -n "get_plan_issues" references/` 命中更新后的描述

**Done**:
Task output: <one line>
Files touched: <fill in after implementation>
- [ ] The implementation agent has completed all development and verification steps above.

---

## Delegation Strategy

| Wave | Task | Executor | Depends on | Why delegated |
|------|------|----------|------------|---------------|
| 1 | Task 1、Task 4 | fae | none | 多 Issue 解析与 Plan hygiene 触面独立，可并行 |
| 2 | Task 2、Task 3 | fae | Task 1 | 两条收尾路径都依赖复数解析入口，彼此触面不同 |
| 3 | Task 5 | fae | Task 1、Task 2、Task 3、Task 4 | 最后按真实实现统一 references，避免先写文档再漂移 |

## Delivery

`space sync` 与原生 Git/GitHub 发布由用户决定，本提案不自行上传。

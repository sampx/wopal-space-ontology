# 106-fix-repair-workflow-bugs-and-harden-design

## Metadata

- **Issue**: #106
- **Type**: fix
- **Target Project**: ontology
- **Created**: 2026-04-15
- **Status**: done

## Scope Assessment

- **Complexity**: High
- **Confidence**: High

## Goal

修复 dev-flow 中已确认的脚本/校验缺陷，重建 fix 类 Issue 的内容模型与 Plan→Issue 渲染链路，并补强 Plan 模板中的 Test Plan / User Validation 构建规范、校验纪律与 verify 运行时 gate，使审计事实、测试步骤和用户确认都能在执行过程中被具体计划、逐步验证和显式阻断。

## Technical Context

### Confirmed Bugs

| # | File | 已确认缺陷 | 影响 | 修复边界 |
|---|------|------------|------|----------|
| 1 | `scripts/cmd/approve.sh` | 用 `git branch --contains <file-path>` 判断 Plan 是否已 push；同时又用 `origin/main..HEAD` 的全仓 ahead 数做二次判断 | 既有类型错误，也会把“仓库里别的未推送提交”误判成“当前 Plan 未 push” | 必须改成“定位最后一次修改该 Plan 文件的 commit → 判断该 commit 是否已进入 `origin/main`”的文件级检测，不能继续用文件路径或仓库级 ahead 数代替 |
| 2 | `scripts/cmd/archive.sh` | `root_dir` 在 `project_dir="$root_dir/projects/$project"` 之前尚未初始化 | 项目变更检测读错路径，archive 收尾阶段对项目工作区状态的判断不可信 | 只修正变量初始化顺序和依赖关系，不改变 archive 的提交、push、关 Issue 流程 |
| 3 | `scripts/cmd/complete.sh` | 无 Issue 模式 `complete --pr` 调用了不存在的 `create_pr_for_plan` | 无 Issue 工作流在打开 PR 时直接断路 | 必须补齐真实 helper，且复用现有 PR 创建逻辑；不能只在 `complete.sh` 里补一个临时分支 |
| 4 | `lib/check-doc.sh` | 文件名校验只接受 `<issue>-<type>-<slug>` | `plan.sh` 已允许 `<type>-<slug>`，但 `approve` 阶段会把合法无 Issue Plan 拒掉 | 必须让 `check-doc` 与 `plan.sh` 的命名规则对齐，避免两处正则继续漂移 |
| 5 | `lib/check-doc.sh` | `plan --check` 只做全局 checkbox 数量启发式检查，没有验证每个 Task 的 `**Changes**` 块必须使用 `- [ ] Step N:` 结构 | 像“`**Changes**` 用 1. 2. 3. 编号列表、step 出现在别处”的错误 Plan 也会被错误放行，执行级质量门失效 | 必须把校验改成 section-aware：逐个 Task 提取 `**Changes**` 到 `**Verification**` 之间的内容，只接受 `- [ ] Step N:` 形式 |
| 6 | `templates/plan.md` + `lib/check-doc.sh` | `## Test Plan` 模板只给“目标 / 方法 / 预期结果”级别的空泛提示，`plan --check` 也只要求 Test Plan 非空 | Agent 即使写出很多测试标题，仍然可能没有 fixture、执行步骤、证据和进度打勾方式，空洞测试计划会被错误放行 | 必须给出最小可执行测试用例骨架，并要求测试步骤使用 step checkbox；不适用的测试类别必须显式写 `N/A — 理由`，不能凑数 |
| 7 | `scripts/cmd/verify.sh` + `lib/plan.sh` + `templates/plan.md` | `verify --confirm` 在 `check_user_validation` 失败时只警告继续；`check_user_validation` 又允许无 section / 空内容 / 纯文本通过；模板和 skill 示例也没有要求最终用户确认 checkbox | Agent 可以在没有显式用户勾选的情况下擅自完成 verify，User Validation 既不可执行也不可阻断 | 必须把 User Validation 改成“场景用例 + 最终确认 checkbox”的显式 gate，且 `verify --confirm` 未勾选时硬阻断 |

### Content Model Defects

1. `templates/issue.md` 只定义了极薄的骨架，无法承载 `Confirmed Bugs`、`Content Model Defects`、`Cleanup Scope`、`Key Findings` 这类审计事实。
2. `scripts/cmd/new-issue.sh` 在“无结构化参数”路径上直接 `cat templates/issue.md`，而 `lib/issue.sh` 在“有结构化参数”路径上又单独拼一套 body，默认模板与实际生成链路天然漂移。
3. `lib/plan-sync.sh` 又维护了第三套独立 heredoc，并且每次同步都会整段覆盖 Issue body；只要事实没有被 plan-sync 这套 renderer 重建出来，就一定会丢。
4. 当前 `build_structured_issue_body` 与 `build_issue_body_from_plan` 都只理解 `Goal / Background / In Scope / Out of Scope / Acceptance Criteria / Related Resources`，无法稳定表达 bug 审计类事实。
5. `templates/plan.md` 对 `## Test Plan` 的指导只停留在“写几个测试项”，没有告诉 agent 应该如何构造 fixture、执行动作、预期证据和步骤勾选；`check-doc` 也不会阻止这种空洞写法。
6. `templates/plan.md` 与 `SKILL.md` 仍把 `### User Validation` 描述为纯文本确认项，没有给 agent 提供“如何设计用户验证场景”和“必须保留最终确认 checkbox”的明确 contract。

### Cleanup Scope

- 清理范围只限本次涉及文件：`approve.sh`、`archive.sh`、`complete.sh`、`new-issue.sh`、`check-doc.sh`、`issue.sh`、`plan-sync.sh`、`templates/issue.md`。
- 允许做的清理只有三类：删除无用变量 / 无效分支、合并重复的 Issue body 组装逻辑、把一次性字符串拼装抽成共享 helper。
- 明确禁止：改变状态机语义、改写 PR body 设计、扩大到无关脚本或历史文档。

### Key Findings

1. `approve` 的 push 检测必须以“当前 Plan 文件最后一次修改 commit 是否已进入 `origin/main`”为准；仓库级 `ahead_count` 只能说明 HEAD 是否领先，不能说明这个 Plan 文件本身是否已 push。
2. 修复无 Issue 模式 PR 路径时，真正需要补的是 `lib/issue.sh` 中的共享 PR 创建能力；只改 `complete.sh` 只能掩盖未定义函数，不能解决路径缺口。
3. Issue 内容模型升级不能只改 `templates/issue.md`；`new-issue.sh`、`lib/issue.sh`、`lib/plan-sync.sh` 必须共用同一个 section contract，否则模板、创建链路、同步链路会再次漂移。
4. 由于 Plan 顶层格式不能改，本次应把 bug 审计事实编码到 `## Technical Context` 的命名子段落中，由 `plan-sync` 精确提取这些子段落并重建 Issue body，而不是新增 Plan 顶层章节。
5. plan-sync 若继续“整段覆盖但使用独立 heredoc”，事实仍会丢；正确方向是“共享 renderer + 从 Plan 中提取命名子段落”。
6. `check-doc` 当前的 granularity check 只比较“Task 数量”和“全局 `- [ ] Step` 数量”，并不关心 step 是否真的位于 `**Changes**` 块内；因此 `plan --check` 不能证明结构规范已满足。
7. Test Plan 不能靠“单元 / 集成 / E2E”几个标题充数；每个保留的测试用例都必须回答 4 个问题：测什么、在哪里测、怎么执行、以什么证据判定通过。
8. 测试类别不是强制配额；某类测试没有必要时，应写 `N/A — 理由`，而不是制造空洞案例凑结构。
9. 要阻止 agent 擅自通过 verify，用户确认必须落在 Plan 中一个可检查的 `[x]` 状态上；纯文本“用户已验证”无法作为可靠 gate。
10. User Validation 用例应围绕本次变更后用户能直接感知的行为差异设计，至少写清场景目标、前置条件、用户操作和可见结果，不能照搬内部实现步骤。

## In Scope

- 修复 `approve.sh` 的 Plan push 检测，改成文件级 commit 可达性判断
- 修复 `archive.sh` 的 `root_dir` 初始化时序错误
- 为无 Issue 模式补齐可用的 PR 创建 helper，并让 `complete --pr` 走真实路径
- 让 `check-doc` 与 `plan.sh` 一致地接受有 Issue / 无 Issue 两种 Plan 命名
- 让 `check-doc` 强制校验每个 Task 的 `**Changes**` 块必须使用 `- [ ] Step N:` 结构，而不是宽松地统计全局 checkbox
- 优化 `templates/plan.md` 的 `## Test Plan` 指引，让 agent 能按统一骨架编写可执行测试用例而不是空泛条目
- 让 `check-doc` 校验 Test Plan 的最小可执行结构：保留的测试用例必须包含目标、fixture、执行方式、预期证据和 step checkbox；不适用类别允许 `N/A — 理由`
- 让 `templates/plan.md` 与 `SKILL.md` 明确 User Validation 的场景设计方法：按本次变更设计 1-3 个用户场景，并保留最终确认 checkbox
- 让 `check-doc` 校验 User Validation 的最小结构：至少一个具名用户场景 + 一个最终确认 checkbox
- 让 `verify --confirm` 只有在最终用户确认 checkbox 已勾选时才允许通过，不能再 warn-and-proceed
- 为 fix 类 Issue 定义统一 section order 与字段 contract，能表达 bug 审计事实
- 让 `new-issue` 默认 body、`build_structured_issue_body`、`plan-sync` 三条链路共用同一套 renderer
- 让 `plan-sync` 从 `## Technical Context` 的命名子段落中提取 `Confirmed Bugs`、`Content Model Defects`、`Cleanup Scope`、`Key Findings`
- 清理本次涉及文件中的重复 body 拼装逻辑、无效变量和旧分支，但不改变对外行为

## Out of Scope

- 不改 dev-flow 的 4-state 状态机语义
- 不重写已有的 Issue/PR label 体系
- 不重设计有 Issue 路径下的 PR body 内容
- 不修改 Plan 顶层章节格式；只优化 `## Test Plan` 内部的测试用例骨架、注释和校验要求
- 不追溯修改 `done/` 下的历史 Plan 或其他无关 Issue
- 不扩大到本次未触及的 skill 文档、命令或项目

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| Approve flow | `projects/ontology/agents/wopal/skills/dev-flow/scripts/cmd/approve.sh` | 修改 | 将 Plan push 检测改为文件级 commit 可达性判断 |
| Archive flow | `projects/ontology/agents/wopal/skills/dev-flow/scripts/cmd/archive.sh` | 修改 | 修复 `root_dir` 初始化顺序，保证项目工作区检测可信 |
| Complete flow | `projects/ontology/agents/wopal/skills/dev-flow/scripts/cmd/complete.sh` | 修改 | 让无 Issue 模式 `complete --pr` 走真实 helper |
| New issue entrypoint | `projects/ontology/agents/wopal/skills/dev-flow/scripts/cmd/new-issue.sh` | 修改 | 让默认 Issue body 与共享 renderer 对齐，消除 raw template 漂移 |
| Plan validator | `projects/ontology/agents/wopal/skills/dev-flow/lib/check-doc.sh` | 修改 | 让命名校验与 `plan.sh` 的双格式规则一致，并强制 `**Changes**`、Test Plan、User Validation 使用可执行结构 |
| Plan template | `projects/ontology/agents/wopal/skills/dev-flow/templates/plan.md` | 修改 | 为 `## Test Plan` 和 `### User Validation` 提供最小可执行骨架、场景设计提示与最终确认 checkbox |
| Verify gate | `projects/ontology/agents/wopal/skills/dev-flow/lib/plan.sh`, `projects/ontology/agents/wopal/skills/dev-flow/scripts/cmd/verify.sh` | 修改 | 把 User Validation 改成显式 checkbox gate，并阻止 warn-and-proceed |
| Skill docs | `projects/ontology/agents/wopal/skills/dev-flow/SKILL.md` | 修改 | 同步 User Validation 示例与模板规则，避免 agent 继续按纯文本旧例编写 |
| Issue renderer | `projects/ontology/agents/wopal/skills/dev-flow/lib/issue.sh` | 修改 | 定义 fix 类 Issue 的统一 section contract，并补齐无 Issue PR helper |
| Plan-to-Issue sync | `projects/ontology/agents/wopal/skills/dev-flow/lib/plan-sync.sh` | 修改 | 从 Plan 的命名子段落提取审计事实，并复用共享 renderer |
| Issue template | `projects/ontology/agents/wopal/skills/dev-flow/templates/issue.md` | 修改 | 将静态模板调整为与统一 contract 一致的 skeleton |
| Shared cleanup | 上述涉及文件 | 精简/合并 | 删除重复 body heredoc、无效变量、临时分支，保持外部行为不变 |

## Implementation

### Task 1: 修复 approve 的文件级 push 检测

**Files**: `projects/ontology/agents/wopal/skills/dev-flow/scripts/cmd/approve.sh`

**Changes**:
- [x] Step 1: 用 `git log -n 1 -- <plan>` 或等价手段定位"最后一次修改该 Plan 文件的 commit"。
- [x] Step 2: 用该 commit 与 `origin/main` 做可达性判断，替换当前错误的 `git branch --contains <file-path>`。
- [x] Step 3: 删除把仓库级 `origin/main..HEAD` ahead 数当作 Plan push 结论的分支，避免 unrelated commit 造成误报。
- [x] Step 4: 保留现有审批门控语义和提示语，只修正判断依据。

**Verification**: 在 `.tmp` 或系统临时目录构造 3 组 git fixture：`Plan 未 commit`、`Plan commit 已在 origin/main`、`HEAD 有其他未推送 commit 但 Plan commit 已在 origin/main`，确认只有真正“Plan 未进入 origin/main”的场景被阻断。

### Task 2: 修复 archive 的 `root_dir` 初始化时序

**Files**: `projects/ontology/agents/wopal/skills/dev-flow/scripts/cmd/archive.sh`

**Changes**:
- [x] Step 1: 把 `root_dir=$(find_workspace_root)` 提前到首次构造 `project_dir` 之前。
- [x] Step 2: 统一 `project_dir`、space repo commit/push、收尾提示中对 `root_dir` 的引用顺序。
- [x] Step 3: 只做顺序修复和局部清理，不改 archive 的业务流程与输出语义。

**Verification**: 在 `.tmp` 构造带目标项目的 workspace fixture，执行 archive 相关路径，确认项目变更检测使用的是解析后的 workspace root，且不存在未初始化变量引用。

### Task 3: 补齐无 Issue 模式的 PR 创建路径

**Files**: `projects/ontology/agents/wopal/skills/dev-flow/scripts/cmd/complete.sh`, `projects/ontology/agents/wopal/skills/dev-flow/lib/issue.sh`

**Changes**:
- [x] Step 1: 在 `lib/issue.sh` 中补齐"基于 Plan 元数据创建 PR"的共享 helper，避免 `complete.sh` 继续调用不存在的函数。
- [x] Step 2: 让该 helper 复用现有 PR 创建逻辑：目标项目 repo 解析、当前 feature branch 检查、PR title/body 组装、`gh pr create` 调用。
- [x] Step 3: 在 `complete.sh` 的无 Issue 路径上接入该 helper，并保持有 Issue 路径不受影响。
- [x] Step 4: 只修复路径缺口和重复逻辑，不顺手重写 PR body 模板。

**Verification**: 在 `.tmp/projects/<project>` 的 feature branch fixture 中调用无 Issue `complete --pr` 路径，确认不会再出现未定义函数；若 GitHub 环境不可用，则用 stub `gh` 验证 helper 入参与分支检查逻辑。

### Task 4: 让 `check-doc` 同时覆盖命名规则、`**Changes**` 结构、Test Plan 与 User Validation 质量门

**Files**: `projects/ontology/agents/wopal/skills/dev-flow/lib/check-doc.sh`

**Changes**:
- [x] Step 1: 将文件名校验从"硬编码 issue-only 正则"改成与 `plan.sh` 一致的双格式规则。
- [x] Step 2: 仅在文件名带 Issue 前缀时检查"文件名 Issue 号 = Metadata Issue 号"；无 Issue Plan 不做这条一致性约束。
- [x] Step 3: 为每个 Task 提取 `**Changes**:` 到 `**Verification**:` 之间的块内容，并把它作为独立结构校验对象。
- [x] Step 4: 强制 `**Changes**` 块中的非空条目使用 `- [ ] Step N:` 形式，拒绝 `1.` `2.` 这类编号列表或把 step 写在错误段落里的情况。
- [x] Step 5: 为 `## Test Plan` 增加最小结构校验：每个非 `N/A` 的测试类别至少包含一个具名 Case，且 Case 内有目标、fixture、执行方式、预期证据和 step checkbox。
- [x] Step 6: 允许 `N/A — 理由` 作为合法空类别写法，拒绝只有空洞 bullet 的 Test Plan。
- [x] Step 7: 为 `### User Validation` 增加最小结构校验：至少一个具名用户场景 + 一个最终确认 checkbox；缺任一项都视为不合格。
- [x] Step 8: 避免两套规则继续分别维护，优先复用共享 helper 或至少复用同一条正则语义。

**Verification**: 使用一个 Issue Plan（`106-fix-...`）、一个无 Issue Plan fixture（`fix-sample-name.md`）、一个 `**Changes**` 使用编号列表的坏样例、一个 `**Changes**` 正确但 Test Plan 只有空洞 bullet 的坏样例、一个缺少用户最终确认 checkbox 的坏样例、以及一个包含 `Case + Step checkbox + 用户最终确认 checkbox` 的好样例分别执行 `check_doc_plan`，确认命名规则、Task 结构规则、Test Plan 结构规则和 User Validation 结构规则都会被准确判定。

### Task 5: 优化 Plan 模板与技能文档中的 Test Plan / User Validation 构建规范

**Files**: `projects/ontology/agents/wopal/skills/dev-flow/templates/plan.md`, `projects/ontology/agents/wopal/skills/dev-flow/SKILL.md`

**Changes**:
- [x] Step 1: 在 `## Test Plan` 下定义最小测试用例骨架：`Case 标题` + `Goal` + `Fixture` + `Execution` + `Expected Evidence` + `- [ ] Step N:`。
- [x] Step 2: 明确"每个类别宁缺毋滥"的原则：只有真正需要覆盖的类别才写 Case，不适用时用 `N/A — 理由`。
- [x] Step 3: 把当前"目标 / 方法 / 预期结果"式空泛占位，替换成能直接指导 agent 写出执行步骤的注释和 skeleton。
- [x] Step 4: 在 `### User Validation` 下定义用户场景骨架：`Scenario 标题` + `Goal` + `Precondition` + `User Actions` + `Expected Result`。
- [x] Step 5: 增加唯一的最终确认 checkbox：`- [ ] 用户已完成上述功能验证并确认结果符合预期`，并明确只有用户才能在验证完成后勾选。
- [x] Step 6: 在模板注释与 `SKILL.md` 中说明用户场景的设计原则：优先挑选 1-3 个本次变更直接影响的可感知行为，不写内部实现细节，不凑数。
- [x] Step 7: 保持 `## Test Plan` / `### User Validation` 的顶层分组不变，只优化组内写法与说明，避免影响现有 Plan 总体格式。

**Verification**: 读取更新后的模板与 `SKILL.md`，确认 agent 只看注释与 skeleton 就能知道如何写测试 fixture、执行方式、用户场景、最终确认 checkbox；再用模板衍生的最小好样例通过 `check_doc_plan`。

### Task 6: 收紧 verify 运行时的 User Validation gate

**Files**: `projects/ontology/agents/wopal/skills/dev-flow/lib/plan.sh`, `projects/ontology/agents/wopal/skills/dev-flow/scripts/cmd/verify.sh`

**Changes**:
- [x] Step 1: 重写 `check_user_validation` 的判定规则：不再允许"无 section / 空内容 / 纯文本存在即可通过"，而是要求至少一个具名用户场景和最终确认 checkbox。
- [x] Step 2: 让 `check_user_validation` 只在"最终确认 checkbox 已勾选且不存在未勾选用户确认项"时返回成功。
- [x] Step 3: 在 `verify.sh` 中移除"校验失败只警告继续"的逻辑，改为明确阻断并提示先完成用户验证再重试。
- [x] Step 4: 保持 PR merged 检查、状态迁移顺序和归档入口不变，只收紧用户验证 gate。

**Verification**: 准备一份处于 `verifying` 状态的样例 Plan，先保持最终确认 checkbox 为未勾选执行 `flow.sh verify <plan> --confirm`，确认被阻断；再勾选 checkbox 并复跑，确认才允许进入 `done`。

### Task 7: 定义 fix 类 Issue 的统一 section contract 与共享 renderer

**Files**: `projects/ontology/agents/wopal/skills/dev-flow/lib/issue.sh`

**Changes**:
- [x] Step 1: 为 fix 类 Issue 定义唯一 section order：`Goal` → `Background` → `Confirmed Bugs` → `Content Model Defects` → `Cleanup Scope` → `Key Findings` → `In Scope` → `Out of Scope` → `Acceptance Criteria` → `Related Resources`。
- [x] Step 2: 让这些 section 支持"有值则渲染、无值则用明确占位或按类型省略"，避免把 bug 审计块强加给不相关类型。
- [x] Step 3: 把列表渲染、section 拼接、Related Resources 行组装收敛到共享 helper，删除 `issue.sh` 内现有的专用 heredoc 拼装重复。
- [x] Step 4: 保持现有 `Goal / Background / Scope / Out of Scope / Reference` 入参兼容，不破坏 `new-issue` 现有 CLI。

**Verification**: 直接调用 renderer 生成一份 fix issue body 和一份非 fix issue body，确认 fix body 具备审计 section，非 fix body 不出现无意义空块，且 `Related Resources` 始终保留。

### Task 8: 统一模板与 `new-issue` 的默认 body 生成链路

**Files**: `projects/ontology/agents/wopal/skills/dev-flow/templates/issue.md`, `projects/ontology/agents/wopal/skills/dev-flow/scripts/cmd/new-issue.sh`, `projects/ontology/agents/wopal/skills/dev-flow/lib/issue.sh`

**Changes**:
- [x] Step 1: 将 `templates/issue.md` 更新为与共享 contract 一致的 skeleton，确保静态模板可读、字段顺序正确。
- [x] Step 2: 让 `new-issue.sh` 的默认 body 生成链路与共享 renderer 对齐，消除"直接 cat 模板"和"代码另拼一套 body"的双轨漂移。
- [x] Step 3: 保持现有 CLI 参数不变；缺少研究信息时使用明确占位文本，而不是继续输出过薄骨架。
- [x] Step 4: 只调整默认 body 生成路径，不扩大到 `gh issue create` 之外的命令接口。

**Verification**: 离线生成 3 份 body 对比：`templates/issue.md` skeleton、`new-issue` 默认 body、`create_issue` 结构化 body，确认 section 顺序一致、fix 类审计块一致、占位策略一致。

### Task 9: 改造 plan-sync，使审计事实可从 Plan 重建并在同步中保留

**Files**: `projects/ontology/agents/wopal/skills/dev-flow/lib/plan-sync.sh`, `projects/ontology/agents/wopal/skills/dev-flow/lib/issue.sh`

**Changes**:
- [x] Step 1: 在 `plan-sync.sh` 中增加对 `## Technical Context` 命名子段落的提取：`### Confirmed Bugs`、`### Content Model Defects`、`### Cleanup Scope`、`### Key Findings`。
- [x] Step 2: 保持 Plan 顶层格式不变：仍然只依赖 `Goal / Technical Context / In Scope / Out of Scope / Acceptance Criteria / Related Resources` 等既有顶层章节。
- [x] Step 3: 让 `build_issue_body_from_plan` 不再维护独立 heredoc，而是把提取结果交给 Task 7 的共享 renderer。
- [x] Step 4: 对缺少这些命名子段落的旧 Plan 保留向后兼容回退：至少仍能渲染 `Goal / Background / In Scope / Out of Scope / Acceptance Criteria / Related Resources`。

**Verification**: 用当前 Plan 作为 fixture 调用 `build_issue_body_from_plan`，确认输出包含 `Confirmed Bugs`、`Content Model Defects`、`Cleanup Scope`、`Key Findings`；再用旧结构 Plan fixture 验证 fallback 不会崩。

### Task 10: 对本次涉及文件做等价清理与回归收口

**Files**: 本次所有涉及文件

**Changes**:
- [x] Step 1: 删除旧的重复 body 拼装片段、修复后失效的中间变量和无效分支。
- [x] Step 2: 统一本次涉及文件中的 section 名称、占位文本和 helper 调用顺序，避免同义不同写法继续扩散。
- [x] Step 3: 对 `approve`、`check-doc`、`new-issue`、`complete --pr`、`plan-sync` 做定向回归，确认没有因为清理改变外部行为。

**Verification**: 对比清理前后的 CLI 入口行为与输出语义，只允许内部实现收敛，不允许改变状态推进、参数格式、提示意图和现有正常路径的结果。

## Delegation Strategy

| 批次 | Task | 执行者 | 依赖 |
|------|------|--------|------|
| 1 | Task 1 | fae | 无 |
| 1 | Task 2 | fae | 无 |
| 1 | Task 4 | fae | 无 |
| 2 | Task 3 | fae | 无 |
| 3 | Task 5 | Wopal | Task 4 |
| 4 | Task 6 | fae | Task 5 |
| 5 | Task 7 | Wopal | Task 1-6 研究结论已固定 |
| 6 | Task 8 | fae | Task 7 |
| 6 | Task 9 | fae | Task 7 |
| 7 | Task 10 | Wopal | Task 1-9 |

## Test Plan

自动化测试脚本位于技能源码 `tests/` 目录，`wopal skills install` 部署时自动排除。运行方式：`cd tests && ./run-tests.sh`

#### 单元测试

##### Case U1: `approve` 只按 Plan 文件 commit 判断 push 状态
- Goal: 证明 `is_file_pushed` 只关注"最后一次修改 Plan 文件的 commit 是否进入 `origin/main`"，不被无关 ahead commit 干扰。
- Fixture: `tests/unit/test-approve-push.sh` 在 `/tmp/dev-flow-test-<pid>/` 创建 bare remote、clone、样例 Plan 文件；构造三条提交时间线：(1) Plan commit 已 push + unrelated ahead commit (2) Plan commit 未 push (3) Plan 未 commit。
- Execution:
  - [x] Step 1: 运行 `tests/unit/test-approve-push.sh`
  - [x] Step 2: 确认 3 条场景全部 pass（放行/阻断结论正确）
- Expected Evidence: 只有"最新 Plan commit 不在 origin/main"时返回失败；unrelated ahead commit 场景返回成功。

##### Case U2: `check-doc` 拒绝坏的 Task/Test 结构并放行好样例
- Goal: 证明 `check_doc_plan` 拒绝 `**Changes**` 编号列表、空洞 Test Plan、缺少 User Validation checkbox 的 Plan，放行合法 issue/no-issue plan。
- Fixture: `tests/fixtures/plans/` 下 7 份具名 fixture：`valid-issue-plan.md`、`valid-no-issue-plan.md`、`bad-changes-numbered.md`、`bad-testplan-empty.md`、`bad-user-validation-no-checkbox.md`、`good-user-validation-checked.md`、`old-plan-no-techcontext.md`。
- Execution:
  - [x] Step 1: 运行 `tests/unit/test-check-doc.sh`
  - [x] Step 2: 确认好样例全部通过，坏样例全部被拒且报错位置可定位
- Expected Evidence: `valid-issue-plan` 和 `valid-no-issue-plan` 退出码 0；其余坏样例退出码 1，错误信息指向具体规则。

##### Case U3: `check_user_validation` 只接受显式用户确认 checkbox
- Goal: 证明 User Validation gate 不因"有纯文本内容"就放行，最终必须落在用户勾选的 checkbox 上。
- Fixture: `tests/fixtures/plans/` 下 3 份 verifying Plan fixture：`bad-user-validation-no-checkbox.md`（仅纯文本）、`good-user-validation-checked.md`（checkbox 未勾选变体）、`good-user-validation-checked.md`（checkbox 已勾选变体）。脚本运行时动态修改 checkbox 状态。
- Execution:
  - [x] Step 1: 运行 `tests/unit/test-user-validation.sh`
  - [x] Step 2: 确认纯文本和未勾选均失败，已勾选才成功
- Expected Evidence: 前 2 份返回失败并指出缺失/未勾选的最终确认项；第 3 份返回成功。

#### 集成测试

##### Case I1: Issue renderer 三路输出共享同一 contract
- Goal: 证明 fix 类 Issue 的默认 body、结构化 body、Plan→Issue body 在 section 顺序和关键字段上保持一致。
- Fixture: `tests/integration/test-issue-contract.sh` 使用 `tests/fixtures/plans/` 中的 fix plan 样例，source `lib/issue.sh`、`lib/plan-sync.sh`，对比三路输出。
- Execution:
  - [x] Step 1: 运行 `tests/integration/test-issue-contract.sh`
  - [x] Step 2: 确认三路输出 section 顺序一致，fix body 有审计 section，non-fix body 无
- Expected Evidence: `build_structured_issue_body`、`build_issue_body_from_plan`、`templates/issue.md` 的 section 标题行完全一致；fix body 包含 Confirmed Bugs / Content Model Defects / Cleanup Scope / Key Findings。

##### Case I2: 无 Issue 模式 `complete --pr` 走共享 helper
- Goal: 证明无 Issue `complete --pr` 已接入真实 PR helper，不再调用未定义函数。
- Fixture: `tests/integration/test-no-issue-pr.sh` 在 `/tmp/dev-flow-test-<pid>/` 创建临时项目 repo、feature branch、样例 Plan 和 stub `gh`（将调用参数写入日志文件）。
- Execution:
  - [x] Step 1: 运行 `tests/integration/test-no-issue-pr.sh`
  - [x] Step 2: 确认 stub `gh` 日志包含 `gh pr create`，参数含 repo/base/title/body
- Expected Evidence: 流程无未定义函数错误；stub 日志记录到正确的 `gh pr create` 调用。

##### Case I3: `verify --confirm` 未勾选时阻断，勾选后才放行
- Goal: 证明 verify 阶段的运行时 gate 真正依赖用户最终确认 checkbox。
- Fixture: `tests/integration/test-verify-gate.sh` 使用 `tests/fixtures/plans/verifying-plan.md`（含 2 个用户场景 + 未勾选最终 checkbox），运行时动态修改 checkbox 状态。
- Execution:
  - [x] Step 1: 运行 `tests/integration/test-verify-gate.sh`
  - [x] Step 2: 确认未勾选时被阻断，勾选后放行
- Expected Evidence: 第一次 `verify --confirm` 返回非零并提示先完成 User Validation；修改 checkbox 为 `[x]` 后第二次返回成功。

#### E2E 测试

N/A — 核心端到端场景已由集成测试覆盖；完整的 Issue 同步链路验证需真实 GitHub 环境，通过 User Validation 由用户人工执行。

### Regression Testing

N/A — 旧 Plan 兼容性（R1）和 verifying Plan 补勾选（R2）已分别在 U2（old-plan fixture 通过 check_doc_plan）和 U3（checkbox 动态修改）中覆盖。

### Adjustment Strategy

- 如果真实 GitHub / 远程环境不可用于 PR 或 Issue 写回测试，先在 `.tmp` 用 stub `gh` 完成功能级验证，再补一轮真实环境 smoke test。
- 如果共享 renderer 迁移暴露出 fix / non-fix issue 对 section 需求不同，优先采用“同一 renderer + 可选 section”而不是再拆第二套 renderer。
- 如果旧 Plan 无法提供命名子段落，plan-sync 必须走兼容 fallback，不能因为新 contract 让旧 Plan 的同步直接失效。
- 如果某个测试类别没有真实价值，明确写 `N/A — 理由`，不要为了凑齐 Unit / Integration / E2E / Regression 标题而编造案例。

## Acceptance Criteria

### Agent Verification

- [x] `approve.sh` 的 push 检测已经基于"Plan 文件最后一次修改 commit 是否进入 `origin/main`"，不再依赖文件路径或仓库级 ahead 数。
- [x] `archive.sh` 不再在 `root_dir` 初始化前读取它，项目工作区检测使用的是正确 workspace root。
- [x] 无 Issue 模式 `complete --pr` 走的是存在且可验证的共享 PR helper，不再调用未定义函数。
- [x] `check-doc` 同时接受 `<issue>-<type>-<slug>` 与 `<type>-<slug>`，且 Issue Plan 的编号一致性检查仍然有效。
- [x] `check-doc` 会拒绝 `**Changes**` 使用编号列表或 step 出现在错误段落的 Plan，只放行 `- [ ] Step N:` 结构正确的 Task。
- [x] `templates/plan.md` 的 `## Test Plan` 已提供最小可执行 Case 骨架：`Goal / Fixture / Execution / Expected Evidence + Step checkbox`，并明确允许 `N/A — 理由`。
- [x] `check-doc` 会拒绝只有空洞 bullet、缺少执行步骤或缺少通过证据的 Test Plan，不再把"标题很多但无法执行"的方案判定为合格。
- [x] `templates/plan.md` 与 `SKILL.md` 的 `### User Validation` 已提供场景设计骨架，并包含唯一的最终用户确认 checkbox。
- [x] `check_user_validation` 与 `verify --confirm` 已收紧为硬 gate：最终确认 checkbox 未勾选时，命令必须阻断而不是继续通过。
- [x] fix 类 Issue 的默认模板、结构化创建链路、plan-sync 链路使用同一套 section contract，并能稳定表达 `Confirmed Bugs`、`Content Model Defects`、`Cleanup Scope`、`Key Findings`。
- [x] approve / complete / verify / archive 过程中的 Issue 同步不会再把上述审计事实覆盖丢失。
- [x] 本次涉及文件中的重复 body 拼装逻辑、无效变量和旧分支已清理，且对外命令语义未发生变化。

### User Validation

#### Scenario 1: 新模板生成的 User Validation 骨架可直接用于人工验证
- Goal: 确认未来 agent 用 dev-flow 新建 Plan 时，`### User Validation` 不再是空洞两行，而是带场景骨架和最终确认 checkbox。
- Precondition: 用更新后的模板创建一份临时 Plan。
- User Actions:
  1. 打开生成的 Plan，定位 `### User Validation`。
  2. 检查是否存在 `Scenario / Goal / Precondition / User Actions / Expected Result` 骨架。
  3. 检查是否存在唯一的最终确认 checkbox，且默认是未勾选。
- Expected Result: 模板输出提供可直接填写的用户场景骨架，并包含唯一的最终确认 checkbox；不再出现只有两条空泛 bullet 的旧结构。

#### Scenario 2: `verify --confirm` 只有在用户勾选最终确认后才允许通过
- Goal: 确认 agent 不能在用户未勾选时自作主张通过验证环节。
- Precondition: 准备一份处于 `verifying` 状态的样例 Plan，`### User Validation` 已填写场景，但最终确认 checkbox 仍为未勾选。
- User Actions:
  1. 让 agent 执行 `flow.sh verify <plan> --confirm`。
  2. 确认命令被阻断，并提示先完成 User Validation。
  3. 在你实际完成场景验证后，将最终确认 checkbox 改为 `[x]`。
  4. 再让 agent 执行 `flow.sh verify <plan> --confirm`。
- Expected Result: 第一次执行被明确阻断；只有在你亲自勾选最终确认 checkbox 后，第二次执行才允许进入 `done`。

- [x] 用户已完成上述验证场景，并确认本次变更涉及的功能结果符合预期。

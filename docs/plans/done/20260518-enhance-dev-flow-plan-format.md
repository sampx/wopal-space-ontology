# enhance-dev-flow-plan-format

## Metadata

- **Type**: enhance
- **Target Project**: wopal-space-ontology
- **Project Path**: .wopal
- **Project Type**: ontology-worktree
- **Created**: 2026-05-16
- **Status**: done

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

优化 dev-flow 技能 Plan 方案的格式与内容规范，从三个方向提升方案的可表达性、可执行性和验证清晰度。

## Technical Context

### Architecture Context

当前 dev-flow Plan 模板（`templates/plan.md`，213 行）定义了从 Metadata 到 Acceptance Criteria 的完整结构，通过 `check_doc.py` 强制校验格式。核心流程依赖三篇文件：

| 文件 | 作用 |
|------|------|
| `templates/plan.md` | 定义 Plan 骨架和字段引导注释 |
| `references/plan-validation.md` | 定义校验规则和使用方式 |
| `scripts/dev_flow/domain/validation/check_doc.py` | 执行实际校验逻辑 |

模板和校验的耦合点：模板中的 HTML 注释（`<!-- ... -->`）是给 Planner 的引导，而 `check_doc.py` 通过正则匹配结构化字段（如 Done checkbox `- [ ]` 格式、`**Design**:` 字段）。两者必须同步更新。

### Research Findings

基于对 WSF（space-flow 项目）的深度研究，提取到以下可适配的设计原则：

**1. WSF 的 Technical Context 分层设计**：WSF 通过 CONTEXT.md（用户决策）、RESEARCH.md（技术调查）、PLAN.md 内 `<interfaces>` 块（类型契约）三层传递上下文。启示：dev-flow 的单 Plan 文件应在 Technical Context 章节承载研究结论和关键接口定义。

**2. WSF 的 Task 设计**：每个 Task 包含 `<name>`, `<files>`, `<read_first>`, `<action>`, `<verify>`, `<done>` 六个字段，其中 `<action>` 是完整实施指引（含具体值、约束、避免项）。同时支持 TDD 标记（`tdd="true"`）和独立 TDD Plan 类型（`type: tdd`）。启示：dev-flow Task 需增加 `Design` 和 `TDD` 字段，从 Step 罗列升级为完整设计方案。

**3. WSF 的自动化优先原则**：Agent 验证必须是 `<automated>` 命令可判定 pass/fail 的；用户只做人工感知验证（视觉、交互、体验），从不运行 CLI 命令。启示：dev-flow 的 Agent Verification 和 User Validation 必须明确边界规则。

**参考资料**：
- `projects/space-flow/agents/wsf-planner.md` — WSF Planner 设计（Task 分解、TDD 检测、Goal-backward 验证）
- `projects/space-flow/agents/wsf-executor.md` — WSF Executor 设计（deviation rules、checkpoint 协议、commit 协议）
- `projects/space-flow/docs/zh-CN/references/tdd.md` — WSF TDD 参考（RED→GREEN→REFACTOR、何时用 TDD）
- `projects/space-flow/docs/zh-CN/references/verification-patterns.md` — WSF 验证分层模式（存在/实质性/连接/功能性）

### Key Decisions

- D-01: Technical Context 拆为 4 子节（Architecture Context / Research Findings / Key Decisions / Key Interfaces），均非必填以保持轻量。Research Findings 要求附带参考资料列表——文件路径或 URL 链接——确保研究来源可追溯
- D-02: Task 结构增强：新增 Pre-read、Design、TDD、Behavior、Verify（命令化）、Done（含 checkbox）字段。Changes 改为清晰编号列表（1. 2. 3.），去掉所有 checkbox。每个 Task 仅在 Done 处设一个 checkbox——Agent 运行 Verify 命令通过后才可打勾
- D-03: 删除 `## Test Plan` 章节——WSF 无此章节，验证归于 Task 内 `**Verify**`（单 Task 范围）+ `### Agent Verification`（跨 Task 范围）+ `### User Validation`（人工感知项）。按测试类型分类（Unit/Integration/E2E/Regression）无法回答"Agent 能否自动执行"这个核心问题
- D-07: **TDD 驱动结构** — Agent Verification 移至 Implementation 之前（位于 Affected Files 之后，保持上下文连通）。方案级作用是让审阅者在掌握全部上下文后、进入实现细节前，先看到成功标准。TDD 的实质约束在 Task 级别：每个 Task 的 `**Behavior**` 在 `**Design**` 之前 + `**Verification Intent**` 关联 AC 项 + `**Verify**` 必须可执行。AC 章节前置是 readability 设计，不是 TDD 执行机制
- D-04: Agent Verification 强制命令化——每条必须写具体命令和预期输出，纯描述性条目校验阻断
- D-05: User Validation 限人工感知项——禁止放入构建/测试/lint 等 Agent 可自动判定的验证
- D-06: Delegation Strategy 模板注释大幅增强——嵌入 wave 分配规则（同 wave files 不交集，高 wave 依赖低 wave）、默认委派规则、Autonomous 标记概念、强依赖处理规则、步骤上限、上下文评估规则、wave 间门控规则。与 WSF 完全对齐。Agent 创建新 Plan 时看到注释即可生成合理的委派策略
- D-08: **Verify 字段的务实约束** — `**Verify**` 必须非空（check_doc.py 已有校验）。允许两种形式：shell 命令（如 `rg -c 'pattern' file`）或 `Manual — 理由`（纯人工验证场景）。不做命令格式验证——判断一段文本是否"真的可执行"是正则无法完成的任务。真正的约束在执行纪律：Agent 必须运行 Verify 命令看到 exit 0 后才能勾选 Done checkbox。WSF 同样不校验命令格式，约束力来自 executor 强制执行 verify 步骤

### Key Interfaces

模板更新涉及校验逻辑的同步修改。`check_doc.py` 当前关键校验点：

```python
# 当前校验项（需保留并扩展）：
# - Done checkbox 存在性（- [ ] 格式）
# - Task.Design 字段存在性（非空，但不强制详细级别）
# - Agent Verification 条目是否含命令（grep 模式可检测）
# - User Validation 条目是否含构建/测试类关键词（负向检测）
```

## In Scope

- 更新 `templates/plan.md`：重构 Technical Context 章节（4 子节）、增强 Task 结构（新增 Pre-read/Design/TDD/Behavior/Verify/Done）、重新定义验证章节边界
- 更新 `references/plan-validation.md`：同步校验规则变更，新增 Agent Verification 命令化规则、User Validation 排除规则
- 更新 `scripts/dev_flow/domain/validation/check_doc.py`：新增字段校验逻辑（Task 必要字段检查、Agent Verification 命令格式检查）
- 更新 `scripts/dev_flow/commands/sync.py`：适配新 Plan 格式——Technical Context 结构变更（4 子节）、AC 章节位置不变但需确认提取逻辑不受影响、删除 Test Plan 相关引用
- 更新 `scripts/dev_flow/domain/issue/sync.py`：同步修复 `_build_issue_body_from_plan` 中的 Technical Context 提取逻辑
- 更新 `SKILL.md`：同步 Plan 编写指引、验证层级说明；排查并更新全部旧格式引用（"步骤勾选范围"→"Done 打勾"、"Step completion"→"Done completion"、"Test Plan 章节"→删除引用、边缘场景和错误处理表中的旧描述）
- 新增 `references/tdd-guide.md`：TDD Plan 编写指南（小体量，~80 行）

## Out of Scope

- Issue 模板不在此次范围（本次只改 Plan 模板）
- `flow.sh` 命令参数和状态机不变（`plan`、`approve`、`complete`、`verify --confirm`、`archive` 的命令行接口保持不变）
- `flow.py` 不变（CLI 解析层不变）
- 现有 Plan 文件不做迁移（新模板对存量 Plan 无影响，存量 Plan 校验沿用旧规则——通过保留旧校验分支实现兼容）

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| **Plan 模板** | `templates/plan.md` | 大幅修改 | 重构全部章节结构和引导注释 |
| **校验规则文档** | `references/plan-validation.md` | 大幅修改 | 同步校验规则变更 |
| **校验脚本** | `scripts/dev_flow/domain/validation/check_doc.py` | 修改 | 新增字段校验逻辑 |
| **Sync 脚本（手动）** | `scripts/dev_flow/commands/sync.py` | 修改 | `flow.sh sync` 命令：适配 Technical Context 新格式 |
| **Sync 脚本（自动）** | `scripts/dev_flow/domain/issue/sync.py` | 修改 | `complete`/`approve`/`archive`/`verify` 内部调用：同步适配 |
| **技能文档** | `SKILL.md` | 修改 | 同步新 Plan 编写指引 |
| **TDD 指南** | `references/tdd-guide.md` | 创建 | TDD Task 编写指南 |

## Acceptance Criteria

### Agent Verification

- [x] `templates/plan.md` 包含 Technical Context 4 子节（Architecture Context / Research Findings / Key Decisions / Key Interfaces）
- [x] `templates/plan.md` 中 Research Findings 引导注释含"参考资料列表"要求（文件路径或 URL 链接）
- [x] `templates/plan.md` 中 Acceptance Criteria 章节位于 Implementation 之前
- [x] `templates/plan.md` 中 Task 字段顺序为 Verification Intent → Behavior → Design
- [x] `templates/plan.md` 中 Task Changes 引导注释含"编号列表，无 checkbox"要求
- [x] `templates/plan.md` 中 Task Done 引导注释含唯一 checkbox 格式要求
- [x] `check_doc.py` 中校验 Task 的 Verification Intent 非空、Behavior 非空、Behavior 在 Design 之前
- [x] `templates/plan.md` 中 Agent Verification 引导注释含"命令 → 预期输出"要求
- [x] `templates/plan.md` 中 User Validation 引导注释含"排除自动化验证项"规则
- [x] `references/plan-validation.md` 已同步所有新规则（Technical Context 子节、Task 新字段、验证分层规则、兼容策略）
- [x] `check_doc.py` 中 `detect_template_version` 函数通过 `### Architecture Context` 识别新模板
- [x] `check_doc.py` 中 `check_task_structure` 校验 Task 的 Design 非空、TDD=true 时 Behavior 必填
- [x] `check_doc.py` 中 `check_agent_verification` 校验 Agent Verification 至少一条含可执行命令
- [x] `check_doc.py` 中 `check_user_validation` 校验 User Validation 不含构建/测试命令
- [x] `check_doc.py` 对旧模板 Plan 文件校验不回归（兼容）
- [x] `SKILL.md` 已同步新 Plan 编写指引和验证规则，无"Step checkbox""Test Plan""步骤勾选范围"等旧格式残留引用
- [x] `flow.sh complete` 命令能正确检查新模板 Plan 的 Done checkbox 完成状态（无 Step checkbox 遗留检查导致误判失败）
- [x] `references/tdd-guide.md` 已创建，包含 TDD 判断启发式、写法、提交建议、错误处理
- [x] 所有新增 `flow.sh` 命令（plan/approve/complete/verify/archive）对新模板正常可用（通过 smoke tests）— #144（新模板）走完 plan→approve→done→archive 全生命周期验证通过
- [x] `python scripts/dev_flow/domain/validation/check_doc.py <.tmp 中的新模板 Plan>` 返回 0（新格式校验通过）
- [x] `python scripts/dev_flow/domain/validation/check_doc.py docs/products/wopal-space-ontology/plans/140-*.md` 返回 0（旧格式校验不回归）
- [x] 对故意违规的 Plan（缺 Design、TDD=true 无 Behavior、Agent Verification 无命令）执行 `check_doc.py`，返回非 0 且错误信息明确指向对应字段
- [x] `cd .wopal/skills/dev-flow && bash scripts/flow.sh plan 140 --check` 返回 0（--check 参数可用）— 已验证通过
- [x] `cd .wopal/skills/dev-flow && bash scripts/flow.sh sync <issue> --body-only` 对新模板 Plan 生成正确 Issue body（Technical Context 结构化提取，无 Test Plan 残留）
- [x] `cd .wopal/skills/dev-flow && bash scripts/flow.sh sync <old-issue> --body-only` 对旧模板 Plan 生成正确 Issue body（无回归）

### User Validation

#### Scenario 1: 新模板编写体验验证
- Goal: 确认 Planner 使用新模板编写方案时，引导注释充分，编写流程顺畅
- Precondition: 开发任务就绪，需从零编写一份 Plan
- User Actions:
  1. 加载 dev-flow 技能，执行 `flow.sh plan` 创建新 Plan
  2. 按新模板引导注释逐章节填写 Plan 内容
  3. 观察引导注释是否清晰（尤其 Technical Context 4 子节的边界、Task Design 与 Changes 的区别、Agent/User 验证的边界）
  4. 执行 `flow.sh plan --check` 确认校验通过
- Expected Result: 引导注释帮助 Planner 无歧义地完成填写，校验一次性通过（无需反复修改格式）

#### Scenario 2: TDD Task 编写和执行
- Goal: 确认 TDD Task 的 Behavior → Design → Changes 循环能产出可执行方案
- Precondition: 一个适合 TDD 的开发任务（如"添加 email 验证函数"）
- User Actions:
  1. 在 Plan 中创建一个 TDD Task（`**TDD**: true`）
  2. 填写 Behavior（输入→输出映射）
  3. 填写 Design（RED → GREEN → REFACTOR 步骤）
  4. 填写 Changes 步骤（对应 TDD 三阶段）
  5. 交予 Agent 执行，观察 RED 和 GREEN 阶段是否按预期提交
- Expected Result: Agent 能按 Behavior → 写测试 → 实现 → 重构顺序执行，每个阶段独立提交

- [x] 用户已完成上述功能验证并确认结果符合预期

## Implementation

### Task 1: 重构 Plan 模板

**Files**: `templates/plan.md`
**TDD**: false
**Behavior**: 模板文件按新结构重写后，包含 Technical Context 4 子节、Task 新增字段且在正确顺序、Test Plan 章节已删除、AC 在 Implementation 之前

**Pre-read**: `references/plan-validation.md`, `SKILL.md`

**Design**:
将 213 行模板重构为新的 5 区域结构。关键技术决策：

1. **Technical Context** 拆为 4 子节（均为可选）：
   - `### Architecture Context` — 当前架构现状、涉及模块
   - `### Research Findings` — 前期研究结论摘要。**必须附带参考资料列表**——研究来源的文件路径（如 `projects/space-flow/agents/wsf-planner.md`）或 URL 链接。确保后续审阅者可追溯到原始研究材料
   - `### Key Decisions` — 已确定技术决策（D-01 格式）
   - `### Key Interfaces` — 关键类型/接口定义

2. **TDD 驱动结构**（章节重排 + Task 内字段重排）：
   - **章节重排**：`## Acceptance Criteria` 移至 `## Affected Files` 之后、`## Implementation` 之前。上下文流为：Goal → Technical Context → In Scope → Out of Scope → Affected Files → AC → Implementation。审阅者在了解全部上下文后看到成功标准，再进入实现设计。
   - **Task 内字段重排**：`**Behavior**` 移至 `**Design**` 之前。每个 Task 必须先描述预期行为，再写实现设计。同时新增 `**Verification Intent**` 字段指向对应的 AC 项。
   - **非 TDD Task 的处理**：对于纯配置/删除/文档类 Task（无测试化行为），`**TDD**: false`，`**Behavior**` 描述预期状态变化（如"wopal-task-diff.ts 文件不再存在"）。

3. **Task 结构增强**（新增字段，按 TDD 顺序排列）：
   - `**Verification Intent**` — 引用的 AC 项（必填：本 Task 对应 Agent Verification 的哪几条）
   - `**Behavior**` — 预期行为（必填：TDD 驱动，在 Design 之前定义"什么是对的"；非代码 Task 描述预期状态变化）
   - `**Files**` — 涉及文件（保留）
   - `**Pre-read**` — 实施前需阅读的文件（可选字段，无必要可 N/A）
   - `**Design**` — 完整实施设计（必填，但必须在 Behavior 之后）
   - `**TDD**` — TDD 标记：`true` 或 `false`（默认 false；true 时 Changes 按 RED→GREEN→REFACTOR 组织）
   - `**Changes**` — 实施改动列表，编号格式（1. 2. 3.），无 checkbox
   - `**Verify**` — 内联验证命令（必填：Agent 可自动执行的命令或 `Manual — 理由`）
   - `**Done**` — 任务产出说明（一句话描述）+ 唯一 checkbox：
     ```
      - [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）
      ```

   **每 Task 仅 1 次 Plan 编辑**：Done 打勾。无其他 checkbox。

4. **验证分层重构**：
   - 删除 `## Test Plan` 章节——WSF 的设计证明了按测试类型分类（Unit/Integration/E2E/Regression）无法回答"Agent 能否自动执行"的核心问题，该章节在 Agent 执行流程中形同虚设
   - `### Agent Verification` — 每条的引导注释明确要求"可自动执行的命令+预期输出"，承载原 Test Plan 中可自动化的跨 Task 验证
   - `### User Validation` — 引导注释新增排除规则："禁止放入 Agent 可自动验证的项"
   - 新增 `<!-- agent-verify-guard -->` 标记供校验脚本定位

5. **注释策略**：
   - 每个新增字段附带 `<!-- 注释 -->` 引导 Planner
   - 关键约束用 `⚠️` 前缀标出
   - Changes 为编号列表（`1. ` `2. ` 格式），Done 为唯一 checkbox（`- [ ]` 格式）

**Changes**:
1. 重写 `## Technical Context` 为 4 子节结构，每个子节附带引导注释和示例占位符
2. 将 `## Acceptance Criteria` 章节移至 `## Affected Files` 之后、`## Implementation` 之前（模板中物理重排）
3. 重构 `### Task N` 字段顺序为 Verification Intent → Behavior → Files → Pre-read → Design → TDD → Changes（编号列表）→ Verify → Done（含 checkbox），去掉 Changes 中的 `- [ ] Step N:` checkbox 格式
4. 重写 `## Delegation Strategy` 注释，嵌入以下委派决策规则（与 WSF wave 概念对齐）：
   - **Wave 分配**：用 wave 代替批次编号，同 wave 内 Task 并行执行（files 不交集）；高 wave 依赖低 wave
   - **默认委派规则**：实施类 Task 默认委派 fae，Wopal 只做切片和验证。极简单任务（≤3 步，无外部依赖）可由 Wopal 直接执行
   - **Autonomous 标记**：每个 Task 需说明是否含 checkpoint；含 checkpoint 则标记 `autonomous: false` 并在 fae prompt 中明确停止点
   - **强依赖处理**：多个 Task 存在强逻辑依赖时整组委派给单个 fae（不拆分），在 prompt 中明确顺序
   - **步骤上限**：单个委派任务 ≤30 步
   - **上下文评估**：预估 Task 读改测总步数 ≥ 自己执行成本时才委派
   - **Wave 间门控**：每 wave 完成后 Wopal 运行 Verify 命令验证产出，通过后才释放下一 wave
5. 删除模板中 `## Test Plan` 章节及其所有子节（Unit/Integration/E2E/Regression Tests）
6. 重写 `### Agent Verification` 引导注释，强制要求"命令 → 预期输出"格式，新增禁止项清单，说明此处同时承载单 Task 内验证和跨 Task 集成验证
7. 重写 `### User Validation` 引导注释，新增"排除自动化验证项"规则和禁止项清单
8. Review 完整模板，确认所有引导注释覆盖新规则，HTML 注释语法正确，章节顺序为 Goal → Technical Context → In Scope → Out of Scope → Affected Files → Acceptance Criteria → Implementation → Delegation，无 Test Plan 残留引用

**Verify**:
1. `rg -c '### Architecture Context' templates/plan.md` ≥ 1（Architecture Context 子节存在）
2. `rg -c '### Research Findings' templates/plan.md` ≥ 1（Research Findings 子节存在）
3. `rg -c '### Key Decisions' templates/plan.md` ≥ 1（Key Decisions 子节存在）
4. `rg -c '### Key Interfaces' templates/plan.md` ≥ 1（Key Interfaces 子节存在）
5. `rg -c '## Test Plan' templates/plan.md` = 0（Test Plan 章节已删除）
6. `rg -c '\*\*Behavior\*\*' templates/plan.md` ≥ 2（Task 模板含 Behavior 字段，出现 ≥2 次确认在模板注释和占位 Task 中）
7. `rg -c '\*\*Verification Intent\*\*' templates/plan.md` ≥ 1（Verification Intent 字段存在）
8. `rg -c '\*\*TDD\*\*' templates/plan.md` ≥ 1（TDD 标记存在）
9. Step checkbox 格式 `- [ ] Step N:` 已从模板中移除（`rg -c '\- \[ \] Step \d+:' templates/plan.md` = 0）
10. Done checkbox 格式存在（`rg -c '\- \[ \]' templates/plan.md` ≥ 2，确认在人类审阅提示和 Task Done 中存在）
11. Delegation Strategy 注释含 wave 概念（`rg -c 'wave\|Wave' templates/plan.md` ≥ 1）

**Done**:
任务产出：plan.md 模板含 Technical Context 4 子节 + 无 Test Plan 章节 + Tasks 含 Verification Intent/Behavior/Design/TDD/Verify/Done + Changes 为编号列表 + AC 在 Implementation 之前
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

### Task 2: 更新校验规则文档

**Files**: `references/plan-validation.md`
**TDD**: false
**Behavior**: 校验规则文档与新模板字段一一对应，Agent/User 验证规则边界清晰，新旧模板兼容策略已说明

**Pre-read**: `templates/plan.md`（已更新的模板）, `scripts/dev_flow/domain/validation/check_doc.py`

**Design**:
将校验规则从当前的单表结构重构为分章节说明，与模板新结构对应。关键变更：

1. **Technical Context 校验**：`Technical Context` 非空 → 改为顶层非空即可（不强制 4 子节都填，只要求至少一个有内容）
2. **Task 字段校验**：新增 `Design` 非空检查，`TDD=true` 时 `Behavior` 必填检查，`Verify` 字段格式检查
3. **删除 Test Plan 校验**：移除 Test Plan 章节的格式校验要求——该章节已从新模板中删除
4. **Agent Verification 校验**：新增"至少一条含可执行命令"规则——检测条目中是否包含 `reg '\.\/|npm|bun|pip|go|pytest|cargo|curl'` 或类似 shell 命令模式
5. **User Validation 校验**：新增负向检测——条目中不得包含 `npm test`, `bun run`, `tsc`, `cargo build` 等构建/测试命令
6. **兼容性说明**：旧模板 Plan 文件校验保持不变（通过识别模板版本区分）

**Changes**:
1. 重写"重点检查项"表格，新增 Technical Context 子节检查、Task 新增字段检查
2. 新增"Agent Verification 校验规则"小节，定义命令化检测逻辑和禁止项清单
3. 新增"User Validation 校验规则"小节，定义排除规则和禁止项清单
4. 删除"Test Plan 章节怎么写"小节，改为在 Agent Verification 规则中说明跨 Task 验证的编写方式
5. 新增"新旧模板兼容"小节，说明识别机制和校验分支
6. 更新"使用方式"小节示例命令

**Verify**:
1. `rg -c 'Technical Context' references/plan-validation.md` ≥ 2（校验规则多次引用 Technology Context）
2. `rg -c 'Verification Intent' references/plan-validation.md` ≥ 1（Verification Intent 字段校验已记录）
3. `rg -c 'Behavior' references/plan-validation.md` ≥ 1（Behavior 字段校验已记录）
4. `rg -c '命令化\|可执行命令\|automated' references/plan-validation.md` ≥ 1（Agent Verification 命令化要求已记录）
5. `rg -c 'npm test\|bun run\|tsc\|pytest' references/plan-validation.md` ≥ 1（User Validation 禁止项清单含构建/测试命令）
6. `rg -c 'Test Plan' references/plan-validation.md` = 0（Test Plan 章节引用已清除）

**Done**:
任务产出：plan-validation.md 含 Task 新字段校验规则 + Agent/User 验证分层规则 + 新旧模板兼容策略 + Test Plan 引用已清除
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

### Task 3: 更新校验脚本

**Verification Intent**: AC 引用 `check_doc.py` 中 4 个新校验函数的正确性（detect_template_version / check_task_structure / check_agent_verification / check_user_validation）

**Behavior**:
- `detect_template_version(content_with_arch_context) → "new"`, `detect_template_version(content_without) → "old"`
- `check_task_structure(missing_design) → ["MISSING: Design"]`, `check_task_structure(complete) → []`
- `check_task_structure(tdd_true_no_behavior) → ["MISSING: Behavior (TDD=true requires Behavior)"]`
- `check_task_structure(behavior_after_design) → ["ORDER: Behavior must precede Design"]`
- `check_task_structure(done_no_checkbox) → ["MISSING: Done must contain at least one checkbox"]`
- `check_task_structure(changes_has_step_checkbox) → ["FAIL: Changes must not contain checkbox format"]`
- `check_agent_verification(no_commands) → ["FAIL: At least one AC item must contain executable command"]`
- `check_agent_verification(ac_after_impl) → ["FAIL: Agent Verification must appear before Implementation"]`
- `check_user_validation(contains_npm_test) → ["FAIL: User Validation must not contain automated test commands"]`
- 旧模板 Plan 经新校验脚本后，旧规则路径全部通过（兼容）

**Files**: `scripts/dev_flow/domain/validation/check_doc.py`

**Design**:
在现有 `check_doc.py` 基础上新增 4 个校验函数 + 版本检测分流。实现策略：

- **RED**：先写单元测试覆盖上述 Behavior 中所有场景（在 `.tmp/test-check-doc/` 下创建 fixture Plan 文件），测试全部失败
- **GREEN**：逐个实现 `detect_template_version` → `check_task_structure` → `check_agent_verification` → `check_user_validation`，每个函数实现后跑对应测试至通过
- **REFACTOR**：提取公共正则模式（`DESIGN_PATTERN`, `BEHAVIOR_PATTERN`, `TDD_PATTERN`, `COMMAND_PATTERN`）到模块级常量

兼容策略：检测 Plan 文件是否含 `### Architecture Context` → 是则走新规则，否则走旧规则（旧逻辑保留不变）。

**TDD**: true

**Changes**:
1. （RED）在 `.tmp/test-check-doc/` 创建 fixture Plan 文件（覆盖新格式通过、旧格式通过、缺 Design、缺 Behavior、Behavior 在 Design 后、Done 无 checkbox、Changes 含 Step checkbox、AC 无命令、AC 在 Impl 后、User Val 含测试命令等场景），编写 pytest 测试函数验证预期行为
2. （RED）运行测试，确认全部 FAIL（预期行为尚未实现）
3. （GREEN）实现 `detect_template_version(content)` — 检测 `### Architecture Context` 存在性，运行对应测试至 PASS
4. （GREEN）实现 `check_task_structure(content)` — 校验 Design/Behavior/TDD/Verify/Verification Intent/Done(含 checkbox)/Changes(无 Step checkbox) 字段及顺序，同时修改 `check_doc.py` 中 `complete` 门控逻辑：将 Step checkbox 完成检查改为 Done checkbox 完成检查（或确认 `complete` 命令通过 check_doc.py 委托此校验）
5. （GREEN）实现 `check_agent_verification(content)` — 校验命令化 + AC 前置 + Intent 引用存在，运行对应测试至 PASS
6. （GREEN）实现 `check_user_validation(content)` — 校验排除构建/测试命令，运行对应测试至 PASS
7. （GREEN）修改主校验入口，根据模板版本分流新旧校验分支；运行旧模板 Plan 确认兼容不回归
8. （REFACTOR）提取公共正则模式到模块级常量，确保所有测试仍 PASS

**Verify**: `python -m pytest tests/test_check_doc.py -v`（TDD 测试全部 pass，覆盖新格式通过、旧格式通过、8 种违规场景拦截）

**Done**:
任务产出：check_doc.py 新增 4 个校验函数均有对应测试覆盖，新旧模板双轨校验正常，RED→GREEN→REFACTOR 三阶段各产生独立提交
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

### Task 4: 更新技能文档 + 新增 TDD 指南

**Files**: `SKILL.md`, `references/tdd-guide.md`（创建）
**TDD**: false
**Behavior**: SKILL.md 已同步新 Plan 编写指引，tdd-guide.md 创建完成，SKILL.md 无旧格式残留引用

**Pre-read**: `templates/plan.md`（已更新的模板）, `references/plan-validation.md`（已更新的规则）

**Design**:
1. **SKILL.md 修改**（最小化改动）：
   - 更新"Plan 质量门"章节 — 新增"校验覆盖 Task 新字段"说明
   - 更新"Acceptance Criteria 的使用方式"章节 — 同步 Agent/User 验证边界规则
   - 更新"参考"表格 — 新增 tdd-guide.md 条目
   - 不新增章节，保持现有结构

2. **新增 tdd-guide.md**（~80 行）：
   - TDD 判断启发式（何时用 TDD，何时不用）
   - Task 内 TDD 写法（Behavior/Design/Changes 的 TDD 模式）
   - 提交建议（RED → GREEN → REFACTOR 三提交）
   - 错误处理（RED 不失败、GREEN 不过、REFACTOR 回退）

**Changes**:
1. 更新 SKILL.md "Plan 质量门"章节，新增 Task 新字段校验说明 + 委派策略指引的模板注释说明
2. 更新 SKILL.md "Acceptance Criteria 使用方式"章节，明确 Agent Verification 命令化要求和 User Validation 排除规则
3. 更新 SKILL.md "参考"表格，新增 `references/tdd-guide.md` 条目
4. 排查并更新 SKILL.md 中所有旧格式引用： "最容易遗漏的两步"（步骤勾选范围→Done 打勾）、"C. 进入 executing"（每完成步骤勾选→每 Task 运行 Verify 后勾 Done）、"D. 完成实施"（所有步骤勾选→所有 Task Done 勾选）、"complete 硬门控"（Step completion→Done completion）、"边缘场景 #2 #3"（Step 未完成→Done 未勾选）、"错误处理"表（Step completion failed→Done completion failed）
5. 删除 SKILL.md 中所有 Test Plan 章节引用
6. 创建 `references/tdd-guide.md`，包含 TDD 判断启发式、Task 内 TDD 写法、提交建议、错误处理

**Verify**:
1. SKILL.md 修改部分与模板/校验规则一致（三方核对）
2. tdd-guide.md 内容从 WSF 的 `tdd.md` 提取并精简适配，无版权冲突

**Done**:
任务产出：SKILL.md 已同步新规则，tdd-guide.md 创建完成
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

### Task 5: 适配 Sync 脚本

**Verification Intent**: AC 引用 `flow.sh sync --body-only` + 状态转换时自动 sync 均在新模板下正确生成 Issue body

**Behavior**:
- 新模板 Plan 经 `complete`/`approve`/`archive`/`verify` 状态转换时自动 sync → Issue body 的 Background 包含 Technical Context 结构化内容
- `flow.sh sync --body-only` 手动执行 → 同样正确
- 旧模板 Plan sync 无回归

**Files**: `scripts/dev_flow/commands/sync.py`, `scripts/dev_flow/domain/issue/sync.py`

**Pre-read**: `templates/plan.md`（已更新的模板）
**TDD**: false

**Design**:
两份 `build_issue_body_from_plan` 实现都需适配。注意：这是代码重复——`domain/issue/sync.py::_build_issue_body_from_plan`（被 4 个状态转换命令调用）和 `commands/sync.py::build_issue_body_from_plan`（手动 sync 命令）各自维护一份提取逻辑。本次只做功能适配，不合并。

1. **Technical Context 提取增强**：
   - `commands/sync.py`：`_extract_plan_section("Technical Context", 20)` → 检测 4 子节后去掉 20 行限制
   - `domain/issue/sync.py`：`_extract_section(content, "Technical Context")` 同样需要检测 4 子节

2. **Research Findings 提取**：两份都在 Background 中注入 `### Research Findings` 子节

3. **AC 提取确认**：两份的 Accept Criteria 提取均通过 heading 定位，位置无关——但需确认 Agent/User 子节完整提取

4. **技术债标记**：在脚本中加注释注明两份实现重复，后续可合并为共享模块

**Changes**:
1. 新增 `_extract_research_findings(plan_file)` 函数——提取 `### Research Findings` 子节内容
2. 修改 `build_issue_body_from_plan` 中 `background` 提取逻辑——检测新格式后去掉 20 行限制，或拼接 4 子节
3. 修改 `build_issue_body_from_plan` 中 Background 章节——新格式下将 Research Findings 注入 Background 或新增独立章节
4. 确认 `_extract_acceptance_criteria` 在新模板下正确提取（AC 位置无关，但需确认 Agent/User 子节完整提取）
5. 同步更新 `domain/issue/sync.py` 的 `_build_issue_body_from_plan`
6. 验证 `sync --body-only` 在新旧格式 Plan 下均正常生成 Issue body

**Verify**:
1. `python -c "from dev_flow.commands.sync import build_issue_body_from_plan; body = build_issue_body_from_plan('docs/products/wopal-space-ontology/plans/enhance-dev-flow-plan-format.md', 'test', 'sampx/wopal-space'); assert '研究' in body"` 确认新格式 Technical Context 被提取
2. `rg -c 'Test Plan'` 在生成的 Issue body 中为 0
3. `sync --body-only` 对旧格式 Plan（如 #140）仍正常生成——无回归

**Done**:
任务产出：sync 脚本在新旧两种 Plan 格式下均正确生成 Issue body，Technical Context 结构化提取，无 Test Plan 残留
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

## Delegation Strategy

| Wave | Task | 执行者 | 依赖 | 委派理由 |
|------|------|--------|------|---------|
| 1 | Task 1 | **fae** | 无 | 模板 Markdown 文档重写（8 步），纯文件编辑；这是所有 Task 的**基础依赖**，必须最先完成并验证通过后释放 Wave 2 |
| 2 | Task 2 | **fae** | Task 1 | 校验规则文档更新（6 步），与 Task 3 无文件冲突（plan-validation.md ≠ check_doc.py），同 wave 并行 |
| 2 | Task 3 | **fae** | Task 1 | TDD Python 代码（8 步 RED→GREEN→REFACTOR），fae 执行后 pytest 全绿即通过 |
| 3 | Task 4 | **fae** | Task 2 + Task 3 | SKILL.md 更新 + tdd-guide.md 创建（6 步），与 Task 5 无文件冲突（SKILL.md ≠ sync.py），同 wave 并行 |
| 3 | Task 5 | **fae** | Task 2 + Task 3 | sync.py 两份脚本适配（6 步），与 Task 4 并行 |

**执行流程**（WSF wave 模式）：
1. **Wave 1**：启动 fae 执行 Task 1 → fae 返回产出后 Wopal 运行 10 条 grep Verify 命令 → 通过则标记 Task 1 Done，释放 Wave 2
2. **Wave 2**：并行启动 2 个 fae 实例执行 Task 2 + Task 3 → 全部返回后 Wopal 分别运行对应 Verify 命令 → 通过则标记 Done，释放 Wave 3
3. **Wave 3**：并行启动 2 个 fae 实例执行 Task 4 + Task 5 → 全部返回后 Wopal 分别验证 → 执行最终集成验证（pytest + flow.sh sync smoke tests）
4. Wopal 角色：编写委派 prompt、审查每 wave 产出、运行验证命令；不亲自动手实施任何 Task
5. 委派前必须加载 fae-collab 技能，严格执行"检前评审 prompt、产出后验证结果"纪律

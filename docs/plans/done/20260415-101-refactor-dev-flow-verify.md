# 101-refactor-dev-flow-verify

## Metadata

- **Issue**: #101
- **Type**: refactor
- **Target Project**: ontology
- **Created**: 2026-04-15
- **Status**: done

## Scope Assessment

- **Complexity**: High
- **Confidence**: Medium

## Goal

将 dev-flow 重构为 `planning → executing → verifying → done` 四阶段主状态机，使 Plan 状态与 Issue 主状态一一对应，恢复 `verify --confirm` 作为用户验证门，补回 approve 阶段自动提交评审方案的 git 行为，修复 `complete` 后 Issue 中 Agent Verification 未同步的问题，纠正 `--confirm` 命令输出对 agent 的误导表述，并在实施前强制检查目标项目 git 脏工作区风险。

## Technical Context

当前 dev-flow 采用 3-state 主状态机：`planning → executing → done`。无 PR 路径下，`complete` 不会推进主状态，只会给 Issue 叠加 `validation/awaiting`，同时原本应存在的两个流程能力也缺失：其一，提交用户评审的方案没有在 `approve` 阶段自动 git commit；其二，用户确认仍绑在 `archive --confirm`，导致 verify 阶段虽然恢复为主状态，却没有独立的人类门控命令。因此：

1. **Plan 与 Issue 主状态不一致**：Plan 仍为 `executing`，Issue 主状态仍是 `status/in-progress`，真正的“等待验证”只藏在 overlay label 中。
2. **状态语义过载**：`executing` 同时表示“正在编码”和“编码完成等待验证”，Agent 只看主状态会误判当前位置。
3. **查询与文档认知割裂**：`status`/`list`、SKILL.md、help 文案、标签体系都围绕 3-state 描述，但实际流程依赖 `validation/*` 子标签补语义。
4. **Issue 同步存在事实分叉 bug**：`complete` 校验的是 Plan 中 `### Agent Verification` 的勾选结果，但执行完成后没有把这些 `[x]` 状态同步回 Issue body，导致 Issue 仍显示旧的 Acceptance Criteria 内容。
5. **实施入口缺少仓库安全门**：当前进入实施阶段前，没有强制检查目标项目 git 仓库是否有未提交变更，容易把历史脏改动与当前 Issue 混在一起，污染任务边界并提高回滚风险。
6. **评审与验证门控位置失真**：`archive --confirm` 把人类确认放在归档阶段，导致真正重要的“用户验证通过”没有在 verify 阶段显式表达；同时 approve 阶段也没有把待评审 Plan 自动提交到 git，评审对象不稳定。
7. **`--confirm` 输出文案误导 agent**：当前命令输出常写成“用户执行这个命令”，但 skill 的脚本实际始终由 agent 执行。正确语义应是：agent 收到用户明确的“评审通过 / 验证通过”等授权后，再由 agent 执行带 `--confirm` 的命令。现有提示语会误导 agent 认为要让用户亲自运行脚本。

本次应把 `verify` 升格为主状态，建立单一真相：

```text
planning → executing → verifying → done
```

对应要求：

- Plan Status 与 Issue 主状态标签 1:1 对应
- `complete` 从“加 overlay label”改为真正的状态跃迁：`executing -> verifying`
- `verify --confirm` 作为用户验证门，负责确认 `verifying` 阶段通过
- `archive` 退回为归档收尾动作，不再承担核心的人类确认职责
- `approve` 在提交用户评审的方案时自动完成 git commit，保证评审对象稳定
- `complete` 后同步 Issue body 中的 Agent Verification 勾选结果
- 所有 `--confirm` 相关命令输出都必须改为“等待用户授权后由 agent 执行”，不能再表述为“用户自己执行脚本”
- 所有活跃文档、模板、帮助、查询输出、长期记忆统一到 4-state 语义
- 开始实施前必须检查目标项目 git 仓库是否有未提交变更；若存在，则要求用户先提交，或建议使用 worktree 隔离开发，并向用户明确提示风险

风险与边界：

- 影响范围横跨状态机、标签域、命令脚本、查询脚本、模板、技能文档、长期记忆，必须整体更新，不能局部替换
- 已归档历史计划文档（`docs/products/plans/done/`、`docs/products/ontology/plans/done/`）按空间规则不追溯改写，仅更新活跃文档与长期记忆
- 需处理 3-state 到 4-state 的兼容性，避免已有进行中 Issue 因旧标签而查询异常
- 项目 git 脏工作区检查必须以目标项目仓库为准，不能误判空间根仓库或其他子仓库状态

## In Scope

- 将 dev-flow 主状态机升级为 `planning → executing → verifying → done`
- 为 Issue 引入 `status/verifying` 主状态标签，并使 Plan Status 与 Issue 主状态标签保持 1:1 映射
- 重构 `complete`/`verify`/`archive`/`status`/`list`/`reset` 等命令逻辑以匹配 4-state
- 恢复/补回 `approve` 阶段在提交评审方案时自动 git commit 的能力
- 修复 `complete` 后 Issue body 中 `## Acceptance Criteria` 未同步 Agent Verification `[x]` 勾选结果的问题
- 纠正 `approve` / `verify` / `archive` 等 `--confirm` 输出文案，避免误导 agent 让用户自己执行脚本
- 为实施入口增加目标项目 git 脏工作区强制检查、用户提醒与 worktree 建议
- 按 ontology 项目技能规范与 skill-creator 要求重写 `SKILL.md`，确保 frontmatter、触发描述、主体结构、依赖声明与示例说明标准、清晰、准确、简练
- 统一更新 `SKILL.md`、模板、脚本帮助文本、状态映射说明、查询输出
- 显式扫描并清理 `SKILL.md` / 帮助文案 / 示例中的旧 `validate` 命令或 validate-era 验证语义残留，避免新旧流程词汇混用
- 统一更新长期记忆中所有引用旧 3-state/`validation/awaiting` 语义的条目
- 核查并更新活跃文档中对旧状态机的描述，使之与实现一致

## Out of Scope

- 重写 dev-flow 整体架构或命令集合（本次聚焦状态机与同步一致性）
- 改动与本次状态机无关的其他技能
- 已归档历史 Plan / 历史研究文档的追溯改写
- 额外引入新的人工门控命令（维持 `approve --confirm`、`archive --confirm` 两个门）
- 变更与当前 Issue 无关的提交流程约定

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| dev-flow state machine | `projects/ontology/agents/wopal/skills/dev-flow/lib/state-machine.sh`, `lib/labels.sh` | 修改 | 定义 4-state、状态顺序、状态→标签映射、标签组同步 |
| dev-flow command flow | `projects/ontology/agents/wopal/skills/dev-flow/scripts/cmd/complete.sh`, `approve.sh`, `verify.sh`, `archive.sh`, `query.sh`, `utility.sh`, `scripts/flow.sh` | 修改 | 让 complete/verify/archive/status/list/help 与 4-state 一致 |
| dev-flow safety gate | `projects/ontology/agents/wopal/skills/dev-flow/scripts/cmd/approve.sh`, `scripts/cmd/utility.sh`, `lib/common.sh`（如需共享 helper） | 修改 | 实施前强制检查目标项目 git 脏工作区，提示先提交或使用 worktree，并输出风险提醒 |
| dev-flow review commit | `projects/ontology/agents/wopal/skills/dev-flow/scripts/cmd/approve.sh`, 相关 git helper | 修改 | 在提交用户评审方案时自动提交 Plan 变更，保证评审对象稳定 |
| dev-flow issue sync | `projects/ontology/agents/wopal/skills/dev-flow/lib/plan-sync.sh`, `lib/issue.sh`, `lib/plan.sh` | 修改 | complete 后同步 Issue body 中 Agent AC 勾选结果，保证 Plan/Issue 一致 |
| dev-flow confirm prompts | `projects/ontology/agents/wopal/skills/dev-flow/scripts/cmd/approve.sh`, `verify.sh`, `archive.sh`, `utility.sh`, `SKILL.md` | 修改 | 统一 `--confirm` 输出语义：等待用户授权，由 agent 执行命令，避免误导 |
| dev-flow docs & templates | `projects/ontology/agents/wopal/skills/dev-flow/SKILL.md`, `templates/plan.md`, `templates/issue.md` | 修改 | 按 ontology + skill-creator 规范重写 `SKILL.md`，更新流程说明、状态机、用户验证语义、模板文案，并清理旧 `validate`/validate-era 术语残留 |
| workspace active docs | `docs/products/ontology/plans/101-refactor-dev-flow-verify.md` 及 grep 命中的活跃文档 | 修改 | 同步状态机术语与流程说明 |
| long-term memory | LanceDB memory entries（通过 `memory_manage` 更新） | 更新 | 将旧 3-state / `validation/awaiting` 语义改为 4-state / `verifying` |

## Implementation

### Task 1: 状态域重构为 4-state 主状态机

**Files**: `lib/state-machine.sh`, `lib/labels.sh`

**Changes**:
1. 将合法状态从 `planning/executing/done` 扩展为 `planning/executing/verifying/done`
2. 调整状态顺序、合法跃迁、状态说明与显示信息
3. 新增 `status/verifying` 标签，更新状态标签集合、颜色、描述、状态→标签映射
4. 清理旧 `validation/awaiting` 作为主流程判断依据的设计；仅保留必要的 overlay 语义（如仍需 `pr/opened`）

**Verification**: 读取状态机与标签库，确认存在 `executing -> verifying -> done`，且 `plan_status_to_issue_label verifying -> status/verifying`

- [x] Step 1: 更新 state-machine.sh 的合法状态与合法跃迁
- [x] Step 2: 更新 labels.sh 的状态标签集合与映射
- [x] Step 3: 确认 `sync_status_label_group` 支持 `status/verifying`

### Task 2: 命令流转统一到 verify 主状态

**Files**: `scripts/cmd/complete.sh`, `verify.sh`, `archive.sh`, `approve.sh`, `query.sh`, `utility.sh`, `scripts/flow.sh`

**Changes**:
1. `approve --confirm` 保持 `planning -> executing`
2. `complete` 改为 `executing -> verifying`，不再只叠加 `validation/awaiting`
3. 引入 `verify --confirm` 作为用户验证门：无 PR 路径下由 `verifying -> done` 的授权确认发生在 verify，而不是 archive
4. `archive` 改为归档收尾动作；无 PR 路径下在 verify 通过后执行归档，有 PR 路径下在 merged 后归档
5. `status` / `list` / help 文案统一展示 4-state 与新命令流
6. `reset` 回到 `planning` 时，清理旧验证子标签，避免旧状态残留误导

**Verification**: grep + 读取脚本，确认 `complete` 调用 `update_plan_status ... verifying`，`verify --confirm` 存在并承担用户验证门，`archive` 不再承担核心确认职责，`status`/`list` 输出包含 verifying

- [x] Step 1: 修改 complete 命令为主状态跃迁到 verifying
- [x] Step 2: 新增 verify 命令并前置用户确认门
- [x] Step 3: 修改 archive/query/help/reset 逻辑与文案
- [x] Step 4: 确认 PR 路径在 4-state 下仍可正常归档

### Task 3: approve 阶段自动提交评审方案

**Files**: `scripts/cmd/approve.sh`, 相关 git helper / 文档说明

**Changes**:
1. 在提交用户评审方案时，自动将当前 Plan 变更提交到对应 git 仓库，保证评审对象稳定可追踪
2. commit 时机明确：仅用于“提交评审”的 Plan 文档变更，不越权提交无关代码变更
3. 输出清晰提示：已提交用于评审的 commit hash，便于用户基于固定版本评审
4. 与 git 脏工作区检查配合：若工作区混杂无关变更，则先阻断并提示用户处理，避免把脏改动一起提交到评审 commit

**Verification**: 在仅有 Plan 变更的场景运行 approve（非 confirm 路径），确认会生成评审 commit；有无关脏变更时会阻断并提示风险

- [x] Step 1: 明确 approve 阶段的评审 commit 触发点与范围
- [x] Step 2: 实现仅提交评审所需 Plan 变更的 git commit 逻辑
- [x] Step 3: 验证 commit hash 会回显给用户且脏工作区/无关变更下会阻断

### Task 4: 修复 complete 后 Issue Agent AC 不同步 bug

**Files**: `scripts/cmd/complete.sh`, `lib/plan-sync.sh`, `lib/issue.sh`, `lib/plan.sh`

**Changes**:
1. 在 `complete` 通过 Agent Verification 校验后，立即同步 Plan 到 Issue body
2. 确保 `## Acceptance Criteria` 中 `### Agent Verification` 的 `[x]` 勾选状态能进入 Issue body
3. 保证 complete 后 Issue body 与 Plan 文件事实一致，不再出现 Plan 已勾选、Issue 未更新的分叉
4. 如有必要，补足 plan-sync 对 Agent/User 分层 AC 的提取兼容性

**Verification**: 创建/复用测试 Issue，勾选 Agent Verification 后执行 `complete`，检查 Issue body 中对应 AC 为 `[x]`

- [x] Step 1: 在 complete 中接入 Plan→Issue 同步
- [x] Step 2: 验证 Agent Verification 勾选状态进入 Issue body
- [x] Step 3: 验证 complete 后 Issue 主状态与 body 同时正确更新

### Task 5: 按规范重写 SKILL.md，并统一文档、模板与活跃说明

**Files**: `SKILL.md`, `templates/plan.md`, `templates/issue.md`, 活跃文档 grep 命中项

**Changes**:
1. 按 ontology 项目技能开发规范重写 `SKILL.md`：规范 YAML frontmatter（至少 `name`、`description`、必要时 `compatibility`）、显式声明依赖技能/工具、主体结构清晰可扫描
2. 按 skill-creator 要求重写 `description`：既准确描述 dev-flow 的作用，也明确触发场景与关键词，降低 undertrigger；同时避免把执行细节塞进 description
3. 精简和重组 `SKILL.md` 主体：保留核心流程、输出约束、关键边界与必要示例；去掉过时、重复、误导或过度啰嗦的描述，确保整体标准、清晰、准确、简练
4. 将所有 3-state、`validation/awaiting` 主流程描述改为 4-state + `verifying`
5. 更新流程图、状态映射表、Label 体系、命令说明、用户验证说明
6. 纠正所有 `--confirm` 命令输出与技能文案：强调“agent 收到用户明确授权后执行”，而不是“让用户自己执行脚本命令”
7. 确保模板中关于 `complete`、`verify`、`archive`、User Validation 的文案与新状态机一致
8. 显式扫描并清理旧 `validate` 命令名或 validate-era 验证语义残留（如旧示例、旧门控描述、旧状态说明），避免实现已迁移但文案仍混用旧词
9. 对活跃文档进行一致性修正；历史归档文档不追溯

**Verification**: 读取 `SKILL.md` 确认其 frontmatter、description、依赖声明与主体结构符合 ontology/skill-creator 规范；grep 确认活跃源码/文档中不再用旧主流程描述 `planning -> executing -> done`、`complete -> validation/awaiting` 或旧 `flow.sh validate` 命令描述，且 `--confirm` 提示不再要求用户自己执行脚本

- [x] Step 1: 依据 ontology 规范重写 `SKILL.md` 的 frontmatter、依赖声明与主体结构
- [x] Step 2: 依据 skill-creator 要求重写 `SKILL.md` 的 description 与触发说明
- [x] Step 3: 更新 `SKILL.md` 的状态机、命令流、映射表与示例
- [x] Step 4: 更新模板与帮助文本
- [x] Step 5: 清理 `SKILL.md`、模板、示例中的旧 `validate` 命令/术语残留
- [x] Step 6: 修正 `--confirm` 输出文案与技能说明语义
- [x] Step 7: 更新活跃文档中的旧状态机描述

### Task 6: 实施前 git 脏工作区强制检查

**Files**: `scripts/cmd/approve.sh`, `scripts/cmd/utility.sh`, `scripts/flow.sh`, `lib/common.sh`（如需）

**Changes**:
1. 在进入实施阶段前，强制检查目标项目 git 仓库是否存在 staged / unstaged / untracked 变更
2. 若存在未提交变更，停止继续实施，并明确提示风险：新任务与旧变更混在一起会污染当前 Issue，增加回滚与验证成本
3. 输出明确引导：优先要求用户先提交；若不适合直接提交，则建议改用 `--worktree` 隔离开发
4. 即使建议 worktree，也必须保留风险提醒，禁止只给“可以继续”的乐观提示

**Verification**: 构造干净仓库与脏仓库两种场景，确认干净仓库可继续，脏仓库会被阻断并显示提交 / worktree 建议与风险说明

- [x] Step 1: 实现目标项目 git 工作区脏状态检测
- [x] Step 2: 在实施入口接入阻断逻辑与风险提示
- [x] Step 3: 验证脏仓库下会要求先提交或建议 worktree

### Task 7: 长期记忆一致性更新

**Files**: LanceDB memory entries（`memory_manage`）

**Changes**:
1. 搜索所有涉及 dev-flow 旧 3-state、`validation/awaiting`、complete/archive 旧语义的长期记忆
2. 逐条更新为 `planning -> executing -> verifying -> done` 的新模型
3. 记录 `complete` 的新语义：技术完成后进入 verifying，并同步 Issue 中 Agent AC

**Verification**: memory 检索结果中不再存在与新状态机冲突的高价值记忆

- [x] Step 1: 搜索并列出受影响的长期记忆条目
- [x] Step 2: 逐条更新旧状态机语义
- [x] Step 3: 复检检索结果与实现文档一致

## Delegation Strategy

| 批次 | Task | 执行者 | 依赖 |
|------|------|--------|------|
| 1 | Task 1 | fae | 无 |
| 1 | Task 3 | fae | 无 |
| 2 | Task 2 | fae | Task 1 |
| 2 | Task 4 | fae | Task 1 |
| 2 | Task 6 | fae | 无 |
| 3 | Task 5 | Wopal | Task 1-4 |
| 4 | Task 7 | Wopal | Task 5-6 |

## Test Plan

#### 单元测试

- 状态机单测：验证 `planning -> executing -> verifying -> done` 为合法路径，`executing -> done` 非法
- 标签映射单测：验证 `planning/executing/verifying` 分别映射到 `status/planning`、`status/in-progress`、`status/verifying`
- complete 同步单测：验证 complete 后 `build_issue_body_from_plan` 产出的 Acceptance Criteria 含已勾选 Agent Verification
- approve 评审提交单测：验证提交评审时会生成仅包含 Plan 变更的 commit，且脏工作区下会阻断
- `--confirm` 提示单测：验证 approve/verify/archive 的等待提示都表述为“等待用户授权，随后由 agent 执行”

#### 集成测试

- 无 PR 流程：`plan -> approve -> approve --confirm -> complete -> verify --confirm -> archive`，确认 complete 后 Plan 状态为 `verifying` 且用户确认发生在 verify
- PR 流程：`complete --pr` 后进入 `verifying + pr/opened`，PR merged 后允许 archive
- status/list 查询：确认查询输出能准确显示 `verifying`，不再依赖 `validation/awaiting`
- reset 流程：从 `verifying` reset 回 `planning`，旧验证标签不会残留
- 实施入口安全检查：目标项目仓库有未提交变更时，实施会被阻断，并输出“先提交 / 用 worktree”建议与风险提醒

#### E2E 测试

- 创建测试 Issue，完整走一遍 4-state 生命周期，验证 Plan/Issue 状态始终一致
- 在 complete 后立即查看 Issue body，确认 Agent AC `[x]` 已同步
- 在 verify 阶段执行用户确认，确认 `verify --confirm` 后才进入归档收尾
- 重启 OpenCode 后重新加载技能，确认新文案和流程仍按 4-state 生效
- 在目标项目制造脏工作区后尝试进入实施，确认脚本拒绝继续并正确提示风险

### Regression Testing

- `flow.sh plan --check` 仍能通过新模板
- `approve` 与 `verify` 的人工门控语义清晰且稳定
- `--confirm` 相关命令输出不会误导 agent 去要求用户亲自执行脚本
- 无 Issue 模式（plan by title）在 4-state 下仍可完成完整流程
- PR URL 检测、Issue 关闭、Plan 归档路径更新等既有功能不被破坏

### Adjustment Strategy

- 若旧 Issue 仍残留 `validation/awaiting`，在状态同步与 reset/complete 逻辑中一并清理，避免查询混乱
- 若 `status/verifying` 标签在空间仓库不存在，命令执行时自动创建并加入 label catalog
- 若 Issue body 中 Acceptance Criteria 分层提取不完整，优先补 plan-sync 提取逻辑，禁止在 complete 中写死字符串拼接
- 若项目仓库在多 worktree / detached HEAD 场景下检测结果不稳定，优先在目标项目目录内执行 git 状态检测，避免误判空间根仓库
- 若 approve 自动提交评审方案时会误包含无关文件，必须进一步收窄 git add 范围，禁止扩大提交面

## Acceptance Criteria

### Agent Verification

- [x] `lib/state-machine.sh` 支持 `planning -> executing -> verifying -> done`，且 `executing -> done` 被拒绝
- [x] `lib/labels.sh` 存在 `status/verifying`，并用于 `verifying` 的主状态映射
- [x] `scripts/cmd/complete.sh` 执行后会把 Plan 状态推进到 `verifying`
- [x] `scripts/cmd/verify.sh` 存在且承担用户验证门，`archive` 退回归档收尾职责
- [x] `scripts/cmd/approve.sh` 在提交用户评审方案时会自动生成稳定的评审 commit
- [x] `scripts/cmd/archive.sh` 仅承担 verify 通过后的归档收尾（或 `verifying + pr/opened` 且 PR merged）
- [x] `approve` / `verify` / `archive` 的等待提示都明确写成"收到用户授权后由 agent 执行 --confirm"
- [x] `scripts/cmd/query.sh` / `flow.sh help` / `SKILL.md` 全部反映 4-state 语义
- [x] `SKILL.md` 满足 ontology 技能规范与 skill-creator 要求：frontmatter 完整、description 触发条件清晰、依赖声明明确、主体结构标准且简练
- [x] 活跃源码文档（尤其 `SKILL.md`）中不再残留旧 `flow.sh validate` 命令或 validate-era 验证语义
- [x] complete 后 Issue body 中 `### Agent Verification` 的勾选状态与 Plan 一致
- [x] 实施入口在目标项目 git 仓库存在未提交变更时会阻断继续执行，并提示先提交或改用 worktree，同时明确风险
- [x] 活跃文档与长期记忆中不再保留与新状态机冲突的高价值描述

### User Validation

- 重启 OpenCode 后，用 `flow.sh status <issue>` 能直观看到 `verifying` 阶段，不再需要从 `validation/awaiting` 推断
- 完成一次无 PR 流程后，确认 complete 阶段会同步 Issue 中的 Agent AC 勾选结果
- 无 PR 流程中，确认命令发生在 `verify --confirm`，而不是 `archive --confirm`

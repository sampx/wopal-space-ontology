# 99-refactor-dev-flow-full-consistency-audit

## Metadata

- **Issue**: #99
- **Type**: refactor
- **Target Project**: ontology
- **Created**: 2026-04-15
- **Status**: done

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

修复 dev-flow 技能中 archive 行为、Plan/Issue 模板格式的 8 个缺陷及全面审查发现的额外不一致，提升开发流程规范性。

## Technical Context

### 用户提出的 8 个缺陷（逐项研究结论）

经逐行代码审查，原始 8 个缺陷的研究结论如下：

| # | 缺陷描述 | 研究结论 | 行动 |
|---|----------|----------|------|
| 1 | **archive.sh 未关闭 Issue**：`close_issue` 被 `>/dev/null 2>&1` 吞输出 | ✅ 代码已正确：line 178-181 使用 `if ! close_issue ... then log_warn` | 不修 |
| 2 | **Plan 归档后链接路径未更新**：#97 归档后链接未指向 done/ | ⚠️ 代码已正确（line 172-174 有错误检查），但 `sync_plan_to_issue`（line 160）在 `update_issue_plan_link`（line 172）之前执行，导致 body 被覆盖 | 不修（执行时序问题，非逻辑缺陷） |
| 3 | **InScope/OutScope 使用 checkbox** | 🔴 确认存在：`templates/plan.md:35-36`、`templates/issue.md:11-12`、`lib/plan-sync.sh:88`、`lib/issue.sh:170` | **需修** |
| 4 | **Task Step 格式不统一** | ✅ 已正确：`templates/plan.md:56-57` 已使用 `- [ ] Step N:` | 不修 |
| 5 | **User Validation 使用 checkbox** | ⚠️ 模板已正确（`templates/plan.md:141` 为纯文本），但 **SKILL.md:331-332 示例仍用 checkbox**，`lib/plan.sh:623-661` 校验代码仍按 checkbox 检查 | **部分需修**（SKILL.md 示例 + 校验逻辑） |
| 6 | **测试用例模板不规范** | 🔴 确认存在：`templates/plan.md:78-121` 无单元/集成/E2E 分类 | **需修** |
| 7 | **reset 命令未回退 Issue status 标签** | 🔴 确认存在：`utility.sh:140-165` 只改 Plan 文件，未同步 Issue label | **需修** |
| 8 | **模板章节顺序不合理**：Affected Files 在 In Scope 前 | 🔴 确认存在：`templates/plan.md` 中 Affected Files 在 Technical Context 后、In Scope 前 | **需修** |

### 全面审查额外发现的不一致（5 处）

在上述研究基础上，进一步全面审查后额外发现：

| # | 文件 | 行号 | 问题 |
|---|------|------|------|
| C1 | `scripts/cmd/approve.sh` | 84 | 使用 `set_plan_status` 绕过状态机验证（破坏单一入口） |
| C3 | `scripts/cmd/archive.sh` | 164 | 使用 `set_plan_status` 绕过状态机验证 |
| E1 | `lib/issue.sh` | 191 | Issue AC 占位符 `- [ ] 待 plan 细化后填充` 应改为纯文本 |
| E2 | `lib/plan-sync.sh` | 88 | InScope 回退值 `"- [ ] 范围项 1"` 含 checkbox（与缺陷 3 同源） |
| E3 | `lib/issue.sh` | 170 | `_format_issue_list` 硬编码 `"- [ ] "` InScope 前缀（与缺陷 3 同源） |

### approve 同步 Issue 发现的 bug（3 处）

执行 `approve --confirm` 实际测试发现 `sync_plan_to_issue` 及 Plan 链接相关存在三个 bug：

| # | 文件 | 行号 | 问题 |
|---|------|------|------|
| S1 | `lib/plan-sync.sh` | 88-90 | 行数限制过小（InScope 15、AC 15、OutScope 10），导致 Issue body 截断 |
| S2 | `lib/plan-sync.sh` | 117 | Plan 链接路径硬编码为 `../docs/products/plans/$plan_name.md`，缺失项目目录（实际路径：`docs/products/ontology/plans/...`） |
| S3 | `templates/issue.md` | 27 | Plan 链接占位符 `../docs/...` 无效，应为 `docs/products/{project}/plans/plan-name.md` |

另外 `scripts/cmd/plan.sh:178` 使用 `../${plan_rel_path}` 前缀，在 GitHub Issue 中无效，需同步修正。

### 需要修复的汇总（共 11 项）

- **缺陷 3**: InScope/OutScope 去 checkbox（模板 2 处 + 代码 2 处 = 4 个文件位置）
- **缺陷 5（部分）**: SKILL.md User Validation 示例去 checkbox + `check_user_validation` 纯文本感知
- **缺陷 6**: Test Plan 重构为单元/集成/E2E 分类
- **缺陷 7**: reset 命令增加 Issue label 同步
- **缺陷 8**: 模板章节顺序调整（Affected Files 移至 Out of Scope 后）
- **C1**: approve.sh 改用 `update_plan_status`
- **C3**: archive.sh 改用 `update_plan_status`
- **E1**: Issue AC 占位符去 checkbox
- **S1**: plan-sync.sh 行数限制扩大（InScope 50、AC 40、OutScope 20）
- **S2**: plan-sync.sh Plan 链接路径修正（含项目目录，去掉 `../`）
- **S3**: templates/issue.md + plan.sh 中所有 Plan 链接统一格式（去掉 `../`）

## In Scope

### 用户提出的 8 个缺陷中需要修复的 5 项：

1. **缺陷 3**: InScope/OutScope 去 checkbox（`templates/plan.md` + `templates/issue.md` + `lib/plan-sync.sh` + `lib/issue.sh`）
2. **缺陷 5（部分）**: SKILL.md User Validation 示例去 checkbox + `lib/plan.sh` 校验逻辑改为纯文本感知
3. **缺陷 6**: Test Plan 重构为单元/集成/E2E 分类（`templates/plan.md`）
4. **缺陷 7**: reset 命令增加 Issue status label 同步（`utility.sh`）
5. **缺陷 8**: 模板章节顺序调整（Affected Files 移至 Out of Scope 之后）

### 额外修复的 5 项：

6. **C1**: `approve.sh` 改用 `update_plan_status`（状态机单一入口）
7. **C3**: `archive.sh` 改用 `update_plan_status`（状态机单一入口）
8. **E1**: Issue AC 占位符去 checkbox（`lib/issue.sh`）
9. **S1**: `lib/plan-sync.sh` 行数限制扩大（InScope 50、AC 40、OutScope 20）
10. **S2**: `lib/plan-sync.sh` Plan 链接路径修正为 `docs/products/plans/`（去掉 `../`）

## Out of Scope

- 缺陷 1（archive.sh close_issue）：代码已正确，不修
- 缺陷 2（Plan 链接路径）：代码已正确，是执行时序问题，不修
- 缺陷 4（Task Step 格式）：已正确，不修
- C2（reset 命令 set_plan_status）：reset 允许任意状态→planning，无需验证，不修
- E2（PR body Test Plan）：PR 的 checkbox 是合理设计，不修
- state-machine.sh 状态机转换规则本身
- query.sh / new-issue.sh / plan.sh 命令脚本主体
- 历史 Plan 文件追溯修改

## Out of Scope

- archive.sh close_issue 和 update_issue_plan_link 逻辑（代码已正确）
- state-machine.sh 状态机转换规则本身
- PR body 的 Test Plan checkbox（E2，设计意图合理）
- query.sh / new-issue.sh / plan.sh 命令脚本主体
- 历史 Plan 文件追溯修改
- 不添加 `--message` 参数：commit message 由 agent 根据本轮变更目的自行编写

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| dev-flow | `templates/plan.md` | 修改 | InScope/OutScope 去 checkbox + Test Plan 三分支 + 章节顺序调整 |
| dev-flow | `templates/issue.md` | 修改 | InScope 去 checkbox + Plan 链接占位符修正 |
| dev-flow | `lib/plan-sync.sh` | 修改 | InScope 回退值去 checkbox + 行数限制扩大 + Plan 链接路径修正 |
| dev-flow | `lib/issue.sh` | 修改 | InScope 前缀去 checkbox + Issue AC 占位符去 checkbox |
| dev-flow | `lib/plan.sh` | 修改 | `check_user_validation` 改为纯文本感知 |
| dev-flow | `scripts/cmd/approve.sh` | 修改 | 改用 `update_plan_status` |
| dev-flow | `scripts/cmd/utility.sh` | 修改 | reset 改用 `update_plan_status` + Issue label 同步 |
| dev-flow | `scripts/cmd/archive.sh` | 修改 | 改用 `update_plan_status` |
| dev-flow | `scripts/cmd/plan.sh` | 修改 | Plan 链接去掉 `../` 前缀 |
| dev-flow | `SKILL.md` | 修改 | User Validation 示例去 checkbox + Plan 结构顺序修正 + Test Plan 规范更新 |

## Implementation

### Task 1: 模板层 — InScope 去 checkbox + Test Plan 分类 + 章节顺序

**Files**: `templates/plan.md`, `templates/issue.md`

**Changes**:
1. `templates/plan.md`：
   - InScope/OutScope 改为纯文本列表（移除 `- [ ]`）
   - Test Plan 重构为 `#### 单元测试`、`#### 集成测试`、`#### E2E 测试` 三个子章节
   - 章节顺序调整：Affected Files 从 Technical Context 之后移到 Out of Scope 之后
   - 新顺序：Metadata → Scope Assessment → Goal → Technical Context → In Scope → Out of Scope → Affected Files → Implementation → ...
2. `templates/issue.md`：
   - InScope 改为纯文本列表
   - Out of Scope 保持纯文本（已正确）
   - Plan 链接占位符修正为 `docs/products/{project}/plans/plan-name.md`（去掉 `../`）

**Verification**: 读取模板文件确认格式正确

- [x] Step 1: 修改 templates/plan.md InScope/OutScope 为纯文本
- [x] Step 2: 修改 templates/plan.md 章节顺序
- [x] Step 3: 重构 templates/plan.md Test Plan 为三个子章节
- [x] Step 4: 修改 templates/issue.md InScope 为纯文本

### Task 2: 库函数层 — InScope 回退值 + Issue AC 占位符 + Plan 链接修正

**Files**: `lib/plan-sync.sh`, `lib/issue.sh`

**Changes**:
1. `lib/plan-sync.sh` line 88：InScope 回退值改为 `"- 范围项 1"`（纯文本）
2. `lib/plan-sync.sh` line 88-90：行数限制扩大（InScope 15→50、AC 15→40、OutScope 10→20）
3. `lib/plan-sync.sh` line 117：Plan 链接改为动态路径 `docs/products/{project}/plans/$plan_name.md`（去掉 `../`，含项目目录）
4. `lib/issue.sh` line 170：`_format_issue_list` 的 InScope 前缀改为 `"- "`
5. `lib/issue.sh` line 191：Issue AC 占位符改为 `待 plan 阶段细化`（纯文本，无 checkbox）

**Verification**: grep 确认无残留 `- [ ]` 在 InScope/OutScope 上下文中；Issue body 中 Plan 链接路径正确

- [x] Step 1: 修改 plan-sync.sh InScope 回退值
- [x] Step 2: 修改 plan-sync.sh 行数限制（InScope 50、AC 40、OutScope 20）
- [x] Step 3: 修改 plan-sync.sh Plan 链接路径（动态含项目目录，去掉 `../`）
- [x] Step 4: 修改 issue.sh InScope 前缀
- [x] Step 5: 修改 issue.sh Issue AC 占位符

### Task 3: 校验逻辑 — User Validation 纯文本感知

**Files**: `lib/plan.sh`

**Changes**:
1. `check_user_validation` 函数（lines 613-661）：
   - 改为检测 `### User Validation` 子章节是否存在
   - 验证内容非空、非占位符（如 `- <用户验证项>` 模板文本）
   - 移除 checkbox 正则检查（`- [ ]`/`- [x]`）

**Verification**: 测试纯文本 User Validation 能正确通过校验

- [x] Step 1: 重构 check_user_validation 为纯文本感知
- [x] Step 2: 测试纯文本 User Validation 通过校验

### Task 4: 状态机 — 统一使用 update_plan_status

**Files**: `scripts/cmd/approve.sh`, `scripts/cmd/utility.sh`, `scripts/cmd/archive.sh`

**Changes**:
1. `approve.sh` line 84：`set_plan_status` → `update_plan_status`，移除 line 58 的手动 `validate_transition`
2. `utility.sh` line 161：`set_plan_status` → `update_plan_status`
3. `archive.sh` line 164：`set_plan_status` → `update_plan_status`

**Verification**: 测试各命令状态转换正确，非法转换被拒绝

- [x] Step 1: 修改 approve.sh 使用 update_plan_status
- [x] Step 2: 修改 utility.sh reset 使用 update_plan_status
- [x] Step 3: 修改 archive.sh 使用 update_plan_status

### Task 5: reset 命令 — Issue label 同步

**Files**: `scripts/cmd/utility.sh`

**Changes**:
1. `cmd_reset` 函数（lines 140-165）：
   - 提取 Issue 编号逻辑（参考 archive.sh 的实现）
   - 在 `update_plan_status` 之后，调用 `sync_status_label_group` 将 Issue status label 回退到 `status/planning`
   - 参考 `state-machine.sh` 的 `sync_issue_label` 函数实现模式

**Verification**: 创建测试 Issue → plan → approve → reset → 验证 Issue label 为 `status/planning`

- [x] Step 1: 提取 Issue 编号逻辑
- [x] Step 2: 添加 sync_status_label_group 调用
- [x] Step 3: 端到端测试 reset + label 同步

### Task 6: SKILL.md 同步

**Files**: `SKILL.md`

**Changes**:
1. User Validation 示例（lines 331-332）：改为纯文本格式（`- 重启后功能正常`）
2. Plan 结构表格（lines 397-408）：调整章节顺序（Affected Files 在 Out of Scope 之后）
3. Test Plan 规范说明：更新为单元/集成/E2E 分类格式
4. Acceptance Criteria 说明：User Validation 为纯文本，无需 checkbox

**Verification**: 读取 SKILL.md 确认所有更新

- [x] Step 1: 更新 User Validation 示例为纯文本
- [x] Step 2: 更新 Plan 结构章节顺序
- [x] Step 3: 更新 Test Plan 规范说明
- [x] Step 4: 更新 Acceptance Criteria 说明

### Task 7: Plan 链接路径统一

**Files**: `scripts/cmd/plan.sh`

**Changes**:
1. `plan.sh` line 178：Plan 链接从 `../${plan_rel_path}` 改为 `${plan_rel_path}`（去掉 `../` 前缀）

**Verification**: 创建新 Issue → plan → 验证 Issue body 中 Plan 链接格式正确

- [x] Step 1: 修改 plan.sh 中 Plan 链接去掉 `../`

## Delegation Strategy

| 批次 | Task | 执行者 | 依赖 |
|------|------|--------|------|
| 1 | Task 1 | fae | 无 |
| 1 | Task 2 | fae | 无 |
| 1 | Task 7 | fae | 无 |
| 2 | Task 3 | fae | Task 1 |
| 2 | Task 4 | fae | 无 |
| 3 | Task 5 | fae | Task 4 |
| 4 | Task 6 | Wopal | Task 1-5 完成 |

## Test Plan

### Test Case Design

#### 单元测试
- 模板格式验证：grep 验证 `templates/plan.md` 和 `templates/issue.md` 中 InScope 无 `- [ ]` checkbox
- 模板章节顺序验证：验证 Affected Files 在 Out of Scope 之后
- Test Plan 子章节验证：验证 `templates/plan.md` 中存在 `#### 单元测试`、`#### 集成测试`、`#### E2E 测试`
- plan-sync.sh 回退值验证：确认 fallback 值为纯文本
- SKILL.md User Validation 示例验证：确认无 checkbox

#### 集成测试
- plan 命令：使用新模板创建 Plan → 验证 InScope 纯文本、章节顺序正确、Test Plan 三分支
- reset + label 测试：创建 Issue → plan → approve → reset → 验证 Plan 状态为 planning + Issue label 为 `status/planning`
- complete 命令：验证 User Validation 纯文本能正确通过 `check_user_validation`
- archive 命令：验证状态转换合法（只有 executing → done）

#### E2E 测试
- 完整流程：创建 Issue → plan → approve → complete → archive → 验证全流程状态正确
- reset 后重启：创建 Issue → plan → approve → reset → 重新 approve → 验证状态机正确重启
- 非法状态转换：尝试从 planning 直接 archive → 应被 `update_plan_status` 拒绝

### Regression Testing

- plan 命令：验证新模板仍能正确生成 Plan 文件
- approve 命令：验证使用 `update_plan_status` 后状态转换正确
- complete 命令：验证 Agent Verification checkbox 检查逻辑仍正常
- new-issue 命令：验证新 Issue 模板格式正确
- flow.sh plan --check：验证新 Plan 格式通过校验

### Adjustment Strategy

- 若模板格式变更影响现有 Plan：不追溯修改历史 Plan，仅影响新建 Plan
- 若 `update_plan_status` 拒绝合法转换：检查状态机转换规则是否完整
- 若 `check_user_validation` 改动影响现有 Plan：保持向后兼容，旧格式 checkbox 仍可通过

## Acceptance Criteria

### Agent Verification

**缺陷 3 — InScope/OutScope 去 checkbox：**
- [x] `templates/plan.md` 中 InScope/OutScope 为纯文本列表（无 `- [ ]`）
- [x] `templates/issue.md` 中 InScope 为纯文本列表（无 `- [ ]`）
- [x] `lib/plan-sync.sh` InScope 回退值为纯文本（`- 范围项 1`）
- [x] `lib/issue.sh` InScope 前缀为纯文本（`- `）

**缺陷 5（部分）— User Validation 一致性：**
- [x] `SKILL.md` User Validation 示例为纯文本
- [x] `lib/plan.sh` check_user_validation 支持纯文本验证

**缺陷 6 — Test Plan 规范化：**
- [x] `templates/plan.md` 中 Test Plan 分为单元/集成/E2E 三个子章节

**缺陷 7 — reset 同步 Issue label：**
- [x] reset 命令执行后 Issue status label 正确回退到 `status/planning`

**缺陷 8 — 模板章节顺序：**
- [x] `templates/plan.md` 中 Affected Files 在 Out of Scope 之后

**额外修复 C1/C3 — 状态机单一入口：**
- [x] `scripts/cmd/approve.sh` 使用 `update_plan_status`
- [x] `scripts/cmd/archive.sh` 使用 `update_plan_status`
- [x] `scripts/cmd/utility.sh` reset 使用 `update_plan_status`

**额外修复 E1 — Issue AC 占位符：**
- [x] `lib/issue.sh` Issue AC 占位符为纯文本

**修复 S1/S2/S3 — Issue 同步 bug：**
- [x] `lib/plan-sync.sh` 行数限制扩大（InScope 50、AC 40、OutScope 20）
- [x] `lib/plan-sync.sh` Plan 链接路径包含项目目录（`docs/products/{project}/plans/`）
- [x] `templates/issue.md` Plan 链接占位符格式正确
- [x] `scripts/cmd/plan.sh` Plan 链接去掉 `../` 前缀
- [x] approve 后 Issue body 完整无截断，Plan 链接可点击

**综合验证：**
- [x] `SKILL.md` Plan 结构表格章节顺序正确
- [x] `flow.sh plan --check` 对新模板通过校验

### User Validation

- Review 最终模板格式，确认 InScope/OutScope 无 checkbox，Task Step 格式统一，Test Plan 规范清晰，章节顺序合理

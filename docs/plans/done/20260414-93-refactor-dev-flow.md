# 93-refactor-dev-flow

## Metadata

- **Issue**: #93
- **Type**: refactor
- **Target Project**: ontology
- **Created**: 2026-04-14
- **Status**: done

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

将 5 状态 9 命令压缩为 3 状态 5 命令，统一动词命名规范，消除 Plan 与 Issue 状态不一致问题，降低 Agent 认知负担。

## Technical Context

### 当前架构分析

**状态机（lib/state-machine.sh:36-37）**：
- 5 状态定义：investigating/planning/approved/executing/done
- 状态转换：investigating → planning → approved → executing → done
- reset 通配：任意状态 → investigating

**Label 映射（lib/state-machine.sh:147-157, lib/labels.sh:147-157）**：
- investigating → status/planning（与 planning 共用 Label，无法区分）
- planning → status/planning
- approved → status/approved
- executing → status/in-progress
- done → status/done（实际 Issue closed 时不使用，改为 clear + status/done）

**Label 同步（lib/labels.sh:335-341）**：
- sync_status_label_group：替换所有 status/* labels（主状态单一互斥）
- add_validation_label（lib/labels.sh:378-400）：替换 validation/* labels（先移除后添加）
- add_pr_label（lib/labels.sh:408-414）：添加 pr/opened（叠加）

**命令调用关系**：
- create（cmd/create.sh:cmd_create）→ create_issue → 默认 labels status/planning
- start（cmd/create.sh:cmd_start）→ create_plan → 默认状态 investigating
- spike（cmd/planning.sh:cmd_spike）→ 空操作（只检查状态）
- plan（cmd/planning.sh:cmd_plan）→ set_plan_status planning → ensure_issue_labels
- approve（cmd/approve.sh:cmd_approve）→ check_doc_plan → set_plan_status approved → sync_plan_to_issue → ensure_issue_labels
- dev（cmd/execution.sh:cmd_dev）→ validate_transition → set_plan_status executing → sync_status_label_group → worktree（可选）
- complete（cmd/execution.sh:cmd_complete）→ check_acceptance_criteria → add_validation_label（替换）或 create_pr + add_pr_label
- validate（cmd/closing.sh:cmd_validate）→ check_user_validation → add_validation_label passed → sync_plan_to_issue
- archive（cmd/closing.sh:cmd_archive）→ is_pr_merged 或 validation/passed → set_plan_status done → archive_plan → close_issue

**Plan 模板（templates/plan.md:9）**：
- 默认状态：investigating

### 问题识别

| 问题 | 文件位置 | 影响 |
|------|----------|------|
| investigating/planning 共用 Label | state-machine.sh:150-151, labels.sh:150-151 | Issue 侧无法区分，Agent 困惑 |
| spike 空操作 | cmd/planning.sh:2-44 | 增加认知负担，无实质作用 |
| dev 无中间操作 | cmd/execution.sh:2-83 | approve 后可直接 executing |
| create 语义模糊 | cmd/create.sh:88-220 | Agent 不确定创建 Issue 还是 Plan |
| complete 替换主状态 | cmd/execution.sh:165, labels.sh:395-399 | Plan executing 但 Issue awaiting-validation |
| Plan 默认 investigating | templates/plan.md:9 | 新状态机需改为 planning |

### 设计决策

| 决策 | 变更 | 保持 |
|------|------|------|
| 状态机精简 | 删除 investigating/approved | planning/executing/done |
| Label 叠加 | validation/awaiting 叠加而非替换 | 主状态单一互斥 |
| 命令合并 | start+spike+plan → plan | Spike 质量标准内嵌 |
| approve 合并 dev | approve --confirm → executing | --worktree 参数保留 |
| archive 合并 validate | archive 检测验证条件 | --confirm 参数保留 |
| 参数自动化 | 删除 --update-issue（自动同步 Issue） | --confirm（人为关卡）保留 |
| Plan 默认状态 | investigating → planning | 模板结构不变 |
| 命令命名 | create → new-issue | 动词短语 |

### 全局风险

| 风险 | 影响范围 | 缓解策略 |
|------|----------|----------|
| 旧 Plan 状态兼容 | 现有 Plan 文件使用 investigating/approved | 新状态机只处理新 Plan，旧 Plan 保持不变 |
| 旧命令依赖 | 其他脚本/技能可能调用旧命令名 | 保留兼容别名 + 提示废弃 |
| Label 同步逻辑 | add_validation_label 改为叠加 | 新增 add_validation_overlay_label 函数 |

## Affected Components

| Component | Key Files | Role |
|-----------|-----------|------|
| 状态机定义 | `lib/state-machine.sh:36-63, 147-157` | 状态常量、转换逻辑、Label 映射 |
| Label 同步 | `lib/labels.sh:32-54, 335-341, 378-400` | 主状态替换、子状态叠加 |
| Plan 文档验证 | `lib/check-doc.sh:223-232` | 调查充分性校验 |
| Plan 模板 | `templates/plan.md:9` | 默认状态 |
| 命令入口 | `scripts/flow.sh:173-193` | 命令路由 |
| 命令实现 | `scripts/cmd/*.sh` | 各命令逻辑 |

## In Scope

- [ ] 状态机重构（3 状态：planning/executing/done）
- [ ] Label 体系规范（主状态单一 + 子状态叠加）
- [ ] Plan 模板修改（默认状态 planning）
- [ ] check-doc 调查充分性校验
- [ ] 命令实现重构（new-issue/plan/approve/complete/archive）
- [ ] 参数自动化：删除 --update-issue（自动同步 Issue）
- [ ] 命令兼容性处理（旧命令别名 + 废弃提示）
- [ ] SKILL.md 更新（命令说明、流程图、状态映射表、Spike 质量标准）

## Out of Scope

- 现有 Issue 自动迁移（保持旧 Label，手动处理）
- 旧 Plan 文件向后兼容（新状态机只处理新 Plan）
- 测试框架引入（本次仅手动验证）
- 其他技能/脚本依赖更新（本次完成后手动更新）

## Files

| 文件 | 操作 | 说明 |
|------|------|------|
| `lib/state-machine.sh` | 修改 | 状态定义（删除 investigating/approved）、转换逻辑、Label 映射 |
| `lib/labels.sh` | 修改 | Label 定义（删除 status/approved）、新增 add_validation_overlay_label |
| `lib/check-doc.sh` | 修改 | 调查充分性校验（Technical Context 非空、Affected Components 至少一行） |
| `templates/plan.md` | 修改 | 默认状态改为 planning |
| `scripts/flow.sh` | 修改 | 命令路由、帮助文本、旧命令兼容 |
| `scripts/cmd/create.sh` | 重命名 → `new-issue.sh` | cmd_create 改名为 cmd_new_issue |
| `scripts/cmd/planning.sh` | 重构 → `plan.sh` | 合并 cmd_start/cmd_spike/cmd_plan |
| `scripts/cmd/approve.sh` | 修改 | 合并 cmd_dev 逻辑，--worktree 参数 |
| `scripts/cmd/execution.sh` | 拆分 | cmd_dev 移入 approve.sh，cmd_complete 移入 complete.sh |
| `scripts/cmd/complete.sh` | 新建 | 从 execution.sh 提取 cmd_complete |
| `scripts/cmd/closing.sh` | 重构 → `archive.sh` | 合并 cmd_validate，删除独立 validate |
| `scripts/cmd/utility.sh` | 修改 | cmd_help 全面更新 |
| `SKILL.md` | 修改 | 状态机、命令列表、流程图、状态映射表、Spike 质量标准 |

## Implementation

### Task 1: 状态机重构

**Files**: `lib/state-machine.sh`

**Changes**:

1. **状态常量（36-37 行）**：
   ```bash
   # 原：STATES_LIST="investigating:planning:approved:executing:done"
   # 新：
   STATES_LIST="planning:executing:done"
   ```

2. **状态验证函数（40-50 行）**：
   ```bash
   # 删除 investigating|approved case
   _is_valid_state() {
       case "$state" in
           planning|executing|done)
               return 0
               ;;
           *)
               return 1
               ;;
       esac
   }
   ```

3. **状态顺序函数（53-63 行）**：
   ```bash
   # 删除 investigating(1)、approved(3)、planning(2)→planning(1)
   _get_state_order() {
       case "$state" in
           planning)   echo 1 ;;
           executing)  echo 2 ;;
           done)       echo 3 ;;
           *)          echo 0 ;;
       esac
   }
   ```

4. **状态转换逻辑（105-122 行）**：
   ```bash
   # 新转换规则：planning → executing → done（+ reset 通配）
   case "${current_status}:${new_status}" in
       planning:executing|executing:done)
           return 0
           ;;
       *:planning)  # reset
           return 0
           ;;
       *)
           # 错误提示
           ;;
   esac
   ```

5. **Label 映射（147-157 行）**：
   ```bash
   # 删除 investigating/approved，done 映射改为空（Issue closed）
   plan_status_to_issue_label() {
       case "$plan_status" in
           planning)  echo "status/planning" ;;
           executing) echo "status/in-progress" ;;
           done)      echo "" ;;  # Issue closed，无 status label
           *)         echo "" ;;
       esac
   }
   ```

6. **状态显示信息（237-249 行）**：
   ```bash
   # 删除 investigating/approved case
   get_status_info() {
       case "$status" in
           planning)  echo "1:planning:📝" ;;
           executing) echo "2:executing:🚀" ;;
           done)      echo "3:done:📦" ;;
           *)         echo "0:unknown:❓" ;;
       esac
   }
   ```

7. **状态列表说明（253-263 行）**：
   ```bash
   # 更新状态说明
   list_valid_states() {
       echo "Valid states (in order):"
       echo "  1. planning  - Writing plan document (includes investigation)"
       echo "  2. executing - Currently being executed"
       echo "  3. done      - Archived"
   }
   ```

**Verification**: 状态转换测试

- [ ] Step 1: 修改 STATES_LIST 常量
- [ ] Step 2: 修改 _is_valid_state 函数
- [ ] Step 3: 修改 _get_state_order 函数
- [ ] Step 4: 修改 validate_transition 函数
- [ ] Step 5: 修改 plan_status_to_issue_label 函数
- [ ] Step 6: 修改 get_status_info 函数
- [ ] Step 7: 修改 list_valid_states 函数
- [ ] Step 8: 验证状态转换：planning → executing → done
- [ ] Step 9: 验证 reset：任意状态 → planning

### Task 2: Label 体系规范

**Files**: `lib/labels.sh`

**Changes**:

1. **主状态 Label 定义（32-34 行）**：
   ```bash
   # 删除 status/approved, status/done（改为 Issue closed）
   get_status_label_names() {
       echo "status/planning status/in-progress"
   }
   ```

2. **全量 Label 定义（52-54 行）**：
   ```bash
   # 删除 status/approved, status/done
   get_all_flow_label_names() {
       echo "status/planning status/in-progress validation/awaiting validation/passed pr/opened"
   }
   ```

3. **Label 属性（63-89 行）**：
   ```bash
   # 删除 status/approved, status/done case
   _get_label_props() {
       case "$label_name" in
           status/planning)    printf 'fbca04\tPlanning\n' ;;
           status/in-progress) printf '1d76db\tIn progress\n' ;;
           # 其他不变
       esac
   }
   ```

4. **状态 Label 映射（147-157 行）**：
   ```bash
   # 删除 investigating/approved 映射
   plan_status_to_issue_label() {
       case "$plan_status" in
           planning)  echo "status/planning" ;;
           executing) echo "status/in-progress" ;;
           done)      echo "" ;;
           *)         echo "" ;;
       esac
   }
   ```

5. **新增叠加 Label 函数（400 行后插入）**：
   ```bash
   # Add validation label as overlay (keep main status)
   # Usage: add_validation_overlay_label <issue_number> <label_type> [repo]
   add_validation_overlay_label() {
       local issue_number="$1"
       local label_type="$2"
       local repo=$(_labels_resolve_repo "${3:-}")
       
       case "$label_type" in
           awaiting|passed) ;;
           *)
               log_error "Invalid validation label type: $label_type"
               return 1
               ;;
       esac
       
       local label="validation/$label_type"
       
       # Remove other validation labels (keep status labels)
       remove_issue_label "$issue_number" "validation/awaiting" "$repo"
       remove_issue_label "$issue_number" "validation/passed" "$repo"
       
       # Add new validation label
       ensure_issue_label "$issue_number" "$label" "$repo"
   }
   ```

6. **修改 sync_status_label_group（335-341 行）**：
   ```bash
   # 更新主状态列表（删除 status/approved, status/done）
   sync_status_label_group() {
       local issue_number="$1"
       local desired_label="$2"
       local repo="${3:-}"
       sync_issue_label_group "$issue_number" "$desired_label" "$repo" \
           "status/planning" "status/in-progress"
   }
   ```

**Verification**: Label 变更测试

- [ ] Step 1: 修改 get_status_label_names 函数
- [ ] Step 2: 修改 get_all_flow_label_names 函数
- [ ] Step 3: 修改 _get_label_props 函数
- [ ] Step 4: 修改 plan_status_to_issue_label 函数
- [ ] Step 5: 新增 add_validation_overlay_label 函数
- [ ] Step 6: 修改 sync_status_label_group 函数
- [ ] Step 7: 测试主状态替换（status/planning → status/in-progress）
- [ ] Step 8: 测试子状态叠加（validation/awaiting 添加但不移除主状态）

### Task 3: Plan 模板修改

**Files**: `templates/plan.md`

**Changes**:

1. **默认状态（第 9 行）**：
   ```markdown
   # 原：- **Status**: investigating
   # 新：
   - **Status**: planning
   ```

**Verification**: 模板验证

- [ ] Step 1: 修改默认状态
- [ ] Step 2: 测试 create_plan 使用新模板

### Task 4: check-doc 调查充分性校验

**Files**: `lib/check-doc.sh`

**Changes**:

1. **Spike 章节验证增强（223-232 行）**：
   ```bash
   # 从 warning 改为 error（强制验证）
   for section in "## Technical Context" "## Affected Components"; do
       if grep -q "$section" "$plan_file"; then
           # 检查内容非空
           local section_content
           section_content=$(sed -n "/^$section/,/^##[^#]/p" "$plan_file" | sed '1d;$d' | grep -v '^$' || true)
           if [[ -z "$section_content" ]]; then
               echo "$section is empty (required for investigation completeness)"
               ((issues++))
           else
               log_success "$section (spike investigation)"
           fi
       else
           echo "Missing $section (required for spike investigation)"
           ((issues++))
       fi
   done
   ```

2. **Scope Assessment 验证（236-248 行）**：
   ```bash
   # 强制验证 Complexity 和 Confidence 非占位符
   if grep -q '^## Scope Assessment' "$plan_file"; then
       local complexity_value
       complexity_value=$(grep '^\- \*\*Complexity\*\*:' "$plan_file" | sed 's/^.*: //' || true)
       local confidence_value
       confidence_value=$(grep '^\- \*\*Confidence\*\*:' "$plan_file" | sed 's/^.*: //' || true)
       
       if [[ -z "$complexity_value" || "$complexity_value" =~ Low\|Medium\|High ]]; then
           if [[ "$complexity_value" == "Low|Medium|High" ]]; then
               echo "Complexity not evaluated (placeholder)"
               ((issues++))
           fi
       else
           echo "Complexity invalid: $complexity_value"
           ((issues++))
       fi
       
       # 同理检查 Confidence
   fi
   ```

**Verification**: 调查充分性测试

- [ ] Step 1: 增强 Technical Context 验证（非空）
- [ ] Step 2: 增强 Affected Components 验证（至少一行）
- [ ] Step 3: 增强 Complexity/Confidence 验证（非占位符）
- [ ] Step 4: 测试占位符 Plan 被 check-doc 拒绝
- [ ] Step 5: 测试完整 Plan 通过 check-doc

### Task 5: 命令重构 - new-issue

**Files**: `scripts/cmd/create.sh` → 重命名为 `scripts/cmd/new-issue.sh`

**Changes**:

1. **函数名（88-220 行）**：
   ```bash
   # 原：cmd_create
   # 新：
   cmd_new_issue() {
       # 功能不变
   }
   ```

2. **输出提示（218-219 行）**：
   ```bash
   echo "Issue #${issue_number}: $issue_url"
   echo "Next: flow.sh plan $issue_number"
   ```

**Verification**: new-issue 测试

- [ ] Step 1: 重命名文件为 new-issue.sh
- [ ] Step 2: 修改函数名 cmd_create → cmd_new_issue
- [ ] Step 3: 修改输出提示
- [ ] Step 4: 测试 flow.sh new-issue --title --project --type

### Task 6: 命令重构 - plan（合并 start/spike）

**Files**: `scripts/cmd/planning.sh` → 重构为 `scripts/cmd/plan.sh`

**Changes**:

1. **合并 cmd_start 逻辑（原 create.sh:2-85 行）**：
   ```bash
   cmd_plan() {
       # 合并原 cmd_start 的 Plan 文件创建逻辑
       # 合并原 cmd_plan 的状态设置逻辑
       # 删除原 cmd_spike 空操作逻辑
   }
   ```

2. **核心流程**：
   ```bash
   # 1. 解析 Issue 号和 project 参数
   # 2. 获取 Issue 信息（title、labels）
   # 3. 解析 plan type 和 slug
   # 4. 创建 Plan 文件（使用新模板，默认状态 planning）
   # 5. 更新 Issue link（Plan 路径）
   # 6. ensure_issue_labels（status/planning + type/* + project/*）
   # 7. 输出提示："Plan: $plan_file, Status: planning, Next: approve <issue>"
   ```

3. **--check 参数**：
   ```bash
   if [[ "$check_only" == true ]]; then
       if check_doc_plan "$plan_file" >/dev/null 2>&1; then
           echo "Plan passes validation"
           echo "Next: flow.sh approve $issue_number"
       else
           check_doc_plan "$plan_file"
           log_error "Plan has issues"
       fi
       exit 0
   fi
   ```

4. **删除 cmd_spike 函数**

**Verification**: plan 命令测试

- [ ] Step 1: 合并 cmd_start 的 Plan 创建逻辑
- [ ] Step 2: 合并 cmd_plan 的状态设置逻辑
- [ ] Step 3: 删除 cmd_spike 函数
- [ ] Step 4: 修改 --check 参数处理
- [ ] Step 5: 测试 flow.sh plan <issue>
- [ ] Step 6: 测试 flow.sh plan <issue> --check

### Task 7: 命令重构 - approve（合并 dev）

**Files**: `scripts/cmd/approve.sh` + `scripts/cmd/execution.sh:cmd_dev` → 合并为 `scripts/cmd/approve.sh`

**Changes**:

1. **参数精简**：
   - 删除 `--update-issue` 参数（**自动同步 Issue**）
   - 保留 `--confirm`（人为关卡）
   - 保留 `--worktree`（可选隔离）
   
   理由：审批通过 = Plan 已定稿 = 自动同步 Issue。Agent 不需要判断，减少参数出错概率。

2. **合并 cmd_dev 逻辑**：
   ```bash
   cmd_approve() {
       # 原 approve 逻辑 + dev 逻辑
   }
   ```

3. **核心流程（有 --confirm）**：
   ```bash
   # 1. 查找 Plan 文件
   # 2. 获取当前状态
   # 3. 验证转换：planning → executing
   # 4. check_doc_plan 验证
   # 5. set_plan_status executing
   # 6. sync_status_label_group（status/in-progress）
   # 7. ensure_issue_labels（自动同步 type/project labels）
   # 8. sync_plan_to_issue（自动同步，删除 --update-issue 参数）
   # 9. 如果 --worktree：创建 worktree（调用 git-worktrees 技能）
   # 10. 输出提示："Status: executing, Next: complete <issue>"
   ```

4. **无 --confirm 时暂停**：
   ```bash
   if [[ "$confirm" != true ]]; then
       echo "Status: awaiting approval"
       echo "Next: flow.sh approve $issue_number --confirm"
       exit 0
   fi
   ```

5. **--worktree 参数处理**：
   ```bash
   if [[ "$use_worktree" == true ]]; then
       local project=$(get_plan_project "$plan_file")
       local plan_name=$(get_plan_name "$plan_file")
       local slug=$(extract_slug "$plan_name")
       local branch="issue-${issue_number}-${slug}"
       
       local worktree_script="$SKILL_DIR/../git-worktrees/scripts/worktree.sh"
       bash "$worktree_script" create "$project" "$branch" --no-install --no-test
   fi
   ```

6. **自动同步 Issue（原需 --update-issue）**：
   ```bash
   # 删除 --update-issue 参数解析
   # 在 --confirm 分支中无条件执行：
   sync_plan_to_issue "$issue_number" "$plan_file" "$repo" >/dev/null 2>&1
   ```

**Verification**: approve 流程测试

- [ ] Step 1: 删除 --update-issue 参数解析
- [ ] Step 2: 合并 cmd_dev 的状态转换逻辑
- [ ] Step 3: 合并 cmd_dev 的 Label 同步逻辑
- [ ] Step 4: 添加自动 sync_plan_to_issue（无参数判断）
- [ ] Step 5: 添加 --worktree 参数处理
- [ ] Step 6: 测试 flow.sh approve <issue>（无 confirm，暂停）
- [ ] Step 7: 测试 flow.sh approve <issue> --confirm（状态 executing + 自动同步 Issue）
- [ ] Step 8: 测试 flow.sh approve <issue> --confirm --worktree

### Task 8: 命令重构 - complete

**Files**: `scripts/cmd/execution.sh:cmd_complete` → 移入 `scripts/cmd/complete.sh`

**Changes**:

1. **新建 complete.sh**：
   ```bash
   cmd_complete() {
       # 从 execution.sh 提取 cmd_complete 逻辑
   }
   ```

2. **核心流程**：
   ```bash
   # 1. 查找 Plan 文件
   # 2. 验证状态为 executing
   # 3. check_acceptance_criteria（Agent Verification）
   # 4. 有 PR：
   #    - get_plan_project
   #    - add_pr_label（叠加）
   #    - create_pr（project repo）
   #    - 输出："Status: PR opened, Next: archive <issue>"
   # 5. 无 PR：
   #    - add_validation_overlay_label awaiting（叠加，不移除主状态）
   #    - 输出："Status: awaiting validation, Next: archive <issue> --confirm"
   ```

3. **Label 变更改为叠加**：
   ```bash
   # 原：add_validation_label（替换主状态）
   # 新：add_validation_overlay_label（叠加）
   add_validation_overlay_label "$issue_number" "awaiting" "$repo"
   ```

**Verification**: complete 流程测试

- [ ] Step 1: 创建 complete.sh 文件
- [ ] Step 2: 提取 cmd_complete 逻辑
- [ ] Step 3: 修改 Label 变更为叠加
- [ ] Step 4: 测试 flow.sh complete（无 PR，叠加 validation/awaiting）
- [ ] Step 5: 测试 flow.sh complete --pr（创建 PR）

### Task 9: 命令重构 - archive（合并 validate）

**Files**: `scripts/cmd/closing.sh` → 重构为 `scripts/cmd/archive.sh`

**Changes**:

1. **合并 cmd_validate 逻辑**：
   ```bash
   cmd_archive() {
       # 原 archive 逻辑 + validate 逻辑
   }
   ```

2. **核心流程**：
   ```bash
   # 1. 查找 Plan 文件
   # 2. 检测归档条件：
   #    - PR 路径：is_pr_merged（检测 PR merged）
   #    - 无 PR 路径：validation/awaiting label + --confirm 参数
   # 3. 无 --confirm 且无 PR merged：输出提示，暂停
   # 4. 归档条件满足：
   #    - sync_plan_to_issue（同步 AC）
   #    - set_plan_status done
   #    - archive_plan（移动到 done/）
   #    - close_issue（关闭 + clear_all_flow_labels）
   #    - 输出："Status: done"
   ```

3. **验证条件检测**：
   ```bash
   # PR 路径
   if issue_has_label "$issue_number" "pr/opened" "$repo"; then
       local pr_url=$(get_pr_url_from_issue "$issue_number" "$repo")
       if [[ -n "$pr_url" ]] && is_pr_merged "$pr_url"; then
           can_archive=true
           archive_reason="PR merged"
       else
           log_error "PR not merged yet"
           exit 1
       fi
   fi
   
   # 无 PR 路径
   if issue_has_label "$issue_number" "validation/awaiting" "$repo"; then
       if [[ "$confirm" != true ]]; then
           echo "Issue awaiting validation"
           echo "Next: flow.sh archive $issue_number --confirm"
           exit 0
       fi
       # check_user_validation（可选）
       can_archive=true
       archive_reason="validation confirmed"
   fi
   ```

4. **删除 cmd_validate 函数**

**Verification**: archive 流程测试

- [ ] Step 1: 合并 cmd_validate 逻辑
- [ ] Step 2: 实现 PR merged 检测逻辑
- [ ] Step 3: 实现 validation/awaiting + --confirm 逻辑
- [ ] Step 4: 测试 flow.sh archive（有 PR，自动归档）
- [ ] Step 5: 测试 flow.sh archive（无 PR，暂停）
- [ ] Step 6: 测试 flow.sh archive --confirm（无 PR，归档）

### Task 10: 主入口更新

**Files**: `scripts/flow.sh`

**Changes**:

1. **命令路由（173-193 行）**：
   ```bash
   case "${1:-help}" in
       new-issue)      shift; cmd_new_issue "$@" ;;
       plan)           shift; cmd_plan "$@" ;;
       approve)        shift; cmd_approve "$@" ;;
       complete)       shift; cmd_complete "$@" ;;
       archive)        shift; cmd_archive "$@" ;;
       status)         shift; cmd_status "$@" ;;
       list)           shift; cmd_list "$@" ;;
       decompose-prd)  shift; cmd_decompose_prd "$@" ;;
       reset)          shift; cmd_reset "$@" ;;
       help|--help|-h) cmd_help ;;
       # 旧命令兼容
       create)         shift; log_warn "create is deprecated, use new-issue"; cmd_new_issue "$@" ;;
       start)          shift; log_warn "start is deprecated, use plan"; cmd_plan "$@" ;;
       spike)          shift; log_warn "spike is deprecated, use plan"; exit 0 ;;
       dev)            shift; log_warn "dev is deprecated, approve --confirm enters executing"; exit 0 ;;
       validate)       shift; log_warn "validate is deprecated, use archive --confirm"; exit 0 ;;
       *)
           log_error "Unknown command: $1"
           cmd_help
           exit 1
           ;;
   esac
   ```

2. **source 文件顺序（160-167 行）**：
   ```bash
   source "$SKILL_DIR/scripts/cmd/utility.sh"
   source "$SKILL_DIR/scripts/cmd/new-issue.sh"
   source "$SKILL_DIR/scripts/cmd/plan.sh"
   source "$SKILL_DIR/scripts/cmd/approve.sh"
   source "$SKILL_DIR/scripts/cmd/complete.sh"
   source "$SKILL_DIR/scripts/cmd/archive.sh"
   source "$SKILL_DIR/scripts/cmd/query.sh"
   ```

**Verification**: 命令路由测试

- [ ] Step 1: 修改命令路由（new-issue/plan/approve/complete/archive）
- [ ] Step 2: 修改 source 文件顺序
- [ ] Step 3: 添加旧命令兼容处理（create/start/spike/dev/validate）
- [ ] Step 4: 测试 flow.sh help
- [ ] Step 5: 测试旧命令兼容（create → new-issue）

### Task 11: 帮助文本更新

**Files**: `scripts/cmd/utility.sh`

**Changes**:

1. **cmd_help 全面更新（167-228 行）**：
   ```bash
   cmd_help() {
       cat << 'EOF'
   dev-flow — 统一开发工作流 (3-state model)
   
   Usage: flow.sh <command> <issue> [options]
   
   生命周期命令:
     new-issue --title "<title>" --project <name> --type <type> [options]
                                         创建规范化 Issue
     plan <issue>                      创建 Plan 并进入规划阶段
     approve <issue> --confirm [--worktree]
                                         审批通过 → 进入执行阶段
     complete <issue> [--pr]           完成开发，等待验收
     archive <issue> [--confirm]       归档（PR merged 或用户确认）
   
   查询命令:
     status <issue>                   查看任务状态
     list                             列出进行中任务
   
   其他:
     decompose-prd <prd> [--dry-run]  从 PRD 创建 Issue
     reset <issue>                    重置到 planning 状态
     help                             显示帮助
   
   状态机 (3-state): planning -> executing -> done
   
   选项说明:
     --confirm        确认操作（仅限用户执行）
     --worktree       创建隔离 worktree
     --pr             创建 PR
     --update-issue   同步 Plan 到 Issue
   
   示例:
     # 创建 Issue
     flow.sh new-issue --title "feat(cli): add command" --project ontology --type feature
     
     # 完整工作流
     flow.sh plan 42
     flow.sh approve 42 --confirm
     flow.sh complete 42
     flow.sh archive 42 --confirm
   
   旧命令兼容:
     create → new-issue
     start → plan
     spike → (已废弃，调查内嵌在 plan)
     dev → (已废弃，approve --confirm 进入 executing)
     validate → (已废弃，archive --confirm 处理验证)
   EOF
   }
   ```

**Verification**: 帮助文本测试

- [ ] Step 1: 更新 cmd_help 函数
- [ ] Step 2: 测试 flow.sh help

### Task 12: SKILL.md 更新

**Files**: `SKILL.md`

**Changes**:

1. **状态机说明（61-76 行）**：
   ```markdown
   ## 状态机 (3-State Model)
   
   ```
   planning → executing → done
                ↑              ↑
           用户确认审批    验证/PR merged
   ```
   
   | 状态 | 含义 | Label |
   |------|------|-------|
   | `planning` | 规划编写（含调查） | `status/planning` |
   | `executing` | 执行中 | `status/in-progress` |
   | `done` | 已归档 | Issue closed |
   
   ### Label 子状态机制
   
   | 类别 | Label | 含义 |
   |------|-------|------|
   | 验证 | `validation/awaiting` | 等待用户验证（叠加） |
   | PR | `pr/opened` | PR 已创建（叠加） |
   ```

2. **命令列表（85-106 行）**：
   ```markdown
   ## 命令
   
   ```bash
   # 创建 Issue
   flow.sh new-issue --title "<title>" --project <name> --type <type> [options]
   
   # 生命周期
   flow.sh plan <issue>                      # 创建 Plan（含调查）
   flow.sh approve <issue> --confirm [--worktree]  # 审批 → 执行
   flow.sh complete <issue> [--pr]           # 完成
   flow.sh archive <issue> [--confirm]       # 归档
   
   # 查询
   flow.sh status <issue>                    # 查看状态
   flow.sh list                              # 列出任务
   ```
   ```

3. **验证路径（178-194 行）**：
   ```markdown
   ## 验证路径
   
   ```
   executing
       │
       ├── complete --pr ──→ pr/opened ──→ PR merged ──→ archive
       │
       └── complete ──→ validation/awaiting
                                 │
                                 └── archive --confirm ──→ done
   ```
   ```

4. **标准工作流程（243-257 行）**：
   ```markdown
   ## 标准工作流程
   
   ```
   1. plan <issue>        → AI 创建 Plan + 调查研究 + 编写 (status: planning)
   2. approve <issue>     → AI 提交审批，暂停等待
       用户确认后 → approve <issue> --confirm [--worktree]
   3. complete <issue>    → AI 完成，添加验证 Label 或创建 PR
       无 PR → 用户验证后执行 archive --confirm
       有 PR → 等待 PR merge
   4. archive <issue>     → AI 归档 (status: done)
   ```
   ```

5. **plan 命令阶段规范（保留原 Spike 质量标准）**：
   ```markdown
   ## plan 命令阶段：调查 + 编写
   
   plan 命令包含两个子阶段（AI 自然衔接，无显式切换）：
   
   ### 调查子阶段（10 步 Spike 流程）
   
   1. **识别组件** - 确定涉及的模块/子系统，阅读代码确认
   2. **彻底阅读源文件** - 理解逻辑，跟踪调用链
   3. **映射当前架构** - 组件交互、数据流、边界
   4. **识别精确代码路径** - 文件路径和行号
   5. **评估复杂度**：Low/Medium/High
   6. **识别风险与边界情况** - 权衡、需人类输入的决策
   7. **检查现有模式** - 类似功能实现方式
   8. **查看测试** - 测试模式、覆盖率
   9. **检查架构文档** - docs/ 相关文档
   10. **确定 Issue 类型** - feat/fix/refactor/chore/perf/docs
   
   ### 编写子阶段
   
   基于调查结果填充 Plan 章节：
   - Scope Assessment：Complexity、Confidence
   - Technical Context：架构描述、变更原因、风险
   - Affected Components：表格
   - In Scope/Out of Scope
   - Files：文件列表
   - Implementation：Task 分解
   - Test Plan
   
   ### approve 时验证调查充分性
   
   check-doc 强制验证：
   - Technical Context 非空
   - Affected Components 至少一行
   - Complexity/Confidence 已填写（非占位符）
   - 每个 Task 有 Files 和 Verification
   ```

6. **状态映射表**：
   ```markdown
   ## 状态映射表
   
   | 命令 | Plan 状态 | Issue Labels |
   |------|----------|-------------|
   | new-issue | 无 | status/planning + type/* + project/* |
   | plan | planning | status/planning（不变） |
   | approve --confirm | executing | status/in-progress（替换） |
   | complete | executing | status/in-progress + validation/awaiting（叠加） |
   | complete --pr | executing | status/in-progress + pr/opened（叠加） |
   | archive | done | closed |
   ```

7. **示例流程更新（445-472 行）**：
   ```markdown
   ## 示例
   
   ```
   用户: 帮我开发 Issue #14
   
   AI: 
     flow.sh plan 14
     [调查研究 + 编写 Plan...]
     flow.sh plan 14 --check
     flow.sh approve 14
     ⚠️ 暂停，等待审批确认
   
   用户: 审批通过
   
   AI: flow.sh approve 14 --confirm --worktree
       [执行实施...]
       flow.sh complete 14
       ⚠️ 暂停，等待验证
   
   用户: 验证通过
   
   AI: flow.sh archive 14 --confirm
   ```
   ```

**Verification**: 文档完整性检查

- [ ] Step 1: 更新状态机说明
- [ ] Step 2: 更新命令列表
- [ ] Step 3: 更新验证路径
- [ ] Step 4: 更新标准工作流程
- [ ] Step 5: 迁移 Spike 质量标准到 plan 命令阶段规范
- [ ] Step 6: 添加状态映射表
- [ ] Step 7: 更新示例流程
- [ ] Step 8: 删除旧命令说明（start/spike/dev/validate）

## Delegation Strategy

N/A — 本 Plan 涉及核心状态机重构，需 Wopal 直接实施以确保质量和一次性完成。

## Test Plan

### Test Case Design

| 测试用例 | 目标 | 方法 | 预期结果 |
|---------|------|------|---------|
| 无 PR 完整流程 | 验证状态转换和 Label 变化 | new-issue → plan → approve --confirm → complete → archive --confirm | planning → executing → done，Label 一致 |
| 有 PR 完整流程 | 验证 PR 路径 | new-issue → plan → approve --confirm → complete --pr → archive（模拟 merged） | PR 创建，Label 叠加 pr/opened |
| 旧命令兼容 | 验证废弃提示 | flow.sh create → 应提示 "use new-issue" | 输出废弃提示并执行新命令 |
| 状态一致性 | 验证 Plan 状态 vs Issue Label | 每个 stage 检查 Plan 和 Issue | 完全对应 |
| 调查充分性 | 验证 check-doc 拒绝占位符 | Plan 使用占位符 → approve | check-doc 拒绝 |

### Regression Testing

- **现有 Issue**：创建新 Issue #93 测试，不影响已有 Issue
- **Plan 文件**：新 Plan 使用新状态机，旧 Plan 保持不变（不处理）
- **其他技能依赖**：本次完成后手动更新调用方

### Adjustment Strategy

| 阻塞情况 | 应对策略 |
|---------|---------|
| 某命令重构复杂 | 先完成其他命令，最后处理阻塞点 |
| Label 叠加逻辑问题 | 保留旧 add_validation_label 作为别名，逐步迁移 |
| check-doc 验证过严 | 调整为 warning 而非 error，后续迭代 |

## Acceptance Criteria

### Agent Verification

- [x] 状态机重构完成（3 状态定义、转换逻辑、Label 映射）
- [x] Label 体系规范完成（主状态替换、子状态叠加、add_validation_overlay_label）
- [x] Plan 模板修改完成（默认状态 planning）
- [x] check-doc 调查充分性校验完成（Technical Context/Affected Components/Complexity/Confidence）
- [x] 所有命令重构完成（new-issue/plan/approve/complete/archive）
- [x] 参数自动化完成（删除 --update-issue，自动同步 Issue）
- [x] 主入口更新完成（命令路由、旧命令兼容）
- [x] SKILL.md 更新完成（状态机、命令、流程图、状态映射表、Spike 质量标准）
- [x] 完整流程测试通过（无 PR 和有 PR）
- [x] Plan 状态与 Issue Label 一致性验证通过
- [x] approve --confirm 自动同步 Issue 验证通过（无 --update-issue 参数）

### User Validation

- 验证流程精简是否符合预期（9 命令 → 5 命令）
- 验证状态一致性是否解决（Plan 状态 vs Issue Label）
- 验证命令命名是否清晰（动词短语语义明确）
- 验证 Spike 质量标准是否完整保留
- 验证 Agent 认知负担是否降低
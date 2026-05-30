# fix-dev-flow-archive-issue-plan-scope

## Metadata

- **Module**: dev-flow/archive
- **Type**: fix
- **Target Project**: ontology
- **Created**: 2026-04-14
- **Status**: done

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

修复 archive 后 Issue Plan 链接失效问题，并完善无 Issue 模式的模块关联信息。

## Technical Context

### 问题 1：archive 后 Issue Plan 链接失效

**根因**：`archive.sh` 中 `sync_plan_to_issue`（第 160 行）在 `archive_plan`（第 168 行）之前执行。`sync_plan_to_issue` 用 `build_issue_body_from_plan`（plan-sync.sh:81-119）生成 Issue body，其中 Plan 链接硬编码为 `../docs/projects/plans/$plan_name.md`（第 117 行）。

归档后 Plan 移到 `done/` 目录，路径变为 `done/YYYYMMDD-$plan_name.md`，但 Issue body 中的链接仍是旧路径。

**修复方案**：在 `archive_plan` 之后，用归档后的实际路径更新 Issue Related Resources 表格中的 Plan 链接。

### 问题 2：find_plan 无法查找项目级 Plan（无 Issue 模式阻塞）

**根因**：`find_plan`（flow.sh:144-160）对字符串输入调用 `resolve_plan_file`，后者默认搜索 `docs/products/plans/`（全局目录），不搜索 `docs/products/ontology/plans/`（项目目录）。无 Issue 模式创建的 Plan 在项目目录下，导致 `approve`/`complete`/`archive` 命令找不到 Plan。

**修复方案**：让 `find_plan` 对字符串输入搜索所有项目 plan 目录（类似 `find_plan_by_issue` 的搜索逻辑）。

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| plan-sync | `lib/plan-sync.sh` | 修改 | 新增更新 Issue Plan 链接函数 |
| archive | `scripts/cmd/archive.sh` | 修改 | 归档后更新 Issue Plan 链接 |
| 主入口 | `scripts/flow.sh` | 修改 | `find_plan` 搜索所有项目目录 |

## In Scope

- [x] archive.sh 归档后更新 Issue Plan 链接
- [x] plan-sync.sh 新增 `update_issue_plan_link` 函数
- [x] flow.sh `find_plan` 支持搜索项目级 Plan

## Out of Scope

- 无 Issue 模式命名规范修改（当前已支持 scope）
- 其他 Issue body 同步逻辑改动

## Implementation

### Task 1: 新增 update_issue_plan_link 函数

**Files**: `lib/plan-sync.sh`

**Changes**:

1. 在文件末尾新增函数：
```bash
# Update Issue Plan link after archive
# Usage: update_issue_plan_link <issue_number> <archived_file> [repo]
# This updates the Plan link in Related Resources table to the archived path
update_issue_plan_link() {
    local issue_number="$1"
    local archived_file="$2"
    local repo
    repo=$(_resolve_repo "${3:-}")
    
    if [[ ! -f "$archived_file" ]]; then
        log_warn "Archived plan file not found: $archived_file"
        return 1
    fi
    
    if ! command -v gh &> /dev/null; then
        log_warn "gh CLI not available, skipping Plan link update"
        return 0
    fi
    
    local plan_name
    plan_name=$(basename "$archived_file" .md)
    
    # Build relative path from Issue (docs/products/ontology/plans/done/YYYYMMDD-plan.md)
    local plan_dir
    plan_dir=$(dirname "$archived_file")
    local relative_path
    relative_path=$(realpath --relative-to="$PWD/docs/products" "$archived_file" 2>/dev/null || \
        echo "ontology/plans/done/$(basename "$archived_file")")
    
    # Get current Issue body
    local current_body
    current_body=$(gh issue view "$issue_number" --repo "$repo" --json body --jq '.body')
    
    # Update Plan link in Related Resources table
    local new_body
    new_body=$(echo "$current_body" | sed -E "s|\[$plan_name\]\([^)]*\)|[$plan_name](../docs/products/$relative_path)|")
    
    # If Plan link not found by name, try updating the whole row
    if [[ "$new_body" == "$current_body" ]]; then
        # Pattern: | Plan | [plan-name](old-path) |
        new_body=$(echo "$current_body" | sed -E "s|Plan \| \[([^]]+)\]\([^)]*\)|Plan | [$plan_name](../docs/products/$relative_path)|")
    fi
    
    gh issue edit "$issue_number" --repo "$repo" --body "$new_body" >/dev/null && \
        log_success "Issue #$issue_number Plan link updated to archived path" || \
        log_warn "Failed to update Issue #$issue_number Plan link"
}
```

**Verification**: 函数存在且语法正确

- [ ] Step 1: 在 plan-sync.sh 末尾新增 `update_issue_plan_link` 函数
- [ ] Step 2: 检查函数语法 `bash -n lib/plan-sync.sh`

### Task 2: archive.sh 归档后调用更新函数

**Files**: `scripts/cmd/archive.sh`

**Changes**:

1. 在 `archive_plan` 之后（第 168 行后）、`close_issue` 之前（第 171 行前）插入：
```bash
# Update Issue Plan link to archived path (if Issue exists)
if [[ -n "$issue_number" && -n "$archived_file" ]]; then
    update_issue_plan_link "$issue_number" "$archived_file" "$repo" >/dev/null 2>&1
fi
```

2. 在文件开头 source plan-sync.sh（如果尚未 source）：
```bash
source "$SKILL_DIR/lib/plan-sync.sh"
```

**Verification**: 归档后 Issue Plan 链接指向 done/ 目录

- [ ] Step 1: 在 archive.sh 中插入调用 `update_issue_plan_link`
- [ ] Step 2: 确保 plan-sync.sh 被 source
- [ ] Step 3: 检查脚本语法 `bash -n scripts/cmd/archive.sh`

### Task 3: find_plan 支持搜索项目级 Plan

**Files**: `scripts/flow.sh`

**Changes**:

1. 修改 `find_plan` 函数（第 144-160 行）：
```bash
find_plan() {
    local input="$1"
    
    if [[ -z "$input" ]]; then
        log_error "Issue number or Plan name required"
        return 1
    fi
    
    # Numeric input → Issue lookup
    if [[ "$input" =~ ^[0-9]+$ ]]; then
        find_plan_by_issue "$input"
        return $?
    fi
    
    # String input → search all plan directories (global + project)
    local root_dir
    root_dir=$(find_workspace_root)
    local search_dir="$root_dir/docs/products"
    
    if [[ ! -d "$search_dir" ]]; then
        log_error "No plan directory found"
        return 1
    fi
    
    # Search: docs/products/plans/ and docs/products/*/plans/
    local matches=()
    while IFS= read -r -d '' plan_file; do
        local plan_name
        plan_name=$(basename "$plan_file" .md)
        # Match by full name or substring
        if [[ "$plan_name" == "$input" || "$plan_name" == *"$input"* ]]; then
            matches+=("$plan_file")
        fi
    done < <(find "$search_dir" -name "*.md" -not -path "*/done/*" -print0 2>/dev/null)
    
    if [[ ${#matches[@]} -eq 0 ]]; then
        log_error "No plan found matching: $input"
        echo "   Searched in: $search_dir/*/plans/" >&2
        return 1
    fi
    
    if [[ ${#matches[@]} -gt 1 ]]; then
        log_error "Multiple plans matched: $input"
        printf '  - %s\n' "${matches[@]}" >&2
        return 1
    fi
    
    echo "${matches[0]}"
}
```

**Verification**: 无 Issue Plan 可被 find_plan 找到

- [ ] Step 1: 修改 `find_plan` 搜索所有项目 plan 目录
- [ ] Step 2: 测试 `find_plan fix-dev-flow-archive-issue-plan-scope` 返回正确路径

## Delegation Strategy

N/A — Task 1 和 Task 2 有依赖关系（Task 1 函数被 Task 2 调用），Task 3 独立可并行。

## Test Plan

### Test Case Design

| 测试用例 | 目标 | 方法 | 预期结果 |
|---------|------|------|---------|
| 归档后链接更新 | Issue Plan 链接指向归档路径 | 创建测试 Issue → approve → complete → archive | Issue body Plan 链接包含 `done/YYYYMMDD` |
| find_plan 项目级搜索 | 无 Issue Plan 可被找到 | 创建项目级 Plan → approve | approve 命令找到 Plan 并执行 |

### Regression Testing

- 现有有 Issue 的 Plan 归档流程仍正常工作
- 无 Issue 的 Plan 归档流程正常（无 Issue 时跳过链接更新）
- find_plan 对 Issue 数字输入仍正常工作

### Adjustment Strategy

| 阻塞情况 | 应对策略 |
|---------|---------|
| realpath 不可用 | 用相对路径拼接替代 |
| sed 替换失败 | 用 gh issue edit 直接替换整行 |
| find 匹配过多 | 精确匹配优先，子串匹配次之 |

## Acceptance Criteria

### Agent Verification

- [x] `update_issue_plan_link` 函数在 plan-sync.sh 中定义
- [x] archive.sh 在归档后调用 `update_issue_plan_link`
- [x] `find_plan` 支持搜索所有项目 plan 目录
- [x] 脚本语法检查通过（plan-sync.sh, archive.sh, flow.sh）
- [x] 无 Issue Plan 可被 approve 命令找到（验证 find_plan）
- [x] Plan 命名已包含 scope（验证 `title_to_slug` 行为）

### User Validation

- 验证归档后 Issue Plan 链接正确指向 done/ 目录
- 验证无 Issue 流程完整可用（plan → approve → complete → archive）
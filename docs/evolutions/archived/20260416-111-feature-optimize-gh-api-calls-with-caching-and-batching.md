# 111-feature-optimize-gh-api-calls-with-caching-and-batching

## Metadata

- **Issue**: #111
- **Type**: feature
- **Target Project**: ontology
- **Created**: 2026-04-16
- **Status**: done

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

减少 `flow.sh plan` 命令 gh API 调用时间从 15-20s 至 3-5s，通过引入 Label 缓存和批量操作机制。

## Technical Context

### 当前问题

`flow.sh plan 110 --project ontology` 执行时超时（30s timeout）。根因分析：

**API 调用链追踪**：
```
cmd_plan()
  → get_space_repo()                    # gh repo view (1s)
  → get_issue_info()                     # gh issue view (1s)
  → update_issue_link()                  # gh issue view + edit (2s)
  → ensure_issue_labels()
      → ensure_flow_labels_exist()
          → ensure_label_exists() × 4    # gh label list × 4 (4s)
      → sync_status_label_group()
          → remove_issue_label() × 3     # gh issue edit × 3 (3s)
          → ensure_issue_label()         # gh issue edit (1s)
      → sync_type_label_group()
          → remove_issue_label() × 5     # gh issue edit × 5 (5s)
          → ensure_issue_label()         # gh issue edit (1s)
      → sync_project_label_group()
          → remove_issue_label() × 3     # gh issue edit × 3 (3s)
          → ensure_issue_label()         # gh issue edit (1s)
```

**关键瓶颈**：
1. `ensure_label_exists` 每次调用 `gh label list` 查询全量 labels（即使 label 已存在）
2. `sync_*_label_group` 逐个调用 `gh issue edit --add/remove-label`（多次 API 调用）
3. Issue 信息查询重复（`get_issue_info` / `update_issue_link` / `ensure_issue_labels`）

### 优化策略

| 策略 | 当前耗时 | 优化后 | 实现 |
|------|---------|--------|------|
| Label 缓存 | ~4-8s | ~1s | 全局变量缓存已知 labels |
| 批量 label 操作 | ~10s | ~1s | 单次 `gh issue edit` 多个 label |
| Issue 信息复用 | ~2s | ~1s | 一次查询复用 body + labels |

### 风险评估

- **低风险**：缓存失效场景仅限于同一脚本进程内，跨进程自动失效
- **兼容性**：bash 3.x（macOS）兼容，使用全局变量而非数组
- **回退策略**：若缓存失效可回退到原实现

## In Scope

- `lib/labels.sh`：引入 Label 缓存机制 + 批量操作函数
- `lib/issue.sh`：Issue 信息复用（可选，优先级低）
- `scripts/cmd/plan.sh`：复用优化后的函数
- 性能验证：实测 `flow.sh plan` 调用时间

## Out of Scope

- 其他 dev-flow 命令优化（approve/complete/verify 等）
- 并行 API 调用（需要更复杂架构）
- Issue 信息复用（低优先级，后续任务）

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| labels | `lib/labels.sh` | 修改 | Label 缓存 + 批量操作核心实现 |
| issue | `lib/issue.sh` | 修改 | Issue 信息复用辅助函数（可选） |

## Implementation

### Task 1: Label 缓存机制

**Files**: `lib/labels.sh`

**Changes**:
- [x] Step 1: 添加全局变量 `_LABELS_CACHE`
- [x] Step 2: 实现 `_get_all_labels_cached()` 函数
- [x] Step 3: 修改 `ensure_label_exists()` 使用缓存检查

**核心逻辑**：
```bash
# 全局缓存
_LABELS_CACHE=""

# 缓存获取函数
_get_all_labels_cached() {
    local repo="$1"
    if [[ -z "${_LABELS_CACHE:-}" ]]; then
        _LABELS_CACHE=$(gh label list --repo "$repo" --json name -q '.[].name' 2>/dev/null || echo "")
    fi
    echo "${_LABELS_CACHE:-}"
}

# 修改 ensure_label_exists
ensure_label_exists() {
    local label_name="$1"
    local repo="$2"
    
    # 从缓存检查
    if echo "$(_get_all_labels_cached "$repo")" | grep -qxF "$label_name"; then
        return 0  # 命中缓存，零网络开销
    fi
    
    # 创建 label（创建后不更新缓存，下次脚本调用会重新查询）
    # ... 原有创建逻辑 ...
}
```

**Verification**: 验证缓存生效

- [x] Step 1: 创建测试脚本调用 `ensure_label_exists` 多次
- [x] Step 2: 确认仅首次调用触发 `gh label list`

### Task 2: 批量 Label 操作

**Files**: `lib/labels.sh`

**Changes**:
- [x] Step 1: 实现 `batch_sync_issue_labels()` 函数
- [x] Step 2: 修改 `sync_*_label_group()` 使用批量操作

**核心逻辑**：
```bash
# 批量同步（单次 API 调用）
batch_sync_issue_labels() {
    local issue_number="$1"
    local repo="$2"
    local add_labels="$3"    # 空格分隔
    local remove_labels="$4" # 空格分隔
    
    local gh_args=()
    
    # 构建批量参数
    for label in $remove_labels; do
        gh_args+=(--remove-label "$label")
    done
    for label in $add_labels; do
        gh_args+=(--add-label "$label")
    done
    
    # 单次 API 调用
    if [[ ${#gh_args[@]} -gt 0 ]]; then
        gh issue edit "$issue_number" --repo "$repo" "${gh_args[@]}" >/dev/null 2>/dev/null || true
    fi
}

# 修改 sync_status_label_group
sync_status_label_group() {
    local issue_number="$1"
    local desired_label="$2"
    local repo="$3"
    
    local add_labels=""
    local remove_labels="status/planning status/in-progress status/verifying"
    
    [[ -n "$desired_label" ]] && add_labels="$desired_label"
    
    batch_sync_issue_labels "$issue_number" "$repo" "$add_labels" "$remove_labels"
}
```

**Verification**: 验证批量操作生效

- [x] Step 1: 创建测试 Issue 并调用 `sync_status_label_group`
- [x] Step 2: 确认仅触发 1 次 `gh issue edit`

### Task 3: 性能验证

**Files**: 无（验证任务）

**Changes**:
- [x] Step 1: 实测优化前 `flow.sh plan` 调用时间（基准）
- [x] Step 2: 实测优化后 `flow.sh plan` 调用时间
- [x] Step 3: 确认优化后时间 < 5s

**Verification**: 实测结果对比

- [x] Step 1: 在 Issue #111 上执行 `time flow.sh plan 111 --project ontology --check`
- [x] Step 2: 记录时间对比并更新 Plan

## Delegation Strategy

| Task | 执行者 | 理由 |
|------|--------|------|
| Task 1: Label 缓存机制 | Wopal | Shell script 改造是 Wopal 专长 |
| Task 2: 批量 Label 操作 | Wopal | 依赖 Task 1 缓存结果，不适合并行 |
| Task 3: 性能验证 | Wopal | 纯验证任务，在 `.tmp/` 隔离执行 |

**执行顺序**：Task 1 → Task 2 → Task 3（顺序执行，无并行）

**不委派 fae 的理由**：单文件修改（`lib/labels.sh`），fae 不擅长 bash 调试，委派成本高于收益

## Test Plan

#### Integration Tests

##### Case I1: Label 缓存生效验证
- Goal: 确认缓存机制减少 API 调用
- Fixture: 空间仓库（sampx/wopal-space）+ 已存在的 labels
- Execution:
  - [x] Step 1: 创建测试脚本调用 `ensure_label_exists "status/planning" "sampx/wopal-space"` 5 次
  - [x] Step 2: 检查缓存是否生效（仅首次调用触发 gh label list）
- Expected Evidence: bash 调用日志仅显示 1 次 `gh label list`

##### Case I2: 批量 Label 操作验证
- Goal: 确认批量同步减少 API 调用
- Fixture: 测试 Issue + 多个待移除 labels
- Execution:
  - [x] Step 1: 创建测试 Issue 并添加多个 labels
  - [x] Step 2: 调用 `sync_status_label_group` 并检查 gh 调用次数
- Expected Evidence: bash 调用日志仅显示 1 次 `gh issue edit`

#### Regression Tests

##### Case R1: 现有 flow.sh 功能不受影响
- Goal: 确认优化不破坏现有 dev-flow 功能
- Fixture: 空间仓库 + Issue #111
- Execution:
  - [x] Step 1: 执行 `flow.sh plan 111 --project ontology --check`
  - [x] Step 2: 确认输出正常（无错误）
- Expected Evidence: 脚本输出 "Plan passes validation" 或正确错误信息

## Acceptance Criteria

### Agent Verification

- [x] Label 缓存机制实现并通过 Case I1 验证
- [x] 批量 Label 操作实现并通过 Case I2 验证
- [x] 现有 flow.sh 功能通过 Case R1 回归测试
- [x] 实测 `flow.sh plan` 调用时间 < 5s（实测 1.92s）

### User Validation

#### Scenario 1: plan 命令执行速度显著提升
- Goal: 确认用户感知到 plan 命令执行速度变快
- Precondition: 空间仓库已配置，存在未创建 Plan 的 Issue
- User Actions:
  1. 执行 `flow.sh plan <issue> --project ontology`
  2. 观察命令完成时间
- Expected Result: 命令在 5 秒内完成（而非之前的 15-20 秒超时）

- [x] 用户已完成上述功能验证并确认结果符合预期

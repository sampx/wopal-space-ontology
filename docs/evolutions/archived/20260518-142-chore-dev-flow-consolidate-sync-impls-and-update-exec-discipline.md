# 142-chore-dev-flow-consolidate-sync-impls-and-update-exec-discipline

## Metadata

- **Issue**: #142
- **Type**: chore
- **Target Project**: wopal-space-ontology
- **Project Path**: .wopal
- **Project Type**: ontology-worktree
- **Created**: 2026-05-18
- **Status**: done

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

清理 dev-flow Plan 格式优化后遗留的 4 项技术债：合并重复 sync 实现、更新记忆规则、审查职责边界、增强 issue create 参数。

## Technical Context

### Architecture Context

dev-flow 技能在 `enhance-dev-flow-plan-format` 方案后遗留以下技术债：

1. **sync 实现重复**：`domain/issue/sync.py`（domain 层）和 `commands/sync.py`（command 层）各自维护 `sync_status_label_group`、`ensure_issue_labels`、`plan_status_to_issue_label` 等函数。此外 `commands/issue.py`、`commands/reset.py`、`commands/plan.py` 也有类似 helper 重复。

2. **记忆规则过期**：记忆 `653ec111` 的 "Step checkbox" 语义已过时，新模板使用 Done checkbox。

3. **issue create 限制**：当前只接受单行字符串参数（`--background`, `--scope`），无法输入多段落、表格、代码块，被迫用临时文件 + `issue update` 两步操作。

### Research Findings

代码重复分析结果：

| 文件 | 重复函数 | 影响调用方 |
|------|----------|-----------|
| `commands/sync.py` | `sync_status_label_group`, `ensure_issue_labels`, `plan_status_to_issue_label`, `ensure_label_exists`, `get_plan_metadata` | `cmd_sync` |
| `commands/issue.py` | `ensure_label_exists`, `sync_type_label_group`, `sync_project_label_group` | `cmd_issue_create`, `cmd_issue_update` |
| `commands/reset.py` | `sync_status_label_group` | `cmd_reset` |
| `commands/plan.py` | `_ensure_issue_labels`, `_get_issue_info` | `cmd_plan` |

**domain 层函数签名差异**：
- `domain.issue.sync.sync_status_label(issue_number: int, status: str, repo: str)` — 接 status，内部转换 label
- `commands.sync.sync_status_label_group(issue_number: str, label: str, repo: str)` — 接 label，直接操作

需要统一接口。

**参考资料**：
- `.wopal/skills/dev-flow/scripts/dev_flow/domain/issue/sync.py`
- `.wopal/skills/dev-flow/scripts/dev_flow/commands/sync.py`
- `.wopal/skills/dev-flow/scripts/dev_flow/commands/issue.py`
- `.wopal/skills/dev-flow/scripts/dev_flow/commands/reset.py`
- `.wopal/skills/dev-flow/scripts/dev_flow/commands/plan.py`

### Key Decisions

- D-01: domain 层函数保持纯逻辑（无日志），command 层包装 domain 函数并添加日志输出。统一接口为 `sync_status_label_group(issue_number: int | str, target_label: str, repo: str)` — 接 label 参数，domain 层提供适配。
- D-02: 记忆 `653ec111` 更新为 "Done checkbox" 版本，删除过时的 "Step checkbox" 语义。
- D-03: complete.py 与 check_doc.py 职责边界已清晰，无需简化。
- D-04: issue create 新增 `--body-file` 参数，支持从文件读取完整 body，避免两步操作。

## In Scope

- 合并 `commands/sync.py`、`commands/issue.py`、`commands/reset.py`、`commands/plan.py` 中的重复 helper 函数，统一导入 `domain.issue.sync`
- 更新记忆 `653ec111` 为 Done checkbox 版本
- 审查并确认 complete.py 与 check_doc.py 职责边界清晰
- issue create 新增 `--body-file` 参数

## Out of Scope

- sync 功能扩展（仅做合并，不新增功能）
- Plan 格式本身的变更（已完成）
- 其他命令的重构

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| domain | `domain/issue/sync.py` | 修改 | 统一导出接口，适配 command 层参数差异 |
| command | `commands/sync.py` | 修改 | 删除重复函数，import from domain |
| command | `commands/issue.py` | 修改 | 删除重复函数，import from domain |
| command | `commands/reset.py` | 修改 | 删除重复函数，import from domain |
| command | `commands/plan.py` | 修改 | 删除重复函数，import from domain |
| memory | LanceDB | 更新 | 记忆 `653ec111` 更新为 Done checkbox 版本 |

## Acceptance Criteria

### Agent Verification

1. [x] `rg -c 'from dev_flow.domain.issue.sync import' commands/sync.py commands/issue.py commands/reset.py commands/plan.py` ≥ 4（所有文件导入 domain 层）
2. [x] `rg -c 'def sync_status_label_group|def ensure_label_exists' commands/sync.py commands/issue.py commands/reset.py` = 0（重复函数已删除）
3. [x] `python -m pytest tests/python/unit/test_sync_consolidation.py -v` 全部 pass（新增单元测试验证合并正确性）
4. [x] `python -m pytest tests/ --tb=no -q` 5 failed → 0 failed（现有测试不回归）
5. [x] `memory_manage search query=执行纪律` 返回的记忆 `653ec111` 包含 "Done checkbox" 而非 "Step checkbox"
6. [x] `flow.sh issue create --help | grep body-file` 输出包含 `--body-file` 参数说明

### User Validation

#### Scenario 1: issue create 多段落内容验证
- Goal: 确认用户可使用 `--body-file` 输入多段落 Markdown 内容
- Precondition: dev-flow 技能已更新，Issue 测试环境可用
- User Actions:
  1. 准备一个包含多段落、表格、代码块的 Markdown 文件（如 `.tmp/test-issue-body.md`）
  2. 执行 `flow.sh issue create --title "test(scope): body-file test" --project test-project --body-file .tmp/test-issue-body.md`
  3. 在 GitHub 查看创建的 Issue body
- Expected Result: Issue body 与文件内容一致，多段落、表格、代码块渲染正确

- [x] 用户已完成上述功能验证并确认结果符合预期

## Implementation

### Task 1: Consolidate sync helper functions

**Verification Intent**: AC#1, AC#2, AC#3, AC#4

**Behavior**: 所有 commands 文件删除重复 helper，统一从 domain.issue.sync 导入；domain 层适配 command 层参数差异。

**Behavior**: 输入/输出映射：
- `domain.sync_status_label_group(42, "status/in-progress", "repo")` → 移除其他 status/* labels，添加 "status/in-progress"
- `commands/s.cmd_sync(...)` 调用 `domain.sync_status_label_group` → 与旧本地实现行为一致
- `commands/issue.py` 中 `ensure_label_exists` → 调用 domain 版本，颜色映射一致
- `commands/reset.py` 中 `sync_status_label_group` → 调用 domain 版本，label 切换行为一致
- `commands/plan.py` 中 label 操作 → 调用 domain 版本

**Files**: `commands/sync.py`, `commands/issue.py`, `commands/reset.py`, `commands/plan.py`, `domain/issue/sync.py`, `tests/python/unit/test_sync_consolidation.py`

**Pre-read**: N/A

**Design**:
分三阶段实现（RED → GREEN → REFACTOR）：

**RED 阶段**：编写测试验证期望行为
- 创建 `tests/python/unit/test_sync_consolidation.py`
- 测试用例覆盖：domain 层 `sync_status_label_group` 参数适配（int/str 兼容）、`ensure_label_exists` 颜色映射
- mock `gh` CLI 调用，验证 command 层调用 domain 函数的参数传递
- 运行测试确认失败（domain 层尚无 wrapper）

**GREEN 阶段**：实现合并
- domain/issue/sync.py：添加 `sync_status_label_group` wrapper 函数
- commands/sync.py：删除 10 个重复函数，改用 import from domain
- commands/issue.py：删除 3 个重复函数，改用 import from domain
- commands/reset.py：删除 `sync_status_label_group`，import from domain
- commands/plan.py：保留 `_get_issue_info`（逻辑特有），删除 `_ensure_issue_labels`
- 运行测试确认通过

**REFACTOR 阶段**：清理
- 统一函数签名命名（domain 层 wrapper 与 command 层调用点）
- 移除未使用的 import
- 确认所有现有测试不回归

**TDD**: true

**Changes**:

1. RED：创建 `tests/python/unit/test_sync_consolidation.py`，编写测试用例覆盖 `sync_status_label_group` 参数适配、`ensure_label_exists` 颜色映射、command 层调用 domain 的参数传递（mock gh CLI）
2. GREEN：domain/issue/sync.py 添加 `sync_status_label_group` wrapper；commands/sync.py、issue.py、reset.py、plan.py 删除重复函数并 import from domain
3. REFACTOR：统一命名、清理未使用 import、确认所有现有测试不回归

**Verify**:

```bash
cd /Users/sam/coding/wopal/wopal-workspace/.wopal/skills/dev-flow && python -m pytest scripts/dev_flow/tests/python/unit/test_sync_consolidation.py -v && rg -c 'def sync_status_label_group|def ensure_label_exists' scripts/dev_flow/commands/sync.py scripts/dev_flow/commands/issue.py scripts/dev_flow/commands/reset.py || echo "PASS: no duplicates in command layer"
```

**Done**:

任务产出：domain 层统一导出接口，command 层删除重复函数
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

### Task 2: Update execution discipline memory

**Verification Intent**: AC#5

**Behavior**: 记忆 `653ec111` 的规则文本从 "Step checkbox" 版本更新为 "Done checkbox" 版本。

**Files**: LanceDB memory entry `[653ec111]`

**Pre-read**: `.wopal/skills/dev-flow/templates/plan.md`（理解新 Done checkbox 机制）

**Design**:

当前记忆内容（过期部分）：
- "每个 Task Step 完成后立即勾选 checkbox"
- "所有 Step + AC 全部打勾"
- "Step 实际完成但 checkbox 未即时勾选"

新版本应改为：
- "每个 Task 运行 Verify 命令通过后立即勾选 Done checkbox"
- "所有 Task Done + Agent Verification checkbox 全部勾选"
- "Done 实际完成但 checkbox 未即时勾选"

**具体更新**：
1. 用 `memory_manage command=update id=653ec111` 更新文本字段
2. 保留 tags：`dev-flow,plan,checkbox,verification,AC,complete`
3. 保留 importance：0.9
4. 更新 description 内容

**TDD**: false（非代码 Task：更新数据库条目，无业务逻辑可测试）

**Changes**:

1. 执行 `memory_manage command=update id=653ec111 text="<新版本规则文本>"`

**Verify**:

```bash
memory_manage command=search query=653ec111 | grep -c "Done checkbox" && echo "PASS: memory updated" || echo "FAIL: memory not updated"
```

**Done**:

任务产出：记忆规则更新为 Done checkbox 版本
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

### Task 3: Audit complete.py vs check_doc.py boundary

**Verification Intent**: AC#4（职责边界清晰，无需变更）

**Behavior**: 确认 complete.py 与 check_doc.py 职责边界清晰，无需简化。

**Files**: `commands/complete.py`, `domain/validation/check_doc.py`

**Pre-read**: N/A

**Design**:

**当前职责划分**：
- `check_doc.py`：domain 层校验逻辑（`check_step_completion`, `check_acceptance_criteria`, `check_user_validation`）
- `complete.py`：command 层流程编排，调用 domain 校验函数

**审查结论**：
- complete.py 第162-186行调用 `check_step_completion` 和 `check_acceptance_criteria`
- complete.py 无独立校验逻辑，完全依赖 check_doc.py
- 职责边界清晰

**结论**：无需变更。Issue #142 第3项技术债是"审查"而非"修改"。

**TDD**: false（审查 Task：无代码变更，无业务逻辑可测试）

**Changes**:

1. 无代码变更（仅审查确认）

**Verify**:

```bash
cd /Users/sam/coding/wopal/wopal-workspace/.wopal/skills/dev-flow && rg -c 'def check_step_completion|def check_acceptance_criteria' scripts/dev_flow/domain/validation/check_doc.py && echo "PASS: domain layer has validation"
```

**Done**:

任务产出：职责边界审查确认清晰
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

### Task 4: Add --body-file to issue create

**Verification Intent**: AC#6

**Behavior**: 输入/输出映射：
- `issue create --title "t(s): test" --project p --body-file .tmp/body.md` → Issue body 等于文件内容
- `issue create --title "t(s): test" --project p --body-file .tmp/nonexistent.md` → 错误提示 "body-file not found"
- `issue create --title "t(s): test" --project p --body-file .tmp/body.md --goal "g"` → 优先使用 body-file，忽略结构化参数（或报错）

**Files**: `commands/issue.py`, `tests/python/unit/test_issue_body_file.py`

**Pre-read**: N/A

**Design**:
分三阶段实现（RED → GREEN → REFACTOR）：

**RED 阶段**：编写测试
- 创建 `tests/python/unit/test_issue_body_file.py`
- 测试用例：body-file 读取文件内容、文件不存在报错、body-file 与结构化参数共存行为
- mock `gh issue create` 调用，验证 body 参数传递
- 运行测试确认失败

**GREEN 阶段**：实现
- argparse 添加 `--body-file` 参数
- cmd_issue_create：实现文件读取逻辑，与结构化参数互斥处理
- 运行测试确认通过

**REFACTOR 阶段**：清理
- 统一错误消息格式
- 确认现有测试不回归

**TDD**: true

**Changes**:

1. RED：创建 `tests/python/unit/test_issue_body_file.py`，编写 3 个测试用例（文件读取、文件不存在、参数互斥）
2. GREEN：commands/issue.py 添加 `--body-file` 参数和文件读取逻辑
3. REFACTOR：统一错误消息，确认不回归

**Verify**:

```bash
cd /Users/sam/coding/wopal/wopal-workspace/.wopal/skills/dev-flow && python -m pytest scripts/dev_flow/tests/python/unit/test_issue_body_file.py -v
```

**Done**:

任务产出：issue create 支持 `--body-file` 参数
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

## Delegation Strategy

| Wave | Task | 执行者 | 依赖 | 委派理由 |
|------|------|--------|------|---------|
| 1 | Task 1 | fae | 无 | 代码重构 Task（5 文件 import 合并），TDD 流程含测试编写，委派 fae 执行 RED→GREEN→REFACTOR |
| 1 | Task 4 | fae | 无 | 代码新功能 Task（--body-file 参数），TDD 流程含测试编写，与 Task 1 无文件交集可并行 |
| 2 | Task 2 | Wopal | Task 1 | 非代码操作：更新 LanceDB 记忆条目，需展示全文确认 |
| 2 | Task 3 | Wopal | Task 1 | 非代码操作：纯审查确认，无代码变更 |
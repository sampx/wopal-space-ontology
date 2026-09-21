# 72-refactor-dev-flow-plan

## Metadata

- **Issue**: #72
- **Type**: refactor
- **Target Project**: ontology
- **Created**: 2026-04-08
- **Status**: done

## Scope Assessment

- **Complexity**: Low
- **Confidence**: High

## Goal

合并 Plan 模板中 3 组重叠章节，从 15 个 `##` 级标题精简到 12 个。

## Technical Context

当前 Plan 模板存在三处章节重叠：

1. **Code References vs Affected Components** — 两者都是"受影响代码"，只是粒度不同（文件级 vs 行级）。实际上 Code References 的行级引用可以直接放在 Affected Components 的 Key Files 列中（如 `file:line`），无需独立章节
2. **Documentation Impact vs Files** — 两者都是"文件变更记录"。Documentation Impact 本质是"需要变更的文档文件"，完全可以合并到 Files 表中（操作列标注"修改"即可）
3. **Risks & Open Questions** — 大多数 Plan 只有 1-2 行泛泛之谈，真正有用的风险应在对应 Task 的 Changes 中说明。全局性风险可附在 Technical Context 末尾

**当前章节清单**（15 个 `##` 级标题）：
Metadata, Scope Assessment, Goal, Technical Context, Affected Components, In Scope, Out of Scope, Code References, Files, Implementation, Delegation Strategy, Test Plan, Risks & Open Questions, Documentation Impact, Acceptance Criteria

**精简后**（12 个 `##` 级标题）：
Metadata, Scope Assessment, Goal, Technical Context, Affected Components, In Scope, Out of Scope, Files, Implementation, Delegation Strategy, Test Plan, Acceptance Criteria

## Affected Components

| Component | Key Files | Role |
|-----------|-----------|------|
| Plan 模板 | `projects/ontology/skills/dev-flow/templates/plan.md` | 删除 Code References / Risks / Documentation Impact 章节 |
| SKILL.md | `projects/ontology/skills/dev-flow/SKILL.md` | 同步更新 Plan 模板示例 + Spike 调查章节填充要求 |
| check-doc | `projects/ontology/skills/dev-flow/lib/check-doc.sh:223-231` | 移除 Code References 推荐 check，改为可选 |
| Spike 填充要求 | `projects/ontology/skills/dev-flow/SKILL.md:327-356` | 更新 Plan 文档填充要求模板 |

## In Scope

- [ ] 删除 `## Code References` 章节（行级引用合并到 Affected Components 的 Key Files 列）
- [ ] 删除 `## Documentation Impact` 章节（文档变更合并到 `## Files` 表）
- [ ] 删除 `## Risks & Open Questions` 独立章节（全局风险附 Technical Context 末尾）
- [ ] 修正 User Validation 为纯文本格式（#70 遗留：模板仍是 checkbox，但 `check_user_validation` 已支持跳过无 checkbox 的情况）
- [ ] 更新 `templates/plan.md`
- [ ] 更新 SKILL.md 中 Plan 模板示例（两处：Spike 填充要求 + Plan 模板格式）
- [ ] 更新 `check-doc.sh` 适配新章节结构
- [ ] 同步更新活跃 Plan 文件（#70、#50、ontology-feature-task-collab-wopal-fae）

## Out of Scope

- Implementation / Test Plan / Acceptance Criteria 等核心章节的结构调整
- done/ 目录下的历史 Plan 文件（历史文档不追溯）

## Files

| 文件 | 操作 | 说明 |
|------|------|------|
| `projects/ontology/skills/dev-flow/templates/plan.md` | 修改 | 删除 Code References / Risks / Documentation Impact 章节 |
| `projects/ontology/skills/dev-flow/SKILL.md` | 修改 | 同步 Plan 模板示例 + Spike 填充要求 |
| `projects/ontology/skills/dev-flow/lib/check-doc.sh` | 修改 | Code References 从 recommended spike check 降级或移除 |
| `docs/projects/ontology/plans/70-refactor-dev-flow-plan.md` | 修改 | 合并章节到新结构 |
| `docs/projects/ontology/plans/50-feature-add-rook-code-review-subagent.md` | 修改 | 合并章节到新结构 |
| `docs/projects/ontology/plans/ontology-feature-task-collab-wopal-fae.md` | 修改 | 合并章节到新结构 |

## Implementation

### Task 1: 更新 templates/plan.md

**Files**: `projects/ontology/skills/dev-flow/templates/plan.md`

**Changes**:
1. 删除 `## Code References` 章节（L43-48）
2. 删除 `## Risks & Open Questions` 章节（L134-136）
3. 删除 `## Documentation Impact` 章节（L138-140）
4. User Validation 从 checkbox 改为纯文本（L154-162：删除 `- [ ]` 前缀和"打勾"相关注释）
5. Affected Components 表头 Key Files 列说明更新，支持 `file:line` 格式
6. Technical Context 末尾增加"如有全局性风险在此说明"提示

**Verification**: 模板渲染正确性

- [ ] Step 1: 确认模板不包含已删除章节
- [ ] Step 2: `flow.sh plan 72 --check` 通过

### Task 2: 更新 SKILL.md

**Files**: `projects/ontology/skills/dev-flow/SKILL.md`

**Changes**:
1. Spike Plan 文档填充要求（L327-356）：删除 Code References 和 Risks & Open Questions 示例
2. Plan 模板格式（L383-454）：删除 Code References / Risks / Documentation Impact 章节
3. Affected Components 表说明支持 `file:line` 格式

**Verification**: SKILL.md 与模板一致

- [ ] Step 1: SKILL.md Plan 模板示例与 templates/plan.md 一致
- [ ] Step 2: `flow.sh plan 72 --check` 通过

### Task 3: 更新 check-doc.sh

**Files**: `projects/ontology/skills/dev-flow/lib/check-doc.sh`

**Changes**:
1. L223-231：移除 `## Code References` 推荐 check（或改为 optional warn）
2. 确认无其他对已删除章节的引用

**Verification**: check-doc 逻辑正确

- [ ] Step 1: `flow.sh plan 72 --check` 无 Code References 相关错误
- [ ] Step 2: 已有活跃 Plan 无 check-doc 报错

### Task 4: 同步活跃 Plan 文件

**Files**: `docs/projects/ontology/plans/70-refactor-dev-flow-plan.md`, `docs/projects/ontology/plans/50-feature-add-rook-code-review-subagent.md`, `docs/projects/ontology/plans/ontology-feature-task-collab-wopal-fae.md`

**Changes**:
1. Code References 内容合并到 Affected Components 的 Key Files 列（`file:line` 格式）
2. Documentation Impact 内容合并到 Files 表
3. Risks & Open Questions 中真正有价值的内容迁移到对应 Task 或 Technical Context 末尾
4. 删除已合并的章节标题

**Verification**: 活跃 Plan 结构一致

- [ ] Step 1: 三个 Plan 文件不包含已删除章节
- [ ] Step 2: 原 Code References 内容可在 Affected Components 中找到
- [ ] Step 3: 原 Documentation Impact 内容可在 Files 表中找到

### Task 5: 部署验证

**Files**: 部署层（`.agents/skills/dev-flow/`）

**Changes**:
1. 运行 `sync-to-wopal.py` 部署更新
2. 用新模板创建测试 Plan 验证端到端流程

**Verification**: 端到端流程

- [ ] Step 1: 部署后 `flow.sh plan 72 --check` 通过
- [ ] Step 2: 创建测试 Issue → start → plan --check 验证新结构

## Delegation Strategy

| 批次 | Task | 执行者 | 依赖 |
|------|------|--------|------|
| 1 | Task 1 (模板) | Wopal | 无 |
| 1 | Task 2 (SKILL.md) | Wopal | 无 |
| 1 | Task 3 (check-doc) | Wopal | 无 |
| 2 | Task 4 (同步 Plan) | fae | Task 1（模板结构确定后） |
| 3 | Task 5 (部署) | Wopal | Task 1-4 全部完成 |

## Test Plan

### Test Case Design

- templates/plan.md 不包含 `## Code References` / `## Risks` / `## Documentation Impact` 章节 ✓
- SKILL.md Plan 模板示例与 templates/plan.md 一致 ✓
- check-doc.sh 无 Code References 相关强制校验 ✓
- `flow.sh plan --check` 对新结构 Plan 通过 ✓
- 活跃 Plan 文件已合并章节、原内容可追溯 ✓

### Regression Testing

- `flow.sh complete` 对已有 Plan（#70 已 done）无影响 ✓
- check-doc.sh 对已有 Plan（包含 Code References 章节的 done/ 文件）不报错 ✓
- Spike 阶段 `flow.sh spike` 输出不受影响 ✓

### Adjustment Strategy

- N/A — 改动范围明确，仅删减章节，无逻辑变更

## Acceptance Criteria

### Agent Verification

- [x] templates/plan.md 不包含 `## Code References`、`## Risks & Open Questions`、`## Documentation Impact` 章节
- [x] Affected Components 表支持 `file:line` 格式引用
- [x] templates/plan.md User Validation 为纯文本（无 `- [ ]` 前缀）
- [x] SKILL.md Plan 模板示例中 User Validation 为纯文本
- [x] SKILL.md Spike 填充要求不引用已删除章节
- [x] check-doc.sh 无已删除章节的强制校验
- [x] 活跃 Plan 文件（#70、#50、ontology-feature-task-collab-wopal-fae）已合并章节
- [x] 部署后 `flow.sh plan 72 --check` 通过

### User Validation

- 新 Plan 模板结构更简洁，写作负担降低
- SKILL.md Spike 填充要求指引清晰

# enhance-assembly-state-ignore

## Metadata

- **Type**: enhance
- **Project Path**: .wopal
- **Created**: 2026-09-26
- **Stage**: draft
- **Mode**: (accept 时记录：isolated | quick)
- **Worktree**: (accept 时记录)
- **Branch**: (accept 时记录)
- **Base Commit**: (accept 时记录)
- **Final Commit**: (integrate 时记录：集成到空间分支后的提交)

## Scope Assessment

- **Complexity**: Low
- **Confidence**: High

## Goal

所有新建空间的骨架精确忽略 CLI 管理的私有装配运行态，同时保留受跟踪的稳定空间身份及其他用户文件。

## Technical Context

### Architecture Context

`.wopal/docs/DESIGN-assembly.md` 的 Assembly Facts and Ownership 定义空间根跟踪 `.wopal-space/space-meta.json` 的稳定身份，CLI 私有选择和保全内容进入 `.wopal-space/state/`。现行 `assembly/templates/gitignore:25-28` 只忽略 `.tmp/` 和日志；骨架 `assembly/schemas/coding-space-schema.yaml:26-27` 将此模板复制为空间根 `.gitignore`，因此新运行态会被根仓库看作普通未跟踪文件。空间 init 重跑保留用户编辑的现有 `.gitignore`，该文件的受控规则补齐属于 CLI Plan `refactor-space-assembly-state`，本提案只定义新空间模板。

### Key Decisions

- D-01: 只忽略 `.wopal-space/state/` 子树：其中的本地选择、CLI 保全与备份均属本机状态，不得进入空间根 Git；`.wopal-space/` 其他结构和用户文档保留正常跟踪能力。
- D-02: 模板与 CLI 重跑契约分工：模板决定新空间默认规则；已有空间的用户 `.gitignore` 由 CLI 在受控片段内最小补丁，不在本体模板中覆盖用户文件。
- D-03: 不编写未发布格式的兼容迁移；本空间既有快照由用户在机制可用后单独人工处理。

### Key Interfaces

空间根 `.gitignore` 包含只针对 `.wopal-space/state/` 的忽略规则；`.wopal-space/space-meta.json` 及 `.wopal-space/` 其他用户资产仍可由根仓库跟踪。无新命令或机读 schema。

## In Scope

- 更新 `assembly/templates/gitignore` 的装配状态忽略规则。
- 确认 coding/content 两类骨架物化时均引用一致的根 `.gitignore` 模板；若模板路径不同，按实际引用对齐。
- 在隔离空间验证状态子树被忽略，而稳定身份和用户资产不被忽略。

## Out of Scope

- CLI `space init` 对现有用户 `.gitignore` 的最小补丁、状态分离、导出恢复和同步修复，归 wopal-cli Plan `refactor-space-assembly-state`。
- 当前空间的旧状态清理和上行同步，由用户在实现后决定；不自动处理。

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| space skeleton | `assembly/templates/gitignore` | 修改 | 新空间根仓库忽略规则 |
| schema references | `assembly/schemas/coding-space-schema.yaml`, `assembly/schemas/content-space-schema.yaml` | 只读核对，必要时修改 | 两类空间均消费统一规则 |

## Acceptance Criteria

### Agent Verification

1. [ ] 从 coding 与 content 骨架渲染的根 `.gitignore` 均忽略 `.wopal-space/state/assembly.json` 和 `.wopal-space/state/held/` 下的文件。
2. [ ] 同一隔离空间内，`git check-ignore` 对 `.wopal-space/space-meta.json`、`.wopal-space/REGULATIONS.md` 与任一用户文档不命中；模板没有整目录忽略 `.wopal-space/`。
3. [ ] 变更仅涉及本体骨架及必要的模板引用，不改动用户实际空间的文件；文档集与模板检查通过。

### User Validation

不设 User Validation 场景：模板忽略范围及骨架引用可由 Agent 在隔离空间用 Git 和 CLI 完整验证；真实空间的人工迁移由 CLI Plan 的用户验证承载。

## Implementation

### Task 1: 新空间精确忽略 CLI 状态

**Verification Intent**: AC#1, AC#2, AC#3

**Behavior**:
- 从两类骨架新建隔离空间，状态文件被忽略；稳定身份、REGULATIONS 和用户文档均可跟踪。

**Pre-read**: `.wopal/docs/DESIGN-assembly.md`、`.wopal/assembly/templates/gitignore`、`.wopal/assembly/schemas/coding-space-schema.yaml`、`.wopal/assembly/schemas/content-space-schema.yaml`

**Design**:
模板只添加 CLI 拥有的 `state/` 子树规则；先核实两类 schema 的模板引用，不改变其他忽略规则。验证在临时目录完成，不触碰用户空间。

**TDD**: false（模板配置和文档变更，无业务逻辑；使用真实 Git 忽略判定验证）

**Changes**:
1. 在隔离空间记录现行模板的忽略判定基线。
2. 修改模板并核对两类骨架引用；用 `git check-ignore` 验证仅状态子树命中。
3. 运行本体文档质量门禁并检查变更范围。

**Verify**: 在系统临时目录分别物化 coding/content 骨架并运行 `git check-ignore -q .wopal-space/state/assembly.json`（exit 0）、`git check-ignore -q .wopal-space/space-meta.json`（exit 1）；运行 `python3 .wopal/skills/dev-doc-master/scripts/verify-docset.py .wopal/docs --main DESIGN.md`。

**Done**:
任务产出：待实施后填写。
实际触碰文件：待实施后回填。
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤

---

## Delegation Strategy

N/A：单个模板配置 Task；实施前仍遵守 ontology-evolution 技能的审查与交付纪律。

## Delivery

`space sync` 与 `ontology contribute` 由用户拍板，提案不会自动上行。

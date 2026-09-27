# refactor-assembly-refs

## Metadata

- **Type**: refactor
- **Project Path**: .wopal
- **Created**: 2026-09-26
- **Stage**: implementing
- **Mode**: quick
- **Worktree**: (none)
- **Branch**: (none)
- **Base Commit**: (none)
- **Final Commit**: (integrate 时记录：集成到空间分支后的提交)

## Scope Assessment

- **Complexity**: Low
- **Confidence**: High

## Goal

把 `assembly/archetypes/coding.yaml` 现有能力文件引用迁移为显式扩展名（`*.md` 等），保持目录引用不变，并用现行解析器在隔离环境验证兼容。它是 CLI 严格解析 Plan 的直接前置，一次实施、一次验证后归档。**不含 `paths:dsh`、根模板、提案模板与技能措辞。**

## Technical Context

### Architecture Context

- `assembly/archetypes/coding.yaml` 当前引用形如 `wopal.md`/`dev-flow` 并混有无扩展名写法；目标能力引用契约见 `.wopal/docs/DESIGN-assembly.md` 的 Capability Reference Syntax and Resolution。
- 旧解析器按候选探测工作；本迁移只需在新语法出现前完成，是 CLI Plan D-06 的显式前置。

### Key Decisions

- D-01: 只迁移现有条目到显式扩展名，不新增、不删除资产，不改目录、不改 `plugins` 分段。
- D-02: 验证即归档：用隔离目录跑通旧解析器全量，无未决任务。
- D-03: 不预先声明 `paths`，等 CLI 严格解析与 `paths` 消费交付后由 `enhance-assembly-carriers` 声明（避免新条目使旧 CLI 无法运行）。

### Key Interfaces

`coding.yaml` 能力引用满足：文件显式扩展名；目录无斜杠歧义；无悬空引用（旧解析器可消费）。不新增 CLI/文件约定。

## In Scope

- `assembly/archetypes/coding.yaml` 现有条目迁移为显式扩展名。
- 隔离环境验证旧解析器可消费迁移结果。

## Out of Scope

- CLI 严格解析与 `paths` 实现：`projects/wopal-cli` Plan。
- `paths: [dsh]` 生产声明、空间根模板、提案模板与技能文案：`enhance-assembly-carriers`。
- 真实空间实例、私有持有文件与同步：用户另行拍板。

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| coding 装配单 | `assembly/archetypes/coding.yaml` | 修改 | 现有引用显式扩展名 |

## Acceptance Criteria

### Agent Verification

1. [ ] 迁移后 `coding.yaml` 内文件引用均含显式扩展名、目录引用不变、分段插件内容不变（隔离环境）。
2. [ ] 用现行解析器在隔离目录验证全部引用可消费，无悬空/错误形态。
3. [ ] 变更范围限定在本表内单文件；文档与解析检查通过。

### User Validation

不设用户验证：文件引用迁移由隔离解析验收；实际空间迁移在相应 CLI 与执行载体中回归。

## Implementation

### Task 1: coding 引用迁移

**Verification Intent**: AC#1, AC#2, AC#3

**Behavior**: 现有条目显式化；旧解析器可消费；不产生多余变更。

**Pre-read**: `.wopal/docs/DESIGN-assembly.md`（引用语法）、`assembly/archetypes/coding.yaml`、CLI `refactor-space-assembly-state` D-06

**Design**:
先逐项核对目标树文件形态与旧解析器兼容性；文件型条目补扩展名，目录型维持目录形态；若任何条目无法确认则停止回报。

**TDD**: false（声明数据；隔离解析验证）

**Changes**:
1. 核对现有条目形态与旧解析器行为基线。
2. 迁移并运行隔离解析，确认无悬空与新语法专属条目（如 `paths`）提前声明。
3. 运行文档质量门禁并检查 diff 范围。

**Verify**: 隔离目录构造旧解析器消费命令全绿；`python3 .wopal/skills/dev-doc-master/scripts/verify-docset.py .wopal/docs --main DESIGN.md` 通过；diff 仅含装配单。

**Done**:
任务产出：待实施后回填。
实际触碰文件：待实施后回填。
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤

## Delegation Strategy

| Wave | Task | 执行者 | 依赖 | 委派理由 |
|------|------|--------|------|---------|
亲自实施不委派.

## Delivery

实施留在空间分支；`space sync` 与 `ontology contribute` 由用户拍板。
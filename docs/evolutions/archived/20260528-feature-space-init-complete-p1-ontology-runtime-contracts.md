# feat(space-init): complete p1 ontology runtime contracts

## Metadata

- **Type**: feature
- **Target Project**: wopal-space-ontology
- **Project Path**: .wopal
- **Project Type**: ontology-worktree
- **Created**: 2026-05-28
- **Status**: done
- **Worktree**: init-complete-p1-ontology-runtime-contracts | /Users/sam/coding/wopal/wopal-workspace/.worktrees/ontology-init-complete-p1-ontology-runtime-contracts

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

补齐 WopalSpace Phase 1 所需的本体初始化目标结构：提供 canonical runtime templates，让 schema 对齐 `.wopal-space/` 与 space root，并把 `/init` 收敛为面向 space runtime 的维护入口。

## Technical Context

### Architecture Context

- `wopal-cli space init` 依赖 `.wopal/templates/` 渲染 `space-root/AGENTS.md` 与 `.wopal-space/` 骨架；ontology 负责声明式模板与维护命令，CLI 只负责确定性 materialize。
- 当前 `.wopal/templates/` 只有文档模板、`memory/USER.md` 与 `wopalspace-schema.yaml`，缺少 `root-AGENTS.md`、`STRUCTURE.md`、`REGULATIONS.md`、`memory/MEMORY.md`。
- 当前 `.wopal/commands/init.md` 仍是仓库级 `AGENTS.md` 生成器，与产品 P1 所需的 space runtime 校准职责不一致。

### Research Findings

- `docs/products/wopal-space/phases/wopal-space-p1-one-click-distribution.md` 已把 ontology P1 工作收敛为 template、schema、`/init` 与空间守则目标形态。
- `docs/projects/wopal-space-ontology/DESIGN.md` 已声明目标模板集合、schema 草案、root AGENTS 职责、`REGULATIONS.md` 目标形态与 `/init` 结构校准职责，但运行时文件尚未补齐。
- `.wopal/templates/wopalspace-schema.yaml` 仍引用 `.workspace.md`，会把 CLI 初始化导向过时结构。
- 用户已明确：`cupdate-project-spec` 已删除，不再作为本阶段工作项。

**参考资料**：
- `docs/products/wopal-space/DESIGN-wopalspace.md`
- `docs/products/wopal-space/phases/wopal-space-p1-one-click-distribution.md`

### Key Decisions

- D-01: `.wopal/templates/` 是 Phase 1 初始化资产的 canonical source；必需模板缺失时 CLI fail fast，并报告缺失模板、ontology source/path 与修复建议。
- D-02: semantic template / command 变更遵循 review-first：先写 `docs/projects/wopal-space-ontology/LANG/*/` 下的用户首选语言审阅版，再同步英文 runtime 源。
- D-03: `/init` 负责已有 space 的 runtime 校准与模板差异提示；不替代 CLI 的 `space init`。
- D-04: `REGULATIONS.md` 初始化为通用空间守则，后续作为用户可持续维护的运行态文件；ontology 守则升级通过 diff/建议由用户确认后吸收。

### Key Interfaces

```text
.wopal/templates/root-AGENTS.md       -> space-root/AGENTS.md
.wopal/templates/gitignore             -> space-root/.gitignore
.wopal/templates/STRUCTURE.md         -> space-root/.wopal-space/STRUCTURE.md
.wopal/templates/REGULATIONS.md       -> space-root/.wopal-space/REGULATIONS.md
.wopal/templates/memory/USER.md       -> space-root/.wopal-space/memory/USER.md
.wopal/templates/memory/MEMORY.md     -> space-root/.wopal-space/memory/MEMORY.md
```

`/init` target behavior:
1. 读取当前 space runtime 结构
2. 识别缺失的 startup/runtime 文件
3. 检查 `REGULATIONS.md` 与模板之间需要用户人工处理的差异
4. 保留用户自定义与已有文件内容
5. 报告需要用户确认或后续处理的差异

## In Scope

- 补齐缺失的 space runtime 模板（root-AGENTS.md, STRUCTURE.md, REGULATIONS.md, memory/USER.md, memory/MEMORY.md, gitignore）及对应审阅版
- 修正 `wopalspace-schema.yaml` 的结构真相源
- 重写 `/init` 命令语义与维护边界
- 建立 `REGULATIONS.md` 通用空间守则目标形态
- 同步本项目 DESIGN / AGENTS 中与模板与 `/init` 相关的实现真相

## Out of Scope

- `manifest.yaml`
- `wopal space validate`
- `wopal-cli` 的 `space init` / `setup` 实现
- ellamaka runtime 能力改造
- cupdate 命令族重命名或新增

## Business Rules Impact

N/A — 无业务规则变更。本计划补的是 runtime template / command contract，不引入新的产品域规则。

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| Runtime templates | `.wopal/templates/root-AGENTS.md`, `.wopal/templates/STRUCTURE.md`, `.wopal/templates/REGULATIONS.md`, `.wopal/templates/gitignore`, `.wopal/templates/memory/USER.md`, `.wopal/templates/memory/MEMORY.md` | 创建/修改 | 提供 canonical init assets，并补齐 `USER.md`/`MEMORY.md` 职责边界 |
| Schema | `.wopal/templates/wopalspace-schema.yaml` | 修改 | 对齐目标 runtime 结构 |
| Init command | `.wopal/commands/init.md` | 重写 | space runtime 校准、runtime 检查与模板差异提示入口 |
| Review copies | `docs/projects/wopal-space-ontology/LANG/*/templates/*`, `docs/projects/wopal-space-ontology/LANG/*/commands/init.md` | 创建/修改 | preferred-language review-first workflow |
| Project docs | `docs/projects/wopal-space-ontology/DESIGN.md`, `.wopal/AGENTS.md` | 修改 | 同步 template / init contract 真相 |

## Acceptance Criteria

### Agent Verification

1. [x] `test -f ".wopal/templates/root-AGENTS.md" && test -f ".wopal/templates/STRUCTURE.md" && test -f ".wopal/templates/REGULATIONS.md" && test -f ".wopal/templates/gitignore" && test -f ".wopal/templates/memory/USER.md" && test -f ".wopal/templates/memory/MEMORY.md"` exit 0
2. [x] `rg -n '\.workspace\.md' ".wopal/templates/wopalspace-schema.yaml"` 无输出
3. [x] `rg -n 'space-master|agents-collab|dev-flow' ".wopal/templates/REGULATIONS.md"` 至少匹配 3 行
4. [x] `rg -n 'STRUCTURE\.md|REGULATIONS\.md|runtime|diff|confirm' ".wopal/commands/init.md"` 至少匹配 5 行
5. [x] `test -n "$(rg --files "docs/projects/wopal-space-ontology/LANG" | rg '/templates/root-AGENTS\.md$')" && test -n "$(rg --files "docs/projects/wopal-space-ontology/LANG" | rg '/templates/STRUCTURE\.md$')" && test -n "$(rg --files "docs/projects/wopal-space-ontology/LANG" | rg '/templates/REGULATIONS\.md$')" && test -n "$(rg --files "docs/projects/wopal-space-ontology/LANG" | rg '/templates/memory/USER\.md$')" && test -n "$(rg --files "docs/projects/wopal-space-ontology/LANG" | rg '/templates/memory/MEMORY\.md$')"` exit 0
6. [x] `test -n "$(rg --files "docs/projects/wopal-space-ontology/LANG" | rg '/commands/init\.md$')"` exit 0
7. [x] `rg -n 'root-AGENTS\.md|STRUCTURE\.md|REGULATIONS\.md|memory/USER\.md|memory/MEMORY\.md|/init' "docs/projects/wopal-space-ontology/DESIGN.md" ".wopal/AGENTS.md"` 至少匹配 5 行
8. [x] `rg -nc 'space-master|agents-collab|dev-flow|REGULATIONS|技能路由' ".wopal/templates/root-AGENTS.md"` stdout 0 — root-AGENTS 不承载核心技能说明或流程路由

### User Validation

#### Scenario 1: 审阅初始化模板契约
- Goal: 确认 canonical 模板集合完整表达了新 space 所需的启动入口与 runtime 文件
- Precondition: 变更已完成，审阅版与英文 runtime 源均可打开
- User Actions:
  1. 打开 `root-AGENTS.md`、`STRUCTURE.md`、`REGULATIONS.md`、`memory/USER.md`、`memory/MEMORY.md`
  2. 对照当前 `main` space 的目标结构检查字段与边界
- Expected Result: 模板集合完整，`USER.md` / `MEMORY.md` 职责边界清晰，`REGULATIONS.md` 明确承载通用空间守则与核心技能入口概要

#### Scenario 2: `/init` 命令文档已转向 runtime 维护
- Goal: 确认 `/init` 的命令文档内容已从仓库级 AGENTS 生成器转向 space runtime 校准与模板差异提示
- Precondition: `/init` 命令文档（`.wopal/commands/init.md` 及 LANG 审阅版）已完成重写
- User Actions:
  1. 阅读 `.wopal/commands/init.md`，确认其目标变为读取现状、校准结构、提示模板差异、等用户确认后写入
  2. 对照审阅版确认语义一致
- Expected Result: `/init` 文档以 `STRUCTURE.md` / `REGULATIONS.md` / runtime 校准为中心，不再把目标描述为“生成仓库 AGENTS.md”

- [x] 用户已完成上述功能验证并确认结果符合预期

## Implementation

### Task 1: 补齐 runtime templates 与审阅版

**Verification Intent**: AC#1, AC#3, AC#5, AC#8

**Behavior**: ontology 提供完整的 runtime template 集合；模板内容与当前目标 space 结构一致，并先产生用户首选语言审阅版再同步英文 runtime 源。

**Files**: `.wopal/templates/root-AGENTS.md`, `.wopal/templates/STRUCTURE.md`, `.wopal/templates/REGULATIONS.md`, `.wopal/templates/gitignore`, `.wopal/templates/memory/USER.md`, `.wopal/templates/memory/MEMORY.md`, `docs/projects/wopal-space-ontology/LANG/*/templates/*`

**Pre-read**: `.wopal-space/STRUCTURE.md`, `.wopal-space/REGULATIONS.md`, `.wopal-space/memory/USER.md`, `docs/projects/wopal-space-ontology/DESIGN.md`

**Design**:
- 以当前 `main` space 的 startup/runtime 真相为蓝本，抽象出可分发模板，去掉本空间私有值
- 在审阅版中先用用户语言表达模板标题与正文，再同步到英文 runtime 源
- `memory/USER.md` 需纳入本次对齐，明确它与 `MEMORY.md` 的边界，避免 canonical template set 缺口
- `REGULATIONS.md` 模板需包含通用空间守则与核心技能入口概要：`space-master`、`agents-collab`、`dev-flow`
- `MEMORY.md` 模板只提供文件型长期记忆骨架，不预填当前 space 的私有记忆

**TDD**: false

**Changes**:
1. 创建缺失的六个 runtime 模板（root-AGENTS.md, gitignore, STRUCTURE.md, REGULATIONS.md, memory/USER.md, memory/MEMORY.md）与对应 `LANG/*/` 审阅版
2. 审视并对齐现有 `.wopal/templates/memory/USER.md` 与其 `LANG/*/` 审阅版，保证 `USER.md` 与 `MEMORY.md` 模板职责分离
3. 在 `REGULATIONS.md` 模板中加入通用空间守则与核心技能入口概要

**Verify**:
`test -f ".wopal/templates/root-AGENTS.md" && test -f ".wopal/templates/gitignore" && test -f ".wopal/templates/STRUCTURE.md" && test -f ".wopal/templates/REGULATIONS.md" && test -f ".wopal/templates/memory/USER.md" && test -f ".wopal/templates/memory/MEMORY.md" && rg -n 'space-master|agents-collab|dev-flow' ".wopal/templates/REGULATIONS.md" && ! rg -n 'space-master|agents-collab|dev-flow|REGULATIONS|技能路由' ".wopal/templates/root-AGENTS.md" && test -n "$(rg --files \"docs/projects/wopal-space-ontology/LANG\" | rg '/templates/root-AGENTS\\.md$')" && test -n "$(rg --files \"docs/projects/wopal-space-ontology/LANG\" | rg '/templates/STRUCTURE\\.md$')" && test -n "$(rg --files \"docs/projects/wopal-space-ontology/LANG\" | rg '/templates/REGULATIONS\\.md$')" && test -n "$(rg --files \"docs/projects/wopal-space-ontology/LANG\" | rg '/templates/memory/USER\\.md$')" && test -n "$(rg --files \"docs/projects/wopal-space-ontology/LANG\" | rg '/templates/memory/MEMORY\\.md$')"`

**Done**:
任务产出：runtime template 集合与审阅版齐备，可作为 CLI `space init` 的 canonical source
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

### Task 2: 修正 schema 草案并重写 `/init` 维护目标

**Verification Intent**: AC#2, AC#4, AC#6

**Behavior**: `wopalspace-schema.yaml` 描述新的 runtime / space 初始化结构；`/init` 描述 runtime 校准、runtime 检查与模板差异提示，目标从仓库级 AGENTS 生成转向 space runtime 维护。

**Files**: `.wopal/templates/wopalspace-schema.yaml`, `.wopal/commands/init.md`, `docs/projects/wopal-space-ontology/LANG/*/commands/init.md`

**Pre-read**: `.wopal/templates/wopalspace-schema.yaml`, `.wopal/commands/init.md`, `docs/products/wopal-space/phases/wopal-space-p1-one-click-distribution.md`, `docs/projects/wopal-space-ontology/DESIGN.md`

**Design**:
- schema 采用 `runtime` / `space` 概念命名，显式声明 `STRUCTURE.md` / `REGULATIONS.md` / `memory/*` 与 root `AGENTS.md` / `.gitignore` 映射
- `/init` 文案按“读取现状 → 校准结构 → 检查 runtime → 提示模板差异 → 等用户确认后写入”重写
- `/init` 保留 Wopal 的交互式确认风格，不把 deterministic init 逻辑搬进 ontology command

**TDD**: false

**Changes**:
1. 更新 `wopalspace-schema.yaml` 的 runtime 结构与 truth source
2. 重写 `.wopal/commands/init.md` 的目标、调查范围、执行顺序与输出约束
3. 同步 `LANG/*/commands/init.md` 审阅版，确保中英文语义一致

**Verify**:
`! rg -n '\.workspace\.md' ".wopal/templates/wopalspace-schema.yaml" && rg -n 'runtime:|space:|STRUCTURE\.md|REGULATIONS\.md|root-AGENTS\.md|gitignore' ".wopal/templates/wopalspace-schema.yaml" && rg -n 'STRUCTURE\.md|REGULATIONS\.md|runtime|diff|confirm' ".wopal/commands/init.md" && test -n "$(rg --files "docs/projects/wopal-space-ontology/LANG" | rg '/commands/init\.md$')"`

**Done**:
任务产出：schema 草案与 `/init` 目标对齐 Phase 1 初始化目标
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

### Task 3: 同步项目文档与维护规范

**Verification Intent**: AC#7

**Behavior**: 项目文档与开发规范准确反映新的 template/init 边界，避免后续再把缺失模板误判为已完成。

**Files**: `docs/projects/wopal-space-ontology/DESIGN.md`, `.wopal/AGENTS.md`

**Pre-read**: `docs/projects/wopal-space-ontology/DESIGN.md`, `.wopal/AGENTS.md`, `docs/products/wopal-space/phases/wopal-space-p1-one-click-distribution.md`

**Design**:
- 更新 DESIGN 中 template set、初始化契约和 Phase 1 实施真相
- 仅在现有 AGENTS 不能覆盖新约束时补充 `.wopal/AGENTS.md`，避免把一次性实施细节写进长期规则
- 不回溯修改历史计划文档

**TDD**: false

**Changes**:
1. 修正 DESIGN 中对 template completeness 与 `/init` 职责的陈述
2. 检查 `.wopal/AGENTS.md` 是否需要新增 repo-specific maintenance guidance；需要则最小补充
3. 保持产品 phase doc、project DESIGN 与 runtime source 的同一真相

**Verify**:
`rg -n 'root-AGENTS\.md|STRUCTURE\.md|REGULATIONS\.md|memory/USER\.md|memory/MEMORY\.md|/init' "docs/projects/wopal-space-ontology/DESIGN.md" ".wopal/AGENTS.md"`

**Done**:
任务产出：ontology 项目文档与维护规范已同步新的初始化契约
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

## Delegation Strategy

| Wave | Task | 执行者 | 依赖 | 委派理由 |
|------|------|--------|------|---------|
| 1 | Task 1 | fae | 无 | 模板与审阅版需成组创建，适合单个实现代理连续处理 |
| 2 | Task 2 | fae | Task 1 | schema 与 `/init` 依赖模板目标形态稳定后再收敛 |
| 3 | Task 3 | fae | Task 2 | 文档同步必须基于最终 template/init 实现真相 |

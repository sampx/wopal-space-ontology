# enhance-assembly-carriers

## Metadata

- **Type**: enhance
- **Project Path**: .wopal
- **Created**: 2026-09-27
- **Stage**: draft
- **Mode**: (accept 时记录：isolated | quick)
- **Worktree**: (accept 时记录)
- **Branch**: (accept 时记录)
- **Base Commit**: (accept 时记录)
- **Final Commit**: (integrate 时记录：集成到空间分支后的提交)

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: Medium

## Goal

CLI 的 `refactor-space-assembly-state` Plan 全部交付后，一次性把 ontology 装配载体对齐新契约：`coding.yaml` 声明 `paths: [dsh]`；空间根 `.gitignore` 模板仅忽略 CLI 保盘的私有持有内容；提案模板增加 `Assembly Intent`；`ontology-evolution` 技能中的 `--local` 与状态提交措辞与自动提交事实一致。**本提案启动时全部前置已交付，内部无中途等待另一个 Plan 的任务。**

## Technical Context

### Architecture Context

前提：CLI 已提供严格引用解析、`paths` 消费、单文件 `space-meta.json` 状态与限路径提交（`refactor-space-assembly-state` done）。本体提案 `refactor-assembly-refs` 已把 `coding.yaml` 现有文件引用迁移为显式扩展名。本提案只改动本体静态资产，不实现 CLI 机制。

- `paths` 生效面见 `./../DESIGN-assembly.md` Generic Path Assembly；本提案只把已存在的 `dsh/` 声明为类型默认，不新增内容。
- 根模板目标态只忽略私有持有的实际文件路径，不忽略 `.wopal-space/state/` 整目录或 `space-meta.json`；模板只负责新空间，既有空间的 `.gitignore` 补丁归已交付的 CLI。
- 提案模板按 `ontology-evolution` 技能结构新增 `## Assembly Intent`：新建整项资产逐项声明 `type-default` / `space-local`。
- 技能 Maintenance Protocols 把 `--local` 描述为「状态变化时 CLI 限路径提交空间根仓库」，不得写零提交，也不得暗示自动上行。

### Key Decisions

- D-01: 本提案是一次实施、一次验证、一次归档；验收全部通过即关闭，不把部分界面留到后续载体。
- D-02: `paths: [dsh]` 只在 CLI `paths` 消费已交付后声明；整目录物化与碰撞校验在隔离工作区用真实 Git 断言。
- D-03: 私有内容保盘路径以已交付 CLI 契约为准（`.wopal-space/state/held/` 等）；模板不忽略注册的装配状态与任何用户文档。
- D-04: 技能措辞对齐状态提交事实，内容上行仍由用户逐次 `space sync` / `ontology contribute` 决定。

### Key Interfaces

`coding.yaml` 增加 `paths: [dsh]`（目录引用）；`assembly/templates/gitignore` 增加 CLI 保盘私有内容规则；提案模板 `## Assembly Intent` 表字段为 `Ref / Scope / 理由`；技能命令面不变，无新增机器接口。

## In Scope

- `assembly/archetypes/coding.yaml`：`paths: [dsh]` 声明。
- `assembly/templates/gitignore`：私有保盘内容忽略规则；核对 `assembly/schemas/coding-space-schema.yaml` 模板引用。
- `skills/ontology-evolution/templates/proposal.md`：`Assembly Intent` 表与托管说明。
- `skills/ontology-evolution/SKILL.md`：`--local` 状态提交、维护命令与交付措辞对齐。

## Out of Scope

- CLI 严格解析、`path:` 选择、稀疏与状态机制：已交付 `refactor-space-assembly-state`。
- `coding.yaml` 现有能力条目的显式扩展名迁移：已交付 `refactor-assembly-refs`。
- 本体三个插件配置消费（ONT-G5）：独立提案 `refactor-plugin-config-consumption`。
- 武器库清单、派发与会话规则注入（ONT-G2/G3）：未定稿讨论。
- 既有空间 `.gitignore` 维护与真实空间迁移；上游交付由用户拍板。

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| coding 装配单 | `assembly/archetypes/coding.yaml` | 修改 | `paths: [dsh]` |
| 骨架模板 | `assembly/templates/gitignore`, `assembly/schemas/coding-space-schema.yaml` | 修改/核对 | 仅忽略私有持有内容 |
| 进化载体 | `skills/ontology-evolution/templates/proposal.md`, `skills/ontology-evolution/SKILL.md` | 修改 | 装配归属与状态提交语义 |

## Acceptance Criteria

### Agent Verification

1. [ ] 隔离工作区内 `coding.yaml` 的 `paths: [dsh]` 经 CLI 物化出 `.wopal/dsh` 整目录，与能力类目/保留目录无碰撞；引用缺失时 fail。
2. [ ] 隔离空间 `git check-ignore` 只命中约定私有持有文件；`space-meta.json`、`REGULATIONS.md` 与用户文档不命中；两类骨架的模板引用核对一致。
3. [ ] 新提案模板的 `Assembly Intent` 表格可被工具解析校验；技能文案不再出现「`--local` 零提交/永不上行」，且状态提交与用户逐次上行分开表达。

### User Validation

不设用户验证：全部变更在隔离工作区由 Agent 验证；真实空间迁移与运行时观察归此阶段 CLI Plan 的用户验证或后续运行时讨论。

## Implementation

### Task 1: 类型路径声明与空间根模板

**Verification Intent**: AC#1, AC#2

**Behavior**: 隔离物化 `dsh` 整目录；私有保持内容被忽略、状态文件可跟踪。

**Pre-read**: `.wopal/docs/DESIGN-assembly.md`、`assembly/archetypes/coding.yaml`、`assembly/templates/gitignore`、`assembly/schemas/coding-space-schema.yaml`

**Design**: 不再分批：CLI 验收完成后在此 Task 直接声明并物化；忽略规则按 CLI 定稿路径一次写全并在临时目录验证。

**TDD**: false（声明与模板；真实 Git + CLI 隔离验证）

**Changes**:
1. 隔离目录预置 `dsh/` 内容，先跑 CLI 物化基线。
2. 修改装配单与模板，跑物化与 `git check-ignore` 断言。
3. 核对 schema 引用并复查差异范围。

**Verify**: 临时目录运行 `git check-ignore` 两组断言（私有内容 exit 0；`space-meta.json`/`REGULATIONS.md` exit 1），运行已有隔离物化校验命令。

**Done**:
任务产出：待实施后回填。
实际触碰文件：待实施后回填。
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤

### Task 2: 提案模板与技能措辞

**Verification Intent**: AC#3

**Behavior**: 新模板含归属表；技能维护协议与自动状态提交对齐。

**Pre-read**: `skills/ontology-evolution/templates/proposal.md`、`skills/ontology-evolution/SKILL.md`

**Design**: 在模板加入 `Assembly Intent` 节并说明只登记新增整项资产；技能按最终契约改文案，运行技能自带文档校验。

**TDD**: false（模板与文档；结构样例校验）

**Changes**:
1. 编辑模板与技能文案。
2. 用一份样例提案验证 `Assembly Intent` 解析;运行文档质量门禁。

**Verify**: `python3 .wopal/skills/dev-doc-master/scripts/verify-docset.py .wopal/docs --main DESIGN.md` 通过，样例提案通过 `space evo check`（隔离环境）。

**Done**:
任务产出：待实施后回填。
实际触碰文件：待实施后回填。
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤

## Delegation Strategy

| Wave | Task | 执行者 | 依赖 | 委派理由 |
|------|------|--------|------|---------|
| 1 | Task 1 | fae | CLI Plan 已 done | 同为装配载体命名与忽略规则 |
| 1 | Task 2 | fae | CLI 状态契约已定稿 | 文档/技能协议与载体互不阻挡 |

## Delivery

实施留在空间分支；`space sync` 与 `ontology contribute` 由用户拍板。
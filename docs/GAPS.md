# GAPS — 设计优化落地追踪

> **Status**: Active
> **Updated**: 2026-09-12
> **Parent Architecture**: `./DESIGN.md`
> **Companion**: 本文档追踪 2026-09 设计优化（中央能力池 + 装配 worktree + `space sync`）的目标态与实现落地偏差，按项目归属拆分，逐项解决后关闭。

---

## 背景

2026-09 设计优化确立「中央能力池 + 空间装配 worktree」模型：local main 集中维护能力，空间按装配单 sparse-checkout 物化为可写 worktree，进化经 `space sync` 汇入 local main，类型语义由装配单承载（不设 `type/*` 分支）。

设计已定稿并归一至 DESIGN / DESIGN-distribution / 产品级 DESIGN / wopal-cli DESIGN。以下为**实现落地 gap**，按项目归属拆分。

---

## 项目归属

| 项目 | 负责的落地项 |
|------|-------------|
| **wopal-cli** | `space sync`、`space status`、`space capability`、`ontology` 命令面改造、装配物化、`prepare-ontology` 装配语义（onboarding CLI machine operation） |
| **ontology** | 装配单资产、Agent 体系资产清理、Evolver 等新代理 |
| **产品级** | 跨项目一致性维护（onboarding 设计文档对齐；ellamaka 项目仅消费 CLI machine operation，无实现残留） |

---

## Gap 清单

### CLI-G1: `space sync` 双向同步命令未实现（wopal-cli, P0）

**目标态**: `wopal space sync` 与 local main 双向对齐——先上行（隔离临时 worktree 整合空间独有进化，成功才推进、冲突即停）、后下行（fast-forward 到 local main 最新）、刷新装配版本。dry-run 预览 → `--confirm` 执行。

**当前状态**: wopal-cli 仍实现旧的 `space update`（merge type/*）与 `space contribute`（squash 到 type/*）；`space sync` 不存在。

**落地**: 新增 `space sync`，移除 `space update` / `space contribute`；实现定序、隔离整合、fast-forward 与工作区状态检查。

### CLI-G2: `space status` / `space capability` 未对齐新语义（wopal-cli, P0）

**目标态**: `space status` 展示空间分支 ↔ local main 同步状态 + 装配状态；`space capability add/remove` 增删装配单能力并重新物化（移除含未提交修改的能力时保留文件并警告）。

**当前状态**: `space status` 仍展示 space ↔ type 分支；`space capability` 不存在。

### CLI-G3: ontology 命令面改造未实现（wopal-cli, P0）

**目标态**: `ontology install` 只物化 local main + 类型装配单；`ontology update` 仅 upstream/main → local main（无 top-down 多分支）；`ontology contribute` 仅 fork 模式、local main → upstream PR；删除 `ontology reconcile` / `ontology promote`。

**当前状态**: `install` 物化全部 type/* 分支；`update` top-down 多分支合并；`reconcile` / `promote` 仍在命令面。

### CLI-G4: Space Init 装配物化未实现（wopal-cli, P0）

**目标态**: `space init --type <type>` 读取 `config/types/<type>.yaml` 装配单，sparse-checkout 物化 `.wopal/` worktree，写入 `.wopal-space/assembly.yaml`。

**当前状态**: `space init` 映射 `type/<type>` 分支、materialize 全量 worktree，无装配单消费、无 assembly.yaml。

### CLI-G5: 装配技术可行性已验证，需固化实现规范（wopal-cli, P0）

**目标态**: 装配物化基于 Git `worktree` + `sparse-checkout` + `merge --ff-only` + 隔离临时 worktree，正常推进全 fast-forward，冲突在隔离 worktree 中处理。

**当前状态**: 技术在 `.wopal-space/.tmp/git-assembly-spike.*` 已实测通过（独立装配、快进更新/贡献、事务隔离、脏文件保护），未固化进实现。

### ONB-G1: onboarding `prepare-ontology` 装配语义未实现（wopal-cli, P0）

**目标态**: onboarding 的 `prepare-ontology`（CLI machine operation）物化 local main 与类型装配单（`config/types/*.yaml`），供 `space init --type` 消费；类型选择走装配单而非 type/* 分支。

**当前状态**:
- 设计文档已对齐：产品级 `DESIGN-onboarding.md` 的 `prepare-ontology` 已更新为"物化 local main 与类型装配单"；产品级 DESIGN 与 ellamaka onboarding 文档均已明确「operation 语义由 wopal-cli 实现、ellamaka/Desktop 仅消费」的边界。
- wopal-cli 实现仍残留 type/*：`setup-operations.ts` `prepare-ontology` 收集并物化全部 `type/*` 分支；`types/cli.ts` 的 `BehindCommonAnalysis` / `AheadOfCommonAnalysis` 均基于 type/* 分支。需随 CLI-G3 一并改造。

### ONT-G1: 装配单资产未建立（ontology, P0）

**目标态**: `config/types/<type>.yaml`（common/coding/content 等）声明类型默认装配的 agents/skills/rules，作为空间初始化模板与公共能力演进。

**当前状态**: `config/types/` 不存在。

### ONT-G2: Agent 体系资产未清理、未新建、未瘦身（ontology, P0）

**目标态**: `agents/` 仅含四维核心 + 按类型装配的专职子代理；8 个微型伪专员移除；Evolver 与 writer/editor/analyst/statistician 建立；核心提示词瘦身至 ~40 行。

**当前状态**: 8 个伪专员仍在（architect、code-reviewer、code-simplifier、code-skeptic、data、docs-specialist、frontend-specialist、test-engineer）；Evolver 及新代理不存在；核心提示词未瘦身。

### ONT-G3: WSF 资产与新装配模型关系未定义（ontology, P1）

**目标态**: `.wopal/wsf/` 资产与新「按类型装配」模型的关系明确（保留作 skill 引用 / 迁移 / 移除）。

**当前状态**: `.wopal/wsf/` 仍存在，关系未定义。

### DOC-G1: space-master 技能仍描述旧多分支模型（ontology, P1）

**目标态**: `space-master` 技能的 ontology 维护指南对齐新模型（space sync、装配、Evolver 回流），去除 type/* 分支与 promote/reconcile 流程。

**当前状态**: `skills/space-master/SKILL.md` 及 `references/ontology-maintenance.md` 仍描述 main → type/* → space/* 三层分支与 space contribute / ontology promote。

---

## 解决顺序建议

1. CLI-G1~G5 + ONB-G1（wopal-cli 命令面、装配实现与 onboarding 流程，设计主体落地）
2. ONT-G1~G2（装配单资产 + Agent 体系清理，装配物化的内容前提）
3. DOC-G1（space-master 技能对齐）
4. ONT-G3（WSF 资产决策）

---

## Related Documents

| 文档 | 说明 |
|------|------|
| `./DESIGN.md` | 设计目标态真相源（Ontology 协作模型章节） |
| `./DESIGN-distribution.md` | 分发与装配契约 |
| `../../projects/wopal-cli/docs/DESIGN.md` | CLI 命令面设计与空间装配实现 |
| `../../docs/products/wopal-space/DESIGN.md` | 产品级架构（Ontology 装配模型章节） |

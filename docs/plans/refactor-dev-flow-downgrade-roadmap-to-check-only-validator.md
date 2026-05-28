# refactor(dev-flow): simplify roadmap to project-only check + decompose

## Metadata

- **Type**: refactor
- **Target Project**: wopal-space-ontology
- **Project Path**: .wopal
- **Project Type**: ontology-worktree
- **Created**: 2026-05-27
- **Updated**: 2026-05-29 — 简化设计：砍掉项目 phase 文档，roadmap 仅操作项目 DESIGN §8
- **Status**: planning

## Goal

1. 简化阶段文档管道：只保留产品 phase 文档（`phase-product.md`），项目 phase 文档不再独立存在。产品 phase 目标通过 cupdate-roadmap 自动级联到各项目 DESIGN §8。
2. roadmap 命令降级为项目 DESIGN 专属校验 + 分解工具：校验项目 DESIGN §8 格式、关联产品 phase doc 完整性；通过后从项目 DESIGN §8 创建 Issue 或直接创建 Plan（1:1）。
3. phase 模板结构化：对齐 Plan 模板的 Metadata 风格，字段可脚本校验。

## Architecture

### 简化后的完整管道

```
Product PRD + Product DESIGN §9 (Evolution Roadmap)
  │
  │ /cupdate-roadmap (产品模式，唯一入口)
  │  → 生成 product phase docs (跨项目)
  │  → 自动回写 project DESIGN §8 (各项目目标 + `> Phase doc:` 引用)
  ▼
┌─────────────────────────┐
│ Product Phase Docs       │  ← 唯一 phase doc（跨项目视角）
│ phases/<p>-pN-<slug>.md │     Involved Projects 含多项目
│ (结构化模板，可脚本校验)   │
└─────────────────────────┘
         │ 级联
    ┌────┴────────────────────┐
    ▼                         ▼
┌───────────────┐   ┌───────────────┐
│ Project A     │   │ Project B     │
│ DESIGN §8     │   │ DESIGN §8     │
│ ### Phase N   │   │ ### Phase N   │
│ > Phase doc   │   │ > Phase doc   │
│ 目标/已落地/缺口│   │ 目标/已落地/缺口│
└───────┬───────┘   └───────┬───────┘
        │                   │
        └─────────┬─────────┘
                  │
     flow.sh roadmap <project> --check    (脚本校验)
     flow.sh roadmap <project> --decompose (创建 Issue)
     flow.sh roadmap <project> --decompose --plan (直接创建 Plan)
                  │
                  ▼
        ┌──────────────────┐
        │  Issue → Plan    │  (项目级, 1:1)
        │  projects/  │    每 phase 1 Issue + 1 Plan
        │  <project>/docs/plans/│
        └──────────────────┘
```

**砍掉**：`phase-project.md` 模板、`phases/<project>-pN-<slug>.md` 项目 phase 文档、cupdate-roadmap 项目模式的独立 phase doc 生成。

### 各层职责

| 层级 | 谁产出 | 产物 | 跨项目 | 校验方式 |
|------|--------|------|--------|---------|
| 产品 phase | `/cupdate-roadmap` (产品模式) | 1 个 phase doc | 是（Involved Projects 含多项目） | 脚本格式 + agent 内容 |
| 项目 DESIGN §8 | `/cupdate-roadmap` 自动回写 | DESIGN §8 phase 目标 | 否（每项目独立） | `road --check` 脚本校验 |
| Issue/Plan | `road --decompose` | 1 Issue + 1 Plan | 否（项目级） | dev-flow 状态机 |

## Technical Context

### Phase Doc 模板结构化（`phase-product.md`）

对齐 Plan 模板的 `## Metadata` 风格，字段可脚本校验：

```markdown
# Phase {id}: {title}

## Metadata
- **Product**: `<product>`
- **Phase ID**: P0 | P1 | P2...
- **Status**: Planned | Active | Completed
- **Created**: YYYY-MM-DD
- **Updated**: YYYY-MM-DD

## Goal
<!-- MUST: 一句话产品能力陈述。禁止占位符、禁止"继续 Phase N"的循环引用。 -->

## Involved Projects
<!-- MUST: ≥1 行，Role ∈ {core delivery, tooling, enablement} -->
| Project | Role | Notes |
|---------|------|-------|

## Exit Criteria
<!-- MUST: ≥1 条，每条 `- [ ] \`<project>\`: <可验证条件>` -->
- [ ] `<project>`: <条件>

## Risks
<!-- MUST: ≥1 条，表格格式 -->
| Risk | Impact | Mitigation |
|------|--------|------------|

## Decomposition Hints
<!-- 供 road --decompose 创建 Issue/Plan 时注入上下文 -->
- **Suggested Plan Type**: feature | enhance | fix | refactor
- **Key Context**: <agent 分解 Issue/Plan 时需要知道的技术背景>
```

### Project DESIGN §8 格式要求

road --check 校验 enforce：

```markdown
### Phase {N}: {title}
> Phase doc: [phases/<product>-p{N}-<slug>.md](phases/<product>-p{N}-<slug>.md)
- **目标**：<本项目在本阶段的分工目标，≥20 字符>
- **已落地**：<已实现，≥10 字符或 无>
- **剩余缺口**：<待实现，≥10 字符或 无>
```

### 命令接口

```bash
flow.sh roadmap                          # 无参：所有项目 DESIGN §8 phase 状态总览
flow.sh roadmap <project>                # --check（默认）：校验项目 DESIGN §8 格式 + 关联产品 phase doc
flow.sh roadmap <project> --decompose    # 为 DESIGN §8 每个 phase 创建 1 个 Issue
flow.sh roadmap <project> --decompose --plan   # 直接创建 Plan（跳过 Issue）
flow.sh roadmap <project> --decompose P1        # 仅处理指定 phase
flow.sh roadmap <project> --decompose --dry-run # 预览，不创建
```

`<project>` 是 `projects/` 下的项目名（如 `wopal-cli`）。

### road --decompose 创建逻辑

**Issue 路径**（`--decompose`，无 `--plan`）：
1. 读项目 DESIGN §8 phase 信息 + 关联的产品 phase doc
2. 从产品 phase doc 提取 Goal、Exit Criteria、Decomposition Hints
3. 每条 phase → 1 个 Issue：
   - Title: `feat({project}): P{N} — {goal_summary}`
   - Body: Product/Phase/Phase Doc 元数据 + Goal + Exit Criteria 种子
   - Labels: `status/planning`, `type/feature`, `project/{project}`
4. 用户后续 `flow.sh plan <issue>` 进入标准 Issue-driven 路径

**Plan 路径**（`--decompose --plan`）：
1-2 同上
3. 每条 phase → 1 个 Plan（复用 `create_plan_from_template()`）：
   - Plan 目录: `projects/{project}/docs/plans/`
   - Plan 名: `{type}-{project}-p{N}-{slug}`
   - Body: 注入 product/phase/phase_doc/goal/exit_criteria 上下文
4. 直接进入 `approve → execute → complete → verify → archive` 标准流程

### road --check 校验矩阵

格式正确性由脚本保证，内容正确性由人类/AI 审核。

**项目 DESIGN §8 校验**：

| 校验项 | 执行者 | 规则 | 失败级别 |
|--------|--------|------|---------|
| Phase heading `### Phase \d+:` 存在 | 脚本 | Regex | FAIL |
| `> Phase doc:` 引用存在 | 脚本 | 行级匹配 | FAIL |
| 引用路径真实 | 脚本 | `os.path.isfile` | FAIL |
| 目标/已落地/剩余缺口 非空 | 脚本 | 每字段 ≥10 字符 | FAIL |
| Phase ID 匹配产品 phase doc | 脚本 | §8 heading 编号 = phase doc Phase ID | WARN |

**产品 Phase Doc 校验**：

| 校验项 | 执行者 | 规则 | 失败级别 |
|--------|--------|------|---------|
| Metadata 字段齐全 | 脚本 | Product/Phase ID/Status/Created/Updated 均存在 | FAIL |
| Phase ID 匹配 `P\d+` | 脚本 | Regex | FAIL |
| Status ∈ {Planned, Active, Completed} | 脚本 | 枚举 | FAIL |
| Goal 非空非占位符 | 脚本 | 排除空/`_(none)_`/`TBD`/`TODO` | FAIL |
| Involved Projects ≥1 数据行 | 脚本 | 表行计数 | FAIL |
| Role ∈ {core delivery, tooling, enablement} | 脚本 | 枚举 | FAIL |
| Exit Criteria ≥1 checkbox | 脚本 | `- [ ]` 计数 | FAIL |
| Exit Criteria 项目前缀格式 | 脚本 | 每条以 `` - [ ] `<project>`: `` 开头 | WARN |
| Risks ≥1 数据行 | 脚本 | 表行计数 | FAIL |
| Decomposition Hints > Suggested Plan Type 非空 | 脚本 | 枚举 ∈ {feature, enhance, fix, refactor} | FAIL |
| Goal 是否为可验证的产品能力陈述 | 人/AI | 主观判断 | — |
| Exit Criteria 条目是否可测试 | 人/AI | 主观判断 | — |
| Project Role 分配是否准确 | 人/AI | 主观判断 | — |

### Key Decisions

- D-01: 砍掉项目 phase 文档。产品 phase 是唯一 phase doc，项目目标直接写在 DESIGN §8。
- D-02: roadmap 只接受 `<project>` 参数（无需 product/project 双模式分支）。模式由 `projects>/<name>/docs/DESIGN.md` 路径自动确定。
- D-03: Phase doc 模板统一使用 `## Metadata` 格式（`- **Field**: value`），不再使用 blockquote 元数据格式。
- D-04: 校验分两层——脚本负责格式（字段存在、枚举值、Regex），人/AI 负责内容质量（Goal 可验证性、Exit Criteria 可测试性）。
- D-05: `--decompose --plan` 读产品 phase doc 做上下文注入（Goal/Exit Criteria/Decomposition Hints），确保 Plan 有足够 Agent 可消费的上下文。
- D-06: `--decompose` 不自动创建 Plan——Issue 是独立步骤。`--plan` 显式跳过 Issue。

## In Scope

- 重写 `roadmap.py`：check 模式（校验 project DESIGN §8 + 关联产品 phase doc）、decompose 模式（创建 Issue 或 Plan）
- 重构 `phase-product.md` 模板：统一 Metadata 格式，新增 Scope Assessment / Exit Criteria 结构化 / Decomposition Hints
- 删除 `phase-project.md` 模板
- 更新 `cupdate-roadmap` 命令：移除项目模式 phase doc 生成，保留自动级联到 project DESIGN §8
- 更新 `/cupdate-design` 命令：项目模式创建时保证 §8 格式符合校验要求
- 修改 `create_plan_from_template()` 新增 `goal` / `exit_criteria` 可选参数（用于 phase→Plan 上下文注入）
- 更新 SKILL.md、commands.md
- 单元测试：check 校验 + decompose 创建

## Out of Scope

- `/cupdate-prd`、`/cupdate-design` 产品模式流程
- `/cupdate-agent-rules`、`/cupdate-readme`
- ROADMAP.md Slices 表解析
- 已存在的 `phase-project.md` 实例文件（保留不动，不强制迁移）

## Business Rules Impact

N/A — 纯技术重构 + 管道简化，无业务规则变更。

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| roadmap 命令 | `scripts/commands/roadmap.py` | 重写 | check + decompose 核心逻辑 |
| plan 创建函数 | `scripts/commands/plan.py` | 修改 | `create_plan_from_template()` 新增参数 |
| 产品 phase 模板 | `templates/phase-product.md` | 重写 | 结构化模板 |
| 项目 phase 模板 | `templates/phase-project.md` | 删除 | 不再需要 |
| cupdate-roadmap | `commands/cupdate-roadmap.md` | 修改 | 移除项目模式 phase doc 生成 |
| cupdate-design | `commands/cupdate-design.md` | 修改 | 项目模式 §8 格式对齐 |
| dev-flow 技能文档 | `SKILL.md` | 修改 | roadmap check + decompose 章节 |
| 命令参考 | `references/commands.md` | 修改 | roadmap 说明 |
| 单元测试 | `tests/python/unit/test_roadmap_check.py` | 创建 | check + decompose 测试 |

## Acceptance Criteria

### Agent Verification

所有命令在 `.wopal/skills/dev-flow` 下执行。

**check 模式**：

1. [ ] `flow.sh roadmap --help` 显示 `<project>`、`--check`、`--decompose`、`--plan`、`--dry-run`
2. [ ] `flow.sh roadmap` 无参输出所有项目 DESIGN §8 的 phase 总览
3. [ ] `flow.sh roadmap wopal-cli` 等价于 `flow.sh roadmap wopal-cli --check`
4. [ ] 对 §8 格式合规的项目→全部 PASS，exit 0
5. [ ] `> Phase doc:` 引用文件不存在→FAIL
6. [ ] 目标/已落地/剩余缺口 为空→FAIL
7. [ ] 关联产品 phase doc Metadata 字段缺失→FAIL
8. [ ] 产品 phase doc Goal 为空→FAIL
9. [ ] 产品 phase doc Involved Projects 无数据→FAIL
10. [ ] 产品 phase doc Exit Criteria 无 checkbox→FAIL
11. [ ] 产品 phase doc Role 不在枚举内→WARN

**decompose 模式**：

12. [ ] `flow.sh roadmap <p> --decompose --dry-run` 显示将创建的 Issue，不实际创建
13. [ ] `flow.sh roadmap <p> --decompose` 每 phase 创建 1 个 Issue，body 含 Product/Phase/Phase Doc 元数据
14. [ ] Issue labels 含 `status/planning`、`type/feature`、`project/{p}`
15. [ ] `flow.sh roadmap <p> --decompose P1` 仅创建 P1 的 Issue
16. [ ] `flow.sh roadmap <p> --decompose --plan --dry-run` 预览 Plan，不创建
17. [ ] `flow.sh roadmap <p> --decompose --plan` 每 phase 创建 1 个 Plan
18. [ ] Plan 文件与 `flow.sh plan --title "..." --project <p> --type feature` 格式一致
19. [ ] Plan Metadata 含 Product/Phase 字段，Goal 与产品 phase doc 一致
20. [ ] `--decompose --plan` 缺少 `--project`（或无法从 DESIGN 推断项目）时报错

**清理**：

21. [ ] `rg -c '_discuss\|_produce\|_decompose' scripts/commands/roadmap.py` = 0
22. [ ] `ls templates/phase-project.md` 不存在
23. [ ] `python -m pytest tests/python/ -v` 全部 pass

### User Validation

- [ ] 用户已完成功能验证并确认结果符合预期

## Implementation

### Task 1: 重写 phase 模板 + 更新 cupdate 命令

**Behavior**: `phase-product.md` 重构为结构化模板，Metadata 改用 `## Metadata` 格式，新增 Decomposition Hints 节。`cupdate-roadmap` 移除项目模式 phase doc 生成环节。`cupdate-design` 确保项目 §8 格式符合校验要求。`phase-project.md` 删除。

**Files**: `templates/phase-product.md`(重写), `templates/phase-project.md`(删除), `commands/cupdate-roadmap.md`(修改), `commands/cupdate-design.md`(修改)

**Done**:
- [ ] Agent 完成并确认

---

### Task 2: 重写 roadmap.py（check + decompose）

**Behavior**: 新 roadmap.py 支持：无参总览、`<project> --check`（校验 §8 + 产品 phase doc）、`<project> --decompose`（创建 Issue）、`<project> --decompose --plan`（直接创建 Plan）。按校验矩阵区分脚本校验和内容校验。decompose 读产品 phase doc 做上下文注入。

**Files**: `scripts/commands/roadmap.py`(重写), `scripts/commands/plan.py`(修改)

**Done**:
- [ ] Agent 完成并确认

---

### Task 3: 编写单元测试 + 清理已有测试

**Behavior**: check 模式测试（10+ 用例）+ decompose 模式测试（8+ 用例）。清理已废弃函数测试。全量 pass。

**Files**: `tests/python/unit/test_roadmap_check.py`(创建), 受影响的已有测试文件(修改)

**Done**:
- [ ] Agent 完成并确认

---

### Task 4: 更新文档

**Behavior**: 更新 SKILL.md roadmap 章节、commands.md 命令参考。

**Files**: `SKILL.md`(修改), `references/commands.md`(修改)

**Done**:
- [ ] Agent 完成并确认

## Delegation Strategy

| Wave | Task | 执行者 | 依赖 | 委派理由 |
|------|------|--------|------|---------|
| 1 | Task 1 | fae | 无 | 模板 + cupdate 命令修改（独立） |
| 2 | Task 2 | fae | Task 1 | 依赖最终模板格式 + API 签名 |
| 2 | Task 3 | fae | Task 2 | road.py 稳定后测 |
| 3 | Task 4 | fae | Task 2 | 文档依赖命令接口 |

# dev-flow: roadmap 工作流 + Issue 体系优化

## Metadata

- **Type**: feature
- **Target Project**: wopal-space-ontology
- **Project Path**: .wopal
- **Project Type**: ontology-worktree
- **Created**: 2026-05-26
- **Status**: executing
- **Worktree**: add-roadmap-workflow | /Users/sam/coding/wopal/wopal-workspace/.worktrees/ontology-add-roadmap-workflow

## Scope Assessment

- **Complexity**: High
- **Confidence**: High

## Goal

为 dev-flow 添加 `roadmap` 命令（产品阶段规划前置工作流），并大规模简化 Issue 模板/命令体系（借鉴 GSD decompose-into-slices 设计），根治当前"模板多、参数杂、上下文断裂"三大顽疾。

## Design Analysis: 当前 Issue 体系问题诊断

### 问题 1: 6 个模板,90% 冗余

| 模板 | 行数 | 与 `issue.md` 的差异 |
|------|------|-------------------|
| `issue.md` | 27 | 基准 |
| `issue-fix.md` | 43 | +4 section (Confirmed Bugs, Content Model Defects, Cleanup Scope, Key Findings) |
| `issue-refactor.md` | 33 | +2 section (Affected Components, Refactor Strategy) |
| `issue-perf.md` | 33 | +2 section (Baseline, Target) |
| `issue-test.md` | 33 | +2 section (Test Scope, Test Strategy) |
| `issue-docs.md` | 33 | +2 section (Target Documents, Audience) |

每种类型只差 1-2 个专属 section，但整个骨架被完整复制。GSD 的反例：所有 milestone/slice/plan 使用统一模板，type-specific 内容由 agent 在自由文本区写入。

### 问题 2: 20+ CLI 参数,对 Agent 是灾难

`issue create` 有 20 个 CLI flag（goal, background, scope, out_of_scope, confirmed_bugs, content_model_defects, cleanup_scope, key_findings, baseline, target, affected_components, refactor_strategy, target_documents, audience, test_scope, test_strategy, body, body_file, reference, acceptance_criteria）。Agent 不可能记住这些参数，实际上只用过 `--body-file`。

根本原因：CLI 被设计为"参数拼装 body"，但 agent 应该直接用 markdown 写 body。

### 问题 3: 上下文断裂（最严重）

`sync` 用 Plan 内容**全量覆盖** Issue body → agent 之前在 Issue 中写的任何研究结论、决策依据、分析过程全部丢失。GSD 的反例：context 通过 markdown 文档自然流动，每个阶段产出的文档都是可以被后续阶段读取的独立 artifact。

### 问题 4: `decompose-prd` 能力极弱

只解析 PRD 的 `Phase N:` heading，生成光秃秃的 body：
```markdown
## Source
From PRD: [path](../path)

## Phase Description  
<title>

---
This Issue was auto-created by dev-flow decompose-prd.
```

没有任何结构化上下文传递、无依赖信息、无 scope 界定。

### 借鉴 GSD decompose-into-slices 的设计精华

| GSD 做法 | 当前 dev-flow | 差距 |
|----------|-------------|------|
| 1 个 roadmap 模板服务于所有 milestone | 6 个 issue 模板按 type 区分 | 6x 冗余 |
| Agent 直接写 markdown 到文件，无需 CLI flag | 20+ CLI flag 拼装 body | 对 agent 极不友好 |
| 上下文在 markdown 文档间自然流动（SUMMAR→下一个 PLAN 的 Pre-read） | sync 全量覆盖导致上下文丢失 | **致命** |
| Slices 表格式：`- [ ] **S01: Title** \`risk:high\` \`depends:[]\`` | Phase table 无格式约定 | 无法机器解析 |
| Boundary Map：Produces/Consumes 契约 | 无跨 Phase 契约 | 信息丢失 |
| Forward Intelligence：每个 slice summary 含 "What the next slice should know" | Issue 间无上下文传递 | 重复探索 |

### ROADMAP.md Slices 表语法规范（最小可执行契约）

ROADMAP.md 的 Slices 表是 `decompose --from ROADMAP.md` 的解析输入。以下是正式格式契约：

**表格格式**：Markdown table，位于 `## Slices` 标题下。

| 列名 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `Slice` | 是 | `S01`, `S02`, ... | Slice 编号，用于 Issue 标题：`feat({project}): S01 — {title}` |
| `Title` | 是 | text | Slice 标题，同时用作 Issue title 描述和 `## Goal` |
| `Project` | 是 | text | 目标项目名（对应 `--project` label）。若 `=` 前缀（如 `=ontology`），表示与父 ROADMAP 的默认 project 相同 |
| `Risk` | 否 | `high\|medium\|low` | 风险等级，默认 `medium` |
| `Depends` | 否 | `S01, S02` 或 `none` | 逗号分隔的前置 Slice 编号。空或 `none` 表示无依赖。填入 `## Depends on` 并在 Issue body 中渲染为：`- S01: {title}`（通过 cross-reference ROADMAP.md 解析 slice title） |
| `Demo` | 否 | text | 演示验证描述。填入 `## Demo` 节。来源：ROADMAP.md 中该 Slice 的 `After this:` 行（位于 Slice 描述段落末尾） |

**Slice 描述段落格式**（每个 Slice 在 ROADMAP.md 中对应一段 prose）：

```markdown
### S01: {Title}
{description paragraph}

After this: {demo verification text}
```

**解析规则**：
- Parser 读取 `## Slices` 下的 markdown table，提取列值
- 对于每个 Slice，额外搜索对应 `### S01: {Title}` 段落，提取 `After this:` 行作为 Demo 列值
- `Depends` 列中的 Slice 编号仅用于生成 `## Depends on` 列表；不执行拓扑排序（人工保证顺序）
- 若 `Project` 列以 `=` 开头，取其后的字符串作为 project 名

**最小示例**：

```markdown
## Slices

| Slice | Title | Project | Risk | Depends | Demo |
|-------|-------|---------|------|---------|------|
| S01 | CLI 多空间管理 | =space-flow | high | none | `wopal space list` 显示多空间 |
| S02 | 空间切换热加载 | space-flow | medium | S01 | 切换空间后 3s 内配置生效 |

### S01: CLI 多空间管理
... description ...

After this: `wopal space list` 显示多空间

### S02: 空间切换热加载
... description ...

After this: 切换空间后 3s 内配置生效
```

## Key Interfaces（模块间契约）

本 Plan 涉及多个模块的接口变更。以下定义关键契约，避免并行实施时接口冲突：

### Interface 1: Plan metadata ↔ Issue body（`plan.py` + `plan/body.py`）

**职责边界**：
- `plan.py:_extract_product_phase_from_body()` — 从 Issue body 读取 `- **Product**:` / `- **Phase**:`，**纯读取**
- `plan.py:create_plan_from_template()` — 接收 `product` / `phase` 参数，填入 Plan template 的 `{product_line}` / `{phase_line}` 占位符，**纯写入**
- `plan/body.py:build_issue_body_from_plan()` → 简化为 `build_plan_link_for_issue()` — 只返回 Plan 链接 markdown 行（用于 sync 更新 Related Resources），**不构建完整 body**

**数据流**：
```
Issue body (Product/Phase meta)
  → plan.py 读取 → Plan template 占位符 → Plan 文件
  → plan/body.py 读取 Plan → 生成 Plan 链接行 → sync.py 写入 Issue Related Resources
```

**依赖声明**：Task 2（plan.py）和 Task 5（sync 行为变更 + body.py 简化）串行执行：Task 2 必须先完成 metadata 继承接口，Task 5 才能基于稳定的 Plan 模板格式设计简化的 body builder。

### Interface 2: ROADMAP.md Slices → decompose Issue（`decompose.py`）

**数据流**：
```
ROADMAP.md (Slices table + ### Snn: paragraphs)
  → decompose.py:parse_roadmap_slices() → Slice dataclass list
  → decompose.py:create_slice_issue() → Issue (title + body + labels)
```

**Slice dataclass**（内部契约）：
```python
@dataclass
class Slice:
    id: str           # "S01"
    title: str        # "CLI 多空间管理"
    project: str      # "space-flow"（已解析 = 前缀）
    risk: str         # "high" | "medium" | "low"
    depends: list[str]  # ["S01"] 或 []
    demo: str         # After this: 后的文本，或 ""
```

### Interface 3: issue write --append 行为契约

**行为规则**：
1. **分隔符**：append 前在现有 body 末尾插入 `\n\n`，再拼接新内容
2. **空文件**：若 `--body-file` 指向空文件或文件不存在，报错退出（exit 1）
3. **重复追加**：允许同一文件多次 append（每次追加均加 `\n\n` 分隔）
4. **文件类型**：不校验文件内容类型，但输出 warning 若文件不以 `#` 或 `-` 开头
5. **尾部换行**：拼接后保证 body 以 `\n` 结尾

### Interface 4: Phase 文档 schema（Produce → Decompose 输入链）

Phase 文档由 Task 1 Produce 阶段写入，Task 5 Decompose 读取。以下字段必须可机器解析：

```markdown
# Phase {id}: {title}

## Metadata
- **Phase ID**: {id}       ← format: "P1", "P2", ...
- **Product**: {product}   ← 产品线名
- **Status**: {status}

## Goal
{goal summary}

## Involved Projects
- project: {name}, scope: {description}
- project: {name}, scope: {description}

## Exit Criteria
- {criterion 1}
- {criterion 2}
```

Decompose 读取 `## Metadata` 获取 Phase ID / Product，读取 `## Involved Projects` 确定每个 Issue 的 project label。

### Architecture Context

dev-flow 当前缺少产品阶段规划的前置流程，且 Issue 体系过度工程化。本次变更分两大模块：

**模块 A: roadmap 命令**（四阶段工作流）

`Analyze → Discuss → Produce → Decompose` 四阶段工作流：
- **Analyze**：读取 PRD/DESIGN，输出阶段分析报告
- **Discuss**：逐 phase 与用户 CLI 交互确认目标、范围、涉及项目、退出条件
- **Produce**：按模板写入 phase 定义文档，同步 PRD 引用
- **Decompose**：从 phase 文档或 roadmap 为每个涉及项目生成 Issue，注入 Product/Phase 元信息；或从 ROADMAP.md 的 Slices 表直接生成 Issue

**模块 B: Issue 体系优化**（借鉴 GSD）

- 6→1 模板：删除 type-specific 模板，统一为 `issue-stub.md`
- 20+→3 CLI 参数：`issue create` 只保留 `--title`、`--project`、`--body-file`（+ `--type` 可选）
- 新增 `issue write --append`：agent 可渐进式注入上下文，不覆盖已有内容
- `sync` 不再全量覆盖 body：只更新 Related Resources 中的 Plan 链接
- `decompose-prd` → `decompose`：支持 `--from roadmap.md` 从 Slices 表生成 Issue

### Key Decisions

- D-01: `roadmap` 替代 `decompose-prd` 作为产品阶段规划的唯一入口
- D-02: 四阶段工作流中，Analyze 全自动，Discuss 通过 CLI `input()` 交互，Produce 和 Decompose 全自动
- D-03: Decompose 阶段复用 `build_structured_issue_body()` 构建 Issue body，在 body 顶部注入 Product/Phase 元数据行
- D-04: `flow.sh plan <issue>` 通过 `_extract_product_phase_from_body()` 从 issue body 自动继承 Product/Phase
- D-05: 删除 5 个 type-specific 模板（`issue-fix/refactor/perf/test/docs.md`），统一为 `issue-stub.md`——agent 在 Context section 自由写入 type-specific 内容
- D-06: 新增 `issue write --append` 命令替代 20+ CLI 参数和 section-by-section 更新——agent 写 markdown 到临时文件，然后追加到 Issue body
- D-07: `sync --body-only` 不再全量覆盖 Issue body——只更新 `## Related Resources` 中的 Plan 链接行。Agent 写入的 Context 内容永不丢失
- D-08: 简化 `build_structured_issue_body()`：移除所有 type-specific section 渲染逻辑，统一为 `Goal → Context → Scope → AC → Related Resources` 五段结构

## In Scope

**模块 A: roadmap 命令**
- 新增 `flow.sh roadmap <prd-path> [--product <product>] [--project <project>]` 命令
- Analyze/Discuss/Produce/Decompose 四阶段实现（含 phase 数据结构、文档命名规则、字段定义）
- ROADMAP.md Slices 语法规范实现（`parse_roadmap_slices()` parser）
- `plan.py` 新增 Product/Phase 解析：`_extract_product_phase_from_body()` + Plan metadata 填充
- `plan/body.py` 简化为 `build_plan_link_for_issue()` — 只返回 Plan 链接行
- `flow.sh` / `flow.py` 路由注册
- dev-flow SKILL.md + references/commands.md 文档更新
- 单元测试：roadmap 核心逻辑 + plan 元信息继承 + Slices parser

**模块 B: Issue 体系优化**
- 删除 5 个 type-specific 模板，创建统一 `issue-stub.md`
- `build_structured_issue_body()` 简化为五段统一结构
- `issue create` 缩减参数：只保留 `--title`, `--project`, `--body-file`, `--type`(可选)
- 新增 `issue write <issue> --append <path>` 命令
- `issue write <issue> --body-file <path>` 全量替换
- `issue update` 废弃（`issue write --append` 替代 section-by-section 更新）
- `sync --body-only` 行为变更：只更新 Plan 链接，不覆盖全文
- `decompose-prd` → `decompose --from <source>`（支持 PRD 和 ROADMAP.md）
- 清理 `replace_issue_section()` / `update_structured_issue_body()` 等已被替代的函数
- 更新 commands.md 命令参考
- 更新受影响测试

## Out of Scope

- `decompose-prd` 别名保留兼容（内部重定向到 `decompose --from`）
- Issue label 系统变更：继续使用现有 `project/*`、`status/*`、`type/*` 标签体系
- phase 文档自动同步 PRD 引用：Produce 阶段写引用，后续手动维护

## Business Rules Impact

N/A — 无业务规则变更，dev-flow 内部命令扩展与重构。

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| roadmap 命令 | `dev-flow/scripts/dev_flow/commands/roadmap.py` | 创建 | 四阶段工作流实现 |
| 命令路由 | `dev-flow/scripts/flow.py` | 修改 | 注册 roadmap 子命令 |
| 脚本路由 | `dev-flow/scripts/flow.sh` | 修改 | PYTHON_COMMANDS 添加 roadmap |
| plan 元信息继承 | `dev-flow/scripts/dev_flow/commands/plan.py` | 修改 | 新增 Product/Phase 解析与 Plan metadata 填充 |
| Plan 模板 | `dev-flow/templates/plan.md` | 修改 | metadata section 新增 product/phase 占位符 |
| Issue 模板统一 | `dev-flow/templates/issue-stub.md` | 创建 | 统一 Issue stub 模板 |
| Issue 模板清理 | `dev-flow/templates/issue-fix.md` | 删除 | |
| Issue 模板清理 | `dev-flow/templates/issue-refactor.md` | 删除 | |
| Issue 模板清理 | `dev-flow/templates/issue-perf.md` | 删除 | |
| Issue 模板清理 | `dev-flow/templates/issue-test.md` | 删除 | |
| Issue 模板清理 | `dev-flow/templates/issue-docs.md` | 删除 | |
| Issue 模板更新 | `dev-flow/templates/issue.md` | 修改 | 更新为简化版（保留兼容） |
| Issue 命令简化 | `dev-flow/scripts/dev_flow/commands/issue.py` | 修改 | 缩减 create 参数 + 新增 write 命令 |
| Issue body 简化 | `dev-flow/scripts/dev_flow/domain/issue/body.py` | 修改 | 移除 type-specific 渲染 |
| Sync 行为变更 | `dev-flow/scripts/dev_flow/commands/sync.py` | 修改 | body sync 只更新 Plan 链接 |
| Plan body 简化 | `dev-flow/scripts/dev_flow/domain/plan/body.py` | 修改 | 简化 sync body 导出 |
| decompose 升级 | `dev-flow/scripts/dev_flow/commands/decompose.py` | 修改 | 支持 --from roadmap.md |
| 技能文档 | `dev-flow/SKILL.md` | 修改 | Roadmap 章节 + Issue 体系更新 |
| 命令参考 | `dev-flow/references/commands.md` | 修改 | roadmap + issue write 说明 |
| Issue 格式参考 | `dev-flow/references/issue-format.md` | 修改 | 更新 Issue body 结构说明 |
| Phase 模板 | `.wopal/templates/phase.md` | 已完成 | 阶段定义文档模板 |
| 单元测试 | `dev-flow/tests/python/unit/test_roadmap_analyze.py` | 创建 | |
| 单元测试 | `dev-flow/tests/python/unit/test_roadmap_decompose.py` | 创建 | |
| 单元测试 | `dev-flow/tests/python/unit/test_roadmap_produce.py` | 创建 | |
| 单元测试 | `dev-flow/tests/python/unit/test_plan_product_phase.py` | 创建 | |
| 单元测试 | `dev-flow/tests/python/unit/test_issue_write.py` | 创建 | issue write + append 测试 |
| 单元测试 | `dev-flow/tests/python/unit/test_roadmap_slices_parse.py` | 创建 | ROADMAP.md Slices parser 测试 |
| 单元测试 | `dev-flow/tests/python/unit/test_append_boundary.py` | 创建 | append 边界行为测试 |
| 单元测试 | `dev-flow/tests/python/unit/test_sync_preserves_context.py` | 创建 | sync 不覆盖 Context 测试 |
| 单元测试 | `dev-flow/tests/python/unit/test_update_deprecated.py` | 创建 | issue update 废弃警告测试 |
| 单元测试 | `dev-flow/tests/python/unit/test_issue_body_file.py` | 修改 | 适配简化参数 |
| 集成测试 | `dev-flow/tests/python/integration/test_issue_create_command.py` | 修改 | 适配简化参数 |
| 集成测试 | `dev-flow/tests/python/integration/test_issue_update_command.py` | 修改 | 适配 update→write 迁移 |

## Acceptance Criteria

### Agent Verification

1. [ ] `python -m pytest .wopal/skills/dev-flow/tests/python/ -v` 全部 pass
2. [ ] `rg -c 'roadmap' .wopal/skills/dev-flow/scripts/flow.sh` ≥ 1（路由注册）
3. [ ] `rg -c 'roadmap' .wopal/skills/dev-flow/scripts/flow.py` ≥ 1（Python 路由）
4. [ ] `rg -c 'Roadmap' .wopal/skills/dev-flow/SKILL.md` ≥ 1（技能文档）
5. [ ] `rg -c 'issue write' .wopal/skills/dev-flow/references/commands.md` ≥ 1（命令参考）
6. [ ] `rg -c '_extract_product_phase_from_body' .wopal/skills/dev-flow/scripts/dev_flow/commands/plan.py` ≥ 1
7. [ ] `rg -c '--append' .wopal/skills/dev-flow/scripts/dev_flow/commands/issue.py` ≥ 1（issue write append）
8. [ ] `test -f .wopal/skills/dev-flow/templates/issue-stub.md`（新模板存在）
9. [ ] `test ! -f .wopal/skills/dev-flow/templates/issue-fix.md`（旧模板已删除 ×5）
10. [ ] `rg -c 'issue write' .wopal/skills/dev-flow/SKILL.md` ≥ 1（技能文档已更新）
11. [ ] `test -f .wopal/skills/dev-flow/templates/issue.md`（旧模板保留兼容）且内容包含五段结构
12. [ ] `python -c "from dev_flow.commands.issue import cmd_issue_update; print('ok')"` 可导入（issue update 兼容）
13. [ ] `echo '' > /tmp/empty.md && flow.sh issue write <issue> --append /tmp/empty.md 2>&1; echo $?` 返回 1（空文件报错）
14. [ ] 连续两次 `--append /tmp/a.md; --append /tmp/b.md` 后 body 含 `\n\n` 分隔：`gh issue view <issue> --json body | python3 -c "import json,sys; b=json.load(sys.stdin)['body']; lines=b.split('\n'); assert len(lines) >= 3"` exit 0
15. [ ] `python -m pytest .wopal/skills/dev-flow/tests/python/ -v -k "test_append_boundary or test_sync_preserves_context or test_roadmap_slices_parse"` 全部 pass

### User Validation

#### Scenario 1: Roadmap 完整流程验证
- Goal: 确认 roadmap 四阶段工作流能正常产出 phase 文档和 Issue
- Precondition: PRD 包含阶段定义章节
- User Actions:
  1. 执行 `flow.sh roadmap docs/projects/wopal-space-ontology/PRD.md`
  2. 观察四阶段输出
- Expected Result: phase 文档符合模板，Issue 携带 Product/Phase 元信息和标签

- [ ] 用户已完成上述功能验证并确认结果符合预期

#### Scenario 2: Plan 继承 Product/Phase
- Goal: 确认 `flow.sh plan <issue>` 从 roadmap Issue 中继承 Product/Phase
- Precondition: Issue 由 roadmap Decompose 阶段创建
- User Actions:
  1. `flow.sh plan <issue-from-roadmap>`
  2. 检查 Plan metadata section
- Expected Result: Plan 包含 `- **Product**: <product>` 和 `- **Phase**: <phase-id>` 行

- [ ] 用户已完成上述功能验证并确认结果符合预期

#### Scenario 3: Issue write --append 渐进注入上下文
- Goal: 确认 agent 可通过 `issue write --append` 不丢失已有内容
- Precondition: Issue 已创建，含初始 body
- User Actions:
  1. 写研究结论到 `/tmp/research.md`
  2. 执行 `flow.sh issue write <issue> --append /tmp/research.md`
  3. 查看 Issue body——原内容保留，新内容追加
  4. 再执行 `flow.sh sync <issue> --body-only`
  5. 查看 Issue body——Context 内容未被 sync 覆盖
- Expected Result: append 保留原内容，sync 不覆盖 Context

- [ ] 用户已完成上述功能验证并确认结果符合预期

## Implementation

### Task 1: 创建 roadmap.py + 注册路由

**Verification Intent**: AC#1, AC#2, AC#3

**Behavior**: 新建 `roadmap.py` 实现四阶段工作流，并在 `flow.sh` / `flow.py` 中注册路由。

**Files**: `dev-flow/scripts/dev_flow/commands/roadmap.py`(创建), `dev-flow/scripts/flow.sh`(修改), `dev-flow/scripts/flow.py`(修改)

**Pre-read**: plan.py 模板填充模式, decompose.py PRD 解析模式, phase.md 模板

**Design**:

命令入口 `cmd_roadmap(args)` 按 Analyze→Discuss→Produce→Decompose 执行。每个阶段有明确的输入→输出契约：

**Analyze（全自动）**：
- 输入：PRD/DESIGN 文件路径
- 输出：`List[PhaseInfo]` — 每个 PhaseInfo 含 `id (str)`, `title (str)`, `goal (str)`, `involved_projects (List[str])`, `exit_criteria (List[str])`
- 实现：正则匹配 PRD 中 `## Phase N:` 或 `### Phase N:` heading，提取同级列表项和段落文字
- Product 名推断：优先 `--product` flag → 次选 PRD 文件名 stem

**Discuss（交互式）**：
- 输入：`List[PhaseInfo]`
- 输出：`List[ConfirmedPhase]` — 补充了用户确认/修改的字段（title, goal, projects, exit_criteria 均可被覆盖）
- 实现：逐 phase `input()` 交互，每 phase 显示：Phase ID, 当前 title, 当前 goal → 用户可回车确认或输入新值
- `--yes` 跳过交互直接使用 Analyze 结果（非 TTY 且无 `--yes` 时报错）

**Produce（全自动）**：
- 输入：`List[ConfirmedPhase]`
- 输出：`phases/{project}-p{N}-{slug}.md`（每个 phase 一个文件），存放于 PRD 同级 `phases/` 目录
- Phase 文档遵循 Key Interfaces#4 定义的 schema（Metadata + Goal + Involved Projects + Exit Criteria）
- 同步 PRD 引用：在 PRD 中对应 Phase heading 后追加 `> Phase doc: [phases/{filename}.md](...)` 引用行

**Decompose（全自动，可选 `--yes` 跳过确认）**：
- 输入：`List[ConfirmedPhase]` + phase 文档路径
- 输出：每个 Involved Project 一个 GitHub Issue（标题格式见下方）
- Issue 标题: `feat({scope}): {phase-id} — {goal-summary}` (≤72 chars, summary 截断加 `...`)
- Body 内容：复用 `build_structured_issue_body()` 统一五段结构，顶部注入：
  ```
  - **Product**: {product}
  - **Phase**: {phase_id}
  ```
- 标签：自动应用 `project/{name}`, `status/planning` 标签

**TDD**: false

**Changes**:
1. 创建 `roadmap.py` —— `_analyze()`, `_discuss()`, `_produce()`, `_decompose()`, `register_roadmap_parser()`
2. flow.sh: PYTHON_COMMANDS 添加 `|roadmap`
3. flow.py: 导入 + build_parser 注册 + main dispatch

**Verify**:
```bash
# 语法存在
rg -c 'roadmap' .wopal/skills/dev-flow/scripts/flow.sh
rg -c 'roadmap' .wopal/skills/dev-flow/scripts/flow.py
# 行为：PhaseInfo 数据结构可导入
python -c "from dev_flow.commands.roadmap import PhaseInfo, parse_prd_phases; print('ok')"
# 行为：PRD 解析 demo
python -c "
from dev_flow.commands.roadmap import parse_prd_phases
phases = parse_prd_phases('docs/projects/wopal-space-ontology/PRD.md')
assert len(phases) > 0, 'No phases found'
print(f'Found {len(phases)} phases')
"
```

- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

### Task 2: plan.py 新增 Product/Phase 元信息继承

**Verification Intent**: AC#6, AC#12

**Behavior**: `plan.py` 新增 `_extract_product_phase_from_body()` 从 Issue body 提取 Product/Phase，填充到 Plan metadata。**本 Task 先于 Task 5 执行**——Task 5 依赖 Task 2 完成后稳定的 Plan 模板格式来设计简化的 `build_plan_link_for_issue()`。

**Files**: `dev-flow/scripts/dev_flow/commands/plan.py`, `dev-flow/templates/plan.md`

**Depends On**: 无（Wave 1 独立，但 Task 5 依赖本 Task 完成）

**Design**:
1. 新增 `_extract_product_phase_from_body(issue_info) -> (product, phase)` —— 正则匹配 `- **Product**:` / `- **Phase**:`
   - 接口对齐 Key Interfaces#1：纯读取 Issue body，返回 `(str|None, str|None)`
2. `cmd_plan()` Issue mode 中调用（line ~500），紧跟 `_extract_project_metadata_from_body` 之后
3. `create_plan_from_template()` 新增 `product: str | None = None`, `phase: str | None = None` 参数
   - 占位符映射：`{product_line}` → `- **Product**: {product}` 或空字符串
   - `{phase_line}` → `- **Phase**: {phase}` 或空字符串
4. `templates/plan.md` metadata section 新增占位符（在 `{project_type_line}` 之后）：

```markdown
{product_line}
{phase_line}
- **Created**: {date}
```

**TDD**: false

**Changes**:
1. plan.py: 新增 `_extract_product_phase_from_body()`
2. plan.py: `cmd_plan()` Issue mode 中调用新函数，传入 `create_plan_from_template()`
3. plan.py: `create_plan_from_template()` 新增 product/phase 参数 + 占位符替换
4. templates/plan.md: metadata section 新增 `{product_line}` / `{phase_line}` 占位符

**Verify**:
```bash
# 函数存在
rg -c '_extract_product_phase_from_body' .wopal/skills/dev-flow/scripts/dev_flow/commands/plan.py
# 模板占位符存在
rg -c '{product_line}' .wopal/skills/dev-flow/templates/plan.md
rg -c '{phase_line}' .wopal/skills/dev-flow/templates/plan.md
# 行为：从 body 提取 Product/Phase（单元测试）
python -m pytest .wopal/skills/dev-flow/tests/python/unit/test_plan_product_phase.py -v
```

- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

### Task 3: 精简 Issue 模板（6→1） + 简化 body builder

**Verification Intent**: AC#8, AC#9

**Behavior**:
- 删除 5 个 type-specific 模板（issue-fix/refactor/perf/test/docs.md）
- 创建统一 `issue-stub.md`：Goal + Context + Scope(In/Out) + AC + Related Resources 五段结构
- `build_structured_issue_body()` 移除所有 type-specific 分支，统一为五段渲染
- `issue.md` 保留兼容（更新为 stub 同结构）

**Files**: `dev-flow/templates/issue-stub.md`(创建), `dev-flow/templates/issue*.md`(删除×5+修改), `dev-flow/scripts/dev_flow/domain/issue/body.py`(修改), `dev-flow/scripts/dev_flow/domain/issue/__init__.py`(不变)

**Design**: 

issue-stub.md:
```markdown
## Goal
一句话

## Context
<!-- 背景、研究发现、决策依据、参考资料 —— agent 自由写入 -->

## Scope
### In
### Out

## Acceptance Criteria
待 plan 阶段细化

## Related Resources
| Plan | _待关联_ |
```

body.py 简化: `build_structured_issue_body(type, goal, context, scope, out_of_scope, reference)` — 不再有 fix/perf/refactor/docs/test 分支。

**TDD**: false

**Changes**:
1. 创建 `templates/issue-stub.md`
2. 删除 issue-fix.md, issue-refactor.md, issue-perf.md, issue-test.md, issue-docs.md
3. 更新 `issue.md` 为简化版
4. 简化 `body.py:build_structured_issue_body()` —— 移除 60+ 行 type-specific 渲染

**Verify**:
```bash
test -f .wopal/skills/dev-flow/templates/issue-stub.md
test ! -f .wopal/skills/dev-flow/templates/issue-fix.md
test ! -f .wopal/skills/dev-flow/templates/issue-refactor.md
test ! -f .wopal/skills/dev-flow/templates/issue-perf.md
test ! -f .wopal/skills/dev-flow/templates/issue-test.md
test ! -f .wopal/skills/dev-flow/templates/issue-docs.md
```

- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

### Task 4: 新增 `issue write` 命令 + 简化 `issue create`

**Verification Intent**: AC#7, AC#13, AC#14

**Behavior**:
- `issue create` 缩减参数为 `--title`, `--project`, `--body-file`, `--type`(可选)
- 新增 `issue write <issue> --body-file <path>` 全量替换 body
- 新增 `issue write <issue> --append <path>` 追加到 body 末尾
- `issue update` 保留兼容但废弃（stderr 输出 deprecated 警告）

**Files**: `dev-flow/scripts/dev_flow/commands/issue.py`(修改)

**Design**:

issue create 简化:
```bash
flow.sh issue create --title "feat(cli): ..." --project <name> [--type feat] [--body-file ctx.md]
```
Type 从 title 自动推断（和现在一样），`--type` 可选覆盖。移除所有 type-specific 参数。

issue write 新命令:
```bash
flow.sh issue write <issue> --body-file path    # 全量替换 body
flow.sh issue write <issue> --append path       # 追加到 body 末尾
```

`--append` 行为契约（对齐 Key Interfaces#3）：
1. 追加前在现有 body 末尾插入 `\n\n`，再拼接新文件内容
2. 若 `--body-file` 指向空文件（0 bytes）或文件不存在 → exit 1 + 报错
3. 允许同一文件多次 append（每次追加均加 `\n\n` 分隔）
4. 不校验文件内容类型，但输出 warning 若文件不以 `#` 或 `-` 开头
5. 拼接后保证 body 以 `\n` 结尾

`issue update` 废弃策略：
- 保留函数实现不变，但在入口输出 `[DEPRECATED] use issue write --body-file or --append instead` 到 stderr
- 其他行为不变（仍可使用 `--body-file`, `--body`, `--reference` 等参数）

**TDD**: false

**Changes**:
1. issue.py: `cmd_issue_create` 移除 18 个 type-specific 参数
2. issue.py: 新增 `cmd_issue_write` —— `--body-file` 替换, `--append` 追加
3. issue.py: `register_issue_parser` 新增 write 子命令，create/update 参数清理

**Verify**:
```bash
# 代码存在
rg -c '--append' .wopal/skills/dev-flow/scripts/dev_flow/commands/issue.py
rg -c 'cmd_issue_write' .wopal/skills/dev-flow/scripts/dev_flow/commands/issue.py
# 行为：空文件 append 报错
python -m pytest .wopal/skills/dev-flow/tests/python/unit/test_issue_write.py -v -k "empty"
# 行为：append 保留原内容
python -m pytest .wopal/skills/dev-flow/tests/python/unit/test_issue_write.py -v -k "preserve"
```

- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

### Task 5: 优化 sync 行为 + 升级 decompose

**Verification Intent**: AC#10, AC#15

**Behavior**:
- `sync --body-only` 不再全量覆盖 Issue body——只更新 `## Related Resources` 中的 Plan 链接行
- `decompose-prd` → 新增 `decompose --from roadmap.md` 支持（从 ROADMAP.md 的 Slices 表生成 Slice Issues）

**Files**: `dev-flow/scripts/dev_flow/commands/sync.py`(修改), `dev-flow/scripts/dev_flow/domain/plan/body.py`(修改), `dev-flow/scripts/dev_flow/commands/decompose.py`(修改)

**Depends On**: Task 2（plan.py Product/Phase 接口）、Task 3（统一 issue body builder）

**Design**:

**sync body 变更**：
`sync_plan_to_issue()` 不再调用 `build_issue_body_from_plan()` 全量替换 —— 改为:
1. 读取当前 Issue body
2. 正则匹配 `## Related Resources` table 中的 `| Plan | ... |` 行
3. 替换为新的 Plan 链接行
4. `gh issue edit --body` 写回。其余内容完整保留
5. 边界处理：若 Issue body 中无 `## Related Resources` table，追加到 body 末尾

**plan/body.py 简化**：
`build_issue_body_from_plan()` → 重命名为 `build_plan_link_for_issue(plan_file, repo, workspace_root)` —— 只返回一行 markdown：`| Plan | [{plan_name}]({github_url}) |`。接口对齐 Key Interfaces#1：只负责 Plan 链接行生成，不重构 body。

**decompose 升级**：
- 新增 `--from <path>` 参数（必填，不兼容现有无参数调用）
  - `--from PRD.md` 模式：保持现有 `extract_phases()` 行为（兼容）
  - `--from ROADMAP.md` 模式：调用 `parse_roadmap_slices()` 解析 Slices 表

**`parse_roadmap_slices(md_path) -> List[Slice]`**（对齐 Key Interfaces#2）：
- 定位 `## Slices` heading 下的 markdown table
- 逐行解析列值（按表头顺序）
- `Project` 列的 `=name` 前缀：去掉 `=` 取 name 字符串
- `Depends` 列：`none` 或空 → `[]`；`S01, S02` → `["S01", "S02"]`
- 辅助函数 `_extract_demo_text(md_path, slice_id)`：搜索 `### {slice_id}:` heading，用正则提取 `After this:` 后的文本
- 返回 `List[Slice]`（见 Key Interfaces#2 dataclass 定义）

**`create_slice_issue(slice, repo, roadmap_path) -> str`**：
- 标题：`feat({project}): {slice.id} — {slice.title}`（≤72 chars）
- Body 结构：
  ```markdown
  - **Product**: <从 ROADMAP.md 或 --product flag 推断>
  - **Slice**: {slice.id}

  ## Goal
  {slice.title}

  ## Depends on
  - {dep_slice_id}: {dep_title}（或 _无_）

  ## Demo
  {slice.demo 或 _待定义_}

  ## Related Resources
  | Roadmap | [{roadmap}]({roadmap_url}) |
  ```
- 标签：自动应用 `project/{slice.project}`, `type/feat`

**TDD**: false

**Changes**:
1. sync.py: `sync_plan_to_issue()` 改为只更新 Related Resources 中的 Plan 链接
2. plan/body.py: 简化/重命名为 `build_plan_link_for_issue()` —— 只返回 Plan 链接行
 3. decompose.py: 新增 `--from` 参数 + `parse_roadmap_slices()` + `_extract_demo_text()` + `Slice` dataclass + `create_slice_issue()`

**Verify**:
```bash
# 代码存在
rg -c 'decompose --from' .wopal/skills/dev-flow/scripts/dev_flow/commands/decompose.py
# 行为：ROADMAP.md Slices 解析
python -c "
from dev_flow.commands.decompose import parse_roadmap_slices
slices = parse_roadmap_slices('/tmp/test_roadmap.md')
assert len(slices) > 0, 'Should find at least 1 slice'
s = slices[0]
assert s.id == 'S01', f'Expected S01, got {s.id}'
assert '多空间' in s.title, f'Title missing expected text: {s.title}'
assert s.project == 'space-flow', f'Expected space-flow, got {s.project}'
print(f'Parsed {len(slices)} slices correctly')
"
# 行为：sync 保留上下文
python -m pytest .wopal/skills/dev-flow/tests/python/ -v -k "test_sync_preserves_context"
```

- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

### Task 6: 单元测试 + 测试适配

**Verification Intent**: AC#1

**Behavior**: 为所有新功能编写测试，适配受影响测试。

**Files**:
- `dev-flow/tests/python/unit/test_roadmap_analyze.py`(创建)
- `dev-flow/tests/python/unit/test_roadmap_decompose.py`(创建)
- `dev-flow/tests/python/unit/test_roadmap_produce.py`(创建)
- `dev-flow/tests/python/unit/test_plan_product_phase.py`(创建)
- `dev-flow/tests/python/unit/test_issue_write.py`(创建)
- `dev-flow/tests/python/unit/test_roadmap_slices_parse.py`(创建)
- `dev-flow/tests/python/unit/test_append_boundary.py`(创建)
- `dev-flow/tests/python/unit/test_sync_preserves_context.py`(创建)
- `dev-flow/tests/python/unit/test_update_deprecated.py`(创建)
- `dev-flow/tests/python/unit/test_issue_body_file.py`(修改)
- `dev-flow/tests/python/integration/test_issue_create_command.py`(修改)
- `dev-flow/tests/python/integration/test_issue_update_command.py`(修改)

**Design**:

新增测试:
- test_roadmap_analyze.py (4): PRD 解析, phase 提取, product 推断, 空文件处理
- test_roadmap_decompose.py (5): Issue 标题格式, 截断, body 注入, --yes 跳过, 非 TTY 报错
- test_roadmap_produce.py (3): phase 文档创建, 目录创建, PRD 引用更新
- test_plan_product_phase.py (4): 提取 Product/Phase, 缺失场景, Plan 模板填充, product 为 None 时模板正确输出空行
- test_issue_write.py (6): --body-file 替换, --append 追加, 追加保留原内容, 空文件 append 报错(AC#13), 连续 append 分隔符验证(AC#14), 替换后内容独立验证
- test_roadmap_slices_parse.py (5): 基本表解析, depends 解析, =project 前缀处理, 空 demo, After this 提取
- test_append_boundary.py (2): 空文件报错, 连续追加分隔符
- test_sync_preserves_context.py (2): sync 后 Context 区域未被覆盖, sync 后 Plan 链接已更新
- test_update_deprecated.py (1): issue update 输出 deprecated 警告

适配测试:
- test_issue_body_file.py: 移除 15 个设为 None 的 type-specific 参数
- test_issue_create_command.py: 移除 type-specific 参数检查
- test_issue_update_command.py: 适配 update→write 迁移或标记废弃

**TDD**: false

**Changes**:
1. 创建 9 个新测试文件（32 个测试用例）
2. 修改 3 个现有测试文件适配参数简化

**Verify**:
```bash
# 全部新测试通过
python -m pytest .wopal/skills/dev-flow/tests/python/ -v -k "roadmap or product_phase or issue_write or test_append_boundary or test_sync_preserves_context or test_roadmap_slices_parse or test_update_deprecated"
# 旧测试不受影响
python -m pytest .wopal/skills/dev-flow/tests/python/ -v -k "not (roadmap or product_phase or issue_write or test_append_boundary or test_sync_preserves_context or test_roadmap_slices_parse or test_update_deprecated)"
```

- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

### Task 7: 更新技能文档

**Verification Intent**: AC#4, AC#5, AC#10

**Behavior**: 在 SKILL.md、commands.md、issue-format.md 中更新所有受影响的文档。

**Files**: `dev-flow/SKILL.md`(修改), `dev-flow/references/commands.md`(修改), `dev-flow/references/issue-format.md`(修改)

**Design**:
- SKILL.md: 插入 Roadmap 章节 + 更新 Issue 创建说明（`--body-file` 为主路径）+ Issue Write 使用说明
- commands.md: 命令表添加 roadmap 和 issue write, 移除 issue update, 更新 decompose
- issue-format.md: 更新 Issue body 结构说明为五段式

**Changes**:
1. SKILL.md: A0 Roadmap 章节 + C0 Issue 编写章节
2. commands.md: 新增 roadmap, issue write, decompose 说明
3. issue-format.md: 更新 body 结构

**Verify**:
```bash
rg -c 'Roadmap' .wopal/skills/dev-flow/SKILL.md
rg -c 'issue write' .wopal/skills/dev-flow/references/commands.md
```

- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

## Delegation Strategy

| Wave | Task | 执行者 | 依赖 | 委派理由 |
|------|------|--------|------|---------|
| 1 | Task 1 | fae | 无 | roadmap.py + 路由，独立新文件 |
| 1 | Task 3 | fae | 无 | 模板删除 + body.py 简化，独立 |
| 2 | Task 2 | fae | Task 1 | plan.py Product/Phase 继承；Task 5 依赖本 Task 完成后稳定的 Plan 模板格式 |
| 3 | Task 4 | fae | Task 3 | issue write 依赖简化后 body builder |
| 4 | Task 5 | fae | Task 2, Task 3, Task 4 | sync/decompose 依赖 Plan 模板 + body builder + issue write；串行于 Task 4 |
| 5 | Task 6 | fae | Task 1-5 | 测试依赖实现完成 |
| 5 | Task 7 | fae | Task 1-5 | 文档依赖命令实现稳定 |

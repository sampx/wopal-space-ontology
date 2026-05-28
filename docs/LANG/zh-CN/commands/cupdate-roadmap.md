---
description: 创建或更新产品阶段路线图文档
---

# 创建或更新 Roadmap

从产品 DESIGN 或项目 DESIGN 的 Evolution Roadmap 章节讨论并生成符合规范的阶段文档。逐 phase 交互确认后写入，写入后由 dev-flow `roadmap` 命令校验，校验通过后引导使用 `decompose` 拆分 Issue。

**用户输入参数**：`$1` `$2`

**参数说明**: `<名称> [类型: product|project]`。用户未输入时，去 `docs/products/` 和 `docs/projects/` 查目录和上下文匹配推断，有疑问向用户确认. 


**两种模式**：

| | 产品 DESIGN 模式 | 项目 DESIGN 模式 |
|---|---|---|
| Phase 语义 | 产品级里程碑，涉及多个项目协同 | 项目成熟度阶段，聚焦单个项目的分工目标 |
| Involved Projects | 列出本阶段参与的所有项目 | 通常只含本项目，可能存在工具或基础依赖 |
| Goal 描述 | 本阶段要交付的产品能力 | 本项目在本阶段要达成的分工目标 |
| 拆分方式 | 跨项目拆 Issue，每个 Involved Project 一个 Issue | 本项目内拆 Issue |

根据输入的 DESIGN 类型自动选择对应模式。

---

## 核心原则

### 输出语言

生成的 phase 文档使用用户偏好语言，除非用户明确要求其他语言。

### 文档路径

- Phase 文档存放于 DESIGN 同级 `phases/` 目录
- 文件命名：`{product}-{phase-id}-{slug}.md`
  - `product`：从 DESIGN 或上下文推断的产品名，小写
  - `phase-id`：`p0`, `p1`, `p2` ...（小写）
  - `slug`：从 phase 标题生成，**必须去除尾部状态标记**（`— .*`、`- .*` 等模式），只保留实际标题内容

示例：
```
# 产品 DESIGN：
docs/products/wopal-space/phases/wopal-space-p0-core-foundation.md
# 项目 DESIGN：
docs/projects/wopal-cli/phases/wopal-cli-p1-one-click-distribution.md
```

存量文档保留现有路径不变。

### 前置条件

**需要读取的上下文**：
- 目标 DESIGN 文件（产品 DESIGN 或项目 DESIGN）
- 上级产品 PRD / DESIGN（如为项目 DESIGN）
- 已存在的 phase 文档（如更新）
- 当前对话上下文：用户需求、决策、已确认问题
- `.wopal-space/STRUCTURE.md`

### 核心规则

- Phase 文档回答：本阶段要交付什么产品能力、涉及哪些项目、完成标准是什么。
- Position: Phase 文档不重复 DESIGN 的完整产品愿景或用户分析。
- Phase 文档不包含实现步骤、技术方案细节、代码清单——这些属于 Plan。
- 已有准确内容应保留精炼，不过度改写。
- 过时信息在证据充分时更新或移除。
- 未决问题标注为待确认，不默认定稿。

### 写作质量要求

每个 phase 文档必须可作为 decompose 的可靠输入，这意味着：
- Goal 必须是可验证的产品能力陈述，不能是"继续 Phase N 的工作"
- Involved Projects 必须明确每个项目在本阶段的职责（core delivery / tooling / enablement）
- Exit Criteria 必须是可证伪的检查项（`- [ ]` checkbox 格式），能通过代码审查或测试验证
- Scope / Out of Scope 边界清晰，不给分解阶段留下歧义

**严禁**：
- 以 `_(none)_`、`_(to be defined)_` 等占位符作为最终内容
- Phase 之间完全复用相同的 Goal 描述（每个 phase 有独立产品目标）
- 在 Scope 中填写实现状态（"已完成"、"进行中"），这些信息属于 DESIGN 的 Evolution Roadmap

---

## 模板

根据 DESIGN 类型选择对应模板：

- **产品 DESIGN 模式** → `.wopal/templates/phase-product.md`（跨项目视角，多个 Involved Projects）
- **项目 DESIGN 模式** → `.wopal/templates/phase-project.md`（单项目视角，一个核心项目 + 依赖）

---

## 步骤 1：解析 DESIGN，识别 Phase 列表

读 DESIGN，定位 `# Evolution Roadmap` / `# 演进路线` 章节（产品 DESIGN 为 §9，项目 DESIGN 为 §8）。

**项目 DESIGN 模式额外步骤**：同时读取上级产品 DESIGN 的 Evolution Roadmap（§9）和已有产品 phase 文档，理解本项目在每个产品大阶段中的定位和分工，确保项目阶段的 Goal 与产品阶段对本项目的期望对齐。

从 `## Phase N:` 或 `### Phase N:` heading 提取 phase 列表。

对每个 phase，提取 DESIGN 中已写的：
- Phase ID（编号）
- 标题（去除 `— 已完成`、`- 当前阶段` 等状态标记）
- Goal 描述段落
- 能力方向列表
- 已有引用（如 `> Phase doc: [phases/...]`）

**产出**：Phase 列表（ID、标题、DESIGN 原文摘要、已有文档路径）

---

## 步骤 2：逐 Phase 交互讨论

对每个 phase，展示 DESIGN 中已有信息，引导用户补充缺失字段。

**讨论结构**（每 phase）：

```
### Phase {id}: {标题}
DESIGN 摘要: {从 DESIGN 提取的 Goal 和能力描述}
已有文档: {路径或 未创建}

产品 DESIGN 模式需确认/补充：
1. 目标 — 本阶段要交付的产品能力是什么？（跨项目视角）
2. 范围 / 不包含 — 产品级边界
3. 涉及项目 — 哪些项目参与本阶段？各自承担什么角色？
4. 完成条件 — 如何验证产品能力已交付？（至少 2 条可证伪条件）
5. 风险 — 跨项目依赖和协调风险

项目 DESIGN 模式需确认/补充（展示对应产品阶段上下文）：
1. 产品阶段 — 本项目的这个阶段对应产品大阶段的哪个 Phase？该产品阶段对本项目的期望是什么？
2. 目标 — 本项目在本阶段要达成的分工目标是什么？（单项目视角，对齐产品期望）
3. 范围 / 不包含 — 本项目的阶段边界
4. 涉及项目 — 本项目依赖的其他项目（工具/基础能力），通常只含本项目
5. 完成条件 — 如何验证本项目的阶段目标已达成？（至少 2 条可证伪条件）
6. 风险 — 项目内技术风险和外部依赖
```

**交互规则**：
- 若 DESIGN 中已有明确信息，展示原文并问"是否沿用？"
- 缺失字段必须逐一确认，不允许留空占位符
- 用户可能一次性提供所有字段，也可能逐字段回复——根据上下文灵活处理
- 若用户跳过某 phase 或在讨论中要求"稍后处理"，标记该 phase 为跳过，不阻止其他 phase 继续

**产出**：每个 phase 的完整信息（目标、范围、不包含、涉及项目、完成条件、风险）

---

## 步骤 3：生成 Phase 文档，展示变更方案

为每个已讨论完成的 phase 生成文档内容（按上方模板章节中对应 DESIGN 类型的模板）。

**生成规则**：
- Status：已完成→`Completed`，当前阶段→`Active`，其余→`Planned`
- slug 生成：标题 → 小写 → 去除非字母数字 → 空格替换为 `-` → 去首尾连字符 → 截断 ≤40 字符
- **slug 必须去除尾部状态标记**：在 slugify 前用正则 `[-—].*$` 去除标题尾部的状态标记
- 涉及项目表格：每行包含项目 / 角色 / 备注
- 完成条件：`- [ ]` 格式，每条独立可验证

**展示内容**（写文件前必须展示）：
1. 将创建/更新的文件列表及路径
2. 每个 phase 文档的完整内容或关键字段摘要
3. 若更新已有文档，展示标题/目标/范围/项目/条件的前后变更

等待用户确认后再写入任何文件。

---

## 步骤 4：写入并回写 DESIGN 引用

用户确认后：

1. 创建 `phases/` 目录（如不存在）
2. 按文件命名规则写入 phase 文档
3. 在 DESIGN 中对应 `### Phase N:` heading 下方插入引用行：
   ```
   > Phase doc: [phases/{文件名}.md](phases/{文件名}.md)
   ```
   若引用已存在则跳过。

---

## 步骤 5：dev-flow 校验

Phase 文档写入后，运行 dev-flow 的 `roadmap` 命令进行格式和内容校验：

```bash
flow.sh roadmap <design-path> --check
```

**校验内容**（由 roadmap 命令实现）：
- Phase 文档存在性（DESIGN 中的每个 phase 是否有对应文档）
- Metadata 完整性（Phase ID、Product、Status）
- 必填字段：Goal 不为空且非占位符、Involved Projects 有至少一个项目、Exit Criteria 有至少一条可验证条件
- 文件名 slug 不含状态标记
- DESIGN 引用完整性（每个 phase heading 后必须有 phase doc 引用）

**校验不通过** → 输出具体问题，引导 agent 回到步骤 2 补充缺失字段。

**校验通过** → 进入步骤 6。

---

## 步骤 6：引导 Issue 拆分

校验通过后，引导用户使用 dev-flow 的 `decompose` 命令创建 Issue。

**产品 DESIGN 模式**（跨项目拆分）：
```bash
# 每个 Involved Project 生成一个 Issue
flow.sh decompose --from phases/<phase-doc>.md --product <name> [--dry-run]
```

**项目 DESIGN 模式**（本项目内拆分）：
```bash
# 为单个项目生成 Issue
flow.sh decompose --from phases/<phase-doc>.md --project <name> [--dry-run]
```

**引导话术**：
> Phase 文档已就绪。产品模式可通过 `flow.sh decompose --from phases/<file>.md` 为各项目创建 Issue；项目模式可直接为当前项目创建 Issue。建议先用 `--dry-run` 预览。

不要自动执行 decompose——Issue 创建是独立的用户决策。

---

## 更新模式

更新已有 phase 文档时：

1. 保留现有文档路径
2. 更新 `Updated` 日期
3. 对照 DESIGN、对话上下文和实现事实进行校验
4. 添加缺失字段
5. 移除或修正过时信息
6. 更新 Status（如适用）

---

## 确认策略

在写入任何文件之前，必须展示完整方案并获取用户明确确认。

方案应包含：
1. 将创建/更新的文件清单及路径
2. 每个 phase 的关键字段摘要（目标、涉及项目、完成条件）
3. DESIGN 中将写入的引用行
4. 任何跳过未创建的 phase 及原因

用户确认前，不得写入、覆盖或重新组织任何文件。

---

## 质量检查清单

- [ ] DESIGN 路径正确，Phase 列表已完整提取
- [ ] 每个 phase 讨论充分，目标 / 范围 / 项目 / 完成条件均非占位符
- [ ] 目标是可验证的产品能力陈述
- [ ] 涉及项目表每行有明确角色（核心交付 / 工具支持 / 基础能力）
- [ ] 完成条件每条可独立验证（checkbox 格式）
- [ ] slug 已去除状态标记
- [ ] 文档状态与 DESIGN 演进路线一致（Completed / Active / Planned）
- [ ] DESIGN 引用行已回写
- [ ] `flow.sh roadmap --check` 通过
- [ ] 方案已在写入前展示并获得确认
- [ ] 已引导用户使用 `decompose --from` 创建 Issue（未自动执行）

---

## 完成后回复

完成后用用户偏好语言回复：

1. 已创建/更新的 phase 文档清单
2. 每个 phase 的关键决策摘要（目标、涉及项目、完成条件要点）
3. 任何跳过的 phase 及原因
4. `roadmap --check` 校验结果
5. 下一步引导：`flow.sh decompose --from phases/<文件>.md`（产品模式用 `--product`，项目模式用 `--project`）

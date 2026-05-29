---
description: 引导产品阶段讨论，生成阶段定义与跟踪文档
---

# 创建或更新 Roadmap

以产品 DESIGN §5 Evolution Roadmap 为起点，引导用户逐 phase 讨论阶段目标、范围、涉及项目、验收条件与风险，产出 Phase 文档并回写产品 DESIGN 和项目 DESIGN。

**Input**: `$1` `$2`

**Parameter Notes**: `<名称> [phase-id]`。未输入时从 `docs/products/` 匹配推断产品名，有疑问向用户确认。`phase-id` 可选，不提供时默认讨论当前 Active phase。

---

## Core Principles

- 核心职责是帮助用户明确阶段目标、范围、涉及项目和验收条件。
- 讨论以产品 DESIGN §5 的 Evolution Roadmap 为骨架，产品 PRD 为愿景基准。
- 讨论产物是 Phase 文档（阶段定义和验收标准），同步回写到产品 DESIGN 和对应项目 DESIGN。
- Phase 文档为下一步拆分 Plan 提供可靠输入。
- Phase 文档使用 `.wopal/templates/phase.md` 模板。
- 所有写入操作前展示方案并获取用户明确确认。

## Step 1: 识别当前 Phase

读产品 DESIGN §5 和产品 PRD，列出所有 Phase 及其当前状态（Active / Completed / Planned）。

引导用户选择要讨论的 phase。默认选择当前 Active phase；用户可指定已完成 phase 做回顾调整，或提前讨论 Planned phase。

**Output**: 选定的 phase ID、标题、产品 DESIGN 中已有 Goal 描述

## Step 2: 讨论阶段目标

结合产品 PRD 的产品愿景和产品 DESIGN 的架构契约，与用户讨论本阶段的产品能力目标。

- 展示产品 DESIGN 中已有的 Goal 描述，询问是否沿用或调整。
- 目标必须是可验证的产品能力陈述，≥20 字符。
- 允许在讨论中修正目标，直到达成共识。

**Output**: 确认的阶段 Goal

## Step 3: 讨论阶段范围

明确本阶段的产品能力边界：

- **Scope**：本阶段要交付的产品能力范围，概括涉及的子系统或项目。
- **Out of Scope**：明确排除在本阶段之外的能力或项目。

**Output**: Scope 和 Out of Scope 清单

## Step 4: 明确涉及项目

确定哪些项目参与本阶段，各自承担什么角色。

对每个项目，讨论：
- 项目角色（core delivery / tooling / enablement）
- 项目在本阶段的设计目标——需要完成哪些架构决策、接口定义或能力建设

**Output**: Involved Projects 表（项目、角色、阶段设计目标）

## Step 5: 确定验收条件

为每个涉及项目逐条确定 Exit Criteria。

- 按项目分组（`### 项目名`），每组 1~6 条。
- 每条 `- [ ]` checkbox 格式，独立可验证。
- 验收条件描述交付事实。

**Output**: 按项目分组的 Exit Criteria

## Step 6: 讨论风险与依赖

识别跨项目依赖和协调风险，讨论缓解措施。

**Output**: 风险/依赖表（风险、影响、缓解措施）

## Step 7: 生成 Phase 文档

按 `.wopal/templates/phase.md` 模板，汇总以上讨论结果生成 Phase 文档。

生成规则：
- Status：已完成→`Completed`，当前阶段→`Active`，其余→`Planned`
- 文件命名：`{product}-{phase-id}-{slug}.md`，存放于产品 DESIGN 同级 `phases/`
- slug：标题→小写→去除非字母数字→空格替换 `-`→正则 `[-—].*$` 去尾部状态标记→去首尾连字符→截断 ≤40 字符

展示完整文档内容和文件路径，等待用户确认。

**Output**: Phase 文档内容，等待确认

## Step 8: 写入并回写 DESIGN

用户确认后：

1. 创建 `phases/` 目录（如不存在）
2. 写入 Phase 文档
3. 在产品 DESIGN §5 对应 phase heading 下方插入 Phase doc 引用链接
4. 在对应项目 DESIGN 中写入本阶段项目交付目标引用

**Output**: 已写入的文件路径，DESIGN 引用变更

## Step 9: 引导拆分 Plan

Phase 文档就绪后，引导用户为每个项目的 Involved Project 创建 Plan，将阶段验收条件分解为可执行的开发任务。

---

## Completion Standard

以下条件全部满足时，本命令引导讨论结束：

1. 阶段目标已明确，达成目标所需的设计决策已共识
2. 涉及项目及各自阶段设计目标已清晰
3. 验收条件（Exit Criteria）已按项目确定，每条独立可验证
4. 已识别的核心风险已有缓解方案
5. 本阶段具备拆分为各项目 Issue 和 Plan 的条件

本阶段产出和更新的文档（Phase 文档、产品 DESIGN、项目 DESIGN）在一次提交中固化成果。

---

## Response After Completion

使用用户偏好语言回复：

1. 已创建/更新的 Phase 文档
2. 阶段关键决策摘要（Goal、涉及项目、Exit Criteria）
3. 产品 DESIGN 和项目 DESIGN 的引用变更
4. 提示将变更一次性提交固化
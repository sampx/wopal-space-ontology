---
description: 创建或更新产品 DESIGN 文档
---

# 创建或更新 DESIGN

创建或更新产品或项目 DESIGN 文档。产品 DESIGN 是总体设计，从产品 PRD 派生，描述跨项目的系统组成、架构层和项目间契约。项目 DESIGN 是分系统设计，从上级产品 PRD 和总体 DESIGN 派生，描述单个项目的内部架构、技术栈和能力范围。

**用户输入参数**：`$1` `$2`

**参数说明**: `<名称> [product|project] `。用户未输入时，去 `docs/products/` 和 `projects/*/docs/` 查目录和上下文匹配推断，有疑问向用户确认.

---

## 核心原则

### 输出语言

默认使用用户偏好的语言编写生成或更新后的文档；除非用户明确要求其他语言。

### 文档路径

**产品 DESIGN**：更新时保留既有路径。新建时默认：`docs/products/<product-name>/DESIGN-<product-name>.md`。可接受既有变体：`DESIGN.md`、`DESIGN-*.md`。

**项目 DESIGN**：更新时保留既有路径。新建时默认：`projects/<project-name>/docs/DESIGN.md`。

### 前置条件

**产品 DESIGN** 应基于产品 PRD 编写。**项目 DESIGN** 应基于上级产品 PRD 和总体 DESIGN 编写——项目 DESIGN 是总体设计的子系统落地，其能力范围和阶段路线需承接上级产品对该模块的定义。

**必需上下文**：

- 目标 PRD（产品 DESIGN 时必需）
- 上级产品 PRD + 上级产品 DESIGN（项目 DESIGN 时必需）
- 既有目标 DESIGN（更新时）
- 当前对话中的用户决策、研究结论、确认需求
- 从实际实现更新时，应读取代码或项目文档事实

产品 DESIGN 没有对应 PRD 时，询问是否先创建 PRD。项目 DESIGN 没有独立 PRD——其产品定义从上级产品 PRD 中提取模块相关部分，承载于 DESIGN 的 §2 Capability Scope 和 §8 Evolution Roadmap。

**WopalSpace 场景优先参考**：

- `.wopal-space/STRUCTURE.md`
- `.wopal-space/REGULATIONS.md`

### 核心规则

- DESIGN 回答：系统如何组织、模块如何交互、关键技术选择为什么成立。
- DESIGN 可描述已确认但未完全落地的目标态设计。
- DESIGN 不重复 PRD 的愿景、目标用户和产品路线，只做必要引用。
- DESIGN 不写成实施清单、编码规范或命令执行记录。
- 产品 DESIGN 负责：系统组成、架构层、项目契约、运行模型、流程、治理、关键决策和演进路线。产品 DESIGN 是总体设计，面向跨项目架构和 ownership。
- 产品 DESIGN 的 §9 Evolution Roadmap 必须使用结构化 `### Phase N: Title` heading 格式，以便 `/cupdate-roadmap` 解析。每个 phase 应包含 Target / Landed / Remaining 三项信息。
- 项目 DESIGN 负责：内部模块架构、技术栈选型、接口、数据 / 状态模型、能力范围（Capability Scope）、演进路线（Evolution Roadmap），以及对齐产品阶段的实施状态。项目 DESIGN 是分系统设计，面向单个项目内部结构。
- 项目 DESIGN 的 §2 Capability Scope 承接上级产品 PRD 中对该模块的产品定义，描述目标态能力边界，不包含阶段时间、实现状态或交付进度。
- 项目 DESIGN 的 §8 Evolution Roadmap 必须使用结构化 `### Phase N: Title` heading 格式，以便 `/cupdate-roadmap` 解析。每个 phase 应包含 Target / Landed / Remaining 三项信息。已完成阶段应标注状态，供后续 `/cupdate-roadmap` 创建对应 phase 文档。
- 准确既有内容应保留并收紧，不为“新鲜感”重写。
- 有明确证据时，应修订或删除过时内容。
- 未确认事项应明确标注为“待确认”，不能默默决定。

### 写作质量线

DESIGN 必须使用“设计语言”，不是“过程语言”。

**必须满足**：

- 每段都应给出结构、边界、契约、状态 owner、技术选择或运行行为。
- 使用设计态措辞：描述目标架构和 ownership，不写临时实现位置或任务进度。
- 从代码更新时，把代码事实转译为设计责任和契约。
- 每个集成或技术选择都要说明本系统拥有什么、不拥有什么。
- 实施状态要回答 PRD 路线阶段落地情况，不是简单罗列模块。

**禁止**：

- “本节应该……”这类模板说明。
- 不增加系统理解的架构套话。
- 比句子或表格更难读的装饰图。
- 以“当前位置”这类实现态字段作为主结构。
- 默认把 backlog、task plan、命令记录等临时实施产物放入相关文档。

---

## 共享文档头

每个 DESIGN 标题后应有简洁元信息：

```markdown
> **状态**: Active  
> **更新时间**: YYYY-MM-DD  
> **产品意图**: `<prd-path>`
```

项目 DESIGN 还应包含：

```markdown
> **上级架构**: `<parent-design-path>`
> **上级产品**: `<parent-product-prd-path>`
```

## Section 0: Change Log

所有 DESIGN 都应在元信息后、第一节前放置 Change Log：

```markdown
## 0. Change Log

| Date | Type | Summary |
|---|---|---|
| YYYY-MM-DD | Created / Updated | One-line summary |
```

规则：

- 只记录有意义的设计意图、架构、边界、契约或状态变化。
- 不记录错别字、格式调整等纯润色。
- 更新时追加一行。
- Summary 保持一行。
- Change Log 不放在文末。

---

## 模板

- 产品 DESIGN：`.wopal/templates/design-product.md`
- 项目 DESIGN：`.wopal/templates/design-project.md`

---

## 更新模式

更新既有 DESIGN 时：

1. 除非明显错误，否则保留既有路径和标题。
2. 更新 `Updated` 日期。
3. 对齐用户确认需求、对话决策、实现事实、相关 PRD / DESIGN、已知路线和实现证据。项目 DESIGN 需检查关联 phase 文档（`phases/*.md` §6）中的 Plan 完成情况，据此更新 §8 Evolution Roadmap 的 Landed / Remaining。
4. 结构不完整时补齐必要章节。
5. 证据明确时，移除或修订过时架构、边界、接口或状态声明。
6. 在 Section 0 追加一条 Change Log。
7. 未解决事项明确写“待确认”或等价表述。

不要把代码级实现细节粘贴到 DESIGN。应把代码事实转译为架构、契约、状态 ownership、边界或实施状态。

## 质量检查

- [ ] 选择了正确模板：产品或项目
- [ ] 文档语言符合用户偏好
- [ ] Header 包含当前 Updated 日期
- [ ] 产品 DESIGN 基于 PRD
- [ ] 产品 DESIGN 的 §9 Evolution Roadmap 使用 `### Phase N:` heading 格式
- [ ] 项目 DESIGN 基于上级产品 PRD / DESIGN，且 §2 Capability Scope 承接了产品对模块的能力定义
- [ ] 项目 DESIGN 的 §8 Evolution Roadmap 使用 `### Phase N:` heading 格式
- [ ] DESIGN 使用简洁技术设计语言，不写模板 / 过程说明
- [ ] 产品 DESIGN 解释跨项目架构和 ownership
- [ ] 项目角色简洁、技术化、边界清楚
- [ ] 项目模块架构使用设计态语言，不用实现位置语言
- [ ] 项目 DESIGN 解释模块、技术栈、契约、状态、能力范围、演进路线，以及对齐产品阶段的实施状态
- [ ] 技术栈选型包含理由和 ownership 边界
- [ ] 实施状态对齐 PRD 阶段或路线，不是平铺模块表
- [ ] 相关文档默认排除 backlog plan 和临时实施产物
- [ ] 产品 DESIGN 避免重复 PRD 级愿景 / 用户 / 路线；项目 DESIGN 避免重复上级产品 PRD 的完整愿景
- [ ] DESIGN 避免任务级实施指令
- [ ] 准确既有内容已保留
- [ ] 过时内容已修订或删除
- [ ] Change Log 已更新
- [ ] 已链接相关长期文档

## 完成后响应

用用户语言回复：

1. 文件路径
2. 创建 / 更新摘要
3. 有意义的新增、修订、移除 / 废弃、待确认项
4. 建议下一步：DESIGN 写完后，通常接着拆阶段（`/cupdate-roadmap`），把路线图变成可执行的 phase 文档。
   若项目已完成初始化，可运行 `/cupdate-agent-rules` 为本项目生成或更新开发规范。

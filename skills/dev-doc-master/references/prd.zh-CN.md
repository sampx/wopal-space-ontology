# PRD 参考 — 产品 PRD 编写

创建或更新产品 PRD 文档。模板：`templates/prd.md`。

## 文档路径与命名

- 主 PRD 无后缀：`docs/products/<product-name>/PRD.md`。
- 子 PRD（按主题拆分时）用 `PRD-<topic>.md`，与主 PRD 构成父子关系。存在子 PRD 时，主 PRD 头部在 `Sub-PRDs` 字段列出它们；它们是结构声明，绝不进入末尾章节。
- 更新时保留既有文件路径。

## 上下文收集

阅读足够的上下文以避免编造需求。**必需**：既有目标 PRD、关联 DESIGN 文档、当前对话上下文（用户需求、决策、研究结论、未决问题）。从实现更新时，检查代码或项目文档只为提取产品事实、当前能力与实际边界——绝不把实现细节变成 PRD 内容。

WopalSpace 专属上下文：优先使用规范启动与结构文件 `.wopal-space/STRUCTURE.md` 与 `.wopal-space/REGULATIONS.md`。

## 写作规则

- PRD 回答：做什么、为谁、为什么重要、服务于哪些产品结果。
- PRD 不得解释内部架构、API、存储 schema、实施步骤或编码约定。
- 产品 PRD 拥有愿景、用户、产品形态、能力边界、治理与演进。
- Capability Scope / Core Capability Boundaries 只描述目标态边界：拥有的能力、排除的能力、委派边界。无阶段时机、当前/未来分组、实施状态、交付进度、模块状态、checkbox 或 "done / partial / pending" 标签。实施状态属于 Phase、Plan、UAT 或 Verification 文档。
- PRD 中不设独立的成功标准或验证信号章节。需要验证信号时，放在 Plan、UAT、验证文档或 roadmap 阶段验收说明中。
- PRD 正文使用产品语言，而非文档编写语言。不解释章节是做什么的、模板该如何使用。
- 每个段落与表格行传达一个产品事实：用户问题、产品角色、用户收益、拥有的能力、排除的边界、产品入口或 roadmap 结果。
- 保留必要结构但重写薄弱措辞；保留准确既有内容（收紧，而非为新颖而重写）；证据明确时修订或移除过期内容；未决的不确定性标记为需确认。

## 头部

头部只承载强制文档：该 PRD 遵循的 DESIGN（或兄弟 DESIGN），以及存在时的子 PRD。仅参考文档属于末尾章节，绝不属于头部。

```markdown
> **Status**: Active  
> **Updated**: YYYY-MM-DD  
> **Related DESIGN** (mandatory): `<path>` — the DESIGN contract this PRD follows  
> **Sub-PRDs** (mandatory when they exist): list every `PRD-<topic>.md`
```

文档语言非英文时使用本地化字段标签。

## 写作质量线

优选："Users can ..."、"Wopal can ..."、"The CLI provides ..."、"This capability reduces ..."、"CLI owns ... / does not own ..."、"Phase N delivers ..."。

拒绝并重写：章节注释（"This section describes ..."）、模板注释（"According to the template ..."）、含糊的演进语言（"has grown into ..."）、无产品价值的抽象对比（"not an API platform"）、无用户收益的纯架构标签（"exposes product interfaces"）。

## 更新模式

1. 除非明确错误，保留既有文档路径与标题。
2. 更新 `Updated` 日期。
3. 对照用户确认的需求、已实现代码事实与关联 PRD/DESIGN 文档对账。
4. 补齐缺失的必要章节；移除或修订过期陈述；未决项保持显式。
5. 移除独立的成功标准或验证信号章节。

**文档集一致性**：对照更新后的 PRD 审查 DESIGN（产品 + 项目）与阶段文档；能力边界或愿景变化时对齐。子 PRD 与主 PRD 保持一致；`Sub-PRDs` 头部清单与实际文件匹配。

## 质量清单

- [ ] 选择了正确的模板：产品
- [ ] 文档语言跟随用户偏好
- [ ] PRD 保持产品级，无架构/实现细节
- [ ] Capability Scope 只含目标态边界
- [ ] PRD 中无实施状态（属于 Phase/Plan/UAT/Verification）
- [ ] 无独立的成功标准 / 验证信号章节
- [ ] 必要结构保留，薄弱措辞已改进
- [ ] 无模板注释或文档编写语言
- [ ] 每个段落/表格行传达产品事实或边界
- [ ] 准确的既有内容保留；过期内容修订/移除
- [ ] 头部 = 仅强制链接；Reference Documents = 仅参考；无重复
- [ ] 整套文档集已审查并对齐

## 完成后回复

用用户语言回复：文件路径；创建/更新摘要；有意义的 新增/修订/移除/需确认 项；受影响的文档集（已检查 / 已对齐 / 需跟进）；建议的下一步（PRD 完成 → `/cupdate-design`）。
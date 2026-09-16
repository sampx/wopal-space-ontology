---
name: dev-doc-master
description: |
  编写与维护产品/项目的开发文档集——PRD、DESIGN（主文档与子文档）、阶段/Roadmap、README、BUSINESS_RULES、GAPS——并保持文档集与仓库实际一致。

  使用场景：用户要求创建、更新、拆分或对齐其中任何文档，或需要检查文档集一致性（头部链接 vs 末尾引用、子文档双向索引、跨文档对齐），例如"写方案文档"、"更新设计文档"、"拆分设计文档"、"创建阶段文档"、"更新 README"、"业务规则"、"差距文档"，或任何 /cupdate-* 命令。

  不适用：编写开发 Plan（用 dev-flow）或审查实施代码（用 df-implement-review）。
---

# dev-doc-master — 开发文档规范与维护

产品/项目文档集的编写与维护工作流：PRD、DESIGN（主 + 子）、阶段/Roadmap、README、BUSINESS_RULES。本技能拥有规则与模板；`/cupdate-*` 命令是薄入口，全部路由到这里。

## 使用时机

- 创建或更新产品 PRD、产品 DESIGN、项目 DESIGN、阶段文档、roadmap、项目 README 或项目 BUSINESS_RULES。
- 把过大的主文档按主题拆分为子文档。
- 变更后对齐文档集（PRD ↔ DESIGN ↔ Phase ↔ README ↔ BUSINESS_RULES ↔ AGENTS.md）。
- 记录或更新设计目标态与实现之间的项目差距（`GAPS.md`）。

## 文档集与路由

| 文档 | 命令 | 参考 | 模板 |
|---|---|---|---|
| 产品 PRD | `/cupdate-prd` | `references/prd.md` | `templates/prd.md` |
| 产品 / 项目 DESIGN | `/cupdate-design` | `references/design.md` | `templates/design-product.md` / `templates/design-project.md` |
| 子 DESIGN | （经由 `/cupdate-design`） | `references/design.md` | `templates/design-sub.md` |
| 阶段 | `/cupdate-roadmap` | `references/phase.md` | `templates/phase.md` |
| 项目 README | `/cupdate-readme` | `references/readme.md` | （内联于 `references/readme.md`） |
| 项目 GAPS | （无命令） | `references/gaps.md` | `templates/gaps.md` |
| 项目 BUSINESS_RULES | `/cupdate-br` | `references/business-rules.md` | `templates/business-rules.md` |
| AGENTS.md | `/cupdate-agent-rules` | space-master 技能 | space-master 技能模板 |

写文档前先加载对应的参考文件。所有参考共享 `references/consistency.md` 中的通用规则——每个会话读一次。

## 通用规则（应用于文档集中每一份文档）

完整正文见 `references/consistency.md`。要点：

- **不编号章节**：标题只用 Markdown 标题层级，不加 `## 1.` 前缀。
- **只用相对链接**：所有文档链接相对于仓库根或文档所在目录。禁止绝对路径（文档提交进 git 并共享）。
- **头部 = 必须，末尾 = 参考**：头部链接只放本文档必须遵循的文档（父文档、兄弟文档）。末尾章节放仅参考的材料。一份文档绝不出现两次——同时出现在两个区域会让义务无法解读。
- **主文档罗列子文档**：无后缀主文档头部枚举其全部 `DESIGN-<topic>.md` / `PRD-<topic>.md` 子文档；每个子文档头部通过 `Parent: ./DESIGN.md` 指回。双向索引必须与实际文件一致。
- **文档集一致性**：更新一份文档绝不是孤立的。审查整个文档集（PRD、DESIGN 主/子、Phase、README、AGENTS.md），对齐每个受影响的文档。完成回复中报告受影响的文档集。
- **目标态写作**：文档只描述目标态——系统是什么、存在什么、谁拥有它。禁止过程态描述：不写 "deprecated"、"legacy"、"moved from X"、"old path"、"migration" 之类的说明。能力归他处所有时，陈述归属，而非迁移。
- **差距明细只有一个家**：差距明细存在于项目 `GAPS.md`。阶段文档只按标识、标题、优先级、设计指针列出其范围关闭的差距——绝不复述 Current / Target / Exit。
- **差距是设计陈述，Issue 是代码缺陷**：差距记录未实现的设计契约、代码未跟随的设计变更、或等待收敛的实验性设计领域。契约已满足但存在 bug 是 Issue，不是差距。每个差距恰好属于一个项目——跨项目工作被拆分，使每一半都能独立关闭。方法见 `references/gaps.md`（What Counts as a Gap）。
- **阶段文档不携带能力路线追踪**：Goal 用产品语言陈述阶段交付的能力。每个能力维度站在哪里由产品 DESIGN 中的 Capability Roadmap 回答。复制到阶段文档的追踪需要维护成本，并会偏离它所复制的图。
- **差距通过有界枚举发现**：设计被重做时，以转折提交的设计 diff 为锚点搜索，并用 `file:line` 证据逐项对照实现验证每个变更主题。在铸造新标识前，对照既有差距的完整 `Exit` 清单核对发现。方法见 `references/gaps.md`（Gap Discovery）。
- **写作风格**：读起来像人写的自然语言；一句只表达一个想法；肯定优于否定；归属优于排除。陈述组件做什么、拥有什么，而不是罗列它不做什么。

## 语言

技能自身的参考与模板用英文书写，产出文档的章节标题保持英文。两个原因：质量门脚本按字面匹配标题，且稳定的标题集使文档跨项目、跨语言可比。

文档正文跟随用户偏好语言。用户写中文时正文是中文；写英文时正文是英文。

头部**字段名**保持英文以便质量门脚本解析。头部**字段值**跟随文档语言，读者得到自然的说明而非中英混杂：

```
> **Design Source**: `./DESIGN.md`（差距对照的设计真相源）
> **Companion**: 追踪本项目的目标态差距，逐项解决后关闭。
```

这个拆分意味着文档结构是语言无关的——读者或脚本到处都能找到相同的标题与字段——而内容对受众自然可读。标题保持英文的原因与字段名相同：门禁脚本按字面匹配它们，且稳定的标题集让文档跨项目可比。

## 命名约定

- 主 PRD：`PRD.md`（无后缀）。主 DESIGN：`DESIGN.md`（无后缀）。
- 子文档：`PRD-<topic>.md`、`DESIGN-<topic>.md`（kebab-case），与主文档同目录。无后缀 = 主，带后缀 = 子。
- 拆分阈值：主文档约 500 行，或单个章节约 150 行。
- 支持性文档按内容分类，而非按当前文件名。承载主 DESIGN 关注点的就是子设计，需重命名以匹配；跨切面真相源保持伴随文档。判据见 `references/consistency.md`（Companion Documents vs Sub-DESIGNs）。
- 完整拆分规则见 `references/consistency.md` 与 design 参考。

## 工作流

1. **路由**：从命令或用户请求识别文档类型；加载匹配的参考。
2. **收集上下文**：阅读既有目标文档、其父/兄弟文档，以及实际代码（更新时）。绝不编造事实。
3. **决策，而非反问**：凡规则或仓库能回答的问题，通过阅读解决。`references/consistency.md` 定义哪类事实由哪份文档承载；代码是具体事实的证据。只与用户讨论真正需要其决策的事——未定案的产品意图、边界取舍、方向变更。给出决策，而非你本可以自己解决的一串选项。
4. **写作**：按模板产出文档，应用通用规则。
5. **验证**：运行参考中的质量清单，然后运行**强制质量门**：`scripts/verify-docset.py <docs-dir> --main DESIGN.md`。脚本在真实文件系统上扫描子设计枚举、父链接、绝对路径、坏链、末尾章节重复、过程态词汇、缺失日期。在把更新报告为完成前必须 exit 0。检查文档集一致性与双向索引。
6. **报告**：文件路径、变更摘要、质量门结果（PASS/FAIL）、整个受影响文档集（已检查 / 已对齐 / 需跟进）。

## 文档集一致性（始终）

更新 PRD 影响 DESIGN 与 Phase。更新主 DESIGN 影响子 DESIGN。更新 Phase 影响 PRD 与 DESIGN。更新 README 影响 DESIGN 与 AGENTS.md。完成回复必须说明哪些关联文档被检查、被对齐、或仍需跟进更新。
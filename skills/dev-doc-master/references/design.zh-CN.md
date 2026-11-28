# DESIGN 参考 — 产品与项目现状 DESIGN 编写

创建或更新产品 DESIGN（`templates/design-product.md`）或项目/子模块现状 DESIGN（`templates/design-project.md`、`templates/design-sub.md`）。写作项目主/子现状 DESIGN 时，务必一并阅读 [`design-project-guide.md`](design-project-guide.md) 获取完整分片、实测取证、双场景同步与语义审查标准。

## 两类 DESIGN 的定位区分

| 类型 | 定位 | 模板 | 核心参考 |
|---|---|---|---|
| **产品 DESIGN**（含产品子 DESIGN） | 跨项目系统分层、子系统边界、运行时模型、端到端流程与能力路线图（**允许先于项目实施进行前瞻规划**） | `templates/design-product.md`、`templates/design-sub.md`（产品子 DESIGN 分支） | 本文件（产品章节）+ `consistency.md` |
| **项目 / 子模块现状 DESIGN** | **已落地可核实的当前系统说明**：面向最终用户与新人说清当前提供了什么能力、架构与接口契约、生效业务规则及完整失败边界 | `templates/design-project.md`、`templates/design-sub.md`（项目模块分支） | 本文件 + [`design-project-guide.md`](design-project-guide.md) |

## 两类工作流

| 适用范围 | 上下文定位 | 演进与同步闭环 |
|---|---|---|
| **多项目产品（标准）** | PRD → 产品 DESIGN（系统分层 + `Sibling DESIGNs` + 能力图） | 重大演进经 Proposal（`proposals/proposed/<class>/...`）审议批准后实施；交付时同步更新相关项目/模块现状 `DESIGN` 并将 Proposal 迁入 `implemented/<class>/` |
| **独立项目（简化）** | 无产品 PRD 与产品 DESIGN（项目主 DESIGN 头部 `Parent Product: N/A`、`Parent Architecture: N/A`） | 现状以项目主/子 `DESIGN` 维护；重大演进经项目 `proposals/proposed/<class>/...` 审议，代码+测试+模块现状 `DESIGN`+Proposal 迁入 `implemented/` 同步交付；小修小改按双场景规则按需同步 |

> 注记：项目级工作不再生成或更新 `Phase` 与 `GAPS.md`；未实施的能力目标与跨期演进决定归属 `Proposal`。

## 讨论焦点

- **产品 DESIGN**：系统分层与子系统边界、运行时模型、端到端流程、能力路线（能力维度及其成熟步骤，描述方向而非排期）。
- **项目 / 子模块现状 DESIGN**：用户优先的当前能力、关键限制、薄主地图架构、模块契约、技术选型、对外接口（触发条件/时序/副作用/失败后果）、生效业务规则、数据与状态所有权。
- DESIGN 不保留任务清单、实施中状态勾选或审批会议过程记录。

## 产品 DESIGN：能力路线（保留原貌）

产品 DESIGN 中的 `Capability Roadmap` 是方向性能力图，而非排期表。每行代表一个能力维度，列表示其成熟步骤与主责项目；仅阐述能力将向何形态演化，不写日期或实施进度表。当新能力维度出现或推进时更新对应行；后续演进决策通过产品或项目 Proposal 落地。

## 文档命名与拆分

- 主产品 DESIGN 无后缀：`docs/products/<product-name>/DESIGN.md`。
- 项目主现状 DESIGN 无后缀（位于项目文档目录，如 `docs/DESIGN.md`）。
- 模块/主题子 DESIGN 使用 `DESIGN-<module>.md`（kebab-case），与主文档同目录。
- **多模块项目默认拆分（防多 Agent 并行冲突）**：项目只要存在多个独立模块或职责域，**默认将主 `DESIGN.md` 压薄为概念与模块地图，把详细契约拆入 `DESIGN-<module>.md`**（不必等到主文档超过 500 行才拆）；只有紧密耦合的单模块小项目保留单份 `DESIGN.md`。同时，紧密耦合的单一契约不要为了拆分而机械切碎（详细判据见 `design-project-guide.md`）。
- **按归属选用 `templates/design-sub.md` 双场景契约**：分解**产品主 `DESIGN.md`** 的产品子 DESIGN 允许并应该在实施前规划目标架构与能力演进；分解**项目主 `DESIGN.md`** 的模块子 DESIGN 严格执行现状文档与代码实证契约，不写未交付能力。
- **子文档指回主文档，全面取消主文档头部 `Sub-DESIGNs` 枚举**：每个子 DESIGN 头部必须包含 `> **Parent**: ./DESIGN.md`。**所有主 `DESIGN.md`（含产品 DESIGN 与项目主 DESIGN）头部均不写 `Sub-DESIGNs` 列表**——靠目录内 `DESIGN-*.md` 文件命名即可一眼辨识，主文档在正文章节或模块地图表按需链接，彻底消除并行碰撞主文档头部的风险与无意义脚本检查（词表中仅保留 `Sub-DESIGNs` 容忍存量未改老文档）。

## 头部规则

头部只承载强制依赖链接：

- **产品 DESIGN**：`Product Intent`（遵循的 PRD）+ `Sibling DESIGNs`（核心子系统的项目 DESIGN）+ 存在时的 `Companion Documents`。**不列出 `Sub-DESIGNs`。**
- **项目主现状 DESIGN**：`Parent Architecture`（父产品 DESIGN，无则 `N/A`）+ `Parent Product`（父 PRD，无则 `N/A`）+ 存在时的 `Companion Documents`。**不列出 `Sub-DESIGNs`。**
- **子 DESIGN（产品子 DESIGN / 项目模块子 DESIGN）**：`Parent: ./DESIGN.md` + `Parent Architecture` + `Parent Product`。

## 产品 DESIGN 与项目 DESIGN 的契约关系

产品 DESIGN 统筹多个核心子系统，每个子系统由其独立的项目 DESIGN 承载内部细节。二者属于上下游架构契约归属：

- 产品 DESIGN 的 `Core Projects` 章节界定各子系统的角色、职责边界与跨项目交互契约，并链接到对应的项目 DESIGN。
- 这些项目 DESIGN 必须在产品 DESIGN 头部的 `Sibling DESIGNs` 中声明，即便它位于另一座仓库内，只要其契约约束产品架构，就属于头部强制依赖而非末尾参考材料。

## Sibling DESIGNs vs Reference Documents

区别在于义务而非文件路径远近：

- **Sibling DESIGNs**（头部）：本文档必须遵循其契约的上下游系统 DESIGN。
- **Reference Documents**（末尾章节）：仅作背景参考的材料（外部规范、调研笔记、历史快照或辅助文档）。

一份文档不能同时出现在头部和末尾 `Reference Documents` 中。

## 头部中的伴随文档

像 `BRANDING.md`（品牌常量）或 `API-CONTRACT.md`（跨切面契约）等文件属于文档集但不是某模块子 DESIGN，在主文档头部 `Companion Documents` 或文档关系表声明，保持原名。可选的领域 `GLOSSARY.md` 遵循 `references/glossary.md`，在所属主 DESIGN 或 PRD 头部登记，不作为子 DESIGN。反之，凡实际承担主 DESIGN 某个架构模块或子系统详述的支持性文件，必须识别并命名为 `DESIGN-<module>.md`，加上 `Parent: ./DESIGN.md` 并在主文档正文地图中链接（参见 `consistency.md` 的伴随文档 vs 子 DESIGN 判据）。

## 元数据字段语义

- 通用必填字段：`Status`（`Draft` / `Proposed` / `Active`）与 `Updated`（`YYYY-MM-DD`，每次修改刷新）。
- 对已落地运行的项目/子模块现状 DESIGN，`Status` 为 `Active`；仅尚未定型的新建草案使用 `Draft` / `Proposed`。设计文档没有 `"Completed"` 状态。
- 子文档使用 `Parent: ./DESIGN.md` 指回直接父级，`Parent Architecture` 指回产品级 DESIGN，两者分别成行。

## 更新模式与同步流

1. 保留既有文件路径与英文标题。
2. 先核实真实代码、配置与实际命令/测试运行证据（**详见 `design-project-guide.md`**）。
3. 刷新 `Updated` 日期。
4. 按双场景同步规则修改受影响章节（纯内部重构不动 DESIGN；单模块改动只改对应 `DESIGN-<module>.md` 不碰主文档；并行发现写集外漂移仅上报主控）。
5. 补齐失效边界与生效业务规则，移除过期或无法在代码中核实的内容（无法实测之处显式标注未实测）。

## 质量清单

### 通用与产品 DESIGN 审查项

- [ ] 选择正确模板（`design-product.md` / `design-project.md` / `design-sub.md`）
- [ ] 英文标题（无数字编号）、英文头部字段名；正文及字段解释符合用户偏好语言
- [ ] `Updated` 为最新日期，`Status` 准确反映当前态（现状文档生效为 `Active`）
- [ ] 头部 = 强制依赖链接；末尾 `Reference Documents` = 仅参考；二者无重复；所有链接为相对路径且真实存在
- [ ] 无过程态迁移碎语（`deprecated`、`legacy`、`moved from`、`已废弃`、`历史机制` 等）
- [ ] 产品 DESIGN（如适用）：紧扣 PRD；`Capability Roadmap` 描述能力方向而非排期；核心子系统列于 `Sibling DESIGNs`

### 项目与子模块现状 DESIGN 必查项（完整清单与四道把控闭环见 `design-project-guide.md`）

- [ ] **现状真实与实测证据**：全部内容为已落地系统事实，无未来计划冒充现状；命令/配置/默认值/限制经代码或运行结果核实，无法实测项显式标注未实测
- [ ] **并行防冲突与通用骨架**：主 `DESIGN.md` 保持薄地图（含跨模块协作主流程、`Source Carrier` 路径前缀、头部无 `Sub-DESIGNs` 强枚举）；多模块细节按“固定首尾锚点 + 1..N 个领域自由分节”写入 `DESIGN-<module>.md`（带 `Parent: ./DESIGN.md`，零孤立子文档）；未手抄源码文件树、完整 CLI 参数表或全量 API 字段表
- [ ] **用户优先与五项必填覆盖**：不读代码也能看懂核心能力与限制；关键流程覆全行为主体/触发、组件时序、许可与禁令、副作用/状态所有权及完整失败后果与恢复；含 `## Business Rules and Failure Boundaries`；`Key Decisions` 仅留落地结论与对应 Proposal 链接
- [ ] **Slop Checklist 通过**：无思考过程泄露、无实现状态标签、无规则堆砌、无滥用加粗、无跨级逐字重复

## 强制质量门（报告完成前）

先完成上述语义清单，再运行脚本：`python3 scripts/verify-docset.py <docs-dir> --main DESIGN.md`（代码与文档联动交付时加 `--check-sync [--base <git-ref>]`；必须 exit 0 后才可声明完成）。脚本检查磁盘与结构事实：

1. 扫描磁盘 `DESIGN-*.md` 子文档确认均带有 `Parent: ./DESIGN.md` 指回（全面取消头部 `Sub-DESIGNs` 枚举），且均在主文档正文除 `Reference Documents` 外被链接（零孤立子文档）
2. 零绝对路径（`file:///`、`/Users/...`、`/Volumes/...`）
3. 所有相对路径与 Markdown 链接真实存在
4. 末尾 `Reference Documents` 不重复头部链接或本地子 DESIGN
5. 零未替换模板占位符与空表格骨架行
6. 所有 `##` 章节非空，且项目主/生效模块子文档必备 `## Business Rules and Failure Boundaries`
7. 无过程态禁语，具备 `Updated` 日期、合法英文头部字段与有效 `Status`
8. 可选 `--check-sync`：按 `Source Carrier` 映射本轮非测试代码改动，要求同步更新所属 `DESIGN-<module>.md`（纯内部重构需显式声明 `--pure-refactor "<原因>"` 留痕交评审复核）

## 完成后回复

用用户语言汇报：修改文件路径、变更摘要、**真实核实与显式标注的未实测项**、语义审查及 `verify-docset.py` 结果（PASS/FAIL）、并行期发现但未越界修改的写集外文档漂移（若有），以及符合逻辑的下一步建议（例如：产品 DESIGN 影响子系统时检查对应现状 DESIGN 或按需起草 Proposal；项目现状 DESIGN 留下新长期工程规则时运行 `/cupdate-agent-rules`；随代码交付时继续完成验证与提交）。

## 一份 DESIGN 文档拥有什么

| 属于 DESIGN | 属于别处 |
|---|---|
| 系统/模块定位、能力边界与用户可观察行为 | 未实施的设计演进、方案对比与审批状态 → Proposal（`proposals/proposed/<class>/...`） |
| 薄主地图、模块拆分与核心协作流 | 历史/已完成方案决策记录与后果 → Proposal（`proposals/implemented/<class>/...`） |
| 经核实的接口契约、数据/状态所有权、生效业务规则与失败边界 | 复杂任务的拆分、委派与执行编排 → Plan（可选，由 `dev-flow` 管） |
| 关键落地决策摘要（附 Proposal 链接）与技术选型理由 | Agent 操作命令、门禁检查、测试流程 → `AGENTS.md` / `rules/testing.md` |
| 部署机制设计（架构组成、状态落点、回滚语义） | 部署操作 Runbook 与分支门禁 → `AGENTS.md` |

## 区分产品意图与项目现状事实

- **项目/子模块现状 DESIGN**：只记代码与运行事实。哪怕某个模块已经规划但尚未开发，也绝不在项目现状 DESIGN 中写成已存在能力；若因特性开关/配置门控导致表面接口不可达，必须写明开关条件，不得将不可达路径呈报为常规生效行为；符号链接或仓外资源须标明实际源头。
- **产品 DESIGN**：允许在 `Capability Roadmap` 等架构愿景节阐述方向性意图，但列出的现有组件路径、真实边界必须与仓库一致。发现与代码存在方向性分歧时，先核实源码并按对齐纪律报告分歧，不擅自拍板改产品意图。

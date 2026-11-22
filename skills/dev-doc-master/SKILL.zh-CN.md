---
name: dev-doc-master
description: |
  编写与审查产品文档集——产品 PRD、产品 DESIGN，以及项目/模块现状 DESIGN（DESIGN.md、DESIGN-<module>.md）。

  使用场景：用户要求编写、更新、按模块拆分或一致性校验 PRD、产品 DESIGN、项目/模块现状 DESIGN，依据真实代码同步项目 DESIGN，或执行 /cupdate-prd、/cupdate-design 时。

  不适用：/cupdate-agent-rules、/cupdate-readme 或 AGENTS.md/项目 README 治理（用 space-master）、编写开发 Plan 或 Task 编排（用 dev-flow）、编码实施（用 df-implement）、或独立方案/代码评审（用 df-proposal-review / df-implement-review）。
---

# dev-doc-master — 开发文档规范与维护

面向多项目空间的跨项目文档规范与写作底座，覆盖产品 PRD、产品 DESIGN，以及项目/子模块**现状 DESIGN**（主 `DESIGN.md` + `DESIGN-<module>.md`）。`/cupdate-prd` 与 `/cupdate-design` 为薄入口，均路由至此技能；`AGENTS.md` 与项目 `README.md` 编制归 `space-master`。

## 使用时机

- 创建或更新产品 PRD、产品 DESIGN。
- 编写、同步或按模块拆分项目与子模块现状 DESIGN（将已落地系统行为、生效业务规则与失败边界写给读者）。
- 对现有文档集执行语义审查（新人可读性、实测取证、Slop Checklist）与结构一致性检查。

> 未实施的需求演进、架构提案、替代方案对比与批准状态归 **Proposal**（`proposals/{proposed,implemented,rejected,archived}/{class}/yyyy-mm-dd-<slug>.md`），不预写进项目现状 DESIGN。

## 文档集与路由

| 文档 | 命令 | 参考 | 模板 |
|---|---|---|---|
| 产品 PRD | `/cupdate-prd` | `references/prd.md` | `templates/prd.md` |
| 产品 DESIGN | `/cupdate-design` | `references/design.md` | `templates/design-product.md` |
| 项目主现状 DESIGN | `/cupdate-design` | `references/design.md`、`references/design-project-guide.md` | `templates/design-project.md` |
| 模块/子现状 DESIGN | （经由 `/cupdate-design`） | `references/design.md`、`references/design-project-guide.md` | `templates/design-sub.md` |
| AGENTS.md / README | `/cupdate-agent-rules` / `/cupdate-readme` | `space-master` 技能 | `space-master` 模板 |

动笔前先读 `references/consistency.md` 通用规则，并按文档类型加载对应参考；写或更新项目/子模块现状 DESIGN 时务必加载 `references/design-project-guide.md`。

## 核心规则要点（完整规范见 `references/consistency.md` 与 `references/design-project-guide.md`）

- **现状准确（项目/子 DESIGN）vs 产品意图（PRD/产品 DESIGN）**：项目与子模块 DESIGN 只陈述**已落地、经核实存在且真实运行**的行为、约束与生效业务规则，不预写未交付蓝图或进度表；产品 PRD 与产品 DESIGN 保留原有架构与能力路线规范。两者均禁止过程态迁移碎语（`deprecated`/`legacy`/`moved from`/`已废弃`/`历史机制`）。
- **防多 Agent 并行冲突结构**：
  1. 主 `DESIGN.md` 压薄为项目定位、核心流转与模块地图，模块内部细节不堆在主文档；
  2. 多模块或有独立职责域的项目**默认按模块拆出 `DESIGN-<module>.md`**（不等到 500 行才拆）；紧耦合单模块小项目保留单份 `DESIGN.md`；
  3. **全面取消主文档头部 `Sub-DESIGNs` 强枚举**（无论产品 DESIGN 还是项目主 DESIGN，均靠文件名 `DESIGN-*.md` 与子文档头部 `Parent: ./DESIGN.md` 识别，主文档在正文对应章节/地图链接），消除并发碰撞；
  4. 日常单模块开发与修 Bug 不改主 `DESIGN.md`；多 Agent 并行期只改授权写集内所属子文档，发现主文档或他人模块漂移**只上报主控，严禁越界修改共享文档**。
- **不手抄易变代码清单**：严禁手抄完整源码文件树、全量 CLI 参数表或 API 字段清单；按通用“固定首尾锚点 + 1..N 个领域自由分节”写出满足五项必填覆盖要素的完整行为契约（行为主体/触发、时序、必须/可能/禁止、状态副作用、完整失败后果与恢复），并在主地图标注 `Source Carrier` 源码路径前缀。
- **业务规则与关键决策归属**：项目不再新建独立 `BUSINESS_RULES.md`（存量仅作只读参考）；生效业务规则与失败边界直接写入 `## Business Rules and Failure Boundaries`（项目主/生效模块子文档强制要求）；`## Key Decisions` 仅保留已落地结论摘要及指向对应 `proposals/implemented/<class>/...`（或引用历史快照时 `proposals/archived/<class>/...`）的链接。
- **实测取证与诚实边界**：记录的命令、配置、默认值、路由、错误码与限制必须由实际代码、测试或亲手运行结果核实；无法实测之处必须**显式标注未实测及验证条件**，绝不伪造已通过结论。
- **英文标题 + 用户偏好语言正文**：所有章节标题（无数字编号，如 `## Module Architecture`）与头部字段名保持英文以便脚本解析与跨项目对比；正文及头部字段值解释跟随用户偏好语言。只使用相对链接，头部放必须遵循的依赖、末尾 `## Reference Documents` 放仅参考材料，互不重复。

## 命名与拆分准则

- 主文档无后缀：`PRD.md`、`DESIGN.md`；子文档：`PRD-<topic>.md`、`DESIGN-<module>.md`（kebab-case，与主文档同目录）。
- 拆分以**独立模块或独立职责所有权**为准，多模块项目默认拆分以支持并发分工；单模块紧耦合规则保持在同一文档内，不为了凑字数机械切碎。
- 跨切面参考真相源（如 `BRANDING.md`、`API-CONTRACT.md`）作为伴随文档在主文档头部 `Companion Documents` 声明，按内容而非按原文件名区分归属。

## 工作流

1. **路由判断**：识别文档类型（PRD / 产品 DESIGN / 项目主现状 DESIGN / 模块子现状 DESIGN），加载 `references/consistency.md` 及对应指南。
2. **采集并核实事实**：阅读现有目标文档、上下游关联文档与**真实代码/测试**；对关键命令与行为做实际验证取证；只把需要产品拍板的模糊点交用户决策，可从代码读出的问题不反问。
3. **撰写或同步更新**：按对应模板与规则编写，遵守双场景同步纪律（随 Proposal 落地同批同步，或无 Proposal 修对外可见缺陷时同步所属模块子文档；纯内部重构不动文档；并行期严禁越界修改写集外文档）。
4. **语义审查与机械门禁**：
   - 运行 `references/design-project-guide.md` 的**统一语义审查清单**与**四道质量把控闭环**（其中文风清晰与 **Slop Checklist** 适用于全部文档；**“已交付并经代码/运行实测核实”仅约束项目与模块现状 DESIGN**，不限制产品 PRD 与产品 DESIGN 提前规划目标架构）；
   - 运行确定性检查门禁：`python3 scripts/verify-docset.py <docs-dir> --main DESIGN.md`（代码与文档联动交付时加 `--check-sync [--base <git-ref>]` 检查孤立子文档、模板占位符、必填边界与 `Source Carrier` 代码同步，无脚本环境时按规则逐项检查），必须 exit 0 后才可声明完成。
5. **汇报结果**：输出变动文件路径、变更摘要、真实核实与未实测项、门禁结果（PASS/FAIL）、关联文档集检查情况，以及若存在的写集外文档漂移上报。

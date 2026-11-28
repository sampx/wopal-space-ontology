---
name: dev-doc-master
description: |
  编写与审查产品文档集——产品 PRD、产品 DESIGN，项目/模块现状 DESIGN（DESIGN.md、DESIGN-<module>.md），以及领域术语表（GLOSSARY.md）。

  使用场景：用户要求编写、更新、按模块拆分或一致性校验 PRD、产品 DESIGN、项目/模块现状 DESIGN，领域术语表编写与同步、依据真实代码同步项目 DESIGN，或执行 /cupdate-prd、/cupdate-design 时。

  不适用：/cupdate-agent-rules、/cupdate-readme 或 AGENTS.md/项目 README 治理（用 space-master）、编写开发 Plan 或 Task 编排（用 dev-flow）、编码实施（用 df-implement）、或独立方案/代码评审（用 df-proposal-review / df-implement-review）。
---

# dev-doc-master — Development Documentation Master

面向多项目空间的跨项目文档规范与写作底座，覆盖产品 PRD、产品 DESIGN，项目/子模块**现状 DESIGN**（主 `DESIGN.md` + `DESIGN-<module>.md`），以及可选领域术语表。`/cupdate-prd` 与 `/cupdate-design` 为薄入口，均路由至此技能；`AGENTS.md` 与项目 `README.md` 编制归 `space-master`。

## Document Set and Routing

| 文档 | 命令 | 参考 | 模板 |
|---|---|---|---|
| 产品 PRD | `/cupdate-prd` | `references/prd.md` | `templates/prd.md` |
| 产品 DESIGN | `/cupdate-design` | `references/design.md` | `templates/design-product.md` |
| 项目主现状 DESIGN | `/cupdate-design` | `references/design.md`、`references/design-project-guide.md` | `templates/design-project.md` |
| 模块/子现状 DESIGN | （经由 `/cupdate-design`） | `references/design.md`、`references/design-project-guide.md` | `templates/design-sub.md` |
| 领域术语表 | （按需或交付同步） | `references/glossary.md` | `templates/glossary.md` |
| AGENTS.md / README | `/cupdate-agent-rules` / `/cupdate-readme` | `space-master` 技能 | `space-master` 模板 |

动笔前先读 `references/consistency.md` 通用规则，并按文档类型加载对应参考；写或更新项目/子模块现状 DESIGN 时务必加载 `references/design-project-guide.md`。

## 核心原则

`references/consistency.md` 负责文档归属、命名、约束引用和共享写集纪律；`references/design-project-guide.md` 负责目标与现状共用的五项行为契约、实测取证、语义审查及交付同步；`references/glossary.md` 负责术语定义及同步。产品 PRD 与产品 DESIGN 可表达意图，项目/模块 DESIGN 记录经核实的交付行为。未交付的目标契约与新定义归 Proposal。

## Workflow

1. **路由判断**：识别文档类型（PRD / 产品 DESIGN / 项目主现状 DESIGN / 模块子现状 DESIGN / 领域术语表），加载 `references/consistency.md` 及对应指南。
2. **采集并核实事实**：阅读现有目标文档、上下游关联文档与**真实代码/测试**；对关键命令与行为做实际验证取证；只把需要产品拍板的模糊点交用户决策，可从代码读出的问题不反问。
3. **撰写或同步更新**：遵循对应模板与指南；交付同步受影响 DESIGN 与术语，按写集协作。
4. **语义审查与机械门禁**：
   - 运行 `references/design-project-guide.md` 的**统一语义审查清单**与**四道质量把控闭环**（其中文风清晰与 **Slop Checklist** 适用于全部文档；**“已交付并经代码/运行实测核实”仅约束项目与模块现状 DESIGN**，不限制产品 PRD 与产品 DESIGN 提前规划目标架构）；
   - 运行确定性检查门禁：`python3 scripts/verify-docset.py <docs-dir> --main DESIGN.md`（代码与文档联动交付时加 `--check-sync [--base <git-ref>]` 检查孤立子文档、模板占位符、必填边界与 `Source Carrier` 代码同步，无脚本环境时按规则逐项检查），必须 exit 0 后才可声明完成。
5. **汇报结果**：输出变动文件路径、变更摘要、真实核实与未实测项、门禁结果（PASS/FAIL）、关联文档集检查情况，以及若存在的写集外文档漂移上报。

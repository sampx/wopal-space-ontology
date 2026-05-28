# ontology 产品文档工作区 — Agent 开发规范

## 1. 定位

ontology 产品的文档工作区，承载 PRD、DESIGN、本地化审阅、计划、研究与参考资料。

## 2. 目录

| 目录 | 职责 |
|---|---|
| `LANG/<locale>/` | 本地化审阅版；按 locale 分目录，内部 agents/commands/rules/templates 与 `.wopal/` 运行时目录对齐，规则见子目录 AGENTS.md |
| `plans/` | 开发计划归档 |
| `backlogs/` | 产品级待决策问题沉淀 |
| `research/` | 技术调研记录 |
| `research/memory/` | Agent 记忆技能调研（外部记忆方案对比、LanceDB 选型） |
| `research/claude-code/` | Claude Code 子代理角色参考 |
| `references/` | 外部参考规范与功能借鉴 |
| `references/agentskills/` | Agent Skills 开放格式规范（SKILL.md 格式、目录结构约定） |
| `references/openspec/` | OpenSpec SDD 操作指南（spec-driven 开发流程规范） |


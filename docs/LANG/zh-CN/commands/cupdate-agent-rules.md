---
description: 创建或更新项目 AGENTS.md
---

# Create or Update Agent Rules — 创建或更新 Agent 规则

创建或更新项目级（`<project>/AGENTS.md`）、文档目录级（`<project>/docs/AGENTS.md`）或模块子目录级（`<project>/<dir>/AGENTS.md`）规范文件。

**输入参数**: `$1` `$2`

**参数说明**: `[path|project-name] [extra-rules-context]`。路径或项目名必填。仅给项目名时，从 `.wopal-space/STRUCTURE.md` 与 `projects/` 推断候选，无法唯一解析时向用户确认。凡在装配了 `dev-doc-master` 的空间中以路径或项目名指向项目根，且其 `docs/` 目录缺少 `docs/AGENTS.md` 时，在同一确认方案中主动提议同步建档 `<project>/docs/AGENTS.md`。

---

## 工作方式

本命令仅为入口——权威规范位于 `space-master` 技能。

1. 加载 `space-master` 技能。
2. 遵循技能中的 **AGENTS.md 维护**（AGENTS.md Maintenance）章节及其 `references/agents-md-maintenance.md` 的完整工作流：按层选模板（`templates/agent-rules.md` / `agent-rules-docs.md` / `agent-rules-subdir.md`）、规则审计、质量门禁（含 `Doc sync`）、确认计划、语言版本顺序、链接与标题规则、文档集一致性、质量清单。
3. 若本命令无法解析任务，使用技能的路由表找到正确工作流。

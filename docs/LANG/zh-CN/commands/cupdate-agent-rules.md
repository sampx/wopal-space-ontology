---
description: 创建或更新项目 AGENTS.md
---

# Create or Update Agent Rules — 创建或更新 Agent 规则

创建或更新项目级或目录级 `AGENTS.md`。

**输入参数**: `$1` `$2`

**参数说明**: `[path|project-name] [extra-rules-context]`。路径或项目名必填。仅给项目名时，从 `.wopal-space/STRUCTURE.md` 与 `projects/` 推断候选；无法唯一解析时需向用户确认。

---

## 工作方式

本命令仅为入口——权威规范位于 `space-master` 技能。

1. 加载 `space-master` 技能。
2. 遵循技能中的 **AGENTS.md 维护**（AGENTS.md Maintenance）章节及其 `references/agents-md-maintenance.md` 的完整工作流：规则审计、确认计划、语言版本顺序、链接与标题规则、文档集一致性、质量清单。
3. 若本命令无法解析任务，使用技能的路由表找到正确工作流。

此处不重复或转述规范内容。不确定时，阅读参考文档。
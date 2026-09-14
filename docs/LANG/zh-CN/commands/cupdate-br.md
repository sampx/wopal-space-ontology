---
description: 创建或更新项目 BUSINESS_RULES.md
---

# Create or Update Business Rules — 创建或更新业务规则

创建或更新项目级 `BUSINESS_RULES.md`——产品业务规则的单一真相源。

**输入参数**: `$ARGUMENTS`

**参数说明**: 项目名。未提供时，从 `projects/` 与上下文推断；不清晰时向用户确认。

---

## 工作方式

本命令仅为入口——权威规范位于 `dev-doc-master` 技能。

1. 加载 `dev-doc-master` 技能。
2. 遵循 `references/business-rules.md` 中的 **BUSINESS_RULES 参考**（BUSINESS_RULES Reference）与 `references/consistency.md` 中的通用规则，覆盖完整工作流：规则定义边界、文档定位、头部、正文格式、来源优先级、提炼步骤、更新模式与质量清单。
3. 使用技能内模板 `templates/business-rules.md`。

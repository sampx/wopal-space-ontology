---
description: 创建或更新产品 DESIGN 或项目 DESIGN
---

# Create or Update DESIGN — 创建或更新 DESIGN

创建或更新产品 DESIGN（产品架构）或项目 DESIGN（项目内部设计）。简单项目可跳过产品 DESIGN，走简化流程：项目 DESIGN（内含产品级设计）→ Plan。

**输入参数**: `$1` `$2`

**参数说明**: `<name> [product|project]`。未提供时，从 `docs/products/` 与 `projects/*/docs/` 目录匹配推断；不清晰时向用户确认。

---

## 工作方式

本命令仅为入口——权威规范位于 `dev-doc-master` 技能。

1. 加载 `dev-doc-master` 技能。
2. 遵循 `references/design.md` 中的 **DESIGN 参考**（DESIGN Reference）与 `references/consistency.md` 中的通用规则，覆盖完整工作流：两种设计流程、讨论重点、文档命名与拆分、头部、更新模式、质量清单。
3. 使用技能内模板：`templates/design-product.md`（产品）与 `templates/design-project.md`（项目）。

此处不重复或转述规范内容。不确定时，阅读参考文档。
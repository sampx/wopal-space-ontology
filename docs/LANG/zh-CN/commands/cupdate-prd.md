---
description: 创建或更新产品 PRD 文档
---

# Create or Update PRD — 创建或更新 PRD

创建或更新产品 PRD 文档。

**输入参数**: `$ARGUMENTS`

**参数说明**: 产品名。未提供时，从 `docs/products/` 推断。

- 项目级信息由 DESIGN 文档维护；PRD 仅存在于产品级。

---

## 工作方式

本命令仅为入口——权威规范位于 `dev-doc-master` 技能。

1. 加载 `dev-doc-master` 技能。
2. 遵循 `references/prd.md` 中的 **PRD 参考**（PRD Reference）与 `references/consistency.md` 中的通用规则，覆盖完整工作流：文档路径与命名、上下文收集、编写规则、头部、更新模式、质量清单。
3. 使用技能内模板 `templates/prd.md`。

此处不重复或转述规范内容。不确定时，阅读参考文档。
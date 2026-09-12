---
description: 引导产品阶段讨论并产出阶段定义与跟踪文档
---

# Create or Update Roadmap — 创建或更新 Roadmap

引导用户完成逐阶段讨论：目标、当前状态、范围、目标与差距（含设计更新），以及面向上层残余风险的整体评审。产出阶段定义与跟踪文档。

**输入参数**: `$1` `$2`

**参数说明**: `<name> [phase-id]`。未提供时，从 `docs/products/` 推断产品名；不清晰时向用户确认。`phase-id` 可选；省略时默认当前 Active 阶段。

---

## 工作方式

本命令仅为入口——权威规范位于 `dev-doc-master` 技能。

1. 加载 `dev-doc-master` 技能。
2. 遵循 `references/phase.md` 中的 **Phase 参考**（Phase Reference）与 `references/consistency.md` 中的通用规则，覆盖完整工作流：阶段目标讨论、当前状态、范围、目标与差距、残余风险、文档更新纪律、质量清单。
3. 使用技能内模板 `templates/phase.md`。

此处不重复或转述规范内容。不确定时，阅读参考文档。
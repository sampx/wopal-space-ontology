---
description: 创建或更新产品 DESIGN 或项目 DESIGN
---

# Create or Update DESIGN — 创建或更新 DESIGN

创建或更新产品 DESIGN（产品架构）或项目/模块现状 DESIGN（经核实的当前系统行为、契约、生效业务规则与完整失败边界）。独立项目可跳过产品 DESIGN（头部 `Parent Architecture: N/A`、`Parent Product: N/A`）。

**输入参数**: `$1` `$2`

**参数说明**: `<name> [product|project]`。未提供时，从 `docs/products/` 与 `projects/*/docs/` 目录匹配推断；不清晰时向用户确认。

---

## 工作方式

本命令仅为入口——权威规范位于 `dev-doc-master` 技能。

1. 加载 `dev-doc-master` 技能。
2. 遵循 `references/design.md` 中的 **DESIGN 参考**、编写或同步项目/模块文档时的 `references/design-project-guide.md`，以及 `references/consistency.md` 中的通用规则。
3. 使用技能内模板：`templates/design-product.md`（产品）、`templates/design-project.md`（含 `Source Carrier` 的项目薄主地图）与 `templates/design-sub.md`（通用固定首尾锚点 + 领域自由分节 + 五项必填覆盖）。
4. 完成后运行 `python3 scripts/verify-docset.py <docs-dir> --main DESIGN.md`（随代码交付时加 `--check-sync [--base <git-ref>]`）确保 exit 0。

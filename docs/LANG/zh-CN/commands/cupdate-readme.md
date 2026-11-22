---
description: 创建或更新项目 README.md
---

# Create or Update README — 创建或更新 README

创建或更新项目 `README.md`（或独立发布 monorepo 子包的薄消费入口 `README.md`）。

**输入参数**: `$ARGUMENTS`

**参数说明**: 项目名。未提供时，从 `projects/` 下的项目列表结合上下文推断；不清晰时向用户确认。

示例：

```bash
/cupdate-readme
/cupdate-readme projects/wopal-cli
```

---

## 工作方式

本命令仅为入口——权威规范位于 `space-master` 技能。

1. 加载 `space-master` 技能。
2. 遵循 `references/readme-maintenance.md` 中的 **README 维护**完整工作流：能力感知、项目级或独立发布子包命名边界、开篇价值与关键限制、核心规则、更新模式、确认策略、质量清单。
3. 使用 README 维护参考中的内嵌模板。

---
description: 创建或更新项目 README.md
---

# Create or Update README — 创建或更新 README

创建或更新项目 `README.md`。

**输入参数**: `$ARGUMENTS`

**参数说明**: 项目名。未提供时，从 `projects/` 下的项目列表结合上下文推断；不清晰时向用户确认。

示例：

```bash
/cupdate-readme
/cupdate-readme projects/wopal-cli
```

---

## 工作方式

本命令仅为入口——权威规范位于 `dev-doc-master` 技能。

1. 加载 `dev-doc-master` 技能。
2. 遵循 `references/readme.md` 中的 **README 参考**（README Reference）与 `references/consistency.md` 中的通用规则，覆盖完整工作流：文档路径与命名、用途、核心规则、更新模式、确认策略、质量清单。
3. 使用 README 参考中的内嵌模板。

此处不重复或转述规范内容。不确定时，阅读参考文档。
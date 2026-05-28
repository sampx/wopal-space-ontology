# zh-CN 本地化审阅目录 — Agent 开发规范

## 1. 项目定位

ontology 产品的中文（zh-CN）本地化审阅目录，存放 Agent 灵魂、命令、规则、模板的中文审阅版本。

## 2. 架构与目录

审阅版 → 人工确认 → 同步到 `.wopal/` 对应英文运行时源文件。

| 目录 | 对应运行时源 | 内容 |
|---|---|---|
| `agents/` | `.wopal/agents/` | Agent 灵魂中文审阅版（wopal、fae、rook） |
| `commands/` | `.wopal/commands/` | 命令中文审阅版，含 `wopal/` 子目录 |
| `rules/` | `.wopal/rules/` | 规则中文审阅版，含 `fae/`、`wopal/` 子目录 |
| `templates/` | `.wopal/templates/` | 模板中文审阅版 |


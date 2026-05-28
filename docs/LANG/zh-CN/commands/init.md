---
description: 校准空间运行时结构
---

校准当前 WopalSpace 的运行时结构：检查 `.wopal-space/` 骨架是否完整、检测结构与实际布局之间的漂移、比对模板差异，汇总为报告供你确认后再执行写入。

$ARGUMENTS

## 目标

本命令面向**已有空间的维护场景**，负责：
- 校验运行时结构与 `STRUCTURE.md` 声明的一致性
- 确保关键运行时文件（`REGULATIONS.md`、`memory/USER.md`、`memory/MEMORY.md`）存在且内容不是严重过时的

它不是 `wopal space init` 的替代——初始化走 CLI，维护走 `/init`。

## 调查范围

/w 会读取以下来源来构建当前空间的状态快照：

1. **结构真相源**：`.wopal-space/STRUCTURE.md` — 从 frontmatter 和 Markdown 表格中提取空间应包含的结构声明
2. **运行时目录**：`.wopal-space/` — 实际扫描目录和文件，与声明结构逐项对比
3. **空间根目录**：检查根目录下的 `AGENTS.md` 和 `.gitignore` 是否存在
4. **本体模板**：`.wopal/templates/` — 用于差异比较的参考模板（`STRUCTURE.md`、`REGULATIONS.md`、`root-AGENTS.md`、`gitignore`、`memory/USER.md`、`memory/MEMORY.md`）
5. **Schema**：`.wopal/templates/wopalspace-schema.yaml` — 定义了运行时和空间文件的规范布局

如果 `STRUCTURE.md` 根本不存在，报告并提示先运行 `wopal space init`，终止。

## 执行顺序

1. **读取现状** — 加载 `STRUCTURE.md`，扫描 `.wopal-space/` 和空间根目录的实际文件和目录树
2. **校准结构** — 将实际布局与 `STRUCTURE.md` 的 frontmatter 以及 schema 对比，识别：缺失的目录、缺失的文件、`STRUCTURE.md` 中声明了但实际不存在的条目
3. **检查运行时文件** — 逐个检查 `REGULATIONS.md`、`memory/USER.md`、`memory/MEMORY.md` 是否存在；检查根目录 `AGENTS.md` 和 `.gitignore`
4. **报告模板差异** — 对每个有对应模板的运行时文件，展示模板内容和当前实例之间的 diff 摘要，高亮必须保留的用户自定义内容
5. **等你确认** — 将所有发现整理成结构化报告展示给你，在你明确说"可以"之前不动任何文件
6. **写入** — 确认后仅执行你批准的变更：创建缺失的目录/文件、更新 `STRUCTURE.md` 的结构事实、保留所有你写过的内容

## 输出约束

- 结构报告必须明确引用 `STRUCTURE.md` 和 `REGULATIONS.md`
- 每项发现必须清晰标注分类：**缺失**（不存在）、**漂移**（存在但与声明结构不一致）、**模板差异**（实例内容与模板有出入）
- 不得在未展示 diff 并获得确认的情况下覆盖 `REGULATIONS.md`、`memory/USER.md` 或 `memory/MEMORY.md` 中你写过的内容
- 保持交互式确认风格：先报、你批、再写
- 不要把确定性的初始化逻辑（创建目录、渲染模板）塞进这个命令——那是 `wopal space init` 的事

## 问答

仅当现有信息不足以判断运行时状态时才提问。用 `question` 工具，最多一次简短批量问完。

适合问的场景：
- `STRUCTURE.md` 中有歧义的结构条目
- `STRUCTURE.md` 与实际布局信息冲突
- 扫描中发现了未声明的目录，不确定你的意图

Schema 或 `STRUCTURE.md` 已经明确的事情别问。

---
description: 校准空间运行时结构
---

校准当前 WopalSpace 运行时结构：验证 `.wopal-space/` 骨架，检测结构漂移，并报告模板差异供用户确认后再写入。

用户提供的焦点或约束（必须遵守）：
$ARGUMENTS

## 目标

确保当前空间运行时与其 `STRUCTURE.md` 声明的结构一致，且关键运行时文件（`REGULATIONS.md`、`memory/USER.md`、`memory/MEMORY.md`）存在且保持最新。这是已有空间的维护命令——不是 `wopal space init` 的替代。

## 调查范围

读取以下来源以构建当前状态图景：

1. **结构真相源**：`.wopal-space/STRUCTURE.md` — frontmatter 与 Markdown 表格定义了空间应包含的内容。
2. **运行时目录**：`.wopal-space/` — 扫描实际目录与文件，对照声明结构。
3. **空间根目录**：检查空间根目录下的 `AGENTS.md` 和 `.gitignore`。
4. **本体模板**：`.wopal/templates/` — 参考模板用于差异比较（`STRUCTURE.md`、`REGULATIONS.md`、`root-AGENTS.md`、`gitignore`、`memory/USER.md`、`memory/MEMORY.md`）。
5. **Schema**：`.wopal/templates/wopalspace-schema.yaml` — 定义规范的运行时与空间文件/目录布局。

若 `STRUCTURE.md` 缺失，报告需先运行 `wopal space init` 并终止。

## 执行顺序

1. **读取现状** — 加载 `STRUCTURE.md`，扫描 `.wopal-space/` 与空间根目录的实际文件和目录。
2. **校准结构** — 将实际布局与 `STRUCTURE.md` frontmatter 及 schema 对比。识别缺失目录、缺失文件和未声明条目。
3. **检查运行时文件** — 验证 `REGULATIONS.md`、`memory/USER.md`、`memory/MEMORY.md` 是否存在。检查根目录 `AGENTS.md` 和 `.gitignore` 是否存在。
4. **报告模板差异** — 对每个有对应模板的运行时文件，展示模板与当前实例之间的差异摘要。高亮必须保留的用户自撰内容。
5. **等待用户确认** — 将所有发现以结构化报告呈现。在用户明确确认前不写入任何文件。
6. **写入** — 确认后仅执行已批准的变更：创建缺失目录/文件、更新 `STRUCTURE.md` 结构事实、保留所有用户自撰内容。

## 输出约束

- 结构报告必须显式引用 `STRUCTURE.md` 和 `REGULATIONS.md`。
- 每项发现清晰标注为：**缺失**（不存在）、**漂移**（存在但与声明结构不符）或 **模板差异**（实例与模板不同）。
- 不得在未展示差异并获得明确确认的情况下覆盖 `REGULATIONS.md`、`memory/USER.md` 或 `memory/MEMORY.md` 中的用户自撰内容。
- 保留交互式确认风格：先报告、等待用户批准、再写入。
- 不将确定性初始化逻辑（目录创建、模板渲染）放入此命令——这些属于 `wopal space init`。

## 问答

仅在可用来源无法解决运行时状态时才向用户提问。使用 `question` 工具，最多一次简短批量提问。

适宜提问的场景：
- `STRUCTURE.md` 中有歧义的结构条目
- `STRUCTURE.md` 与实际布局信息冲突
- 扫描中发现的未声明目录的用户意图

不要就 schema 或 `STRUCTURE.md` 已明确的内容提问。

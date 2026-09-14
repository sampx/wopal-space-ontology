# GAPS — ontology Design vs Implementation Divergence

> **Status**: Active
> **Updated**: 2026-09-14
> **Design Source**: `./DESIGN.md`（差距对照的设计真相源，子设计见其 Sub-DESIGNs）
> **Companion**: 追踪 ontology 本体资产与 wopal-plugin 实现的目标态差距，逐项解决后关闭。

---

## About This Document

本文件是**过程文档**，不是长期设计文档——记录"当前实现"与"目标规范"的差距，作为规划 Plan 的输入。差距条目随实现收敛而移除；全部差距关闭后，本文件整体删除。

设计与规范的真相源是 `./DESIGN.md` 及其子设计。本文件不重复规范内容，只描述差距。

## Numbering

`ONT-G<n>` = 本体资产差距，`DOC-G<n>` = 文档与技能差距，`ASSEMBLY-G<n>` = 运行时装配差距（wopal-plugin 侧）。编号一经分配不复用、不重排。

wopal-plugin 随 ontology 分发，其实现差距归入本文档。

---

## Assembly Model

### ONT-G1: Assembly definition directory not established (P0)

**目标态**: 装配定义集中于 `.wopal/assembly/`，含 `archetypes/`（类型装配单）、`schemas/`（空间骨架）、`templates/`（渲染素材）；`config/` 只保留 settings 类配置。装配定义作为物化源头保留在中央仓库，不物化进空间。

**当前状态**: 装配单位于 `config/types/`，与 settings 混处；模板位于根目录 `templates/`；骨架内嵌于 `templates/wopalspace-schema.yaml`，未独立。

**落地**:
- 建立 `assembly/archetypes/`、`assembly/schemas/`、`assembly/templates/` 三级结构。
- 装配单从 `config/types/` 迁入 `assembly/archetypes/`。
- 骨架从 `templates/wopalspace-schema.yaml` 拆分，按类型独立为 `assembly/schemas/<type>-space-schema.yaml`。
- 模板迁入 `assembly/templates/`。

### ONT-G2: Manifest fields not aligned with design (P0)

**目标态**: 装配单声明五类可装配能力（`agents`、`skills`、`rules`、`commands`、`plugins`），`schema` 字段可省略并按约定取 `<type>-space-schema.yaml`。

**当前状态**: 装配单声明五类能力但缺 `schema` 字段；`config/types/` 下的装配单未包含骨架约定。

**落地**: 迁移后的装配单补齐 `schema` 约定说明；物化时按 `<type>-space-schema.yaml` 约定解析，显式 `schema` 字段优先。

### ONT-G3: Space structure not differentiated by type (P0)

**目标态**: 不同空间类型拥有不同骨架——coding 空间建立 `projects/`，content 空间建立 `contents/`，结构差异由装配单的 `schema` 选择。

**当前状态**: `wopalspace-schema.yaml` 硬编码 `projects/`、`contents/`、`docs/` 三个目录，所有空间物化为同一套布局。

**落地**: 按类型拆分骨架，`coding-space-schema.yaml` 声明 `projects/` 与 `docs/`，`content-space-schema.yaml` 声明 `contents/` 与 `docs/`。

---

## Capability System

### ONT-G4: Agent permission block contains wildcard keys (P1)

**目标态**: 角色权限块的键使用工具的真实标识，语义明确无歧义。

**当前状态**: fae / rook / evolver 的权限块使用 `wopal_*` 通配键覆盖插件工具。

**落地**: 待插件工具标识命名规范确立后统一调整。

### ONT-G5: `prompts/` not internalized into the plugin (P1)

**目标态**: 插件默认提示词内置于 wopal-plugin 源码，`prompts/` 退出 ontology 根目录；文件层保留为可选覆盖路径。

**当前状态**: `prompts/` 位于 ontology 根目录，含 `title.md`、`distill.md`、`dedup.md`、`commit-msg-gen.md`，由插件按多层路径加载。

**落地**: 默认值内化进插件源码，移除根目录 `prompts/`，保留文件覆盖机制。

### ONT-G6: tui-ellamaka plugin not normalized (P1)

**目标态**: `plugins/tui-ellamaka/` 为标准插件目录，含 `index.tsx`、`package.json`、`ellamaka-theme.json` 与 `asset/`；settings 以相对路径 `../plugins/tui-ellamaka` 引用。

**当前状态**: `plugins/tui-ellamaka.tsx` 为散落单文件（32KB），主题 `plugins/ellamaka-theme.json` 与音频资源 `plugins/asset/` 独立散落。

**落地**: 建立 `plugins/tui-ellamaka/` 目录，迁入插件、主题与资源；更新 settings 引用。`plugins/dsh-adapter` 保持纯文件插件。

### DOC-G1: space-master skill still describes the old model (P1)

**目标态**: `space-master` 技能的 ontology 维护指南对齐新模型（`space sync`、装配、`ontology capability list`、Evolver 回流），去除 type/* 分支与 contribute/promote 流程。

**当前状态**: `skills/space-master/SKILL.md`（13 处 type/* 引用）与 `references/ontology-maintenance.md`（5 处）仍描述 main → type/* → space/* 三层分支与 `space contribute` / `ontology promote`。

**落地**: 重写技能主体与维护参考文档，对齐新命令面与装配模型。

---

## Runtime Assembly (wopal-plugin)

### ASSEMBLY-G3: Arsenal scan and capability listing not implemented (P0)

**目标态**: 插件启动时扫描空间 worktree 构建武器库清单，通过 `wopal_capability_list` 提供给 Wopal；清单含未授予任何角色基线的能力，每项携带名称、描述与物理路径。

**当前状态**: 插件无武器库概念，无能力清单工具。技能与规则的物理清单只存在于各自模块的内部扫描结果中。

**落地**: 实现武器库扫描（技能、规则、MCP），构建清单结构；新增 `wopal_capability_list` 工具暴露清单。

### ASSEMBLY-G4: `wopal_task` lacks capability assembly parameters (P0)

**目标态**: `wopal_task` 接受 `capabilities` 参数（`skills` / `rules` / `mcp` 名称数组），派发时合成会话级权限并注入子会话，实现超越角色基线的运行时装配。

**当前状态**: `wopal_task` 只接受 `description` / `prompt` / `agent`。子会话创建后以 `promptAsync` 的 `tools` 参数传递工具开关。

**落地**: 新增 `capabilities` 参数；派发流程改为在会话创建后经会话更新接口注入合成权限；移除 `promptAsync` 的 `tools` 传参，避免其替换已注入的权限。

### ASSEMBLY-G5: Rule injection not assembled per session (P0)

**目标态**: 规则注入读取会话级装配结果，只注入该会话被授予的规则，并保持既有的提示词匹配与去重行为。

**当前状态**: 规则注入按角色名与提示词关键词匹配（`hooks/rule-injector.ts`、`rules/matcher.ts`），无会话级装配概念。

**落地**: 规则注入路径接入会话级装配结果，按授予范围过滤可用规则集，保留既有匹配与去重逻辑。

---

## Reference Documents

| 文档 | 说明 |
|------|------|
| `./DESIGN-assembly.md` | 装配模型设计 |
| `./DESIGN-capabilities.md` | 能力体系设计 |
| `./DESIGN-evolution.md` | 进化闭环设计 |
| `./DESIGN-wopal-plugin.md` | wopal-plugin 设计 |

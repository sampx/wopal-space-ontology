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

`ASSEMBLY-G<n>` = 运行时装配差距（wopal-plugin 侧）。编号一经分配不复用、不重排；已关闭的编号保持退役，使 Plan、Issue 与提交中的引用始终可解析。

wopal-plugin 随 ontology 分发，其实现差距归入本文档。

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

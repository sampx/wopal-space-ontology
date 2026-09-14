# GAPS — ontology Design vs Implementation Divergence

> **Status**: Active
> **Updated**: 2026-09-14
> **Design Source**: `./DESIGN.md`（差距对照的设计真相源，子设计见其 Sub-DESIGNs）
> **Companion**: 追踪 ontology 本体资产与 wopal-plugin 实现的目标态差距，逐项解决后关闭。

---

## Runtime Assembly (wopal-plugin)

### ASSEMBLY-G3: Arsenal scan and capability listing not implemented (P0)

**Current**: 插件无武器库概念，无能力清单工具。技能与规则的物理清单只存在于各自模块的内部扫描结果中。

**Target**: 插件启动时扫描空间 worktree 构建武器库清单，通过 `wopal_capability_list` 提供给 Wopal；清单含未授予任何角色基线的能力，每项携带名称、描述与物理路径。

**Design**: `./DESIGN-wopal-plugin.md` 的 Capability Assembly Module

**Exit**:
- [ ] 插件启动时扫描 `.wopal/skills/`、`.wopal/rules/` 与 MCP 服务声明
- [ ] 清单保留全部扫描结果，不做角色基线过滤
- [ ] `wopal_capability_list` 无参数返回技能、规则、MCP 三类清单
- [ ] 每项含名称、描述与物理路径

### ASSEMBLY-G4: `wopal_task` lacks capability assembly parameters (P0)

**Current**: `wopal_task` 只接受 `description` / `prompt` / `agent`。子会话创建后以 `promptAsync` 的 `tools` 参数传递工具开关。

**Target**: `wopal_task` 接受 `capabilities` 参数（`skills` / `rules` / `mcp` 名称数组），派发时合成会话级权限并注入子会话，实现超越角色基线的运行时装配。

**Design**: `./DESIGN-wopal-plugin.md` 的 Dispatch Assembly Contract 与 Assembly Injection

**Exit**:
- [ ] `wopal_task` 接受 `skills`、`rules`、`mcp` 三类名称数组
- [ ] 省略 `capabilities` 时装配结果与角色基线一致
- [ ] 装配参数只接受名称，插件构造权限规则
- [ ] 装配在会话创建时确定，上下文压缩后仍生效

### ASSEMBLY-G5: Rule injection not assembled per session (P0)

**Current**: 规则注入按角色名与提示词关键词匹配（`hooks/rule-injector.ts`、`rules/matcher.ts`），无会话级装配概念。

**Target**: 规则注入读取会话级装配结果，只注入该会话被授予的规则，并保持既有的提示词匹配与去重行为。

**Design**: `./DESIGN-wopal-plugin.md` 的 Rules Module 与 Assembly Injection

**Exit**:
- [ ] 未装配的规则不进入该会话系统提示词
- [ ] 系统提示词每轮重建时依既有会话权限重新渲染
- [ ] 保留既有的匹配与去重逻辑

---

## Reference Documents

| 文档 | 说明 |
|------|------|
| `./DESIGN-assembly.md` | 装配模型设计 |
| `./DESIGN-capabilities.md` | 能力体系设计 |
| `./DESIGN-evolution.md` | 进化闭环设计 |
| `./DESIGN-wopal-plugin.md` | wopal-plugin 设计 |

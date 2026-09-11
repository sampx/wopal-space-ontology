# ellamaka 能力 → dsh 工具映射表（评审草案）

> **Status**: Draft — 待评审
> **评审范围**: wopal / fae / rook 核心三角 + 能力类别主表
> **Updated**: 2026-09-03
> **评审后生效**: 成为「预设生成器」（见 poc DESIGN-dsh-poc.md 的「预设生成器」）把 ellamaka 定义翻译成 dsh 配置单的契约真相源
> **Language**: 中文（Sam 偏好；docs/ 不强制 i18n 拆分）

---

## 1. 背景与定位

ellamaka 的 Agent 定义（`.wopal/agents/*.md` 的 `permission:` frontmatter）与 dsh 的工具收窄（agent preset 的工具行集合）**词汇表、粒度、语义三者都不一致**，无法逐键机械翻译。本表是人工评审确定的「意图 → dsh 工具行」映射，是两套引擎之间唯一可靠的语言桥梁。

本表**不是** ellamaka 定义的运行时镜像，而是翻译契约。落成 dsh 配置单后独立演进，两边可不同——它们是不同引擎（见 D-10.2 精神）。

---

## 2. 核心事实：为什么不能机械翻译

| 维度 | ellamaka 侧 | dsh 侧 | 结论 |
|---|---|---|---|
| 词汇 | 能力类别键（read/edit/bash/mcp/skill） | 工具行 id（tool-fs/tool-bash/tool-skill…） | 无一对一键 |
| 粒度 | 有扩展名级（`edit: {"*.md": allow}`） | 只能到工具行级；扩展名过滤归 fs 策略层 | 粒度不匹配 |
| 语义 | allow/ask/deny = 执行拦截（工具可见） | 行不写 = 可见性收窄（从模型眼里消失、省 token） | 语义不同 |
| 特有键 | wopal_* / memory_manage / context_manage | 无对应物 | 只能丢弃或转注 |

因此翻译保留的是**每个 agent 的角色意图**，不是逐键。

---

## 3. 能力类别主表（意图 → dsh 工具行）

| ellamaka 能力类别 | ellamaka 值 | dsh 配置单表达 | 边界/例外 |
|---|---|---|---|
| `read` | allow | `tool-fs` + `tool-fs-search`（保留文件读与检索） | env/敏感文件的 deny 走 fs 策略层，不进 preset |
| `edit` | allow | 与 read 同由 `tool-fs` 提供（dsh 读写合一工具） | dsh 无独立的"写"工具行，edit 权限靠沙箱文件模式而非 preset |
| `edit: {"*.md": allow}` | 扩展名白名单 | **不映射**到 preset 行；改由 fs 策略/沙箱实现，或接受放行 | 需评审：见「待定边界」 |
| `bash` | allow | `tool-bash`（POSIX）/`tool-pwsh`（win32） | 平台互斥 |
| `mcp` | allow | dsh 的 MCP 工具按需单列 | 本轮核心三角不涉，见「范围外」 |
| `skill: {"*": allow}` | 全开 | 该 agent 挂载 `skill-filesystem` + `tool-skill`（技能目录不设限） | wopal 专属 |
| `skill: {名单: allow}` | 白名单 | 该 agent 挂 `skill-filesystem` 但 `customSkillDirs` 只指向名单技能目录（物理隔离） | rook 专属：只给 review 技能目录 |
| `skill: {"*": deny}` 单技能 allow | 全禁单放 | 同上，只挂单技能目录 | fae 专属：skill-creator |
| `question` / `ask` | allow | `tool-ask-user` | allow 才挂 |
| **技能白名单机制** | — | dsh **无**技能白名单字段，只有技能根目录；白名单靠 `skill-filesystem.customSkillDirs` 指向一个**只含目标技能子目录**的物理目录实现 | fae/rook 的 customSkillDirs 需额外物理隔离目录，是评审关注点 |
| `task`（委派） | allow | `tool-subagent` + `tool-subagent-fork` + `tool-workflow` + `tool-subagent-list-agents` | 编排者才挂 |
| `memory_manage` / `context_manage` / `wopal_*` | — | **无 dsh 对应物**：不映射，转为 dsh 原生技能目录/记忆机制，或丢弃 | 核心三角全部 deny，天然安全 |
| `plan_enter` / `plan_exit` | allow/deny | 挂/不挂 `plan-mode` 组 | fae 禁（plan_enter deny） |
| `doom_loop` / `sandbox_escalation` | — | dsh 无对等开关，由沙箱策略 / 审批层承接 | 不在 preset 声明 |
| `external_directory` | allow/deny | dsh 沙箱文件范围由 fs 策略承接 | 不在 preset 声明 |

---

## 4. 核心三角意图翻译

### 4.1 wopal — 全能编排者

**ellamaka 意图**: 万能巫师，理解意图、调动所有能力、委派协作，全能。permission 几乎无 deny（plan_exit/skill 全开/doom_loop 与 sandbox_escalation 为 ask）。

**persona = 灵魂全文复刻**：`.wopal/agents/wopal.md` 正文完整搬入 dsh persona（角色身份 + Soul/Role/Character/Mission + Conduct 全部 7 阶段 + Output Standards + Code Standards + 双模确认 CRITICAL_RULE）。仅裁剪 1 处，见「附录 A · persona 裁剪点」。

**dsh 配置单 = 近似 full 工具集**：`tool-fs` + `tool-fs-search` + `tool-bash` + `tool-skill`（技能目录不设限）+ `tool-ask-user` + `tool-todo` + `plan-mode` 组 + 委派组（`tool-subagent` + `tool-subagent-fork` + `tool-subagent-list-agents` + `tool-workflow`）+ `tool-goal`。

### 4.2 fae — 受限执行者

**ellamaka 意图**: 执行编码/重构/文件操作/构建测试的精灵，只收明确工作、返证据。不做规划/设计/审查。permission：deny wopal_*/task/memory/context/doom_loop/question/plan_enter，skill 只放 skill-creator，read 全开。

**persona = 灵魂全文复刻**：`.wopal/agents/fae.md` 正文完整搬入 persona（身份 + Role + Tone/Style + Professional Objectivity + Task Management + Tool Usage Strategy + Code References）。裁剪 2 处，见「附录 A · persona 裁剪点」。

**dsh 配置单 = 受限执行集**：`tool-fs` + `tool-fs-search` + `tool-bash` + `tool-skill`（`customSkillDirs` 只指向 skill-creator 目录）+ `tool-todo`。**不挂** `tool-ask-user`（question deny）、**不挂** `plan-mode`（plan_enter deny）、**不挂** 委派组（task deny）。

### 4.3 rook — 只读审查者

**ellamaka 意图**: 黑门乌鸦，只读审查，绝不执行/修复/规划。permission：deny wopal_*/task/memory/context/question，skill 只放 df-plan-review 与 df-implement-review，read 全开，bash allow（跑测试取证？——实际 body 有 READ_ONLY_BOUNDARY 禁写禁执行，但 bash allow 与 read-only 矛盾，见「待定边界」）。

**persona = 灵魂全文复刻**：`.wopal/agents/rook.md` 正文（Identity + Core Judgment Principles + Skill Routing + Tone + READ_ONLY_BOUNDARY）完整搬入 persona，零裁剪（见「附录 A · persona 裁剪点」）。

**dsh 配置单 = 只读审查集**：`tool-fs` + `tool-fs-search` + `tool-bash`（评审需读输出）+ `tool-skill`（`customSkillDirs` 指向 df-plan-review + df-implement-review 两技能目录）。**不挂** `tool-ask-user`（question deny）、**不挂** plan-mode 里的 exit 能力（如需 plan_enter 只读进场则可挂 plan-mode 但不授 exit，见待定）。fs 沙箱模式设为 read-only（禁写）落实 READ_ONLY_BOUNDARY。

---

## 5. 待定边界（需 Sam 裁决）

1. **扩展名级 edit 白名单**（`*.md` 允许、`*` 拒绝）在 dsh 里没有 preset 层对应，只能放 fs 沙箱文件模式。是否把「扩展名 → 沙箱可写模式」也纳入映射表？还是接受 dsh 的粗粒度、把细粒度留给 fs 策略？建议后者（dsh 语义本就到工具行级，细粒度是 fs 层职责）。
2. **rook 的 read-only**：ellamaka 用 body 里的 READ_ONLY_BOUNDARY（提示词约束）+ bash allow 并存，靠 agent 自觉。dsh 若真要"禁写"，应在 fs 沙箱层设 read-only 模式，而非只在 preset 层删工具。是否如此落实？
3. **data.md 及 architect/code-reviewer/code-skeptic 等专职 agent** 是否也纳入本轮映射？本轮范围只到核心三角，专职 agent 多为 WSF 工作流内部角色，建议 defer。
4. **灵魂全文复刻的 token 成本**：wopal 灵魂全文约 9.5k 字符、fae 3.7k、rook 4.6k。全文进 persona（system prompt）每轮都占上下文。dsh 允许 persona 设 `complete: true`（视为完整系统提示词、不追加全局身份）或仅保留核心段。权衡：完整复刻保真 vs 上下文成本。建议 wopal/fae/rook 作为「角色化」独立 agent 可接受全文（它们不是常驻主会话），但需确认——见附录 A 设计原则。

---

## 6. 范围外（本轮不映射）

- MCP 工具按需单列（dsh MCP 机制另行评审）
- 24 个 WSF 子代理（由 space-flow 分发，非本轮）
- doom_loop / sandbox_escalation / external_directory：由 dsh 沙箱与审批层承接，不写进 preset

---

## 7. 结论与下一步

映射表把「不可行的机械转换」替换为「可行的意图翻译」。它固化了 wopal / fae / rook 三个 dsh 配置单的表达方式。persona 采用**灵魂全文复刻**，工具行采用**意图裁剪**。**评审通过后**，本表成为「预设生成器」的契约真相源，并把第 4 节的三个配置单样例落为 dsh 可运行的 user preset（D-10.2：`presets/` 是机器生成的可复现产物）。

---

## 附录 A · persona 裁剪点（需 Sam 核对每一项是否合理）

dsh 的 persona 不是概括，而是把 `.wopal/agents/*.md` 的灵魂正文**几乎完整**搬过去。仅当某句提到 ellamaka 特有、dsh 不存在的东西时才裁剪，裁剪处用 `[CSS-x]` 在配置单里标出。汇总：

| agent | CSS-id | 原文要点 | 为何裁剪 | 改法 |
|---|---|---|---|---|
| wopal | CSS-1 | Phase 7: `memory_manage command=search` | dsh 无 memory_manage 工具 | 改成「主动召回记忆/空间上下文」原则表述 |
| fae | CSS-1 | 两处 "Prefer Task tool for file searches" | fae task=deny 无委派；dsh 无 Task 工具 | 改用文件搜索工具替代 |
| fae | CSS-2 | "When WebFetch redirects, retry with redirect URL" | fae 无 web 工具 | 删除该句 |
| rook | — | — | 全文与 dsh 兼容 | 零裁剪 |

> 设计原则：**只在 "该句指向的工具 dsh 确实没有" 时才裁剪**；纯粹的能力差异（如 dsh 有 web 搜索而 rook 不该用）一律靠工具行取舍解决，不动 persona 文字。若你认为某处裁剪过度或不够，直接指出 CSS-id 即可改回。

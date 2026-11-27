# Proposal 生命周期与字段契约

技能入口文件给出状态机骨架；本文件补齐每一步的完整字段、迁移清单与判定细则。需要具体操作时读这里。

## 1. 根目录与归属

Proposal 属于**一个**归属地，二选一：

| 归属 | 根目录 | 适用 |
|---|---|---|
| 产品级 | `docs/products/{product}/proposals/` | 决定影响整个产品的定位、能力边界或多项目共同约定 |
| 项目级 | `projects/{project}/docs/proposals/` | 决定只影响单个项目或其中若干模块 |

一项决定只有一个归属。跨项目但边界清楚的决定，写进主导项目的 `proposals/`，其他项目用相对链接引用。不要在两处各写一份。

本体能力进化提案不在此列，位于本体仓库 `docs/evolutions/`，由 `ontology-evolution` 拥有。

## 2. 路径

```text
<proposals-root>/{lifecycle}/{class}/yyyy-mm-dd-<slug>.md
```

- `lifecycle ∈ {proposed, implemented, rejected, archived}`
- `class ∈ {feature, bug-fix, simplification, architecture, process, testing}`
- 日期取**首次提出日**，迁移与归档都不改文件名。
- slug 小写 kebab-case，2–4 个词，描述决定本身而不是文件类型。
- 文件名不允许带状态或版本后缀（`-v2`、`-approved`、`-final` 都不行）。

### 禁止项

| 禁止 | 原因 |
|---|---|
| 单数 `proposal/` 目录 | 与 `proposals/` 并存会造成两个真相源 |
| 未知分类目录（`refactor/`、`misc/`、`other/`） | 分类靠闭集强制，自创分类让检索失效 |
| 集中 `INDEX.md` | 它与路径重复，且所有无关改动争抢同一文件 |
| 中英 `.i18n.yaml` 三元组配对 | 本空间不做双语配对；一份决定一种语言 |
| `archived/implemented/` 深层 | 只有已实施记录能归档，层级已隐含 |

存量前格式文件保持历史只读兼容：可以读、可以引用、可以复制其结构，但不要为了"统一格式"去改写它，也不要把它当作本次校验的失败项。

## 3. 文件头

```markdown
# <标题>

Status: proposed

- **Class**: architecture
- **Created**: 2026-11-22
- **Updated**: 2026-11-22
```

`Status` 必须在第一处正文之前单独成行，前缀就是 `Status: `，且一个文件只能有一条：两条状态行是对同一份记录的两个互斥主张，校验器直接拒绝。校验器按这一行判定生命周期与目录是否一致。`Class` 与 `Created` 是每个格式化文件的必填身份字段——没有 `Class`，「分类与目录是否一致」就无从比较；`Created` 是这个主题首次提出的日期。

### 各状态允许的取值

| 目录 | 允许的 `Status` |
|---|---|
| `proposed/` | `proposed`、`approved` |
| `implemented/` | `implemented` |
| `rejected/` | `rejected — <一行理由>` |
| `archived/` | `implemented`（另需 `Archived: YYYY-MM-DD`） |

`archived/` 中的记录**不要求**重写为 `Status: archived`：归档只加一行日期，正文与状态原样冻结。

### 批准字段

`Status: approved` 的文件必须有下面三条，缺一条就是未授权：

```markdown
- **Approved**: 2026-11-22 — <批准人>
- **Authorized scope**: <批准范围，含明确排除项>
- **Delivery**: direct
```

- `Approved`：日期 + 批准人，写作 `YYYY-MM-DD — <批准人>`，写清是谁拍的板。像日期但不是真实日历日期的值，或者没有署名的批准，都过不了检查。
- `Authorized scope`：一句话，能回答"批准了什么、没批准什么"。写"全部"而没有边界，等于没有范围。
- `Delivery`：只能取 `direct` 或 `plan`，且必须是用户的选择。

脚本能校验这三条存在且格式正确，但**校验通过不等于有人真的批准过**。审批是人的动作，Agent 不得代填。

### 归档字段

```markdown
Status: implemented
Archived: 2026-11-22
```

`Archived` 紧贴 `Status: implemented` 的下一行，格式固定 `YYYY-MM-DD`。这是归档时唯一允许写入的内容。

## 4. 正文骨架

### `proposed/`（含 `approved`）— 目标态

必填章节，顺序固定：

```markdown
## Problem
## Proposal
…（0..N 个专属章节）…
## Alternatives considered
## Acceptance criteria
## Risks
```

- `## Problem`：为什么现在要做这件事。要能脱离方案独立成立——读者看完就知道痛点，不必先读 `## Proposal`。
- `## Proposal`：用用户偏好语言、正向肯定式的目标态描述选定行为与边界；批准前解决待定决策。
- `## Alternatives considered`：真实考虑过的其它路径与它们失败的原因。
- `## Acceptance criteria`：什么可观察状态算完成。每条都要能被第三方判断达成或未达成。
- `## Risks`：可能出的问题，以及这次明知放弃的东西。

专属章节按需插入在 `## Proposal` 与 `## Alternatives considered` 之间，例如接口契约、数据迁移、分阶段策略。

### `implemented/` — 现在时

必填章节，顺序固定：

```markdown
## Problem
## Decision
…（0..N 个专属章节）…
## Alternatives considered
## Consequences
```

禁用章节（出现即为格式错误）：

- `## Proposal`
- `## Plan`
- `## Migration plan`
- `## Acceptance criteria`

理由：这些是计划期词汇。已实施记录描述的是现在的系统，不是当初的计划。原 `## Acceptance criteria` 与 `## Risks` 的内容合并进 `## Consequences`——写清这套决定最终换来了什么、付出了什么。

### `rejected/`

保留提议期的章节结构（可以有 `## Acceptance criteria`、`## Plan`），结论只写在状态行。若这份否决理由要长期留存，正文应说明"当初为什么诱人、为什么最终不成立"。

### `archived/`

保留归档那一刻的正文与章节，只加 `Archived` 行。冻结之后不再要求满足任何活跃骨架规则，也不再抽查它的出链。

### `## Alternatives considered` 的硬要求

四种生命周期都要有这一节。它存在的意义是：一项决定如果没写下被否掉的路径，将来一定会有人重新提一遍。

写法要求：

- 每条一行起头，加粗写方案名，后接为什么输；
- 只记录**真实发生过**的备选讨论，不编造；
- 早于本格式的存量文件不追溯补写，可保留原样。

## 5. 迁移清单

### `proposed` → `approved`

1. 确认用户已明确同意，并明确同意了什么范围。
2. 追加 `Approved`、`Authorized scope`、`Delivery`。
3. `Status` 改为 `approved`。
4. **文件位置不变**，仍在 `proposed/<class>/`。
5. **创建交付分支或工作树前，先提交已批准的 Proposal**：在集成分支上提交，让它进入交付基线。

留在 `proposed/` 是刻意的：实施期内 Plan 与其他关联提案都指向原路径，搬走就会断链。注意：现状 `DESIGN.md` / `DESIGN-<module>.md`（含 `## Reference Documents`）严禁在 `proposed/` 或 `rejected/` 期间反向链接该提案——只有迁入 `implemented/`（或封存 `archived/`）后才由现状 DESIGN 链接。

### 验收前维护 `approved` 提案

以 SKILL.md 的验收前维护规则为准。用户明确授权的新决定优先在代码调整前融入当前提案；同步授权范围、设计、验收标准及受影响的备选和风险，保持路径、状态、基线不变。原地替换失效内容，不追加过程记录。自动实施不得自行改变授权。

### `approved` → `implemented`

前提：批准范围**全部**交付，且用户已验收放行。

1. 移动到 `implemented/<class>/`，文件名不变。
2. `Status` 改为 `implemented`。
3. 同一次改动内改写骨架：`## Proposal` → `## Decision`；`## Acceptance criteria` 与 `## Risks` 合并进 `## Consequences`，删除计划期标题。
4. 正文转现在时，删掉"计划""待定""v1 先这样"这类计划期表述。
5. 同交付同步受影响的现状 DESIGN（`DESIGN.md` / `DESIGN-<module>.md`），补上 `## Key Decisions` 的相对链接。
6. 修好所有指向旧路径的入链。

部分交付不执行本迁移：留在 `proposed/`，`Status: approved`，用交付证据说明已完成哪部分。

### `proposed` / `approved` → `rejected`

先判断留存价值：

- **留**：这份否决能防止将来有人再犯同样有诱惑力的错误 → 移到 `rejected/<class>/`，`Status: rejected — <一行理由>`。
- **删**：想法已过时、被后续决定吸收、或明显不会再被提 → 整份删除，并修好所有入链。

### `implemented` → `archived`

前提：已完成使命，且不再指导日常工作。

1. 移动到 `archived/<class>/`（不再有 `implemented` 层）。
2. `Status: implemented` 下一行插入 `Archived: YYYY-MM-DD`。
3. 除此之外**不改正文**：不翻译、不重排、不更新事实、不修出链。
4. 修复或删除活跃文档中指向它的入链。活跃文本可以有意引用归档记录作为历史背景，但不要把归档当现状权威。

微小的 UI 调整或纯机械变更**不归档**，直接删除并修好入链。归档不是垃圾桶。

### `implemented` → 删除

仅当整个决定已被新提案完全吸收，且所有独特理由、备选方案、代价、验证方式与遗留缺口都已迁入新提案、所有入链已修好时执行。删除前逐项核对，不要以"Git 历史还有"作为唯一备份。

## 6. 入链维护

每次移动、改名、删除都要扫入链：

```bash
rg -n "<旧文件名或旧路径片段>" <文档根目录>

# 再让校验器把这些引用文件一起检查
python3 scripts/verify-proposals.py <proposals-root> --link-scope <文档根目录>
```

处置三种情况：

1. 指向现状文档的链接——改到新路径；
2. 指向历史引用的链接——改到 `archived/` 路径，或删掉；
3. 指向 Proposal 内部互链的——同批修复。

校验器会扫描非冻结目录内的相对出链与本目录内的本地入链。传 `--link-scope <docs-dir>` 可把引用 Proposal 的外部文档一并纳入检查，可重复传多个目录；这样移动或删除文件时，断链在调用方就会被发现，而不是等人偶然读到。归档记录双向都不查出链，跨仓库引用仍靠人工核对。

## 7. 校验器边界

`scripts/verify-proposals.py` 只做**单快照静态确定性检查**：

- 目录与六类闭集、路径命名（日期须为真实日历日期）、禁 `proposal/` 与 `INDEX.md`；
- 从父目录入口调用时，同时拒绝与 `proposals/` 并存的单数 `proposal/`；
- 路径 `{lifecycle}` 与文件头 `Status` 一致，且文件头只有一条状态行；
- 每个格式化文件的身份字段（`Class`、`Created`）及其取值；
- 骨架必填章节与禁用章节；
- `Status: approved` 的三条授权字段、`Approved` 的真实日期与批准人、`Delivery` 取值；
- `archived/` 的 `Status: implemented` 与紧贴其下一行的 `Archived: YYYY-MM-DD`，不查其出链；
- 非冻结目录的相对出链可达、无本地绝对路径（HTTP(S) URL 里的路径段不算本地路径）、本地入链不断链。

它**不**做：历史数据库、冻结内容哈希清单、Git 历史回退比对、跨仓库全量扫描。跨提交的状态回退（例如曾为 `implemented/` 的文件被移回 `proposed/`）与归档正文篡改，靠 Agent 规则与正常评审把关。

文件名 slug 词数与章节顺序属于写作约定，不是结构不变量：脚本只查章节是否存在，不查形状。

直接躺在树根、不属于任何生命周期目录的 Markdown 会按 `outside-lifecycle-layout` 报为跳过，而不是被静默忽略。

既无 `Status:` 行也无 `**Class**` 字段的文件按前格式处理：报为跳过，不做判定。项目完成迁移后可用 `--strict` 把这类文件的存在变成失败。

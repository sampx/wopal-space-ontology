# enhance-ontology-evolution

## Metadata

- **Type**: enhance
- **Project Path**: .wopal
- **Created**: 2026-10-28
- **Stage**: archived
- **Mode**: quick
- **Worktree**: (none)
- **Branch**: (none)
- **Base Commit**: (none)
- **Final Commit**: (none)

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

把 ontology-evolution 从“提案撰写 + 落地”扩展为 Wopal 与 Maka 的持续进化协作流程，使真实会话中的批评、失败和摩擦先被低干扰地观察、诊断与归类，只有成熟信号才在会话收尾时形成提案。

## Technical Context

### Architecture Context

现有设计已经规定 Maka 负责从会话错误、用户纠偏和经验中形成提案，但缺少会话内持续观察、信号积累、延迟汇总，以及“问题应落到哪种能力组件”的路由协议。`docs/DESIGN-evolution.md` 与 `skills/ontology-evolution/SKILL.md` 是该流程的设计与执行真相源。

### Research Findings

WopalSpace 产品设计已经定义 Skill、Rule、Agent、Plugin、Assembly、Memory/AGENTS 等组件的职责。Maka 不需要每次重读完整产品设计；应在技能正文保留精简路由表，在详细 reference 中保留边界与误判规则，只有能力架构本身存在歧义时才回查 DESIGN。

**References**:
- `docs/DESIGN-evolution.md`
- `../docs/products/wopal-space/DESIGN.md`

### Key Decisions

- D-01: 会话内按需创建并复用一个 Maka 子线程；Wopal 继续主任务，不等待或向用户暴露 Maka 的中间分析。
- D-02: Maka 观察期只积累并分类信号，不创建提案；只有 Wopal 明确发出 synthesis 时才合并证据并决定是否写提案。
- D-03: 信号分为 discard / local / candidate / mature；成熟不等于立即落盘。
- D-04: ontology-evolution 正文内置精简能力路由地图，详细组件边界放 `references/capability-routing.md`；产品 DESIGN 只在架构归属不清时按需读取。

### Key Interfaces

N/A。此次只调整 Agent 执行协议与文档能力，不改变 `wopal space evo` CLI 契约或状态机。

## In Scope

- 扩展 ontology-evolution 的观察、诊断、路由、汇总阶段，并保持现有 Proposal → Landing 生命周期不变。
- 增加能力组件路由 reference，并保持中英文语义一致。
- 同步 `docs/DESIGN-evolution.md`。

## Out of Scope

- 不修改 `wopal space evo` CLI、状态机或持久化机制。
- 不增加常驻后台进程；Maka 仍是 Codex 可复用的子 Agent 线程。
- 不改变 Fae 的实施职责。

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| evolution skill | `skills/ontology-evolution/SKILL.zh-CN.md`, `skills/ontology-evolution/SKILL.md` | modify | 完整协作协议 |
| routing reference | `skills/ontology-evolution/references/capability-routing.zh-CN.md`, `skills/ontology-evolution/references/capability-routing.md` | create | 能力组件职责与路由 |
| landing / maintenance references | `skills/ontology-evolution/references/landing*.md`, `skills/ontology-evolution/references/maintenance*.md`, `skills/ontology-evolution/references/commands.md` | create / modify | 将落地、命令与维护细节从主 Skill 下沉，保持 progressive disclosure |
| design | `docs/DESIGN-evolution.md` | modify | 设计真相源同步 |

## Assembly Intent

| Ref | Scope | 理由 |
|-----|-------|------|

## Acceptance Criteria

### Agent Verification

1. [x] SKILL 明确定义观察期与 synthesis 期，并规定 Wopal 不因 Maka 中间分析阻塞主任务。— `rg -n "Observation|Synthesis|观察|汇总" skills/ontology-evolution/SKILL*.md`
2. [x] SKILL 能将常见问题路由到 Agent / Rule / Skill / Plugin / Assembly / space-private，并要求优先修正已有 owner。— `rg -n "Capability routing|能力路由|existing capability owner|已有能力" skills/ontology-evolution/SKILL*.md`
3. [x] 详细路由 reference 可独立解释各能力组件职责、边界与何时回查 DESIGN。— `rg -n "Component responsibilities|组件职责|When DESIGN|什么时候必须回查" skills/ontology-evolution/references/capability-routing*.md`
4. [x] 中英文 SKILL 与 routing reference 语义一致，DESIGN 与 Skill 不冲突。— `git -C .wopal diff --check` + `wopal space evo check enhance-ontology-evolution`
5. [x] SKILL description 直接、强触发；主正文控制在 250 行以内，落地与维护细节通过 references 按需加载。— `wc -l skills/ontology-evolution/SKILL*.md` + reference link check

### User Validation

#### Scenario 1: 会话内持续进化协作
- Goal: 验证 Wopal 在真实批评或重复摩擦发生时按需复用 Maka，主任务不被中间分析打断，并在会话收尾时统一 synthesis。
- Environment: 新 Codex 会话
- Precondition: 重新启动/新建会话以加载最新提示词与 skill。
- Launch command: N/A
- User Actions:
  1. 在一次任务中对 Wopal 给出一次有复用价值的纠正，再继续完成主任务。
  2. 会话收尾时要求结束或总结。
- Pass criteria: Wopal 主流程不中断；Maka 不因单次信号立即产出提案；收尾时才汇总成熟信号，弱信号允许无提案结束。
- Failure feedback: 提供 Wopal/Maka 的实际行为与偏差。

- [x] The user has validated/accepted the behavior and explicitly authorized upstream contribution. Current-session evidence: a reusable correction about merged-PR closeout was routed back to the owning ontology-evolution capability, audited as a workflow gap, repaired through the instant defect path, and the primary contribution task continued. This environment had no usable Maka sub-agent, so validation exercised the Skill's documented no-sub-agent fallback rather than pretending a Maka thread ran.

## Implementation

### Task 1: 建立持续进化协作协议与能力路由

**Verification Intent**: 1, 2, 3, 4

**Behavior**:
- 当会话出现可复用的能力问题信号时，Wopal 可把证据交给可复用 Maka 子线程；Maka 观察期只分析积累，synthesis 时才生成成熟提案，并按能力职责选择正确 owner。

**Pre-read**: `docs/DESIGN-evolution.md`, `skills/ontology-evolution/SKILL.md`, `../docs/products/wopal-space/DESIGN.md`

**Design**: 保持现有 landing 状态机不变，在前端新增 Observe → Diagnose → Route → Synthesize；正文放短路由表，详细职责放 reference；Codex prompt 只放触发器。

**TDD**: false

**Changes**:
1. 更新中英文 skill 与 routing reference。
2. 同步 DESIGN-evolution。

**Verify**: 文本一致性检查 + `wopal space evo check enhance-ontology-evolution`

**Done**:
Task output: ontology-evolution 已扩展为 Observe → Diagnose → Route → Synthesize → Proposal → Landing；description 改为强触发；主 Skill 精简为决策与主流程，落地、命令和维护细节按需下沉到 references；中英文保持同步。
Files touched: `docs/DESIGN-evolution.md`; `skills/ontology-evolution/AGENTS.md`; `skills/ontology-evolution/AGENTS.zh-CN.md`; `skills/ontology-evolution/SKILL.md`; `skills/ontology-evolution/SKILL.zh-CN.md`; `skills/ontology-evolution/references/capability-routing.md`; `skills/ontology-evolution/references/capability-routing.zh-CN.md`; `skills/ontology-evolution/references/landing.md`; `skills/ontology-evolution/references/landing.zh-CN.md`; `skills/ontology-evolution/references/maintenance.md`; `skills/ontology-evolution/references/maintenance.zh-CN.md`; `skills/ontology-evolution/references/commands.md`; `docs/evolutions/enhance-ontology-evolution.md`
- [x] The implementation agent has completed all development and verification steps above.

**Implementation Review**: PASS（Blocker 0 / Warning 0）。按 `df-implement-review` 的 Delivery review 对 `7b8a513..02c0b9e` 检查 Q1–Q4：主 Skill 中英文均 189 行并保持强触发 description；Observation / Synthesis / capability routing 与 `docs/DESIGN-evolution.md` 一致；Agent / Rule / Skill / Plugin / Assembly / space-private 路由齐全；新增 capability-routing / landing / maintenance references 均由主 Skill 引用且文件存在，无 orphan；`references/commands.md` 未改变 CLI 契约，只把 landing 细节改为 reference 路由；stub / broken-link 扫描 clean；`wopal space evo check enhance-ontology-evolution` 为 OK。

---

## Delivery

`space sync` and native Git/GitHub PR publication are the user's call — the skill never uploads on its own.

## Delegation Strategy

单一文档能力演进任务；当前环境无可用本体实施子 Agent，按已批准范围直接完成并做一致性验证。

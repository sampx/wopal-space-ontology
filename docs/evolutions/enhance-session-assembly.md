# enhance-session-assembly

## Metadata

- **Type**: enhance
- **Project Path**: .wopal
- **Created**: 2026-09-27
- **Updated**: 2026-10-08
- **Stage**: draft
- **Mode**: (accept 时记录：isolated | quick)
- **Worktree**: (accept 时记录)
- **Branch**: (accept 时记录)
- **Base Commit**: (accept 时记录)
- **Final Commit**: (integrate 时记录：集成到空间分支后的提交)

## Scope Assessment

- **Complexity**: High
- **Confidence**: High — Session Assembly 的总体边界已经收敛；进一步研究确认 Skill、Tool、Rule 三类能力的运行时语义不同，应拆成三个独立 Evolution Proposal 分别设计、评审和实施。

## Goal

定义 Wopal Session Assembly 的总体目标、共同约束与交付拆分：主 Agent 根据具体任务，为主会话或受管子会话叠加所需能力，同时将 Skill、Tool、Rule 分成三个独立 Evolution Proposal 分别演进。

## Technical Context

### Architecture Context

WopalSpace 已经有三层稳定事实：空间物化后的能力池、Agent 的角色默认能力，以及 Session 的运行态。Stage 2 要补的是第四层：主 Agent 根据任务，把角色默认能力之外的能力叠加到具体 Session。

原提案把 Skill、Tool、Rule 放在同一个交付里，并试图用一套 Session Capability Envelope 同时解释能力发现、授权、模型可见性和上下文注入。进一步研究后确认三类能力生命周期不同：

- Skill 是“能力目录 + 按需加载正文/资源”，动态选择不等于动态改 Tool schema；
- Tool 涉及模型 tool schema、执行入口、MCP/DSH scope 与授权，缓存和安全边界与 Skill 不同；
- Rule 是运行时指导上下文，核心问题是匹配时机、事实来源和 request-tail 注入，不等同于执行权限。

因此本提案不再承担三个能力域的实现细节，而成为 Session Assembly 的 umbrella proposal。三个子提案共享总体原则，但各自拥有独立接口、验收标准和实施生命周期。

权威设计参考：

- `docs/DESIGN-capabilities.md`
- `docs/DESIGN-wopal-plugin.md`
- Ellamaka `docs/DESIGN.md` 的 Capability Discovery、Session Capability Contract、Runtime Context Contribution

### Research Findings

1. Ellamaka discovery 适合作为“引擎当前加载了什么”的能力池来源，Wopal 不需要为 Skill/Tool/Rule 再建第二套 registry。
2. Agent frontmatter/config 是角色默认能力；任务装配应叠加在 baseline 之上，而不是改写角色定义。
3. 动态能力不应为了统一接口而强迫使用同一种运行时机制。Skill、Tool、Rule 可以共享 Session Assembly 概念，但其模型可见性、授权和恢复方式应由各自子提案定义。
4. Prompt prefix cache 是共同约束：动态变化应尽量发生在稳定 system/tool prefix 之后，不能为了运行时装配频繁重写 system prompt。
5. 已有 Ellamaka/Wopal-plugin 扩展点优先复用。只有现有 seam 无法表达且确属通用引擎能力时，才增加最小的 Ellamaka core/plugin SDK 扩展。

### Key Decisions

- D-01: `enhance-session-assembly` 是 umbrella proposal，只定义 Session Assembly 总体目标、共同不变量和子提案关系，不直接实施 Skill/Tool/Rule。
- D-02: Session Assembly 拆成三个独立 Evolution Proposal：Skill、Tool、Rule。每个子提案独立经历 draft → accepted → implementing → validating → archived。
- D-03: Skill 子提案为 `enhance-session-skill`，当前优先推进；Tool 与 Rule 子提案在设计成熟后再创建，本提案不提前锁定其最终接口。
- D-04: Ellamaka discovery 是运行时能力池的权威来源。Wopal 可以做任务级选择和装配，但不复制引擎 registry 或完整 permission evaluator。
- D-05: Agent 配置是 baseline，Session Assembly 是 additive overlay。是否支持 revoke/subtract/exact-set 由各子提案单独论证，不能从一个能力域外推到另一个能力域。
- D-06: 动态装配必须保护稳定 prompt prefix。运行时变化不得无必要地改写 system prompt；是否影响 tool schema、使用 request-tail 或其他 scope，由各子提案根据能力特性决定。
- D-07: 模型“看得到能力”和“实际能使用能力”必须来自同一 Session 事实源。每个子提案都必须证明可见性与执行/加载边界不会形成双真相源。
- D-08: Session metadata 可以承载 wopal-plugin 私有装配事实；SessionStore/cache 只能是派生状态，不能成为恢复后的唯一授权事实。
- D-09: 主 Agent 可以为主会话或受管子会话做任务级能力选择；获得某项能力不会自动授予派发、沙箱、文件写入或其他无关能力。
- D-10: 安全上限仍由引擎、沙箱和 profile 等硬边界拥有。Session Assembly 不能通过业务层 overlay 绕过不可提升的执行边界。
- D-11: Skill/Tool/Rule 子提案必须小步交付。一个子提案完成不能解释为其他两类能力已经获得相同动态语义。
- D-12: 本 umbrella 保持 `draft`，作为 Stage 2 编排真相源；它本身不创建实施 worktree。三个子提案独立交付后，再由用户决定 umbrella 的归档方式。

### Key Interfaces

本 umbrella 只保留概念级入口，不冻结三个能力域的最终 wire contract：

```ts
wopal_task({
  ...,
  capabilities?: {
    skills?: string[]
    tools?: unknown // final shape belongs to Tool child proposal
    rules?: unknown // final shape belongs to Rule child proposal
  }
})
```

共同语义：

- 省略某能力类别表示不增加该类别的任务级 overlay；角色 baseline 继续生效。
- 名称必须来自对应引擎 discovery/物化能力池；未知能力不能靠插件猜测或临时安装来补齐。
- 子提案可以增加独立的运行时控制面，但必须明确 Session target、持久状态、恢复语义和权限边界。
- 上述接口仅表达 umbrella 方向；Tool/Rule 子提案有权在保持总体语义的前提下定义自己的最终字段和错误模型。

## Child Evolutions

| Capability | Proposal | Status | Responsibility |
|------------|----------|--------|----------------|
| Skill | `docs/evolutions/enhance-session-skill.md` | draft | Skill Pool → Session Skill Overlay → request-tail catalog → native `skill(name)` loading；创建时与运行时增量 grant |
| Tool | 待拆分 | not created | Tool/MCP/DSH scope、schema visibility、runtime grant 与执行授权；另行设计 |
| Rule | 待拆分 | not created | Rule eligibility、runtime matching、tool/path facts 与 request-tail snapshot；另行设计 |

Skill 子提案的直接引擎前置为 Ellamaka `feature-plugin-runtime-perm-hook`：它只提供通用 per-ask permission rules seam，不属于 ontology 子提案本身。

## In Scope

- 定义 Session Assembly 的四层关系：能力池、Agent baseline、Session additive overlay、各能力域自己的 runtime activation/loading。
- 将 Skill、Tool、Rule 从单一大实施提案拆成三个独立 Evolution Proposal。
- 固化三个子提案共同遵守的 discovery、单一事实源、恢复、安全边界和 prompt-cache 原则。
- 记录子提案之间及其引擎前置的交付关系。

## Out of Scope

- Skill 的字段、grant tool、permission hook 消费、catalog 格式与生命周期实现；由 `enhance-session-skill` 定义。
- Tool/MCP/DSH runtime scope、Tool schema 动态变化、tool permission mapping；等待 Tool 子提案。
- Rule tool/path matching、eligibility、snapshot 格式与恢复事实；等待 Rule 子提案。
- 在 umbrella 中直接修改 wopal-plugin、Agent、Rule、Skill 或 Ellamaka runtime 代码。
- 提前 accept/implement umbrella；当前只作为 Stage 2 设计编排与子提案索引。

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| Umbrella proposal | `docs/evolutions/enhance-session-assembly.md` | modify | Session Assembly 总设计、拆分和交付关系 |
| Skill child proposal | `docs/evolutions/enhance-session-skill.md` | create | Skill 动态装配独立设计与实施契约 |
| Capability design | `docs/DESIGN-capabilities.md` | reference / later sync | 保持总体装配概念一致 |
| Plugin design | `docs/DESIGN-wopal-plugin.md` | reference / later sync | 各子提案实施时保持插件边界一致 |

## Assembly Intent

| Ref | Scope | 理由 |
|-----|-------|------|

本次拆分只新增设计文档，不新增需要 assembly registration 的 capability asset。

## Acceptance Criteria

### Agent Verification

1. [ ] umbrella 只保留 Session Assembly 的共同原则和三类子演进关系，不再包含可直接实施的 Skill/Tool/Rule 混合细节或混合 AC。
2. [ ] Skill 子提案独立存在并承载当前已定型的 Skill Pool、Session Skill Overlay、原生 loader、runtime permission overlay、恢复和验收契约。
3. [ ] Tool/Rule 在 umbrella 中只保留边界与待拆分状态，没有被 Skill 子提案或现有 Ellamaka hook 提前锁定实现。
4. [ ] `docs/DESIGN-capabilities.md`、`docs/DESIGN-wopal-plugin.md` 与本 umbrella/Skill 子提案不存在“整个 Session capability envelope 必须生命周期冻结”等已废弃冲突描述。
5. [ ] P2 交付 DAG 能表达 Ellamaka runtime permission hook → Skill 子提案的前置关系，且不把 ontology Skill 工作表示为普通 dev-flow Plan。

### User Validation

#### Scenario 1: Stage 2 拆分可读性确认

- Goal: 确认 Session Assembly 总设计与 Skill/Tool/Rule 子演进边界符合产品意图。
- Environment: 直接阅读 `.wopal/docs/evolutions/` 中 umbrella 与 Skill 子提案。
- Precondition: umbrella 与 `enhance-session-skill` 均处于 `draft`，未创建 implementation worktree。
- Launch command: `sed -n '1,260p' .wopal/docs/evolutions/enhance-session-assembly.md && sed -n '1,360p' .wopal/docs/evolutions/enhance-session-skill.md`
- User Actions:
  1. 确认 umbrella 只解释总目标、共同原则与三块拆分。
  2. 确认 Skill 的具体动态注入设计只存在于 Skill 子提案。
  3. 确认 Tool/Rule 仍标记为待独立设计，没有被本次 Skill 方案顺带实现。
- Pass criteria: 两份提案职责不重叠；Skill 能独立进入评审/实施；Tool/Rule 可在未来不改写 Skill 方案的情况下继续拆分。
- Failure feedback: 指出冲突章节或需要保留/下沉的具体条目。

- [ ] The user has validated the behavior above and confirmed the result.

## Implementation

本 umbrella 不直接进入 capability implementation，也不创建 isolation worktree。它维护三个子演进的编排关系：

### Child 1: Session Skill

**Proposal**: `enhance-session-skill`

**Status**: draft — 当前已拆分，等待独立评审/批准。

### Child 2: Session Tool

**Proposal**: 待创建。

**Entry condition**: DSH/Tool 动态装配设计完成并与 Ellamaka runtime/tool schema 边界收敛后，再建立独立 Evolution Proposal。

### Child 3: Session Rule

**Proposal**: 待创建。

**Entry condition**: Rule runtime matching、tool/path facts 与 request-tail 生命周期重新独立评审后，再建立独立 Evolution Proposal。

## Delegation Strategy

N/A — umbrella 不直接实施；每个子 Evolution Proposal 自己定义实施波次、评审和用户交付门禁。

## Delivery

- `enhance-session-assembly` 保持 `draft`，作为 Stage 2 Session Assembly 的 umbrella/index。
- 每个子提案独立 accept、implement、review、validate、archive。
- Skill 子提案完成不自动推进 Tool/Rule，也不自动归档 umbrella。
- 三个子提案全部完成后，由用户决定 umbrella 是归档为设计索引，还是继续承载后续 Session Assembly 扩展。
- `space sync` 和 `ontology contribute` 仍由用户单独决定，不自动执行。

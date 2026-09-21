# enhance-workflow-deferred-plan-lifecycle

## Metadata

- **Issue**: N/A
- **Type**: enhance
- **Target Project**: wopal-space-ontology
- **Product**: wopal-space
- **Project Path**: .wopal
- **Project Type**: ontology-worktree
- **Created**: 2026-09-16
- **Updated**: 2026-09-17
- **Status**: reviewing
- **Plan ID**: `wopal-space-ontology/enhance-workflow-deferred-plan-lifecycle`
- **Depends On**: None
- **Base Commit**: (approve 时自动记录实施基线，集成分支 HEAD)
- **Final Commit**: (verify 时自动记录合入提交，集成分支 HEAD)

## Scope Assessment

- **Complexity**: High
- **Confidence**: Medium

## Goal

让用户批准设计后安全停留在 `approved`；只有显式开始实施或调度器实际派发时才准备执行环境。同时提供版本化 Plan Provider 与依赖声明校验，使 dev-flow 能作为跨项目 Plan 编排的唯一工作流真相源。

## Technical Context

### Architecture Context

当前 dev-flow 的实际状态机是 `planning → reviewing → executing → verifying → done`；`approve` 同时创建 worktree 并推进 `executing`。这会把“评审批准”“排期”“实际实施”混为一个动作，无法满足 Plan Orchestration 的延后实施模型。

本 Plan 在空间实际 ontology worktree `.wopal` 实施。权威 Plan 始终位于空间 `.wopal-space/plans/<project>/`，不复制到 worktree；`projects/wopal-space-ontology` 不是可写项目路径，严禁直接修改 ontology 主仓库。

产品契约与跨项目边界见 [Plan Orchestration 设计](../../../docs/products/wopal-space/DESIGN-plan-orchestration.md)。本 Plan 完成后，C 才能消费 Provider；调度时间、daemon、运行态 JSON、Workbench 和正式分发仍由 C/E/S 分别拥有。

### Research Findings

本轮已将 dev-flow 收敛为单一的行为驱动格式：Key Interfaces 钉住跨边界契约，两拍制 AC 钉住验收结果，Task 按行为组而非文件拆分。旧的独立 `outcome-driven` profile 概念不再存在；仍未交付的是 `approved` 生命周期、Provider、JIT 准备和 Plan 依赖声明校验。

**参考资料**：
- [Plan Orchestration 设计](../../../docs/products/wopal-space/DESIGN-plan-orchestration.md)
- [Plan Orchestration 交付索引](../../../docs/products/wopal-space/PLAN-plan-orchestration-delivery.md)

### Key Decisions

- D-01: 工作流唯一状态机扩展为 `planning → reviewing → approved → executing → verifying → done`；`approved` 只记录明确授权和审批语义 revision，绝不创建 worktree、分支或 Agent。
- D-02: 审批与实施是两个动作。手工开始和调度器派发都必须经 Provider 的 prepare/begin 语义；成功绑定实际环境后才进入 `executing`。
- D-03: Plan 规范化、审批凭据、状态合法性和执行准备只在 Provider 实现一次；C 只能经适配器消费机器接口，不解析 Markdown 重建真相。
- D-04: 审批绑定 Goal、范围、AC、依赖、权限和执行策略等语义内容。格式、进度和运行报告不使审批失效；手改 `Status` 绝不构成审批凭据。
- D-05: 依赖建议只能生成候选与理由；保存依赖图和授予审批均不启动隐式 Agent 推理。O 只做静态声明校验，C 才保存用户确认的运行图。
- D-06: 这是自举 Plan。O 在用户明确批准“现在实施 O”后仍按当前人工工作流进入 `executing`；C/E/S 在 O 交付前不得使用当前 `approve` 伪装“只批准不实施”。

### Key Interfaces

以下 Provider 语义由 O 发布给 C，是跨项目红线。实现可确定命令拼写与 DTO 组织，但不得删改操作集合、字段语义、错误类别、revision 或幂等规则；变更须先修订本 Plan 和消费者兼容测试。

```typescript
type WorkflowState =
  | "planning" | "reviewing" | "approved"
  | "executing" | "verifying" | "done"

type ProviderError =
  | "PLAN_NOT_FOUND"
  | "REVISION_MISMATCH"
  | "APPROVAL_INVALID"
  | "DEPENDENCY_PENDING"
  | "EXECUTION_CONFLICT"
  | "ENVIRONMENT_INVALID"
  | "RECOVERY_REQUIRED"

interface PlanDescriptor {
  planId: string
  spacePath: string
  planPath: string
  projectPath: string
  projectType: "standard" | "ontology-worktree"
  workflowState: WorkflowState
  semanticRevision: string
  approvalRevision?: string
  dependencies: readonly { planId: string; gate: string }[]
  executionPolicy: "new-worktree" | "no-worktree" | "existing-worktree"
}

interface PlanProvider {
  describe(planId: string): PlanDescriptor
  approve(planId: string, expectedRevision: string): { approvalRevision: string; state: "approved" }
  prepare(executionId: string, expectedApproval: string): {
    executionId: string; baseline: string; executionPath: string
  }
  begin(executionId: string): { executionId: string; state: "executing" | "already-executing" }
  resultRead(executionId: string): { executionId: string; outcome: string; evidence: readonly string[] }
}
```

- `prepare` 和 `begin` 使用同一稳定 execution ID；重复调用返回同一执行身份，不能创建第二个 worktree。
- `prepare` 仅在有效审批、调用方 execution ownership、依赖证据、仓库身份和预期 revision 均成立时运行；审批时 `executionPath` 可以为空。
- `begin` 在绑定实际环境前再次复验审批和依赖；撤回发生在 prepare 与 begin 之间时必须拒绝启动。
- 所有机器接口都返回结构化成功或上述错误；非零退出、错误码和可读修复建议在 CLI/JSON 表达中保持一致。

## In Scope

- 扩展 dev-flow 生命周期、审批凭据和撤回/修订语义，提供审批后停下与显式开始实施能力。
- 实现 Plan Provider 的规范化描述、semantic revision、审批、prepare、begin、结果读取和恢复语义。
- 支持新 worktree、显式无 worktree、复用 worktree 与 ontology-worktree 四类执行策略；记录实际基线和 execution identity。
- 为 `Depends On` 声明实现 Plan ID、缺失引用、循环和交付门槛的静态校验。
- 更新 dev-flow 脚本、模板、双语技能说明、测试和装配后的能力发现；向 C 发布接口样例、错误码、兼容规则与测试夹具。

## Out of Scope

- cron、时区、DAG 运行图、daemon、运行态 JSON、claim、资源锁和三平台服务——由 C 负责。
- 受控 Agent、工具权限、Session、Runtime API、Workbench——由 E 负责。
- 官网安装、升级入口和最终发布验收——由 S 负责。
- 通用工作流引擎、跨 Space/跨主机调度，或在未经用户授权时自动提交、合并、complete、verify、archive。
- 直接修改 ontology 主仓库或覆盖其他进行中的 df-plan-review 工作。

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| dev-flow state and provider | `skills/dev-flow/scripts/` | 修改/创建 | 生命周期、Provider、prepare/begin、命令包装与恢复协议 |
| Plan validation | `skills/dev-flow/templates/plan.md`, `skills/dev-flow/scripts/validation.py` | 修改 | `approved` 生命周期、依赖声明和行为驱动 Plan 的一致校验 |
| Skill documentation | `skills/dev-flow/SKILL.md`, `SKILL.zh-CN.md`, `references/` | 修改 | 双语命令语义、契约、验证和自举流程 |
| Regression suite | `skills/dev-flow/tests/python/` | 修改/创建 | 临时 Git、故障注入、兼容性和装配回归 |
| Assembly | `assembly/archetypes/`, `assembly/templates/` | 修改 | 装配后可发现的版本、解释器前提和修复诊断 |

## Acceptance Criteria

### Agent Verification

1. [ ] 在真实临时 Git Space 中，批准 reviewing Plan 后状态为 `approved`，worktree/分支集合和 Agent 子进程集合均不增加；显式开始实施成功后才记录实际环境并进入 `executing`。
2. [ ] 新 worktree、无 worktree、复用 worktree 与 ontology-worktree 四种策略均通过真实 Git 夹具；同 execution ID 重试、prepare 中崩溃、状态写入失败、基线变化均可恢复且不重复建树。
3. [ ] 手改 `Status` 不能伪造审批；Goal、范围、AC、依赖或权限变更使批准 revision 失效，格式/进度/运行报告修改不失效；prepare 与 begin 之间撤回会阻止启动。
4. [ ] 既有 Plan、无 Issue Plan、人工手工开发链路和显式接管已有 `executing` Plan 的回归测试全部通过，新状态不破坏既有生命周期。
5. [ ] 行为驱动 Plan 能通过 check/submit/review/complete 链路；缺失验收、不存在的依赖 ID、循环依赖和不合格交付门槛被拦截，未预先列出逐文件施工清单不被拒绝。
6. [ ] 装配后的真实空间暴露与源码一致的 Provider 版本、接口样例、错误码、兼容规则和测试夹具；缺失或不兼容时 C 能获得可执行的诊断。

### User Validation

#### Scenario 1: 批准后停下与行为驱动 Plan 可读性

- Goal: 用户确认“批准”只记录授权，而不开始实施；同时确认新的 Plan 结构能清楚表达目标、契约、验收和实施边界。
- 验证环境: 本空间已装配 O 的集成版本；下游 Plan `196-feature-cli-plan-scheduler` 处于 reviewing。
- Precondition: 记录执行前的 `git worktree list` 输出；确认当前不准备立即开始 C 的代码实施。
- 启动命令: `bash .wopal/skills/dev-flow/scripts/flow.sh approve 196-feature-cli-plan-scheduler --confirm`
- User Actions:
  1. 阅读 C Plan 的 Goal、Key Interfaces、Agent Verification、User Validation 和行为组 Task。
  2. 运行启动命令，再运行 `bash .wopal/skills/dev-flow/scripts/flow.sh plan status 196-feature-cli-plan-scheduler`。
  3. 再次运行 `git worktree list`，与批准前输出对照。
- 通过判据: status 明确显示 `approved`；没有新 worktree、分支或运行进程；Plan 的目标、跨项目接口、自动验证与人工验证边界可直接理解。
- 失败反馈: approve/status 的完整输出、`git worktree list` 前后对照，以及无法理解的 Plan 段落与原因。

- [ ] 用户已完成上述功能验证并确认结果符合预期

## Implementation

### Task 1: 实现 approved 生命周期与审批凭据

**Verification Intent**: AC#1, AC#3, AC#4

**Behavior**:
- reviewing Plan 经有效用户确认批准后 → `workflowState: "approved"`，无 worktree、feature branch 或 Agent 子进程。
- approved Plan 的语义 revision 未变时重复批准 → 返回同一批准语义，不重复创建审批副作用。
- Goal、范围、AC、依赖或权限改变后 → 原 `approvalRevision` 不再有效；仅改进度、格式或运行报告 → 保持有效。
- approved Plan 被撤回或修订 → 回到 reviewing，旧凭据失效；已有 executing Plan 只能显式接管，不能仅按状态猜测 ownership。

**Pre-read**:
- `skills/dev-flow/scripts/workflow.py` — 状态、转移和 metadata 规则
- `skills/dev-flow/scripts/commands/approve.py` — 当前 approve 与 worktree 创建路径
- `skills/dev-flow/scripts/commands/plan.py` — Plan 定位与状态读取
- `skills/dev-flow/tests/python/` — 当前生命周期夹具与回归模式

**Design**:
将批准记录建模为独立、可审计的语义凭据，并把 `approved` 加入唯一状态机。裸 approve 只写入批准证据和 revision；开始实施由单独的 Provider 调用路径完成。兼容既有 `executing` Plan 和无 Issue Plan，绝不把手改 Status 当授权来源。

**TDD**: true

**Changes**:
1. RED：将上述批准、撤回、语义失效和既有 Plan 兼容行为写成失败生命周期测试
2. GREEN：实现 `approved` 状态、批准凭据和撤回/接管语义，使测试全绿
3. REFACTOR：收敛状态/凭据解析为单一入口，消除 approve 与后续命令的重复判断

**Verify**: `cd .wopal/skills/dev-flow && python -m pytest tests/python/ -q`

**Done**:
任务产出：可审计的 `approved` 生命周期、审批 revision 与旧 Plan 兼容回归测试
实际触碰文件：实施后回填
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤。

---

### Task 2: 发布版本化 Plan Provider 规范化接口

**Verification Intent**: AC#3, AC#4, AC#6

**Behavior**:
- `describe(planId)` → 返回稳定 Plan ID、空间/项目/Plan 路径、workflow state、semantic revision、依赖、执行策略和资格原因。
- canonicalization 对同一语义 Plan → 产生相同 revision；改 Goal、范围、AC、依赖或权限 → revision 改变。
- Provider 遇到不存在 Plan、revision 不符、无效审批或环境冲突 → 返回约定的结构化错误，而非靠 Markdown 解析异常泄漏。
- C 只消费 Provider 的描述和错误契约 → 不需要复制 Markdown parser 或自行判定状态合法性。

**Pre-read**:
- `skills/dev-flow/scripts/flow.sh` — 对外命令包装方式
- `skills/dev-flow/scripts/workflow.py` — 状态与 metadata 读取规则
- `skills/dev-flow/scripts/commands/plan.py` — Plan 发现与 metadata 提取
- `skills/dev-flow/scripts/validation.py` — 规范化内容与校验边界
- `docs/products/wopal-space/DESIGN-plan-orchestration.md` — Provider 语义和 revision 约束

**Design**:
以单一 Provider 模块实现规范化、revision、审批读取和结构化错误。机器接口采用稳定 JSON 信封与明确错误码；命令拼写和 DTO 组织可按现有脚本架构落地，但 Key Interfaces 中的字段语义、拒绝行为、幂等和版本约束不可漂移。

**TDD**: true

**Changes**:
1. RED：为 describe、canonical revision、错误映射和旧 metadata 兼容写失败测试
2. GREEN：实现 Provider 描述与审批读取接口，使 C 可用适配器消费
3. REFACTOR：将重复的 Plan metadata 解析迁入 Provider，保持唯一 canonical Plan 真相源

**Verify**: `cd .wopal/skills/dev-flow && python -m pytest tests/python/ -q`

**Done**:
任务产出：版本化 Provider 描述/错误契约、兼容夹具和消费者示例
实际触碰文件：实施后回填
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤。

---

### Task 3: 实现 JIT prepare/begin 与可恢复执行准备

**Verification Intent**: AC#1, AC#2, AC#3, AC#4

**Behavior**:
- 有效批准和 execution ownership 下调用 prepare → 校验仓库、依赖证据、预期 revision 和执行策略后返回实际基线与 executionPath。
- 同 execution ID 重复 prepare/begin → 返回同一执行身份；prepare 中途崩溃或状态写失败后重试不创建第二个 worktree。
- prepare 失败、依赖不满足或 runtime 不兼容 → 不推进 `executing`，不把残留目录标记为成功，也不删除未经核实的用户文件。
- begin 绑定实际环境前再次校验批准和依赖；准备后撤回批准 → 拒绝 begin；成功 begin → 原子进入 `executing`。

**Pre-read**:
- `skills/dev-flow/scripts/commands/approve.py` — 当前 worktree/branch 准备路径
- `skills/dev-flow/scripts/lib/git.py` — 仅列路径提交与 Git 安全辅助
- `skills/dev-flow/scripts/workflow.py` — 生命周期写入与状态转移
- `skills/dev-flow/tests/python/` — 临时 Git、故障注入和恢复夹具
- `docs/products/wopal-space/DESIGN-plan-orchestration.md` — dispatch/recovery 协议

**Design**:
prepare/begin 不假称跨 Git、文件和状态存储是一个事务，而是记录阶段、execution ID 和恢复判据。实施基线在 prepare 时确定；集成分支移动按兼容规则复验。支持新/无/复用 worktree 与 ontology-worktree，且始终保护外部未提交工作。

**TDD**: true

**Changes**:
1. RED：为四种执行策略、幂等重试、撤回竞态、崩溃和基线变化写故障注入测试
2. GREEN：实现 prepare/begin、恢复日志和实际环境 metadata，使夹具全绿
3. REFACTOR：统一执行策略解析和恢复判断，删除 approve 时提前准备环境的路径

**Verify**: `cd .wopal/skills/dev-flow && python -m pytest tests/python/ -q`

**Done**:
任务产出：四类执行策略的 JIT 准备、幂等 begin 和可恢复故障协议
实际触碰文件：实施后回填
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤。

---

### Task 4: 校验 Plan 依赖声明并贯通行为驱动流程

**Verification Intent**: AC#5

**Behavior**:
- `Depends On` 中引用不存在的 Plan ID → check/submit 返回缺失 ID 与定位信息。
- A→B→A 或更长循环 → check/submit 拒绝并输出完整环路；无依赖单 Plan 与合法 DAG → 通过。
- 依赖声明包含未认可交付门槛或跨 Space 引用 → 被拒绝；声明与 C 的 `verified-integrated-deliverable` / artifact gate 语义一致。
- 行为驱动 Plan 的 Key Interfaces、两拍制 Agent Verification、User Validation 和行为组 Task → 在 check/submit/approve/start/complete 入口获得一致处理，不要求 Task 级 Files 清单。

**Pre-read**:
- `skills/dev-flow/templates/plan.md` — 当前单一 Plan 结构
- `skills/dev-flow/scripts/validation.py` — submit/complete 校验入口
- `skills/dev-flow/references/plan-guide.md` — 两拍制、Task、AV/UV 边界
- `skills/dev-flow/SKILL.md` — 状态机和人类授权门
- `docs/products/wopal-space/DESIGN-plan-orchestration.md` — 依赖 gate 与 graph-stale 语义

**Design**:
保留已交付的单一行为驱动模板，不重新引入 profile 分叉。新增的静态校验只读取 Plan 声明、以确定性算法检查身份/边/环/门槛；依赖建议和运行图保存仍由用户/C 负责。所有中英文规则同步描述新的 `approved` 与依赖语义。

**TDD**: true

**Changes**:
1. RED：为缺失 ID、跨 Space、循环、非法 gate 和合法 DAG 写失败 Plan 校验测试
2. GREEN：实现依赖声明解析与确定性校验，并接入 check/submit 等入口
3. REFACTOR：统一模板、validator 和双语指南对依赖/验收字段的术语

**Verify**: `cd .wopal/skills/dev-flow && python -m pytest tests/python/ -q`

**Done**:
任务产出：依赖声明静态校验与新生命周期/行为驱动格式的全链路回归测试
实际触碰文件：实施后回填
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤。

---

### Task 5: 装配 Provider 能力并交付双语诊断资料

**Verification Intent**: AC#6

**Behavior**:
- 从装配后的真实空间调用 Provider → 暴露与源码一致的能力版本、操作语义和错误码。
- 缺少 Provider、解释器或兼容版本 → 输出可执行修复说明，不伪装为可派发。
- C 消费发布的接口样例和夹具 → 能区分缺能力、版本不兼容和正常可用状态。

**Pre-read**:
- `assembly/archetypes/coding.yaml` — 空间装配入口
- `assembly/templates/REGULATIONS.md` — 装配内容约束
- `skills/dev-flow/SKILL.md`, `skills/dev-flow/SKILL.zh-CN.md` — 双语运行时说明
- `skills/dev-flow/tests/python/` — 装配与能力回归模式

**Design**:
将 Provider 所需脚本、模板、夹具、版本信息和双语修复指南随 ontology 正式装配。此任务不实现调度器，只保证手工流程和 C 的适配器都有可发现、可诊断的输入。交付记录实际接口版本、测试命令、装配证据和 revision。

**TDD**: false
理由：装配与双语资料是声明式交付，使用渲染/发现回归夹具验证而非为文案建立单元测试。

**Changes**:
1. RED：新增装配后 Provider 缺失、版本不符和发现失败的回归夹具
2. GREEN：同步装配声明、版本信息、双语说明和 C 消费样例，使夹具通过
3. REFACTOR：去除过期的 approve 即实施说明，统一修复建议和错误码命名

**Verify**: `cd .wopal/skills/dev-flow && python -m pytest tests/python/ -q`

**Done**:
任务产出：装配后的 Provider 能力、C 兼容夹具和双语运行/修复说明
实际触碰文件：实施后回填
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤。

---

## Delegation Strategy

| Wave | Task | 执行者 | 依赖 | 委派理由 |
|------|------|--------|------|---------|
| 1 | Task 1 | fae | 无 | 先固定生命周期和审批凭据，避免后续接口建立在旧 approve 语义上 |
| 2 | Task 2 | fae | Task 1 | Provider 必须消费已固定的 approved/revision 语义 |
| 3 | Task 3 | fae | Task 1, Task 2 | prepare/begin 依赖 Provider、审批和 ownership 契约 |
| 4 | Task 4 | fae | Task 1 | 静态依赖校验与状态机入口需以新生命周期为基线 |
| 5 | Task 5 | fae | Task 2, Task 3, Task 4 | 最后装配真实能力并发布完整消费者资料 |

验证纪律：每个 Task 由 fae 先运行自身 Verify、立即回填 Done 与实际文件；Wopal 在 rook 通过后逐条实证 Agent Verification，并确认双语内容和装配产物与源码一致。

# enhance-session-assembly

## Metadata

- **Type**: enhance
- **Project Path**: .wopal
- **Created**: 2026-09-27
- **Updated**: 2026-09-29
- **Stage**: draft
- **Mode**: (accept 时记录：isolated | quick)
- **Worktree**: (accept 时记录)
- **Branch**: (accept 时记录)
- **Base Commit**: (accept 时记录)
- **Final Commit**: (integrate 时记录：集成到空间分支后的提交)

## Scope Assessment

- **Complexity**: High
- **Confidence**: High — 跨项目架构已完成源码验证、写入正式 DESIGN 并经用户评审通过；本提案负责 ontology/wopal-plugin 的配套实施。

## Goal

让 `wopal_task` 在不替代角色静态能力的前提下，按任务从 Space Arsenal 为子 Session **增量授予** Skill/Tool 能力，并让 Rule 与按需 Skill guidance 在 run loop 中按当前 intent/action/path 动态激活。装配结果必须可持久恢复，动态上下文必须 append-only、cache-safe；ellamaka core 保持产品无关。

## Technical Context

### Architecture Context

权威设计为 `.wopal/docs/DESIGN-capabilities.md`、`.wopal/docs/DESIGN-wopal-plugin.md` 与 `projects/ellamaka/docs/DESIGN.md` 的 Session Capability Contract / Runtime Context Contribution。引擎侧配套实施由 `.wopal-space/plans/ellamaka/feature-ellamaka-session-permissions.md` 承载；本提案保持 `draft`，直到用户明确批准本体实施。实施前置是 ellamaka Plan 已交付可消费的 effective-permission 与 request-tail contribution 契约。

### Key Decisions

- D-01: `wopal_task.capabilities` 是 Agent baseline 上的 incremental grant；省略类别即只用 baseline。P2 不提供 exact-set/subtract/deny。
- D-02: Session Capability Envelope 在首个模型请求前一次编译并在子 Session 生命周期内冻结；Tool/Skill grant 编译到既有 `session.permission`，Wopal assembly intent 写入 session metadata。
- D-03: Space Arsenal 负责“可授予什么”的名称/物化校验；ellamaka permission 负责“运行时能否看见/执行”。插件不复制引擎 permission evaluator。
- D-04: Rule 创建时只确定 eligibility/scope，正文在 run loop 根据 user intent、tool/action/path 动态 resolve；Skill 采用稳定轻量 catalog + progressive disclosure。
- D-05: Rule/Skill 动态 guidance 统一通过 ellamaka request-tail contribution seam 追加；禁止回写旧 history、反复改 system prompt 或 tool schema。
- D-06: `session.permission` 与 `session.metadata` 是持久事实；SessionStore/插件内存只做派生 cache。resume/restart/compaction 后必须可重建。
- D-07: 子 Session 自身禁止递归 `wopal_task` 等限制与 capability grants 一次编入创建时 overlay；首轮 `promptAsync` 不再用会覆盖 permission 的临时 tools rewrite。
- D-08: 不改变现有静态 config/agent.md 机制；没有 `capabilities` 或没有动态 activation 时行为保持现状。

### Key Interfaces

#### `wopal_task.capabilities`

保持现有 `wopal_task` 为派发入口，增加/收敛可选能力声明：

```ts
capabilities?: {
  skills?: string[]
  tools?: string[]
  rules?: string[] // eligibility/scope only; not eager body injection
}
```

语义：
- 每个列表按 Space Arsenal 的规范名称解析、去重；未知、歧义、未物化能力在创建子 Session 前失败，不产生半创建 Session。
- `skills` / `tools` 只追加到角色 baseline，不表达撤销。
- `rules` 只限制本次 Session 可被 runtime resolver 激活的候选范围；Rule 正文不在 spawn 时注入。
- 省略 `capabilities` 与当前派发行为兼容。

#### Session assembly metadata

使用既有 `session.metadata` 保存 Wopal 私有装配意图；具体 key 采用 namespaced 结构并带 schema/version，至少能重建：requested/resolved capability identities、rule eligibility 与 assembly version。metadata 不是执行授权；授权真相仍是 `session.permission`。

#### Runtime contribution

wopal-plugin 消费 ellamaka 的 request-tail contribution hook：每一步从当前 Session 持久状态 + 当前 request/tool/action/path 状态解析 active Rules / Skill guidance，生成确定性 contribution。相同有效集合产生稳定 digest/序列化；集合变化只影响新的 tail contribution。

## In Scope

- `wopal_task.capabilities` schema、解析、Space Arsenal 校验、去重与失败原子性。
- 子 Session Envelope：Skill/Tool incremental permission overlay、递归派发 deny、Wopal namespaced metadata 一次写入。
- Rule eligibility 与 run-loop resolver；基于 intent/tool/action/path 的动态 activation。
- Skill 稳定 catalog 的消费与按需正文/guidance progressive disclosure。
- request-tail contribution 的确定性格式/digest、append-only 注入与重复抑制策略。
- resume、plugin restart、compaction 后从 session permission/metadata/current history 重建派生状态。
- 派发失败清理、父子 Session 隔离与现有无-capabilities 路径回归。

## Out of Scope

- ellamaka core 的 effective-permission 与 request-tail hook 实现（由 P-D Plan 承载）。
- exact-set/subtract/动态撤销角色 baseline。
- CLI capability discovery/list、空间物化与 sync。
- plugin config consumption、Workbench UI、sandbox profile 设计。
- 把 Rule/Skill resolver 上移到 ellamaka core。

## Affected Files

| Component | Range | Role |
|---|---|---|
| Wopal task dispatch | `.wopal/plugins/wopal-plugin/` task/session assembly paths | capability parsing、Envelope 编译、失败清理 |
| Runtime context | `.wopal/plugins/wopal-plugin/` rule/skill/context hook paths | Rule resolver、Skill activation、request-tail contribution |
| Persistent reconstruction | `.wopal/plugins/wopal-plugin/` SessionStore/session metadata integration | restart/resume/compaction 重建 |
| Tests | `.wopal/plugins/wopal-plugin/` test suites | isolation、cache-safe lifecycle、integration regression |

## Acceptance Criteria

### Agent Verification

1. [ ] `wopal_task` 不带 `capabilities` 时保持现有派发行为；带 skills/tools 时仅在目标子 Session 的 Agent baseline 上增量授予，父 Session、兄弟 Session 与其他 Agent 不受影响。
2. [ ] capability 名称在创建前按 Space Arsenal 校验并去重；未知/歧义/未物化能力失败时不留下半创建 child Session、permission 或 metadata。
3. [ ] 创建 child 时 capability grant 与 `wopal_task: deny` 等子会话限制一次编入稳定 overlay；首轮 prompt 不再覆盖/擦除该 overlay，后续 step/compaction 也不改 Tool/Skill capability envelope。
4. [ ] namespaced session metadata 足以在 plugin restart/resume 后重建 resolved assembly 与 Rule eligibility；内存 cache 清空不改变可观察行为。
5. [ ] Rule resolver 只从 eligibility 中按当前 intent/tool/action/path 激活；未匹配 Rule 不注入，匹配集合变化只产生新的 request-tail contribution，不修改较早 history/system/tool schema。
6. [ ] Skill 使用稳定 catalog + progressive disclosure；未需要的 Skill body 不 eager 注入，需要时可加载并在后续 retained context 中正常工作。
7. [ ] 相同 active Rule/Skill context 的序列化/digest 稳定且不会无意义重复膨胀；有效集合变化产生完整、可解释的新 tail snapshot/replacement。
8. [ ] resume、plugin restart、compaction 后下一 step 能根据持久状态重新 resolve；测试能抓住依赖旧进程 cache、回写旧 message 或动态修改 tool schema 的错误实现。
9. [ ] 真实父/子/兄弟 Session 集成测试覆盖增量能力、Rule 动态激活、Skill 按需加载与隔离；插件受影响测试、typecheck/build 全绿。

### User Validation

#### Scenario 1: 任务级增量能力与动态上下文
- Goal: 在真实 Wopal 派发中观察角色 baseline 保留、任务能力增量生效，并确认 Rule/Skill 只在需要时进入上下文。
- 验证环境: 本空间启用已交付 P-D 的 ellamaka 与当前 ontology feature branch；按项目规范启动 ellamaka/Workbench。
- Precondition: Space Arsenal 中至少存在一个角色 baseline 未包含的测试 Skill/Tool，以及可由不同 action/path 触发的 Rule。
- 启动命令: `cd projects/ellamaka && ./scripts/dev.sh`
- User Actions:
  1. 用同一角色派发 A/B 两个子任务：A 声明额外 Skill/Tool，B 不声明；分别询问并实际调用能力。
  2. 在 A 中先执行不匹配 Rule 的动作，再执行匹配 path/tool 的动作，观察上下文/行为变化；按需调用声明的 Skill。
  3. 对 A 执行一次 compaction 或重启插件/恢复 Session 后重复能力调用与 Rule 触发。
- 通过判据: A 保留角色 baseline 且多出声明能力，B 只有 baseline；Rule 只在匹配步骤生效，Skill 正文按需加载；恢复/压缩后 A 的能力与 eligibility 不丢失，兄弟 Session 不被污染。
- 失败反馈: 提供 A/B session id、`wopal_task` 输入、能力/规则观察结果与 ellamaka 日志定位信息。

- [ ] 用户已完成上述功能验证并确认结果符合预期

## Implementation

### Task 1: 编译并持久化 Session Capability Envelope

**Verification Intent**: AC#1, AC#2, AC#3, AC#4

**Behavior**:
- no capabilities → legacy-equivalent child creation.
- valid incremental skills/tools → baseline 保留且只追加到 child effective permission；递归派发 deny 同时存在。
- invalid arsenal identity → fail before child side effects.
- plugin cache cleared → metadata/permission 可重建同一 assembly view.

**Pre-read**: `.wopal/plugins/wopal-plugin` 中 `wopal_task`、SessionStore、session create/prompt 调用路径；`.wopal/docs/DESIGN-wopal-plugin.md` 与 `.wopal/docs/DESIGN-capabilities.md`。

**Design**: spawn 前完成 normalize → arsenal validate → compile overlay/metadata → create child 的单向流水线。不要在首轮 prompt 用临时 `tools` 参数重写 session permission；metadata namespaced/versioned，permission 只承载 enforcement。

**TDD**: true

**Changes**:
1. RED：覆盖 no-op、incremental grant、invalid atomicity、child/sibling isolation、first-prompt preservation、cache rebuild。
2. GREEN：实现 capability parser/validator、overlay compiler 与 metadata persistence，并修正派发调用顺序。
3. REFACTOR：统一错误/cleanup 路径与 deterministic normalization，避免复制 ellamaka evaluator。

**Verify**: RED 阶段按真实插件测试位置回填精确命令；最终运行 wopal-plugin 受影响测试与 typecheck/build。

**Done**:
任务产出：待实施后填写。
实际触碰文件：待实施后回填。
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤

### Task 2: Runtime Rule Resolver 与 request-tail activation

**Verification Intent**: AC#5, AC#7, AC#8

**Behavior**:
- eligible but unmatched rule → no contribution.
- intent/tool/action/path match → only matching eligible rules enter tail context.
- same active set → stable serialization/digest and no pointless repeated growth.
- changed active set → new complete tail snapshot/replacement; old retained messages remain immutable.

**Pre-read**: current rule/memory injection path, ellamaka request-tail hook delivered by P-D, plugin tool before/after hooks and SessionStore.

**Design**: 把现有回写旧 synthetic/user message 的 Rule 注入迁到 resolver + request-tail contributor。Resolver 输入是持久 eligibility 与当前 step signals；输出先 canonicalize/digest，再生成确定性 context。Rule body 不在 child spawn 时 eager 注入。

**TDD**: true

**Changes**:
1. RED：为 unmatched/matched/change/same-set/history-immutability/compaction cases 建失败测试。
2. GREEN：实现 eligibility resolver、canonical snapshot/digest 与 request-tail contributor 接入，移除对应旧消息回写路径。
3. REFACTOR：统一 signal 提取与重复抑制，保证 tool schema/system prompt 不受动态 Rule 影响。

**Verify**: RED 阶段回填精确命令；最终覆盖 rule injection、tool hooks、session lifecycle 与插件质量门禁。

**Done**:
任务产出：待实施后填写。
实际触碰文件：待实施后回填。
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤

### Task 3: Skill progressive activation 与生命周期恢复

**Verification Intent**: AC#6, AC#8, AC#9

**Behavior**:
- eligible Skill appears in stable catalog without eager body injection.
- selected/needed Skill body loads through existing Skill mechanism and remains usable in retained context.
- restart/resume/compaction → catalog/envelope stays stable and dynamic guidance can be regenerated from persistent facts.
- parent/sibling sessions never inherit child-only grant or activation state.

**Pre-read**: current skill loading/catalog integration in wopal-plugin, Task 1 metadata, Task 2 contributor, session resume/compaction handlers.

**Design**: 不复制 ellamaka Skill loader；插件只管理 Wopal eligibility/activation guidance。稳定 availability 由 Session permission + 引擎 Skill catalog 提供，正文继续现有 progressive disclosure。生命周期测试以真实 child/sibling Session 为边界。

**TDD**: true

**Changes**:
1. RED：覆盖 catalog/body 分离、按需加载、restart/resume/compaction 与 parent/sibling isolation。
2. GREEN：接通 Skill activation guidance 与持久 assembly 重建，消除依赖进程内 cache 的正确性路径。
3. REFACTOR：跑完整插件集成测试/typecheck/build，并把真实命令回填 AC/Task。

**Verify**: RED 阶段回填精确命令；最终运行 wopal-plugin 全量受影响测试、typecheck/build。

**Done**:
任务产出：待实施后填写。
实际触碰文件：待实施后回填。
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤

## Delegation Strategy

| Wave | Task | 执行者 | 依赖 | 委派理由 |
|---|---|---|---|---|
| 1 | Task 1 | fae | ellamaka P-D 已交付 | Envelope 是后续 runtime resolver 的持久底座 |
| 2 | Task 2 | fae | Task 1 | Rule activation 消费 metadata 与 request-tail seam |
| 3 | Task 3 | fae | Task 1–2 | Skill/恢复在完整生命周期上收口 |

## Delivery Dependency

本提案可在 `draft` 中继续评审，但不得在 ellamaka `feature-ellamaka-session-permissions` 交付前进入实际实施。P-D 交付后，用户仍需按 ontology-evolution 流程明确批准本提案，才能 `accept → implementing`。

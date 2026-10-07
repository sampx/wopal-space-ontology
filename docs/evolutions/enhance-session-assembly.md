# enhance-session-assembly

## Metadata

- **Type**: enhance
- **Project Path**: .wopal
- **Created**: 2026-09-27
- **Updated**: 2026-10-07
- **Stage**: draft
- **Mode**: (accept 时记录：isolated | quick)
- **Worktree**: (accept 时记录)
- **Branch**: (accept 时记录)
- **Base Commit**: (accept 时记录)
- **Final Commit**: (integrate 时记录：集成到空间分支后的提交)

## Scope Assessment

- **Complexity**: High
- **Confidence**: Medium — 已验证现有消息 transform、任务派发和正式 SDK 的接口。首次模型请求前授权、tool/path 条件、跨进程恢复仍需真实集成测试证明。

## Goal

让 Wopal 在派发任务时，通过 `wopal_task.capabilities` 为这一个子会话追加 Skill、Tool 或明确声明的工具权限组。授权与装配意图在首个模型请求前保存，模型清单与实际调用消费同一个 Session 权限结果。

Rule 继续由 wopal-plugin 处理。除已有关键词与 Agent 作用域外，本提案增加 tool/path 条件；每个模型请求根据当前用户提示与最近工具批次重新匹配，把一份完整的有效 Rule 快照通过既有 `messages.transform` 追加到请求末尾。Skill 全文继续由引擎 Skill 工具按需加载。

临时注入通过现有 context dump 观察。提案复用现有 Session API、Plugin hook、Skill loader 和 Chat 机制，不增加引擎钩子或合成消息生命周期。

## Technical Context

### Evidence and Delivery Boundary

- 本提案是 ontology 进化提案，保持 `draft`；优化提案不等于批准实施。
- `.wopal/plugins/wopal-plugin/src/tasks/task-launcher.ts` 创建子会话后，在首轮 `promptAsync` 传 `tools: { wopal_task: false }`。引擎 `SessionPrompt.prompt` 会据此覆盖 `session.permission`，因此增量授权必须与防递归限制在创建时一起编译，首轮不再传 `tools`。
- `.wopal/plugins/wopal-plugin/src/hooks/message-hooks.ts` 已接入 `messages.transform`。当前 Rule injector 修改最近 user 消息的 parts，并依赖 `lastRulesPrompt` 跳过重复注入；新请求从 DB 重建后，不能因为上次已注入而省略仍然有效的临时 Rule。
- `.wopal/plugins/wopal-plugin/src/rules/discoverer.ts` 的 Rule metadata 目前只有 keywords；tool/path 条件是本提案真正新增的规则能力。
- `.wopal/plugins/wopal-plugin/src/tools/dump-formatter.ts` 优先导出 transform 后消息快照，已能展示不落库的 synthetic 内容。
- 正式发布包 `@wopal/ellamaka-sdk@2.0.8` 的 **v2** 入口包含 Skill/Rule/Tool discovery、Session create/update 的 permission 和 metadata 类型；根 v1 入口的相应 Session 请求类型不包含这些字段。仅升级版本、不选择正确入口，不能完成接口适配。
- Ellamaka `feature-ellamaka-session-permissions` 当前成果保留 Session-aware Skill 清单修复，已撤除新增 request-context hook。实施依赖是该引擎修复交付；不等待新 Plugin hook。

### Design Alignment

权威资料为 `docs/DESIGN-capabilities.md`、`docs/DESIGN-wopal-plugin.md` 和 Ellamaka DESIGN 的 Session Capability Contract / Runtime Context Contribution。

本次用户确认三项设计：同时实施 tool/path Rule 条件；支持显式共享权限组；任务授权可以覆盖 Agent 的明确 deny，但沙箱、调度 profile 和防递归派发等硬限制保持。Agent permission 因此是可由任务 overlay 覆盖的角色默认值，不能独自承担不可放宽的安全上限。

现有两份 ontology DESIGN 仍含新增 request-tail hook、跨请求 digest 去重及角色静态禁止不可覆盖的旧描述。Task 2/3 必须同步这些契约；本次只优化提案，不修改运行时资产或已发布接口。

### Key Decisions

- D-01: Skill/Tool 是 baseline + incremental grant。未声明类别沿用 Agent 默认值，空 skills/tools/toolGroups 不撤销默认能力；本提案不支持 exact-set/subtract。
- D-02: 用户明确声明的 allow 可以覆盖 Agent 的 deny。请求不能提高沙箱/profile 上限，也不能授予子会话递归派发权限；防递归 deny 在所有 grant 后追加。read-only 硬边界下请求 edit 组必须在创建前拒绝，不能把 Agent deny 当作唯一安全上限。
- D-03: Skill、独立 Tool 和共享权限组分别解析。共享组必须使用 `toolGroups` 明确声明，不能从单个 write/edit/apply_patch 名称悄悄推导为 edit 整组授权。
- D-04: 引擎 discovery 是空间能力名称与物化状态的来源；插件负责输入归一化和授权目标编译，引擎负责 permission 求值。插件不另建能力注册表或复制完整 permission evaluator。
- D-05: 稳定的 `session.permission` 与 assembly metadata 在首轮请求前形成。运行期 Rule 匹配不能改写 permission、system prompt 或工具定义。
- D-06: Rule 注入仍受 rules.enabled 控制，默认关闭；显式 rules 不开启全局开关，也不绕过 Agent 作用域。省略 rules 沿用现有候选范围；显式 rules 为本次任务选择候选集合，不是执行权限。
- D-07: tool/path 条件使用已经观察到的工具信号，影响下一次模型请求。它们提供指导，不拦截已经决定执行的工具，不承担工具授权。
- D-08: 每个正常模型 step 重新匹配并在请求尾部追加一份完整 Rule 快照。相同结果也必须随本次请求发送；digest 仅复用解析/格式化结果，不做跨请求的发送抑制。
- D-09: transient synthetic 只存在于本次 transform 数组，不调用 Session 消息写入接口；保留旧消息内容与顺序。持久 synthetic 仍按现有机制保存并参与后续历史，两种路径不混用。
- D-10: Skill catalog 和正文加载归引擎；插件只维护成功加载名称的恢复事实与必要的恢复提示，不新增 Skill resolver、catalog 或 eager body injection。
- D-11: assembly 是不可变的装配意图；runtime 是可更新的恢复事实。两者在 Session metadata 中分区，SessionStore/内存 digest cache 都是可清空的派生状态。
- D-12: 上下文验收使用已有 context dump，区分“模型请求中的临时内容”和“DB 历史”。本提案不新增 Chat 持久追踪界面。

### Key Interfaces

#### Task capability declaration

```ts
capabilities?: {
  skills?: string[]
  tools?: string[]       // canonical independent Tool IDs
  toolGroups?: ("edit")[] // explicit permission groups; initially only edit
  rules?: string[]       // canonical relative Rule paths, including extension
}
```

- Skill 身份使用引擎 discovery 的 name。Rule 身份使用含扩展名的相对路径，例如 `fae/typescript.md`。未知、歧义、未物化的名称在创建子会话前失败。
- 独立 Tool 授权必须有与实际 execution gate 一致的已验证映射，授权范围不扩大到其他工具；无法证明的工具返回不支持错误，不能猜 permission key。
- 共享组 `edit` 编译为 `{ permission: "edit", pattern: "*", action: "allow" }`，成员为 edit/write/apply_patch。单独请求这些共享组成员但未声明 edit 组时，返回 TOOL_GROUP_REQUIRED，并说明完整范围。
- `toolGroups: ["edit"]` 即是调用方明确请求整组权限，无额外确认轮。结果与 metadata 列出组名、成员和实际 permission 规则。引擎按模型过滤工具的既有行为保留，因此声明成员不保证每个模型同时暴露所有变体。
- skills/tools/toolGroups 去重并确定性排序；多处声明相同授权目标只生成一条 allow。子会话 `wopal_task`、引擎 `task` 等递归派发入口为禁授目标，相关 deny 最后编入。
- `rules` 省略时沿用当前角色的候选范围；`rules: []` 使该任务不注入 Rule；非空时只从声明集合中匹配。跨 Agent 作用域规则被拒绝。全局 rules.enabled=false 时显式请求非空 rules 返回 RULES_DISABLED。

#### SDK integration

新 assembly 调用使用正式 `@wopal/ellamaka-sdk/v2` 类型；以已发布 2.0.8 为已验证接口基线。复用插件现有 v2 客户端/transport bridge，保留 in-process fetch、认证头、directory/workspace 路由。不能把 v1 客户端强制断言成 v2 或用 `as any` 补出缺失字段。

现有 transport bridge 提取宿主客户端配置的兼容代码需要集中并明确记录其依赖；本提案不把它扩散到多个模块，不新增引擎私有模块导入。测试必须覆盖无真实 HTTP listener 的 TUI in-process 场景与带认证的 HTTP 场景。

使用现有 Session create/update/get/message API 与 `app.skills`、`app.ruleCapabilities`、`app.toolCapabilities`。创建请求同时携带 parentID、agent、permission 与 metadata；首轮 promptAsync 只携带任务 prompt、agent 和已有必要的模型/沙箱信息，不传 tools rewrite。SDK v2 已有 sandboxMode 字段；派发链必须保留父会话/宿主有效边界，不能因遗漏字段而回到更宽默认值。实际 profile 上限无法可靠取得或沿既有机制传递时，作为明确前置失败处理，不发明新的沙箱体系。

#### Session assembly and recovery state

```ts
session.metadata["wopal.sessionAssembly"] = {
  version: 1,
  assembly: {
    agent,
    requested: { skills, tools, toolGroups, rules },
    resolved: { skills, tools, toolGroups, ruleSelection },
    // ruleSelection distinguishes baseline mode from an explicit [] selection
  },
  runtime: {
    currentUserMessageID,
    recentToolBatch,
    loadedSkills,
  },
}
```

此为字段语义示意，最终类型由 Task 2 生产并供后续任务使用。assembly 在创建后冻结；runtime 是恢复指针/事实，不保存 Rule 全文、合成消息或完整模型请求。

currentUserMessageID 指向最近真实、非 synthetic 用户输入，恢复时可通过 Session message API读取其文字。recentToolBatch 保存当前用户轮中最近一个模型工具调用批次的规范 tool/callID、成功或失败状态及已知路径；新真实用户输入清空旧批次。loadedSkills 只记录成功加载名称，不能用于授予权限。

同一 Session 的并行工具事件更新由本插件统一串行合并，读写时保留其他 metadata namespace，不能丢失同批次的另一条 tool/path。命名空间不等于跨插件写入事务：本提案不承诺多个不协作 writer 对同一 metadata 的原子并发更新，也不新增 CAS API。规则快照由这些事实和当前 retained history重新计算；元数据写入失败不能悄悄降级为只有内存状态却声称恢复成功。

派发与回复使用 assembly 中记录的 Agent；授权隔离单位是 Session，不能宣称 Session overlay 天然随 Agent 切换撤销。恢复指针指向不存在的消息时，从有效持久历史校正 runtime，不复活已消失的工具信号。

#### Rule match conditions

复用顶层 keywords，并增加可选 match 字段：

```yaml
keywords: []
match:
  tools: [write, edit, apply_patch]
  paths: ["src/**/*.ts"]
```

- keywords 匹配当前真实用户输入，沿用现有大小写/通配行为；不引入 LLM intent classifier。
- 每个非空列表内部是 OR，已声明的条件组之间是 AND。工具名与路径条件必须在同一 tool signal 上成立，不能拼接不同调用的 tool 与 path。
- 无 match 的旧规则保留“无 keywords 不注入”的语义；新规则至少有一个非空 keywords/tools/paths 条件，空匹配条件不产生无条件注入。
- tools 使用规范 Tool ID。工具信号是当前用户轮中最近终态工具批次；无已观察工具批次时 tool/path 条件不匹配。成功和失败均可提供指导信号，pending 调用不当作已完成。
- paths 以 Session 工作目录为基准，标准化为 POSIX 相对路径；空间外路径不匹配本地规则。glob 大小写敏感，`*` 不跨 `/`，`**` 可跨零或多个目录，`?` 匹配一个非 `/` 字符；排除表达式和字符类不在本版支持范围，非法表达式校验失败。
- 本版路径提取覆盖 read/write/edit 的 filePath，以及 apply_patch 的文件目标；其他工具没有已验证的路径适配时只支持 tool 条件。不得从任意 bash 命令或未知 JSON 字段猜文件路径。
- 权限拒绝、文件缺失等失败信号仍可影响后续指导；规则不会补授权限或绕过失败。匹配只是模型提示，实际操作仍由工具授权/沙箱承担。

#### Injection and observability

在现有 messages.transform 内从事实生成本次有效 Rule 集合，按 canonical identity 排序，格式化为一份带来源/命中原因的完整快照，追加为独立 user 消息的 synthetic TextPart。使用合法请求消息/Part shape，原 retained messages 的文本、顺序和 tool results 不被改写。

每次请求只出现一份本次快照；后续请求不自动携带上一份。正文变化也需使 digest 变化，不能仅凭同名 Rule 沿用旧正文。空集合不追加占位消息。快照依赖的 cache 清空后，应生成相同结果。

messages.transform 后由引擎转换模型消息并在需要时追加 MAX_STEPS assistant 收尾指令。插件保留此顺序，也保留原有 memory/recovery 注入的职责和开关；不制造多个相互重复的恢复提醒。

context dump 的 Messages 部分应包含本次 synthetic 快照及命中原因。它是插件层最近一次 transform 快照，不宣称等同最终 provider HTTP 请求；重启后旧临时内容不在 DB，下一次请求重新生成后才出现新的快照。自动 dump 有现有数量限制，不引入逐 step 永久审计记录。

#### Failure contract

Task 2 生产 grant/Rule 声明验证 schema 和统一错误，Task 3 消费该 schema 执行运行期匹配。错误至少区分 CAPABILITY_UNKNOWN、CAPABILITY_AMBIGUOUS、CAPABILITY_UNMATERIALIZED、CAPABILITY_GRANT_FORBIDDEN、TOOL_GROUP_REQUIRED、TOOL_GROUP_UNSUPPORTED、RULE_SCOPE_FORBIDDEN、RULES_DISABLED、INVALID_RULE_MATCH、SESSION_ASSEMBLY_WRITE_FAILED。

无效输入在 concurrency allocation / Session create 前失败。创建成功但明确未启动时，清理仅属于本次 launch 的新 Session 并释放资源。无法确定 prompt 是否已被接受时，先停止该新任务、保留明确失败状态与 Session ID，报告清理结果；不能删除父/兄弟 Session，也不能假称没有残留。已经启动后失败保留可诊断的任务记录。

## In Scope

- capabilities schema、正式 SDK v2 适配与 Space Arsenal 校验。
- Skill、独立 Tool、显式 edit 组增量授权；用户允许覆盖 Agent deny，硬边界与防递归 deny 保留。
- 稳定 assembly / 可恢复 runtime metadata、派发失败清理与父子隔离。
- Rule keywords/tool/path 条件、现有 opt-in/Agent scope、每请求完整快照。
- 现有 messages.transform、Skill loader、recovery 与 context dump 集成。
- SDK 类型/transport、并行事件、真实 plugin restart/resume/compaction 集成验证。
- 配套 ontology DESIGN 契约同步。

## Out of Scope

- 新的 Ellamaka Plugin hook、公开 Session API、独立 permission evaluator 或 capability registry。
- exact-set/subtract、会话期间修改冻结的授权集合。
- LLM intent classifier、未知工具路径猜测、工具执行前的 Rule 强制拦截。
- 新增 Chat 持久注入追踪、合成消息自动过期机制或完整 provider request recorder。
- 重做 Skill catalog、Skill body loader 或强制每轮加载所有 Skill。
- CLI discovery、空间物化/sync、沙箱/profile 的设计与放宽。

## Affected Files

| Component | Range | Role |
|---|---|---|
| SDK boundary | wopal-plugin dependencies/types/client adapter | published v2 typed calls and transport reuse |
| Task dispatch | wopal_task / task manager / launcher | declarations, validation, group expansion, create-before-prompt |
| Runtime context | rules discoverer/matcher/formatter, message/command/event hooks | tool/path conditions, independent request-tail synthetic snapshot |
| Recovery state | Session metadata / SessionStore | stable assembly, mutable facts, concurrent update/rebuild |
| Tests | plugin task/rule/context/lifecycle integration suites | grant/isolation/recovery/dump evidence |
| Design | docs/DESIGN-capabilities.md, docs/DESIGN-wopal-plugin.md | explicit grant overrides, groups, reuse existing hooks |

## Acceptance Criteria

### Agent Verification

1. [ ] 正式发布 SDK v2 支持 Session permission/metadata 与三类 discovery；typed client adapter 在 in-process 和 authenticated HTTP 中保持路由/认证；不能用 v1 强转补字段。
2. [ ] 无 capabilities 时保留角色默认能力与正常派发；Skill/独立 Tool/共享组只授予目标 Session，父/兄弟不受影响；声明空数组不会撤销 Skill/Tool baseline。
3. [ ] 无效身份、隐式共享组、禁授递归工具、Rule 跨作用域或关闭模块时请求 Rule，均在创建和分配资源前失败；launch 后的失败/清理结果可验证且不会影响其他 Session。
4. [ ] edit 组必须显式声明，结果与 metadata 展示所有成员及 permission 规则；Agent deny 可被任务 allow 覆盖，但沙箱/profile 不提升、防递归 deny 始终最后生效。
5. [ ] create 同时携带稳定 permission/assembly；首轮 promptAsync 不传 tools rewrite，授权集合在后续 step/compaction 保持不变。
6. [ ] rules.enabled 与 Agent scope 生效；省略 rules、rules=[] 与显式非空选择可区分；无 match 的旧 keywords 规则保持条件匹配语义。
7. [ ] 新 Rule 条件验证同组 OR、跨组 AND、同一调用的 tool/path、最近终态批次、新用户清空、glob 零目录/多目录、路径不明/空间外及错误工具调用；不会声称影响已经执行的操作。
8. [ ] 同一规则连续两个模型 step 都出现在各自请求末尾，各请求只有一份；规则变更/移除、正文变化、空集合均正确；旧历史/system/tools 不变、临时快照不在 DB、MAX_STEPS guard 在快照之后。
9. [ ] Skill 清单由引擎根据 Session 权限生成；未调用无正文注入，成功调用按需加载。loadedSkills 恢复事实不授权其他 Skill，不新建插件 loader。
10. [ ] 销毁旧插件并创建新实例后，从持久 metadata/消息恢复同样的授权与匹配；真实 compaction、并行工具同批次信号及 cache 清空不会丢条件或产生重复恢复提醒。
11. [ ] context dump 能导出临时 synthetic 及命中原因，DB 无该快照；插件重启后重新请求可再次观察；不将模型自述当作真实注入证据。
12. [ ] wopal-plugin 受影响测试、typecheck/build 与正式 SDK 契约检查通过；关联 DESIGN 已同步，无失效 hook 依赖。

### User Validation

#### Scenario 1: 任务授权与动态 Rule 的真实使用

- Goal: 体验任务声明与实际能力、规则指导的一致性，观察真实工具流程中的追加上下文。
- 验证环境: 已交付 Session-aware Skill 修复的 Ellamaka，加当前 ontology feature 验证视图；空间已开启 rules.enabled，准备符合目标角色作用域的 keywords 与 tool/path 测试 Rule。
- Precondition: 准备一个角色 baseline 未允许的已安装 Skill 和可独立授权的 Tool；共享 edit 组测试与前两项区分，避免拿 baseline 已有的能力声称验证了新增授权。
- 启动命令: `cd projects/ellamaka && WOPAL_PLUGIN_LOG_MODULES=context ./scripts/dev.sh tui`。
- User Actions:
  1. 同角色派发 A/B：A 声明额外已安装 Skill、独立测试 Tool 和显式 edit 组，B 不声明；检查返回的完整授权范围和实际 Skill/Tool 使用。
  2. A 执行不匹配路径的工具，再执行匹配 tool/path 的工具。检查下一次模型请求的 dump：只有匹配 Rule，具有明确原因，原消息内容保持；同一有效集合连续请求仍存在且不重复。
  3. 由有 context_manage 权限的父会话调用 `context_manage(action="dump", session_id="<A>", detail=true)`，读取返回文件；不为观察临时扩大子 Agent 的 context_manage 权限。
  4. 对 A 执行 compaction 或重启/恢复，再继续任务。检查重新生成的 dump 与工具使用；B 的权限/状态不被污染。
- 通过判据: 任务 grant 与用户声明一致、共享组范围清楚；指导规则对实际任务有用，命中可在 dump 查证；恢复后继续工作，模型正常加载所需 Skill；自动化 AC 证明权限/生命周期内部不变量。
- 失败反馈: A/B Session ID、task 输入、工具结果、dump 文件与模型步骤定位信息。

- [ ] 用户已完成上述功能验证并确认结果符合预期

## Implementation

### Task 1: 正式 SDK v2 与 Session assembly 调用边界

**Verification Intent**: AC#1, AC#12

**Behavior**:
- published v2 contract exposes permission/metadata/discovery without fake type casts.
- in-process transport, directory/workspace and authentication reach the correct instance.
- existing v1 consumers remain routed through their own compatible adapter.

**Pre-read**: wopal-plugin package.json/types/index/client bridge，正式 SDK 2.0.8 v2 发布包，现有 task-launcher 与 Session API。

**Design**: 复用当前 v2 transport bridge，集中类型化 Session/discovery 适配；新调用只用 v2 请求 shape，不在每个调用点做跨版本强转。采用正式依赖，公开 API 缺口必须明确作为前置，不用私有引擎模块填补。

**TDD**: true

**Changes**:
1. RED：对正式 SDK 类型、in-process/authenticated HTTP 和 directory/workspace 路由建立契约失败测试。
2. GREEN：更新正式 SDK 依赖和内部 typed assembly adapter，保留现有 transport 行为。
3. REFACTOR：删除新调用链不必要的强转，记录现有 transport bridge 的集中兼容依赖，确保新适配没有丢认证头。

**Verify**: RED 阶段在 AC#1/12 回填真实 SDK 契约命令与插件 typecheck/build；已确认发布包只证明接口前置，不能代替运行时测试。

**Done**:
任务产出与实际触碰文件：实施时回填。
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤

### Task 2: Task declarations 与稳定 Session grants

**Verification Intent**: AC#2, AC#3, AC#4, AC#5, AC#12

**Behavior**:
- no capabilities preserves role baseline and dispatch; task allows can override baseline denies.
- edit group requires explicit declaration and reports all members; hard sandbox/profile and recursion limits remain.
- invalid declaration or Rule match schema causes no child/resource effects; post-create failures report real cleanup outcomes.
- immutable assembly and grant rules are stored before first prompt; no tools rewrite.

**Pre-read**: Task 1 adapter，wopal_task/task-launcher/manager，引擎 Tool permission gate 与 aliases，DESIGN-capabilities。

**Design**: normalize → discovery validate → compile allow/group + final recursion deny → create with permission/metadata → prompt。生产统一错误、Rule match 声明校验与 metadata schema，供 Task 3 使用。明确软默认与硬边界；同步能力设计，避免重复权限求值系统。

**TDD**: true

**Changes**:
1. RED：覆盖 baseline、明确 deny 覆盖、groups、无效原子性、首次 prompt 保持、父子/兄弟隔离、不同失败阶段清理。
2. GREEN：接入声明、校验、编译、metadata 一次创建和 structured launch result，去除首轮 tools 重写。
3. REFACTOR：统一 supported grant mapping、禁止项、错误/清理结果与确定性输出；同步 DESIGN-capabilities 的授权语义。

**Verify**: RED 阶段在 AC#2–5 回填真实 task/permission 集成命令，最终运行受影响测试/typecheck/build。

**Done**:
任务产出与实际触碰文件：实施时回填。
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤

### Task 3: Tool/path Rule conditions 与逐请求 synthetic 快照

**Verification Intent**: AC#6, AC#7, AC#8, AC#12

**Behavior**:
- old keywords rules retain opt-in/scope behavior; explicit task candidate set is applied.
- tool/path match uses the same terminal signal and influences the next request only.
- parallel signals persist without loss; new real user input clears old batch.
- unchanged rule set appears once on every request; changed/empty set affects only current tail, no old-history mutation.

**Pre-read**: Task 2 metadata / Rule match 声明 schema，rules discoverer/matcher/formatter，message/command/event hooks，现有 dump，Ellamaka messages.transform/模型转换/步数保护。

**Design**: 使用 Task 2 生产的 match 声明 schema 扩展既有发现/匹配器，规范化有限支持的 tool/path 信号并保存恢复事实。替换 lastRulesPrompt 发送抑制，以每请求派生快照追加一个 synthetic user message；digest 只缓存正文解析。更新 DESIGN-wopal-plugin 的复用钩子、条件/时序/生命周期契约。

**TDD**: true

**Changes**:
1. RED：覆盖开关/作用域、AND/OR、同信号匹配、路径 glob/未知路径、成功失败/并行批次、连续步骤不丢 Rule、旧历史不变及 MAX_STEPS。
2. GREEN：实现 Rule metadata 条件、信号持久化与每请求尾部追加，保留其他注入职责。
3. REFACTOR：统一来源/命中原因与内容 digest，防止重复 snapshot/recovery；同步设计中的 obsolete hook 依赖。

**Verify**: RED 阶段在 AC#6–8 回填真实 matcher/hooks/Session request 集成测试命令。

**Done**:
任务产出与实际触碰文件：实施时回填。
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤

### Task 4: Skill 恢复、真实生命周期与 context dump 收口

**Verification Intent**: AC#9, AC#10, AC#11, AC#12

**Behavior**:
- engine-owned Skill catalog/loading works with child grants; unselected Skill body is not eager injected.
- successful loaded names and tool/path facts rebuild after actual plugin dispose/recreate, resume and compaction.
- parent/sibling isolation and deterministic per-request snapshots survive cache clearing.
- dump shows transient injection while DB omits it; old pre-restart transient data is not falsely reported as persisted.

**Pre-read**: Task 2/3 schema/hooks，existing Skill loader、loadedSkills/recovery 路径，dump-formatter、真实 Session/lifecycle 测试设施。

**Design**: 用真实父/子/兄弟 Session 和独立插件实例验证，不用同一 closure 第二次调用冒充 restart。成功 Skill 加载事实供恢复提示使用，现有 loader 继续授权/加载；元数据和消息是事实源，cache 仅派生。context dump 为观察入口，不新建持久注入轨迹。

**TDD**: true

**Changes**:
1. RED：覆盖实际 dispose/recreate、压缩丢 retained tool history、并行事件、加载成功/失败、隔离、dump/DB 差异与重复恢复提示。
2. GREEN：修复实测暴露的 state reconstruction/recovery/dump 接线缺口。
3. REFACTOR：跑全量受影响测试/typecheck/build，回填 AC/Done 与真实证据，核对公开接口和相关设计一致性。

**Verify**: RED 阶段在 AC#9–12 回填生命周期/集成/dump 测试与质量门禁真实命令。

**Done**:
任务产出与实际触碰文件：实施时回填。
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤

## Delegation Strategy

| Wave | Task | 执行者 | 依赖 | 委派理由 |
|---|---|---|---|---|
| 1 | Task 1 | fae | 引擎 Skill 清单修复交付 | 正式客户端契约先行 |
| 2 | Task 2 | fae | Task 1 | 生产后续复用的授权与 metadata schema |
| 3 | Task 3 | fae | Task 2 | Rule 条件与请求快照依赖持久事实 |
| 4 | Task 4 | fae | Task 2–3 | 在完整链路上证明恢复、隔离和观察能力 |

## Delivery Dependency

保持 draft，等待用户评审本次优化版本并明确批准 ontology 实施。引擎侧必须已经交付可运行的 Skill 清单权限修复；SDK 使用正式发布的 v2 入口，不依赖新增 Plugin hook。能力实现与 stage 转换按 ontology-evolution 执行，本次提案优化不创建实施 worktree、不进入 implementing。

## Revision Evidence

2026-10-07 用户已确认：保留 tool/path 条件；共享工具权限组显式声明并展示整组范围；任务授权允许覆盖 Agent deny，仅保留沙箱/递归派发等硬限制。

现有 mechanisms 已经能临时追加普通/synthetic 消息，并通过 context dump 观察；因此提案撤除 request-context hook 前置。提案明确下一请求匹配时机、每请求发送、rules 开关/作用域、正式 SDK v1/v2 区别及未启动失败/不确定状态的清理语义。

# {plan_name}

## Metadata

- **Issue**: #{issue}
- **Type**: {type}
- **Target Project**: {project}
- **Product**: {product}
- **Phase**: {phase}
- **Project Path**: {path}
- **Project Type**: {ptype}
- **Created**: {date}
- **Status**: planning
- **Base Commit**: (approve 时自动记录实施基线,集成分支 HEAD)
- **Final Commit**: (verify 时自动记录合入提交,集成分支 HEAD)


## Scope Assessment

- **Complexity**: Low|Medium|High
- **Confidence**: High|Medium|Low

## Goal

一句话描述本计划要达成的目标。

## Technical Context

<!-- 4 个子节均为可选，至少填写一个。简单任务只填 Architecture Context 即可。 -->

### Architecture Context

<!-- 当前架构现状、涉及模块、为什么需要变更。 -->
<当前架构描述，涉及模块，为什么需要变更>

### Research Findings

<!-- 前期研究结论摘要。参考资料只放上下文文档，不放本项目 DESIGN、源文件、配置文件。 -->
<研究结论摘要>

**参考资料**：
- `<上下文文档路径>`

### Key Decisions

<!-- 已确定的技术决策，使用 D-NN 编号格式。 -->
- D-01: <决策内容及理由>

### Key Interfaces

<!--
  对外契约章（硬约束）。入册门槛：跨模块、跨项目、对外的接口——CLI 命令、
  API 端点、事件、schema、导出的类型。模块内部私有函数禁止入册。

  定义到什么程度：签名 + 错误码 + 关键语义（幂等/版本/失败行为），
  用项目自己的语言写（TS interface / Python type / JSON Schema 均可）。

  判据：下游能只凭这一节写出消费方代码和兼容测试，才算定准。

  约束力：入册即红线。实施中要改这里的签名或错误码，必须先回报修订
  Plan，禁止静默改。没有对外契约时写 N/A。
-->
<契约定义，无则 N/A>

## In Scope

列出本次要完成的具体内容：

- 功能点 1
- 功能点 2

## Out of Scope

列出本次不做的内容：

- <本次不做的内容及原因>

## Affected Files

<!--
  预计涉及范围，不是施工清单。实施中允许偏离：实施 Agent 按实际
  实现调整文件选择，Done 时在 Task 内记录实际触碰的文件。
-->
| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| <component> | `file1`, `file2` | 修改/创建/删除 | <在此变更中的作用>

## Acceptance Criteria

<!-- 审阅者先看成功标准，再看实现细节。详见 plan-guide.md 的 AV/UV 规则。 -->

### Agent Verification

<!--
  两拍制（Two-beat AC）：
  第一拍（Plan 阶段，现在写）：每条 = 行为判据 + 通过标准。写"系统
  表现出什么可观察行为、看到什么算过"，允许判据式（不用猜未来
  的测试文件名）。判据必须可判定——能抓住坏实现，不能怎么写都能过。
  第二拍（RED 阶段，实施时回填）：实施 Agent 把每条 AC 落成真实
  命令（如 `python -m pytest tests/xxx/ -v` 全绿），原地更新本节。
  已勾选的 AC 必须是命令式，否则 complete 会被拦下。

  每条必须映射回 Task 的 Verification Intent。
-->
1. [ ] <行为判据 + 通过标准，如「runner 一致性测试全绿，后台无交互死等」>
2. [ ] <行为判据 + 通过标准>

### User Validation

<!--
  用户验证边界（强制）：
  1. 只能列入 Agent 无法自动验证、必须由用户手动执行并观察的项。
     任何可自动化验证的内容（测试、lint、typecheck、静态检查、可脚本断言的行为）禁止放这里。
  2. 每个场景必须具备完整的验证环境：场景、环境准备、可执行命令、通过判据。
     验证所需的环境/机制如果项目规范还没有，必须先补入项目 AGENTS.md（或本 Plan 前置任务），再引用。
  3. 没有用户可执行命令、或只有通用描述的验证项不得通过 submit 校验。
-->

#### Scenario 1: <本次变更影响的可感知行为>
- Goal: <用户通过本次手动验证要确认的行为>
- 验证环境: <运行环境引用：项目规范中的验证机制章节，或 README/脚本入口>
- Precondition: <前置条件：已构建/已启动/沙箱已就绪，指明准备命令>
- 启动命令: <一条用户可直接复制执行的真实命令，含必要的环境变量>
- User Actions:
  1. <用户操作步骤 1>
  2. <用户操作步骤 2>
- 通过判据: <用户可观察到的具体预期结果，可断言；禁止"行为一致"等空泛描述>
- 失败反馈: <验证失败时用户应提供什么，如日志文件路径或 `git diff -w` 输出>

- [ ] 用户已完成上述功能验证并确认结果符合预期

## Implementation

<!--
  Task 拆分维度：行为组，不是文件。一个 Task = 一组高内聚 Behavior +
  完整的 RED→GREEN→REFACTOR + 独立可跑的 Verify。
  粒度三问：这组 Behavior 共享同一批测试吗？一次委派一个 fae 上下文
  装得下吗？Verify 能独立执行吗？

  Plan 阶段写清行为规格和设计意图；文件路径、内部 API、测试组织
  由实施 Agent 在最新代码上决定。详细指导见 plan-guide.md。
-->

### Task 1: Task Title

**Verification Intent**: <引用的 Agent Verification 条目编号，如 AC#1, AC#3>

**Behavior**: 
<!--
  可测试的行为规格（TDD=true 时必填，写法自由：输入→输出映射、
  Given/When/Then 均可）。判据：实施 Agent 能不猜地把每条 Behavior
  直接写成一个失败测试。写不出测试的 Behavior = 没写清楚。
-->
- <给定条件/输入 → 可观察结果，如 valid_email("user@example.com") → true>
- <边界/失败行为，如 缺凭证 → readiness 在建 worktree 前失败>

**Pre-read**: <实施前需阅读的文件路径，无必要可写 N/A>

**Design**:
<!-- 完整实施设计（必填）：技术方案、关键思路、约束。设计意图和边界写清楚；不规定到每个文件怎么改。 -->
<完整实施设计>

**TDD**: true

<!-- true：代码 Task，Behavior 必填；false：非代码 Task，需说明理由。 -->

**Changes**:
<!-- 
  编号列表格式，禁止 checkbox。
  第 1 条固定语义：把本 Task 全部 Behavior 落成失败测试并确认失败（RED）。
  后续条目描述 GREEN/REFACTOR 的意图，不逐文件铺陈。
-->
1. RED：将上述 Behavior 全部落成失败测试并确认失败
2. <GREEN：实现至测试全绿的关键步骤>
3. <REFACTOR：如需清理>

**Verify**:
<!-- 可执行命令。Agent 必须运行看到 exit 0 后才能勾选 Done。 -->
<验证命令，如 `cd projects/xxx && pnpm test:run` 全部通过>

**Done**:
<!-- 任务产出说明 + 要求委派的子 agent 实施后勾选, 每完成一个 task  后提交 git。 -->
任务产出：<一句话描述本 Task 产出>
实际触碰文件：<实施后回填实际修改的文件列表>
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

## Delegation Strategy

<!--
  Plan 有 2+ Task 或 Complexity = High 时必须填写。单一 Task 可写 N/A。
  用 wave 划分并行批次，高 wave 依赖低 wave。详见 plan-guide.md。
-->

| Wave | Task | 执行者 | 依赖 | 委派理由 |
|------|------|--------|------|---------|
| 1 | Task 1 | fae | 无 | <委派理由> |

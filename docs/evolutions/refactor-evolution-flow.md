# refactor-evolution-flow

## Metadata

- **Type**: refactor
- **Project Path**: .wopal
- **Created**: 2026-09-27
- **Stage**: draft
- **Mode**: (accept 时记录：isolated | quick)
- **Worktree**: (accept 时记录)
- **Branch**: (accept 时记录)
- **Base Commit**: (accept 时记录)
- **Final Commit**: (integrate 时记录：集成到空间分支后的提交)

## Goal

把 `ontology-evolution` 技能对齐到**优化后的 wopal-cli 流程**（Issue #240，实施中），使这条链路成为技能里可直接照做的明文：

```
实施不提交 → 主控验证并记录 → 每完成一个 task 一次提交（该 task 代码 + 提案更新）
→ rook 实施评审 → 询问用户选择验证方式（优先推荐分支切换：把 `.wopal` 切到隔离分支观察，验证后切回）→ 用户确认 → integrate → 归档
```

依赖：**Issue #240**（六项：去覆盖式 sync / `advance` 即时镜像 / 主控单提交 / 验证切换（分支切换：`.wopal` ↔ 隔离分支）/ `integrate` 用户门控 / `--paths` 示例修正）。#240 落地前本提案不得实施；两者行为分叉时先修订本提案。本提案只改技能文档，不实现 CLI。

## Technical Context

### 问题（Problem）

- **记录协议缺失**：谁填 Done、写在哪、什么时候写——技能里没有，实际做法靠考古 git 历史。
- **角色×命令矩阵缺失**：每个动作由谁执行（实施 agent / 主控 / rook / 用户）无明文，靠推断。
- **并行实施规范缺失**：同一隔离工作区多任务并行时的提交纪律每轮手抄进委派 prompt。
- **评审门与集成门缺失**：技能把评审写成「用户想看才做」的可选项；`integrate` 无用户确认门，验证被迫在集成之后。
- **`--paths` 基准未定义**：示例带 `.wopal/` 前缀，照抄会被拒绝。

### 方案（Solution）

技能文档按优化后的 CLI 写死四条规则 + 配套规范：

1. **记录**：唯一作者 = 主控；位置按模式（isolated = 隔离工作区副本；quick = 空间工作区副本）；时机 = 验证通过后、提交前；实施 agent 不编辑提案文件。
2. **提交**：实施不提交；**每完成一个 task 一次提交**——主控把「该 task 的代码 + 提案文件更新（完成勾选、回填记录）」作为一个提交，落在工作分支（isolated = 隔离分支；quick = 空间分支）；不跨分支；并行在途时用 `--paths` 点名本任务文件 + 提案文件。
3. **评审门**：全部任务 + 主控验证之后、邀请用户验证之前，强制 rook 实施评审（2 轮预算，首轮列全）。
4. **验证与集成门**：评审通过后**先询问用户选择验证方式，优先推荐分支切换**——把 `.wopal` 切到隔离分支（运行时直接加载特性分支内容），用户观察后切回；备选「先集成后验证」（用户显式选择）。`integrate` 仅在用户明确确认后执行。

配套：角色×命令矩阵（九项动作）、runbook 时序重排、**命令用法实操段（逐步可复制命令 + 端到端示例）**、并行实施规范、验证切换操作表述、`--paths` 基准修正、模板与 AGENTS 注记。

## In Scope

- `.wopal/skills/ontology-evolution/SKILL.md`：角色×命令矩阵（new / accept / advance / commit / integrate / archive / 记录回填 / 实施评审 / 集成门控，九项）；runbook 重排（逐行执行者 + 评审/验证/确认/集成时序 + 每任务一次提交）；新增记录协议、并行实施规范与**命令用法实操段**（逐步可复制命令、运行目录与预期结果、端到端示例）；状态机评审句修订；**验证切换操作表述**（分支切换：评审通过后先询问用户、优先推荐该方式；何时切、切什么、如何切回）。
- `.wopal/skills/ontology-evolution/references/commands.md`：`--paths` 基准（被提交侧工作区根）与正确示例；记录/评审/集成流程表述（引用 #240，不展开实现）。
- `.wopal/skills/ontology-evolution/templates/proposal.md`：`Done` 段记录归属注记。
- `.wopal/skills/ontology-evolution/AGENTS.md` §3：记录归属与提交粒度两条长期边界。

## Out of Scope

- CLI 实现（#240，实施中）；`DESIGN-evolution.md` 契约修订随 #240。
- 其他 evo 命令（`new` / `status` / `check` / `accept` / `advance` / `archive`）行为不变。
- assembly 装配机制；`space sync` / `ontology contribute`（交付终端，用户拍板）。

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| 技能主文档 | `skills/ontology-evolution/SKILL.md` | 修改 | 矩阵、runbook、记录协议、并行规范、验证切换/评审门/集成门 |
| 命令参考 | `skills/ontology-evolution/references/commands.md` | 修改 | `--paths` 基准与示例、流程表述 |
| 提案模板 | `skills/ontology-evolution/templates/proposal.md` | 修改 | `Done` 段记录注记 |
| 技能开发规则 | `skills/ontology-evolution/AGENTS.md` | 修改 | 记录归属与提交粒度 |

## Acceptance Criteria

### Agent Verification

1. [ ] **矩阵与 runbook**：`SKILL.md` 有角色×命令矩阵（九项动作各有执行者与条件）；runbook 逐行标注执行者、含「评审 → 用户验证 → 用户确认 → `integrate`」时序、无裸命令行。验证：`rg` 命中矩阵与 runbook 标注。
2. [ ] **记录与提交**：五条断言命中——① 唯一作者 = 主控；② 位置按模式（isolated = 隔离工作区副本 / quick = 空间工作区副本）；③ 时机 = 验证后、提交前；④ 禁止项（实施 agent 不编辑提案；isolated 禁止空间侧记录提交）；⑤ 提交粒度 = **每完成一个 task 一次提交**（该 task 代码 + 提案更新同提交，落工作分支；并行在途时 `--paths` 点名本任务文件）。验证：逐条 `rg` 命中。
3. [ ] **并行实施规范**：四项命中——`--paths` 的省略语义（= 全部已跟踪改动 + 提案文件）与三种显式例外（新文件 / 收子集 / instant）；并发被拒原样重试；不处置他人文件；工作区保护禁令（禁 `reset` / `checkout` / `restore` / `clean` / `stash`）。验证：逐条 `rg` 命中。
4. [ ] **评审门与验证/集成门**：状态机不再含 "happens when the user asks" 类可选表述；评审为强制门（含 2 轮预算）；**验证方式选择**：评审通过后先询问用户、优先推荐分支切换（切出/切回的步骤可照做）；`integrate` 标注用户门控。验证：`rg -n 'happens when the user asks' .wopal/skills/ontology-evolution/SKILL.md` 零命中 + 「分支切换」「询问用户」「集成门控」逐条命中。
5. [ ] **路径基准与注记**：`commands.md` 基准句（被提交侧工作区根）存在、`--paths` 示例均不带 `.wopal/` 前缀；模板 `Done` 注记与 AGENTS 两条边界命中。验证：`rg` 逐条命中。
6. [ ] **旧表述零命中**：`sparse-safe, per task` 零命中；「实施不提交 / 每任务一次提交 / 落在工作分支」跨文件表述一致。验证：`rg` + 人工比对。
7. [ ] **命令用法实操段**：`SKILL.md` 含逐步可复制命令（每步标注运行目录与预期结果），并给出端到端示例：`accept` → 每任务 `commit`（代码+记录）→ 评审 → 验证（分支切换）→ `integrate` → `archive`。验证：`rg` 命中命令序列与目录标注。

### User Validation

#### Scenario: 冷读复述完整流程（重启加载）
- Goal: 只读 `SKILL.md` 的新会话能无歧义复述完整流程（记录作者、提交者与落点、评审时机与执行者、验证方式选择、集成条件）。
- 验证环境: 本空间 dev 构建；重启后开新会话（不给本提案与历史上下文）。
- 启动命令: `cd projects/ellamaka && ./scripts/dev.sh tui`
- User Actions:
  1. 重启 TUI、新开会话，要求 agent「只读 `.wopal/skills/ontology-evolution/SKILL.md`，口述 isolated 模式下两个并行 task 的完整流程：每步谁执行、记录写在哪、**每个 task 提交什么、怎么提交**、评审何时由谁做、集成在什么条件下执行，并给出每步**可直接复制**的命令（含分支切换怎么切、怎么切回）」；
  2. 追问五问：「实施 agent 能不能自己改提案？」「`--paths` 带不带 `.wopal/` 前缀？」「集成由谁在什么条件下发起？」「评审能不能跳过？」「验证前要做什么？用哪种验证方式？」
- 通过判据: 复述与 SKILL.md 一致；五问均唯一答案（不可；不带；仅用户确认后；不可跳过、2 轮预算；**验证前先询问用户、优先推荐分支切换，切出与切回步骤明确**）；**能给出每步可直接复制的命令序列（含运行目录与预期结果）**；技能加载无报错、新流程各节在加载内容中可见。
- 失败反馈: 贴出完整回答并指明与哪条文档冲突。

- [ ] 用户已完成上述功能验证并确认结果符合预期

## Implementation

### Task 1: SKILL.md 流程重写（矩阵 + runbook + 记录协议 + 并行规范 + 验证切换/评审门/集成门）

**Verification Intent**: AC#1、AC#2、AC#3、AC#4、AC#7

**Behavior**:
- 角色×命令矩阵：九项动作（new / accept / advance / commit / integrate / archive / 记录回填 / 实施评审 / 集成门控）各有唯一执行者与触发条件；
- runbook：逐行标注执行者，含「实施不提交 → 主控验证并记录 → 每任务一次提交（代码+提案更新）→ rook 评审 → 用户验证 → 用户确认 → `integrate`」时序；quick 分支差异单列；
- 每任务一次提交：并行在途时 `--paths` 点名本任务文件 + 提案文件；串行/独占时可省略；
- 记录协议节：见方案规则 1 的四条断言；isolated 模式给出「为何不写空间侧」的耐久理由（记录无法随工作分支回滚；空间侧未提交会阻塞 `integrate`；两侧分叉会冲突）；
- 并行实施规范节：提交默认可省略 `--paths`（= 该工作区全部已跟踪改动 + 提案文件）；仅三种例外显式——纳管新文件、并行在途时收子集、instant 模式；并发被拒重试；不处置他人文件；工作区保护禁令；
- 状态机一节：删除 "Review … happens when the user asks for it" 可选句，改为「`implementing` 内的强制门（全部任务 + 主控验证之后、邀请用户验证之前）」；
- 验证与集成门表述：评审通过后**先询问用户选择验证方式、优先推荐分支切换**（把 `.wopal` 切到隔离分支观察，验证后切回，步骤可照做）；备选「先集成后验证」；`integrate` 仅在用户确认后执行；
- 命令用法实操段：逐步可复制命令（运行目录 + 预期结果）+ 端到端示例（`accept` → 每任务 `commit` → 评审 → 验证（分支切换）→ `integrate` → `archive`）。

**Pre-read**: `.wopal/skills/ontology-evolution/SKILL.md`（全篇）；`.wopal/docs/evolutions/refactor-plugin-config-consumption.md`（记录实际填写形态参照）

**Design**: 以优化后的 CLI 流程（#240）为唯一蓝本；矩阵是「谁跑什么」的唯一真相源，runbook 只做时序叙述；记录与并行两节独立成节。不描述 CLI 尚未具备的行为——依赖统一引用 #240。

**TDD**: false（文档重写；判据为可 grep 的文本契约）

**Changes**:
1. 起草角色×命令矩阵（九项动作 × 执行者 / 条件）。
2. 重排 runbook：逐行执行者 + 评审/验证/确认/集成时序 + 每任务一次提交 + quick 差异行。
3. 新增记录协议、并行实施规范、命令用法实操段；修订状态机评审句与验证/集成门表述（含分支切换与询问用户）。
4. 自查 AC#1-4、AC#7 逐条命中。

**Verify**: `rg -n 'happens when the user asks' .wopal/skills/ontology-evolution/SKILL.md` 零命中；`rg -n '主控|唯一作者|实施评审|集成门控|每完成一个 task' .wopal/skills/ontology-evolution/SKILL.md` 命中协议、门控与提交粒度表述；用法段含端到端命令序列；「分支切换」「询问用户」相关表述命中。

**Done**:
任务产出：待实施后回填。
实际触碰文件：待实施后回填。
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤

### Task 2: references/commands.md（`--paths` 基准 + 流程表述）

**Verification Intent**: AC#5

**Behavior**:
- 明确基准 = 被提交侧工作区根（isolated = 隔离工作区；quick / instant = `.wopal`）；`.wopal/` 前缀会被判 invalid 拒绝（错误码 `SPACE_EVO_COMMIT_TARGET_INVALID`）；
- 补一条可照抄的正确示例；文档内所有 `--paths` 示例均按该基准书写；
- 补记录/评审/集成流程表述：记录编辑由主控在工作区副本执行、随代码单提交；评审与验证切换/集成门控一句引用 #240。

**Pre-read**: `.wopal/skills/ontology-evolution/references/commands.md`（`commit` 节）

**Design**: 基准定义放 `commit` 节 `--paths` 首次出现处（三态一句话）；流程表述交叉引用 SKILL.md，避免两处各写一套。

**TDD**: false（文档修正）

**Changes**:
1. 补基准定义与反例（含错误码）。
2. 补正确示例。
3. 补流程交叉引用；自查与 SKILL.md 一致。

**Verify**: `rg -n -- '--paths' .wopal/skills/ontology-evolution/references/` 无 `.wopal/` 前缀示例；基准定义句存在；`SPACE_EVO_COMMIT_TARGET_INVALID` 命中。

**Done**:
任务产出：待实施后回填。
实际触碰文件：待实施后回填。
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤

### Task 3: templates/proposal.md 注记 + AGENTS.md 同步

**Verification Intent**: AC#5、AC#6

**Behavior**:
- `templates/proposal.md` 的 `Done` 段以 HTML 注释补注记：记录段整体（完成勾选 + 任务产出 + 实际触碰文件）由主控在工作区分支的提案副本填写；实施 agent 不编辑提案文件任何部分；注记不引入尖括号占位符（不得触发占位符扫描）；
- `AGENTS.md` §3 增加记录归属与提交粒度两条长期边界。

**Pre-read**: `.wopal/skills/ontology-evolution/templates/proposal.md`（`Done` 段）；`.wopal/skills/ontology-evolution/AGENTS.md` §3

**Design**: 注记措辞与 SKILL.md 记录协议逐句对齐；AGENTS 只收长期边界，不复制流程细节。

**TDD**: false（文档修改）

**Changes**:
1. 模板 `Done` 段加注释注记。
2. `AGENTS.md` §3 加两条边界。
3. 自查：未新增未替换占位符。

**Verify**: `rg -n '主控' .wopal/skills/ontology-evolution/templates/proposal.md .wopal/skills/ontology-evolution/AGENTS.md` 命中；占位符扫描无新增。

**Done**:
任务产出：待实施后回填。
实际触碰文件：待实施后回填。
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤

## Delegation Strategy

三个 Task 文件不相交（SKILL.md / commands.md / 模板+AGENTS），**一波并行**；均依赖 #240 落地后实施。本提案自身按其定稿流程实施：实施不提交 → 主控验证并记录 → 单提交 → rook 评审 → 用户确认后集成。

| Wave | Task | 执行者 | 依赖 | 说明 |
|------|------|--------|------|------|
| 1 | Task 1 SKILL.md 重写 | fae | #240 已落地 | 主文档，动作最全 |
| 1 | Task 2 commands.md | fae | #240 已落地 | 文件不相交，并行 |
| 1 | Task 3 模板 + AGENTS | fae | #240 已落地 | 文件不相交，并行 |

并行纪律：每任务提交时，工作区有并行在途 → `--paths` 点名**本任务文件 + 提案文件**（不得省略，否则扫入他人改动）；串行/独占时可省略；纳管新文件必须点名；并发被拒原样重试；禁自行处置他人文件与工作区状态（工作区保护禁令块随委派 prompt 下发）。

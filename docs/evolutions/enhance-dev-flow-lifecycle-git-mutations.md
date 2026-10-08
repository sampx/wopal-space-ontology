# enhance-dev-flow-lifecycle-git-mutations

## Metadata

- **Type**: enhance
- **Project Path**: .wopal
- **Created**: 2026-10-02
- **Stage**: validating
- **Mode**: isolated
- **Worktree**: .worktrees/ontology-enhance-dev-flow-lifecycle-git-mutations
- **Branch**: ontology-enhance-dev-flow-lifecycle-git-mutations
- **Base Commit**: 8c8ead1a6de4f6a5f9bb3b887ba14cd206c1fd46
- **Final Commit**: 327d1ca8a228c18e415eaa6d1de14fc8dcebeeb0

## Scope Assessment

- **Complexity**: Medium — 改动集中在 dev-flow 生命周期命令、共享 Git helper、技能说明和测试；不改变任何特定 Harness 的沙箱实现，但需统一 Git mutation 前的 Agent 执行约束、错误透明性与事务顺序。
- **Confidence**: High — 已实证 approve / complete / archive 存在跨仓库 Git metadata mutation；`commit_paths` 会吞 `git add/commit` stderr；complete 在 commit 失败后仍可继续并成功退出；archive 在 archive durability 之前删除 worktree/branch，且部分 `git add/commit` 结果未检查。本体已有跨引擎权限边界：Agent `sandbox_escalation: ask`，Fae 明确“沙箱环境必要时向委派者申请提权”，dsh adapter 也明确 escalation 由各引擎沙箱/审批层承接。

## Goal

让通用 dev-flow 在 ellamaka、DeepSeek harness、OpenCode、Codex 及其他执行引擎中保持同一生命周期语义：Agent 在执行需要 Git metadata mutation 的生命周期命令前，使用**当前 Harness 自己提供的权限/提权机制**确保命令具备所需权限；dev-flow 本身不感知具体 Harness，只保证 Git mutation 失败不被吞掉、关键状态不在 durability 失败后继续推进、破坏性清理不早于持久化成功。

## Technical Context

### Architecture Context

dev-flow 是跨引擎通用技能。它不能假设某个 Harness 存在 Codex 的 `workspace-write`、某种 approval API、某种 host broker，也不能通过脚本自行提权。本体已有清晰分层：

1. Agent 灵魂/权限声明表达**意图**：核心执行 Agent 具备 `sandbox_escalation: ask`；Fae 的通用 Tool Usage 明确“如果工作在沙箱环境，必要时向委派者申请提权”。
2. 不同 Harness/adapter 负责把 escalation 意图映射到自身机制。现有 `DESIGN-dsh-adapter.md` 明确：`sandbox_escalation` 不机械映射为 preset 工具，由沙箱策略/审批层承接。
3. dev-flow 技能负责告诉 Agent **哪些命令具有 Git control-plane mutation**，以及执行前应确保当前环境能完成这些 mutation；具体如何申请/获得权限由当前 Harness 决定。
4. dev-flow Python 实现只负责业务正确性与 fail-loud，不实现 sandbox detection、提权、sudo、Codex 特例或 Harness RPC。

当前 lifecycle mutation 至少涉及：
- `approve`：Plan repo commit/push + Target Project branch/worktree registration + workspace `.worktrees` checkout。
- `complete`：Plan 状态/Verification Commit 写入 + Plan repo commit + Issue sync。
- `verify`：Plan verification 结果 commit。
- `verify-switch`：checkout/worktree remove/prune + Plan commit。
- `archive`：Target Project worktree/branch cleanup + Plan `git mv`/commit/push + phase doc commit/push + Issue close。
- `submit` 等其他 lifecycle 入口需在实施时按实际调用链审计，不以命令名猜测。

### Research Findings

1. Codex 是暴露问题的一个环境，但不是 dev-flow 的设计中心。在该环境中，普通 workspace 文件可写不代表 Git metadata 可写，因此 Agent 必须使用 Codex 自己的 escalation/approval 能力；这一事实不应写进 dev-flow 的运行时实现。
2. ellamaka / DeepSeek harness / OpenCode 等可能没有同样的 Git metadata 限制，或具有不同的审批机制；通用技能只声明“需要 mutation 权限”，不能规定“outside sandbox rerun”“danger-full-access”等某一引擎动作。
3. `scripts/lib/git.py:commit_paths` 对 `git add` / `git commit` 使用 `capture_output=True`，失败只返回 `False`，导致底层 stderr 丢失；这是与 Harness 无关的通用缺陷。
4. `complete.py` 在 commit 失败时仅 warn，随后仍可 Issue sync 并 `return 0`；这是通用事务一致性缺陷。
5. `archive.py` 在 archive record durability 之前执行 worktree/branch cleanup，且存在未检查的 `git add` / commit 结果；这是通用 destructive-ordering 缺陷。
6. `approve` worktree fallback 可能用第二次失败覆盖第一次失败证据；root failure 与 rollback outcome 需要分层呈现。
7. “给 workspace 加 writable root”“修改 chmod”不是跨引擎解决方案；“默认 full access”也不应成为通用技能契约。

**References**:
- `.wopal/agents/fae.md`
- `.wopal/agents/wopal.md`
- `.wopal/docs/DESIGN-dsh-adapter.md`
- `.wopal/skills/dev-flow/scripts/commands/approve.py`
- `.wopal/skills/dev-flow/scripts/commands/complete.py`
- `.wopal/skills/dev-flow/scripts/commands/verify.py`
- `.wopal/skills/dev-flow/scripts/commands/verify_switch.py`
- `.wopal/skills/dev-flow/scripts/commands/archive.py`
- `.wopal/skills/dev-flow/scripts/lib/git.py`
- `.wopal/skills/dev-flow/scripts/lib/plan_commit.py`
- `.wopal/skills/dev-flow/scripts/lib/worktree.py`

### Key Decisions

- D-01 **Harness-neutral**：dev-flow 不检测“是否 Codex/OpenCode/ellamaka”，不实现任何 Harness 专属提权 API，不自动切换 sandbox mode，不调用 sudo，不定义 host broker。
- D-02 **Agent 在调用前负责获得执行能力**：dev-flow 技能把会产生 Git metadata mutation 的 lifecycle 命令标为“可能需要 sandbox escalation”。Agent 若处于受限环境，必须使用当前 Harness 原生的权限/审批机制申请必要权限后再执行；若当前 Harness 无限制则正常执行。
- D-03 **能力描述而非命令名单硬编码**：技能说明以 mutation surface（commit/index/refs/worktree/checkout/branch 等）解释为什么可能需要提权，并给出当前 lifecycle 命令清单作为事实性导航；未来命令新增 Git mutation 时必须同步该说明。
- D-04 **脚本不做权限探针协议**：不新增 `DEV_FLOW_PRIVILEGE_REQUIRED`、Codex-specific preflight 或通过临时 branch/worktree 探权。脚本执行真实操作；失败必须忠实、完整、非零地返回。
- D-05 **Git mutation fail-loud**：共享 helper 对失败保留 command（安全展示）、cwd、exit code、stdout/stderr；调用者不得把底层错误降格为裸 `False` 后继续成功路径。
- D-06 **durability before external progression**：生命周期状态只有在其要求的本地 Git durability 成功后才能继续 Issue sync/close 等外部 side effect。push failure 是否阻断按各命令既有契约处理，不借本案重定义远端策略。
- D-07 **destructive cleanup last**：archive 等命令的 worktree removal / branch deletion 必须后置到 archive record 已可靠持久化并满足既有远端门之后；执行期 cleanup 失败应报告“归档记录已持久化、清理未完成”，不得伪装成全量回滚。
- D-08 **root failure 优先**：approve 等带 rollback 的命令，root failure 与 rollback outcome 分层；rollback 失败不能覆盖原始错误。
- D-09 **跨引擎 UAT**：至少用一个无限制 host 环境验证正常路径，并用一个具备真实 sandbox/escalation 的 Harness 验证 Agent 会先申请其原生提权再运行 lifecycle mutation；Harness 选择不进入脚本实现。

### Key Interfaces

1. `SKILL.md` / `SKILL.zh-CN.md` 明确：执行 commit/index/refs/worktree/checkout/branch mutation 的 lifecycle 操作需要真实 Git metadata 写能力；受限环境下 Agent 应使用**当前 Harness 原生 escalation mechanism**，不得假定某一具体实现。
2. lifecycle Python 命令不接受 `--codex`、`--sandbox`、`--elevate` 等 Harness-specific 参数。
3. 任一关键 Git mutation 非零退出时，最终诊断保留 command、cwd、exit code 与原始非空 stdout/stderr，并以非零结果终止依赖该 mutation 的后续成功路径。
4. `complete` 的 Plan commit 失败后不得 Issue sync，不得返回成功；Plan 工作树状态应恢复到可重试的一致状态或明确报告未恢复状态。
5. `archive` 不得在 archive record 达到既定 durability point 前删除 Target Project worktree/branch；关键 stage/commit 失败不得 close Issue。
6. `approve` worktree 双尝试失败时保留首个根因；rollback outcome 不覆盖 root failure。
7. `verify`、`verify-switch`、`submit` 及其他实际 Git mutation 入口完成一致性审计：关键失败必须非零且不继续依赖它的外部/破坏性步骤。

## In Scope

- 更新 dev-flow 中英文技能/命令参考，声明 lifecycle Git mutation 的跨引擎权限要求与“由当前 Harness 负责 escalation”的通用规则。
- 审计 dev-flow lifecycle commands 的真实 Git mutation 调用链，不以 Codex 特例或命令名猜测。
- 修复共享 Git mutation helper 的 stderr/exit/cwd/command 丢失。
- 修复 complete 的 commit-failure-continues-success 缺陷。
- 修复 archive 的 destructive cleanup 时序与未检查 Git mutation 结果。
- 修复 approve 的 worktree fallback/root-failure 诊断保真。
- 对 verify / verify-switch / submit 等实际 mutation 入口补齐同类 fail-loud / no-invalid-progression 约束。
- 增加通用 deterministic tests 与跨引擎真实 UAT。

## Out of Scope

- 不修改 Codex、OpenCode、ellamaka、DeepSeek harness、dsh 或其他引擎自身的 sandbox/approval 实现。
- 不在 dev-flow 中新增 Codex-specific detection、`danger-full-access`、sudo、host RPC、broker 或自动提权。
- 不要求所有 Harness 采用同一种 escalation API/文案/配置。
- 不修改 Agent `sandbox_escalation` 的本体权限语义；现有 `ask` 与“必要时申请提权”已经提供正确抽象。
- 不把所有 Git 操作重构成大型 framework；只抽取 lifecycle 路径为保证错误透明与事务一致性所需的最小共享结构。
- 不改变 Plan 状态机、用户确认门、Issue 内容契约或与本问题无关的 push policy。
- 不执行 `space sync` / `ontology contribute`。

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| dev-flow skill | `.wopal/skills/dev-flow/SKILL.md`, `.wopal/skills/dev-flow/SKILL.zh-CN.md` | modify | 跨引擎 lifecycle Git mutation / escalation 指引 |
| command reference | `.wopal/skills/dev-flow/references/commands.md` | modify | 标记 mutation surfaces 与失败语义 |
| Git helper | `.wopal/skills/dev-flow/scripts/lib/git.py` | modify | mutation 失败诊断保真 |
| plan commit | `.wopal/skills/dev-flow/scripts/lib/plan_commit.py` | modify | commit/push 调用方错误传播 |
| worktree | `.wopal/skills/dev-flow/scripts/lib/worktree.py` | modify | worktree attempt/root cause 保真 |
| approve | `.wopal/skills/dev-flow/scripts/commands/approve.py` | modify | rollback/root failure 分层 |
| complete | `.wopal/skills/dev-flow/scripts/commands/complete.py` | modify | commit durability gate |
| archive | `.wopal/skills/dev-flow/scripts/commands/archive.py` | modify | destructive cleanup 后置、检查 mutation |
| other lifecycle | `.wopal/skills/dev-flow/scripts/commands/verify.py`, `verify_switch.py` 及审计确认的其他入口 | modify if needed | 同类一致性治理 |
| tests | `.wopal/skills/dev-flow/tests/python/**` | modify | mutation diagnostics / ordering / no-invalid-progression |

## Assembly Intent

| Ref | Scope | 理由 |
|-----|-------|------|

## Acceptance Criteria

### Agent Verification

1. [x] **跨引擎技能契约**：中英文 dev-flow 技能明确 lifecycle Git mutation 需要真实 Git metadata 写能力；受限环境要求 Agent 使用“当前 Harness 原生 escalation/approval mechanism”，正文不出现要求某一 Harness 的专属命令、配置或 API。（→ Task 1）
2. [x] **Git mutation 不吞错**：注入 `git add` / `git commit` / worktree mutation 非零退出，最终错误保留 command、cwd、exit code 与原始 stderr/stdout；关键调用方非零退出，不以裸 warn/False 继续成功路径。（→ Task 2）
3. [x] **complete durability gate**：Plan commit 失败时不执行 Issue sync、不返回 0；状态恢复或失败后可重试状态有 deterministic 测试覆盖。成功路径保持现有 executing→verifying 语义。（→ Task 3）
4. [x] **archive destructive ordering**：在 archive commit 前注入失败，断言 worktree/branch 未删除、Issue 未关闭；archive record 达到既定 durability point 后才允许 cleanup；cleanup 自身失败明确报告 partial cleanup，不伪装成未归档。（→ Task 3）
5. [x] **approve root-cause 保真**：worktree 双尝试失败保留首个失败证据；root failure 与 rollback outcome 独立；rollback 成败均不覆盖 root cause。（→ Task 3）
6. [x] **lifecycle mutation 全量审计**：对 `approve/complete/archive/verify/verify-switch/submit` 及实际调用链发现的其他 mutation 入口形成测试/代码结论；不存在“关键 Git mutation 失败但继续外部 side effect 并 return 0”的已知路径。（→ Task 4）
7. [x] **全量回归**：dev-flow Python suite 全绿；普通无限制 host 环境下既有 lifecycle 成功路径不退化。（→ Task 4）

### User Validation

#### Scenario 1: 受限 Harness 原生提权 + dev-flow lifecycle
- Goal: 验证通用技能能指导 Agent 在真实受限执行环境中使用该 Harness 自己的提权机制完成 lifecycle Git mutation，而 dev-flow 脚本本身无需知道 Harness 类型。
- Environment: 任一实际启用 sandbox/escalation 的 Agent Harness（可使用 Codex 作为当前可复现场景）+ 一个安全 scratch Plan。
- Precondition: scratch Plan 已到对应 lifecycle 前置阶段；Agent 已加载 dev-flow skill；记录 Plan repo / Target Project 的 HEAD、status、worktree/branch 状态。
- Launch command: 按该 Harness 正常方式让 Agent 执行 scratch Plan 的 lifecycle 命令。
- User Actions:
  1. 观察 Agent 是否依据 dev-flow 技能识别该操作需要 Git metadata mutation；
  2. 在当前 Harness 限制实际阻止 mutation 时，确认 Agent 使用**该 Harness 自己的** escalation/approval 流程，而不是要求 dev-flow 特殊参数或修改脚本；
  3. 批准后确认 lifecycle 命令成功，Git commit/worktree/branch 状态与 Plan 生命周期一致；
  4. 清理 scratch artifacts。
- Pass criteria: 受限 Harness 通过自身权限机制完成操作；dev-flow 输出/参数保持 Harness-neutral；无 `.git/index.lock` 等权限错误被吞掉或误报成功。
- Failure feedback: 提供 Harness 的权限请求/拒绝证据、dev-flow 完整 stdout/stderr、运行前后 Git/Plan 状态。

- [ ] The user has validated the behavior above and confirmed the result.

#### Scenario 2: 无额外沙箱限制的 Harness / host
- Goal: 验证新增权限指引不会让正常环境多出无意义的提权步骤。
- Environment: Mac Mini 原生 shell 或当前具备完整 repo Git mutation 权限的 Agent Harness。
- Precondition: 使用安全 scratch Plan。
- Launch command: 正常执行对应 lifecycle 命令。
- User Actions:
  1. 执行 approve/complete/archive 代表性路径；
  2. 确认环境已有权限时直接执行，不要求 Harness-specific escalation；
  3. 确认状态、commit、worktree/branch 与 Issue side effect 顺序正确。
- Pass criteria: 正常环境行为不退化，技能规则只在实际受限时要求 Agent 使用其 Harness 权限机制。
- Failure feedback: 提供完整 stdout/stderr 与前后状态差异。

- [ ] The user has validated the behavior above and confirmed the result.

## Implementation

### Task 1: 固化跨引擎 lifecycle mutation / escalation 技能契约

**Verification Intent**: AC#1

**Behavior**:
- Given Agent 加载 dev-flow；When 即将执行会修改 Git index/refs/worktree/branch 的 lifecycle 操作；Then 技能要求先确保当前执行环境具有所需能力，受限时使用当前 Harness 原生 escalation mechanism。
- Given 环境本身无限制；Then 不要求无意义提权。
- Given 不同 Harness；Then 技能不规定 Codex/OpenCode/ellamaka 专属 API。

**Pre-read**: `SKILL.md`、`SKILL.zh-CN.md`、`references/commands.md`、`.wopal/agents/fae.md`、`.wopal/docs/DESIGN-dsh-adapter.md`

**Design**: 在技能的执行纪律/生命周期命令说明中加入 capability-level guidance；沿用现有 `sandbox_escalation: ask` 抽象，不新增 permission vocabulary。命令参考列出实际 mutation surfaces，供 Agent 在不同 Harness 中决定是否需要申请权限。

**TDD**: false

**Changes**:
1. 审计实际 lifecycle 命令 mutation surfaces；
2. 更新中英文技能；
3. 更新 commands reference；
4. grep 双向验证：正向确认指引已写入；负向确认正文零 Harness-specific 专属命令/参数引用。

**Verify**: 正向 `rg -n 'sandbox|escalat|Git metadata|worktree|commit' SKILL.md SKILL.zh-CN.md references/commands.md`（应命中）；负向 `rg -n 'codex|opencode|danger-full-access|workspace-write|--elevate|--sandbox' SKILL.md SKILL.zh-CN.md references/commands.md`（应零命中，命中即回改措辞）

**Done**:
Task output: Harness-neutral 的 lifecycle Git mutation 权限指引：中英 SKILL 新增「生命周期 Git mutation 的执行能力」节（surface 表 + 两档规则 + fail-loud）；commands.md 新增逐命令 mutation surface 审计表与失败语义。核验：正向 grep 命中、负向引擎词零命中、diff 纯新增 73 行。
Files touched: `skills/dev-flow/SKILL.md`、`skills/dev-flow/SKILL.zh-CN.md`、`skills/dev-flow/references/commands.md`
- [x] The implementation agent has completed all development and verification steps above.

---

### Task 2: Git mutation 错误透明化

**Verification Intent**: AC#2

**Behavior**:
- Given add/commit/worktree 等关键 Git mutation 非零；Then command/cwd/exit/stdout/stderr 不丢失。
- Given上层 lifecycle command；Then 不把底层失败压缩成只有 `Commit failed` 后继续。

**Pre-read**: `scripts/lib/git.py`、`scripts/lib/plan_commit.py`、`scripts/lib/worktree.py` 与对应测试。

**Design**: 引入最小结构化 Git mutation failure/exception，保留诊断字段；只覆盖 lifecycle 直接依赖的 mutation helpers。worktree fallback 保留每次 attempt，首个失败不被覆盖。

**TDD**: true

**Changes**:
1. RED：add/commit stderr、worktree attempts 测试；
2. GREEN：实现并接通 helper；
3. REFACTOR：移除相关裸 `False` 吞错路径。

**Verify**: `python -m pytest tests/python/unit/test_git_semantics.py tests/python/unit/test_worktree_context.py -v`

**Done**:
Task output: lifecycle Git mutation fail-loud：`GitMutationFailure` 结构体（command/cwd/exit/stdout/stderr，falsy 保持既有 `if not` 调用方零改动）；`commit_paths`/`commit_all` 补齐 `git add` 退出码检查；`plan_commit` 失败信息携带根因；worktree create/remove 双 attempt 证据全保留。核验：聚焦 69 passed、全量单测 503 passed（+5 新用例）、主控独立失败注入抽查通过。
Files touched: `skills/dev-flow/scripts/lib/git.py`、`skills/dev-flow/scripts/lib/plan_commit.py`、`skills/dev-flow/scripts/lib/worktree.py`、`skills/dev-flow/tests/python/unit/test_git_semantics.py`、`skills/dev-flow/tests/python/unit/test_worktree_context.py`
- [x] The implementation agent has completed all development and verification steps above.

---

### Task 3: 修复 complete / archive / approve 的事务边界

**Verification Intent**: AC#3、AC#4、AC#5

**Behavior**:
- complete commit failure → 不 Issue sync、不成功退出、保持可重试一致状态。
- archive durability 前 failure → 不删除 worktree/branch、不 close Issue；durability 后 cleanup failure → 明确 partial cleanup。
- approve runtime failure → root cause 与 rollback outcome 分层。

**Pre-read**: `scripts/commands/complete.py`、`archive.py`、`approve.py`、相关 unit tests、已归档 `20260929-refactor-dev-flow-issue-sync`。

**Design**: 不引入 sandbox-specific preflight；仅按事务依赖重排通用业务步骤。Git durability 是外部 side effect / destructive cleanup 的门。保留各命令既有 push policy，不在本案扩展状态机。

**TDD**: true

**Changes**:
1. RED：三命令失败注入与 ordering 测试；
2. GREEN：修复控制流；
3. REFACTOR：统一 root failure / cleanup outcome 呈现。

**Verify**: `python -m pytest tests/python/unit/test_approve.py -v`（AC#5 root-cause 保真）— `python -m pytest tests/python -k 'complete or archive' -v`（AC#3 durability gate / AC#4 destructive ordering）

**Done**:
Task output: lifecycle 关键事务顺序与失败一致性修复：complete commit 失败 → 恢复 Plan + 清 index 残留 + 非零退出、不 Issue sync；archive 重排为 durability（commit+push）→ cleanup → close，push 失败阻断 cleanup/close 且重跑真正补推（含复审返工），失败指引给出归档名重跑命令；approve root failure 与 rollback outcome 分层输出。核验：26/51/513/522 全绿 + 主控独立重跑实验（origin 实收 archive commit）。
Files touched: `skills/dev-flow/scripts/lib/plan_state.py`（新增）、`skills/dev-flow/scripts/commands/complete.py`、`skills/dev-flow/scripts/commands/archive.py`、`skills/dev-flow/scripts/commands/approve.py`、`skills/dev-flow/tests/python/unit/test_approve.py`、`skills/dev-flow/tests/python/unit/test_archive.py`、`skills/dev-flow/tests/python/unit/test_complete_verification_commit.py`、`skills/dev-flow/tests/python/integration/test_no_issue_lifecycle.py`
- [x] The implementation agent has completed all development and verification steps above.

---

### Task 4: 全量 lifecycle Git mutation 审计与回归

**Verification Intent**: AC#6、AC#7

**Behavior**:
- Given dev-flow 全部 lifecycle commands；When 静态扫描与失败注入；Then 所有实际 Git mutation 入口均符合 fail-loud / no-invalid-progression 契约。
- Given普通 host；Then成功路径不退化。

**Pre-read**: `scripts/commands/*.py`、`scripts/lib/*.py`、`tests/python/**`

**Design**: 以真实 helper/subprocess 调用链为准审计 `verify`、`verify-switch`、`submit` 等；只有发现同类缺陷才修改，避免无证据重构。最终跑全量 Python suite。

**TDD**: true

**Changes**:
1. 生成审计矩阵：command → mutation → failure handling → external/destructive successor；
2. 为发现的缺口先补失败测试再修；
3. 全量回归。

**Verify**: `python -m pytest tests/python -v`

**Done**:
Task output: 全量审计闭环：审计矩阵覆盖全部 12 个 lifecycle 入口（command → 真实 mutation 调用链 → failure handling → 后继门 → 三态结论），确证 5 处缺口全部按 TDD 修复。缺陷修复：`verify --confirm` commit 失败由 warn 吞错改为快照回滚 + 清 index + 完整诊断 + 非零退出（不 Issue sync、不 close Issue）；`verify-switch` Plan 元数据 commit 从项目仓库改到 `resolve_plan_location` 解析出的 Plan 所属仓库，并检查结果、失败给出可执行手工提交指引。评估项：submit commit 失败确认可重试性被卡（半写 `reviewing` 使重跑报 "already submitted"）→ 快照恢复 planning + 清 index；complete `--pr` 顺序确认无法结构性重排（gh PR 先于 Plan commit）→ 补最小失败指引（点名已创建 PR URL + 重跑勿再传 `--pr`）；其余入口独立扫描确认零 git mutation。另修 archive `git mv` 失败丢 stderr（改用 `GitMutationFailure.from_completed`，保留 command/cwd/exit/stderr）。记录性结论 6 条（gh close 吞错、worktree prune、阶段文档 warn-only、branch delete 幂等语义、write_worktree_context 不可达分支、lib/git.py 死代码）均未改动并附理由。核验：聚焦 83 passed、全量 530 passed（基线 522，+8）、主控独立复核 diff 与异常处理路径（`archive_plan_file` 的 `RuntimeError` 仍被调用方 `except Exception` 捕获、`pr_url` 定义在 `create_pr` 分支内、`resolve_plan_location` 向上查找 `.git` 命中空间仓库）。
Files touched: `skills/dev-flow/scripts/commands/verify.py`、`skills/dev-flow/scripts/commands/verify_switch.py`、`skills/dev-flow/scripts/commands/submit.py`、`skills/dev-flow/scripts/commands/complete.py`、`skills/dev-flow/scripts/commands/archive.py`、`skills/dev-flow/tests/python/unit/test_verify.py`、`skills/dev-flow/tests/python/unit/test_verify_switch.py`、`skills/dev-flow/tests/python/unit/test_submit.py`、`skills/dev-flow/tests/python/unit/test_complete_verification_commit.py`、`skills/dev-flow/tests/python/unit/test_archive.py`、`skills/dev-flow/tests/python/support/git_fixtures.py`（新增）
- [x] The implementation agent has completed all development and verification steps above.

---

### Task 5: 实施审查返工（Rook BLOCK findings）

**Origin**: mandatory implementation review 对 `8c8ead1..82d739a` 判 BLOCK（6 Blocker + 4 Warning）。评审总预算 2 次，返工须一轮做全。

**Behavior**:
- Given Rook 列出的 B-01～B-06 / W-01～W-04；When 逐项按 TDD 修复；Then durability 门、fail-loud、no-invalid-progression 三条契约在全部可达 mutation 路径上成立。

**Pre-read**: Task 1–4 的 Done 记录、`scripts/commands/*.py`、`scripts/lib/*.py`、`references/commands.md`

**Design**: 逐项落到既有 helper（`GitMutationFailure`、`plan_state`、`worktree`），不新建事务 framework；既有 push 策略（submit/approve warn-continue、archive 阻断）保留不动，只增强诊断与门控。审计矩阵落 `references/commands.md`（提案文件禁改）。

**TDD**: true

**Changes**:
1. B-01 archive 的 Issue sync / labels / Plan link 后置到 durability 成功之后，数据源改用归档后路径；
2. B-02 `delete_branch` 区分 deleted / absent / skipped / failed 四态，真失败触发 partial cleanup + 非零退出；
3. B-03 archive push 显式绑定实际承载提交的分支，detached HEAD 拒绝，新增 `is_commit_pushed` 验证 origin 真收到归档 commit；
4. B-04 `push_repo` / `is_commit_in_remote` / stage / fallback / fetch / checkout / remove / prune / reset 全部接通结构化诊断，fallback 保留双 attempt 证据；
5. B-05 `commit_paths` 改 pathspec commit（`git commit -m … -- <paths>`），无关 staged 文件既不进提交也不被清掉；archive rename 同时处理旧新路径；
6. B-06 PR 提交失败回滚后重新写回 PR 字段，区分保留成功/失败，指引改为「重跑勿传 --pr，将采用已有 PR」；
7. W-01 `reset_plan_index` / `recover_plan_after_failed_commit` 分层返回文件恢复与 index 恢复结果，四个调用方改用分层报告；
8. W-02 phase-doc 改 path-isolated 提交，失败不再输出假成功日志；
9. W-03 switch 测试重写为行为断言（真实 worktree / HEAD / 落仓 / 文件内容），fixture 合并，1042 → 554 行；PR 样本改用有来源记录的 fixture；
10. W-04 审计矩阵落 `references/commands.md`，六条记录性结论按修完后实际状态更新。

**Verify**: `python -m pytest tests/python -q -p no:cacheprovider`

**Done**:
Task output: Rook 全部 10 项 finding 一轮修完并按 TDD 留证。B-01 archive 外部更新后置到 durability 之后（sync/labels/link 全用归档路径，durability 失败时 Issue 零触碰）；B-02 `BranchDeleteResult` 四态 + 真实 `.git/refs/heads/<branch>.lock` 注入验证 partial cleanup 与非零退出；B-03 detached HEAD 拒绝 + `is_commit_pushed` 验证 bare origin 真实收到归档 commit（修正了 push 到默认分支而归档提交落在当前分支的假 durability）；B-04 诊断接通 7 处调用链，并实测发现 `git worktree prune` 会 rc=0 但把错误写进 stderr，改为 rc + stderr 双检；B-05 pathspec commit 使 `foreign.txt` 在 `git status --porcelain` 仍为 `A ` 且不入 lifecycle commit；B-06 失败→照指引重跑→verify 仍以保留 URL 走 `_is_pr_merged` 的完整链路（含无 Issue 场景）；W-01 `PlanRecovery` 分层返回 + `index.lock` 真实注入验证不再输出「可直接重试」；W-02 忽略的未跟踪 phase doc 不再输出假成功；W-03 switch 测试删除固定下标与调用序列断言、fixture 全合并、行数降至 554；W-04 矩阵落入 `references/commands.md`。保留未改：push 策略、脏 worktree 警告后继续、gh close 吞错、写不出的不可达分支、lib 死代码，均附理由入矩阵。核验：全量 541 passed（基线 530，+11）、42 subtests、逐 finding 聚焦 42 passed；主控独立复跑全量 541 passed，核对提案文件零改动、`commit_paths` pathspec 实现、`BranchDeleteResult` / `PlanRecovery` 分层 API、R2 fixture 来源记录（`tests/fixtures/github/SOURCES.md`）。
Files touched: `skills/dev-flow/references/commands.md`、`skills/dev-flow/scripts/commands/approve.py`、`skills/dev-flow/scripts/commands/archive.py`、`skills/dev-flow/scripts/commands/complete.py`、`skills/dev-flow/scripts/commands/submit.py`、`skills/dev-flow/scripts/commands/verify.py`、`skills/dev-flow/scripts/commands/verify_switch.py`、`skills/dev-flow/scripts/lib/git.py`、`skills/dev-flow/scripts/lib/plan_commit.py`、`skills/dev-flow/scripts/lib/plan_state.py`、`skills/dev-flow/scripts/lib/worktree.py`、`skills/dev-flow/tests/python/unit/test_archive.py`、`skills/dev-flow/tests/python/unit/test_complete_verification_commit.py`、`skills/dev-flow/tests/python/unit/test_git_semantics.py`、`skills/dev-flow/tests/python/unit/test_push_race_recovery.py`、`skills/dev-flow/tests/python/unit/test_verify_switch.py`、`skills/dev-flow/tests/python/unit/test_worktree_context.py`、`skills/dev-flow/tests/python/unit/test_plan_state_recovery.py`（新增）、`skills/dev-flow/tests/fixtures/github/pr-merged-recorded.json`（新增）、`skills/dev-flow/tests/fixtures/github/SOURCES.md`（新增）
- [x] The implementation agent has completed all development and verification steps above.

**Rework after Rook 终局 BLOCK（2 轮预算用尽后主控自修）**：

Rook 终局复审仍判 BLOCK（3 Blocker + 4 Warning），评审预算 2 轮已用尽，用户指示主控自行修复。逐项修复与证据：

- B-01（归档重跑漏提交旧路径删除）：`commit_archived_plan` 新增 `_recover_staged_archive_sources`，在重跑场景（`source_path == archived_file`）从 `git diff --cached --name-status` 读出已 staged 的旧路径删除（D 状态，文件名匹配），纳入 `commit_targets`，使 pathspec commit 携带完整 rename。测试：commit 失败→归档名重跑→origin/main 旧路径不存在、新路径存在、index 无 rename 残留、`foreign.txt` 仍为 `A `。
- B-02（非默认分支归档生成错误链接）：`build_plan_blob_url` 接受可选 `branch` 参数；`update_issue_plan_link` 接受可选 `branch` 透传；`cmd_archive` 在 durability 成功后取 `get_current_branch` 传给 `update_issue_plan_link`，使链接指向实际承载归档提交的分支。测试：非默认分支 `work` 归档→`update_issue_plan_link` mock 的 `branch` kwarg == `"work"`。
- B-03（Issue 同步失败仍报成功）：`cmd_archive` 消费 `sync_plan_to_issue_body` 返回值，失败时不输出 `log_success`、不执行 labels/link、明确报告「body sync failed」并给出重跑指引。测试：`sync_body` mock 返回 False→输出不含「Plan synced to Issue」、含「body sync failed」、labels/link 未调用。
- W-01（`is_commit_pushed` 单分支 clone 误判）：改用 `git ls-remote origin <branch>` 直接查询远端 ref，不再依赖 tracking ref。测试：push 到 `work` 分支后删除 tracking ref→`is_commit_pushed` 仍返回 True；未 push 返回 False。
- W-02（rev-parse 读取失败被误标 absent）：`delete_branch` 区分「ref 不存在」（stderr 空 → absent）与「rev-parse 本身失败」（stderr 非空 → failed）。测试：mock rev-parse 返回非空 stderr→`status == "failed"`。
- W-03（测试 `log_error` mock 导致断言无效）：`test_reset_failure_not_reported_as_retry_ready` 将 mock 的调用内容拼入断言。
- W-04（审计矩阵 approve 语义写错）：`references/commands.md` approve 行区分 commit/worktree 失败与 push 失败。

核验：全量 547 passed（基线 541，+6 新测试）、42 subtests；主控独立复跑 547 passed。

---

## Delegation Strategy

| Wave | Task | Executor | Depends on | Why delegated |
|------|------|----------|------------|---------------|
| 1 | Task 1 | fae | none | 技能契约独立，可先锁定跨引擎权限边界 |
| 1 | Task 2 | fae | none | Git helper 可独立 TDD |
| 2 | Task 3 | fae | Task 2 | 事务修复依赖稳定的 mutation failure 传播 |
| 3 | Task 4 | fae | Task 1, Task 2, Task 3 | 最终全量审计与回归 |
| 4 | Task 5 | fae | Task 4 | Rook BLOCK 返工，预算内一轮做全 10 项 |

## Delivery

`space sync` and `ontology contribute` are the user's call — the skill never uploads on its own.

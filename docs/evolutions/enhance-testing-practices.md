# enhance-testing-practices

## Metadata

- **Type**: enhance
- **Project Path**: .wopal
- **Created**: 2026-10-29
- **Stage**: validating
- **Mode**: quick
- **Worktree**: (none)
- **Branch**: ontology-enhance-testing-practices
- **Base Commit**: 162c59bb82313923407d7633bbc224dce16e9599
- **Final Commit**: (none)

## Scope Assessment

- **Complexity**: Low
- **Confidence**: High

## Goal

新增一条跨语言的 Testing Best Practices 规则，统一约束 coding 空间中的测试价值、分层、确定性、隔离、异步同步、资源生命周期、flaky 修复与性能成本，并让项目规范只保留项目特有的测试约束。

## Technical Context

### Architecture Context

当前 coding archetype 只默认装配 `rules/typescript.md` 与 `rules/python.md`。其中 `typescript.md` 内含一整套通用测试方法，但这些原则并不属于 TypeScript，且存在固定 70/25/5 比例、“发布前运行全部 E2E”、把 unit 定义为“所有依赖都 mock”等过度具体或不普适的约束。Python 规则则只有框架级测试约定，导致不同语言项目对测试质量、确定性和分层没有统一标准。

本次事故已验证一组稳定、跨语言的工程原则：坏代码应可靠变红、好代码应稳定通过；同一 SHA 重复执行应确定；异步同步基于事件而非时间；资源与进程全局状态必须有 owner；低成本测试优先；flaky 不得靠 retry、延长 timeout、弱化断言或全局串行化掩盖；昂贵 system/E2E 只验证低层无法证明的系统风险。

### Research Findings

1. 测试原则天然跨语言，owner 应是独立 Rule，而不是 TypeScript Rule。
2. coding archetype 应默认装配该 Rule，使所有 coding space 获得一致的测试设计边界。
3. 语言规则只应保留语言/runner 特有约束，避免与通用 Testing Rule 产生双真相源。
4. 项目 `AGENTS.md` 应引用通用规则并只补充项目特有命令、fixture、隔离门禁和真实宿主验证要求。

**References**:
- `rules/typescript.md`
- `rules/python.md`
- `assembly/archetypes/coding.yaml`
- `projects/ellamaka/AGENTS.md`（项目级消费方，不属于本体仓库）

### Key Decisions
- D-01: 新增独立 `testing.md` Rule，作为跨语言测试设计的唯一通用 owner。
- D-02: coding archetype 默认装配 `testing.md`，因此 coding space 中所有项目默认受该规则约束。
- D-03: Rule 不规定固定测试比例、固定框架或“发布必须跑全套 E2E”；测试层级按风险与最低充分证明选择。
- D-04: flaky 修复必须证明根因被消除；禁止以 retry、延长 timeout、弱化断言或全局串行化作为稳定性修复。
- D-05: TypeScript/Python 规则只保留语言/runner 特定内容；与通用测试原则重复或冲突的内容移交 `testing.md`。
- D-06: Ellamaka `AGENTS.md` 仅引用 Testing Best Practices，并继续保留项目特有的 TISO、fixture、Bun/process-global、真实平台与 release 验证约束。

### Key Interfaces

- 新规则 canonical runtime path: `rules/testing.md`
- 中文 review path: `docs/LANG/zh-CN/rules/testing.md`
- coding archetype 必须包含 `testing.md`
- Rule frontmatter 使用 `trigger: model_decision`，关键词覆盖 test/testing/测试/flaky/unit/integration/e2e/ci 等测试意图。

## In Scope

- 新增 Testing Best Practices Rule 的中英文版本。
- 将 `testing.md` 加入 coding archetype 默认 rules。
- 从 TypeScript Rule 中移除跨语言测试方法的重复/冲突内容，只保留 TypeScript/JS runner 特有约定并引用通用 rule。
- Python Rule 的 Testing 段保留 pytest 特有约定，并引用通用 rule。
- Ellamaka 项目规范引用 Testing Best Practices；项目特有隔离规则不重复搬入本体。

## Out of Scope

- 不统一测试框架、目录结构或固定 unit/integration/E2E 比例。
- 不修改具体项目的测试代码或 CI workflow。
- 不把 Ellamaka 的 TISO 规则、Bun mock 限制或 package-local fixture 提升为通用规则。

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| Testing Rule | `rules/testing.md`, `docs/LANG/zh-CN/rules/testing.md` | create | 跨语言测试最佳实践唯一 owner |
| Language Rules | `rules/typescript.md`, `docs/LANG/zh-CN/rules/typescript.md`, `rules/python.md`, `docs/LANG/zh-CN/rules/python.md` | modify | 去除重复通用原则，只保留语言/runner 特有内容 |
| Coding Assembly | `assembly/archetypes/coding.yaml` | modify | coding 空间默认装配 testing rule |
| Ellamaka project rules | `projects/ellamaka/AGENTS.md`, `projects/ellamaka/AGENTS.zh-CN.md` | modify outside ontology | 引用通用规则并保留项目特有测试约束 |

## Assembly Intent

<!--
Register only the new whole assets this proposal introduces — one
canonical reference per asset (`skill:new-skill`, `path:assets`, ...) —
and only when no held asset already covers the new path. A file inside
an asset the space already holds is an ordinary content change; reserved
content (`assembly/`, `config/`, `docs/`, repository-root files) is
never claimable — neither belongs here. `type-default` writes the
reference into the current type manifest, so every space of the type
receives the asset; `space-local` records it in this space's `include`,
so only this space mounts it. Each reference appears once; a whole asset
left undeclared is refused when the proposal lands. Leave the table
empty when nothing new is added; one row reads
`skill:new-skill | space-local | why only this space`.
-->

| Ref | Scope | 理由 |
|-----|-------|------|
| rule:testing.md | type-default | 所有 coding space 都需要统一的测试设计与稳定性原则 |

## Acceptance Criteria

### Agent Verification

1. [x] coding archetype 默认包含 `testing.md`，且引用解析成功。
2. [x] `testing.md` 明确覆盖测试价值、最低成本分层、确定性/隔离、事件同步、资源 owner、并发边界、失败路径、flaky 修复证据与性能成本。
3. [x] Rule 明确禁止 retry、单纯增加 timeout、弱化断言、全局串行化作为 flaky 修复手段。
4. [x] TypeScript/Python Rule 不再各自维护一套冲突的通用测试理论；语言规则只保留 runner/命名等技术栈特有内容。
5. [x] Ellamaka AGENTS 引用通用 Testing Best Practices，同时保留它已有的项目特有 Test Isolation Rules。
6. [x] 中英文 rule 与项目 AGENTS 语义一致，`git diff --check` 通过。

### User Validation

<!--
Only items an agent cannot verify and the user must observe by hand. Every
scenario needs: environment, launch command, user actions, pass criteria,
failure feedback.
-->
N/A。本变更为声明式规则与 assembly 配置，行为可由文件内容、引用解析和装配验证完成，不需要人工运行时观察。

## Implementation

<!--
Tasks split by behavior group, not by file. One Task = one cohesive
behavior unit, independently testable.
-->

### Task 1: Add the shared testing rule

**Verification Intent**: 2, 3, 6

**Behavior**:
- `testing.md` Rule 给出跨语言的稳定测试设计约束且无固定框架/比例绑定。

**Pre-read**: `rules/typescript.md`, `rules/python.md`, `assembly/archetypes/coding.yaml`, `.wopal/AGENTS.md`

**Design**: 中文 review 版本先写，再同步正式英文 runtime source。

**TDD**: false — 声明式内容变更，以结构/装配验证代替代码 TDD。

**Changes**:
1. 新增中英文 `testing.md`。

**Verify**: 检查 frontmatter、中英文语义与 `git diff --check`。

**Done**:
Task output: 新增跨语言 Testing Best Practices rule 的中英文版本，并声明为 coding type-default capability。
Files touched: `rules/testing.md`, `docs/LANG/zh-CN/rules/testing.md`, `docs/evolutions/enhance-testing-practices.md`
- [x] The implementation agent has completed all development and verification steps above.

### Task 2: Remove duplicated language-level policy and reference it from Ellamaka

**Verification Intent**: 1, 4, 5, 6

**Behavior**:
- TypeScript/Python 规则只保留技术栈特有测试约束；Ellamaka 项目规范引用通用 Testing Best Practices，同时继续约束 TISO/fixture/Bun/process-global 等项目事实。

**Pre-read**: language rules plus Ellamaka `AGENTS.md` / `AGENTS.zh-CN.md`

**Design**: one fact, one owner；通用原则只在 `testing.md`，项目 AGENTS 只引用并保留项目特有增量。

**TDD**: false — 文档/规则结构变更。

**Changes**:
1. 将 `testing.md` 加入 coding archetype。
2. 精简 TypeScript/Python Testing 段。
3. 更新 Ellamaka 双语 AGENTS 引用。

**Verify**: 中英文语义对照、grep 无冲突规则、`git diff --check`。

**Done**:
Task output: `testing.md` 已装配为 coding 默认 rule；TypeScript/Python 只保留技术栈特有测试约定；Ellamaka 双语 AGENTS 已改为引用 Testing Best Practices，并保留项目特有 Test Isolation Rules（项目提交 `7ff07b48e3`）。
Files touched: `assembly/archetypes/coding.yaml`, `rules/typescript.md`, `docs/LANG/zh-CN/rules/typescript.md`, `rules/python.md`, `docs/LANG/zh-CN/rules/python.md`, `docs/evolutions/enhance-testing-practices.md`; Ellamaka `AGENTS.md`, `AGENTS.zh-CN.md` in project commit `7ff07b48e3`
- [x] The implementation agent has completed all development and verification steps above.

---

## Delegation Strategy

| Wave | Task | Executor | Depends on | Why delegated |
|------|------|----------|------------|---------------|
| 1 | Task 1 | fae | none | 本体 capability asset 修改 |
| 2 | Task 2 | fae | Task 1 | 需要引用新建的 canonical testing rule |

## Delivery

`space sync` and native Git/GitHub PR publication are the user's call — the skill never uploads on its own.

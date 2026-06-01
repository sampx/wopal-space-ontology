---
name: dev-flow
description: |
  Issue/Plan 驱动的开发工作流。⚠️ 任务需以 GitHub Issue 或 Plan 为执行载体。

  🔴 Trigger: "#14"、"这个 issue"、"出个计划"、"开始开发"、"执行计划"、Plan 生命周期推进（approve/complete/verify/archive）、从 PRD 拆分 Issue。
  ❌ Skip: spec 驱动流程、单纯研究/讨论/解释、不需 Issue/Plan 的临时小改动。
compatibility:
  - bash 3.x+
  - gh CLI
  - jq
---

# dev-flow — Issue / Plan 驱动开发流程

统一状态机：`planning → executing → verifying → done`

统一命令链：`plan → approve → approve --confirm → complete → verify --confirm → archive`

## 核心原则

1. 先进入 Plan 生命周期，再开始实施。
2. `approve --confirm` 和 `verify --confirm` 都是人类授权门。
3. `complete` 表示"实施完成，活动 Plan 状态已更新为 verifying，进入用户验证阶段"，不代表"用户已验证通过"。代码提交由实施 agent 负责。
4. `archive` 只做 push + 归档收尾，不承担验证职责。
5. **Plan 必须先通过 `flow.sh plan ...` 生成或定位 stub**；禁止手写创建 Plan 文件，禁止自行猜测 Plan 路径。

## 最容易遗漏的两步

1. **Plan 写完后**：`--check` → 必要时 `sync <issue> --body-only` → `approve` → 等用户审批。
2. **实施完成后**：每个 Task 运行 Verify 通过后立即勾选 Done → 完成 Agent Verification → `complete` → 再等用户验证。

**Done 勾选范围**：Implementation 中每个 Task 的 `- [ ]` checkbox，以及 `### Agent Verification` 中的所有 checkbox。`complete` 强制校验全部勾选。

## 状态机与命令映射

| 命令 | 前置状态 | 后置状态 | 作用 |
|------|---------|---------|------|
| `plan` | 无 | `planning` | 创建或定位 Plan |
| `approve` | `planning` | `planning` | 校验 Plan，提交方案评审 |
| `approve --confirm` | `planning` | `executing` | 用户审批通过，开始实施 |
| `complete` | `executing` | `verifying` | 实施完成，Plan-only 提交活动 Plan（脏实施树报错退出） |
| `verify --confirm` | `verifying` | `done` | 用户验证通过，Plan-only 提交到集成分支 |
| `archive` | `done` | 归档 | 归档 Plan，清理 worktree，关闭 Issue |

命令顺序不合法时，回到正确状态顺序执行，不要强行推进。

## 人类授权门

| 命令 | 用户信号 |
|------|---------|
| `approve --confirm` | "审批通过"、"approved"、"可以开始" |
| `verify --confirm` | "验证通过"、"没问题"、"validation passed" |
| `reset` | "重置"、"reset" |

禁止未经授权执行任何 `--confirm`；禁止跳过 `approve` 直接开工。

## 标准流程

### A. 进入 planning

Issue 驱动：`flow.sh plan <issue>`。无 Issue：`flow.sh plan --title "..." --project <name> --type <type>`。

#### Plan 目录规则

- 先执行 `flow.sh plan ...` 生成或定位 stub，再编辑内容。
- Plan 目录由 `--project` 决定；`--project` 是必填参数。
- **标准项目**：`projects/<project>/docs/plans/`
- **ontology-worktree**：`.wopal/docs/plans/`
- `docs/projects/<project>/plans/` 是 **DEPRECATED** 只读回退，禁止新写入。

#### --project 必填

`--project` 是 `plan` 命令的必填参数。不存在"空间级 Plan"——每个 Plan 必须归属一个项目。

### A+. Plan 编写要点

**业务规则影响评估**：

Plan 编写时，读取产品已有 `projects/<project>/docs/BUSINESS_RULES.md`，判断本次改动是否影响业务规则：

| 场景 | Plan 中标注 |
|------|-----------|
| 引入新业务约束 | `## Business Rules Impact → 新增: BR-NNN 规则描述` |
| 改变已有规则判定条件 | `## Business Rules Impact → 修改: BR-NNN 旧→新（原因）` |
| 系统设计变更使规则不再适用 | `## Business Rules Impact → 废弃: BR-NNN 废弃原因` |
| 纯技术重构、bug 修复（无新约束） | `N/A — 无业务规则变更` |

**同步时机**：`complete` 前 Wopal 负责将 `## Business Rules Impact` 中非 N/A 的变更同步到 `BUSINESS_RULES.md`，然后勾选同步确认 checkbox。

---

### B. Plan 写完后，方案评审

1. 完成 Plan 编写，运行 `flow.sh plan <issue> --check`
2. Issue 驱动时若 Plan 影响 Issue body，执行 `flow.sh sync <issue> --body-only`
3. **委派 rook 审 Plan**（强制）—— prompt 契约格式见 agents-collab
4. 根据 rook 判定：PASS → 继续；REVISE/BLOCK → 修订后重审（最多 3 轮）
5. 通过后：`flow.sh approve <issue>`，停止推进，等用户审批
6. 用户授权后：`flow.sh approve <issue> --confirm`（默认创建 worktree 隔离）

禁止：跳过 rook 审查直接 approve、rook BLOCK 后强行 approve。

### C. 进入 executing 后实施

每完成一个 Task 立即勾选 Done checkbox，不积压。

**委派体系**：

- 实施 Task → 委派 fae。Wopal 职责：切片 → 委派 → 验证 → 推进下一 Wave
- 审查 Task → 委派 rook。rook 返回 PASS/REVISE/BLOCK

```text
Plan 切片 → 委派 fae 实施 → 委派 rook 审查 → 根据结果推进/修正 → 下一 Wave
```

**fae 保留策略**：rook 审查未完成前不 finish fae task（上下文 >50% 例外）。rook REVISE/BLOCK 时 reply 同一 fae 修复，不新开 task。

**rook 委派时机**：
1. Plan 写完后（approve 前）— 审方案质量
2. fae 最终交付后（complete 前）— 最终审查

rook 契约格式见 agents-collab。委派 rook 前不预加载 df-plan-review / df-implement-review —— rook 自行加载。

**委派 prompt 必须**：末尾附加 Done checkbox 更新指令（格式见 `references/plan-authoring.md`）。

**委派用活动 Plan 路径**：子代理 prompt 中的 Plan 路径必须使用活动 Plan 的本地路径。对于 worktree 隔离的 executing Plan，活动 Plan 位于 feature 分支的 worktree 内，与 main 分支上的 Plan 是独立副本。禁止在委派 prompt 中使用 main 分支的 Plan 路径——这会导致代理在 feature 分支上实施时读取或更新错误的 Plan 副本。

### D. 实施完成后，进入用户验证

1. 确认所有 Task Done 已勾选
2. **委派 rook 审 fae 实施结果**（强制，prompt 格式见 agents-collab）
3. 根据 rook 判定：PASS → 继续；REVISE/BLOCK → fix + re-review（最多 3 轮）
4. 通过后勾选 `### Agent Verification`
5. **同步业务规则**：如 Plan 的 `## Business Rules Impact` 非 N/A，将变更同步到 `projects/<project>/docs/BUSINESS_RULES.md`，勾选 Plan 中的同步确认 checkbox
6. `flow.sh complete <issue>`

`complete` 硬门控：所有 Task Done ✓ + Agent Verification ✓ + rook PASS ✓。`complete` 在脏实施树上报错退出，不提交代码——代码提交由实施 agent 负责。

### worktree 隔离下的验证切换

`complete` 将活动 feature Plan 状态更新为 `verifying`。此时代码和 Plan 都在 feature 分支上。用户验证在 feature 分支上进行。

**Phase 1 — 切换到 feature 分支验证**：
```bash
flow.sh verify-switch <issue>
```
检出 feature 分支。提示用户在 feature 分支上验证实施结果。

**Phase 2 — 用户确认后合并到集成分支**：
```bash
flow.sh verify-switch <issue> --merge
```
检出集成分支（main） → merge feature 分支。合并后 feature 分支的工作已集成到 main。

**⚠️ 硬约束**：`verify-switch --merge` **必须**在用户明确确认验证通过后执行。禁止手动 merge，统一使用本命令。

### E. 用户验证通过后进入 done

feature 分支已集成到 main 后：`flow.sh verify <issue> --confirm`。前置：Plan 状态 = `verifying`，User Validation 最终 checkbox 已勾选，feature 分支已合并到集成分支。

`verify --confirm` 在集成分支上提交 Plan-only commit（`verifying` → `done`）。对于 PR 流程，需确认 PR 已合并后才在 main 上提交 `done`。

### F. 最后归档

`flow.sh archive <issue>`。前置：Plan 状态 = `done`。

`archive` 在集成分支上将已接受 Plan 移至 `done/` 目录，清理 worktree，更新 Issue 链接。`archive` 永远不提交代码。

## Wopal 编排规则

以下规则约束 Wopal 在 dev-flow worktree 生命周期中的编排行为：

1. **活动 Plan 路径委派**：Wopal 只使用活动 Plan 的本地路径委派实施。对于 worktree 隔离的 Plan，活动 Plan 位于 feature 分支的 worktree 内。
2. **脏树交接失败**：Wopal 将脏的实施树视为交接失败。如果 `complete` 因脏树报错，Wopal 要求实施 agent（fae）提交代码后重试。
3. **feature 分支验证**：Wopal 在 feature 分支上运行 `verify-switch` 供用户验证实施结果。
4. **合并需用户确认**：Wopal 仅在用户明确验证确认后运行 `verify-switch --merge`。
5. **done 需已集成**：Wopal 仅在 feature 分支已集成到集成分支或 PR 已合并后运行 `verify --confirm`。
6. **不要求脚本提交代码**：Wopal 不要求生命周期脚本提交代码。代码提交由实施 agent 负责。

## Roadmap

产品阶段规划前置工作流。从 PRD/DESIGN 文档生成 phase 文档和 Issue。

```bash
flow.sh roadmap <prd-path> [--product <name>] [--project <name>] [--yes] [--dry-run]
```

**四阶段流程**：
1. **Analyze**（全自动）：解析 PRD，提取 Phase 定义
2. **Discuss**（交互式）：逐 Phase 与用户确认目标、范围、退出条件（`--yes` 跳过）
3. **Produce**（全自动）：按模板写入 phase 定义文档到 `phases/` 目录
4. **Decompose**（全自动）：为每个涉及项目创建 Issue，注入 Product/Phase 元信息

**Issue 标题格式**：`feat({scope}): {phase-id} — {goal-summary}`（≤72 chars）

## Issue 编写

### 创建 Issue

以 `--body-file` 为主路径——agent 直接写 markdown 文件，不需要通过 CLI 参数拼装 body：

```bash
flow.sh issue create --title "feat(scope): desc" --project <name> --body-file body.md
```

`--type` 可选覆盖（默认从标题自动推断），`--body-file` 指向包含完整五段结构的 markdown 文件。

### 写入 Issue body

```bash
flow.sh issue write <issue> --body-file <path>    # 全量替换 body
flow.sh issue write <issue> --append <path>       # 追加到 body 末尾
```

- `--body-file`：用文件内容替换整个 Issue body
- `--append`：在现有 body 末尾追加文件内容，用 `\n\n` 分隔，保留已有内容

### decompose --from ROADMAP.md

从 ROADMAP.md 的 Slices 表生成 Slice Issues：

```bash
flow.sh decompose-prd --from ROADMAP.md [--product <name>] [--dry-run]
```

Slices 表格式见 ROADMAP.md Slices 语法规范。

## 主流路径

| 场景 | 命令路径 |
|------|----------|
| Issue 驱动 | `plan → --check → sync(如需) → approve → approve --confirm → complete → verify --confirm → archive` |
| Plan 驱动 | `plan → approve → approve --confirm → complete → verify --confirm → archive` |

## worktree 隔离（默认）

worktree 是默认执行策略。`approve --confirm` 自动创建 worktree 隔离环境；只有 `--no-worktree` 才跳过。

```bash
flow.sh approve <issue> --confirm              # 默认创建 worktree
flow.sh approve <issue> --confirm --no-worktree # 跳过 worktree
```

Worktree 元数据（2 字段）自动写入 Plan metadata：

```yaml
- **Worktree**:
  - branch: <feature-branch-name>
  - path: <workspace-relative-worktree-path>
```

- `branch`：feature 分支名
- `path`：worktree 的 workspace 相对路径

验证目录结构：`ls .worktrees/<project>-issue-<N>-*/`

禁止在主工作空间编辑——所有变更在 worktree 内进行。

## Plan 分支归属

Plan 在不同阶段归属于不同分支：

| 阶段 | 归属分支 | Plan 状态 | 说明 |
|------|---------|----------|------|
| `planning` | 集成分支（main 或 space/main） | `planning` | Plan 基线在集成分支上提交 |
| `approve --confirm` | 集成分支 → 创建 feature 分支 | `executing` | 先在集成分支提交 executing + Worktree 元数据，再从该基线创建 worktree |
| 实施（executing） | feature 分支 | `executing` | 实施在 feature 分支的 worktree 中进行 |
| `complete` | feature 分支 | `verifying` | Plan-only 提交活动 Plan（脏实施树报错退出） |
| 用户验证 | feature 分支 | `verifying` | 用户在 feature 分支上验证实施结果 |
| `verify-switch --merge` | feature → 集成分支 | `verifying` | 用户确认后将 feature 合并到集成分支 |
| `verify --confirm` | 集成分支 | `done` | Plan-only 提交到集成分支 |
| `archive` | 集成分支 | 归档 | 移至 `done/`，清理 worktree |

**Plan-only commit 原则**：生命周期脚本只提交 Plan 状态变更，不提交实施代码。代码提交由实施 agent（fae）负责。脚本在遇到脏实施树时报错退出，而非代为提交代码。

## 不要这样做

- Task 完成但不勾选 Done checkbox
- Agent Verification 未完成就推进
- 忘记执行 `complete`
- 跳过 rook 审查直接 complete
- rook BLOCK 后强行 complete
- 用户验证通过前 merge feature 分支到主分支——提前 merge 留下 revert 补丁，后续 merge 产生大量冲突

## 参考

对所有命令，使用 `flow.sh <cmd> --help` 获取完整参数。以下文档补充使用模式和边缘场景：

| 文件 | 用途 |
|------|------|
| `references/commands.md` | 命令概览与使用模式 |
| `references/plan-authoring.md` | Plan 质量门、AC、TDD、委派 prompt 格式 |
| `references/troubleshooting.md` | 错误处理、边缘场景、PR 工作流 |
| `templates/plan.md` | Plan 骨架模板 |
| `templates/issue*.md` | 各类型 Issue 模板 |
| `references/plan-validation.md` | Plan 校验规则 |
| `references/tdd-guide.md` | TDD Task 编写指南 |
| `references/issue-format.md` | Issue 标题、Plan 命名规范与 Issue body 五段结构 |

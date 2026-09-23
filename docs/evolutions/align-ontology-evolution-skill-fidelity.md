# align-ontology-evolution-skill-fidelity

## Metadata

- **Type**: enhance
- **Project Path**: .wopal
- **Created**: 2026-09-22
- **Stage**: implementing
- **Mode**: isolated
- **Worktree**: .worktrees/ontology-align-ontology-evolution-skill-fidelity
- **Branch**: ontology-align-ontology-evolution-skill-fidelity
- **Base Commit**: 1a47d0f235bdff567d076697a27d30f98e05bf32
- **Final Commit**: (integrate 时记录：集成到空间分支后的提交)

## Scope Assessment

- **Complexity**: High
- **Confidence**: High

## Goal

将 `ontology-evolution` 从薄版复刻升维为**纪律机制化**的进化工作流：继承 dev-flow 打磨多年的纪律资产（归档卫生、门控、提案契约、命名边界），并超越之——每条在 dev-flow 中靠散文与 agent 记忆维持的纪律，在本技能中要么成为脚本强制的不变量（含具名测试），要么被显式拒绝继承。**核心是保证稀疏检出 worktree 处理机制的正确性**（本技能与 dev-flow 的立身差异）：2026-09-23 临时仓库探针实锤了 integrate 静默投毒等 P0 缺陷，本轮一并闭合。禁止以散文复刻纪律。

## Technical Context

### Architecture Context

`ontology-evolution` 由已归档提案 `refactor-ontology-evolution-skill-split` 交付，流程复刻自 dev-flow（仅状态机词汇改造），但复刻停留在"形似"层。审计（2026-09-22，静态）与探针（2026-09-23，临时仓库实跑两轮）确认缺陷如下：

**P0 — 稀疏 worktree 机制缺陷（探针实锤，本提案核心）**

1. **integrate 在 worktree 缺失时静默投毒能力池**（探针 B1-B8 全链实证）：
   - 失效链：实施中 worktree 目录丢失（误删/磁盘/人工清理），`_branch_patterns`（worktree.py:263-282）对"分支存在但无 worktree"静默返回 `[]` → 集成时零 widening → `merge --squash` 把新能力 commit 进 index，路径落在 range 外 → merge 给它们打上 skip-worktree 位（flags `40004000`）→ **提交成功、git status 干净、运行时永久不可见**。
   - **全部既有守卫对此失明**：space 侧 `sparse.preflight` 返回空（B7）——"已提交 + skip 位 + range 外"恰是 range 外条目的合法形态，守卫按设计不报。
   - 收尾闭环更糟：`check` 此后因 recorded worktree 缺失永久失败（B5）；重跑 `accept` 撞分支已存在，错误信息第一建议是 **"remove the stale branch"**（evo.py:109-111）——引导用户删掉可能载有未集成成果的分支（R1-R3）。
2. **accept 非事务化，失败留残渣且误导恢复**（探针 G4-G6）：
   - 流程顺序：metadata 写入并 commit 到 space 分支（evo.py:408-415）→ derive worktree → `assert_isolated`。源 `.wopal` 稀疏被 disable 时（2026-09-20 真实事故形态），derive 出**全量 checkout**（beta 物化，G5），assert 拦截（G4 rc=1）——但分支已创建、worktree 目录已落盘、metadata 已提交（G6），零清理。
   - 之后 re-accept 撞 R1，用户被引导删分支。
3. **integrate 无 worktree/分支身份守卫**（源码 evo.py:765-770 只查 dirty；探针 D 因 dirty 先拦未达分支断言）：merge 源是 ref 本身不受 worktree 检出位置影响，故非投毒路径，但 worktree 停在杂散分支上的已提交工作会被静默跳过（B 的变体）；且防御纵深要求 integrate 前重跑 `assert_isolated`（accept 之后的漂移目前只有 commit 时 preflight 覆盖）。

**既有安全行为（探针确认为正确，须防回归，具名测试固化）**

- 冲突 squash 被拒后 `_reset` 恢复干净：无 unmerged 残留、`.wopal` clean（E4-E6）。
- dirty 检查先于一切变更：range 内 untracked 文件使 integrate 拒绝且文件幸存（E7-E8）。
- `git add` 带 unmatched pathspec 原子拒绝（F1），mirror-commit 无半提交风险。
- derive 源继承稀疏形态、happy path archive 镜像后 worktree clean（A1-A3）。

**P1 — 复刻保真度缺陷（静态审计实证）**

4. **归档无日期前缀**：dev-flow `archive.py:352-354` 落盘 `YYYYMMDD-<name>`；evo `evo.py:938,943` 裸 move。语料佐证：`docs/evolutions/archived/` 74 个历史文件几乎全部带日期，唯独本次归档的 `refactor-ontology-evolution-skill-split.md` 没有——**静默漏过是因为没有任何机制审视语料**。
5. **归档无 worktree/分支清理**：dev-flow `archive.py:574-647` + `_cleanup_worktree`（含 `--keep-worktree` 逃生口）；evo 零命中。现场残留：分支 `wopal-space-ontology-evolution-skill-split` 仍在（非 space 分支祖先，squash 所致）。
6. **无集成守卫**：dev-flow 清理前校验 `check_branch_merged`（archive.py:624-628）；evo 无对应物。
7. **模板机制缺失且与实态脱节**：dev-flow 模板是外部文件 `templates/plan.md`（198 行逐节注释，`plan.py:230-236` 加载）；evo 是 `evo.py:53-91` 内嵌字符串（6 薄节零指引），与在用提案格式（Technical Context 四子节 / In·Out of Scope / Affected Files / AC(AV+UV) / Tasks / Delegation）不一致；`evo.sh new` 产出的外壳没有任何真实提案使用过。
8. **无每命令状态门控**：evo `commit` 只查 Mode（evo.py:648-652）、`integrate` 只查 isolated（evo.py:748-753）。
9. **`check` 未兑现结构校验**：原提案 Task 5 ④ 承诺校验 Task 结构；实际只查 metadata/占位符/稀疏/隔离（evo.py:811-910）。
10. **SKILL.md 内部自相矛盾**：:124 "no issue layer, no worktree-manager layer" 与已交付的 `lib/worktree.py` 矛盾；"Landing an evolution" 把用户观察放在 `integrate` 前（隔离模式下不可执行）；"commit 是唯一写工作区的命令"与 `integrate`/`accept` 不符。
11. **原提案承诺未兑现**：边界章节（与 `/wopal:evolve`、`/wopal:distill`、`ontology-maintain` 分工、overlay 说明）grep 零命中。
12. **Base Commit 记录点不一致**：记录 metadata 提交前 HEAD（evo.py:393），却从其后 HEAD 派生（evo.py:426-439），差一个提交（探针 H1 实证）。

**设计有意裁剪（非缺陷，不动）**：Issue 层、reset 回退边、verify-switch、rook 门不占状态位。

### Research Findings

- **纪律载体的代差**：dev-flow 纪律 ≈28 条铁律 + 367 行 plan-guide，载体散文、执行靠自觉；evo 已有的载体是代码：refuse-before-first-write、script-owned stage、commit/integrate 共享 preflight、幂等重入。**这是肩膀：不补散文，把纪律搬进代码。**
- **探针方法**：两轮共 8 组探针在临时仓库复刻真实布局（host main + `.wopal` on space/demo + 派生 worktree），全部结论有运行输出背书；探针脚本留存于 `.wopal-space/.tmp/evo_sparse_probes*.py`，其断言将转正为具名测试。
- **投毒形态与 2026-09-20 事故同构**：B8 的 `flags=40004000`（skip 位 + range 外标记）正是 sparse.py 头注所述事故签名——事故可以从技能自身的"正常流程 + 目录丢失"重现，而非仅由误操作触发。
- 体量对照：dev-flow ≈2025 行文档 + 10 脚本 + 37 测试文件；ontology-evolution ≈623 行文档 + 6 脚本 + 4 测试文件（82 passed）。体量差不等于缺陷——按机制逐项判定。
- canonical 流程语义：`implementing` = 实施与提交进行中；`validating` = 已集成到空间分支、等待用户重启观察确认。

**参考资料**：
- `.wopal/docs/evolutions/archived/refactor-ontology-evolution-skill-split.md` — 被审提案（契约薄化源头）
- `.wopal/skills/ontology-evolution/scripts/lib/worktree.py` — 隔离与集成实现（`_branch_patterns` 静默空返回是 E-1 根因）
- `.wopal/skills/dev-flow/scripts/commands/archive.py` — 归档卫生基准
- `.wopal/skills/dev-flow/templates/plan.md` — 模板外部化基准
- `.wopal/docs/DESIGN-evolution.md` — 状态机设计真相源

### Key Decisions

- **D-01（总则）：纪律机制化。** dev-flow 的每一条散文纪律，本技能要么升维为脚本不变量（配具名测试），要么显式拒绝继承并记录理由；禁止以散文复刻纪律。SKILL.md 只承载脚本无法强制的内容（角色分工、用户决策点、验证哲学）。
- **D-13（P0）：integrate 工作区身份守卫 + 隔离重断言。** `integrate` 前置校验：Metadata 声明的 worktree 必须存在且检出 Branch 必须与记录一致，否则拒绝并给出安全恢复指引（re-derive，而非删分支）；worktree 存在时重跑 `assert_isolated`（防御纵深：accept 后的漂移在集成前最后拦截）。
- **D-14（P0）：集成毒杀断言（corpus assertion）。** `worktree.integrate` 在 squash staged 之后、commit 之前：对全部新增 staged 路径断言 `path_in_range(path, widening 后的 space patterns)`；任一路径 range 外 → `_reset` + 列出路径拒绝。**不变量："任何进入空间分支的路径必须对运行时可见。"** 无论 widening 如何遗漏，静默投毒在此成为响亮失败。`_branch_patterns` 的"无 worktree → 静默空"路径被 D-13 前置守卫封死，本断言兜底一切残余。
- **D-15（P0）：accept 事务化。** 重排为：源 `.wopal` preflight（稀疏关闭/空 range 直接拒绝，fail fast）→ derive → assert_isolated → 全部通过后才写 metadata 并 commit。任何失败自动清理本次创建的 worktree/分支（仅限本次产物）并保持 metadata 未提交。恢复指引改为"re-accept 或显式恢复"，禁止把"删除可能载有成果的分支"作为第一建议。
- **D-02：事务化归档。** `archive` 实现为"全部 preflight（集成校验/清理目标存在性/模式判定/命名冲突）先于第一个变更，随后按序执行，任一步失败即停止并上报"，失败零残留；`--keep-worktree` 逃生口保留；quick 模式跳过清理；清理只取 Metadata 声明的 Worktree/Branch，禁止按名相似批量清理；清理前以 `_pending_content` 校验内容已集成（对齐 dev-flow `check_branch_merged`）。
- **D-03：命名不变量。** 归档落盘名是纯函数 `archive_name(date, name) -> YYYYMMDD-<name>.md`（同名冲突拒绝并提示）；`_resolve_proposal` 支持裸名 → `archived/` 带日期文件解析；`_mirror_into_worktree` 同步旧名 → 新名。
- **D-04：语料自审。** `check` 新增 corpus lint：`archived/` 内裸名文件报 warning；活跃提案不符合格式契约报 warning（draft）/ 失败（accepted+）。
- **D-07：自验证提案契约。** 模板外部化到 `templates/proposal.md`（章节对齐在用提案格式 + 逐节 authoring 注释）；evo.py 删除内嵌模板，占位符从模板文件派生；提案结构契约由 `check` 机械校验（Task 六要素），draft 警告、accepted+ 失败；`accept` 前置同一校验。
- **D-08：集中守卫表。** 单一 `_GUARDS` 映射（command → 前置 stage）派生所有命令前置检查，配全命令穷举测试；拒绝信息统一含当前 stage、合法前置、可复制的 next command。
- **D-09：Base Commit 同源。** 记录点统一为派生 worktree 的实际分叉 HEAD，一次读取两处共用。
- **D-10：不变量测试矩阵。** 既有与新增安全性质全部具名测试化：refuse-before-first-write、零副作用拒绝、幂等重入、稀疏安全（range widen 先于 staging）、**集成毒杀断言（B1-B8 转正）**、**accept 事务零残渣（G4-G6 转正）**、**失败 integrate 恢复干净且 untracked 幸存（E4-E8 转正）**、事务化归档失败零残留、命名纯函数（冲突 + 截断）。
- **D-11：文档降维。** 三源文档对齐 canonical 语义；已机制化的铁律从散文删除（如 "never git add -A" 压缩为一句机制指向）；Landing 流程统一为 `new → 用户读 → accept → advance --to implementing → 实施 + commit(s) → integrate → advance --to validating → 用户重启观察确认 → advance --to archived → archive`；删除过期文案；新增 Boundary 分工小节。**SKILL.md 净变短是质量信号。**
- **D-12：TDD 强制。** 新增行为先写失败测试；测试仓库只在临时目录构造。

### Key Interfaces

`evo.sh integrate`（守卫 + 毒杀断言）：

```text
evo.sh integrate <name>
# preflight: recorded worktree 存在 && 检出分支 == recorded Branch
#            && assert_isolated(worktree) 通过 && space 侧 preflight 通过
# squash staged 后、commit 前: 新增 staged 路径必须全部 in-range，
# 否则 reset + 列出路径 + 拒绝（毒杀断言）
# worktree 缺失: 拒绝 + 恢复指引（re-derive; 不建议删分支）
```

`evo.sh accept`（事务化）：

```text
evo.sh accept <name> [--no-worktree]
# preflight: check 全量校验通过 && 源 .wopal 稀疏形态健康（enabled + 非空 range）
# 顺序: derive -> assert_isolated -> 成功后才写 metadata + commit
# 任一步失败: 清理本次创建的 worktree/分支, metadata 不落盘, 零残渣
```

`evo.sh archive`（事务化）：

```text
evo.sh archive <name> [--keep-worktree]
# preflight 全过 -> 变更序列；任一步失败即停止，零残留
# 落盘: docs/evolutions/archived/YYYYMMDD-<name>.md（同名已存在则拒绝）
# isolated: 集成守卫通过后清理 Metadata 声明的 Worktree/Branch（--keep-worktree 跳过）
# quick: 不触碰 worktree/分支
```

`evo.sh check`（维度扩展）：结构契约（Task 六要素，draft 警告 / accepted+ 失败）+ 语料自审（archived 裸名 warning；活跃提案格式不符 warning/失败）。

守卫表（单一真相源，示意）：`_GUARDS = {"commit": "implementing", "integrate": "implementing", "archive": "archived", ...}`

## In Scope

- `evo.py` + `lib/worktree.py`：integrate 身份守卫与毒杀断言、accept 事务化与源 preflight、失败自动清理、恢复指引修正
- `evo.py` + `lib/`：事务化归档、命名纯函数与解析、集中守卫表、模板加载外部化、check 结构契约 + 语料自审、Base Commit 同源、slug 长度截断
- `templates/proposal.md` 新建（含逐节 authoring 注释）
- `SKILL.md` / `references/commands.md` 文档降维与对齐
- `docs/DESIGN-evolution.md` 状态语义措辞统一
- `assembly/archetypes/coding.yaml` 尾随空格 hygiene
- `tests/python/` 不变量测试矩阵补齐（探针断言转正 + TDD 红绿）

## Out of Scope

- 现档文件 `refactor-ontology-evolution-skill-split.md` 是否补 `YYYYMMDD-` 重命名 —— 历史归档不追溯，需用户单独拍板
- 遗留分支 `wopal-space-ontology-evolution-skill-split` 删除 —— 需用户明确确认（非快进，需 `-D`）
- zh-CN 镜像 / troubleshooting / proposal-guide / `list` 命令 —— 低优先级，用户决定是否另立提案
- `enhance-workflow-deferred-plan-lifecycle.md` 旧格式迁移 —— 另行处理
- Issue 层 / reset / verify-switch / rook 状态位 —— 设计有意裁剪，维持

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| scripts | `scripts/evo.py`, `scripts/lib/worktree.py` | 修改 | 毒杀断言 / 身份守卫 / accept 事务化 / 守卫表 / 归档 / 模板加载 / 结构契约 / slug 截断 |
| templates | `templates/proposal.md` | 创建 | 模板外部化（唯一模板源） |
| docs | `SKILL.md`, `references/commands.md` | 修改 | 文档降维与契约对齐 |
| design | `docs/DESIGN-evolution.md` | 修改 | 状态语义措辞统一 |
| assembly | `assembly/archetypes/coding.yaml` | 修改 | 尾随空格 hygiene |
| tests | `tests/python/unit/*.py` | 修改/创建 | 不变量测试矩阵（探针转正 + TDD） |

## Acceptance Criteria

### Agent Verification

1. [ ] **集成毒杀不可达**（临时仓库实跑）：worktree 缺失时 `integrate` 拒绝（exit 非零、零变更、恢复指引不含"删分支"）；worktree 在杂散分支时拒绝；worktree 健康 range 被人为缩窄致新增 staged 路径出 range 时，毒杀断言在 commit 前 reset 并拒绝；happy path 不受影响（对照既有 `test_integrate_squashes_work_into_space_branch`）
2. [ ] **accept 事务化**：源 `.wopal` 稀疏 disable 时 accept 在 derive 前拒绝（零 worktree/分支/ metadata 残留）；derive 或 assert 失败时自动清理本次产物，metadata 未提交；happy path 与幂等 re-accept 行为不变
3. [ ] **失败路径零残留**：冲突 squash 被拒后 `.wopal` clean、无 unmerged 条目；range 内 untracked 文件在拒绝后幸存（E4-E8 转正为具名测试）
4. [ ] **事务化归档**：归档后为 `YYYYMMDD-<name>.md`；隔离模式下 Metadata 声明的 worktree 目录与分支已清除、`--keep-worktree` 保留；特性未集成时拒绝（零残留）；quick 模式不触碰 worktree/分支；同名归档已存在时拒绝
5. [ ] **自验证提案契约**：`evo.sh new` 产出与在用提案章节一致；evo.py 无内嵌模板、占位符从模板文件派生；Task 缺六要素时 draft 警告、accepted+ 失败；`accept` 对未通过校验的提案拒绝
6. [ ] **语料自审**：`check` 对 `archived/` 裸名文件报 warning，对活跃提案旧格式报 warning（draft）/失败（accepted+）
7. [ ] **集中守卫表**：Stage != `implementing` 时 `commit`/`integrate` 拒绝且 exit 非零、零副作用，拒绝信息含当前 stage 与可复制的 next command；re-advance 当前 stage 为 no-op
8. [ ] **Base Commit 同源**：Metadata 记录值 == worktree 实际分叉 HEAD
9. [ ] **文档降维**：SKILL.md 无 "no worktree-manager layer"；Landing 流程与 D-11 顺序一致；已机制化铁律不在散文中复刻；Boundary 小节覆盖 `/wopal:evolve`、`/wopal:distill`、`ontology-maintain`、overlay；SKILL.md 行数 < 240
10. [ ] **不变量测试矩阵全绿**：毒杀断言 / accept 事务 / 失败零残留 / refuse-before-write / 幂等重入 / 稀疏安全 / 事务化归档 / 命名纯函数均有具名测试；`python3 -m pytest tests/python/ -q` 全绿，存量 82 用例无回归

### User Validation

#### Scenario 1: 技能改动在 ellamaka 中正常加载
- Goal: 确认修改后的 ontology-evolution 技能被 ellamaka 正常加载，evo.sh 全命令可用
- 验证环境: `.wopal` 装配 worktree（space 分支已集成），ellamaka 桌面端
- Precondition: integrate 完成且 `evo.sh status` 显示 validating
- 启动命令: 重启 ellamaka
- User Actions:
  1. 打开 ellamaka，确认 ontology-evolution 技能出现在可用技能列表
  2. 对任一提案执行 `evo.sh status <name>` 观察输出
- 通过判据: 技能列表含 ontology-evolution；status 输出含 Stage / Mode / Worktree / Branch / Base Commit / Next 字段且与提案文件 Metadata 一致
- 失败反馈: 提供 ellamaka 启动日志与 `evo.sh status` 完整输出

- [ ] 用户已完成上述功能验证并确认结果符合预期

## Implementation

### Task 1: 稀疏 worktree 正确性：毒杀断言 + 身份守卫 + accept 事务化（P0）

**Verification Intent**: AC#1, AC#2, AC#3, AC#8（Base Commit 同源随本 Task 顺带统一）

**Behavior**:
- worktree 缺失（目录删、分支在）→ `integrate` 拒绝：exit 非零、`.wopal` 零变更、指引为 re-derive/re-accept 而非删分支
- worktree 检出分支 != recorded Branch → `integrate` 拒绝
- 新增 staged 路径任一在 widening 后仍出 range → commit 前被毒杀断言拦截：`_reset` 执行、路径清单打印、exit 非零
- `integrate` 前置重跑 `assert_isolated`，漂移即拒绝
- 源 `.wopal` 稀疏 disable / 空 range → `accept` 在 derive 前拒绝，零残留
- derive / assert 失败 → accept 自动清理本次创建的 worktree 与分支，metadata 未提交
- Metadata Base Commit == worktree 实际分叉 HEAD
- 回归保护：happy path integrate/accept、幂等 re-accept、冲突 reset 干净、untracked 幸存（既有测试全绿）

**Pre-read**: `.wopal/skills/ontology-evolution/scripts/lib/worktree.py`（`integrate`、`_branch_patterns`、`derive`）、`scripts/evo.py`（`cmd_accept`、`cmd_integrate`）、`.wopal-space/.tmp/evo_sparse_probes.py` 与 `evo_sparse_probes2.py`（探针断言即测试蓝本）

**Design**: `cmd_integrate` 增加 worktree 存在性与分支一致性前置（D-13）；`worktree.integrate` 在 `merge --squash` staged 后、`reapply` 与 commit 之间插入毒杀断言：`diff --cached` 新增路径逐一 `path_in_range`，失败走既有 `_reset`（D-14）；`cmd_accept` 重排为 preflight 源健康 → derive → assert → 提交 metadata，失败清理仅限本次产物（D-15）；Base Commit 读取点与 derive 共用同一次 HEAD（D-09 顺带落地）。所有检查先于第一个变更。

**TDD**: true

**Changes**:
1. RED：探针 B1-B8 / G4-G6 / E4-E8 / R1-R3 断言全部转正为失败测试（临时仓库 fixture）
2. GREEN：实现身份守卫 + 毒杀断言 + accept 事务化 + Base Commit 同源
3. 更新 `references/commands.md` 的 integrate / accept 契约

**Verify**: `python3 -m pytest tests/python/ -q` 全绿

**Done**:
任务产出：稀疏 worktree 机制正确性闭环（毒杀不可达 / 事务化 accept / 零残留失败路径）。
实际触碰文件：`scripts/evo.py`、`scripts/lib/worktree.py`、`tests/python/unit/test_sparse_safety.py`
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤

### Task 2: 事务化归档：命名不变量 + 清理 + 集成守卫（P0）

**Verification Intent**: AC#4

**Behavior**:
- `archive_name(date, name)` 纯函数产 `YYYYMMDD-<name>.md`；目标已存在 → 拒绝不覆盖
- archive 后新名存在、原路径不存在；`status <裸名>` 解析到 archived 带日期文件
- 隔离模式 archive 成功后 Metadata 声明的 worktree 目录与分支不存在；`--keep-worktree` 全保留
- `_pending_content` 非空 → archive 拒绝且零残留；quick 模式不触碰 worktree/分支
- preflight 任一检查失败 → 无任何变更发生

**Pre-read**: dev-flow `archive.py`（`_cleanup_worktree`、`check_branch_merged`）、evo `cmd_archive`、`_pending_content`

**Design**: `cmd_archive` 两段式——preflight（集成守卫 / 清理目标存在性 / 模式 / 命名冲突）全过后进入变更序列（move → remove → prune → branch -D）；`-D` 仅在 `_pending_content` 已证实内容集成后使用，失败停止上报；命名走纯函数；`_mirror_into_worktree` 处理旧名 → 新名。

**TDD**: true

**Changes**:
1. RED：上述 Behavior 落成失败测试（含 preflight 失败零残留断言）
2. GREEN：实现纯函数命名 + 两段式事务归档 + 守卫 + keep 逃生口 + 裸名解析
3. 同步 `references/commands.md` archive 契约

**Verify**: `python3 -m pytest tests/python/ -q` 全绿

**Done**:
任务产出：事务化归档闭环。
实际触碰文件：`scripts/evo.py`、`tests/python/unit/test_sparse_safety.py`、`tests/python/unit/test_cli_behavior.py`
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤

### Task 3: 自验证提案契约：模板外部化 + 结构契约 + 语料自审（P1）

**Verification Intent**: AC#5, AC#6

**Behavior**:
- `evo.sh new` 从 `templates/proposal.md` 加载填充，产出完整骨架；evo.py 无 `PROPOSAL_TEMPLATE` 常量；占位符从模板文件派生
- `check` 对缺 Task 六要素的提案：draft 警告；accepted 及以后失败；`accept` 前置同一校验
- `check` 语料自审：`archived/` 裸名文件 → warning；活跃提案缺格式契约节 → draft warning / accepted+ 失败

**Pre-read**: dev-flow `templates/plan.md`（注释风格基准）、evo `cmd_new` / `_placeholders` / `cmd_check`

**Design**: 新建 `templates/proposal.md`（骨架对齐在用提案实态，逐节 authoring 注释——注释承载"怎么写"、check 强制"写没写"）；`cmd_new` 读文件替换占位符；`_placeholders()` 改从文件解析；`cmd_check` 新增结构扫描（仅 prose）与 corpus lint；`cmd_accept` 前置调用。

**TDD**: true

**Changes**:
1. RED：模板加载、占位符派生、结构契约分级、accept 门控、corpus lint 落成失败测试
2. GREEN：实现模板文件加载 + 结构契约 + 语料自审
3. REFACTOR：删除内嵌模板与旧占位符逻辑

**Verify**: `python3 -m pytest tests/python/ -q` 全绿，且 `evo.sh new` 实跑产出与在用提案章节一致

**Done**:
任务产出：自验证提案契约闭环。
实际触碰文件：`scripts/evo.py`、`templates/proposal.md`、`tests/python/unit/test_sparse_safety.py`
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤

### Task 4: 集中守卫表 + 拒绝信息标准化（P1）

**Verification Intent**: AC#7

**Behavior**:
- `_GUARDS` 表外所有命令前置 stage 与表一致（穷举测试：每命令 × 每 stage）
- Stage ∈ {draft, accepted, validating, archived} 时 `commit` 拒绝；Stage != `implementing` 时 `integrate` 拒绝；均 exit 1、零副作用
- 拒绝信息统一含当前 stage、合法前置、可复制的 next command
- re-advance 当前 stage 仍为 no-op

**Pre-read**: evo `cmd_commit` / `cmd_integrate`、dev-flow `guard_status`（对照）

**Design**: 模块级 `_GUARDS` 映射，命令入口统一 `_guard_stage(command, proposal)`；与 Task 1/3 的前置检查合并为统一入口，避免散落。

**TDD**: true

**Changes**:
1. RED：穷举守卫矩阵、拒绝信息格式、幂等回归落成失败测试
2. GREEN：实现守卫表与统一入口

**Verify**: `python3 -m pytest tests/python/ -q` 全绿

**Done**:
任务产出：集中守卫表。
实际触碰文件：`scripts/evo.py`、`tests/python/unit/test_sparse_safety.py`
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤

### Task 5: 文档降维：矛盾消除 + 流程修正 + Boundary（P1）

**Verification Intent**: AC#9

**Behavior**:
- SKILL.md / commands.md / DESIGN-evolution.md 的流程、状态语义与实际脚本一致；SKILL.md 仅承载脚本无法强制的边界与用户决策点。

**Pre-read**: `SKILL.md`、`references/commands.md`、`.wopal/docs/DESIGN-evolution.md`

**Design**: SKILL.md：删除 :124 过期文案；Landing 流程按 D-11 重写；状态表语义统一（implementing = 实施进行中；validating = 已集成待用户确认）；"commit 唯一写工作区"修正；已机制化铁律压缩为一句机制指向；新增 Boundary 分工小节（语义车道提案、机制车道落地、`/wopal:evolve` 与 `/wopal:distill` 为用户入口、`ontology-maintain` 为维护操作、overlay 边界）。commands.md：integrate / accept / archive / check / commit 契约与实现对齐。DESIGN-evolution.md：状态措辞统一。验收信号：SKILL.md 行数下降。

**TDD**: false（纯文档）

**Changes**:
1. SKILL.md 矛盾消除、流程重写、铁律去散文、Boundary 小节
2. commands.md 契约对齐
3. DESIGN-evolution.md 措辞统一

**Verify**: grep 断言 AC#9 各项；行数对比记录于 Done

**Done**:
任务产出：三源文档降维对齐。
实际触碰文件：`SKILL.md`、`references/commands.md`、`AGENTS.md`、`docs/DESIGN-evolution.md`
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤

### Task 6: P2 收口：slug 截断 + status 增强 + hygiene

**Verification Intent**: AC#10（回归保护）

**Behavior**:
- slug 纯函数：>55 字符输入产出 `截断(≤55)-<4hex>`
- `evo.sh status` 在 Metadata 已记录时输出 Worktree / Branch / Base Commit 行
- `assembly/archetypes/coding.yaml` 无尾随空格

**Pre-read**: `lib/worktree.py`（slugify）、dev-flow 对应截断实现

**Design**: 移植 dev-flow 命名边界为纯函数；status 增补三行；coding.yaml 单字符修正以 quick 方式落地。

**TDD**: true

**Changes**:
1. RED：slug 截断（边界值 55/56）落成失败测试
2. GREEN：实现截断 + status 增补 + yaml hygiene

**Verify**: `python3 -m pytest tests/python/ -q` 全绿；`grep -n ' $' assembly/archetypes/coding.yaml` 零命中

**Done**:
任务产出：命名边界 + status 信息量 + hygiene 收口。
实际触碰文件：`scripts/evo.py`、`scripts/lib/worktree.py`、`assembly/archetypes/coding.yaml`、`tests/python/unit/test_sparse_safety.py`
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤

---

## Delegation Strategy

| Wave | Task | 执行者 | 依赖 | 委派理由 |
|------|------|--------|------|---------|
| 1 | Task 1 | fae | 无 | 稀疏机制正确性是其余一切的地基，最先落地 |
| 2 | Task 2 | fae | Wave 1 | 事务化归档复用 Task 1 的清理与守卫原语 |
| 3 | Task 3, Task 4 | fae | Wave 2 | 同改 evo.py，串行防冲突 |
| 4 | Task 5, Task 6 | fae | Wave 3 | 文档降维依赖最终实现形态；收口项并行 |

## Delivery

`space sync` 与 `ontology contribute` 由用户拍板，技能不自动上行。

# dev-flow 技能问题分析备忘

> **日期**: 2026-05-20
> **状态**: 待决策
> **背景**: Wopal 深度分析 dev-flow 技能实现，识别当前流程架构问题与优化方向

---

## 一、当前流程架构概览

### 状态机

```
planning → executing → verifying → done
```

**特征**: 强制线性推进，不可回退（除非 `reset`）

### 命令链

```
plan → approve → approve --confirm → complete → verify --confirm → archive
```

### 关键门控

| 阶段 | 门控命令 | 检查项 |
|------|---------|--------|
| approve 前 | `check_doc_plan()` | Plan 完整性（Task 字段、AC 格式、无占位符） |
| complete 前 | `check_step_completion()` + `check_acceptance_criteria()` | Done checkbox + Agent Verification checkbox |
| verify --confirm 前 | `check_user_validation()` | User Validation 最终 checkbox |

---

## 二、核心问题清单

### P1: 状态机强制顺序过强，无局部修正路径

**现象**: executing 发现 Plan 有缺陷 → 必须全局 `reset` → planning → 重走流程

**代码位置**: `approve.py:317-330` — `guard_status()` 强制状态匹配，只返回错误无修正路径

**影响**:
- 用户体验差，返工成本高
- 不支持"局部修订"（只修改某个 Task）后继续实施
- 大型 Issue（10+ Tasks）风险放大：发现遗漏 → reset → 重做已完成的 Task

**场景示例**: 实施 Task 1-5 后发现 Task 3 设计遗漏 → 当前流程：reset → planning → 修订 → approve --confirm → complete → 重做 Task 1-5 + Task 6-10

---

### P2: rook 审查时机固定，滞后成本高

**现象**: 审查只在 approve 前 + complete 前触发，无法介入实施过程

**SKILL.md 定义**:
> - Plan 写完后（approve 前）— 审方案质量
> - fae 最终交付后（complete 前）— 最终审查

**影响**:
- 大型 Issue 实施周期长 → 审查滞后 → 发现问题时已大量返工
- 无"Wave 审查"机制（每完成一组 Task 就审查）
- 无法支持用户主动触发审查

**场景示例**: 实施 Task 1-5 后发现 Task 3 设计缺陷 → 当前流程：必须等 Task 6-10 完成 → rook BLOCK → 修复 Task 3 → 重新审查 → 返工 Task 6-10（依赖链）

---

### P3: Done checkbox 更新依赖文字提醒，易遗漏

**现象**: 委派 prompt 必含项只是 SKILL.md 文字指令，无强制注入机制

**plan-authoring.md:75-80**:
```markdown
每次委派 fae 执行 Plan Task 时，prompt 末尾必须附加：

    完成后在 Plan 文件中编辑对应 Task 的 Done checkbox（- [ ] → - [x]）
    禁止修改 Plan Status
```

**影响**:
- Wopal 容易遗漏该指令（文字提醒无强制检查）
- fae 完成 Task 但忘记勾选 Done → `complete` 被 `check_step_completion()` 阻断
- 只检查 checkbox 是否 `[x]`，不验证是否与 git diff 匹配（假勾选风险）

**代码位置**: `check_doc.py:479-511` — `_check_done_completion()` 只检查 checkbox，无 git diff 验证

---

### P4: worktree 验证切换流程复杂，两阶段需手动协调

**现象**: `verify-switch` 两阶段流程分散在不同代码分支，用户需理解 Phase 1/2 区分

**当前流程**:
1. Phase 1: `flow.sh verify-switch <issue>` → 移除 worktree → 切换到 feature 分支 → **重启 ellamaka**
2. Phase 2: 用户验证通过后 → `flow.sh verify-switch <issue> --merge` → merge → verify --confirm

**代码位置**: `verify_switch.py:113-166` — 两阶段分散在不同 `if/else` 分支

**影响**:
- Phase 1 后需重启 ellamaka（增加操作成本）
- Phase 2 merge 有冲突时流程卡住（无自动解决）
- 用户容易混淆两阶段触发时机

---

### P5: Plan 编写负担重，小 Issue 成本不成比例

**现象**: `check_doc` 验证要求过细，不区分 Issue 复杂度

**plan-validation.md:18-25**: Task 字段 9 个必填项（Verification Intent / Behavior / Design / TDD / Changes / Verify / Done / Files / Pre-read）

**影响**:
- fix typo 类 Issue → Plan 编写成本远超实施成本
- Planner 容易遗漏字段 → 反复被 `check_doc` 阻断
- Plan 文件篇幅长（10+ Tasks 的 Issue 可达 100+ 行）

**代码位置**: `check_doc.py:610-641` — `check_task_structure()` 对所有 Task 无差别校验

---

### P6: Issue 同步逻辑分散，状态易不一致

**现象**: Issue 同步分散在多个命令，逻辑不统一

**代码位置**:
- `approve.py:541-549`: sync status label + sync plan body + ensure labels
- `complete.py:316-322`: sync status label + sync Agent Verification
- `verify.py`: sync status label → close issue（archive 前）

**影响**:
- Issue 状态与 Plan 状态不完全一致（同步时机分散）
- Issue body 更新频率高，但可能只同步部分章节
- 同步逻辑维护成本高（分散在多个文件）

---

### P7: 实施过程无进度追踪，进度不透明

**现象**: executing 状态无进度指标，用户/Wopal 人工读取 Plan 检查 Done checkbox

**影响**:
- 大型 Issue 实施周期长 → 进度不透明
- 用户询问进度 → Wopal 花费上下文读取 Plan 检查 Done
- 无"进度可视化"（Issue comment / Plan metadata Progress 字段）

---

### P8: reset 命令破坏性强，无警告与清理

**现象**: reset 直接回退 Plan Status，不检查已实施代码

**推断**: reset 只更新 Plan Status，不处理：
- 已提交的 git commit
- 已创建的 worktree
- Issue 状态回退

**影响**:
- reset 后已实施代码仍在 git → Plan 回到 planning → 状态不一致
- worktree 残留 → 用户需手动清理
- Issue 状态未同步 → 外部观察者看到 Issue 仍在 executing

---

### P9: archive 命令职责过重，状态不一致风险

**现象**: archive 同时处理 push + 归档 + Issue 关闭

**影响**:
- archive 失败（push 出错）→ Plan 已归档 + Issue 已关闭 → 状态不一致
- 职责不清，维护成本高
- 归档路径硬编码，不支持自定义

---

### P10: 命令参数不一致，Issue 驱动 vs Plan 驱动混淆

**现象**: 参数命名不统一，同一参数位置接收不同类型

**代码证据**:
- `approve <issue>` vs `approve <plan-name>`（同一参数位置，不同类型）
- `complete <issue>` vs `complete <plan-name>`
- `plan` 命令只有 `plan --title`（无 `plan <issue>` 模式）

**影响**:
- 用户容易混淆参数类型
- 文档负担重（需解释两种模式）
- 命令帮助信息不一致

---

## 三、优化方向分类

### A. 流程灵活性（高优先级）

| 优化项 | 方案 | 成本 | 收益 | 优先级 |
|-------|------|------|------|--------|
| 支持回退 | executing → planning（带警告）→ 修订 → continue | 中 | 减少全局 reset，降低返工成本 | P1 |
| Wave 审查 | 每完成 Wave → 自动委派 rook | 高 | 审查前置，降低滞后成本 | P2（需评估 ROI） |
| 进度追踪 | 增加 `progress` 命令 + Issue comment 自动更新 | 中 | 进度透明，减少用户询问成本 | P7 |

---

### B. 质量门优化（高优先级）

| 优化项 | 方案 | 成本 | 收益 | 优先级 |
|-------|------|------|------|--------|
| Done 更新强制注入 | 在委派工具层自动注入 Done 更新指令（而非文字提醒） | 中 | 杜绝遗漏，降低 complete 阻断率 | P3 |
| Done 验证增强 | complete 时检查 git diff → Task 文件变更是否匹配 | 高 | 防止假勾选，提升质量门有效性 | P3 |
| 轻量 Plan 模式 | 针对 fix/docs/perf 类 Issue，减少必填字段（Behavior/TDD 可选） | 中 | 降低小 Issue 编写成本 | P5 |

---

### C. 命令一致性（中优先级）

| 优化项 | 方案 | 成本 | 收益 | 优先级 |
|-------|------|------|------|--------|
| 统一参数命名 | 增加 `--issue <N>` / `--plan <name>` 明确区分 | 低 | 降低用户混淆，文档简化 | P10 |
| Issue 同步统一 | 提取 `sync_issue_state(issue, plan, status)` 统一入口 | 中 | 状态一致性，维护成本降低 | P6 |
| reset 增强 | 增加 `--clean` 选项（回退 git commit + 清理 worktree） + 强制警告 | 低 | 降低状态不一致风险 | P8 |

---

### D. worktree 流程简化（中优先级）

| 优化项 | 方案 | 成本 | 收益 | 优先级 |
|-------|------|------|------|--------|
| verify-switch 单命令 | 合并 Phase 1/2 → `flow.sh verify-worktree <issue>` 自动检测阶段 | 中 | 降低用户操作成本，减少混淆 | P4 |
| 预检 merge | Phase 1 时提前检测 merge 是否有冲突 → 提示用户 | 低 | 降低流程卡住风险 | P4 |

---

## 四、实施建议

### 优先级排序（按收益/成本）

| 序号 | 优化项 | 成本 | 收益 | 决策建议 |
|------|-------|------|------|---------|
| 1 | 统一参数命名 | 低 | 高 | **立即实施** |
| 2 | reset 增强 | 低 | 高 | **立即实施** |
| 3 | Issue 同步统一 | 中 | 高 | **立即实施** |
| 4 | Done 更新强制注入 | 中 | 高 | **高优先级** |
| 5 | 支持回退 | 中 | 高 | **高优先级** |
| 6 | 进度追踪 | 中 | 中 | **中优先级** |
| 7 | 轻量 Plan 模式 | 中 | 中 | **中优先级** |
| 8 | Wave 审查 | 高 | 高 | **需评估 ROI（大型 Issue 比例）** |
| 9 | verify-switch 简化 | 中 | 中 | **中优先级** |

### 实施路径

**阶段 1（低成本高收益）**:
- [ ] 统一参数命名（`--issue` / `--plan`）
- [ ] reset 增强（警告 + `--clean` 选项）
- [ ] Issue 同步统一入口（`sync_issue_state()`）

**阶段 2（质量门强化）**:
- [ ] Done 更新强制注入（工具化）
- [ ] 支持 executing → planning 回退
- [ ] 增加进度追踪（`progress` 命令）

**阶段 3（流程优化）**:
- [ ] Wave 审查机制（需评估大型 Issue 比例）
- [ ] 轻量 Plan 模式（需定义简化规则）
- [ ] worktree 流程简化（verify-switch 单命令）

---

## 五、技术债清单

| 类别 | 当前状态 | 建议 | 对应问题 |
|------|---------|------|---------|
| 代码分散 | Issue 同步逻辑分散在 3+ 文件 | 提取统一模块 `sync_issue_state()` | P6 |
| 状态一致性 | reset 不清理 worktree/git commit | 增强 reset 或引入 StateCleaner | P8 |
| 参数一致性 | 同一参数位置接收不同类型 | 明确区分 `--issue`/`--plan` | P10 |
| 文档负担 | SKILL.md + 6 个 references + troubleshooting | 统一到命令帮助 + 按需 references | P10 |
| 质量门弱化 | Done 验证只检查 checkbox | 增加 git diff 验证 | P3 |

---

## 六、决策待定项

1. **Wave 审查 ROI**: 需统计当前空间大型 Issue（10+ Tasks）比例 → 决定是否投入
2. **轻量 Plan 模式规则**: 需定义哪些 Issue 类型适用简化规则（fix/docs/perf vs feature/refactor）
3. **回退路径设计**: executing → planning 后如何处理已实施代码（保留还是回滚 git commit）
4. **进度追踪方式**: Issue comment 自动更新 vs Plan metadata Progress 字段

---

## 七、新增优化提案: rook 文档一致性审查

### P11: 项目文档与代码脱节，业务逻辑未文档化

**现象**：当前 dev-flow 流程只关注 Plan → 代码 → 验证闭环，**缺失文档更新环节**

**实际状态**：
- PRD 文档停留在创建时状态，极少更新
- DESIGN 文档与实现不一致（架构变更未同步）
- 每个项目的功能版图缺失（只有碎片化的 Plan，无全景）
- 业务逻辑锁在代码中，无文档化沉淀

**代码证据**：
- `archive.py` 只处理 Plan 归档 + Issue 关闭，无文档检查
- `check_doc.py` 只检查 Plan 质量，不检查项目文档一致性
- `.wopal-space/STRUCTURE.md` 项目索引列出 7 个项目，但只有 3 个有 PRD/DESIGN
- PRD 文档最后更新日期：ontology（2026-05-07）、wopal-cli（2026-03-20）、space-flow（2026-04-10）

**影响**：
- 新开发者（或未来的 Wopal）无法快速理解项目全貌
- 功能演进历史断层，无法追溯设计决策
- 重构时缺乏文档支撑，容易误伤隐性业务逻辑
- 空间协作可靠性降低（文档是上下文的重要载体）

---

### E. 文档一致性审查（高优先级）

| 优化项 | 方案 | 成本 | 收益 | 优先级 |
|-------|------|------|------|--------|
| PRD 简化 | 12 章节 → 8 章节，移除冗余，新增"功能版图"章节 | 低 | 减少文档负担，职责清晰 | P11 |
| Plan check 文档计划 | check_doc 强制检查"Document Update Plan"章节 | 低 | 规划阶段就考虑文档，源头保障 | P11 |
| rook 分类文档审查 | 功能变化查 PRD（功能版图），设计变化查 DESIGN | 中 | 精准检查，不无差别审查 | P11 |
| 文档优化闭环 | Plan → 实施同步更新 → rook 审查 → archive 确认 | 高 | 系统化闭环，一次到位 | P11 |

---

## 八、文档一致性审查实施方案（方案 C-2）

### 8.1 核心问题诊断

**当前文档状态**（基于实际检查）：

| 项目 | PRD 状态 | DESIGN 状态 | FEATURES 状态 | 最后更新 |
|------|---------|-------------|--------------|---------|
| ontology | ✅ 有 PRD | ❌ 无 DESIGN | ❌ 无 | 2026-05-07 |
| wopal-cli | ✅ 有 PRD | ✅ 有 DESIGN | ❌ 无 | 2026-03-20（设计）<br>2026-05-15（PRD） |
| space-flow | ✅ 有 PRD | ✅ 有 DESIGN | ❌ 无 | 2026-04-10 |
| ellamaka | ❌ 无 PRD | ❌ 无 DESIGN | ❌ 无 | — |
| gesp | ❌ 无 PRD | ❌ 无 DESIGN | ❌ 无 | — |
| firecrawl | ✅ 有 PRD | ✅ 有 DESIGN | ❌ 无 | 2026-04-14 |

**问题根因**：
1. dev-flow 流程无文档更新节点
2. Plan 是临时方案，不是持久文档
3. 缺乏项目级文档结构规范
4. archive 只归档 Plan，不触达项目文档

---

### 8.2 文档体系设计（方案 C-2）

**核心决策**：不新增 FEATURES.md，功能版图作为 PRD 的新增章节（§6）。

**PRD 简化前后对比**：

| 原结构（12 章节 + 附录） | 简化后（8 章节） | 理由 |
|------------------------|-----------------|------|
| §1 执行摘要 | §1 执行摘要（含成功标准） | 保留，合并 §8 成功标准 |
| §2 使命 | §2 使命（含用户场景） | 保留，合并 §6 用户场景 |
| §3 定位 | §3 定位 | 保留 |
| §4 目标用户 | §4 目标用户 | 保留 |
| §5 产品范围 | §5 产品范围（概括级） | 保留，保持概括级描述 |
| §6 用户场景 | — | 合并到 §2 使命 |
| §7 技术栈 | — | 移到 DESIGN 文档 |
| §8 成功标准 | — | 合并到 §1 执行摘要 |
| §9 演进路线 | §7 演进路线（含实现阶段） | 保留，合并 §10 |
| §10 实现阶段 | — | 合并到 §7 演进路线 |
| §11 风险与缓解 | — | 移出（精简为附录或删除） |
| §12 相关文档 | §8 相关文档 | 保留 |
| 附录 | — | 合并到 §7 演进路线 |
| — | **§6 功能版图（新增）** | 细粒度功能清单 + 业务逻辑 + 演进历史 + 依赖关系 |

**简化后 PRD 模板**：

```markdown
# <Project> PRD

> **状态**: Active | Draft
> **创建日期**: <date>
> **更新日期**: <date>
> **项目路径**: projects/<name>/（或 .wopal/）
> **配套文档**: DESIGN-<project>.md

---

## 1. 执行摘要

<产品定位、核心能力、当前状态、关键指标>

---

## 2. 使命

<使命声明 + 核心原则 + 关键用户场景>

---

## 3. 在 WopalSpace 中的定位

<与其他组件的关系、所属层、职责域>

---

## 4. 目标用户

| 用户类型 | 技术水平 | 核心需求 | 痛点 |
|---------|---------|---------|------|

---

## 5. 产品范围（概括级）

### 5.1 已落地能力

<按大类分组，概括级描述>

### 5.2 当前边界外

<不在当前范围内的能力>

---

## 6. 功能版图（细粒度级，新增） 🆕

> **⚠️ 高频更新区**: 此章节在每次 feat/enhance 变更时同步更新。
> PERF / REFACTOR 变更如果涉及功能变化也需更新。

### 6.1 功能清单

| 功能 | Issue | 实现日期 | 状态 | 描述 |
|------|-------|---------|------|------|

### 6.2 关键业务逻辑

<从代码中提取的关键业务逻辑，按模块组织>

### 6.3 功能演进历史

| 日期 | 变更类型 | 功能 | Issue | 描述 |
|------|---------|------|-------|------|

### 6.4 功能间依赖关系

<用文本或 ASCII 图描述依赖关系，重构时的保护网>

---

## 7. 演进路线

<当前 Phase + 已完成阶段 + 后续规划>

---

## 8. 相关文档

| 文档 | 位置 | 说明 |
|------|------|------|
```

**DESIGN 文档**：保持现有结构，额外承担"技术栈"内容（从 PRD §7 移入）。

---

### 8.3 文档优化闭环

```
Issue 创建
  │
  ├─ Type: feat → PRD §6 可能需更新
  │        enhance → PRD §6 可能需更新
  │        refactor → DESIGN 可能需更新
  │        perf → DESIGN 可能需更新
  │        fix/docs/chore → 不需要文档更新
  │
  ▼
Plan check（check_doc_plan 增强）
  │
  ├─ 如果 Type ∈ {feat, enhance, refactor, perf}
  │   └─ 必须包含 "### Document Update Plan" 章节
  │        ├─ 列出需要更新的文档（PRD / DESIGN）
  │        ├─ 说明每个文档的变更内容
  │        └─ 若不需要更新，写 "— | — | 无文档变更 | —"
  │
  ├─ 若缺失 → BLOCK Plan（无法 approve）
  └─ 若存在 → Plan 通过
  │
  ▼
approve --confirm → 开始实施
  │
  ├─ fae 实施代码变更
  └─ Wopal 按 Document Update Plan 同步更新文档
      ├─ feat/enhance → 更新 PRD §6 功能版图
      └─ refactor/perf → 更新 DESIGN 相关章节
  │
  ▼
complete 前
  │
  ├─ rook 审查：df-implement-review（代码质量）
  └─ rook 审查：df-doc-review（文档一致性）
        ├─ 根据 Plan Type 决定检查哪个文档
        │   ├─ feat/enhance → 检查 PRD §6 是否已更新
        │   └─ refactor/perf → 检查 DESIGN 是否已同步
        ├─ 对比代码变更 vs 文档内容
        └─ PASS / REVISE / BLOCK
  │
  ▼
archive
  │
  ├─ 确认 rook 文档审查已通过
  ├─ 归档 Plan
  ├─ 关闭 Issue
  └─ 推送代码 + 文档变更
```

**关键约束**：
- **Plan 阶段强制**：缺少 Document Update Plan → 无法 approve
- **实施阶段同步**：代码和文档同时更新（同一个 Issue 范围内）
- **complete 前审核**：rook 验证文档是否真的更新了（不看意愿，看结果）

---

### 8.4 rook 分类检查设计

**技能名称**: `df-doc-review`

**触发规则**（按 Plan Type 分类）：

| Plan Type | 变更性质 | 检查文档 | 检查重点 |
|-----------|---------|---------|---------|
| **feat** | 功能新增 | PRD §6.1 / §6.2 | 新功能是否已记录、业务逻辑是否文档化 |
| **enhance** | 功能增强 | PRD §6.1 / §6.2 | 功能描述是否更新、逻辑变更是否同步 |
| **refactor** | 架构重构 | DESIGN | 架构描述是否同步、组件关系是否更新、技术栈是否一致 |
| **perf** | 性能优化 | DESIGN | 优化方案是否记录、设计变更是否同步 |
| fix / chore / test / docs | 无功能/设计变化 | 不触发 | — |

**审查流程**（rook 执行）：

```
Step 1: 提取信息
    ├─ 从 Plan 读取 Document Update Plan
    ├─ 从 Plan 读取 Goal + Key Features
    └─ 从 git diff 提取实际文件变更

Step 2: 定位文档
    ├─ feat/enhance → 读取 PRD §6 功能版图
    └─ refactor/perf → 读取 DESIGN 相关章节

Step 3: 对比分析
    ├─ Plan 声称的文档更新是否真的执行了
    ├─ git diff 中的代码变更是否在文档中有对应描述
    └─ 新增功能/业务逻辑是否已记录

Step 4: 输出审查报告
    ├─ PASS: 文档与代码一致
    ├─ REVISE: 文档需修正（提供具体修改建议）
    └─ BLOCK: 文档缺失或严重不一致
```

**审查报告格式**：

```markdown
# 文档一致性审查报告

## 概要
- 审查类型: Doc Consistency
- Plan Type: feat / enhance / refactor / perf
- 检查文档: PRD §6 / DESIGN
- 判定: PASS | REVISE | BLOCK

## Blocker（必须修正）
### B-01: 功能未记录
- 功能: <功能名称>
- Plan 声明: Document Update Plan 要求更新 PRD §6.1
- 实际: PRD §6.1 中无此功能记录
- 修复: 在 PRD §6.1 中添加：`| <功能> | #<N> | <date> | Active | <描述>`

### B-02: 架构描述与代码不一致
- 位置: DESIGN.md §<X>
- Plan 声明: 重构了 Y 组件
- 实际: DESIGN.md §<X> 仍描述旧架构
- 修复: 更新 §<X> 为新的组件关系和接口定义

## Warning（建议修正）
### W-01: 业务逻辑未文档化
- 代码位置: <file>:<line>
- 业务逻辑: <描述>
- 建议: 在 PRD §6.2 中记录此逻辑

## Positive Findings
- ✅ PRD §6.1 已正确记录新功能 X
- ✅ DESIGN §3 已同步更新为新的接口定义
```

---

### 8.5 Plan check 增强（`check_doc_plan` 新增检查项）

**新增检查**: 如果 Plan Type ∈ {feat, enhance, refactor, perf}，Plan 必须包含 `### Document Update Plan` 章节。

**Plan 模板新增章节**（位于 Implementation 之前）：

```markdown
## Document Update Plan

<!--
  ⚠️ feat/enhance/refactor/perf 类型必填。
  说明本次变更如何影响项目文档，列出需要更新的文档及其变更内容。

  feat/enhance → 检查 PRD §6 功能版图
  refactor/perf → 检查 DESIGN 架构设计

  如果不需要更新文档，填写 "无文档变更" 并说明理由。
-->

| 文档 | 变更类型 | 更新内容 | 负责方 |
|------|---------|---------|--------|
| PRD-ontology.md §6.1 | 新增 | 添加"X 功能"到功能清单 | Wopal |
| DESIGN-ontology.md §3 | 更新 | 补充"Y 组件"的接口定义 | Wopal |
| — | — | 无文档变更（仅为内部重构，不涉及功能变化） | — |
```

**校验逻辑**（`check_doc.py` 新增）：

```python
def _check_doc_update_plan(content: str, plan_type: str) -> list[str]:
    """Check Plan contains Document Update Plan for relevant types."""
    errors = []
    
    doc_types = {'feat', 'enhance', 'perf', 'refactor'}
    if plan_type not in doc_types:
        return errors
    
    # Must have Document Update Plan section
    if '### Document Update Plan' not in content:
        errors.append(
            "MISSING: Document Update Plan (required for feat/enhance/perf/refactor)"
        )
        return errors
    
    # Must reference at least one document or explicitly declare "无文档变更"
    section = _extract_level3_section(content, "### Document Update Plan")
    if not section:
        errors.append("EMPTY: Document Update Plan is empty")
    
    return errors
```

---

### 8.6 实施路径

**阶段 1: 文档简化 + 模板化（低成本）**

- [ ] 简化现有 PRD（ontology: 190 行 → ~120 行）
- [ ] 为 wopal-cli / space-flow / ellamaka / gesp 创建简化 PRD
- [ ] 更新 Plan 模板（`templates/plan.md`）：新增 Document Update Plan 章节

**阶段 2: Plan check 增强（低成本）**

- [ ] `check_doc.py` 新增 `_check_doc_update_plan()` 函数
- [ ] `check_doc_plan()` 中调用（针对 feat/enhance/perf/refactor）
- [ ] 更新 `references/plan-validation.md` 校验规则

**阶段 3: rook 文档审查技能（中成本）**

- [ ] 创建 `df-doc-review` 技能（rook 专属）
- [ ] 实现分类检查逻辑（feat/enhance → PRD §6，refactor/perf → DESIGN）
- [ ] 集成到 dev-flow 流程（complete 前委派 rook）

**阶段 4: 闭环验证（低成本）**

- [ ] 在真实 Issue 中走通完整闭环（Plan → 实施同步更新 → rook 审查 → archive 确认）
- [ ] 收集反馈 → 优化审查规则
- [ ] 建立"文档更新习惯"（每次变更后主动更新）

---

## 九、后续行动

1. 本文档归档后，相关 Issue 可引用本备忘作为背景
2. 实施优化时，按阶段推进，每阶段完成后更新本文档状态
3. 决策待定项需用户确认后才能展开详细设计
4. 文档一致性审查方案需用户确认后才能启动实施
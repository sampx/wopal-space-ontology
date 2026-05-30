# 120-refactor-dev-flow-optimize-new-issue-flow

## Metadata

- **Issue**: #120
- **Type**: refactor
- **Target Project**: ontology
- **Created**: 2026-04-21
- **Status**: done

## Scope Assessment

- **Complexity**: High
- **Confidence**: Medium

## Goal

重构 dev-flow 的 issue 管理对外行为，合并 #113 与 #120 的目标：统一 `issue create/update` 命令面，移除遗留 `new-issue` 入口，补齐 perf 类型与差异化模板，修复 Plan 链接契约，降低创建摩擦，并让后续结构化更新可持续复用。

## Technical Context

### 当前架构

- 当前入口仍是 `flow.sh new-issue`
- 创建调用链：`scripts/cmd/new-issue.sh` → `lib/issue.sh:create_issue()` → `lib/issue.sh:build_structured_issue_body()` → `gh issue create`
- `flow.sh` 还没有 `issue create` / `issue update` 这种统一命令面
- `labels.sh` 中的 label cache / batch sync 已存在，应在新方案中复用，避免回退到高频 `gh issue edit` / `gh label list`
- `plan.sh` 创建 Plan 后仍通过 `update_issue_link` 写入 Plan 链接，但当前创建阶段写的是仓库相对路径，不是稳定的 GitHub blob URL

### 核心问题

| 问题 | 现状 | 影响 |
|---|---|---|
| 命令面过时 | 只有 `new-issue`，没有 `issue create/update` 统一入口 | 语义不清，且遗留入口阻碍统一迁移 |
| 缺少结构化 update | Issue 创建后只能手动 `gh issue edit` 或等待 `sync_plan_to_issue` 覆盖 | 中途修正 Goal / Scope / 模板字段成本高，易漂移 |
| `perf` 类型缺失 | `_extract_type_from_title`、`validate_issue_title`、`normalize_plan_type`、label 路由都未完整支持 `perf` | 性能优化类 issue 无法端到端正确分类 |
| 类型模板未拆分 | `build_structured_issue_body` 仅区分 `fix` / 非 `fix` | `perf/refactor/docs/test` 等结构信息被压平 |
| 模板字段不足 | 当前 CLI 参数无法表达 `baseline`、`target`、`affected-components` 等类型专属字段 | 结构化 issue 仍需大量手写 |
| 创建摩擦过高 | `new-issue` 仍强依赖 `--type`，尽管 title 已编码 type | 轻量创建体验差 |
| 创建路径重复 | `new-issue.sh` 与 `create_issue()` 重复解析结构化参数并重复触发 body 构建 | 新命令面难以收敛到单一路径，维护成本高 |
| 空字段占位垃圾 | `_render_issue_section` 默认输出占位内容 | Issue body 噪音高、可读性差 |
| 错误被吞掉 | `new-issue.sh` 调用 `create_issue` 时仍有 `2>/dev/null` | 创建失败时诊断困难 |
| scope 规则不清晰 | Agent 未被明确要求先读项目规范文档确定 scope | 易写出项目关联不清的标题 |
| Plan 链接契约错误 | `plan.sh` 创建阶段写入相对路径，`plan-sync.sh` archive 后再改 GitHub URL | 同一资源有两套链接格式，Issue 中链接不稳定 |

### 合并约束

- #113 没有对应的 Plan 文件留存，本次以 **#113 issue body** 作为范围合并来源
- #120 继续作为唯一承接 issue，#113 关闭并指向 #120
- #121 仍只负责 `issue/pr` 职责拆分、路径解析收敛与 sourced 库副作用清理，不承接本次对外行为设计

### 源码路径

所有修改在 `projects/ontology/agents/wopal/skills/dev-flow/`。

## In Scope

- 引入统一命令面：`flow.sh issue create` / `flow.sh issue update`
- 移除遗留 `new-issue` 命令入口，不再保留兼容 alias
- create 路径收敛为单一路径，不再保留并行旧入口
- 创建 issue 时允许从 title 推断 type，`--type` 由必填降为可选
- 新增 `perf` canonical type 与独立 `type/perf` label
- 拆分 issue 类型模板：`perf/refactor/docs/test` 独立模板；`feature/enhance/chore` 复用通用模板；`fix` 保留专用模板
- 为类型模板补齐结构化字段参数（如 `baseline`、`target`、`affected-components`、`refactor-strategy`、`target-documents`、`audience`、`test-scope`、`test-strategy` 及 fix 审计字段）
- 将模板路由同时接入 create 与 update 两条路径
- 空字段 section 默认不输出，仅保留必要的 Goal 占位
- 在 SKILL.md 中明确：创建 / 更新 issue 前先读对应项目 `AGENTS.md`，由项目规范决定合法 scope
- 移除 issue 创建吞错行为，保留真实错误输出
- 修复 `flow.sh plan` 创建 Plan 时的链接写法：直接写 GitHub blob URL，而不是仓库相对路径
- 统一 `update_issue_link` / `update_issue_plan_link` 的 Plan 链接契约，避免创建时和归档后的两套格式漂移
- 结构化 update 时保留未触及的 `Related Resources` 行，避免覆盖已有关联

## Out of Scope

- `issue.sh` / `pr.sh` 的内部文件拆分与深度清理（移交 Issue #121）
- 公共路径解析与 sourced 库副作用清理（移交 Issue #121）
- 其他生命周期命令（`approve` / `complete` / `verify` / `archive`）的非必要体验优化
- 交互式表单填写模式
- GitHub Issue Forms / YAML 表单方案
- `sync_plan_to_issue` 的整体重写；本次仅做与模板 / 链接契约直接相关的兼容调整

## Affected Files

| Component | Files | Operation | Role |
|---|---|---|---|
| 命令分发 | `scripts/flow.sh` | 修改 | 增加 `issue` 命令入口并移除遗留 `new-issue` 入口 |
| Issue 命令 | `scripts/cmd/new-issue.sh`, `scripts/cmd/issue.sh`, `scripts/cmd/utility.sh` | 修改 / 新建 / 删除 | 承载 create/update 子命令与帮助输出，并清理旧入口 |
| 类型系统 | `lib/labels.sh` | 修改 | 添加 `perf` 类型与标签映射，保持现有 cache/batch 机制 |
| Issue body 构建 | `lib/issue.sh` | 修改 | 模板路由、结构化字段、update 合并、错误透出、链接更新契约 |
| Plan 同步 | `scripts/cmd/plan.sh`, `lib/plan-sync.sh` | 修改 | 创建 / archive 阶段使用统一 Plan URL 契约 |
| 技能文档 | `SKILL.md` | 修改 | 声明 scope 规则与新命令面 |
| 模板 | `templates/issue.md`, `templates/issue-fix.md`, `templates/issue-perf.md`, `templates/issue-refactor.md`, `templates/issue-docs.md`, `templates/issue-test.md` | 修改 / 新建 | 定义通用与专用模板结构 |

## Implementation

### Task 1: 统一 issue 命令面并移除旧创建入口

**Files**: `scripts/flow.sh`, `scripts/cmd/new-issue.sh`, `scripts/cmd/issue.sh`, `scripts/cmd/utility.sh`, `lib/issue.sh`, `SKILL.md`
 
**Changes**:
- [x] Step 1: 在 `flow.sh` 中新增 `issue` 命令入口，支持 `issue create` / `issue update`
- [x] Step 2: 新建 `scripts/cmd/issue.sh`（或等价实现）承载 issue 子命令分发
- [x] Step 3: 移除 `new-issue` 命令分支，不再暴露兼容 alias
- [x] Step 4: 删除 `scripts/cmd/new-issue.sh`，或将其残留逻辑完全并入 `issue create` 路径
- [x] Step 5: `create_issue()` 成为唯一结构化 body 构建入口，避免 create 链路双份逻辑
- [x] Step 6: 更新 `utility.sh` 帮助输出与 `SKILL.md` 使用说明，只保留新命令面
- [x] Step 7: 明确 create / update 的必填与可选参数边界，避免继续沿用旧入口的歧义行为

**Verification**:
- [x] Step 1: `bash -n scripts/flow.sh scripts/cmd/issue.sh scripts/cmd/utility.sh lib/issue.sh`
- [x] Step 2: `flow.sh help` 中出现 `issue create` / `issue update`
- [x] Step 3: `flow.sh help` 中不再出现 `new-issue`
- [x] Step 4: 仓库内不再存在可执行的 `new-issue` 创建路径

### Task 2: 补齐 perf 类型并降低创建摩擦

**Files**: `scripts/flow.sh`, `lib/labels.sh`, `lib/issue.sh`, `scripts/cmd/issue.sh`

**Changes**:
- [x] Step 1: `_extract_type_from_title`、`validate_issue_title`、`normalize_plan_type` 全面支持 `perf`
- [x] Step 2: `get_type_label_names`、`_get_label_props`、`plan_type_to_issue_label`、`issue_label_to_plan_type`、`sync_type_label_group` 补齐 `type/perf`
- [x] Step 3: `issue create` 允许在 `--type` 缺失时从 title 推断 type
- [x] Step 4: 当 title 与显式 `--type` 冲突时给出清晰错误，避免 silent mismatch
- [x] Step 5: 保持现有 label cache / batch sync 路径，不回退到逐 label 单独调用的实现

**Verification**:
- [x] Step 1: `bash -n scripts/flow.sh lib/labels.sh lib/issue.sh scripts/cmd/issue.sh`
- [x] Step 2: 验证 `normalize_plan_type perf` 返回 `perf`
- [x] Step 3: 验证 `plan_type_to_issue_label perf` 返回 `type/perf`
- [x] Step 4: 用 `perf(dev-flow): ...` title 且不传 `--type` 创建 issue，确认类型被正确推断

### Task 3: 建立类型模板与字段契约

**Files**: `templates/issue.md`, `templates/issue-fix.md`, `templates/issue-perf.md`, `templates/issue-refactor.md`, `templates/issue-docs.md`, `templates/issue-test.md`, `lib/issue.sh`

**模板策略**:
- `feature` / `enhance` / `chore` → 复用 `templates/issue.md`
- `fix` → 使用 `templates/issue-fix.md`
- `perf` → 使用 `templates/issue-perf.md`
- `refactor` → 使用 `templates/issue-refactor.md`
- `docs` → 使用 `templates/issue-docs.md`
- `test` → 使用 `templates/issue-test.md`

**Changes**:
- [x] Step 1: 新增 `templates/issue-perf.md`，包含 `Baseline` / `Target`
- [x] Step 2: 新增 `templates/issue-refactor.md`，包含 `Affected Components` / `Refactor Strategy`
- [x] Step 3: 新增 `templates/issue-docs.md`，包含 `Target Documents` / `Audience`
- [x] Step 4: 新增 `templates/issue-test.md`，包含 `Test Scope` / `Test Strategy`
- [x] Step 5: 为 create / update 补齐模板专属字段参数，并统一写入渲染层
- [x] Step 6: 调整 `_render_issue_section` 或等价逻辑：空内容 section 默认不输出；`Goal` 作为 required section 保留占位提示
- [x] Step 7: 保持 `Acceptance Criteria` 与 `Related Resources` 的统一输出契约

**Verification**:
- [x] Step 1: 4 个新模板文件存在
- [x] Step 2: 每个模板包含其专属章节
- [x] Step 3: 分别生成 `perf/refactor/docs/test` 示例 body，确认使用正确模板
- [x] Step 4: 创建不带 background / optional fields 的 body，确认不会输出空 section 垃圾

### Task 4: 增加结构化 issue update 能力

**Files**: `scripts/cmd/issue.sh`, `lib/issue.sh`, `lib/labels.sh`

**Changes**:
- [x] Step 1: 增加 `issue update <issue>` 命令，支持按字段更新结构化 issue 内容
- [x] Step 2: 读取当前 issue body，解析现有 section / table，形成可覆盖的数据模型
- [x] Step 3: 仅用传入字段覆盖目标 section，未触及 section 与 `Related Resources` 行保持原值
- [x] Step 4: 当 update 修改 title / type / project 时，同步刷新对应 labels
- [x] Step 5: update 路径复用与 create 相同的模板契约，避免两套渲染逻辑漂移

**Verification**:
- [x] Step 1: `bash -n scripts/cmd/issue.sh lib/issue.sh lib/labels.sh`
- [x] Step 2: 只更新 Goal，确认其他 section 保持不变
- [x] Step 3: 更新 `perf` 类型 issue 的专属字段，确认模板与 label 一起正确变化
- [x] Step 4: 现有 `Related Resources` 行在 update 后仍被保留

### Task 5: 修复 scope 规则、Plan 链接契约与错误透出

**Files**: `SKILL.md`, `scripts/cmd/plan.sh`, `lib/issue.sh`, `lib/plan-sync.sh`

**Changes**:
- [x] Step 1: 在 `SKILL.md` 中明确：创建 / 更新 issue 前先读目标项目 `AGENTS.md`，合法 scope 由项目规范决定；无法确定模块名时退回项目名
- [x] Step 2: 确保创建路径不吞掉 `create_issue` 错误，失败时输出真实错误上下文
- [x] Step 3: `scripts/cmd/plan.sh` 创建 Plan 后直接写入 GitHub blob URL 形式的 Plan 链接
- [x] Step 4: 提炼或复用统一的 Plan URL 构造逻辑，确保创建阶段与 archive 更新阶段使用同一契约
- [x] Step 5: `update_issue_link` 以当前英文 `## Related Resources` / `| Plan | ... |` 结构为主路径，减少历史中文 fallback 的主导地位

**Verification**:
- [x] Step 1: `bash -n scripts/cmd/plan.sh lib/issue.sh lib/plan-sync.sh`
- [x] Step 2: 用非法 title 触发失败，确认能看到具体报错
- [x] Step 3: 新建测试 issue 并执行 `flow.sh plan <issue>`，确认 Issue 中的 Plan 链接为可点击 GitHub blob URL
- [x] Step 4: 模拟 archive 后，确认 Plan 链接仍被正确更新到 archived 文件 URL

## Delegation Strategy

遵循 `fae-collab` 协议：先由 Wopal 冻结命令 / 模板 / 链接契约，再把集中实现型任务交给 fae，最后由 Wopal 自己做回读与行为验证。

| 批次 | Task | 执行者 | 依赖 |
|---|---|---|---|
| 1 | Task 1（命令面设计） | Wopal | 无 |
| 1 | Task 2（perf 类型与推断规则） | Wopal | 无 |
| 2 | Task 3（模板与字段契约） | Wopal | Task 2 |
| 3 | Task 4（issue update 实现） | fae | Task 1, 2, 3 |
| 3 | Task 5（scope / Plan link / 错误透出） | Wopal | 无 |

说明：
- Task 1/2/3/5 都属于规则、命令协议与对外行为定义，Wopal 自己做更稳
- Task 4 改动集中在解析 / 合并 / 复用渲染逻辑，机械实现较多，适合在 `fae-collab` 约束下委派给 fae
- 若委派 fae，prompt 必须显式写明：**禁止修改 Plan Status，仅修改源码层文件**

## Verification Discipline

| 轮次 | 时机 | 检查项 | 验证者 |
|---|---|---|---|
| Round 1 | Task 1 / 2 完成后 | 命令分发可用、`perf` 类型与 label 路由成立、旧入口已移除 | Wopal |
| Round 2 | Task 3 完成后 | 模板专属章节正确、空 section 被抑制、create 路径输出符合契约 | Wopal |
| Round 3 | Task 4 完成后 | update 只覆盖目标字段、未触及 section / `Related Resources` 保留、label 同步正确 | Wopal（fae 自测后，Wopal 复验） |
| Round 4 | Task 5 完成后 | scope 规则文档正确、报错可见、Plan 链接创建 / archive 契约一致 | Wopal |

规则：
- 每轮验证通过后再勾选对应 Task / AC，不允许积压到最后统一补勾
- fae 的结果只算候选实现，不算最终通过；最终结论必须由 Wopal 复验给出
- 用户验证只覆盖可感知行为，不替代 Agent Verification

## Test Plan

##### Case U1: create 自动推断 type
- Goal: 不传 `--type` 时，create 能从 title 推断 issue 类型
- Fixture: dev-flow 源码环境
- Execution:
  - [x] Step 1: 使用 `perf(dev-flow): ...` title 且只传 `--project` 创建 issue
  - [x] Step 2: 检查 issue title、body 与 labels
- Expected Evidence: issue 使用 perf 模板，label 为 `type/perf`

##### Case U2: 旧入口已移除
- Goal: 遗留 `new-issue` 不再作为受支持命令存在
- Fixture: dev-flow 源码环境
- Execution:
  - [x] Step 1: 检查 `flow.sh help` 输出与命令分发
  - [x] Step 2: 确认仓库中不存在仍暴露给用户的 `new-issue` 创建入口
- Expected Evidence: 用户侧只暴露 `issue create` / `issue update`，不存在兼容 alias

##### Case I1: 类型模板路由
- Goal: 不同类型生成不同 body 结构
- Fixture: dev-flow 源码环境
- Execution:
  - [x] Step 1: 分别生成 perf、refactor、docs、test 类型 body
  - [x] Step 2: 对比结构差异
- Expected Evidence: perf 有 `Baseline/Target`，refactor 有 `Affected Components/Refactor Strategy`，docs 有 `Target Documents/Audience`，test 有 `Test Scope/Test Strategy`

##### Case I2: issue update 精准覆盖
- Goal: update 只修改目标字段，不覆盖无关 section
- Fixture: 已创建的结构化测试 issue
- Execution:
  - [x] Step 1: 仅更新 Goal / In Scope
  - [x] Step 2: 检查 Background、Out of Scope、Related Resources
- Expected Evidence: 仅目标 section 变化，其余内容保持原值

##### Case I3: 空字段折叠
- Goal: 空字段不再输出垃圾占位 section
- Fixture: dev-flow 源码环境
- Execution:
  - [x] Step 1: 创建不带 background / optional fields 的 body
  - [x] Step 2: 检查生成结果
- Expected Evidence: `Goal` 保留，占空 section 不出现

##### Case I4: Plan 链接创建即正确
- Goal: `flow.sh plan` 创建 plan 后，Issue 中的 Plan 链接立即可点击
- Fixture: dev-flow 源码环境
- Execution:
  - [x] Step 1: 创建测试 issue 并执行 `flow.sh plan <issue>`
  - [x] Step 2: 打开 Issue body 中的 Plan 链接
- Expected Evidence: 链接是 GitHub blob URL，直接打开对应 plan 文件

##### Case R1: Plan 链接归档后仍正确
- Goal: archive 后的 Plan 链接仍能正确指向 done 目录文件
- Fixture: 已创建并可归档的测试 plan
- Execution:
  - [x] Step 1: 执行 archive 流程触发 `update_issue_plan_link`
  - [x] Step 2: 检查 Issue body 中的 Plan 链接
- Expected Evidence: 链接更新为 archived plan 的 GitHub blob URL

##### Case R2: 创建失败时错误可见
- Goal: 创建失败时能看到真实错误
- Fixture: dev-flow 源码环境
- Execution:
  - [x] Step 1: 用非法 title 调用 `flow.sh issue create`
  - [x] Step 2: 观察 stderr
- Expected Evidence: 有具体错误文本，不再静默失败

## Acceptance Criteria

### Agent Verification

- [x] `flow.sh` 已支持 `issue create` / `issue update`
- [x] `new-issue` 已不再作为兼容 alias 对外暴露
- [x] `create_issue()` 已成为唯一结构化 body 构建入口
- [x] `perf` 类型已被 `_extract_type_from_title`、标题校验、type 归一化、label 路由完整支持
- [x] `type/perf` 已加入类型标签集合
- [x] create 在 `--type` 缺失时可从 title 推断类型
- [x] `templates/issue-perf.md`, `templates/issue-refactor.md`, `templates/issue-docs.md`, `templates/issue-test.md` 存在
- [x] create / update 都会路由到正确模板
- [x] 空字段不再输出无意义 section
- [x] `issue update` 可只修改目标字段并保留未触及的 `Related Resources` 行
- [x] `flow.sh plan` 创建时写入的 Plan 链接为 GitHub blob URL
- [x] archive 后的 Plan 链接仍保持同一 URL 契约
- [x] SKILL.md 已明确要求先读项目 `AGENTS.md` 确定 scope

### User Validation

#### Scenario 1: 快速创建 perf issue
- Goal: 用户能用更轻量的命令创建 perf issue
- Precondition: 无
- User Actions:
  1. 用 `perf(dev-flow): ...` title 创建一个 issue，只传必要参数
  2. 查看 issue 的 labels 与 body
- Expected Result: issue 使用 perf 模板，且自动带上 `type/perf`

#### Scenario 2: 结构化更新 issue
- Goal: 用户能只改目标字段，而不是整段重写 body
- Precondition: 已存在一个结构化 issue
- User Actions:
  1. 使用 `flow.sh issue update <issue>` 只修改 Goal 或 In Scope
  2. 检查其他 section 和 Related Resources
- Expected Result: 仅目标 section 被更新，其他内容保持原样

#### Scenario 3: Plan 链接可点击
- Goal: 创建 plan 后，Issue 中的 Plan 链接可直接打开
- Precondition: 无
- User Actions:
  1. 创建一个 issue 并执行 `flow.sh plan <issue>`
  2. 点击 Issue body 中的 Plan 链接
- Expected Result: 直接打开 GitHub 上对应的 plan 文件，而不是无效相对路径

#### Scenario 4: 错误信息清晰可见
- Goal: 非法输入时用户能直接看到失败原因
- Precondition: 无
- User Actions:
  1. 使用非法 title 调用 `flow.sh issue create`
  2. 观察命令输出
- Expected Result: 命令输出具体错误原因，而不是静默失败

- [x] 用户已完成上述功能验证并确认结果符合预期

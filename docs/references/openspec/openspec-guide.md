# OpenSpec 操作指南与规范

> 专为 AI Agent 和开发者设计的 OpenSpec 轻量级规范驱动开发（SDD）操作手册。

## 1. 核心概念字典

- **Specs (主规范)**: `openspec/specs/`。系统当前行为的**唯一真实来源 (Single Source of Truth)**。定义外部可观察行为（输入/输出/错误），不涉及内部实现。
- **config.yaml**: `openspec/config.yaml`。项目级配置文件，包含三个关键字段：
  - `schema`: 工作流 schema（如 spec-driven）
  - `context`: 项目上下文，**自动注入到所有 artifacts 的指令中**
  - `rules`: 按 artifact ID 分组的规则，**只注入到匹配的 artifact**（如 `rules.specs` 注入到所有规格生成指令）
- **Changes (变更)**: `openspec/changes/<name>/`。工作单元容器，包含完成该变更所需的所有产物。
- **Artifacts (产物)**: 
  - `proposal.md`: 变更提案（Why & What）
  - `specs/`: Delta 规范（精确的增量需求）
  - `design.md`: 技术设计（How）
  - `tasks.md`: 实施步骤清单
- **Delta Specs (增量规范)**: 描述**"改变了什么"**（ADDED, MODIFIED, REMOVED, RENAMED），而非重述整个规范。**在归档之前，必须使用 `/opsx:sync` 将其合并到主规范中。**
- **Archive (归档)**: `openspec/changes/archive/YYYY-MM-DD-<name>/`。已完成的变更历史。

## 2. 核心工作流命令

| 命令 | 用途 | 何时使用 | 
|------|------|---------|
| `/opsx:explore` | 探索思考 | 需求不明确，实施前需要理清思路，或实施中途遇到严重阻碍时。 | 
| `/opsx:propose` | 快速提案 | 需求明确，一步生成 proposal, specs, design, tasks 所有产物。 | 
| `/opsx:apply` | 实施任务 | 按 `tasks.md` 执行代码修改。遵循最小修改原则。 | 
| `/opsx:verify` | 验证实施 | **[必做]** 归档前验证代码完整性、正确性，及跨规格一致性。 | 
| `/opsx:sync` | 同步规范 | **[必做]** 将 Delta Specs 智能合并到主规范中。 | 
| `/opsx:archive` | 归档变更 | 变更全部完成并 verify/sync 通过后，移入归档区。 | 
| `/opsx:bulk-archive`| 批量归档 | 多个并行变更同时完成时使用，自动处理规格合并冲突。 |
| `/opsx:new` | 新建变更 | 仅创建目录，适合需要一步一步思考的大型复杂功能。 |
| `/opsx:continue` | 继续工作 | 结合 `/opsx:new` 使用，按依赖顺序一次只生成一个产物。 |

## 3. wopal-workspace 集成规范

### 与 Git Submodule 工作流集成
1. 进入子项目 (`cd projects/xxx`)
2. 创建变更 (`/opsx:propose add-xxx`)
3. 实施变更 (`/opsx:apply`)
4. **子项目内提交** (`git commit`)
5. 归档变更 (`/opsx:archive`)
6. 回到主仓库更新指针 (`/pin-submodule`)

### 与 Worktree 集成 (并行开发)
**重要原则**：`openspec` 目录**必须**存放在各个子项目的根目录下（如 `projects/ontology/openspec/`），绝不能放在工作空间根目录。只有这样，创建 Worktree 时 OpenSpec 数据才能与代码一起被正确隔离和拷贝。

1. **创建工作树**（使用技能）：`/skill git-worktrees create ontology feature/xxx`
2. **进入工作树**：`cd .worktrees/ontology-feature-xxx`
3. 使用 OpenSpec 完成开发闭环 (`/opsx:propose` -> `/opsx:apply` -> `/opsx:archive`)
4. 提交代码并合并回主分支。
5. **清理工作树**：`/skill git-worktrees remove ontology feature/xxx`

## 4. 最佳实践与绝对红线

### 4.1 统一的命名规范
- **规格目录名必须包含层级前缀**: `<产品>-<功能域>-<具体能力>`
  - 正确: `wopal-cli-skills-download`, `wopal-cli-skills-scan`
  - 错误: `bugfix`, `feature-123`, `download`

### 4.2 应对跨规格一致性 (Cross-Spec Consistency)
1. **单一真相来源 (Single Source of Truth)**：对于通用错误处理、接口定义等共享概念，**必须**在一个主流规格文档中集中定义，其他文档只能通过引用调用。禁止重复造轮子。
2. **全局规范注入 (Global Rules Injection)**：对于跨所有实现的全局性系统行为规范（如 CLI UX 规范、语言统一要求、错误码标准等），**必须**定义在 `config.yaml` 的 `rules.design` 字段中，而非创建独立的规格文档。这些规则会在设计阶段自动注入，生成包含全局规范的设计文档。由于 tasks 生成和 apply 阶段都会读取 design.md，因此无需在 rules.tasks 中重复注入，避免冗余。
3. **写前必读**：创建新 Spec 前，AI Agent 必须先阅读 `openspec/specs/` 下已有的相关文档，确保新加入的行为规范（提示语、退出码、重试逻辑）不与现有体系冲突。

### 4.3 处理实现偏离 (SDD 落地红线)
在严格的规范驱动开发 (SDD) 中，如果边写代码边发现原定规范（Spec）不合理，应遵循以下**“偏离处理三原则”**：
1. **发现规格有缺陷（遗漏、错误）** → **暂停实现** → 更新 delta spec/tasks，确认无误后再继续写代码。
2. **发现了明显更优的设计方案** → **暂停实现** → 明确记录偏离原因并更新 design/spec。对于重大改变需向人类报告，确认后再改代码。
3. **仅仅是代码未按规范落实** → **必须改回代码**，绝不允许图省事保留不合规的代码。
  - 🚫 **绝对红线**：绝不允许一边偷偷写代码，一边偷偷修改原定规格，且不留下任何解释。**“代码正确但设计文档却已过时”是严重违规状态**。

### 4.4 归档标准链路
代码开发 (`apply`) 完成后，严禁直接跳到归档 (`archive`)，必须执行防御链路：
1. **Verify (`/opsx:verify`)**: 检查代码是否偏离，检查新规格是否与老规格冲突。
2. **Sync (`/opsx:sync`)**: 将确认无误的新规格合入主规格库。
3. **Archive (`/opsx:archive`)**: 确认无误后封存变更历史。

---

## 更新日志

- **2026-03-09**: 添加 `config.yaml` 的 `rules` 机制说明，强调全局规范应使用 `rules.specs` 注入而非独立规格文档。
- **2026-03-07**: 极限精简文档，移除繁杂的输出示例与教程，仅保留对开发和 Agent 具有指导意义的"核心字典"、"操作速查表"以及"SDD防线与集成规范"。
- **2026-03-03**: 初始版本，基于 OpenSpec 最新文档整理。

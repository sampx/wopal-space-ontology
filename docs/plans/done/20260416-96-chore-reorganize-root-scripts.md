# 96-chore-reorganize-root-scripts

## Metadata

- **Issue**: #96
- **Type**: chore
- **Target Project**: ontology
- **Created**: 2026-04-16
- **Status**: done

## Scope Assessment

- **Complexity**: Low
- **Confidence**: High

## Goal

将 wopal-plugin 根目录 8 个散落 TypeScript 脚本按功能分类归入 scripts/ 子目录，删除功能重叠和过时脚本，使根目录仅保留 src/、scripts/、配置文件和文档。

## Technical Context

当前 `projects/ontology/plugins/wopal-plugin/` 根目录存在 8 个散落 `.ts` 脚本（共 ~940 行），与 `scripts/` 目录内 5 个脚本职责重叠。根目录应仅保留 `src/` 源码、`scripts/` 工具脚本和配置文件。

**现状清单**：

| 文件 | 行数 | 功能 | 判定 |
|------|------|------|------|
| `check-memories.ts` | 31 | 直接查 LanceDB 打印所有记忆 | 调试 → 保留到 `scripts/debug/` |
| `clean-memories.ts` | 37 | 删除空记录和损坏记录 | 调试 → **删除**（功能被 `manage-memories.ts delete` 覆盖） |
| `test-retrieval.ts` | 67 | 6 个查询测试检索相关性 | 调试 → 保留到 `scripts/debug/` |
| `test-retriever-live.ts` | 25 | 单查询测试 retriever | 调试 → **删除**（功能被 `test-retrieval.ts` 覆盖） |
| `manage-memories.ts` | 201 | CLI：list/search/delete/stats | CLI 工具 → 移到 `scripts/cli/` |
| `import-memory-md.ts` | 380 | 导入 MEMORY.md 到 LanceDB | **删除**（`scripts/import-memory.ts` 15K 行更完整） |
| `migrate-embeddings.ts` | 185 | 切换 embedding 模型 | 迁移 → 归档 `scripts/migrations/archive/` |
| `validate-rules-plugin.ts` | 184 | 验证规则插件功能 | 验证 → 移到 `scripts/validation/` |

**scripts/ 现有文件**：

| 文件 | 判定 |
|------|------|
| `benchmark-retrieval.ts` | 验证 → 移到 `scripts/validation/` |
| `import-memory.ts` | 保留（主力导入工具） |
| `migrate-single-body.ts` | 迁移 → 归档 `scripts/migrations/archive/` |
| `migrate-tags.ts` | 迁移 → 归档 `scripts/migrations/archive/` |
| `test-distill-prompt.ts` | 保留（蒸馏测试） |

**风险评估**：低风险。纯文件移动和删除，不涉及 `src/` 源码逻辑，`bun run build` 仅编译 `src/` 下的 TS 代码（根目录和 scripts/ 不参与编译），不影响插件运行时行为。

## In Scope

- 创建 scripts/ 子目录结构（cli/, debug/, validation/, migrations/archive/）
- CLI 工具移动到 `scripts/cli/`
- 调试脚本移动到 `scripts/debug/`（保留有价值的）
- 删除功能重叠脚本（clean-memories.ts, import-memory-md.ts, test-retriever-live.ts）
- 验证脚本归到 `scripts/validation/`
- 迁移脚本归到 `scripts/migrations/archive/`
- 更新 wopal-plugin AGENTS.md 文档结构图

## Out of Scope

- src/ 源码目录重构（#87 子 Issue 已处理）
- 新功能开发
- 测试框架切换
- 迁移脚本的功能验证（归档即可，不保证能运行）

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| CLI 工具 | `manage-memories.ts` | 移动 → `scripts/cli/` | 记忆管理 CLI |
| 调试脚本 | `check-memories.ts`, `test-retrieval.ts` | 移动 → `scripts/debug/` | 调试工具 |
| 待删脚本 | `clean-memories.ts`, `import-memory-md.ts`, `test-retriever-live.ts` | 删除 | 功能重叠 |
| 验证脚本 | `validate-rules-plugin.ts`, `scripts/benchmark-retrieval.ts` | 移动 → `scripts/validation/` | 功能验证 |
| 迁移脚本 | `migrate-embeddings.ts`, `scripts/migrate-single-body.ts`, `scripts/migrate-tags.ts` | 移动 → `scripts/migrations/archive/` | 已完成迁移 |
| 文档 | `plugins/wopal-plugin/AGENTS.md` | 修改 | 更新目录结构描述 |

## Implementation

### Task 1: 创建 scripts/ 子目录结构

**Files**: `scripts/`

**Changes**:
- [x] Step 1: 创建 `scripts/cli/`
- [x] Step 2: 创建 `scripts/debug/`
- [x] Step 3: 创建 `scripts/validation/`
- [x] Step 4: 创建 `scripts/migrations/archive/`

**Verification**: `ls -d scripts/cli scripts/debug scripts/validation scripts/migrations/archive` 四个目录均存在

- [x] Step 1: 创建四个子目录
- [x] Step 2: `ls -d` 确认四个目录存在

### Task 2: 移动 CLI 工具

**Files**: `manage-memories.ts` → `scripts/cli/manage-memories.ts`

**Changes**:
- [x] Step 1: `git mv manage-memories.ts scripts/cli/manage-memories.ts`

**Verification**: `bun scripts/cli/manage-memories.ts list` 返回记忆列表

- [x] Step 1: git mv 移动文件
- [x] Step 2: `bun scripts/cli/manage-memories.ts list` 运行成功

### Task 3: 移动调试脚本

**Files**: `check-memories.ts`, `test-retrieval.ts` → `scripts/debug/`

**Changes**:
- [x] Step 1: `git mv check-memories.ts scripts/debug/check-memories.ts`
- [x] Step 2: `git mv test-retrieval.ts scripts/debug/test-retrieval.ts`

**Verification**: `ls scripts/debug/` 包含两个文件

- [x] Step 1: git mv 移动两个调试脚本
- [x] Step 2: 确认 `scripts/debug/` 包含两个文件

### Task 4: 删除功能重叠脚本

**Files**: `clean-memories.ts`, `import-memory-md.ts`, `test-retriever-live.ts`

**Changes**:
- [x] Step 1: `trash clean-memories.ts`（功能已被 `manage-memories.ts delete` 覆盖）
- [x] Step 2: `trash import-memory-md.ts`（`scripts/import-memory.ts` 功能更完整）
- [x] Step 3: `trash test-retriever-live.ts`（功能被 `scripts/debug/test-retrieval.ts` 覆盖）

**Verification**: 根目录不再有这三个 `.ts` 文件

- [x] Step 1: 删除三个重叠脚本
- [x] Step 2: `ls *.ts` 确认根目录无残留散落脚本

### Task 5: 归档验证脚本

**Files**: `validate-rules-plugin.ts`, `scripts/benchmark-retrieval.ts` → `scripts/validation/`

**Changes**:
- [x] Step 1: `git mv validate-rules-plugin.ts scripts/validation/validate-rules-plugin.ts`
- [x] Step 2: `git mv scripts/benchmark-retrieval.ts scripts/validation/benchmark-retrieval.ts`

**Verification**: `ls scripts/validation/` 包含两个文件

- [x] Step 1: git mv 移动两个验证脚本
- [x] Step 2: 确认 `scripts/validation/` 包含两个文件

### Task 6: 归档迁移脚本

**Files**: `migrate-embeddings.ts`, `scripts/migrate-single-body.ts`, `scripts/migrate-tags.ts` → `scripts/migrations/archive/`

**Changes**:
- [x] Step 1: `git mv migrate-embeddings.ts scripts/migrations/archive/migrate-embeddings.ts`
- [x] Step 2: `git mv scripts/migrate-single-body.ts scripts/migrations/archive/migrate-single-body.ts`
- [x] Step 3: `git mv scripts/migrate-tags.ts scripts/migrations/archive/migrate-tags.ts`

**Verification**: `ls scripts/migrations/archive/` 包含三个文件

- [x] Step 1: git mv 移动三个迁移脚本
- [x] Step 2: 确认 `scripts/migrations/archive/` 包含三个文件

### Task 7: 更新 AGENTS.md

**Files**: `projects/ontology/plugins/wopal-plugin/AGENTS.md`

**Changes**:
- [x] Step 1: 更新「当前结构」中的根目录描述，移除散落脚本条目
- [x] Step 2: 添加 `scripts/` 子目录结构说明（cli/, debug/, validation/, migrations/archive/）

**Verification**: AGENTS.md 根目录部分不再引用散落脚本，scripts/ 子目录结构清晰

- [x] Step 1: 更新 AGENTS.md
- [x] Step 2: 验证文档结构描述正确

## Delegation Strategy

N/A — 纯文件移动/删除和文档更新，7 个 Task 均为简单操作，Wopal 直接执行。

## Test Plan

#### Unit Tests

N/A — 纯文件移动和删除，不涉及 src/ 逻辑变更。

##### Case R1: build 编译通过
- Goal: 确认文件移动后项目仍可编译
- Fixture: wopal-plugin 项目当前状态
- Execution:
  - [x] Step 1: `bun run build`
  - [x] Step 2: 确认 exit code 0 且无错误输出
- Expected Evidence: tsc 编译成功，dist/ 目录更新

##### Case R2: 测试通过
- Goal: 确认文件移动后测试仍通过
- Fixture: wopal-plugin 项目当前状态
- Execution:
  - [x] Step 1: `bun run test:run`
  - [x] Step 2: 确认所有测试通过
- Expected Evidence: vitest 报告所有测试通过

##### Case R3: 根目录整洁
- Goal: 确认根目录仅保留 src/、scripts/、配置文件
- Fixture: wopal-plugin 移动后的目录
- Execution:
  - [x] Step 1: `ls *.ts` 检查根目录
  - [x] Step 2: 确认仅有 `vitest.config.ts`（配置文件）
- Expected Evidence: 根目录无散落工具脚本

### Adjustment Strategy

N/A — 纯文件操作，无复杂阻塞场景。

## Acceptance Criteria

### Agent Verification

- [x] scripts/ 四个子目录创建完成（cli/, debug/, validation/, migrations/archive/）
- [x] manage-memories.ts 移动到 `scripts/cli/`
- [x] check-memories.ts, test-retrieval.ts 移动到 `scripts/debug/`
- [x] clean-memories.ts, import-memory-md.ts, test-retriever-live.ts 已删除
- [x] validate-rules-plugin.ts, benchmark-retrieval.ts 移动到 `scripts/validation/`
- [x] 三个迁移脚本归档到 `scripts/migrations/archive/`
- [x] AGENTS.md 目录结构描述已更新
- [x] `bun run build` 编译通过
- [x] `bun run test:run` 测试通过

### User Validation

#### Scenario 1: 脚本目录结构合理性
- Goal: 确认脚本按功能分类合理，可维护性提升
- Precondition: wopal-plugin 项目已完成所有文件移动
- User Actions:
  1. 查看 `ls -R scripts/` 目录结构
  2. 确认分类逻辑（cli/debug/validation/migrations/archive）清晰
- Expected Result: scripts/ 下每个子目录职责明确，无放错类别的脚本

#### Scenario 2: 无误删有用脚本
- Goal: 确认被删除的 3 个脚本确实无独立价值
- Precondition: 已了解删除原因
- User Actions:
  1. 确认 clean-memories.ts 功能被 manage-memories.ts delete 覆盖
  2. 确认 import-memory-md.ts 功能被 scripts/import-memory.ts 覆盖
  3. 确认 test-retriever-live.ts 功能被 scripts/debug/test-retrieval.ts 覆盖
- Expected Result: 无有价值脚本被误删

- [x] 用户已完成上述功能验证并确认结果符合预期

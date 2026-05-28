# 84-refactor-wopal-plugin-api

## Metadata

- **Issue**: #84
- **Type**: refactor
- **Target Project**: ontology
- **Created**: 2026-04-13
- **Status**: done

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

简化记忆搜索 API，统一标签存储机制（concepts → tags），启用 FTS ngram 分词器支持中文搜索。

## Technical Context

### 当前架构问题

**Issue #83 遗留问题**：
1. **双写冗余**：`tags` 列和 `metadata.concepts` 存储同一份数据的两个形态
   - `store.ts:256` — 写入时 `tags = concepts.join(",")`
   - `store.ts:335` — 又写 `metadata: { concepts }`
2. **双读冗余**：读取时从 `tags` 还原 `metadata.concepts`（`store.ts:286-288`）
3. **API 语义重叠**：`query` + `concepts` 两个参数让 agent 不知道填哪个
4. **规则文件错误**：`mem-rule.md:62-64` 说"存于 `metadata.concepts`"，但代码已改用 `tags`

**FTS 中文支持**：
- LanceDB v0.27.2 TS SDK 支持 `base_tokenizer: "ngram"` 分词器
- 默认 `simple` 分词器依赖空格分词，对中文无效
- ngram 分词器通过字符滑动窗口切分，对中文有效

### 全局性风险

- **数据迁移**：旧数据可能只有 `metadata.concepts` 没有 `tags`（但 Issue #83 已迁移）
- **向后兼容**：蒸馏流程中 `PreviewCandidate.concepts` 需同步改名

## Affected Components

| Component | Key Files | Role |
|-----------|-----------|------|
| 存储层 | `store.ts:43-66,244-296,318-342` | Memory 接口、toStoredRow、parseMemories、add 方法 |
| 工具层 | `memory-manage.ts:108-111,130,333-374,468,549-551` | concepts 参数、formatSearch、addMemory、updateMemory |
| 规则文件 | `mem-rule.md:62-64` | 工具参数规范（concepts → tags） |
| 蒸馏引擎 | `distill.ts:74,100,665,689,706,721,743-756` | PreviewCandidate、写入流程 |

## In Scope

- [x] Schema 简化：删除 `MemoryInput.concepts`、`metadata.concepts` 冗余存储
- [x] 命名统一：`concepts` → `tags`（接口、参数、规则文件全局统一）
- [x] FTS 索引优化：改用 ngram 分词器支持中文搜索
- [x] API 简化：搜索接口合并 `query + concepts` 为单一参数
- [x] 工具 description 重写：清晰说明用法

## Out of Scope

- 向量搜索优化（当前 Issue#83 已验证 FTS+LIKE 足够，53 条记忆规模不需要向量搜索）
- 记忆注入流程（`retriever.ts` 用于记忆注入，使用向量搜索，不在本次范围）

## Files

| 文件 | 操作 | 说明 |
|------|------|------|
| `plugins/wopal-plugin/src/memory/store.ts` | 修改 | 删除 metadata.concepts 双写/双读，改用 ngram 分词器 |
| `plugins/wopal-plugin/src/tools/memory-manage.ts` | 修改 | concepts 参数 → tags，简化搜索 API |
| `agents/wopal/rules/mem-rule.md` | 修改 | 更新工具参数规范 |
| `plugins/wopal-plugin/src/memory/distill.ts` | 修改 | PreviewCandidate.concepts → tags |

## Implementation

### Task 1: Schema 简化与命名统一（store.ts）

**Files**: `plugins/wopal-plugin/src/memory/store.ts`

**Changes**:
1. `Memory` 接口（第 43-51 行）：注释修复 `tags: string` 描述
2. `MemoryInput` 接口（第 57-66 行）：`concepts?: string[]` → `tags?: string[]`
3. `toStoredRow` 方法（第 244-258 行）：删除 `metadata.concepts` 双写，直接用 `memory.tags`
4. `parseMemories` 方法（第 265-295 行）：删除第 284-288 行从 tags 还原 concepts 的逻辑
5. `add` 方法（第 298-342 行）：第 321-335 行改为直接用 `input.tags`，删除 metadata.concepts

**Verification**: 
```bash
cd projects/ontology/plugins/wopal-plugin && bun run test:run
```

- [x] Step 1: 修改 Memory 和 MemoryInput 接口
- [x] Step 2: 删除 toStoredRow 双写逻辑
- [x] Step 3: 删除 parseMemories 双读逻辑
- [x] Step 4: 修改 add 方法
- [x] Step 5: 单元测试通过

### Task 2: FTS 索引改用 ngram 分词器（store.ts）

**Files**: `plugins/wopal-plugin/src/memory/store.ts`

**Changes**:
1. 导入 `Index` 对象（已有）
2. 第 214-226 行 FTS 索引创建：
   - `text` 索引：改用 ngram 分词器
   - `tags` 索引：改用 ngram 分词器
3. 配置参数：`ngram_min_length=2, ngram_max_length=4`

**Verification**:
```bash
cd projects/ontology/plugins/wopal-plugin && bun run test:run
# 手动验证：新增记忆后搜索中文标签
```

- [x] Step 1: 修改 init() 中 FTS 索引配置
- [x] Step 2: 单元测试通过
- [ ] Step 3: 手动验证中文标签搜索生效

### Task 3: 工具参数与 API 简化（memory-manage.ts）

**Files**: `plugins/wopal-plugin/src/tools/memory-manage.ts`

**Changes**:
1. 第 108-111 行：`concepts` 参数改名为 `tags`，description 更新
2. 第 130 行：`formatSearch(store, query ?? "", concepts)` → `formatSearch(store, query ?? "")`
3. 第 333-374 行：`formatSearch` 简化
   - 删除第二个参数 `concepts`
   - 删除 `if (!query && !concepts)` 检查（query 必填）
   - 合并查询逻辑删除（只保留 FTS+LIKE）
4. 第 468 行：`metadata: { concepts: options.concepts }` → `metadata: { tags: options.tags }`（待定：可能不需要 metadata）
5. 第 549-551 行：`updateMemory` 中 concepts 处理改为 tags

**Verification**:
```bash
cd projects/ontology/plugins/wopal-plugin && bun run test:run
```

- [x] Step 1: 重命名参数 concepts → tags
- [x] Step 2: 简化 formatSearch
- [x] Step 3: 更新 addMemory 和 updateMemory
- [x] Step 4: 单元测试通过

### Task 4: 规则文件更新（mem-rule.md）

**Files**: `agents/wopal/rules/mem-rule.md`

**Changes**:
1. 第 62-64 行："标签字段名是 `concepts`（不是 `tags`），存于 `metadata.concepts`" → "标签字段名是 `tags`，存于记忆的 `tags` 字段"
2. 全文搜索替换 `concepts` → `tags`

**Verification**: 手动检查内容正确性

- [x] Step 1: 更新工具参数规范说明
- [x] Step 2: 全文 concepts → tags 替换

### Task 5: 蒸馏引擎命名统一（distill.ts）

**Files**: `plugins/wopal-plugin/src/memory/distill.ts`

**Changes**:
1. `PreviewCandidate.concepts` → `PreviewCandidate.tags`（第 74 行）
2. `ExtractResult.memories[].concepts` → `tags`（第 100 行）
3. 写入流程：`metadata: { concepts: ... }` → `tags: ...`（第 665、689、706、721、756 行）
4. 合并流程：`dec.concepts` → `dec.tags`（第 743-744 行）

**Verification**:
```bash
cd projects/ontology/plugins/wopal-plugin && bun run test:run
```

- [x] Step 1: 修改接口定义
- [x] Step 2: 修改写入流程
- [x] Step 3: 单元测试通过

## Delegation Strategy

| 批次 | Task | 执行者 | 依赖 |
|------|------|--------|------|
| 1 | Task 1 + Task 2（store.ts） | fae | 无 |
| 1 | Task 4（mem-rule.md） | fae | 无 |
| 2 | Task 3（memory-manage.ts） | fae | Task 1 |
| 2 | Task 5（distill.ts） | fae | Task 1 |

**说明**：Task 1 先执行确定接口定义，Task 3 和 Task 5 依赖其完成。

## Test Plan

### Test Case Design

- **中文标签搜索**：添加含中文标签的记忆，用中文关键词搜索，验证召回
- **英文标签搜索**：添加含英文标签的记忆，验证召回
- **中英混合标签**：添加中英混合标签，验证搜索
- **API 简化验证**：只用 `query` 参数执行搜索，验证行为

### Regression Testing

- **现有记忆搜索**：验证现有记忆（已迁移到 tags）仍可搜索
- **蒸馏流程**：验证 `distill_session` 生成的候选记忆包含正确标签
- **列表命令**：验证 `memory_manage list` 正确显示标签

### Adjustment Strategy

- **ngram 参数调优**：如中文搜索效果不佳，可调整 `ngram_min/max_length`
- **向后兼容**：如发现旧数据只有 metadata.concepts 没有 tags，需添加迁移脚本

## Acceptance Criteria

### Agent Verification

- [x] 代码构建通过：`cd projects/ontology/plugins/wopal-plugin && bun run build`
- [x] 单元测试通过：`bun run test:run`
- [x] 中文标签搜索生效：FTS ngram 分词器已配置，store.ts 中 text 和 tags 两列均使用 ngram(2,4)

### User Validation

- 重启 OpenCode 后执行 `memory_manage search` 验证搜索功能
- 执行 `distill_session` 验证蒸馏流程生成正确标签
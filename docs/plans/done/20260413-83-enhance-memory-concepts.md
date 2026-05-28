# 83-enhance-memory-concepts

## Metadata

- **Issue**: #83
- **Type**: enhance
- **Target Project**: ontology
- **Created**: 2026-04-12
- **Status**: done

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

实现记忆搜索按 concepts 标签模糊匹配，通过 Schema 改造将 `metadata.concepts` 提升为独立 `tags` 列并建立 FTS 索引，提升检索召回率。

## Technical Context

### 当前架构

```
Memory {
  id, text, vector, category, project, session_id,
  importance, created_at, updated_at, access_count,
  metadata: { concepts: string[], ... }  // JSON 字符串存储
}
```

**问题**：
1. `concepts` 存储在 `metadata` JSON 字符串中，无法建立 FTS 索引
2. `searchByQuery` 只能对 `text` 列进行 FTS/LIKE 搜索
3. `Retriever.computeConceptBoost` 是后处理匹配，性能低且召回率有限

### 目标架构

```
Memory {
  id, text, vector, category, project, session_id,
  importance, created_at, updated_at, access_count,
  tags: string,  // 扁平化："distill,memory,rule"
  metadata: { ... }  // concepts 迁移后保留其他字段
}
```

**方案**：
- LanceDB TS SDK 支持 `fullTextSearch(query, columns[])` 多列搜索
- FTS 索引仅支持字符串列，需将数组扁平化为逗号分隔字符串
- 新增 `tags` 列存储扁平化的 concepts，建立 FTS 索引
- 搜索时对 `text` + `tags` 多列 FTS

### 风险

- **数据迁移**：需遍历所有现有记忆，从 `metadata.concepts` 提取到 `tags`
- **向后兼容**：旧版 `metadata.concepts` 读取需保留一段时间

## Affected Components

| Component | Key Files | Role |
|-----------|-----------|------|
| MemorySchema | `src/memory/store.ts` | Schema 定义与 LanceDB 表管理 |
| Retriever | `src/memory/retriever.ts` | 搜索逻辑改造 |
| Tool | `src/tools/memory-manage.ts` | 增加 concepts 参数 |
| Migration | `scripts/migrate-tags.ts` | 数据迁移脚本 |

## In Scope

- [ ] Schema 改造：新增 `tags` 列，迁移 `metadata.concepts`
- [ ] FTS 索引：在 `tags` 列建立 FTS 索引
- [ ] `search` 命令：增加 `concepts` 参数，支持多列 FTS
- [ ] 数据迁移：脚本从 `metadata.concepts` → `tags`
- [ ] 向后兼容：保留旧字段读取兼容

## Out of Scope

- `Retriever.retrieve()` 的 `conceptBoost` 权重调整（属于记忆注入场景）
- 精确过滤功能（通过 `where` 条件实现，不在本期范围）

## Files

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/memory/store.ts` | 修改 | Schema 增加 tags 列，init() 建索引 |
| `src/memory/retriever.ts` | 修改 | 暂无改动，保留 conceptBoost 后处理 |
| `src/tools/memory-manage.ts` | 修改 | search 增加 concepts 参数 |
| `src/memory/store.test.ts` | 修改 | 增加测试用例 |
| `scripts/migrate-tags.ts` | 创建 | 数据迁移脚本 |

## Implementation

### Task 1: Schema 改造与 FTS 索引

**Files**: `src/memory/store.ts`

**Changes**:

1. **Memory 接口新增 `tags` 字段**：
   ```typescript
   export interface Memory {
     // ...existing fields
     tags: string;  // 扁平化 concepts: "distill,memory,rule"
   }
   ```

2. **MemoryInput 接口新增可选 `concepts` 参数**：
   ```typescript
   export interface MemoryInput {
     // ...existing fields
     concepts?: string[];  // 传入数组，内部扁平化为 tags
   }
   ```

3. **StoredMemoryRow 新增 `tags` 列**：
   ```typescript
   interface StoredMemoryRow {
     // ...existing fields
     tags: string;  // 替代 metadata 中的 concepts
   }
   ```

4. **init() 创建 FTS 索引**：
   ```typescript
   await this.table.createIndex("text", { config: lancedb.Index.fts() });
   await this.table.createIndex("tags", { config: lancedb.Index.fts() });
   ```

5. **add() 方法改造**：
   - 将 `concepts` 数组扁平化为 `tags` 字符串
   - `metadata` 保留 concepts 用于向后兼容

6. **toStoredRow() 转换**：
   ```typescript
   tags: (memory.metadata?.concepts as string[] || []).join(",")
   ```

7. **parseMemories() 解析**：
   ```typescript
   // 从 tags 反向填充 metadata.concepts（兼容）
   ```

**Verification**:

```bash
cd projects/ontology/plugins/wopal-plugin
bun run test:run src/memory/store.test.ts
```

- [ ] Schema 定义正确，新增 `tags` 字段
- [ ] 初始化时 FTS 索引创建成功
- [ ] add() 正确扁平化 concepts
- [ ] parseMemories() 正确反向填充

### Task 2: searchByQuery 支持多列 FTS

**Files**: `src/memory/store.ts`

**Changes**:

1. **修改 `searchByQuery` 方法签名**：
   ```typescript
   async searchByQuery(
     query: string,
     limit: number = 10,
     queryType: QueryType = "hybrid",
     ftsColumns: string[] = ["text", "tags"]  // 默认多列
   ): Promise<Memory[]>
   ```

2. **FTS 搜索使用多列**：
   ```typescript
   // fts 和 hybrid 模式
   .fullTextSearch(query, { columns: ftsColumns })
   ```

3. **向后兼容**：
   - 旧调用传入 `["text"]` 时仍正常工作
   - 新调用默认 `["text", "tags"]`

**Verification**:

- [ ] FTS 搜索能匹配 `tags` 列内容
- [ ] 多列搜索 `text` + `tags` 正确返回结果

### Task 3: memory_manage search 增加 concepts 参数

**Files**: `src/tools/memory-manage.ts`

**Changes**:

1. **新增 `concepts` 参数**：
   ```typescript
   concepts: tool.schema
     .string()
     .optional()
     .describe("按标签过滤（逗号分隔，如 'distill,memory'）")
   ```

2. **formatSearch 使用 concepts 参数**：
   ```typescript
   async function formatSearch(
     store: MemoryStore,
     query: string,
     concepts?: string  // 新增
   ): Promise<string> {
     // 如果有 concepts，追加到 query 进行 FTS
     const fullQuery = concepts
       ? `${query} ${concepts.replace(/,/g, " ")}`
       : query;
     // 或使用多列直搜
   }
   ```

3. **调用示例**：
   ```typescript
   memory_manage command=search query="OpenCode" concepts="skill,distill"
   ```

**Verification**:

- [ ] `search` 命令接受 `concepts` 参数
- [ ] 搜索结果能匹配 `tags` 列中的词汇

### Task 4: 数据迁移脚本

**Files**: `scripts/migrate-tags.ts`

**Changes**:

创建迁移脚本，将现有 `metadata.concepts` 迁移到 `tags` 列：

```typescript
// scripts/migrate-tags.ts
import { MemoryStore } from "../src/memory/store.js";

async function migrate() {
  const store = new MemoryStore();
  await store.init();
  
  const all = await store.searchByQuery("", 10000, "like", ["text"]);
  
  for (const memory of all) {
    const concepts = memory.metadata?.concepts as string[] | undefined;
    if (concepts && concepts.length > 0) {
      const tags = concepts.join(",");
      await store.update(memory.id, { tags } as any);
      console.log(`Migrated ${memory.id.slice(0, 8)}: ${tags}`);
    }
  }
  
  console.log(`Migrated ${all.length} memories`);
}

migrate();
```

**Verification**:

```bash
cd projects/ontology/plugins/wopal-plugin
bun run scripts/migrate-tags.ts
# 检查迁移结果
bun run -e "import { MemoryStore } from './src/memory/store.js'; const s = new MemoryStore(); await s.init(); const all = await s.searchByQuery('', 10, 'like', ['text']); console.log(all[0]);"
```

- [ ] 迁移脚本正确提取 `metadata.concepts`
- [ ] 所有记忆的 `tags` 列正确填充
- [ ] 迁移后 FTS 搜索正常工作

## Delegation Strategy

N/A — 单一任务链，按顺序执行。

## Test Plan

### Test Case Design

- **Schema 验证**：单元测试验证新增 `tags` 字段读写
- **FTS 多列搜索**：单元测试验证 `searchByQuery` 多列匹配
- **迁移脚本**：手动执行 + 结果验证
- **工具参数**：手动测试 `memory_manage search concepts=...`

### Regression Testing

- 现有 `add/update/delete/list` 命令不受影响
- 现有 `searchByQuery(query, limit, "fts", ["text"])` 向后兼容
- Retriever 的 `conceptBoost` 后处理逻辑保留

### Adjustment Strategy

- 如果 LanceDB TS SDK 的 FTS 多列搜索有问题，降级为单列 + 后处理过滤
- 迁移脚本优先幂等性，可重复执行

## Acceptance Criteria

### Agent Verification

- [x] `bun run test:run` 所有测试通过（396 tests, store.test.ts 单独运行 6/6 通过；全量运行时 debug.js ESM 问题是已有缺陷）
- [x] `bun run build` 编译通过
- [x] 迁移脚本已创建（`scripts/migrate-tags.ts`）
- [x] `memory_manage command=search query="test" concepts="skill"` 返回匹配结果

### User Validation

- 重启 OpenCode 后验证 `memory_manage search` 正常工作
- 验证迁移后旧记忆的 concepts 仍可搜索到
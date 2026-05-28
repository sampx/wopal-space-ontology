# 89-refactor-memory-internal-split

## Metadata

- **Issue**: #89
- **Parent**: #87
- **Type**: refactor
- **Target Project**: ontology
- **Created**: 2026-04-14
- **Status**: done
- **Dependencies**: 无

## Scope Assessment

- **Complexity**: Low
- **Confidence**: High
- **Risk**: 内部拆分，无外部模块依赖

## Goal

将 `memory/distill.ts` (864 行) 和 `memory/store.ts` (508 行) 内部拆分，提取类型、分类、对话处理、prompt 构建为独立模块。职责分离，降低单文件行数。

## Technical Context

### 当前文件结构

```
src/memory/
├── distill.ts (864 lines)
│   ├── CATEGORY_LABELS / TAG_TO_CATEGORY (~40 lines)
│   ├── validateCategory / getDefaultImportance (~60 lines)
│   ├── extractConversationText / filterSystemReminder (~90 lines)
│   ├── resolvePromptFilePath / loadPromptTemplate (~80 lines)
│   ├── buildExtractionPrompt / buildBatchDedupPrompt (~120 lines)
│   └── DistillEngine 类 (~400 lines)
├── store.ts (508 lines)
│   ├── Memory / MemoryInput / MemoryUpdate 等类型 (~100 lines)
│   ├── LanceDB 操作 (~300 lines)
│   └── embedder.ts / injector.ts / retriever.ts 等 (保持不变)
```

### 目标结构

```
src/memory/
├── types.ts              # ← store.ts 提取：Memory/MemoryInput/MemoryCategory/MemoryUpdate/StoredMemoryRow
├── categories.ts         # ← distill.ts 提取：CATEGORY_LABELS/TAG_TO_CATEGORY/validateCategory/getDefaultImportance
├── conversation.ts       # ← distill.ts 提取：extractConversationText/filterSystemReminder/MIN/MAX 常量
├── prompts.ts            # ← distill.ts 提取：resolvePromptFilePath/loadPromptTemplate/buildExtractionPrompt/buildBatchDedupPrompt
├── distill.ts            # 瘦身：仅 DistillEngine 类 (~300 lines)
├── store.ts              # 瘦身：类型移走 (~400 lines)
├── embedder.ts           # 保持
├── injector.ts           # 保持
├── retriever.ts          # 保持
├── llm-client.ts         # 保持
├── session-context.ts    # 保持
├── index.ts              # 更新 re-export
└── store.test.ts         # 更新导入
```

## In Scope

- [ ] 创建 `src/memory/types.ts`（类型提取）
- [ ] 创建 `src/memory/categories.ts`（分类提取）
- [ ] 创建 `src/memory/conversation.ts`（对话提取）
- [ ] 创建 `src/memory/prompts.ts`（prompt 构建）
- [ ] 瘦身 `distill.ts` 和 `store.ts`
- [ ] 更新 `memory/index.ts` 和 `store.test.ts` 导入

## Out of Scope

- memory/ 其他文件（embedder.ts、injector.ts、retriever.ts 等）保持不变
- memory/ 外部调用者（wopal-plugin 入口等）不涉及
- 行为变化（纯结构重构）

## Files

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/memory/types.ts` | 创建 | 类型定义 (~100 lines) |
| `src/memory/categories.ts` | 创建 | 分类常量 + 验证 (~100 lines) |
| `src/memory/conversation.ts` | 创建 | 对话提取 (~90 lines) |
| `src/memory/prompts.ts` | 创建 | prompt 构建 (~200 lines) |
| `src/memory/distill.ts` | 瘦身 | 仅 DistillEngine (~300 lines) |
| `src/memory/store.ts` | 瘦身 | 类型移走 (~400 lines) |
| `src/memory/index.ts` | 修改 | 更新 re-export |
| `src/memory/store.test.ts` | 修改 | 导入路径更新 |

## Implementation

### Task 1: 提取类型到 types.ts
**Files**: `src/memory/types.ts`, `src/memory/store.ts`, `src/memory/distill.ts`
**Changes**: 从 store.ts 提取类型定义到 types.ts，更新导入
- [ ] Step 1: 创建 `memory/types.ts`（Memory、MemoryInput、MemoryUpdate、MemoryCategory、StoredMemoryRow 等）
- [ ] Step 2: 更新 `store.ts`：`import { ... } from "./types.js"`
- [ ] Step 3: 更新 `distill.ts`：类型导入从 `./types.js`
**Verification**: `bun run build` 编译通过

### Task 2: 提取分类到 categories.ts
**Files**: `src/memory/categories.ts`, `src/memory/distill.ts`
**Changes**: 从 distill.ts 提取分类常量和验证函数
- [ ] Step 1: 创建 `memory/categories.ts`（CATEGORY_LABELS、TAG_TO_CATEGORY、validateCategory、getDefaultImportance）
- [ ] Step 2: 更新 `distill.ts`：`import { ... } from "./categories.js"`
**Verification**: `bun run build` 编译通过

### Task 3: 提取对话处理到 conversation.ts
**Files**: `src/memory/conversation.ts`, `src/memory/distill.ts`
**Changes**: 从 distill.ts 提取对话提取函数
- [ ] Step 1: 创建 `memory/conversation.ts`（extractConversationText、filterSystemReminder、MIN_TOKENS、MAX_TOKENS）
- [ ] Step 2: 更新 `distill.ts`：`import { ... } from "./conversation.js"`
**Verification**: `bun run build` 编译通过

### Task 4: 提取 prompt 构建到 prompts.ts
**Files**: `src/memory/prompts.ts`, `src/memory/distill.ts`
**Changes**: 从 distill.ts 提取 prompt 构建函数
- [ ] Step 1: 创建 `memory/prompts.ts`（resolvePromptFilePath、loadPromptTemplate、buildExtractionPrompt、buildBatchDedupPrompt、ExtractResult）
- [ ] Step 2: 更新 `distill.ts`：`import { ... } from "./prompts.js"`
**Verification**: `bun run build` 编译通过

### Task 5: 更新 index.ts 和测试 + 清理
**Files**: `src/memory/index.ts`, `src/memory/store.test.ts`
**Changes**: 更新 re-export 和测试导入
- [ ] Step 1: 更新 `memory/index.ts`：re-export 新模块
- [ ] Step 2: 更新 `memory/store.test.ts`：导入路径
- [ ] Step 3: 运行 `bun run test:run` + `bun run build` + `bun run lint` 验证
**Verification**: `bun run test:run` 全通过

## Verification

- `bun run test:run` 全部通过（memory/store.test.ts）
- `bun run build` 编译通过
- `bun run lint` 无新增 error
- 新建文件 ≤ 200 行
- distill.ts 瘦身后 ≤ 350 行
- store.ts 瘦身后 ≤ 420 行

## Delegation Strategy

| 批次 | Task | 执行者 | 依赖 |
|------|------|--------|------|
| 1 | Task 1-5 | fae | 无 |

## Test Plan

### Test Case Design
- 运行 `bun run test:run` 验证所有 memory 相关测试通过
- 对比重构前后 distill.ts 和 store.ts 行数

### Regression Testing
- 每个 Task 完成后：`bun run build` 编译验证
- 最终：`bun run test:run` + `bun run lint`

### Adjustment Strategy
- 如编译失败，检查类型导入路径
- 如测试失败，检查 re-export 是否完整

## Acceptance Criteria

### Agent Verification
- [x] `src/memory/types.ts` 已创建
- [x] `src/memory/categories.ts` 已创建
- [x] `src/memory/conversation.ts` 已创建
- [x] `src/memory/prompts.ts` 已创建
- [x] `src/memory/distill.ts` ≤ 350 行
- [x] `src/memory/store.ts` ≤ 420 行
- [x] `bun run test:run` 全通过
- [x] `bun run build` 编译通过
- [x] `bun run lint` 无新增 error
# 88-refactor-utils-to-rules

## Metadata

- **Issue**: #88
- **Parent**: #87
- **Type**: refactor
- **Target Project**: ontology
- **Created**: 2026-04-14
- **Status**: done
- **Dependencies**: 无

## Scope Assessment

- **Complexity**: Low
- **Confidence**: High
- **Risk**: 单文件拆分，边界清晰，无跨模块依赖

## Goal

将 `utils.ts` (607 行) 拆分为 `rules/` 子系统目录，职责分离为规则发现、匹配、格式化、路径提取四个模块。同时迁移 index.test.ts 中对应的测试用例。

## Technical Context

### 当前文件结构

```
src/utils.ts (607 lines)
├── extractFilePathsFromMessages + 私有函数 (~120 lines)
├── promptMatchesKeywords (~120 lines)
├── toolsMatchAvailable (~40 lines)
├── parseRuleMetadata + clearRuleCache (~180 lines)
├── discoverRuleFiles + cache (~80 lines)
├── readAndFormatRules (~80 lines)
└── 类型定义 (~80 lines)
```

### 目标结构

```
src/rules/
├── discoverer.ts      # discoverRuleFiles + parseRuleMetadata + clearRuleCache + cache
├── matcher.ts         # promptMatchesKeywords + toolsMatchAvailable + fileMatchesGlobs
├── formatter.ts       # readAndFormatRules
├── path-extractor.ts  # extractFilePathsFromMessages + 私有函数
├── index.ts           # 统一 re-export
└── *.test.ts          # 4 个测试文件（← index.test.ts）
```

### 外部引用关系

| 引用文件 | 当前导入 | 拆分后导入 |
|----------|----------|------------|
| `src/index.ts` | `./utils.js` | `./rules/index.js` |
| `src/runtime.ts` | `./utils.js` (多处) | `./rules/index.js` |
| `src/message-context.ts` | 类型 `from "./utils.js"` | 类型 `from "./utils.js"` → #90 处理 |
| `src/index.test.ts` | `./utils.js` | `./rules/index.js` |

### index.test.ts Describe 块迁移映射

| Describe | 行号范围 | 目标文件 |
|----------|----------|----------|
| extractFilePathsFromMessages | L47-641 | rules/path-extractor.test.ts |
| promptMatchesKeywords | L642-761 | rules/matcher.test.ts |
| toolsMatchAvailable | L762-802 | rules/matcher.test.ts |
| parseRuleMetadata | L803-982 | rules/discoverer.test.ts |
| discoverRuleFiles (含嵌套) | L983-1314 | rules/discoverer.test.ts |
| readAndFormatRules | L1315-1961 | rules/formatter.test.ts |

## In Scope

- [ ] 创建 `src/rules/` 目录，含 5 个源文件
- [ ] 迁移 index.test.ts 中 6 个 describe 块到 rules/ 测试文件
- [ ] 更新 `src/index.ts`、`src/runtime.ts` 导入路径
- [ ] 删除 `src/utils.ts`

## Out of Scope

- message-context.ts 中的类型引用（#90 处理）
- runtime.ts 的其他重构（#90 处理）
- rules/ 内部逻辑修改（纯迁移，零行为变化）

## Files

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/utils.ts` | 删除 | 拆分为 rules/ |
| `src/rules/discoverer.ts` | 创建 | ~180 行 |
| `src/rules/matcher.ts` | 创建 | ~160 行 |
| `src/rules/formatter.ts` | 创建 | ~80 行 |
| `src/rules/path-extractor.ts` | 创建 | ~120 行 |
| `src/rules/index.ts` | 创建 | re-export |
| `src/rules/discoverer.test.ts` | 创建 | ← index.test.ts L803-1314 |
| `src/rules/matcher.test.ts` | 创建 | ← index.test.ts L642-802 |
| `src/rules/formatter.test.ts` | 创建 | ← index.test.ts L1315-1961 |
| `src/rules/path-extractor.test.ts` | 创建 | ← index.test.ts L47-641 |
| `src/index.ts` | 修改 | 导入路径 `./utils.js` → `./rules/index.js` |
| `src/runtime.ts` | 修改 | 导入路径 `./utils.js` → `./rules/index.js` |
| `src/index.test.ts` | 修改 | 删除迁移的 describe 块，导入路径更新 |

## Implementation

### Task 1: 创建 rules/ 目录结构
**Files**: `src/rules/discoverer.ts`, `src/rules/matcher.ts`, `src/rules/formatter.ts`, `src/rules/path-extractor.ts`, `src/rules/index.ts`
**Changes**: 从 `utils.ts` 提取函数到 5 个模块文件
- [ ] Step 1: 创建 `src/rules/discoverer.ts`：discoverRuleFiles、parseRuleMetadata、clearRuleCache、ruleCache、私有辅助
- [ ] Step 2: 创建 `src/rules/matcher.ts`：promptMatchesKeywords、toolsMatchAvailable、fileMatchesGlobs
- [ ] Step 3: 创建 `src/rules/formatter.ts`：readAndFormatRules
- [ ] Step 4: 创建 `src/rules/path-extractor.ts`：extractFilePathsFromMessages + parseFilePath + normalizePath
- [ ] Step 5: 创建 `src/rules/index.ts`：统一 re-export
**Verification**: `bun run build` 编译通过

### Task 2: 迁移测试用例
**Files**: `src/rules/path-extractor.test.ts`, `src/rules/matcher.test.ts`, `src/rules/discoverer.test.ts`, `src/rules/formatter.test.ts`
**Changes**: 从 `index.test.ts` 提取 6 个 describe 块到 4 个测试文件
- [ ] Step 1: 创建 `rules/path-extractor.test.ts` ← index.test.ts L47-641
- [ ] Step 2: 创建 `rules/matcher.test.ts` ← index.test.ts L642-802
- [ ] Step 3: 创建 `rules/discoverer.test.ts` ← index.test.ts L803-1314
- [ ] Step 4: 创建 `rules/formatter.test.ts` ← index.test.ts L1315-1961
- [ ] Step 5: 更新各测试文件导入路径 `from "./utils.js"` → `from "./index.js"`
**Verification**: `bun run test:run` 测试通过（新增 4 个测试文件）

### Task 3: 更新外部引用 + 清理
**Files**: `src/index.ts`, `src/runtime.ts`, `src/index.test.ts`, `src/utils.ts`
**Changes**: 更新导入路径、删除迁移的 describe 块、删除 utils.ts
- [ ] Step 1: `src/index.ts`：`from "./utils.js"` → `from "./rules/index.js"`
- [ ] Step 2: `src/runtime.ts`：所有 `from "./utils.js"` → `from "./rules/index.js"`
- [ ] Step 3: `src/index.test.ts`：删除已迁移的 6 个 describe 块，更新剩余导入
- [ ] Step 4: 删除 `src/utils.ts`
**Verification**: `bun run test:run` + `bun run build` + `bun run lint`

## Delegation Strategy

| Step | 执行者 | 备注 |
|------|--------|------|
| Step 1-4 | fae | 整体委派，Wopal 验证 |

## Test Plan

### Test Case Design
- 迁移前统计 index.test.ts 中 6 个 describe 块的测试用例数
- 迁移后验证 rules/ 下 4 个测试文件用例数一致
- 运行 `bun run test:run --coverage` 验证覆盖率无下降

### Regression Testing
- Task 1 完成后：`bun run build` 编译验证
- Task 2 完成后：`bun run test:run` 测试验证
- Task 3 完成后：`bun run lint` 检查无新增 error

### Adjustment Strategy
- 如测试失败，检查导入路径是否正确
- 如编译失败，检查类型定义是否遗漏 export

## Acceptance Criteria

### Agent Verification
- [x] `src/rules/` 目录已创建，含 5 个源文件（各 ≤ 200 行）
- [x] `src/rules/` 含 4 个测试文件，测试用例数与迁移前一致
- [x] `src/utils.ts` 已删除
- [x] `src/index.ts`、`src/runtime.ts` 导入路径已更新
- [x] `bun run test:run` 全通过
- [x] `bun run build` 编译通过
- [x] `bun run lint` 无新增 error
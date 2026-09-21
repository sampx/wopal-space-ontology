# 90-refactor-wopal-plugin-runtime-ts-hooks

## Metadata

- **Issue**: #90
- **Parent**: #87
- **Type**: refactor
- **Target Project**: ontology
- **Created**: 2026-04-14
- **Status**: done
- **Dependencies**: #88 (rules/ 路径)

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High
- **Risk**: 大文件拆分 + 散件归位，hooks 间有内部依赖

## Goal

将 `runtime.ts` (967 行) 拆分为 `hooks/` 子系统，同时归位 2 个散件（message-context.ts、mcp-tools.ts）。迁移相关测试文件。

## In Scope

- [x] 创建 `src/hooks/` 目录，含 6 个核心源文件 + 2 散件归位
- [x] 迁移 5 个测试文件到 hooks/
- [x] 迁移 index.test.ts OpenCodeRulesPlugin describe 到 hooks/integration.test.ts
- [x] 更新 `src/index.ts` 导入路径
- [x] 删除 `src/runtime.ts` 及散件原文件

## Out of Scope

- hooks 内部逻辑重构（保持原有行为）
- 新增 hooks 功能
- 性能优化

## Technical Context

### 当前文件结构

```
src/runtime.ts (967 lines)
├── HookContext 接口
├── 规则注入链路 (~250 lines)
├── 记忆注入链路 (~150 lines)
├── chat.message + messages.transform (~120 lines)
├── session.idle/error/permission/question (~180 lines)
├── command/tool hooks (~100 lines)
├── session.compacting/compacted (~80 lines)
└── OpenCodeRulesRuntime 类组装

src/message-context.ts  # 散件，归位到 hooks/
src/mcp-tools.ts        # 散件，归位到 hooks/
```

### 目标结构

```
src/hooks/
├── system-transform.ts   # 规则注入 + 记忆注入全链路 (~250 lines)
├── message-hooks.ts      # chat.message + messages.transform (~120 lines)
├── event-router.ts       # session.idle/error/permission/question (~180 lines)
├── command-hooks.ts      # 命令/工具 hooks (~100 lines)
├── compaction.ts         # session.compacting/compacted + isChildSession (~80 lines)
├── message-context.ts    # ← src/ 归位
├── mcp-tools.ts          # ← src/ 归位
├── index.ts              # HookContext + createAllHooks() 组装
└── *.test.ts             # 测试文件
```

### 外部引用关系

| 引用文件 | 当前导入 | 拆分后导入 |
|----------|----------|------------|
| `src/index.ts` | `./runtime.js` | `./hooks/index.js` |
| `src/runtime.*.test.ts` | `./runtime.js` | `./hooks/index.js` |

### index.test.ts Describe 块迁移映射

| Describe | 行号范围 | 目标文件 |
|----------|----------|----------|
| OpenCodeRulesPlugin | L1962-2718 | hooks/integration.test.ts |

### 现有测试文件迁移

| 现有文件 | 目标文件 |
|----------|----------|
| `src/runtime.events.test.ts` | `src/hooks/event-router.test.ts` |
| `src/runtime.memory.test.ts` | `src/hooks/memory.test.ts` |
| `src/runtime.tool-ids.test.ts` | `src/hooks/tool-ids.test.ts` |
| `src/message-context.test.ts` | `src/hooks/message-context.test.ts` |
| `src/mcp-tools.test.ts` | `src/hooks/mcp-tools.test.ts` |

## Files

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/runtime.ts` | 删除 | 拆分为 hooks/ |
| `src/hooks/system-transform.ts` | 创建 | 规则 + 记忆注入 |
| `src/hooks/message-hooks.ts` | 创建 | message hooks |
| `src/hooks/event-router.ts` | 创建 | 事件分发 |
| `src/hooks/command-hooks.ts` | 创建 | 命令 hooks |
| `src/hooks/compaction.ts` | 创建 | compaction hooks |
| `src/hooks/index.ts` | 创建 | 组装 + HookContext |
| `src/message-context.ts` | 移动 | → hooks/ |
| `src/mcp-tools.ts` | 移动 | → hooks/ |
| `src/runtime.*.test.ts` | 移动+重命名 | → hooks/ |
| `src/hooks/integration.test.ts` | 创建 | ← index.test.ts L1962-2718 |
| `src/index.ts` | 修改 | 导入 `./runtime.js` → `./hooks/index.js` |
| `src/index.test.ts` | 修改 | 删除 OpenCodeRulesPlugin describe |

## Implementation

### Task 1: 创建 hooks/ 目录并拆分 runtime.ts

**Files**: `src/hooks/system-transform.ts`, `src/hooks/message-hooks.ts`, `src/hooks/event-router.ts`, `src/hooks/command-hooks.ts`, `src/hooks/compaction.ts`, `src/hooks/index.ts`

**Changes**:
1. 创建 `src/hooks/` 目录
2. 创建 `hooks/system-transform.ts`：提取规则注入 + 记忆注入全链路
3. 创建 `hooks/message-hooks.ts`：提取 chat.message + messages.transform
4. 创建 `hooks/event-router.ts`：提取 session.idle/error/permission/question 分发
5. 创建 `hooks/command-hooks.ts`：提取 command/tool hooks
6. 创建 `hooks/compaction.ts`：提取 compaction hooks + isChildSession
7. 创建 `hooks/index.ts`：HookContext 接口 + createAllHooks() 组装所有 hooks

**Verification**: 
```bash
cd projects/ontology/plugins/wopal-plugin && bun run build
```

### Task 2: 散件归位 + 测试迁移

**Files**: `src/hooks/message-context.ts`, `src/hooks/mcp-tools.ts`, `src/hooks/*.test.ts`, `src/hooks/integration.test.ts`

**Changes**:
1. 移动 `src/message-context.ts` → `src/hooks/message-context.ts`
2. 移动 `src/mcp-tools.ts` → `src/hooks/mcp-tools.ts`
3. 移动 `src/runtime.events.test.ts` → `src/hooks/event-router.test.ts`，更新导入
4. 移动 `src/runtime.memory.test.ts` → `src/hooks/memory.test.ts`，更新导入
5. 移动 `src/runtime.tool-ids.test.ts` → `src/hooks/tool-ids.test.ts`，更新导入
6. 移动 `src/message-context.test.ts` → `src/hooks/message-context.test.ts`
7. 移动 `src/mcp-tools.test.ts` → `src/hooks/mcp-tools.test.ts`
8. 创建 `hooks/integration.test.ts`：复制 index.test.ts L1962-2718

**Verification**: 
```bash
cd projects/ontology/plugins/wopal-plugin && bun run test:run
```

### Task 3: 更新外部引用并清理

**Files**: `src/index.ts`, `src/index.test.ts`, `src/runtime.ts`

**Changes**:
1. `src/index.ts`：导入 `./runtime.js` → `./hooks/index.js`
2. `src/index.test.ts`：删除 OpenCodeRulesPlugin describe，导入路径更新
3. 删除 `src/runtime.ts`
4. 删除 `src/message-context.ts`（原位置）
5. 删除 `src/mcp-tools.ts`（原位置）

**Verification**: 
```bash
cd projects/ontology/plugins/wopal-plugin && bun run test:run && bun run build
```

## Delegation Strategy

| 批次 | Task | 执行者 | 依赖 |
|------|------|--------|------|
| 1 | Task 1 | fae | 无 |
| 1 | Task 2 | fae | Task 1 完成 |
| 1 | Task 3 | fae | Task 2 完成 |

## Test Plan

### Test Case Design

- hooks 文件拆分：单元测试验证各 hooks 模块独立导入正常
- 散件归位：测试文件迁移后导入路径正确
- 集成测试：hooks/integration.test.ts 验证 OpenCodeRulesPlugin 整体行为

### Regression Testing

- 396 单元测试全部通过（无新增失败）
- build 编译无错误

### Adjustment Strategy

- 如果某 hooks 文件行数超限，可进一步拆分内部函数
- 如果测试迁移后导入路径有问题，逐个文件排查修复

## Acceptance Criteria

### Agent Verification

- [x] `src/hooks/` 目录已创建，含 6 个核心源文件
- [x] message-context.ts、mcp-tools.ts 已归位到 hooks/
- [x] 5 个测试文件已迁移到 hooks/
- [x] `hooks/integration.test.ts` 已创建（← index.test.ts OpenCodeRulesPlugin describe）
- [x] `src/runtime.ts` 已删除
- [x] `src/index.ts` 导入路径已更新
- [x] `bun run test:run` 全通过
- [x] `bun run build` 编译通过

### User Validation

- 重启 OpenCode 后 wopal-plugin 功能正常
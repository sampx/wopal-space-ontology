# feature-wopal-plugin-add-environment-variable-toggle-for-rules-injection

## Metadata

- **Type**: feature
- **Target Project**: wopal-space-ontology
- **Created**: 2026-05-13
- **Status**: done

## Scope Assessment

- **Complexity**: Low
- **Confidence**: High

## Goal

为 wopal-plugin 添加环境变量开关，允许用户通过 `WOPAL_RULES_INJECTION_ENABLED=false` 禁用规则注入功能。

## Technical Context

当前规则注入在 `hooks/system-transform.ts` 中无条件执行（第 108-116 行）。用户需要一种方式在特定场景下禁用此功能（如调试、性能测试、或不需要规则约束的环境）。

插件已有环境变量机制（`WOPAL_PLUGIN_DEBUG`、`WOPAL_PLUGIN_LOG_FILE`），本次扩展此机制。

## In Scope

- 添加环境变量 `WOPAL_RULES_INJECTION_ENABLED`（默认 `true`）
- 在 `system-transform.ts` 中检查环境变量，决定是否跳过规则注入
- 更新 `wopal-plugin/AGENTS.md` 文档环境变量说明

## Out of Scope

- Memory 注入开关（当前记忆注入是核心功能，暂不需要开关）
- Rules 注入位置迁移（从 system prompt 迁移到 user message，属于 Issue #139 原方案，不在本次范围）

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| hooks | `.wopal/wopal-plugin/src/hooks/system-transform.ts` | 修改 | 添加环境变量检查逻辑 |
| docs | `.wopal/wopal-plugin/AGENTS.md` | 修改 | 添加环境变量文档 |

## Implementation

### Task 1: 添加环境变量检查

**Files**: `.wopal/wopal-plugin/src/hooks/system-transform.ts`

**Changes**:

- [x] Step 1: 在 `injectRules` 调用前添加环境变量检查
- [x] Step 2: 环境变量为 `false` 时跳过注入并记录 debug 日志

**Verification**:

- [x] Step 1: 执行 `bun run build` 编译通过
- [x] Step 2: 执行 `bun run test:run` 所有测试通过

### Task 2: 更新文档

**Files**: `.wopal/wopal-plugin/AGENTS.md`

**Changes**:

- [x] Step 1: 在"调试日志"章节后新增"规则注入开关"章节，说明环境变量用途和用法

**Verification**:

- [x] Step 1: 确认文档格式正确，示例命令可执行

## Delegation Strategy

N/A — 单一任务，无需并行委派

## Test Plan

#### Unit Tests

N/A — 环境变量逻辑简单，无需新增单元测试

#### Integration Tests

##### Case I1: 环境变量禁用规则注入
- Goal: 确认 `WOPAL_RULES_INJECTION_ENABLED=false` 时规则注入被跳过
- Fixture: 设置环境变量 `WOPAL_RULES_INJECTION_ENABLED=false`，启动 OpenCode 新会话
- Execution:
  - [x] Step 1: 启动 OpenCode 并观察 system prompt（启用 `WOPAL_PLUGIN_DEBUG=context`）
  - [x] Step 2: 确认 system blocks 中无规则内容
- Expected Evidence: debug 日志显示 "Rules injection disabled by environment variable"

##### Case I2: 默认启用规则注入
- Goal: 确认无环境变量时规则注入正常执行
- Fixture: 不设置 `WOPAL_RULES_INJECTION_ENABLED`，启动 OpenCode 新会话
- Execution:
  - [x] Step 1: 启动 OpenCode 并发送触发规则的消息
  - [x] Step 2: 确认 system prompt 包含规则内容
- Expected Evidence: system blocks 中包含 `<rules-context>` 内容

#### E2E Tests

N/A — 集成测试已覆盖核心场景

#### Regression Tests

##### Case R1: 规则注入功能不破坏现有行为
- Goal: 确认环境变量功能不影响默认行为
- Fixture: 现有规则文件（如 TypeScript 规范）
- Execution:
  - [x] Step 1: 不设置环境变量，发送违反规则的消息
  - [x] Step 2: 确认模型仍遵守规则
- Expected Evidence: 模型回复符合规则约束

### Adjustment Strategy

N/A — 单一任务，无复杂阻塞场景

## Acceptance Criteria

### Agent Verification

- [x] `bun run build` 编译通过
- [x] `bun run test:run` 所有测试通过
- [x] `system-transform.ts` 包含环境变量检查逻辑
- [x] `AGENTS.md` 包含环境变量文档

### User Validation

#### Scenario 1: 环境变量禁用规则注入生效
- Goal: 确认用户可以通过环境变量禁用规则注入
- Precondition: 设置 `WOPAL_RULES_INJECTION_ENABLED=false`
- User Actions:
  1. 启动 OpenCode 新会话
  2. 发送消息并观察行为
- Expected Result: 模型不遵守规则约束（如测试 TypeScript 分号规则被忽略）

- [x] 用户已完成上述功能验证并确认结果符合预期
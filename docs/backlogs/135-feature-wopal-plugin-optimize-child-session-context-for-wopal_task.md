# 135-feature-wopal-plugin-optimize-child-session-context-for-wopal_task

## Metadata

- **Issue**: #135
- **Type**: feature
- **Target Project**: wopal-plugin
- **Created**: 2026-05-11
- **Status**: planning

## Scope Assessment

- **Complexity**: Low
- **Confidence**: High

## Goal

在 `experimental.chat.system.transform` hook 中对子会话做系统提示词瘦身，过滤掉为主 agent 设计的空间级指令，将子会话系统提示词从 ~4200 tokens 降至 ~1000 tokens。

## Technical Context

wopal_task 启动的子会话与主 agent 共享同一套 OpenCode 系统提示词构造管线（`session/prompt.ts:1568-1574`）：

```
system = [...env, ...instructions, ...(skills ? [skills] : [])]
```

其中 `instructions` 来自 `instruction.system()`，会加载 AGENTS.md、CLAUDE.md 等指令文件。对主 agent（Wopal）来说这些是必要的行为守则，但对只执行具体编码任务的子 agent（fae、explore）来说全是噪音。

当前 wopal-plugin 已有基础设施：
1. `isChildSession()` — 通过 taskManager.findBySession + session.parentID 双重检测
2. 记忆注入跳过 — 子会话已跳过 LanceDB 记忆注入
3. `experimental.chat.system.transform` hook — 能 in-place 修改 system 数组

**关键机制**：`llm.ts:118-122` 在组装完系统提示词后触发 hook，hook 可以修改 `system` 数组（删除、替换、新增元素）。当前 wopal-plugin 只往里加东西（规则、记忆），没有删东西的能力。

## In Scope

- 在 `system-transform.ts` 中对子会话过滤 system 数组中的 instructions 段
- 保留环境信息（env，~200 chars）和工具规范
- 可选：注入精简版子 agent 指令（工具使用规范、编码约束）
- 新增单元测试验证过滤逻辑

## Out of Scope

- 修改 OpenCode 引擎层（session.create 的 directory/permission 参数）
- 创建子 agent 专属 AGENTS.md 文件（需要引擎支持不同目录）
- 修改 agent 定义（agent.prompt 字段）
- 过滤技能列表（子 agent 可能需要 skill tool 选择技能）

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| Hook | `src/hooks/system-transform.ts` | 修改 | 新增子会话系统提示词过滤逻辑 |
| Hook | `src/hooks/memory-injector.ts` | 参考 | isChildSession 已有实现 |
| Test | `src/hooks/system-transform.test.ts` | 创建 | 过滤逻辑单元测试 |

## Implementation

### Task 1: 子会话系统提示词过滤

**Files**: `src/hooks/system-transform.ts`

**Changes**:

- [ ] Step 1: 在 `onSystemTransform` 中，子会话检测后、规则注入前，新增 `stripHeavyweightContent` 函数调用
- [ ] Step 2: 实现 `stripHeavyweightContent(output, isChild)` — 过滤 system 数组中以 `"Instructions from:"` 开头的段（AGENTS.md、CLAUDE.md 等），保留 env 和 skills
- [ ] Step 3: 为子会话注入精简版指令（可选）—— 仅包含工具使用规范和编码约束，不含空间架构/记忆进化/委派规则

**Verification**:

- [ ] Step 1: 运行 `cd .wopal/wopal-plugin && bun run test:run` 确认所有测试通过
- [ ] Step 2: 检查新增测试覆盖了子会话过滤场景

## Delegation Strategy

N/A — 单一任务，无需并行委派。由 Wopal 直接执行。

## Test Plan

#### Unit Tests

##### Case U1: 子会话 system 数组过滤
- Goal: 验证子会话的 system 数组中 instructions 段被正确过滤
- Fixture: 构造包含 env + 2 个 instructions + skills 的 system 数组
- Execution:
  - [ ] Step 1: 模拟子会话（isChildSession 返回 true）
  - [ ] Step 2: 调用 onSystemTransform
  - [ ] Step 3: 验证 system 数组中不再包含 "Instructions from:" 段
  - [ ] Step 4: 验证 env 和 skills 仍保留
- Expected Evidence: system 数组长度减少，仅含 env 和 skills

##### Case U2: 主会话不受影响
- Goal: 验证主会话的 system 数组不被过滤
- Fixture: 构造与 Case U1 相同的 system 数组
- Execution:
  - [ ] Step 1: 模拟主会话（isChildSession 返回 false）
  - [ ] Step 2: 调用 onSystemTransform
  - [ ] Step 3: 验证 system 数组中 instructions 段保留
- Expected Evidence: system 数组与输入一致

##### Case U3: 空 system 数组不报错
- Goal: 验证边界情况不崩溃
- Fixture: 空 system 数组
- Execution:
  - [ ] Step 1: 传入 `{ system: [] }` 给子会话过滤函数
  - [ ] Step 2: 验证不抛异常，返回空数组
- Expected Evidence: 无异常，返回 `{ system: [] }`

#### Integration Tests

N/A — hook 逻辑为纯函数，无需集成测试。

#### E2E Tests

N/A — 需要完整 OpenCode 环境，超出插件测试范围。

#### Regression Tests

##### Case R1: 主会话规则+记忆注入不受影响
- Goal: 确认主会话的规则注入和记忆注入流程不受子会话过滤逻辑影响
- Fixture: 主会话 + 规则文件 + 记忆数据
- Execution:
  - [ ] Step 1: 模拟主会话的完整 onSystemTransform 流程
  - [ ] Step 2: 验证规则和记忆正常注入
- Expected Evidence: system 数组包含规则和记忆内容

### Adjustment Strategy

N/A — 单一任务，无复杂阻塞场景。

## Acceptance Criteria

### Agent Verification

- [ ] `cd .wopal/wopal-plugin && bun run test:run` 全部通过
- [ ] 新增测试覆盖子会话过滤、主会话不受影响、边界情况

### User Validation

#### Scenario 1: wopal_task 子会话上下文瘦身
- Goal: 确认 wopal_task 启动的子会话系统提示词不再包含 AGENTS.md 等主 agent 专属内容
- Precondition: OpenCode 运行中，wopal-plugin 已加载
- User Actions:
  1. 通过 Wopal 启动一个 wopal_task 子会话（如委派 fae 执行简单编码任务）
  2. 观察子会话的系统提示词内容
- Expected Result: 子会话系统提示词中不包含 "Instructions from:" 段（AGENTS.md 等），仅保留环境信息和工具规范

- [ ] 用户已完成上述功能验证并确认结果符合预期

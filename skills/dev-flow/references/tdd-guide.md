# TDD Task 编写指南

## 何时使用 TDD

**核心启发式**：能在编写 `fn` 之前用 `expect(fn(input)).toBe(output)` 描述行为吗？

- 能 → 使用 TDD（`**TDD**: true`）
- 不能 → 使用标准 Task，事后按需加测试

### 适合 TDD 的场景

- 有明确输入/输出的业务逻辑
- 有请求/响应契约的 API 端点
- 数据转换、解析、格式化
- 验证规则和约束
- 有可测试行为的算法
- 状态机和工作流

### 不适合 TDD 的场景

- UI 布局、样式、视觉组件
- 配置更改、文件删除
- 胶水代码（连接现有组件）
- 探索性原型
- 无业务逻辑的简单 CRUD

## Task 内 TDD 写法

在 Plan 的 Task 中，TDD 通过字段配合实现：

```markdown
**Verification Intent**: AC#1, AC#2

**Behavior**:
输入 → 输出映射：
- valid_email("user@example.com") → true
- valid_email("") → false
- valid_email("no-at-sign") → false

**Files**: `src/validators/email.py`, `tests/test_email_validator.py`

**Pre-read**: `src/validators/pattern.py`

**Design**:
分三阶段实现（RED → GREEN → REFACTOR）：
1. RED：编写测试覆盖上述 Behavior 中的输入/输出映射，运行测试确认失败
2. GREEN：实现 email 验证函数，最小代码使测试通过
3. REFACTOR：提取正则常量，清理实现（如需）

**TDD**: true

**Changes**:
1. 创建 `tests/test_email_validator.py`，编写 3 个测试用例覆盖 Behavior
2. 在 `src/validators/email.py` 实现 `valid_email()` 函数
3. 提取 `EMAIL_REGEX` 常量，消除硬编码

**Verify**:
`python -m pytest tests/test_email_validator.py -v` 全部 pass

**Done**:
任务产出：email 验证函数含 3 个测试用例，RED→GREEN→REFACTOR 三阶段完成
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）
```

### 关键字段说明

| 字段 | TDD 下的要求 |
|------|-------------|
| **Behavior** | 必填且详细。列出具体的输入/输出映射 |
| **Design** | 按 RED → GREEN → REFACTOR 三阶段描述 |
| **Changes** | 三步对应三阶段，编号列表 |
| **Verify** | 运行测试命令，确认全部通过 |

## 提交建议

TDD Task 产生 2-3 个原子提交（每个阶段一个）：

```
test(scope): add failing test for email validation
feat(scope): implement email validation
refactor(scope): extract regex to constant
```

**原则**：
- RED 阶段提交：测试存在且失败
- GREEN 阶段提交：最小实现使测试通过
- REFACTOR 阶段提交：仅在有实际改进时提交

## 错误处理

| 阶段 | 问题 | 处理 |
|------|------|------|
| RED | 测试没有失败 | 功能可能已存在或测试有误，调查后再继续 |
| GREEN | 测试没有通过 | 调试实现，持续迭代直到通过，不要跳到重构 |
| REFACTOR | 测试失败 | 撤销重构，用更小的步骤重试 |

**RED 不失败是最常见的陷阱**：意味着测试没有真正覆盖预期行为，必须修复后才能继续。

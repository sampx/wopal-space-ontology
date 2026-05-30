# Issue 与 Plan 命名规范

## Issue 标题格式

```text
<type>(<scope>): <description>
```

要求：
- `type` 必须合法
- `scope` 必填
- `description` 使用英文祈使句
- `description` ≤ 55 chars
- 整体标题 ≤ 72 chars

## 合法 type

| type | 用途 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `perf` | 性能优化 |
| `refactor` | 重构 |
| `docs` | 文档更新 |
| `test` | 测试相关 |
| `chore` | 工具 / 构建 |
| `enhance` | 功能增强 |

## 示例

- `feat(cli): add skills remove command`
- `fix(dev-flow): handle expired tokens`
- `perf(sync): reduce issue body rewrite cost`

## Issue body 五段结构

所有 Issue body 统一使用以下五段式结构（按顺序）：

| 段落 | 标题 | 用途 |
|------|------|------|
| 1 | `## Goal` | 一句话目标 |
| 2 | `## Context` | 背景、研究发现、决策依据、参考资料——agent 自由写入 |
| 3 | `## Scope` | `### In` + `### Out`，明确范围边界 |
| 4 | `## Acceptance Criteria` | 可验证的完成条件，plan 阶段细化 |
| 5 | `## Related Resources` | 关联文档（Plan、PRD、Roadmap 等）表格 |

**Roadmap 生成的 Issue** 在 `## Goal` 之前额外包含元信息行：
```markdown
- **Product**: {product}
- **Phase**: {phase-id}
```

**Roadmap Slice Issue** 额外包含 `## Depends on` 和 `## Demo` 段落。

## Plan 名称

### Issue 模式

```text
<issue_number>-<type>-<scope>-<slug>
```

示例：

```text
110-feat-cli-add-skills-remove
```

### 无 Issue 模式

```text
<type>-<scope>-<slug>
```

示例：

```text
fix-dev-flow-handle-expired-tokens
```

## 规则

- `slug` 来自标题 description 部分
- 用 kebab-case
- 无 Issue 模式下，后续命令统一传 `plan-name`

## Plan 目录规则

- 新 Plan 必须先通过 `flow.sh plan ...` 生成或定位，禁止手写创建文件。
- `--project` 是必填参数，Plan 目录由其决定。
- **标准项目**：`projects/<project>/docs/plans/`
- **ontology-worktree**：`.wopal/docs/plans/`
- `docs/projects/<project>/plans/` 是 **DEPRECATED** 只读回退，禁止新写入。

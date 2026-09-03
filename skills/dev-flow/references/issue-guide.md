# Issue 编写指南

Issue 创建、编写、同步的详细指导。核心规则见 SKILL.md。

## Issue 创建

**必须使用 `flow.sh issue create`**，禁止直接调 `gh issue create`。脚本通过 `detect_space_repo` 自动检测空间仓库，无需手动指定 `--repo`。

```bash
flow.sh issue create --title "add skills remove command" --project <name> --type feat
```

**创建错误的 Issue 必须彻底删除**（`gh issue delete`），不能只是 close。用户不喜欢仓库里留垃圾记录。

## Issue 查询

**查询未完成 Issue 必须使用 `flow.sh issue list`**，禁止手动 `gh issue list`。脚本通过 `detect_space_repo` 自动定位空间仓库并显示 repo URL，避免 Agent 因不知道仓库归属而查错仓库（如误查已禁用 issues 的 ontology 仓库）。

```bash
flow.sh issue list                          # 列出空间仓库所有未完成 Issue
flow.sh issue list --project firecrawl      # 按 project 过滤
flow.sh issue list --status planning        # 按 status 过滤
flow.sh issue list --limit 100              # 指定数量
```

## Issue 标题格式

Issue 标题是**自由文本**，不再强制 `type(scope): description` 格式。宽松 type 前缀（可选）用于 label 推断。

```text
<自由描述>            # 推荐
<type>: <描述>        # 可选 type 前缀
<type>(<scope>): <描述>  # 兼容旧格式
```

要求：
- 宽松 type 前缀（若存在）必须合法（见下表）
- `scope` 不再必填
- `description` 使用英文祈使句
- `description` ≤ 55 chars
- 整体标题 ≤ 72 chars

### 合法 type

| type | 用途 |
|------|------|
| `feature` | 新功能 |
| `fix` | Bug 修复 |
| `perf` | 性能优化 |
| `refactor` | 重构 |
| `docs` | 文档更新 |
| `test` | 测试相关 |
| `chore` | 工具 / 构建 |
| `enhance` | 功能增强 |

### 示例

- `add skills remove command`
- `fix: handle expired tokens`
- `perf(sync): reduce issue body rewrite cost`

**标题语言规则**：标题使用英文（遵循项目仓库规范）。body 内容使用用户偏好语言编写（与 Plan 文档一致）。

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

## Issue 同步规则

只要 Plan 中实际映射到 issue body 的章节发生变化，**必须立即同步**，不应反问用户是否要同步。

**映射关系**：
- Plan `Goal` → Issue `## Goal`
- Plan `In Scope` / `Out of Scope` → Issue `## Scope`
- Plan `Acceptance Criteria` → Issue `## Acceptance Criteria`
- Plan `Related Resources` → Issue `## Related Resources`

**不需要同步的章节**：`Implementation`、`Technical Context`、`Delegation Strategy` 等仅存在于 Plan 的章节。

**同步命令**：
```bash
flow.sh sync <issue> --body-only
```

## Issue 驱动 vs 无 Issue 流程

| 模式 | 触发词 | 流程 |
|------|--------|------|
| Issue 驱动 | Issue 号、"处理 issue"、"开发" | 先创建 Issue → 再出 Plan |
| 无 Issue（Plan 驱动） | "出方案"、"写 Plan" | 直接 `flow.sh plan --title ... --project ... --type ...` |

两者都是 dev-flow 流程，区别在于是否有 Issue 载体。

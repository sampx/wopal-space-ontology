# 命令参考

对所有命令，使用 `flow.sh <cmd> --help` 获取完整参数列表和说明。本文档仅补充 `--help` 不覆盖的使用模式和边缘场景。

---

## 命令概览

### 工作流命令（状态机推进）

| 命令 | 说明 |
|------|------|
| `plan <issue>` | 创建或定位 Plan（裸命令，后向兼容） |
| `plan new <issue>` | 创建新 Plan |
| `plan status <plan-id>` | 查看 Plan 完整状态 |
| `plan list [--issue]` | 列出活跃 Plan（`--issue` 含 GitHub Issues） |
| `submit <plan>` | 提交人工审阅（planning → reviewing） |
| `approve <plan> --confirm` | 用户审批通过，默认创建 worktree 隔离 |
| `approve <plan> --confirm --no-worktree` | 用户审批通过，跳过 worktree |
| `complete <issue> [--pr]` | 实施完成，进入用户验证 |
| `verify <issue> --confirm` | 用户验证通过 |
| `archive <issue>` | 归档 Plan，推送 Plan 变更，同步阶段文档 |
| `verify-switch <issue> [--yes]` | 切换到特性分支验证 |
| `roadmap <prd-path> [--product ...] [--project ...]` | 产品阶段规划（四阶段工作流） |

### Issue 管理

| 命令 | 说明 |
|------|------|
| `issue create --title "..." --project <name> --body-file <path>` | 创建 Issue（`--body-file` 为主路径） |
| `issue list [--project X] [--status Y] [--limit N]` | 列出空间仓库未完成 Issue（含 repo URL，可按 project/status 过滤） |
| `issue write <issue> --body-file <path>` | 全量替换 Issue body |
| `issue write <issue> --append <path>` | 追加到 Issue body 末尾 |
| `issue update <issue>` | ⚠️ **已废弃**，使用 `issue write` 替代 |
| `decompose-prd <prd-path> [--dry-run]` | 从 PRD 拆分 Issue |
| `decompose-prd --from ROADMAP.md [--product <name>] [--dry-run]` | 从 ROADMAP.md Slices 表生成 Slice Issues |

### Plan 子命令

| 命令 | 说明 |
|------|------|
| `plan new <issue>` | 创建新 Plan，与裸 `plan <issue>` 等效 |
| `plan status <plan-id>` | 查看 Plan 完整状态（metadata、Issue、worktree） |
| `plan list` | 列出本地活跃 Plan |
| `plan list --issue` | 列出活跃 Plan，含 GitHub Issues 合并展示 |
| `plan <issue>` | 裸命令，后向兼容（自动创建或定位 Plan） |

### 其他命令

| 命令 | 说明 |
|------|------|
| `sync <issue> [--body-only\|--labels-only]` | Plan → Issue 同步 |
| `reset <issue>` | 重置 Plan 到 planning 状态 |

---

## 使用模式

### issue create 参数速记

```bash
# 最小创建（--body-file 为主路径）；标题自由文本，type 由 --type 显式指定
flow.sh issue create --title "add skills remove command" --project <name> --type feat --body-file body.md

# --type 可选覆盖（默认从标题宽松前缀推断）
--type feat
```

`--body-file` 指向包含五段结构的 markdown 文件。不再支持 type-specific 参数（`--confirmed-bugs`、`--baseline` 等）——agent 在 body 文件的 `## Context` 中自由写入。

### issue write

写入 Issue body（全量替换或追加）。

```bash
flow.sh issue write <issue> --body-file <path>    # 全量替换 body
flow.sh issue write <issue> --append <path>       # 追加到 body 末尾
```

**行为**：
- `--body-file`：用文件内容替换整个 Issue body
- `--append`：在现有 body 末尾追加文件内容，用 `\n\n` 分隔
- 空文件或文件不存在时报错退出（exit 1）
- 文件不以 `#` 或 `-` 开头时输出 warning

### issue list

列出空间仓库中所有未完成（open）Issue，并显示所在仓库 URL。

```bash
flow.sh issue list                          # 列出未完成 Issue（默认 50 条）
flow.sh issue list --limit 100              # 指定数量
flow.sh issue list --project firecrawl      # 按 project 过滤（可多次，OR）
flow.sh issue list --status planning        # 按 status 过滤（可多次，OR）
flow.sh issue list --project firecrawl --project wopal-cli --status planning --status verifying
```

**行为**：
- 通过 `detect_space_repo` 自动定位空间仓库，无需也不允许手动指定 `--repo`
- `--project`：按项目过滤，多次指定取 OR
- `--status`：按状态过滤（`planning`/`executing`/`in-progress`/`verifying`/`done`，`executing` 与 `in-progress` 等价），多次指定取 OR；project 与 status 之间为 AND
- 每行显示 `#<number>  <title>  [<label>...]`
- 末尾显示 `Issues in: https://github.com/<owner>/<repo>`
- 仓库检测失败或 `gh` 调用失败时报错退出（exit 1）

Agent 查询未完成 Issue 一律使用本命令，避免手动 `gh issue list` 查错仓库。

### issue update（已废弃）

```bash
flow.sh issue update <issue> [options]
```

⚠️ 已废弃，使用 `issue write --body-file` 或 `--append` 替代。调用时输出 deprecated 警告。

### plan 子命令

```bash
# 创建
flow.sh plan new <issue>                # 从 Issue 创建
flow.sh plan new --title "..." --project <name> --type <type>  # 无 Issue 创建

# 查询
flow.sh plan status <plan-id>           # 查看 Plan 完整状态
flow.sh plan list                       # 列出本地活跃 Plan
flow.sh plan list --issue               # 列出活跃 Plan + GitHub Issues

# 校验
flow.sh plan check <plan-name-or-path>  # 校验 Plan 质量（Issue 号 / Plan 名 / 文件路径均可）
```

`plan list` 默认离线，仅扫描本地 Plan 文件。`--issue` 增加 GitHub Issues 合并展示，无 Plan 的 Issue 显示 `[recorded]`。

### sync

```bash
flow.sh sync <issue>           # 全量同步（body + labels）
flow.sh sync <issue> --body-only    # 仅 body
flow.sh sync <issue> --labels-only  # 仅 labels
```

### submit

```bash
flow.sh submit <plan>       # planning → reviewing，提交人工审阅
```

提交 Plan 状态变更，commit/push 到集成分支。输出 "Next: flow.sh approve <plan> --confirm" 提示。

### approve --confirm

```bash
flow.sh approve <plan> --confirm                            # 默认创建 worktree
flow.sh approve <plan> --confirm --no-worktree               # 跳过 worktree（main 直实施）
flow.sh approve <plan> --confirm --existing-worktree <path> # 独立分支演进模式（复用已有 worktree）
```

`approve` 不带 `--confirm` 时报错退出，提示使用 `submit`。`--confirm` 接受 `reviewing` 或 `planning`（快捷路径）→ `executing`。

**模式选择**：
1. **默认模式**：创建独立 feature 分支与工作树（`.worktrees/<project>-<plan-name>`），记录集成分支 HEAD 为 Base Commit。
2. **`--no-worktree`**：直接在集成分支（main）实施，不建分支不建工作树。
3. **`--existing-worktree <path>`**：**独立分支演进模式**。复用已有工作树路径 `<path>`，自动绑定其检出的 feature 分支写入 Plan 元数据，并将 Base Commit 记录为该分支当前最新 HEAD（上一个 Plan 的实施产物终点）。

### verify --confirm [--keep-worktree]

```bash
flow.sh verify <plan> --confirm                # 标准模式（要求已合并到集成分支）
flow.sh verify <plan> --confirm --keep-worktree # 演进模式（跳过 merge 检查，记录 feature HEAD）
```

### archive [--keep-worktree]

```bash
flow.sh archive <plan>                # 标准模式（清理 worktree 与分支）
flow.sh archive <plan> --keep-worktree # 演进模式（保留 worktree 与分支）
```

### complete --pr

```bash
flow.sh complete <issue> --pr    # PR 路径（默认不走 PR）
```

### verify-switch

切换工作空间到特性分支供用户验证。适用 standard 和 ontology-worktree 两种项目类型。

执行流程：
1. 检查规范路径 git 状态（脏时输出 warning，不阻塞）
2. 移除开发工作树
3. 在规范路径 checkout 特性分支
4. 更新 Plan Worktree 元数据（path → "(removed)"，新增 Verification Dir 字段）
5. commit Plan 变更（保持特性分支 git 状态干净）
6. 输出验证指引

standard 项目规范路径为项目目录（如 `projects/<name>/`）；ontology-worktree 规范路径为 `.wopal/`。

```bash
# 切换到特性分支验证
flow.sh verify-switch <issue>
```

验证通过后，合并特性分支到集成分支。**默认优先 squash 合并**（保持 main 历史干净）：

```bash
cd <repo_root>
git checkout main        # standard 项目；ontology-worktree 用 space/<name>
git merge --squash <feature_branch>   # 压成单个提交
git commit -m "feat(scope): <description> (#<issue>)"
# 或保留历史: git merge --no-ff <feature_branch>
```

squash 合入后 verify 的 tree 相等判据原生识别已合并，无需手动干预。

### decompose-prd

```bash
# 从 PRD 拆分 Issue（兼容旧模式）
flow.sh decompose-prd projects/<project>/docs/PRD.md --dry-run   # 预览
flow.sh decompose-prd projects/<project>/docs/PRD.md --project <name>  # 创建

# 从 ROADMAP.md Slices 表生成 Slice Issues
flow.sh decompose-prd --from ROADMAP.md [--product <name>] [--dry-run]
```

`--from ROADMAP.md` 模式解析 ROADMAP.md 中 `## Slices` 下的 markdown table，为每个 Slice 生成独立 Issue。Slices 表格式见 ROADMAP.md Slices 语法规范。`--product` 指定产品线名称，用于 Issue 标签和 body 元信息。

### roadmap

```bash
flow.sh roadmap projects/<project>/docs/PRD.md --product <name> [--project <name>] [--yes] [--dry-run]
```

四阶段工作流：Analyze → Discuss → Produce → Decompose。

- `--product`：产品线名称（默认从 PRD 文件名推断）
- `--project`：指定项目（影响 Issue label）
- `--yes`：跳过 Discuss 交互，直接使用 Analyze 结果（非 TTY 环境必须指定）
- `--dry-run`：只输出阶段分析，不创建文件和 Issue

### reset（破坏性）

```bash
flow.sh reset <issue>       # Issue 驱动
flow.sh reset <plan-name>   # Plan 驱动
```
仅用户明确要求时使用。

---

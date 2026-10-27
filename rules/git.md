# Git 与 Issue 工程规范

本文档为 Wopal 空间内所有仓库的 Git 提交、分支管理及 Issue 路由之详细执行标准。仅在执行 Git 提交、合并及 Issue 操作时按需读取。

---

## 1. Issue 规范

### 标题格式

`<type>(<scope>): <description>`

- **type**（必选）：见下方 Label 映射。
- **scope**（可选）：括号包裹，小写简洁，全局不明确时可省略。
- **description**（必选）：英文祈使句，首字母小写，结尾无句号；≤70 chars（以 type 前缀后的文本计算），首行总长 ≤100 chars。

**Label 映射**：
- `feat` / `enhance` → `type/feature`
- `fix` → `type/bug`
- `refactor` → `type/refactor`
- `docs` → `type/docs`
- `test` → `type/test`
- `chore` → `type/chore`
- `perf` 无 label

### Issue 项目归属与流程路由

`--project` 填改动对象所在的空间组件，决定 `project/<name>` 标签、Plan/提案目录，以及后续走哪套流程：

| Issue 要改的东西 | `--project` | 流程 |
|---|---|---|
| `.wopal/` 下的本体能力资产（skills、rules、agents、commands、plugins、assembly） | `wopal-space-ontology` | 本体进化流程 |
| `projects/` 下的代码仓库 | 该仓库名 | 开发流程 |

- 本体工作固定用 `wopal-space-ontology`，不得写 `ontology`、`space` 等变体。
- 标为 `wopal-space-ontology` 的 Issue 一律走本体提案，不走开发流程的 Plan、分支与 worktree。
- 所有 Issue/Plan 一律创建并存储于空间仓库，由开发流程自动定位；`--project` 仅决定 Plan 目录划分，禁止质疑归属。

---

## 2. Git 工作流

### 基本法

- **显式指定目标仓库**：必须用 `git -C <path>` 显式指定目标仓库；空间根目录是独立 Git repo，禁止依赖默认工作目录对子项目执行 Git 操作。
- **实施前前置检查**：
  1. `git status`（有未提交变更先提醒用户提交）
  2. `git log --oneline -5`（非本会话未推送提交先报告）
- **提交前确认检查**：
  1. `git status` + `git diff --staged --name-only`（确认变更范围与提交意图一致，无其他任务文件）
  2. `git log --oneline -5`
  3. 确认不在 detached HEAD。
- **提交语言**：空间内所有 repo 一律使用英文提交信息，包括空间根仓库、`projects/*` 与 `.wopal/` worktree。提交信息是面向 Git 历史的工程记录，不随文档正文语言变化。
- **分层提交**：先项目后空间；变更路径决定检查哪个仓库（`projects/*/` 的变更不检查空间根仓库）；在项目内完成 add → commit → push。

### 提交格式

`<type>(scope): <description> [#ref]`

- **type** 必选（见下表）；scope 可选，括号包裹、小写简洁（如 `(api)`、`(cli)`），全局不明确时省略。
- **description**：祈使句，英文首字母小写，结尾无句号；≤70 chars，有 Issue ref 时 ≤60 chars；首行总长 ≤100。
- **body**（可选）：空行分隔，解释 what/why 而非 how，每行 ≤72 chars；破坏性变更以 `BREAKING CHANGE:` 开头。
- **原子提交**：相关变更合为一提交，不相关变更拆分，便于回滚与 bisect。

| Type | 用途 | 版本变更 | Type | 用途 | 版本变更 |
|------|------|----------|------|------|----------|
| `feat` | 新功能 | MINOR | `enhance` | 功能增强 | MINOR |
| `fix` | Bug 修复 | PATCH | `perf` | 性能优化 | — |
| `refactor` | 重构（功能不变） | — | `ci` | CI/CD 配置 | — |
| `docs` | 文档更新 | — | `build` | 构建系统 | — |
| `test` | 测试相关 | — | `revert` | 回滚提交 | — |
| `chore` | 构建/工具 | — | `style` | 代码格式（无逻辑变更） | — |

### 分支策略

| 分支 | 用途 |
|------|------|
| `main` | 主分支，稳定版本 |
| `feature/*` | 功能开发 |
| `bugfix/*` | Bug 修复 |
| `hotfix/*` | 紧急修复 |
| `refactor/*` | 重构 |

### 合并验证（结构变更铁律）

特性分支含文件重命名、目录重组、多文件合并/拆分等结构变更时，合并禁止依赖 Git 自动合并；无冲突 ≠ 变更无损。

**合并前必须执行**：
1. `git merge-base` 找到共同祖先；
2. 列出目标分支新增提交；
3. 逐文件分类判断（1:1 rename 可自动处理但须验证；merge/split 必须手动移植）；
4. 上报分类结果，获用户确认后执行 merge。

---

## 3. 提交禁令

敏感凭证（`.env`、密钥）与临时产物（`__pycache__/`、`node_modules/`、`.ruff_cache/`、IDE 配置）一律不得进入仓库。

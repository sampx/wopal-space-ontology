---
trigger: model_decision
description: 在 WopalSpace 仓库执行 Git、分支、合并、提交或 Issue 操作时遵守此规则。
keywords:
  - 'git'
  - 'commit'
  - 'branch'
  - 'merge'
  - 'issue'
  - 'pull request'
  - 'pr'
---

# Git 与 Issue 工程规范

本文档定义 WopalSpace 仓库中 Git 与 Issue 操作的共享执行底线。只有任务实际涉及 Git、分支、合并、提交或 Issue 操作时才按需加载。

具体 owning workflow 的规则优先于本共享规则。当 `dev-flow`、`ontology-evolution` 或其他能力已经定义分支命名、提交归属、集成、发布或 Issue 路由时，应遵守对应 workflow，不在这里另造或强加第二套 Git 流程。

---

## 1. Issue 规范

### 标题格式

`<type>(<scope>): <description>`

- **type** 必选，使用下方 Label 映射。
- **scope** 可选，括号包裹、小写简洁。
- **description** 使用英文祈使短语，首字母小写、结尾无句号；type 前缀之后最多 70 字符，首行总长最多 100 字符。

**Label 映射**：
- `feat` / `enhance` → `type/feature`
- `fix` → `type/bug`
- `refactor` → `type/refactor`
- `docs` → `type/docs`
- `test` → `type/test`
- `chore` → `type/chore`
- `perf` → 不加 type label

### 项目归属与流程路由

`--project` 填实际改动对象，决定 `project/<name>` 标签与 owning workflow：

| 改动对象 | `--project` | Owning workflow |
|---|---|---|
| `.wopal/` 下可复用能力资产（`skills`、`rules`、`agents`、`commands`、`plugins`、`assembly`） | `wopal-space-ontology` | `ontology-evolution` |
| `projects/` 下代码仓库 | 该仓库名 | `dev-flow` |

- 本体工作固定使用规范项目名 `wopal-space-ontology`，不得写 `ontology`、`space` 等别名。
- 本体工作由 `ontology-evolution` 判断路径：已约定行为的实现缺陷走 instant repair；能力或契约变化走 proposal 生命周期。
- 不把本体能力工作路由到 `dev-flow` Plan；也不把项目代码工作路由到 ontology proposal，除非 owning workflow 明确规定例外。
- `--project` 只决定归属与路由，不授权移动记录、跨仓库写入或绕过 owning workflow。

---

## 2. Git 工作流

### 基本规则

- **显式指定目标仓库**：直接检查或手工执行 Git 操作时使用 `git -C <path>`。空间根目录本身是独立仓库，禁止依赖当前工作目录隐式操作嵌套项目。
- **尊重 workflow 的 Git 所有权**：当前 workflow 已经负责 commit、integration、PR 发布或 cleanup 时，使用其命令与门控，不用 raw Git 替代。
- **手工 mutation 前**：
  1. 检查 `git status`，保留无关工作；
  2. 检查 `git log --oneline -5`，报告意外的仅本地历史；
  3. 除非 owning workflow 与用户授权明确允许当前精确动作，不用 reset、stash、clean、force-push 或 branch deletion 重塑他人的现场。
- **手工 commit 前**：
  1. 检查 `git status` 与 `git diff --staged --name-only`，确认提交范围；
  2. 检查 `git log --oneline -5`；
  3. 确认 HEAD 附着在预期分支。
- **提交语言**：空间内所有仓库一律使用英文提交信息，包括空间根仓、`projects/*` 与 ontology worktree。Git 历史语言不随文档正文语言变化。
- **仓库归属**：改动在真正拥有它的仓库提交；不能借空间根仓暂存项目仓内容，也不能绕过负责 `.wopal` 能力变更的 workflow。

### 提交格式

`<type>(scope): <description> [#ref]`

- `type` 必选；`scope` 可选、小写、简洁。
- `description` 使用英文祈使短语，首字母小写、结尾无句号；最多 70 字符（附 Issue ref 时最多 60），首行总长最多 100 字符。
- 可选 body 用空行分隔，说明 what/why 而不是 how，每行最多 72 字符；破坏性变更以 `BREAKING CHANGE:` 开头。
- 保持原子提交：一个提交只承载一个完整主题，无关变化拆开，便于回滚与 bisect。

| Type | 用途 | 版本 | Type | 用途 | 版本 |
|------|------|------|------|------|------|
| `feat` | 新能力 | MINOR | `enhance` | 能力增强 | MINOR |
| `fix` | Bug 修复 | PATCH | `perf` | 性能优化 | — |
| `refactor` | 行为不变的重构 | — | `ci` | CI/CD | — |
| `docs` | 文档 | — | `build` | 构建系统 | — |
| `test` | 测试 | — | `revert` | 回滚 | — |
| `chore` | 工具/维护 | — | `style` | 仅格式 | — |

### 分支归属

- 不对 workflow 管理的分支强加统一的 `feature/*`、`bugfix/*`、`hotfix/*` 或 `refactor/*` 规范。
- `dev-flow` 自己定义 Work Branch 与 Integration Branch；`ontology-evolution` 自己定义 ontology isolation 与 `contribute/<slug>` 贡献分支。
- 确实不属于任何 owning workflow 的手工仓库工作，才使用简短、有意义的分支名，并遵守该仓库自身规则。

### 结构变更的手工合并验证

只有在合并不属于现成 workflow 管理、需要手工执行时，文件重命名、目录迁移、多文件合并/拆分等结构变更才按本节检查；“Git 无冲突”不能证明结果无损。

手工合并前：
1. 找到 merge base；
2. 列出目标分支新增提交；
3. 逐文件分类结构变化（1:1 rename 可自动合并但仍需验证；merge/split 必须显式移植）；
4. 上报分类，并按 owning process 所要求的用户决定门取得放行后再改写历史。

---

## 3. 提交禁令

禁止提交凭证或临时/生成型工作区产物，例如 `.env`、私钥、`__pycache__/`、`node_modules/`、`.ruff_cache/`、IDE 本地配置；只有仓库明确声明的安全跟踪例外可以保留。

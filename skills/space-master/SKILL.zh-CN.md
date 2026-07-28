---
name: space-master
description: |
  空间工作规范总纲。⚠️ MUST LOAD FIRST — Wopal 不确定怎么做或任务意图不明确时，第一个加载本技能。

  Triggers: 任何意图不明确的任务、"用什么流程"、"该加载什么技能"、
  技能管理（安装/卸载/搜索）、空间运维（worktree/同步/上游/PR贡献）、多 Space 管理。
  
  🔴 即使用户未明确说"上游同步"，只要涉及 ontology 仓库协作（update/sync/contribute/promote/PR），就必须加载本技能。
---

# space-master — 空间工作规范总纲

本技能是 Wopal 的空间导航员。加载后，Wopal 应知道本空间有什么流程、场景到技能的路由规则、委派原则以及标准流畅的本体（Ontology）维护与 PR 贡献工作流。

---

## 空间工作体系

本空间支持多种工作流程，按任务类型选择：

| 流程 | 适用场景 | 加载技能 |
|------|---------|---------|
| **dev-flow** | 开发/修复/重构 GitHub Issue、Plan 驱动的小功能迭代 | dev-flow + agents-collab |
| **无流程** | 单纯研究、讨论、解释、评审、临时小改动 | 无（Wopal 直接处理） |

dev-flow 是默认开发流程。

---

## 场景→技能路由

| 场景 | 加载技能 | 说明 |
|------|---------|------|
| 开发/修复/重构 Issue | dev-flow + agents-collab | 先加载 agents-collab，再走 dev-flow |
| 委派任何子 Agent | agents-collab | 任何委派前必须加载 |
| 空间与本体运维（技能安装/同步/上游PR/Promote） | 仅本技能 | 不加载 dev-flow 或 agents-collab |
| 创建/修改技能 | skill-creator | 独立技能（修改/创建技能前必载） |
| 配置 ellamaka | ellamaka-config | 独立技能 |

---

## Ontology 维护与上游 PR 贡献标准流程

Wopal 本体采用三层架构（`main` ➔ `type/<type>` ➔ `space/<name>`）。日常维护与上游 Pull Request 贡献遵循以下四个标准闭环阶段：

```
[空间层 space/*] 
      │ 1. space contribute (--include 链式)
      ▼
[类型层 type/*] 
      │ 2. ontology contribute (--include 链式) ➔ 自动在 Fork 远端创建 PR
      ▼
[官方上游 upstream] (GitHub 网页点击 Merge)
      │ 3. ontology update (--confirm) ➔ 自动同步拓扑 + 自动擦除 Fork 远端临时分支
      ▼
[主干升维 promote] (--include 链式) ➔ 从 type/* 提炼通用能力回流 main 主干
```

### 1. 检查状态（Check First）
在执行任何变更前，总是先运行预检：
```bash
WOPAL_HOME=~/.wopal wopal ontology status
```

### 2. 空间上行合入类型（space contribute）
把当前空间的修改增量 squash merge 到本地类型分支 `type/<type>`：
```bash
WOPAL_HOME=~/.wopal wopal space contribute --message "feat(scope): short description" --confirm
```

### 3. 创建上游 Pull Request（ontology contribute）
通过链式 `--include` 精准白名单模式，按主题独立打包并自动在 GitHub Fork 远端创建 PR（零混入杂质/绝不误删框架）：
```bash
WOPAL_HOME=~/.wopal wopal ontology contribute \
  --type coding \
  --include "skills/dev-flow/**" \
  --include "skills/space-master/**" \
  --message "feat(skills): update dev-flow and space-master skills" \
  --confirm
```
* 💡 **链式 `--include` 特性**：支持多次传入 `--include` 标志，自动收集并严格只打包目标路径文件，其余不相干改动安全排除（`exclude`）。

### 4. 网页合并与下行闭环（ontology update）
当用户在 GitHub 网页上审核并合并 PR 后，在本地一键运行：
```bash
WOPAL_HOME=~/.wopal wopal ontology update --confirm
```
* 💡 **自动清理特性**：`ontology update` 会在完成拓扑平滑对齐后，**自动擦除**在 GitHub Fork 远端（`origin`）上为 PR 创建的陈旧 `contribute/*` 临时 Head 分支，保持远端仓库绝对干净。

### 5. 主干提炼升维（ontology promote）
将类型分支（如 `type/coding`）上验证通过的全局通用能力（如通用模板 `templates/`、通用文档 `docs/`、通用技能）提炼升级回 `main` 主干：
```bash
WOPAL_HOME=~/.wopal wopal ontology promote \
  --from type/coding \
  --include "templates/**" \
  --include "docs/**" \
  --include "skills/space-master/**" \
  --message "feat(ontology): promote generic templates and skills to main branch" \
  --confirm
```

---

## Quick Commands 常用速查

```bash
# 1. 状态查看
WOPAL_HOME=~/.wopal wopal ontology status

# 2. 本地直接提交（.wopal 是 git worktree）
git -C .wopal add -A && git -C .wopal commit -m "feat(scope): description"

# 3. 下行拉取与自动清理（合并 PR 后运行）
WOPAL_HOME=~/.wopal wopal ontology update --confirm

# 4. 空间合入类型
WOPAL_HOME=~/.wopal wopal space contribute --message "..." --confirm

# 5. 上游 PR 贡献（支持链式 --include）
WOPAL_HOME=~/.wopal wopal ontology contribute \
  --type coding \
  --include "path1/**" \
  --include "path2/**" \
  --message "..." \
  --confirm

# 6. 主干提炼升维（支持链式 --include）
WOPAL_HOME=~/.wopal wopal ontology promote \
  --from type/coding \
  --include "templates/**" \
  --include "docs/**" \
  --message "..." \
  --confirm
```

---

## 核心铁律

1. **链式 `--include` 白名单机制**：涉及 `ontology contribute` 与 `promote` 时，总是明确使用链式 `--include` 标志分主题打包，绝不盲目提交包含全量未审核差异的巨型 PR。
2. **先状态后操作**：先执行 `wopal ontology status` 明确 Downstream / Upstream 拓扑后，再与用户确认构建命令。
3. **闭环自动清理**：在 GitHub 网页上合并 PR 后，必定提醒或执行 `wopal ontology update --confirm` 完成基线对齐与 Fork 远端陈旧临时分支擦除。

---
name: space-master
description: |
  空间工作规范总纲。[MUST LOAD FIRST] — Wopal 不确定怎么做或任务意图不明确时，第一个加载本技能。

  Triggers: 任何意图不明确的任务、"用什么流程"、"该加载什么技能"、
  技能管理（安装/卸载/搜索）、空间运维（worktree/同步/上游/PR贡献）、多 Space 管理。
  
  [CRITICAL] 即使用户未明确说"上游同步"，只要涉及 ontology 仓库协作（update/sync/contribute/promote/PR），就必须加载本技能。
---

# space-master — 空间工作规范总纲

本技能定义 Wopal 空间流程选择、场景技能路由、Agent 委派原则以及标准本体（Ontology）维护与 PR 贡献操作指令。

---

## 空间工作体系

本空间支持以下工作流程，按任务类型选择：

| 流程 | 适用场景 | 加载技能 |
|------|---------|---------|
| **dev-flow** | 开发/修复/重构 GitHub Issue、Plan 驱动的小功能迭代 | dev-flow + agents-collab |
| **无流程** | 单纯研究、讨论、解释、评审、临时小改动 | 无（Wopal 直接处理） |

dev-flow 是默认开发流程。

---

## 场景➔技能路由

| 场景 | 加载技能 | 说明 |
|------|---------|------|
| 开发/修复/重构 Issue | dev-flow + agents-collab | 先加载 agents-collab，再走 dev-flow |
| 委派任何子 Agent | agents-collab | 任何委派前必须加载 |
| 空间与本体运维（技能安装/同步/上游PR/Promote） | 仅本技能 | 不加载 dev-flow 或 agents-collab |
| 创建/修改技能 | skill-creator | 独立技能（修改/创建技能前必载） |
| 配置 ellamaka | ellamaka-config | 独立技能 |

---

## Ontology 维护与上游 PR 贡献指令规程

处理本体仓库协作时，按以下顺序执行命令：

### 1. 检查状态
```bash
WOPAL_HOME=~/.wopal wopal ontology status
```

### 2. 空间改动合入类型分支
把当前空间的修改增量合入本地类型分支 `type/<type>`：
```bash
WOPAL_HOME=~/.wopal wopal space contribute --message "feat(scope): description" --confirm
```

### 3. 创建上游 Pull Request（分主题链式 `--include`）
按主题使用链式 `--include` 标志独立打包并创建 PR：
```bash
WOPAL_HOME=~/.wopal wopal ontology contribute \
  --type coding \
  --include "skills/dev-flow/**" \
  --include "skills/space-master/**" \
  --message "feat(skills): update dev-flow and space-master skills" \
  --confirm
```

### 4. 上游网页 PR 合并后收尾
在 GitHub 上合并 PR 后，运行下行同步：
```bash
WOPAL_HOME=~/.wopal wopal ontology update --confirm
```

### 5. 主干提炼升维（promote）
将类型分支（如 `type/coding`）上的通用改进合并入 `main` 主干：
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
# 状态查看
WOPAL_HOME=~/.wopal wopal ontology status

# 下行拉取（合并 PR 后运行）
WOPAL_HOME=~/.wopal wopal ontology update --confirm

# 空间合入类型
WOPAL_HOME=~/.wopal wopal space contribute --message "..." --confirm

# 上游 PR 贡献（链式 --include）
WOPAL_HOME=~/.wopal wopal ontology contribute \
  --type coding \
  --include "path1/**" \
  --include "path2/**" \
  --message "..." \
  --confirm

# 主干提炼升维（链式 --include）
WOPAL_HOME=~/.wopal wopal ontology promote \
  --from type/coding \
  --include "templates/**" \
  --include "docs/**" \
  --message "..." \
  --confirm
```

---

## 核心约束

1. **使用链式 `--include`**：贡献或升维时必须传入链式 `--include` 明确白名单范围，禁止盲目提交全量差异。
2. **先读取状态**：在构建并执行修改类命令前，必须先调用 `wopal ontology status` 确认当前 Downstream 与 Upstream 拓扑。
3. **分主题贡献**：不同主题的改动必须拆分为独立 PR 分批贡献，禁止合并提交。

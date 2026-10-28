---
name: ontology-evolution
description: 本体能力进化 — 持续观察、汇总、提案与落地（状态机、稀疏隔离、交付归用户）
---

# Agent 开发规则

## 1. 权威参考

- 上级规则：`.wopal/AGENTS.md`
- 技能入口：`SKILL.md`
- 命令契约：`references/commands.md`
- 设计真相源：`docs/DESIGN-evolution.md`

## 2. 架构与目录

本技能只包含协作/路由规范、参考文档与提案模板。机制——状态机命令、稀疏安全、隔离——由 wopal CLI 实现（`wopal space evo`）；技能自身不保留任何脚本层。

| 目录 | 职责 |
|---|---|
| `templates/proposal.md` | 带撰写注释的提案骨架；提案格式的唯一来源 |
| `references/` | 命令参考、能力路由说明与背景资料 |

稀疏状态**只能**通过 `wopal space` 命令族写入。在空间稀疏工作树中直接执行 `git add -A`、`git checkout` 或 `git sparse-checkout` 会破坏范围与索引的一致性。上游贡献在独立、完整检出的贡献 worktree 内使用原生 Git，规范见 `references/contribution.zh-CN.md`。

## 3. 实现规则

### 状态机

`draft -> accepted -> implementing -> validating -> archived`

这套词汇与 `dev-flow` 的（`planning / reviewing / approved / executing / verifying / done`）刻意不共享任何一词。改动状态名属于契约变更：必须同步更新本文件、`docs/DESIGN-evolution.md` 与 `references/commands.md`。

`Stage` 只由 `wopal space evo` 命令写入——永远不要手改该字段；字段找不到的提案无法推进。命令的前置条件与拒绝语义由 wopal CLI 实现。

### 记录归属

任务的 Done 记录——完成勾选、任务产出与实际触碰文件——唯一作者是主控。记录写入工作分支的提案副本（isolated = 隔离工作区副本；quick = 空间工作区副本），在验证通过后、提交前。实施 agent 不编辑提案文件的任何部分。

### 提交粒度

实施不提交。每完成一个 task 一次提交，落工作分支——该 task 的内容连同提案记录。落地主流程见 `references/landing.zh-CN.md`；具体命令行为见 `references/commands.md`。

### 缺陷立即修复

缺陷——既有、已商定的行为出了错——直接用 `wopal space evo commit` 的 **instant 模式**（不带提案名）修复，提交落在空间分支上。它不走提案生命周期：提案要提供的那道评审，对已经商定的行为早已完成。安全契约（稀疏预检、先扩范围再暂存、按名暂存）照旧适用。instant 模式是设计好的修复路径——不存在独立的 `fix` 命令；不要新增它、别名或壳。任何改变已商定行为的改动都是进化，走提案生命周期。

### 不自动交付

`space sync` 与原生 Git/GitHub PR 发布由用户逐次决定（`docs/DESIGN-evolution.md`，交付终端）。只有用户授权后才执行对应同步或发布，不擅自添加远端、推送、合并或删除。贡献命名、worktree 保留与安全收尾规范单点维护于 `references/contribution.zh-CN.md`。

## 4. 用户补充规则

（无）

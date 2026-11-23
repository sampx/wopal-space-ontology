---
description: 创建、批准、迁移或归档 Proposal
---

# Create, Approve, Migrate, or Archive a Proposal — 创建、批准、迁移或归档 Proposal

创建或维护一份业务/产品 Proposal 的完整生命周期，或对待变更的已实施 Proposal 做分流判断。本命令只是薄入口：契约由 `dev-proposal` 技能拥有。

**输入参数**: `$ARGUMENTS`

**参数说明**: 可以是 Proposal 路径、待查主题，或一句简短请求。未指明目标时，按 `docs/products/*/proposals/` 与 `projects/*/docs/proposals/` 匹配确定归属根目录；归属不清时向用户确认。

---

## Core Principles

- Proposal 记录决定，不记录进度：不设 `implementing` / `verifying` / `done` 状态，不设任务表。
- 只有用户能批准、只有用户能选择 `Delivery: direct | plan`；格式校验通过绝不等于已获批准。
- 已 `implemented/` 的决定不得原地改写：事实可原地同步，决定变化必须新建 `proposed/` 提案。

## Step 1: Load the contract

加载 `dev-proposal` 技能并按其工作流执行。目录布局、状态机与骨架规则不在本命令重复。

**Output**: 本次任务所需的契约。

## Step 2: Establish the ownership and the starting point

确定归属根目录（`docs/products/{product}/proposals/` 或 `projects/{project}/docs/proposals/`），并审计同主题的既有 Proposal。若命中 `implemented/` 记录，先判断属于纯事实同步、部分替代还是完全替代，再动笔。

**Output**: 目标路径与分流结论。

## Step 3: Do the work

按技能提供的骨架模板起草、记录批准、迁移、否决、归档或分流。

**Output**: 按请求步骤改变的 Proposal 文件。

## Step 4: Verify

```bash
python3 <dev-proposal-skill-dir>/scripts/verify-proposals.py <proposals-root> --link-scope <docs-root>
```

exit 0 才可声明完成；非零退出会逐条列出问题与修复提示。

**Output**: 校验结果。

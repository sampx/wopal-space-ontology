# enhance-session-assembly

## Metadata

- **Type**: enhance
- **Project Path**: .wopal
- **Created**: 2026-09-27
- **Stage**: draft
- **Mode**: (accept 时记录：isolated | quick)
- **Worktree**: (accept 时记录)
- **Branch**: (accept 时记录)
- **Base Commit**: (accept 时记录)
- **Final Commit**: (integrate 时记录：集成到空间分支后的提交)

## Scope Assessment

- **Complexity**: High
- **Confidence**: High — 跨项目设计已完成源码验证并经用户评审通过；实施仍须由后续项目 Plan 承载。

## Goal

在不推翻 ellamaka 静态 config / agent permission 体系的前提下，让 Wopal 在派发任务时为子 Session **增量授予**空间武器库中的 Skill/Tool 能力，并为 Rule/Skill 的 run-loop 动态上下文激活建立持久 eligibility 与 cache-safe 注入契约。该跨项目设计已于 2026-09-29 经用户评审通过并转为正式设计基线；实施仍须由各项目独立 Plan 承载。

## Technical Context

### Architecture Context

- `projects/ellamaka` 现有 `feature-plugin-config` 交付插件配置整表；CLI `refactor-space-assembly-state` 交付空间物化并从隔离环境支持 `path`/`paths`。引擎会话级权限能力本文讨论尚未定稿，`.wopal-space/plans/ellamaka/feature-ellamaka-session-permissions.md` 尚处 planning，需先与用户完成设计确认。
- 本提案不预先锁定以下未定问题，也不引用状态与边界作为已知事实；各接口与行为以最终设计为唯一依据。

## Design Decisions（正式设计基线）

1. **兼容优先**：不推翻 ellamaka 的 config / agent frontmatter / permission 体系；Session 动态能力是 additive overlay，没有新装配时 observable behavior 不变。
2. **增量语义**：`wopal_task.capabilities` 在角色 baseline 上追加能力。P2 不做 exact-set、subtract、deny。
3. **稳定 Envelope**：Skill/Tool 的 session-scoped 授权在首个模型请求前形成，Session 生命周期内冻结；复用 ellamaka 已有 `session.permission`，Wopal 私有意图使用 session metadata。
4. **统一 effective view**：Tool/Skill 的模型可见性与执行门禁都必须消费 `agent.permission + session.permission`。ellamaka 只补 Skill catalog 当前未消费 session permission 的一致性缺口。
5. **运行时激活**：Rule 不是创建时注入正文，而是只记录 eligibility；run loop 按 user intent、tool/action/path 动态 resolve。Skill 正文继续 progressive disclosure，需要的动态 guidance 与 Rule 一样在运行时追加。
6. **缓存稳定性**：动态上下文不得回写旧消息、反复改 system prompt 或 tool schema。ellamaka 提供通用 request-tail context contribution seam，wopal-plugin 以 append-only snapshot/replacement 使用它。
7. **持久与恢复**：session permission / metadata 是事实源；插件 cache 可丢弃。resume、restart、compaction 后按持久状态重新解析。
8. **插件归属**：Rule/Skill resolver、digest、格式和 Wopal capability 语义全部属于 wopal-plugin；ellamaka core 只保留通用 permission 与 context extension seam。

## Cross-project Contract

- **ellamaka**：保持既有 Session permission/API/SDK；统一 Skill visibility 与 execution 的 effective permission；增加 additive、默认空的 request-tail plugin contribution contract。
- **wopal-plugin / ontology**：定义 `wopal_task.capabilities`、编译 Session Capability Envelope、持久 metadata、运行时 Rule/Skill 激活与恢复。
- **wopal-cli**：只负责武器库 discovery/list，不进入 Session runtime。

上述设计已转为正式设计基线；本 evolution 仍保持 `draft`，仅表示尚未进入实施生命周期，不否定设计定稿状态。后续实施必须拆入各项目 Plan 并单独受理。

## In Scope

- `wopal_task.capabilities` 解析、会话装配、派发失败清理。
- 规则注入按会话装配结果过滤。
- 三插件配置消费不在此提案（另见 `refactor-plugin-config-consumption`）。

## Out of Scope

- ellamaka 的通用 Session permission 一致性与 request-tail contribution seam：由独立 ellamaka Plan 承载；本提案不直接修改 engine core。
- CLI 装配与同步、通用 paths、私有持有：另有主体。
- 面向用户的 UI/UX 与真实空间迁移落地顺序。

## Acceptance Criteria

### Agent Verification

由后续项目 Plan 按本设计基线分别定义可执行 AC；本跨项目 evolution 不重复定义项目级 AC。

### User Validation

由后续项目 Plan 按本设计基线分别定义用户验证场景。

## Implementation

不直接实施；按项目拆分 Plan 后分别实施与验证。

## Delegation Strategy

由各项目 Plan 决定；本跨项目 evolution 不直接委派实施。

## Delivery

任何交付必须由对应项目 Plan 承载并完成验收；不得以本跨项目设计文档直接作为施工入口。
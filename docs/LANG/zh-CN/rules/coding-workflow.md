---
trigger: model_decision
description: 在 coding 空间开展产品/项目研发、编写或审查文档、处理提案与 Plan、维护项目规范，或协调 dev-doc-master、space-master、dev-proposal、dev-flow 与实施/评审技能时遵循此规则。
keywords:
  - 'coding workflow'
  - 'dev-doc-master'
  - 'space-master'
  - 'dev-proposal'
  - 'dev-flow'
  - 'df-implement'
  - 'df-implement-review'
  - 'df-proposal-review'
  - 'proposal'
  - 'DESIGN'
  - 'PRD'
  - 'AGENTS.md'
  - 'cupdate-design'
  - 'cupdate-prd'
  - 'cupdate-proposal'
  - 'cupdate-agent-rules'
  - '开发流程'
  - '现状设计'
  - '设计文档'
  - '提案'
  - '工作流规则'
---

# Coding 空间技能协作与调用规则

本规则为多产品、多项目工程空间提供统一的元协作路由：不绑定单一技术栈或固定仓库路径，而是明确能力底座与流程技能的职责边界及按需调用方式，驱动任意项目建立严谨的提案、分片现状 DESIGN、分级 `AGENTS.md`、自动化测试与独立评审体系。

## 开发流程与技能分层

### 端到端开发流程（`dev-flow` 为可选中间层）

```text
PRD（产品目标，dev-doc-master）
    ├─ Issue（既有设计内的问题/任务） ───────────────┐
    └─ Proposal（重大设计决定，dev-proposal）        │
           └─ 方案评审（df-proposal-review）→ 用户批准 ┤
                                                     ▼
                          ┌──── 简单/有界任务（direct，跳过 dev-flow）────┐
                          │                                              ▼
                          └─ 复杂/多任务/需并行（可选：dev-flow 拆 Plan/Task + Graph）
                                                                         │
                                                                         ▼
                                     df-implement（写代码 + 测试 + 按需同步 DESIGN/Proposal/AGENTS）
                                                                         │
                                                                         ▼
                                 df-implement-review（独立只读评审：代码↔测试↔现状 DESIGN/Proposal）
                                                                         │
                                                                         ▼
                                                        用户验证 → 授权交付
```

### 技能分层与按需调用关系

```text
能力底座（单一规则真相源，按需调用，不重复抄写）：
  • dev-doc-master   ── 产品 PRD、产品 DESIGN、项目/模块现状 DESIGN（写作、防并行分片、实测取证、Slop Checklist）
  • space-master     ── 空间治理、项目/目录 AGENTS.md（三级归属、门禁实证、Rule Audit）与项目 README.md
  • rules/testing.md ── 自动化测试分层与 TDD 决策规则

流程技能（只管阶段推进与质量门禁，需要写/改/审文档或规范时显式调用底座）：
  • dev-proposal ──▶ df-proposal-review ──▶ [可选: dev-flow] ──▶ df-implement ──▶ df-implement-review
        │                                                            │    │               │
        └─ 正文表达参照 dev-doc-master（不动现状 DESIGN）              │    │               └─ 文档与流水账审查参照 dev-doc-master
                                                                     │    └─ 长期工程约束变更 → 调用 space-master
                                                                     └─ 对外行为/契约变化 → 调用 dev-doc-master 同步模块子 DESIGN
```

## 按场景路由与禁止越界

| 任务场景 | 首选入口 | 关键边界与排除项 |
|---|---|---|
| 编写、更新、按模块拆分或校验产品 PRD / 产品 DESIGN / 项目或模块现状 DESIGN | `dev-doc-master`（`/cupdate-prd`、`/cupdate-design`） | 项目/模块 DESIGN 仅写核实已落地的现状；产品 DESIGN 负责前瞻架构与能力图；不抢 `/cupdate-agent-rules` 或 `/cupdate-readme` |
| 创建、维护或审查业务/产品 Proposal 生命周期（`proposals/{proposed,implemented,rejected,archived}/{class}/`） | `dev-proposal`（`/cupdate-proposal`） | 管重大设计决策、备选方案、用户批准与 `Delivery: direct \| plan`；普通缺陷走 Issue；不替代现状 DESIGN 或 Plan |
| 独立方案 / Proposal / Plan 评审 | `df-proposal-review` | 实施前只读审查问题、备选方案、边界与可验收性，不代替作者改写或代用户批准 |
| 复杂任务的开发编排、direct vs Plan 判定、Plan/Task 拆分、并行写集协调与 Plan Graph | `dev-flow` | **可选中间层**：仅跨项目、多独立交付或需并行委派时启用；简单有界任务直接 `df-implement`；但已批准 Proposal 中记录的 `Delivery` 选择优先于该经验判断；不替代 Proposal 审批，不自造文档规范 |
| 具体代码实现、单元测试与交付同步 | `df-implement` + `rules/testing.md` | 不擅自篡改批准的设计边界；`direct` 交付（已批准 Proposal 或独立 Issue）默认先建 `git-worktrees` 隔离工作树再实施，除非用户明确要求改主分支或主控已指派工作树；对外行为/边界变化时按需调 `dev-doc-master` 同步模块子 DESIGN 与 Proposal，纯内部重构不动 DESIGN；交付出口跑覆盖整次交付的 `verify-docset.py --check-sync --base <delivery-base>`；留下长期工程约束时按需调 `space-master` |
| 实施后代码 / 测试 / 现状文档独立只读复核 | `df-implement-review` | 只读核查覆盖整次交付基线的完整 diff（代码↔测试↔授权范围↔现状 DESIGN/Proposal 同步），参照 `dev-doc-master` 清单抓假实现与 AI 废话；不修改代码或文档 |
| 创建、审计或维护空间/项目/文档/模块 `AGENTS.md`、项目 `README.md`，或装删外部技能 | `space-master`（`/cupdate-agent-rules`、`/cupdate-readme`） | 生成由 Harness 自动注入、不可绕过的分级 `AGENTS.md`（接通 `Doc sync` 与现状 `DESIGN` 同步的项目根规范、轻量 `docs/AGENTS.md` 护栏卡、按需模块子目录规范）；遵循父子不重复、机械门禁非空正反实证、历史 `BUSINESS_RULES.md` 只读兼容；不负责编写 PRD/DESIGN |
| 修改本体能力资产（技能、规则、Agent、命令、插件、装配） | `ontology-evolution` | **强制分流**：本体仓库修改一律直接走 `ontology-evolution`，不走 `dev-flow` 或业务 Proposal |

## 跨层硬约束

1. **按需加载，禁止复制规则**：流程技能在需要写/改/审文档或工程规范时显式调用 `dev-doc-master`、`space-master` 与 `rules/testing.md`，绝不在流程技能内抄写模板、写作细则或审计清单。
2. **一类事实一个权威归属**：PRD 管产品目标，Proposal 管重大决策及演进生命周期，Issue 管既定设计内的缺陷与任务，可选 `dev-flow`/Plan 管复杂实施拆分，Graph 管跨 Plan 依赖，项目/模块 DESIGN 管已交付现状与生效业务规则，`AGENTS.md` 管操作命令与门禁。Proposal 部分交付不冒充全部实现，单个 Plan 完成不自动将 Proposal 标记为 `implemented`。
3. **多 Agent 并行文档防冲突**：所有主 `DESIGN.md`（产品与项目）均不在头部枚举 `Sub-DESIGNs`；项目主 `DESIGN.md` 压薄为地图并默认按模块拆 `DESIGN-<module>.md`；日常模块改动与修 Bug 仅改写集内所属子文档，发现授权写集外漂移只上报主控协调，严禁越界修改共享文档；不手抄易变代码清单，以真实源码、测试与实跑结果为准，未实测项显式标明。

# <产品名称>

> **状态**: Active  
> **更新时间**: YYYY-MM-DD  
> **产品意图**: `<prd-path>`

## 0. Change Log

| 日期 | 类型 | 摘要 |
|------|------|------|
| YYYY-MM-DD | 创建 / 更新 | 一行摘要 |

## 1. Architecture Design

提供产品整体架构图（ASCII 优先）和分层表。

```text
<ASCII 架构图>
```

### Layers

| Layer | 位置 | Owner | 职责 |
|---|---|---|---|
| ... | ... | ... | ... |

## 2. Core Projects

定义每个核心子系统的角色、边界和交互契约。每子系统一节，明确职责、设计原则、对外契约。链接对应项目 DESIGN 文档。

## 3. Runtime Model

描述运行时结构、状态位置、数据归属、配置分层、生命周期行为、持久化边界。

## 4. End-to-End Flows

描述关键跨项目流程。使用编号步骤，聚焦系统行为。

## 5. Evolution Roadmap

以设计决策为单位描述产品从当前到目标态的演进。每阶段一个 Goal 加一组 D-NN 决策：

```markdown
### Phase N: 标题

> Phase doc: [phases/<product>-pN-<slug>.md]

- **Goal**: 本阶段产品能力目标（一句话，≥20 字符，禁止占位符）

- [x] D-01: <设计决策，已完成>
- [ ] D-02: <设计决策，待实现>
```

**编写要求**：
- 每 phase 必须有 **Goal** 行和 ≥1 条 D-NN 决策
- D-NN 编号每 phase 独立，`[x]` 表示已落地，`[ ]` 表示待实现
- 判断依据为设计是否已确定并实施，不是代码是否写完
- 全部 `[x]` 的 phase 即为已完成
- 本节是 `/cupdate-roadmap` 的输入源

## 6. Related Documents

只链接长期有效的产品 / 设计参考：PRD、项目 DESIGN、业务规则、架构参考、研究摘要、项目规范。
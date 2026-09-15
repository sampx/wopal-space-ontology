# GAPS — ontology Design vs Implementation Divergence

> **Status**: Active
> **Updated**: 2026-09-15
> **Design Source**: `./DESIGN.md`（差距对照的设计真相源，子设计见其 Sub-DESIGNs）
> **Companion**: 追踪 ontology 本体资产与 wopal-plugin 实现的目标态差距，逐项解决后关闭。

---

## Runtime Assembly (wopal-plugin)

### ONT-G1: Wopal 看不到空间里有哪些能力可派（P0）

**Current**: Wopal 手上没有一份"这个空间里有哪些技能、规则与外部服务"的清单。它只能知道角色默认带的那部分，因此无法把一项未在默认范围内的能力派给某个任务——即便那项能力就在空间里躺着。用户也无法询问"我现在有哪些能力可用"。

**Target**: Wopal 启动时扫描空间，得到一份完整的能力清单，并可通过一个查询工具随时取用。清单包含空间里的全部能力——包括任何角色默认都不带的那些——每项说明它是什么、做什么用、放在哪里。Wopal 据此判断某项能力能否派给当前任务，用户也能问出同样的问题。

**Design**: `./DESIGN-wopal-plugin.md` 的 Capability Assembly Module

**Exit**:
- [ ] 可查询到空间内的技能、规则与外部服务三类清单
- [ ] 清单包含角色默认不带的能力，不做过滤
- [ ] 每项说明名称、用途与所在位置
- [ ] 空间内容变化后，清单反映变化

### ONT-G2: 派发任务时无法指定要用哪些能力（P0）

**Current**: Wopal 把任务派给子代理时，只能决定用哪个角色，不能决定这个任务额外需要哪些技能或规则。结果是只能靠角色自带的配置，任务真正需要的那项能力要么用不上，要么得写进提示词里靠文字描述。

**Target**: 派发任务时可一并声明该任务需要哪些技能、规则与外部服务。子代理接手时，这些能力已经就位；没有特别声明时，子代理得到的能力与角色默认一致。能力在任务开始时确定，之后不会因为对话变长而丢失。

**Design**: `./DESIGN-wopal-plugin.md` 的 Dispatch Assembly Contract 与 Assembly Injection

**Exit**:
- [ ] 派发任务时可指定技能、规则与外部服务三类能力
- [ ] 未指定时子代理得到的能力与角色默认一致
- [ ] 被指定的能力在子代理侧确实生效，而不只是记录
- [ ] 任务执行过程中能力保持有效，不因上下文变长而失效

### ONT-G3: 规则注入不看这个会话被赋予了什么（P0）

**Current**: 一个会话会看到哪些规则，取决于它的角色和当前提示词里出现的关键词，与该会话实际被赋予的能力无关。因此给某个任务特别指定的规则不会生效，而未赋予的规则可能照常注入。

**Target**: 规则注入以该会话实际被赋予的能力为准，只注入被赋予的规则，提示词匹配与去重行为保持原有表现。给任务特别指定的规则在该会话生效，未赋予的规则不进入。

**Design**: `./DESIGN-wopal-plugin.md` 的 Rules Module 与 Assembly Injection

**Exit**:
- [ ] 未赋予该会话的规则不出现在它的系统提示词中
- [ ] 特别为该会话指定的规则确实生效
- [ ] 上下文重建后仍按该会话被赋予的能力渲染
- [ ] 原有的关键词匹配与去重表现不变

---

## Reference Documents

| 文档 | 说明 |
|------|------|
| `./DESIGN-assembly.md` | 装配模型设计 |
| `./DESIGN-capabilities.md` | 能力体系设计 |
| `./DESIGN-evolution.md` | 进化闭环设计 |
| `./DESIGN-wopal-plugin.md` | wopal-plugin 设计 |

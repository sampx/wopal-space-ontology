# GAPS — ontology Design vs Implementation Divergence

> **Status**: Active
> **Updated**: 2026-09-27
> **Design Source**: `./DESIGN.md`（差距对照的设计真相源，子设计见其 Sub-DESIGNs）
> **Companion**: 追踪 ontology 本体资产与 wopal-plugin 实现的目标态差距，逐项解决后关闭。

---

## Runtime Assembly (wopal-plugin)

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

## Assembly Carriers

### ONT-G6: 类型装配载体与空间装配状态契约不一致（P0）

**Current**: coding 装配单还没有把通用 `dsh` 目录列入 `paths`；空间根模板和本体进化提案模板尚不能准确表达单文件状态、私有内容保盘与新资产归属。Agent 执行能力进化时缺少一次声明资产装配归属的固定槽位。

**Target**: 类型装配单使用可严格解析的引用并声明实际通用目录；空间根模板保盘私有内容而不忽略受跟踪的装配状态；进化提案对新增整项资产声明 `type-default` 或 `space-local`，技能中的维护命令语义与 CLI 自动状态提交一致。

**Design**: `./DESIGN-assembly.md`（引用、状态与 Generic Path Assembly）；`./DESIGN-evolution.md`（进化命令边界）。余下部分由本体提案 `enhance-assembly-carriers`（`paths`、根模板、Assembly Intent、技能措辞）承载。

**Exit**:
- [ ] coding 装配单引用与目标资产形态一致，`paths` 声明的目录能在隔离空间完整物化
- [ ] 根模板不忽略 `space-meta.json` 与用户文档，私有内容保盘路径被精确忽略
- [ ] 新整项资产在提案模板有装配归属槽位，维护技能不误称本地选择零根仓库提交

---

## Reference Documents

| 文档 | 说明 |
|------|------|
| `./DESIGN-assembly.md` | 装配模型设计 |
| `./DESIGN-capabilities.md` | 能力体系设计 |
| `./DESIGN-evolution.md` | 进化闭环设计 |
| `./DESIGN-wopal-plugin.md` | wopal-plugin 设计 |

# 深层蒸馏功能设计方案 v2

> **研究日期**：2026-04-08
> **Issue**：#49
> **状态**：设计方案

---

## 一、需求分析

### 1.1 Issue #49 核心需求

基于 Phase 1 积累的提取状态数据，实现跨 session 级别的深度分析：

| 功能 | 说明 | 优先级 |
|------|------|--------|
| **批量蒸馏** | 批量处理多个 session 的待蒸馏记忆 | P0 |
| **跨 session 模式挖掘** | 发现跨会话的重复模式、高频概念 | P1 |
| **记忆冲突检测** | 识别矛盾的记忆条目并标记 | P1 |
| **Session 清理管理** | 清理过期/冗余的 session 状态文件 | P2 |
| **记忆质量评估** | 评估记忆质量，自动降权低价值条目 | P1 |

**触发方式**：手动触发 `/distill --deep` 或 `wopal memory deep-distill`

**前置条件**：memories 表规模达数百条

---

## 二、研究资料分析

### 2.1 memory-lancedb-pro 核心特性

| 特性 | 实现方式 | 可借鉴点 |
|------|---------|----------|
| **6 类记忆提取** | LLM-powered：profile / preferences / entities / events / cases / patterns | 分类体系设计 |
| **L0/L1/L2 分层存储** | L0 摘要（索引）→ L1 概述 → L2 完整内容 | 渐进式披露 |
| **Weibull 衰减引擎** | `composite = recency + frequency + intrinsic` | 记忆生命周期管理 |
| **三层 Tier 管理** | Core ↔ Working ↔ Peripheral 自动升降级 | 质量评估模型 |
| **冲突检测** | `support` / `contextualize` / `contradict` / `supersede` 决策 | 冲突处理策略 |
| **两阶段去重** | 向量预过滤（≥0.7 相似度）+ LLM 语义决策 | 去重流水线 |

### 2.2 OpenSpace 进化机制

| 特性 | 实现方式 | 可借鉴点 |
|------|---------|----------|
| **ExecutionAnalyzer** | 独立 LLM Agent 分析执行轨迹 | 深度分析模式 |
| **质量追踪** | selections / applied / completions / fallbacks 四级计数器 | 质量指标体系 |
| **三种进化触发** | Post-Analysis / Tool Degradation / Metric Monitor | 触发策略设计 |
| **防循环机制** | 数据驱动 + 状态标记 | 自动化安全性 |

### 2.3 当前实现分析

`wopal-plugin/src/memory/` 已实现：

| 组件 | 文件 | 功能 |
|------|------|------|
| DistillEngine | `distill.ts` | 单层 body 蒸馏、两阶段去重 |
| MemoryStore | `store.ts` | LanceDB 存储 |
| MemoryRetriever | `retriever.ts` | 语义检索 |
| SessionContext | `session-context.ts` | 会话状态管理 |

**当前局限**：
- 仅支持单 session 蒸馏
- 无跨 session 分析能力
- 无记忆质量评估
- 无清理机制

---

## 三、设计方案

### 3.1 架构概览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Deep Distillation System                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                      CLI Entry Point                                     ││
│  │                   wopal memory deep-distill                              ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                     │                                        │
│                                     ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                      Batch Processor                                     ││
│  │  • Session Queue                                                         ││
│  │  • Parallelism Control                                                   ││
│  │  • Rate Limit                                                            ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                     │                                        │
│                                     ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                      Analysis Pipeline                                   ││
│  │  • Pattern Mining                                                        ││
│  │  • Conflict Detection                                                    ││
│  │  • Quality Evaluation                                                    ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                     │                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        Storage Layer                                   │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────────┐│  │
│  │  │  LanceDB    │  │   SQLite    │  │      File System               ││  │
│  │  │  (memories) │  │  (metrics)  │  │  ~/.wopal/memory/state/*.json  ││  │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────────────┘│  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 核心组件设计

#### 3.2.1 批量蒸馏引擎

**文件**：`memory/batch-distill.ts`

**职责**：批量处理多个 session 的待蒸馏记忆

```typescript
interface BatchDistillConfig {
  maxParallelism: number;        // 最大并行数（默认 3）
  batchSize: number;             // 每批处理 session 数（默认 10）
  skipDistilled: boolean;        // 跳过已蒸馏 session（默认 true）
  minSessionLength: number;      // 最小 session 消息数（默认 5）
}

interface BatchDistillResult {
  processedSessions: number;
  createdMemories: number;
  mergedMemories: number;
  skippedSessions: number;
  errors: Array<{ sessionID: string; error: string }>;
}
```

**流程**：
1. 扫描 `~/.wopal/memory/state/` 下所有 session 状态文件
2. 过滤已蒸馏或消息数不足的 session
3. 按批次并行调用 `DistillEngine.distill()`
4. 汇总结果并记录到日志

#### 3.2.2 跨 Session 模式挖掘器

**文件**：`memory/pattern-miner.ts`

**职责**：发现跨会话的重复模式、高频概念

```typescript
interface PatternMiningResult {
  frequentConcepts: Array<{
    concept: string;
    count: number;
    sessions: string[];
    category: MemoryCategory;
  }>;
  duplicatePatterns: Array<{
    pattern: string;
    occurrences: number;
    memoryIds: string[];
  }>;
  crossSessionThemes: Array<{
    theme: string;
    relatedConcepts: string[];
    sessionCount: number;
  }>;
}
```

**算法**：
1. 从 LanceDB 提取所有 `metadata.concepts` 字段
2. 计算概念频率（TF）和跨 session 分布（IDF）
3. 识别高频概念（count ≥ 3 且跨 ≥ 2 个 session）
4. 聚类相似概念，发现主题

**输出**：
- 高频概念列表（供 Wopal 参考）
- 重复模式标记（候选合并）
- 跨会话主题（指导记忆注入优先级）

#### 3.2.3 记忆冲突检测器

**文件**：`memory/conflict-detector.ts`

**职责**：识别矛盾的记忆条目并标记

```typescript
interface ConflictPair {
  memoryA: Memory;
  memoryB: Memory;
  conflictType: "contradict" | "supersede" | "contextualize";
  severity: "high" | "medium" | "low";
  reason: string;
  resolution: "auto" | "manual";
}

interface ConflictDetectionResult {
  conflicts: ConflictPair[];
  autoResolved: number;
  manualRequired: number;
}
```

**检测策略**：

| 冲突类型 | 检测条件 | 处理方式 |
|----------|---------|----------|
| **contradict** | 同概念相反陈述 | 标记为 manual，提示用户 |
| **supersede** | 同实体新旧信息（有时间戳） | 自动保留新条目，标记旧条目 `invalidated_at` |
| **contextualize** | 同概念不同语境 | 标记 `contexts` 元数据，并存 |

**实现**：
1. 按概念聚类记忆（`metadata.concepts`）
2. 对同概念记忆做语义相似度 + LLM 判断
3. 根据 LLM 返回的 `conflict_type` 分类
4. 自动处理 `supersede`，其他标记待人工确认

#### 3.2.4 记忆质量评估器

**文件**：`memory/quality-evaluator.ts`

**职责**：评估记忆质量，自动降权低价值条目

```typescript
interface QualityMetrics {
  recency: number;           // 0-1，基于 Weibull 衰减
  frequency: number;         // 0-1，访问频率
  intrinsic: number;         // importance × confidence
  composite: number;         // 加权综合分
}

interface QualityEvaluationResult {
  evaluated: number;
  promoted: number;          // 升级到 Core
  demoted: number;           // 降级到 Peripheral
  stale: number;             // 标记为过期
}
```

**Tier 管理**（借鉴 memory-lancedb-pro）：

| Tier | 阈值 | 行为 |
|------|------|------|
| **Core** | `access_count ≥ 10` 且 `composite ≥ 0.8` | 最高优先级注入 |
| **Working** | 默认 | 正常注入 |
| **Peripheral** | `composite < 0.3` 或 `age > 90 days` | 低优先级，候选清理 |

**Weibull 衰减公式**：
```
effective_half_life = base_half_life * exp(importance_modulation * importance)
recency = exp(-lambda * days_since^beta)
composite = 0.4 * recency + 0.3 * frequency + 0.3 * intrinsic
```

**参数**（可配置）：
- `base_half_life`: 30 天
- `importance_modulation`: 1.5
- `beta_core`: 0.8（Core 记忆衰减更慢）
- `beta_peripheral`: 1.3（Peripheral 记忆衰减更快）

#### 3.2.5 Session 清理管理器

**文件**：`memory/session-cleaner.ts`

**职责**：清理过期/冗余的 session 状态文件

```typescript
interface CleanupConfig {
  maxAge: number;            // 最大保留天数（默认 90）
  minMemories: number;       // 最少记忆数才保留（默认 1）
  dryRun: boolean;           // 仅报告不执行（默认 false）
}

interface CleanupResult {
  scanned: number;
  cleaned: number;
  freedBytes: number;
  keptSessions: string[];
}
```

**清理策略**：

| 条件 | 动作 |
|------|------|
| `age > max_age` 且 `memories_created = 0` | 删除状态文件 |
| `age > max_age * 1.5` | 标记为 `archived`，移入归档目录 |
| `duplicate session title` | 保留最新的，清理旧的 |

---

### 3.3 CLI 命令设计

#### 3.3.1 主命令

```bash
# 手动触发深度蒸馏（执行全部步骤）
wopal memory deep-distill

# 仅执行特定步骤
wopal memory deep-distill --step batch-distill
wopal memory deep-distill --step pattern-mining
wopal memory deep-distill --step conflict-detect
wopal memory deep-distill --step quality-evaluate
wopal memory deep-distill --step cleanup

# 并行度和批次大小
wopal memory deep-distill --parallel 5 --batch 20

# Dry run（仅报告不执行）
wopal memory deep-distill --dry-run
```

#### 3.3.2 报告查看

```bash
# 查看最近的深度蒸馏报告
wopal memory report latest

# 查看模式挖掘结果
wopal memory report patterns

# 查看冲突列表
wopal memory report conflicts --unresolved

# 查看质量评估结果
wopal memory report quality
```

---

### 3.4 执行流程

```
wopal memory deep-distill
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Deep Distill Pipeline                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Step 1: Batch Distill                                          │
│  ├─ 扫描未蒸馏 session                                          │
│  ├─ 并行蒸馏（max 3 parallel）                                   │
│  └─ 写入结果日志                                                │
│                                                                  │
│  Step 2: Pattern Mining                                         │
│  ├─ 提取高频概念                                                │
│  ├─ 发现跨 session 主题                                         │
│  └─ 生成报告：~/.wopal/memory/reports/patterns-{date}.json      │
│                                                                  │
│  Step 3: Conflict Detection                                     │
│  ├─ 按概念聚类                                                  │
│  ├─ LLM 判断冲突类型                                            │
│  ├─ 自动解决 supersede                                          │
│  └─ 标记 manual 冲突                                            │
│                                                                  │
│  Step 4: Quality Evaluation                                     │
│  ├─ 计算 composite score                                        │
│  ├─ Tier 升降级                                                 │
│  └─ 标记 stale 记忆                                             │
│                                                                  │
│  Step 5: Cleanup                                                │
│  ├─ 清理过期 session 状态                                       │
│  └─ 归档旧 session                                              │
│                                                                  │
│  Step 6: Report                                                 │
│  └─ 生成摘要报告                                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.5 失败恢复

**状态追踪**：`~/.wopal/memory/deep-distill-state.json`

```typescript
interface PipelineState {
  lastRun: string;           // ISO 时间戳
  status: "success" | "failed" | "running";
  currentStep: string;
  error?: string;
  metrics: {
    sessionsProcessed: number;
    memoriesCreated: number;
    conflictsResolved: number;
    cleanedSessions: number;
  };
}
```

**恢复机制**：
- 检测到上次运行未完成 → 从断点继续
- 超时（> 30 分钟）→ 标记 failed，下次重试

---

### 3.6 数据结构扩展

#### 3.6.1 Memory 元数据扩展

```typescript
interface MemoryMetadata {
  concepts: string[];           // 已有
  tier?: "core" | "working" | "peripheral";
  access_count?: number;
  last_accessed_at?: number;
  confidence?: number;          // 0-1
  contexts?: string[];          // 适用语境标签
  invalidated_at?: number;      // 被取代时间
  superseded_by?: string;       // 取代它的 memory ID
  support_info?: {              // 支持统计
    [context: string]: {
      support: number;
      contradict: number;
    };
  };
}
```

#### 3.6.2 SessionContext 扩展

```typescript
interface SessionContext {
  sessionID: string;
  title: string | null;
  distill?: {
    messageCount: number;
    extractedAt: string;
    depth: "shallow" | "deep";
    patterns?: string[];          // 发现的模式
    conflicts?: string[];         // 冲突标记
  };
  summary?: {
    text: string;
    messageCount: number;
    generatedAt: string;
  };
  archived?: boolean;             // 是否已归档
}
```

#### 3.6.3 新增：PipelineReport

```typescript
interface PipelineReport {
  runId: string;
  timestamp: string;
  duration: number;               // 毫秒
  steps: {
    name: string;
    status: "success" | "failed" | "skipped";
    duration: number;
    metrics: Record<string, number>;
  }[];
  summary: {
    sessionsProcessed: number;
    memoriesCreated: number;
    memoriesMerged: number;
    conflictsDetected: number;
    conflictsResolved: number;
    qualityPromoted: number;
    qualityDemoted: number;
    sessionsCleaned: number;
  };
  errors: Array<{ step: string; error: string }>;
}
```

---

## 四、实现计划

### 4.1 Phase 划分

| Phase | 内容 | 预估工作量 |
|-------|------|-----------|
| **Phase 1** | 批量蒸馏引擎 | 2-3 天 |
| **Phase 2** | 模式挖掘 + 冲突检测 | 3-4 天 |
| **Phase 3** | 质量评估 + Tier 管理 | 2-3 天 |
| **Phase 4** | Session 清理 + 报告系统 | 1-2 天 |
| **Phase 5** | 集成测试 + 文档 | 1-2 天 |

### 4.2 Phase 1 详细任务

**目标**：实现批量蒸馏引擎

**任务清单**：
- [ ] 创建 `memory/batch-distill.ts`
- [ ] 实现 `BatchDistillEngine` 类
- [ ] 添加 `wopal memory deep-distill` CLI 命令
- [ ] 实现 PipelineState 持久化
- [ ] 编写单元测试

**验收标准**：
- [ ] 批量蒸馏能并行处理多个 session
- [ ] 失败后能从断点恢复

### 4.3 Phase 2 详细任务

**目标**：实现模式挖掘和冲突检测

**任务清单**：
- [ ] 创建 `memory/pattern-miner.ts`
- [ ] 实现概念频率统计
- [ ] 实现跨 session 主题发现
- [ ] 创建 `memory/conflict-detector.ts`
- [ ] 实现冲突类型分类（contradict/supersede/contextualize）
- [ ] 实现 supersede 自动解决
- [ ] 扩展 MemoryMetadata 结构
- [ ] 编写单元测试

**验收标准**：
- [ ] 能发现高频概念和重复模式
- [ ] 能检测并分类记忆冲突
- [ ] supersede 冲突能自动解决

### 4.4 Phase 3 详细任务

**目标**：实现质量评估和 Tier 管理

**任务清单**：
- [ ] 创建 `memory/quality-evaluator.ts`
- [ ] 实现 Weibull 衰减计算
- [ ] 实现 Tier 升降级逻辑
- [ ] 扩展 MemoryStore 支持质量查询
- [ ] 在注入逻辑中加入 Tier 优先级
- [ ] 编写单元测试

**验收标准**：
- [ ] 能计算 composite score
- [ ] 能自动升降级 Tier
- [ ] 注入时 Core 记忆优先级最高

### 4.5 Phase 4 详细任务

**目标**：实现清理和报告系统

**任务清单**：
- [ ] 创建 `memory/session-cleaner.ts`
- [ ] 实现过期 session 清理
- [ ] 实现归档机制
- [ ] 创建 `memory/reporter.ts`
- [ ] 实现 PipelineReport 生成
- [ ] 添加 `wopal memory report` CLI 命令
- [ ] 编写单元测试

**验收标准**：
- [ ] 能清理过期 session 状态文件
- [ ] 能生成完整报告
- [ ] 报告可查询历史记录

---

## 五、配置设计

### 5.1 配置文件

**位置**：`~/.wopal/memory/deep-distill-config.json`

```json
{
  "batchDistill": {
    "maxParallelism": 3,
    "batchSize": 10,
    "skipDistilled": true,
    "minSessionLength": 5
  },
  "quality": {
    "baseHalfLife": 30,
    "importanceModulation": 1.5,
    "betaCore": 0.8,
    "betaWorking": 1.0,
    "betaPeripheral": 1.3,
    "coreThreshold": 10,
    "peripheralAgeDays": 90
  },
  "cleanup": {
    "maxAge": 90,
    "minMemories": 1,
    "archiveThreshold": 135
  },
  "conflict": {
    "autoResolveSupersede": true,
    "similarityThreshold": 0.7
  }
}
```

### 5.2 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `WOPAL_DEEP_DISTILL_PARALLEL` | 批量蒸馏并行度 | `3` |

---

## 六、风险与缓解

### 6.1 风险分析

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| **LLM 调用成本过高** | 高 | 中 | 批量处理时复用 embedding，缓存 LLM 结果 |
| **自动冲突解决误判** | 中 | 中 | supersede 仅在有时间戳时自动解决，其他标记 manual |
| **大量 session 导致处理超时** | 中 | 中 | 分批处理，支持断点续传 |
| **质量评估参数不合理** | 低 | 中 | 可配置参数，提供调优指南 |

### 6.2 安全边界

- **禁止自动删除记忆**：仅标记为 stale，需人工确认后删除
- **禁止修改用户确认的记忆**：标记为 `user_confirmed` 的记忆不受自动降权影响
- **限制 LLM 调用频率**：每分钟最多 30 次，超出则暂停

---

## 七、与现有系统集成

### 7.1 与 wopal-plugin 集成

```
wopal-plugin
    │
    ├── hooks/system-transform.ts
    │   └── 注入时读取 Memory.tier，Core 优先
    │
    ├── memory/injector.ts
    │   └── buildEnrichedQuery() 读取 SessionContext.summary
    │
    └── memory/store.ts
        └── 新增 query() 方法支持 tier 过滤
```

### 7.2 与 distill_session 工具集成

```
distill_session (手动)
    │
    ├── 写入 LanceDB
    │
    ├── 更新 SessionContext
    │
    └── 触发增量模式挖掘（可选）
```

### 7.3 与 context_manage 工具集成

```
context_manage summary
    │
    ├── 生成摘要
    │
    └── 写入 SessionContext.summary
        │
        └── 被 buildEnrichedQuery() 读取，增强检索
```

---

## 八、验收标准

### 8.1 功能验收

- [ ] 批量蒸馏能处理 100+ session 无阻塞
- [ ] 模式挖掘能发现高频概念（count ≥ 3）
- [ ] 冲突检测能识别 contradict/supersede/contextualize
- [ ] 质量评估能正确升降级 Tier
- [ ] Session 清理能安全删除过期文件
- [ ] 失败后能从断点恢复

### 8.2 性能验收

| 指标 | 目标 |
|------|------|
| 批量蒸馏吞吐量 | ≥ 10 session/min |
| 模式挖掘延迟 | < 30s（1000 条记忆） |
| 冲突检测延迟 | < 60s（500 对候选） |
| 质量评估延迟 | < 10s（全量记忆） |

### 8.3 质量验收

- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 无 P0/P1 级 Bug
- [ ] 所有配置项有文档说明

---

## 九、后续优化方向

### 9.1 近期（1-2 个月）

- **增量模式挖掘**：新记忆入库时实时更新模式
- **可视化仪表盘**：记忆质量趋势图

### 9.2 中期（3-6 个月）

- **记忆合并建议**：基于模式挖掘自动建议合并
- **多语言支持**：支持中英文混合概念提取

### 9.3 远期（6+ 个月）

- **主动记忆注入**：根据任务上下文主动注入相关记忆
- **记忆遗忘机制**：自动清理长期未访问的 Peripheral 记忆
- **跨空间记忆共享**：支持多 WopalSpace 实例间同步记忆

---

## 十、参考资料

| 文档 | 链接 |
|------|------|
| memory-lancedb-pro 架构 | `labs/research/memory-lancedb-pro/README.md` |
| OpenSpace 技能进化机制 | `docs/research/openspace/openspace-skill-evolution-mechanism.md` |
| claude-mem 文档 | `labs/research/claude-mem/repo/README.md` |
| 当前记忆系统实现 | `projects/ontology/agents/wopal/plugins/wopal-plugin/src/memory/` |
| WopalSpace PRD | `docs/products/wopal-space/PRD-wopalspace.md` |

---

## 附录：关键代码示例

### A. 批量蒸馏引擎核心

```typescript
// memory/batch-distill.ts
export class BatchDistillEngine {
  constructor(
    private store: MemoryStore,
    private embedder: EmbeddingClient,
    private llm: DistillLLMClient,
    private config: BatchDistillConfig
  ) {}

  async run(): Promise<BatchDistillResult> {
    const sessions = await this.scanPendingSessions();
    const batches = this.createBatches(sessions);

    const results = await Promise.all(
      batches.map(batch => this.processBatch(batch))
    );

    return this.aggregateResults(results);
  }

  private async processBatch(
    sessions: string[]
  ): Promise<BatchDistillResult> {
    // 使用信号量控制并行度
    const semaphore = new Semaphore(this.config.maxParallelism);

    const results = await Promise.all(
      sessions.map(sessionID =>
        semaphore.run(() => this.distillSession(sessionID))
      )
    );

    return this.aggregateResults(results);
  }
}
```

### B. 质量评估器核心

```typescript
// memory/quality-evaluator.ts
export class QualityEvaluator {
  constructor(private config: QualityConfig) {}

  evaluate(memory: Memory): QualityMetrics {
    const recency = this.computeRecency(memory);
    const frequency = this.computeFrequency(memory);
    const intrinsic = this.computeIntrinsic(memory);
    const composite = this.computeComposite(recency, frequency, intrinsic);

    return { recency, frequency, intrinsic, composite };
  }

  private computeRecency(memory: Memory): number {
    const daysSince = this.daysSince(memory.last_accessed_at ?? memory.timestamp);
    const importance = memory.importance ?? 0.5;
    const effectiveHL = this.config.baseHalfLife *
      Math.exp(this.config.importanceModulation * importance);
    const lambda = Math.LN2 / effectiveHL;
    const beta = this.getBeta(memory.tier);

    return Math.exp(-lambda * Math.pow(daysSince, beta));
  }

  private getBeta(tier?: MemoryTier): number {
    switch (tier) {
      case "core": return this.config.betaCore;
      case "peripheral": return this.config.betaPeripheral;
      default: return this.config.betaWorking;
    }
  }
}
```

### C. 冲突检测器核心

```typescript
// memory/conflict-detector.ts
export class ConflictDetector {
  constructor(
    private store: MemoryStore,
    private llm: DistillLLMClient
  ) {}

  async detect(): Promise<ConflictDetectionResult> {
    // 1. 按概念聚类
    const clusters = await this.clusterByConcept();

    // 2. 对每个聚类检测冲突
    const conflicts: ConflictPair[] = [];
    for (const cluster of clusters) {
      const pairs = await this.detectConflictsInCluster(cluster);
      conflicts.push(...pairs);
    }

    // 3. 自动解决 supersede
    const autoResolved = await this.autoResolveSupersede(conflicts);

    return {
      conflicts,
      autoResolved,
      manualRequired: conflicts.length - autoResolved
    };
  }

  private async detectConflictsInCluster(
    memories: Memory[]
  ): Promise<ConflictPair[]> {
    const conflicts: ConflictPair[] = [];

    for (let i = 0; i < memories.length; i++) {
      for (let j = i + 1; j < memories.length; j++) {
        const conflict = await this.checkConflict(memories[i], memories[j]);
        if (conflict) conflicts.push(conflict);
      }
    }

    return conflicts;
  }
}
```
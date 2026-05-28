# Agent 记忆技能调研报告

> **日期**: 2026-03-28（v5：对齐最终方案 — 手动蒸馏 + SDK 查询）
> **目的**: 调研外部 AI Agent 记忆技能/插件 + 轻量级向量数据库，评估适配 WopalSpace 的潜力
> **范围**: Claude Code / OpenCode / OpenClaw 生态 + 嵌入式向量数据库 + OpenCode Plugin Hook 能力边界

---

## 一、调研概览

从 4 个维度（通用搜索、Claude Code 生态、Cursor 生态、GitHub 仓库）搜索了 40+ 结果，深入抓取 14 个项目源码，最终聚焦 3 个 Tier 1 项目深度分析。

### 源码存放位置

| 项目 | 本地路径 |
|------|----------|
| Acontext | `labs/research/acontext/repo/` |
| claude-mem | `labs/research/claude-mem/repo/` |
| claude-mem-opencode | `labs/research/claude-mem-opencode/repo/` |

---

## 二、项目分级评估

### Tier 1: 值得深入研究

| 项目 | Stars | 定位 | 关键特点 |
|------|-------|------|----------|
| **[Acontext](https://github.com/memodb-io/Acontext)** | 3.2k | "Skill is Memory, Memory is Skill" | 云端 LLM 蒸馏会话 → 生成 SKILL.md → 同步回本地。Markdown 原生、无 embedding、渐进式披露。Go API + Python Core + TS SDK |
| **[claude-mem](https://github.com/thedotmack/claude-mem)** | 40.8k | 自动捕获 + AI 压缩 + 语义搜索 | 5 个 Claude Code Hook 自动捕获 → Bun Worker AI 压缩 → SQLite + Chroma 向量存储。完全本地，3 层渐进式检索 |
| **[DSP](https://github.com/k-kolomeitsev/data-structure-protocol)** | 33 | 图结构代码记忆 | UID 标记代码实体 → 依赖图 → 图遍历替代全仓库扫描。Git-native，支持影响分析。bootstrap 成本高 |
| **[memory-lancedb-pro](https://github.com/CortexReach/memory-lancedb-pro)** | 3.6k | OpenClaw 记忆插件（LanceDB） | LanceDB 单库（向量+BM25 FTS）+ Weibull 衰减 + Smart Extraction（6 类分类 L0/L1/L2）+ Cross-encoder Rerank + 三级晋升（Core/Working/Peripheral） |

### Tier 2: 有参考价值

| 项目 | Stars | 特点 | 参考点 |
|------|-------|------|--------|
| **[hanfang/claude-memory-skill](https://github.com/hanfang/claude-memory-skill)** | 5 | 层级文件记忆：core.md(摘要+指针) + topics/(详情)，后台 agent 自动读写 | grep-based 确定性检索，与 MEMORY.md 体系最接近 |
| **[memory-systems](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering)** (14.4k repo) | — | 短期/长期/图记忆架构设计教学型技能 | 含 Cognee、MemGPT 等参考文档 |
| **[PowerMem](https://github.com/oceanbase/powermem)** | 583 | OceanBase 出品，向量+全文+图三混合存储，艾宾浩斯遗忘曲线 | Benchmark: LOCOMO 78.7% vs 全上下文 52.9%，但需数据库 |
| **[mem0](https://github.com/mem0ai/mem0)** | 25k+ | 通用 Agent 记忆层 SDK | 广泛引用，但定位 SDK 库非技能，更适合嵌入产品 |

### Tier 3: 不适配（偏云端/SaaS）

| 项目 | 原因 |
|------|------|
| **[HPKV Memory MCP](https://github.com/hpkv-io/memory-mcp-server)** | 云端 MCP Server (SaaS)，需注册账号 |
| **[CogMemAI MCP](https://github.com/hifriendbot/cogmemai-mcp)** | 云端持久记忆 |

---

## 三、深度分析

### 3.1 Acontext

**理念**: "Skill is Memory, Memory is Skill" — 记忆以 SKILL.md 格式存储，可读可编辑可分享。

- Session messages → LLM 蒸馏 → 更新/创建 SKILL.md 文件
- 下次会话 → agent 通过工具按需获取技能内容（渐进式披露）
- 无 embedding、无语义搜索、无 API lock-in

**架构**:
```
Claude Code Plugin (TypeScript)
  ├── hooks: session-start, post-tool-use, stop, notification
  ├── hook-handler.ts: 统一入口，读 transcript JSONL
  ├── bridge.ts: AcontextBridge — 与云端 API 通信
  ├── config.ts: 配置管理
  └── mcp-server.ts: 5 个 MCP tools (search/get/history/stats/learn)
        ↓ HTTPS
云端服务
  ├── API (Go + Gin + GORM/PostgreSQL + Redis + RabbitMQ + S3)
  └── Core (Python + FastAPI + SQLAlchemy/pgvector + LLM)
        ↓ LLM 蒸馏
  Learning Space → 技能文件 → 同步回 ~/.claude/skills/
```

**关键源码**:

| 文件 | 路径 | 说明 |
|------|------|------|
| Hook 入口 | `src/packages/claude-code/src/hook-handler.ts` | 4 个 hook handler，统一 stdin JSON → Bridge 调用 |
| Bridge | `src/packages/claude-code/src/bridge.ts` | 核心桥接：session 管理、消息捕获、学习触发、技能同步 |
| Config | `src/packages/claude-code/src/config.ts` | 配置：API key、base URL、autoCapture/Learn、minTurns |
| MCP Server | `src/packages/claude-code/src/mcp-server.ts` | 5 个 MCP tool 定义 |
| Hooks 定义 | `src/packages/claude-code/plugin/hooks/hooks.json` | Claude Code hooks 配置 |
| 安装器技能 | `landingpage/public/SKILL.md` | Agent 可读的安装指南 |

**Hook 流程**:
```
session-start:
  clearSessionState() → ensureSession() → saveSessionState()
  → fire-and-forget: syncSkillsToLocal()

post-tool-use:
  readStdin() → parseStdinJson() → acquireLock()
  → readTranscriptMessages(transcript_path) → mergeConsecutiveMessages()
  → storeMessages(sessionId, merged, lastIdx) → incrementTurnCount()
  → if turnCount >= minTurnsForLearn: learnFromSession()
  → releaseLock()

stop:
  loadSessionState() → 最终 transcript 捕获
  → 无条件触发 learnFromSession()
  → learn 成功后 syncSkillsToLocal()
```

**关键设计**:
- **增量 transcript 读取**: `lastProcessedIndex` + `mergeConsecutiveMessages()` 避免重复
- **文件锁防并发**: `.hook-lock` 目录，post-tool-use 非阻塞跳过，stop 阻塞重试
- **技能同步**: manifest (`.manifest.json`) 30 分钟缓存 + `updated_at` 增量更新 + name collision 检测
- **自动学习触发**: `minTurnsForLearn` (默认 4 轮)，Stop 时无条件触发

---

### 3.2 claude-mem + claude-mem-opencode

#### 3.2.1 claude-mem（Claude Code 原版）

**定位**: Claude Code 插件，自动捕获编码会话 → AI 压缩 → 语义搜索 → 跨会话注入。

**架构**:
```
5 Lifecycle Hooks (TypeScript → ESM)
  ├── SessionStart
  ├── UserPromptSubmit
  ├── PostToolUse
  ├── Summary
  └── SessionEnd
        ↓
Worker Service (Express :37777, Bun 管理)
  ├── AI 压缩 (Claude Agent SDK)
  ├── SQLite3 (~/.claude-mem/claude-mem.db)
  ├── Chroma 向量数据库 (~/.claude-mem/chroma/)
  ├── FTS5 全文搜索
  └── Web Viewer UI (http://localhost:37777)
        ↓
mem-search Skill (MCP tools)
  ├── search → 索引 (~75 tokens/result)
  ├── timeline → 上下文
  └── get_observations → 详情 (~500-1000 tokens)
```

**关键特性**:
- 完全本地运行，零外部服务依赖
- `<private>` 标签隐私过滤（edge processing）
- 3 层渐进式检索：~10x token 效率
- Web Viewer UI 实时查看记忆流
- `~/.claude-mem/settings.json` 配置
- AGPL-3.0 许可证

**关键源码**:
| 文件 | 说明 |
|------|------|
| `plugin/hooks/hooks.json` | 5 个 Hook 配置 |
| `plugin/CLAUDE.md` | Claude 开发指南（架构、隐私、构建） |
| `plugin/skills/mem-search/SKILL.md` | 搜索技能（3 层工作流） |
| `plugin/skills/make-plan/SKILL.md` | 规划技能 |
| `plugin/skills/do/SKILL.md` | 执行技能 |

#### 3.2.2 claude-mem-opencode（OpenCode 适配层）

**定位**: OpenCode 插件，桥接 OpenCode 事件 → claude-mem Worker HTTP API。

**架构**:
```
plugin.ts (OpenCode 插件入口, 27 行)
  └── ClaudeMemIntegration (门面类)
        ├── WorkerClient        — HTTP fetch 封装, 7 个端点
        ├── EventListeners       — Bus.subscribe() 注册事件监听
        ├── ContextInjector      — 获取历史上下文（未真正集成）
        ├── SessionMapper        — OpenCode ID ↔ claude-mem ID 映射 (内存 Map)
        ├── ProjectNameExtractor — cwd → 项目名
        └── PrivacyTagStripper   — 剥离 <private> 和 <claude-mem-context>
```

**数据流**:
```
Session.Event.Created
  → workerClient.initSession({contentSessionId, project, prompt})
  → 返回 {sessionDbId, promptNumber}
  → sessionMapper.map()

MessageV2.Event.PartUpdated (type=tool_call only)
  → privacyStripper.stripFromJson(toolArgs) / stripFromText(toolResult)
  → workerClient.addObservation({sessionDbId, promptNumber, toolName, toolInput, toolOutput, cwd, timestamp})

Session.Event.Updated (info.time.archived)
  → workerClient.completeSession(claudeMemSessionId)
  → sessionMapper.unmap()
```

**WorkerClient API 端点**:

| 方法 | HTTP | 用途 |
|------|------|------|
| `checkHealth()` | `GET /api/health` | 健康检查 |
| `readinessCheck()` | `GET /api/readiness` | 就绪检查 |
| `initSession()` | `POST /api/sessions/init` | 初始化会话 |
| `addObservation()` | `POST /api/sessions/observations` | 添加工具调用 |
| `completeSession()` | `POST /sessions/{id}/complete` | 完成会话 |
| `getProjectContext()` | `GET /api/context/inject?project=` | 获取项目上下文 |
| `search()` | `GET /api/search?q=&limit=` | 搜索记忆 |
| `getObservations()` | `POST /api/observations/batch` | 批量获取详情 |
| `getTimeline()` | `GET /api/timeline?session=&observation=&window=` | 时间线上下文 |

**关键源码**:
| 文件 | 行数 | 说明 |
|------|------|------|
| `src/plugin.ts` | 27 | 插件入口，返回空 event handler |
| `src/integration/index.ts` | 161 | ClaudeMemIntegration 门面类 |
| `src/integration/event-listeners.ts` | 196 | OpenCode Bus 事件订阅核心 |
| `src/integration/worker-client.ts` | 248 | HTTP 客户端 |
| `src/integration/context-injector.ts` | 55 | 上下文注入（未集成） |
| `src/integration/session-mapper.ts` | 71 | Session ID 映射 |
| `src/integration/utils/privacy.ts` | 71 | 隐私标签剥离 |
| `src/integration/utils/project-name.ts` | 32 | 项目名提取 |
| `src/integration/opencode.d.ts` | 52 | OpenCode 类型声明 |
| `src/skill/SKILL.md` | 118 | 搜索技能说明 |
| `src/bundle/index.ts` | 13 | Bundle 入口 |

**已知问题**:

| 问题 | 严重性 | 说明 |
|------|--------|------|
| **插件 event 回调空壳** | 中 | `plugin.ts` 返回 `{ event: async () => {} }` 空壳，实际工作全在 `Bus.subscribe()` 中 |
| **OpenCode 内部路径导入** | 高 | `import('@/bus')` 和 `import('@/session')` 依赖未文档化的路径别名，版本更新可能断裂 |
| **opencode.d.ts 类型不完整** | 中 | `PartUpdated` 事件的 part 字段与实际不符 |
| **ContextInjector 未集成** | 中 | 方法存在但 initialize() 中未调用 |
| **SessionMapper 内存态** | 低 | 进程重启丢失 |

---

### 3.3 memory-lancedb-pro（OpenClaw 插件）

**定位**: OpenClaw 平台的 LanceDB 记忆插件，3.6k stars，MIT 许可证。

> **注意**: OpenClaw ≠ OpenCode。OpenClaw 是 AI Agent Gateway（WhatsApp/Telegram/Discord 多通道消息网关），OpenCode 是本地编码 Agent（CLI/TUI）。两者 hook 模型不同，不能直接安装，但设计理念高度可借鉴。

**架构**:
```
OpenClaw Plugin (TypeScript, 350 commits)
  ├── index.ts: 入口，Plugin API 注册 + 生命周期 hooks
  ├── src/store.ts: LanceDB 存储层（CRUD + FTS + Vector search）
  ├── src/embedder.ts: Embedding 抽象（OpenAI-compatible）
  ├── src/retriever.ts: 混合检索引擎（Vector + BM25 → Fusion → Rerank → Decay → Filter）
  ├── src/smart-extractor.ts: LLM 6 类提取（profile/preference/entity/event/case/pattern）+ L0/L1/L2 分层
  ├── src/decay-engine.ts: Weibull 衰减模型（recency + frequency + importance）
  ├── src/tier-manager.ts: 三级晋升（Peripheral ↔ Working ↔ Core）
  ├── src/noise-filter.ts: 降噪过滤（agent 拒绝、meta 问题、问候）
  ├── src/adaptive-retrieval.ts: 自适应检索决策
  ├── src/scopes.ts: 多 scope 隔离（global / agent / project / user）
  ├── src/tools.ts: Agent 工具（recall/store/forget/update + 管理）
  └── cli.ts: CLI 命令（list/search/stats/delete/export/import/reembed/upgrade/migrate）
```

**存储设计**:
- **单一 LanceDB** — 向量搜索 + 内置 BM25 FTS（基于 Tantivy），无需额外 SQLite
- DB Schema: `memories` 表（id, text, vector, category, scope, importance, timestamp, metadata）
- L0/L1/L2 分层存储：L0（一句话索引）→ L1（结构化摘要）→ L2（完整叙述）

**检索 Pipeline**:
```
Query → embedQuery() ─┐
                       ├─→ Hybrid Fusion → Cross-encoder Rerank → Weibull Decay Boost
Query → BM25 FTS ─────┘         → Length Norm → Hard Min Score → MMR Diversity
```

**关键特性**:
- **Smart Extraction**: LLM 驱动的 6 类分类 + 两阶段去重（向量相似度 ≥0.7 预过滤 → LLM 语义决策 CREATE/MERGE/SKIP）
- **Weibull 衰减**: composite = recency + frequency + (importance × confidence)，核心记忆 beta=0.8（慢衰减），外围 beta=1.3（快衰减）
- **三级晋升**: Peripheral ↔ Working ↔ Core，基于访问频率和时效
- **噪声过滤**: 过滤 agent 拒绝、meta 问题、问候语；CJK 感知阈值（中文 6 字 vs 英文 15 字）
- **自适应检索**: 短查询/问候语/斜杠命令跳过检索，记忆关键词（"remember"/"previously"）强制检索

---

### 3.4 三项目对比

| 维度 | Acontext | claude-mem | memory-lancedb-pro |
|------|----------|------------|-------------------|
| **宿主** | Claude Code Plugin | Claude Code Plugin | OpenClaw Plugin |
| **存储** | 云端 (PostgreSQL+S3+Redis) | 本地 (SQLite+Chroma) | **本地 (LanceDB 单库)** |
| **全文搜索** | 服务端 grep | SQLite FTS5 | **LanceDB 内置 BM25 (Tantivy)** |
| **捕获** | Hooks → transcript → 云端 | Hooks → Bun Worker → AI 压缩 | Hooks → LLM 6 类提取 + 两阶段去重 |
| **检索** | grep-based + MCP tools | 3 层渐进式 | **Hybrid Fusion + Rerank + Decay + MMR** |
| **衰减** | 无 | 无 | **Weibull + 三级晋升** |
| **许可证** | — | AGPL-3.0 | **MIT** |
| **代码质量** | 高（Go+TS SDK） | 中（有已知问题） | **高（350 commits，活跃维护）** |

---

## 四、向量数据库选型

WopalSpace 记忆系统需要语义搜索能力，需要选型一个轻量级嵌入式向量数据库。筛选标准：**本地文件存储、无外部服务、可嵌入应用进程**。

### 4.1 候选方案

#### sqlite-vec

| 维度 | 详情 |
|------|------|
| **仓库** | [asg017/sqlite-vec](https://github.com/asg017/sqlite-vec) (~2.5k★) |
| **定位** | SQLite 向量搜索扩展，"sqlite for vectors" |
| **语言** | 纯 C，零依赖 |
| **存储** | SQLite `.db` 文件（vec0 虚拟表） |
| **安装** | `pip install sqlite-vec` |
| **语言支持** | Python / Node.js / Ruby / Go / Rust |
| **检索** | 暴力 KNN，支持 float/int8/binary 向量 |
| **全文搜索** | 需配合 SQLite FTS5（同一 db 文件内） |
| **混合搜索** | 不支持原生混合，需自行组合 vec0 + FTS5 |
| **许可证** | Apache-2.0 / MIT |
| **特点** | Mozilla 赞助；向量+结构化数据同一文件；WASM 可跑浏览器 |
| **关键限制** | **只有暴力搜索**，无 ANN 索引。万级向量毫秒级，10万+开始变慢 |

#### LanceDB

| 维度 | 详情 |
|------|------|
| **仓库** | [lancedb/lancedb](https://github.com/lancedb/lancedb) (~16k★) |
| **定位** | 多模态 AI 数据湖，嵌入式检索库 |
| **语言** | Rust 核心（基于 Lance 列式格式） |
| **存储** | `.lance` 列式文件 |
| **安装** | `pip install lancedb` |
| **语言支持** | Python / JS / Rust |
| **检索** | 暴力 KNN + ANN（IVF_PQ / DiskANN） |
| **全文搜索** | 内置（Tantivy） |
| **混合搜索** | 原生支持：向量 + 全文 + 元数据过滤，同一查询 |
| **许可证** | Apache-2.0 |
| **特点** | PB 级扩展；零拷贝；自动版本管理；GPU 索引构建 |
| **生态** | LangChain / LlamaIndex / Pandas / Polars / DuckDB 集成 |

#### Zvec

| 维度 | 详情 |
|------|------|
| **仓库** | [alibaba/zvec](https://github.com/alibaba/zvec) (9.2k★) |
| **定位** | 轻量级 in-process 向量数据库 |
| **语言** | C++ 核心（基于 Proxima，阿里内部向量引擎） |
| **存储** | 本地目录 |
| **安装** | `pip install zvec` |
| **语言支持** | Python / Node.js |
| **检索** | HNSW + RaBitQ |
| **全文搜索** | 不支持 |
| **混合搜索** | 支持向量 + 结构化过滤 |
| **许可证** | Apache-2.0 |
| **特点** | macOS ARM64 支持；百亿级向量毫秒级 |
| **风险** | **太新**（2025-12 创建，v0.2.1），API 可能有 breaking changes |

#### Chroma（参考项）

| 维度 | 详情 |
|------|------|
| **仓库** | [chroma-core/chroma](https://github.com/chroma-core/chroma) (18k★) |
| **定位** | AI-native embedding database |
| **存储** | 内存 或 SQLite/DuckDB 持久化 |
| **安装** | `pip install chromadb` |
| **检索** | HNSW |
| **许可证** | Apache-2.0 |
| **排除原因** | claude-mem 使用的方案，但依赖较重；作为嵌入式方案不如 LanceDB 简洁 |

### 4.2 对比总结

| 维度 | sqlite-vec | LanceDB | Zvec | Chroma |
|------|-----------|---------|------|--------|
| **像 SQLite 吗** | 就是 SQLite | 类似，列式文件 | 类似，本地目录 | 内存/SQLite 持久化 |
| **依赖** | 零（纯 C） | 中（Rust runtime） | 中（C++） | 重（Python + 依赖链） |
| **向量+文本混合** | 需 FTS5 配合 | **内置原生** | 仅向量 | 需外部配合 |
| **万级向量速度** | 毫秒 | 毫秒 | 毫秒 | 毫秒 |
| **10万+向量** | 暴力搜索会慢 | ANN 索引，毫秒 | HNSW，毫秒 | HNSW，毫秒 |
| **成熟度** | 稳定（pre-v1） | **成熟** | 很新 | 成熟 |
| **Python SDK** | 原生 | 原生 | 原生 | 原生 |
| **适合 Wopal 记忆量级** | 够用 | **一步到位** | 够用 | 够用但偏重 |

### 4.3 选型结论：LanceDB

**理由**：
1. **一步到位** — 暴力 KNN 到 ANN 索引全覆盖，万级到亿级无切换成本
2. **原生混合搜索** — 向量 + 全文 + 元数据过滤同一查询，省去组合多个系统的复杂度
3. **嵌入式运行** — 无需外部服务，`pip install` 即可
4. **生态成熟** — LangChain/LlamaIndex 等主流集成，社区活跃
5. **Apache-2.0 许可证** — 无合规风险

**备选降级路径**：如果 LanceDB 的 Rust runtime 在某些环境有兼容问题，可降级到 sqlite-vec（纯 C，零依赖），代价是放弃 ANN 索引和原生混合搜索。

---

## 五、OpenCode Plugin Hook 能力分析

> **目的**: 确认 OpenCode Plugin SDK 能否承载记忆系统的捕获、存储和注入需求。
> **源码**: `labs/ref-repos/opencode/packages/plugin/src/index.ts`（250 行完整 Hooks 定义）

### 5.1 记忆系统所需的 Hook 能力

| 需求 | 所需 Hook | OpenCode 是否提供 | 备注 |
|------|----------|-----------------|------|
| 会话事件监听 | 全局事件回调 | ✅ `event: (input: { event: Event }) => Promise<void>` | 接收所有 Bus 事件 |
| 工具调用捕获 | 工具执行后回调 | ✅ `tool.execute.after` | 可获取 tool name + args + output |
| 消息接收监听 | 新消息回调 | ✅ `chat.message` | 可获取 sessionID + agent + message |
| 系统提示注入 | 修改系统 prompt | ✅ `experimental.chat.system.transform` | **记忆注入的关键入口** |
| 消息变换 | 变换消息列表 | ✅ `experimental.chat.messages.transform` | 可插入上下文 |
| 会话压缩定制 | 压缩前自定义 | ✅ `experimental.session.compacting` | 可注入压缩上下文 |

### 5.2 关键 Hook 详情

#### `event` — 全局事件回调

```typescript
event?: (input: { event: Event }) => Promise<void>
```

接收所有 Bus 事件（Session.Created/Updated、MessageV2.*、Part.* 等）。这是捕获层的核心入口。

#### `experimental.chat.system.transform` — 系统提示变换

```typescript
"experimental.chat.system.transform"?: (
  input: { sessionID?: string; model: Model },
  output: { system: string[] },
) => Promise<void>
```

可以修改发送给 LLM 的系统提示数组。**这是记忆注入的关键入口** — 在新会话启动时，检索相关记忆并追加到 system prompt。

#### `tool.execute.after` — 工具执行后

```typescript
"tool.execute.after"?: (
  input: { tool: string; sessionID: string; callID: string; args: any },
  output: { title: string; output: string; metadata: any },
) => Promise<void>
```

每次工具调用后触发。可用于捕获工具调用记录作为 raw observation。

### 5.3 结论

OpenCode Plugin SDK **完全能承载记忆系统**：

| 能力 | 可行性 | 依赖标记 |
|------|--------|---------|
| 事件捕获 | ✅ 稳定 | `event` hook |
| 系统提示注入 | ⚠️ experimental | `experimental.chat.system.transform` |
| 工具调用记录 | ✅ 稳定 | `tool.execute.after` |
| 消息上下文 | ✅ 稳定 | `chat.message` |

**风险**: `experimental.chat.system.transform` 标注为 experimental，可能在未来版本变更。但这是目前唯一能在不修改 Agent 定义的情况下注入上下文的机制，值得冒险。

---

## 六、WopalSpace 记忆系统整合方案

> 基于调研 + 6 个 Spike 验证，确定最终方案。
> **对齐**: PRD §10 Stage 2、DESIGN §4.4

### 6.1 整体架构

在现有 wopal-plugin 内扩展 memory 模块，单进程、单语言。

```
wopal-plugin (TypeScript, 已有)
  └── 新增 src/memory/
        ├── store.ts        — LanceDB 存储层
        ├── embedder.ts     — Embedding（本地 macmini）
        ├── llm-client.ts   — 蒸馏 LLM（云端 API）
        ├── distill.ts      — 蒸馏引擎（手动触发）
        ├── retriever.ts    — 混合检索 + 衰减排序
        ├── injector.ts     — 上下文注入（system.transform）
        └── index.ts        — 模块导出
```

**数据流**:
```
/distill → SDK 查询 session 消息 → LLM 提取 → memories (LanceDB)
                                             │
                                     新会话启动时
                                             │
                                       retriever → 相关记忆 → injector → system prompt
```

### 6.2 核心决策清单

| # | 决策 | 推荐 | 决策依据 |
|---|------|------|---------|
| D1 | 实现路径 | Plugin 内扩展 | PRD "唯一插件"定位；最小复杂度 |
| D2 | 存储层 | LanceDB 单库 | 内置 BM25 FTS，原生混合搜索，一步到位 |
| D3 | 蒸馏触发 | **手动 /distill** | 实时事件捕获信噪比低；手动触发简单可靠；提取状态为后续批量蒸馏保留接口 |
| D4 | 蒸馏输入 | **SDK 查询 session 消息** | Plugin `client.session.messages()` 可直接获取完整对话；LLM 有充分上下文区分信号和噪声 |
| D5 | 检索策略 | 混合（向量+FTS+LIKE） | LanceDB 原生支持，无额外成本 |
| D6 | Embedding | 本地模型 | 已有 Qwen3-Embedding-0.6B（macmini:8000），零 API 成本 |
| D7 | 蒸馏 LLM | 云端 API | 本地算力不足；3 环境变量配置（LLM_BASE_URL/API_KEY/MODEL） |

### 6.3 关键设计决策过程

#### 实时捕获 vs SDK 查询

**最初方案**：Plugin event hook 实时捕获每个事件 → raw_observations → LLM 蒸馏

**问题**：
- 信噪比低：assistant text 大部分是即时响应（"好的"、"我来处理"），高价值的执行经验穿插在工具调用之间
- 时序不可靠：OpenCode 事件流异步，精确过滤（如"工具调用后的 assistant text"）边界情况多
- 多实例冲突：定时蒸馏任务在多个 OpenCode 实例下重复执行

**最终方案**：/distill 手动触发 → SDK 一次性查询完整 session 消息 → LLM 有充分上下文判断信号和噪声

#### 自动蒸馏 vs 手动蒸馏

**自动蒸馏的困难**：
- 增量触发需要 raw_observations 表 + 定时任务
- 定时任务在多实例下冲突
- 蒸馏频率难以确定

**手动蒸馏的优势**：
- 简单可靠，零额外复杂度
- 用户对何时蒸馏有控制权
- 提取状态记录为后续批量蒸馏保留接口

### 6.4 设计借鉴来源

| 设计点 | 借鉴来源 | 吸收方式 |
|--------|---------|---------|
| LanceDB 单库方案 | memory-lancedb-pro | store.ts 存储方案 |
| Smart Extraction | memory-lancedb-pro (LLM 6 类分类 + 两阶段去重) | distill.ts 蒸馏管线 |
| Weibull 衰减模型 | memory-lancedb-pro (recency + frequency + importance) | retriever.ts 排序加权 |
| Hybrid Fusion Pipeline | memory-lancedb-pro | retriever.ts 简化版检索 |
| LLM 客户端封装 | memory-lancedb-pro (openai SDK + JSON repair) | llm-client.ts |
| 蒸馏 Prompt 模板 | memory-lancedb-pro (6 分类 + few-shot) | distill.ts Prompt |

### 6.5 存储设计：LanceDB 单库

**Schema**:
```
memories 表:
  id: string          — UUID
  text: string        — 记忆正文（L0 abstract）
  vector: float[]     — embedding 向量
  category: string    — 类型（profile/preferences/entities/events/cases/patterns）
  project: string     — 所属项目
  session_id: string  — 来源会话
  importance: float   — 重要性（0-1）
  created_at: number  — 创建时间戳
  metadata: dict      — 扩展元数据（overview, content, source_session, etc.）
```

**无 raw_observations 表**：手动蒸馏直接从 SDK 查询 session 消息，无需中间存储。

### 6.6 Embedding 配置

```
EMBEDDING_BASE_URL=http://macmini.local:8000/v1
EMBEDDING_API_KEY=123456789
EMBEDDING_MODEL=Qwen3-Embedding-0.6B
```

升级路径：Qwen3-Embedding-4B（更高质量）→ jina-embeddings-v3（多语言）→ nomic-embed-text-v1.5（英文）。全部本地运行，零 API 成本。

### 6.7 与现有体系的关系

| 现有 | 处理方式 | 说明 |
|------|---------|------|
| `MEMORY.md` | **保留** | 核心骨架，手动维护，语义搜索是补充 |
| `memory/diary/` | **保留** | /memo 命令继续写入，与 /distill 互补 |
| `/memo` 命令 | **保留** | 记录到文本日记，人类可读 |
| `/distill` 命令 | **新增** | 提取到向量数据库，语义检索 |
| wopal-plugin | **扩展** | 新增 memory 模块 |

### 6.8 Phase 2 规划：深层提取蒸馏

基于 Phase 1 积累的提取状态数据，实现跨 session 级别的深度分析：

1. **批量蒸馏**：遍历提取状态，筛选未深层提取的 session，批量关联分析
2. **跨 session 模式挖掘**：多 session 聚合后，LLM 提取行为模式（反复犯的同类错误、效率瓶颈）
3. **记忆冲突检测**：同一主题的新旧记忆矛盾时，自动标记或 supersede
4. **session 管理**：垃圾 session 识别 + 过期归档
5. **记忆质量评估**：追踪命中率，低质量记忆自动降权

**触发方式**：`/distill --deep` 或 `wopal memory deep-distill`

### 6.9 不做的事

- 不做实时自动捕获 — 信噪比低，SDK 查询更可靠
- 不做自动蒸馏定时任务 — 多实例冲突，手动触发更简单
- 不替换 MEMORY.md — 语义搜索是补充不是替代
- 不做自动进化写入长期文件 — 进化必须人工审批
- 不做 Cross-encoder Rerank — <1 万条记忆收益有限
- 不做三级晋升 — 先用 importance + recency
- 不做 L0/L1/L2 分层存储 — v1 只需结构化条目

---

## 七、Spike 验证计划

在正式开发前，需要验证以下关键技术假设：

| # | 验证项 | 方法 | 预期结果 | 时间 |
|---|--------|------|---------|------|
| S1 | `event` hook 事件完整性 | 在 wopal-plugin 中注册 event hook，完整会话中记录所有收到的事件 | 确认能收到 Session.Created/Updated、MessageV2.PartUpdated、Tool.Execute.After | 0.5h |
| S2 | `experimental.chat.system.transform` 可用性 | 注册 hook，向 system 数组追加测试字符串，验证 LLM 是否收到 | 确认注入生效且不被 compaction 丢弃 | 0.5h |
| S3 | LanceDB npm 包基本操作 | `pnpm add lancedb`，测试 create_table / add / search / FTS | 确认 TypeScript SDK 可用，FTS 正常工作 | 1h |
| S4 | 混合检索质量 | 导入现有 MEMORY.md + diary 内容，测试 5 个真实查询的召回质量 | 确认语义搜索优于 grep，混合搜索优于纯向量 | 1h |
| S5 | 蒸馏质量 | 取 3 个真实会话的 raw observations，用 LLM 蒸馏，人工评估 | 确认蒸馏出的记忆条目有价值和准确性 | 1h |
| S6 | Plugin 内 LLM 调用可行性 | 在 wopal-plugin 中测试直接调用 provider API（或 OpenCode 内部 LLM 接口） | 确认 Plugin 能发起 LLM 请求，获取响应，无明显延迟或权限问题 | 0.5h |

**Spike 预估总时间**: 4.5 小时

---

## 八、风险与缓解

| 风险 | 严重性 | 缓解措施 |
|------|--------|---------|
| `experimental.chat.system.transform` 在未来版本被移除或变更 | 高 | 准备降级方案：通过 `chat.message` 注入到用户消息；关注 OpenCode changelog |
| LanceDB npm 包在 macOS ARM64 上有兼容问题 | 中 | 备选降级路径：sqlite-vec（纯 C，零依赖），代价是放弃原生混合搜索 |
| 蒸馏 LLM 调用成本不可控 | 中 | 设置蒸馏预算上限（每月 N 次）；使用低成本模型；蒸馏前先降噪过滤 |
| 记忆注入导致上下文膨胀 | 中 | 设置注入 token 上限（1500）；参考 memory-lancedb-pro 的 dedup + cap 策略 |
| Plugin 包体积增大影响启动速度 | 低 | memory 模块懒加载；LanceDB 连接池化 |

---

## 九、相关资源链接

### 项目仓库
- Acontext: https://github.com/memodb-io/Acontext
- claude-mem: https://github.com/thedotmack/claude-mem
- claude-mem-opencode: https://github.com/mc303/claude-mem-opencode
- DSP: https://github.com/k-kolomeitsev/data-structure-protocol
- hanfang/claude-memory-skill: https://github.com/hanfang/claude-memory-skill
- memory-systems: https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering
- PowerMem: https://github.com/oceanbase/powermem
- mem0: https://github.com/mem0ai/mem0
- awesome-agent-skills: https://github.com/VoltAgent/awesome-agent-skills

### 向量数据库
- LanceDB: https://github.com/lancedb/lancedb
- sqlite-vec: https://github.com/asg017/sqlite-vec
- Zvec: https://github.com/alibaba/zvec
- Chroma: https://github.com/chroma-core/chroma

### 技能市场
- skills.sh: https://skills.sh/
- MCP Market (Agent Memory): https://mcpmarket.com/tools/skills/agent-memory

### 文档
- Claude Code 官方记忆文档: https://code.claude.com/docs/en/memory
- Acontext 官方文档: https://docs.acontext.io/
- claude-mem 官方文档: https://docs.claude-mem.ai/
- PowerMem 中文文档: https://github.com/oceanbase/powermem/blob/main/README_CN.md
- LanceDB 文档: https://lancedb.com/docs
- sqlite-vec 文档: https://alexgarcia.xyz/sqlite-vec/
- 轻量向量数据库对比: https://cybergarden.au/blog/5-lightweight-vector-databases-gen-ai-2025

### WopalSpace 内部参考
- OpenCode 插件事件流: `MEMORY.md` (Wopal-Fae 协作 → 模式2: wopal_task)
- OpenCode Plugin Hooks 定义: `labs/ref-repos/opencode/packages/plugin/src/index.ts`
- OpenCode 事件类型: `labs/ref-repos/opencode/packages/opencode/src/session/message-v2.ts`
- OpenCode Bus 事件: `labs/ref-repos/opencode/packages/opencode/src/bus/`
- OpenCode MCP 客户端: `labs/ref-repos/opencode/packages/opencode/src/mcp/index.ts`
- OpenClaw 源码: `labs/ref-repos/openclaw/`
- memory-lancedb-pro README: `.tmp/cortexreach-memory-plugin.md`
- memory-lancedb-pro manifest: `.tmp/mlp-plugin-json.md`
- 现有记忆体系: `MEMORY.md` + `memory/diary/` + `/memo` 命令
- 现有规则: `.agents/rules/mem-rule.md`
- PRD Stage 2 定义: `docs/products/wopal-space/PRD-wopalspace.md` §10 Stage 2
- DESIGN 记忆架构: `docs/products/wopal-space/DESIGN-wopalspace.md` §4.4

---

*(本报告由 Wopal 持续更新。v1: 外部项目调研 + 源码深度分析。v2: 向量数据库选型 + 方案初版。v3: memory-lancedb-pro 分析 + Hook 能力分析 + 可行性研究。v4: 结构重组 + WopalSpace 整合思路。v5: 对齐最终方案 — 手动蒸馏 + SDK 查询，移除自动捕获)*

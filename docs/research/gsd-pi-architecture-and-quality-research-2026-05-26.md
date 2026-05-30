# GSD-PI 架构与源码质量研究报告

> 研究日期: 2026-05-26
> 研究对象: `labs/research/gsd-pi/`（GSD-PI v1.0.2，包名 `@opengsd/gsd-pi`）
> 目的: 为评估 GSD 工作流体系在 Wopal 生态系统中的可借鉴性与可集成性，提供详尽的架构分析、内部工具机制研究和源码质量评估基线

---

## 1. 研究目标

本次研究的核心问题有五个：

1. GSD-PI 的整体架构是什么？工具、扩展、技能、子 Agent 四类资源如何组织？
2. 系统如何启动、如何加载资源、如何注册工具到 LLM？
3. 26 个内部工作流工具的底层实现是什么？耦合度如何？
4. 能否将 `gsd_decision_save` 等内部工具提取为 CLI 命令，由 Skill 指导 Agent 调用？
5. 项目源码质量如何？有哪些值得借鉴的设计模式和需要规避的问题？

本报告聚焦"事实、结构、机制、质量判断"，不直接承担集成设计；集成方案另见后续规划文档。

---

## 2. 研究范围与参考源

### 2.1 主要参考路径

| 路径 | 角色 |
|------|------|
| `labs/research/gsd-pi/src/` | 核心源码（CLI、加载器、资源管理） |
| `labs/research/gsd-pi/src/resources/extensions/gsd/` | GSD 核心扩展（350+ 文件，最大子系统） |
| `labs/research/gsd-pi/packages/` | 9 个子包（contracts、rpc-client、mcp-server 等） |
| `labs/research/gsd-pi/gsd-orchestrator/` | 无头编排技能（Markdown prompt 定义） |
| `~/.gsd/agent/` | 运行时部署目录（资源同步目标） |

### 2.2 关键源码文件

| 类型 | 路径 | 用途 |
|------|------|------|
| 引导加载器 | `src/loader.ts` | Stage 1 启动，环境注入 |
| 主入口 | `src/cli.ts` | Stage 2 启动，会话创建 |
| 资源加载 | `src/resource-loader.ts` | 打包资源同步到 `~/.gsd/agent/` |
| 扩展发现 | `src/extension-discovery.ts` | 扫描+合并扩展路径 |
| 扩展注册表 | `src/extension-registry.ts` | 启用/禁用状态持久化 |
| 扩展校验 | `src/extension-validator.ts` | 社区扩展安装时校验 |
| 无头模式 | `src/headless.ts` | CLI 无头模式主逻辑 |
| 无头查询 | `src/headless-query.ts` | 零成本状态查询（无 LLM） |
| 工具注册 | `src/resources/extensions/gsd/bootstrap/exec-tools.ts` | 工具注册引导 |
| 工具执行器 | `src/resources/extensions/gsd/tools/workflow-tool-executors.ts` | MCP 适配层 |
| 状态协调 | `src/resources/extensions/gsd/state-reconciliation.ts` | 文件-DB 一致性修复 |
| 自动调度 | `src/resources/extensions/gsd/auto-dispatch.ts` | 1829 行状态机，20+ 调度规则 |
| 任务完成 | `src/resources/extensions/gsd/tools/complete-task.ts` | 最复杂的工具实现 |
| 错误分类 | `src/resources/extensions/gsd/error-classifier.ts` | LLM 错误分类与重试判定 |
| RPC 类型 | `packages/contracts/src/rpc.ts` | 43 个 RPC 命令类型 |
| 工具契约 | `packages/contracts/src/workflow.ts` | 27 个工作流工具元数据 |
| RPC 客户端 | `packages/rpc-client/src/client.ts` | JSONL 协议 SDK |
| MCP 服务器 | `packages/mcp-server/src/server.ts` | MCP 协议桥，44+ 工具 |
| 守护进程 | `packages/daemon/src/orchestrator.ts` | Discord Bot 自然语言编排 |
| 编排技能 | `gsd-orchestrator/SKILL.md` | 外部 Agent 驱动 GSD 的 prompt |

---

## 3. 项目概述

### 3.1 GSD 是什么

GSD (Get Stuff Done) 是一个**项目管理方法论 + AI 编码 Agent 运行时**。它不是一个简单的提示词模板，而是一个完整的平台，包含：

- **方法论层**：`GSD-WORKFLOW.md` 定义了 Milestone → Slice → Task 的三级分解体系，7 个工作阶段（Discuss → Research → Plan → Execute → Verify → Summarize → Advance）
- **运行时层**：基于 Node.js 22+ 的 TypeScript 运行时，包含扩展系统、工具注册、会话管理、LLM 多提供商适配
- **编排层**：无头模式（CLI）、RPC 协议（SDK）、MCP 协议（外部工具集成）、Discord Bot（自然语言控制）

### 3.2 版本与模型配置

当前部署版本 `1.0.2`，运行时配置（`~/.gsd/agent/settings.json`）：

```json
{
  "defaultProvider": "wopal-ai",
  "defaultModel": "glm-5-turbo",
  "defaultThinkingLevel": "off"
}
```

通过 `models.json` 配置了自建 API 端点 `aiapi.wopal.cn/v1`，接入 12 个国产模型（通义千问、DeepSeek、智谱 GLM 系列）。

### 3.3 统计规模

| 维度 | 数量 |
|------|------|
| 子包 | 9 |
| 核心源文件（src/） | 54 |
| 打包扩展 | 21 |
| 打包技能 | 35 |
| 子 Agent 定义 | 13 |
| 内部工作流工具 | 27 |
| RPC 命令类型 | 43 |
| MCP 暴露工具 | 44+ |
| 单元测试文件 | 312 |
| 集成测试文件 | 37 |

---

## 4. 架构分析

### 4.1 包分层架构

整个系统是一个 9 包 monorepo，分为 4 层：

```
┌─────────────────────────────────────────────────────────┐
│  Layer 4: 编排层                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │ daemon       │  │ mcp-server   │  │ cloud-gateway  │ │
│  │ (Discord Bot)│  │ (MCP 协议桥) │  │ (云端网关)     │ │
│  └──────┬───────┘  └──────┬───────┘  └────────────────┘ │
├─────────┼─────────────────┼──────────────────────────────┤
│  Layer 3: RPC 通信层                                     │
│  ┌──────┴───────────────┐                                │
│  │ rpc-client           │  JSONL over stdin/stdout       │
│  │ (SDK，驱动 CLI 子进程)│                                │
│  └──────┬───────────────┘                                │
├─────────┼────────────────────────────────────────────────┤
│  Layer 2: Agent 核心                                     │
│  ┌──────┴───────────────┐  ┌──────────┐                  │
│  │ pi-coding-agent      │  │ pi-tui   │                  │
│  │ (主 CLI，~900 行入口) │  │ (终端UI) │                  │
│  └──────┬───────────────┘  └──────────┘                  │
├─────────┼────────────────────────────────────────────────┤
│  Layer 1: 基础设施                                       │
│  ┌──────┴──────┐ ┌────────┐ ┌──────────┐ ┌───────────┐  │
│  │ contracts   │ │ pi-ai  │ │pi-agent  │ │ native    │  │
│  │ (类型协议)  │ │ (LLM) │ │ -core    │ │ (Rust)    │  │
│  └─────────────┘ └────────┘ └──────────┘ └───────────┘  │
└─────────────────────────────────────────────────────────┘
```

各包职责：

| 包 | 职责 | 关键特性 |
|---|------|---------|
| `@opengsd/contracts` | 共享类型和常量 | 零依赖，43 个 RPC 命令类型，27 个工具契约 |
| `@gsd/native` | Rust N-API 绑定 | 17 个子模块（grep/glob/ast/diff/parser 等） |
| `@gsd/pi-ai` | 统一 LLM 接口 | 20+ 提供商适配（Anthropic/OpenAI/Google/Bedrock 等） |
| `@gsd/pi-agent-core` | Agent 循环抽象 | 无依赖的基础 Agent 抽象 |
| `@gsd/pi-coding-agent` | 主 CLI 二进制 | 扩展系统、工具注册、会话管理 |
| `@gsd/pi-tui` | 终端 UI | chalk 渲染、markdown 渲染、图片支持 |
| `@opengsd/rpc-client` | RPC 客户端 SDK | JSONL 协议，typed API，async generator 事件流 |
| `@opengsd/mcp-server` | MCP 协议桥 | 44+ 工具，SQLite 状态管理，安全边界校验 |
| `@opengsd/daemon` | 常驻后台进程 | Discord Bot、SessionManager、CloudRuntime |
| `@opengsd/cloud-gateway` | 云端网关 | WebSocket 桥接远程运行时 |

### 4.2 启动流程（两阶段加载器）

```
用户运行 `gsd` 命令
    │
    ▼
Stage 1: loader.ts（~250 行，轻量引导，不加载重依赖）
    ├─ Node.js 版本检查（>= 22）
    ├─ 环境变量注入
    │   ├─ PI_PACKAGE_DIR = pkg/
    │   ├─ GSD_CODING_AGENT_DIR = ~/.gsd/agent/
    │   ├─ GSD_VERSION from package.json
    │   ├─ GSD_WORKFLOW_PATH → 打包的 GSD-WORKFLOW.md
    │   └─ NODE_PATH 前置 GSD 的 node_modules（供 jiti 加载的扩展使用）
    ├─ 工作区包链接（扫描 packages/* 中 gsd.linkable=true 的包，符号链接到 node_modules）
    ├─ 发现打包扩展路径 → 序列化到 GSD_BUNDLED_EXTENSION_PATHS 环境变量
    └─ await import('./cli.js')  ← 动态 import，延迟 ESM 评估
          │
          ▼
Stage 2: cli.ts（~900 行主逻辑）
    ├─ 解析 CLI 参数（headless/auto/web/worktree 等子命令路由）
    ├─ AuthStorage / ModelRegistry / SettingsManager 初始化
    ├─ ensureManagedTools() → 安装 fd、rg 到 ~/.gsd/agent/bin/
    ├─ initResources(agentDir)
    │   ├─ 指纹校验（content hash + version）→ 跳过未变化的同步
    │   ├─ 同步 extensions/ → ~/.gsd/agent/extensions/
    │   ├─ 同步 skills/     → ~/.gsd/agent/skills/
    │   ├─ 同步 agents/     → ~/.gsd/agent/agents/
    │   └─ 同步 GSD-WORKFLOW.md
    ├─ buildResourceLoader()
    │   ├─ 发现 ~/.gsd/agent/extensions/ 中的扩展
    │   ├─ 发现 ~/.pi/agent/extensions/ 中的扩展（跨兼容）
    │   ├─ 按注册表过滤启用/禁用状态
    │   └─ 拓扑排序（Kahn BFS）处理扩展依赖
    ├─ resourceLoader.reload()  ← 最重步骤：jiti 编译所有扩展模块
    ├─ createAgentSession() → 创建 LLM 会话，注册所有工具
    └─ new InteractiveMode(session).run() → 启动 TUI
```

**关键设计点：**

- **指纹同步**：`resource-loader.ts` 通过 content hash + version 指纹避免每次启动都复制文件。只有源码变化时才重新同步到 `~/.gsd/agent/`
- **拓扑排序加载**：扩展之间有依赖关系，通过 Kahn BFS 算法按拓扑序加载。缺失依赖产生警告但不阻塞。循环依赖被检测，参与者按字母序追加
- **两阶段引导**：Stage 1 不加载任何重依赖（@gsd/*），只做环境准备。Stage 2 才动态 import 全部模块。这使得 `gsd --version` 和 `gsd --help` 几乎瞬时返回

### 4.3 四类资源的本质与协作

| 维度 | Extensions（扩展） | Skills（技能） | Agents（子Agent） | Workflow Doc |
|------|-------------------|---------------|-------------------|-------------|
| **格式** | TypeScript/JS 代码 | Markdown + XML | Markdown + YAML frontmatter | Markdown |
| **数量** | 21 | 35 | 13 | 1 (GSD-WORKFLOW.md) |
| **加载方式** | jiti 编译执行 | 文件发现，按需读取 | 文件发现，派生子会话 | 按需读取 |
| **注册时机** | 启动时 `reload()` | 会话中按需加载 | 用户调用时 | 被 skill 引用 |
| **能做什么** | 注册工具、命令、钩子、快捷键、UI 覆盖层 | 提供结构化 prompt 指导 LLM 行为 | 创建独立上下文窗口执行专一任务 | 方法论文档 |
| **运行时开销** | 高（编译+注册） | 零（纯文本） | 中（子会话） | 零 |
| **平台耦合** | 强（依赖 ExtensionAPI） | 无（纯 prompt） | 弱（依赖子会话机制） | 无 |

#### 4.3.1 扩展：运行时插件

每个扩展的 `index.ts` 导出默认函数，接收 `ExtensionAPI`：

```typescript
export default function(pi: ExtensionAPI) {
  // 注册工具 — LLM 可调用的函数
  pi.registerTool("bg_shell", {
    description: "Run a background shell process",
    parameters: { /* JSON Schema */ },
    execute: async (params) => { /* 实现 */ }
  });

  // 注册命令 — 用户输入的斜杠命令
  pi.registerCommand("bg", {
    description: "Manage background processes",
    handler: async (args) => { /* 实现 */ }
  });

  // 注册钩子 — 生命周期事件回调（16 种钩子类型）
  pi.on("session_start", async () => { /* 初始化 */ });
  pi.on("tool_call", async (event) => { /* 拦截/修改工具调用 */ });
}
```

扩展通过 manifest 声明能力：

```json
{
  "id": "gsd",
  "tier": "core",
  "requires": { "platform": ">=2.29.0" },
  "provides": {
    "tools": ["bash", "read", "write", "edit", "gsd_decision_save", ...],
    "commands": ["gsd", "kill", "worktree", "exit"],
    "hooks": ["session_start", "tool_call", "agent_end", ...],
    "shortcuts": ["Ctrl+Alt+G"]
  }
}
```

**GSD 核心扩展**（`extensions/gsd/`，350+ 文件）是系统中最复杂的部分，注册了 8 个工具、4 个命令、16 个钩子、1 个快捷键。它的 `bootstrap/register-extension.ts` 负责：
- 动态工具注册（bash/read/write/edit 带工作空间感知）
- 生命周期钩子（session_start → 读 STATE.md、tool_call → 写门控、agent_end → 崩溃恢复）
- 生态系统扩展加载器（加载 `.gsd/extensions/` 中的第三方 GSD 扩展）
- 进程错误防护（EPIPE、EIO、ENOENT 处理器）
- 工具调用循环守卫和写门控（审批工作流）

#### 4.3.2 技能：结构化 Prompt 文件

技能是纯 Markdown 文件，格式为 YAML frontmatter + XML 标签体：

```markdown
---
name: tdd
description: Test-driven development with red-green-refactor loops...
---

<objective>
Drive feature implementation through one red-green-refactor cycle per vertical slice.
</objective>

<core_principle>
TESTS VERIFY BEHAVIOR THROUGH PUBLIC INTERFACES, NOT IMPLEMENTATION DETAILS.
</core_principle>

<process>
## Step 1: Confirm the interface
...
</process>
```

复杂技能采用 Router 模式：

```
skill-name/
├── SKILL.md              # 路由器 + 核心原则（< 500 行）
├── workflows/            # 按步骤流程（FOLLOW）
├── references/           # 领域知识（READ）
├── templates/            # 输出结构（COPY + FILL）
└── scripts/              # 可执行代码（EXECUTE）
```

SKILL.md 充当路由器："你想做什么？" → 引导到具体 workflow → workflow 指定需要读取哪些 references。这种渐进披露（Progressive Disclosure）模式控制了上下文预算。

**关键特性：** 技能不调用任何 GSD 专属 API。它是纯文本指令，任何 AI Agent 都能理解和执行。GSD 自身的 `spike-wrap-up` 技能甚至直接写入 `.claude/skills/` 目录，表明技能在 Claude Code 中也可发现。

#### 4.3.3 子 Agent：专业化执行者

13 个子 Agent 定义为 Markdown 文件，YAML frontmatter 声明模型、冲突关系等元数据。核心设计模式：

| Agent | 职责 | 关键约束 |
|-------|------|---------|
| worker | 通用执行 | 全工具权限，但不能派生子 Agent |
| planner | 规划 | 只产出计划，不写代码 |
| scout | 代码侦察 | 只读，压缩输出供其他 Agent 使用 |
| debugger | 调试 | 调查阶段只读，决策门后才可修改 |
| reviewer | 代码审查 | 输出 APPROVE/REQUEST_CHANGES/NEEDS_DISCUSSION |
| refactorer | 重构 | 每次改动前后必须跑测试，绝不在 RED 状态重构 |
| security | 安全审计 | 基于 OWASP 分类，CRITICAL/HIGH/MEDIUM/LOW 评级 |

### 4.4 运行时协作流程

以一个典型工作场景为例：

```
用户: "创建用户认证功能"
    │
    ▼
1. GSD 核心扩展 session_start 钩子
   ├─ 读取 STATE.md → 确定当前状态
   ├─ 读取 GSD-WORKFLOW.md → 加载方法论
   └─ 加载 M###-CONTEXT.md → 项目决策
    │
    ▼
2. 用户: /gsd start
   ├─ 核心扩展 /gsd 命令触发
   ├─ 加载 skill: decompose-into-slices → 指导 LLM 分解切片
   ├─ LLM 产出 M###-ROADMAP.md + Boundary Map
   └─ gsd_decision_save 工具 → 写入 DECISIONS.md
    │
    ▼
3. 执行阶段
   ├─ LLM 调用 bash/read/write/edit（核心扩展提供）
   ├─ context7 扩展提供 resolve_library/get_library_docs
   ├─ search-the-web 扩展提供 search_and_read
   ├─ subagent 扩展可派生 worker Agent 执行子任务
   ├─ bg-shell 扩展支持后台长时间运行的命令
   └─ ttsr 扩展实时监控流式输出，匹配正则规则
    │
    ▼
4. 验证阶段
   ├─ 加载 skill: verify-before-complete → 强制验证
   ├─ LLM 调用 bash 运行测试
   ├─ browser-tools 扩展可截图验证 UI
   └─ mac-tools 可验证原生应用行为
    │
    ▼
5. 完成阶段
   ├─ gsd_summary_save → 写 T##-SUMMARY.md
   ├─ gsd_requirement_update → 更新 checkbox
   ├─ 通知 UI 覆盖层更新进度
   └─ 推进到下一个 Task/Slice
```

### 4.5 两层编排器

系统有两个"编排器"概念：

**1. gsd-orchestrator/（技能级编排器）**

纯 Markdown 文件组成的 skill，教会外部 AI Agent 以无头模式驱动 GSD：

```
gsd headless --context spec.md new-milestone --auto
    │
    ├─ 退出码 0 = 成功
    ├─ 退出码 1 = 错误/超时
    ├─ 退出码 10 = 被阻塞（需人工干预）
    └─ 退出码 11 = 已取消
```

三种工作流模式：
- **build-from-spec** — 端到端：写规格 → 初始化 → 启动自动模式
- **step-by-step** — 精细控制：循环调用 `gsd headless next`，每步检查预算
- **monitor-and-poll** — 通过 `gsd headless query` 零成本监控（不消耗 LLM token）

**2. daemon/（进程级编排器）**

常驻后台进程，包含 Anthropic 驱动的 Discord Bot：

```
Discord #gsd-control 频道
    │ "开始构建用户认证模块"
    ▼
Orchestrator (Anthropic LLM)
    ├─ tool: list_projects → 查看项目列表
    ├─ tool: start_session → 启动 GSD 会话
    ├─ tool: get_status → 查看进度
    └─ tool: stop_session → 停止会话
         │
         ▼
    rpc-client → gsd --mode rpc (子进程，JSONL 协议)
         │
         ▼
    SessionManager（环缓冲事件追踪 + 阻塞检测 + 成本累计）
```

---

## 5. 内部工作流工具深度分析

### 5.1 工具架构

工具实现分三层：

```
Handler 层 (tools/*.ts)          ← 纯业务逻辑，接收 params + basePath
    │
Executor 层 (workflow-tool-executors.ts)  ← MCP 适配，打开 DB、委托 Handler、包装结果
    │
Registration 层 (bootstrap/exec-tools.ts)  ← 注册 Context Mode 工具到 ExtensionAPI
```

所有工具的底层数据只有两个来源：

1. **SQLite 数据库**（`.gsd/gsd.db`）
2. **文件系统**（`.gsd/milestones/...` 下的 Markdown 投影文件）

**没有任何工具依赖仅存在于内存中的状态。** 三个内存缓存（state cache、path cache、parse cache）都是进程局部的 Map，CLI 命令每次全新启动不需要失效它们。

### 5.2 全部 26 个工具分类

#### 读取类工具（7 个）

| 工具名 | 操作 | 运行时耦合 |
|--------|------|-----------|
| `gsd_milestone_generate_id` | ID 生成 | 低 |
| `gsd_milestone_status` | 读里程碑状态 | 低 |
| `gsd_journal_query` | 查询日志 | 低 |
| `gsd_exec_search` | 扫描 `.gsd/exec/*.meta.json` | 极低（纯文件读取） |
| `gsd_resume` | 读 `.gsd/last-snapshot.md` | 极低（单个文件读取） |
| `gsd_memory_query` | SQLite 查询 + JS 排名 | 中（需 SQLite 适配器 + 排名逻辑） |
| `gsd_memory_graph` | SQLite 图遍历 | 中（需 SQLite 适配器） |

#### 写入类工具（19 个）

**低耦合（可直接提取为 CLI 命令）：**

| 工具名 | 操作 | 耦合原因 |
|--------|------|---------|
| `gsd_exec` | 子进程执行 + 写 `.gsd/exec/` | 自包含的沙箱执行 |
| `gsd_skip_slice` | 单次 SQLite 写入 | 最简单的变更工具，同步执行 |

**中等耦合（需导入共享模块）：**

| 工具名 | 操作 | 额外依赖 |
|--------|------|---------|
| `memory_capture` | SQLite 写入 | `memory-store.ts` |
| `gsd_task_reopen` | SQLite 写 + 文件清理 + 投影渲染 | 需导入渲染模块 |
| `gsd_slice_reopen` | 级联重置 + 文件清理 | 同上，范围更大 |
| `gsd_milestone_reopen` | 全级联重置 | 同上，范围最大 |
| `gsd_plan_task` | SQLite 写 + Markdown 渲染 | 需导入渲染模块 |

**高耦合（需导入多个共享模块）：**

| 工具名 | 操作 | 复杂度来源 |
|--------|------|-----------|
| `gsd_plan_milestone` | 多表事务 + 渲染 + 缓存失效 + 事件日志 | 渲染从 DB 状态到 Markdown |
| `gsd_plan_slice` | 复杂验证 + 质量门种子 + 渲染 | 路径范围验证 + 门种子植入 |
| `gsd_complete_task` | 所有权检查 + 过期检测 + 升级产物 + 门关闭 + 图重建 | 最复杂的工具，311 行主函数 |
| `gsd_complete_slice` | 门关闭 + Roadmap 重渲染验证 + 图重建 | 异步图重建（fire-and-forget） |
| `gsd_complete_milestone` | 跨实体深链验证 + 验证评估 | 全链路状态守卫 |
| `gsd_validate_milestone` | 浏览器证据门 + UOK 门运行器 + 功能标志 | 特性开关控制行为 |
| `gsd_reassess_roadmap` | 结构变更检测 + 过期验证清理 | 切片增删改的完整性保护 |
| `gsd_replan_slice` | 重规划历史 + 任务变更守卫 | 已完成任务的保护 |

### 5.3 共享的后置钩子模式

所有"高耦合"工具共享相同的后置操作：

```
1. invalidateStateCache()     ← CLI 命令不需要（进程局部的 Map）
2. clearPathCache()           ← CLI 命令不需要
3. clearParseCache()          ← CLI 命令不需要
4. renderAllProjections()     ← 从 SQLite 渲染 Markdown 到磁盘
5. writeManifest()            ← 更新 .gsd/manifest.json
6. appendEvent()              ← 追加到 .gsd/events.jsonl
```

其中 1-3 是进程局部缓存，CLI 命令每次全新进程根本不需要失效。只需要导入 4-6 三个模块。

### 5.4 数据流图

```
LLM 工具调用参数（JSON）
    │
    ▼
ExtensionAPI.registerTool().execute()
    │
    ▼
workflow-tool-executors.ts
    ├─ ensureDbOpen(basePath)     ← 打开 SQLite 连接
    ├─ 调用 handler(params, basePath)
    │   │
    │   ▼
    │   handler (tools/*.ts)
    │   ├─ 验证参数（ID 非空、状态合法）
    │   ├─ SQLite 事务（多表操作）
    │   ├─ 文件系统写入（Markdown 投影、Summary、UAT）
    │   ├─ 缓存失效
    │   ├─ renderAllProjections()
    │   ├─ writeManifest()
    │   └─ appendEvent()
    │
    ├─ 包装 ToolExecutionResult
    └─ 返回给 LLM
```

---

## 6. CLI 提取可行性研究

### 6.1 现状：CLI 与内部工具的差距

当前 CLI 只暴露**编排级命令**：

| 命令 | 说明 | 是否需要 LLM |
|------|------|-------------|
| `gsd headless auto` | 自动循环 | 是 |
| `gsd headless next` | 执行一个单元 | 是 |
| `gsd headless dispatch <phase>` | 切换阶段 | 是 |
| `gsd headless query` | 读状态（JSON） | 否 |
| `gsd headless steer` | 纠偏 | 是 |
| `gsd headless skip` | 跳过 | 是 |
| `gsd headless undo` | 回退 | 是 |
| `gsd headless recover` | 从 Markdown 重建 DB | 否 |
| `gsd headless doctor` | 健康检查 | 否 |

**26 个细粒度工具没有直接 CLI 入口。** 所有操作都必须经过 LLM 会话（LLM 决定调用哪个工具）。

### 6.2 提取方案

#### 目标架构

```
┌─────────────────────────────────────────────────────┐
│  任何 AI Agent（Claude Code / opencode / Cursor）    │
│                                                     │
│  加载 SKILL.md（纯文本 prompt）                      │
│    ↓                                                │
│  Skill 指导 Agent:                                   │
│    "完成任务时运行: gsd task-complete T01"            │
│    "保存决策时运行: gsd decision-save --cat arch ..." │
│    "查看状态时运行: gsd query"                        │
│    ↓                                                │
│  Agent 通过 bash 工具调用 CLI                        │
│    → gsd query → JSON 输出 → Agent 解析             │
│    → gsd plan-milestone --json '{...}'              │
│    → gsd task-complete T01 --summary '...'          │
└─────────────────────────────────────────────────────┘
```

#### 分阶段实施建议

**Phase 1: 抽取共享库**

将 `gsd-db`、`renderAllProjections`、`writeManifest`、`appendEvent` 模块提取为 `@opengsd/workflow-core` 包，确保无 ExtensionAPI 依赖。

**Phase 2: 实现常用 CLI 命令（低+中等耦合工具）**

```
gsd query              ← 已有
gsd decision-save      ← 新增
gsd summary-save       ← 新增
gsd task-complete      ← 新增
gsd task-reopen        ← 新增
gsd plan-slice         ← 新增
gsd memory-query       ← 新增
gsd exec               ← 新增
```

输入格式建议：简单操作用 flag，复杂操作用 `--json` 接收 stdin：

```bash
# 简单操作
gsd task-complete T01 --milestone M001 --slice S01

# 复杂操作
echo '{"title":"...","mustHaves":[...]}' | gsd plan-task --json
```

**Phase 3: 适配 Skills**

修改 SKILL.md 中的指令，从工具调用改为 CLI 命令调用，并添加 JSON 输入/输出格式说明。

**Phase 4: 实现剩余高耦合工具**

**Phase 5: MCP 协议适配**（可选）

### 6.3 风险与注意事项

| 风险 | 说明 | 缓解措施 |
|------|------|---------|
| 原子性差距 | 当前工具在 SQLite 事务中执行多个操作 | CLI 命令复用相同事务逻辑 |
| 验证逻辑复现 | `gsd_complete_task` 有过期检测和升级产物验证 | 从共享库导入相同验证函数 |
| 图重建副作用 | `complete_task/slice` 触发异步知识图谱重建 | CLI 命令可选触发，默认跳过 |
| 输入格式设计 | 复杂工具参数嵌套深 | `--json` stdin + JSON Schema 验证 |

---

## 7. 源码质量评估

### 7.1 总评

**B+（高质量专业项目，有明确的改进空间）**

### 7.2 分维度评分

| 维度 | 评分 | 说明 |
|------|------|------|
| **TypeScript 类型安全** | 5/5 | `strict: true`，discriminated union，极低 `any` 使用率 |
| **包架构/依赖管理** | 5/5 | 零依赖 contracts 包，清晰分层，无循环依赖 |
| **API 设计** | 5/5 | 公共接口干净，JSDoc 完整，安全边界深思熟虑 |
| **错误处理** | 4/5 | 原子写入、双重故障恢复、分类错误，个别静默吞错 |
| **测试** | 4/5 | 483+ 测试文件，模式多样，但阈值偏低（40/20%） |
| **代码组织** | 3/5 | 几个巨型文件需拆分（1829 行文件、782 行单函数） |
| **安全** | 3/5 | MCP server 安全性优秀，但工具层路径穿越未验证 |
| **DRY/代码复用** | 3.5/5 | 类型/常量集中化好，后置钩子和关闭状态检查有重复 |
| **可维护性** | 4/5 | Issue/ADR 引用充分，注释质量高，巨型函数增加理解成本 |

### 7.3 做得好的设计模式

#### 7.3.1 Discriminated Union 错误分类

`error-classifier.ts` 的 `ErrorClass` 是教科书级实现：

```typescript
type ErrorClass =
  | { kind: "rate_limit"; retryAfterMs: number }
  | { kind: "auth_expired" }
  | { kind: "context_overflow" }
  | { kind: "unknown" };

function isTransient(cls: ErrorClass): boolean {
  switch (cls.kind) {
    case "rate_limit": return true;
    case "auth_expired": return false;
    // ... TypeScript 编译器检查穷尽性
  }
}
```

不抛异常，每条路径都返回有效结果。新增 kind 时 TypeScript 编译器会标记缺失的 case。

#### 7.3.2 原子写入 + 双重故障恢复

注册表持久化使用原子写入模式（先写 `.tmp`，再 `renameSync`）。任务完成工具的升级写失败有补偿回滚：

```typescript
// complete-task.ts — 升级产物写失败的回滚
try {
  await writeEscalationArtifact(...)
} catch (escalationErr) {
  // 回滚已提交的 DB 完成
  try {
    updateTaskStatus(db, taskId, "in_progress")
  } catch (rollbackErr) {
    logError("rollback also failed", rollbackErr)  // 双重故障记录
  }
}
```

#### 7.3.3 零依赖类型包

`@opengsd/contracts` 零运行时依赖，纯 TypeScript 类型和常量。使用 `as const` 断言从数组推导穷尽联合类型：

```typescript
const RPC_COMMAND_TYPES = ["prompt", "steer", "abort", ...] as const;
type RpcCommandType = typeof RPC_COMMAND_TYPES[number];  // 联合类型自动推导
```

#### 7.3.4 RPC 客户端的 JSONL 实现

`rpc-client` 不用 Node 的 readline，自己处理 LF 分帧来避免 Unicode 分隔符 bug。代码注释详细解释了这个设计决策的原因。

#### 7.3.5 MCP Server 安全边界

`validateProjectDir()` 使用 realpath 符号链接验证、home 目录拒绝、GSD_WORKFLOW_PROJECT_ROOT 边界强制。`runSerializedWorkflowOperation` 防止并发 SQLite 写入。每个工具 handler 都被 `wrapServerWithErrorHandler` 装饰器包装，统一错误捕获和结构化返回。

### 7.4 需要改进的问题

#### 7.4.1 巨型文件和函数（严重度：高）

| 文件 | 行数 | 问题 |
|------|------|------|
| `auto-dispatch.ts` | 1829 行 | 20+ 调度规则混杂，应拆分为独立规则模块 + 共享注册表 |
| `headless.ts` `runHeadlessOnce` | 782 行 | 单个函数，内含 267 行事件回调，嵌套 6 层 |
| `workflow-tools.ts` | ~2258 行 | Schema + 导入解析 + 注册 + 安全执行混杂 |
| `cli.ts` | 903 行 | 顶层脚本执行，无可测试入口函数 |

#### 7.4.2 路径穿越未验证（严重度：高）

`milestoneId`、`sliceId`、`taskId` 来自 LLM 工具调用参数，直接用于 `join()` 构造文件路径，没有 `../` 校验：

```typescript
// complete-task.ts — 典型问题
join(gsdProjectionRoot(basePath), "milestones", milestoneId, "slices", sliceId, ...)
// 如果 milestoneId = "../../../etc" → 路径逃逸
```

影响文件：`complete-task.ts`、`plan-milestone.ts`、`plan-slice.ts`、`auto-dispatch.ts`。修复建议：添加 `!/(\.\.|\/)/.test(id)` 校验。

#### 7.4.3 关闭状态检查不一致（严重度：中）

`isClosedStatus()` 定义 4 个关闭状态：`"complete" | "done" | "skipped" | "closed"`

但多处使用硬编码子集：

| 位置 | 检查的状态 | 缺失 |
|------|-----------|------|
| `plan-milestone.ts:303` | `"complete" || "done"` | `"skipped"`, `"closed"` |
| `auto-dispatch.ts:374` | `Set(["skipped", "complete", "done"])` | `"closed"` |

可能导致 `"closed"` 状态的 slice 在重规划时不被保护。

#### 7.4.4 重复的后置钩子模式（严重度：中）

三个工具文件包含几乎相同的后置钩子代码块（各 ~20 行），应提取为共享函数。

#### 7.4.5 `headless-query.ts` 的类型盲区（严重度：中）

7 个连续的 `as any` 强转来自 jiti 动态导入。应定义模块接口类型替代 `any`。

#### 7.4.6 封装违规（严重度：低）

```typescript
// headless.ts:953 — 通过 Reflect.get 访问私有属性
const internalProcess = Reflect.get(client as object, 'process') as ChildProcess | undefined
```

如果 RpcClient 内部重构，这里会静默失败。

#### 7.4.7 测试覆盖率阈值偏低（严重度：低）

```
Statements: 40% | Lines: 40% | Branches: 20% | Functions: 20%
```

关键路径（工作流工具、状态协调）的实际覆盖率远高于此，但整体阈值应逐步提升。

### 7.5 `any` 使用审计

| 文件 | `any` 数量 | 原因 | 严重度 |
|------|-----------|------|--------|
| `loader.ts` | 1 | Node.js 未文档化 API `_initPaths` | 低（不可避免） |
| `headless-query.ts` | 7 | jiti 动态导入返回类型 | 中（应定义接口） |
| `register-extension.ts` | 1 | `err.path` 不在 ErrnoException 类型中 | 低（可用类型扩展替代） |
| `state-reconciliation.ts` | 1 | `DriftHandler<any>` 泛型放宽 | 低（应使用 branded type） |

---

## 8. 关键发现与建议

### 8.1 对 Wopal 生态的可借鉴性

| 维度 | 可借鉴程度 | 说明 |
|------|-----------|------|
| **GSD 方法论** | 高 | 三级分解 + 7 阶段流程 + 边界映射是通用方法论，任何工具都能手动遵循 |
| **Skill 格式** | 高 | 纯 Markdown + XML，无平台耦合，可直接适配到 `.claude/commands/` 或 `.cursor/rules/` |
| **扩展架构** | 中 | ExtensionAPI 模式值得参考，但具体实现绑定 GSD 运行时，需重写 |
| **内部工具 → CLI** | 中 | 架构上完全可行（所有数据在 SQLite + 文件系统），需要工程投入提取共享库 |
| **类型系统设计** | 高 | contracts 包的零依赖类型+常量模式、discriminated union 错误分类值得直接采用 |
| **安全模式** | 高 | MCP server 的路径验证、序列化写入、写门控模式值得直接采用 |
| **巨型文件反模式** | 警示 | auto-dispatch.ts 1829 行是可维护性风险，Wopal 应控制文件/函数大小 |

### 8.2 技能的跨平台复用策略

通用性最强的 10 个 Skill（几乎不依赖 GSD 特有概念）：

1. `review` — 代码审查
2. `tdd` — 测试驱动开发
3. `lint` — Lint/Format 自动检测
4. `security-review` — 安全审查
5. `debug-like-expert` — 科学方法论调试
6. `verify-before-complete` — 强制验证
7. `api-design` — API 设计
8. `dependency-upgrade` — 安全依赖升级
9. `observability` — 可观测性设计
10. `test` — 测试生成/运行

复用方式：复制 `SKILL.md` 内容到目标平台的 prompt 加载位置（`.claude/commands/`、`.cursor/rules/` 等）。

### 8.3 集成优先级建议

```
Phase 0: 直接使用
  └─ 在 Claude Code 中通过 .claude/commands/ 加载通用 Skill

Phase 1: CLI 命令提取
  ├─ 提取 @opengsd/workflow-core 共享库
  ├─ 实现 gsd query / decision-save / summary-save / task-complete
  └─ 编写适配 Skill 指导 Agent 调用 CLI

Phase 2: 协议桥接
  ├─ 通过 MCP 协议暴露 GSD 工具给外部 Agent
  └─ 或通过 rpc-client SDK 实现程序化控制

Phase 3: 深度集成
  └─ 将 GSD 工作流引擎作为 Wopal 编排子系统的一部分
```

---

## 9. 附录

### 9.1 21 个扩展清单

| 扩展 | 类型 | 核心能力 |
|------|------|---------|
| gsd | core | 工作流引擎（350+ 文件），工具注册，生命周期管理 |
| subagent | bundled | 子 Agent 派生（single/parallel/chain） |
| claude-code-cli | 无 manifest | Claude Code CLI 作为模型提供者 |
| bg-shell | bundled | 后台 Shell 进程管理 |
| async-jobs | bundled | 异步任务追踪和取消 |
| mcp-client | 无 manifest | MCP 协议客户端 |
| context7 | bundled | 实时库文档获取 |
| search-the-web | bundled | 网络搜索 + 网页抓取 |
| browser-tools | bundled | Playwright 浏览器自动化（60+ 工具） |
| mac-tools | bundled | macOS 无障碍 API 自动化 |
| github-sync | 无 manifest | GSD → GitHub 同步（里程碑/PR/Issue） |
| voice | bundled | 语音输入 |
| visual-brief | bundled | 可视化 HTML 摘要 |
| remote-questions | bundled | Slack/Discord/Telegram 远程交互 |
| cmux | 无 manifest | cmux 终端复用器集成 |
| ttsr | bundled | 零成本流式输出守卫 |
| aws-auth | 无 manifest | AWS 凭据自动刷新 |
| ollama | 无 manifest | 本地 Ollama 自动发现 |
| universal-config | 无 manifest | 跨工具配置读取 |
| slash-commands | bundled | 脚手架生成器 |
| google-search | 已弃用 | 迁移到独立包 |

### 9.2 35 个技能分类

**开发流程类（11）：** create-gsd-extension, create-mcp-server, create-skill, create-workflow, decompose-into-slices, design-an-interface, write-milestone-brief, handoff, grill-me, spike-wrap-up, btw

**代码质量类（8）：** tdd, test, lint, review, security-review, code-optimizer, debug-like-expert, verify-before-complete, forensics

**前端/UI 类（8）：** frontend-design, userinterface-wiki, make-interfaces-feel-better, react-best-practices, core-web-vitals, web-design-guidelines, web-quality-audit, accessibility

**工具类（8）：** agent-browser, api-design, best-practices, dependency-upgrade, github-workflows, observability, write-docs

### 9.3 关键设计模式索引

| 模式 | 位置 | 说明 |
|------|------|------|
| 两阶段加载器 | `src/loader.ts` + `src/cli.ts` | 轻量引导 → 延迟加载 |
| 指纹同步 | `src/resource-loader.ts` | content hash + version 避免重复复制 |
| 拓扑排序扩展加载 | `src/extension-sort.ts` | Kahn BFS 处理依赖 |
| 原子写入 | `src/extension-registry.ts` | writeFileSync(tmp) + renameSync |
| Discriminated Union 错误 | `extensions/gsd/error-classifier.ts` | tagged union，编译器穷尽检查 |
| 双重故障恢复 | `extensions/gsd/tools/complete-task.ts` | rollback 失败也被 catch |
| 渐进披露 Skill | `skills/*/SKILL.md` | Router → Workflow → Reference |
| JSONL 协议 | `packages/rpc-client/src/jsonl.ts` | 自定义 LF 分帧，避免 Unicode bug |
| 序列化写入 | `packages/mcp-server/src/server.ts` | 防止并发 SQLite 写入 |
| 进程级锁 | `extensions/gsd/auto-dispatch.ts` | `writeFileSync` flag `wx` 原子创建 |

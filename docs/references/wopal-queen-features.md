# wopal-queen 功能借鉴清单

> 来源：`labs/fork/sampx/wopal-queen` — oh-my-opencode 插件

---

## 高价值功能

### 1. opencode-skill-loader（33 文件，~3.2k LOC）

**功能**：4 层作用域技能加载（project > opencode > user > global）

**核心能力**：
- YAML frontmatter 解析 SKILL.md 文件
- 技能合并与优先级去重
- 模板解析与变量替换
- Provider 网关（模型特定技能）

**借鉴价值**：WopalSpace 当前技能系统较简单，可参考其多层作用域设计

**文件位置**：`src/features/opencode-skill-loader/`

---

### 2. background-agent（31 文件，~10k LOC）

**功能**：后台任务生命周期管理

**核心能力**：
- 状态机：pending → running → completed/error/cancelled/interrupt
- 并发控制：per-model/provider 限制，FIFO 队列
- 轮询机制：3s 间隔，idle 事件 + 稳定性检测（10s 不变）
- Spawner 模式：8 个专注文件通过 `SpawnerContext` 组合
- **process-cleanup**：进程退出清理（已借鉴）

**借鉴价值**：并发控制、稳定性检测机制

**文件位置**：`src/features/background-agent/`

---

### 3. tmux-subagent（30 文件，~3.6k LOC）

**功能**：Tmux 子代理管理

**核心能力**：
- `TmuxSessionManager`：pane 生命周期、网格规划
- Spawn 动作决策器 + 目标查找器
- 会话健康轮询管理器
- pane 创建/销毁事件处理

**借鉴价值**：持久化沙箱、多窗口协作场景

**文件位置**：`src/features/tmux-subagent/`

---

### 4. mcp-oauth（18 文件，HIGH 复杂度）

**功能**：MCP OAuth 2.0 + PKCE + DCR (RFC 7591) 认证

**核心能力**：
- OAuth 2.0 授权码流程
- PKCE (Proof Key for Code Exchange) 安全增强
- DCR (Dynamic Client Registration) 自动注册
- 支持 MCP server 认证场景

**借鉴价值**：MCP server 接入外部服务时的认证需求

**文件位置**：`src/features/mcp-oauth/`

---

### 5. skill-mcp-manager（12 文件，MEDIUM 复杂度）

**功能**：MCP 客户端生命周期管理

**核心能力**：
- 每个 session 独立的 MCP 客户端
- 支持 stdio + HTTP 两种传输方式
- MCP server 启动/关闭/健康检查

**借鉴价值**：WopalSpace MCP 管理增强

**文件位置**：`src/features/skill-mcp-manager/`

---

## 中价值功能

### 6. context-injector（6 文件，MEDIUM 复杂度）

**功能**：AGENTS.md/README.md 自动注入上下文

**借鉴价值**：优化上下文注入机制

**文件位置**：`src/features/context-injector/`

---

### 7. task-toast-manager（4 文件，MEDIUM 复杂度）

**功能**：任务进度通知

**借鉴价值**：后台任务进度可视化

**文件位置**：`src/features/task-toast-manager/`

---

### 8. hook-message-injector（5 文件，MEDIUM 复杂度）

**功能**：Hook 消息注入

**借鉴价值**：事件钩子系统增强

**文件位置**：`src/features/hook-message-injector/`

---

## 低价值功能（暂不借鉴）

| 功能 | 说明 | 原因 |
|------|------|------|
| builtin-skills | 6 个内置技能 | WopalSpace 有自己的技能体系 |
| builtin-commands | 命令模板 | 已有命令系统 |
| claude-code-* loaders | Claude Code 兼容层 | WopalSpace 专注 OpenCode |

---

## 架构设计参考

### 插件初始化流程

```
OhMyOpenCodePlugin(ctx)
  ├─→ loadPluginConfig()         # JSONC 解析 → 合并 → Zod 验证
  ├─→ createManagers()           # 创建管理器
  ├─→ createTools()              # 注册工具
  ├─→ createHooks()              # 组装钩子
  └─→ createPluginInterface()    # 返回插件接口
```

### 8 个 OpenCode Hook Handler

| Handler | 用途 |
|---------|------|
| `config` | 配置加载（6 阶段） |
| `tool` | 工具注册 |
| `chat.message` | 消息处理 |
| `chat.params` | 参数调整 |
| `chat.headers` | Header 注入 |
| `event` | 事件处理 |
| `tool.execute.before` | 工具执行前 |
| `tool.execute.after` | 工具执行后 |

### 钩子分层

```
createHooks()
  ├─→ createCoreHooks()           # 37 个
  │   ├─ createSessionHooks()     # 23 个
  │   ├─ createToolGuardHooks()   # 10 个
  │   └─ createTransformHooks()   # 4 个
  ├─→ createContinuationHooks()   # 7 个
  └─→ createSkillHooks()          # 2 个
```

---

## 后续行动

| 优先级 | 功能 | 行动项 |
|--------|------|--------|
| P1 | opencode-skill-loader | 研究 4 层作用域设计，评估整合方案 |
| P1 | skill-mcp-manager | 增强 WopalSpace MCP 管理能力 |
| P2 | tmux-subagent | 评估持久化沙箱场景 |
| P2 | mcp-oauth | 需要 OAuth 认证时再研究 |
| P3 | context-injector | 优化上下文注入 |
| P3 | task-toast-manager | 进度通知可视化 |

---

*此文档随研究进展持续更新*
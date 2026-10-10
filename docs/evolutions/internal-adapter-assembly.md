# 新版 ontology 停止装配外部 DSH adapter

## Metadata


- **Type**: refactor
- **Project Path**: .wopal
- **Created**: 2026-10-10
- **Stage**: draft
- **Mode**: (none)
- **Worktree**: (none)
- **Branch**: (none)
- **Base Commit**: (none)
- **Final Commit**: (none)

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

在 Ellamaka 内部 adapter 可用后，新版 ontology 不再装配外部副本；保留旧源码和现有用户参数。

## Technical Context

### Architecture Context

coding 默认装配目前仍声明 dsh-adapter，外部包使用独立 Plugin SDK。Ellamaka unified-sdk Task 4 先完成内置实现与旧条目的提前接管；本提案随后调整声明并准备其联合验收视图，无需等待正式 SDK 发布。runtime-consumer 的 SDK 模板消费在正式发布后再做，避免循环依赖。

### Key Decisions

- D-01: 删除的是新版默认装配引用；plugins/dsh-adapter 源码与依赖暂留，不更新、不安装、不执行。
- D-02: settings.jsonc 的 wopal.pluginConfig.dsh-adapter、sandbox/escalation、三层覆盖保持。不删除整张 plugin 数组或其他插件。
- D-03: 不新增适配器版本协商；旧产品配合保留的旧装配声明/兼容 ontology 版本验证。仅回退 Home 不会恢复新版已移除的外部声明。

### Key Interfaces

新版类型默认装配和生成的 ellamaka.plugin 不含外部 dsh-adapter。内部实现由产品提供，参数键和默认值保持。初始化宿主不替用户改装配文件；已有空间通过正式装配流程更新。

## In Scope

- 新版默认清单、相关装配示例与生成配置不再引用外部 adapter。
- 对已有空间重新物化，核对所有配置层的有效外部引用及参数保留；旧源码/依赖保持。
- 准备 Ellamaka 计划的真实联合验收视图。

## Out of Scope

- 不迁移 SDK 消费，不删除旧 adapter 源码，不增加新行为或修改其依赖。
- 不实施 Config Engine、Plan Scheduler、Session Assembly，不清空用户 Home。

## Affected Files

| Component | Files | Operation | Role |
| --- | --- | --- | --- |
| 装配声明 | assembly/archetypes、必要配置默认值 | 修改 | 新版移除外部引用 |
| 兼容源码 | plugins/dsh-adapter | 保留 | 旧声明的兼容资产 |
| 验证视图 | 由演进流程准备 | 重新物化 | 联合验收 |

## Assembly Intent

| Ref | Scope | 理由 |
| --- | --- | --- |

## Acceptance Criteria

### Agent Verification

1. [ ] 新空间和已有空间重新物化后的有效插件列表均无外部 dsh-adapter；其他插件、settings 注释和用户已有参数保持。
2. [ ] 候选新产品仅提供内部 adapter，无外部源码仍能执行文件/沙箱工具；旧配置条目由新产品在安装/import前接管。
3. [ ] 旧源码/依赖未改；兼容旧产品搭配旧声明的临时 fixture 可运行，不宣称它能消费移除声明后的新版 ontology。

### User Validation

#### Scenario 1: 更新装配后的正常使用
- Goal: 观察已有空间的参数与助理交互；与 Ellamaka 主计划联合验收，不重复做一轮。
- 验证环境：当前 wopal-workspace 的演进验证视图，WOPAL_HOME 为 `/Users/sam/tmp/wopal-e2e/home`，不清空或重置。
- Precondition：候选 Ellamaka 内部 adapter 已通过自动验收，装配已重新物化；Agent 检查有效配置与进程占用。
- 启动命令：`WOPAL_HOME=/Users/sam/tmp/wopal-e2e/home ./.worktrees/ellamaka-feature-upgrade-dsh-v0.2/scripts/dev.sh serve --port 3018 --app-port 3019`，从空间根执行；若候选脚本在另一个工作树，Agent 交付前回填实际路径。
- User Actions：打开脚本输出的 Workbench 地址，进入当前空间，观察 sandbox 参数与一次正常助理交互。
- 通过判据：无需外部 adapter 的装配提示，现有模式可识别，工具交互和错误说明可理解。
- 失败反馈：提供步骤、截图和脱敏提示，由 Agent 检查脚本日志；先保留证据再依次用 dev.sh stop frontend、stop backend 停止本次实例。

- [ ] 用户已完成上述功能验证并确认结果符合预期

## Implementation

### Task 1: 默认装配与已有空间更新

**Verification Intent**: AC#1

**Behavior**:
- 新默认清单不含外部 adapter；已有空间重新物化只移除对应生成引用，其他插件与参数保持。
- 用户显式配置的残留外部引用需清楚报告并按用户授权处理，不改整个 plugin 数组、不删除 pluginConfig。

**Pre-read**: assembly/archetypes/coding.yaml、docs/DESIGN-assembly.md、当前装配物化实现

**Design**:
复用正式装配流程，不在宿主启动时修写空间。保留旧源码，默认不装配。

**TDD**: true

**Changes**:
1. RED：为新建/重装配与配置保留写失败断言，记录实际命令。
2. GREEN：移除默认外部引用，重新物化验证视图。
3. REFACTOR：清理相关示例，复验。

**Verify**: 用真实装配 fixture 核对有效插件与配置保留，RED 阶段回填命令。

**Done**:
任务产出与实际触碰文件：实施完成后记录。
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤。

### Task 2: 内部独立运行与旧配置回归

**Verification Intent**: AC#2, AC#3

**Behavior**:
- 新产品无需外部目录或独立 SDK，正常文件/沙箱执行；旧外部项不触发安装、import 或工厂。
- 旧产品使用兼容旧声明，旧源码和依赖无变化；两种产品使用隔离临时 Home。

**Pre-read**: Ellamaka DESIGN-ellamaka-tools.md、unified-sdk Task 4 的候选交付

**Design**:
自动验证独立运行和旧组合；已有 e2e Home 只做主计划的正常用户交互。

**TDD**: true

**Changes**:
1. RED：将行为变成可执行跨项目断言，回填命令。
2. GREEN：验证正确声明与候选产品。
3. REFACTOR：复核有效配置，准备联合 UV。

**Verify**: 运行候选产品与真实声明的临时 fixture；核对旧源码 Git 摘要。

**Done**:
任务产出与实际触碰文件：实施完成后记录。
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤。

## Delegation Strategy

按用户要求人工推进，本轮只规划、不启动实施。Task 1 后执行 Task 2；通过后先联合 UV，再由用户授权整合，不绕过演进机制。

## Delivery

本提案位于 Ellamaka Task 4 与其联合 UV 之间；不等待新 SDK 发布。正式 SDK 发布后再实施 runtime-consumer 与 Wopal SDK 消费。同步与上游贡献由用户另行决定。

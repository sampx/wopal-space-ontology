# GAPS — 设计优化落地追踪

> **Status**: Active
> **Updated**: 2026-09-14
> **Parent Architecture**: `./DESIGN.md`
> **Companion**: 本文档追踪 2026-09 设计优化（中央能力池 + 装配 worktree + `space sync`）的目标态与实现落地偏差，按项目归属拆分，逐项解决后关闭。

---

## 背景

2026-09 设计优化确立「中央能力池 + 空间装配 worktree」模型：local main 集中维护能力，空间按装配单 sparse-checkout 物化为可写 worktree，进化经 `space sync` 汇入 local main，类型语义由装配单承载（不设 `type/*` 分支）。

设计已定稿并归一至 DESIGN / DESIGN-distribution / 产品级 DESIGN / wopal-cli DESIGN。以下为**实现落地 gap**，按项目归属拆分。

---

## 项目归属

| 项目 | 负责的落地项 |
|------|-------------|
| **wopal-cli** | `space sync`、`space status`、`space capability`、`ontology` 命令面改造、装配物化与类型骨架消费、装配定义读取、`prepare-ontology` 装配语义（onboarding CLI machine operation） |
| **ontology** | 装配定义目录（装配单 / 骨架 / 模板）、类型骨架分化、Agent 体系资产清理、Evolver 等新代理、space-master 技能对齐、武器库清单与派发装配契约 |
| **ellamaka** | Desktop onboarding 契约消费对齐（`prepare-ontology` 返回契约变化后，`onboarding-ipc.ts` 的 `availableTypes` 消费与测试联动）；插件相对路径规范化缺陷（已修复）；技能与 MCP 的会话级权限判定 |
| **wopal-plugin** | 武器库扫描与能力清单工具、`wopal_task` 装配参数与权限合成、规则按会话注入、子会话权限注入通道 |

---

## Gap 清单

### CLI-G1: `space sync` 双向同步命令未实现（wopal-cli, P0）

**目标态**: `wopal space sync` 与 local main 双向对齐——先上行（隔离临时 worktree 整合空间独有进化，成功才推进、冲突即停）、后下行（fast-forward 到 local main 最新）、刷新装配版本。dry-run 预览 → `--confirm` 执行。

**当前状态**: wopal-cli 仍实现旧的 `space update`（merge type/*）与 `space contribute`（squash 到 type/*）；`space sync` 不存在。

**落地**: 新增 `space sync`，移除 `space update` / `space contribute`；实现定序、隔离整合、fast-forward 与工作区状态检查。

### CLI-G2: `space status` / `space capability` 未对齐新语义（wopal-cli, P0）

**目标态**: `space status` 展示空间分支 ↔ local main 同步状态 + 装配状态；`space capability add/remove` 增删装配单能力并重新物化（移除含未提交修改的能力时保留文件并警告）。

**当前状态**: `space status` 仍展示 space ↔ type 分支；`space capability` 不存在。

### CLI-G3: ontology 命令面改造未实现（wopal-cli, P0）

**目标态**: `ontology install` 只物化 local main + 类型装配单；`ontology update` 仅 upstream/main → local main（无 top-down 多分支）；`ontology contribute` 仅 fork 模式、local main → upstream PR；删除 `ontology reconcile` / `ontology promote`。

**当前状态**: `install` 物化全部 type/* 分支；`update` top-down 多分支合并；`reconcile` / `promote` 仍在命令面。

### CLI-G4: Space Init 装配物化未实现（wopal-cli, P0）

**目标态**: `space init --type <type>` 读取 `assembly/archetypes/<type>.yaml` 装配单与其 `schema` 指向的骨架，sparse-checkout 物化 `.wopal/` worktree，写入 `.wopal-space/space-meta.json`。

**当前状态**: `space init` 映射 `type/<type>` 分支、materialize 全量 worktree，无装配单消费、无类型骨架消费、无 space-meta.json。

### CLI-G5: 装配技术可行性已验证，需固化实现规范（wopal-cli, P0）

**目标态**: 装配物化基于 Git `worktree` + `sparse-checkout` + `merge --ff-only` + 隔离临时 worktree，正常推进全 fast-forward，冲突在隔离 worktree 中处理。

**当前状态**: 技术在 `.wopal-space/.tmp/git-assembly-spike.*` 已实测通过（独立装配、快进更新/贡献、事务隔离、脏文件保护），未固化进实现。

### CLI-G6: CLI 未消费类型骨架（wopal-cli, P0）

**目标态**: `space init --type <type>` 读取装配单的 `schema` 字段，按所选骨架创建空间结构；骨架缺失或格式错误时以 fail fast 报错，保持 space registry 与 active space 状态不变。

**当前状态**: CLI 从 `join(wopalDir, "templates")` 读取单一 `wopalspace-schema.yaml`，所有空间使用同一套骨架。

**落地**: 改从 `assembly/archetypes/` 读装配单、`assembly/schemas/` 读骨架；实现 `schema` 字段解析与稳健的错误兼容；按装配单生成空间特有插件配置到 `settings.local.jsonc`；写出 `.wopal-space/space-meta.json`。

### ONB-G1: onboarding `prepare-ontology` 装配语义未实现（wopal-cli, P0）

**目标态**: onboarding 的 `prepare-ontology`（CLI machine operation）物化 local main 与装配定义（`assembly/archetypes/*.yaml`、`assembly/schemas/*.yaml`），供 `space init --type` 消费；类型选择走装配单而非 type/* 分支。

**当前状态**:
- 设计文档已对齐：产品级 `DESIGN-onboarding.md` 的 `prepare-ontology` 已更新为"物化 local main 与类型装配单"；产品级 DESIGN 与 ellamaka onboarding 文档均已明确「operation 语义由 wopal-cli 实现、ellamaka/Desktop 仅消费」的边界。
- wopal-cli 实现仍残留 type/*：`setup-operations.ts` `prepare-ontology` 收集并物化全部 `type/*` 分支；`types/cli.ts` 的 `BehindCommonAnalysis` / `AheadOfCommonAnalysis` 均基于 type/* 分支。需随 CLI-G3 一并改造。

### ONT-G1: 装配定义目录未建立（ontology, P0）

**目标态**: 装配定义集中于 `.wopal/assembly/`，含 `archetypes/`（类型装配单）、`schemas/`（空间骨架）、`templates/`（渲染素材）；`config/` 只保留 settings 类配置。装配定义作为物化源头保留在中央仓库，不物化进空间。本地中央仓库 `main` 是能力合集，不对应任何空间类型。

**当前状态**: 装配单已建立于 `config/types/`（coding、content），但与 settings 混处，语义混乱；模板位于根目录 `templates/`；骨架内嵌于模板目录，未独立；装配单未声明所用骨架。

**落地**:
- 建立 `assembly/archetypes/`、`assembly/schemas/`、`assembly/templates/` 三级结构。
- 装配单从 `config/types/` 迁入 `assembly/archetypes/`，新增 `schema` 字段与 `scripts` 能力类目。
- 骨架从 `templates/wopalspace-schema.yaml` 拆分，按类型独立为 `assembly/schemas/<type>-space-schema.yaml`。
- 模板迁入 `assembly/templates/`。

### ONT-G5: 空间结构未按类型分化（ontology, P0）

**目标态**: 不同空间类型拥有不同骨架——coding 空间建立 `projects/`，content 空间建立 `contents/`，结构差异由装配单的 `schema` 字段选择。

**当前状态**: `wopalspace-schema.yaml` 硬编码 `projects/`、`contents/`、`docs/` 三个目录，所有空间物化为同一套布局。

**落地**:
- 按类型拆分骨架：`coding-space-schema.yaml` 声明 `projects/` 与 `docs/`；`content-space-schema.yaml` 声明 `contents/` 与 `docs/`。
- 共享部分（runtime 骨架、memory、logs 等）在两套骨架中各自声明，由装配单的 `schema` 字段选择。

### ONT-G2: Agent 体系资产未清理、未新建、未瘦身（ontology, P0）

**目标态**: `agents/` 仅含四维核心角色（wopal/fae/rook/evolver），跨类型常驻；类型差异由装配单的 skills / rules 承载；核心提示词保持精简，只承载角色定位、职责边界、能力武器纪律与交互风格。

**当前状态**: ✅ 已完成。
- 四核心齐备：`wopal`、`fae`、`rook`、`evolver`，跨类型常驻。
- 核心提示词已精简：wopal 97 行、fae 82 行、rook 101 行、evolver 65 行，各含能力武器纪律章节。
- 提示词不再假设任务来源，任务可来自用户直接委派或 Wopal。

### ONT-G3: WSF 资产与新装配模型关系未定义（ontology, P1）

**目标态**: `.wopal/wsf/` 遗留资产处置明确。

**当前状态**: ✅ 已解决——WSF 资产经决策移除（其为 space-flow 产品仓的内容快照，新装配模型下无运行时引用，活体归 `projects/space-flow`）。

### ELL-G1: Desktop onboarding 消费 `prepare-ontology` 契约需对齐（ellamaka, P0）

**目标态**: `prepare-ontology` 返回契约从「type/* 分支列表」改为「装配单类型列表」后，ellamaka Desktop 的消费逻辑与测试随之对齐。

**当前状态**: `packages/ellamaka-desktop/src/main/onboarding-ipc.ts` 消费返回的 `availableTypes`（L883-893、L1188、L1457-1586，fallback 已是 `[{ type: "common", branch: "main" }]`）；`setup-machine-client.ts` 为 `prepare-ontology` 特设 300s 超时（L86）；`onboarding-ipc.test.ts` / `setup-machine-client.test.ts` 的 mock 契约需联动。当前契约仍沿用 type/* 分支语义。

**落地**: 契约变更定稿后，对齐 `onboarding-ipc.ts` 消费逻辑、复核 `setup-machine-client` 超时与探测，更新两处测试 mock。

### DOC-G1: space-master 技能仍描述旧多分支模型（ontology, P1）

**目标态**: `space-master` 技能的 ontology 维护指南对齐新模型（space sync、装配、Evolver 回流），去除 type/* 分支与 promote/reconcile 流程。

**当前状态**: `skills/space-master/SKILL.md` 及 `references/ontology-maintenance.md` 仍描述 main → type/* → space/* 三层分支与 space contribute / ontology promote。

### SETTINGS-G1: settings.jsonc 中 plugin 绝对路径污染 central main（ontology, P0）

**目标态**: `settings.jsonc` 人工维护、随 main 分发、CLI 永不改写；其中插件以相对空间 config 目录的路径引用（`../plugins/<name>`）。CLI 只写 gitignored 的 `settings.local.jsonc`。

**当前状态**: ✅ 已完成。
- `.wopal/config/settings.jsonc` 的 `ellamaka.plugin` 已改用相对路径（`../plugins/<name>`），随 main 分发不再携带实例绝对路径。
- 相对路径解析依赖的 ellamaka 缺陷已修复并验证（见 ELL-G2）。
- 相对路径声明必须使用合法 Spec 形态：无 options 时写裸字符串，禁止单元素数组 `["path"]`（不是合法的 `String | [String, Options]` 形态，会致整个 ellamaka 配置块解析失败被跳过）。

**落地**: settings 分层写入权契约已记录于 DESIGN「配置分层与写入权」。CLI 只写 `settings.local.jsonc`，永不改写 `settings.jsonc`。

### ELL-G2: WopalSpace settings 加载跳过 plugin 相对路径规范化（ellamaka, P0）

**目标态**: `settings.jsonc` / `settings.local.jsonc` 中的插件相对路径，在 WopalSpace 模式下以声明它的 config 文件为基准规范化为绝对路径。

**当前状态**: ✅ 已修复并验证（issue #227，提交 `db2dd48f12`）。

**根因**: `config.ts` 的 `loadConfig` 只在 `{ path }` 分支调用 `resolveLoadedPlugins`，WopalSpace settings 走 `{ dir, source }` 分支时被 early return 跳过，相对路径最终按进程 CWD 解析，导致 `Cannot find module` 与插件加载失败。

**修复**: 将 `resolveLoadedPlugins` 移至 early return 之前，两分支共用、以 `source` 为基准；连带修复规范化后暴露的去重碰撞（目录式插件入口均为 `index.*`，按 basename 取身份会合并不同插件，改为按包目录识别）。

**验证**: 用户重启 ellamaka 后确认 serve 日志 target 指向 `.wopal/plugins/...`、插件日志正常输出。

### PLUGIN-G2: prompts 应内置进 wopal-plugin（ontology, P1）

**目标态**: `plugins/wopal-plugin` 内置 title / distill / dedup 提示词默认值（现有 fallback 常量机制），`prompts/` 目录退出必装能力，文件层仅作可选覆盖。

**当前状态**: `prompts/{title,distill,dedup,commit-msg-gen}.md` 由 `wopal-plugin/src/context/prompts.ts` 按「空间 `.wopal/prompts/` → 用户级 `WOPAL_HOME/prompts/`」多层加载，目录被当作空间可装配资产。

**落地**: 将默认提示词内化进插件源码，移除对 `prompts/` 目录的必装依赖，保留文件覆盖路径。

### PLUGIN-G3: tui-ellamaka 插件未正规化（ontology, P1）

**目标态**: `plugins/tui-ellamaka/` 为标准插件目录，含 `index.tsx`、`package.json`、`ellamaka-theme.json` 与 `asset/`（5 个 wav 音频资源）；settings.jsonc 以相对路径 `../plugins/tui-ellamaka` 引用。

**当前状态**: `plugins/tui-ellamaka.tsx` 为散落单文件（32KB），主题 `plugins/ellamaka-theme.json` 与音频资源 `plugins/asset/`（1.1MB）独立散落在插件根；插件代码以 `./ellamaka-theme.json`、`import.meta.dir + "/asset"` 与 `./asset/*.wav` 引用。

**落地**: 建立 `plugins/tui-ellamaka/` 目录，迁入 `index.tsx`、`ellamaka-theme.json` 与 assets（`asset/` 随迁）；代码引用为相对插件文件解析，迁移后无需改动；更新 settings.jsonc 引用为目录形式。`plugins/dsh-adapter` 保持纯 file 插件，不补 package.json。

### ASSEMBLY-G1: 引擎侧技能可见性未支持会话级权限（ellamaka, P0）

**目标态**: 技能可见性判定综合角色基线与会话级权限，使 Wopal 为会话装配的技能能够出现在该会话的可用技能清单中。

**当前状态**: 技能可见性判定只读角色基线（`skill/index.ts` 的 `available()` 接收 `agent` 并仅按 `agent.permission` 过滤；`session/system.ts` 的技能段注入同样只依据角色基线）。会话级权限无法影响技能可见性，运行时装配技能后技能不会出现在子会话的可用清单中。

**落地**: 扩展技能可见性判定，接收并合并会话级权限规则；同步调整系统提示词技能段的注入判定。技能执行时的授权判定已综合两侧规则，无需调整。

### ASSEMBLY-G2: MCP 工具未纳入权限过滤（ellamaka, P1）

**目标态**: MCP 工具的可见性与执行授权纳入权限规则判定，可按会话装配。

**当前状态**: MCP 工具按连接状态收集（`mcp/index.ts` 的 `tools()`），不经过权限规则过滤。

**落地**: 在 MCP 工具收集路径加入权限规则判定，与技能保持一致的作用域语义。

### ASSEMBLY-G3: 武器库扫描与能力清单工具未实现（wopal-plugin, P0）

**目标态**: 插件启动时扫描空间 worktree 构建武器库清单，并通过 `wopal_capability_list` 工具提供给 Wopal；清单含未授予任何角色基线的能力，每项携带名称、描述与物理路径。

**当前状态**: 插件无武器库概念，无能力清单工具。技能与规则的物理清单只存在于各自模块的内部扫描结果中。

**落地**: 实现武器库扫描（技能、规则、MCP），构建清单结构；新增 `wopal_capability_list` 工具暴露清单。

### ASSEMBLY-G4: `wopal_task` 未支持能力装配参数（wopal-plugin, P0）

**目标态**: `wopal_task` 接受 `capabilities` 参数（`skills` / `rules` / `mcp` 名称数组），派发时合成会话级权限并注入子会话，实现超越角色基线的运行时装配。

**当前状态**: `wopal_task` 只接受 `description` / `prompt` / `agent`。子会话创建后以 `promptAsync` 的 `tools` 参数传递工具开关，该参数为引擎的兼容形态，会整体替换会话级权限。

**落地**: 新增 `capabilities` 参数；派发流程改为在会话创建后经会话更新接口注入合成权限；移除 `promptAsync` 的 `tools` 传参，避免兼容形态替换已注入的权限。

### ASSEMBLY-G5: 规则注入未按会话装配（wopal-plugin, P0）

**目标态**: 规则注入读取会话级装配结果，只注入该会话被授予的规则，并保持既有的提示词匹配与去重行为。

**当前状态**: 规则注入按角色名与提示词关键词匹配（`hooks/rule-injector.ts`、`rules/matcher.ts`），无会话级装配概念。

**落地**: 规则注入路径接入会话级装配结果，按授予范围过滤可用规则集，保留既有匹配与去重逻辑。

### ASSEMBLY-G6: `agents/*.md` 权限块含通配键（ontology, P1）

**目标态**: 角色权限块的键使用工具的真实标识，语义明确无歧义。

**当前状态**: fae / rook / evolver 的权限块使用 `wopal_*` 通配键覆盖插件工具。

**落地**: 待插件工具标识命名规范确立后统一调整，确保插件工具与内置工具的权限键语义清晰。

### TEMPLATES-G1: templates 与装配定义保留在 ontology（ontology + wopal-cli, P1）

**目标态**: 空间骨架、模板与类型装配单留在 ontology，作为中央能力池的装配定义；wopal-cli 从中央仓库读取装配定义并物化到空间。模板的版本管理与维护归属 ontology，与空间结构契约的治理面一致。

**当前状态**: 装配定义散落——`templates/` 位于 ontology 根目录，装配单位于 `config/types/`，骨架未独立，三者语义混杂。CLI 的 `schema-consumer.ts` / `space-initializer.ts` 从 `join(wopalDir, "templates")` 读取。

**落地**:
- ontology 侧建立 `assembly/` 目录，收纳 `archetypes/`（类型装配单）、`schemas/`（空间骨架）、`templates/`（渲染素材）；`config/` 只保留 settings 类配置。
- 装配单新增 `schema` 字段指向所用骨架，使空间结构成为类型差异的一部分。
- wopal-cli 改从 `assembly/` 读取装配定义，并对缺失、路径错误、版本不匹配做稳健处理与明确报错。

---

## 落地方式：讨论直施 + 两个 Plan

P1 为设计与资产决策，由 Wopal 与用户讨论定稿后直接实施，不走 Plan 生命周期。P2/P3 为代码实现，各成一个 Plan，按仓库聚合。

| 项 | 形态 | 仓库 | 覆盖 gap | 范围 | 依赖 |
|------|------|----------|------|------|------|
| **P1** | 讨论直施 | ontology | ONT-G1、ONT-G5、DOC-G1、SETTINGS-G1、PLUGIN-G2、PLUGIN-G3、ASSEMBLY-G6 | 装配定义目录 `assembly/{archetypes,schemas,templates}`；类型骨架分化；Evolver 建立；核心提示词瘦身；settings 相对路径与分层契约；prompts 内置进插件；tui 插件正规化；space-master 对齐 | 无 |
| **P2** | Plan | wopal-cli | CLI-G1~G6、ONB-G1、TEMPLATES-G1 | `space sync`/`status`/`capability`；`ontology install/update/contribute` 改造；删除 `reconcile`/`promote`；`space init` 装配物化与类型骨架消费；装配技术固化；`prepare-ontology` 装配语义；装配定义读取与错误兼容 | P1（消费装配单） |
| **P3** | Plan | ellamaka | ELL-G1、ASSEMBLY-G1、ASSEMBLY-G2 | Desktop onboarding 消费新 `availableTypes` 契约、`setup-machine-client` 复核、测试联动；技能可见性支持会话级权限；MCP 纳入权限过滤 | P2（契约定稿） |
| **P4** | Plan | wopal-plugin | ASSEMBLY-G3、ASSEMBLY-G4、ASSEMBLY-G5 | 武器库扫描与 `wopal_capability_list`；`wopal_task` 能力装配参数与权限合成；规则按会话装配 | P3（引擎判定就绪） |

> ELL-G2 已作为独立 bug 修复完成（issue #227，提交 `db2dd48f12`），不进入 P3 范围。

### 直接动作（不建 Plan）

- ✅ 移除 `.wopal/wsf/` 遗留资产（ONT-G3）
- ✅ 移除 8 个微型伪专员（ONT-G2 删除部分）

### 实施顺序

```text
P1 装配资产落地（讨论直施）
  → P2 wopal-cli 命令面与装配实现（Plan）
    → P3 ellamaka 引擎会话级权限判定（Plan）
      → P4 wopal-plugin 运行时装配实现（Plan）
```

顺序理由：P1 的装配单是 P2 全部装配物化的硬输入前提；P2 定稿 `prepare-ontology` 返回契约后，P3 才能对齐消费端；P3 打通引擎侧的会话级权限判定后，P4 的装配注入才有生效落点。每个 Plan 内部 Task 按文件域分组，可委派多个 fae 并行。

---

## Related Documents

| 文档 | 说明 |
|------|------|
| `./DESIGN.md` | 设计目标态真相源（Ontology 协作模型章节） |
| `./DESIGN-distribution.md` | 分发与装配契约 |
| `../../projects/wopal-cli/docs/DESIGN.md` | CLI 命令面设计与空间装配实现 |
| `../../docs/products/wopal-space/DESIGN.md` | 产品级架构（Ontology 装配模型章节） |

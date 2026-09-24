# enhance-plugins-consumer-migration

## Metadata

- **Type**: enhance
- **Project Path**: .wopal
- **Created**: 2026-09-19
- **Stage**: validating
- **Mode**: isolated
- **Worktree**: .worktrees/ontology-enhance-plugins-consumer-migration
- **Branch**: ontology-enhance-plugins-consumer-migration
- **Base Commit**: 481dd5f3331477ebc3c12a7c7dc6091bea24e303
- **Final Commit**: f7866f5ad97ea61416b1df569f8e5d670c3a5a37

## Scope Assessment

- **Complexity**: Medium
- **Confidence**: High

## Goal

将 `wopal-plugin` 与 `dsh-adapter` 两个核心插件从「手抄 fork 扩展类型 + 寄生依赖 + 混合包管理器 + 配置写入断裂」迁移重构为「显式声明 `@wopal/ellamaka-plugin` 与 `@wopal/ellamaka-sdk` 依赖、纯 Bun 工具链开发、零手抄类型、统一通过 `wopal.pluginConfig` 读取配置（插件条目零内联 options）」，一次性闭合 ONT-G4 并消除所有契约与依赖异味。

## Technical Context

### Architecture Context

两个插件深度消费 ellamaka fork 插件契约层与 SDK 层的扩展（`wopalSpaceRoot`、`chat.params.systemMetadata`、`tool.provider`、`ToolContext.extra`，以及 `/v2` client），同时在配置消费上存在历史断裂：

1. **契约类型与实现分离**：`wopal-plugin` 在 `src/types.ts` 手抄了 `SystemPromptMetadata` / `SystemPromptSection` / `SystemPromptSectionKind` 三个类型（与 fork 契约层同构），依赖声明写的是上游 `@opencode-ai/plugin@~1.15.13`，运行时靠 fork 引擎注入扩展字段。
2. **SDK 依赖未对齐**：`wopal-plugin` 在 `src/index.ts` 导入 `@opencode-ai/sdk/v2` 的 `createOpencodeClient`，在 `src/hooks/system-transform.ts` 导入 `@opencode-ai/sdk` 的 `Model` 类型，依赖声明写的是上游 `@opencode-ai/sdk@~1.15.13`，需随品牌化统一收敛到 `@wopal/ellamaka-sdk`。
3. **dsh-adapter 寄生依赖**：`dsh-adapter` 连 `package.json` 都没有，直接放在 `.wopal/plugins/dsh-adapter/`，import 的 `@opencode-ai/plugin` 依赖完全靠寄生 `wopal-plugin` 的依赖安装产物或引擎全局注入解析。
4. **工具链混乱**：`wopal-plugin` 曾误引入 `pnpm-lock.yaml` 与 `pnpm-workspace.yaml`，导致双锁文件冲突且 pnpm 的隔离软链布局破坏了 `tsc --noEmit`。经排查，插件开发标准为纯 Bun，原生构建由 `package.json` 的 `trustedDependencies` 承载。
5. **ONT-G4 配置断裂（Plugin Side）**：`dsh-adapter` 的沙箱选项和策略当前依赖插件挂载条目的内联 options 注入，无继承、面板不可达、schema 不覆盖；根据 `DESIGN-config-cli.md` 与 `DESIGN-config-settings.md` 的目标态，插件条目必须保持零内联配置，所有本体生态插件行为配置统一通过轻量共享/复用配置读取器从 `wopal.pluginConfig.<插件名>` 读取，插件只读不写。

设计真相源已在 `projects/ellamaka/docs/DESIGN-distribution.md`（npm 包发布机制）、`.wopal/docs/DESIGN-wopal-plugin.md`、`.wopal/docs/DESIGN-dsh-adapter.md`、`projects/wopal-cli/docs/DESIGN-config-cli.md` 与 `docs/products/wopal-space/DESIGN-config-settings.md` 确认。

**参考资料**：
- `projects/ellamaka/docs/DESIGN-distribution.md` — npm 包发布机制（包身份、版本策略、兜底 pin）
- `.wopal/docs/DESIGN-wopal-plugin.md` — wopal-plugin 的 Plugin SDK Contract 与 Configuration 章节
- `.wopal/docs/DESIGN-dsh-adapter.md` — dsh-adapter 的 Plugin SDK Contract 与配置读取章节
- `projects/wopal-cli/docs/DESIGN-config-cli.md` — 插件配置注入与 `pluginConfig` 规范
- `docs/products/wopal-space/DESIGN-config-settings.md` — 全局三层配置与 settings 顶层 `wopal` 节点设计

### Key Decisions

- D-01: 两个插件改声明 `@wopal/ellamaka-plugin` 为直接依赖，版本跟随产品主版本（纯 `x.y.z`，如 `2.0.5`）。
- D-02: `wopal-plugin` 同步改声明 `@wopal/ellamaka-sdk` 为直接依赖，消费点从 `@opencode-ai/sdk` 切换为 `@wopal/ellamaka-sdk`（含 `/v2`）。
- D-03: `wopal-plugin` 删除 `src/types.ts` 中手抄的 `SystemPromptMetadata` 等三个类型，改从 `@wopal/ellamaka-plugin` 导入。
- D-04: `dsh-adapter` 补齐 `package.json`（声明 `@wopal/ellamaka-plugin` 依赖与插件元数据），不再依赖同目录其他插件的依赖安装结果。
- D-05: 两个插件声明的 `@wopal/ellamaka-plugin` 版本必须严格一致（D-06 同步约束）——引擎的 `collectPluginDeps` 用 Map 聚合所有插件依赖，同名依赖后者覆盖前者；版本不一致会导致安装结果不确定。
- D-06: 插件依赖仍由引擎的插件依赖收集机制安装到 `.wopal/` 运行时 node_modules，不改变安装路径。
- D-07: `@wopal/ellamaka-*` 包已发布至 npm（2.0.5、2.0.6，latest 为 dist-tag）；本地验证直接声明依赖，走引擎依赖收集安装机制（重启触发）或插件本地 `bun install`，不做 symlink 接线。`.wopal/node_modules/@wopal/` 下的旧 symlink 接线已悬空（目标 worktree 已删除），实施前需清理。
- D-08: 确立纯 Bun 开发工具链铁律：清理所有 pnpm/npm 遗留锁文件与配置，锁文件仅认 `bun.lock`；native build 由 `trustedDependencies` 管理。
- D-09: 修正 `DESIGN-wopal-plugin.md` 内部目标态自相矛盾（消除"本地 types.ts 定义"历史遗留句，与依赖声明章节保持一致）。
- D-10 (ONT-G4): 收敛插件配置消费面。`wopalPluginConfigSchema` 扩展支持可选的 `pluginConfig` 节点；`dsh-adapter` 优先从 `wopal.pluginConfig.dsh-adapter` 读取行为配置（回退支持 rawOptions 兼容），彻底支持插件条目零内联 options。

### Key Interfaces

`wopal.pluginConfig` 配置结构（Zod 定义）：

```typescript
pluginConfig: z.record(z.string(), z.record(z.string(), z.unknown())).optional()
```

`dsh-adapter` 行为配置定义（`wopal.pluginConfig.dsh-adapter`）：

```typescript
export interface DshAdapterConfig {
  sandbox?: {
    enabled: boolean;
    mode?: "read-only" | "workspace-write";
  };
  escalation?: "ask" | "never";
}
```

## In Scope

- `wopal-plugin` 依赖迁移：`package.json` 声明 `@wopal/ellamaka-plugin` 与 `@wopal/ellamaka-sdk`，移除 `@opencode-ai/*` 依赖，改 import fork 包
- `wopal-plugin` 类型去重：删除 `src/types.ts` 中手抄类型定义
- `wopal-plugin` 消费点切换：`src/index.ts`、`src/hooks/system-transform.ts` 等切换为新包导入
- `wopal-plugin` 配置模型扩充：`schema.ts` 支持 `pluginConfig` 节，使本体生态插件配置走统一继承链
- `dsh-adapter` 补齐 `package.json` 并声明 `@wopal/ellamaka-plugin` 依赖，切换 `index.ts` 的 import 来源
- `dsh-adapter` 配置消费迁移（ONT-G4）：支持从三层 settings 的 `wopal.pluginConfig.dsh-adapter` 读取沙箱与升级策略，支持零内联 options
- 确立 Bun 单一工具链：彻底清除 pnpm 相关配置，验证 `bun run typecheck` 与 `bun run test:run` 全绿
- 修订相关文档：消除 `DESIGN-wopal-plugin.md` 目标态自相矛盾并更新配置架构，加固 `wopal-plugin/AGENTS.md` 工具链铁律

## Out of Scope

- `@wopal/ellamaka-plugin` / `@wopal/ellamaka-sdk` 的品牌化与 npm 发布（归 ellamaka 侧 Plan `feature-npm-plugin-sdk-publish`）
- 引擎侧 `config.ts` 的 pin 逻辑调整（归 ellamaka 侧）
- CLI 侧 `wopal config` 命令族与 operation 实现（归 CLI 侧 P-J 槽位）
- 运行时能力装配（ONT-G1 ~ ONT-G3，依赖 ellamaka P-C 完成后再行动）
- 配置写入端与 settings 迁移：`wopal.pluginConfig` 的值本次由用户手工调整（不做迁移步骤）；待 wopal-cli `config` 命令族落地（CLI P-J）后经 CLI 配置与管理
- `tui-ellamaka` TUI 插件迁移：其仍消费 `@opencode-ai/plugin/tui`（无 package.json），本次不覆盖。风险备忘：引擎依赖重装剪除未声明包后 TUI 插件可能加载失败——后续提案处理（切换 `@wopal/ellamaka-plugin/tui` 或补自有 package.json）

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| wopal-plugin 依赖 | `.wopal/plugins/wopal-plugin/package.json` | 修改 | 声明 `@wopal/ellamaka-plugin` 与 `@wopal/ellamaka-sdk` 依赖，移除 `@opencode-ai/*` |
| wopal-plugin 类型 | `.wopal/plugins/wopal-plugin/src/types.ts` | 修改 | 删除手抄 SystemPrompt 类型，改 import |
| wopal-plugin 消费点 | `.wopal/plugins/wopal-plugin/src/index.ts`、`src/hooks/system-transform.ts`、`src/tools/*.ts` 等 | 修改 | 包导入来源切换为 `@wopal/ellamaka-*` |
| wopal-plugin 配置 | `.wopal/plugins/wopal-plugin/src/config/schema.ts` | 修改 | schema 扩展 `pluginConfig` 节点 |
| dsh-adapter 依赖 | `.wopal/plugins/dsh-adapter/package.json` | 创建 | 补齐包声明与依赖 |
| dsh-adapter 消费与配置 | `.wopal/plugins/dsh-adapter/index.ts` | 修改 | 切换 import 来源，支持从 `wopal.pluginConfig.dsh-adapter` 读配置 |
| 工具链与测试 | 两个插件的测试与锁文件（`bun.lock`） | 修改/验证 | 确保 Bun 环境测试与类型检查全绿，增加配置读取测试 |
| 设计文档 | `.wopal/docs/DESIGN-wopal-plugin.md` | 修改 | 消除目标态描述矛盾，补齐 SDK 声明与 `pluginConfig` 说明 |
| 项目规范 | `.wopal/plugins/wopal-plugin/AGENTS.md`、`AGENTS.zh-CN.md` | 修改 | 加固 Bun 工具链与契约类型使用规范 |

## Acceptance Criteria

### Agent Verification

1. [ ] `wopal-plugin` 的 `package.json` 依赖声明已迁移：包含 `@wopal/ellamaka-plugin` 与 `@wopal/ellamaka-sdk`（纯 `x.y.z` 稳定版本），且不再包含 `@opencode-ai/*` 依赖；`src/types.ts` 不再定义手抄的 `SystemPromptMetadata` 等类型，两个插件目录内（源码、测试与 package 清单）无 `@opencode-ai/*` 导入残留（`bun.lock` 随 `bun install` 再生成）。
2. [ ] `dsh-adapter` 目录包含合法的 `package.json`，声明 `@wopal/ellamaka-plugin` 依赖且版本与 `wopal-plugin` 保持一致，`index.ts` 无 `@opencode-ai/*` 导入残留。
3. [ ] ONT-G4 闭合验证：`dsh-adapter` 在插件条目零 options 时，能正确从 `wopal.pluginConfig.dsh-adapter` 读取沙箱配置（`sandbox.enabled`、`sandbox.mode`、`escalation`）且行为等价；`wopal-plugin` 配置 schema 支持 `pluginConfig` 节点校验。
4. [ ] 工具链纯净性验证：插件目录下无任何 `pnpm-lock.yaml` / `pnpm-workspace.yaml` / `package-lock.json`，`bun run typecheck` 退出码为 0，`bun run test:run` 全绿，`dsh-adapter` 测试全绿。
5. [ ] 依赖收集自洽：引擎的 `collectPluginDeps` 能同时识别两个插件的依赖，依赖清单与运行时 pin 一致。
6. [ ] 文档与规范一致：`DESIGN-wopal-plugin.md` 描述完全对齐目标态；`AGENTS.md` 明确规定 Bun 单一工具链与 `trustedDependencies` 规则。

### User Validation

#### Scenario 1: 真实引擎加载插件且依赖、契约与配置自洽

- Goal: 用户确认迁移后两个插件在 ellamaka 引擎中正常加载，依赖声明与运行时一致，且 `dsh-adapter` 通过配置生效
- 验证环境: 本空间 `.wopal`（wopal-plugin 与 dsh-adapter 的实际运行位置）
- Precondition: `@wopal/ellamaka-*` 包已就绪（本地 symlink 或 npm 已发布）
- 启动命令: `cd /Volumes/U500G/coding/wopal-workspace && ellamaka serve`（或重启引擎）
- User Actions:
  1. 启动或重启 ellamaka serve，观察 `serve-*.log`
  2. 确认日志无 `background dependency install failed` 警告
  3. 打开 workbench，验证工具（`wopal_task`、`memory_manage`、`context_manage`）正常工作，沙箱工具正常代理
- 通过判据: serve 日志无依赖安装失败警告；插件初始化正常（`Runtime context initialized` 可见）；核心功能可用
- 失败反馈: 提供 `$WOPAL_HOME/logs/serve-*.log` 与 `.wopal-space/logs/wopal-plugin.log` 的输出

- [ ] 用户已完成上述功能验证并确认结果符合预期

## Implementation

### Task 1: 修正设计文档矛盾、更新配置架构与加固插件规范

**Verification Intent**: AC#6

**Behavior**:
- `DESIGN-wopal-plugin.md` 运行时契约章节消除"本地 types.ts 定义"陈旧描述，改为从 `@wopal/ellamaka-plugin` 导入
- 依赖声明章节补齐 `@wopal/ellamaka-sdk` 消费说明
- 补充 `wopal.pluginConfig` 配置节架构说明，指出生态插件零内联 options 规范
- `wopal-plugin/AGENTS.md` 与 `AGENTS.zh-CN.md` 明确禁止任何非 Bun 锁文件与配置，规范 `trustedDependencies` 机制与包导入规则

**TDD**: false

**Changes**:
1. 修改 `.wopal/docs/DESIGN-wopal-plugin.md`
2. 修改 `.wopal/plugins/wopal-plugin/AGENTS.md` 与 `AGENTS.zh-CN.md`

**Verify**:
`python3 skills/dev-doc-master/scripts/verify-docset.py docs --main DESIGN.md` 退出码 0（在隔离 worktree 根目录运行）；`grep` 断言文档中不再出现手抄描述

**Done**:
- [ ] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

### Task 2: wopal-plugin 依赖迁移、SDK 统一、类型去重与配置 schema 扩充

**Verification Intent**: AC#1, AC#3, AC#4

**Behavior**:
- `package.json` dependencies 声明 `@wopal/ellamaka-plugin` 与 `@wopal/ellamaka-sdk`（纯 `x.y.z` 稳定版），移除 `@opencode-ai/*`
- `src/types.ts` 删除 `SystemPromptSectionKind` / `SystemPromptSection` / `SystemPromptMetadata` 定义
- `src/index.ts`、`src/hooks/system-transform.ts` 及所有工具代码中的 `@opencode-ai/*` import 全部替换为 `@wopal/ellamaka-*`
- `src/config/schema.ts` 扩展 `pluginConfig` 节点支持
- 在纯 Bun 环境下 `bun run typecheck` 与 `bun run test:run` 全绿

**TDD**: true

**Changes**:
1. RED: 添加断言全仓无 `@opencode-ai/*` 残留、types.ts 无手抄类型及 schema 支持 pluginConfig 的测试，确认失败
2. GREEN: 修改 `package.json`，切换所有 import 来源，删除手抄类型，更新 schema
3. REFACTOR: 简化因引入完整类型而不再需要的类型断言

**Verify**:
`cd .wopal/plugins/wopal-plugin && bun run typecheck && bun run test:run` 全绿；`grep -rn "@opencode-ai" src/` 退出码 1（无匹配）

**Done**:
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

### Task 3: dsh-adapter 补齐 package.json、依赖声明与 ONT-G4 配置消费

**Verification Intent**: AC#2, AC#3, AC#4, AC#5

**Behavior**:
- `.wopal/plugins/dsh-adapter/package.json` 创建完成，声明 `name: "dsh-adapter"`、`@wopal/ellamaka-plugin` 依赖（版本与 Task 2 严格一致）
- `index.ts` 中的 `@opencode-ai/plugin` 导入全部切换为 `@wopal/ellamaka-plugin`
- `index.ts` 实现配置读取逻辑：优先从三层 settings（通过 input.wopalSpaceRoot 或配置解析）读取 `wopal.pluginConfig.dsh-adapter`，回退兼容 rawOptions；实现零内联 options
- 测试覆盖新配置路径与工具代理逻辑，测试全绿

**TDD**: true

**Changes**:
1. RED: 为 dsh-adapter 添加无 `@opencode-ai/plugin` 残留及支持 `wopal.pluginConfig.dsh-adapter` 配置读取的失败测试
2. GREEN: 创建 `package.json`，切换 import，增加配置解析与回退逻辑
3. REFACTOR: 清理代码结构与测试断言

**Verify**:
`cd .wopal/plugins/dsh-adapter && bun test` 全绿；`grep -rn "@opencode-ai/plugin" index.ts` 退出码 1

**Done**:
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤.

---

## Delegation Strategy

| Wave | Task | 执行者 | 依赖 | 委派理由 |
|------|------|--------|------|---------|
| 1 | Task 1 | Wopal 直接执行 | 无 | 设计与规范对齐，属统筹与守则收敛 |
| 2 | Task 2 | fae | Task 1 | wopal-plugin 依赖切换与代码修改，实施工作 |
| 2 | Task 3 | fae | Task 1 | dsh-adapter 依赖补齐与配置读取，可与 Task 2 并行或串行 |

Wave 2 完成后由 Rook 执行质量守门审查，随后由 Wopal 推进 Stage 至 validating。

## Delivery

`space sync` 与 `ontology contribute` 由用户拍板，技能不自动上行。

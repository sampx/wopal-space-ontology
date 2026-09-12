# Ontology — Distribution

> **Status**: Active
> **Updated**: 2026-09-12
> **上级**: `./DESIGN.md`
> **Parent Architecture**: `../../docs/products/wopal-space/DESIGN.md`

---

## Scope

本文件定义 ontology 的分发方式：中央能力池（local main）与空间装配 worktree（sparse-checkout 物化）。

ontology 的分发天然是 Git 仓库模型。wopal-cli 的 `wopal space init` / `wopal setup` 封装了这个过程，将其与 space runtime 初始化串联。分发模型详见 `DESIGN.md` 的 Ontology 协作模型章节。

能力边界、模板语义与运行态维护设计见 `DESIGN.md`。

---

## Distribution Model

ontology 分发模型：

```text
ontology source repo (upstream/main)
  -> local ontology clone (local main)          # 中央能力池，用户级唯一真相源
  -> space/<name> branch + sparse-checkout      # 空间装配 worktree，按装配单物化
  -> CLI renders deterministic runtime skeleton from templates
  -> ellamaka loads commands/agents/plugins/config at runtime
```

### Supported source inputs

1. 默认 canonical ontology source
2. 用户显式提供的 GitHub ontology URL
3. 已存在于本地 ontology directory 下的 ontology name

路径解析遵循"先复用本地已有 ontology，再按目标 source 补齐本地 repo"的原则。

P1 canonical identity 是 `wopal-space-ontology`。同一个 identity 用于默认 local ontology directory、setup source metadata、初始化后的 `STRUCTURE.md` 记录，以及承载 CLI artifacts 的 public GitHub Release carrier。自定义 ontology URL 保持为显式 override。

---

## Materialization Contract

ontology 的安装形态是 Git 仓库 + 装配 worktree。

`wopal space init` / `wopal setup` 负责：

1. 解析目标 ontology source
2. 准备本地 ontology repo（clone/fork，物化 local main）
3. 读取 `config/types/<type>.yaml` 装配单（缺省 common）
4. 创建 `space/<space-name>` 分支
5. 在 `<space>/.wopal/` 建立装配 worktree（sparse-checkout 按装配单物化）

P1 目标语义：

1. 默认使用 clone-based canonical source flow
2. fork flow 是显式选择的替代模式
3. 每个 space 拥有独立的 `space/<name>` 分支与装配 worktree
4. `.wopal/` 是装配 worktree，不是复制目录，也不持有独立能力演化
5. 空间装配单 `.wopal-space/assembly.yaml` 记录类型、来源 revision 与装配时间

---

## Template and Runtime Skeleton Contract

ontology 通过 `.wopal/templates/wopalspace-schema.yaml` 与相关模板，为 CLI 提供确定性初始化输入。

CLI 消费 ontology templates 时负责：

1. 创建 `<space>/AGENTS.md`
2. 创建 `<space>/.gitignore`
3. 创建 `.wopal-space/STRUCTURE.md`
4. 创建 `.wopal-space/REGULATIONS.md`
5. 创建 `.wopal-space/memory/USER.md`
6. 创建 `.wopal-space/memory/MEMORY.md`
7. 补齐 schema 中声明的固定目录

Contract：

1. ontology 声明 template 和 schema，CLI 负责确定性 materialization。
2. rerun 时补齐缺失项，已有文件的用户内容保持不动。
3. `/init` 在初始化之后承接智能校准，与首次确定性 materialization 分工协作。

---

## Base Capability Source Contract

`wopal setup` 从 ontology source 物化 user-level base capabilities 到 `$WOPAL_HOME/`，为所有 space 提供共享基础能力层。物化逻辑由 wopal-cli 实现（P1-06），ontology 在此声明 source 侧契约。

### Materialization

macOS / Linux 将 ontology source 目录整体 symlink 到 `$WOPAL_HOME/` 对应位置；Windows 使用 managed copy。整个目录链接后内容完整可达，无需按文件筛选。

| Source | Target |
|--------|--------|
| `ontologies/wopal-space-ontology/agents/` | `agents/` |
| `ontologies/wopal-space-ontology/skills/` | `skills/` |
| `ontologies/wopal-space-ontology/commands/` | `commands/` |
| `ontologies/wopal-space-ontology/rules/` | `rules/` |
| `ontologies/wopal-space-ontology/plugins/` | `plugins/` |
| `ontologies/wopal-space-ontology/dsh/agents-presets/` | `dsh/agents-presets/` |

> **注**：user-level base capabilities 是跨空间共享的**只读入口**，物化为 symlink 合理——它们由 `ontology update` 统一推进，不经由空间内修改。空间内可写的装配资产位于 `<space>/.wopal/`（sparse-checkout 真实文件），两者职责不同。

### DSH Profiles 物化契约

DSH Profile（`web` 与 `ellamaka-tools`）的基准声明属于本体能力基因，但其执行环境必须位于本地运行态：

1. **基准源**：`ontologies/wopal-space-ontology/dsh/profiles/<profile>/` 仅受版本控制维护 `package.json`（bundles 依赖）与 `cordis.patch.yml`（参数与规则补丁）。
2. **确定性物化**：`wopal setup` / `space init` 将基准源文件物理复制（Copy）到 `$WOPAL_HOME/dsh/home/profiles/<profile>/`，支持增量合并（bundles 去重合并、用户自定义 patch 保护）。
3. **运行时闭环**：物理文件就位后，由 `ellamaka dsh init` 执行闭包依赖解析、本地 `node_modules` 安装及 fallback 符号链接自愈，并在启动时动态生成 `cordis.yml` 锚点。禁止对 profiles 根目录进行跨文件系统软链接。

### Space Overlay

`<space>/.wopal/{agents,skills,commands,rules,plugins}` 是 space overlay 层。同名能力由 overlay 覆盖 base，ellamaka 按目录优先级顺序加载：

```text
$WOPAL_HOME/{agents,skills,commands,rules,plugins}  # base
-> <space>/.wopal/{agents,skills,commands,rules,plugins}  # overlay，优先级最高
```

空间 overlay 层由装配 worktree 物化（sparse-checkout 真实文件），空间内可写可进化；进化经 `space sync` 汇入 local main。

---

## Runtime Loading Handoff

ontology 被 materialize 后，ellamaka 在 wopal-space mode 下负责运行时加载：

1. `.wopal/config/settings.jsonc`
2. `.wopal/agents/*.md`
3. `.wopal/commands/*.md`
4. `.wopal/plugins/`
5. 其他声明式 ontology contents

运行时边界：

1. plugin 依赖由 ellamaka 在启动时按 path plugin 语义处理。
2. `~/.wopal/ellamaka/*` 全局运行目录由 ellamaka 管理。
3. CLI 的 global setup 由 wopal-cli 负责。
4. `/init` 的结构维护与差异吸收由 ontology command 在运行时承接。

---

## Out of Scope for P1

1. binary installer
2. release asset metadata
3. package manager integration
4. 在分发阶段替代 ellamaka runtime loading
5. 在分发阶段替代 CLI 的 global setup / engine install

---

## Related Documents

| Document | Purpose |
|---|---|
| `../../docs/products/wopal-space/DESIGN.md` | 产品级架构与版本体系 |
| `./DESIGN.md` | ontology 的能力边界、模板、命令、规则与 runtime 维护设计 |
| `../../projects/wopal-cli/docs/DESIGN.md` | CLI 的 deterministic init、space sync 与 runtime handoff 设计 |
| `../../projects/ellamaka/docs/DESIGN.md` | ellamaka 的 wopal-space mode 与 runtime loading 设计 |

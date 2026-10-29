# 本体与空间维护参考

在做状态检查、空间 / 本体同步、能力装配或本地能力选择时读取本文件。上游 GitHub PR 的创建、修改和收尾另见 [`contribution.zh-CN.md`](contribution.zh-CN.md)。

## 命令面

| 命令 | 作用 |
|------|------|
| `wopal space status` | 查看空间分支与 `local main` 的差异、装配状态、稀疏一致性、本地 include / exclude / private 选择和未登记文件 |
| `wopal space sync [--confirm]` | 在空间分支与 `local main` 之间对齐：先向上整合空间独有进化，再向下 fast-forward |
| `wopal space capability add/remove <kind>:<name> [--local]` | 不带 `--local` 修改共享装配；带 `--local` 只调整当前空间的 include / exclude / private 选择 |
| `wopal ontology capability list` | 查看中央能力池拥有的能力 |
| `wopal ontology status` | 查看本体 downstream / upstream 差异和 contribution 状态 |
| `wopal ontology sync [--confirm]` | 对齐 `upstream ⇄ origin ⇄ local main` 来源链；clone 模式按实际拓扑收缩 |

## 如何读状态

`wopal space status` 重点区分：

- **to contribute**：空间分支有尚未进入 `local main` 的共享变化。
- **behind local main**：空间需要吸收本体主线变化。
- **include**：当前空间额外挂载的共享能力。
- **exclude**：当前空间停用的类型默认能力。
- **private**：只留本地、不允许随共享同步上传的能力内容。

`wopal ontology status` 同时报告：

- **Downstream**：`upstream → origin → local main`。
- **Upstream**：`local main → origin → upstream` 的待贡献文件集。
- 本地 / 远端 `contribute/*` 分支、worktree 与 PR 状态。

“已合并、等待收尾”不代表已经获得删除授权，但它也不是可以被动忽略的提示。状态一旦显示某个已合并 PR 仍保留 contribution 资源，Agent 必须在同一次交互中报告具体残留并取得用户的清理决定后再结束；如果当前指令已经授权清理该 PR，就立即按 `contribution.zh-CN.md` 执行。普通同步仍然绝不自动获得删除权限。

## 共享装配与本地选择

`space capability` 有两个通道：

- **共享通道**（不带 `--local`）：修改 archetype / assembly，并重新物化；只接受能力池已经拥有的能力。命令本身不创建 Git commit，manifest 的提交是后续独立动作。
- **本地通道**（带 `--local`）：只记录当前空间的 include / exclude / private，并调整稀疏范围；状态发生变化时，CLI 只提交空间根仓中的这份状态记录，不把能力内容当成本地状态一起上传。

装配选择与内容传播是两件事。include / exclude 决定“当前空间是否挂载”，不决定“共享内容是否可上传”。private 才是上传保护边界。

## Upload gate

`space sync` 向上整合前会检查 private 能力根。任何空间独有提交只要触碰 private-registered capability root，就必须拒绝上传。

这道门用来兜底人工 `git add` / `commit`：本地隔离不能依赖操作者永远记得哪些内容不能上传。

## 执行原则

- CLI 默认可以提供 dry-run 预览；用户已经明确要求执行时，可直接使用 `--confirm`，不要再叠加一次无意义确认。
- 同步授权只覆盖同步，不自动包含 PR 创建、review-fix push、合并或删除。
- 冲突、范围不清或状态不一致时停止，不靠 reset / stash / force 处理现场。

## 准备上游贡献

在创建 PR 前：

1. 先列出所有待贡献路径并按主题 / 能力分组。
2. 区分真正共享的能力变化与只属于某个空间 / 类型的变化。
3. 让用户决定哪些组进入本次 contribution。
4. 一个主题一个 PR；共享文件里的无关 hunk 也要排除。

一旦开始创建、修改、重试或收尾 contribution，转到 [`contribution.zh-CN.md`](contribution.zh-CN.md)，不要在本文件里自行补 Git/GitHub 流程。

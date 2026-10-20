---
name: dsh-web-fetch-http-fakeip
description: 官方 dsh-web-fetch-http 的 @wopal fork 插件——双运行时（ellamaka/官方 dsh）安装与依赖解析边界、fork 修改约束与验证要求
---

# dsh-web-fetch-http-fakeip — Agent 规范

官方 `@deepseek-ai/dsh-web-fetch-http` 的 fork：放行 Clash TUN fake-ip 段
（198.18.0.0/15）使 `ctx.web` / `web_fetch` 在用户代理环境下可用，其余 SSRF
防护全部保留。本包直接修改 `lib/index.js`，无独立构建链。

权威文档：

- 上游参考源码（与本包同版本）：`labs/ref-repos/deepseek-harness/`（下称 REF）
- 替换契约：`cordis.patch.yml` 头部注释（禁改 `name`、先 disable 后 insert 新 id）

## 插件依赖解析边界（最高优先级）

两个运行时共用同一个安装器：官方 pluginManager 的 pnpm，作用于 profile
自己的 `package.json`。`ellamaka dsh plugin add <目录>` 直接转发给它，因此安
装记为 `file:<绝对路径>`，pnpm 按 `files` 字段把包拷进
`<profile>/node_modules/`，并就地解析本包的 registry 依赖。

- **registry 依赖**（`dependencies`）装进 profile。只放真正的第三方包；把
  `@deepseek-ai/*` 写在这里会让宿主已有的模块多出一份实例（见下方 peer 规则）。
- **peer**（`peerDependencies`）在 boot 时经共享兜底层
  `$DSH_HOME/profiles/node_modules/@deepseek-ai/*` 解析。`link-peers` 只适用
  于独立官方 `dsh` 安装记录成 `link:`（而非 `file:`）的情况，ellamaka 不使
  用。
- **源码目录保持纯净**——不含 `node_modules` 与 lockfile；`file:` 安装从源
  目录拷贝。

## link-peers.mjs 维护约束

- `scripts/link-peers.mjs` 通过 `which dsh` → realpath 推导官方闭包，**禁止
  改为读取 `$DSH_HOME` 或任何 home 路径**（本机存在官方 `~/.dsh` 与
  ellamaka `~/.wopal/dsh/home` 两个 home，环境变量指向后者，混用即错）。
- `PEER_PACKAGES` 清单必须与 `package.json` 的 `peerDependencies` 保持一致；
  增删 peer 时两处同步修改。
- 链接目标是官方闭包的 symlink（非拷贝），版本自动跟随官方 dsh 升级；
  禁止用 `npm install` 落地 peer 实体（会产生与宿主不同的模块副本）。

## fork 修改约束

- fork 修改点必须携带 `// Fork (dsh-web-fetch-http-fakeip): ...` 注释锚点，
  说明修改意图与放行范围；与上游 diff 保持最小。
- 升级上游版本时：重新套用全部 Fork 锚点修改，不得引入锚点之外的改动。

## 验证要求

本包无测试链，验证按目标运行时执行：

- ellamaka：`ellamaka dsh plugin --profile web add <目录>` 重装后由用户重启
  引擎验证（重启永远由用户执行）。
- 官方 dsh：在**隔离副本**的 `$DSH_HOME` 下 `dsh web` 启动验证插件树
  零错误；禁止对着任何 live home 做启动实验。
- 每次修改后核对：`cordis.patch.yml` 的 disable/insert 对与上游 provider id
  的对应关系未被破坏。

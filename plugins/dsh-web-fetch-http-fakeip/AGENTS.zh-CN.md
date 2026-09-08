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

## 双运行时依赖解析边界（最高优先级）

本插件同时服务两个运行时，两者的依赖解析机制不同，禁止混用：

- **ellamaka**（`ellamaka dsh plugin add`）：拷贝 `lib/` 进 profile，依赖由
  运行时 flat closure（`$DSH_HOME/profiles/node_modules/@deepseek-ai/*`）在
  boot 时自动兜底。**源码目录必须保持纯净**——不含 `node_modules` 与
  lockfile；ellamaka-only 开发禁止运行 `pnpm run link-peers`。
- **官方 dsh**（`dsh plugin --profile <name> add <dir>`）：`link:` 软链源码
  目录，Node 按源码目录物理向上解析 import。装进官方 profile 后必须
  **运行一次 `pnpm run link-peers`**，否则 boot 报
  `Cannot find package`。注册成功不代表可运行。

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

- ellamaka：`ellamaka dsh plugin add <dir>` 重装后由用户重启引擎验证
  （重启永远由用户执行）。
- 官方 dsh：在**隔离副本**的 `$DSH_HOME` 下 `dsh web` 启动验证插件树
  零错误；禁止对着任何 live home 做启动实验。
- 每次修改后核对：`cordis.patch.yml` 的 disable/insert 对与上游 provider id
  的对应关系未被破坏。

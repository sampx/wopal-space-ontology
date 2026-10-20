---
name: dsh-sandbox-roots
description: 沙箱可写根扩展插件（@wopal/dsh-sandbox-roots）——插件依赖解析边界、TDD 强制与 link-peers 维护约束
---

# dsh-sandbox-roots — Agent 规范

在 `workspace-write` 沙箱模式下，把 settings（`sandbox-policy:` 节，热重载）
声明的 `writableRoots` 并入 fs 工具 allow-list、进程沙箱 allow-list 与策略
对象。实现规格（design of record）：`docs/design.md`——含上游版本锚点、
已核实事实与逐文件设计，**实现前必读，本文件不复述其内容**。

权威文档：

- 实现规格：`docs/design.md`
- 上游参考源码（与部署闭包同版本）：`labs/ref-repos/deepseek-harness/`（REF）

## 开发命令

```bash
pnpm typecheck   # tsc --noEmit
pnpm test        # vitest run
pnpm build       # tsdown，产物进 lib/
pnpm check       # typecheck + test + build 全链
```

## TDD 强制

`src/` 全部逻辑（含 `internal/` 纯函数与三个服务子类）必须有先行的失败
测试（`tests/*.test.ts`）再实现；重构同步调整测试。上游行为复刻类代码
（如 `internal/containment.ts` 复制自 REF）同样以测试锁定行为。

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

## 上游对齐约束

- 闭包内官方包不带 `src/`，运行时不可深导 `@deepseek-ai/*` 的 `src/*`；
  需要的上游实现按 `docs/design.md` 的指示复制进 `internal/` 并以测试锁定。
- 覆盖官方服务（sandbox-policy / fs-sandbox / sandbox provider 三行）时，
  `static Config` 必须完整复述 stock 字段再加新增字段（patch 行 config 整体
  替换、不深合并）。

## 验证要求

- 自动化：`pnpm check` 全绿是提交前置条件。
- ellamaka：`ellamaka dsh plugin --profile web add <目录>` 重装后由用户重启
  引擎验证（重启永远由用户执行）。
- 官方 dsh：在**隔离副本**的 `$DSH_HOME` 下 `dsh web` 启动验证插件树
  零错误；禁止对着任何 live home 做启动实验。

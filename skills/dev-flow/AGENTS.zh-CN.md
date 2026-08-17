---
name: dev-flow
description: Issue/Plan-driven development workflow CLI — state-machine commands, plan validation, worktree isolation, and delegation orchestration
---

# Agent Development Rules

## 1. Canonical References

- Parent Rules: `.wopal/AGENTS.md`
- Commands: `references/commands.md`
- Plan Guide: `references/plan-guide.md`
- Issue Guide: `references/issue-guide.md`
- Troubleshooting: `references/troubleshooting.md`

## 2. Architecture and Directories

| Directory | Responsibility |
|---|---|
| `scripts/flow.sh` | CLI 入口，路由到 Python |
| `scripts/flow.py` | argparse 主程序、子命令分发 |
| `scripts/commands/` | 子命令实现 (submit, approve, complete, verify, plan, issue, sync, archive, roadmap, decompose, reset) |
| `scripts/lib/` | 共享库 (git, github, project, workspace, worktree, logging) |
| `templates/` | Plan 和 Issue 模板 |
| `references/` | 命令参考、Plan 编写指南、故障处理 |
| `tests/python/` | unit/ + integration/ 测试 |

## 3. Development Commands

| Scenario | Command |
|---|---|
| 运行测试 | `python -m pytest tests/python/ -v` |
| CLI 帮助 | `bash scripts/flow.sh <cmd> --help` |
| Plan 校验 | `bash scripts/flow.sh plan <issue> --check` |

运行目录：`.wopal/skills/dev-flow/`

运行依赖：bash 3.x+, `gh` CLI, `jq`, Python 3

## 4. Implementation Rules

### Command Routing

`flow.sh` 匹配已知命令路由到 `flow.py`（argparse），未知命令输出错误列表并 exit 1。新增命令必须同时在 `PYTHON_COMMANDS` 正则和 `flow.py` 中注册。

### State Machine

`planning → reviewing → executing → verifying → done`

每个命令有前置状态要求，非法转换报错。新增命令必须声明前置/后置状态。

`plan check` 验证 Plan 中声明的 Status 属于该状态机。User Validation 节存在时，校验器要求至少一个场景和最终确认 checkbox；`verify` 阶段负责确认该 checkbox 已由用户勾选。

### Plan Directory Rules

- `--project` 是 `plan` 命令必填参数
- 所有项目：`.wopal-space/plans/<项目名>/`
- Plan 文件必须通过 `flow.sh plan ...` 生成或定位，禁止手写创建

### Script Conventions

- `scripts/lib/` 中的模块可被子命令直接 import
- 日志通过 `scripts/lib/logging.py` 统一处理
- GitHub API 操作通过 `scripts/lib/github.py`，不直接调用 `gh`
- Git 操作通过 `scripts/lib/git.py`，不直接调用 `git`

## 5. Testing

- 测试框架：pytest
- 测试目录：`tests/python/unit/`（单元测试）、`tests/python/integration/`（集成测试）
- 测试 fixture：`tests/fixtures/`
- 测试支持工具：`tests/python/support/bootstrap.py`
- **TDD 要求**：新命令或 `scripts/lib/` 模块功能必须先写失败测试，再实现功能使测试通过
- 修改子命令逻辑后必须运行对应单元测试确认无回归

### 六条硬规则（R1–R6）

以下规则用于防止测试膨胀与装饰性测试（测试全绿但逻辑错误）。每个新增或修改的测试必须同时满足全部六条。

**R1 只断言行为。** 每个测试只断言给定的输入 → 输出映射（返回值、异常、文件结果）。断言调用序列、mock 走了哪个分支、中间状态、精确的输出格式字符串（如 `">> planning <<"`）、对源码做字符串搜索（如 `assert "--merge" not in source`）一律禁止——应断言返回码和关键子串。有效性判据：实现换成等价写法，测试必须原样通过；做不到说明测试耦合实现，无效。

**R2 mock 数据必须可溯源。** 任何 mock 输出必须来自 `tests/fixtures/` 中录制的真实样本。禁止手写凭空捏造的假数据（如 `"tree-main\n"` 或临时拼凑的 porcelain 片段）。每个 fixture 必须注明录制场景。

**R3 一行为一用例。** 同一输入 → 输出映射只允许一个用例。"实现路径不同、行为相同"属于重复，禁止。禁止穷举字典查找表写 N 个 `assertEqual(func("key"), "value")`；同类用例必须 `parametrize` 表格化——一行一例，禁止复制粘贴变体。

**R4 样板阈值：3 次即抽。** 同类 mock/构造样板出现 3 次必须抽取为共享 helper。测试文件行数超过其覆盖的实现文件 3 倍时，停止新增测试，先瘦身。

**R5 红绿铁律。** 新测试必须先在坏代码上失败过（RED），修复后才转绿。无法构造失败的测试是装饰品，不是测试。修复 bug 时，与新测试覆盖同一判定的旧测试必须删除——禁止叠加。

**R6 禁止固化实现巧合。** 仅当前实现恰好成立的行为（如"worktree 目录名 == 分支名"）不得写成断言，除非有契约文档依据。此类测试会把 bug 固化成规范。

### Mock 隔离规则

**模块级 mock 禁令**：禁止在测试文件顶层用 `sys.modules[name] = MagicMock()` 注入 mock。这种做法会污染全局模块缓存，导致后续测试文件拿到假模块而非真实代码。正确做法是直接 import 真实模块，在函数级用 `@patch` mock 有副作用的函数。

**函数级 mock 原则**：只 mock 有副作用的函数（git 操作、网络请求、日志输出），不要 mock 整个模块。Python 导入模块 = 加载函数定义，不会执行任何副作用。被测函数操作文件系统时必须用 `tempfile.mkdtemp()` 隔离，`tearDown` 中清理。

## 6. User-Supplied Rules

(None)

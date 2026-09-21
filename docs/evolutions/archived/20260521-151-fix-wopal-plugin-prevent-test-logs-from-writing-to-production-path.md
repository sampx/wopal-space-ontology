# 151-fix-wopal-plugin-prevent-test-logs-from-writing-to-production-path

## Metadata

- **Issue**: #151
- **Type**: fix
- **Target Project**: wopal-space-ontology
- **Project Path**: .wopal
- **Project Type**: ontology-worktree
- **Created**: 2026-05-21
- **Status**: done

## Scope Assessment

- **Complexity**: Low
- **Confidence**: High

## Goal

logger.ts 在 vitest 环境下不写入生产路径日志文件。

## Technical Context

### Architecture Context

`logger.ts` 的 `getLogFile()` 默认用 `join(process.cwd(), ".wopal-space", "logs", "wopal-plugin.log")` 解析路径。vitest 运行时 cwd 是 `.wopal/plugins/wopal-plugin/`，导致测试在插件项目内产生 `.wopal-space/logs/wopal-plugin.log` 副产物。

现有测试通过 `WOPAL_PLUGIN_LOG_FILE` 重定向到 `/tmp`，但未设置该变量的测试（或未来新增测试）仍会写入生产路径。

### Key Decisions

- D-01: 通过 `process.env.VITEST` 检测测试环境，不写入文件。Vitest 会自动设置此变量，零配置。不使用 `NODE_ENV` 因为 wopal-plugin 运行在 EllaMaka 进程中，不应干扰宿主环境。

## In Scope

- logger.ts 增加 vitest 环境检测，测试时抑制文件写入
- 补充对应的测试用例验证抑制生效

## Out of Scope

- 生产运行时日志路径逻辑（Issue 明确排除）

## Affected Files

| Component | Files | Operation | Role |
|-----------|-------|-----------|------|
| wopal-plugin | `.wopal/plugins/wopal-plugin/src/logger.ts` | 修改 | 增加测试环境检测，抑制文件写入 |
| wopal-plugin | `.wopal/plugins/wopal-plugin/src/logger.test.ts` | 修改 | 新增测试用例验证抑制行为 |

## Acceptance Criteria

### Agent Verification

1. [x] `cd /Users/sam/coding/wopal/wopal-workspace/.wopal && bun run test:run --filter logger` 全部 pass
2. [x] 以下命令确认无生产路径日志残留：`test ! -d /Users/sam/coding/wopal/wopal-workspace/.wopal/plugins/wopal-plugin/.wopal-space`
3. [x] `bun run typecheck` 在 `.wopal` 目录通过
4. [x] `rg 'VITEST' /Users/sam/coding/wopal/wopal-workspace/.wopal/plugins/wopal-plugin/src/logger.ts` 匹配到检测逻辑

### User Validation

#### Scenario 1: 测试运行后无日志残留
- Goal: 确认 `bun run test:run` 不再在 wopal-plugin 项目内产生 `.wopal-space/logs/` 目录
- Precondition: 确保之前残留的 `.wopal-space/` 已清理
- User Actions:
  1. 删除 `.wopal/plugins/wopal-plugin/.wopal-space/`（如存在）
  2. 在 `.wopal/` 目录运行 `bun run test:run`
  3. 检查 `.wopal/plugins/wopal-plugin/` 下是否出现 `.wopal-space/`
- Expected Result: `.wopal/plugins/wopal-plugin/.wopal-space/` 不存在

- [x] 用户已完成上述功能验证并确认结果符合预期

## Implementation

### Task 1: 在 logger 中增加测试环境检测，抑制文件写入

**Verification Intent**: AC#1, AC#2, AC#3, AC#4

**Behavior**: vitest 环境下（`process.env.VITEST` 为 truthy）且未显式设置 `WOPAL_PLUGIN_LOG_FILE` 时，`writeLine` 不执行任何文件操作。显式设置 `WOPAL_PLUGIN_LOG_FILE` 的测试仍正常写入（现有测试行为不变）。

**Files**: `.wopal/plugins/wopal-plugin/src/logger.ts`, `.wopal/plugins/wopal-plugin/src/logger.test.ts`

**Pre-read**: `.wopal/plugins/wopal-plugin/src/logger.ts`, `.wopal/plugins/wopal-plugin/src/logger.test.ts`

**Design**:
在 `writeLine` 函数顶部增加测试环境判断：当 `process.env.VITEST` 存在且未显式设置 `WOPAL_PLUGIN_LOG_FILE` 时，直接 return。这保证：
1. 生产运行不受影响（无 VITEST 变量）
2. 现有测试不受影响（显式设置了 WOPAL_PLUGIN_LOG_FILE 到 /tmp）
3. 未设置日志路径的测试不再写入生产路径

**注意**：`ensureLogFile()` 会先 `mkdirSync` 创建目录再写文件，因此检测必须拦截在 `writeLine` 入口（目录创建之前），而不是在 `writeLine` 内部 `ensureLogFile` 之后。修复后 `.wopal-space/` 目录本身也不应被创建。

新增测试用例设计：
- describe "Test environment suppression"，独立于现有测试（不继承它们的 env 设置）
- **beforeEach**：清理插件目录下可能残留的 `.wopal-space/`；确保 `WOPAL_PLUGIN_LOG_FILE` 未设置；显式设置 `WOPAL_PLUGIN_LOG_LEVEL=info`，清空 `WOPAL_PLUGIN_LOG_MODULES`（确保穿过 `shouldLog()` 到达 `writeLine`）
- **afterEach**：再次清理 `.wopal-space/`；恢复 env（LEVEL、MODULES、LOG_FILE）
- **断言 1**：`process.env.VITEST` 为 truthy（锁定前提，防止环境变化导致静默回归）
- **断言 2**：`.wopal/plugins/wopal-plugin/.wopal-space/` 目录不存在（不是只检测文件，而是检测整个目录）

**TDD**: true

**Changes**:
1. RED: 在 `logger.test.ts` 新增 describe "Test environment suppression"，包含 beforeEach/afterEach 清理 `.wopal-space/` 残留 + 恢复 env；测试用例：不设 WOPAL_PLUGIN_LOG_FILE，调用 coreLogger.info()，断言 process.env.VITEST 为 truthy，断言插件目录下 `.wopal-space/` 目录不存在
2. GREEN: 在 `logger.ts` 的 `writeLine` 函数最顶部（ensureLogFile 调用之前）增加检测：`if (process.env.VITEST && !process.env.WOPAL_PLUGIN_LOG_FILE) return`
3. REFACTOR: 确认现有测试全部通过，清理插件目录下残留的 `.wopal-space/`

**Verify**:
```bash
cd /Users/sam/coding/wopal/wopal-workspace/.wopal && rm -rf /Users/sam/coding/wopal/wopal-workspace/.wopal/plugins/wopal-plugin/.wopal-space && bun run typecheck && bun run test:run --filter logger && test ! -d /Users/sam/coding/wopal/wopal-workspace/.wopal/plugins/wopal-plugin/.wopal-space
```

**Done**:
任务产出：logger 在 vitest 环境下不再写入生产路径日志文件，补充测试用例验证
- [x] 实施 Agent 已完成上述功能开发和验证的所有步骤执行, 并确认结果符合预期（必须由实施 Agent 勾选）

---

## Delegation Strategy

N/A — 单一 Task，Complexity = Low，无需并行委派。

# wopal-plugin — Agent Development Rules

## 1. Project Positioning

Wopal's dedicated ellamaka runtime plugin — rule injection, task delegation, memory system, context management.

Canonical references:

- PRD: `.wopal/docs/PRD.md`
- DESIGN: `.wopal/docs/DESIGN.md`
- Parent Rules: `.wopal/AGENTS.md`

## 2. Architecture and Directories

| Module | Responsibility | Disable Switch |
|--------|---------------|----------------|
| Global (`index.ts`) | Load .env, load config, register Hooks/Tools | None |
| Rules (`rules/`) | Rule discovery → condition matching → system prompt injection | None (always enabled) |
| Memory (`memory/`) | LanceDB storage, semantic retrieval, memory injection | `wopal.memory.enabled` (master), `wopal.memory.injection` (injection only) — config `wopal` node |
| Task (`tasks/`) | Non-blocking sub-sessions, state monitoring, bidirectional communication, concurrency control | None |
| Monitor (`monitor/`) | Periodic scheduling engine, unified strategy management | None |
| Context (`hooks/`, `context/`) | Session compaction and recovery, title generation, distillation | `wopal.context.enabled` — gates title/recovery/distillation; compaction always on |

| Directory | Responsibility |
|-----------|---------------|
| `src/hooks/` | Hook registration and injection logic; `system-transform.ts` is the sole system prompt modification entry |
| `src/tasks/` | Task management; `SimpleTaskManager` is the sole public entry |
| `src/memory/` | Memory persistence; `MemoryStore` (`store.ts`) is the sole persistence access entry |
| `src/monitor/` | `MonitorEngine` is the sole periodic scheduling engine |
| `src/tools/` | Plugin tool definitions; task tools use unified `wopal-task-*` prefix |
| `src/lifecycle/` | Generic process cleanup registry |
| `src/rules/` | Rule discovery, matching, formatting |
| `scripts/` | CLI tools, migrations, validation utilities |

Deployment: `.wopal/plugins/wopal-plugin.ts` → symlink → `src/index.ts`.

## 3. Development Commands

| Scenario | Command |
|----------|---------|
| Install dependencies | `bun install` |
| Type check | `bun run typecheck` |
| Auto-fix types | `bun run typecheck:fix` |
| Run tests | `bun run test:run` |
| Watch tests | `bun run test` |
| Build | `bun run build` |
| Lint | `bun run lint` |
| Format | `bun run format` / `bun run format:fix` |
| Format check | `bun run format:check` (not a hard gate) |

### Post-Change Verification Order

`bun run typecheck:fix` → `bun run typecheck` → `bun run test:run`.

Issues that `typecheck:fix` cannot resolve must be fixed manually; do not skip and commit. `build` is for artifact verification/release only, not routine validation.

### Verification Mechanisms

Runtime behavior that unit tests cannot exercise (plugin bootstrap, config loading from real files, resource construction, tool registration) is verified by launching ellamaka headless against the real space:

```bash
# From the space root; prints plugin logs to stderr and appends to the plugin log file.
ellamaka run "reply with exactly: OK" --print-logs --log-level DEBUG
```

Output lands in `<space>/.wopal-space/logs/wopal-plugin.log`. Boot markers to look for:

| Marker | Meaning |
|--------|---------|
| `Runtime context initialized` | Space root and `wopalHome` resolved |
| `Effective wopal config loaded` | Three-layer config merged; secrets redacted |
| `Resources resolved` | Which of store / embedder / llm were constructed |
| `Plugin initialized` | Final tool list and `memory` flag |

Config-driven behavior is exercised with isolated fixtures under `.wopal-space/.tmp/` (never by editing the user's real `settings.local.jsonc`); `loadWopalConfig` accepts injected `wopalHome` / `wopalSpaceRoot` / `fallbackEnvironment` for this purpose.

`WOPAL_HOME` overrides the user-level config and storage root, which makes sandboxed runs possible.

## 4. Implementation Rules

### Logging

Use module-level loggers (`src/logger.ts`); `console.log` is forbidden.

| Logger | Scope |
|--------|-------|
| `coreLogger` | Bootstrap, lifecycle |
| `rulesLogger` | Rule discovery/matching/injection |
| `taskLogger` | Task delegation/monitoring/communication |
| `memoryLogger` | LanceDB/retrieval/injection |
| `contextLogger` | Session state/compaction/recovery/distillation |

- Log levels: trace(10) / debug(20) / info(30) / warn(40) / error(50) / fatal(60); default `info`
- **Log level usage rules**:
  - `info`: Core event completion — one info log per key event (e.g., distill done, confirm done, cancel). Do not add more
  - `debug`: Important data display — log key metrics/data points for operational visibility (e.g., message count, conversation length after extraction)
  - `trace`: Detailed debugging flow — step-by-step traces for troubleshooting (e.g., "already extracted", "too short, skip", "no memories extracted")
  - `warn`: Structured error output — must carry `{ err: error }`, never interpolate error.message
- Structured fields via `data` object, field names in snake_case; do not interpolate into message
- Error logs must carry `{ err: error }`; logging only `error.message` is forbidden
- sessionID format: `formatSessionID(sessionID, isTask)` → `<last10chars>(main|task)`

### Module Boundaries

- **tasks**: `SimpleTaskManager` periodic monitoring must register via `MonitorStrategy` into `MonitorEngine`
- **monitor**: New monitoring strategies implement `MonitorStrategy` and register with engine; creating independent scheduling chains in other modules is forbidden
- **memory**: `MemoryStore` is the sole persistence entry; records use `tags` field (not `concepts`)
- **context**: distillation follows `preview → confirm` two-step flow, skipping user review is forbidden

### Agent-Facing Tools

- `memory_manage`: pure memory operations — list/stats/search/add/update/delete/injected; registered when the memory store is available
- `context_manage`: session context — status/dump/compact, plus distillation actions distill/confirm/cancel; distillation requires the context capability (`context.enabled`)

### `promptAsync` Session Model Discipline

- Any `promptAsync` call that sends a message to a session must explicitly use the **target session's current trusted model** as `body.model`; never rely on the default model
- Sending to the main session → use the main session's current model; sending to a child session → use that child session's current model
- If the target session's current model is unknown, first resolve it from session state or the runtime API; only degrade safely when it still cannot be resolved, and log the reason at debug/warn level
- Never use the sender session, current executing agent, or default provider/model configuration as a substitute for the target session's model

### Adding New Features

- **New hook**: Create file in `hooks/`, register in `hooks/index.ts` `createAllHooks()`
- **New tool**: Create file in `tools/`, register in `tools/index.ts` `createWopalTools()`; task tools use `wopal_task_*` prefix
- **New memory category**: Add in `memory/categories.ts`; identifier in English, importance 0-1
- **New monitoring strategy**: Implement `MonitorStrategy` interface, register with `MonitorEngine`
- **New environment variable**: `WOPAL_` prefix + `UPPER_SNAKE_CASE`; must sync to debug switch table and `loadWopalEnv()`
- **New HookContext field**: Must be optional (`?: boolean`, default `true`) for backward compatibility

### Naming Conventions

| Category | Convention | Example |
|----------|-----------|---------|
| Source files | `kebab-case.ts` | `idle-diagnostic.ts` |
| Test files | Same directory as source, `*.test.ts` | `task-launcher.test.ts` |
| Tool definitions | `wopal-task-*.ts` | `wopal-task-output.ts` |
| Hook functions | `create*` factory pattern | `createAllHooks()` |
| Loggers | Module-level singleton, import from `logger.ts` | `taskLogger`, `memoryLogger` |
| Environment variables | `WOPAL_` + `UPPER_SNAKE_CASE` | `WOPAL_PLUGIN_LOG_LEVEL` |

### Error Handling

- All async operations must try/catch; log with module logger at `error` level carrying `{ err: error }`, return safe fallback value
- Sub-session exceptions classified via `task-stop-classifier.ts`: `idle` / `stuck` / `error`
- LanceDB connection failure → degrade to empty Store; Embedding API failure → skip injection + warn log

### Type Safety

- Bare `as any` is forbidden; use type guards, `unknown` narrowing, or minimal interface definitions
- When SDK types are missing, add local declarations in `types.ts`; do not escape with `as any`
- `typecheck:fix` handles only mechanically fixable type issues; complex cases must be fixed manually
- Routine validation uses `bun run typecheck`; do not call `tsc` directly

### File Size

Source files ≤500 lines; split when exceeded. Split signals: >500 lines / function >50 lines / >2 responsibilities / >15 imports.

## 5. Testing

- Follow TDD: write a failing test first, then implement to make it pass
- New modules must have `*.test.ts` covering main paths and edge cases
- Code style: TypeScript ESM, `.js` extension imports; Vitest framework, tests co-located with source

## 6. Do Not

- Use `console.log` (use module-level loggers)
- Use npm / pnpm (Bun only)
- Use `^` prefix for LanceDB — `@lancedb/lancedb` and `@lancedb/lancedb-darwin-x64` must have matching exact versions (currently `0.22.3`); ABI incompatibility crashes the memory system
- Directly concatenate injection content in `system-transform.ts`
- Cross-use loggers across modules

## 7. Debug Switches

| Variable | Default | Description |
|----------|---------|-------------|
| `WOPAL_PLUGIN_LOG_LEVEL` | `info` | Log threshold: trace/debug/info/warn/error/fatal (env override; config `wopal.logLevel` is the default source) |
| `WOPAL_PLUGIN_LOG_FILE` | `<cwd>/.wopal-space/logs/wopal-plugin.log` | Log file path (env override; config `wopal.logFile` is the default source) |
| `WOPAL_PLUGIN_LOG_MODULES` | (empty) | Module filter (comma-separated), empty=all. Options: core/rules/task/memory/context (env override; config `wopal.logModules` is the default source) |

## 8. Config Nodes (`wopal` node in settings.jsonc)

Feature switches and connection settings live in the `wopal` node of the three-layer settings (`global` → `space-public` → `space-local`, later wins):

| Node | Fields | Notes |
|------|--------|-------|
| `memory` | `enabled`, `injection` | Default both `true`; `injection=false` stops auto-injection but keeps `memory_manage` and search |
| `context` | `enabled` | Default `true`; gates title generation, auto-recovery, and distillation; compaction always on |
| `llm` | `baseUrl`, `model`, `apiKey` | apiKey supports `$VAR` referencing process.env / `.env` files; never store plaintext keys |
| `embedding` | `baseUrl`, `model`, `apiKey` | Same `$VAR` semantics as `llm` |
| `logLevel` / `logFile` / `logModules` | — | Config is the default source; `WOPAL_PLUGIN_LOG_*` env vars override |

`.env` files hold only secrets referenced via `$VAR` (e.g. `WOPAL_LLM_API_KEY`) plus the log diagnostic overrides; feature switches never go in `.env`.

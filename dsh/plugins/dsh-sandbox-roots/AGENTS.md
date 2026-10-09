---
name: dsh-sandbox-roots
description: Sandbox writable-roots extension plugin (@wopal/dsh-sandbox-roots) — dual-runtime dependency-resolution boundary, mandatory TDD, and link-peers maintenance constraints
---

# dsh-sandbox-roots — Agent Rules

In `workspace-write` sandbox mode, merge the `writableRoots` declared in
settings (the `sandbox-policy:` section, hot-reloaded) into the fs tool
allow-list, the process sandbox allow-list, and the policy object itself.
The implementation specification (design of record) is `docs/design.md` —
it holds the upstream version anchor, verified facts, and per-file design.
**Read it before implementing; this file does not restate its content.**

Authoritative documents:

- Implementation specification: `docs/design.md`
- Upstream reference source (same version as the deployment closure):
  `labs/ref-repos/deepseek-harness/` (REF)

## Development commands

```bash
pnpm typecheck   # tsc --noEmit
pnpm test        # vitest run
pnpm build       # tsdown, output into lib/
pnpm check       # typecheck + test + build full chain
```

## TDD is mandatory

All logic in `src/` (including `internal/` pure functions and the three
service subclasses) requires a failing test first (`tests/*.test.ts`), then
the implementation; refactors adjust tests in step. Upstream-behavior
replication (e.g. `internal/containment.ts` copied from REF) is likewise
locked by tests.

## Dual-runtime dependency resolution boundary (highest priority)

This plugin serves two runtimes whose dependency resolution differs; never
mix the two flows:

- **ellamaka** (`ellamaka dsh plugin add`): copies `lib/` into the profile;
  dependencies are served by the runtime's flat closure
  (`$DSH_HOME/profiles/node_modules/@deepseek-ai/*`) at boot. **The source
  directory must stay clean** — no `node_modules`, no lockfile; never run
  `pnpm run link-peers` for ellamaka-only development.
- **Official dsh** (`dsh plugin --profile <name> add <dir>`): records a
  `link:` to the source directory; Node resolves the plugin's imports by
  walking up from the source directory. After installing into an official
  profile, **run `pnpm run link-peers` once**, or boot fails with
  `Cannot find package`. Registration success proves nothing about
  runnability.

## link-peers.mjs maintenance constraints

- `scripts/link-peers.mjs` derives the official closure from `which dsh` →
  realpath. **Never rewrite it to read `$DSH_HOME` or any home path** (this
  machine has two homes — official `~/.dsh` and ellamaka
  `~/.wopal/dsh/home`; the environment variable points at the latter, and
  mixing them up is a real failure mode).
- `PEER_PACKAGES` must stay in sync with `peerDependencies` in
  `package.json`; update both when adding or removing a peer.
- Links are symlinks into the official closure (not copies), so versions
  follow official dsh upgrades automatically; never materialize peer copies
  with `npm install` (that creates module duplicates distinct from the
  host's).

## Upstream alignment constraints

- Official packages inside the closure ship without `src/`; never deep-import
  `@deepseek-ai/*` `src/*` at runtime. Upstream implementations this plugin
  needs are copied into `internal/` as directed by `docs/design.md` and
  locked by tests.
- When overriding official services (the sandbox-policy / fs-sandbox /
  sandbox provider rows), `static Config` must restate every stock field
  before adding new ones (a patch row's config is replaced wholesale, never
  deep-merged).

## Verification requirements

- Automated: a green `pnpm check` is a precondition for any commit.
- ellamaka: reinstall with `ellamaka dsh plugin add <dir>`, then the user
  restarts the engine to verify (restarts are always performed by the user).
- Official dsh: boot `dsh web` under an **isolated copy** of `$DSH_HOME` and
  verify a zero-error plugin tree; never run boot experiments against any
  live home.

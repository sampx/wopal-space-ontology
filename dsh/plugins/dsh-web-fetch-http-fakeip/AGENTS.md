---
name: dsh-web-fetch-http-fakeip
description: @wopal fork of the official dsh-web-fetch-http plugin — dual-runtime (ellamaka/official dsh) install and dependency-resolution boundaries, fork modification constraints, and verification requirements
---

# dsh-web-fetch-http-fakeip — Agent Rules

Fork of the official `@deepseek-ai/dsh-web-fetch-http`: allows the Clash TUN
fake-ip range (198.18.0.0/15) so `ctx.web` / `web_fetch` works behind the
user's proxy while every other SSRF guard stays intact. This package edits
`lib/index.js` directly and has no build chain of its own.

Authoritative documents:

- Upstream reference source (same version as this package):
  `labs/ref-repos/deepseek-harness/` (REF)
- Replacement contract: header comment of `cordis.patch.yml` (never change a
  row's `name`; disable the stock row, then insert a new row with a new id)

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

## Fork modification constraints

- Every fork modification point carries a
  `// Fork (dsh-web-fetch-http-fakeip): ...` comment anchor stating intent
  and allow scope; keep the diff against upstream minimal.
- When upgrading the upstream version: re-apply all Fork-anchor changes and
  introduce nothing beyond the anchors.

## Verification requirements

This package has no test chain; verify against the target runtime:

- ellamaka: reinstall with `ellamaka dsh plugin add <dir>`, then the user
  restarts the engine to verify (restarts are always performed by the user).
- Official dsh: boot `dsh web` under an **isolated copy** of `$DSH_HOME` and
  verify a zero-error plugin tree; never run boot experiments against any
  live home.
- After every change, check that the disable/insert pair in
  `cordis.patch.yml` still maps correctly onto the upstream provider id.

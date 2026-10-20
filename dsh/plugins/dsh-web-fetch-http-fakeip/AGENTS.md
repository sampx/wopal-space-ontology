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

## Plugin dependency resolution (highest priority)

One installer serves both runtimes: the official plugin manager's pnpm, on
the profile's own `package.json`. `ellamaka dsh plugin add <dir>` forwards to
it, so an install is recorded as `file:<abs>` and pnpm copies the package
(per its `files` field) into `<profile>/node_modules/`, resolving this
package's registry dependencies there.

- **Registry dependencies** (`dependencies`) install into the profile. Keep
  them genuinely third-party; a `@deepseek-ai/*` entry here duplicates a
  module the host already runs (see the peer rule below).
- **Peers** (`peerDependencies`) resolve through the shared fallback
  `$DSH_HOME/profiles/node_modules/@deepseek-ai/*` at boot. `link-peers` is
  only for a standalone official `dsh` install that recorded `link:` instead
  of `file:` — never for ellamaka.
- **pnpm** is a host prerequisite, exactly as for the official `dsh` CLI:
  neither product bundles or installs one. A missing `pnpm` fails the install
  with an explicit message.
- **The source directory stays clean** — no `node_modules`, no lockfile;
  `file:` installs copy from the source tree.

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

- ellamaka: reinstall with `ellamaka dsh plugin --profile web add <dir>`,
  then the user restarts the engine to verify (restarts are always performed
  by the user).
- Official dsh: boot `dsh web` under an **isolated copy** of `$DSH_HOME` and
  verify a zero-error plugin tree; never run boot experiments against any
  live home.
- After every change, check that the disable/insert pair in
  `cordis.patch.yml` still maps correctly onto the upstream provider id.

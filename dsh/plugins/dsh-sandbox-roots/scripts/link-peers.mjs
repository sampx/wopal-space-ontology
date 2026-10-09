#!/usr/bin/env node
// Link this plugin's @deepseek-ai peer dependencies to the official dsh
// installation closure. Required only for running under the standalone
// official `dsh` CLI, whose plugin install (`dsh plugin add <dir>`) links the
// source directory verbatim — Node then resolves the plugin's own imports by
// walking up from the source directory, so the peers must exist there.
// The ellamaka runtime copies the plugin into its profile and serves peers
// from its own flat closure; under ellamaka this script is unnecessary.
//
// Usage:  pnpm run link-peers   (or: node scripts/link-peers.mjs)
// Resolution chain: `which dsh` → realpath → the @deepseek-ai/dsh package →
// its nested node_modules closure (npm global layout) or the flat install
// tree (pnpm global layout). No environment variables, no home paths.

import { spawnSync } from "node:child_process"
import { existsSync, mkdirSync, readdirSync, realpathSync, symlinkSync, unlinkSync, lstatSync } from "node:fs"
import { dirname, join, resolve } from "node:path"
import { fileURLToPath } from "node:url"

const pluginRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..")

/** Packages this plugin imports at runtime and that live in the dsh closure. */
const PEER_PACKAGES = [
  "@deepseek-ai/cordis",
  "@deepseek-ai/dsh-fs",
  "@deepseek-ai/dsh-fs-local",
  "@deepseek-ai/dsh-fs-sandbox",
  "@deepseek-ai/dsh-sandbox",
  "@deepseek-ai/dsh-sandbox-local",
  "@deepseek-ai/dsh-sandbox-policy",
  "@deepseek-ai/dsh-session",
  "@deepseek-ai/dsh-settings",
  "@deepseek-ai/schemastery"
]

function fail(message) {
  console.error(`link-peers: ${message}`)
  process.exit(1)
}

function findDshBinary() {
  const probe = process.platform === "win32" ? "dsh.cmd" : "dsh"
  const result = spawnSync("which", [probe], { encoding: "utf8" })
  const first = result.stdout?.trim().split("\n")[0]
  if (result.status !== 0 || !first) {
    fail("no `dsh` binary on PATH. Install the official CLI first (npm i -g @deepseek-ai/dsh), or skip this script when targeting ellamaka only.")
  }
  return realpathSync(first)
}

/** Locate the @deepseek-ai scope directory that backs the running official dsh. */
function findOfficialClosure(dshRealPath) {
  // dshRealPath points at the CLI entry: <scope>/dsh/lib/bin.js (npm layout)
  // or a .bin symlink into <store>/@deepseek-ai/dsh/... (pnpm layout).
  let probe = dirname(dshRealPath)
  for (let hop = 0; hop < 6; hop += 1) {
    const scope = join(probe, "node_modules", "@deepseek-ai")
    if (existsSync(join(scope, "dsh", "package.json"))) return scope
    const nested = join(probe, "node_modules", "@deepseek-ai")
    if (existsSync(join(nested, "dsh-web", "package.json"))) return nested
    probe = dirname(probe)
  }
  fail("could not locate the official @deepseek-ai dependency closure near the dsh binary")
}

function countLinked(scope) {
  try { return readdirSync(scope).length } catch { return 0 }
}

const dshRealPath = findDshBinary()
let scope = findOfficialClosure(dshRealPath)

// Prefer the dsh package's own nested closure when both exist: it is the exact
// tree the running CLI loads its own dependencies from.
const nested = join(scope, "dsh", "node_modules", "@deepseek-ai")
if (existsSync(join(nested, "dsh-web", "package.json"))) scope = nested

console.log(`link-peers: official closure at ${scope} (${countLinked(scope)} packages)`)

const nodeModules = join(pluginRoot, "node_modules")
for (const packageName of PEER_PACKAGES) {
  // scope already ends with "@deepseek-ai"; the package name's second segment applies.
  const packageSegments = packageName.split("/").slice(1)
  const targetDir = join(scope, ...packageSegments)
  if (!existsSync(join(targetDir, "package.json"))) {
    fail(`${packageName} not found in the official closure (${targetDir}); is the dsh installation complete?`)
  }
  const link = join(nodeModules, ...packageName.split("/"))
  const targetPath = join(targetDir, "package.json")
  try {
    if (lstatSync(link).isSymbolicLink() && realpathSync(link) === realpathSync(targetDir)) {
      console.log(`link-peers: ${packageName} already linked`)
      continue
    }
  } catch { /* absent — fall through and create */ }
  mkdirSync(dirname(link), { recursive: true })
  try { unlinkSync(link) } catch { /* absent */ }
  symlinkSync(targetDir, link, "dir")
  console.log(`link-peers: ${packageName} -> ${targetDir}`)
}
console.log("link-peers: done")

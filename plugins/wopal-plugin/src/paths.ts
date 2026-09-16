/**
 * Path normalisation for the Wopal home root.
 *
 * `WOPAL_HOME` reaches the plugin from several places that do not all agree on
 * the spelling: a shell profile exports `$HOME/.wopal` (absolute), while some
 * hosts inject the literal template `~/.wopal` unexpanded. A raw value must
 * never be fed straight into `path.join`, because `join("~/.wopal", "logs")`
 * yields the *relative* path `~/.wopal/logs`, which then resolves against the
 * process cwd — creating a junk `~/` directory inside the plugin package.
 *
 * Every consumer must therefore route the value through `resolveWopalHome`.
 */

import { homedir } from "os";
import { join, resolve } from "path";

/** Expand a leading `~` (bare or `~/…`) into the user's home directory. */
function expandHome(value: string): string {
  if (value === "~") return homedir();
  if (value.startsWith("~/")) return join(homedir(), value.slice(2));
  return value;
}

/**
 * Resolve a raw `WOPAL_HOME` value into an absolute path.
 *
 * - `~` / `~/…` is expanded against the user's home directory
 * - a relative path is absolutised against the current working directory
 * - a missing, empty, or whitespace-only value falls back to `<home>/.wopal`
 */
export function resolveWopalHome(raw?: string | undefined): string {
  const trimmed = raw?.trim();
  if (!trimmed) return join(homedir(), ".wopal");
  return resolve(expandHome(trimmed));
}

/**
 * Global test isolation.
 *
 * `WOPAL_HOME` decides where the plugin writes memory, session context, prompt
 * overrides, and logs. Tests that never touch it would otherwise inherit the
 * ambient value from the developer's shell — which on this machine is the
 * literal, unexpanded `~/.wopal`. Any raw `path.join` on that value produces a
 * *relative* path and litters the plugin package with a junk `~/` directory
 * (see `src/paths.ts`). With no ambient value at all, the same tests fall back
 * to the real `~/.wopal` and pollute the user's live home.
 *
 * This setup pins `WOPAL_HOME` to a per-file temporary directory (an ABSOLUTE
 * path, so the `~` class of bug cannot recur) before any test module loads.
 * Tests that manage `WOPAL_HOME` themselves still override it locally and
 * restore to this isolated value.
 */

import { mkdtempSync, rmSync } from "fs";
import { join } from "path";
import { tmpdir } from "os";

const isolatedRoot = mkdtempSync(join(tmpdir(), "wopal-test-home-"));

process.env.WOPAL_HOME = join(isolatedRoot, "home");

// Never inherit a developer shell's provider credentials — resource clients
// must only ever be constructed from explicit test fixtures.
for (const key of [
  "WOPAL_LLM_BASE_URL",
  "WOPAL_LLM_MODEL",
  "WOPAL_LLM_API_KEY",
  "WOPAL_EMBEDDING_BASE_URL",
  "WOPAL_EMBEDDING_MODEL",
  "WOPAL_EMBEDDING_API_KEY",
] as const) {
  delete process.env[key];
}

process.on("exit", () => {
  try {
    rmSync(isolatedRoot, { recursive: true, force: true });
  } catch {
    // best-effort cleanup
  }
});

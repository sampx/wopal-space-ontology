/**
 * Dependency boundary guard.
 *
 * The plugin consumes ellamaka's fork contract layer and SDK through
 * `@wopal/ellamaka-plugin` and `@wopal/ellamaka-sdk`. The upstream scope must
 * not leak back in: a residual import resolves against a second, divergent
 * copy of the contract and drifts silently from the engine.
 *
 * The forbidden scope string is assembled at runtime so this guard file never
 * matches itself when it scans `src/`.
 */

import { describe, it, expect } from "vitest";
import { readdirSync, readFileSync, statSync } from "fs";
import { dirname, join } from "path";
import { fileURLToPath } from "url";

const SRC_DIR = dirname(fileURLToPath(import.meta.url));
const UPSTREAM_SCOPE = ["@open", "code-ai"].join("");

function collectSourceFiles(dir: string): string[] {
  const files: string[] = [];
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) {
      files.push(...collectSourceFiles(full));
    } else {
      files.push(full);
    }
  }
  return files;
}

describe("dependency boundary", () => {
  it("has no upstream package references anywhere under src/", () => {
    const hits: string[] = [];
    for (const file of collectSourceFiles(SRC_DIR)) {
      readFileSync(file, "utf8")
        .split("\n")
        .forEach((line, index) => {
          if (line.includes(UPSTREAM_SCOPE)) {
            hits.push(`${file}:${index + 1}: ${line.trim()}`);
          }
        });
    }
    expect(hits).toEqual([]);
  });

  it("package.json declares no upstream dependencies", () => {
    const manifest = JSON.parse(
      readFileSync(join(SRC_DIR, "..", "package.json"), "utf8"),
    ) as { dependencies?: Record<string, string>; devDependencies?: Record<string, string> };
    const offenders = Object.keys({
      ...manifest.dependencies,
      ...manifest.devDependencies,
    }).filter((name) => name.startsWith(UPSTREAM_SCOPE));
    expect(offenders).toEqual([]);
  });

  it("package.json pins the fork contract and SDK at the same exact version", () => {
    const manifest = JSON.parse(
      readFileSync(join(SRC_DIR, "..", "package.json"), "utf8"),
    ) as { dependencies?: Record<string, string> };
    const deps = manifest.dependencies ?? {};
    expect(deps["@wopal/ellamaka-plugin"]).toMatch(/^\d+\.\d+\.\d+$/);
    expect(deps["@wopal/ellamaka-sdk"]).toMatch(/^\d+\.\d+\.\d+$/);
    expect(deps["@wopal/ellamaka-plugin"]).toBe(deps["@wopal/ellamaka-sdk"]);
  });

  it("types.ts declares none of the hand-copied fork contract types", () => {
    const source = readFileSync(join(SRC_DIR, "types.ts"), "utf8");
    const declarations =
      /export\s+(?:type|interface)\s+(SystemPromptSectionKind|SystemPromptSection|SystemPromptMetadata)\b/;
    expect(declarations.test(source)).toBe(false);
  });
});

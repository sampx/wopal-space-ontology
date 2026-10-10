/**
 * Shared types for the plugin's extension of the stock policy shape. Types
 * only — no runtime code.
 * @module dsh-sandbox-roots/internal/types
 */

import type { SandboxExecutionPolicy } from '@deepseek-ai/dsh-sandbox'

/**
 * The `sandbox-policy` settings-section shape: the extra writable roots the
 * user document carries. Schema-optional; the composition entry (and
 * therefore every resolved section) always carries an array. A type alias on
 * purpose: the implicit index signature keeps the section assignable to the
 * schemastery `Dict`-extended schema parameter types.
 */
export type SandboxRootsSection = {
  /** Extra writable directory roots as configured (`~` and relative spellings allowed). */
  writableRoots?: string[]
}

/**
 * The resolved policy extension: the stock execution policy plus the
 * settings-derived extra roots, attached under `workspace-write` only.
 */
export type WithExtras = SandboxExecutionPolicy & SandboxRootsSection

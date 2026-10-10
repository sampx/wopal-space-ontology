/**
 * The sandbox-policy service replacement: stock `SandboxPolicyService`
 * resolution (mode, session cwd, override kit, prompt context) with the
 * settings document's extra writable roots attached to every
 * `workspace-write` policy. The enforcing consumers — the fs fence
 * (`./fs`) and the process wrapper (`./sandbox`) — read the extra
 * `writableRoots` field; stock consumers see the plain policy shape.
 *
 * @module dsh-sandbox-roots
 */

import { Context } from '@deepseek-ai/cordis'
import z from '@deepseek-ai/schemastery'
import { SandboxPolicyService } from '@deepseek-ai/dsh-sandbox-policy'
import type { Config as PolicyConfig, SandboxPolicyRequest } from '@deepseek-ai/dsh-sandbox-policy'
import type {} from '@deepseek-ai/dsh-settings'
import { expandRoot } from './internal/roots.ts'
import type { SandboxRootsSection, WithExtras } from './internal/types.ts'

export type { SandboxRootsSection, WithExtras } from './internal/types.ts'

/**
 * Plugin config: the stock sandbox-policy keys verbatim plus the extra
 * writable roots (the settings section's composition base layer).
 */
export interface Config extends PolicyConfig {
  /** Extra canonical-or-tilde writable roots honored under `workspace-write` (default: none). */
  writableRoots?: string[]
}

/**
 * The settings section schema — the only field this plugin owns in the
 * `sandbox-policy` settings namespace. `mode`/`workspaceRoot` deliberately
 * stay out: a user document carrying them fails the section schema, keeping
 * those facts composition-owned.
 */
const settingsSectionSchema: z<SandboxRootsSection> = z.object({
  writableRoots: z.array(z.string()).default([]),
})

/**
 * The policy service (`ctx.sandboxPolicy`). Registers the `sandbox-policy`
 * settings section when the settings service is present and stamps every
 * resolved `workspace-write` policy with the current extra roots as
 * `writableRoots` (canonical, deduplicated; absent when the list is empty, so
 * the stock policy shape is preserved).
 */
export class SandboxRootsPolicyService extends SandboxPolicyService {
  // Inline schema call: the config catalog walks `static Config` statically.
  static Config: z<Config> = z.object({
    mode: z.union(['read-only', 'workspace-write', 'danger-full-access'] as const).default('read-only'),
    workspaceRoot: z.string(),
    writableRoots: z.array(z.string()).default([]),
  })

  // Identical to the stock injection: the settings attachment is a lazy
  // `ctx.inject` so the service loads with or without the settings service.
  static inject = ['sessionProjections']

  /** The current extra-roots source: the settings section while attached, the composition entry otherwise. */
  private source: () => readonly string[] = () => this.baseRoots
  private readonly baseRoots: string[]

  constructor(ctx: Context, config: Config) {
    super(ctx, config)
    this.baseRoots = config.writableRoots ?? []
    ctx.inject(['settings'], (settingsCtx) => {
      settingsCtx.settings.installSection(ctx, 'sandbox-policy', settingsSectionSchema, { writableRoots: this.baseRoots }, {
        setSource: (section) => {
          this.source = () => section().writableRoots ?? []
        },
        onChange: () => {
          // Roots are re-read on every resolve; nothing else derives from them.
        },
      })
    })
  }

  /**
   * Resolve the complete policy for one capability call — the stock mode,
   * workspace root, and session identity, plus the settings-derived
   * `writableRoots` under `workspace-write` (expanded, canonical,
   * deduplicated; the field is omitted when no extra root is configured).
   * @param request - optional session and approved mode override.
   * @returns the fully resolved per-call policy.
   */
  override resolve(request: SandboxPolicyRequest = {}): WithExtras {
    const base = super.resolve(request)
    if (base.mode !== 'workspace-write') return base
    const extras = [...new Set(this.source().map(expandRoot))]
    if (extras.length === 0) return base
    return { ...base, writableRoots: extras }
  }
}

export default SandboxRootsPolicyService

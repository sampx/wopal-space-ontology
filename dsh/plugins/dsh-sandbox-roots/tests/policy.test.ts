/**
 * Policy-service tests with minimal fake dependencies: the settings-section
 * attachment contract, expansion of the settings roots, and hot reload.
 */

import { homedir } from 'node:os'
import { join, resolve } from 'node:path'
import { Context } from '@deepseek-ai/cordis'
import type { Session } from '@deepseek-ai/dsh-session'
import { describe, expect, it } from 'vitest'
import { canonicalPath } from '@deepseek-ai/dsh-sandbox'
import { SandboxRootsPolicyService } from '../src/index.ts'
import type { WithExtras } from '../src/index.ts'

type PolicyConfig = ConstructorParameters<typeof SandboxRootsPolicyService>[1]

/** The settings-section fake: the `installSection` contract, nothing more. */
function fakeSettings(initial: { writableRoots?: string[] }): {
  settings: { installSection: (owner: unknown, ns: string, schema: unknown, entry: unknown, hooks: FakeHooks) => void }
  set: (next: { writableRoots?: string[] }) => void
  calls: { ns?: string; schema?: unknown; entry?: unknown }
} {
  const calls: { ns?: string; schema?: unknown; entry?: unknown } = {}
  let current = initial
  const settings = {
    installSection: (_owner: unknown, ns: string, schema: unknown, entry: unknown, hooks: FakeHooks) => {
      calls.ns = ns
      calls.schema = schema
      calls.entry = entry
      hooks.setSource(() => current)
      hooks.onChange()
    },
  }
  return {
    settings,
    set: (next) => { current = next },
    calls,
  }
}

interface FakeHooks {
  setSource: (current: () => { writableRoots?: string[] }) => void
  onChange: () => void
}

function fakeSession(cwd?: string): Session {
  const id = 'sess-fake'
  return { id, header: { id, ...(cwd === undefined ? {} : { cwd }) } } as unknown as Session
}

const tick = (): Promise<void> => new Promise(resolve => setImmediate(resolve))

async function mounted(
  config: PolicyConfig,
  settings?: ReturnType<typeof fakeSettings>['settings'],
): Promise<SandboxRootsPolicyService> {
  const ctx = new Context()
  ctx.provide('sessionProjections', { register: () => () => {}, stateOf: () => undefined })
  if (settings !== undefined) ctx.provide('settings', settings)
  return new SandboxRootsPolicyService(ctx, config)
}

describe('SandboxRootsPolicyService', () => {
  it('resolves the stock-shaped policy while settings stay absent and config roots are empty', async () => {
    const service = await mounted({ mode: 'workspace-write', workspaceRoot: '/fallback', writableRoots: [] })
    await tick()
    expect(service.resolve()).toEqual({ mode: 'workspace-write', workspaceRoot: resolve('/fallback') })
  })

  it('falls back to the composition config roots while settings stay absent', async () => {
    const service = await mounted({ mode: 'workspace-write', workspaceRoot: '/fallback', writableRoots: ['/cfg/root'] })
    await tick()
    expect(service.resolve()).toEqual({
      mode: 'workspace-write',
      workspaceRoot: resolve('/fallback'),
      writableRoots: [canonicalPath('/cfg/root')],
    })
  })

  it('carries no writableRoots outside workspace-write even with configured roots', async () => {
    for (const mode of ['read-only', 'danger-full-access'] as const) {
      const service = await mounted({ mode, workspaceRoot: '/fallback', writableRoots: ['/cfg/root'] })
      await tick()
      const policy = service.resolve()
      expect(policy.mode).toBe(mode)
      expect('writableRoots' in policy).toBe(false)
    }
  })

  it('attaches the settings roots expanded, canonicalized, and deduplicated', async () => {
    const settings = fakeSettings({ writableRoots: ['~/docs', '~/docs', 'rel-root'] })
    const service = await mounted({ mode: 'workspace-write', workspaceRoot: '/fallback', writableRoots: [] }, settings.settings)
    await tick()
    const policy = service.resolve() as WithExtras
    expect(policy.writableRoots).toEqual([
      canonicalPath(join(homedir(), 'docs')),
      canonicalPath(resolve('rel-root')),
    ])
  })

  it('installs the section under the sandbox-policy namespace with the composition entry as base', async () => {
    const settings = fakeSettings({ writableRoots: ['/tmp/from-settings'] })
    await mounted({ mode: 'workspace-write', workspaceRoot: '/fallback', writableRoots: ['/cfg/root'] }, settings.settings)
    await tick()
    expect(settings.calls.ns).toBe('sandbox-policy')
    expect(settings.calls.entry).toEqual({ writableRoots: ['/cfg/root'] })
    // The section schema is a schemastery schema (callable, with toJSON), the
    // same kind the stock settings consumer passes.
    expect(typeof (settings.calls.schema as { toJSON?: unknown })?.toJSON).toBe('function')
  })

  it('reflects a settings change on the next resolve, including back to no extra roots', async () => {
    const settings = fakeSettings({ writableRoots: ['/tmp/first-root'] })
    const service = await mounted({ mode: 'workspace-write', workspaceRoot: '/fallback', writableRoots: [] }, settings.settings)
    await tick()
    expect((service.resolve() as WithExtras).writableRoots).toEqual([canonicalPath('/tmp/first-root')])

    settings.set({ writableRoots: ['~/second-root'] })
    expect((service.resolve() as WithExtras).writableRoots).toEqual([canonicalPath(join(homedir(), 'second-root'))])

    settings.set({})
    expect('writableRoots' in service.resolve()).toBe(false)
  })

  it('keeps the stock session-cwd and approved-override semantics', async () => {
    const settings = fakeSettings({ writableRoots: ['/tmp/extra'] })
    const service = await mounted({ mode: 'workspace-write', workspaceRoot: '/fallback', writableRoots: [] }, settings.settings)
    await tick()
    expect(service.resolve({ session: fakeSession('/projects/x') })).toEqual({
      mode: 'workspace-write',
      workspaceRoot: resolve('/projects/x'),
      sessionId: 'sess-fake',
      writableRoots: [canonicalPath('/tmp/extra')],
    })
    const overridden = service.resolve({ session: fakeSession('/projects/x'), mode: 'read-only' })
    expect('writableRoots' in overridden).toBe(false)
  })
})
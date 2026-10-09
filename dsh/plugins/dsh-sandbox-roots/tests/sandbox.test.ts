/**
 * Process-wrap tests: extra roots reach the Seatbelt profile, the no-extras
 * path stays identical to the stock provider (or fails closed identically
 * where the sandbox environment blocks runner selection), and a non-darwin
 * runner platform fails loud instead of silently dropping the roots.
 */

import { Context } from '@deepseek-ai/cordis'
import { LocalSandboxProvider } from '@deepseek-ai/dsh-sandbox-local'
import type { SandboxPolicy } from '@deepseek-ai/dsh-sandbox'
import { describe, expect, it } from 'vitest'
import { stockWritableRoots } from '../src/internal/roots.ts'
import { seatbeltProfile } from '../src/internal/seatbelt.ts'
import { SandboxRootsSandboxProvider } from '../src/sandbox.ts'

type ProviderConfig = ConstructorParameters<typeof LocalSandboxProvider>[1]

const isDarwin = process.platform === 'darwin'

function mount(): { provider: SandboxRootsSandboxProvider; stock: LocalSandboxProvider } {
  const config = { runnerCommand: [], runnerFailureSignatures: [], probeTimeoutMs: 5_000 } as ProviderConfig
  return {
    provider: new SandboxRootsSandboxProvider(new Context(), config),
    stock: new LocalSandboxProvider(new Context(), config),
  }
}

function policy(writableRoots?: string[]): SandboxPolicy {
  return {
    mode: 'workspace-write',
    workspaceRoot: '/ws',
    ...(writableRoots === undefined ? {} : { writableRoots }),
  }
}

/** Run one confine call, capturing the throw instead of propagating it. */
function attempt(provider: { confine: (argv: readonly string[], policy: SandboxPolicy) => unknown }, argv: readonly string[], pol: SandboxPolicy): unknown {
  try {
    return { ok: provider.confine(argv, pol) }
  } catch (error) {
    return { threw: error instanceof Error ? error.name : error }
  }
}

describe('SandboxRootsSandboxProvider', () => {
  it.skipIf(!isDarwin)('wraps extra roots into the seatbelt profile with the stock seatbelt evidence', () => {
    const { provider } = mount()
    const result = provider.confine(['sh', '-c', 'echo hi'], policy(['/tmp/extra-root']))
    expect(result.argv.slice(0, 2)).toEqual(['sandbox-exec', '-p'])
    expect(result.argv[3]).toBe('--')
    expect(result.argv.slice(4)).toEqual(['sh', '-c', 'echo hi'])
    const stockRoots = stockWritableRoots(policy())
    const profile = result.argv[2]
    expect(profile).toContain(`(subpath "${stockRoots[0]}")`)
    expect(profile).toContain('(subpath "/tmp/extra-root")')
    expect(result.enforcement).toBe('full')
    expect(result.denialSignatures).toEqual(['operation not permitted'])
    expect(result.runnerFailureRules).toEqual([{ fatalSignatures: ['sandbox-exec: '] }])
  })

  it('stays identical to the stock provider without extra roots, or fails closed identically', () => {
    const { provider, stock } = mount()
    const argv = ['sh', '-c', 'echo hi']
    expect(attempt(provider, argv, policy())).toEqual(attempt(stock, argv, policy()))
  })

  it('fails loud for extra roots on a non-darwin runner platform', () => {
    const { provider } = mount()
    const actual = process.platform
    Object.defineProperty(process, 'platform', { value: 'linux', configurable: true })
    try {
      expect(() => provider.confine(['sh'], policy(['/tmp/extra-root']))).toThrowError(/writableRoots.*Seatbelt/i)
    } finally {
      Object.defineProperty(process, 'platform', { value: actual, configurable: true })
    }
  })

  it.skipIf(!isDarwin)('merges the stock roots with deduplicated extras into one profile', () => {
    const { provider } = mount()
    const workspace = '/nonexistent-dsh-roots-ws'
    const passed = { mode: 'workspace-write' as const, workspaceRoot: workspace, writableRoots: [workspace, '/tmp/extra-root', workspace] }
    const result = provider.confine(['true'], passed)
    expect(result.argv[2]).toBe(seatbeltProfile([...stockWritableRoots(passed), '/tmp/extra-root']))
  })
})

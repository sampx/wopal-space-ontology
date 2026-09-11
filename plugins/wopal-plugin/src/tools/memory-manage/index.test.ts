import { describe, expect, it, vi } from 'vitest';

import { createMemoryManageTool } from './index.js';

function getToolArgEnum(toolDefinition: unknown): string[] {
  const args = (toolDefinition as { args: { command: { values?: string[]; options?: string[] } } }).args;
  const schema = args.command as unknown as {
    values?: string[];
    options?: string[];
    _def?: { values?: string[] };
  };
  return schema.values ?? schema.options ?? schema._def?.values ?? [];
}

function getExecute(toolDefinition: unknown) {
  return (toolDefinition as { execute: (...args: unknown[]) => Promise<string> }).execute;
}

describe('memory_manage: pure memory operations', () => {
  it('does not expose distillation actions after the context migration', () => {
    const tool = createMemoryManageTool({} as never);
    const commands = getToolArgEnum(tool);

    expect(commands).not.toContain('distill');
    expect(commands).not.toContain('confirm');
    expect(commands).not.toContain('cancel');
    expect(commands).toContain('search');
    expect(commands).toContain('add');
  });

  it('does not reference distillation actions in the tool description', () => {
    const tool = createMemoryManageTool({} as never) as { description: string };

    expect(tool.description.toLowerCase()).not.toContain('distill');
    expect(tool.description).not.toContain('- confirm:');
    expect(tool.description).not.toContain('- cancel:');
  });

  it('rejects distillation actions as unknown commands', async () => {
    const tool = createMemoryManageTool({} as never);
    const execute = getExecute(tool);

    const result = await execute({ command: 'distill' }, { sessionID: 'ses-test' });

    expect(result).toContain('未知命令');
    expect(result).not.toContain('Distillation');
  });

  it('keeps search available without a distill engine dependency', async () => {
    const store = {
      searchByQuery: vi.fn().mockResolvedValue([]),
    } as never;
    const tool = createMemoryManageTool(store);
    const execute = getExecute(tool);

    const result = await execute({ command: 'search', query: 'anything' }, { sessionID: 'ses-test' });

    expect(store.searchByQuery).toHaveBeenCalled();
    expect(result).not.toContain('unknown');
  });
});

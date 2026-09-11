import { describe, expect, it } from 'vitest';

import {
  ECHO_REMINDER_DISTILL,
  formatPreviewReport,
  formatConfirmReportWithDedup,
} from './context-formatters.js';

describe('context distillation formatters', () => {
  it('guides the user to context_manage for confirm and cancel', () => {
    const output = formatPreviewReport(
      [
        {
          category: 'knowledge',
          body: '## [技术知识]: 测试\n这是一条用于验证 formatter 归属的候选记忆正文。',
          tags: ['context'],
          importance: 0.7,
        },
      ],
      'Test Session',
      3,
    );

    expect(output).toContain('context_manage action=confirm');
    expect(output).toContain('context_manage action=cancel');
    expect(output).not.toContain('memory_manage command=confirm');
    expect(output).not.toContain('memory_manage command=cancel');
  });

  it('echo reminder points at context_manage without memory_manage distill guidance', () => {
    expect(ECHO_REMINDER_DISTILL).toContain('context_manage');
    expect(ECHO_REMINDER_DISTILL).not.toContain('memory_manage');
  });

  it('confirm report renders created/merged/skipped counts', () => {
    const output = formatConfirmReportWithDedup(
      [{ category: 'fact', body: 'body text', tags: [], importance: 0.5 }],
      'Title',
      { created: 1, merged: 0, skipped: 0 },
    );

    expect(output).toContain('Distillation Complete');
    expect(output).toContain('Created:** 1');
  });
});

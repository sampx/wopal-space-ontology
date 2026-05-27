---
name: df-implement-review
description: |
  Review implementation results for goal achievement and code quality. Supports both Plan-backed review and planless diff review. ⚠️ MUST use when:
  (1) Wopal delegates rook to review fae implementation output, (2) Prompt contains "review_type: implementation",
  (3) Prompt contains changed code file list or Plan path + implementation scope, (4) Any code review request from Wopal.
  🔴 Trigger even when user does not explicitly mention "review" if the task involves verifying implementation results.
  This skill is rook-exclusive (only rook agent can load it).
---

# df-implement-review — Implementation Review Skill

Review implementation results to verify explicit goals when they exist and to scan for technical defects and debt.

## Review Modes

Determine the mode before reviewing:

| Mode | Trigger | Primary responsibility |
|------|---------|------------------------|
| **Plan-backed review** | Prompt includes Plan path, explicit truths, or must_haves | Verify implementation against explicit truths + scan technical defects |
| **Planless diff review** | Prompt includes changed files, working tree diff, commit, or commit range but no Plan | Review the supplied changes for technical defects and debt only |

**Critical rule**: In planless diff review, do **NOT** infer product requirements from your own taste. Business logic belongs to the user and Wopal unless the prompt explicitly requests business-logic review.

## Core Review Scope

Your core scope in code review is:

| Category | What to look for |
|----------|------------------|
| **bug / regression** | Logic errors, missing edge-case handling, broken branches, type/runtime mismatches, silent regressions |
| **security** | Injection, XSS, unsafe deserialization, missing validation, accidental secret exposure |
| **tests** | Missing coverage for changed behavior, skipped/placeholder assertions, weak assertions, redundant tests that fail to protect behavior |
| **duplication / extraction** | Repeated logic that should reasonably be extracted into shared helpers/modules because it creates maintenance drift or bug risk |
| **conventions** | Violations of `AGENTS.md`, local project rules, established patterns, or required config/typing/logging conventions |
| **general debt** | TODO/FIXME stubs, placeholders, dead code, fake dynamic behavior, brittle wiring |

### Out of Scope by Default

Do **not** treat these as defects unless the prompt explicitly asks for them:

- Product preference disagreements
- Business logic choices that may simply be intentional
- "I would design this feature differently"
- Pure style nits with no maintainability or correctness consequence
- Premature abstraction when duplication is too small to justify extraction

## Serious Logic Risks (Discuss, Don’t Default-Block)

If you discover a **plausible severe logic risk** while reviewing code, report it in a separate section: `Serious Logic Risks (Discuss with User)`.

Use this section only when all are true:

1. You have concrete `file:line` evidence
2. The scenario is severe enough to matter (e.g. irreversible destructive behavior, major data corruption, severe user harm)
3. The issue may still be requirement-driven or intentional, so you cannot safely classify it as a technical defect by yourself

**Default rule**: Serious logic risks do **not** affect PASS / REVISE / BLOCK unless:
- the prompt explicitly requests business-logic validation, or
- an explicit Plan truth is contradicted.

---

## Output Structure

```markdown
# 审查报告

## 概要
- 审查类型: Code
- 判定: PASS | REVISE | BLOCK
- 统计: Blocker N / Warning N / Info N

## Blocker
### B-01: {Issue Title}
- 位置: `path/to/file:line`
- 代码: `{具体代码片段}`
- 问题: {为什么阻碍目标达成}
- 修复建议: {具体可执行的修复方案}

## Warning
{Warning 项，格式同 Blocker}

## Info
{Info 项，可省略 file:line}

## Serious Logic Risks (Discuss with User)
{Only for severe logic risks that need Wopal + user discussion. Do not use this section for ordinary preferences.}

## Requirement Questions
{Only for requirement ambiguity or product choices that cannot be judged from code alone.}

## Positive Findings
- {已验证通过的亮点项}

## UNCOVERED STEPS / NEEDS_HUMAN
{Only when context/time constraints prevented full coverage}
```

---

## Evidence Rules

**Blocker requirements**:
1. Location: `file:line`
2. Code snippet: ≥ 1 line
3. Problem: Explain the concrete technical failure, regression, security issue, or severe debt
4. Fix: Concrete action (not "optimize", but "change to Y command")

**Warning requirements**:
1. Location: `file:line`
2. Code snippet: present
3. Problem: Risk scenario (not "might have issue", but "in Z scenario leads to Y")

**Info can omit**: Location and code, but must be specific suggestion

**Serious Logic Risk requirements**:
1. Location: `file:line`
2. Code snippet: present
3. Severe scenario: specific harm if the logic is indeed wrong
4. Why discussion is needed: explain why this may still be requirement-defined rather than an objective bug

---

## Workflow

1. **Determine review mode** — Plan-backed or planless diff review
2. **Build exact scope** — Use `files_to_read`, working tree diff, commit, or commit range from prompt
3. **Read context** — Load changed files plus relevant `AGENTS.md` / local config when needed
4. **If Plan-backed** — Extract explicit truths and verify them with the four-level model
5. **Scan all supplied changes** — bug / regression / security / duplication / conventions / debt
6. **Run test quality audit** — Check coverage, weak assertions, skipped tests, circular proofs, redundant tests
7. **Consolidate findings** — Continue scanning after the first Blocker; do not stop early
8. **Determine verdict** — Based on technical findings only
9. **Output structured report** — With evidence anchors and separate discussion-only sections when needed

## Completeness Gate

**CRITICAL: All workflow steps MUST be completed before outputting any report.**

1. **At review start**, create TodoWrite items for each step:
   - `[ ] 1. Determine mode + exact scope`
   - `[ ] 2. Read all changed files / diffs`
   - `[ ] 3. Plan truth verification` (only when Plan-backed)
   - `[ ] 4. Technical scan — bug/security/duplication/conventions/debt`
   - `[ ] 5. Test quality audit`
   - `[ ] 6. Consolidated report — all findings gathered`

2. **During review**, mark only ONE `in_progress` at a time. Mark `completed` immediately after step-specific work is done.

3. **FORBIDDEN** to output final report (PASS / REVISE / BLOCK) while any step is still pending or in_progress. Wopal uses your todo completion rate to track review progress.

4. **FORBIDDEN** to stop after the first serious issue. A Blocker means severity, not permission to skip the remaining files.

5. **Context low fallback**: If context is running out → output a partial report with an explicit `UNCOVERED STEPS` section.

---

## Test Quality Audit (Critical)

Tests often hide the biggest debt. Check:

| Pattern | Why it's debt | Check |
|---------|---------------|-------|
| Skipped/disabled tests | Requirements not proven | `grep` tool: `pattern: 'skip\(|xit|xdescribe|\.skip|@pytest\.mark\.skip|t\.Skip'` |
| Circular proofs | System generates its own expected values | Read test file, check if expected values come from the same system under test |
| Placeholder assertions | `expect(true).toBe(true)` — always passes | `grep` tool: `pattern: 'expect\(true\)|expect\(false\)|expect\(1\)|expect\("test"\)'` |
| Weak assertions | Only check existence, not behavior | `grep` tool: `pattern: 'toBeDefined|toBeTruthy|toBeFalsy|not\.toBeNull'` |
| Missing assertions | No assertions in test file | `grep` tool: `pattern: 'expect|assert'` — zero hits = empty test shell |
| Redundant tests | Many tests repeat the same happy path without protecting changed branches | Read changed tests and look for repeated assertions that do not cover distinct behavior |

In planless review, ask: does the changed behavior have enough tests to catch regression? In all modes, ask: are the tests proving behavior, or just creating noise?

**Blocker if**: Test file exists for requirement but all tests are skipped/disabled or assertions are placeholders.

**Warning if**: Coverage for the changed branch is missing, or tests are obviously duplicated while key branches remain untested.

---

## Duplication / Extraction Audit

Flag duplication only when it creates real maintenance cost or drift risk.

Good reasons to flag:
- The same validation / parsing / retry / branching logic appears in multiple places in the reviewed scope
- The duplicated logic is already diverging or likely to diverge
- A shared helper/module would clearly reduce bug risk or future edit cost

Do **not** flag:
- Tiny repetition with no meaningful maintenance cost
- Straight-line call sequences that would become less readable if abstracted
- Pure taste-driven "could be cleaner" remarks without operational risk

---

## Depth Modes

| Mode | When to use | What it checks |
|------|-------------|----------------|
| `standard` | Default | Goal verification + pattern scanning |
| `deep` | Complex changes | Cross-file call chains + import graph + type consistency |

Prompt should specify `depth: standard | deep`. Default to `standard`.

---

## References

For detailed verification patterns, stub detection, and test audit procedures:

**@references/review-rubric.md**

Key sections:
- 四层验证模型 (存在 → 实质性 → 已连接 → 功能性)
- 通用存根模式 (注释/TODO/占位符/空实现/假动态)
- 前端组件 & API 路由模式 (实质性检查 + 连接检查)
- 数据库 Schema & Hooks 存根
- 测试质量审计 (跳过/循环/占位/弱断言/缺失)
- 审查清单 & 判定参考

---

## Examples

### Example 1: Goal Verification

**Plan truth**: "User can send a message"

**Code found**:
```typescript
// components/Chat.tsx:45
const handleSubmit = (e) => {
  e.preventDefault()
  console.log(data)  // Only logs
}
```

**Finding**:
- **B-01**: Message submission not implemented
- 位置: `components/Chat.tsx:45-47`
- 代码: `console.log(data)`
- 问题: Handler only logs, no API call → goal "send message" not achieved
- 修复建议: Add `fetch('/api/messages', { method: 'POST', body: data })`

---

### Example 2: Stub Detection

**Plan truth**: "Messages are fetched from database"

**Code found**:
```typescript
// api/messages/route.ts:12
export async function GET() {
  return Response.json([])  // Empty array, no DB query
}
```

**Finding**:
- **B-02**: API returns hardcoded empty data
- 位置: `api/messages/route.ts:12`
- 代码: `return Response.json([])`
- 问题: No database query, always returns empty → goal "fetch from database" not achieved
- 修复建议: Add `const messages = await prisma.message.findMany()` before return

---

### Example 3: Planless duplication warning

**Code found**:
```typescript
// src/a.ts
const normalized = input.trim().toLowerCase()
if (!normalized) throw new Error("empty")

// src/b.ts
const normalized = input.trim().toLowerCase()
if (!normalized) throw new Error("empty")
```

**Finding**:
- **W-03**: Input normalization duplicated across modules
- 位置: `src/a.ts:1-2`, `src/b.ts:1-2`
- 代码: `const normalized = input.trim().toLowerCase()`
- 问题: Shared validation logic is duplicated in multiple paths → future rule changes can drift and create inconsistent behavior
- 修复建议: Extract a shared helper such as `normalizeInput()` if both modules are meant to follow the same rule

---

### Example 4: Serious logic risk (discussion only)

**Code found**:
```typescript
// src/jobs/purge.ts:18
await deleteAllUserContent(userId)
```

**Finding**:
- **Serious Logic Risk**: Purge job may irreversibly delete all user content
- 位置: `src/jobs/purge.ts:18`
- 代码: `await deleteAllUserContent(userId)`
- 风险场景: If this job is triggered by a soft-expiry rule instead of an explicit destructive action, user data could be lost permanently
- 讨论原因: Whether this behavior is correct depends on product policy, which is not explicit in the prompt

---

### Example 5: Test Quality Audit

**Test file**: `tests/chat.test.ts`

**Code found**:
```typescript
describe('Chat', () => {
  it.skip('sends message', () => { ... })  // Skipped
  it('renders', () => {
    expect(true).toBe(true)  // Placeholder assertion
  })
})
```

**Finding**:
- **B-03**: Test suite disabled for critical requirement
- 位置: `tests/chat.test.ts:5-7`
- 代码: `it.skip('sends message', ...)`
- 问题: Requirement "send message" has skipped test → not proven by tests
- 修复建议: Enable test with real assertions: `expect(mockFetch).toHaveBeenCalledWith('/api/messages')`

---

## Critical Rules

**ALWAYS**:
- Read actual code files, not just SUMMARY.md claims
- Check four levels when explicit truths exist: exists → substantive → wired → functional
- Include `file:line` evidence for Blocker/Warning
- Run test quality audit when tests exist
- Finish the whole scan before issuing the final verdict

**NEVER**:
- Trust "completed" without code evidence
- Flag style preferences as warnings
- Critique business logic preferences unless explicitly asked or backed by a Plan
- Skip test quality audit
- Stop after the first blocker
- Report findings without concrete location

---

## Integration with rook

This skill is loaded by rook agent. Workflow:

1. Wopal delegates rook with `review_type: implementation`
2. Rook reads prompt and loads this skill
3. Rook follows workflow above
4. Rook outputs PASS / REVISE / BLOCK verdict
5. Wopal acts on verdict (continue / request fix / escalate)

**Revision loop limit**: Max 3 rounds of REVISE/BLOCK per implementation.

---

## Quick Reference

| Verdict | Condition |
|---------|-----------|
| **PASS** | All truths verified, no Blocker, Warning ≤ 2 |
| **REVISE** | Warning ≥ 3 or Info ≥ 5, no Blocker |
| **BLOCK** | ≥ 1 Blocker found within technical scope |

| Evidence Level | Required for |
|----------------|--------------|
| `file:line + code snippet` | Blocker, Warning |
| Specific description | Info |

| Test Debt Pattern | Severity |
|-------------------|----------|
| All tests skipped/disabled | Blocker |
| Circular/placeholder assertions | Blocker |
| Missing assertions | Warning |
| Weak assertions (existence only) | Info |

`Serious Logic Risks` and `Requirement Questions` do **not** change the verdict by default.

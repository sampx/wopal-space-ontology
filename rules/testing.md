---
trigger: model_decision
description: Follow this rule when designing, writing, changing, reviewing, or debugging automated tests, CI stability, or flaky tests.
keywords:
  - 'test'
  - 'testing'
  - 'unit test'
  - 'integration test'
  - 'e2e'
  - 'system test'
  - 'contract test'
  - 'ci'
  - 'flaky'
  - 'race'
  - 'timeout'
  - '测试'
---

# Testing Best Practices

## Goal

- The primary value of a test is to **reliably distinguish correct behavior from incorrect behavior**: bad code should reliably fail and good code should reliably pass.
- The same code, inputs, and controlled environment should produce the same result repeatedly; ordering, machine load, or unrelated tests must not change the conclusion.
- Obtain sufficient proof at the lowest practical cost. Escalate to a more expensive layer only when a lower layer cannot prove the relevant risk.
- Test speed is a quality attribute: give developers local, fast feedback first, then widen verification according to risk.

## Test Value

- Every test must protect a clear observable behavior, protocol, or invariant. If you cannot explain what broken implementation would make it fail, redesign the test.
- Assert outcomes, state, protocols, or effects rather than private implementation details, call counts, or internal structure unless those details are themselves part of the public contract.
- A success-path test must prove output or final state, not merely that no exception was thrown. Trigger failure paths explicitly and assert the specific error, preserved state, and cleanup result.
- Apply fault-injection / mutation thinking to important logic: deliberately introducing the target defect should make existing tests fail reliably. Coverage percentage is not a substitute for that proof.
- For behavior code, prefer red → green → refactor: first make a test fail because the behavior is missing or wrong, then implement it. The test itself should prove that it can catch the problem before the fix.

## Lowest-Cost Sufficient Layer

- Choose the test layer by the **boundary that must be proved**; do not enforce a fixed Unit/Integration/E2E percentage.
- A common escalation order is: pure Unit → boundary/Contract → Integration → System/E2E → release-specific verification.
- Do not promote behavior to real networks, real processes, or a full system merely because a higher layer feels "more realistic" when a lower layer can prove it reliably.
- Use Integration/Contract tests for real serialization, protocol compatibility, process boundaries, filesystems, databases, or local-tool collaboration. Use System/E2E only when external-system or real-host semantics are the thing being proved.
- When a high-layer test discovers a defect that can be reproduced reliably at a lower layer, add the lower-layer regression test instead of keeping only the expensive reproduction.
- A release gate proves that a release candidate is safe to ship. It should not unconditionally repeat the complete nightly/full CI suite. If a product requires Full CI as a release prerequisite, prefer reusing a trustworthy result for the exact same SHA rather than recomputing the same expensive suite.

## Determinism and Isolation

- Unit/Contract tests should not secretly depend on a real network, wall clock, user HOME, current cwd, undeclared environment variables, fixed ports, shared temporary directories, random ordering, or machine-global caches.
- Inject, freeze, fake, or isolate such dependencies. When real semantics are the subject under test, move the test to the layer that owns that resource.
- Each test owns only the resources it creates and cleans them up on success, failure, cancellation, and exceptional paths. Never delete or reuse state owned by another test.
- Any process-global/runtime-global mutation such as env, cwd, locale, global mocks, or singleton caches needs a clear owner and must restore the exact pre-test state.
- Tests must not depend on data left by another test. Running alone, in a different order, or in a related combination should preserve semantics.
- Concurrency is allowed only for genuinely independent tests. Shared process globals, ports, paths, database records, mock registries, or lifecycle resources are not independent by assumption.

## Test Doubles and Boundaries

- Do not define "Unit" as "mock every dependency". Stable, cheap, in-process collaborators are often more valuable when kept real.
- Put test doubles at explicit external-system, transport, time, randomness, or high-cost boundaries, or where a test must isolate side effects it does not own.
- Prefer dependency injection, services/factories/layers, or explicit seams over process-wide monkey patches or module replacement that can leak across tests.
- Use contract tests for cross-module or cross-process protocols so both sides agree on the same facts instead of mocking incompatible worlds independently.

## Async and Time

- Synchronize on **events, state, or completion signals produced by the operation under test**, never on a fixed sleep/delay that guesses readiness.
- Timeouts are failure backstops and deadlock protection, not readiness mechanisms. Increasing a timeout alone is never a flaky-test fix.
- For one-shot readiness, completion, or shutdown, expose an observable Promise/Future/Deferred/Latch/callback. Poll only genuinely published state and always use a defined termination condition.
- When using a fake clock, advance and restore it explicitly. Use real time only in a higher-layer test whose purpose is to verify timing or scheduling semantics.

## Flaky-Test Policy

- A flaky test is a defect, not acceptable CI noise. Classify the root cause: product race, test pollution, resource lifecycle, incorrect synchronization, ordering dependency, real external dependency, or environmental assumption.
- A fix must explain the root cause and remove the trigger. One successful rerun is not evidence.
- **Never** make flaky tests green by retry/until-green, merely increasing a timeout, weakening/removing assertions, shortening an observation window, fixed sleeps, or serializing the entire test suite.
- A test that inherently owns a shared resource may constrain concurrency at that test or fixture boundary; do not serialize the whole suite to hide ownership problems.
- Verify a flaky fix against the original failure scenario, independent cold processes, and relevant combined/order-sensitive execution. Any failed run means the issue remains unresolved.
- If the full suite still fails, inspect the failing evidence and reclassify it; do not loop until a green run appears.

## Performance and Verification Cost

- Run the smallest scope that can answer the current question: target test → owning module/package → related combination/integration → full suite.
- Do not repeatedly run expensive System/E2E checks after every small edit; widen verification when the risk boundary changes or the work is approaching delivery.
- Projects should maintain an explainable baseline or budget for important test entry points. Material regressions require explanation and removal of unnecessary real I/O, repeated setup, or duplicated suites.
- Concurrency is a cost optimization for independent tests, not a correctness prerequisite. Achieve isolation first, then parallelize.
- CI should surface failures early and locally. Nightly/full CI owns whole-repository health scanning; release gates own release-candidate-specific risk. Do not duplicate the same work across gates without an explicit requirement.

## External Systems and Shared Assets

- Real external accounts, repositories, services, or fixed topologies that must persist should be controlled read-only test assets; do not destroy or rebuild shared assets for a single run.
- Temporary branches, files, data, containers, processes, listeners, and sockets created by a test remain that test's responsibility and must leave no cross-run residue.
- Never put real credentials or production data into fixtures, logs, or assertion output. Distinguish product failures from environment failures and test-infrastructure failures.

## Review Checklist

Before delivering a test-related change, answer at least:

1. What behavior or invariant does this test protect?
2. What implementation defect makes it fail reliably?
3. Is this the lowest-cost layer that can prove the behavior?
4. Does it depend on undeclared time, network, environment, paths, global state, or ordering?
5. Does async synchronization use events/state rather than elapsed time?
6. Does every resource and process-global mutation have an owner and exceptional-path cleanup?
7. Is concurrency limited to genuinely independent state?
8. Does a flaky fix have root-cause evidence rather than retry/timeout/weaker assertions/global serialization?
9. Does verification widen from cheaper to more expensive scopes instead of jumping straight to the most expensive suite?
10. Is the cost of the new test proportionate to the risk it proves?

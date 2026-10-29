---
trigger: model_decision
description: Follow this rule when developing TypeScript or JavaScript in Node.js projects. Covers coding conventions and JavaScript/TypeScript test-runner conventions.
keywords:
  - 'typescript'
  - '.ts'
  - 'javascript'
  - '.js'
  - '测试'
  - 'test'
  - 'vitest'
  - 'jest'
  - '单元测试'
  - '集成测试'
  - '端到端'
  - 'e2e'
  - '测试金字塔'
---

# TypeScript Development Conventions

## Code Style

- Formatting is handled by the project's prettier config; style values (quotes, semicolons, indentation, line width) follow the project config, not hardcoded
- Do not use style enforcement tools other than ESLint/Prettier, to avoid conflicts between rules and tool config

## Naming Conventions

- Variables and functions: camelCase
- Classes and interfaces: PascalCase
- Constants: UPPER_SNAKE_CASE
- Private members: #privateField or _privateField

## Type Definitions

- Specify types for all function parameters and return values
- Use interfaces to define object types
- Use type aliases for complex types
- Prefer `interface` over `type`, unless union types or mapped types are needed

## Module Imports

- Use ES6 import/export
- Group in order: Node.js built-ins, third-party libraries, local modules
- Use named imports rather than default imports

## Async Operations

- Use async/await rather than Promise chains
- Handle errors properly (try/catch)
- Avoid using the `any` type

## Code Organization

- Export one primary functionality per file
- Place related functionality in the same directory
- Use index.ts to export the public API

## Testing

- Follow the shared `testing.md` rule for test value, layering, determinism, isolation, async synchronization, flaky-test handling, and verification cost. Do not redefine general test-layer ratios, CI policy, or release-gate policy here.
- Use the project's established JavaScript/TypeScript runner and configuration (`bun test`, Vitest, Jest, or equivalent). Do not introduce a second runner without a concrete project need; for a new Node.js project with no settled runner, prefer Vitest.
- Use runner-native assertions, fixtures/hooks, fake timers, tags/filters, structured failure output, and shared helpers instead of shell-scripted pass/fail counting when the behavior can be expressed in the test runner.
- Test naming and placement follow the owning project's configured discovery rules. When no convention exists, use `*.test.ts` / `*.test.js` for ordinary tests and explicit `.integration.` / `.e2e.` markers for higher layers that need separate selection.
- Keep unit and integration setup separate when their dependency boundaries or fixtures would interfere; do not force a directory layout merely to encode the layer.

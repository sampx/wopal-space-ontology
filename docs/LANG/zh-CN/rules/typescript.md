---
trigger: model_decision
description: Nodejs 类项目开发 Typescript 或 Javascript 时遵守此规则。包含编码规范与 JavaScript/TypeScript 测试运行器约定。
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

# TypeScript 开发规范

## 代码风格

- 格式化由项目 prettier 配置负责,风格值(引号、分号、缩进、行宽)以项目配置为准,不写死
- 不使用 ESLint/Prettier 以外的风格强制工具,避免规则与工具配置冲突

## 命名约定

- 变量和函数:camelCase
- 类和接口:PascalCase
- 常量:UPPER_SNAKE_CASE
- 私有成员:#privateField 或 _privateField

## 类型定义

- 为所有函数参数和返回值指定类型
- 使用接口定义对象类型
- 使用类型别名处理复杂类型
- 优先使用 `interface` 而非 `type`,除非需要联合类型或映射类型

## 模块导入

- 使用 ES6 import/export
- 按顺序分组:Node.js 内置, 第三方库, 本地模块
- 使用命名导入而非默认导入

## 异步操作

- 使用 async/await 而非 Promise 链
- 正确处理错误(try/catch)
- 避免使用 `any` 类型

## 代码组织

- 每个文件只导出一个主要功能
- 相关功能放在同一目录
- 使用 index.ts 导出公共 API

## 测试

- 测试价值、分层、确定性、隔离、异步同步、flaky 修复和验证成本统一遵循 `testing.md` 通用规则；本节不再定义固定测试比例、通用 CI 策略或发布门禁策略。
- 使用项目已经采用的 JavaScript/TypeScript 测试运行器和配置（`bun test`、Vitest、Jest 或等价方案）；没有具体项目需要时不要引入第二套 runner。新建且尚无既定 runner 的 Node.js 项目优先 Vitest。
- 能用测试框架原生能力表达的行为，使用 runner 自带的结构化断言、fixture/hook、fake timer、tag/filter、失败 diff 和共享 helper，不用 shell 脚本手写通过/失败计数。
- 测试命名与存放遵循所属项目实际的 discovery 配置。项目没有约定时，普通测试可用 `*.test.ts` / `*.test.js`，需要独立筛选的高层测试使用明确的 `.integration.` / `.e2e.` 标记。
- 当 Unit 与 Integration 的依赖边界或 fixture 会互相干扰时拆分 setup/文件；不要仅为了表达测试层级而强制额外目录结构。

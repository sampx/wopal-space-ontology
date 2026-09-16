# BUSINESS_RULES 参考 — 业务规则编写

创建或更新项目级 `BUSINESS_RULES.md`：产品业务规则的唯一真相源。模板：`templates/business-rules.md`。

## 业务规则是什么

业务规则是稳定、可测试的领域约束，独立于实现细节而成立。需求说"要做什么"；规则说"如何正确地计算它"。

**业务规则**："密码必须至少 6 个字符"。**技术规则**："用 bcryptjs 哈希密码"。技术规则属于 `AGENTS.md`。

不是业务规则的内容：

- 编码约定、命名约定、缩进风格。
- 架构约束与技术栈选择。
- 测试隔离策略与 CI/CD 配置。
- 日志格式与错误处理模式。

## 文档范围

`BUSINESS_RULES.md` 位于 `projects/<project-name>/docs/BUSINESS_RULES.md`——每项目一份。它是**伴随文档**，不是子设计：它不分解主 DESIGN 章节，因此不携带 `Parent` 链接，并在主设计的 `Companion Documents` 字段中声明。

## 头部

```
# Business Rules — <Product Name>

> **Status**: Active
> **Updated**: YYYY-MM-DD
> **Companion**: `./DESIGN.md`（业务规则所属的设计文档集）
> **Scope**: 业务规则的单一真相源。技术规则归 `<AGENTS.md 路径>`。
```

`Status` 与 `Updated` 遵循通用文档规则。`Companion` 命名本文件所属的设计文档集——该字段声明成员关系，而非父子谱系，这正是伴随文档用它而非 `Parent` 的原因。

## 正文格式

规则在 `##` 标题下按领域分组。每条规则是 `BR-NNN Rule Name \`status\`` 形式的 `###` 标题，后跟 1-3 行业务语言描述。

```markdown
## <Domain>

### BR-001 <Rule Name> `active`
<1-3 line rule description, in business language. Not bound to code paths.>

### BR-002 <Rule Name> `planned`
<same as above>
```

硬性要求：

- 每条规则一个 `###` 标题，格式为 `BR-NNN Rule Name \`status\``。
- 状态值：`active`（已实现）、`planned`（设计中）、`deprecated`（已退役）。
- 描述 1-3 行，业务语言，不绑定代码路径。
- 编号跨领域连续、全局递增；退役数字绝不回收。
- 领域信息存在于 `##` 标题分组中，绝不编码进 BR 标识。

标题保持英文（通用语言规则）；规则名与描述跟随文档语言。

## 创建文档

1. 确认目标项目并阅读其 `DESIGN.md`、数据模型文档与服务层代码。绝不编造规则。
2. 提取候选规则：哪些约束必须成立，哪些判断可以独立测试？
3. 原子化——一条规则承载一个约束。合并重复，拆分复合规则。
4. 去技术化——移除函数名与文件路径等实现细节，保留业务语义。
5. 标记状态：代码中已实现 → `active`；仅在文档中描述 → `planned`。
6. 按领域分组并按模板写文档。

### 来源优先级

| 优先级 | 来源 | 提取策略 |
|---|---|---|
| 1 | `PRD.md` / `DESIGN.md` | 从系统定位与功能约束提取原子规则 |
| 2 | 数据模型文档 | 从字段约束、关系规则与状态机提取 |
| 3 | 服务层代码 | 从常量、分支条件与守卫条件反推 |
| 4 | 共享常量 | 从枚举定义与注释提取 |

### 常见代码模式

| 代码模式 | 对应业务规则 |
|---|---|
| 常量 `MAX_*`、`LIMIT_*` | 数值上限约束 |
| `if (status === "completed") return error` | 状态机转换约束 |
| `role >= ROLE.ADMIN` | 权限判断规则 |
| `score >= 6 ? correct : incorrect` | 评分阈值规则 |
| `.split(/[、，]/)` | 数据格式或拆分规则 |

## 更新文档

1. 刷新 `Updated`。
2. 在其领域下以下一个空闲编号添加新规则，始终在全局序列末尾。
3. 业务语义变化时就地修订规则描述；保留其编号。
4. 退役规则通过标记为 `deprecated` 而非删除——编号保持保留，引用它的代码注释保持可解析。
5. 实现存在后把 `planned` 规则提升为 `active`，并验证描述仍与代码行为匹配。
6. 复查文档集：由 DESIGN 变更驱动的规则变化意味着 DESIGN 是那次变更的源头，因此确认两者仍一致。

## 代码引用约定

用 `@BR-NNN` 注释在代码中标记规则引用：

```typescript
// @BR-003 评级升降判定
if (correctCount >= thresholdUp) {
  newLevel = Math.min(currentLevel + 1, 8);
}
```

- 注释放在规则生效的代码块上方。
- 每条引用一条注释。
- 只标记核心规则；辅助代码保持不加注释。

## 质量清单

- [ ] 头部使用 `Companion`，而非 `Parent`
- [ ] `Updated` 日期是当前
- [ ] 每条规则一个 `###` 标题，形式为 `BR-NNN Rule Name \`status\``
- [ ] 每个状态是 `active` / `planned` / `deprecated` 之一
- [ ] 编号全局连续；无编号被重用
- [ ] 描述是 1-3 行业务语言，无代码路径与函数名
- [ ] 领域以 `##` 组表达，绝不嵌入 BR 标识
- [ ] 标题为英文；正文跟随文档语言
- [ ] 技术规则在 `AGENTS.md`，不在此处

## 末尾章节

文档以 `## Reference Documents` 章节收尾，承载仅参考材料——通常是被技术规则归属的 `AGENTS.md`，以及提取规则所依据的设计文档。头部链接与末尾链接保持不相交。
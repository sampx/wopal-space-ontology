---
description: Extract business rules to BUSINESS_RULES.md
---

# /wopal:extract-br

Input: `$ARGUMENTS` (product name, e.g. `gesp`, `wopal-cli`)

## Execution

1. **Confirm argument**: if `$ARGUMENTS` is empty or ambiguous, list candidate product names and ask user to confirm. Do not infer.
2. **Load spec**: must read and follow: @.wopal/rules/business-rules.md
3. **Extract rules per spec**, output to `projects/{project-name}/docs/BUSINESS_RULES.md`
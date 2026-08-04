# 故障与高级流程

## 错误处理

| 错误 | 处理 |
|------|------|
| `Invalid transition` | 回到正确状态顺序执行 |
| `Plan not found` | 先运行 `plan` |
| `check-doc failed` | 修好 Plan 再 `approve` |
| `Done completion failed` | 勾选所有 Task Done checkbox |
| `Agent Verification failed` | 补齐 Agent Verification checkbox |
| `dirty workspace` | 清理/提交 或使用 worktree 隔离 |
| `PR not merged yet` | 等 merge 后再 `verify --confirm` |
| `User Validation gate failed` | 让用户完成验证并勾选最终 checkbox |
| `Feature branch not yet merged`（squash 后仍报错） | 确认合并方式：tree 相等判据已自动识别 squash/ff/--no-ff。若仍报错,检查 Plan `Verification Commit` 字段是否残留旧 SHA(错误 fill 或 stale),删掉该字段后重试 |

## 边缘场景

1. 已有 Plan 再次 `plan` — 不重复创建，继续推进
2. `complete` 时 Done 未勾选 — 先勾选再 complete
3. `complete` 时 Agent Verification 未完成 — 先补齐
4. rook BLOCK 后 complete — 停止，修复后重新审查
5. rook 连续 3 轮 BLOCK/REVISE — 保留分歧注释，用户裁决
6. PR 未 merge 时 `verify --confirm` — 等 merge
7. 目标项目工作区不干净 — 清理或使用 worktree 隔离
8. 参数选择：Issue 驱动传 issue number，无 Issue 传 plan-name
9. **squash 合并后 verify 通过** — 默认支持。squash 的 feature tip 不是 main
   祖先，但 tree 相等判据（L2）会识别已合并。合并后 feature 分支保留到
   archive 才删除，verify 期间不要手动删分支
10. **实施基线可追溯** — approve 记录 `Base Commit`（集成分支 HEAD），
    verify 记录 `Final Commit`（合入后 HEAD）。两字段对照可确定 feature
    影响范围，revert 时用 `git diff Base..Final` 查看完整变更

## PR 工作流（可选）

默认不走 PR。仅当仓库要求 PR 合并或需要 CI/branch protection 时使用：

```text
complete --pr → PR opened → PR merged → verify --confirm → archive
```

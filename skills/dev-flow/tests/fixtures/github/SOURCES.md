# GitHub fixture provenance

| Fixture | Recorded from |
|---------|---------------|
| `pr-merged-recorded.json` | `gh pr list --repo wopal-cn/wopal-cli --state all --limit 3 --json number,url,state` on 2026-10-07; pruned to the merged PR row actually needed by the tests |
| `issue-list-open.json` | Recorded `gh issue list` output for `sampx/wopal-space` (open issues, full label metadata) |
| `issue-list-empty.json` | Recorded `gh issue list` output for an empty result set |

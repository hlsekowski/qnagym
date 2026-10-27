# Exceptions Log

Record of approved exceptions to MUST rules.

| Date | Rule | Justification | Owner | Expiry | Status |
|---|---|---|---|---|---|
| | | | | | |

## Exception Process

For **MUST** rules only:
1. Open issue with `exception` label.
2. Document: rule ID, justification, owner, expiry date.
3. Approval from maintainer required.
4. Record in this file.

## Hotfix Path

For urgent production fixes that bypass CI:
1. Create `hotfix/` branch from `main`.
2. Apply minimal fix with tests.
3. Get maintainer approval (documented in PR).
4. Merge with `--no-ff` to preserve history.
5. Run full CI post-merge; if failures, revert immediately.
6. Document exception in this file.

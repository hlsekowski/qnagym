# ADR 0004 Implementation Specification

> **Purpose:** Translates ADR 0004 architectural invariants into implementable contracts and testable acceptance criteria for all 12 follow-up items.
> **Read when:** implementing worker/task execution, claims, safe effects, observation, or any runtime behavior governed by ADR 0004.
> **Owns:** the implementation contracts for ADR 0004 follow-up items 1–12.

## Source

- [ADR 0004: Worker and Task Execution Model](../adr/0004-worker-task-model.md) — Accepted
- [ADR 0003: Local AI-Driven Development Workflow](../adr/0003-local-development-workflow.md) — Accepted

## 1. Task kinds for each process

| Kind | Process | Scope | Inputs | Outcomes | Effects | Prerequisites | Coalescing | Class | Max duration | Retry limit | Identity format |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `issue_evaluation` | Issue | Evaluate one issue revision against clarity/consistency criteria | Issue description, revision hash | Pass / Fail / Ambiguous / Inconsistent | None (decision record only) | Issue exists, not reopened, not exception | One per issue+revision | short | 300s | 3 | `issue_evaluation|<work_item>|<target>|<revision>|<generation>` |
| `sdd_cycle` | SDD | Run one SDD cycle: spec, tests, code, verify, push | Sealed issue, branch name | Completed / Failed | Branch push, PR creation | Issue accepted and sealed, branch created | One per work item | long | 3600s | 3 | `sdd_cycle|<work_item>|<target>|<revision>|<generation>` |
| `feedback_evaluation` | PR | Evaluate PR feedback item against accepted requirements | Feedback body, author, surface | ClearActionable / Ambiguous / ScopeChange / Conflict / NoAction | None (decision record only) | PR exists, feedback exists | One per feedback event | short | 300s | 3 | `feedback_evaluation|<work_item>|<target>|<revision>|<generation>` |
| `check_result_handling` | PR | Process one PR check result | Check name, status, conclusion | Pass / Fail / InfrastructureFailed | None (correction task may be enqueued) | PR exists, check run exists | One per check run | short | 300s | 3 | `check_result_handling|<work_item>|<target>|<revision>|<generation>` |
| `post_merge_completion` | PR | Post-merge: close issue, finalize | Merged PR, linked issue | Completed / Failed | Issue closure comment | PR merged | One per PR | short | 300s | 3 | `post_merge_completion|<work_item>|<target>|<revision>|<generation>` |
| `observation` | Repository | Read GitHub, create tasks, advance watermark | GitHub issues, comments, check runs | Tasks created | Task creation (via queue) | None (repository-scoped) | One at a time | short | 300s | 3 | `observation|<repository>|<target>|<revision>|<generation>` |

**Identity format:** `kind|work_item|target|revision|generation` where `work_item` is the issue number (or empty for repository-scoped tasks), `target` is the branch/PR/target identifier, `revision` is the input revision hash or comment ID, and `generation` defaults to 0.

**Coalescing policy:** Inputs for the same work item that arrive before a task starts produce one task per kind, evaluating the latest state. All unprocessed event identifiers are preserved.

## 2. Execution state

### Schema

Execution state is a JSON document persisted per named state file:

| Field | Type | Description |
|---|---|---|
| `tasks` | `dict[str, Task]` | Logical task identities and lifecycle states, keyed by task identity string |
| `attempts` | `dict[str, list[ExecutionAttempt]]` | Execution attempt counters and retry deadlines per task |
| `claims` | `dict[str, Claim]` | Claim ownership, expiry, and fencing generations per task key |
| `observation_watermark` | `float` | Unix epoch seconds; only fully processed events |
| `processed_event_ids` | `set[str]` | Deduplication keys for observed GitHub events |
| `generation_counter` | `int` | Monotonically increasing counter for explicit retry requests |
| `correction_attempts` | `dict[str, int]` | Correction-attempt accounting per work item |
| `effects` | `dict[str, dict]` | Effect intent and outcome records keyed by effect ID |

### Content

Each `Task` record includes: identity, created_time, not_before_time, event_time, state, priority, max_duration, retry_limit, attempt_count.

Each `ExecutionAttempt` record includes: attempt_number, outcome, retry_deadline, claim_id.

Each `Claim` record includes: task_identity, worker_id, expiry_time, fencing_generation.

### Location

Execution state files live in `data/execution_state/` (configurable via `QNAGYM_DATA_DIR`). One JSON file per named state.

### Durability

- Atomic write: temp file + `os.replace` (rename) for crash safety
- File permissions: `0o600`
- Corruption detection: `is_corrupt()` returns True for invalid JSON or missing required fields
- Load failure raises `ExecutionStateServiceError`

### Shared access

Execution state is file-based and shared by all workers on the same machine. Cross-machine sharing requires a separate decision (ADR 0004 §9 deployment neutrality).

### Backup/recovery

No automatic backup. Corrupt state causes fail-closed behavior: workers must not produce effects based on guessed state.

### Handling of state loss

If execution state is lost, corrupt, or unavailable, workers fail closed. Recovery must restore or verify required state before effects resume.

### Alignment with ADR 0003

Execution state stores decision records and input revisions (ADR 0003 follow-up item 1) and sealed requirement baselines with fingerprints (ADR 0003 follow-up item 2).

## 3. Claims

### Atomic acquisition

Claim acquisition is atomic: `claim_task()` checks for an existing non-expired claim and raises `ValueError` if one exists. Two workers cannot acquire valid claims for the same task or concurrent tasks of the same work item.

### Claim fields

| Field | Type | Description |
|---|---|---|
| `task_identity` | `TaskIdentity` | The task being claimed |
| `worker_id` | `str` | The worker claiming the task |
| `expiry_time` | `float` | Unix epoch seconds; claim expires at this time |
| `fencing_generation` | `int` | Monotonically increasing; incremented on each new claim for the same task |

### Expiry

A claim is expired when `now >= expiry_time`. Expired claims permit takeover by another worker after ownership checks.

### Renewal

`renew_claim()` updates `expiry_time` while preserving `fencing_generation`. Only the owning worker can renew.

### Fencing generations

Each new claim for a task increments `fencing_generation`. A worker must present the current fencing generation before producing an effect; stale generations are rejected.

### Takeover

Takeover is permitted after claim expiry. `take_over_after_expiry()` returns True only when the existing claim is expired.

### Clock assumptions

All times are Unix epoch seconds, UTC. Clock skew between workers on different machines is not handled; single-machine deployment is assumed.

### Multiple workers

At most one task per work item runs at a time. Claims enforce this. Multiple workers on one or several machines must share durable execution state (separate decision required for multi-machine).

## 4. Safe effects

### Effect identifiers

Each effect has a stable identifier derived from the task identity and effect step: `effect_id = f"{task_key}:{effect_step}"`.

### Durable intent/outcome records

Before dispatching an effect, `record_intent()` persists:
- `task_identity_key`: key of the producing task
- `effect_step`: the step name (e.g. "post_comment", "push_and_open_pr")
- `body`: the payload to dispatch
- `outcome`: initially `None`

After dispatch, `record_outcome()` sets the outcome string.

### Reconciliation

If a machine stops or a response is lost after an effect may have succeeded, the implementation reconciles external state using the effect identifier before retrying. If the outcome cannot be established, report uncertainty rather than blindly repeat.

### Duplicate prevention

`dispatch_if_needed()` returns `None` without re-dispatching when an effect ID already has a recorded outcome. Replaying the same effect ID does not open a second PR or post a duplicate comment.

### Behavior when outcome uncertain

Report uncertainty rather than blindly repeat a potentially non-idempotent effect.

## 5. Observation

### Interval

Configuration value (seconds). Default: 300s (5 minutes).

### Enumeration and pagination

GitHub list endpoints are paginated with `per_page=100`. All pages are fetched until a page returns fewer than `per_page` items.

### Change detection

Events since the observation watermark are detected using the `since` parameter on GitHub list APIs. Processed event IDs are tracked in `processed_event_ids` for deduplication.

### Watermarks

The observation watermark is advanced only after every event up to that watermark has a corresponding task or durable outcome recorded. Watermark advancement and task creation are saved atomically.

### GitHub request budget

Observation frequency is constrained by GitHub rate limits. Unauthorized (401), rate-limit (429), and server errors (5xx) are classified as `InfrastructureFailure`, not development failures.

### Retry exhaustion

If an observation task exhausts its retries, its terminal-failure transition durably creates the successor observation task together with the terminal failure record.

### Unauthorized or workflow-marked content

Workflow-authored comments (starting with `WORKFLOW_COMMENT_MARKER`) are marked as processed but not treated as input (rule D8). Unauthorized responses are infrastructure failures.

## 6. Withdrawal checks

| Check | Condition | GitHub state required |
|---|---|---|
| Issue closed before PR | Work item withdrawn | Issue state = closed, no PR exists |
| Branch deleted | Tasks depending on branch withdrawn | Branch ref no longer exists |
| PR closed without merge | Tasks targeting that PR withdrawn | PR state = closed, not merged |
| Merged PR | All tasks targeting PR withdrawn except post-merge | PR state = merged |
| Issue closed while PR open | Not withdrawal | Issue closed, PR still open |

Withdrawal is evaluated before every externally visible effect. If withdrawal is detected before any effect, the task ends as `Obsolete` without effects. If some effects completed, the task stops, records partial outcome, ends as `Obsolete`.

## 7. Workspace isolation

### Isolation

Each task runs in a temporary, disposable working directory (`tempfile.mkdtemp(prefix="qnagym-workspace-")`). Concurrent tasks of different work items operate without interference.

### Branch naming

Branches follow the workflow.md convention: `<type>/<short-description>` where type is `feat`, `fix`, `chore`, or `docs`.

### Fast-forward sync

`git merge --ff-only <base_branch>` is used to sync. If the merge would conflict, `GitWorkspaceConflict` is raised and the conflict is recorded, not resolved.

### No push

The workspace service does not push. Push is a separate safe effect (issue #157).

## 8. Infrastructure failure classification

| Status | Classification | Consumes correction attempt |
|---|---|---|
| `Passing` | Non-failure | No |
| `Pending` | Non-failure | No |
| `Running` | Non-failure | No |
| `Cancelled` | Non-failure | No |
| `Skipped` | Non-failure | No |
| `InfrastructureFailed` | Non-failure | No |
| `Failed` | Development failure | Yes |

### Retry limits and spacing

Infrastructure retries are execution retries (not correction attempts). They are spaced by `not_before_time` and limited by `retry_limit` per task kind.

### Notification delivery

Notification delivery follows safe-effect and retry rules. Failure to deliver does not cause the original task to re-execute.

## 9. Attempt accounting

### Execution retries vs correction attempts

Execution retries (infrastructure failures) are not counted against `MAX_CORRECTION_ATTEMPTS_PER_BATCH`. Correction attempts (ADR 0003 §7) are tracked separately in `CorrectionBatch`.

### Correction batch

| Field | Default | Description |
|---|---|---|
| `limit` | `MAX_CORRECTION_ATTEMPTS_PER_BATCH` (5) | Maximum attempts per batch |
| `attempts_used` | 0 | Attempts consumed in this batch |
| `history` | `[]` | Descriptions of completed attempts |
| `current_step` | `None` | Active correction step |
| `feedback_queued` | `[]` | Feedback received during active/exhausted batch |

### Attempt counting rules

- An attempt counts when completed, not when started
- An attempt reaching `LocalVerification` counts even if `Push` never happens
- Only one attempt may be active at a time
- Starting a new attempt while one is active abandons the previous without counting it
- Feedback never resets the attempt counter and is never discarded
- A new batch starts only on an explicit retry request; reopening the PR does not reset the counter

### Explicit retry interaction

`start_new_batch()` resets `attempts_used` to 0 while preserving history. This is invoked only on an explicit retry request from the user.

## 10. Merge conflicts

### Detection

`git merge --ff-only` returns non-zero when a fast-forward is not possible. This is detected as `GitWorkspaceConflict`.

### Reporting

The conflict is recorded (logged, saved to execution state) and the worker stops. The conflict is not resolved automatically.

### Interim assumption

The user resolves merge conflicts manually. No automated merge conflict resolution is implemented.

## 11. Observability

### Structured logs

Logs at I/O boundaries identify: task, worker, work item, target, execution attempt, and input revision where applicable. PII is redacted per security and privacy rules.

### Trace ID

A trace ID per task links it to the task that created it.

### Metrics

| Metric | Description |
|---|---|
| Queue wait time | Time a task spends in Queued before being claimed |
| Execution duration | Time from claim to outcome for each task |
| Outcome per task kind | Distribution of Completed/Failed/Obsolete per kind |
| Task creations suppressed by identity | Count of deduplicated/coalesced task creations |

Queue wait time is a metric, not a task timeout.

## 12. Acceptance scenarios

All scenarios verified with stub tasks that call no model:

| Scenario | Invariant | Test |
|---|---|---|
| One running task per work item | At most one valid claim per work item | Claim conflict returns None |
| Claim expiry and takeover | Expired claims permit takeover | Takeover after expiry succeeds |
| Stale-worker fencing | Stale fencing generations rejected | `is_claim_valid()` returns False |
| Restart recovery | State survives process restart | Load from file after save |
| Deduplication | Same event processed once | `processed_event_ids` prevents duplicates |
| Coalescing | One task per kind per work item | Multiple inputs → one task |
| Event preservation | All unprocessed event IDs preserved | `processed_event_ids` retains all |
| Effect reconciliation | Replay does not duplicate effects | `dispatch_if_needed()` returns None on replay |
| Workspace isolation | Concurrent tasks don't interfere | Separate temp directories |
| Obsolete tasks | Withdrawn work items end as Obsolete | Withdrawal check before effects |

## Files touched

| File | Purpose |
|---|---|
| `src/qnagym/contracts/task_model.py` | Task, TaskIdentity, ExecutionAttempt, Claim, ExecutionState data shapes |
| `src/qnagym/contracts/constants.py` | Task kinds, states, priorities, correction batch config |
| `src/qnagym/domain/task_queue.py` | Task creation, eligibility, ordering, claiming, coalescing |
| `src/qnagym/domain/execution_state.py` | Serialization, validation, corruption detection, merging |
| `src/qnagym/services/execution_state.py` | Atomic file persistence |
| `src/qnagym/services/task_runner.py` | Single task execution: claim, run, record, save |
| `src/qnagym/services/task_queue.py` | Task queue orchestration |
| `src/qnagym/services/github_observation.py` | Read-only GitHub observation |
| `src/qnagym/services/effect_log.py` | Safe effect intent/outcome logging |
| `src/qnagym/services/pr_creation.py` | Push + open PR as safe effect |
| `src/qnagym/services/git_workspace.py` | Isolated git workspace |
| `src/qnagym/services/pr_check_observation.py` | PR check result observation |
| `src/qnagym/services/issue_evaluation.py` | Issue evaluation task |
| `src/qnagym/domain/pr_checks.py` | Check classification and correction batch |
| `src/qnagym/services/pr_checks.py` | PR check monitoring service |

## Test plan

Each follow-up item has corresponding unit tests:

1. Task kinds: `tests/unit/services/test_task_queue_service.py` — task creation, coalescing, duplicate prevention
2. Execution state: `tests/unit/domain/test_execution_state.py`, `tests/unit/services/test_execution_state_service.py` — serialization, atomic write, corruption detection
3. Claims: `tests/unit/services/test_task_runner.py` — claim conflict, expiry, takeover, fencing
4. Safe effects: `tests/unit/services/test_effect_log.py`, `tests/unit/services/test_pr_creation.py` — intent/outcome, idempotent dispatch
5. Observation: `tests/unit/services/test_github_observation.py`, `tests/unit/services/test_pr_check_observation.py` — pagination, watermark, deduplication, infrastructure failure
6. Withdrawal: `tests/unit/domain/test_flow.py` — withdrawal checks before effects
7. Workspace: `tests/unit/services/test_git_workspace.py` — branch naming, fast-forward, conflict detection
8. Infrastructure failure: `tests/unit/services/test_pr_check_observation.py` — cancelled/skipped/infrastructure-failed don't consume attempts
9. Attempt accounting: `tests/unit/services/test_pr_checks.py` — correction batch counting, retry interaction
10. Merge conflicts: `tests/unit/services/test_git_workspace.py` — conflict detection and reporting
11. Observability: structured logs and metrics verified by code review
12. Acceptance scenarios: all above tests run with stub tasks, no model calls

## Review status

**Pending owner review.** This specification document must be reviewed and approved by the project owner before implementation issues referencing it are considered complete.

## Related

- [ADR 0004: Worker and Task Execution Model](../adr/0004-worker-task-model.md)
- [ADR 0003: Local AI-Driven Development Workflow](../adr/0003-local-development-workflow.md)
- [ADR 0006: PR Process](../adr/0006-pr-process.md)
- [Project constitution](../constitution.md)
- [Rule catalog](../rules.md)

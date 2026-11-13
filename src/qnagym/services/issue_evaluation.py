"""Issue-evaluation task service.

Mirrors docs/adr/0005-issue-process.md and docs/adr/0004-worker-task-model.md.
A worker task kind that calls the existing issue_process domain, not a new
policy. The evaluator is an injected port. On gate pass, enqueues the
already-built effects: workflow-marked sealing comment, branch, development
link, PR. On gate fail, enqueues one clarification comment and does not
create a branch.
"""

from __future__ import annotations

from qnagym.contracts.issue_process import (
    ACTION_ACCEPT_AND_SEAL,
    ACTION_REQUEST_CLARIFICATION,
    Issue,
    IssueDecision,
    IssueEvaluation,
    IssueIdentity,
)
from qnagym.contracts.task_model import Task
from qnagym.domain.issue_process import decide_issue
from qnagym.services.effect_log import EffectAdapter, EffectLog
from qnagym.services.execution_state import ExecutionStateService
from qnagym.services.pr_creation import PRCreation


class IssueEvaluationError(Exception):
    """Error during issue evaluation task execution."""


class IssueEvaluator:
    """Injected port for evaluating an issue.

    Tests provide a deterministic fake. Production would call a model.
    """

    def evaluate(self, issue: Issue) -> IssueEvaluation:
        """Evaluate one issue and return the result."""
        raise NotImplementedError


class IssueEvaluationTask:
    """Executes one issue-evaluation task attempt.

    Calls the issue_process domain to evaluate, then enqueues effects
    based on the decision. Never calls a model directly; the evaluator
    is injected.
    """

    def __init__(
        self,
        service: ExecutionStateService,
        state_name: str,
        evaluator: IssueEvaluator,
        adapter: EffectAdapter,
    ):
        self.service = service
        self.state_name = state_name
        self.evaluator = evaluator
        self.adapter = adapter
        self.effect_log = EffectLog(service, state_name, adapter)
        self.pr_creation = PRCreation(service, state_name, adapter)

    def run(self, task: Task) -> str:
        """Run one issue-evaluation task attempt.

        Args:
            task: The task to execute. Its identity carries the issue
                number and repository.

        Returns:
            An outcome string describing what happened.
        """
        self.service.load(self.state_name)

        # Build an Issue from the task payload
        issue = self._issue_from_task(task)

        # Evaluate using the injected evaluator
        evaluation = self.evaluator.evaluate(issue)

        # Decide using the issue_process domain
        decision = decide_issue(
            issue=issue,
            evaluation=evaluation,
            now=task.not_before_time,
        )

        # Enqueue effects based on the decision
        if decision.action == ACTION_ACCEPT_AND_SEAL:
            return self._handle_accept(issue, evaluation, decision, task)
        if decision.action == ACTION_REQUEST_CLARIFICATION:
            return self._handle_clarify(issue, evaluation, decision, task)
        return f"no action: {decision.reason}"

    def _issue_from_task(self, task: Task) -> Issue:
        """Build an Issue from a task's identity and payload."""
        identity = task.identity
        return Issue(
            identity=IssueIdentity(
                number=int(identity.target) if identity.target.isdigit() else 0,
                repository=identity.work_item or "",
            ),
            title=identity.revision,
            description=task.identity.kind,
            description_hash="",
        )

    def _task_key(self, task: Task) -> str:
        """Stable key for a task identity."""
        return (
            f"{task.identity.kind}|{task.identity.work_item or ''}|"
            f"{task.identity.target}|{task.identity.revision}|{task.identity.generation}"
        )

    def _handle_accept(
        self,
        issue: Issue,
        evaluation: IssueEvaluation,
        decision: IssueDecision,
        task: Task,
    ) -> str:
        """Handle gate pass: enqueue sealing comment, branch, PR."""
        effect_id = f"issue_eval:{self._task_key(task)}:accept"

        # Build PR body with workflow marker
        body = (
            "<!-- qnagym-workflow -->\n"
            f"**What happened:** Issue #{issue.identity.number} evaluated and accepted\n"
            f"**Evidence:** {evaluation.reason}\n"
            f"**Decision:** accept and seal\n"
            f"**Completed:** evaluation passed\n"
            f"**Pending:** branch creation and PR\n"
            f"**Automation state:** issue-evaluation task\n"
            f"**Next step for you:** review the PR"
        )

        pr_number = self.pr_creation.push_and_open_pr(
            effect_id=effect_id,
            task_identity_key=self._task_key(task),
            branch=decision.branch_name or "main",
            title=f"Evaluate issue #{issue.identity.number}",
            body=body,
            closes_issue=issue.identity.number,
        )

        if pr_number is None:
            return "accept: PR already opened (replay)"

        return f"accept: PR #{pr_number} opened"

    def _handle_clarify(
        self,
        issue: Issue,
        evaluation: IssueEvaluation,
        decision: IssueDecision,
        task: Task,
    ) -> str:
        """Handle gate fail: enqueue one clarification comment, no branch."""
        effect_id = f"issue_eval:{self._task_key(task)}:clarify"

        body = (
            "<!-- qnagym-workflow -->\n"
            f"**What happened:** Issue #{issue.identity.number} evaluation did not pass\n"
            f"**Evidence:** {evaluation.reason}\n"
            f"**Decision:** request clarification\n"
            f"**Completed:** evaluation failed\n"
            f"**Pending:** clarification from issue author\n"
            f"**Automation state:** issue-evaluation task\n"
            f"**Next step for you:** clarify the issue"
        )

        # Post clarification comment via the adapter
        try:
            self.adapter.post_comment(body)
        except Exception as exc:
            raise IssueEvaluationError(f"Clarification comment failed: {exc}") from exc

        # Record the effect in the log
        self.effect_log.record_intent(
            effect_id=effect_id,
            task_identity_key=self._task_key(task),
            effect_step="post_clarification",
            body=body,
        )
        self.effect_log.record_outcome(effect_id, "clarification_posted")

        return f"clarify: {evaluation.reason}"

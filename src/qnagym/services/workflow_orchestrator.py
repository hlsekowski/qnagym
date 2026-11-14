"""Workflow orchestrator service.

Mirrors docs/adr/0003-local-development-workflow.md and
docs/adr/0004-worker-task-model.md. Connects the Issue → SDD → PR
vertical slice: discovers eligible issues, creates and claims tasks,
runs the issue-evaluation task, and reports results. Uses stubs for
external systems (GitHub, model) in tests.
"""

from __future__ import annotations

from qnagym.contracts.task_model import (
    TASK_KIND_ISSUE_EVALUATION,
    ExecutionState,
)
from qnagym.services.effect_log import EffectAdapter
from qnagym.services.execution_state import ExecutionStateService
from qnagym.services.issue_evaluation import (
    IssueEvaluationTask,
    IssueEvaluator,
)
from qnagym.services.task_queue import create_task
from qnagym.services.task_runner import run_once


class WorkflowOrchestratorError(Exception):
    """Error during workflow orchestration."""


class WorkflowOrchestrator:
    """Single-worker end-to-end Issue → SDD → PR execution.

    Orchestrates the smallest meaningful vertical slice:
    1. Discover eligible GitHub issues (via injected observation port)
    2. Create and claim tasks
    3. Run the issue-evaluation task
    4. Report results

    Uses stubs for external systems in tests.
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
        self.issue_evaluation = IssueEvaluationTask(
            service=service,
            state_name=state_name,
            evaluator=evaluator,
            adapter=adapter,
        )

    def discover_and_evaluate(
        self,
        issue_number: int,
        repository: str,
        title: str,
        description: str,
        now: float,
    ) -> str:
        """Discover an issue, create a task, claim it, and evaluate.

        Args:
            issue_number: The GitHub issue number.
            repository: The repository name.
            title: The issue title.
            description: The issue description.
            now: Current time as Unix epoch seconds.

        Returns:
            An outcome string describing what happened.
        """
        state = self.service.load(self.state_name)

        # Create a task for issue evaluation
        task, skip_reason = create_task(
            state,
            kind=TASK_KIND_ISSUE_EVALUATION,
            work_item=str(issue_number),
            target=str(issue_number),
            revision=title,
            created_time=now,
            not_before_time=now,
            event_time=now,
        )

        if skip_reason:
            return f"skipped: {skip_reason}"

        # Save state with the new task
        self.service.save(self.state_name, state)

        # Run the task via the task runner
        result_task, outcome = run_once(
            self.service,
            self.state_name,
            worker_id="worker-1",
            expiry_time=now + 300.0,
            run_task=self.issue_evaluation.run,
        )

        if result_task is None:
            return "no eligible task"

        return outcome or "completed"

    def get_state(self) -> ExecutionState:
        """Get the current execution state."""
        return self.service.load(self.state_name)

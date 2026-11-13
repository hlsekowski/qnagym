"""SDD Process contracts (pure data shapes, no logic).

Mirrors docs/adr/0007-sdd-process.md. Defines SDD task kinds, states,
inputs, results, and handoff information.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from qnagym.contracts.task_model import (
    PRIORITY_LONG,
    PRIORITY_SHORT,
)

# --- SDD task kinds (ADR 0007 follow-up item 1) ---

SDD_TASK_KIND_INITIAL_ANALYSIS = "initial_analysis"
SDD_TASK_KIND_SPEC_UPDATE = "spec_update"
SDD_TASK_KIND_CODE_CONTRACT_UPDATE = "code_contract_update"
SDD_TASK_KIND_TEST_UPDATE = "test_update"
SDD_TASK_KIND_IMPLEMENTATION = "implementation"
SDD_TASK_KIND_TRACEABILITY = "traceability"
SDD_TASK_KIND_VERIFICATION = "verification"
SDD_TASK_KIND_COMMIT_PUSH = "commit_push"

SDD_TASK_KINDS = frozenset(
    {
        SDD_TASK_KIND_INITIAL_ANALYSIS,
        SDD_TASK_KIND_SPEC_UPDATE,
        SDD_TASK_KIND_CODE_CONTRACT_UPDATE,
        SDD_TASK_KIND_TEST_UPDATE,
        SDD_TASK_KIND_IMPLEMENTATION,
        SDD_TASK_KIND_TRACEABILITY,
        SDD_TASK_KIND_VERIFICATION,
        SDD_TASK_KIND_COMMIT_PUSH,
    }
)

# --- SDD task origin types ---

SDD_TASK_ORIGIN_ISSUE = "issue"
SDD_TASK_ORIGIN_PR = "pr"

SDD_TASK_ORIGINS = frozenset({SDD_TASK_ORIGIN_ISSUE, SDD_TASK_ORIGIN_PR})

# --- Task kind -> priority class mapping (ADR 0004 §3) ---

# Short tasks: quick, non-blocking. Long tasks: may take significant time.
SDD_TASK_KIND_PRIORITY: dict[str, str] = {
    SDD_TASK_KIND_INITIAL_ANALYSIS: PRIORITY_SHORT,
    SDD_TASK_KIND_SPEC_UPDATE: PRIORITY_SHORT,
    SDD_TASK_KIND_CODE_CONTRACT_UPDATE: PRIORITY_SHORT,
    SDD_TASK_KIND_TEST_UPDATE: PRIORITY_SHORT,
    SDD_TASK_KIND_IMPLEMENTATION: PRIORITY_LONG,
    SDD_TASK_KIND_TRACEABILITY: PRIORITY_SHORT,
    SDD_TASK_KIND_VERIFICATION: PRIORITY_SHORT,
    SDD_TASK_KIND_COMMIT_PUSH: PRIORITY_SHORT,
}

# --- SDD task states ---

SDD_TASK_STATE_ANALYZING = "Analyzing"
SDD_TASK_STATE_SPECIFYING = "Specifying"
SDD_TASK_STATE_IMPLEMENTING = "Implementing"
SDD_TASK_STATE_VERIFYING = "Verifying"
SDD_TASK_STATE_DELIVERING = "Delivering"
SDD_TASK_STATE_COMPLETED = "Completed"
SDD_TASK_STATE_INCOMPLETE = "Incomplete"

SDD_TASK_STATES = frozenset(
    {
        SDD_TASK_STATE_ANALYZING,
        SDD_TASK_STATE_SPECIFYING,
        SDD_TASK_STATE_IMPLEMENTING,
        SDD_TASK_STATE_VERIFYING,
        SDD_TASK_STATE_DELIVERING,
        SDD_TASK_STATE_COMPLETED,
        SDD_TASK_STATE_INCOMPLETE,
    }
)

# Terminal states
TERMINAL_SDD_STATES = frozenset({SDD_TASK_STATE_COMPLETED, SDD_TASK_STATE_INCOMPLETE})

# --- SDD result types ---

SDD_RESULT_SUCCESSFUL = "Successful"
SDD_RESULT_INCOMPLETE = "Incomplete"

SDD_RESULTS = frozenset({SDD_RESULT_SUCCESSFUL, SDD_RESULT_INCOMPLETE})


@dataclass(frozen=True)
class SDDTaskIdentity:
    """The immutable identity of an SDD task."""

    task_id: str
    source: str  # "issue" or "pr"
    source_ref: str  # issue number or PR number

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SDDTaskIdentity:
        return cls(
            task_id=str(data["task_id"]),
            source=str(data["source"]),
            source_ref=str(data["source_ref"]),
        )


@dataclass
class SDDTaskInput:
    """Input to an SDD task (ADR 0007 §2).

    Records the accepted input revision and issue/PR feedback references
    used for traceability (ADR 0007 follow-up item 2).
    """

    source: str
    source_ref: str
    accepted_requirements: str
    accepted_input_revision: str | None = None
    branch_name: str | None = None
    issue_number: int | None = None
    pr_number: int | None = None
    feedback_reference: str | None = None
    check_evidence: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SDDTaskInput:
        return cls(
            source=str(data["source"]),
            source_ref=str(data["source_ref"]),
            accepted_requirements=str(data["accepted_requirements"]),
            accepted_input_revision=data.get("accepted_input_revision"),
            branch_name=data.get("branch_name"),
            issue_number=data.get("issue_number"),
            pr_number=data.get("pr_number"),
            feedback_reference=data.get("feedback_reference"),
            check_evidence=data.get("check_evidence"),
        )


@dataclass
class SDDTask:
    """An SDD task carrying one development change through the cycle (ADR 0007)."""

    identity: SDDTaskIdentity
    input: SDDTaskInput
    state: str = SDD_TASK_STATE_ANALYZING
    spec_changed: bool = False
    contract_changed: bool = False
    tests_updated: bool = False
    implementation_done: bool = False
    traceability_updated: bool = False
    local_verification_passed: bool = False
    pr_diff_size: int = 0
    pr_diff_limit: int = 400
    result: str | None = None
    result_evidence: str | None = None
    result_diagnostics: str | None = None
    commit_sha: str | None = None
    pr_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity": self.identity.to_dict(),
            "input": self.input.to_dict(),
            "state": self.state,
            "spec_changed": self.spec_changed,
            "contract_changed": self.contract_changed,
            "tests_updated": self.tests_updated,
            "implementation_done": self.implementation_done,
            "traceability_updated": self.traceability_updated,
            "local_verification_passed": self.local_verification_passed,
            "pr_diff_size": self.pr_diff_size,
            "pr_diff_limit": self.pr_diff_limit,
            "result": self.result,
            "result_evidence": self.result_evidence,
            "result_diagnostics": self.result_diagnostics,
            "commit_sha": self.commit_sha,
            "pr_url": self.pr_url,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SDDTask:
        return cls(
            identity=SDDTaskIdentity.from_dict(data["identity"]),
            input=SDDTaskInput.from_dict(data["input"]),
            state=str(data.get("state", SDD_TASK_STATE_ANALYZING)),
            spec_changed=bool(data.get("spec_changed", False)),
            contract_changed=bool(data.get("contract_changed", False)),
            tests_updated=bool(data.get("tests_updated", False)),
            implementation_done=bool(data.get("implementation_done", False)),
            traceability_updated=bool(data.get("traceability_updated", False)),
            local_verification_passed=bool(data.get("local_verification_passed", False)),
            pr_diff_size=int(data.get("pr_diff_size", 0)),
            pr_diff_limit=int(data.get("pr_diff_limit", 400)),
            result=data.get("result"),
            result_evidence=data.get("result_evidence"),
            result_diagnostics=data.get("result_diagnostics"),
            commit_sha=data.get("commit_sha"),
            pr_url=data.get("pr_url"),
        )

    @property
    def is_terminal(self) -> bool:
        return self.state in TERMINAL_SDD_STATES

    @property
    def is_complete(self) -> bool:
        return self.state == SDD_TASK_STATE_COMPLETED

    @property
    def is_incomplete(self) -> bool:
        return self.state == SDD_TASK_STATE_INCOMPLETE

    @property
    def pr_diff_within_limit(self) -> bool:
        return self.pr_diff_size <= self.pr_diff_limit


@dataclass
class SDDResult:
    """The result of an SDD task handed to the PR Process (ADR 0007 §7)."""

    result: str  # SDD_RESULT_SUCCESSFUL or SDD_RESULT_INCOMPLETE
    issue_number: int | None = None
    pr_number: int | None = None
    branch_name: str | None = None
    commit_sha: str | None = None
    spec_references: list[str] = field(default_factory=list)
    local_verification: str | None = None
    pr_diff_size: int = 0
    pr_diff_limit: int = 400
    evidence: str | None = None
    work_completed: str | None = None
    diagnostics: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SDDResult:
        return cls(
            result=str(data["result"]),
            issue_number=data.get("issue_number"),
            pr_number=data.get("pr_number"),
            branch_name=data.get("branch_name"),
            commit_sha=data.get("commit_sha"),
            spec_references=list(data.get("spec_references") or []),
            local_verification=data.get("local_verification"),
            pr_diff_size=int(data.get("pr_diff_size", 0)),
            pr_diff_limit=int(data.get("pr_diff_limit", 400)),
            evidence=data.get("evidence"),
            work_completed=data.get("work_completed"),
            diagnostics=data.get("diagnostics"),
        )

    @property
    def is_successful(self) -> bool:
        return self.result == SDD_RESULT_SUCCESSFUL

    @property
    def is_incomplete(self) -> bool:
        return self.result == SDD_RESULT_INCOMPLETE

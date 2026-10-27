"""Contract tests for flow."""

from qnagym.contracts.flow import (
    ALLOWED_TRANSITIONS,
    VALID_STATUSES,
    FlowError,
    VagueMaterialError,
    check_confirmed_or_drilling,
    check_drilling,
    check_drilling_or_evaluated,
    check_evaluated,
    check_no_unanswered,
    check_prepared,
    enforce_transition,
    reset_session,
    validate_transition,
)


class TestFlowContract:
    def test_allowed_transitions_defined(self):
        assert ALLOWED_TRANSITIONS["prepared"] == {"prepared", "confirmed"}
        assert ALLOWED_TRANSITIONS["confirmed"] == {"drilling"}
        assert ALLOWED_TRANSITIONS["drilling"] == {"evaluated", "confirmed", "prepared"}
        assert ALLOWED_TRANSITIONS["evaluated"] == {"confirmed", "prepared"}

    def test_valid_statuses_defined(self):
        assert {"prepared", "confirmed", "drilling", "evaluated"} == VALID_STATUSES

    def test_exceptions_defined(self):
        assert issubclass(FlowError, Exception)
        assert issubclass(VagueMaterialError, Exception)

    def test_guard_functions_defined(self):
        assert callable(check_prepared)
        assert callable(check_confirmed_or_drilling)
        assert callable(check_drilling)
        assert callable(check_evaluated)
        assert callable(check_no_unanswered)
        assert callable(check_drilling_or_evaluated)
        assert callable(enforce_transition)
        assert callable(validate_transition)
        assert callable(reset_session)

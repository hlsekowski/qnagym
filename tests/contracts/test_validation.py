"""Contract tests for validation."""

import pytest

from qnagym.contracts.constants import (
    ALLOWED_TRANSITIONS,
    FALLBACK_COUNT,
    QUESTION_COUNT_MAX,
    QUESTION_COUNT_MIN,
    VALID_STATUSES,
)
from qnagym.contracts.types import Config, Context, Progress, Question, Session
from qnagym.contracts.validation import (
    FlowError,
    build_evaluate_messages,
    build_generate_messages,
    build_material_blob,
    build_refine_messages,
    close_alternatives,
    enforce_transition,
    material_too_short,
    question_count,
    reset_session,
    should_show_confidence,
    validate_config,
    validate_context,
    validate_evaluation,
    validate_progress,
    validate_question,
    validate_session,
    validate_transition,
)


class TestMaterialValidation:
    def test_material_too_short(self):
        assert material_too_short("a" * 19) is True
        assert material_too_short("a" * 20) is False
        assert material_too_short("  a  ") is True  # whitespace trimmed

    def test_question_count_formula(self):
        assert question_count(None) == FALLBACK_COUNT
        assert question_count(0) == QUESTION_COUNT_MIN
        assert question_count(1000) == QUESTION_COUNT_MAX
        # Test specific boundaries
        assert question_count(30) == 5
        assert question_count(45) == 8
        assert question_count(90) == 15


class TestSessionValidation:
    def test_validate_session_valid(self, sample_session: Session):
        validate_session(sample_session)  # Should not raise

    def test_validate_session_missing_id(self, sample_session: Session):
        sample_session.id = ""
        with pytest.raises(ValueError, match="session id is required"):
            validate_session(sample_session)

    def test_validate_session_invalid_status(self, sample_session: Session):
        sample_session.status = "invalid"
        with pytest.raises(ValueError, match="invalid status"):
            validate_session(sample_session)

    def test_validate_session_missing_material(self, sample_session: Session):
        sample_session.material = ""
        with pytest.raises(ValueError, match="material is required"):
            validate_session(sample_session)

    def test_validate_session_question_count_mismatch(self, sample_session: Session):
        sample_session.question_count = 5
        with pytest.raises(ValueError, match="question_count"):
            validate_session(sample_session)

    def test_validate_question_valid(self):
        q = Question(id="q1", prompt="What?", agreed_answer="Answer")
        validate_question(q)

    def test_validate_question_missing_prompt(self):
        q = Question(id="q1", prompt="", agreed_answer="Answer")
        with pytest.raises(ValueError, match="prompt is required"):
            validate_question(q)

    def test_validate_question_missing_agreed_answer(self):
        q = Question(id="q1", prompt="What?", agreed_answer="")
        with pytest.raises(ValueError, match="agreed_answer is required"):
            validate_question(q)

    def test_validate_context_valid(self):
        ctx = Context(duration_minutes=30, difficulty="medium", language="en")
        validate_context(ctx)

    def test_validate_context_invalid_difficulty(self):
        ctx = Context(difficulty="invalid")
        with pytest.raises(ValueError, match="invalid difficulty"):
            validate_context(ctx)

    def test_validate_progress_valid(self):
        p = Progress(
            attempts=1, best_score=0.8, last_score=0.7, improving=True, break_suggested=False
        )
        validate_progress(p)

    def test_validate_progress_negative_attempts(self):
        p = Progress(attempts=-1)
        with pytest.raises(ValueError, match="attempts must be non-negative"):
            validate_progress(p)

    def test_validate_progress_score_out_of_range(self):
        p = Progress(best_score=1.5)
        with pytest.raises(ValueError, match="best_score must be in"):
            validate_progress(p)

    def test_validate_evaluation_valid(self):
        from qnagym.contracts.types import Evaluation

        ev = Evaluation(score=0.8, confidence=0.9, feedback="Good")
        validate_evaluation(ev)

    def test_validate_evaluation_score_out_of_range(self):
        from qnagym.contracts.types import Evaluation

        ev = Evaluation(score=1.5, confidence=0.5, feedback="Good")
        with pytest.raises(ValueError, match="score must be in"):
            validate_evaluation(ev)


class TestFlowValidation:
    def test_validate_transition_valid(self):
        assert validate_transition("prepared", "confirmed") is True
        assert validate_transition("confirmed", "drilling") is True
        assert validate_transition("drilling", "evaluated") is True
        assert validate_transition("evaluated", "confirmed") is True

    def test_validate_transition_invalid(self):
        assert validate_transition("prepared", "drilling") is False
        assert validate_transition("confirmed", "evaluated") is False
        assert validate_transition("evaluated", "prepared") is True  # reset allowed

    def test_enforce_transition_valid(self):
        enforce_transition("prepared", "confirmed")  # Should not raise

    def test_enforce_transition_invalid(self):
        with pytest.raises(FlowError, match="invalid transition"):
            enforce_transition("prepared", "drilling")

    def test_allowed_transitions_structure(self):
        assert ALLOWED_TRANSITIONS["prepared"] == {"prepared", "confirmed"}
        assert ALLOWED_TRANSITIONS["confirmed"] == {"drilling"}
        assert ALLOWED_TRANSITIONS["drilling"] == {"evaluated", "confirmed", "prepared"}
        assert ALLOWED_TRANSITIONS["evaluated"] == {"confirmed", "prepared"}

    def test_valid_statuses(self):
        assert {"prepared", "confirmed", "drilling", "evaluated"} == VALID_STATUSES


class TestPromptBuilding:
    def test_build_material_blob(self):
        ctx = Context(duration_minutes=30, difficulty="hard", language="fr")
        blob = build_material_blob("photosynthesis", ctx)
        assert "Material:" in blob
        assert "photosynthesis" in blob
        assert "duration_minutes: 30" in blob
        assert "difficulty: hard" in blob
        assert "language: fr" in blob

    def test_build_generate_messages(self):
        ctx = Context(duration_minutes=30)
        messages = build_generate_messages("photosynthesis", ctx, 5)
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert "Knowledge coach" in messages[0]["content"]
        assert messages[1]["role"] == "user"
        assert "Generate 5 Q&A" in messages[1]["content"]

    def test_build_refine_messages(self):
        ctx = Context()
        questions = [Question(id="q1", prompt="What?", agreed_answer="Answer")]
        comments = [{"question_id": "q1", "comment": "Make it simpler"}]
        messages = build_refine_messages("photosynthesis", ctx, questions, comments)
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert "Refine Q&A" in messages[0]["content"]
        assert "Make it simpler" in messages[1]["content"]

    def test_build_evaluate_messages(self):
        ctx = Context()
        questions = [
            Question(id="q1", prompt="What?", agreed_answer="Answer", user_answer="My answer")
        ]
        session = Session(
            id="s1",
            material="photosynthesis",
            question_count=1,
            context=ctx,
            questions=questions,
            status="drilling",
        )
        messages = build_evaluate_messages(session)
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert "Score each user answer" in messages[0]["content"]
        assert "My answer" in messages[1]["content"]


class TestDisplayRules:
    def test_should_show_confidence(self):
        assert should_show_confidence(0.94) is True
        assert should_show_confidence(0.95) is False
        assert should_show_confidence(0.99) is False

    def test_close_alternatives(self):
        alts = [
            {"summary": "a", "score": 0.8},
            {"summary": "b", "score": 0.76},
            {"summary": "c", "score": 0.7},
        ]
        # Convert to Alternative objects
        from qnagym.contracts.types import Alternative

        alt_objs = [Alternative(**a) for a in alts]
        close = close_alternatives(0.8, alt_objs)
        assert len(close) == 2  # 0.8 and 0.76 (within 0.05)
        assert close[0].summary == "a"
        assert close[1].summary == "b"


class TestConfigValidation:
    def test_validate_config_valid(self):
        cfg = Config(
            base_url="http://localhost:11434/v1",
            model="gemma3:12b",
            api_key="ollama",
            data_dir="./data",
            temperature=0.0,
            max_tokens=4096,
            timeout=60,
        )
        validate_config(cfg)

    def test_validate_config_invalid_base_url(self):
        cfg = Config(
            base_url="invalid",
            model="gemma3:12b",
            api_key="ollama",
            data_dir="./data",
            temperature=0.0,
            max_tokens=4096,
            timeout=60,
        )
        with pytest.raises(ValueError, match="base_url must be a valid"):
            validate_config(cfg)

    def test_validate_config_empty_model(self):
        cfg = Config(
            base_url="http://localhost:11434/v1",
            model="",
            api_key="ollama",
            data_dir="./data",
            temperature=0.0,
            max_tokens=4096,
            timeout=60,
        )
        with pytest.raises(ValueError, match="model must be non-empty"):
            validate_config(cfg)

    def test_validate_config_temperature_out_of_range(self):
        cfg = Config(
            base_url="http://localhost:11434/v1",
            model="gemma3:12b",
            api_key="ollama",
            data_dir="./data",
            temperature=3.0,
            max_tokens=4096,
            timeout=60,
        )
        with pytest.raises(ValueError, match="temperature must be in"):
            validate_config(cfg)


class TestResetSession:
    def test_reset_from_drilling(self, sample_session: Session):
        sample_session.status = "drilling"
        sample_session.questions[0].user_answer = "answer"
        from qnagym.contracts.types import Evaluation

        sample_session.questions[0].evaluation = Evaluation(
            score=0.5, confidence=0.5, feedback="ok"
        )
        sample_session.next_steps = ["step1"]
        sample_session.progress.attempts = 1

        reset_session(sample_session)

        assert sample_session.status == "prepared"
        assert sample_session.questions[0].user_answer is None
        assert sample_session.questions[0].evaluation is None
        assert sample_session.next_steps == []
        assert sample_session.progress.attempts == 0

    def test_reset_from_evaluated(self, sample_session: Session):
        sample_session.status = "evaluated"
        reset_session(sample_session)
        assert sample_session.status == "prepared"

    def test_reset_invalid_state(self, sample_session: Session):
        sample_session.status = "confirmed"
        with pytest.raises(FlowError, match="must be in 'drilling' or 'evaluated'"):
            reset_session(sample_session)

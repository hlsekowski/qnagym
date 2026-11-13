"""Unit tests for progress service."""

import pytest

from qnagym.contracts.types import Context, Progress, Question, Session
from qnagym.services.progress import (
    ProgressError,
    get_progress_display_data,
    repeat_service,
    reset_service,
)


class TestProgressService:
    def test_repeat_service_success(self, tmp_path):
        from qnagym.adapters.config import load_config
        from qnagym.adapters.session_store import SessionStore

        config = load_config({"data_dir": tmp_path})
        store = SessionStore(config.data_dir)

        session = Session(
            id="test-session",
            material="photosynthesis",
            question_count=1,
            context=Context(),
            questions=[
                Question(id="q1", prompt="What?", agreed_answer="Answer", user_answer="My answer")
            ],
            status="evaluated",
            progress=Progress(attempts=1, best_score=0.8, last_score=0.8, improving=True),
        )
        store.save(session)

        repeated = repeat_service(store, "test-session")

        assert repeated.status == "confirmed"
        assert repeated.questions[0].user_answer is None
        assert repeated.questions[0].evaluation is None
        assert repeated.progress.attempts == 1  # preserved
        assert repeated.progress.best_score == 0.8  # preserved

    def test_repeat_weak_only_re_drills_only_weak_questions(self, tmp_path):
        from qnagym.adapters.config import load_config
        from qnagym.adapters.session_store import SessionStore

        config = load_config({"data_dir": tmp_path})
        store = SessionStore(config.data_dir)

        session = Session(
            id="test-session",
            material="photosynthesis",
            question_count=3,
            context=Context(),
            questions=[
                Question(
                    id="q1",
                    prompt="Strong?",
                    agreed_answer="Answer",
                    user_answer="My answer",
                    score_history=[0.9],
                    last_score=0.9,
                    best_score=0.9,
                    weak=False,
                ),
                Question(
                    id="q2",
                    prompt="Weak?",
                    agreed_answer="Answer",
                    user_answer="My answer",
                    score_history=[0.3],
                    last_score=0.3,
                    best_score=0.3,
                    weak=True,
                ),
                Question(
                    id="q3",
                    prompt="Also weak?",
                    agreed_answer="Answer",
                    user_answer="My answer",
                    score_history=[0.4],
                    last_score=0.4,
                    best_score=0.4,
                    weak=True,
                ),
            ],
            status="evaluated",
            progress=Progress(attempts=1, best_score=0.53, last_score=0.53, improving=True),
        )
        store.save(session)

        repeated = repeat_service(store, "test-session", weak_only=True)

        assert repeated.status == "confirmed"
        assert len(repeated.questions) == 2
        assert repeated.questions[0].id == "q2"
        assert repeated.questions[1].id == "q3"
        assert repeated.progress.attempts == 1  # preserved

    def test_repeat_weak_only_no_weak_questions(self, tmp_path, capsys):
        from qnagym.adapters.config import load_config
        from qnagym.adapters.session_store import SessionStore

        config = load_config({"data_dir": tmp_path})
        store = SessionStore(config.data_dir)

        session = Session(
            id="test-session",
            material="photosynthesis",
            question_count=2,
            context=Context(),
            questions=[
                Question(
                    id="q1",
                    prompt="Strong?",
                    agreed_answer="Answer",
                    user_answer="My answer",
                    score_history=[0.9],
                    last_score=0.9,
                    best_score=0.9,
                    weak=False,
                ),
                Question(
                    id="q2",
                    prompt="Also strong?",
                    agreed_answer="Answer",
                    user_answer="My answer",
                    score_history=[0.8],
                    last_score=0.8,
                    best_score=0.8,
                    weak=False,
                ),
            ],
            status="evaluated",
            progress=Progress(attempts=1, best_score=0.85, last_score=0.85, improving=True),
        )
        store.save(session)

        repeated = repeat_service(store, "test-session", weak_only=True)

        assert repeated.status == "evaluated"  # unchanged
        assert len(repeated.questions) == 2
        captured = capsys.readouterr()
        assert "No weak questions" in captured.out

    def test_repeat_service_wrong_state(self, tmp_path):
        from qnagym.adapters.config import load_config
        from qnagym.adapters.session_store import SessionStore

        config = load_config({"data_dir": tmp_path})
        store = SessionStore(config.data_dir)

        session = Session(
            id="test-session",
            material="photosynthesis",
            question_count=1,
            context=Context(),
            questions=[Question(id="q1", prompt="What?", agreed_answer="Answer")],
            status="drilling",
        )
        store.save(session)

        with pytest.raises(ProgressError) as exc:
            repeat_service(store, "test-session")
        assert exc.value.exit_code == 2

    def test_reset_service_from_drilling(self, tmp_path):
        from qnagym.adapters.config import load_config
        from qnagym.adapters.session_store import SessionStore

        config = load_config({"data_dir": tmp_path})
        store = SessionStore(config.data_dir)

        session = Session(
            id="test-session",
            material="photosynthesis",
            question_count=1,
            context=Context(),
            questions=[
                Question(id="q1", prompt="What?", agreed_answer="Answer", user_answer="My answer")
            ],
            status="drilling",
            progress=Progress(attempts=1, best_score=0.8, last_score=0.8),
        )
        store.save(session)

        reset = reset_service(store, "test-session")

        assert reset.status == "prepared"
        assert reset.questions[0].user_answer is None
        assert reset.progress.attempts == 0

    def test_reset_service_from_evaluated(self, tmp_path):
        from qnagym.adapters.config import load_config
        from qnagym.adapters.session_store import SessionStore

        config = load_config({"data_dir": tmp_path})
        store = SessionStore(config.data_dir)

        session = Session(
            id="test-session",
            material="photosynthesis",
            question_count=1,
            context=Context(),
            questions=[
                Question(id="q1", prompt="What?", agreed_answer="Answer", user_answer="My answer")
            ],
            status="evaluated",
            progress=Progress(attempts=2, best_score=0.9, last_score=0.7),
        )
        store.save(session)

        reset = reset_service(store, "test-session")

        assert reset.status == "prepared"
        assert reset.progress.attempts == 0

    def test_reset_service_wrong_state(self, tmp_path):
        from qnagym.adapters.config import load_config
        from qnagym.adapters.session_store import SessionStore

        config = load_config({"data_dir": tmp_path})
        store = SessionStore(config.data_dir)

        session = Session(
            id="test-session",
            material="photosynthesis",
            question_count=1,
            context=Context(),
            questions=[Question(id="q1", prompt="What?", agreed_answer="Answer")],
            status="confirmed",
        )
        store.save(session)

        with pytest.raises(ProgressError) as exc:
            reset_service(store, "test-session")
        assert exc.value.exit_code == 2

    def test_get_progress_display_data(self):
        session = Session(
            id="s1",
            material="photosynthesis",
            question_count=1,
            context=Context(),
            questions=[],
            status="evaluated",
            progress=Progress(
                attempts=2, best_score=0.9, last_score=0.8, improving=False, break_suggested=True
            ),
            next_steps=["Review material"],
        )
        data = get_progress_display_data(session)
        assert data["attempts"] == 2
        assert data["best_score"] == "90%"
        assert data["last_score"] == "80%"
        assert data["trend"] == "📉"
        assert data["break_suggested"] is True
        assert data["next_steps"] == ["Review material"]

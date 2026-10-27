"""Unit tests for drill service."""

from io import StringIO
from unittest.mock import patch

import pytest

from qnagym.contracts.types import Context, Question, Session
from qnagym.services.drill import (
    DrillError,
    _drill_interactive,
    drill_service,
    get_drill_display_data,
)


class TestDrillService:
    def test_drill_service_first_answer(self, tmp_path):
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
                Question(id="q1", prompt="What?", agreed_answer="Answer"),
                Question(id="q2", prompt="What 2?", agreed_answer="Answer 2"),
            ],
            status="confirmed",
        )
        store.save(session)

        updated = drill_service(store, "test-session", "q1", "My answer")

        assert updated.questions[0].user_answer == "My answer"
        assert updated.status == "drilling"

    def test_drill_service_subsequent_answer(self, tmp_path):
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
                Question(id="q1", prompt="What?", agreed_answer="Answer", user_answer="First"),
                Question(id="q2", prompt="What 2?", agreed_answer="Answer 2"),
            ],
            status="drilling",
        )
        store.save(session)

        updated = drill_service(store, "test-session", "q2", "Second answer")

        assert updated.questions[1].user_answer == "Second answer"
        assert updated.status == "drilling"

    def test_drill_service_wrong_state(self, tmp_path):
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
            status="prepared",
        )
        store.save(session)

        with pytest.raises(DrillError) as exc:
            drill_service(store, "test-session", "q1", "Answer")
        assert exc.value.exit_code == 2

    def test_drill_service_unknown_question(self, tmp_path):
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

        with pytest.raises(DrillError) as exc:
            drill_service(store, "test-session", "q99", "Answer")
        assert exc.value.exit_code == 2

    def test_get_drill_display_data_next_question(self):
        session = Session(
            id="s1",
            material="photosynthesis",
            question_count=2,
            context=Context(),
            questions=[
                Question(id="q1", prompt="What?", agreed_answer="Answer"),
                Question(id="q2", prompt="What 2?", agreed_answer="Answer 2"),
            ],
            status="confirmed",
        )
        data = get_drill_display_data(session)
        assert data["complete"] is False
        assert data["question"]["id"] == "q1"
        assert data["progress"] == "0/2"

    def test_get_drill_display_data_complete(self):
        session = Session(
            id="s1",
            material="photosynthesis",
            question_count=2,
            context=Context(),
            questions=[
                Question(id="q1", prompt="What?", agreed_answer="Answer", user_answer="A1"),
                Question(id="q2", prompt="What 2?", agreed_answer="Answer 2", user_answer="A2"),
            ],
            status="drilling",
        )
        data = get_drill_display_data(session)
        assert data["complete"] is True


class TestDrillInteractive:
    def test_drill_interactive_answers_all_questions(self, tmp_path):
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
                Question(id="q1", prompt="What?", agreed_answer="Answer"),
                Question(id="q2", prompt="What 2?", agreed_answer="Answer 2"),
            ],
            status="confirmed",
        )
        store.save(session)

        # Simulate user input: answer q1, answer q2, then quit
        user_input = "Answer 1\nAnswer 2\nquit\n"
        with patch("sys.stdin", StringIO(user_input)):
            updated = _drill_interactive(store, session)

        assert updated.questions[0].user_answer == "Answer 1"
        assert updated.questions[1].user_answer == "Answer 2"
        assert updated.status == "drilling"

    def test_drill_interactive_skip_question(self, tmp_path):
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
                Question(id="q1", prompt="What?", agreed_answer="Answer"),
                Question(id="q2", prompt="What 2?", agreed_answer="Answer 2"),
            ],
            status="confirmed",
        )
        store.save(session)

        # Simulate user input: skip q1, answer q2, then quit
        user_input = "skip\nAnswer 2\nquit\n"
        with patch("sys.stdin", StringIO(user_input)):
            updated = _drill_interactive(store, session)

        assert updated.questions[0].user_answer == "[skipped]"
        assert updated.questions[1].user_answer == "Answer 2"

    def test_drill_interactive_quit_early(self, tmp_path):
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
                Question(id="q1", prompt="What?", agreed_answer="Answer"),
                Question(id="q2", prompt="What 2?", agreed_answer="Answer 2"),
            ],
            status="confirmed",
        )
        store.save(session)

        # Simulate user input: quit immediately
        user_input = "quit\n"
        with patch("sys.stdin", StringIO(user_input)):
            updated = _drill_interactive(store, session)

        # No answers recorded
        assert updated.questions[0].user_answer is None
        assert updated.questions[1].user_answer is None

    def test_drill_interactive_wrong_state(self, tmp_path):
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
            status="prepared",
        )
        store.save(session)

        with pytest.raises(DrillError) as exc:
            _drill_interactive(store, session)
        assert exc.value.exit_code == 2

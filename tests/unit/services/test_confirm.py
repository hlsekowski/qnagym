"""Unit tests for confirm service."""

import pytest

from qnagym.contracts.types import Context, Question, Session
from qnagym.services.confirm import ConfirmError, confirm_service, get_confirm_display_data


class TestConfirmService:
    def test_confirm_service_success(self, tmp_path):
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

        confirmed = confirm_service(store, "test-session")

        assert confirmed.status == "confirmed"
        assert confirmed.id == "test-session"

    def test_confirm_service_wrong_state(self, tmp_path):
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

        with pytest.raises(ConfirmError) as exc:
            confirm_service(store, "test-session")
        assert exc.value.exit_code == 2

    def test_get_confirm_display_data(self):
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
        data = get_confirm_display_data(session)
        assert data["id"] == "s1"
        assert data["question_count"] == 2
        assert len(data["questions"]) == 2

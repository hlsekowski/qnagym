"""Unit tests for refine service."""

import pytest

from qnagym.contracts.types import Context, Question, Session
from qnagym.services.refine import RefineError, get_refine_display_data, refine_service
from tests.http import model_client


class TestRefineService:
    def test_refine_service_success(self, tmp_path):
        from qnagym.adapters.config import load_config
        from qnagym.adapters.session_store import SessionStore

        config = load_config({"data_dir": tmp_path})
        store = SessionStore(config.data_dir)

        # Create a session in prepared state
        session = Session(
            id="test-session",
            material="photosynthesis",
            question_count=1,
            context=Context(),
            questions=[Question(id="q1", prompt="What?", agreed_answer="Answer")],
            status="prepared",
        )
        store.save(session)

        client = model_client(
            {
                "ok": True,
                "questions": [
                    {
                        "id": "q1",
                        "prompt": "What is photosynthesis?",
                        "model_answer": "Process by which plants...",
                    }
                ],
            }
        )

        refined = refine_service(
            client, store, "test-session", [{"question_id": "q1", "comment": "Make it specific"}]
        )

        assert refined.questions[0].prompt == "What is photosynthesis?"
        assert refined.questions[0].agreed_answer == "Process by which plants..."
        assert len(refined.questions[0].refinement_history) == 2

    def test_refine_service_wrong_state(self, tmp_path):
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

        client = model_client({"ok": True, "questions": []})

        with pytest.raises(RefineError) as exc:
            refine_service(
                client, store, "test-session", [{"question_id": "q1", "comment": "test"}]
            )
        assert exc.value.exit_code == 2

    def test_refine_service_no_comments(self, tmp_path):
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

        client = model_client({"ok": True, "questions": []})

        with pytest.raises(RefineError) as exc:
            refine_service(client, store, "test-session", [])
        assert exc.value.exit_code == 4

    def test_get_refine_display_data(self):
        session = Session(
            id="s1",
            material="photosynthesis",
            question_count=1,
            context=Context(),
            questions=[
                Question(id="q1", prompt="What?", agreed_answer="Answer", refinement_history=[])
            ],
            status="prepared",
        )
        data = get_refine_display_data(session)
        assert data["id"] == "s1"
        assert data["material"] == "photosynthesis"
        assert len(data["questions"]) == 1

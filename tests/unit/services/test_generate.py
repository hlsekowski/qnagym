"""Unit tests for generate service."""

import pytest

from qnagym.contracts.types import Context, Question, Session
from qnagym.services.generate import GenerateError, generate_service, get_generate_display_data
from tests.http import model_client


class TestGenerateService:
    def test_generate_service_success(self, tmp_path):
        from qnagym.adapters.config import load_config
        from qnagym.adapters.session_store import SessionStore

        config = load_config({"data_dir": tmp_path})
        store = SessionStore(config.data_dir)
        client = model_client(
            {
                "ok": True,
                "questions": [
                    {"prompt": "What is photosynthesis?", "model_answer": "Process...", "id": "q1"},
                    {"prompt": "What are inputs?", "model_answer": "CO2, water, light", "id": "q2"},
                ],
            }
        )

        session = generate_service(
            client, store, "photosynthesis process in plants", question_count=2
        )

        assert session.material == "photosynthesis process in plants"
        assert session.question_count == 2
        assert session.status == "prepared"
        assert len(session.questions) == 2
        assert session.questions[0].prompt == "What is photosynthesis?"

    def test_generate_service_vague_material(self, tmp_path):
        from qnagym.adapters.config import load_config
        from qnagym.adapters.session_store import SessionStore

        config = load_config({"data_dir": tmp_path})
        store = SessionStore(config.data_dir)
        client = model_client({"ok": False, "questions": ["What topic?", "What scope?"]})

        with pytest.raises(GenerateError) as exc:
            generate_service(client, store, "short")
        assert exc.value.exit_code == 4
        assert "Material too vague" in exc.value.message

    def test_generate_service_model_error(self, tmp_path):
        from qnagym.adapters.config import load_config
        from qnagym.adapters.session_store import SessionStore

        config = load_config({"data_dir": tmp_path})
        store = SessionStore(config.data_dir)

        class FailingClient:
            def chat_json(self, messages):
                raise Exception("Connection failed")

        client = FailingClient()

        with pytest.raises(GenerateError) as exc:
            generate_service(
                client, store, "photosynthesis basics and advanced concepts", question_count=2
            )
        assert exc.value.exit_code == 1
        assert "Model error" in exc.value.message

    def test_get_generate_display_data(self):
        session = Session(
            id="s1",
            material="photosynthesis",
            question_count=2,
            context=Context(),
            questions=[
                Question(id="q1", prompt="What?", agreed_answer="Answer"),
                Question(id="q2", prompt="What 2?", agreed_answer="Answer 2"),
            ],
            status="prepared",
        )
        data = get_generate_display_data(session)
        assert data["id"] == "s1"
        assert data["material"] == "photosynthesis"
        assert data["question_count"] == 2
        assert len(data["questions"]) == 2


# Need to import Question for the last test

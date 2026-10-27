"""Integration tests for full E2E flow."""

from qnagym.services.confirm import confirm_service
from qnagym.services.drill import drill_service
from qnagym.services.evaluate import evaluate_service
from qnagym.services.generate import generate_service
from qnagym.services.progress import repeat_service
from qnagym.services.refine import refine_service
from tests.http import model_client_sequence


class TestE2EFlow:
    def test_full_flow_generate_refine_confirm_drill_evaluate_repeat(self, tmp_path):
        from qnagym.adapters.config import load_config
        from qnagym.adapters.session_store import SessionStore

        config = load_config({"data_dir": tmp_path})
        store = SessionStore(config.data_dir)

        # Step 1: Generate
        client = model_client_sequence(
            [
                # Generate response
                {
                    "ok": True,
                    "questions": [
                        {
                            "prompt": "What is photosynthesis?",
                            "model_answer": "Process by which plants convert light to energy",
                            "id": "q1",
                        },
                        {
                            "prompt": "What are the inputs?",
                            "model_answer": "CO2, water, light",
                            "id": "q2",
                        },
                    ],
                },
                # Refine response
                {
                    "ok": True,
                    "questions": [
                        {
                            "id": "q1",
                            "prompt": "What is photosynthesis?",
                            "model_answer": (
                                "Process by which green plants convert light energy "
                                "into chemical energy"
                            ),
                        },
                        {
                            "id": "q2",
                            "prompt": "What are the inputs for photosynthesis?",
                            "model_answer": "Carbon dioxide, water, and light energy",
                        },
                    ],
                },
                # Evaluate response
                {
                    "evaluations": [
                        {
                            "id": "q1",
                            "score": 0.9,
                            "confidence": 0.95,
                            "feedback": "Excellent",
                            "covered_points": ["light energy", "chemical energy"],
                            "missed_points": [],
                            "alternatives": [],
                        },
                        {
                            "id": "q2",
                            "score": 0.8,
                            "confidence": 0.9,
                            "feedback": "Good",
                            "covered_points": ["CO2", "water"],
                            "missed_points": ["light energy"],
                            "alternatives": [],
                        },
                    ],
                    "next_steps": ["Review light energy role"],
                },
            ]
        )

        # Generate
        session = generate_service(
            client, store, "photosynthesis process in plants", question_count=2
        )
        assert session.status == "prepared"
        assert session.question_count == 2
        session_id = session.id

        # Refine
        session = refine_service(
            client,
            store,
            session_id,
            [
                {"question_id": "q1", "comment": "Make more precise"},
                {"question_id": "q2", "comment": "Add light energy"},
            ],
        )
        assert session.status == "prepared"
        assert "chemical energy" in session.questions[0].agreed_answer
        assert "light energy" in session.questions[1].agreed_answer

        # Confirm
        session = confirm_service(store, session_id)
        assert session.status == "confirmed"

        # Drill - answer both questions
        session = drill_service(store, session_id, "q1", "Plants convert light to chemical energy")
        assert session.status == "drilling"
        session = drill_service(store, session_id, "q2", "CO2 and water")
        assert session.status == "drilling"

        # Evaluate
        session = evaluate_service(client, store, session_id)
        assert session.status == "evaluated"
        assert session.progress.attempts == 1
        assert abs(session.progress.last_score - 0.85) < 0.001  # (0.9 + 0.8) / 2
        assert abs(session.progress.best_score - 0.85) < 0.001

        # Repeat
        session = repeat_service(store, session_id)
        assert session.status == "confirmed"
        assert session.questions[0].user_answer is None
        assert session.questions[0].evaluation is None
        assert session.progress.attempts == 1  # preserved

    def test_flow_with_break_suggestion(self, tmp_path):
        from qnagym.adapters.config import load_config
        from qnagym.adapters.session_store import SessionStore

        config = load_config({"data_dir": tmp_path})
        store = SessionStore(config.data_dir)

        client = model_client_sequence(
            [
                # Generate
                {
                    "ok": True,
                    "questions": [
                        {
                            "prompt": "What is photosynthesis?",
                            "model_answer": "Process...",
                            "id": "q1",
                        },
                    ],
                },
                # Evaluate 1 - low score
                {
                    "evaluations": [
                        {
                            "id": "q1",
                            "score": 0.2,
                            "confidence": 0.8,
                            "feedback": "Needs work",
                            "covered_points": [],
                            "missed_points": ["everything"],
                            "alternatives": [],
                        },
                    ],
                    "next_steps": ["Review basics"],
                },
                # Evaluate 2 - still low, not improving
                {
                    "evaluations": [
                        {
                            "id": "q1",
                            "score": 0.25,
                            "confidence": 0.8,
                            "feedback": "Still needs work",
                            "covered_points": [],
                            "missed_points": ["everything"],
                            "alternatives": [],
                        },
                    ],
                    "next_steps": ["Take a break", "Review basics"],
                },
            ]
        )

        # Generate
        session = generate_service(
            client, store, "photosynthesis process in plants", question_count=1
        )
        session_id = session.id

        # Confirm
        session = confirm_service(store, session_id)

        # Drill
        session = drill_service(store, session_id, "q1", "I don't know")

        # Evaluate 1
        session = evaluate_service(client, store, session_id)
        assert session.progress.attempts == 1
        assert session.progress.last_score == 0.2
        assert session.progress.break_suggested is True  # score < 0.3

        # Repeat
        session = repeat_service(store, session_id)

        # Drill again
        session = drill_service(store, session_id, "q1", "Still don't know")

        # Evaluate 2
        session = evaluate_service(client, store, session_id)
        assert session.progress.attempts == 2
        assert session.progress.last_score == 0.25
        assert session.progress.improving is True  # 0.25 > 0.2
        # Score < 0.3 triggers break suggestion even if improving
        assert session.progress.break_suggested is True  # score < 0.3

    def test_reset_to_prepared(self, tmp_path):
        from qnagym.adapters.config import load_config
        from qnagym.adapters.session_store import SessionStore
        from qnagym.services.progress import reset_service

        config = load_config({"data_dir": tmp_path})
        store = SessionStore(config.data_dir)

        client = model_client_sequence(
            [
                # Generate
                {
                    "ok": True,
                    "questions": [
                        {
                            "prompt": "What is photosynthesis?",
                            "model_answer": "Process...",
                            "id": "q1",
                        },
                    ],
                },
                # Evaluate
                {
                    "evaluations": [
                        {
                            "id": "q1",
                            "score": 0.8,
                            "confidence": 0.9,
                            "feedback": "Good",
                            "covered_points": [],
                            "missed_points": [],
                            "alternatives": [],
                        },
                    ],
                    "next_steps": [],
                },
            ]
        )

        # Generate -> Confirm -> Drill -> Evaluate
        session = generate_service(
            client, store, "photosynthesis process in plants", question_count=1
        )
        session_id = session.id
        session = confirm_service(store, session_id)
        session = drill_service(store, session_id, "q1", "My answer")
        session = evaluate_service(client, store, session_id)
        assert session.status == "evaluated"

        # Reset to prepared
        session = reset_service(store, session_id)
        assert session.status == "prepared"
        assert session.questions[0].user_answer is None
        assert session.questions[0].evaluation is None
        assert session.progress.attempts == 0

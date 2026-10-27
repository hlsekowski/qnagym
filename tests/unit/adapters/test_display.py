"""Unit tests for display adapter."""

from qnagym.adapters.display import (
    print_confirm_result,
    print_drill_result,
    print_error,
    print_evaluate_result,
    print_generate_result,
    print_info,
    print_json,
    print_progress_result,
    print_refine_result,
    print_session_detail,
    print_session_list,
)
from qnagym.contracts.types import Context, Evaluation, Progress, Question, Session


class TestDisplayAdapter:
    def test_print_json(self, capsys):
        print_json({"key": "value"})
        captured = capsys.readouterr()
        assert '{\n  "key": "value"\n}' in captured.out

    def test_print_error(self, capsys):
        print_error("Test error")
        captured = capsys.readouterr()
        assert "Error: Test error" in captured.err

    def test_print_info(self, capsys):
        print_info("Test info")
        captured = capsys.readouterr()
        assert "Test info" in captured.out

    def test_print_session_list_empty(self, capsys):
        print_session_list([])
        captured = capsys.readouterr()
        assert "No sessions found" in captured.out

    def test_print_session_list(self, capsys):
        sessions = [
            Session(
                id="test-123",
                material="photosynthesis",
                question_count=2,
                context=Context(),
                questions=[Question(id="q1", prompt="What?", agreed_answer="Answer")],
                status="prepared",
                progress=Progress(attempts=0, best_score=0.0, last_score=0.0),
            )
        ]
        print_session_list(sessions)
        captured = capsys.readouterr()
        assert "test-123" in captured.out
        assert "photosynthesis" in captured.out

    def test_print_session_detail(self, capsys):
        session = Session(
            id="test-123",
            material="photosynthesis",
            question_count=1,
            context=Context(),
            questions=[
                Question(
                    id="q1",
                    prompt="What?",
                    agreed_answer="Answer",
                    user_answer="My answer",
                    evaluation=Evaluation(score=0.8, confidence=0.9, feedback="Good"),
                )
            ],
            status="evaluated",
            progress=Progress(attempts=1, best_score=0.8, last_score=0.8),
            next_steps=["Review"],
        )
        print_session_detail(session)
        captured = capsys.readouterr()
        assert "test-123" in captured.out
        assert "photosynthesis" in captured.out
        assert "What?" in captured.out
        assert "80%" in captured.out

    def test_print_generate_result(self, capsys):
        data = {
            "id": "test-123",
            "material": "photosynthesis",
            "question_count": 2,
            "questions": [
                {"id": "q1", "prompt": "What?", "agreed_answer": "Answer"},
                {"id": "q2", "prompt": "What 2?", "agreed_answer": "Answer 2"},
            ],
        }
        print_generate_result(data)
        captured = capsys.readouterr()
        assert "test-123" in captured.out
        assert "photosynthesis" in captured.out

    def test_print_refine_result(self, capsys):
        data = {
            "id": "test-123",
            "material": "photosynthesis",
            "questions": [
                {
                    "id": "q1",
                    "prompt": "What?",
                    "agreed_answer": "Answer",
                    "refinement_history": [],
                },
            ],
        }
        print_refine_result(data)
        captured = capsys.readouterr()
        assert "test-123" in captured.out

    def test_print_confirm_result(self, capsys):
        data = {"id": "test-123", "question_count": 2}
        print_confirm_result(data)
        captured = capsys.readouterr()
        assert "test-123" in captured.out
        assert "2" in captured.out

    def test_print_drill_result_next(self, capsys):
        data = {
            "id": "test-123",
            "status": "drilling",
            "complete": False,
            "progress": "1/2",
            "question": {"id": "q1", "prompt": "What?"},
        }
        print_drill_result(data)
        captured = capsys.readouterr()
        assert "test-123" in captured.out
        assert "What?" in captured.out

    def test_print_drill_result_complete(self, capsys):
        data = {"complete": True, "message": "All done!"}
        print_drill_result(data)
        captured = capsys.readouterr()
        assert "All done!" in captured.out

    def test_print_evaluate_result(self, capsys):
        session = Session(
            id="test-123",
            material="photosynthesis",
            question_count=1,
            context=Context(),
            questions=[
                Question(
                    id="q1",
                    prompt="What?",
                    agreed_answer="Answer",
                    user_answer="My answer",
                    evaluation=Evaluation(
                        score=0.8,
                        confidence=0.9,
                        feedback="Good",
                        covered_points=["a"],
                        missed_points=["b"],
                    ),
                )
            ],
            status="evaluated",
            progress=Progress(attempts=1, best_score=0.8, last_score=0.8, improving=True),
            next_steps=["Review"],
        )
        evaluations = [
            {
                "id": "q1",
                "evaluated": True,
                "score": 0.8,
                "confidence": 0.9,
                "show_confidence": False,
                "feedback": "Good",
                "covered_points": ["a"],
                "missed_points": ["b"],
                "alternatives": [],
            },
        ]
        next_steps = ["Review"]
        print_evaluate_result(session, evaluations, next_steps)
        captured = capsys.readouterr()
        assert "test-123" in captured.out
        assert "80%" in captured.out
        assert "Good" in captured.out

    def test_print_progress_result(self, capsys):
        data = {
            "id": "test-123",
            "attempts": 2,
            "best_score": "80%",
            "last_score": "70%",
            "trend": "📈",
            "improving": True,
            "break_suggested": False,
            "next_steps": ["Review"],
        }
        print_progress_result(data)
        captured = capsys.readouterr()
        assert "test-123" in captured.out
        assert "80%" in captured.out
        assert "📈" in captured.out

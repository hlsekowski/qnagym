"""Contract tests for types."""

import pytest
from freezegun import freeze_time

from qnagym.contracts.types import (
    Alternative,
    Config,
    Context,
    Evaluation,
    GenerateQuestion,
    GenerateResponse,
    Progress,
    Question,
    RefinementEntry,
    Session,
)


class TestAlternative:
    def test_to_dict(self):
        alt = Alternative(summary="test", score=0.5)
        assert alt.to_dict() == {"summary": "test", "score": 0.5}

    def test_from_dict(self):
        alt = Alternative.from_dict({"summary": "test", "score": 0.5})
        assert alt.summary == "test"
        assert alt.score == 0.5


class TestEvaluation:
    def test_to_dict(self):
        ev = Evaluation(
            score=0.8, confidence=0.9, feedback="Good", covered_points=["a"], missed_points=["b"]
        )
        d = ev.to_dict()
        assert d["score"] == 0.8
        assert d["confidence"] == 0.9
        assert d["feedback"] == "Good"
        assert d["covered_points"] == ["a"]
        assert d["missed_points"] == ["b"]

    def test_from_dict_none(self):
        assert Evaluation.from_dict(None) is None

    def test_from_dict_full(self):
        ev = Evaluation.from_dict(
            {
                "score": 0.8,
                "confidence": 0.9,
                "feedback": "Good",
                "covered_points": ["a"],
                "missed_points": ["b"],
                "alternatives": [{"summary": "alt", "score": 0.7}],
            }
        )
        assert ev.score == 0.8
        assert len(ev.alternatives) == 1


class TestRefinementEntry:
    def test_roundtrip(self):
        entry = RefinementEntry(
            timestamp="2024-01-01T00:00:00+00:00",
            question_id="q1",
            field="prompt",
            comment="Make it clearer",
            previous_value="old",
            new_value="new",
        )
        d = entry.to_dict()
        entry2 = RefinementEntry.from_dict(d)
        assert entry2.timestamp == entry.timestamp
        assert entry2.question_id == entry.question_id
        assert entry2.field == entry.field
        assert entry2.comment == entry.comment
        assert entry2.previous_value == entry.previous_value
        assert entry2.new_value == entry.new_value


class TestQuestion:
    def test_to_dict(self):
        q = Question(id="q1", prompt="What?", agreed_answer="Answer")
        d = q.to_dict()
        assert d["id"] == "q1"
        assert d["prompt"] == "What?"
        assert d["agreed_answer"] == "Answer"
        assert d["user_answer"] is None
        assert d["evaluation"] is None
        assert d["refinement_history"] == []

    def test_from_dict_valid(self):
        q = Question.from_dict({"id": "q1", "prompt": "What?", "agreed_answer": "Answer"})
        assert q.id == "q1"
        assert q.prompt == "What?"
        assert q.agreed_answer == "Answer"

    def test_from_dict_missing_prompt(self):
        with pytest.raises(ValueError, match="prompt is required"):
            Question.from_dict({"id": "q1", "agreed_answer": "Answer"})

    def test_from_dict_missing_agreed_answer(self):
        with pytest.raises(ValueError, match="agreed_answer is required"):
            Question.from_dict({"id": "q1", "prompt": "What?"})


class TestContext:
    def test_defaults(self):
        ctx = Context()
        assert ctx.duration_minutes is None
        assert ctx.difficulty == "medium"
        assert ctx.language == "en"

    def test_from_dict(self):
        ctx = Context.from_dict({"duration_minutes": 30, "difficulty": "hard", "language": "fr"})
        assert ctx.duration_minutes == 30
        assert ctx.difficulty == "hard"
        assert ctx.language == "fr"


class TestProgress:
    def test_defaults(self):
        p = Progress()
        assert p.attempts == 0
        assert p.best_score == 0.0
        assert p.last_score == 0.0
        assert p.improving is True
        assert p.break_suggested is False

    def test_from_dict(self):
        p = Progress.from_dict(
            {
                "attempts": 2,
                "best_score": 0.9,
                "last_score": 0.8,
                "improving": False,
                "break_suggested": True,
            }
        )
        assert p.attempts == 2
        assert p.best_score == 0.9
        assert p.last_score == 0.8
        assert p.improving is False
        assert p.break_suggested is True


class TestSession:
    def test_to_dict(self, sample_session: Session):
        d = sample_session.to_dict()
        assert d["id"] == "test-session-123"
        assert d["material"] == "photosynthesis"
        assert d["question_count"] == 2
        assert d["status"] == "prepared"
        assert len(d["questions"]) == 2

    def test_from_dict(self, sample_session: Session):
        d = sample_session.to_dict()
        session2 = Session.from_dict(d)
        assert session2.id == sample_session.id
        assert session2.material == sample_session.material
        assert len(session2.questions) == 2

    def test_unanswered(self, sample_session: Session):
        assert len(sample_session.unanswered()) == 2
        sample_session.questions[0].user_answer = "My answer"
        assert len(sample_session.unanswered()) == 1

    def test_touch_updates_timestamp(self, sample_session: Session):
        with freeze_time("2024-01-01T00:00:00+00:00"):
            old = sample_session.updated_at
        with freeze_time("2024-01-01T00:00:01+00:00"):
            sample_session.touch()
        assert sample_session.updated_at != old


class TestGenerateQuestion:
    def test_roundtrip(self):
        GenerateQuestion(prompt="What?", model_answer="Answer", id="q1")
        # GenerateResponse handles serialization


class TestGenerateResponse:
    def test_from_dict_ok(self):
        resp = GenerateResponse.from_dict(
            {"ok": True, "questions": [{"prompt": "What?", "model_answer": "Answer", "id": "q1"}]}
        )
        assert resp.ok is True
        assert len(resp.questions) == 1
        assert resp.questions[0].prompt == "What?"

    def test_from_dict_not_ok(self):
        resp = GenerateResponse.from_dict({"ok": False, "questions": ["Clarifying?"]})
        assert resp.ok is False
        assert len(resp.questions) == 1
        assert resp.questions[0].prompt == "Clarifying?"


class TestConfig:
    def test_to_dict(self):
        from pathlib import Path

        cfg = Config(
            base_url="http://localhost:11434/v1",
            model="gemma3:12b",
            api_key="ollama",
            data_dir=Path("./data"),
            temperature=0.0,
            max_tokens=4096,
            timeout=60,
        )
        d = cfg.to_dict()
        assert d["base_url"] == "http://localhost:11434/v1"
        assert d["model"] == "gemma3:12b"
        assert d["data_dir"] == "data"

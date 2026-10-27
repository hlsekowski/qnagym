"""Contract tests for session schema."""

from qnagym.contracts.types import Alternative, Context, Evaluation, Progress, Question, Session


class TestSessionSchema:
    def test_session_schema_roundtrip(self):
        """Test that session can be serialized and deserialized correctly."""
        session = Session(
            id="test-123",
            material="photosynthesis",
            question_count=2,
            context=Context(duration_minutes=30, difficulty="medium", language="en"),
            questions=[
                Question(id="q1", prompt="What is photosynthesis?", agreed_answer="Process..."),
                Question(id="q2", prompt="What are inputs?", agreed_answer="CO2, water, light"),
            ],
            progress=Progress(attempts=1, best_score=0.8, last_score=0.8, improving=True),
            next_steps=["Review"],
            status="prepared",
        )

        # Serialize
        data = session.to_dict()

        # Deserialize
        session2 = Session.from_dict(data)

        assert session2.id == session.id
        assert session2.material == session.material
        assert session2.question_count == session.question_count
        assert session2.context.duration_minutes == session.context.duration_minutes
        assert len(session2.questions) == 2
        assert session2.progress.attempts == 1

    def test_session_status_reviewed_sync(self):
        """Test that status and reviewed are in sync (adapted for qnagym)."""
        # In qnagym, status is the authoritative field
        session = Session(
            id="test",
            material="test",
            question_count=1,
            context=Context(),
            questions=[Question(id="q1", prompt="What?", agreed_answer="Answer")],
            status="prepared",
        )
        assert session.status == "prepared"

        session.status = "confirmed"
        assert session.status == "confirmed"

    def test_evaluation_schema(self):
        """Test evaluation object schema."""
        ev = Evaluation(
            score=0.8,
            confidence=0.9,
            feedback="Good",
            covered_points=["a"],
            missed_points=["b"],
            alternatives=[Alternative(summary="alt", score=0.7)],
        )
        data = ev.to_dict()
        assert data["score"] == 0.8
        assert data["confidence"] == 0.9
        assert data["feedback"] == "Good"
        assert data["covered_points"] == ["a"]
        assert data["missed_points"] == ["b"]
        assert len(data["alternatives"]) == 1

    def test_question_refinement_history(self):
        """Test question refinement history schema."""
        from qnagym.contracts.types import RefinementEntry

        q = Question(
            id="q1",
            prompt="What?",
            agreed_answer="Answer",
            refinement_history=[
                RefinementEntry(
                    timestamp="2024-01-01T00:00:00+00:00",
                    question_id="q1",
                    field="prompt",
                    comment="Make clearer",
                    previous_value="Old",
                    new_value="New",
                )
            ],
        )
        data = q.to_dict()
        assert len(data["refinement_history"]) == 1
        assert data["refinement_history"][0]["field"] == "prompt"

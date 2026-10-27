"""Unit tests for session store adapter."""

import pytest

from qnagym.adapters.session_store import SessionStore, new_session_id
from qnagym.contracts.types import Context, Question, Session


class TestSessionStore:
    def test_new_session_id(self):
        id1 = new_session_id()
        id2 = new_session_id()
        assert id1 != id2
        assert len(id1) == 36  # UUID format

    def test_save_and_load(self, tmp_path):
        store = SessionStore(tmp_path)
        session = Session(
            id="test-123",
            material="photosynthesis",
            question_count=1,
            context=Context(),
            questions=[Question(id="q1", prompt="What?", agreed_answer="Answer")],
            status="prepared",
        )
        path = store.save(session)
        assert path.exists()
        assert path.name == "test-123.json"

        loaded = store.load("test-123")
        assert loaded.id == "test-123"
        assert loaded.material == "photosynthesis"

    def test_load_by_path(self, tmp_path):
        store = SessionStore(tmp_path)
        session = Session(
            id="test-123",
            material="photosynthesis",
            question_count=1,
            context=Context(),
            questions=[Question(id="q1", prompt="What?", agreed_answer="Answer")],
            status="prepared",
        )
        path = store.save(session)

        loaded = store.load(str(path))
        assert loaded.id == "test-123"

    def test_load_not_found(self, tmp_path):
        store = SessionStore(tmp_path)
        with pytest.raises(FileNotFoundError):
            store.load("nonexistent")

    def test_list_all(self, tmp_path):
        store = SessionStore(tmp_path)
        for i in range(3):
            session = Session(
                id=f"test-{i}",
                material=f"topic{i}",
                question_count=1,
                context=Context(),
                questions=[Question(id="q1", prompt="What?", agreed_answer="Answer")],
                status="prepared",
            )
            store.save(session)

        sessions = store.list_all()
        assert len(sessions) == 3
        # Should be sorted newest first
        assert sessions[0].id == "test-2"

    def test_delete(self, tmp_path):
        store = SessionStore(tmp_path)
        session = Session(
            id="test-123",
            material="photosynthesis",
            question_count=1,
            context=Context(),
            questions=[Question(id="q1", prompt="What?", agreed_answer="Answer")],
            status="prepared",
        )
        store.save(session)
        store.delete("test-123")
        with pytest.raises(FileNotFoundError):
            store.load("test-123")

    def test_latest(self, tmp_path):
        store = SessionStore(tmp_path)
        for i in range(3):
            session = Session(
                id=f"test-{i}",
                material=f"topic{i}",
                question_count=1,
                context=Context(),
                questions=[Question(id="q1", prompt="What?", agreed_answer="Answer")],
                status="prepared",
            )
            store.save(session)

        latest = store.latest()
        assert latest.id == "test-2"

    def test_invalid_session_id(self, tmp_path):
        store = SessionStore(tmp_path)
        with pytest.raises(ValueError):
            store.path_for("")
        with pytest.raises(ValueError):
            store.path_for("../escape")
        with pytest.raises(ValueError):
            store.path_for("path/with/slash")

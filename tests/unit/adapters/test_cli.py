"""Unit tests for CLI adapter."""

import json
from pathlib import Path

import pytest

from qnagym.adapters.cli import build_parser, parse_comments
from qnagym.adapters.config import load_config
from qnagym.adapters.session_store import SessionStore
from qnagym.contracts.types import Context, Progress, Question, Session


class TestCLIAdapter:
    def test_build_parser(self):
        parser = build_parser()
        assert parser is not None

    def test_parse_comments_with_qid(self):
        comments = parse_comments(["q1:make it simpler", "q2:add detail"], None)
        assert len(comments) == 2
        assert comments[0]["question_id"] == "q1"
        assert comments[0]["comment"] == "make it simpler"
        assert comments[1]["question_id"] == "q2"
        assert comments[1]["comment"] == "add detail"

    def test_parse_comments_with_question_id(self):
        comments = parse_comments(["make it simpler"], "q1")
        assert len(comments) == 1
        assert comments[0]["question_id"] == "q1"
        assert comments[0]["comment"] == "make it simpler"

    def test_parse_comments_error(self):
        with pytest.raises(ValueError, match="needs question ID"):
            parse_comments(["make it simpler"], None)


class TestDeleteExport:
    def _make_session(self, tmp_path, session_id="test-session", status="evaluated"):
        config = load_config({"data_dir": tmp_path})
        store = SessionStore(config.data_dir)
        session = Session(
            id=session_id,
            material="photosynthesis",
            question_count=1,
            context=Context(),
            questions=[
                Question(id="q1", prompt="What?", agreed_answer="Answer", user_answer="My answer")
            ],
            status=status,
            progress=Progress(attempts=1, best_score=0.8, last_score=0.8),
        )
        store.save(session)
        return store, session

    def test_delete_removes_session_file(self, tmp_path):
        store, session = self._make_session(tmp_path)
        file_path = store.path_for(session.id)
        assert file_path.is_file()

        store.delete(session.id)
        assert not file_path.is_file()

    def test_delete_missing_session_raises(self, tmp_path):
        store = SessionStore(Path(tmp_path))
        with pytest.raises(FileNotFoundError, match="No session"):
            store.delete("nonexistent")

    def test_export_writes_json_to_file(self, tmp_path):
        store, session = self._make_session(tmp_path)
        output = Path(tmp_path) / "exported.json"

        store.load(session.id)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(session.to_dict(), indent=2) + "\n", encoding="utf-8")

        assert output.is_file()
        data = json.loads(output.read_text(encoding="utf-8"))
        assert data["id"] == session.id
        assert data["material"] == "photosynthesis"
        assert data["status"] == "evaluated"

    def test_export_load_missing_session_raises(self, tmp_path):
        store = SessionStore(Path(tmp_path))
        with pytest.raises(FileNotFoundError, match="No session"):
            store.load("nonexistent")

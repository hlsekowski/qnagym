"""Unit tests for CLI adapter."""

import pytest

from qnagym.adapters.cli import build_parser, parse_comments


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

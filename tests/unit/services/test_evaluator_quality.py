"""Evaluator quality harness: golden-set test for model score ordering.

Skips when no local model is available (CI-safe).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from qnagym.contracts.types import Context, Question, Session
from qnagym.contracts.validation import build_evaluate_messages
from qnagym.domain.scoring import parse_evaluate_response

GOLDEN_SET_PATH = Path(__file__).parent.parent.parent / "fixtures" / "golden_set.json"


def _load_golden_set() -> list[dict]:
    with open(GOLDEN_SET_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data["questions"]


def _model_available() -> bool:
    """Check whether a local model endpoint is reachable."""
    import os

    if os.environ.get("QNAGYM_RUN_MODEL_TESTS") != "1":
        return False
    try:
        import urllib.request

        req = urllib.request.Request("http://127.0.0.1:11434/v1/models")
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            return resp.status == 200
    except Exception:
        return False


def _score_answer(client, question: dict, answer: str) -> float:
    """Score a single answer using the model evaluator."""
    session = Session(
        id="golden-test",
        material="golden set",
        question_count=1,
        context=Context(),
        questions=[
            Question(
                id="q1",
                prompt=question["question"],
                agreed_answer=question["agreed_answer"],
                user_answer=answer,
            )
        ],
        status="drilling",
    )
    messages = build_evaluate_messages(session)
    response = client.chat_json(messages)
    eval_response = parse_evaluate_response(response)
    return eval_response.evaluations[0].score


@pytest.mark.skipif(not _model_available(), reason="No local model available")
class TestEvaluatorQuality:
    def test_score_ordering_correct_partial_wrong(self):
        """For each golden-set question, score(correct) > score(partial) > score(wrong)."""
        from qnagym.adapters.client import ModelClient
        from qnagym.adapters.config import load_config

        questions = _load_golden_set()
        config = load_config({})
        client = ModelClient(config)

        failures: list[str] = []
        for q in questions:
            scores = {
                "correct": _score_answer(client, q, q["correct_answer"]),
                "partial": _score_answer(client, q, q["partial_answer"]),
                "wrong": _score_answer(client, q, q["wrong_answer"]),
            }
            if not (scores["correct"] > scores["partial"] > scores["wrong"]):
                failures.append(
                    f"{q['id']}: correct={scores['correct']:.2f}, "
                    f"partial={scores['partial']:.2f}, "
                    f"wrong={scores['wrong']:.2f}"
                )

        assert not failures, f"Score ordering failures: {failures}"

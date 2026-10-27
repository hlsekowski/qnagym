"""Type definitions (pure data shapes, no logic).

Mirrors docs/spec/session.md, docs/spec/flow.md, docs/spec/prompts.md,
docs/spec/questions.md, docs/spec/config.md.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


# --- Adapter Protocols (for dependency inversion) ---


class ModelClientProtocol(Protocol):
    """Protocol for model client - implemented by adapters/client.py"""

    def chat_json(self, messages: list[dict[str, Any]]) -> dict[str, Any]: ...


class SessionStoreProtocol(Protocol):
    """Protocol for session store - implemented by adapters/session_store.py"""

    def save(self, session: Session) -> Path: ...

    def load(self, session_id: str) -> Session: ...

    def latest(self) -> Session: ...

    def list_all(self) -> list[Session]: ...

    def delete(self, session_id: str) -> None: ...

    def new_session_id(self) -> str: ...


# --- Session types (from docs/spec/session.md) ---


@dataclass
class Alternative:
    summary: str
    score: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Alternative:
        return cls(
            summary=str(data.get("summary", "")),
            score=float(data.get("score", 0)),
        )


@dataclass
class Evaluation:
    score: float
    confidence: float
    feedback: str
    covered_points: list[str] = field(default_factory=list)
    missed_points: list[str] = field(default_factory=list)
    alternatives: list[Alternative] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "confidence": self.confidence,
            "feedback": self.feedback,
            "covered_points": self.covered_points,
            "missed_points": self.missed_points,
            "alternatives": [a.to_dict() for a in self.alternatives],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> Evaluation | None:
        if data is None:
            return None
        alts = [Alternative.from_dict(a) for a in data.get("alternatives") or []]
        return cls(
            score=float(data.get("score", 0)),
            confidence=float(data.get("confidence", 0)),
            feedback=str(data.get("feedback", "")),
            covered_points=list(data.get("covered_points") or []),
            missed_points=list(data.get("missed_points") or []),
            alternatives=alts,
        )


@dataclass
class RefinementEntry:
    timestamp: str
    question_id: str
    field: str  # "prompt" | "agreed_answer"
    comment: str
    previous_value: str
    new_value: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RefinementEntry:
        return cls(
            timestamp=str(data.get("timestamp", _now())),
            question_id=str(data.get("question_id", "")),
            field=str(data.get("field", "")),
            comment=str(data.get("comment", "")),
            previous_value=str(data.get("previous_value", "")),
            new_value=str(data.get("new_value", "")),
        )


@dataclass
class Question:
    id: str
    prompt: str
    agreed_answer: str
    user_answer: str | None = None
    evaluation: Evaluation | None = None
    refinement_history: list[RefinementEntry] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "prompt": self.prompt,
            "agreed_answer": self.agreed_answer,
            "user_answer": self.user_answer,
            "evaluation": self.evaluation.to_dict() if self.evaluation else None,
            "refinement_history": [r.to_dict() for r in self.refinement_history],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Question:
        prompt = str(data.get("prompt", ""))
        agreed_answer = str(data.get("agreed_answer", ""))
        if not prompt:
            raise ValueError(f"question {data.get('id')} prompt is required")
        if not agreed_answer:
            raise ValueError(f"question {data.get('id')} agreed_answer is required")
        return cls(
            id=str(data["id"]),
            prompt=prompt,
            agreed_answer=agreed_answer,
            user_answer=data.get("user_answer"),
            evaluation=Evaluation.from_dict(data.get("evaluation")),
            refinement_history=[
                RefinementEntry.from_dict(r) for r in data.get("refinement_history") or []
            ],
        )


@dataclass
class Context:
    duration_minutes: int | None = None
    difficulty: str = "medium"
    language: str = "en"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Context:
        duration = data.get("duration_minutes")
        return cls(
            duration_minutes=int(duration) if duration is not None else None,
            difficulty=str(data.get("difficulty", "medium")),
            language=str(data.get("language", "en")),
        )


@dataclass
class Progress:
    attempts: int = 0
    best_score: float = 0.0
    last_score: float = 0.0
    improving: bool = True
    break_suggested: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Progress:
        return cls(
            attempts=int(data.get("attempts", 0)),
            best_score=float(data.get("best_score", 0.0)),
            last_score=float(data.get("last_score", 0.0)),
            improving=bool(data.get("improving", True)),
            break_suggested=bool(data.get("break_suggested", False)),
        )


@dataclass
class Session:
    id: str
    material: str
    question_count: int
    context: Context = field(default_factory=Context)
    questions: list[Question] = field(default_factory=list)
    progress: Progress = field(default_factory=Progress)
    next_steps: list[str] = field(default_factory=list)
    status: str = "prepared"
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status,
            "material": self.material,
            "question_count": self.question_count,
            "context": self.context.to_dict(),
            "questions": [q.to_dict() for q in self.questions],
            "progress": self.progress.to_dict(),
            "next_steps": self.next_steps,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Session:
        return cls(
            id=str(data["id"]),
            created_at=str(data.get("created_at", _now())),
            updated_at=str(data.get("updated_at", _now())),
            status=str(data.get("status", "prepared")),
            material=str(data.get("material", "")),
            question_count=int(data.get("question_count", len(data.get("questions") or []))),
            context=Context.from_dict(data.get("context") or {}),
            questions=[Question.from_dict(q) for q in data.get("questions") or []],
            progress=Progress.from_dict(data.get("progress") or {}),
            next_steps=list(data.get("next_steps") or []),
        )

    def unanswered(self) -> list[Question]:
        return [q for q in self.questions if not (q.user_answer or "").strip()]

    def touch(self) -> None:
        self.updated_at = _now()


# --- Prompt/Response types (from docs/spec/prompts.md) ---


@dataclass
class GenerateQuestion:
    prompt: str
    model_answer: str
    id: str | None = None


@dataclass
class GenerateResponse:
    ok: bool
    questions: list[GenerateQuestion] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        if self.ok:
            return {
                "ok": True,
                "questions": [
                    {"prompt": q.prompt, "model_answer": q.model_answer, "id": q.id}
                    for q in self.questions
                ],
            }
        else:
            return {"ok": False, "questions": [q.prompt for q in self.questions]}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GenerateResponse:
        ok = data.get("ok", True)
        raw_qs = data.get("questions") or []
        questions = []
        if ok:
            for item in raw_qs:
                questions.append(
                    GenerateQuestion(
                        prompt=str(item.get("prompt", "")),
                        model_answer=str(item.get("model_answer", "")),
                        id=item.get("id"),
                    )
                )
        else:
            for item in raw_qs:
                questions.append(GenerateQuestion(prompt=str(item), model_answer=""))
        return cls(ok=ok, questions=questions)


@dataclass
class RefineQuestion:
    id: str
    prompt: str
    model_answer: str


@dataclass
class RefineResponse:
    ok: bool
    questions: list[RefineQuestion] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        if self.ok:
            return {
                "ok": True,
                "questions": [
                    {"id": q.id, "prompt": q.prompt, "model_answer": q.model_answer}
                    for q in self.questions
                ],
            }
        else:
            return {"ok": False, "questions": [q.prompt for q in self.questions]}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RefineResponse:
        ok = data.get("ok", True)
        raw_qs = data.get("questions") or []
        questions = []
        for item in raw_qs:
            questions.append(
                RefineQuestion(
                    id=str(item.get("id", "")),
                    prompt=str(item.get("prompt", "")),
                    model_answer=str(item.get("model_answer", "")),
                )
            )
        return cls(ok=ok, questions=questions)


@dataclass
class EvaluationItem:
    id: str
    score: float
    confidence: float
    feedback: str
    covered_points: list[str] = field(default_factory=list)
    missed_points: list[str] = field(default_factory=list)
    alternatives: list[Alternative] = field(default_factory=list)


@dataclass
class EvaluateResponse:
    evaluations: list[EvaluationItem] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "evaluations": [
                {
                    "id": e.id,
                    "score": e.score,
                    "confidence": e.confidence,
                    "feedback": e.feedback,
                    "covered_points": e.covered_points,
                    "missed_points": e.missed_points,
                    "alternatives": [a.to_dict() for a in e.alternatives],
                }
                for e in self.evaluations
            ],
            "next_steps": self.next_steps,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EvaluateResponse:
        evals = []
        for item in data.get("evaluations") or []:
            alts = [Alternative.from_dict(a) for a in item.get("alternatives") or []]
            evals.append(
                EvaluationItem(
                    id=str(item.get("id", "")),
                    score=float(item.get("score", 0)),
                    confidence=float(item.get("confidence", 0)),
                    feedback=str(item.get("feedback", "")),
                    covered_points=list(item.get("covered_points") or []),
                    missed_points=list(item.get("missed_points") or []),
                    alternatives=alts,
                )
            )
        return cls(
            evaluations=evals,
            next_steps=[str(s) for s in data.get("next_steps") or []],
        )


# --- Config types (from docs/spec/config.md) ---


@dataclass
class Config:
    base_url: str
    model: str
    api_key: str
    data_dir: Path
    temperature: float
    max_tokens: int
    timeout: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "base_url": self.base_url,
            "model": self.model,
            "api_key": self.api_key,
            "data_dir": str(self.data_dir),
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
        }

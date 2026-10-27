"""Display adapter (I/O boundary).

Mirrors docs/spec/cli.md, docs/spec/session.md.
"""

from __future__ import annotations

import json
import sys
from typing import Any

from qnagym.contracts.types import Session


def print_json(data: Any) -> None:
    """Print JSON to stdout."""
    json.dump(data, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


def print_error(message: str) -> None:
    """Print error to stderr."""
    sys.stderr.write(f"Error: {message}\n")


def print_info(message: str) -> None:
    """Print info to stdout."""
    sys.stdout.write(f"{message}\n")


def print_session_list(sessions: list[Session], limit: int = 10) -> None:
    """Print session list in human-readable format."""
    if not sessions:
        print_info("No sessions found.")
        return

    print_info(f"Recent sessions (showing {min(limit, len(sessions))} of {len(sessions)}):")
    print_info("")

    for _i, session in enumerate(sessions[:limit]):
        status_icon = {
            "prepared": "📝",
            "confirmed": "✅",
            "drilling": "✏️",
            "evaluated": "📊",
        }.get(session.status, "❓")

        progress = session.progress
        trend = "📈" if progress.improving else ("📉" if progress.attempts > 1 else "➡️")

        print_info(
            f"  {status_icon} {session.id[:8]}... | "
            f"{session.status:10} | "
            f"Q: {session.question_count:2} | "
            f"Attempts: {progress.attempts} | "
            f"Best: {progress.best_score*100:.0f}% {trend} | "
            f"{session.material[:50]}..."
        )


def print_session_detail(session: Session) -> None:
    """Print full session detail."""
    print_info(f"Session: {session.id}")
    print_info(f"Status: {session.status}")
    print_info(f"Material: {session.material}")
    print_info(f"Questions: {session.question_count}")
    print_info(f"Created: {session.created_at}")
    print_info(f"Updated: {session.updated_at}")
    print_info("")

    print_info("Questions:")
    for q in session.questions:
        print_info(f"  {q.id}: {q.prompt}")
        if q.agreed_answer:
            print_info(f"    Agreed: {q.agreed_answer[:100]}...")
        if q.user_answer:
            print_info(f"    Your answer: {q.user_answer[:100]}...")
        if q.evaluation:
            ev = q.evaluation
            print_info(f"    Score: {ev.score*100:.0f}%")
            if ev.feedback:
                print_info(f"    Feedback: {ev.feedback}")
        print_info("")

    prog = session.progress
    print_info(
        f"Progress: {prog.attempts} attempts, "
        f"Best: {prog.best_score*100:.0f}%, "
        f"Last: {prog.last_score*100:.0f}%"
    )
    if prog.break_suggested:
        print_info("  ⚠️  Break suggested!")
    if session.next_steps:
        print_info("Next steps:")
        for step in session.next_steps:
            print_info(f"  - {step}")


def print_generate_result(data: dict[str, Any]) -> None:
    """Print generate result."""
    session_id = data["id"]
    print_info(f"Generated session: {session_id}")
    print_info(f"Material: {data['material']}")
    print_info(f"Questions: {data['question_count']}")
    print_info("")
    print_info("Questions:")
    for q in data["questions"]:
        print_info(f"  {q['id']}: {q['prompt']}")
        print_info(f"    Answer: {q['agreed_answer'][:100]}...")
    print_info("")
    print_info(
        f"Next: qnagym refine --session {session_id} "
        f"--comment 'q1:your comment here'  # to refine Q&A"
    )
    print_info(f"      qnagym confirm --session {session_id}  # to lock for practice")


def print_refine_result(data: dict[str, Any]) -> None:
    """Print refine result."""
    session_id = data["id"]
    print_info(f"Refined session: {session_id}")
    print_info(f"Material: {data['material']}")
    print_info("")
    print_info("Questions:")
    for q in data["questions"]:
        print_info(f"  {q['id']}: {q['prompt']}")
        print_info(f"    Answer: {q['agreed_answer'][:100]}...")
        if q["refinement_history"]:
            print_info(f"    Refinements: {len(q['refinement_history'])}")
    print_info("")
    print_info(
        f"Next: qnagym refine --session {session_id} "
        f"--comment 'q1:your comment here'  # more refinements"
    )
    print_info(f"      qnagym confirm --session {session_id}  # lock for practice")


def print_confirm_result(data: dict[str, Any]) -> None:
    """Print confirm result."""
    session_id = data["id"]
    print_info(f"Confirmed session: {session_id}")
    print_info(f"Questions locked: {data['question_count']}")
    print_info("")
    print_info(f"Next: qnagym drill --session {session_id}  # start practicing")


def print_drill_result(data: dict[str, Any], interactive: bool = False) -> None:
    """Print drill result."""
    if data.get("complete"):
        print_info(data.get("message", "Drill complete!"))
        return

    print_info(f"Session: {data['id']} | Progress: {data['progress']}")
    print_info("")
    q = data["question"]
    print_info(f"Question {q['id']}: {q['prompt']}")
    print_info("")
    if interactive:
        print_info("Enter your answer (or 'skip' to skip, 'quit' to exit):")
    else:
        print_info(
            "Use --interactive flag for interactive mode, " "or provide --question-id and --answer"
        )


def print_evaluate_result(
    session: Session,
    evaluations: list[dict[str, Any]],
    next_steps: list[str],
) -> None:
    """Print evaluate result."""
    from qnagym.domain.scoring import calculate_progress_trend, format_score

    print_info(f"Evaluation complete for session: {session.id}")
    print_info("")

    prog = session.progress
    trend = calculate_progress_trend(prog)
    print_info(
        f"Attempt #{prog.attempts} | "
        f"Score: {format_score(prog.last_score)} | "
        f"Best: {format_score(prog.best_score)} {trend}"
    )
    if prog.break_suggested:
        print_info("  ⚠️  Break suggested!")
    print_info("")

    for item in evaluations:
        if not item.get("evaluated"):
            print_info(f"  {item['id']}: Not evaluated")
            continue

        score_pct = item["score"] * 100
        print_info(f"  {item['id']}: {score_pct:.0f}%")
        if item.get("show_confidence"):
            print_info(f"    Confidence: {item['confidence']*100:.0f}%")
        if item.get("feedback"):
            print_info(f"    Feedback: {item['feedback']}")
        if item.get("covered_points"):
            print_info(f"    Covered: {', '.join(item['covered_points'])}")
        if item.get("missed_points"):
            print_info(f"    Missed: {', '.join(item['missed_points'])}")
        if item.get("alternatives"):
            print_info(f"    Alternatives: {', '.join(a['summary'] for a in item['alternatives'])}")
        print_info("")

    if next_steps:
        print_info("Next steps:")
        for step in next_steps:
            print_info(f"  - {step}")

    print_info("")
    print_info(f"Next: qnagym repeat --session {session.id}  # practice again")
    print_info(f"      qnagym reset --session {session.id}   # go back to refine")


def print_progress_result(data: dict[str, Any]) -> None:
    """Print progress/repeat result."""
    print_info(f"Session: {data.get('id', 'N/A')}")
    print_info(f"Attempts: {data['attempts']}")
    print_info(f"Best score: {data['best_score']}")
    print_info(f"Last score: {data['last_score']}")
    print_info(f"Trend: {data['trend']}")
    if data.get("break_suggested"):
        print_info("  ⚠️  Break suggested!")
    if data.get("next_steps"):
        print_info("Next steps:")
        for step in data["next_steps"]:
            print_info(f"  - {step}")

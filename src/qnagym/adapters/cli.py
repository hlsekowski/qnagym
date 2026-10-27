"""CLI adapter (I/O boundary).

Mirrors docs/spec/cli.md.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from qnagym.adapters.client import ModelClient, ModelError
from qnagym.adapters.config import load_config
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
from qnagym.adapters.session_store import SessionStore
from qnagym.contracts.constants import (
    EXIT_CODE_CONFIG_ERROR,
    EXIT_CODE_FLOW_ERROR,
    EXIT_CODE_INPUT_ERROR,
    EXIT_CODE_MODEL_ERROR,
    EXIT_CODE_SUCCESS,
)
from qnagym.services.confirm import confirm_service, get_confirm_display_data
from qnagym.services.drill import drill_service, get_drill_display_data
from qnagym.services.evaluate import (
    evaluate_service,
    get_evaluation_display_data,
    get_next_steps,
)
from qnagym.services.generate import generate_service, get_generate_display_data
from qnagym.services.progress import (
    get_progress_display_data,
    repeat_service,
    reset_service,
)
from qnagym.services.refine import get_refine_display_data, refine_service


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="qnagym",
        description="Knowledge acquisition practice",
    )
    parser.add_argument("--version", action="version", version="qnagym 0.1.0")

    # Global flags
    parser.add_argument("--base-url", help="OpenAI-compatible base URL")
    parser.add_argument("--model", help="Model name")
    parser.add_argument("--api-key", help="API key")
    parser.add_argument("--data-dir", type=Path, help="Session data directory")
    parser.add_argument("--config", type=Path, help="Explicit TOML config file")
    parser.add_argument("--json", action="store_true", help="Output JSON")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # generate
    gen = subparsers.add_parser("generate", help="Generate Q&A from material")
    gen.add_argument("--material", required=True, help="Material/topic/URL to learn")
    gen.add_argument("--questions", type=int, help="Number of questions (overrides duration)")
    gen.add_argument("--duration", type=int, help="Session duration in minutes")
    gen.add_argument("--difficulty", choices=["easy", "medium", "hard"], default="medium")
    gen.add_argument("--language", default="en")

    # refine
    ref = subparsers.add_parser("refine", help="Refine Q&A via comments")
    ref.add_argument("--session", required=True, help="Session ID")
    ref.add_argument("--comment", action="append", help="Comment in format 'qid:comment'")
    ref.add_argument("--question-id", help="Question ID for comment (with --comment)")

    # confirm
    conf = subparsers.add_parser("confirm", help="Confirm Q&A bank for practice")
    conf.add_argument("--session", required=True, help="Session ID")

    # drill
    drl = subparsers.add_parser("drill", help="Practice: hide answers, ask questions")
    drl.add_argument("--session", required=True, help="Session ID")
    drl.add_argument("--question-id", help="Question ID to answer")
    drl.add_argument("--answer", help="Your answer")
    drl.add_argument("--interactive", action="store_true", help="Run interactive drill session")

    # evaluate
    ev = subparsers.add_parser("evaluate", help="Score answers vs agreed answers")
    ev.add_argument("--session", help="Session ID (default: latest)")

    # repeat
    rep = subparsers.add_parser("repeat", help="Repeat practice session")
    rep.add_argument("--session", required=True, help="Session ID")

    # reset
    rst = subparsers.add_parser("reset", help="Reset to prepared state for refinement")
    rst.add_argument("--session", required=True, help="Session ID")

    # list
    lst = subparsers.add_parser("list", help="List saved sessions")
    lst.add_argument("--limit", type=int, default=10, help="Max sessions to show")

    # show
    sh = subparsers.add_parser("show", help="Show session details")
    sh.add_argument("--session", required=True, help="Session ID")

    return parser


def parse_comments(comment_args: list[str] | None, question_id: str | None) -> list[dict[str, str]]:
    """Parse --comment and --question-id into comment dicts."""
    comments = []
    if comment_args:
        for c in comment_args:
            if ":" in c:
                qid, comment = c.split(":", 1)
                comments.append({"question_id": qid.strip(), "comment": comment.strip()})
            elif question_id:
                comments.append({"question_id": question_id, "comment": c})
            else:
                raise ValueError(
                    f"Comment '{c}' needs question ID "
                    f"(use --question-id or 'qid:comment' format)"
                )
    return comments


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Load config
    cli_config = {
        "base_url": args.base_url,
        "model": args.model,
        "api_key": args.api_key,
        "data_dir": args.data_dir,
    }
    try:
        config = load_config(cli_config, args.config)
    except Exception as exc:
        print_error(f"Config error: {exc}")
        return EXIT_CODE_CONFIG_ERROR

    # Initialize adapters
    client = ModelClient(config)
    store = SessionStore(config.data_dir)

    # Handle commands
    try:
        if args.command == "generate":
            session = generate_service(
                client,
                store,
                material=args.material,
                question_count=args.questions,
                duration_minutes=args.duration,
                difficulty=args.difficulty,
                language=args.language,
            )
            if args.json:
                print_json(session.to_dict())
            else:
                print_generate_result(get_generate_display_data(session))
            return EXIT_CODE_SUCCESS

        elif args.command == "refine":
            comments = parse_comments(args.comment, args.question_id)
            session = refine_service(client, store, args.session, comments)
            if args.json:
                print_json(session.to_dict())
            else:
                print_refine_result(get_refine_display_data(session))
            return EXIT_CODE_SUCCESS

        elif args.command == "confirm":
            session = confirm_service(store, args.session)
            if args.json:
                print_json(session.to_dict())
            else:
                print_confirm_result(get_confirm_display_data(session))
            return EXIT_CODE_SUCCESS

        elif args.command == "drill":
            session = drill_service(
                store, args.session, args.question_id, args.answer, args.interactive
            )
            if args.json:
                print_json(session.to_dict())
            elif not args.interactive:
                print_drill_result(get_drill_display_data(session), interactive=False)
            return EXIT_CODE_SUCCESS

        elif args.command == "evaluate":
            session = evaluate_service(client, store, args.session)
            if args.json:
                print_json(session.to_dict())
            else:
                evaluations = get_evaluation_display_data(session)
                next_steps = get_next_steps(session)
                print_evaluate_result(session, evaluations, next_steps)
            return EXIT_CODE_SUCCESS

        elif args.command == "repeat":
            session = repeat_service(store, args.session)
            if args.json:
                print_json(session.to_dict())
            else:
                print_progress_result(get_progress_display_data(session))
            return EXIT_CODE_SUCCESS

        elif args.command == "reset":
            session = reset_service(store, args.session)
            if args.json:
                print_json(session.to_dict())
            else:
                print_info(f"Reset session {session.id} to 'prepared' state for refinement.")
            return EXIT_CODE_SUCCESS

        elif args.command == "list":
            sessions = store.list_all()
            if args.json:
                print_json([s.to_dict() for s in sessions[: args.limit]])
            else:
                print_session_list(sessions, args.limit)
            return EXIT_CODE_SUCCESS

        elif args.command == "show":
            session = store.load(args.session)
            if args.json:
                print_json(session.to_dict())
            else:
                print_session_detail(session)
            return EXIT_CODE_SUCCESS

    except ModelError as exc:
        print_error(exc.message)
        return EXIT_CODE_MODEL_ERROR
    except Exception as exc:
        # FlowError, ValueError, etc.
        print_error(str(exc))
        if isinstance(exc, ValueError | KeyError):
            return EXIT_CODE_INPUT_ERROR
        return EXIT_CODE_FLOW_ERROR

    return EXIT_CODE_SUCCESS


if __name__ == "__main__":
    sys.exit(main())

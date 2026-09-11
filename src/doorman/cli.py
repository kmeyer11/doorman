from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

from doorman.benchmark import default_dataset_path, evaluate, format_report, load_dataset
from doorman.config import Thresholds
from doorman.engine import Doorman, ScanResult, Verdict
from doorman.interactive import ChatSession, load_persona
from doorman.llm.factory import get_provider

_VERDICT_COLOR = {Verdict.ALLOW: "\033[32m", Verdict.FLAG: "\033[33m", Verdict.BLOCK: "\033[31m"}
_RESET = "\033[0m"


def _colorize(verdict: Verdict) -> str:
    label = str(verdict).upper()
    if not sys.stdout.isatty():
        return label
    return f"{_VERDICT_COLOR[verdict]}{label}{_RESET}"


def _print_scan_result(result: ScanResult, *, as_json: bool) -> None:
    if as_json:
        payload = {
            "verdict": str(result.verdict),
            "score": result.score,
            "matches": [
                {"heuristic": m.heuristic, "weight": m.weight, "evidence": m.evidence}
                for m in result.matches
            ],
            "llm_verdict": (
                {
                    "is_injection": result.llm_verdict.is_injection,
                    "confidence": result.llm_verdict.confidence,
                    "category": result.llm_verdict.category,
                    "reasoning": result.llm_verdict.reasoning,
                }
                if result.llm_verdict
                else None
            ),
            "latency_ms": round(result.latency_ms, 2),
        }
        print(json.dumps(payload, indent=2))
        return

    print(f"verdict: {_colorize(result.verdict)}  score: {result.score}  ({result.latency_ms:.1f}ms)")
    for m in result.matches:
        print(f"  - {m.heuristic} (+{m.weight}): {m.evidence}")
    if result.llm_verdict:
        lv = result.llm_verdict
        print(
            f"  - llm_judge: is_injection={lv.is_injection} confidence={lv.confidence:.2f} "
            f"category={lv.category} — {lv.reasoning}"
        )


def cmd_scan(args: argparse.Namespace) -> int:
    text = args.text if args.text is not None else sys.stdin.read()
    judge = get_provider(args.judge, model=args.judge_model, for_chat=False) if args.judge else None
    engine = Doorman(judge=judge, thresholds=Thresholds.from_env())
    result = engine.scan(text)
    _print_scan_result(result, as_json=args.json)
    return 1 if result.blocked else 0


def cmd_benchmark(args: argparse.Namespace) -> int:
    dataset_path = Path(args.dataset) if args.dataset else default_dataset_path()
    rows = load_dataset(dataset_path)

    judge = get_provider(args.judge, model=args.judge_model, for_chat=False) if args.llm else None
    engine = Doorman(judge=judge, thresholds=Thresholds.from_env())

    report = evaluate(rows, engine)
    text = format_report(report)
    print(text)
    if args.out:
        Path(args.out).write_text(text + "\n")
        print(f"\nWrote report to {args.out}")
    return 0


def cmd_chat(args: argparse.Namespace) -> int:
    target = get_provider(args.target_provider, model=args.target_model, for_chat=True)
    judge = (
        get_provider(args.judge_provider, model=args.judge_model, for_chat=False)
        if args.judge_provider
        else None
    )
    persona = load_persona(args.persona)

    session = ChatSession(
        target=target,
        judge=judge,
        persona=persona,
        protection=not args.no_protection,
        verbose=args.verbose,
        thresholds=Thresholds.from_env(),
    )
    session.run()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="doorman", description="Prompt injection detection toolkit")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan", help="Scan a single message for prompt injection")
    scan.add_argument("text", nargs="?", help="Text to scan (reads stdin if omitted)")
    scan.add_argument("--judge", choices=["anthropic", "openai", "gemini"], default=None, help="Enable an LLM judge")
    scan.add_argument("--judge-model", default=None, help="Override the judge model")
    scan.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    scan.set_defaults(func=cmd_scan)

    benchmark = subparsers.add_parser("benchmark", help="Run the curated benchmark dataset")
    benchmark.add_argument("--dataset", default=None, help="Path to a JSONL dataset")
    benchmark.add_argument("--llm", action="store_true", help="Also use an LLM judge (needs an API key)")
    benchmark.add_argument("--judge", choices=["anthropic", "openai", "gemini"], default="anthropic")
    benchmark.add_argument("--judge-model", default=None)
    benchmark.add_argument("--out", default=None, help="Write the report to this file too")
    benchmark.set_defaults(func=cmd_benchmark)

    chat = subparsers.add_parser("chat", help="Interactive red-team REPL against a live target LLM")
    chat.add_argument("--target-provider", default="anthropic", choices=["anthropic", "openai", "gemini"])
    chat.add_argument("--target-model", default=None)
    chat.add_argument("--judge-provider", default="anthropic", choices=["anthropic", "openai", "gemini", "none"])
    chat.add_argument("--judge-model", default=None)
    chat.add_argument("--persona", default=None, help="Path to a persona system prompt (default: built-in support bot)")
    chat.add_argument("--no-protection", action="store_true", help="Start with Doorman screening disabled")
    chat.add_argument("--verbose", action="store_true", help="Always show the full score breakdown")
    chat.set_defaults(func=cmd_chat)

    return parser


def main(argv: list[str] | None = None) -> int:
    # Load API keys (and any DOORMAN_* config) from a .env file in or above the cwd, without
    # overriding variables already set in the real environment.
    load_dotenv(find_dotenv(usecwd=True))

    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "command", None) == "chat" and args.judge_provider == "none":
        args.judge_provider = None
    try:
        return args.func(args)
    except Exception as exc:  # noqa: BLE001 - CLI boundary: show a clean message, not a traceback
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

from collections.abc import Callable

from doorman.heuristics import delimiter_injection, exfiltration, instruction_override, obfuscation
from doorman.heuristics.base import HeuristicMatch

_CHECKS: list[Callable[[str], list[HeuristicMatch]]] = [
    instruction_override.check,
    delimiter_injection.check,
    obfuscation.check,
    exfiltration.check,
]


def run_all(text: str) -> list[HeuristicMatch]:
    matches: list[HeuristicMatch] = []
    for check in _CHECKS:
        matches.extend(check(text))
    return matches


def score(matches: list[HeuristicMatch]) -> int:
    return min(100, sum(m.weight for m in matches))

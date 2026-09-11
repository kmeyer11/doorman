from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class HeuristicMatch:
    heuristic: str
    weight: int
    evidence: str


# (compiled pattern, weight, label) triples shared by the pattern-based heuristics.
Pattern = tuple[re.Pattern, int, str]


def compile_patterns(specs: list[tuple[str, int, str]]) -> list[Pattern]:
    return [(re.compile(pattern, re.IGNORECASE), weight, label) for pattern, weight, label in specs]


def scan_patterns(text: str, patterns: list[Pattern], *, max_evidence: int = 60) -> list[HeuristicMatch]:
    matches: list[HeuristicMatch] = []
    for pattern, weight, label in patterns:
        found = pattern.search(text)
        if found:
            evidence = found.group(0).strip()
            if len(evidence) > max_evidence:
                evidence = evidence[:max_evidence] + "..."
            matches.append(HeuristicMatch(heuristic=label, weight=weight, evidence=evidence))
    return matches

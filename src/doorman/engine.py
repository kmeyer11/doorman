from __future__ import annotations

import time
from dataclasses import dataclass
from enum import IntEnum

from doorman.config import Thresholds
from doorman.heuristics.base import HeuristicMatch
from doorman.heuristics.registry import run_all, score
from doorman.llm.base import LLMProvider, LLMVerdict


class Verdict(IntEnum):
    ALLOW = 0
    FLAG = 1
    BLOCK = 2

    def __str__(self) -> str:
        return self.name.lower()


@dataclass(frozen=True)
class ScanResult:
    text: str
    verdict: Verdict
    score: int
    matches: list[HeuristicMatch]
    llm_verdict: LLMVerdict | None = None
    latency_ms: float = 0.0

    @property
    def blocked(self) -> bool:
        return self.verdict is Verdict.BLOCK


def _verdict_for_score(value: int, thresholds: Thresholds) -> Verdict:
    if value >= thresholds.block:
        return Verdict.BLOCK
    if value >= thresholds.flag:
        return Verdict.FLAG
    return Verdict.ALLOW


def _verdict_for_llm(verdict: LLMVerdict) -> Verdict:
    if not verdict.is_injection:
        return Verdict.ALLOW
    return Verdict.BLOCK if verdict.confidence >= 0.7 else Verdict.FLAG


class Doorman:
    """Screens text for prompt injection attempts using heuristics, and optionally an LLM judge."""

    def __init__(self, judge: LLMProvider | None = None, thresholds: Thresholds | None = None):
        self.judge = judge
        self.thresholds = thresholds or Thresholds.from_env()

    def scan(self, text: str) -> ScanResult:
        start = time.perf_counter()

        matches = run_all(text)
        heuristic_score = score(matches)
        verdict = _verdict_for_score(heuristic_score, self.thresholds)

        llm_verdict = None
        if self.judge is not None:
            llm_verdict = self.judge.classify(text)
            verdict = max(verdict, _verdict_for_llm(llm_verdict))

        latency_ms = (time.perf_counter() - start) * 1000
        return ScanResult(
            text=text,
            verdict=verdict,
            score=heuristic_score,
            matches=matches,
            llm_verdict=llm_verdict,
            latency_ms=latency_ms,
        )

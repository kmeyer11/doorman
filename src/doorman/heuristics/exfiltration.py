from __future__ import annotations

from doorman.heuristics.base import HeuristicMatch, compile_patterns, scan_patterns

# Attempts to make the model leak its own system prompt, hidden instructions, or config
# rather than override its behavior outright.
_SPECS: list[tuple[str, int, str]] = [
    (r"\brepeat\s+(your|the)\s+(system\s+prompt|instructions|initial\s+prompt)\b", 40, "prompt_exfiltration"),
    (r"\bprint\s+(your|the)\s+(system\s+prompt|instructions|configuration)\b", 40, "prompt_exfiltration"),
    (r"\bwhat\s+(is|are)\s+your\s+(system\s+prompt|instructions|rules|guidelines)\b", 30, "prompt_exfiltration"),
    (r"\breveal\s+(your|the)\s+(system\s+prompt|hidden\s+instructions|configuration)\b", 40, "prompt_exfiltration"),
    (r"\bshow\s+me\s+your\s+(system\s+prompt|guidelines|rules|instructions)\b", 30, "prompt_exfiltration"),
    (r"\boutput\s+everything\s+(above|before)\s+this\s+(line|message|point)\b", 35, "prompt_exfiltration"),
    (r"\brepeat\s+everything\s+(in|from)\s+your\s+(context|system\s+message)\s+verbatim\b", 40, "prompt_exfiltration"),
    (r"\bwhat\s+were\s+you\s+told\s+(not\s+to\s+(say|do)|before\s+this)\b", 25, "prompt_exfiltration"),
]

_PATTERNS = compile_patterns(_SPECS)


def check(text: str) -> list[HeuristicMatch]:
    return scan_patterns(text, _PATTERNS)

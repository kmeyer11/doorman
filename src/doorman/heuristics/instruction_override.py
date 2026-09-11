from __future__ import annotations

from doorman.heuristics.base import HeuristicMatch, compile_patterns, scan_patterns

# Plain-text phrases that signal an override/jailbreak attempt. Kept separate from the
# regex patterns below so heuristics/obfuscation.py can reuse them for fuzzy/leetspeak matching.
TRIGGER_PHRASES: list[str] = [
    "ignore previous instructions",
    "ignore all previous instructions",
    "ignore the above instructions",
    "disregard previous instructions",
    "disregard all prior instructions",
    "forget your instructions",
    "forget everything you were told",
    "you are now dan",
    "do anything now",
    "developer mode",
    "no restrictions",
    "without restrictions",
    "jailbreak",
]

_SPECS: list[tuple[str, int, str]] = [
    (r"\bignore\s+(all\s+)?(the\s+)?(previous|prior|above|earlier)\s+(instructions?|rules?|prompts?)\b", 40, "instruction_override"),
    (r"\bdisregard\s+(all\s+)?(the\s+)?(previous|prior|above|earlier)\s+(instructions?|rules?|prompts?)\b", 40, "instruction_override"),
    (r"\bforget\s+(everything|all)\s+(you\s+(were|have\s+been)\s+told|your\s+instructions)\b", 40, "instruction_override"),
    (r"\b(new|updated)\s+instructions?\s*[:\-]", 25, "instruction_reframe"),
    (r"\bfrom\s+now\s+on,?\s+you\s+(will|must|are)\b", 20, "instruction_reframe"),
    (r"\byour\s+new\s+(persona|role|identity|directive)s?\s+is\b", 25, "instruction_reframe"),
    (r"\byou\s+are\s+now\s+(dan|in\s+developer\s+mode|an?\s+unrestricted\s+ai)\b", 45, "roleplay_jailbreak"),
    (r"\bact\s+as\s+(dan|an?\s+ai\s+(with\s+no|without)\s+(restrictions|filters|guidelines|rules))\b", 45, "roleplay_jailbreak"),
    (r"\bpretend\s+(you\s+have\s+no|to\s+have\s+no)\s+(restrictions|filters|guidelines|rules)\b", 40, "roleplay_jailbreak"),
    (r"\bdo\s+anything\s+now\b", 35, "roleplay_jailbreak"),
    (r"\benable\s+developer\s+mode\b", 35, "roleplay_jailbreak"),
    (r"\bstay\s+in\s+character\s+no\s+matter\s+what\b", 30, "roleplay_jailbreak"),
    (r"\bwithout\s+any\s+(restrictions|limitations|filters|censorship)\b", 25, "roleplay_jailbreak"),
    (r"\bjailbreak(ing)?\b", 20, "roleplay_jailbreak"),
    (r"\btranslate\s+the\s+following.{0,40}(and\s+then\s+|then\s+)?(execute|follow|obey|do\s+it|run\s+it)\b", 35, "translation_trick"),
    (r"\brespond\s+only\s+in\s+.{0,20}\s+and\s+ignore\b", 30, "translation_trick"),
]

_PATTERNS = compile_patterns(_SPECS)


def check(text: str) -> list[HeuristicMatch]:
    return scan_patterns(text, _PATTERNS)

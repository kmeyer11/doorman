from __future__ import annotations

from doorman.heuristics.base import HeuristicMatch, compile_patterns, scan_patterns

# Fake role/delimiter markers used to smuggle a spoofed system or assistant turn into
# what looks like plain user input, tricking the model into treating it as privileged.
_SPECS: list[tuple[str, int, str]] = [
    (r"\[\s*/?\s*system\s*\]", 35, "fake_system_delimiter"),
    (r"\[\s*/?\s*(admin|root|developer)\s*\]", 30, "fake_privileged_delimiter"),
    (r"<\s*\|?\s*/?\s*(system|im_start|im_end)\s*\|?\s*>", 35, "fake_chat_template_token"),
    (r"<\s*/?\s*(system|admin|root)\s*>", 30, "fake_xml_role_tag"),
    (r"^\s*#{2,3}\s*system\b", 25, "fake_markdown_role_header"),
    (r"^\s*-{2,}\s*system\s*-{2,}\s*$", 25, "fake_markdown_role_header"),
    (r"^\s*system\s*:\s*\S", 25, "fake_role_prefix"),
    (r"^\s*assistant\s*:\s*\S", 20, "fake_role_prefix"),
    (r"\bend\s+of\s+(system\s+)?prompt\b", 20, "fake_prompt_boundary"),
]

_PATTERNS = compile_patterns(_SPECS)


def check(text: str) -> list[HeuristicMatch]:
    matches = scan_patterns(text, _PATTERNS)
    # Multiple distinct role prefixes (system:, user:, assistant:) in one message is a
    # strong signal of a forged transcript being smuggled in, independent of any single match.
    role_prefixes = {"system", "user", "assistant"} & {
        line.split(":", 1)[0].strip().lower()
        for line in text.splitlines()
        if ":" in line and len(line.split(":", 1)[0].strip().split()) == 1
    }
    if len(role_prefixes) >= 2:
        matches.append(
            HeuristicMatch(
                heuristic="forged_transcript",
                weight=30,
                evidence=f"multiple role prefixes found: {', '.join(sorted(role_prefixes))}",
            )
        )
    return matches

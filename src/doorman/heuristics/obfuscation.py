from __future__ import annotations

import base64
import re
import unicodedata

from doorman.heuristics.base import HeuristicMatch

# Single "loaded" words worth catching even when disguised with leetspeak or spacing.
# Multi-word override phrases are already covered verbatim by instruction_override.py;
# de-obfuscating a whole phrase is unreliable, but de-obfuscating single words is precise
# enough to be a useful, if weaker, signal.
WORD_TRIGGERS = {
    "ignore",
    "disregard",
    "override",
    "bypass",
    "jailbreak",
    "unrestricted",
    "dan",
}

_LEET_MAP = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s"})

# Zero-width space, ZWNJ, ZWJ, word joiner, BOM, soft hyphen.
_ZERO_WIDTH_CHARS = '\u200b\u200c\u200d\u2060\ufeff\xad'

_BASE64_BLOB_RE = re.compile(r"(?<![A-Za-z0-9+/=])[A-Za-z0-9+/]{40,}={0,2}(?![A-Za-z0-9+/=])")
_SUSPICIOUS_DECODED = re.compile(
    r"\b(ignore|disregard|instructions?|system prompt|override|password|api[_ ]?key|secret)\b",
    re.IGNORECASE,
)
_SPACED_WORD_RE = re.compile(r"\b(?:\w[\s\-_.]+){3,}\w\b")


def _decode_base64_blob(blob: str) -> str | None:
    padded = blob + "=" * (-len(blob) % 4)
    try:
        raw = base64.b64decode(padded, validate=True)
    except (ValueError, base64.binascii.Error):
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _check_base64(text: str) -> list[HeuristicMatch]:
    matches = []
    for blob_match in _BASE64_BLOB_RE.finditer(text):
        blob = blob_match.group(0)
        decoded = _decode_base64_blob(blob)
        if decoded is None:
            continue
        printable_ratio = sum(c.isprintable() or c.isspace() for c in decoded) / max(len(decoded), 1)
        if printable_ratio < 0.9:
            continue
        if _SUSPICIOUS_DECODED.search(decoded):
            matches.append(
                HeuristicMatch(
                    heuristic="base64_hidden_instructions",
                    weight=45,
                    evidence=f"decodes to: {decoded[:60]!r}",
                )
            )
        else:
            matches.append(
                HeuristicMatch(
                    heuristic="base64_blob",
                    weight=10,
                    evidence=f"{blob[:20]}...",
                )
            )
    return matches


def _check_zero_width(text: str) -> list[HeuristicMatch]:
    count = sum(text.count(ch) for ch in _ZERO_WIDTH_CHARS)
    if count == 0:
        return []
    return [
        HeuristicMatch(
            heuristic="invisible_unicode",
            weight=min(40, 15 + count * 2),
            evidence=f"{count} zero-width/invisible character(s) found",
        )
    ]


def _check_homoglyphs(text: str) -> list[HeuristicMatch]:
    for word in re.findall(r"\w+", text, flags=re.UNICODE):
        has_latin = any("LATIN" in unicodedata.name(c, "") for c in word)
        has_cyrillic = any("CYRILLIC" in unicodedata.name(c, "") for c in word)
        if has_latin and has_cyrillic:
            return [
                HeuristicMatch(
                    heuristic="homoglyph_mixing",
                    weight=30,
                    evidence=f"mixed Latin/Cyrillic characters in {word!r}",
                )
            ]
    return []


def _normalize_leet(token: str) -> str:
    return token.lower().translate(_LEET_MAP)


def _check_leet_and_spacing(text: str) -> list[HeuristicMatch]:
    matches = []
    # Leetspeak substitution within otherwise normal words, e.g. "1gn0re".
    for word in re.findall(r"[\w@$]+", text):
        if _normalize_leet(word) in WORD_TRIGGERS and word.lower() not in WORD_TRIGGERS:
            matches.append(
                HeuristicMatch(heuristic="leetspeak_evasion", weight=20, evidence=word)
            )
    # Letter-by-letter spacing evasion, e.g. "i-g-n-o-r-e" or "i g n o r e".
    for spaced in _SPACED_WORD_RE.finditer(text):
        collapsed = re.sub(r"[\s\-_.]", "", spaced.group(0)).lower()
        if collapsed in WORD_TRIGGERS:
            matches.append(
                HeuristicMatch(heuristic="spacing_evasion", weight=25, evidence=spaced.group(0))
            )
    return matches


def check(text: str) -> list[HeuristicMatch]:
    return [
        *_check_base64(text),
        *_check_zero_width(text),
        *_check_homoglyphs(text),
        *_check_leet_and_spacing(text),
    ]

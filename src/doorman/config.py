from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_FLAG_THRESHOLD = 25
DEFAULT_BLOCK_THRESHOLD = 60

DEFAULT_ANTHROPIC_JUDGE_MODEL = "claude-haiku-4-5-20251001"
DEFAULT_ANTHROPIC_CHAT_MODEL = "claude-sonnet-5"
DEFAULT_OPENAI_JUDGE_MODEL = "gpt-4o-mini"
DEFAULT_OPENAI_CHAT_MODEL = "gpt-4o-mini"


@dataclass(frozen=True)
class Thresholds:
    flag: int = DEFAULT_FLAG_THRESHOLD
    block: int = DEFAULT_BLOCK_THRESHOLD

    @classmethod
    def from_env(cls) -> Thresholds:
        return cls(
            flag=int(os.environ.get("DOORMAN_FLAG_THRESHOLD", DEFAULT_FLAG_THRESHOLD)),
            block=int(os.environ.get("DOORMAN_BLOCK_THRESHOLD", DEFAULT_BLOCK_THRESHOLD)),
        )


def default_judge_model(provider: str) -> str:
    return {
        "anthropic": DEFAULT_ANTHROPIC_JUDGE_MODEL,
        "openai": DEFAULT_OPENAI_JUDGE_MODEL,
    }[provider]


def default_chat_model(provider: str) -> str:
    return {
        "anthropic": DEFAULT_ANTHROPIC_CHAT_MODEL,
        "openai": DEFAULT_OPENAI_CHAT_MODEL,
    }[provider]

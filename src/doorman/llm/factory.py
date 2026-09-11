from __future__ import annotations

import os

from doorman.config import GEMINI_BASE_URL, default_chat_model, default_judge_model
from doorman.llm.base import LLMProvider

_ALIASES = {
    "anthropic": "anthropic",
    "claude": "anthropic",
    "openai": "openai",
    "gpt": "openai",
    "gemini": "gemini",
    "google": "gemini",
}


def _resolve_name(name: str) -> str:
    try:
        return _ALIASES[name.lower()]
    except KeyError:
        raise ValueError(
            f"Unknown provider {name!r}. Choose one of: anthropic, openai, gemini."
        ) from None


def get_provider(name: str, model: str | None = None, *, for_chat: bool = False) -> LLMProvider:
    """Build an LLMProvider by name, importing its SDK lazily.

    `for_chat` picks a sensible default model when `model` is omitted: judges default to a
    fast/cheap model, chat targets default to a stronger conversational one.

    'gemini' uses Google AI Studio's free-tier, OpenAI-compatible endpoint, so it's built on
    the same OpenAIProvider as 'openai' rather than a separate SDK.
    """
    provider = _resolve_name(name)
    resolved_model = model or (default_chat_model(provider) if for_chat else default_judge_model(provider))

    if provider == "anthropic":
        try:
            from doorman.llm.anthropic_provider import AnthropicProvider
        except ImportError as exc:
            raise ImportError(str(exc)) from exc
        return AnthropicProvider(model=resolved_model)

    try:
        from doorman.llm.openai_provider import OpenAIProvider
    except ImportError as exc:
        raise ImportError(str(exc)) from exc

    if provider == "gemini":
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set. Get a free key from https://aistudio.google.com/apikey "
                "and add it to .env."
            )
        return OpenAIProvider(model=resolved_model, api_key=api_key, base_url=GEMINI_BASE_URL, name="gemini")

    return OpenAIProvider(model=resolved_model, name="openai")

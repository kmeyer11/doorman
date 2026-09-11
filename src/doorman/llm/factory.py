from __future__ import annotations

from doorman.config import default_chat_model, default_judge_model
from doorman.llm.base import LLMProvider

_ALIASES = {
    "anthropic": "anthropic",
    "claude": "anthropic",
    "openai": "openai",
    "gpt": "openai",
}


def _resolve_name(name: str) -> str:
    try:
        return _ALIASES[name.lower()]
    except KeyError:
        raise ValueError(
            f"Unknown provider {name!r}. Choose one of: anthropic, openai."
        ) from None


def get_provider(name: str, model: str | None = None, *, for_chat: bool = False) -> LLMProvider:
    """Build an LLMProvider by name, importing its SDK lazily.

    `for_chat` picks a sensible default model when `model` is omitted: judges default to a
    fast/cheap model, chat targets default to a stronger conversational one.
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
    return OpenAIProvider(model=resolved_model)

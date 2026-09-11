from __future__ import annotations

import pytest
from fakes import FakeProvider

from doorman.llm.base import LLMVerdict, Message
from doorman.llm.factory import _resolve_name, get_provider


def test_fake_provider_records_calls():
    provider = FakeProvider(reply="hi")
    verdict = provider.classify("some text")
    reply = provider.chat([Message("user", "hello")], system="be nice")

    assert verdict.is_injection is False
    assert reply == "hi"
    assert provider.classify_calls == ["some text"]
    assert provider.chat_calls == [([Message("user", "hello")], "be nice")]


def test_llm_verdict_is_a_plain_dataclass():
    verdict = LLMVerdict(is_injection=True, confidence=0.9, category="jailbreak", reasoning="because")
    assert verdict.is_injection is True
    assert verdict.confidence == 0.9


@pytest.mark.parametrize(
    "alias, expected",
    [("anthropic", "anthropic"), ("claude", "anthropic"), ("ANTHROPIC", "anthropic"),
     ("openai", "openai"), ("gpt", "openai"), ("gemini", "gemini"), ("google", "gemini")],
)
def test_provider_aliases_resolve_to_canonical_names(alias, expected):
    assert _resolve_name(alias) == expected


def test_unknown_provider_raises_value_error():
    with pytest.raises(ValueError, match="Unknown provider"):
        get_provider("bogus-provider")


def test_gemini_without_api_key_raises_a_helpful_error(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with pytest.raises(ValueError, match="GEMINI_API_KEY is not set"):
        get_provider("gemini")


def test_gemini_uses_its_openai_compatible_endpoint(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key-for-test")
    provider = get_provider("gemini")
    assert provider.name == "gemini"
    assert "generativelanguage.googleapis.com" in str(provider._client.base_url)

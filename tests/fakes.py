from __future__ import annotations

from doorman.llm.base import LLMProvider, LLMVerdict, Message


class FakeProvider(LLMProvider):
    """A network-free stand-in for a real provider, used across the test suite."""

    def __init__(
        self,
        name: str = "fake",
        model: str = "fake-model",
        verdict: LLMVerdict | None = None,
        reply: str = "Hello from the fake target.",
    ):
        self.name = name
        self.model = model
        self._verdict = verdict or LLMVerdict(
            is_injection=False, confidence=0.0, category="benign", reasoning="fake: looks benign"
        )
        self._reply = reply
        self.classify_calls: list[str] = []
        self.chat_calls: list[tuple[list[Message], str | None]] = []

    def classify(self, text: str) -> LLMVerdict:
        self.classify_calls.append(text)
        return self._verdict

    def chat(self, messages: list[Message], system: str | None = None) -> str:
        self.chat_calls.append((list(messages), system))
        return self._reply

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class LLMVerdict:
    is_injection: bool
    confidence: float  # 0.0-1.0
    category: str
    reasoning: str


@dataclass(frozen=True)
class Message:
    role: str  # "user" | "assistant"
    content: str


class LLMProvider(ABC):
    """A provider can act as a judge (classify) and/or as the target chatbot (chat)."""

    name: str
    model: str

    @abstractmethod
    def classify(self, text: str) -> LLMVerdict:
        """Ask the model whether `text` is a prompt injection attempt."""

    @abstractmethod
    def chat(self, messages: list[Message], system: str | None = None) -> str:
        """Send a conversation to the model and return its reply text."""

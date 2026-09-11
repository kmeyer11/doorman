from __future__ import annotations

from doorman.llm.base import LLMProvider, LLMVerdict, Message
from doorman.llm.prompts import JUDGE_SYSTEM_PROMPT, JUDGE_TOOL_SCHEMA

try:
    import anthropic
except ImportError as exc:  # pragma: no cover - exercised via factory.get_provider
    raise ImportError(
        "The 'anthropic' package is required for the Anthropic provider. "
        "Install it with: pip install doorman[anthropic]"
    ) from exc


class AnthropicProvider(LLMProvider):
    def __init__(self, model: str, api_key: str | None = None):
        self.name = "anthropic"
        self.model = model
        self._client = anthropic.Anthropic(api_key=api_key)

    def classify(self, text: str) -> LLMVerdict:
        response = self._client.messages.create(
            model=self.model,
            max_tokens=512,
            system=JUDGE_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": text}],
            tools=[JUDGE_TOOL_SCHEMA],
            tool_choice={"type": "tool", "name": "report_verdict"},
        )
        for block in response.content:
            if block.type == "tool_use":
                verdict = block.input
                return LLMVerdict(
                    is_injection=bool(verdict["is_injection"]),
                    confidence=float(verdict["confidence"]),
                    category=str(verdict["category"]),
                    reasoning=str(verdict["reasoning"]),
                )
        raise RuntimeError("Anthropic judge did not return a tool_use verdict block")

    def chat(self, messages: list[Message], system: str | None = None) -> str:
        response = self._client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system or anthropic.NOT_GIVEN,
            messages=[{"role": m.role, "content": m.content} for m in messages],
        )
        return "".join(block.text for block in response.content if block.type == "text")

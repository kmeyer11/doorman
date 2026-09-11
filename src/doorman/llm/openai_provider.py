from __future__ import annotations

import json

from doorman.llm.base import LLMProvider, LLMVerdict, Message
from doorman.llm.prompts import JUDGE_SYSTEM_PROMPT, JUDGE_TOOL_SCHEMA

try:
    import openai
except ImportError as exc:  # pragma: no cover - exercised via factory.get_provider
    raise ImportError(
        "The 'openai' package is required for the OpenAI provider. "
        "Install it with: pip install doorman[openai]"
    ) from exc

_JUDGE_TOOL = {
    "type": "function",
    "function": {
        "name": JUDGE_TOOL_SCHEMA["name"],
        "description": JUDGE_TOOL_SCHEMA["description"],
        "parameters": JUDGE_TOOL_SCHEMA["input_schema"],
    },
}


class OpenAIProvider(LLMProvider):
    def __init__(self, model: str, api_key: str | None = None):
        self.name = "openai"
        self.model = model
        self._client = openai.OpenAI(api_key=api_key)

    def classify(self, text: str) -> LLMVerdict:
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            tools=[_JUDGE_TOOL],
            tool_choice={"type": "function", "function": {"name": "report_verdict"}},
        )
        tool_calls = response.choices[0].message.tool_calls
        if not tool_calls:
            raise RuntimeError("OpenAI judge did not return a tool call verdict")
        verdict = json.loads(tool_calls[0].function.arguments)
        return LLMVerdict(
            is_injection=bool(verdict["is_injection"]),
            confidence=float(verdict["confidence"]),
            category=str(verdict["category"]),
            reasoning=str(verdict["reasoning"]),
        )

    def chat(self, messages: list[Message], system: str | None = None) -> str:
        chat_messages = []
        if system:
            chat_messages.append({"role": "system", "content": system})
        chat_messages.extend({"role": m.role, "content": m.content} for m in messages)
        response = self._client.chat.completions.create(model=self.model, messages=chat_messages)
        return response.choices[0].message.content or ""

from __future__ import annotations

import importlib.resources
from pathlib import Path

from doorman.config import Thresholds
from doorman.engine import Doorman, ScanResult, Verdict
from doorman.llm.base import LLMProvider, Message
from doorman.llm.factory import get_provider

DEFAULT_PERSONA_FILE = "support_bot.md"

HELP_TEXT = """\
Commands:
  /provider <anthropic|openai>   swap the target chatbot's provider
  /model <name>                  swap the target chatbot's model
  /judge <anthropic|openai|none> swap (or disable) the judge provider
  /judge-model <name>            swap the judge model
  /protection <on|off>           toggle Doorman screening
  /persona <path>                load a different target system prompt
  /verbose <on|off>              show full heuristic/LLM score breakdown
  /reset                         clear the target conversation history
  /help                          show this message
  /quit                          exit\
"""


def load_persona(path: str | Path | None = None) -> str:
    if path is None:
        return importlib.resources.files("doorman.personas").joinpath(DEFAULT_PERSONA_FILE).read_text()
    return Path(path).read_text()


class ChatSession:
    """Drives one interactive red-team conversation: every line is screened by `engine`
    before being forwarded to `target`, mirroring how Doorman would sit in front of a real
    chatbot in production."""

    def __init__(
        self,
        target: LLMProvider,
        judge: LLMProvider | None,
        persona: str,
        *,
        protection: bool = True,
        verbose: bool = False,
        thresholds: Thresholds | None = None,
    ):
        self.target = target
        self.judge = judge
        self.persona = persona
        self.protection = protection
        self.verbose = verbose
        self.history: list[Message] = []
        self.thresholds = thresholds or Thresholds.from_env()
        self.engine = Doorman(judge=judge, thresholds=self.thresholds)

    def _rebuild_engine(self) -> None:
        self.engine = Doorman(judge=self.judge, thresholds=self.thresholds)

    def handle_command(self, line: str) -> str:
        parts = line[1:].split(maxsplit=1)
        cmd = parts[0].lower() if parts else ""
        arg = parts[1].strip() if len(parts) > 1 else ""

        if cmd in ("provider", "model", "judge", "judge-model") and not arg:
            return f"Usage: /{cmd} <value>"

        try:
            if cmd == "provider":
                self.target = get_provider(arg, model=None, for_chat=True)
                return f"Target provider switched to {self.target.name} ({self.target.model})"
            if cmd == "model":
                self.target = get_provider(self.target.name, model=arg, for_chat=True)
                return f"Target model switched to {self.target.model}"
            if cmd == "judge":
                if arg.lower() == "none":
                    self.judge = None
                else:
                    self.judge = get_provider(arg, model=None, for_chat=False)
                self._rebuild_engine()
                return f"Judge switched to {arg}"
            if cmd == "judge-model":
                if self.judge is None:
                    return "No judge is active. Use /judge <provider> first."
                self.judge = get_provider(self.judge.name, model=arg, for_chat=False)
                self._rebuild_engine()
                return f"Judge model switched to {self.judge.model}"
        except (ValueError, ImportError) as exc:
            return f"[error] {exc}"

        if cmd == "protection":
            self.protection = arg.lower() != "off"
            return f"Protection {'ON' if self.protection else 'OFF'}"
        if cmd == "verbose":
            self.verbose = arg.lower() != "off"
            return f"Verbose {'ON' if self.verbose else 'OFF'}"
        if cmd == "persona":
            try:
                self.persona = load_persona(arg or None)
            except OSError as exc:
                return f"[error] could not load persona: {exc}"
            return "Persona loaded."
        if cmd == "reset":
            self.history = []
            return "Conversation history cleared."
        if cmd in ("help", "?"):
            return HELP_TEXT
        if cmd in ("quit", "exit"):
            raise SystemExit
        return f"Unknown command: /{cmd}. Type /help for a list."

    def _format_result(self, result: ScanResult) -> str:
        lines = [f"[doorman] verdict={result.verdict} score={result.score}"]
        for m in result.matches:
            lines.append(f"  - {m.heuristic} (+{m.weight}): {m.evidence}")
        if result.llm_verdict:
            lv = result.llm_verdict
            lines.append(
                f"  - llm_judge: is_injection={lv.is_injection} confidence={lv.confidence:.2f} "
                f"category={lv.category} — {lv.reasoning}"
            )
        return "\n".join(lines)

    def process_line(self, line: str) -> str:
        """Process one line of user input and return text to display. Raises SystemExit on /quit."""
        if line.startswith("/"):
            return self.handle_command(line)

        summary = ""
        if self.protection:
            try:
                result = self.engine.scan(line)
            except Exception as exc:  # noqa: BLE001 - REPL boundary: surface any SDK error, don't crash
                return f"[error] judge failed: {exc}\nTip: /judge none or /protection off."
            if self.verbose or result.verdict is not Verdict.ALLOW:
                summary = self._format_result(result)
            if result.verdict is Verdict.BLOCK:
                return f"[doorman] BLOCKED — message was not forwarded to the target.\n{summary}"

        self.history.append(Message("user", line))
        try:
            reply = self.target.chat(self.history, system=self.persona)
        except Exception as exc:  # noqa: BLE001 - REPL boundary: surface any SDK error, don't crash
            self.history.pop()
            prefix = f"{summary}\n" if summary else ""
            return f"{prefix}[error] target chat failed: {exc}"
        self.history.append(Message("assistant", reply))

        prefix = f"{summary}\n" if summary else ""
        return f"{prefix}bot> {reply}"

    def run(self) -> None:
        print(
            f"Doorman interactive red-team mode. Target: {self.target.name}/{self.target.model}. "
            "Type /help for commands.\n"
        )
        while True:
            try:
                line = input("you> ")
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not line.strip():
                continue
            try:
                output = self.process_line(line)
            except SystemExit:
                break
            if output:
                print(output)

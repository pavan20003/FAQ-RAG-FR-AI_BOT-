"""Small Claude client wrapper and deterministic offline fake."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

from app.config import Settings, get_settings


@dataclass(frozen=True)
class LLMResponse:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0


class LLMClient(Protocol):
    def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse: ...


class ClaudeLLM:
    """Call Claude with configured timeout, retry count, and output cap."""

    def __init__(self, settings: Settings | None = None) -> None:
        settings = settings or get_settings()
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is required; pass --fake-llm for an offline run")
        if not settings.claude_model:
            raise RuntimeError("CLAUDE_MODEL must be set in the environment")

        from anthropic import Anthropic

        self.model = settings.claude_model
        self.max_tokens = settings.claude_max_tokens
        self.client = Anthropic(
            api_key=settings.anthropic_api_key,
            timeout=settings.claude_timeout_seconds,
            max_retries=settings.claude_max_retries,
        )

    def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = "\n".join(block.text for block in response.content if getattr(block, "type", None) == "text")
        return LLMResponse(
            text=text,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )


class FakeLLM:
    """Return a fixed French answer citing the passage IDs in the prompt."""

    def __init__(self) -> None:
        self.calls = 0
        self.last_system_prompt = ""
        self.last_user_prompt = ""

    def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        self.calls += 1
        self.last_system_prompt = system_prompt
        self.last_user_prompt = user_prompt
        passage_ids = re.findall(r'<passage\s+id="(\d+)"', user_prompt)
        citations = " ".join(f"[{passage_id}]" for passage_id in passage_ids)
        if not citations:
            return LLMResponse("Je ne trouve pas cette information dans les passages disponibles.")
        return LLMResponse(f"D'après les informations disponibles, consultez le passage {citations}.")


def get_llm(*, fake: bool = False) -> LLMClient:
    """Create the explicit offline fake or the configured real client."""
    return FakeLLM() if fake else ClaudeLLM()

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


class GeminiLLM:
    """Call the Gemini Developer API with bounded output, timeout, and retries."""

    def __init__(self, settings: Settings | None = None) -> None:
        settings = settings or get_settings()
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini")
        if not settings.gemini_model:
            raise RuntimeError("GEMINI_MODEL must be set when LLM_PROVIDER=gemini")

        from google import genai
        from google.genai import types

        self.model = settings.gemini_model
        self.max_tokens = settings.claude_max_tokens
        self.types = types
        self.client = genai.Client(
            api_key=settings.gemini_api_key,
            http_options=types.HttpOptions(
                timeout=int(settings.claude_timeout_seconds * 1000),
                retry_options=types.HttpRetryOptions(attempts=settings.claude_max_retries + 1),
            ),
        )

    def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        response = self.client.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config=self.types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=self.max_tokens,
                temperature=0.2,
            ),
        )
        usage = response.usage_metadata
        return LLMResponse(
            text=response.text or "",
            input_tokens=getattr(usage, "prompt_token_count", 0) or 0,
            output_tokens=getattr(usage, "candidates_token_count", 0) or 0,
        )


class FakeLLM:
    """Return a fixed, language-aware answer citing passage IDs in the prompt."""

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
        english = "Always answer in natural, polite English" in system_prompt
        if not citations:
            text = "I can't find this information in the available passages." if english else "Je ne trouve pas cette information dans les passages disponibles."
            return LLMResponse(text)
        if english:
            return LLMResponse(f"According to the available information, see passage {citations}.")
        return LLMResponse(f"D'après les informations disponibles, consultez le passage {citations}.")


def get_llm(*, fake: bool = False) -> LLMClient:
    """Create the offline fake or the configured Anthropic/Gemini client."""
    if fake:
        return FakeLLM()
    provider = get_settings().llm_provider.strip().lower()
    if provider == "anthropic":
        return ClaudeLLM()
    if provider == "gemini":
        return GeminiLLM()
    raise ValueError("LLM_PROVIDER must be 'anthropic' or 'gemini'.")

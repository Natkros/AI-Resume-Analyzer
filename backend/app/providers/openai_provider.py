"""OpenAI LLM provider adapter — same interface as AnthropicProvider so the
two are interchangeable via app/providers/factory.py."""

from __future__ import annotations

from app.providers.anthropic_provider import _parse_json_with_repair
from app.providers.base import LLMProvider, LLMResponse


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set")
        import openai

        self._client = openai.OpenAI(api_key=api_key)
        self.model = model

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        schema: dict | None = None,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        import json as _json

        full_prompt = prompt
        if schema:
            full_prompt += (
                "\n\nRespond with ONLY valid JSON matching this schema, no prose:\n"
                f"{_json.dumps(schema)}"
            )
        response = self._client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[
                {
                    "role": "system",
                    "content": system
                    or "You are a precise, grounded resume/job analysis assistant. "
                    "Never fabricate candidate experience.",
                },
                {"role": "user", "content": full_prompt},
            ],
        )
        text = response.choices[0].message.content or ""
        raw_json = _parse_json_with_repair(text) if schema else None
        usage = response.usage
        return LLMResponse(
            text=text,
            raw_json=raw_json,
            model=self.model,
            input_tokens=getattr(usage, "prompt_tokens", None),
            output_tokens=getattr(usage, "completion_tokens", None),
        )

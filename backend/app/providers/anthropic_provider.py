"""Anthropic LLM provider adapter. Used for reasoning tasks (Phase 7):
recommendation generation, resume optimization, interview questions,
learning roadmaps. Never used for deterministic extraction/matching."""

from __future__ import annotations

import json

from app.providers.base import LLMProvider, LLMResponse


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "claude-sonnet-5"):
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set")
        import anthropic

        self._client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        schema: dict | None = None,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        full_prompt = prompt
        if schema:
            full_prompt += (
                "\n\nRespond with ONLY valid JSON matching this schema, no prose:\n"
                f"{json.dumps(schema)}"
            )

        message = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system or "You are a precise, grounded resume/job analysis assistant. "
            "Never fabricate candidate experience. Only state what the provided text supports.",
            messages=[{"role": "user", "content": full_prompt}],
        )
        text = "".join(block.text for block in message.content if hasattr(block, "text"))

        raw_json = None
        if schema:
            raw_json = _parse_json_with_repair(text)

        return LLMResponse(
            text=text,
            raw_json=raw_json,
            model=self.model,
            input_tokens=getattr(message.usage, "input_tokens", None),
            output_tokens=getattr(message.usage, "output_tokens", None),
        )


def _parse_json_with_repair(text: str) -> dict | None:
    text = text.strip()
    for candidate in (text, _strip_code_fence(text), _extract_braces(text)):
        if not candidate:
            continue
        try:
            return json.loads(candidate)
        except (json.JSONDecodeError, TypeError):
            continue
    return None


def _strip_code_fence(text: str) -> str:
    if text.startswith("```"):
        lines = text.splitlines()
        return "\n".join(lines[1:-1]) if len(lines) > 2 else text
    return text


def _extract_braces(text: str) -> str | None:
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return None

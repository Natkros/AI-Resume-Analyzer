"""Provider abstractions so LLM and embedding backends are swappable.

Concrete adapters live in app/providers/{anthropic,openai,local}.py and are
selected at runtime via settings.model_provider / settings.embedding_provider
(see app/providers/factory.py). Business logic must depend only on these
interfaces, never on a specific vendor SDK.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class LLMResponse:
    text: str
    raw_json: dict | None
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None


class LLMProvider(ABC):
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system: str | None = None,
        schema: dict[str, Any] | None = None,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """Generate a completion. If `schema` (JSON schema) is provided,
        implementations should request/validate structured JSON output."""
        raise NotImplementedError


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError

    @property
    @abstractmethod
    def dimensions(self) -> int:
        raise NotImplementedError

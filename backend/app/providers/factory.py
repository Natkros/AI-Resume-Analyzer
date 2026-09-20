"""Selects concrete provider implementations from settings, so the rest of
the app depends only on the LLMProvider / EmbeddingProvider interfaces."""

from __future__ import annotations

from functools import lru_cache

from app.core.config import Settings, get_settings
from app.providers.base import EmbeddingProvider, LLMProvider
from app.providers.local_embeddings import get_local_embedding_provider


class LLMUnavailableError(RuntimeError):
    """Raised when no LLM provider is configured (e.g. missing API key)."""


def get_embedding_provider(settings: Settings | None = None) -> EmbeddingProvider:
    settings = settings or get_settings()
    if settings.embedding_provider == "local":
        return get_local_embedding_provider(settings.embedding_model)
    raise ValueError(f"Unknown embedding provider: {settings.embedding_provider}")


@lru_cache
def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    if settings.model_provider == "anthropic":
        if not settings.anthropic_api_key:
            raise LLMUnavailableError(
                "MODEL_PROVIDER=anthropic but ANTHROPIC_API_KEY is not set. "
                "LLM-dependent features (recommendations, optimization, interview prep, "
                "roadmap) are disabled until it is configured."
            )
        from app.providers.anthropic_provider import AnthropicProvider

        return AnthropicProvider(api_key=settings.anthropic_api_key, model=settings.model_name)
    if settings.model_provider == "openai":
        if not settings.openai_api_key:
            raise LLMUnavailableError("MODEL_PROVIDER=openai but OPENAI_API_KEY is not set.")
        from app.providers.openai_provider import OpenAIProvider

        return OpenAIProvider(api_key=settings.openai_api_key, model=settings.model_name)
    raise ValueError(f"Unknown model provider: {settings.model_provider}")

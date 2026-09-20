"""Local sentence-transformers embedding provider, with a dependency-free
lexical fallback so the app still runs in offline/sandboxed environments
where the transformer model weights cannot be downloaded.

The fallback is a hashed bag-of-words vector (not semantically rich, but
deterministic and dependency-free) purely so cosine similarity still
produces a sane, monotonic signal for exact/near-exact phrase overlap
when the real model is unavailable. It is never presented as a substitute
for genuine semantic embeddings; callers can check `is_fallback`.
"""

from __future__ import annotations

import hashlib
import math
import re
from functools import lru_cache

from app.providers.base import EmbeddingProvider

_FALLBACK_DIM = 256


class LocalEmbeddingProvider(EmbeddingProvider):
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self.is_fallback = False
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(model_name)
        except Exception:
            self.is_fallback = True

    @property
    def dimensions(self) -> int:
        if self._model is not None:
            return self._model.get_sentence_embedding_dimension()
        return _FALLBACK_DIM

    def embed(self, texts: list[str]) -> list[list[float]]:
        if self._model is not None:
            vectors = self._model.encode(texts, normalize_embeddings=True)
            return [v.tolist() for v in vectors]
        return [_hashed_bow_vector(t) for t in texts]


def _hashed_bow_vector(text: str) -> list[float]:
    vec = [0.0] * _FALLBACK_DIM
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    for tok in tokens:
        idx = int(hashlib.md5(tok.encode()).hexdigest(), 16) % _FALLBACK_DIM
        vec[idx] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


@lru_cache
def get_local_embedding_provider(model_name: str) -> LocalEmbeddingProvider:
    return LocalEmbeddingProvider(model_name)

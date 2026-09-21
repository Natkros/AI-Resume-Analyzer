"""Vector store abstraction so the RAG retriever is not tied to a specific
vector DB. `InMemoryVectorStore` needs no external service (used for the
knowledge base, which is small and rebuilt at process start). `QdrantVectorStore`
is a real adapter for production use, selected via VECTOR_DB_PROVIDER.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np


@dataclass
class VectorRecord:
    id: str
    text: str
    vector: list[float]
    metadata: dict


@dataclass
class ScoredRecord:
    record: VectorRecord
    score: float


class VectorStore(ABC):
    @abstractmethod
    def upsert(self, records: list[VectorRecord]) -> None: ...

    @abstractmethod
    def search(self, query_vector: list[float], top_k: int = 5) -> list[ScoredRecord]: ...


class InMemoryVectorStore(VectorStore):
    def __init__(self):
        self._records: list[VectorRecord] = []

    def upsert(self, records: list[VectorRecord]) -> None:
        self._records.extend(records)

    def search(self, query_vector: list[float], top_k: int = 5) -> list[ScoredRecord]:
        if not self._records:
            return []
        q = np.array(query_vector)
        q_norm = np.linalg.norm(q) or 1e-9
        scored = []
        for record in self._records:
            v = np.array(record.vector)
            v_norm = np.linalg.norm(v) or 1e-9
            sim = float(np.dot(q, v) / (q_norm * v_norm))
            scored.append(ScoredRecord(record=record, score=sim))
        scored.sort(key=lambda s: s.score, reverse=True)
        return scored[:top_k]

    def clear(self) -> None:
        self._records = []


class QdrantVectorStore(VectorStore):
    """Thin adapter over the Qdrant client. Not exercised in tests (requires
    a running Qdrant instance); kept interface-compatible with InMemoryVectorStore
    so swapping VECTOR_DB_PROVIDER=qdrant requires no caller changes."""

    def __init__(self, url: str, collection: str = "knowledge_base", dimensions: int = 384):
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams

        self._client = QdrantClient(url=url)
        self._collection = collection
        if not self._client.collection_exists(collection):
            self._client.create_collection(
                collection_name=collection,
                vectors_config=VectorParams(size=dimensions, distance=Distance.COSINE),
            )

    def upsert(self, records: list[VectorRecord]) -> None:
        from qdrant_client.models import PointStruct

        points = [
            PointStruct(id=r.id, vector=r.vector, payload={"text": r.text, **r.metadata}) for r in records
        ]
        self._client.upsert(collection_name=self._collection, points=points)

    def search(self, query_vector: list[float], top_k: int = 5) -> list[ScoredRecord]:
        hits = self._client.search(collection_name=self._collection, query_vector=query_vector, limit=top_k)
        results = []
        for hit in hits:
            payload = dict(hit.payload or {})
            text = payload.pop("text", "")
            record = VectorRecord(id=str(hit.id), text=text, vector=[], metadata=payload)
            results.append(ScoredRecord(record=record, score=hit.score))
        return results
